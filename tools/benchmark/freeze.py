"""Generate and verify a frozen arena recording in two serial game processes."""

import argparse
import filecmp
import hashlib
import json
import math
import os
import subprocess
from bisect import bisect_left
from collections import Counter
from itertools import accumulate, pairwise
from pathlib import Path

from run import BENCHMARK_ROOT, ROOT, read_json, sha256

FRAME_MS = 33
FRAME_SECONDS = FRAME_MS / 1000
CLOCK_TOLERANCE_SECONDS = 0.001
MIN_FRAME_SECONDS = FRAME_SECONDS - CLOCK_TOLERANCE_SECONDS
MAX_FRAME_SECONDS = FRAME_SECONDS + CLOCK_TOLERANCE_SECONDS
AFTERMATH_SECONDS = 5.0  # kAftermathSeconds in runtime/mw3-re/src/mech3/arena.h


def inspect_log(path, map_id, seed, roster_sizes):
    timestamps = []
    activity = []
    events = Counter()
    last = None
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if last == "end":
                raise ValueError("Records after the terminal end")
            record = json.loads(line)
            kind = record["type"]
            if last is None:
                expected = {
                    "type": "start",
                    "version": 2,
                    "map": map_id,
                    "seed": seed,
                    "frame_ms": FRAME_MS,
                    "record_every_update": True,
                }
                if any(record.get(key) != value for key, value in expected.items()):
                    raise ValueError("Recording start does not match the recipe")
                roster = Counter(mech["side"] for mech in record["mechs"])
                if roster != dict(enumerate(roster_sizes)):
                    raise ValueError(f"Unexpected spawned roster: {roster}")
            elif kind == "start":
                raise ValueError("Repeated start record")
            if kind == "state":
                time = record["t"]
                previous = timestamps[-1] if timestamps else 0
                # Native match time is a float. Allow 1 ms of clock precision,
                # well below a dropped or duplicated 33 ms snapshot.
                if (
                    not math.isfinite(time)
                    or not MIN_FRAME_SECONDS <= time - previous <= MAX_FRAME_SECONDS
                ):
                    raise ValueError(f"Off-cadence state at {time} after {previous}")
                if len(record["mechs"]) != sum(roster_sizes):
                    raise ValueError(f"Incomplete mech state at {time}")
                timestamps.append(time)
                activity.append(
                    (
                        len(record["rounds"]) + len(record["beams"]),
                        sum(mech["standing"] for mech in record["mechs"]),
                    )
                )
            events[kind] += 1
            last = kind
    if last != "end" or len(timestamps) < 2:
        raise ValueError("Recording lacks states or a terminal end")
    losses = record["lost"]
    if record["winner"] not in {"A", "B", "draw"} or len(losses) != len(roster_sizes):
        raise ValueError("Malformed end record")
    if any(
        type(lost) is not int or not 0 <= lost <= size for lost, size in zip(losses, roster_sizes)
    ):
        raise ValueError("Malformed end record losses")
    end_time = record["t"]
    last_state = timestamps[-1]
    if not math.isfinite(end_time) or end_time < last_state - CLOCK_TOLERANCE_SECONDS:
        raise ValueError("End record predates the final state")
    # The generator records states through the aftermath. Even allowing the
    # full aftermath and one update, a larger gap implies a truncated stream.
    if end_time > last_state + AFTERMATH_SECONDS + MAX_FRAME_SECONDS:
        raise ValueError("End record is too far past the final state")
    spacing = [1000 * (right - left) for left, right in pairwise(timestamps)]
    return {
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "states": len(timestamps),
        "first_state_seconds": timestamps[0],
        "last_state_seconds": timestamps[-1],
        "spacing_ms": [min(spacing), max(spacing)],
        "events": dict(events),
        "end": record,
        "candidate_windows": rank_windows(timestamps, activity),
    }


def rank_windows(timestamps, activity):
    # Integer-second candidates make the chosen route easy to reproduce.
    # The product counts co-occurrence, so empty aftermath cannot win on roster alone.
    totals = list(accumulate((effects * standing for effects, standing in activity), initial=0))
    effects_totals = list(accumulate((effects for effects, _ in activity), initial=0))
    standing_totals = list(accumulate((standing for _, standing in activity), initial=0))
    windows = []
    for start in range(10, math.floor(timestamps[-1]) - 29):
        left = bisect_left(timestamps, start)
        right = bisect_left(timestamps, start + 30)
        count = right - left
        windows.append(
            {
                "measured_start_seconds": start,
                "activity": (totals[right] - totals[left]) / count,
                "mean_rounds_and_beams": (effects_totals[right] - effects_totals[left]) / count,
                "mean_standing": (standing_totals[right] - standing_totals[left]) / count,
            }
        )
    return sorted(windows, key=lambda window: -window["activity"])


def source_revision():
    """The checkout's commit, or None in an installed launcher, which has no repository."""
    if not (ROOT / ".git").exists():
        return None
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def freeze(executable, game, recipe, seed, output, allowed_root=None):
    # Read the default at call time so the checkout's root can still be redirected.
    if allowed_root is None:
        allowed_root = BENCHMARK_ROOT
    if not output.is_relative_to(allowed_root.resolve()):
        raise ValueError(f"Output must be under {allowed_root}")
    launcher_data = os.environ.get("LOCALAPPDATA")
    read_only_roots = [game]
    if launcher_data:
        read_only_roots.append((Path(launcher_data) / "MW3Remaster").resolve())
    if any(output.is_relative_to(root) for root in read_only_roots):
        raise ValueError("Output overlaps a read-only input")
    setup = read_json(recipe)
    output.mkdir(parents=True)
    logs = []
    for attempt in ("first", "second"):
        directory = output / attempt
        directory.mkdir()
        setup["out"] = (directory / "log").as_posix()
        setup_path = directory / "setup.json"
        setup_path.write_text(json.dumps(setup), encoding="utf-8")
        subprocess.run(
            [
                str(executable),
                str(game),
                "--arena",
                str(setup_path),
                "--seed",
                str(seed),
                "--frame-ms",
                str(FRAME_MS),
                "--hidden",
                "-nofmv",
                "--arena-record-every-update",
                "--write-dir",
                str(directory / "profile"),
                "--no-import",
                "--no-mods",
                "--no-launcher",
                "--no-vfw-helper",
            ],
            cwd=executable.parent,
            check=True,
        )
        logs.append(directory / "log" / f"match-{seed}.jsonl")
    if not filecmp.cmp(*logs, shallow=False):
        raise ValueError("Fresh recordings differ byte for byte")
    result = inspect_log(logs[0], setup["map"], seed, [len(side) for side in setup["sides"]])
    archives = {
        archive.name.casefold(): sha256(archive)
        for archive in sorted((game / "zbd").iterdir())
        if archive.suffix.casefold() == ".zbd" and archive.is_file()
    }
    archive_manifest = json.dumps(archives, sort_keys=True, separators=(",", ":")).encode("utf-8")
    result.update(
        executable_sha256=sha256(executable),
        source_sha=source_revision(),
        reader_zbd_sha256=archives["reader.zbd"],
        game_archives_sha256=hashlib.sha256(archive_manifest).hexdigest(),
        game_archives=archives,
        recipe_sha256=sha256(recipe),
        seed=seed,
    )
    logs[0].replace(output / logs[0].name)
    (output / "freeze.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=BENCHMARK_ROOT / "build/Release/mw3.exe")
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--setup", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    try:
        result = freeze(
            args.exe.resolve(strict=True),
            args.game_dir.resolve(strict=True),
            args.setup.resolve(strict=True),
            args.seed,
            args.out.resolve(),
        )
    except (OSError, KeyError, TypeError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(2, f"freeze: {error}\n")
    result["candidate_windows"] = result["candidate_windows"][:5]
    result.pop("game_archives")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
