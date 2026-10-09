"""Explicit compiled-worker controls; missing workers are errors, no assets used."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", required=True, type=Path)
    parser.add_argument("--native", action="store_true")
    args = parser.parse_args()
    if not args.worker.is_file():
        raise ValueError("Explicit compiled worker is missing")
    worker = str(args.worker.resolve())
    proc = subprocess.run([worker, "--check-protocol"], capture_output=True, text=True)
    if proc.returncode or proc.stdout.strip() != "Sequence protocol controls: 18":
        raise ValueError("Whole-sequence compiled admission failed: " + proc.stdout + proc.stderr)
    checks = 18
    if args.native:
        proc = subprocess.run([worker, "--layout"], capture_output=True, text=True)
        if proc.returncode:
            raise ValueError("Compiled actual State layout failed")
        layout = json.loads(proc.stdout)
        for key, value in {"state_size": 3504, "request_size": 1296, "result_size": 73728,
                           "vec_offset": 16, "vec_size": 2048, "mmx_offset": 2608,
                           "st_offset": 2486, "st_stride": 16, "x87_offset": 2768,
                           "trace_event_size": 16, "trace_capacity": 2048}.items():
            if layout[key] != value:
                raise ValueError("Unexpected compiled " + key)
            checks += 1
    temporary_root = Path(__file__).resolve().parents[2] / "build"
    temporary_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mw34-s3-public-", dir=temporary_root) as directory:
        directory = Path(directory)
        output = directory / "unadmitted.bin"
        proc = subprocess.run([worker, str(directory/"missing-input"), str(output),
                               str(directory/"missing-setter"), str(directory/"missing-consumer"),
                               str(directory/"missing-image")], capture_output=True, text=True)
        if proc.returncode != 1 or output.exists():
            raise ValueError("Unadmitted sequence published output")
        checks += 1
    print(json.dumps({"worker": worker, "asset_free_checks": checks,
                      "game_entry_executions": 0, "passed": True}, sort_keys=True))


if __name__ == "__main__":
    main()
