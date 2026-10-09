"""Read-only asset discovery. Writes metadata, never extracted payloads."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import wave


def inspect_file(path):
    before = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        header = stream.read(32)
        digest.update(header)
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError(f"Input changed during hashing: {path}")
    metadata = {}
    kind = "unknown"
    if header[:4] == b"RIFF" and len(header) >= 12:
        form = header[8:12]
        kind = {b"WAVE": "riff-wave", b"AVI ": "riff-avi"}.get(form, "riff-other")
        metadata["riff_declared_bytes"] = struct.unpack_from("<I", header, 4)[0] + 8
        metadata["riff_size_matches"] = metadata["riff_declared_bytes"] == before.st_size
        if form == b"WAVE":
            try:
                with wave.open(str(path), "rb") as audio:
                    metadata.update(channels=audio.getnchannels(),
                                    sample_rate=audio.getframerate(),
                                    sample_width_bytes=audio.getsampwidth(),
                                    frames=audio.getnframes(),
                                    duration_seconds=audio.getnframes() / audio.getframerate())
            except (wave.Error, EOFError) as error:
                metadata["decode_error"] = str(error)
    elif header[:2] == b"MZ":
        kind = "dos-mz-candidate"
    elif header[:4] == b"DDS ":
        kind = "dds-candidate"
    elif header[:8] == b"\x89PNG\r\n\x1a\n":
        kind = "png-candidate"
    elif header[:3] in (b"BIK", b"SMK"):
        kind = "bink-candidate" if header[:3] == b"BIK" else "smacker-candidate"
    if path.suffix.lower() == ".zbd":
        metadata["container_status"] = "unparsed; extension is not format proof"
        metadata["header_sha256"] = hashlib.sha256(header).hexdigest()
        metadata["header_bytes_observed"] = len(header)
    return {"bytes": before.st_size, "sha256": digest.hexdigest(),
            "extension": path.suffix.lower(), "signature_class": kind,
            "metadata": metadata}


def inventory(root, excluded):
    files = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part.casefold() in excluded for part in relative.parts):
            continue
        if path.is_symlink():
            raise ValueError(f"Symlink input is unsupported: {path}")
        if path.is_file():
            if not path.resolve().is_relative_to(root):
                raise ValueError(f"Input escapes root: {path}")
            files.append({"path": relative.as_posix(), **inspect_file(path)})
    by_hash = {}
    for item in files:
        by_hash.setdefault(item["sha256"], []).append(item["path"])
    return {"schema_version": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
            "root": str(root), "excluded_directory_names": sorted(excluded),
            "file_count": len(files), "total_bytes": sum(f["bytes"] for f in files),
            "extension_counts": dict(sorted(Counter(f["extension"] for f in files).items())),
            "signature_counts": dict(sorted(Counter(f["signature_class"] for f in files).items())),
            "duplicate_groups": [paths for paths in by_hash.values() if len(paths) > 1],
            "files": files}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--exclude-dir", action="append", default=[])
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    output = args.output.resolve()
    if not root.is_dir() or output.is_relative_to(root):
        parser.error("Root must be a directory; output must be outside the input root")
    report = inventory(root, {name.casefold() for name in args.exclude_dir})
    report["tool_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in
                      ("file_count", "total_bytes", "extension_counts", "signature_counts", "duplicate_groups")}, indent=2))


if __name__ == "__main__":
    main()
