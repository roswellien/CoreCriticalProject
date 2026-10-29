# First bounded MW3 Vulkan replay

The original game capture session `20261009-052504-158` recorded one selected
BeginScene/EndScene interval containing 589 successful draws, 51 unique textures,
and initial color/depth plus final color surfaces. The user confirmed “Training
and quit were normal.” The passive monitor recorded exit code 0 with no alerts
or dropped event segments.

`tools/graphics-trace/capture.hpp` snapshots complete vertex/index payloads,
viewport, selected render states, eight texture stages and top-level texture
pixels. Bounded budgets abort incomplete captures. `verify_capture.py` checks
payload hashes and structure; `package_replay.py` accepts only the implemented
state/format profile. Payloads and previews remain in ignored local reports.

`tools/vulkan-probe/replay.cpp` uploads the initial color/depth and recovered
textures, converts triangle fans/strips to triangle lists, and replays transformed
vertices with RHW, diffuse color, texture modulation, vertex fog, greater-than
depth testing, alpha blending and wrap/clamp nearest sampling. Flat and Gouraud
shading use separate shader variants. This is an offscreen prototype, not an
in-game Vulkan replacement or a world-space scene suitable for ray tracing.

Both pixel-center experiments replayed all 589 draws on the Radeon RX 9070 with
zero Khronos validation warnings/errors, including synchronization and teardown.
At 640×480, offset 0.5 yielded 74,723 exact pixels, 270,016 pixels within 8 in every
RGB channel (87.90%), mean absolute channel error 3.2363/255 and maximum error 185.
Offset 0 yielded mean error 5.7848 and 238,020 pixels within 8. These are measured
differences, not acceptance thresholds or proof of equivalent rendering.

The capture does not yet prove command closure: viewport clears, other draw
entry points, surface mutations and presentation are not comprehensively
intercepted. Legacy RGB565 quantization/dithering and raster/interpolation rules
also need controlled investigation. Next work should isolate these differences
and extend the observer before accepting a faithful renderer.

Build with the existing standalone CMake project, targeting
`mw34_vulkan_replay`. It requires Vulkan headers and glslangValidator, and builds
four replay shader variants. Run:

```powershell
./tools/vulkan-probe/run-replay.ps1 -CaptureRun reports/graphics-trace/20261009-052504-158
```

The runner hash-verifies/packages the capture, exports reference previews,
requires validation, runs both offsets and saves image differences and metrics.

## Controlled difference experiments

The same capture now has reproducible one-variable experiments:

| Experiment at offset 0.5 | Mean RGB error /255 | Pixels within 8 per channel |
| --- | ---: | ---: |
| Captured nearest sampling, perspective UV, screen-linear color | 3.2363 | 87.90% |
| Linear sampling | 1.9249 | 99.83% |
| Affine UV with nearest sampling | 6.6988 | 66.34% |
| Perspective color with nearest sampling | 3.2667 | 87.71% |
| Linear sampling, then nearest RGB565 quantization | 1.4585 | 93.32% |

All Vulkan runs passed synchronization validation with zero warnings/errors.
Linear filtering reduces the visible texture discrepancy substantially, but is
an experimental override. SDK enum definitions confirm the captured min/mag
values request point sampling. A subsequent read of the local wrapper config
shows `Filtering=appdriven`, forced `Resolution=1920x1440` and
`Dithering=forcealways`; this was not snapshotted during capture and does not
prove the effective wrapper state. A 3× nearest-filtered Vulkan render followed
by nearest, box or bilinear downsampling gave mean errors 3.2372, 3.1969 and
3.2578 respectively, so that simple scaling model does not explain the match.

Final RGB565 quantization increased exact matches from 37,128 to 178,608 pixels
for the linear experiment, while lowering the within-8 count. This experiment
does not reproduce per-draw precision or dithering. Both exact-match and
tolerance metrics must remain visible; neither alone establishes correctness.

Run `./tools/vulkan-probe/run-replay-experiments.ps1 -CaptureRun <run>` after
building the replay and generating reference previews. It compiles isolated
shader variants, checks each process exit, preserves logs/difference images,
and records hashes of the executable, compiler, sources and package. Default
replay semantics remain unchanged. Remaining work is to recover effective
filtering at the draw boundary, snapshot wrapper configuration during capture,
and close the observer's uninstrumented command paths.

## Filtering discrepancy recovered from live API calls

Capture `20261009-054720-663` closes the filtering investigation for this observed
profile. All 589 draws have successful legacy `GetRenderState` values 2 for
TEXTUREMAG (17) and TEXTUREMIN (18), matching the successful original-game
`SetRenderState` requests tracked from device creation. The stage-zero MINFILTER
and MAGFILTER getters report 1 in every draw. No corresponding stage filter
setter request was observed. The replay therefore needs the legacy filtering
path for this game/device/provider profile; the stage getters alone were
insufficient. This does not establish precedence for every possible mixed API
sequence or provider.

The observer now forwards and records filtering setters without changing their
arguments or results, retains only successful requests per device, and reads
both getter families. Typed fixtures verify successful/failed setter forwarding
and LastError preservation. `verify_filtering.py` independently correlates each
draw's history with the successful live setter log, verifies process identity
and the prelaunch wrapper configuration hash. Six causal controls reject absent
history, failed getters, absent setters, mismatching values, later stage setters
and mixed min/mag profiles.

Package format MW34SCN2 carries a per-draw nearest/linear selection. The host
still accepts MW34SCN1 and uses nearest for those packages. Legacy packaging is
explicit (`--filter-source legacy`) and fails without matching successful
setter/getter evidence, or when a newer stage setter makes precedence ambiguous.
Replay sampling defaults to the packaged selection; optional nearest/linear
arguments remain experiment overrides. The stage packaging mode remains the
default for older captures.

The evidence-based legacy replay renders all 589 draws with zero synchronization
validation warnings/errors. It has 306,677 of 307,200 pixels within 8 per RGB
channel (99.83%), mean error 1.9249/255, and maximum error 182. Remaining errors
still require precision, rasterization and command-coverage work. The user
confirmed Training and normal quit with this observer enabled.

```powershell
./tools/vulkan-probe/run-replay.ps1 -CaptureRun reports/graphics-trace/20261009-054720-663 -FilterSource legacy
python tools/graphics-trace/check_filter_controls.py reports/graphics-trace/20261009-054720-663
```

## Edge-error investigation and capture guards

The 523 pixels exceeding 8/255 per channel in the legacy-filtered replay are
concentrated predominantly along terrain and building edges. The outlier mask
is a local diagnostic, not proof of the cause. An optional D16_UNORM depth
attachment experiment reproduces the captured depth precision but worsens the
within-8 count to 305,777 and mean error to 2.0107/255, versus 306,677 and
1.9249/255 with D32. Both pass Vulkan synchronization validation. D32 remains
the default; `run-replay.ps1 -DepthMode d16` exposes the experiment.

The observer now discovers IDirect3DViewport3 through QI and device viewport
methods. During a selected capture, calls to Clear/Clear2, immediate-mode
Begin/BeginIndexed, strided draws or vertex-buffer draws abort collection with
an explicit unsupported-command reason. All original methods are still called
with their original arguments and results. This prevents those observed paths
from silently producing an accepted partial scene; it does not implement their
replay. Typed fixtures exercise all eight guards plus failed-command forwarding,
and verify results, LastError and selected input data remain preserved.

These guards do not establish comprehensive command closure. Other viewport
interface aliases, surface mutations, immediate-mode sequences begun outside
the selected interval, presentation and thread ownership still need coverage.

Live regression capture `20261009-055506-103` completed 589 draws without
triggering the new unsupported-command guards. The replay retained 306,677
pixels within 8/255 per channel, mean error 1.92493/255, and zero Vulkan
validation warnings/errors. The user confirmed Training and quit were normal;
the passive monitor recorded exit code 0, no alerts and no dropped segments.
Comparison reports now include an explicit outlier count, bounding rectangle
and mask, alongside exact and tolerance metrics. The next rendering work is
controlled edge/precision recovery and additional command/lifetime coverage.

## Saved-capture edge and precision experiments

`run-edge-experiments.ps1` uses verified legacy filtering on the guarded capture,
compiles isolated shader variants, and saves validation logs, hashes, image
metrics and outlier masks. All nine Vulkan executions passed synchronization
validation without warnings or errors. No new gameplay session was needed.

| Experiment | Mean RGB error /255 | Pixels exceeding 8 in any channel |
| --- | ---: | ---: |
| Baseline, offset 0.5 | 1.92493 | 523 |
| Offset 0.49 | 1.99342 | 1,353 |
| Offset 0.51 | 2.50996 | 2,427 |
| Vertex coordinates rounded to 1/16 pixel | 2.00324 | 1,453 |
| Vertex coordinates rounded to 1/256 pixel | 1.92494 | 523 |
| RGB565 shader quantization before blending | 1.53025 | 22,774 |
| 4×4 Bayer dithering plus quantization before blending | 1.99464 | 30,072 |
| 3× render, offset 0.5, nearest downsample | 1.92542 | 560 |
| 3× render, offset 0.5, box downsample | 2.83679 | 16,642 |
| 3× render, offset 0.5, bilinear downsample | 3.08589 | 22,824 |

A scaled offset of 1/6 with all three downsample filters also worsened error
(mean 3.83–4.10). These results reject the tested simple corrections as a clear
improvement on this capture. Quantization raises exact matches to 157,666 but
substantially worsens the outlier count; it is not a fidelity fix. Shader
quantization occurs before blending and does not model a hardware RGB565 target
or the wrapper's dithering algorithm. Vertex snapping and downsampling are
explicit hypotheses, not recovered legacy rules.

The normal renderer defaults remain unchanged. Offset experiments now accept
finite values in [0,1]. Optional shader macros are absent from ordinary builds.
`compare_replay.py --resize-filter` requires an explicit resize choice and
records original candidate dimensions and the chosen filter in its report.
Further fidelity work requires additional evidence about edge coverage and
target precision rather than choosing an empirical correction from this frame.

## Hardware RGB565 color attachment experiment

The replay can now use a real `VK_FORMAT_R5G6B5_UNORM_PACK16` color attachment,
instead of only quantizing shader output. It checks color attachment and blend
format support, packs the initial target, and decodes the two-byte readback.
The format therefore applies precision to stored blending results as well.
RGBA8 remains the default; RGB565 is an explicit experiment.

On guarded capture `20261009-055506-103`, hardware RGB565 gives 174,022 exact
pixels and mean RGB error 1.49501/255, versus 37,131 exact and 1.92493/255 for
RGBA8. However, the pixels exceeding 8/255 rise from 523 to 20,246. This does
not establish a fidelity improvement, nor reproduce the wrapper's dithering
algorithm. Both render modes pass synchronization validation.

`verify_target_formats.py` constructs eight authored 8×8 fixtures covering red,
green, blue, retained initial-target pixels and alpha blending in both formats.
All 512 checked pixels matched their independent expected values exactly, and
all eight runs passed validation without warnings/errors. This checks channel
packing, transfer/readback and blending; it does not claim game equivalence.

```powershell
python tools/vulkan-probe/verify_target_formats.py build/vulkan-replay/Release/mw34_vulkan_replay.exe build/vulkan-replay reports/vulkan-probe/target-formats
./tools/vulkan-probe/run-replay.ps1 -CaptureRun <capture> -FilterSource legacy -ColorMode rgb565
```

Target precision alone does not explain the remaining discrepancy. The next
capture work should recover further command/lifetime behavior and permit
comparisons across independently selected scenes before changing defaults.

## Delayed scene selection

The graphics launcher accepts `-CaptureSkipScenes N` (0–36,000 successful
BeginScene calls) and `-CaptureMinimumDraws N` (0–2,048). The request is read once;
the manifest records requested/skipped intervals and the selection minimum.
Malformed requests stop capture attempts without changing game rendering.

A selected interval below the minimum is preserved as `short-interval-N` rather
than presented as the accepted `frame`. At most four candidates are attempted.
Each candidate retains the existing 64 MiB storage/512 MiB scan budgets, so
candidate storage is bounded to 256 MiB. Unsupported commands still abort
collection instead of being silently skipped. A draw-count minimum selects
substantial intervals; it does not itself prove they contain world geometry.

The first delayed test, `20261009-061055-400`, skipped 300 intervals and captured
three untextured draws. Its data passed structural checks, but the replay
correctly rejected the unsupported render-state profile. It is retained as
evidence of a short interval, not counted as a successful gameplay replay.
The user confirmed normal Training and quit. `compare_capture_scenes.py` reports
geometry fingerprints and texture-payload diversity without claiming that a
different fingerprint alone proves a different gameplay scene.

The selection-enabled delayed run `20261009-061307-498` preserved one short
interval and accepted its second candidate with 140 draws, 17 unique texture
payloads and seven texture payloads absent from the earlier capture. The
reference preview shows a moved viewpoint and a laser shot. The laser draw
keeps depth testing enabled while disabling depth writes; replay packaging
initially rejected this newly observed state rather than guessing.

MW34SCN3 now stores per-draw depth-write enable. Eight pipeline variants cover
flat/Gouraud shading, blend enable and depth writes independently. SCN1/SCN2
remain readable and retain their previous depth-write-enabled behavior. Four
authored overlapping-geometry fixtures distinguish depth test from depth write
in D32 and D16: all 256 pixels match exactly, with zero validation messages.

The delayed replay passes validation, with 11 pixels exceeding 8/255 per channel
across the full target. Crucially, the interval changes only 1,878 reference
pixels; most target pixels were retained from earlier rendering. The changed
region union includes 1,879 pixels, of which 1,868 are within 8 per channel
(99.41%), 79 match exactly, and mean RGB error is 2.26805/255. The full-target
mean of 0.01387/255 must not be interpreted as complete-frame fidelity.
Comparison reports now optionally compute this union from the initial target,
including extra candidate changes so incorrect writes cannot escape scoring.

The user confirmed normal Training and quit for both delayed runs. The passive
monitor for the selection-enabled run recorded exit code 0 and no alerts or
dropped segments. Further work should recover multiple scene intervals and
presentation boundaries to validate complete frames, including HUD and effects.

## Live presentation boundary recovery

`presentation.hpp` observes eligible IDirectDrawSurface4 objects through
DirectDraw4 surface creation, interface queries, device render-target creation
and attached-surface discovery. Typed call-through wrappers record Flip, Blt
and BltFast outcomes with surface metadata, cumulative successful draw counts
and completed BeginScene/EndScene intervals. The original renderer still runs.
Texture-only surfaces are excluded from this observer.

Run `20261009-073222-678` recorded its bounded first 2,048 transfer events:
502 Blts and 1,546 Flips. The verifier identified 1,044 successful gameplay
primary-surface Flip candidates at 640×480, on one observed thread and primary
surface, with scenes closed. Among successive gameplay flips, interval-count
frequencies were 1:72, 5:133, 6:555, 7:1 and 8:282; successful draw deltas ranged
from 1 to 1,538. This empirically establishes that one scene interval is
insufficient to represent a complete frame. The event budget was reached, so
the receipt covers that prefix rather than the entire session.

Fixtures check surface creation and successful/failed Flip/Blt/BltFast
forwarding, return values, LastError and selected input data. Seven causal
controls reject missing events, mixed process/thread identities, failed flips,
open scenes, backwards counters and missing primary-surface classification.
`verify_presentation.py` verifies the trace/provider/source identities before
analyzing the presentation timeline. A successful Flip is a presentation
candidate; the observer has not yet captured every intervening command,
presentation pixels, other interface aliases, or physically displayed output.

The next implementation step is to arm at a primary flip and record through the
next matching flip, preserving the backbuffer before swapping. It must include
all scene intervals, clears, resource mutations and direct surface operations,
with conservative rejection of unimplemented paths. Full-frame comparisons
must then cover the world, HUD and effects together.

The user confirmed Training and normal quit with presentation tracing enabled.
The passive monitor recorded exit code 0, no alerts and no dropped segments.
This completes the live regression check for boundary observation; full-frame
capture and replay remain future implementation work.

## Presentation-window capture prototype

Added 2026-10-09 after the standalone windowed Vulkan viewer. Optional
`-CapturePresentation -CaptureSkipFlips N` arms a capture after a successful
primary flip and collects across BeginScene/EndScene intervals until the next
matching primary flip. The final backbuffer snapshot is taken **before** that
flip; failed flips, changed presentation thread/surface, changed render target,
unsupported clears/draw paths and observed Blt/BltFast transfers reject the
capture. Texture snapshots and existing storage/draw limits remain bounded.
Menu flips before any completed 3D scene do not consume the delay in the final
implementation. A completed scene counter alone is still not proof of Training.

The result lives under `present-frame` and explicitly has
`command_coverage_complete=false`. Unobserved surface aliases, direct writes,
clears and transfer replay still need recovery. The scene verifier rejects
these diagnostics even when the flip boundary closed. This is a capture
foundation, not accepted full-frame replay or playable Vulkan integration.

The initial live diagnostic `20261009-210355-562` used the earlier menu-inclusive
delay rule. After 300 primary flips it captured initial color/depth at 640x480,
then rejected an unsupported surface transfer. The timeline identifies a
menu Blt with flags 0x01000000; no 3D scenes or draws had yet occurred there.
The first 2,048-event prefix and its original source/binary snapshots remain
unchanged. The ordinary presentation verifier does not accept this run because
its required modules.json observation is absent. It adds no verified gameplay
or complete-frame credit.

The user was remote and could not perform Training/quit validation. The agent
canceled only its own diagnostic process; forced cancellation is not normal
quit evidence. The revised menu-selection guard was compiled separately under
`build/graphics-trace-present-check` while the diagnostic was open, without
replacing its loaded DLL.

Both builds passed `/W4 /WX` and the typed forwarding/FP/LastError fixtures.
New boundary checks cover ignored non-primary/open/failed arm candidates,
one-shot completion, and rejection for changed surface, changed thread, open
scene or failed closing flip. The earlier 589-draw capture and authored scene
fixture still pass payload verification. Three acceptance controls reject the
actual diagnostic, forged scene scope with incomplete coverage, and forged
coverage completeness with presentation scope; receipt:
`reports/graphics-trace/present-gate-check-20261009/acceptance-controls.json`.

Next: record and implement ordered clears and bounded surface copies, validate
their color/depth/HUD effects with independent fixtures, then capture a Training
presentation window when a local gameplay check is available. Until then,
offline development can proceed without requiring the user to operate MW3.

## Ordered command replay and local capture check (2026-10-10)

The offscreen and windowed Vulkan prototypes now share an ordered command
executor. SCN4 extends the SCN3 payload with a bounded table of ten-word
commands: draw references, rectangular color/depth clears, and opaque copies
from immutable RGBA8 source snapshots. Each stored draw must appear exactly
once. Earlier SCN1/2/3 files retain their existing draw order. Copies preserve
depth across a render-pass split; clears can affect color, depth or both.
Rectangles and reserved fields are checked before GPU execution.

The independent CPU oracle passed 24 combinations of six command sequences,
D16/D32 depth and 1x/3x rendering: 7,680 exact pixels and zero Vulkan validation
messages. Seven controls rejected unknown commands, overflowing or invalid
rectangles, NaN depth, duplicate/omitted draws and RGB565 copy replay. Receipt:
`reports/vulkan-probe/ordered-commands-20261010/verification.json`.

Copies currently require RGBA8 output and equal logical source/destination
extents. Color keys, alpha copies, stencil, arbitrary stretches, source/target
aliasing and render-target feedback remain unsupported. These authored tests
do not establish that live MW3 clears or HUD transfers have been recovered.
The observer now records actual clear values/rectangles and Blt/BltFast input
rectangles/effects before rejecting unsupported operations.

The first local capture `20261010-054219-796` reached its 2,048-draw limit within
one scene. The user reported normal Training and quit, but module evidence was
missed before process exit. It remains a diagnostic. Presentation diagnostics
now allow up to 8,192 draws while retaining the 64 MiB storage and 512 MiB scan
budgets; single-scene replay acceptance remains limited to 2,048 draws.

The second local run `20261010-054556-752` closed one matching primary-flip
interval: six scene intervals, 1,272 draws, initial color/depth and final color,
with 1,351 resource files totaling 2,415,168 bytes. No observed unsupported clear
or transfer occurred in this selected interval. The provider/module and
presentation verifiers passed. The passive monitor
`reports/mw3-monitor/20261010-054622-c7605897` recorded normal exit code 0, no
alerts and no dropped segments; the user confirmed normal Training and quit.
Module inventory was collected manually while this process was open. The
launcher now attempts automatic collection and handles path separators and
WOW64 module paths; that final automation revision still needs its next launch.

The capture deliberately retains `command_coverage_complete=false`: unobserved
aliases, direct writes and other command paths remain unresolved. Boundary
completion alone is not full-frame equivalence. Next, build a separate
diagnostic replay/comparison for this interval, retaining conservative
acceptance gates, then recover any missing world/HUD/effect commands indicated
by that comparison.

## First flip-interval diagnostic replay (2026-10-10)

`replay_presentation_diagnostic.py` now packages observed draws from an explicitly
incomplete presentation interval into a separate output directory. It validates
scene nesting, draw ordinals, per-scene counts, boundary closure and every
resource's size/hash using the shared payload checks. It rejects unsupported
events and retains `diagnostic_only=true` and `command_coverage_complete=false`
in its receipts. The ordinary scene verifier still rejects presentation input.
The diagnostic packaging CLI requires `--diagnostic-presentation`; no source
manifest is rewritten to claim scene acceptance.

Replay of `20261010-054556-752` rendered all 1,272 draws with 77 packaged textures
and zero Vulkan validation messages including teardown. At the previously used
0.5 pixel offset, D32/RGBA8 output, 283,920 of 307,200 pixels (92.421875%) differed
by at most eight levels per channel. Mean absolute channel error was 3.8170;
23,280 pixels exceeded that tolerance. Within the union of pixels changed from
the initial target, 206,710 of 229,990 met the tolerance. Visible HUD omissions
and world differences remain. Receipt and images:
`reports/vulkan-probe/present-comparison-20261010/report.json`.

Targeted D16, RGB565 and zero-offset experiments did not resolve the mismatch.
A separate hypothesis replaced initial depth with zero: 297,706 pixels met
the eight-level tolerance, but HUD elements disappeared and mean error rose
to 4.0624. This is altered-input evidence, not a recovered clear command or
an improved accepted renderer. It indicates that depth history and unobserved
HUD operations need investigation together. The source's observed-surface
filter currently includes primary/backbuffer/3D-device caps but not Z-buffer
caps, so depth-surface transfers are a concrete observation gap to address.

Six negative diagnostic controls passed (coverage overstatement, nested scene,
draw outside scene, wrong cumulative count, unsupported command, overstated
footer). The ordinary gate still admitted the prior 589-draw scene and rejected
the presentation diagnostic plus two forged scope/coverage controls. No playable
Vulkan integration or full-frame equivalence is claimed. Next: observe depth
surface transfers and other HUD paths, capture their actual parameters, then
replay only recovered semantics and repeat the comparison.

## Observed depth and CPU surface commands (2026-10-11)

The [surface command work](live-native-rendering-current-work.md) now observes
depth surfaces, actual D16 zero fills and RGB565 CPU Lock/Unlock spans. The second
genuine Training capture records 1,082 draws, two fills and two lock spans,
including 8,486 changed CPU pixels. Its ordered SCN4 replay uses clears and copies
only changed pixel runs at their observed positions.

A same-frame comparison improves the eight-level per-channel tolerance result
from 84.85% for deliberately draw-only replay to 99.01% with the surface commands;
outliers fall from 46,528 to 3,039. Both GPU runs have zero validation messages.
The user confirmed normal Training and quit; exit code is zero, with a retained
temporary window warning and later recovery. Complete command coverage, exact
frame equivalence, moving-frame resource persistence and live native gameplay
remain open. Receipts and images are linked from the work record.
