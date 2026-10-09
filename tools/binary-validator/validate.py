#!/usr/bin/env python3
"""Validate a user-supplied MW3 executable against an exact manifest identity."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
from pe import ManifestError, PEError, UnsupportedBinaryError, load_manifest, read_binary, validate_identity  # noqa: E402

DEFAULT_MANIFEST = Path(__file__).resolve().parents[2] / "games/mw3/config/supported-binaries.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path, help="local user-supplied installed MW3 executable")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--json", action="store_true", help="emit the verified identity as JSON")
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest(args.manifest)
        record = validate_identity(read_binary(args.binary), manifest)
        if args.json:
            print(json.dumps({"status": "verified_identity", "game": manifest["game"], "binary": record}, indent=2, sort_keys=True))
        else:
            print(f"Verified binary identity: {record['id']} ({record['title']})")
            print(f"SHA-256: {record['sha256']}")
        return 0
    except UnsupportedBinaryError as error:
        print(f"validation failed: {error}", file=sys.stderr)
        return 2
    except (ManifestError, PEError) as error:
        print(f"invalid input: {error}", file=sys.stderr)
        return 3
    except OSError as error:
        print(f"I/O failed: {error}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(main())
