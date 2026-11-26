"""Compare two complete developer strict arena benchmark runs, tick by tick."""

import argparse
import json
import math
import re
from itertools import zip_longest
from pathlib import Path

WORKLOAD_KEYS = ("scene_id", "log_sha256", "width", "height", "pixel_hash_kind")


def read_strict(path):
    if path.is_dir():
        path = path / "strict.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(document, dict)
        or document.get("mode") != "strict"
        or type(document.get("version")) is not int
        or document["version"] != 1
    ):
        raise ValueError(f"{path}: expected version 1 strict diagnostics")
    if document.get("valid") is not True or "failure" in document:
        raise ValueError(f"{path}: strict run failed: {document.get('failure')}")
    if (
        not isinstance(document.get("scene_id"), str)
        or not document["scene_id"]
        or not isinstance(document.get("log_sha256"), str)
        or re.fullmatch(r"[0-9a-f]{64}", document["log_sha256"]) is None
        or any(
            type(document.get(key)) is not int or document[key] <= 0 for key in ("width", "height")
        )
        or document.get("pixel_hash_kind") != "fnv1a64-swapchain-bgra8"
    ):
        raise ValueError(f"{path}: invalid strict workload or pixel format")
    frames = document.get("frames")
    expected = document.get("expected_ticks")
    if (
        not isinstance(frames, list)
        or type(expected) is not int
        or len(frames) != expected
        or not frames
    ):
        raise ValueError(f"{path}: incomplete strict frame sequence")
    previous = -math.inf
    for index, frame in enumerate(frames):
        if not isinstance(frame, dict):
            raise TypeError(f"{path}: invalid frame at tick {index}")
        time = frame.get("time_seconds")
        pixel_hash = frame.get("pixel_hash")
        if (
            type(frame.get("tick")) is not int
            or frame["tick"] != index
            or type(time) not in (int, float)
            or not math.isfinite(time)
            or time <= previous
            or not isinstance(pixel_hash, str)
            or re.fullmatch(r"[0-9a-f]{16}", pixel_hash) is None
        ):
            raise ValueError(f"{path}: invalid frame at tick {index}")
        previous = time
    return document


def compare(left_path, right_path):
    left = read_strict(left_path)
    right = read_strict(right_path)
    for key in WORKLOAD_KEYS:
        if left[key] != right[key]:
            raise ValueError(f"strict workloads differ in {key}")
    for index, (a, b) in enumerate(zip_longest(left["frames"], right["frames"])):
        if a is None or b is None:
            missing = "left" if a is None else "right"
            return 1, f"First differing tick {index}: missing from the {missing} run"
        if (a["time_seconds"], a["pixel_hash"]) != (b["time_seconds"], b["pixel_hash"]):
            return 1, (
                f"First differing tick {index}: left {a['time_seconds']} s {a['pixel_hash']}, "
                f"right {b['time_seconds']} s {b['pixel_hash']}"
            )
    return 0, f"All {len(left['frames'])} strict ticks match"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    args = parser.parse_args()
    try:
        code, message = compare(args.left, args.right)
    except (OSError, TypeError, ValueError, OverflowError) as error:
        parser.exit(2, f"strict_compare: {error}\n")
    print(message)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
