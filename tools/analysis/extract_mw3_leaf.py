#!/usr/bin/env python3
"""Extract one hash-bound reviewed MW3 leaf to private local research storage.

No executable is loaded or run. This is not a general PE loader or lifter.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

from pe import PEImage, load_manifest, read_binary, validate_identity

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "games/mw3/config/supported-binaries.json"
CONTRACT = ROOT / "games/mw3/symbols/sub_00409ed0.json"
# Independently pin the reviewed identity: editing a metadata file cannot admit
# different code or extend the extraction to an unreviewed range.
REVIEWED = {
    "schema_version": 1,
    "profile_id": "mw3-us-1-2-retail",
    "image_sha256": "95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf",
    "label": "sub_00409ED0",
    "entry_va": 0x409ED0,
    "entry_rva": 0x9ED0,
    "file_offset": 0x92D0,
    "size_bytes": 22,
    "slice_sha256": "560c17c210dd7fedd7de601f42570c2a0473fa71962c13cfa85a005509a77c65",
    "review_status": "static_contract_reviewed_execution_pending",
    "dossier": "../docs/first-function.md",
}


def private_directory(path: Path) -> Path:
    path = path.resolve()
    if not any(
        path.is_relative_to((ROOT / name).resolve())
        for name in ("reports", "local", "recomp/generated")
    ):
        raise ValueError("output must be under ignored reports/, local/, or recomp/generated/")
    return path


def extract(binary: Path, contract: Path, output: Path) -> dict:
    output = private_directory(output)
    contract_bytes = contract.read_bytes()
    metadata = json.loads(contract_bytes.decode("utf-8"))
    if metadata != REVIEWED:
        raise ValueError("slice metadata differs from the reviewed contract")
    data = read_binary(binary)
    image = PEImage(data)
    identity = validate_identity(data, load_manifest(MANIFEST), image)
    if (
        identity["id"] != REVIEWED["profile_id"]
        or hashlib.sha256(data).hexdigest() != REVIEWED["image_sha256"]
    ):
        raise ValueError("input differs from the reviewed MW3 image")
    rva, size = REVIEWED["entry_rva"], REVIEWED["size_bytes"]
    if image.image_base + rva != REVIEWED["entry_va"]:
        raise ValueError("guest address differs from reviewed VA")
    offset, _ = image.rva_range(rva, size)
    if offset != REVIEWED["file_offset"]:
        raise ValueError("raw/virtual slice mapping differs from review")
    sections = [
        s
        for s in image.sections
        if s["virtual_address"] <= rva and rva + size <= s["virtual_address"] + s["virtual_size"]
    ]
    if (
        len(sections) != 1
        or not sections[0]["executable"]
        or not sections[0]["readable"]
        or sections[0]["writable"]
    ):
        raise ValueError("slice must have reviewed read/execute section permissions")
    code = image.read(offset, size)
    if hashlib.sha256(code).hexdigest() != REVIEWED["slice_sha256"]:
        raise ValueError("slice hash differs from review")
    destination = output / "sub_00409ed0.bin"
    record_path = output / "slice.json"
    if binary.resolve() in (destination, record_path) or contract.resolve() in (
        destination,
        record_path,
    ):
        raise ValueError("output must differ from input")
    record = {
        **REVIEWED,
        "binary_path": str(binary.resolve()),
        "contract_sha256": hashlib.sha256(contract_bytes).hexdigest(),
        "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "section": sections[0]["name"],
        "execution": "not attempted",
        "notice": "Private game-derived slice; no relocation, imports, TLS or entry point initialization performed.",
    }
    output.mkdir(parents=True, exist_ok=True)
    # Publish the evidence record last. Invalid input writes no new artifacts.
    for path, contents in (
        (destination, code),
        (record_path, (json.dumps(record, indent=2) + "\n").encode()),
    ):
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=output, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(contents)
            os.replace(temporary, path)
            temporary = None
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("--contract", type=Path, default=CONTRACT)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports/mw3-recon")
    args = parser.parse_args()
    try:
        extract(args.binary, args.contract, args.output_dir)
        print("Extracted reviewed sub_00409ED0; game execution remains pending.")
        return 0
    except (OSError, ValueError) as error:
        print(f"slice admission failed: {error}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
