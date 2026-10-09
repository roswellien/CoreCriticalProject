#!/usr/bin/env python3
"""Revalidate G2 artifacts and full-state results without executing the game/worker."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile

from compare_mw3_leaf import (ADMISSION_CHECKS, COMPARATOR_CHECKS, CONTRACT, ENTRY,
                             LIVE_SNAPSHOT, REQUEST_CHECKS, REVIEWED, ROOT,
                             comparator_controls, corpus, coverage, decode_corpus,
                             digest, encode_corpus, extract, live_input, parse_results,
                             private_directory, require, source_hashes, validate_build,
                             source_digest, validate_generated_layout, validate_records)

REQUIRED_ARTIFACTS = {"sub_00409ed0.bin", "slice.json", "sub_00409ed0-guest.ll",
                      "sub_00409ed0-guest.bc", "sub_00409ed0-host.ll",
                      "sub_00409ed0-host-O2.ll", "sub_00409ed0-O0.obj",
                      "sub_00409ed0-O2.obj", "layout.json"}


def validate_controls(report: dict) -> int:
    admission = report.get("admission_negative_controls", [])
    comparator = report.get("comparator_negative_controls", [])
    workers = report.get("worker_negative_controls", [])
    require([entry.get("name") for entry in admission] == list(ADMISSION_CHECKS) and
            all(entry.get("outcome") == "rejected" and entry.get("reason") for entry in admission),
            "Missing image/contract admission rejection controls")
    require([entry.get("name") for entry in comparator] == list(COMPARATOR_CHECKS) and
            all(entry.get("outcome") == "rejected" and entry.get("difference") for entry in comparator),
            "Missing full-state comparator corruption controls")
    required = {(role, name) for role in ("reference", "O0", "O2") for name in REQUEST_CHECKS}
    observed = [(entry.get("role"), entry.get("name")) for entry in workers]
    require(len(observed) == len(required) and set(observed) == required and
            all(entry.get("outcome") == "rejected" and entry.get("reason") for entry in workers),
            "Missing worker protocol/slice rejection controls")
    return len(admission) + len(comparator) + len(workers)


def verify(report_dir: Path, game: Path = ROOT / "MW3/Mech3.exe") -> dict:
    report_dir = private_directory(report_dir)
    report_file = report_dir / "report.json"
    report = json.loads(report_file.read_bytes())
    require(report.get("schema_version") == 1 and report.get("gate") == "G2" and
            report.get("outcome") == "mw3_leaf_lift_passed" and
            report.get("function") == "sub_00409ED0", "G2 leaf comparison did not pass")
    require(report.get("seed") == 0x3434 and report.get("random_cases", 0) >= 10000 and
            report.get("recorded_input_cases") == 1, "Required seeded/recorded input corpus missing")
    current_sources = source_hashes()
    require(report.get("source_hashes") == current_sources,
            "Reviewed source identities changed or are missing")
    require(report.get("source_digest") == source_digest(ROOT), "Common source graph changed")
    # Re-run the entire admission check against the current private PE. This
    # reads/extracts bytes, not any DLL loading or instruction execution.
    with tempfile.TemporaryDirectory(prefix="verify-admission-", dir=report_dir) as temporary:
        admitted = extract(game, CONTRACT, Path(temporary))
    require(all(report.get("admission", {}).get(name) == value for name, value in REVIEWED.items()),
            "Recorded admission differs from reviewed identity")
    require(report["admission"].get("contract_sha256") == admitted["contract_sha256"] and
            report["admission"].get("tool_sha256") == admitted["tool_sha256"] and
            report.get("slice_sha256") == REVIEWED["slice_sha256"], "Admission tool/contract/slice changed")
    admitted_slice = report_dir / "admitted/sub_00409ed0.bin"
    require(digest(admitted_slice.read_bytes()) == REVIEWED["slice_sha256"],
            "Executed admitted slice artifact differs")
    replay, current_input = live_input(Path(report["recorded_input"]["snapshot"]))
    require(all(report["recorded_input"].get(name) == value for name, value in current_input.items()),
            "Recorded Training input evidence changed")
    wanted_cases = corpus(report["seed"], report["random_cases"], replay)
    encoded = (report_dir / "corpus.bin").read_bytes()
    cases = decode_corpus(encoded)
    require(encoded == encode_corpus(wanted_cases) and
            digest(encoded) == report.get("corpus_sha256"), "Corpus is not the reviewed seeded corpus")
    directed_count = len(cases) - report["random_cases"] - 1
    require(report.get("total_cases") == len(cases) and report.get("directed_cases") == directed_count and
            report["recorded_input"].get("corpus_case_index") == len(cases) - 1 and
            report.get("coverage") == coverage(cases, directed_count), "Corpus count/coverage/replay index differs")
    metadata_path = Path(report["metadata_path"])
    metadata_bytes = metadata_path.read_bytes()
    build = json.loads(metadata_bytes)
    require(digest(metadata_bytes) == report.get("metadata_sha256") and
            report.get("build_provenance") == build, "Build provenance changed")
    require(build.get("fixture_kind") == "mw3_helper" and build.get("entry_va") == ENTRY and
            build.get("game_sha256") == REVIEWED["image_sha256"] and
            build.get("target_triples") == ["i686-pc-windows-msvc", "x86_64-pc-windows-msvc"] and
            build.get("optimization_levels") == ["llc -O0", "opt default<O2>; llc -O2"],
            "Missing reviewed native target/optimization/identity provenance")
    artifacts = build.get("artifacts", {})
    require(isinstance(artifacts, dict) and REQUIRED_ARTIFACTS <= set(artifacts),
            "Generated IR/object/layout artifact identities missing")
    for name, checksum in artifacts.items():
        require(type(name) is str and Path(name).name == name and name not in (".", ".."),
                "Unsafe generated artifact name")
        artifact = metadata_path.parent / name
        require(artifact.stat().st_size > 0 and digest(artifact.read_bytes()) == checksum,
                f"Generated artifact changed: {name}")
    require(artifacts["sub_00409ed0.bin"] == REVIEWED["slice_sha256"],
            "Lifted slice differs from executed original slice")
    layout = validate_generated_layout(build, metadata_path.parent)
    require(report.get("adapter_profile") == layout["profile"] and
            report.get("undefined_flag_policy") == layout["undefined_flag_policy"],
            "Recorded adapter profile/undefined-flag proof differs")
    reference = report.get("reference_run", {})
    natives = report.get("lifted_runs", [])
    require(len(natives) == 2 and [run.get("optimization") for run in natives] == ["O0", "O2"],
            "Required O0/O2 native run records missing")
    workers = [reference, *natives]
    for index, run in enumerate(workers):
        role = ("reference", "O0", "O2")[index]
        command = run.get("command", [])
        expected_output = report_dir / ("reference.bin" if index == 0 else f"lifted-{index - 1}.bin")
        require(isinstance(command, list) and len(command) == 4 and run.get("exit_code") == 0,
                f"{role}: missing successful worker command")
        require(Path(command[1]).resolve() == (report_dir / "corpus.bin").resolve() and
                Path(command[2]).resolve() == expected_output.resolve() and
                Path(command[3]).resolve() == admitted_slice.resolve(),
                f"{role}: recorded input/output/slice paths differ")
        require(digest(Path(command[0]).read_bytes()) == run.get("worker_sha256") and
                digest(expected_output.read_bytes()) == run.get("output_sha256"),
                f"{role}: worker/result artifact identity changed")
        if index:
            require(run.get("differential_result") == "zero mismatches",
                    f"{role}: missing differential pass")
    validate_build(build, Path(reference["command"][0]), [Path(run["command"][0]) for run in natives])
    original = parse_results((report_dir / "reference.bin").read_bytes(), len(cases), 32)
    validate_records(original, cases, "reference_offline_revalidation")
    require(report.get("comparator_negative_controls") == comparator_controls(original[0]),
            "Comparator control evidence differs from current measurements")
    for index, level in enumerate(("O0", "O2")):
        native = parse_results((report_dir / f"lifted-{index}.bin").read_bytes(), len(cases), 64)
        validate_records(native, cases, level + "_offline_revalidation")
        require(native == original, f"{level}: recorded full-state differential mismatch")
    checks = validate_controls(report)
    return {"schema_version": 1, "gate": "G2", "outcome": "passed",
            "function": "sub_00409ED0", "entry_va": hex(ENTRY),
            "scope": "one admitted original x86 leaf compiled to native x64 through Remill",
            "not_proven": "whole-game native recompilation or extended gameplay stability",
            "image_sha256": REVIEWED["image_sha256"], "slice_sha256": REVIEWED["slice_sha256"],
            "comparison_report_sha256": digest(report_file.read_bytes()),
            "metadata_sha256": digest(metadata_bytes), "corpus_sha256": digest(encoded),
            "valid_cases": len(cases), "native_case_comparisons": len(cases) * 2,
            "optimization_levels": ["O0", "O2"], "mismatches": 0,
            "compared_memory_bytes_per_case": 4096, "rejection_controls": checks,
            "recorded_game_input_pairs": 1,
            "recorded_input_scope": "n and ECX base only; remaining entry state authored",
            "undefined_flag_policy": layout["undefined_flag_policy"],
            "sources": current_sources}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", type=Path, default=ROOT / "reports/mw3-leaf-differential")
    parser.add_argument("--game", type=Path, default=ROOT / "MW3/Mech3.exe")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        summary = verify(args.report_dir, args.game)
        if args.output:
            output = private_directory(args.output.parent) / args.output.name
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2))
        return 0
    except (KeyError, TypeError, ValueError, OSError) as error:
        print(f"G2 verification failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
