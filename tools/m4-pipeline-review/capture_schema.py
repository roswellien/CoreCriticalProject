"""Read-only inventory of representative frozen native captures.

This is a transport/schema inventory, not a new execution or semantic acceptance.
All expected bytes come from physically read old artifacts; later roundtrips must
retain this complete logical mapping and every existing observer contract.
"""
import hashlib
import json
import ntpath
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main(output):
    output = Path(output).resolve()
    assert output.parent == ROOT / "reports/m4-pipeline-review"
    output.mkdir(parents=True, exist_ok=False)
    capture = ROOT / "reports/m4-crt-mainargs/root-execution-r1"
    manifest_path = capture / "pins.json"
    frozen = {}
    for name, sha in json.loads(manifest_path.read_text())["files"].items():
        key = ntpath.normcase(ntpath.normpath(name))
        assert key not in frozen or frozen[key] == sha, name
        frozen[key] = sha
    sources = {}
    summary = []
    rows = ("native-O0/row-0", "native-O2/row-0", "native-O0/row-26", "native-O2/row-83")
    for relative in rows:
        row = capture / relative
        files = {}
        for path in sorted(row.rglob("*")):
            assert not path.is_symlink(), str(path)
            if not path.is_file():
                continue
            data = path.read_bytes()
            sha = digest(data)
            key = ntpath.normcase(ntpath.normpath(str(path)))
            assert frozen[key] == sha, str(path)
            files[path.relative_to(row).as_posix()] = {"bytes": len(data), "sha256": sha}
            sources[str(path)] = sha
        result = json.loads((row / "result.json").read_text())
        checkpoints = {}
        for phase in sorted(row.iterdir()):
            if phase.is_dir():
                prefix = phase.name + "/"
                checkpoints[phase.name] = sum(name.startswith(prefix) for name in files)
        summary.append({"row": str(row), "control": result["control"],
                        "writer_complete": result["writer_complete"],
                        "files": files, "file_count": len(files),
                        "payload_bytes": sum(v["bytes"] for v in files.values()),
                        "checkpoint_file_counts": checkpoints})
    for path in (Path(__file__), manifest_path, capture / "execution.json"):
        sources[str(path)] = digest(path.read_bytes())
    report = {"passed": True, "scope": "Frozen-capture transport inventory only",
              "representative_rows": summary, "frozen_dependency_bindings": len(frozen),
              "native_candidate_rerun": False, "frozen_outputs_changed": False,
              "semantic_observer_rules_changed": False, "files": sources}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": True, "rows": len(summary),
                      "files": sum(v["file_count"] for v in summary),
                      "frozen_bindings": len(frozen)}))


if __name__ == "__main__":
    main(sys.argv[1])
