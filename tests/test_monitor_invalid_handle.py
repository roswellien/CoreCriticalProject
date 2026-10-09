"""Authored invalid-handle fixture; proves debugger sensitivity independently of MW3."""

from datetime import datetime
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/game-monitor"))
core = importlib.import_module("core")
monitor = importlib.import_module("monitor")
PROBE = ROOT / "build/game-monitor/Release/monitor_probe.exe"


@unittest.skipUnless(os.name == "nt" and PROBE.exists(), "Build the authored Windows monitor probe first")
class InvalidHandleMonitorTests(unittest.TestCase):
    def run_probe(self, debug):
        name = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8]
        directory = ROOT / "reports/monitor-tests" / ("invalid-handle-" + name)
        log = directory.with_suffix(".probe.log")
        directory.parent.mkdir(parents=True, exist_ok=True)
        config = monitor.Config(game=PROBE, directory=directory, debug=debug, duration=15,
                                command=[str(PROBE), "invalid-handle", str(log)], logs=[log])
        state = None
        try:
            result = monitor.run_session(config)
            state = json.loads((directory / "status.json").read_text())
            self.assertEqual(result, 0, state.get("error"))
            self.assertEqual(state["state"], "exited", state)
            events = core.read_events(directory, limit=10000)["events"]
            return events, state, log.read_text()
        finally:
            # Clean up only this fixture if a failed check unexpectedly leaves it alive.
            if state and state.get("target_pid"):
                from win32 import Process
                try:
                    process = Process(state["target_pid"])
                except OSError:
                    process = None
                if process:
                    try:
                        if process.alive() and Path(process.path).resolve() == PROBE.resolve():
                            subprocess.run(["taskkill", "/PID", str(process.pid), "/F"],
                                           capture_output=True, check=True)
                    finally:
                        process.close()

    def test_passive_invalid_close_returns_error_and_process_survives(self):
        events, state, log = self.run_probe(debug=False)
        self.assertFalse(state["capabilities"]["windows_debug_events"])
        self.assertIn("CloseHandle result=0 error=6\n", log)
        self.assertIn("probe done\n", log)
        exits = [event for event in events if event["event"] == "exit"]
        self.assertEqual([event["data"]["exit_code"] for event in exits], [0])
        self.assertFalse(any(event["event"] == "exception" for event in events))

    def test_debugger_forwards_invalid_handle_to_second_chance_and_exit(self):
        events, state, log = self.run_probe(debug=True)
        self.assertTrue(state["capabilities"]["windows_debug_events"])
        self.assertIn("probe closing deliberately invalid non-pseudo handle\n", log)
        self.assertNotIn("CloseHandle result=", log)
        self.assertNotIn("probe done\n", log)
        exceptions = [event for event in events if event["event"] == "exception"
                      and event["data"]["code"] == "0xC0000008"]
        self.assertEqual([event["data"]["first_chance"] for event in exceptions], [True, False])
        self.assertEqual(exceptions[-1]["severity"], "critical")
        exits = [event for event in events if event["event"] == "exit"]
        self.assertEqual([event["data"]["exit_code"] for event in exits], [0xC0000008])


if __name__ == "__main__":
    unittest.main()
