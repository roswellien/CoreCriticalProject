"""Inspect verified capture state and export supported packed RGB resources."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import struct

from verify_capture import verify


def decode_rgb(info, data):
    if not info["flags"] & 0x40 or info["bits"] not in (16, 24, 32):
        raise ValueError("Only captured packed RGB16/24/32 formats are decoded")
    masks = [info[key] for key in ("r_mask", "g_mask", "b_mask", "a_mask")]
    channels = []
    occupied = 0
    for mask in masks:
        if not mask:
            channels.append(None)
            continue
        shift = (mask & -mask).bit_length() - 1
        maximum = mask >> shift
        if maximum & (maximum + 1) or mask >> info["bits"] or occupied & mask:
            raise ValueError("Invalid/noncontiguous/overlapping channel mask")
        occupied |= mask
        channels.append((mask, shift, maximum))
    result = bytearray()
    step = info["bits"] // 8
    for start in range(0, len(data), step):
        word = int.from_bytes(data[start:start + step], "little")
        for i, channel in enumerate(channels):
            if channel:
                mask, shift, maximum = channel
                value = (word & mask) >> shift
                result.append((value * 255 + maximum // 2) // maximum)
            else:
                result.append(255 if i == 3 else 0)
    return bytes(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--allow-authored", action="store_true")
    args = parser.parse_args()
    report = verify(args.directory, args.allow_authored)
    rows = [json.loads(line) for line in (args.directory / "capture.jsonl").read_text().splitlines()]
    states = defaultdict(set)
    textures = {}
    formats = set()
    for row in rows:
        if row["event"] != "draw":
            continue
        for state, value in row["render_states"].items():
            states[state].add(value)
        for stage in row["stages"]:
            info = stage["texture"]
            if info:
                textures[json.dumps(info, sort_keys=True)] = info
                formats.add((info["flags"], info["bits"], info["r_mask"], info["g_mask"], info["b_mask"], info["a_mask"]))
    report["render_state_values"] = {key: sorted(value) for key, value in states.items()}
    report["unique_texture_snapshots"] = len(textures)
    report["texture_pixel_formats"] = sorted(formats)
    args.output.mkdir(parents=True, exist_ok=True)
    from PIL import Image
    exported = []
    for role in ("initial_target", "final_target"):
        info = next(row["surface"] for row in rows if row["event"] == role)
        data = (args.directory / info["file"]).read_bytes()
        rgba = decode_rgb(info, data)
        Image.frombytes("RGBA", (info["width"], info["height"]), rgba).save(args.output / f"{role}.png")
        exported.append(role + ".png")
    for i, info in enumerate(textures.values()):
        data = (args.directory / info["file"]).read_bytes()
        rgba = decode_rgb(info, data)
        filename = f"texture-{i:03}.png"
        Image.frombytes("RGBA", (info["width"], info["height"]), rgba).save(args.output / filename)
        exported.append(filename)
    report["exported_images"] = exported
    report["decoder_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (args.output / "description.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
