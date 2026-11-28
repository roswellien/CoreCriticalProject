"""Rewrite a pack's `files` table from the files actually in its folder.

Usage, from the repository root:
    python tools/packs/fill_file_table.py <pack folder>

Run it after changing any file in an example pack, so the sizes and SHA-256 hashes in
pack.json match again. It lists every file except pack.json and keeps a `format` an
entry already had. Do not run it on the deliberately broken example packs whose point
is a wrong table (see tests/fixtures/packs/README.md).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

MANIFEST_NAME = "pack.json"


def build_file_table(pack_folder: Path, previous_table: dict) -> dict:
    table = {}
    for path in sorted(pack_folder.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(pack_folder).as_posix()
        if relative == MANIFEST_NAME:
            continue
        content = path.read_bytes()
        entry = {"sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)}
        previous_format = previous_table.get(relative, {}).get("format")
        if previous_format is not None:
            entry["format"] = previous_format
        table[relative] = entry
    return table


def main(arguments: list[str]) -> int:
    if len(arguments) != 1:
        print(__doc__)
        return 2
    pack_folder = Path(arguments[0])
    manifest_path = pack_folder / MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"] = build_file_table(pack_folder, manifest.get("files", {}))
    # newline="\n" keeps the file identical on Windows and Linux.
    with manifest_path.open("w", encoding="utf-8", newline="\n") as output:
        json.dump(manifest, output, indent=2)
        output.write("\n")
    print(f"{manifest_path}: {len(manifest['files'])} files listed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
