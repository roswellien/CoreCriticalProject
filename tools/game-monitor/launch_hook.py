"""Double-click entry point: build/self-test the hook and start live monitoring."""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

from monitor import ROOT, admit, sha


def prepare(game, vs_root):
    game = admit(game)
    source = ROOT / "tools/in-game-hook"
    build = ROOT / "build/in-game-hook"
    cmake = vs_root / "Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe"
    for arguments in (["-S", str(source), "-B", str(build), "-G", "Visual Studio 18 2026", "-A", "Win32"],
                      ["--build", str(build), "--config", "Release"]):
        subprocess.run([str(cmake), *arguments], cwd=ROOT, check=True)
    run = ROOT / "reports/mw3-in-game" / (
        datetime.now().strftime("%Y%m%d-%H%M%S-%f") + "-" + uuid.uuid4().hex[:8])
    run.mkdir(parents=True, exist_ok=False)
    launcher = build / "Release/mw34_hook_launcher.exe"
    dll = build / "Release/mw34_helper_hook.dll"
    subprocess.run([str(launcher), "--selftest", str(game), str(dll), str(run / "selftest.jsonl")],
                   cwd=ROOT, check=True)
    record = {"schema_version": 1, "game_sha256": sha(game), "hook_sha256": sha(dll),
              "launcher_sha256": sha(launcher),
              "scope": "one authored x86 replacement in the original x86 game; native x64 G2 remains separate",
              "source_hashes": {path.name: sha(path) for path in sorted(source.iterdir()) if path.is_file()},
              "launch_sources": {"launch_hook.py": sha(Path(__file__)),
                                 "Launch MW3 with Hook.cmd": sha(ROOT / "Launch MW3 with Hook.cmd")}}
    (run / "build.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(f"Hook self-tests passed. Research run: {run}", flush=True)
    return run


def ensure_closed(game):
    from win32 import pids_for_image
    pids = pids_for_image(game)
    if pids:
        raise RuntimeError(f"MW3 is already running (PID {pids}). Close it before using the hook launcher.")


def wait_ready(child, session, timeout=45):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        path = session / "status.json"
        state = None
        if path.exists():
            state = json.loads(path.read_text(encoding="utf-8"))
            if state["state"] == "running" and child.poll() is None:
                return state
            if state["state"] in ("collector_error", "exited", "detached"):
                raise RuntimeError(f"Startup ended with {state['state']}: {state.get('error')}. Logs: {session}")
        if child.poll() is not None:
            raise RuntimeError(f"Collector exited with code {child.returncode}. Logs: {session}")
        time.sleep(.1)
    # A timeout is not proof of exit, and does not trigger another launch.
    return {"state": "starting", "collector_pid": child.pid, "session": str(session)}


def collector_command(game, run, session, debug=False):
    command = [sys.executable, str(ROOT / "tools/game-monitor/monitor.py"), "launch", "--mode", "hook",
               "--game", str(game), "--hook-run", str(run), "--session", str(session)]
    # Debug attachment changes legacy CloseHandle behavior. The first attached
    # real-game run exited at the menu with STATUS_INVALID_HANDLE; passive did not.
    if not debug:
        command.append("--no-debug")
    return command


def start(game, run, debug=False):
    ensure_closed(game)
    tag = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8]
    session = ROOT / "reports/mw3-monitor" / tag
    output = ROOT / "reports/mw3-monitor-launchers"
    output.mkdir(parents=True, exist_ok=True)
    stdout, stderr = output / (tag + ".stdout.log"), output / (tag + ".stderr.log")
    command = collector_command(game, run, session, debug)
    with stdout.open("xb") as out, stderr.open("xb") as err:
        child = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                 creationflags=subprocess.CREATE_NO_WINDOW)
    # This manifest lets the assistant find the exact run, not a guessed PID.
    record = {"collector_pid": child.pid, "session": str(session), "hook_run": str(run),
              "stdout": str(stdout), "stderr": str(stderr), "command": command}
    (output / (tag + ".launch.json")).write_text(json.dumps(record, indent=2), encoding="utf-8")
    try:
        state = wait_ready(child, session)
    except RuntimeError:
        if stderr.exists():
            print(stderr.read_text(encoding="utf-8", errors="replace")[-4096:], file=sys.stderr)
        raise
    print(f"Monitor session: {session}", flush=True)
    if state["state"] == "running":
        mode = "debugger" if debug else "passive"
        print(f"Hook and {mode} monitoring active. Game PID: {state['target_pid']}. Enter Training in this session.", flush=True)
    else:
        print(f"Collector still starting (PID {child.pid}); inspect the session and launcher logs before retrying.", flush=True)
    # Collector lifetime is intentionally independent of this console wrapper.
    import threading
    threading.Thread(target=child.wait, daemon=True).start()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare-only", action="store_true", help="build/self-test without launching MW3")
    parser.add_argument("--debug", action="store_true", help="opt in to debugger capture; may change legacy game behavior")
    parser.add_argument("--game", type=Path, default=ROOT / "MW3/Mech3.exe")
    parser.add_argument("--vs-root", type=Path, default=Path("C:/Program Files/Microsoft Visual Studio/18/Community"))
    args = parser.parse_args()
    if os.name != "nt":
        raise RuntimeError("This launcher requires Windows")
    game = admit(args.game)
    if not args.prepare_only:
        ensure_closed(game)
    run = prepare(game, args.vs_root)
    if args.prepare_only:
        print("Preparation complete. MW3 was not launched.")
    else:
        start(game, run, debug=args.debug)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as failure:
        print(f"Launch failed: {failure}", file=sys.stderr)
        raise SystemExit(1)
