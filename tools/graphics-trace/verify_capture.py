"""Verify exact payloads and selected scene data; not a proof of frame equivalence."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct


def verify(directory, allow_authored=False):
    rows = [json.loads(line) for line in (directory / "capture.jsonl").read_text().splitlines()]
    if not rows or rows[0]["event"] != "begin" or rows[-1]["event"] != "end" or rows[-1]["complete"] is not True:
        raise ValueError("Capture did not complete; partial/aborted data cannot pass")
    if not allow_authored and rows[0]["live"] is not True:
        raise ValueError("Authored fixture cannot satisfy a live capture gate")
    if "requested_skip" in rows[0] and (rows[0]["requested_skip"] != rows[0].get("skipped_scenes") or not 0 <= rows[0]["requested_skip"] <= 36000):
        raise ValueError("Delayed capture scene accounting mismatch")
    references = set()

    def payload(filename, size):
        if not re.fullmatch(r"[0-9a-f]{64}\.bin", filename):
            raise ValueError("Invalid content-addressed payload filename")
        data = (directory / filename).read_bytes()
        if len(data) != size or hashlib.sha256(data).hexdigest() != filename[:-4]:
            raise ValueError("Payload size/hash mismatch")
        references.add(filename)
        return data

    def surface(info):
        if info["bits"] not in (8, 16, 24, 32) or not (0 < info["width"] <= 4096 and 0 < info["height"] <= 4096):
            raise ValueError("Unsupported surface layout")
        expected = info["width"] * (info["bits"] // 8)
        if info["row_bytes"] != expected or abs(info["source_pitch"]) < expected:
            raise ValueError("Invalid surface row/pitch metadata")
        payload(info["file"], expected * info["height"])
        if info["fourcc"] and info["flags"] & 4:
            raise ValueError("Compressed/FOURCC layout is not recovered")
        if info["flags"] & 0x20:
            raise ValueError("Palette contents are not captured yet")

    initial = [row for row in rows if row["event"] == "initial_target"]
    final = [row for row in rows if row["event"] == "final_target"]
    depth = [row for row in rows if row["event"] == "initial_depth"]
    if len(initial) != 1 or len(final) != 1 or len(depth) != 1:
        raise ValueError("Missing or duplicate target/depth boundary")
    surface(initial[0]["surface"]); surface(final[0]["surface"])
    if not depth[0].get("absent"):
        surface(depth[0]["surface"])
    draws = [row for row in rows if row["event"] == "draw"]
    if not draws or len(draws) != rows[-1]["draws"] or len(draws) > 2048:
        raise ValueError("Missing/inconsistent bounded draw sequence")
    if len(draws) < rows[0].get("minimum_draws", 0):
        raise ValueError("Interval did not meet the requested scene selection minimum")
    texture_snapshots = 0
    for ordinal, draw in enumerate(draws, 1):
        if draw["ordinal"] != ordinal:
            raise ValueError("Dropped or reordered draw")
        fvf = draw["fvf"]
        position, textures = fvf & 14, (fvf >> 8) & 15
        if position not in (2, 4) or textures > 8 or fvf & ~0xFDE:
            raise ValueError("Unrecovered vertex format")
        stride = (16 if position == 4 else 12) + (12 if fvf & 16 else 0) + (4 if fvf & 64 else 0) + (4 if fvf & 128 else 0) + textures * 8
        if stride != draw["stride"]:
            raise ValueError("Vertex stride mismatch")
        payload(draw["vertices"], draw["vertex_count"] * stride)
        if draw["index_count"]:
            indices = payload(draw["indices"], draw["index_count"] * 2)
            if any(index >= draw["vertex_count"] for (index,) in struct.iter_unpack("<H", indices)):
                raise ValueError("Index out of vertex range")
        elif draw["indices"] is not None:
            raise ValueError("Unexpected index payload")
        if depth[0].get("absent") and draw["render_states"]["7"]:
            raise ValueError("Depth is enabled but initial depth was not captured")
        if [stage["stage"] for stage in draw["stages"]] != list(range(8)):
            raise ValueError("Missing texture stages")
        for stage in draw["stages"]:
            if stage["texture"]:
                surface(stage["texture"]); texture_snapshots += 1
                if stage["texture"]["caps"] & 0x400000 and stage["states"]["18"]:
                    raise ValueError("Mip filtering enabled but mip chain not captured")
    actual = {path.name for path in directory.glob("*.bin")}
    if actual != references or len(actual) != rows[-1]["resource_files"]:
        raise ValueError("Missing/unreferenced resource payload")
    total = sum((directory / filename).stat().st_size for filename in references)
    if total != rows[-1]["stored_bytes"] or total > 64 * 1024 * 1024:
        raise ValueError("Storage budget/accounting mismatch")
    return {"live": rows[0]["live"], "pid": rows[0]["pid"], "draws": len(draws),
            "skipped_scenes": rows[0].get("skipped_scenes", 0),
            "texture_snapshots": texture_snapshots, "payload_files": len(actual), "stored_bytes": total,
            "target_size": [initial[0]["surface"]["width"], initial[0]["surface"]["height"]],
            "manifest_sha256": hashlib.sha256((directory / "capture.jsonl").read_bytes()).hexdigest(),
            "scope": "Selected draw/state/resource snapshots; command closure, clear/presentation coverage and Vulkan equivalence unproven"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--allow-authored", action="store_true")
    args = parser.parse_args()
    print(json.dumps(verify(args.directory, args.allow_authored), indent=2))


if __name__ == "__main__":
    main()
