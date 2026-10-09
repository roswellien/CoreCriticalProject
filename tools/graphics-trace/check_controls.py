"""Causal rejection checks against a real bounded graphics-trace receipt."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from verify import verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    accepted = verify(args.run, "draws")
    rows = [json.loads(line) for line in (args.run / "game.jsonl").read_text().splitlines()]
    rejected = []
    with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2] / "local") as temporary:
        directory = Path(temporary)
        for filename in ("game.jsonl", "selftest.jsonl", "build.json", "modules.json"):
            shutil.copyfile(args.run / filename, directory / filename)
        for control in ("fixtures_only", "missing_record", "failed_draws", "wrong_stride", "wrong_transformed", "short_sample", "no_device", "failed_guard", "wrong_provider"):
            mutated = copy.deepcopy(rows)
            if control == "fixtures_only":
                for row in mutated:
                    row["live"] = False
            elif control == "missing_record":
                del mutated[-1]
                del mutated[5]
            elif control == "wrong_provider":
                next(r for r in mutated if r["event"] == "provider")["sha256"] = "0" * 64
            elif control == "failed_guard":
                next(r for r in mutated if r["event"] == "selftest")["fp_vector_guard_verified"] = False
            elif control == "no_device":
                for row in mutated:
                    if row["live"] and row["event"] == "create_device":
                        row["output"] = 0
            else:
                for row in mutated:
                    if not row["live"] or row["event"] not in ("draw_primitive", "draw_indexed_primitive"):
                        continue
                    if control == "failed_draws":
                        row["hresult"] = -1
                    elif control == "wrong_stride":
                        row["vertex_stride"] += 4
                    elif control == "wrong_transformed":
                        row["transformed"] = not row["transformed"]
                    elif control == "short_sample":
                        row["sample_hex"] = row["sample_hex"][:-2]
            (directory / "game.jsonl").write_text("".join(json.dumps(row) + "\n" for row in mutated), encoding="utf-8")
            try:
                verify(directory, "draws")
            except ValueError:
                rejected.append(control)
            else:
                raise AssertionError(f"Control accepted: {control}")
    report = {"positive_receipt": accepted["trace_sha256"], "rejected_controls": rejected,
              "verifier_sha256": hashlib.sha256((Path(__file__).parent / "verify.py").read_bytes()).hexdigest(),
              "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
