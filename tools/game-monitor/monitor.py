"""Local MW3 live diagnostics: launch/attach, cursor reads, status, markers and stop."""

import argparse
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import uuid

from core import EventStore, Tail, ingest, read_events, utc_now

ROOT = Path(__file__).resolve().parents[2]
GAME_SHA = "95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf"


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def admit(game):
    game = Path(game).resolve(strict=True)
    if sha(game) != GAME_SHA:
        raise ValueError("Unsupported MW3 executable; exact admitted image required")
    return game


@dataclass
class Config:
    game: Path
    directory: Path
    mode: str = "baseline"
    pid: int | None = None
    debug: bool = True
    period: float = .02
    metrics_period: float = 1.0
    duration: float | None = None
    hook_run: Path | None = None
    logs: list = field(default_factory=list)
    segment_bytes: int = 8 * 1024 * 1024
    segments: int = 8
    # Authored integration fixtures can invoke this API with their own command.
    # No CLI option admits unreviewed game images.
    command: list | None = None


def run_session(config):
    from win32 import Process, Debugger
    store = EventStore(config.directory, config.segment_bytes, config.segments)
    child, process, debugger, output = None, None, None, None
    state, error = "starting", None
    metrics, unresponsive = {}, False
    started, last_metrics = time.monotonic(), 0.0
    last_status = 0.0
    tails = [("game_log", Tail(config.game.parent / "mech3.out"), False)]
    tails += [(f"extra_log_{i}", Tail(path), False) for i, path in enumerate(config.logs)]
    hook_trace = config.hook_run / "game.jsonl" if config.hook_run else None
    source_failures = set()

    def emit(*args, **kwargs):
        return store.emit(*args, **kwargs)

    def status(force=False):
        nonlocal last_status
        now = time.monotonic()
        if not force and now - last_status < .2:
            return
        store.status(state=state, target_pid=process.pid if process else None,
                     target_path=str(config.game), mode=config.mode, metrics=metrics,
                     capabilities={"file_poll_ms": round(config.period * 1000),
                                   "metrics_poll_ms": round(config.metrics_period * 1000),
                                   "status_poll_ms": 200,
                                   "windows_debug_events": debugger is not None,
                                   "hook_events": hook_trace is not None,
                                   "os_window_health": process is not None,
                                   "source_timestamps": "observer receipt time; original logs may be buffered",
                                   "visual_glitch_detection": False, "frame_timing": False},
                     error=error)
        last_status = now

    def collect(final=False):
        for source, tail, structured in tails:
            try:
                for _ in range(16 if final else 1):
                    lines, notices = tail.poll()
                    for notice in notices:
                        emit(source, notice, "warning", path=str(tail.path))
                    for line in lines:
                        ingest(store, source, line, structured)
                    if not lines:
                        break
                if final and (partial := tail.finish()) is not None:
                    emit(source, "incomplete_final_line", "warning", text=partial[:4096])
                source_failures.discard(source)
            except OSError as failure:
                if source not in source_failures:
                    emit("collector", "source_unavailable", "warning", source_name=source, error=str(failure))
                    source_failures.add(source)

    def commands():
        for path in sorted(store.directory.glob("marker-*.request"))[:32]:
            try:
                request = json.loads(path.read_text(encoding="utf-8"))
                if request.get("session_id") != store.session:
                    raise ValueError("Marker session identity differs")
                text = request.get("text")
                if not isinstance(text, str) or len(text) > 4096:
                    raise ValueError("Invalid marker")
                emit("user", "marker", text=text)
            except (ValueError, OSError) as failure:
                emit("collector", "invalid_marker", "warning", error=str(failure))
            path.unlink(missing_ok=True)
        stop = store.directory / "stop.request"
        if stop.exists():
            request = json.loads(stop.read_text(encoding="utf-8"))
            if request.get("session_id") == store.session:
                return True
        return False

    try:
        emit("collector", "session_start", mode=config.mode, target=str(config.game),
             game_sha256=sha(config.game), poll_ms=round(config.period * 1000))
        if config.mode == "attach":
            if not config.pid:
                raise ValueError("Attach requires an explicit PID")
            process = Process(config.pid)
        else:
            if config.mode == "hook":
                if not config.hook_run or hook_trace.exists():
                    raise ValueError("Hook mode needs a prepared run with no existing game.jsonl")
                record = json.loads((config.hook_run / "build.json").read_text(encoding="utf-8-sig"))
                launcher = ROOT / "build/in-game-hook/Release/mw34_hook_launcher.exe"
                dll = ROOT / "build/in-game-hook/Release/mw34_helper_hook.dll"
                for key, path in (("game_sha256", config.game), ("hook_sha256", dll), ("launcher_sha256", launcher)):
                    if record.get(key) != sha(path):
                        raise ValueError(f"Hook build identity differs: {key}")
                command = [str(launcher), str(config.game), str(dll), str(hook_trace)]
                tails.append(("hook", Tail(hook_trace, from_start=True), True))
            else:
                command = config.command or [str(config.game)]
            output = (store.directory / "launcher-output.log").open("xb", buffering=0)
            tails.append(("launcher", Tail(store.directory / "launcher-output.log", from_start=True), False))
            flags = 2 if config.debug and config.mode == "baseline" else 0
            child = subprocess.Popen(command, cwd=config.game.parent, stdout=output, stderr=output,
                                     creationflags=flags)
            if flags:
                debugger = Debugger(child.pid)
            if config.mode == "baseline":
                process = Process(child.pid)
            else:
                deadline = time.monotonic() + 40
                installed_tail = Tail(hook_trace, from_start=True)
                while not process and time.monotonic() < deadline:
                    lines, _ = installed_tail.poll()
                    for line in lines:
                        record = json.loads(line)
                        if record.get("event") == "installed":
                            process = Process(record["pid"])
                            break
                    collect()
                    status()
                    if child.poll() is not None and child.returncode != 0:
                        raise RuntimeError(f"Hook launcher failed: exit {child.returncode}")
                    if commands():
                        raise RuntimeError("Stopped while waiting for hook installation; inspect launcher output")
                    if not process:
                        time.sleep(config.period)
                if not process:
                    raise RuntimeError("No installed hook PID observed within 40 seconds")
        if Path(process.path).resolve() != config.game.resolve():
            raise ValueError("PID belongs to a different executable")
        if config.debug and config.mode in ("hook", "attach"):
            if config.mode == "hook":
                # The startup debugger must finish before our observer attaches.
                if child.wait(timeout=5) != 0:
                    raise RuntimeError("Hook launcher failed after its installed event")
            debugger = Debugger(process.pid, attach=True)
            emit("collector", "debugger_attached", pid=process.pid,
                 startup_capture="late attach; events before attachment may be unavailable")
        state = "running"
        emit("collector", "target_bound", pid=process.pid, image_sha256=sha(process.path))
        if config.mode == "attach" and hook_trace:
            tails.append(("hook", Tail(hook_trace), True))
        status(force=True)
        print(json.dumps({"session": str(store.directory), "pid": process.pid, "state": state}), flush=True)
        while True:
            loop_start = time.monotonic()
            if debugger:
                debugger.poll(process, emit)
            collect()
            if not process.alive():
                code = process.exit_code()
                state = "exited"
                emit("process", "exit", "info" if code == 0 else "error", pid=process.pid,
                     exit_code=code, exit_hex=f"0x{code:08X}", classification="nonzero_exit" if code else "zero_exit")
                collect(final=True)
                break
            now = time.monotonic()
            if now - last_metrics >= config.metrics_period:
                try:
                    metrics = process.sample()
                    emit("process", "sample", **metrics)
                    hung = any(window["os_not_responding"] for window in metrics["windows"])
                    if hung != unresponsive:
                        emit("process", "window_unresponsive" if hung else "window_responsive_again",
                             "warning" if hung else "info", pid=process.pid,
                             scope="Windows message-pump health; not proof of a simulation/rendering stall")
                        unresponsive = hung
                except OSError as failure:
                    emit("collector", "metrics_unavailable", "warning", error=str(failure))
                last_metrics = now
            if commands():
                state = "detached"
                emit("collector", "stop_requested", game_left_running=True)
                break
            if config.duration and now - started >= config.duration:
                state = "detached"
                emit("collector", "time_limit", game_left_running=True)
                break
            status()
            time.sleep(max(0, config.period - (time.monotonic() - loop_start)))
    except KeyboardInterrupt:
        state = "detached"
        emit("collector", "interrupted", game_left_running=True)
    except Exception as failure:
        state, error = "collector_error", str(failure)
        emit("collector", "failure", "critical", error=error)
    finally:
        if debugger:
            try:
                # Drain pending notifications before detaching an alive target.
                try:
                    if process and not debugger.exited:
                        debugger.poll(process, emit)
                finally:
                    debugger.close()
            except OSError as failure:
                error = str(failure)
                state = "collector_error"
                emit("collector", "detach_failed", "critical", error=error)
        if process:
            process.close()
        if output:
            output.close()
        if child:
            if child.poll() is None:
                # Reap the child when it exits; detaching must leave it alive.
                threading.Thread(target=child.wait, daemon=True).start()
            else:
                child.wait()
        emit("collector", "session_end", state=state, error=error)
        status(force=True)
        store.close()
    return 1 if error else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    for action in ("launch", "attach"):
        launch = sub.add_parser(action)
        launch.add_argument("--game", type=Path, default=ROOT / "MW3/Mech3.exe")
        launch.add_argument("--session", type=Path)
        launch.add_argument("--poll-ms", type=int, default=20)
        launch.add_argument("--duration", type=float)
        launch.add_argument("--log", type=Path, action="append", default=[])
        launch.add_argument("--hook-run", type=Path)
        if action == "launch":
            launch.add_argument("--mode", choices=("baseline", "hook"), default="baseline")
            launch.add_argument("--no-debug", action="store_true")
        else:
            launch.add_argument("--pid", type=int, required=True)
            launch.add_argument("--debug", action="store_true")
    for action in ("read", "watch", "status", "stop", "mark"):
        view = sub.add_parser(action)
        view.add_argument("session", type=Path)
        if action in ("read", "watch"):
            view.add_argument("--after", type=int, default=0)
            view.add_argument("--limit", type=int, default=200)
            view.add_argument("--alerts-only", action="store_true")
        if action == "watch":
            view.add_argument("--duration", type=float, default=30)
        if action == "mark":
            view.add_argument("text")
    args = parser.parse_args()
    if args.action == "read":
        result = read_events(args.session, args.after, args.limit)
        if args.alerts_only:
            result["events"] = [r for r in result["events"] if r["severity"] != "info"]
        print(json.dumps(result, indent=2))
    elif args.action == "watch":
        if not 0 < args.duration <= 60:
            raise ValueError("Watch duration must be > 0 and <= 60 seconds")
        deadline, cursor = time.monotonic() + args.duration, args.after
        while True:
            result = read_events(args.session, cursor, args.limit)
            cursor = result["next_cursor"]
            if args.alerts_only:
                result["events"] = [r for r in result["events"] if r["severity"] != "info"]
            if result["events"] or result["retention_gap"]:
                print(json.dumps({"type": "events", **result}), flush=True)
            state = json.loads((args.session / "status.json").read_text(encoding="utf-8"))
            if time.monotonic() >= deadline or (state["state"] not in ("starting", "running") and cursor >= state["latest_seq"]):
                print(json.dumps({"type": "watch_end", "next_cursor": cursor,
                                  "collector_state": state["state"], "updated_utc": state["updated_utc"]}), flush=True)
                break
            time.sleep(.1)
    elif args.action in ("status", "stop", "mark"):
        state = json.loads((args.session / "status.json").read_text(encoding="utf-8"))
        state["observer_status_age_seconds"] = round((datetime.now().astimezone() -
            datetime.fromisoformat(state["updated_utc"])).total_seconds(), 3)
        state["collector_heartbeat_stale"] = state["state"] in ("starting", "running") and state["observer_status_age_seconds"] > 5
        if args.action == "status":
            print(json.dumps(state, indent=2))
        else:
            if state["state"] not in ("starting", "running"):
                raise ValueError("Collector is not in a running state")
            request = {"session_id": state["session_id"], "timestamp_utc": utc_now()}
            if args.action == "mark":
                if len(args.text) > 4096:
                    raise ValueError("Marker exceeds 4096 characters")
                request["text"] = args.text
            name = "stop.request" if args.action == "stop" else f"marker-{uuid.uuid4()}.request"
            temporary = args.session / (name + ".tmp")
            temporary.write_text(json.dumps(request), encoding="utf-8")
            temporary.replace(args.session / name)
            print(json.dumps({"request": args.action, "session_id": state["session_id"]}))
    else:
        game = admit(args.game)
        if not 20 <= args.poll_ms <= 5000 or (args.duration is not None and args.duration <= 0):
            raise ValueError("Poll must be 20..5000 ms; duration must be positive")
        directory = args.session or ROOT / "reports/mw3-monitor" / (
            datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8])
        directory = directory.resolve()
        report_root = (ROOT / "reports").resolve()
        if not directory.is_relative_to(report_root) or directory == report_root:
            raise ValueError("Live sessions must stay beneath the ignored reports directory")
        return run_session(Config(game=game, directory=directory,
            mode="attach" if args.action == "attach" else args.mode,
            pid=getattr(args, "pid", None), debug=(not args.no_debug if args.action == "launch" else args.debug),
            period=args.poll_ms / 1000, duration=args.duration, hook_run=args.hook_run,
            logs=args.log))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, RuntimeError) as failure:
        print(json.dumps({"error": str(failure)}), file=sys.stderr)
        raise SystemExit(1)
