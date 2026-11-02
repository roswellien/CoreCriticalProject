"""One-click launcher for the MW3 Terrain Material & Height Map Inspector.

Automatically locates regional normal maps and colour banks, generates a self-contained
interactive 3D WebGL inspection report, and opens it directly in the default browser.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import webbrowser

from prepared_environment_packs import REGIONS
from terrain_height_maps import build_region_terrain_sidecar

ROOT = Path(__file__).resolve().parents[2]


def find_default_manifest(region: str) -> Path | None:
    """Scan candidate locations for the regional normal manifest."""
    candidates = [
        ROOT / f"local/asset-packs/environments-20261021-r1/prepared-{region}/environment/authored.txt",
        ROOT / f"local/work-ahead/environment-packs-20261021-r1/prepared-trials/{region}/authored.txt",
        ROOT / f"local/remaster/environment/{region}/authored.txt",
        ROOT / f"local/remaster/{region}/authored.txt",
    ]
    for path in candidates:
        if path.exists():
            return path

    # Fallback glob in local/
    local_dir = ROOT / "local"
    if local_dir.exists():
        matches = list(local_dir.glob(f"**/*{region}*/**/authored.txt"))
        if matches:
            return matches[0]
        matches_normals = list(local_dir.glob(f"**/*{region}*/**/authored-normals.txt"))
        if matches_normals:
            return matches_normals[0]

    return None


def launch_inspector(
    region: str = "training",
    manifest_path: Path | None = None,
    output_html: Path | None = None,
    contact_sheets_dir: Path | None = None,
    open_browser: bool = True,
) -> Path:
    """Build the visual report and optionally launch the browser."""
    if manifest_path is None:
        manifest_path = find_default_manifest(region)
        if manifest_path is None:
            raise FileNotFoundError(
                f"Could not find a normal map manifest for region '{region}'. "
                f"Please ensure environment packs exist in local/ or specify --manifest."
            )

    if output_html is None:
        output_html = ROOT / f"local/remaster/{region}_terrain_inspector.html"

    print(f"Preparing terrain inspection for region: {region}")
    print(f"Using normals manifest: {manifest_path}")

    pages = [
        manifest_path.parent / line
        for line in manifest_path.read_text().splitlines()[1:]
        if line
    ]

    output_html.parent.mkdir(parents=True, exist_ok=True)
    _sidecar_bytes, report = build_region_terrain_sidecar(
        region,
        pages,
        html_report_path=output_html,
        contact_sheets_dir=contact_sheets_dir,
    )

    print(f"Inspection report generated successfully: {output_html}")
    print(f"Processed {report.get('records_count', 0)} materials.")

    if open_browser:
        print("Launching default web browser...")
        webbrowser.open(output_html.resolve().as_uri())

    return output_html


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--region",
        default="training",
        choices=list(REGIONS.keys()),
        help="Campaign region to inspect (default: training)",
    )
    parser.add_argument("--manifest", type=Path, help="Explicit path to authored.txt")
    parser.add_argument("--output", type=Path, help="Explicit path for output HTML")
    parser.add_argument("--contact-sheets-dir", type=Path, help="Optional directory for PNG contact sheets")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")

    args = parser.parse_args()

    try:
        launch_inspector(
            region=args.region,
            manifest_path=args.manifest,
            output_html=args.output,
            contact_sheets_dir=args.contact_sheets_dir,
            open_browser=not args.no_browser,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
