"""Strict MW3 RGB565 decoder for local research previews, without dependencies."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import zlib

from probe import image_table

MAX_PIXELS = 16 * 1024 * 1024
MAX_FILE_BYTES = 256 * 1024 * 1024


def describe(data, entry):
    offset = entry["offset"]
    flags, width, height, reserved, palette, stretch = struct.unpack_from("<IHHIHH", data, offset)
    if flags not in (3, 5, 11):
        raise ValueError(f"Unsupported flags {flags:#x}")
    if reserved or palette or stretch:
        raise ValueError("Reserved field, palette or stretch unsupported in this decoder")
    pixels = width * height
    if not width or not height or pixels > MAX_PIXELS:
        raise ValueError("Invalid or excessive dimensions")
    expected = 16 + pixels * (3 if flags == 11 else 2)
    if entry["span_bytes"] != expected:
        raise ValueError("Entry span does not exactly match descriptor and pixel planes")
    if entry["table_marker"] != 0xFFFFFFFF:
        raise ValueError("Global palette references unsupported")
    return {"flags": flags, "width": width, "height": height,
            "alpha_mode": {3: "black-key", 5: "opaque", 11: "byte-plane"}[flags],
            "palette_count": palette, "stretch": stretch, "pixels": pixels}


def decode(data, entry):
    info = describe(data, entry)
    count = info["pixels"]
    start = entry["offset"] + 16
    colors = memoryview(data)[start:start + count * 2]
    alpha_start = start + count * 2
    rgba = bytearray(count * 4)
    for index, (word,) in enumerate(struct.iter_unpack("<H", colors)):
        red = ((word >> 11) * 255 + 15) // 31
        green = (((word >> 5) & 63) * 255 + 31) // 63
        blue = ((word & 31) * 255 + 15) // 31
        alpha = data[alpha_start + index] if info["flags"] == 11 else (
            0 if info["flags"] == 3 and word == 0 else 255)
        rgba[index * 4:index * 4 + 4] = bytes((red, green, blue, alpha))
    return info, bytes(rgba)


def png_bytes(width, height, rgba):
    if width <= 0 or height <= 0 or width * height > MAX_PIXELS or len(rgba) != width * height * 4:
        raise ValueError("Invalid RGBA image dimensions/data")

    def chunk(kind, payload):
        return (struct.pack(">I", len(payload)) + kind + payload
                + struct.pack(">I", zlib.crc32(kind + payload)))

    stride = width * 4
    rows = b"".join(b"\0" + rgba[pos:pos + stride] for pos in range(0, len(rgba), stride))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


def inspect_package(data):
    table = image_table(data)
    if table["header_words"] != [0, 1, 0, table["entry_count"], 0, 0] or table["gap_before_first_entry"]:
        raise ValueError("Unsupported package header/layout")
    accepted, rejected = [], []
    for entry in table["entries"]:
        try:
            accepted.append({"index": entry["index"], "name": entry["name"], **describe(data, entry)})
        except ValueError as error:
            rejected.append({"index": entry["index"], "reason": str(error)})
    return table, accepted, rejected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--expect-sha256", required=True)
    parser.add_argument("--entry", type=int, action="append", default=[])
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    local_root = Path(__file__).resolve().parents[2] / "local"
    output = args.output_dir.resolve()
    if output == local_root.resolve() or not output.is_relative_to(local_root.resolve()):
        parser.error("Research outputs must stay in a subdirectory of this project's ignored local/")
    with args.input.open("rb") as stream:
        data = stream.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        parser.error("Input exceeds decoder size limit")
    source_hash = hashlib.sha256(data).hexdigest()
    if source_hash != args.expect_sha256.lower():
        parser.error("Input SHA-256 does not match expected source")
    table, accepted, rejected = inspect_package(data)
    previews = []
    if len(args.entry) != len(set(args.entry)):
        parser.error("Duplicate requested entry index")
    # Decode and validate the entire requested batch before writing any outputs.
    for index in args.entry:
        if not 0 <= index < len(table["entries"]):
            parser.error(f"Entry index out of range: {index}")
        entry = table["entries"][index]
        info, rgba = decode(data, entry)
        png = png_bytes(info["width"], info["height"], rgba)
        name = f"entry-{index:05d}.png"
        alpha_counts = Counter(rgba[3::4])
        previews.append((name, png, {"index": index, "name": entry["name"], **info,
                        "source_offset": entry["offset"], "source_span_bytes": entry["span_bytes"],
                        "file": name, "png_sha256": hashlib.sha256(png).hexdigest(),
                        "rgba_sha256": hashlib.sha256(rgba).hexdigest(),
                        "transparent_pixels": alpha_counts[0], "opaque_pixels": alpha_counts[255],
                        "alpha_min": min(alpha_counts), "alpha_max": max(alpha_counts),
                        "partial_alpha_pixels": sum(v for k, v in alpha_counts.items() if 0 < k < 255)}))
    report = {"schema_version": 1, "source_sha256": source_hash,
              "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "parser_sha256": hashlib.sha256(Path(__file__).with_name("probe.py").read_bytes()).hexdigest(),
              "decode_policy": "RGB565 scaled to RGBA8; stored row order; no gamma/stretch/resampling",
              "status": "research-preview; original-renderer comparison pending",
              "accepted_count": len(accepted), "rejected_count": len(rejected),
              "alpha_mode_counts": dict(Counter(item["alpha_mode"] for item in accepted)),
              "accepted_entries": accepted, "rejected_entries": rejected,
              "previews": [item[2] for item in previews]}
    targets = [output / name for name, _, _ in previews] + [output / "manifest.json"]
    if any(path.exists() or path.is_symlink() or not path.resolve().is_relative_to(output) for path in targets):
        parser.error("Output exists; choose a fresh directory to preserve prior evidence")
    output.mkdir(parents=True, exist_ok=True)
    for name, png, _ in previews:
        with (output / name).open("xb") as stream:
            stream.write(png)
    with (output / "manifest.json").open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("accepted_count", "rejected_count", "alpha_mode_counts", "previews")}, indent=2))


if __name__ == "__main__":
    main()
