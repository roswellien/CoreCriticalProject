# HUD fidelity handoff for Vulkan integration

Current priority: use the [faithful modernization plan](faithful-modernization-plan.md)
for native host/menu/Training integration. This dated HUD prototype handoff stays
separately scoped; integrate enhanced UI only with recovered live game state and
an affected original-compatible baseline. Do not substitute it for a native HUD.

Prepared 2026-10-10. Workspace: `D:\Projects\MW34Recomp`.

## Native host HUD path (2026-10-14)

The user's direction: move the HUD off the CPU, use the hi-res HUD work, and allow modernization and new HUD features. The game's own HUD logic still decides what is shown and where; only the drawing moves.

- **Per Training frame** (native service log): 5 Direct3D scenes, 2 DirectDraw `Blt` fills and 1 `Lock`/`Unlock` of the back buffer. The HUD is drawn by game code writing into that locked buffer; the DirectDraw-surface `Blt` branch of the image dispatcher `0x55B1F0` (`0x576F90` -> `Blt` with DDBLT_WAIT, plus a source colour key when the image flag is set) is not the one used.
- **Translucent panels:** the objectives panel and the 'Mech status picture are Direct3D primitives, already on the GPU. A magenta 3D image (`MW34_RT_POISON=1`) shows the rest of the software HUD drawn opaque, except the centre reticle, which picks up a magenta halo and so appears to blend with the image underneath.
- **Complete writer set** (`MW34_HUD_WATCH=<file>`, write-protect the locked back buffer and record the first writer per page; replay-identical through frame 760):

  | Function | Primitive | First writes per page |
  | --- | --- | --- |
  | `0x55B3C0` | 16-bit image blit: source crop, destination clipping, the `[0x800824]` software service | 65,030 |
  | `0x563B80` | Bresenham line | 16,877 |
  | `0x5630C0` | midpoint circle, outline or fill (centre ECX/EDX, radius on the stack, mode `0x72C244`) | 3,581 |
  | `0x564080` | horizontal span fill (ESP-push fill; used by filled shapes) | 931 |
  | `0x577A10` | surface `Lock` wrapper path | 300 |

- **Capture implemented (dual mode):** `MW34_HUD_LOG=<file>` (optionally `MW34_HUD_DETAIL=<frame>`) records each call to the four drawing primitives at the generic stage's `enter()`. It also writes a per-frame summary line; the original bodies still run. The capture is replay-identical (Training through frame 520).
  - A Training frame has about 25 image blits, 9 lines, 1 circle and 62 spans.
  - Blit arguments: ECX = image, EDX = x, [esp+4] = y, [esp+8] = flags, [esp+12] = optional source rectangle. Images have width/height at +4/+6, the flags byte at +9 and pixels at +0x10.
  - Examples: the compass is a 1668×10 strip cropped to 148 px; the speed text is a 29×21 cached image at (602, 304).
  - Spans: ECX = RGB565 colour, EDX = count, destination from `0x72C278`.
- **Lazy 3D-target residency (step 1, implemented, opt-in `MW34_LAZY_RT=1`):** the GPU target images stay authoritative after a scene. Guest memory is refreshed (`gpu_sync`) only before Lock, Blt/BltFast, Flip/presentation or a texture Load/upload touches the surface. Fills on a resident surface become GPU clears, exact for 16-bit values. While stale, the guest pages are inaccessible, so a raw guest access stops typed. Scenes without copy-back are not waited for (the next scene or copy-back waits first).
  - Result: per Training frame, uploads and copy-backs drop from 5/5 to 2/2. The 2 that remain come from the two back-buffer locks the game takes per frame for the software HUD.
  - Byte-identical on the Training baseline (2 runs) at 7.4 / 6.9 ms against 7.5 / 6.9 ms, about break-even at 640×480. At `InGameVMode` 7 the same replay costs about 10.8 ms per frame, so the copy-back/upload path matters more at higher resolutions.
  - Test settings: replays now use a frozen copy of the settings overlay (`MW34_REG_OVERLAY`, the overlay the v3 baselines were recorded with); the game folder's overlay holds the user's play settings (`InGameVMode` 7 since 2026-10-14 13:25).
- **GPU HUD (step 2, implemented, opt-in `MW34_GPU_HUD=1` with `MW34_LAZY_RT=1`; `tools/m4-crt-heap-carry/gpu_hud.inc`):** while the game holds the resident 3D target locked, the four primitives are not executed. Each call becomes pre-transformed draws for the scene renderer and returns with the callee's stack cleanup (`ret 0xC` blit, `ret 0x10` line, `ret 0xC` circle, `ret` span). At Unlock they render onto the resident target.
  - Blits: textured quads (RGBA from RGB565 plus the image's alpha mask or colour key; the colour key is the blit's 16-bit stack argument when image flag `0x02` is set), point sampling, straight-alpha blending. Lines and circles use the software rasterization steps as points; spans are quads. The image layout with `+0x18` set falls back to the CPU.
  - Sync on touch: a guest access to the stale target (for example the screen grab `0x579500` at the first 3D frame) saves the context, renders the HUD so far, copies the image back, unprotects and resumes the faulting instruction (`RtlRestoreContext`, integer/control/FP context only).
  - Result (Training, 1,150 frames): the 3D draw streams are identical on every frame; the HUD is visually indistinguishable from the CPU HUD at frame 500. About 96 HUD draws per frame, 0 fallbacks, 1 touch; uploads/copy-backs are down to 1/1 per frame (presentation still reads guest memory). 7.6 / 6.9 ms.
- **Direct presentation (step 3, implemented; `play.ps1` default since 2026-10-14 together with steps 1-2):**
  - In lazy mode the scenes render on the presenter's Vulkan device (`scene_renderer()`). A Flip of the resident back buffer presents it with `Renderer::present_resident` (blit to the swapchain); there is no copy-back and no upload. Page protection follows the resident surface across the memory swap.
  - Frames that dump a PPM, or that the device cannot present directly, take the synchronized path. The FPS overlay draws onto the resident image on the GPU.
  - Steady state: 0 uploads, 0 copy-backs, 0 HUD fallbacks per frame (1 touch at the first 3D frame).
  - Results (dumps off, 2 alternating runs each):

    | Settings | GPU path (frames 300-700 / 700-1150) | CPU path |
    | --- | --- | --- |
    | 640×480 | 7.1-7.3 / 6.9 ms | 7.2 / 6.9 ms (equal) |
    | `InGameVMode` 7 (1024×768, the user's setting) | 7.96 / 6.95 ms | 9.1-9.2 / 7.9-8.0 ms (−13% / −12%) |

  - Identity: 3D draw streams identical on all frames, at 640×480 and at 1024×768; the HUD is visually identical at both.
  - `MW34_LAZY_RT=0` / `MW34_GPU_HUD=0` select the CPU path; the exact frame-baseline harness uses it.
- **Full-resolution rendering (step 4, implemented; `play.ps1` default):**
  - Window: `MW34_WINDOW=fit` makes the largest window of the mode's aspect that fits the screen (`integer` keeps the 1×/2× window; the replay harness pins it).
  - Render scale: the resident target renders at the window's resolution (scale = client height ÷ game height, 1-4; `MW34_RENDER_SCALE` overrides). The vertex shader's game-size NDC mapping makes geometry scale with no shader change. Viewport, scissors and clear rectangles are scaled.
  - Guest copies (uploads, copy-backs, sync-on-touch) blit through game-resolution staging images. Direct presentation blits the render-resolution image, keeping the aspect ratio with black bars.
  - HUD lines and circles are one-game-pixel-wide quads (circles are polylines or fans), so they stay continuous at any scale.
  - `MW34_HIRES_DUMP=<frame>` with `MW34_HIRES_DUMP_FILE=<ppm>` writes the presented image at the render resolution (diagnostic).
  - Results: identical 3D draw streams on all frames (640×480 rendered at 1760×1320; 1024×768 at 1.72×). 7.18 / 6.94 ms at 2.75× (the same as unscaled); 8.12 / 6.97 ms at mode 7 / 1.72× (against 7.96 at 1×).
- **Hi-res HUD pack (step 5, implemented; loaded by default when present):**
  - `tools/vulkan-hud/build_hires_pack.py COMPONENTS OUT --density 4 --canvas-package …` rasterizes the 31 v3 vector remakes with the prototype's `vector()` (via `rasterize.cjs`). Each is keyed by its original sprite's identity: FNV-1a 64 over width, height and the per-pixel RGB565 word (0 where transparent). Output goes to `local/hires-pack/hud/<key>.rgba` (`MW3H` header, padded straight-alpha RGBA, UV rectangle of the logical image).
  - At run time an in-game image with the same identity (computed with the same rule from its mask or colour key, images up to 64K pixels) is drawn from the pack texture at its logical size, keeping the game's crop and position, with linear filtering. `MW34_HIRES_HUD=0` disables it; `=<dir>` selects another pack.
  - Result: about 4 substitutions per Training frame (gauge frames, heat meter, arrows, reticle states as they appear). Identical 3D draw streams; 8.17 / 6.97 ms at mode 7 / fit window.
- **HUD text at output density (step 6, implemented; on in GPU-HUD mode, `MW34_HUD_TEXT=0` disables):**
  - The game builds each text image in three steps: clear the shared DC over the image (`0x577BA0`, ECX = image), call `DrawTextA` through the host GDI service (shadow, then main string), then copy the DC bitmap into the image (`0x577BD0`).
  - Each `DrawTextA` between a clear and a copy is recorded with its string, rectangle, flags, the DC's `LOGFONT` and the text colour, and attached to that image.
  - A blit of a recorded image at render scale above 1 re-renders the recipes with the same fonts at the scale (antialiased host GDI, straight alpha, cached by recipe hash and scale). The result is drawn at the image's logical size and source crop.
  - The game reuses text images and blits only the width it measured at 1×. Scaled fonts can run wider than `rect × scale` (Arial at 1.72× is about 15% wider), so the font's `lfWidth` is narrowed until the string fits. Without this, the game's crop cut strings like "TRAINING: Movem".
  - `MW34_HUD_TEXT_LOG=<file>` lists each re-rendered image's recipes (diagnostic).
  - Results (mode 7 / fit window, 1150 frames): about 9 text blits per frame; 3D draw streams identical on all 1150 frames to the step-5 run and on 600 frames to the CPU path at mode 7. The CPU path stays byte-identical to the v3 baselines (116/116). 7.66 against 7.51 ms per frame (frames 150-1150; the text cache costs about 0.15 ms).
- **Next:** 3D texture upscaling with the hi-res texture masters (content-keyed, like this pack). Then new HUD features on the GPU path.
- **Earlier plan:** host replacements for these entries that record HUD commands (image ID and crop, destination, colour key; line and circle geometry; fills).
  1. Run them first in a dual mode that still performs the original writes, so replays stay byte-identical while the Vulkan HUD pass is built.
  2. Then draw them on the GPU at output resolution with the `hud-fidelity-v3` components, composited after the 3D scenes.
  3. Finally drop the CPU writes and the full-frame copy-back.

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
