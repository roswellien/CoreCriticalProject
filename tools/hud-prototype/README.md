# HUD component fidelity prototype

Builds an isolated, self-contained HTML/Canvas demonstration and 31 SVG component
remakes using the admitted original reader/image archives. It does not modify
game assets, install a hook or consume game telemetry. The original 53 source
components remain embedded alongside source-informed vector remakes. Artwork
coordinates and known logical sizes are retained; new numeral styling and
some shapes/colors are design candidates requiring visual review.

```powershell
python tools/hud-prototype/prepare.py --output-dir local/work-ahead/my-hud-prototype
```

Requires the existing checked `build/m4-assets-parser-r1/mw34_m4_assets.exe` or
`--parser PATH`. Original `reader.zbd` and `rimage.zbd` identities must match.
Output must be a fresh directory below ignored `local/work-ahead/`.

Open `review.html` to compare regenerated text/vectors, source artwork and a
nonuniform-stretch control at 640×480, 1920×1440, 2560×1440 or 3440×1440. Values
and background are authored. Source-mode text is an illustrative 10-pixel Arial
raster, not captured original-game text. Export saves the selected canvas as PNG.
HUD size can be reduced to 75% of its output-height-based scale; larger sizes
are excluded because the recovered geometry has not been redesigned for them.

Offline validation executes the actual JS renderer against native Skia without
browser automation. Supply the bundled `@napi-rs/canvas` directory returned by
`load_workspace_dependencies`, or an installed equivalent:

```powershell
node tools/hud-prototype/verify.cjs local/work-ahead/my-hud-prototype C:/path/to/node_modules/@napi-rs/canvas
```

Checks 24 resolution/size/render-mode combinations, edge/center anchors, sprite
and panel bounds, 31 vector logical sizes, invalid viewport rejection and
telemetry endpoints. Produces six PNGs and a private hash-bearing validation
receipt. Existing output PNGs/receipts are rejected. Skia's Arial rasterization
is distinct from original Windows GDI; neither these checks nor the HTML's
layout checks establish browser interaction or game integration correctness.

The [HUD investigation](../../docs/mw3-hud-fidelity-investigation.md) records the
original text-cache path and required native integration boundaries.
