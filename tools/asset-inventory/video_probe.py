"""Read-only ISO9660 leading-signature inventory and bounded AVI metadata probe.

Supports the primary ISO9660 tree with 2048-byte sectors, contiguous single
extents, and AVI 1.0 headers. No payloads are exported or codecs invoked.
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import mmap
from pathlib import Path
import struct


SECTOR = 2048
SPECIFICATIONS = [
    "https://ecma-international.org/wp-content/uploads/ECMA-119_2nd_edition_december_1987.pdf",
    "https://learn.microsoft.com/en-us/windows/win32/directshow/avi-riff-file-reference",
    "https://learn.microsoft.com/en-us/previous-versions/ms779632(v=vs.85)",
    "https://learn.microsoft.com/en-us/previous-versions/ms779638(v=vs.85)",
    "https://learn.microsoft.com/en-us/windows/win32/api/wingdi/ns-wingdi-bitmapinfoheader",
    "https://learn.microsoft.com/en-us/previous-versions/dd757713(v=vs.85)",
]


def both_endian(data, offset, width):
    little = int.from_bytes(data[offset:offset + width], "little")
    big = int.from_bytes(data[offset + width:offset + 2 * width], "big")
    if little != big:
        raise ValueError("ISO both-endian values disagree")
    return little


def directory_record(record, volume_bytes):
    if len(record) < 34 or record[0] != len(record):
        raise ValueError("Invalid ISO directory record length")
    name_size = record[32]
    if not name_size or 33 + name_size + (not name_size % 2) > len(record):
        raise ValueError("Invalid ISO identifier bounds")
    if record[1] or record[26] or record[27] or record[25] & 0x80:
        raise ValueError("Extended attributes, interleaving and multi-extents unsupported")
    if both_endian(record, 28, 2) != 1:
        raise ValueError("Multi-volume records unsupported")
    offset = both_endian(record, 2, 4) * SECTOR
    size = both_endian(record, 10, 4)
    if offset + size > volume_bytes:
        raise ValueError("ISO extent exceeds volume bounds")
    return {"offset": offset, "bytes": size, "flags": record[25],
            "identifier": record[33:33 + name_size]}


def iso_files(data):
    primary = None
    descriptors = []
    for sector in range(16, 128):
        block = data[sector * SECTOR:(sector + 1) * SECTOR]
        if len(block) != SECTOR or block[1:7] != b"CD001\x01":
            raise ValueError("Invalid ISO volume descriptor")
        descriptors.append(block[0])
        if block[0] == 1:
            if primary is not None and primary != block:
                raise ValueError("Conflicting primary descriptors unsupported")
            primary = block
        if block[0] == 255:
            break
    else:
        raise ValueError("ISO volume descriptor terminator missing")
    if primary is None or both_endian(primary, 128, 2) != SECTOR:
        raise ValueError("Primary ISO tree with 2048-byte blocks required")
    volume_bytes = both_endian(primary, 80, 4) * SECTOR
    if volume_bytes > len(data):
        raise ValueError("ISO volume exceeds input")
    root = directory_record(primary[156:156 + primary[156]], volume_bytes)
    if not root["flags"] & 2 or root["identifier"] != b"\x00":
        raise ValueError("Invalid ISO root directory")
    pending = [(root, "", 0)]
    visited, paths, files = set(), set(), []
    while pending:
        directory, parent, depth = pending.pop()
        key = (directory["offset"], directory["bytes"])
        if key in visited or depth > 16 or directory["bytes"] > 64 * 1024 * 1024:
            raise ValueError("ISO directory cycle, alias or size/depth limit")
        visited.add(key)
        pos, end = directory["offset"], sum(key)
        while pos < end:
            length = data[pos]
            if not length:
                sector_end = min((pos // SECTOR + 1) * SECTOR, end)
                if any(data[pos:sector_end]):
                    raise ValueError("Nonzero ISO directory padding")
                pos = sector_end
                continue
            if pos + length > end or pos % SECTOR + length > SECTOR:
                raise ValueError("ISO directory record crosses bounds")
            item = directory_record(data[pos:pos + length], volume_bytes)
            pos += length
            if item["identifier"] in (b"\x00", b"\x01"):
                continue
            name = item.pop("identifier").decode("ascii")
            if any(ord(c) < 32 for c in name) or any(c in name for c in "/\\"):
                raise ValueError("Invalid ISO path component")
            path = f"{parent}/{name}" if parent else name
            if path in paths:
                raise ValueError("Duplicate ISO path")
            paths.add(path)
            if len(paths) > 100000:
                raise ValueError("ISO entry limit exceeded")
            if item["flags"] & 2:
                item["identifier"] = name.encode("ascii")
                pending.append((item, path, depth + 1))
            else:
                files.append({"path": path, **item})
    return {"volume_id": primary[40:72].decode("ascii").rstrip(),
            "volume_bytes": volume_bytes, "descriptor_types": descriptors,
            "directory_count": len(visited), "files": sorted(files, key=lambda f: f["path"])}


def chunks(data, start, end):
    pos = start
    while pos < end:
        if pos + 8 > end:
            raise ValueError("Truncated RIFF chunk header")
        size = struct.unpack_from("<I", data, pos + 4)[0]
        following = pos + 8 + size + (size & 1)
        if following > end:
            raise ValueError("RIFF chunk exceeds parent bounds")
        yield data[pos:pos + 4], pos + 8, size
        pos = following


def only_chunk(items, chunk_id):
    matches = [(p, n) for k, p, n in items if k == chunk_id]
    if len(matches) != 1:
        raise ValueError(f"Exactly one {chunk_id!r} chunk required")
    return matches[0]


def avi_metadata(data, offset, size):
    if size < 12 or data[offset:offset + 4] != b"RIFF" or data[offset + 8:offset + 12] != b"AVI ":
        raise ValueError("Expected RIFF/AVI signature")
    end = offset + 8 + struct.unpack_from("<I", data, offset + 4)[0]
    if end < offset + 12 or end > offset + size or offset + size > len(data):
        raise ValueError("Invalid AVI RIFF bounds")
    top = list(chunks(data, offset + 12, end))
    lists = {}
    for kind, pos, length in top:
        if kind == b"LIST":
            if length < 4:
                raise ValueError("Truncated RIFF list type")
            list_type = data[pos:pos + 4]
            if list_type in lists:
                raise ValueError("Duplicate AVI top-level list")
            lists[list_type] = (pos + 4, pos + length)
    if b"hdrl" not in lists or b"movi" not in lists:
        raise ValueError("AVI header and movie lists required")
    header_chunks = list(chunks(data, *lists[b"hdrl"]))
    pos, length = only_chunk(header_chunks, b"avih")
    if length < 56:
        raise ValueError("Truncated AVI main header")
    fields = struct.unpack_from("<14I", data, pos)
    main = dict(zip(("microseconds_per_frame", "max_bytes_per_second", "padding_granularity",
                     "flags", "total_frames", "initial_frames", "stream_count", "suggested_buffer_bytes",
                     "width", "height"), fields[:10]))
    main["duration_seconds_from_main_header"] = fields[4] * fields[0] / 1000000
    streams = []
    for kind, pos, length in header_chunks:
        if kind != b"LIST":
            continue
        if length < 4:
            raise ValueError("Truncated header list")
        if data[pos:pos + 4] != b"strl":
            continue
        stream_chunks = list(chunks(data, pos + 4, pos + length))
        hp, hn = only_chunk(stream_chunks, b"strh")
        fp, fn = only_chunk(stream_chunks, b"strf")
        if hn < 56:
            raise ValueError("Truncated AVI stream header")
        header = struct.unpack_from("<4s4sIHH8I4h", data, hp)
        stream = dict(zip(("type", "handler", "flags", "priority", "language", "initial_frames",
                           "scale", "rate", "start", "length", "suggested_buffer_bytes", "quality",
                           "sample_size"), header[:13]))
        stream.update(type=header[0].decode("ascii"), handler=header[1].decode("ascii"),
                      frame_rectangle=list(header[13:]), index=len(streams))
        if not stream["scale"] or not stream["rate"]:
            raise ValueError("Zero AVI stream timescale")
        stream["units_per_second"] = stream["rate"] / stream["scale"]
        stream["duration_seconds"] = stream["length"] * stream["scale"] / stream["rate"]
        stream["start_seconds"] = stream["start"] * stream["scale"] / stream["rate"]
        if stream["type"] == "vids":
            if fn < 40:
                raise ValueError("Truncated video format")
            values = struct.unpack_from("<IiiHHIIiiII", data, fp)
            if values[0] < 40 or values[0] > fn:
                raise ValueError("Invalid BITMAPINFOHEADER bounds")
            stream["video_format"] = dict(zip(("header_bytes", "width", "height", "planes", "bits_per_pixel",
                "compression", "image_bytes", "x_pixels_per_meter", "y_pixels_per_meter", "colors_used",
                "colors_important"), values))
            stream["video_format"]["compression_fourcc"] = (data[fp + 16:fp + 20].decode("ascii")
                if values[5] > 3 else None)
        elif stream["type"] == "auds":
            if fn < 16:
                raise ValueError("Truncated audio format")
            values = struct.unpack_from("<HHIIHH", data, fp)
            stream["audio_format"] = dict(zip(("format_tag", "channels", "sample_rate", "byte_rate",
                                                 "block_align", "bits_per_sample"), values))
            if fn >= 18:
                extra = struct.unpack_from("<H", data, fp + 16)[0]
                if 18 + extra > fn:
                    raise ValueError("Audio extra format bytes exceed bounds")
                stream["audio_format"]["extra_format_bytes"] = extra
        streams.append(stream)
    if len(streams) != main["stream_count"]:
        raise ValueError("AVI stream count mismatch")
    counts, payload_bytes = Counter(), Counter()
    pending = [(*lists[b"movi"], 0)]
    chunk_count = 0
    while pending:
        start, finish, depth = pending.pop()
        if depth > 16:
            raise ValueError("AVI movie list nesting limit")
        for kind, pos, length in chunks(data, start, finish):
            chunk_count += 1
            if chunk_count > 1000000:
                raise ValueError("AVI chunk count limit")
            if kind == b"LIST":
                if length < 4 or data[pos:pos + 4] != b"rec ":
                    raise ValueError("Unsupported movie list")
                pending.append((pos + 4, pos + length, depth + 1))
            else:
                label = kind.decode("ascii")
                counts[label] += 1
                payload_bytes[label] += length
    for stream in streams:
        prefix = f'{stream["index"]:02d}'
        stream["observed_data_chunks"] = {k: v for k, v in sorted(counts.items()) if k.startswith(prefix)}
        stream["observed_data_bytes"] = {k: v for k, v in sorted(payload_bytes.items()) if k.startswith(prefix)}
    indexes = [n for k, p, n in top if k == b"idx1"]
    if any(n % 16 for n in indexes):
        raise ValueError("AVI index length is not a multiple of 16")
    return {"riff_bytes": end - offset, "trailing_bytes": offset + size - end,
            "main_header": main, "streams": streams, "movie_chunk_counts": dict(sorted(counts.items())),
            "index_entries": sum(indexes) // 16, "index_status": "sizes checked; offsets not validated",
            "payload_status": "not decoded; header/chunk counts do not establish playback correctness"}


def span_hash(data, offset, size):
    digest = hashlib.sha256()
    for pos in range(offset, offset + size, 1024 * 1024):
        digest.update(data[pos:min(pos + 1024 * 1024, offset + size)])
    return digest.hexdigest()


def inventory_iso(path):
    before = path.stat()
    with path.open("rb") as source, mmap.mmap(source.fileno(), 0, access=mmap.ACCESS_READ) as data:
        report = iso_files(data)
        signatures = Counter()
        videos = []
        for item in report["files"]:
            offset, size = item["offset"], item["bytes"]
            header = data[offset:offset + min(32, size)]
            kind = "unknown"
            if header[:4] == b"RIFF" and len(header) >= 12:
                kind = {b"AVI ": "riff-avi", b"WAVE": "riff-wave"}.get(header[8:12], "riff-other")
            elif header[:3] in (b"BIK", b"SMK"):
                kind = "bink-candidate" if header[:3] == b"BIK" else "smacker-candidate"
            elif header[:2] == b"MZ":
                kind = "dos-mz-candidate"
            item.update(sha256=span_hash(data, offset, size), signature_class=kind)
            signatures[kind] += 1
            if kind == "riff-avi":
                item["avi"] = avi_metadata(data, offset, size)
                videos.append(item)
            elif kind.endswith("candidate") and kind != "dos-mz-candidate":
                videos.append(item)
        report.update(source_sha256=span_hash(data, 0, len(data)), source_bytes=len(data),
                      video_count=len(videos), video_bytes=sum(f["bytes"] for f in videos),
                      signature_counts=dict(sorted(signatures.items())), file_count=len(report["files"]),
                      file_bytes=sum(f["bytes"] for f in report["files"]))
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError("ISO changed during inventory")
    report.update(schema_version=1, source_path=str(path),
                  created_utc=datetime.now(timezone.utc).isoformat(), specifications=SPECIFICATIONS,
                  scope="Primary ISO9660 leading signatures only; cabinet/embedded assets and other trees unexamined",
                  tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--expect-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = args.input.resolve()
    if not source.is_file() or source.is_symlink():
        parser.error("Input must be an existing regular ISO file")
    output = args.output.resolve()
    local_root = Path(__file__).resolve().parents[2] / "local" / "work-ahead"
    if not output.is_relative_to(local_root) or output == source or output.exists():
        parser.error("Output must be a new metadata file under local/work-ahead")
    report = inventory_iso(source)
    if report["source_sha256"] != args.expect_sha256.lower():
        parser.error("ISO hash differs from expected source")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as target:
        json.dump(report, target, indent=2)
        target.write("\n")
    print(json.dumps({k: report[k] for k in ("source_sha256", "volume_id", "file_count", "directory_count",
                       "signature_counts", "video_count", "video_bytes")}, indent=2))


if __name__ == "__main__":
    main()
