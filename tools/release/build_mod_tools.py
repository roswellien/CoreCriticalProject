"""Build a local Mod Tools source-preview ZIP from an explicit reviewed file list.

No recursive packaging: new game files, exports, geometry and caches cannot
enter this archive just because they appeared beside the editor's source.
This creates a review candidate only; it does not publish a GitHub release.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path(__file__).with_name("mod-tools-files.json")
ARCHIVE_NAME = "mw3-mod-tools-source-preview-2026-10-21.zip"


def package_entries(root: Path, manifest: Path = MANIFEST) -> dict[str, bytes]:
    """Read listed inputs; reject path escapes, duplicate names and missing files."""
    document = json.loads(manifest.read_text(encoding="utf-8"))
    if document.get("schema_version") != 1:
        raise ValueError("Unsupported package file-list schema.")
    entries = {}
    for name in document["files"]:
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or "\\" in name or ":" in name:
            raise ValueError(f"Invalid package path: {name}")
        path = (root / relative).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            raise ValueError(f"Missing or external package input: {name}")
        if name in entries:
            raise ValueError(f"Duplicate package input: {name}")
        entries[name] = path.read_bytes()
    return entries


def build(output_dir: Path, *, root: Path = ROOT, manifest: Path = MANIFEST) -> Path:
    """Write a fresh source ZIP, content inventory and SHA-256 checksum file.

    Explicit inputs and third-party pins are checked before creating the ZIP.
    Sorted entries, fixed timestamps and file-mode metadata make repeated builds
    reproducible with the same inputs/tooling. Outputs remain review candidates;
    this function neither uploads them nor asserts editor/gameplay readiness.
    """
    entries = package_entries(root, manifest)
    # Verify third-party source identities, not just the presence of a notice.
    browser_dir = "games/mw3/mod-tools/editor/web/static/js/"
    provenance = json.loads(entries[browser_dir + "third-party.json"])
    for item in provenance["files"]:
        if hashlib.sha256(entries[browser_dir + item["file"]]).hexdigest() != item["sha256"]:
            raise ValueError(f"Third-party file changed: {item['file']}")
    inventory = {
        "schema_version": 1,
        "package": "Mod Tools source preview; no game runtime or game content",
        "files": [
            {"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            for name, data in sorted(entries.items())
        ],
    }
    entries["PACKAGE-CONTENTS.json"] = (json.dumps(inventory, indent=2) + "\n").encode()
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / ARCHIVE_NAME
    checksum = output_dir / "SHA256SUMS.txt"
    if archive.exists() or checksum.exists():
        raise ValueError("Candidate files already exist; choose a fresh output directory.")
    with archive.open("xb") as stream:
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as package:
            for name, data in sorted(entries.items()):
                info = zipfile.ZipInfo(name, date_time=(2026, 10, 21, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                package.writestr(info, data)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="ascii")
    return archive


def main() -> int:
    """Build a fresh local source candidate; never upload or publish a release."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Fresh local candidate folder, normally under reports/",
    )
    args = parser.parse_args()
    try:
        print(build(args.output_dir))
        return 0
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        parser.exit(1, f"Package build failed: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
