# MW3 HUD fonts, artwork and fidelity

## Heat display update investigation (2026-10-10)

Static references to `hud_heat_bar` and `hud_heat_meter` initialize HUD members
at offsets 0x1450 and 0x1510; layout keys move these same objects. Member 0x15cc
is the heat arrow. The gameplay HUD update at 0x43c390 calls 0x4455e0 from
0x43c532, passing the HUD in ECX and two floats on the stack (callee RET 8).
The caller reads guest fields 0x554, 0x558 and 0x55c. It scales the first
candidate by approximately two thirds up to a threshold of 1.5; the second
argument combines two other fields with the update argument. Field units and
physical meaning remain unproven.

The target clamps the sum to [0,1] for arrow positioning and changes the bar's
source rectangle and destination using image heights. This establishes a
dynamic crop/position path beyond the previously observed text label. Ghidra
reports an unreliable `unaff_retaddr` expression for part of the arithmetic;
the retained x86 instructions must govern stack-argument recovery. It does
not establish an original source signature.

Private receipts: `reports/vulkan-hud/heat-static-ledger.json`,
`heat-update-decompile.json`, `heat-caller-decompile.json` and
`heat-static-disassembly.txt`. Update evidence:
`ev_7bb83b7b722d105df32f3f8ac5e5ea4a792293bddd225d214bf14da9bd7543ce`;
caller evidence:
`ev_0db9d68c1f1b80a728c691c3091f065f82b8b1aa567ba064429345389004ef8e`.
Next is a bounded call-through observer at this admitted CALL site, preserving
registers, stack, floating-point state and LastError, then Instant Action
firing/cooling capture. No new game session or live heat observation occurred
during this static investigation; Vulkan heat artwork remains static.

Investigated 2026-10-09 against installed U.S. MW3 1.2, executable SHA-256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
This is asset decoding and static binary analysis, plus an authored Windows GDI
probe. No game launch, installed asset change or native HUD integration occurred.

## Located resources

`MW3/zbd/reader.zbd` contains `fonts.zrd` and `hud.zrd`. These are binary token
trees, not loose text files. The existing checked `mw34_m4_assets` parser decoded
both. `fonts.zrd` has an empty bitmap `FONTS` section and 51 `WINDOWS_FONTS`
definitions. HUD-related definitions include:

| Definition | Face | Signed height | RGB |
| --- | --- | ---: | --- |
| `wepif_font` | Arial | 10 | 200, 200, 0 |
| `mech_string` | Arial | -10 | 0, 235, 0 |
| `wepstring_red` | Arial | -10 | 235, 0, 0 |
| `wepstring_green` | Arial | -10 | 0, 235, 0 |
| `wepstring_yellow` | Arial | -10 | 202, 141, 0 |
| `wepstring_grey` | Arial | -10 | 120, 120, 120 |
| `hud_messages` | Arial | 14 | 0, 235, 0 |
| `hud_htal` | Arial | 16 | 0, 235, 0 |

Height is a LOGFONT logical value; positive cell height and negative character
height have different meanings. Preserve the sign when scaling. The selected
definitions specify neither `quality` nor `precision`, so the initializer's
defaults matter. Menu/briefing definitions also use Lucida Console. Not every
HUD text call has been associated with its exact definition yet.

`MW3/zbd/rimage.zbd`, SHA-256
`3519eb39907a08900ec175ec9dd828ba15878e2a4a9b0f7263525eb5a88ad4cc`, has
394 accepted image entries. Entries 278–329 are 52 `hud_` sprites; entry 334 is
`sensor_reticule`. The research package exports all 53 with exact source size,
stored row order and alpha, without resizing or gamma conversion.

| Asset | Index | Stored size | Transparency |
| --- | ---: | --- | --- |
| `hud_compass` | 283 | 1668 × 10 | Black key |
| `hud_compass_frame` | 284 | 148 × 19 | Separate alpha plane |
| `hud_heat_meter` | 294 | 17 × 122 | Black key |
| `hud_speed_frame` | 311 | 28 × 78 | Black key |
| `hud_mech_enemy_sm` | 299 | 5 × 5 | Black key |
| `sensor_reticule` | 334 | 21 × 21 | Black key |

These are genuinely small source graphics. Higher world resolution cannot add
detail to them. Black-key assets require coverage/alpha reconstruction when
redrawn; filtering opaque black borders directly risks dark fringes.

`hud.zrd` provides six named layouts: 640×480, 800×600, 1024×768, 1152×864,
1280×1024 and 1600×1200. Some positions move with the right/bottom screen edge,
while sizes remain fixed: MFD/TARGET are 75×100 and WEAPONS/EQUIPMENT width is
110 in every layout. This supports explicit anchoring as a design direction;
it does not establish how unsupported resolutions are selected at runtime.

## Recovered rendering entry points

REA/Ghidra 12.1.4 evidence is retained privately in
`local/work-ahead/hud-research-v1/rea-evidence.json`. Static references and
decompilation establish these investigation entry points, not live execution:

| Address | Observed role | Evidence |
| --- | --- | --- |
| `0x519E50` | Reads font document, bitmap section, then Windows-font section | `ev_c1062c79261d805c46ed35832a8752a896c0ec07ed8bc5970e72dbf3438c91ce` |
| `0x516FF0` | Loads face, signed height, LOGFONT fields, colors, shadow and alignment; `quality` goes to object+0x1E | `ev_3546b94ddcaaa3fa2e52636db01a0a7ba88993832be65ad9efce96c7b770d0aa` |
| `0x517250` | Clears font state, sets out precision=4 and quality=1 | `ev_dc6768dd61eb815cbfcca4f498fe6dfa5f560ebde74700e78c2ed6cb947b6535` |
| `0x517280` | Calls `CreateFontIndirectA` with LOGFONTA at object+4 | `ev_857c7d3fb200dcadb4e6d529070087cec7238e429eb97c453f7567e0549fdb23` |
| `0x517680` | Looks up and acquires a named Windows font | `ev_aa235b74fc1fda4b91d2275c7153014f1461882ecb2e54147ec4cc4bc15b6d81` |
| `0x47E840` | References `hud_htal` and acquires a font for related widgets | `ev_403391230f9c6136d3a74a9204a4f9cefa9b7a1f3a8ea9b5b71d88df29e328dc` |
| `0x43BB80` | Reads `hud.zrd`, selects a resolution label and configures HUD children | `ev_d898707e7a986e50cf89c9a9d662e94be72f2e20f63572e0e331a264d0efe59c` |
| `0x5A0E20` | Selects HFONT into a compatible DC and uses DrawTextA/DT_CALCRECT for text measurement | `ev_bff80f9e187b883149157d000f28c7e17e645f1ee1fc59b45c5e200bae63ee5a` |

The DrawTextA IAT slot is `0x5BB6F8`; analyzed call sites include `0x5A088F`,
`0x5A0B42`, `0x5A0BB2`, `0x5A0E8D` and `0x5A0EBD`.
Ghidra did not recover enclosing procedures at the first two sites, so this
investigation does **not** claim complete text rasterization/surface-upload
recovery. GetTextExtentPoint32A has a reference at `0x5A0F7A`, also outside a
recovered procedure. These are concrete next disassembly/capture targets.

Existing [graphics tracing](mw3-live-graphics-trace.md) establishes the game's
DirectDraw4/Direct3D3 boundary and transformed vertices, but sampled draws have
not been individually attributed to HUD components. The
[presentation investigation](vulkan-live-replay.md) shows multiple scene
intervals per frame. A single captured world scene is insufficient to validate
the complete HUD or to insert a final overlay correctly.

## Small candidate and measured limitation

Windows SDK 10.0.26100.0 `wingdi.h` defines DRAFT_QUALITY=1 and
ANTIALIASED_QUALITY=4. The
[Microsoft LOGFONT contract](https://learn.microsoft.com/en-us/windows/win32/api/wingdi/ns-wingdi-logfonta)
explains that draft quality can already receive smoothing according to system
settings, while requested antialiasing depends on the font and its size.

The existing loader accepts a numeric `quality` property. The preparation tool
adds `quality [4]` to only the eight definitions listed above, producing
`local/work-ahead/hud-research-v1/reader-antialiased-candidate.zbd`.
It appends a replacement font payload before a copied directory and redirects
only that entry. Original unused font bytes remain in the candidate deliberately.
All 177 other entries retain their offsets, sizes, metadata and payload bytes.
The independent native parser accepts the archive and verifies that the font
tree differs by exactly those eight properties. Sizes, colors, shadows and all
HUD layouts are preserved. Source archives were rehashed unchanged. A missing
target-font negative control was rejected.

This is a prepared experiment, **not a recommended or installed upgrade**.
The authored GDI probe used CreateFontA with the same Arial face, heights,
precision=4 and quality values 1/4, then DrawTextA to a 32-bit DIB on black.
It is not the game's DC, surface format or compositing path. Its results are
retained in `gdi-probe.json` and eight PNGs:

| Arial height | Quality 1 partial green pixels | Quality 4 partial green pixels |
| ---: | ---: | ---: |
| -10 | 684 | 0 |
| 14 | 828 | 0 |
| 16 | 794 | 0 |
| -30 | 1969 | 1192 |

Quality 4 used only black/full-green samples at the three original small sizes;
at -30 it produced 16 green levels including background/full green. Quality 1
used seven green levels. Thus forcing quality 4 alone does not establish a
fidelity gain and may remove smoothing at small sizes in this environment.
Counts are descriptive, not perceptual quality scores. The larger sample also
clips the illustrative string at the fixed canvas width; it is a raster probe,
not a layout acceptance test.

## Practical enhancement path

1. Recover the actual HUD text draw/measurement/surface path and glyph metrics.
   Render Arial from outlines at output pixel density, retaining original
   logical advances, signed-height conventions, baseline, clipping, color and
   shadows. Changing font height alone changes layout and can cause overlap.
   Use grayscale coverage for composited text and verify against the original.
2. Rebuild compass ticks/numerals, reticle, gauges, arrows and radar markers as
   vector artwork or high-resolution alpha assets. Keep their logical display
   dimensions distinct from texture storage dimensions. A 4× texture must not
   automatically make a gauge 4× larger. Simple resampling cannot invent detail.
3. Replace resolution-specific screen coordinates with recovered edge/center
   anchors and one uniform HUD scale. Keep screen-space reticle placement and
   world-projected target markers in their correct coordinate systems. Validate
   cockpit alignment and hit regions separately. The existing widescreen test
   already records HUD stretching at 3440×1440.
4. Composite the HUD at final output resolution after world rendering and any
   world scaling. Determine the correct original ordering before changing it;
   suppress the original HUD contribution to avoid duplicate text/markers.

For the future Vulkan renderer, steps 1–4 offer a direct solution. For the
original executable, the immediate bridge would need a targeted text/asset
replacement hook plus layout handling; a broad CreateFont IAT replacement or
wrapper resolution setting alone cannot provide this result. No integrated
game renderer is currently available in `runtime/graphics`.

Prepare another isolated research package:

```powershell
python tools/asset-inventory/prepare_hud_research.py --output-dir local/work-ahead/hud-research-v2
```

Requires `build/m4-assets-parser-r1/mw34_m4_assets.exe` or an explicit `--parser`.
Only the admitted original reader/image archive hashes are accepted; output
must be a fresh private directory. Candidate hashes intentionally differ and
are not admitted by original-identity-only asset workflows.
`review.html` displays source sprites and an interactive browser comparison of
enlarged small text versus text rendered at output size. That comparison is a
strategy demonstration, not original-game output. Gameplay validation remains
necessary before adopting any candidate.

## Follow-through: component fidelity prototype

The user's request to proceed produced `tools/hud-prototype` and the private
`local/work-ahead/hud-fidelity-v3/` package. It includes 31 standalone SVG remakes,
all 53 original decoded source components, the parsed font/layout definitions,
a self-contained interactive review, six rendered PNGs and a validation receipt.
The canvas code renders Arial at output resolution and draws authored vector
geometry directly in output space. Logical component sizes remain unchanged.
At 3440×1440, the default uniform scale is 3×, with independent left/right,
bottom and center anchors. The reticle remains exactly at 1720,720.

Offline validation uses the same JS renderer with bundled native Skia canvas:
24 render combinations across four resolutions and two HUD sizes passed, along
with source component dimensions, panel/sprite bounds, anchor/center checks,
five rejected invalid viewports and telemetry endpoint renders. All 31 vector
models match the source logical dimensions. Native Skia reports system Arial
available. Visual inspection of rendered PNGs shows cleaner text and gauge
numerals than the enlarged small-raster control. This is a demonstration of the
method, not perceptual equivalence or performance acceptance for the game.

The HTML is available for manual review, but browser automation rejected local
`file:` navigation. No browser screenshot, interaction or export-button test
is claimed. PNGs were produced by offline native canvas execution instead.

The prototype is explicitly incomplete as a replacement game HUD: background,
panel outlines, compass spacing, telemetry and marker placement are authored;
source-mode text is an illustrative small Arial raster. SVG numeral styling,
some silhouettes/colors and heat-meter geometry are candidates. The prototype
does not reproduce original dynamic visibility, animations, cockpit masking,
target projection or menu hit regions. Other components fall back to source
artwork. These limits are displayed in the review, not hidden behind a game
compatibility claim.

### Original text-cache bridge recovered further

A focused LLVM 21.1.8 disassembly of the same hash-admitted executable resolves
the earlier Ghidra procedure gaps without claiming newly recovered Ghidra
function bodies. Literal entry alignment and instruction sequences identify
`0x5A0790..0x5A0D16` as a text preparation/cache routine. It uses object+0x34
for the string, object+0x258 for HFONT and object+0x248 for an image object.
It measures at `0x5A088F` with DrawTextA/DT_CALCRECT, sizes an image at
`0x5A0988`, and draws shadow/main text at `0x5A0B42`/`0x5A0BB2`.
Measurements are retained in object fields +0x460/+0x464 and +0x490..+0x49C.
The source instructions also show gradient processing over 16-bit cached pixels.

`0x57A02F` assigns the image/DC service at `0x72F394` to `0x577BA0`, and
`0x57A039` assigns `0x72F398` to `0x577BD0`. The first service clears the shared
DC via PatBlt/BLACKNESS and returns it; the second reads bitmap pitch with
GetObjectA, iterates image width/height and copies each **nonzero 16-bit word**
into the packed image buffer. Image dimensions are signed shorts at +4/+6;
pixel storage is at +0x10. These observations explain the concrete cached
raster boundary. Exact format negotiation, all alternate service assignments,
DC ownership and synchronization still need complete recovery/live correlation.

For integration, replace this selected text-cache path with an output-density
RGBA coverage cache while preserving original logical measurement fields.
Physical glyph/texture dimensions must be carried in separate host metadata;
blindly enlarging the guest image width/height would alter layout and clipping.
Then identify the downstream draw of that cache, its destination rectangle and
texture coordinates, and render the higher-density cache at the original
logical destination size with recovered anchor handling. A final presentation
overlay needs complete HUD suppression and ordering recovery first. The
prototype provides candidate assets/layout math for this route; it installs
none of those hooks and does not bypass unresolved original ABI/state behavior.

### Text destination recovered in a bounded live run (2026-10-10)

The text class vtable at 0x5cfd28 has draw entry 0x5a10d0. Its selected image
draw calls pass ECX=cached image, EDX=final X and stack Y/flags/source rectangle
to 0x55b1f0. Horizontal alignment adjusts the object X before those calls.
Ghidra evidence:
`ev_fb87fe93f28dcb20c6b36d19cab49fc99dcb93d3f5418a4ae06939421fb12d12`
(text draw) and
`ev_76593ce13d6216630ab208da4670d5dcd0644095f6fb9930e138c3525b1650c9`
(image dispatcher). Full responses and focused LLVM instruction dumps are
retained privately under `reports/vulkan-hud/`. Ghidra has no procedure at
0x5a0790 in this import; that limitation remains, rather than treating its
failed caller query as proof of no callers.

The image dispatcher can call a selected software service instead of issuing
Direct3D primitive draws. Run `20261010-061535-504` observed service 0x55b3c0,
640x480 dimensions and 1280-byte target stride. Its focused instructions show
source-crop extents from right-left/bottom-top, destination bounds clipping
and 16-bit target addressing. Other image alpha/key branches and format modes
are not recovered by this observation.

The new optional `hud_draw.hpp` observer forwarded all original rendering and
captured 512 valid text calls, including ten speed draws at X=602/Y=304 with
29x21 cache dimensions and full-cache source crop. The user confirmed normal
HUD/gameplay/quit; the passive monitor confirmed exit 0 without alerts. The
Vulkan HUD adapter now uses this recorded destination at 640x480 and explicit
right anchoring for a host ultrawide layout. This corrects its earlier
illustrative speed position. It remains an offscreen recorded-state pass:
total presentation order, all HUD paths, exact GDI baselines and original-HUD
suppression are unresolved. See [the implementation notes](../tools/vulkan-hud/README.md).
