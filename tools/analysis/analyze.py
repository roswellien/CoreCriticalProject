#!/usr/bin/env python3
"""Write metadata-only reconnaissance for a user-provided PE32/i386 image."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from pe import (
    ManifestError,
    PEError,
    PEImage,
    UnsupportedBinaryError,
    load_manifest,
    read_binary,
    validate_identity,
)

DEFAULT_MANIFEST = Path(__file__).resolve().parents[2] / "games/mw3/config/supported-binaries.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path, help="local user-supplied executable")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, help="write JSON to a local file; default: stdout")
    parser.add_argument(
        "--require-supported",
        action="store_true",
        help="fail unless the full manifest identity matches",
    )
    args = parser.parse_args(argv)
    try:
        if args.output and args.output.resolve() in {
            args.binary.resolve(),
            args.manifest.resolve(),
        }:
            raise ValueError("output must differ from input binary and manifest")
        data = read_binary(args.binary)
        image = PEImage(data)
        metadata = image.metadata()
        manifest = load_manifest(args.manifest)
        try:
            record = validate_identity(data, manifest, image)
            support = {"status": "verified_identity", "id": record["id"], "title": record["title"]}
        except UnsupportedBinaryError as error:
            if args.require_supported:
                print(f"validation failed: {error}", file=sys.stderr)
                return 2
            support = {"status": "unknown_binary", "reason": str(error)}
        report = {
            "report_schema_version": 1,
            "tool": "MW34 RECOMP PE reconnaissance",
            "filename": args.binary.name,
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "support": support,
            "pe": metadata,
            "notice": "Metadata reconnaissance does not establish game version, successful recompilation, or runtime compatibility.",
        }
        output = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output, encoding="utf-8")
        else:
            print(output, end="")
        return 0
    except (PEError, ManifestError, ValueError) as error:
        print(f"analysis failed: {error}", file=sys.stderr)
        return 3
    except OSError as error:
        print(f"I/O failed: {error}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(main())
