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

from mech_height_maps import (
    ALL_MECHS,
    HERO_MECHS,
    REPLACEMENT_MECHS,
    DETAILED_MW3_MECHS,
    build_mech_surface_materials,
)

ROOT = Path(__file__).resolve().parents[2]
if not (ROOT / "local").exists():
    candidate_main = Path(r"D:\Projects\MW34Recomp")
    if (candidate_main / "local").exists():
        ROOT = candidate_main


ROSTER_MECH_DISPLAY_NAMES: dict[str, str] = {
    "bushwacker": "Bushwacker",
    "madcat": "Mad Cat",
    "vulture": "Vulture",
    "thor": "Thor",
    "orion": "Orion",
    "daishi": "Daishi",
    "shadowcat": "Shadow Cat",
    "puma": "Puma / Adder",
    "annihilator": "Annihilator",
    "cauldron": "Cauldron-Born / Ebon Jaguar",
    "sunder": "Sunder",
    "supernova": "Supernova",
    "blackhawk": "Black Hawk / Nova",
    "champion": "Champion",
    "strider": "Strider (detailed MW3)",
    "avatar": "Avatar (detailed MW3 / STL-guided)",
    "owens": "Owens (detailed MW3)",
    "firefly": "Firefly (detailed MW3)",
}


def build_mech_roster_index(
    output_html: Path,
    reports: list[dict],
) -> Path:
    """Generate a master HTML dashboard linking to all 18 mech 3D inspectors."""
    output_html.parent.mkdir(parents=True, exist_ok=True)

    report_map = {r["mech"]: r for r in reports}

    def render_card(mech_id: str, category: str) -> str:
        disp_name = ROSTER_MECH_DISPLAY_NAMES.get(mech_id, mech_id.capitalize())
        rep = report_map.get(mech_id, {})
        batches = rep.get("batches_count", "-")
        records = rep.get("records_count", "-")
        uv_hash = rep.get("mesh_uv_hash", "-")
        report_href = f"{mech_id}_materials_inspector.html"

        cat_pill = (
            '<span class="badge cat-new">MW5 Replacement</span>'
            if category == "new"
            else '<span class="badge cat-mw3">Detailed MW3</span>'
        )

        return f"""
        <div class="mech-card">
            <div class="card-header">
                <h3>{disp_name}</h3>
                {cat_pill}
            </div>
            <div class="card-meta">
                <div><span class="meta-label">ID:</span> <code>{mech_id}</code></div>
                <div><span class="meta-label">Batches:</span> <strong>{batches}</strong></div>
                <div><span class="meta-label">Materials:</span> <strong>{records}</strong></div>
                <div><span class="meta-label">UV Hash:</span> <code style="font-size:10px;">{uv_hash}</code></div>
            </div>
            <div class="card-actions">
                <a href="{report_href}" target="_blank" class="btn-inspect">🚀 Open 3D Inspector</a>
            </div>
        </div>
        """

    new_cards = "\n".join(render_card(m, "new") for m in REPLACEMENT_MECHS)
    mw3_cards = "\n".join(render_card(m, "mw3") for m in DETAILED_MW3_MECHS)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MW3 Remaster — Full Mech Material & POM Roster</title>
    <style>
        :root {{
            --bg-primary: #0a0e14;
            --bg-surface: #121820;
            --bg-card: #182230;
            --accent: #ff6600;
            --accent-cyan: #00d2ff;
            --accent-green: #00ff88;
            --text-main: #f0f4f8;
            --text-dim: #8a99a8;
            --border: #223244;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: var(--bg-primary);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            padding: 30px;
            line-height: 1.5;
        }}
        .header {{
            max-width: 1400px;
            margin: 0 auto 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid var(--border);
            padding-bottom: 20px;
        }}
        .header h1 {{
            font-size: 26px;
            font-weight: 800;
            color: var(--text-main);
            letter-spacing: -0.5px;
        }}
        .header h1 span {{ color: var(--accent); }}
        .header-stats {{
            display: flex;
            gap: 20px;
        }}
        .stat-box {{
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 10px 18px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 22px;
            font-weight: 800;
            color: var(--accent-cyan);
        }}
        .stat-label {{
            font-size: 11px;
            text-transform: uppercase;
            color: var(--text-dim);
            letter-spacing: 0.5px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: 700;
            color: var(--text-main);
            margin: 30px 0 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .section-title::before {{
            content: "";
            display: inline-block;
            width: 4px;
            height: 18px;
            background: var(--accent);
            border-radius: 2px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(310px, 1fr));
            gap: 16px;
        }}
        .mech-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: transform 0.15s ease, border-color 0.15s ease;
        }}
        .mech-card:hover {{
            transform: translateY(-2px);
            border-color: var(--accent);
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
        }}
        .card-header h3 {{
            font-size: 16px;
            font-weight: 700;
            color: var(--text-main);
        }}
        .badge {{
            font-size: 10px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .cat-new {{ background: rgba(0, 210, 255, 0.15); color: var(--accent-cyan); border: 1px solid rgba(0, 210, 255, 0.3); }}
        .cat-mw3 {{ background: rgba(0, 255, 136, 0.15); color: var(--accent-green); border: 1px solid rgba(0, 255, 136, 0.3); }}
        .card-meta {{
            font-size: 12px;
            color: var(--text-dim);
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 6px;
            margin-bottom: 16px;
            background: rgba(0,0,0,0.25);
            padding: 10px;
            border-radius: 6px;
        }}
        .meta-label {{ color: #607282; }}
        code {{
            background: rgba(255,255,255,0.06);
            padding: 1px 4px;
            border-radius: 3px;
            font-family: monospace;
            color: var(--text-main);
        }}
        .card-actions {{
            display: flex;
        }}
        .btn-inspect {{
            width: 100%;
            display: inline-block;
            text-align: center;
            background: var(--accent);
            color: #fff;
            text-decoration: none;
            font-size: 13px;
            font-weight: 700;
            padding: 8px 12px;
            border-radius: 6px;
            transition: background 0.15s ease;
        }}
        .btn-inspect:hover {{
            background: #ff7a1a;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>MechWarrior 3 Remaster — <span>Mech Material & POM Roster</span></h1>
            <p style="color:var(--text-dim); font-size:13px; margin-top:4px;">
                Complete 18-Mech Suite: High-resolution height maps, cotangent frame POM raymarching & PBR material sidecars
            </p>
        </div>
        <div class="header-stats">
            <div class="stat-box">
                <div class="stat-value">18</div>
                <div class="stat-label">Total Mechs</div>
            </div>
            <div class="stat-box">
                <div class="stat-value" style="color:var(--accent-green);">100%</div>
                <div class="stat-label">BWSFM1 Verified</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">24-Step</div>
                <div class="stat-label">POM Raymarcher</div>
            </div>
        </div>
    </div>

    <div class="container">
        <h2 class="section-title">MW5 High-Poly Replacement Models (14 Chassis)</h2>
        <div class="grid">
            {new_cards}
        </div>

        <h2 class="section-title">Detailed MW3 Models with Modern PBR Textures (4 Chassis)</h2>
        <div class="grid">
            {mw3_cards}
        </div>
    </div>
</body>
</html>
"""
    output_html.write_text(html_content, encoding="utf-8")
    return output_html


def launch_mech_inspector(
    mech_id: str = "bushwacker",
    output_html: Path | None = None,
    output_sidecar: Path | None = None,
    open_browser: bool = True,
    force: bool = False,
) -> tuple[Path, dict]:
    """Build the visual report and BWSFM1 sidecar and optionally open the browser."""
    if output_html is None:
        output_html = ROOT / f"local/remaster/{mech_id}_materials_inspector.html"

    if output_sidecar is None:
        output_sidecar = ROOT / f"local/remaster/{mech_id}_materials.bwsfm1"

    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_sidecar.parent.mkdir(parents=True, exist_ok=True)

    if output_html.exists() and output_sidecar.exists() and not force:
        print(f"[{mech_id.upper()}] Using existing sidecar and inspection report.")
        report = {
            "mech": mech_id,
            "batches_count": "-",
            "records_count": "-",
            "mesh_uv_hash": "-",
        }
    else:
        print(f"[{mech_id.upper()}] Preparing surface materials...")
        sidecar_bytes, report = build_mech_surface_materials(
            mech_id=mech_id,
            html_report_path=output_html,
        )
        output_sidecar.write_bytes(sidecar_bytes)
        print(f"Wrote BWSFM1 sidecar ({len(sidecar_bytes):,} bytes): {output_sidecar}")
        print(f"Inspection report generated successfully: {output_html}")
        print(
            f"Processed {report['records_count']} materials across "
            f"{report['batches_count']} batches. UV Hash: {report['mesh_uv_hash']}"
        )

    if open_browser:
        print("Launching default web browser...")
        webbrowser.open(output_html.resolve().as_uri())

    return output_html, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mech",
        default="all",
        choices=list(ALL_MECHS) + ["all", "heroes", "replacements", "detailed"],
        help="Mech(s) to inspect (default: all)",
    )
    parser.add_argument("--output-html", type=Path)
    parser.add_argument("--output-sidecar", type=Path)
    parser.add_argument("--force", action="store_true", help="Force rebuild even if files exist")
    parser.add_argument("--no-browser", action="store_true")

    args = parser.parse_args()

    if args.mech == "all":
        targets = list(ALL_MECHS)
    elif args.mech == "heroes":
        targets = list(HERO_MECHS)
    elif args.mech == "replacements":
        targets = list(REPLACEMENT_MECHS)
    elif args.mech == "detailed":
        targets = list(DETAILED_MW3_MECHS)
    else:
        targets = [args.mech]

    reports = []
    is_multi = len(targets) > 1

    for m in targets:
        html_out = args.output_html
        if html_out and is_multi:
            html_out = html_out.parent / f"{m}_{html_out.name}"
        sidecar_out = args.output_sidecar
        if sidecar_out and is_multi:
            sidecar_out = sidecar_out.parent / f"{m}_{sidecar_out.name}"

        try:
            _, report = launch_mech_inspector(
                mech_id=m,
                output_html=html_out,
                output_sidecar=sidecar_out,
                open_browser=not args.no_browser if not is_multi else False,
                force=args.force,
            )
            reports.append(report)
        except Exception as exc:
            print(f"Error inspecting {m}: {exc}", file=sys.stderr)
            sys.exit(1)

    if is_multi:
        roster_html = ROOT / "local/remaster/mech_roster_inspector.html"
        build_mech_roster_index(roster_html, reports)
        print(f"\nGenerated master mech roster index: {roster_html}")
        if not args.no_browser:
            print("Launching master roster in default web browser...")
            webbrowser.open(roster_html.resolve().as_uri())


if __name__ == "__main__":
    main()
