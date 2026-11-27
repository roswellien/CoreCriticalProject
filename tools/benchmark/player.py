"""Run the four-scene arena benchmark for a player from the launcher's settings page.

The reference replay logs come from the player's own MechWarrior 3 install, so they
cannot ship with the launcher. The first run generates each scene's log twice in hidden
arena processes, requires the two to be byte identical, and freezes the log's SHA-256
under a key made from the game executable, the install's archives and the recipe. Later
runs reuse a frozen log only while its bytes still match. Results are compared only with
the player's own earlier runs that used the same frozen logs and graphics settings.

The launcher reads progress from stdout lines that start with EVENT_PREFIX followed by
one JSON object. Every other line is diagnostic text from the planner or the game.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVENT_PREFIX = "BENCHMARK-EVENT "
SEED = 7
# Each suite scene and the arena recipe whose hidden recording it replays.
SCENE_RECIPES = {
    "c1mp1": "c1mp1-4v4-reference.json",
    "c2mp2": "c2mp2-4v4-reference.json",
    "c3mp1": "c3mp1-4v4-reference.json",
    "c4mp2": "c4mp2-8v8-stress.json",
}
# Both options must be in the game executable; releases before the benchmark lack them.
REQUIRED_EXECUTABLE_OPTIONS = (b"--arena-record-every-update", b"--benchmark-scene")
# The figures the launcher shows for each scene and overall.
STATISTIC_KEYS = ("average_fps", "low_1_percent_fps", "p95_ms", "p99_ms")


def emit(event, **fields):
    print(EVENT_PREFIX + json.dumps({"event": event, **fields}), flush=True)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def executable_supports_benchmark(executable):
    contents = executable.read_bytes()
    return all(option in contents for option in REQUIRED_EXECUTABLE_OPTIONS)


def reference_key(executable_sha, game_archives_sha, recipes_sha):
    """Logs depend on the build, the install's data and the recipes, so all three key them."""
    combined = f"{executable_sha}:{game_archives_sha}:{recipes_sha}:{SEED}".encode("ascii")
    return sha256_bytes(combined)[:24]


def game_archives_digest(game, sha256):
    archives = {
        archive.name.casefold(): sha256(archive)
        for archive in sorted((game / "zbd").iterdir())
        if archive.suffix.casefold() == ".zbd" and archive.is_file()
    }
    manifest = json.dumps(archives, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(manifest)


def frozen_log(scene_root, sha256):
    """Return the scene's frozen log and hash, or None when it needs generating."""
    receipt_path = scene_root / "freeze.json"
    log_path = scene_root / f"match-{SEED}.jsonl"
    if not receipt_path.is_file() or not log_path.is_file():
        return None
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if sha256(log_path) != receipt.get("sha256"):
        raise ValueError(
            f"The saved {scene_root.name} replay changed since it was first generated. "
            f"Delete {scene_root} to generate it again."
        )
    return log_path, receipt


def prepare_references(references, definition, fixtures, executable, game, freeze, sha256):
    """Generate missing logs and write a definition that points at the frozen copies."""
    references.mkdir(parents=True, exist_ok=True)
    materialized = json.loads(json.dumps(definition))
    notes = []
    for scene in materialized["scenes"]:
        scene_id = scene["id"]
        scene_root = references / scene_id
        found = frozen_log(scene_root, sha256)
        if found is None:
            emit("progress", stage="generate", scene=scene_id)
            # freeze() refuses an existing output, so a stopped attempt leaves only a
            # partial folder that the next run replaces.
            partial = references / f"{scene_id}.partial-{time.time_ns()}"
            freeze(executable, game, fixtures / SCENE_RECIPES[scene_id], SEED, partial, references)
            # An incomplete earlier folder (for example a deleted log) would block the rename.
            if scene_root.exists():
                shutil.rmtree(scene_root)
            partial.replace(scene_root)
            found = frozen_log(scene_root, sha256)
        log_path, receipt = found
        # The shipped hash belongs to the build that qualified the suite. Another build
        # can record a different but equally repeatable log, so a mismatch only warns.
        if receipt["sha256"] != scene["log_sha256"]:
            notes.append(scene_id)
        scene["log"] = log_path.relative_to(references).as_posix()
        scene["log_sha256"] = receipt["sha256"]
    path = references / "suite-benchmark.json"
    path.write_text(json.dumps(materialized, indent=2) + "\n", encoding="utf-8")
    return path, notes


def pooled_statistics(intervals_ms, measured_presents, measured_seconds):
    """Mirror the native per-scene formulas over every scene's measured frames."""
    if len(intervals_ms) < 2 or measured_seconds <= 0:
        raise ValueError("The benchmark has too few measured frames")
    ordered = sorted(intervals_ms)

    def rank(percent):
        return ordered[(len(ordered) * percent + 99) // 100 - 1]

    tail = (len(ordered) + 99) // 100
    slowest = sum(ordered[-tail:])
    return {
        "mean_ms": sum(ordered) / len(ordered),
        "p50_ms": rank(50),
        "p95_ms": rank(95),
        "p99_ms": rank(99),
        "average_fps": measured_presents / measured_seconds,
        "low_1_percent_fps": 1000 * tail / slowest if slowest > 0 else 0,
    }


def read_intervals(frames_csv):
    intervals = []
    with frames_csv.open(encoding="utf-8") as stream:
        header = stream.readline().strip().split(",")
        column = header.index("interval_ms")
        for line in stream:
            fields = line.rstrip("\n").split(",")
            if len(fields) <= column:
                raise ValueError(f"Malformed benchmark frame row in {frames_csv}")
            value = fields[column]
            if value:
                intervals.append(float(value))
    return intervals


def build_report(suite_root, definition, settings, key, notes):
    measured_seconds = {scene["id"]: scene["measured_seconds"] for scene in definition["scenes"]}
    scenes = []
    intervals = []
    presents = 0
    for scene_id in measured_seconds:
        summary = json.loads((suite_root / scene_id / "summary.json").read_text(encoding="utf-8"))
        statistics = summary["statistics"]
        scenes.append({"id": scene_id, **{k: statistics[k] for k in STATISTIC_KEYS}})
        intervals.extend(read_intervals(suite_root / scene_id / "frames.csv"))
        presents += summary["measured_presents"]
    overall = pooled_statistics(intervals, presents, sum(measured_seconds.values()))
    first = json.loads((suite_root / scenes[0]["id"] / "summary.json").read_text(encoding="utf-8"))
    return {
        "version": 1,
        "finished": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "reference_key": key,
        "settings_sha256": sha256_bytes(json.dumps(settings, sort_keys=True).encode("utf-8")),
        "settings": settings,
        "gpu": first.get("gpu"),
        "scenes": scenes,
        "overall": {k: overall[k] for k in STATISTIC_KEYS},
        "reference_mismatch_scenes": notes,
    }


def previous_report(results, report):
    """The newest earlier report with the same frozen logs and settings, if any."""
    for directory in sorted(results.iterdir(), reverse=True):
        path = directory / "report.json"
        if not path.is_file():
            continue
        # A damaged earlier report must not discard the run that just finished.
        try:
            earlier = json.loads(path.read_text(encoding="utf-8"))
            matches = (
                earlier.get("reference_key") == report["reference_key"]
                and earlier.get("settings_sha256") == report["settings_sha256"]
            )
            if matches:
                return {"finished": earlier["finished"], "overall": earlier["overall"]}
        except (OSError, ValueError, KeyError, AttributeError):
            continue
    return None


def failure_reason(suite_root):
    """The native failure reason from the newest scene summary, if a scene recorded one."""
    summaries = sorted(suite_root.glob("*/summary.json"), key=lambda path: path.stat().st_mtime)
    for path in reversed(summaries):
        failure = json.loads(path.read_text(encoding="utf-8")).get("failure")
        if failure:
            return path.parent.name, failure.get("reason", "")
    return None, ""


def classify_failure(reason):
    return "focus_lost" if "focus" in reason.casefold() else "failed"


def run(args):
    # The launcher runs Python with -I, which leaves this script's folder off sys.path.
    sys.path.insert(0, str(args.planner_dir))
    sys.path.insert(0, str(HERE))
    # Imported here because both modules need the planner directory on sys.path first.
    # Load the shipped planner before run.py, which prepends a checkout path of its own.
    import mw3_re_launch  # noqa: F401
    import run as runner
    from freeze import freeze

    data_root = (Path(os.environ["LOCALAPPDATA"]) / "MW3Remaster").resolve(strict=True)
    runtime = args.runtime.resolve(strict=True)
    descriptor = runner.read_json(runtime / "runtime.json")
    executable = (runtime / descriptor["roles"]["executable"]).resolve(strict=True)
    if not executable.is_relative_to(runtime):
        raise ValueError(f"The runtime's game executable is outside {runtime}")
    if not executable_supports_benchmark(executable):
        emit(
            "error",
            kind="unsupported",
            message="This game build does not include the benchmark. Update Core Critical.",
        )
        return 3
    settings = runner.effective_settings(runner.read_json(data_root / "settings.json"), {})
    game = runner.resolve_game(settings)
    settings["GamePath"] = str(game)
    work = args.work_root.resolve()
    for root in (data_root, game, runtime):
        if work.is_relative_to(root) or root.is_relative_to(work):
            raise ValueError(f"The benchmark folder overlaps a read-only input: {work}")
    fixtures = args.fixtures.resolve(strict=True)
    definition = runner.read_json(fixtures / "suite-benchmark.json")
    recipes = b"".join(
        (fixtures / SCENE_RECIPES[s["id"]]).read_bytes() for s in definition["scenes"]
    )
    key = reference_key(
        runner.sha256(executable), game_archives_digest(game, runner.sha256), sha256_bytes(recipes)
    )
    definition_path, notes = prepare_references(
        work / "references" / key, definition, fixtures, executable, game, freeze, runner.sha256
    )
    results = work / "results"
    results.mkdir(parents=True, exist_ok=True)
    suite_root = results / time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    emit("progress", stage="play", scene=None, output=str(suite_root))
    try:
        runner.run_suite(
            definition_path, suite_root, "smoke", data_root, runtime, executable, settings
        )
    except ValueError as error:
        scene, reason = failure_reason(suite_root)
        emit(
            "error",
            kind=classify_failure(reason),
            scene=scene,
            message=reason or str(error),
            output=str(suite_root),
        )
        return 4
    report = build_report(suite_root, definition, settings, key, notes)
    report["previous"] = previous_report(results, report)
    (suite_root / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    emit("result", report=report, output=str(suite_root))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True, help="NativePreview directory")
    parser.add_argument("--planner-dir", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, default=HERE / "fixtures")
    args = parser.parse_args()
    try:
        return run(args)
    # The launcher shows any expected failure as one readable message.
    except (OSError, KeyError, TypeError, ValueError, subprocess.CalledProcessError) as error:
        emit("error", kind="failed", message=str(error))
        return 2


if __name__ == "__main__":
    sys.exit(main())
