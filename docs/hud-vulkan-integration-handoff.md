# HUD fidelity handoff for Vulkan integration

Prepared 2026-10-10. Workspace: `D:\Projects\MW34Recomp`.

## Starting state

The HUD upgrade is a **standalone component prototype**, not an integrated game
HUD or a Vulkan implementation. It demonstrates output-resolution text,
source-informed vector remakes and uniform widescreen layout. No game executable
or installed archive was modified. Gameplay values, visibility and rendering
order still need to come from recovered game behavior.

Begin with the source renderer and generated model below. Do not port the
illustrative scene wholesale as though it were the original HUD.

## Files and locations

| Location under `D:\Projects\MW34Recomp` | Contents / use |
| --- | --- |
| `tools\hud-prototype\prepare.py` | Identity-checked package builder; `vector_models()` contains the authored geometry; `svg()` exports the same models to SVG |
| `tools\hud-prototype\renderer.js` | Actual Canvas prototype; `layout()`, `vector()`, `sprite()`, `text()` and `scene()` are the porting references |
| `tools\hud-prototype\review.html` | Review UI template; this file alone lacks generated model data |
| `tools\hud-prototype\verify.cjs` | Offline native Skia execution/validation of that JS renderer |
| `tools\hud-prototype\README.md` | Preparation and validation instructions |
| `local\work-ahead\hud-fidelity-v3\review.html` | Latest generated self-contained interactive preview |
| `local\work-ahead\hud-fidelity-v3\components.json` | Main integration input: original sprites, vector models, font properties, original layouts |
| `local\work-ahead\hud-fidelity-v3\*.svg` | 31 individually exported vector component candidates |
| `local\work-ahead\hud-fidelity-v3\manifest.json` | Source identities, generator hashes and initial output hashes |
| `local\work-ahead\hud-fidelity-v3\validation.json` | Passed offline checks and hashes of six rendered scene PNGs |
| `local\work-ahead\hud-fidelity-v3\comparison-details.png` | Pixel-scale side-by-side visual comparison |
| `local\work-ahead\hud-fidelity-v3\enhanced-3440x1440.png` | Full ultrawide candidate scene; also a 1920×1440 version |
| `local\work-ahead\hud-fidelity-v3\source-*.png`, `stretch-*.png` | Enlarged-component and nonuniform-stretch controls; text is illustrative |
| `local\work-ahead\hud-fidelity-v3\binary-trace-receipt.json` and `*-disassembly.txt` | Hash-bound focused original-binary static evidence |
| `docs\mw3-hud-fidelity-investigation.md` | Full font/resource findings, evidence IDs, text-cache recovery and limitations |
| `tools\asset-inventory\prepare_hud_research.py` | Earlier source export and isolated font-quality experiment |
| `local\work-ahead\hud-research-v1\` | Original 53 PNG exports, parsed font/layout inventory, GDI probe, REA evidence and quality-only archive candidate |

The `local` directories contain proprietary source-derived material and remain
ignored. Do not commit `components.json`, embedded original sprite data, generated
review HTML, source PNGs, archives or disassembly to the public repository.
Authored prototype source and investigation documentation were still untracked
when this handoff was prepared; they exist locally but have not been committed.
Retain unrelated existing workspace changes.

## What was made

31 source-informed SVG/vector candidates, preserving each source's **logical**
width and height:

- 16 directional arrows: ally, enemy (`en`), navigation (`nav`) and MFB, each
  in four directions.
- Four frames: speed, altitude, fuel and coolant.
- One heat meter.
- Three small mech radar markers: ally, enemy and other.
- Two weapon indicators: chain and selection.
- Five reticles: sensor plus four zoom states.

The four zoom variants currently share identical authored geometry and color.
They are placeholders for state-specific appearance, not four faithfully
recovered state designs. Some other silhouettes/colors and regenerated gauge
numerals also differ from the source; visual approval remains open.

All 53 decoded original components are included for reference/fallback: 52
`hud_` sprites and `sensor_reticule`. Source pixels retain stored dimensions,
row order and decoded alpha. Fonts come from 51 original Windows-font
definitions, mainly Arial and Lucida Console. No font files were bundled;
SVG text and the demo rely on the system's Arial or a fallback. A portable
renderer must deliberately resolve font availability and metrics.

The demo draws fresh text at output pixel density instead of enlarging a small
text raster. Its procedural compass, heat fill, panel outlines, synthetic
background and sample values are demonstration content, not recovered assets
or real game telemetry.

## Generated model schema

`components.json` contains:

```text
resources[name] = { index, width, height, source: "data:image/png;base64,..." }
vectors[name]   = { width, height, shapes: [...] }
fonts[name]     = { face: [...], height: [...], color: [...], ... }
layouts[label]  = { GAUGES: {...}, MFD: {...}, TARGET: {...}, ... }
```

Shape kinds are `line`, `polygon`, `rect` and `text`. Colors are CSS hex values;
coordinates, widths and text sizes are logical units. Text shapes have baseline
X/Y, size and value. Prototype polygons are filled; lines have a stroke width.
`prepare.py` and `renderer.js` are the authoritative shape schema references.

## Layout and font contracts to preserve

Prototype layout uses the recovered 640×480 layout as its logical reference:

```text
scale = min(outputWidth / 640, outputHeight / 480) * userScale
userScale = 0.75 .. 1.0
left-anchored X  = sourceX * scale
right-anchored X = outputWidth - (640 - sourceX) * scale
gauge Y         = sourceY * scale
reticle center  = (outputWidth / 2, outputHeight / 2)
```

The gauge-side selection `sourceX >= 320` is a prototype heuristic, not a
recovered universal anchoring rule. Port known elements to explicit anchors.
MFD/TARGET use bottom distances of 110 logical units, panels are 75×100,
WEAPONS uses a right distance of 110 and top distance of 30, and the compass
is horizontally centered. At 3440×1440/default size, scale is 3 and reticle
center is 1720,720. The original archive also has five other resolution layouts;
use them to check layout assumptions before treating the prototype as canonical.

Keep logical destination size separate from physical texture/glyph dimensions.
A 4× raster must not make the component 4× larger. Preserve original logical
text advances, baseline, clipping, alignment, colors and shadows. Signed GDI
font heights matter: `mech_string` and weapon strings use Arial -10,
`wepif_font` uses +10, `hud_messages` +14 and `hud_htal` +16. Positive cell
height and negative character height are not interchangeable em sizes.

The earlier `quality=4` candidate is **not a proven upgrade**: authored GDI
tests lost smoothing at original small sizes in this environment. Prefer fresh
output-density coverage rather than applying that archive experiment as the
integration solution.

## Original-game rendering investigation entry points

These are static observations for MW3 U.S. 1.2 only, executable SHA-256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`:

- `0x516FF0`: font definition loader, including numeric `quality` property.
- `0x517250`: default font state; out precision 4, quality 1.
- `0x517280`: CreateFontIndirectA wrapper.
- `0x517680`: named Windows font acquisition.
- `0x43BB80`: reads `hud.zrd`, selects original resolution layout.
- `0x5A0790..0x5A0D16`: statically identified text preparation/cache sequence.
  String at object+0x34, HFONT at +0x258, image object at +0x248.
- `0x5A088F`: DrawTextA measurement; `0x5A0B42`/`0x5A0BB2`: shadow/main drawing.
- Logical measurement fields include +0x460/+0x464 and +0x490..+0x49C.
- `0x72F394`/`0x72F398`: image/DC service slots assigned to
  `0x577BA0`/`0x577BD0` at the examined initialization sites. The latter copies
  nonzero 16-bit bitmap words into the packed image buffer. Image dimensions
  are signed shorts at +4/+6 and pixel storage is at +0x10.

Do not assume those service assignments cover all runtime modes or that the
cache's downstream HUD draw, format negotiation and synchronization are already
recovered. Preserve guest structure layouts; attach enhanced physical texture
metadata on the host side instead of enlarging guest dimensions blindly.

## Suggested first Vulkan integration task

This is proposed implementation work, not a claim that it already exists:

1. Read the investigation and current renderer contracts. Existing public entry
   points are `tools\vulkan-probe\raster.cpp`, `replay.cpp`, `replay_scene.hpp`
   and their shaders/CMake targets. `runtime\graphics\README.md` still reports
   no integrated game renderer. If another branch/chat has a newer renderer,
   inspect that implementation and its repository instructions first.
2. Add an isolated HUD draw interface: component ID, logical destination,
   viewport/clip, color, ordered layer and text/font ID. Keep it separate from
   world projection and original guest ABI storage.
3. First upload a few vector assets rasterized to RGBA at the requested density,
   or translate model primitives into triangles. Vulkan does not consume SVG
   directly. Glyph coverage plus textured quads is a practical first text path;
   preserve measurement semantics separately from rasterization density.
4. Implement a final-resolution screen-space HUD pass. Choose and consistently
   apply straight or premultiplied alpha, font coverage, sampler addressing and
   color-space handling. Keep depth behavior explicit and test thin geometry,
   transparent edges and atlas padding. These choices are not settled by the
   Canvas prototype or original RGB565 decoding.
5. Reproduce the isolated prototype at 4:3, 16:9 and ultrawide. Then feed real
   recovered HUD state and validate visibility, localization, clipping, heat,
   weapons, heading, radar and cockpit masks against the original game.
6. Recover presentation ordering and suppress the original HUD contribution
   before enabling replacement in game. Screen-center reticles and
   world-projected target markers require different coordinate handling.
   Existing captures show multiple BeginScene/EndScene intervals per frame;
   one replay interval is not a full-frame integration contract.

A good first deliverable is a Vulkan offscreen HUD render using the generated
models and explicit logical sizes, with an image comparison and no live-game
replacement claim. The prototype is useful input; exact Canvas/Skia pixel
agreement is not an original-GDI compatibility requirement.

## Validation and regeneration

Passed: 24 offline render combinations (four output sizes × two HUD sizes ×
three modes), eight viewport/size checks, sprite/panel bounds, center/edge
anchors, all 31 model dimensions, five rejected invalid viewports, telemetry
endpoint renders, and six PNG exports. Output sizes were 640×480, 1920×1440,
2560×1440 and 3440×1440. Native Skia executed the actual JS renderer and found
system Arial available. Original archives remained unchanged.

Not validated: browser interaction/export button, original-game visual
equivalence, live telemetry, Vulkan rendering, frame ordering, cockpit masking,
target projection or performance. Browser automation blocked local `file:`
navigation; the validation images were rendered offline.

Regenerate to a fresh ignored directory, not over v3:

```powershell
python tools/hud-prototype/prepare.py --output-dir local/work-ahead/hud-vulkan-input-v1
node tools/hud-prototype/verify.cjs local/work-ahead/hud-vulkan-input-v1 C:/Users/jcbla/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@napi-rs/canvas
```

The canvas path is this host's bundled runtime path; resolve the appropriate
dependency path on other hosts. Preparation also requires the checked native
reader parser at `build\m4-assets-parser-r1\mw34_m4_assets.exe` or `--parser`.
Source archive identities are in `manifest.json`; hash-check inputs and preserve
v3 plus the investigation evidence as the reference package.
