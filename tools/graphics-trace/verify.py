"""Verify identities and bounded live graphics observations; never count fixtures."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GAME_SHA = "95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def records(path):
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line]
    if not rows or any(row["seq"] != i + 1 for i, row in enumerate(rows)):
        raise ValueError("Missing or reordered trace records")
    if len({row["pid"] for row in rows}) != 1:
        raise ValueError("Mixed process identity")
    return rows


def verify(run, stage, monitor=None):
    build = json.loads((run / "build.json").read_text(encoding="utf-8-sig"))
    if build["game_sha256"] != GAME_SHA or sha(ROOT / "MW3/Mech3.exe") != GAME_SHA:
        raise ValueError("Game identity mismatch")
    for filename, key in (("mw34_graphics_trace.dll", "dll_sha256"), ("mw34_graphics_launcher.exe", "launcher_sha256")):
        binary = run / "binaries" / filename
        if not binary.exists():
            binary = ROOT / "build/graphics-trace/Release" / filename
        if sha(binary) != build[key]:
            raise ValueError("Tool binary identity mismatch")
    for filename, expected in build["sources"].items():
        source = ROOT / "tools/in-game-hook" / filename[7:] if filename.startswith("shared/") else ROOT / "tools/graphics-trace" / filename
        snapshot = run / "sources" / filename
        if snapshot.exists():
            source = snapshot
        if sha(source) != expected:
            raise ValueError(f"Source identity mismatch: {filename}")
    for path in (run / "selftest.jsonl", run / "game.jsonl"):
        rows = records(path)
        tests = [row for row in rows if row["event"] == "selftest"]
        if len(tests) != 1 or tests[0]["live"] or not all(tests[0].get(key) is True for key in (
            "passed", "last_error_preserved", "failed_qi_preserved", "failed_draw_preserved", "fp_vector_guard_verified")):
            raise ValueError("Missing or failed authored selftests")
    live = [row for row in rows if row["live"]]
    installed = [row for row in live if row["event"] == "installed"]
    if len(installed) != 1 or installed[0]["iat_va"] != 0x5BB044 or installed[0]["on_disk_game_unchanged"] is not True:
        raise ValueError("Missing admitted installation")
    if any(row["event"] in ("fatal", "coverage_limit") for row in rows):
        raise ValueError("Trace has a failure/coverage limit")
    if any(row["event"] == "object" and row["installed"] is not True for row in live):
        raise ValueError("Object instrumentation was not installed")
    modules = json.loads((run / "modules.json").read_text(encoding="utf-8-sig"))
    providers = [row for row in rows if row["event"] == "provider"]
    if len(providers) != 1:
        raise ValueError("Missing provider identity")
    provider = providers[0]
    matches = [m for m in modules if m["base"] == provider["base"] and m["file_sha256"] == provider["sha256"]]
    if len(matches) != 1 or sha(Path(matches[0]["path"])) != provider["sha256"]:
        raise ValueError("Loaded provider inventory mismatch")
    counts = Counter(row["event"] for row in live)
    successful = [row for row in live if row["event"] == "create_device" and row["hresult"] >= 0 and row["output"]]
    if not successful:
        raise ValueError("No successful live device creation")
    expected_iids = {"9c59509a-39bd-11d1-8c4a-00c04fd930c5", "bb223240-e72b-11d0-a9b4-00aa00c0993e"}
    observed_iids = {row["iid"] for row in live if row["event"] == "query_interface" and row["hresult"] >= 0}
    if not expected_iids <= observed_iids:
        raise ValueError("Live DirectDraw4/Direct3D3 chain missing")
    draw_rows = [row for row in live if row["event"] in ("draw_primitive", "draw_indexed_primitive")]
    for row in draw_rows:
        fvf = row["fvf"]
        position = fvf & 0xE
        tex_count = (fvf >> 8) & 0xF
        known = position in (2, 4) and tex_count <= 8 and not (fvf & ~0xFDE)
        expected_stride = ((16 if position == 4 else 12) + (12 if fvf & 0x10 else 0)
                           + (4 if fvf & 0x40 else 0) + (4 if fvf & 0x80 else 0) + 8 * tex_count) if known else 0
        if row["vertex_stride"] != expected_stride or row["transformed"] != (position == 4):
            raise ValueError("FVF/stride interpretation mismatch")
        data = bytes.fromhex(row["sample_hex"])
        if len(data) != row["sample_bytes"] or len(data) > min(256, expected_stride * min(3, row["vertex_count"])):
            raise ValueError("Invalid bounded vertex sample")
    if stage == "draws" and not any(row["hresult"] >= 0 and row["vertex_count"] > 0 and row["sample_bytes"] > 0 for row in draw_rows):
        raise ValueError("No successful sampled live draw; fixtures cannot satisfy this gate")
    report = {"scope": "bounded original-game graphics observations; no replayable frame or native renderer",
            "stage": stage, "pid": rows[0]["pid"], "provider_sha256": provider["sha256"],
            "live_events": dict(counts), "sampled_fvf": sorted({row["fvf"] for row in draw_rows}),
            "vertex_strides": sorted({row["vertex_stride"] for row in draw_rows}),
            "transformed_draws": sum(row["transformed"] for row in draw_rows),
            "trace_sha256": sha(run / "game.jsonl"), "training_playability": "requires separate user observation"}
    if monitor:
        status = json.loads((monitor / "status.json").read_text(encoding="utf-8-sig"))
        observed = []
        for path in sorted(monitor.glob("events-*.jsonl")):
            observed.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line)
        exits = [row for row in observed if row["source"] == "process" and row["event"] == "exit"]
        if (status["target_pid"] != rows[0]["pid"] or status["state"] != "exited" or status["error"]
                or status["dropped_segments"] or status["recent_alerts"] or len(exits) != 1
                or exits[0]["data"]["pid"] != rows[0]["pid"] or exits[0]["data"]["exit_code"] != 0
                or any(row["severity"] in ("warning", "error", "critical") for row in observed)):
            raise ValueError("Monitor does not establish a clean observed exit")
        report["monitor"] = {"exit_code": 0, "alerts": 0, "dropped_segments": 0,
                             "session_id": status["session_id"], "status_sha256": sha(monitor / "status.json"),
                             "scope": "passive process/window health from attachment; no visual, timing or debugger exception coverage"}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--stage", choices=("creation", "draws"), default="draws")
    parser.add_argument("--monitor", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.run, args.stage, args.monitor), indent=2))


if __name__ == "__main__":
    main()
