"""Asset-free checks of an explicitly supplied compiled M3 worker.

This entry point requires a worker; absent binaries are errors, never skipped
or credited as a private-function test. It does not execute admitted game code.
"""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile


def check(worker: Path, native: bool) -> dict:
    if not worker.is_file():
        raise ValueError("Explicit compiled worker is missing")
    run = subprocess.run([str(worker), "--check-protocol"], capture_output=True, text=True)
    if run.returncode or run.stdout.strip() != "Protocol controls: 28":
        raise ValueError("Compiled whole-corpus protocol admission checks failed: " + run.stdout + run.stderr)
    checks = 28
    if native:
        run = subprocess.run([str(worker), "--layout"], capture_output=True, text=True)
        if run.returncode:
            raise ValueError("Compiled native layout failed")
        layout = json.loads(run.stdout)
        for name, value in {"state_size": 3504, "request_size": 568, "result_size": 24564,
                            "vec_size": 2048, "vec_stride": 64, "mmx_size": 128,
                            "st_offset": 2486, "st_stride": 16, "x87_offset": 2768,
                            "x87_size": 512, "eip_offset": 2472}.items():
            if layout[name] != value:
                raise ValueError("Unexpected compiled layout: " + name)
            checks += 1
        if layout["gpr_offsets"] != [2216, 2248, 2264, 2232, 2312, 2328, 2280, 2296]:
            raise ValueError("Unexpected compiled GPR ordering")
        checks += 1
    # The CLI must not publish output when image/code admission is absent.
    temporary_root = Path(__file__).resolve().parents[2] / "build"
    temporary_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mw34-m3-public-", dir=temporary_root) as folder:
        output = Path(folder) / "unadmitted.bin"
        run = subprocess.run([str(worker), str(Path(folder)/"missing-input"), str(output),
                              str(Path(folder)/"missing-code"), str(Path(folder)/"missing-image")],
                             capture_output=True, text=True)
        if run.returncode != 1 or output.exists():
            raise ValueError("Unadmitted worker request published output")
        checks += 1
    return {"worker": str(worker.resolve()), "asset_free_checks": checks,
            "game_entry_executions": 0, "passed": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", required=True, type=Path)
    parser.add_argument("--native", action="store_true")
    args = parser.parse_args()
    print(json.dumps(check(args.worker, args.native), sort_keys=True))


if __name__ == "__main__":
    main()
