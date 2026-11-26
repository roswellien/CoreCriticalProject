"""Validate and compare four complete arena suites in A1 B1 B2 A2 order."""

import argparse
import csv
import hashlib
import json
import math
import re
from fractions import Fraction
from pathlib import Path

from run import BENCHMARK_ROOT, BLOCK_ORDER, SUITE_SCENES, read_json, sha256

BUILD_KEYS = ("source_sha", "executable_sha256")
HOST_KEYS = ("gpu", "vulkan_driver_version")
STAT_KEYS = ("mean_ms", "p50_ms", "p95_ms", "p99_ms", "average_fps", "low_1_percent_fps")
LOAD_KEYS = ("process_to_epoch_seconds", "scene_load_to_epoch_seconds")
PRESSURE_KEYS = ("model_omissions", "preload_stops", "recoveries", "texture_substitutions")
CSV_COLUMNS = [
    "scene_id",
    "frame_seq",
    "replay_time_seconds",
    "present_elapsed_seconds",
    "interval_ms",
]
PINNED_KEYS = {
    "asset_fingerprint",
    "backend",
    "camera",
    "disk_cache",
    "game_dir",
    "log_sha256",
    "log_start_seconds",
    "map",
    "measured_seconds",
    "packs",
    "present_mode",
    "render_worker",
    "scene",
    "seed",
    "stress",
    "vsync",
    "warmup_seconds",
}
FEATURE_CATALOG_DIGESTS = {
    "effects_catalog_sha256",
    "headlight_catalog_sha256",
    "headlight_bindings_sha256",
}
THRESHOLD = Fraction(5)


def digest_valid(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def nonempty_string(value):
    return isinstance(value, str) and bool(value)


def canonical_settings(settings):
    return json.dumps(
        settings, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )


def require_object(value, description):
    if not isinstance(value, dict):
        raise TypeError(f"{description} must be a JSON object")
    return value


def validate_summary(path, scene):
    summary = require_object(read_json(path), path)
    reject_strict(summary, path)
    version = summary.get("version")
    if type(version) is not int or version != 1 or summary.get("scene_id") != scene:
        raise ValueError(f"{path}: wrong summary version or scene")
    if summary.get("valid") is not True or summary.get("failure") is not None:
        raise ValueError(f"{path}: invalid run, failure={summary.get('failure')}")
    pressure = summary["video_memory_pressure"]
    if (
        not isinstance(pressure, dict)
        or not set(PRESSURE_KEYS).issubset(pressure)
        or any(type(count) is not int or count != 0 for count in pressure.values())
    ):
        raise ValueError(f"{path}: invalid video_memory_pressure: {pressure}")
    settings = require_object(summary["settings"], f"{path}: settings")
    statistics = require_object(summary["statistics"], f"{path}: statistics")
    if settings.get("disk_cache") != "disabled":
        raise ValueError(f"{path}: effective disk_cache must be disabled")
    fingerprint = hashlib.sha256(canonical_settings(settings).encode("utf-8")).hexdigest()
    if summary["settings_sha256"] != fingerprint:
        raise ValueError(f"{path}: settings_sha256 does not bind the effective settings")
    if not nonempty_string(summary.get("source_sha")) or not digest_valid(
        summary["executable_sha256"]
    ):
        raise ValueError(f"{path}: missing build identity")
    if not nonempty_string(summary.get("gpu")) or type(summary["vulkan_driver_version"]) is not int:
        raise ValueError(f"{path}: missing GPU or driver identity")
    presents, intervals = summary["measured_presents"], summary["intervals"]
    if type(presents) is not int or presents < 2 or type(intervals) is not int:
        raise ValueError(f"{path}: invalid measured present or interval count")
    if intervals != presents - 1:
        raise ValueError(f"{path}: interval count must equal measured_presents - 1")
    csv_path = path.with_name("frames.csv")
    if sha256(csv_path) != summary["frames_sha256"]:
        raise ValueError(f"{path}: frames_sha256 mismatch")
    rows = 0
    with csv_path.open(encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        if next(reader, None) != CSV_COLUMNS:
            raise ValueError(f"{csv_path}: invalid header")
        for rows, row in enumerate(reader, start=1):
            if len(row) != len(CSV_COLUMNS) or row[0] != scene:
                raise ValueError(f"{csv_path}: invalid frame row {rows}")
            if bool(row[-1]) != (rows > 1):
                raise ValueError(f"{csv_path}: invalid interval in frame row {rows}")
            if rows > 1 and not positive_number(float(row[-1])):
                raise ValueError(f"{csv_path}: invalid interval in frame row {rows}")
    if rows != presents:
        raise ValueError(f"{csv_path}: CSV row count {rows} differs from {presents} presents")
    for key in STAT_KEYS:
        if not positive_number(statistics[key]):
            raise ValueError(f"{path}: invalid {key}")
    for key in LOAD_KEYS:
        value = summary[key]
        if value != "unavailable" and not positive_number(value, minimum=0):
            raise ValueError(f"{path}: invalid {key}")
    return summary


def reject_strict(document, path):
    if document.get("mode") == "strict":
        raise ValueError(f"{path}: strict diagnostics are unscored. Use strict_compare.py.")


def positive_number(value, minimum=None):
    if type(value) not in (int, float) or not math.isfinite(value):
        return False
    return value > 0 if minimum is None else value >= minimum


def inside(root, relative):
    path = (root / relative).resolve(strict=True)
    if path == root or not path.is_relative_to(root) or Path(relative).is_absolute():
        raise ValueError(f"Manifest path must stay inside {root}: {relative}")
    return path


def launch_directory(argv, flag):
    if argv.count(flag) == 1:
        index = argv.index(flag) + 1
        if index < len(argv) and argv[index]:
            return Path(argv[index]).resolve()
    return None


def read_suite(path, label, previous_end, profiles, summaries):
    if path.is_dir():
        if (path / "strict.json").is_file():
            reject_strict(require_object(read_json(path / "strict.json"), path), path)
        path = path / "suite.json"
    path = path.resolve(strict=True)
    manifest = require_object(read_json(path), path)
    reject_strict(manifest, path)
    root = path.parent
    version = manifest.get("version")
    if type(version) is not int or version != 1 or manifest.get("label") != label:
        raise ValueError(f"{path}: expected version 1 suite {label} in A1 B1 B2 A2 order")
    if not nonempty_string(manifest.get("host")) or not digest_valid(manifest["definition_sha256"]):
        raise ValueError(f"{path}: missing host or definition identity")
    entries = manifest["scenes"]
    if not isinstance(entries, list):
        raise TypeError(f"{path}: scenes must be a JSON array")
    if [require_object(entry, f"{path}: scene")["id"] for entry in entries] != list(SUITE_SCENES):
        raise ValueError(f"{path}: missing, extra or out-of-order suite scene")
    start, finish = manifest["started_ns"], manifest["finished_ns"]
    if type(start) is not int or type(finish) is not int or not previous_end <= start < finish:
        raise ValueError(f"{path}: suites overlap or ran out of order")
    previous_end = start

    def read_entry(entry):
        nonlocal previous_end
        scene_start, scene_end = entry["started_ns"], entry["finished_ns"]
        if (
            type(scene_start) is not int
            or type(scene_end) is not int
            or not previous_end <= scene_start < scene_end <= finish
        ):
            raise ValueError(f"{path}: scenes overlap or ran out of order")
        previous_end = scene_end
        profile = inside(root, entry["profile"])
        if not profile.is_dir() or any(
            profile.is_relative_to(used) or used.is_relative_to(profile) for used in profiles
        ):
            raise ValueError(f"{path}: profiles must be distinct and isolated: {profile}")
        plan_path = profile / "launch-plan.json"
        argv = require_object(read_json(plan_path), plan_path)["argv"]
        if not isinstance(argv, list) or not all(isinstance(arg, str) for arg in argv):
            raise TypeError(f"{plan_path}: argv must be a JSON array of strings")
        if "--benchmark-strict" in argv:
            raise ValueError(
                f"{plan_path}: strict diagnostics are unscored. Use strict_compare.py."
            )
        if launch_directory(argv, "--write-dir") != profile:
            raise ValueError(f"{path}: launch plan does not use its isolated profile: {profile}")
        profiles.add(profile)
        summary = inside(root, entry["summary"])
        if summary in summaries:
            raise ValueError(f"{path}: summary paths must be distinct: {summary}")
        output = launch_directory(argv, "--benchmark-out")
        if summary.parent != output:
            raise ValueError(
                f"{path}: summary must be directly in its launch plan --benchmark-out: {summary}"
            )
        if summary.name == "strict.json":
            reject_strict(require_object(read_json(summary), summary), summary)
        if summary.name != "summary.json" or sha256(summary) != entry["summary_sha256"]:
            raise ValueError(f"{path}: summary identity mismatch: {summary}")
        summaries.add(summary)
        return validate_summary(summary, entry["id"])

    conditioning = manifest.get("conditioning")
    if label == "A1":
        if conditioning is None:
            raise ValueError(f"{path}: A1 requires the preceding reference conditioning run")
        conditioning = require_object(conditioning, f"{path}: conditioning")
        if conditioning.get("id") != SUITE_SCENES[0]:
            raise ValueError(f"{path}: A1 requires the preceding reference conditioning run")
        reference = read_entry(conditioning)
    elif conditioning is not None:
        raise ValueError(f"{path}: conditioning belongs before A1")
    scenes = {entry["id"]: read_entry(entry) for entry in entries}
    if label == "A1":
        first = scenes[SUITE_SCENES[0]]
        require_equal(
            reference,
            first,
            (*BUILD_KEYS, *HOST_KEYS, "settings_sha256"),
            f"{path}: conditioning differs from A1",
        )
    first = scenes[SUITE_SCENES[0]]
    for scene, summary in scenes.items():
        require_equal(
            first, summary, (*BUILD_KEYS, *HOST_KEYS), f"{path}: build or GPU changed at {scene}"
        )
    return manifest, scenes


def differing_keys(first, second):
    return {
        key
        for key in first.keys() | second.keys()
        if key not in first
        or key not in second
        or canonical_settings(first[key]) != canonical_settings(second[key])
    }


def require_equal(first, second, keys, reason):
    changed = [key for key in keys if first[key] != second[key]]
    if changed:
        raise ValueError(f"{reason}: {', '.join(changed)}")


def check_delta(runs, setting, dependencies):
    if dependencies and setting is None:
        raise ValueError("Dependent keys require a declared primary setting")
    if setting in dependencies or len(set(dependencies)) != len(dependencies):
        raise ValueError("Declare each setting key once")
    allowed = {setting, *dependencies} - {None}
    optional_digests = FEATURE_CATALOG_DIGESTS.intersection(dependencies)
    pinned = {
        key
        for key in allowed
        if key in PINNED_KEYS
        or ("sha256" in key and key not in optional_digests)
        or key.startswith(
            (
                "override_",
                "prepared_model.",
                "prepared_material.",
                "prepared_skin.",
                "prepared_normal.",
            )
        )
    }
    if pinned:
        raise ValueError(f"Frozen workload keys cannot be declared: {', '.join(sorted(pinned))}")
    observed = set()
    primary_values = None
    for scene in SUITE_SCENES:
        first_a, first_b, second_b, second_a = (runs[label][scene] for label in BLOCK_ORDER)
        for label, first, second in (("A", first_a, second_a), ("B", first_b, second_b)):
            require_equal(first, second, BUILD_KEYS, f"{scene}: arm {label} build drift")
            changed = differing_keys(first["settings"], second["settings"])
            if changed or first["settings_sha256"] != second["settings_sha256"]:
                raise ValueError(
                    f"{scene}: arm {label} settings drift: {', '.join(sorted(changed))}"
                )
        settings_a, settings_b = first_a["settings"], first_b["settings"]
        changed = differing_keys(settings_a, settings_b)
        undeclared = changed - allowed
        if undeclared:
            raise ValueError(
                f"{scene}: undeclared between-arm settings differences: "
                f"{', '.join(sorted(undeclared))}"
            )
        # The runtime omits these digests when their resource paths are disabled.
        mismatched_digests = changed & optional_digests & settings_a.keys() & settings_b.keys()
        if mismatched_digests:
            raise ValueError(
                f"{scene}: catalog digest mismatch between arms: "
                f"{', '.join(sorted(mismatched_digests))}"
            )
        if setting is not None:
            if setting not in changed or setting not in settings_a or setting not in settings_b:
                raise ValueError(
                    f"{scene}: declared primary setting must differ between arms: {setting}"
                )
            values = (
                canonical_settings(settings_a[setting]),
                canonical_settings(settings_b[setting]),
            )
            if primary_values is not None and values != primary_values:
                raise ValueError(f"{scene}: inconsistent between-arm values for {setting}")
            primary_values = values
        observed.update(changed)
    return sorted(observed)


def verdict(ratio_product, scene_count, noise, noisy):
    if noisy:
        return "inconclusive"
    bound = max(THRESHOLD, noise) / 100
    # Comparing products keeps exact thresholds exact, including at the geometric mean.
    if ratio_product > (1 + bound) ** scene_count:
        return "regression"
    if ratio_product < (1 - bound) ** scene_count:
        return "improvement"
    return "no change"


def score(runs):
    scenes = {}
    product = Fraction(1)
    overall_noise = Fraction(0)
    for scene in SUITE_SCENES:
        summaries = {label: runs[label][scene] for label in BLOCK_ORDER}
        means = {
            label: Fraction(str(run["statistics"]["mean_ms"])) for label, run in summaries.items()
        }
        arm_a = (means["A1"] + means["A2"]) / 2
        arm_b = (means["B1"] + means["B2"]) / 2
        spread_a = 100 * abs(means["A1"] - means["A2"]) / arm_a
        spread_b = 100 * abs(means["B1"] - means["B2"]) / arm_b
        noise = max(spread_a, spread_b)
        ratio = arm_b / arm_a
        product *= ratio
        overall_noise = max(overall_noise, noise)
        scenes[scene] = {
            "a_mean_ms": float(arm_a),
            "b_mean_ms": float(arm_b),
            "a_spread_percent": float(spread_a),
            "b_spread_percent": float(spread_b),
            "noise_percent": float(noise),
            "change_percent": float(100 * (ratio - 1)),
            "runs": {
                label: {
                    **summary["statistics"],
                    **{key: summary[key] for key in (*LOAD_KEYS, "measured_presents")},
                }
                for label, summary in summaries.items()
            },
        }
        scenes[scene]["verdict"] = verdict(ratio, 1, noise, noise > THRESHOLD)
    noisy = overall_noise > THRESHOLD
    if noisy:
        for result in scenes.values():
            result["verdict"] = "inconclusive"
    return {
        "scenes": scenes,
        "overall": {
            "change_percent": 100 * (float(product) ** (1 / len(scenes)) - 1),
            "noise_percent": float(overall_noise),
            "verdict": verdict(product, len(scenes), overall_noise, noisy),
        },
    }


def compare(paths, setting=None, dependencies=()):
    runs = {}
    profiles = set()
    summaries = set()
    previous_end = 0
    for path, label in zip(paths, BLOCK_ORDER, strict=True):
        manifest, runs[label] = read_suite(path, label, previous_end, profiles, summaries)
        previous_end = manifest["finished_ns"]
        if label == "A1":
            reference = manifest
        else:
            require_equal(
                reference, manifest, ("host", "definition_sha256"), f"{label}: suite drift"
            )
            require_equal(
                runs["A1"][SUITE_SCENES[0]],
                runs[label][SUITE_SCENES[0]],
                HOST_KEYS,
                f"{label}: hardware drift",
            )
    observed = check_delta(runs, setting, dependencies)
    return {
        "version": 1,
        "run_order": list(BLOCK_ORDER),
        "host": reference["host"],
        "hardware": {key: runs["A1"][SUITE_SCENES[0]][key] for key in HOST_KEYS},
        "definition_sha256": reference["definition_sha256"],
        "settings_delta": {
            "setting": setting,
            "dependents": list(dependencies),
            "observed": observed,
        },
        "builds": {
            arm: {key: runs[arm + "1"][SUITE_SCENES[0]][key] for key in BUILD_KEYS}
            for arm in ("A", "B")
        },
        **score(runs),
    }


def format_report(result):
    overall = result["overall"]
    overall_line = (
        f"Overall: {overall['verdict']} ({overall['change_percent']:+.3f}%, "
        f"noise bound {overall['noise_percent']:.3f}%)"
    )
    lines = [overall_line]
    for scene, stats in result["scenes"].items():
        lines.append(
            f"{scene}: {stats['verdict']} ({stats['change_percent']:+.3f}%), "
            f"A {stats['a_mean_ms']:.3f} ms, B {stats['b_mean_ms']:.3f} ms, "
            f"spreads A {stats['a_spread_percent']:.3f}%, B {stats['b_spread_percent']:.3f}%"
        )
        for label, run in stats["runs"].items():
            startup, load = (
                f"{run[key]:.3f} s" if run[key] != "unavailable" else run[key] for key in LOAD_KEYS
            )
            lines.append(
                f"  {label}: {run['measured_presents']} presents, {run['average_fps']:.2f} FPS, "
                f"1% low {run['low_1_percent_fps']:.2f} FPS, "
                f"p50/p95/p99 {run['p50_ms']:.2f}/{run['p95_ms']:.2f}/{run['p99_ms']:.2f} ms, "
                f"startup {startup}, scene load {load}"
            )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", nargs=4, type=Path, metavar="SUITE")
    parser.add_argument("--setting", help="One effective settings key being changed")
    parser.add_argument(
        "--dependent", action="append", default=[], help="Dependent key (repeatable)"
    )
    parser.add_argument(
        "--out", type=Path, required=True, help="Fresh JSON file under local/benchmark"
    )
    args = parser.parse_args()
    try:
        result = compare(args.runs, args.setting, args.dependent)
        output = args.out.resolve()
        if not output.is_relative_to(BENCHMARK_ROOT.resolve()):
            raise ValueError("Comparison output must be under local/benchmark")
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2, allow_nan=False)
            stream.write("\n")
        print(format_report(result))
    except (OSError, ValueError, TypeError, KeyError, IndexError, csv.Error) as error:
        parser.exit(2, f"compare: {error}\n")


if __name__ == "__main__":
    main()
