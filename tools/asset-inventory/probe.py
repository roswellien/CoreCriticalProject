"""Bounded MW3 image-table hypothesis and concatenated RIFF metadata probes."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct


def image_table(data):
    if len(data) < 24:
        raise ValueError("Truncated table header")
    header = struct.unpack_from("<6I", data)
    count = header[3]
    table_end = 24 + count * 40
    if not count or table_end > len(data):
        raise ValueError("Invalid count/table bounds")
    records = []
    for index in range(count):
        pos = 24 + index * 40
        raw_name, offset, marker = struct.unpack_from("<32sII", data, pos)
        name_bytes = raw_name.split(b"\0", 1)[0]
        if not name_bytes or any(c < 32 or c > 126 for c in name_bytes):
            raise ValueError(f"Invalid name at entry {index}")
        if offset < table_end or offset + 16 > len(data):
            raise ValueError(f"Invalid offset at entry {index}")
        if records and offset <= records[-1]["offset"]:
            raise ValueError("Offsets are not strictly increasing")
        records.append({"index": index, "name": name_bytes.decode("ascii"),
                        "offset": offset, "table_marker": marker})
    for index, item in enumerate(records):
        end = records[index + 1]["offset"] if index + 1 < count else len(data)
        size = end - item["offset"]
        if size < 16:
            raise ValueError("Truncated entry descriptor")
        tag, width, height, word2, word3 = struct.unpack_from("<IHHII", data, item["offset"])
        item.update(span_bytes=size, descriptor_tag=tag, candidate_width=width,
                    candidate_height=height, descriptor_words=[word2, word3],
                    matches_16_byte_header_plus_16bpp=(width > 0 and height > 0 and size == 16 + width * height * 2))
    return {"hypothesis": "24-byte header; count at 12; 40-byte name/offset/marker records",
            "header_words": list(header), "table_end": table_end,
            "gap_before_first_entry": records[0]["offset"] - table_end,
            "entry_count": count,
            "descriptor_tag_counts": dict(Counter(str(r["descriptor_tag"]) for r in records)),
            "exact_16bpp_spans": sum(r["matches_16_byte_header_plus_16bpp"] for r in records),
            "dimension_counts": dict(Counter(f'{r["candidate_width"]}x{r["candidate_height"]}' for r in records)),
            "entries": records}


def riff_streams(data):
    streams = []
    offset = 0
    while offset < len(data):
        if offset + 12 > len(data) or data[offset:offset + 4] != b"RIFF":
            if not streams:
                raise ValueError(f"Expected RIFF at offset {offset}")
            break
        end = offset + 8 + struct.unpack_from("<I", data, offset + 4)[0]
        if end > len(data) or end < offset + 12:
            raise ValueError("Invalid RIFF bounds")
        chunks = []
        pos = offset + 12
        while pos < end:
            if pos + 8 > end:
                raise ValueError("Truncated chunk header")
            size = struct.unpack_from("<I", data, pos + 4)[0]
            next_pos = pos + 8 + size + (size & 1)
            if next_pos > end:
                raise ValueError("Chunk exceeds RIFF bounds")
            chunk = {"id": data[pos:pos + 4].decode("ascii", errors="replace"),
                     "offset": pos, "bytes": size}
            if chunk["id"] == "fmt " and size >= 16:
                fields = struct.unpack_from("<HHIIHH", data, pos + 8)
                chunk["wave_format"] = dict(zip(
                    ("encoding", "channels", "sample_rate", "byte_rate", "block_align", "bits_per_sample"), fields))
            chunks.append(chunk)
            pos = next_pos
        streams.append({"offset": offset, "bytes": end - offset,
                        "form": data[offset + 8:offset + 12].decode("ascii", errors="replace"),
                        "chunks": chunks})
        offset = end + ((end - offset) & 1)
        if offset > len(data):
            raise ValueError("Missing RIFF padding")
    return {"stream_count": len(streams), "covered_bytes": offset,
            "trailing_bytes": len(data) - offset, "trailing_region_status": "unparsed",
            "streams": streams}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("images", "riff"))
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("Output must differ from input")
    data = args.input.read_bytes()
    report = (image_table if args.mode == "images" else riff_streams)(data)
    report.update(source_sha256=hashlib.sha256(data).hexdigest(), source_bytes=len(data),
                  tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("entries", "streams", "dimension_counts")}, indent=2))


if __name__ == "__main__":
    main()
