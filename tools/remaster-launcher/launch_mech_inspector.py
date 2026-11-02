"""One-click launcher for the MW3 Mech Material & Height Map Inspector.

Extracts genuine replacement mech normal maps and albedo textures, derives
calibrated armor height maps, generates self-contained interactive 3D WebGL
reports, and opens them in the default browser.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import webbrowser

from mech_height_maps import HERO_MECHS, build_mech_surface_materials

ROOT = Path(__file__).resolve().parents[2]
if not (ROOT / "local").exists():
    candidate_main = Path(r"D:\Projects\MW34Recomp")
    if (candidate_main / "local").exists():
        ROOT = candidate_main


def launch_mech_inspector(
    mech_id: str = "bushwacker",
    output_html: Path | None = None,
    output_sidecar: Path | None = None,
    open_browser: bool = True,
) -> Path:
    """Build the visual report and BWSFM1 sidecar and optionally open the browser."""
    if output_html is None:
        output_html = ROOT / f"local/remaster/{mech_id}_materials_inspector.html"

    if output_sidecar is None:
        output_sidecar = ROOT / f"local/remaster/{mech_id}_materials.bwsfm1"

    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_sidecar.parent.mkdir(parents=True, exist_ok=True)

    print(f"Preparing surface materials for {mech_id.capitalize()}...")
    sidecar_bytes, report = build_mech_surface_materials(
        mech_id=mech_id,
        html_report_path=output_html,
    )

    output_sidecar.write_bytes(sidecar_bytes)
    print(f"Wrote BWSFM1 sidecar ({len(sidecar_bytes):,} bytes): {output_sidecar}")
    print(f"Inspection report generated successfully: {output_html}")
    print(f"Processed {report['records_count']} materials across {report['batches_count']} batches.")

    if open_browser:
        print("Launching default web browser...")
        webbrowser.open(output_html.resolve().as_uri())

    return output_html


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mech",
        default="bushwacker",
        choices=list(HERO_MECHS) + ["all"],
        help="Hero mech to inspect (default: bushwacker)",
    )
    parser.add_argument("--output-html", type=Path)
    parser.add_argument("--output-sidecar", type=Path)
    parser.add_argument("--no-browser", action="store_true")

    args = parser.parse_args()

    targets = list(HERO_MECHS) if args.mech == "all" else [args.mech]

    for m in targets:
        html_out = args.output_html
        if html_out and args.mech == "all":
            html_out = html_out.parent / f"{m}_{html_out.name}"
        sidecar_out = args.output_sidecar
        if sidecar_out and args.mech == "all":
            sidecar_out = sidecar_out.parent / f"{m}_{sidecar_out.name}"

        try:
            launch_mech_inspector(
                mech_id=m,
                output_html=html_out,
                output_sidecar=sidecar_out,
                open_browser=not args.no_browser,
            )
        except Exception as exc:
            print(f"Error inspecting {m}: {exc}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
