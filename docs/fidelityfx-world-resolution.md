# Independent world resolution (FidelityFX P1)

This development-only renderer step separates world raster dimensions from the
output/HUD target. It implements issue #99, following the
[implementation plan in PR #96](https://github.com/roswellien/MW3Recomp-Private/pull/96)
and the [P0 feasibility work in PR #98](https://github.com/roswellien/MW3Recomp-Private/pull/98).
It does not load FidelityFX, dispatch FSR, add motion vectors or generate frames.
Neither earlier PR is implicitly merged by this change.

## Contract

Owner direction: the RX 9070 is the primary validation target. Integrated-GPU
compatibility passes do not satisfy the discrete-GPU presentation or performance
criterion. The combined RX 9070 presentation checks below use the experimental
same-adapter Vulkan/DXGI bridge; raw Vulkan WSI remains defective on this driver.

The canonical host accepts `MW34_WORLD_SCALE_PERCENT=50..100` (integer, default
100). The percentage applies to each output dimension, rounding down. For
1920x1080 output, 50 selects a 960x540 world raster. Set an explicit
`MW34_REMASTER_WIDTH` / `MW34_REMASTER_HEIGHT`; reduced mode supports AA Off or
FXAA and rejects SSAA. FXAA retains its existing resident-rendering/GPU-HUD
requirements. This control is intentionally absent from launcher settings.

The renderer owns a second color/D32-depth image pair and framebuffer. A leading
full color clear can begin reduced work. Otherwise resident opaque world runs
shade at reduced resolution and use output-resolution coverage replay, described
below. Depth-only submissions themselves retain output color; they no longer
prevent the following opaque world runs from using reduced shading.

Before HUD, guest readback, capture or resident presentation, full-clear world
images promote to output size with linear color and nearest depth sampling.
Retained opaque runs instead reconstruct color in a temporary output image,
apply selected FXAA there, and replay original geometry, alpha rejection and
depth operations into the preserved output target. Untouched output pixels are
not copied or filtered. Contiguous blended/point runs, guest uploads/readbacks
and HUD operations retain the ordered full-resolution path.
Menus/frontend canvases retain their existing fitted output size. Target changes and shutdown retire
both image pairs after device work completes. Guest surface dimensions, D16
upload/readback conversion and translated code stay unchanged.

Depth-only starts preserve prior color at its existing resolution. Reconstruction
is a development path; complete fade/guest-write coverage and temporal inputs
remain separate acceptance work.
The 100% default retains the original allocation and rendering path.

## Reproduce focused checks

Build the maintained host with the command in
[HOST_BUILD.md](../tools/m4-crt-heap-carry/HOST_BUILD.md), omitting `-Release` for
local edits. Refresh the canonical source manifest for intentional source changes.

In an x64 Visual Studio developer shell, with the pinned LLVM and Vulkan headers:

```powershell
clang-cl /nologo /DNOMINMAX /DWIN32_LEAN_AND_MEAN /D_CRT_SECURE_NO_WARNINGS /std:c++20 /EHsc /MD /Itools/m4-crt-heap-carry/host /I<Vulkan-Headers>/include tools/remaster-launcher/test_launcher_display.cpp /Fo<local-output>/display.obj /Fe<local-output>/display.exe /link user32.lib gdi32.lib dxgi.lib d3d11.lib /incremental:no
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

### FXAA mismatch diagnosis

The earlier capture mismatch is explained by deferred FXAA. A matched 100% run
with AA explicitly Off (`retained-aaoff100`) completed 2,200 offscreen Training
frames without validation errors. Its captures at 1801 and 2101 are byte-identical
to `preserve-hidden50`, whose requested FXAA was skipped on retained-color frames.
This isolates the observed difference to the effective AA behavior in these runs;
it does not establish visible presentation compatibility.

The development host now logs a one-time warning when retained output color
prevents both reduction and full-image FXAA. The fixture requires FXAA on fresh
world color and verifies that retained-color composition does not add an FXAA
pass at reduced settings. Temporarily disabling the actual FXAA implementation
fails the fresh-color assertion. The restored renderer passes at 50/67/100.

The maintained host builds with refreshed source pins and unchanged translated
DLL. CTest passed 24 cases initially; `release_and_mod_tools` encountered a local
socket abort (WinError 10053), then passed alone on rerun. Format-check and the
report-only style checks complete. Restoring reduced rendering and selected FXAA
on retained-color frames remains blocked on coverage-aware composition; the
warning makes the development limitation visible rather than accepting it as
complete Stage 2 behavior.

### Scaled depth readback correction

The presenting integrated AMD adapter reproduced the guest-depth failure at 100%:
1280x960 resident depth read back as 65535 where 49151 was required. The raw D32
value was already 1.0 before D16 conversion. A 640x480 unscaled control passed.
Adding early-depth synchronization, using a transfer clear, and changing cached
host-memory selection did not fix it; those experiments were restored exactly.

Depth readback now copies the full D32 raster directly to host staging, then
samples texel centers with integer coordinates and quantizes once into guest D16.
Color readback keeps its existing filter. Staging capacity covers the complete
raster depth, including after promotion. This changes resident depth -> guest
surface transport, with no gameplay or shader change. It increases depth-readback
bandwidth and staging memory at enhanced resolutions; no performance gain is
claimed. Depth upload and world-target depth promotion still use their existing
GPU paths.

The former visible fixture passes at 50/67/100 on `AMD Radeon(TM) Graphics`, with
five swapchain presents and resize/minimize/hide restoration. The depth fixture's
new `visible-scaled` mode selects the presenting adapter and passes all 65,536
guest depths, color transfer, resident fetch, 64 close-surface positions and depth
clear. Native/scaled/odd/2x/4x SSAA checks also pass. Authored CPU cases check
center selection and odd-ratio sampling; removing the half-texel offset fails.

The expanded synchronization run exposed scratch-image reuse hazards. Reuse now
waits for preceding command stages before discarding/transferring the scratch
image. The presenting depth suite then passes with synchronization validation and
no errors; the initial failing validation log is preserved locally. The earlier
visible depth mismatch is resolved within this tested scope. Broader adapter and
physical-PC coverage remain open.

A published-input native visible attempt still fails surface capabilities `-13`
before drawing. The first rebuilt host completes 2,200 offscreen Training frames
at 100%, with synchronization validation and no errors; captures 1801/2101 match
the published reference exactly (`depth-direct-hidden100`). This native run
precedes the final scratch-dependency adjustment and is not final-build evidence.

### Capability-query device selection

A fixture that calls `max_texture_dimension(window)` before its first upload
reproduces the native surface-capability `-13`: the query previously initialized
an offscreen-preferred adapter without considering the supplied window. The
query now creates the host child and selects a window-compatible adapter before
reporting its texture limits. A valid hidden window is included because the game
queries before showing its window. Before a window exists, the query now enumerates physical graphics adapters and advertises their common minimum image limit without creating a logical device. This is conservative and may advertise less than a later-selected adapter can support. Once a window exists, limits come from its actual presenting device.

The hidden-query -> show -> first upload fixture passes on the integrated adapter,
then completes five swapchain presents with resize/minimize/hide restoration.
A first native attempt checking visibility alone still failed; the final valid-
window change includes hidden-window queries and receives separate validation.
This changes device ownership before texture allocation, without inventing a
texture limit or switching devices underneath existing resources.

The pre-window enumeration -> hidden window -> visible presentation fixture passes
with synchronization validation. Replacing the unbound physical-limit query with
early device initialization reproduces `-13` and is rejected. The native final
host (`a90f5a379d0eccdbf7ca16c49c53784bf77ea96fbd0f0d2a8ce3d496618a0237`)
then reaches Training and completes 1,000 actual swapchain presentations on the
integrated AMD GPU at 3440x1440 with published packs, FXAA/16x AF and lighting /
shadows enabled (`deferred-device-visible100`). It records 1,342 native scenes
and no synchronization or other validation errors. The selected GPU lighting / shadow paths are enabled, with directional sun strength 0 and ambient 1; this does not validate nonzero directional lighting. This is bounded startup /
Training evidence, not broad multi-adapter startup acceptance. The maintained
build, source pins, unchanged translated DLL and all 25 standard tests pass.

The matched 50%-requested run completes 900 visible swapchain presentations and
942 native scenes (`deferred-device-visible50`) with synchronization validation
and no errors. It reports zero reduced scenes/promotions and explicitly warns
that FXAA is deferred for retained color. This validates the conservative path,
not reduced Training rendering. These are integrated-GPU compatibility runs: the
RX 9070 still rejects this session's surface. The host selects a compatible
presenting device rather than changing the display driver or forcing an adapter
that cannot present. Local RX 9070 presentation and performance remain unverified
by these runs.

### RX 9070 primary-target investigation

Windows identifies the RX 9070 as the active 3440x1440 primary display adapter.
The session is an active console session with both input and thread desktops
named `Default`; remote access alone is not an established cause of the failure.
Installed versions are RX 9070 32.0.31035.1003 and integrated AMD graphics
32.0.21045.1000. AMD lists both in the [26.7.1 package](https://www.amd.com/en/resources/support-articles/release-notes/RN-RAD-WIN-26-7-1.html), so the version difference itself is not evidence of a bad installation.

A small local program independent of game code reproduces RX 9070 Vulkan
`vkGetPhysicalDeviceSurfaceCapabilitiesKHR` returning `-13` for ordinary
top-level, disabled/enabled child and popup windows. Surface creation, generic
Win32 presentation support and per-surface queue support succeed. The newer
capabilities2 query also fails. Vulkan 1.0/1.1 and pumping pending window messages
do not change the outcome. Selecting only the RX 9070 ICD, disabling AMD's
switchable layer, and disabling all implicit layers for the process also leave
the failure. Controls use process-local environment only; installed drivers and
registry settings are unchanged. Initial forward-slash driver-manifest overrides
failed instance creation and receive no presentation credit; Windows-path retries
reproduced the actual surface error.

A separate D3D11/DXGI control explicitly selects vendor 1002 / device 7550
(RX 9070), creates a flip-discard swapchain and presents successfully (HRESULT 0).
This narrows the current failure to Vulkan presentation rather than establishing
that the RX 9070 cannot present to this display. No driver reset, update or remote
session interruption was performed.

AMD's [RX 9070 download page](https://www.amd.com/en/support/downloads/drivers.html/graphics/radeon-rx/radeon-rx-9000-series/amd-radeon-rx-9070.html) lists 26.10.1 WHQL, dated 2026-10-20. The initial proposed environmental test was a controlled driver update/restart followed by the same standalone Vulkan probe; it is not a proven fix. This session lacks an administrator token, and installation/restart may interrupt RustDesk, so that maintenance requires owner involvement. Once Vulkan presentation succeeds on the 9070, repeat the visible fixture and published-input Training checks on that GPU before accepting the primary-target criterion.

### Combined RX 9070 integration

The owner declined driver changes. PR #105 supplies an experimental same-GPU
Vulkan/DXGI presentation path instead. This branch incorporates that topic branch
for combined validation; neither PR nor either shared branch is merged by these
local feature-branch changes. The option remains `MW34_DXGI_PRESENT=1`, absent
from launcher settings. Vulkan still renders on the RX 9070; DXGI presents the
shared GPU texture on the matching adapter. See the
[presentation contract](dxgi-presentation-bridge.md).

The combination preserves Stage 2's full-raster D32 readback and deferred
window-based adapter selection for direct Vulkan WSI. The explicit bridge can
initialize before a window exists because it matches adapters by LUID. Initially,
the combined pre-window fixture failed with `DXGI presentation request was not
selected`; allowing only an explicitly requested bridge to initialize there
restores it. The 25-presentation bridge fixture then passes. Unknown settings and
exclusive fullscreen still reject visibly.

Combined focused checks on RX 9070, with Khronos synchronization validation:

- Visible world/promotion/lifecycle, retained HUD and partial-world persistence
  pass at 50%, 67% and 100%, with AA Off and FXAA (18 cases).
- The visible cases each count five real presentations and restore after resize,
  minimize and hide. Synthetic full-color replacements exercise actual reduced
  raster dimensions; these are fixture results rather than live Training scaling.
- The depth suite passes native/scaled/odd/2x/4x SSAA and visible-scaled modes,
  including all 65,536 guest depth values and close-surface tests.
- The 25-frame bridge check includes actual copied backbuffer pixels and 16
  alternating frames without diagnostic readback. Configuration rejection modes,
  standard CMake build, 25 CTest cases and format-check pass.

The combined maintained host SHA-256 is
`14d3f0d1f1b64daf535e1d1edf4aff14e30fbe7b18740711d14f9c3d4b068328`.
Its receipt records seven host objects, zero translated objects, and the unchanged
translated DLL. Canonical host pins match the receipt. Private inputs, logs and
captures are under `D:/Projects/MW34-stage2-9070/local/integration/`.

Using published runtime 1.0.44 support inputs and the same 13 verified published
packs, the combined host reaches native menu -> Training on RX 9070 at 3440x1440,
FXAA/16x AF, with GPU lighting/shadow paths enabled (sun strength 0, ambient 1).
At 100% it completes 2,200 actual bridge presentations / 6,142 native scenes with
no validation errors. Captures 1801/2101 match the published runtime byte for byte
(the hashes recorded above). The latest update catalog still names 1.0.44 as the
promoted runtime. The configured budget deliberately stops with exit 1; this is
not normal-quit acceptance or original-executable equivalence.

The matched 50%-requested run also completes 2,200 actual bridge presentations /
6,142 scenes without validation errors. It records zero reduced scenes and zero
promotions, with the explicit retained-color/deferred-FXAA warning. Captures
1801/2101 match the earlier AA-Off control exactly:
`fba31799aa42bc0193ac9b25560e27ee29209240aa4240710be3f1c381df361e` and
`75e3322255fef1394bb59439fb562ad20c32dfa4ab34bc417d2202f7940c3880`.
They differ from the published FXAA reference as expected. This demonstrates
preservation through the bridge, not reduced live Training or complete AA support.
The periodic shrink/grow observation still needs visual confirmation in the game;
the destination-bounds regression passes, but frame counts do not prove that symptom
absent. No performance gain is claimed from these validation runs.

### Retained opaque world reconstruction

The initial whole-scene opaque rule exercised only one native batch because
Training interleaves opaque and blended draws. The implementation now partitions
the original command stream into contiguous opaque and blended/point runs without
reordering clears or draws. Eligible opaque runs shade in the reduced target,
then reconstruct into a separate output-sized color image. Selected FXAA filters
that temporary, not the retained output image. The original geometry, scissor,
texture-alpha rejection and depth tests run at output resolution with a small
fragment shader that samples reconstructed RGB and preserves the original
full-resolution fragment alpha. Output depth is produced by the
original full-resolution replay, rather than a scaled depth approximation.

This advances retained opaque world shading -> reconstructed color -> covered
output pixels while preserving untouched HUD/color/depth. Blended runs continue
at output resolution, reading the updated destination in command order; this
keeps fades from downsampling retained UI. Upload/readback and point runs also
keep the full-resolution path. The 100% path is unchanged. Its historical
whole-image FXAA can reprocess pixels outside a partial world draw; the new strict
untouched-pixel guarantee applies to the opt-in reduced reconstruction path.
That broader assertion exposed the historical 100% behavior during testing; the
failure log is retained rather than relabeled as reduced-path acceptance.

Atmosphere/sky routing is prepared once from the complete original scene, because
it can use camera state from a later draw. Batches share those prepared states.
Geometry, texture and emission containers retain one owner and are restored after
batching, including on exceptions. Coverage replay and batching are reported as
GPU work separately from the count of original guest scenes.

The existing persistence fixture now exercises an opaque draw and an intervening
transparent world draw within one scene. It checks reduced execution, selected
FXAA, retained HUD edges, untouched guest depth, and every pixel safely outside
the original triangle, including pixels inside its bounding rectangle. An
alpha-tested world triangle overlaps the retained HUD but discards all its
fragments; the entire output remains byte-identical. Disabling reconstruction
fails the execution assertion; removing shader alpha rejection fails retained
output preservation. All temporary mutations are restored. Synchronization
validation found a missing depth-store dependency in the scratch FXAA pass;
the corrected barrier includes depth writes. The reusable FXAA source image also
orders prior shader reads before its next discard/transfer write.

A destination-alpha regression additionally places a point-sampled alpha step
under a later `D3DBLEND_DESTALPHA` draw. Its first probe assumed RGBA, but RX 9070
normally selects RGB565, whose destination alpha is implicitly 1. The fixture now
checks the selected format and uses a renderer-constructor preference to exercise
the RGBA8 fallback explicitly, without altering reported device capabilities or
process settings. Both defaults and explicit RGBA are tested. Sampling alpha from
the reconstructed image fails the RGBA regression; retaining the original fragment
alpha passes. This is internal format selection for testing, not a launcher option.
RGBA persistence/alpha cases pass at 50% and 67% with clean synchronization validation.

The authored coverage shader is `host/world_coverage.frag`. Its checked-in header
is reproduced with `glslangValidator -V host/world_coverage.frag --vn world_coverage_frag_spv -o host/world_coverage_frag.h`
from `tools/m4-crt-heap-carry/`; the local SDK reproduces its bytes exactly, and both inputs are pinned in the canonical host manifest. They contain
project-authored shader code, not translated game code. No new runtime shader
compiler or DLL is packaged.

Final source-pinned development host:
`e6deb25f762c029f8f4393554c61449e7204d29aa02ae303ccae1c3c89ec31dc`.
It builds seven host objects with no translated regeneration and retains the same
translated DLL. Both 100% and 50%-requested native runs complete 2,200 actual
Vulkan/DXGI presentations / 6,142 original guest scenes on RX 9070, with published
runtime 1.0.44 support inputs, the 13 verified published packs, 3440x1440, FXAA/16x
AF, sun strength 0 and ambient 1. Both have synchronization validation enabled
and zero diagnostics, and deliberately stop at the configured budget (exit 1).

At 50%, the world raster is 1720x720. The renderer records 1,475 reduced opaque
batches / 1,475 promotions, with 468,743 logical coverage draws in addition to
shading work. The log calls those batches "opaque scenes"; they are not additional
guest scenes. Captures 1801/2101 are
`6f13822cc471e0dc0e3e49e382819aabca76b32cb34c8caeed38629ed09b72ed` and
`6af77b31b2c6cf6e39686e2a925918825cf9ce017a26fb88b0d73a22a5b4ceb4`.
The world differs as expected. The timer's green-glyph masks match the 100%
reference at both frames; the Training/HUD capture was visually inspected.
This does not establish whole-HUD or original-executable equivalence.
The 100% captures still match the published runtime byte for byte at both frames.

Final focused checks pass: 18 world/lifecycle/persistence cases at 50/67/100 with
AA Off and FXAA; 25 actual bridge presentations with 50% requested; six standard
depth modes at 100% and scaled/odd-scaled/visible-scaled at 50% and 67%. The new
`odd-scaled` fixture mode supplies explicit output dimensions for 641x479 guest
surfaces; its pre-change call rejected the missing-output contract, and the new
mode passes. All GPU cases have clean synchronization validation. CMake build,
25 CTest cases, format-check, host-builder tests and style checks pass (web
formatting is enforced; other existing findings remain report-only).

The stronger untouched-pixel assertion was also run against the prior `740ed0f`
100% renderer and reproduces its whole-image FXAA behavior; it is not a regression
introduced by reconstruction. Private receipts, failure controls and captures
remain under `D:/Projects/MW34-retained-composition/local/retained/`.

This path adds geometry replay, texture-alpha sampling, an output-sized scratch
image, copies and queue synchronization. It avoids CPU pixel transport but is a
correctness implementation, not a measured performance improvement. Broader
alpha/guest-write sequences, nonzero directional lighting, performance and
independent review remain open; these checks do not enable FSR or frame generation.
Per-batch reconstruction still starts from retained output, so this is not yet a
validated, clean frame-level world-only history/input contract for temporal FSR.

## Remaining limits

The retained-pixel correction above supersedes the initial persistence failures.
Stage 2 remains incomplete pending broader ordered-write/fade/lifecycle coverage
and independent review. Resident opaque retained-color runs now have a reduced
shading/coverage-reconstruction path; blended and guest-write paths remain full
resolution by design.
FSR remains disabled; do not advance to Stage 3 implementation or mark this draft
ready on the strength of passing CI. Fresh-overlay, stock Training, visible
fixture lifecycle and synchronization checks have bounded evidence above.
Comprehensive guest-write/fade sequences, visible lifecycle checks inside the
game, broader startup and adapter depth coverage, the
reported periodic size change, raw RX 9070 Vulkan WSI, a second
physical PC and independent review remain open. Opaque runs after HUD can use
coverage reconstruction; blended/point and guest-write paths remain full resolution.
No build, asset, release or version was published or merged by these checks.
