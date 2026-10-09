"""Authored logging tests; live Windows probes run only when explicitly built."""

import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/game-monitor"))
core = importlib.import_module("core")
monitor = importlib.import_module("monitor")
PROBE = ROOT / "build/game-monitor/Release/monitor_probe.exe"


class HookLaunchTests(unittest.TestCase):
    def test_default_launch_is_passive_and_debugging_is_explicit(self):
        from launch_hook import collector_command
        arguments = (Path("game.exe"), Path("hook-run"), Path("monitor-session"))
        self.assertIn("--no-debug", collector_command(*arguments))
        self.assertNotIn("--no-debug", collector_command(*arguments, debug=True))

    def test_ready_requires_live_collector(self):
        from launch_hook import wait_ready
        with tempfile.TemporaryDirectory() as directory:
            session = Path(directory)
            (session / "status.json").write_text(json.dumps({"state": "running", "target_pid": 123}))
            live = SimpleNamespace(poll=lambda: None)
            self.assertEqual(wait_ready(live, session)["target_pid"], 123)
            dead = SimpleNamespace(poll=lambda: 7, returncode=7)
            with self.assertRaisesRegex(RuntimeError, "exited with code 7"):
                wait_ready(dead, session)

    def test_failed_collector_status_is_reported(self):
        from launch_hook import wait_ready
        with tempfile.TemporaryDirectory() as directory:
            session = Path(directory)
            (session / "status.json").write_text(json.dumps({"state": "collector_error", "error": "probe failure"}))
            with self.assertRaisesRegex(RuntimeError, "probe failure"):
                wait_ready(SimpleNamespace(poll=lambda: None), session)

    def test_startup_timeout_does_not_claim_ready_or_terminate(self):
        from launch_hook import wait_ready
        with tempfile.TemporaryDirectory() as directory:
            child = SimpleNamespace(pid=123)
            self.assertEqual(wait_ready(child, Path(directory), timeout=0)["state"], "starting")

    @unittest.skipUnless(os.name == "nt" and PROBE.exists(), "requires authored Windows probe")
    def test_duplicate_check_finds_exact_probe_image(self):
        import subprocess
        from launch_hook import ensure_closed
        from win32 import pids_for_image
        with tempfile.TemporaryDirectory() as directory:
            child = subprocess.Popen([str(PROBE), "linger", str(Path(directory) / "probe.log")])
            try:
                self.assertIn(child.pid, pids_for_image(PROBE))
                self.assertNotIn(child.pid, pids_for_image(PROBE.with_name("different.exe")))
                with self.assertRaisesRegex(RuntimeError, "already running"):
                    ensure_closed(PROBE)
            finally:
                child.terminate()
                child.wait(timeout=10)


class MonitorCoreTests(unittest.TestCase):
    def test_partial_lines_are_not_reported_early(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "log"
            tail = core.Tail(path)
            path.write_bytes(b"ERROR: par")
            self.assertEqual(tail.poll()[0], [])
            with path.open("ab") as stream:
                stream.write(b"tial\nnext\n")
            self.assertEqual(tail.poll()[0], ["ERROR: partial", "next"])

    def test_existing_partial_record_is_skipped(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "log"
            path.write_bytes(b"old partial")
            tail = core.Tail(path)
            with path.open("ab") as stream:
                stream.write(b" completed\nnew\n")
            self.assertEqual(tail.poll()[0], ["new"])

    def test_existing_history_skipped_and_truncation_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "log"
            path.write_bytes(b"old old history\n")
            tail = core.Tail(path)
            self.assertEqual(tail.poll()[0], [])
            path.write_bytes(b"new\n")
            self.assertEqual(tail.poll(), (["new"], ["source_reset"]))

    def test_equal_length_rewrite_not_mistaken_for_no_change(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "log"
            path.write_bytes(b"old\n")
            tail = core.Tail(path)
            old_time = path.stat().st_mtime_ns
            path.write_bytes(b"new\n")
            os.utime(path, ns=(old_time + 1000000, old_time + 1000000))
            self.assertEqual(tail.poll(), (["new"], ["source_reset"]))

    def test_replaced_file_and_oversized_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "log"
            path.write_bytes(b"old\n")
            tail = core.Tail(path, max_line=8)
            replacement = path.with_suffix(".new")
            replacement.write_bytes(b"new\n12345678901\nlast\n")
            replacement.replace(path)
            self.assertEqual(tail.poll(), (["new", "last"], ["source_reset", "oversized_line_dropped"]))

    def test_bounded_read_and_unterminated_final_line(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "log"
            tail = core.Tail(path, chunk_bytes=4)
            path.write_bytes(b"one\nlast")
            self.assertEqual(tail.poll()[0], ["one"])
            self.assertEqual(tail.poll()[0], [])
            self.assertEqual(tail.finish(), "last")

    def test_classification_does_not_mistake_success_for_errors(self):
        self.assertEqual(core.severity("init PASSED; no errors; 0 errors"), "info")
        self.assertEqual(core.severity("failed to initialize"), "error")
        self.assertEqual(core.severity("fatal failure"), "critical")
        self.assertEqual(core.severity("handled exception returned normally"), "info")
        self.assertEqual(core.severity("unhandled exception"), "error")
        self.assertEqual(core.severity("handled exception but ERROR in recovery"), "error")

    def test_rotation_cursors_and_explicit_history_gap(self):
        with tempfile.TemporaryDirectory() as directory:
            store = core.EventStore(Path(directory) / "run", segment_bytes=512, segments=2)
            for number in range(12):
                store.emit("test", "message", text="x" * 100, number=number)
            store.status(state="running")
            store.close()
            self.assertEqual(len(list(store.directory.glob("events-*.jsonl"))), 2)
            view = core.read_events(store.directory, limit=1)
            self.assertTrue(view["retention_gap"])
            next_view = core.read_events(store.directory, after=view["next_cursor"])
            self.assertFalse(next_view["retention_gap"])
            self.assertGreater(next_view["next_cursor"], view["next_cursor"])
            state = json.loads((store.directory / "status.json").read_text())
            self.assertEqual(state["latest_seq"], 12)

    def test_hook_failures_and_invalid_json_alerts(self):
        with tempfile.TemporaryDirectory() as directory:
            store = core.EventStore(Path(directory) / "run")
            core.ingest(store, "hook", '{"event":"fatal","message":"mismatch"}', True)
            core.ingest(store, "hook", '{"event":"selftest","mismatches":1}', True)
            core.ingest(store, "hook", 'broken', True)
            store.close()
            self.assertEqual([r["severity"] for r in core.read_events(store.directory)["events"]],
                             ["critical", "critical", "warning"])

    def test_exclusive_sessions_and_invalid_cursors(self):
        with tempfile.TemporaryDirectory() as directory:
            store = core.EventStore(Path(directory) / "run")
            with self.assertRaises(FileExistsError):
                core.EventStore(store.directory)
            with self.assertRaises(ValueError):
                core.read_events(store.directory, after=-1)
            store.close()

    def test_live_partial_event_and_large_hook_records(self):
        with tempfile.TemporaryDirectory() as directory:
            store = core.EventStore(Path(directory) / "run")
            core.ingest(store, "hook", '{"event":"big","text":"' + "x" * 20000 + '"}', True)
            core.ingest(store, "hook", '[' * 2000, True)
            store.file.write(b'{"partial":')
            store.file.flush()
            view = core.read_events(store.directory)
            self.assertEqual([r["event"] for r in view["events"]],
                             ["structured_event_too_large", "invalid_json"])
            store.close()

    def test_wrong_game_identity_rejected_without_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "game.exe"
            path.write_bytes(b"authored invalid image")
            with self.assertRaisesRegex(ValueError, "exact admitted"):
                monitor.admit(path)


@unittest.skipUnless(os.name == "nt", "requires real Win32 file sharing")
class WindowsStatusSharingTests(unittest.TestCase):
    @staticmethod
    def hold_reader(path):
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        create = kernel.CreateFileW
        create.restype = wintypes.HANDLE
        create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                           wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        close = kernel.CloseHandle
        close.restype = wintypes.BOOL
        close.argtypes = [wintypes.HANDLE]
        # Read/write sharing is permitted, but atomic replacement needs DELETE.
        handle = create(str(path), 0x80000000, 1 | 2, None, 3, 0x80, None)
        if handle == wintypes.HANDLE(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        return lambda: close(handle)

    def test_reader_without_delete_sharing_releases_and_status_keeps_events(self):
        with tempfile.TemporaryDirectory() as directory:
            store = core.EventStore(Path(directory) / "run")
            release = None
            timer = None
            try:
                store.emit("test", "before_reader")
                store.status(state="old")
                status = store.directory / "status.json"
                release = self.hold_reader(status)
                temporary = store.directory / "status.tmp"
                temporary.write_text('{"raw_control":true}')
                # Reproduce the old implementation's actual Win32 failure first.
                with self.assertRaises(PermissionError) as failure:
                    temporary.replace(status)
                self.assertIn(failure.exception.winerror, (5, 32, 33))
                self.assertEqual(json.loads(status.read_text())["state"], "old")
                timer = threading.Timer(.05, release)
                timer.start()
                release = None
                started = time.monotonic()
                store.status(state="new")
                elapsed = time.monotonic() - started
                self.assertGreaterEqual(elapsed, .035)
                self.assertLess(elapsed, 1.5)
                store.emit("test", "after_reader")
                store.status(state="new")
                snapshot = json.loads(status.read_text())
                self.assertEqual((snapshot["state"], snapshot["latest_seq"]), ("new", 2))
                self.assertEqual([event["event"] for event in core.read_events(store.directory)["events"]],
                                 ["before_reader", "after_reader"])
                self.assertFalse(temporary.exists())
            finally:
                if timer:
                    timer.join(timeout=2)
                if release:
                    release()
                store.close()

    def test_persistent_sharing_failure_still_propagates_at_deadline(self):
        with tempfile.TemporaryDirectory() as directory:
            store = core.EventStore(Path(directory) / "run")
            release = None
            try:
                store.status(state="old")
                status = store.directory / "status.json"
                release = self.hold_reader(status)
                started = time.monotonic()
                with self.assertRaises(PermissionError) as failure:
                    store.status(state="unpublished")
                self.assertIn(failure.exception.winerror, (5, 32, 33))
                self.assertGreaterEqual(time.monotonic() - started, .9)
                self.assertLess(time.monotonic() - started, 2)
                self.assertEqual(json.loads(status.read_text())["state"], "old")
                self.assertEqual(json.loads((store.directory / "status.tmp").read_text())["state"], "unpublished")
            finally:
                if release:
                    release()
                store.close()

    def test_unrelated_io_failure_propagates_without_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory) / "status.tmp"
            temporary.write_text('{"state":"unpublished"}')
            started = time.monotonic()
            with self.assertRaises(FileNotFoundError):
                core._replace_status_snapshot(temporary, Path(directory) / "missing" / "status.json")
            self.assertLess(time.monotonic() - started, .5)
            self.assertEqual(json.loads(temporary.read_text())["state"], "unpublished")


@unittest.skipUnless(os.name == "nt" and PROBE.exists(), "Build the authored Windows monitor probe first")
class WindowsMonitorTests(unittest.TestCase):
    def run_probe(self, mode, duration=None):
        # Keep artifacts under ignored reports for later inspection.
        from datetime import datetime
        import uuid
        directory = ROOT / "reports/monitor-tests" / (datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8])
        log = directory.with_suffix(".probe.log")
        directory.parent.mkdir(parents=True, exist_ok=True)
        config = monitor.Config(game=PROBE, directory=directory, command=[str(PROBE), mode, str(log)],
                                logs=[log], duration=duration)
        result = monitor.run_session(config)
        records = core.read_events(directory, limit=10000)["events"]
        state = json.loads((directory / "status.json").read_text())
        self.assertEqual(result, 0, state.get("error"))
        return records, state

    def test_normal_unicode_handled_exception_file_error_and_latency(self):
        from datetime import datetime
        records, state = self.run_probe("normal")
        self.assertEqual(state["state"], "exited")
        messages = [r for r in records if r["event"] == "debug_message"]
        self.assertTrue(any(r["data"]["text"] == "MW34 unicode probe: \u03a9" for r in messages))
        self.assertTrue(any("handled exception returned normally" in r["data"]["text"] and
                            r["severity"] == "info" for r in messages))
        self.assertFalse(any(r["event"] == "exception" and r["data"]["code"] == "0x4000001F" for r in records))
        handled = [r for r in records if r["event"] == "exception" and r["data"]["code"] == "0xE0003434"]
        self.assertEqual([r["data"]["first_chance"] for r in handled], [True])
        errors = [r for r in records if r["source"] == "extra_log_0" and r["severity"] == "error"]
        self.assertEqual(len(errors), 1)
        self.assertTrue(any(r["data"].get("text") == "partial line complete" for r in records))
        timed = next(r for r in messages if r["data"]["text"].startswith("MW34_LATENCY_UTC_MS="))
        emitted = int(timed["data"]["text"].split("=", 1)[1])
        received = datetime.fromisoformat(timed["timestamp_utc"]).timestamp() * 1000
        self.assertGreaterEqual(received - emitted, -10)
        self.assertLess(received - emitted, 1000)
        (ROOT / "reports/monitor-tests/latest-latency.json").write_text(json.dumps({
            "debug_receipt_latency_ms": round(received - emitted, 3), "session_id": state["session_id"]}))

    def test_unhandled_exception_reaches_second_chance_and_nonzero_exit(self):
        records, state = self.run_probe("crash")
        exceptions = [r for r in records if r["event"] == "exception" and r["data"]["code"] == "0xE0003435"]
        self.assertEqual([r["data"]["first_chance"] for r in exceptions], [True, False])
        self.assertEqual(exceptions[-1]["severity"], "critical")
        self.assertTrue(any(r["event"] == "exit" and r["data"]["exit_code"] != 0 for r in records))
        self.assertEqual(state["state"], "exited")

    def test_os_hang_and_recovery_transitions(self):
        records, _ = self.run_probe("hang")
        self.assertTrue(any(r["event"] == "window_unresponsive" for r in records))
        self.assertTrue(any(r["event"] == "window_responsive_again" for r in records))

    def test_time_limit_detaches_without_terminating_target(self):
        from win32 import Process
        records, state = self.run_probe("linger", duration=1.5)
        self.assertEqual(state["state"], "detached")
        process = Process(state["target_pid"])
        try:
            self.assertTrue(process.alive())
        finally:
            # Only the explicitly authored test process is cleaned up here.
            subprocess = importlib.import_module("subprocess")
            subprocess.run(["taskkill", "/PID", str(process.pid), "/F"], capture_output=True, check=True)
            process.close()
        self.assertTrue(any(r["event"] == "time_limit" for r in records))

    def test_late_debug_attach_captures_messages_and_leaves_target_alive(self):
        import subprocess
        import uuid
        from win32 import Process
        directory = ROOT / "reports/monitor-tests" / ("late-attach-" + uuid.uuid4().hex[:8])
        log = directory.with_suffix(".probe.log")
        child = subprocess.Popen([str(PROBE), "linger", str(log)])
        try:
            config = monitor.Config(game=PROBE, directory=directory, mode="attach", pid=child.pid,
                                    debug=True, duration=2.5, logs=[log])
            self.assertEqual(monitor.run_session(config), 0)
            records = core.read_events(directory, limit=10000)["events"]
            self.assertTrue(any(r["event"] == "debugger_attached" for r in records))
            self.assertTrue(any(r["event"] == "debug_message" for r in records))
            process = Process(child.pid)
            try:
                self.assertTrue(process.alive())
            finally:
                process.close()
        finally:
            child.terminate()
            child.wait(timeout=5)

    def test_live_reader_marker_and_stop_commands(self):
        import subprocess
        import time
        import uuid
        from win32 import Process
        directory = ROOT / "reports/monitor-tests" / ("commands-" + uuid.uuid4().hex[:8])
        log = directory.with_suffix(".probe.log")
        code = ("import sys; from pathlib import Path; "
                "sys.path.insert(0,sys.argv[1]); import monitor; "
                "c=monitor.Config(game=Path(sys.argv[2]),directory=Path(sys.argv[3]),"
                "command=[sys.argv[2],'linger',sys.argv[4]],logs=[Path(sys.argv[4])]); "
                "raise SystemExit(monitor.run_session(c))")
        child = subprocess.Popen([sys.executable, "-c", code, str(ROOT / "tools/game-monitor"),
                                  str(PROBE), str(directory), str(log)], stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True)
        pid = None
        try:
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if (directory / "status.json").exists():
                    state = json.loads((directory / "status.json").read_text())
                    if state["state"] == "running":
                        pid = state["target_pid"]
                        break
                if child.poll() is not None:
                    self.fail(child.communicate())
                time.sleep(.1)
            self.assertIsNotNone(pid)
            script = str(ROOT / "tools/game-monitor/monitor.py")
            subprocess.run([sys.executable, script, "mark", str(directory), "fixture marker"], check=True, capture_output=True)
            time.sleep(.3)
            view = subprocess.run([sys.executable, script, "read", str(directory), "--after", "0"],
                                  check=True, capture_output=True, text=True)
            self.assertTrue(any(r["event"] == "marker" for r in json.loads(view.stdout)["events"]))
            subprocess.run([sys.executable, script, "stop", str(directory)], check=True, capture_output=True)
            stdout, stderr = child.communicate(timeout=5)
            self.assertEqual(child.returncode, 0, (stdout, stderr))
            self.assertEqual(json.loads((directory / "status.json").read_text())["state"], "detached")
            watch = subprocess.run([sys.executable, script, "watch", str(directory), "--alerts-only", "--duration", "1"],
                                   check=True, capture_output=True, text=True)
            final = json.loads(watch.stdout.splitlines()[-1])
            self.assertEqual(final["type"], "watch_end")
            self.assertEqual(final["collector_state"], "detached")
            process = Process(pid)
            try:
                self.assertTrue(process.alive())
                self.assertEqual(Path(process.path).resolve(), PROBE.resolve())
            finally:
                process.close()
        finally:
            if child.poll() is None:
                child.terminate()
                child.communicate(timeout=5)
            if pid:
                subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, check=False)


if __name__ == "__main__":
    unittest.main()
