# Independent world resolution (FidelityFX P1)

This development-only renderer step separates world raster dimensions from the
output/HUD target. It implements issue #99, following the
[implementation plan in PR #96](https://github.com/roswellien/MW3Recomp-Private/pull/96)
and the [P0 feasibility work in PR #98](https://github.com/roswellien/MW3Recomp-Private/pull/98).
It does not load FidelityFX, dispatch FSR, add motion vectors or generate frames.
Neither earlier PR is implicitly merged by this change.

## Contract

The canonical host accepts `MW34_WORLD_SCALE_PERCENT=50..100` (integer, default
100). The percentage applies to each output dimension, rounding down. For
1920x1080 output, 50 selects a 960x540 world raster. Set an explicit
`MW34_REMASTER_WIDTH` / `MW34_REMASTER_HEIGHT`; reduced mode supports AA Off or
FXAA and rejects SSAA. FXAA retains its existing resident-rendering/GPU-HUD
requirements. This control is intentionally absent from launcher settings.

The renderer owns a second color/D32-depth image pair and framebuffer. A leading
full color clear can begin reduced work. A depth-only clear preserves output
resolution because previous color may contain retained HUD pixels. This also
applies after presentation. Live Training's depth-only starts consequently stay
at output resolution until a full color replacement is demonstrated.

Before HUD, guest readback, capture or resident presentation, the world image is
linearly scaled to output size and D32 depth is transferred with nearest sampling.
FXAA runs before HUD. Subsequent mixed world passes stay at output size until a
new frame boundary or full color clear; they cannot repeatedly filter the HUD.
Menus/frontend canvases retain their existing fitted output size. Target changes and shutdown retire
both image pairs after device work completes. Guest surface dimensions, D16
upload/readback conversion and translated code stay unchanged.

Depth-only starts preserve prior color at its existing resolution. This is a
diagnostic scale path, not a claim that every fade or guest-written overlay
sequence is ready for temporal reconstruction.
The 100% default retains the original allocation and rendering path.

## Reproduce focused checks

Build the maintained host with the command in
[HOST_BUILD.md](../tools/m4-crt-heap-carry/HOST_BUILD.md), omitting `-Release` for
local edits. Refresh the canonical source manifest for intentional source changes.

In an x64 Visual Studio developer shell, with the pinned LLVM and Vulkan headers:

```powershell
clang-cl /nologo /DNOMINMAX /DWIN32_LEAN_AND_MEAN /D_CRT_SECURE_NO_WARNINGS /std:c++20 /EHsc /MD /Itools/m4-crt-heap-carry/host /I<Vulkan-Headers>/include tools/remaster-launcher/test_launcher_display.cpp /Fo<local-output>/display.obj /Fe<local-output>/display.exe /link user32.lib gdi32.lib /incremental:no
$env:MW34_REMASTER_WIDTH = '1280'
$env:MW34_REMASTER_HEIGHT = '960'
$env:MW34_REMASTER_AA = '1'
$env:MW34_REMASTER_AF = '1'
$env:MW34_SUN = '0'
$env:MW34_WORLD_SCALE_PERCENT = '50'
& <local-output>/display.exe --world-resolution
```

Repeat with 67 and 100, and with FXAA (`MW34_LAZY_RT=1`, `MW34_GPU_HUD=1`).
The existing display fixture now checks actual raster dimensions, sharp HUD edges,
interleaved world draws, close-surface depth occlusion after promotion, guest color
and depth readback, depth-only frame boundaries, and frontend target recreation.
Unsupported percentages and reduced mode with SSAA must fail visibly.

## Local native evidence, 2026-10-29

The development host was built from `5b046813c6ffbeac009f7c48c38cb18ccd968063`
plus this patch. Build receipt: seven authored host objects, zero translated object
inputs, `generation_required=false`, `translated_module_unchanged=true`.
Host SHA-256: `57fe7a2cda10950b5166216c08bfd9d46a4fc5110dcacebc939542910427efc5`.
Translated DLL SHA-256: `6d6e3c25fef68727113a6d52859253883dbb554958ddaa5a091187667aa8bfa5`.

On AMD Radeon RX 9070, driver 32.0.31035.1003, native menu -> Training completed
2,200 offscreen frames at 1920x1080, FXAA, 16x AF and the recorded replacement-pack
profile. At 50%, the renderer recorded 5,565 reduced scenes and 1,855 promotions.
Both 50% and 100% runs stopped at the configured presentation budget (the existing
harness reports this deliberate stop as exit code 1). Neither used the swapchain.

A separate 900-frame Instant Action -> MechLab -> briefing run entered the
640x480 logical frontend canvas at frame 281 and left it at frame 535. Its fitted
raster stayed 1440x1080 for 1920x1080 output, without the world percentage.

The 100% output was byte-identical to the previously built host at frames 1801 and
2101. The unchanged reference host SHA-256 is
`01b17fa52ba1f939d271a412c50c5353b2e1fcd885367549e25897dff67cb714`.
The foreground timer glyph masks matched between 50% and 100% at both captures;
the world pixels differed as expected. These are matched native host comparisons,
not comparisons with the original executable.

The mean host frame interval over frames 1200-2200 was 7.340 ms at 50% and
6.894 ms at 100% in these single runs. The additional transfers currently cost more
than this workload saves; no performance gain or displayed FPS is claimed.

Private receipts, isolated game copies and captures remain under
`D:/Projects/MW34-world-resolution/local/world-resolution/`. No original media,
generated game code, executable or game capture is included in this PR.

## Check results

- Maintained host build and canonical source pins: passed; translated DLL unchanged.
- CMake default build, all 25 CTest cases and `format-check`: passed.
- Style `--fix` and report: passed; all languages remain report-only, with existing
  repository findings. No bulk formatting was applied.
- Vulkan display fixture: default/unset, 100%, 67%, 50% and 50% with FXAA passed.
- Deliberately removing HUD promotion made the fixture fail with
  `HUD did not promote to output resolution`; restoring the source passed.
- Invalid percentages 49, 101 and nonnumeric input, and reduced SSAA: rejected.
- Existing D32 fixture: native, scaled, odd guest dimensions, 2x and 4x SSAA passed,
  including all 65,536 guest depth values and 64 close-surface positions.

## Stage 2 follow-up checks

The added `--world-persistence` and `--world-persistence-partial` modes expose a
**confirmed blocker in the initial implementation**. Draw a sharp HUD line,
present, then submit a full depth-only clear in the next frame. At 50%, the line's
red center changes from 255 to 189 and its outside neighbor from 0 to 65. At 67%,
the values are 189 and 16. At 100%, they remain 255 and 0. Both reduced modes exit
1 in that implementation. The partial-world variant draws elsewhere without
overlapping the HUD and originally failed the same way. These checks must pass
before P1 can be accepted; they are
optional fixture modes outside CTest, not marked as expected successes or
suppressed. The standard CMake build, 25 CTest cases and format-check pass;
the local style report completes with existing report-only findings. Those
results do not supersede the failing persistence checks.

The full-image color blits in `select_world_target` resample untouched prior-frame
content. Merely skipping the color transfer for a depth-only submission is
insufficient: the partial-world case needs preservation too. Correct composition
must retain untouched output pixels when a frame does not replace all color.

Additional passing checks:

- Actual GPU HUD inputs at alpha 0, 128 and 255 preserve transparent pixels and
  blend/replace fresh overlays correctly at 50%, 67% and 100%. This tests the
  renderer input after color-key conversion, not every guest image decoder.
  Disabling renderer blending makes the alpha check fail; restoring it passes.
- `--world-present` uses real swapchain counters, resizes the test window,
  minimizes/restores, hides/restores, and presents again. The initial FXAA run on
  RX 9070 completed five swapchain presents before alpha coverage was added.
  Omitting presentation counter increments makes its success assertion fail;
  after restoring the renderer, the ordinary offscreen check passes. The final
  visible check instead fails guest-depth readback, as detailed below. Canonical
  source bytes and manifest pins are unchanged by these temporary failure controls.
- Khronos validation layer 1.4.321 reports synchronization validation enabled;
  the visible FXAA fixture and the stock native run report no Vulkan validation
  errors or synchronization hazards. No diagnostics are filtered out.
- Stock native Training reached 2,200 visible swapchain presentations at 1920x1080,
  50% scale and lighting Off, with 5,565 reduced scenes and 1,855 promotions.
  Its entry object, CRT provider and CRT pack are byte-identical to the current
  installed runtime's resolved inputs; translated DLL identity is unchanged.

The final visible fixture now selects `AMD Radeon(TM) Graphics` instead of the
RX 9070 and fails guest D16 readback: expected 49151 after a 0.75 depth clear,
observed 0 at 50% and 65535 at 67%/100% with AA Off. The FXAA 50% control also
returns 0. Synchronization validation reports no error for the AA Off failure.
The fixture now prints its selected adapter and the mismatched depth value.
Adapter selection checks surface capabilities before preferring a discrete GPU;
this is consistent with the surface-capability failures, but the underlying cause
and the depth defect's relationship to Stage 2 are unresolved. Passing earlier
visible checks do not supersede this final failure.

### Published input verification

At the user's request, the subsequent comparison uses **latest published** updates,
not the mixed development installation. The current live playtest catalog names
launcher 1.0.44-preview and native runtime 1.0.44. All 670 installed runtime files
match its manifest. The signed installed executable hash is
`eb6fd89089f9cb31981bd3278b9a6872396ab6478586d00ce60f076779674c50`.

The live R2 `packs/2026-10-21-r2/packs.json` catalog was fetched read-only. All 13
local archives match its byte counts and SHA-256 values and were extracted into
an isolated test directory. Published versions are environment packs 1.1.0,
remastered models 1.3.0, shared-mech textures 1.1.0, HUD/menu/CD-audio 1.0.0,
Sommerset 1.0.1, Marauder 0.1.1-preview and Gun Metal 0.1.3-preview. Newer local-only
packs are excluded. The published runtime's own coordinator freshly prepares
these inputs; no historical skin-composition environment is reused.

The profile uses 3440x1440, FXAA, 16x AF, dynamic lighting and shadows enabled.
Only the window mode is changed to windowed for controlled visible runs. The
native feature host remains the previously fingerprinted development build.
The intro is skipped through scripted player input before Training navigation.
The first unadjusted run reached the movie/menu only and is not Training evidence.

Visible Training at 50% completed 2,200 swapchain presentations, 4,384 reduced
scenes and 1,460 promotions; the internal world target is 1720x720. The 100% feature
run also completed 2,200 swapchain presentations. Both report no validation errors
with synchronization validation enabled. Captures and complete environments are
local under `published-training50` and `published-feature100`.

The signed published runtime reproduced the prior visible surface-capability
failure (`-13`) before world drawing (`published-reference100`). Later feature-host
attempts (`published50-no-dump`, `published50-no-dump-no-obs`) reproduced it too,
before allocating a reduced world target. The second control disabled the OBS
Vulkan hook only for that process and still failed. Successful visible runs do not
establish reliable startup or resolve this intermittent failure.

The published runtime then completed 2,200 offscreen frames without validation
errors (`published-reference-hidden`). Its output captures at frames 1801 and 2101
are byte-identical to the 100% feature run with periodic dumping disabled:
`0c822b3dd82b25444b1c0dc66dd14bdc26ffb1f49c89a64087404b4ff24389cd` and
`0f7f6f526a793c5cbdd63748fd69949471a298582e83544fe87111dd4d52638e`.
This compares rendered targets, not visible presentation success.

### Periodic size-change observation

The owner observed a small shrink/grow approximately once per second during the
visible runs. The diagnostic harness had `MW34_FRAME_DUMP=100`. In `vdd.inc`, a
scheduled dump explicitly disables resident presentation, synchronizes to guest
pixels, then uses the upload presentation path for that frame. This is a concrete
path change; it does not yet prove the cause of the visual symptom.

A matched feature run with `MW34_FRAME_DUMP=0` completed 2,200 visible frames;
the final readback counter stayed at 1 instead of the recurring periodic readbacks.
Only two output-resolution captures remain, which do not force upload presentation.
The owner is now remote and asked to assume the symptom persists while proceeding.
Visual confirmation remains open; these counters do not establish a fix.

### Presentation bounds correction

The two Vulkan presentation paths had different destination rectangles even at
100% world scale. Resident presentation fits the configured output aspect ratio
inside the window. Uploaded corrected-world pixels previously stretched to the
entire client area. With the recorded 3456x1479 client and 3440x1440 output, the
resident image is 3456x1447 at y=16, while an uploaded frame was 3456x1479 at y=0.
This is a reproducible 32-pixel height change whenever those paths alternate;
periodic diagnostic readbacks are one such trigger, not the only possible one.

Both paths now use the same fitting calculation. A corrected-world upload uses
the configured output aspect even though its storage is guest-sized. Menus and
movies keep their original raster aspect. Bars are cleared even when rounding
leaves a single pixel on only the bottom or right edge. The execution boundary
changed is completed frame -> Vulkan swapchain destination; world rasterization,
guest memory synchronization and filtering are unchanged.

`display.exe --presentation-bounds` passes the recorded ultrawide case, tall and
wide resizes, exact-size output, a one-pixel bar, SSAA aspect and menu aspect.
Restoring the old stretch-to-window branch deliberately fails this check.
The existing offscreen world checks pass at 50%, 67% and 100% with FXAA.
The maintained host build, source-manifest checks, CMake build, 25 CTest cases,
format-check and report-only style checks pass. The new development host hash is
`f7fd767d096fae2b063c54a68b3ed161449583f9a0d745da45b56d0e75c46105`;
its seven host objects and unchanged translated DLL are recorded in
`local/world-resolution/host-present-bounds/source-snapshot.json`.

The same published inputs completed 2,200 offscreen Training frames at 100%
(`bounds-hidden100`) with synchronization validation enabled and no validation
errors. Frames 1801 and 2101 remain byte-identical to the signed runtime's
reference captures listed above. This preserves rendered scene contents; the
offscreen run does not exercise swapchain destination placement.

The visible published-pack attempt (`bounds-visible100-r2`) still fails surface
capabilities `-13` before drawing. An earlier attempt with a relative executable
path failed input opening and receives no native validation credit. The rectangle
defect is fixed and regression-tested, but neither this remote session nor the
bounds fixture establishes that the owner's observed symptom has disappeared.

### Retained output correction

Reduced rendering now requires a leading full color clear. A depth-only clear
keeps the output target, including across presentation, so a partial world draw
cannot filter untouched HUD pixels. The obsolete presentation-boundary flag is
removed. This advances correctness at the previous-output -> next-frame resource
boundary without claiming coverage-aware reduced composition.

The ordinary, depth-only persistence and partial-world persistence checks all
pass at 50%, 67% and 100% with FXAA: the retained line stays 255 at its center and
0 outside. The earlier implementation was observed failing these same sharpness
assertions. The raster assertion now requires output resolution after depth-only
clear; full-color-clear checks still require reduced raster dimensions and actual
promotion counters. This is a conservative rendering restriction: Training's
depth-only frame starts no longer qualify for reduction, so earlier reduced-scene
counts are historical evidence and do not describe the corrected host.

The corrected host completed 2,200 offscreen Training frames with 50% requested and the verified published inputs (`preserve-hidden50`). It reports zero reduced scenes and promotions, with synchronization validation enabled and no validation errors. The captures differ from the earlier published 100% reference; this comparison remains unresolved. The maintained build, manifest checks, 25 standard tests, format-check and report-only style checks pass. Visible startup and integrated-adapter depth issues remain open.

## Remaining limits

The retained-pixel correction below supersedes the initial persistence failures.
Stage 2 remains incomplete because retained-color frames cannot yet be reduced.
FSR remains disabled; do not advance to Stage 3 implementation or mark this draft
ready on the strength of passing CI. Fresh-overlay, stock Training, visible
fixture lifecycle and synchronization checks have bounded evidence above.
Comprehensive guest-write/fade sequences, visible lifecycle checks inside the
game, intermittent visible startup, the visible fixture's depth mismatch, the
reported periodic size change, a second
physical PC and independent review remain open. Mixed world passes after HUD
remain full resolution.
No build, asset, release or version was published or merged by these checks.
