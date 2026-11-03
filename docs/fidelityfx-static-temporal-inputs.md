# Static temporal inputs (FidelityFX P2b)

Development work for [issue #107](https://github.com/roswellien/MW3Recomp-Private/issues/107),
following [authenticated camera history](fidelityfx-camera-history.md).
The execution boundary is immutable original static-source/camera observations to
private GPU depth, motion and validity images. FidelityFX dispatch, object motion,
reactive masks and frame generation remain outside this change.

## Opt-in diagnostic contract

`MW34_TEMPORAL_INPUTS=1` enables the diagnostic pass. `MW34_TEMPORAL_JITTER=0|1`
defaults to zero and requires temporal inputs when enabled. Malformed settings fail
explicitly. These are development environment settings, with no launcher preference.

The original renderer remains authoritative for guest color, depth transfers,
Lock/Blt/readback, presentation and HUD. The diagnostic pass runs once per original
public renderer submission, outside reduced-resolution shading/coverage replay.
It allocates separate R32_SFLOAT depth, R32G32_SFLOAT motion, R8_UNORM validity and
D32_SFLOAT visibility images at the configured internal world dimensions.
The three exported images finish in shader-read-only layouts. Completion occurs
only at the real guest Flip; capture never reads guest memory.

Motion is previous minus current unjittered render-pixel position, with X right and
Y down. Perspective interpolation reconstructs the same static surface point in
both cameras. Previous near/far and screen bounds constrain validity. Exported depth
is reversed infinite `near_clip/camera_z`; finite guest far clipping still applies.
Visibility uses the existing `near_scale/camera_z` depth convention. These two near
values are distinct. The existing guest half-pixel center is applied exactly once.

Render-only jitter is Halton bases 2 and 3, centered about zero, with sequence length
`ceil(8*(output_width/internal_width)^2)`. A view advances once per completed real
frame, independent of scene count. Rejected/missing/reset history restarts the phase.
Raw geometry and supported transformed/lit occluders receive the same pixel offset.
No original camera or culling state is modified.

The diagnostic pass preserves original draw/clear order, culling, depth state and
texture alpha rejection. Unproved geometry masks its actual rasterized footprint
with invalid motion. Unsupported alpha-bearing model geometry rejects the view.
Known output-only HUD work retains its existing output path. Unknown coverage does
not acquire static zero motion by default. A rejected frame cannot supply the next
frame's diagnostic history.

## Original static-source producers

Inspected MW3 U.S. retail 1.2 `Mech3.exe` SHA-256:
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
Addresses below use preferred base 0x400000. LLVM 21.1.8 static inspection and
bounded native observations supplied this evidence; original instruction bodies
and private disassembly stay local under `local/p2b/`.

Context+0 is a vtable, rather than the scenery ownership root. A recorded parent
with no reciprocal child membership is insufficient for static admission.

| Producer | Recovered contract |
| --- | --- |
| `sub_004F6720` | Original cell-render scope owns the selected cell data, frame locals and visible-table row. Bank/index, sector-array entry and 72-byte cell identity must agree. |
| `sub_004F5910` | Original node dispatch is observed only inside that cell scope, at exact original return sites. |
| Return 004F69DC / 004F6B59 | Separate unfiltered/filtered calls use the cell's bounded object list at +3C, count from +38 high word, and original ESI index. Selected root membership must be unique. |
| Return 004F6AE0 | Placement list at cell+44 has bounded count at +40 and 0x44-byte records. Original EBX identifies the record, its first word the subtree, and its next 12 words the independently produced transform. |
| 004F6AB8..004F6AC9 | Placement producer copies the record matrix to type-five data+30 and data+60. Both copies must agree at the observed producer boundary. |
| `sub_004F4AB0` | Type-five renderer applies the selected local transform; reciprocal descendant membership and supported type-five storage are required. |
| `sub_004F4370` | Camera-offset setup freezes the cell/tile offset values into this original scope. Different offsets have different static identities. |
| `sub_004F4170` / `sub_004F41B0` | Camera setup entry/delegate: the first supplies zero offset; the delegate forwards the optional offset to 004F4370 and refreshes camera projection/clipping state. |
| `sub_0051E930` | Matrix-stack copy updates data+60 with camera-dependent render storage. It is checked at the placement producer, then excluded from stable cross-frame identity. |

Static placement is built from independently authenticated cell/local matrices.
It is compared with the captured local-to-camera transform and every original
world vertex using existing world-projection tolerances. Reconstructing a world
matrix solely from camera and local-to-camera values cannot establish ownership.
Nonfinite transforms, unsupported animation/storage, ambiguous membership and
source changes lose admission.

Exact mesh and ownership bytes are shared immutable snapshots. Node/mesh/polygon,
cell/record/route/tile identity, pose, texture version and load/lifetime epochs
must agree across consecutive real frames. Original retirement 004EB050/004EAF90
and tracked guest heap releases invalidate retained sources, including freed blocks
that contain tracked cell/pose addresses. Reader-epoch changes clear current lookup
owners; deferred owners retain their budget charge until released.

At most 2,048 source entries and 64 MiB are retained, including pending/completed
owners and static-source metadata. Overflow fails explicitly. GPU attachments use
at most eight view slots and 512 MiB; missing views release their slots at completion.
Temporal Off allocates no diagnostic attachments.

## Validation scope

The authored RX 9070 fixture checks sampled depth, signed pixel motion, repeated
submissions within a real frame, jitter phases, opaque/texture-alpha occlusion,
reset publication and missing-view cleanup. An independent ray/plane oracle checks
camera rotation plus XYZ translation at 50%, 67% and 100% internal resolution.
A deliberate reversed-motion shader fails the motion assertion; canonical sources
are restored afterward. These GPU fixtures are separate from live native gameplay.

Native acceptance remains incomplete. On November 2, a development host using the
published 1.0.46 translated module and all 13 verified published asset packs reached
live Training and completed 3,300 RX 9070 Vulkan/DXGI presentations with the existing
driver. The registry-selected control profile uses P/W/D; earlier scripts using S
and arrow keys did not establish moving-camera coverage. Corrected input demonstrated
movement and tutorial advancement. No Vulkan validation errors were found, but
moving gameplay repeatedly rejected history with guest-write/view-state resets.
The available stationary captures had zero valid static pixels. Neither result
satisfies native motion acceptance; P3/P4 and frame generation remain gated.

The private preparation required restoring normal_codec.py from the exact signed
release's source commit because that file was absent from the published preparation
payload. This does not establish successful preparation from a pristine release.
No installed runtime, asset pack or driver was changed.

After temporary per-draw tracing was removed, the cell/source CPU fixture, world
binding fixture, seven function-table tests, two host-builder tests and nine RX 9070
temporal GPU cases passed. The GPU cases cover world motion/validity at 50/67/100%
with jitter Off/On, plus three depth precision runs. These authored fixtures do not
replace the missing native acceptance. The newer P2a surface-access dependency
(c998419) is integrated locally. Its comparison completed 2,200 presentations with
zero Vulkan validation errors; the same write resets begin at frame 1401 after
power-up at frame 1400. Authoritative color captures at 801/999/1801/2101 match the
pre-dependency run byte-for-byte. At that checkpoint the actual writing producer was unknown;
view-state in the last-draw log alone does not identify a main-camera failure.
The write guard remains enabled. All 27 CTest cases passed across the initial run
and a targeted source-pin recheck. Native acceptance, final regression checks and
independent review remain pending.
No normal playtest release is produced by this development branch.

## Powered-up depth-clear correction

The subsequent bounded trace identified a DirectDraw z-buffer fill after power-up:
rectangle (962,658)-(1005,758), clear value zero, original return site 005777AB.
A full z-buffer clear at return 0057788F precedes it. No CPU surface-write or HUD
fallback trace fired at the first reset. These are observations from the same
verified executable; no new original-function hook is introduced.

GPU depth fills now carry their real frame and target into the diagnostic pass.
A depth-only, clear-only submission is accepted only with bounded rectangles and
a matching current pending view/diagnostic slot. It clears private visibility in
order while retaining color-associated depth/motion/validity. Untagged, stale or
wrong-target writes, color fills and CPU writes retain conservative rejection.

Six RX 9070 temporal GPU cases pass at 50/67/100%, jitter Off/On. The regression
preserves underlying metadata and proves that geometry previously hidden behind
the old depth can cover the cleared rectangle. Omitting the diagnostic depth clear
in a private negative control fails that assertion. The earlier whole-view guest
write regression still passes. All 27 CTest cases and enforced web style pass;
other style categories remain report-only under the repository policy.

The corrected native run completed 3,300 RX 9070 presentations with zero Vulkan
validation errors. Frames 801/999/1801/2101/3001 match the pre-fix authoritative
color captures byte-for-byte. Power-up no longer causes a continuous reset:
1,574 of the 1,900 post-power frames report reset=none. The remaining 326 frames
still reject history; the first is 2042. Captured temporal images at
801/999/1801/2101 still contain zero valid static pixels, and 3001 has no accepted
temporal image. Thus the power-up defect is narrowed, while native visibility
coverage and remaining history rejection still block P2 acceptance. No FSR or
frame-generation dispatch is enabled, and no release is produced.

## Visible source and color isolation

A private offscreen prefix replay isolated the earlier all-invalid result: the
72 inspected `healthy` draws produce 184 valid pixels alone, all occluded by earlier
native geometry. That replay is diagnostic evidence, not live native acceptance.
The visible occluder was `g29`, an ordinary 39-polygon, 54-vertex mesh in an existing
cell placement, excluded by the candidate-name filter. No new original hook is
needed. It is now an opt-in diagnostic candidate, still subject to the existing
cell/placement/descendant ownership, source-byte/lifetime, texture-version and
projection checks. The name itself never establishes static validity.

Its geometry travels in a separate immutable diagnostic model. The original TL
vertices, color commands and guest depth remain authoritative. Only candidates
whose captured vertex bytes remain identical qualify; reconstructed/clipped changes
are rejected. Diagnostic geometry shares the existing immutable upload queue and
has an independently adapted widescreen projection. The ordinary color path does
not consume it. A native experiment that used the ordinary raw-world color bridge
changed the reference image and was rejected.

The corrected native run completed 2,200 RX 9070 Vulkan/DXGI presentations with the
published 1.0.46 translated module, all 13 verified published packs, 100% scale,
jitter On and lighting Off. Four color captures at 801/999/1801/2101 match the prior
reference byte-for-byte. Valid static coverage is sparse: 57,015 pixels at 801,
56,999 at 999, 57,015 at 1801, 56,725 at 2031, 53,684 at 2071 and 49,031 at 2101.
All valid pixels at 2071 and 2101 have finite motion exceeding 0.01 render pixels
during W-key movement; median vectors are (1.36084,-0.86129) and
(3.47107,-0.26893). Vulkan validation reports zero errors. This demonstrates live
native moving inputs for the inspected surface, not full-scene coverage or FSR.

The first movement rejection at 2042 is a tracked 32-byte source-storage release.
The lifetime guard remains intact. History now retains the first rejection so a
later depth clear cannot replace a transition with a misleading guest-write label.
The regression fails the old behavior and verifies both rejection and recovery.
Eight transitions remain among frames 1401..2200; other post-power frames retain
history. This interval differs from the earlier 3,300-frame test.

An authored GPU case places diagnostic geometry separately from original TL color
and requires unchanged color/guest depth plus valid diagnostic coverage. All six
50/67/100% jitter Off/On cases pass; a private color-alias control fails the new
assertion. The 70-case renderer regression matrix and launcher .NET checks pass.
The initial .NET run lacked SDL3; the existing SHA-256-pinned 3.4.18 archive supplied
the ignored test dependency before the successful rerun. Remaining native modes,
current-develop integration, final source matching and independent review are still
required before P2 acceptance. FSR dispatch and frame generation remain Off.

## Current-develop integration checks

The topic now includes develop through e8129d3, retaining the newer material,
headlight and controller changes alongside temporal metadata. Training readers
1–4 retain their load-epoch invalidation; failed and unrelated opens do not
advance that epoch. Default and manual campaign-lighting fixtures pass.

The integrated host completed two 2,200-presentation RX 9070 Vulkan/DXGI runs at
100% and 50%, with jitter On, lighting Off and all 13 verified published packs
from runtime 1.0.46. Both stopped at the configured budget and reported zero
Vulkan validation errors. The 100% color captures at 801/999/1801/2101 match the
pre-integration reference byte-for-byte. At 50%, the diagnostic target is
1720×720 for the 3440×1440 output: 14,250 valid pixels at 801, 14,240 at 1801,
13,413 at 2071 and 12,252 at 2101. Every valid moving pixel at 2071/2101 has
finite, nonzero motion; median vectors are (0.68048,-0.43210) and
(1.73544,-0.13282) render pixels. This remains sparse static-surface coverage.

All 182 host-source and 196 repository-dependency hashes match the integrated
build receipt; its commit field records the pre-merge checkpoint because the
build started during local integration. The merged files were checked against
the receipt afterward. All 30 CTest checks, the 70-case renderer matrix, six
50/67/100% jitter Off/On temporal GPU cases, source lifecycle checks and launcher
.NET suite pass. Shader compilation reproduces the prior canonical binaries.
Private broken variants for motion sign, output-pixel units, jitter leakage,
older history, source mutation and resource invalidation fail their respective
checks. Ordinary sources remain intact.

Same-source native temporal-Off and jitter-Off runs now also complete 2,200
presentations at both 100% and 50%. All four 801/999/1801/2101 color captures
match their corresponding jitter-On references exactly; all four additional runs
report zero Vulkan validation errors. Off produces no temporal images.

The moving-source GPU regression keeps a valid camera pair while an object moves
or loses its source proof. All six scale/jitter cases remain invalid for that
object; a private variant omitting the static-source condition fails the assertion.
Alpha, unknown occlusion, color/guest-depth isolation, source-lifetime and
per-submission-completion controls also fail their respective checks.

The full published lighting profile also completes 2,200 presentations with
sun, effects, shadows and campaign lighting enabled, both with temporal diagnostics
On and Off. Both runs have zero Vulkan validation errors; their four color captures
match exactly. The On run retains the same valid static coverage counts at
1801/2071/2101 as the lighting-Off run. Lighting-On color differs from lighting-Off,
so this comparison exercises an active rendered lighting path.

Stock configurations and camera/zoom/pause/reload coverage remain required. Independent
review and a draft PR also remain open. No upscaler or frame generation is
dispatched, and these checks do not establish P2 (Stage 3) acceptance.

## Stock camera and pause checks

A fresh stock run completed 4,600 RX 9070 Vulkan/DXGI presentations with no
replacement-pack paths, optional lighting or effects, and zero Vulkan validation
errors. It retained 58,212 valid static pixels at 801/1801 and 49,186 at 2101.
During the D-key turn at 3001, all 44,222 valid pixels have finite, nonzero motion
(median horizontal motion 34.160 pixels). These are live original camera/input
transitions, not saved-scene replay.

V cycles demonstrate mode-zero/one history and mode-two rejection. Switching
controllers invalidates first; mode one has 55,725 valid pixels at 3901. Unsupported
mode two has no admitted temporal image at 4051. Returning to mode zero recovers
29,051 valid pixels at 4151. Escape produces one actual pause entry and exit:
history is invalid during pause, no image is exported at 4251, and 29,186 valid
pixels recover at 4401. The deliberate frame-budget exit is not normal shutdown.

Middle-button input executes the original zoom drawing route while main coverage
remains valid (29,696 pixels at 3601), but no independent zoom temporal view is
admitted in this run. This does not establish native positive zoom coverage;
main/zoom positive isolation remains fixture evidence. Same-Training reload,
native near-plane acceptance and menu/Lab checks remain open.

## Instrumentation and preliminary timing

The validation runs above are not representative gameplay performance tests.
With all published packs, their live 800–2200 interval is about 12.8 FPS even with
temporal diagnostics Off. A separate minimally instrumented run removes Vulkan
validation, scheduled captures and optional logs; it retains the world bridge's
required log and frame timing. The DXGI bridge defaults to VSync, yielding about
60 FPS. The existing development VSync-Off option removes that ceiling.

Single 800–2200 interval measurements at 3440×1440, FXAA, AF16, 1200/1100 distance,
all published packs and lighting On are:

| Host / temporal diagnostics | VSync | Mean presentation FPS |
| --- | --- | ---: |
| Current topic / Off | On | 59.97 |
| Current topic / Off | Off | 80.39 |
| Current topic / On, jitter On | Off | 61.53 |
| Published runtime 1.0.46 / Off | Off | 83.08 |

Each run completes 2,200 presentations and 7,689 guest scenes. These are single
scripted virtual-clock throughput samples, not repeated or real-clock benchmarks;
no regression percentage is established. Diagnostic depth/motion rendering has a
measurable cost here and supplies no upscaling or frame-generation benefit yet.
The historical roughly 100 FPS RX 9070 result used another scene/asset setup;
its difference from these numbers remains unisolated. User installation, driver
and persistent graphics settings are unchanged.

## Large-origin near-plane precision correction

A new authored GPU oracle places a stationary triangle just beyond the near plane
at map-sized world offsets, with the camera and placement sharing the same stored
float origin. Independent double-precision subtraction gives identity and zero
motion. The old absolute-world shader path exceeds the 0.02-pixel motion budget.
An initial fixture-ordering attempt also inherited a rejected submission; that
setup was corrected before establishing the failure against the old shaders.

Motion now transforms the interpolated current-camera point directly into the
previous camera. The CPU subtracts camera origins in double precision before
forming the relative transform; the GPU never adds and cancels the absolute map
origin for motion. Static-source placement/lifetime admission remains mandatory.
The unused GPU world-point varying and uniform rows are removed. All six
50/67/100% jitter Off/On oracle cases pass without validation errors. Final native
and broader regression checks for this shader correction are still pending.

The corrected full-pack same-Training reload sequence also completes 3,000
presentations and 7,922 guest scenes with zero Vulkan validation errors, using
ordinary pause, Quit, Pilot Accept and Training launch controls. It exports no
mission temporal image during loading, then recovers 57,015 valid pixels at 2001.
That run predates this precision correction and is not its final native validation.


## Remove discarded temporal polygon reconstruction

The November2 performance investigation found that temporal-only capture could
rebuild a polygon and compute its lighting before discarding it at the caller's
byte-identity check. The production shortcut is restricted to different corner
counts: reconstruction emits one vertex per original corner, so its payload
length cannot equal the submitted TL payload. Equal-count reconstruction and
projection admission remain unchanged. The submitted TL draw continues to
provide ordinary color and unknown diagnostic occlusion; no source/lifetime
check or original game producer is bypassed.

The production adapter now lives in `world_polygon_capture_stage.inc`, included
by the existing direct binding and an authored fixture in the existing world
geometry executable. The fixture proves exact source identity, early rejection
of different counts, preserved authoritative reconstruction and preserved
same-count reconstruction. Removing the guard in a private control fails the
rejection assertion. Six RX9070 scale/jitter GPU cases pass with zero validation
errors; current CTest is30/30, with style and format checks passing.

Matched minimally instrumented Training runs use all13 current published packs,
runtime/support1.0.46, unchanged RX9070 driver, 3440×1440, FXAA/AF16, distances
1200/1100, lighting On, world100%, jitter On, virtual16.666667 and VSync Off.
Optional logs/captures/validation are disabled equally; required world logging
and frame timing remain. Each run completes2200 presentations/7689 guest scenes.
The interval is800–2200,1400 presentation intervals per run. The harness checks
for competing games and compilers and stops only its owned test if one appears.
No competing game/compiler or timeout occurred in these four runs.

| Run order | Before/after | Mean FPS | Mean ms |
| --- | --- | ---: | ---: |
| A1 | Before |62.354|16.038|
| B1 | After |70.689|14.147|
| B2 | After |70.628|14.159|
| A2 | Before |62.774|15.930|

Across2800 intervals per build, before is62.563FPS/15.984ms and after is
70.658FPS/14.153ms:11.457% less frame time and12.939% more presentation throughput.
Combined p95 improves20.795→18.358ms. These are bounded scripted Training
measurements, not real-clock gameplay, GPU timestamp measurements or a whole-game
performance claim. They do not establish a100FPS target or FSR/FG benefit.

The prechange source is4fb4222324152973bb4e186c93684e6e3cdcb828, executable SHA256
`fb5d63245c6c783712b7aa0265a9dd913db530127d80cf96633c94b02c2f66cc`.
The changed source is9b21565d98b07a8a276bb9bf62d6764af9ca4184, executable SHA256
`efebfef4effd06909d0f96dfd6e1def41b367ac96c5ba3bc0fbdcdfa48c21c87`.
Its clean maintained build records183 host files/197 repository dependencies;
the translated DLL is unchanged. Timing receipts and raw intervals remain
private under `local/p2b/count-perf-*` and `count-reject-performance.json`.
A fresh authorized R2 readback confirms the published runtime envelope and pack
catalog are byte-identical to the previously signature/archive-verified inputs.

Separate validation-enabled full-pack runs complete3200 presentations/13889 guest
scenes each, with no validation, synchronization or host-exception messages.
All30 captured files at801/1801/2101/2102/2801/3001 match byte-for-byte, including
authoritative color and temporal depth/motion/validity/metadata. Stationary
coverage801/1801 has57015 finite valid pixels with maximum0.0001221px motion,
within the unchanged0.02px budget. W movement2101 has49031 valid pixels;
turning2801/3001 has51265/43548 valid pixels, all finite and nonzero. These
are positive native static-source comparisons, not all-invalid output credit.
See private `count-reject-native-validation.json` and both validation run receipts.

This change advances repeated CPU diagnostic preparation → equivalent inputs
with less discarded work. The original recompiled geometry producers still
execute. Their broader migration is tracked in issue177: original transform
scratch also feeds culling/lighting, while projected scratch feeds clipping and
material queues. Those consumers and required effects must be owned before an
earlier GPU producer replaces CPU work. The historical narrow loop bypass had
no net performance win and is not restored by this change.


## Independent review and final-source measurement, November 2

The independent review found an overlapping dependency defect in reduced-world
fixture-shadow preparation. PR #120 head 542a93a is now integrated locally as
commit e9362c95987a71b6fc4ea388f7e480c4392bf65c: all reconstructed batches share
full-scene shadow preparation, and TL casters read the captured vertex owner.
P2b diagnostic model/source fields, ordered depth clears, first-reset retention
and the count rejection guard are preserved. The existing captured-vertex
shadow regression passes at 50/67/100 percent under RX 9070 validation.

The final clean maintained candidate is built from e9362c9, with 183 host files,
197 repository dependencies, source_dirty=false and no changed_source_files.
Executable SHA256:
`3d813f24e887563bd17f9843d7816fbff504740a27999ad2cf3f228e696b5459`.
A private control uses the same commit and unmodified builder with only the
four-line count rejection guard removed. Every other consumed source, manifest,
tool/header pin and translated DLL agrees byte-for-byte. Its executable SHA256 is
`9f06f481a6c48d7cf0fd74c47a4d40313282d88c3516832a01d8bdbb214aebbc`.
The control records source_dirty=true and exactly one changed_source_files entry,
world_polygon_capture_stage.inc; it is a diagnostic control, never release input.

A fresh ABBA comparison uses the same settings, current 13 published packs and
800-2200 interval described above. Each run completes 2,200 presentations/7,689
scenes with no competing compiler/game or timeout. Validation and capture remain
disabled equally during timing; compiler guards remain enabled.

| Run order | Guard | Mean FPS | Mean ms |
| --- | --- | ---: | ---: |
| A1 | Removed |62.070|16.111|
| B1 | Enabled |70.408|14.203|
| B2 | Enabled |70.745|14.135|
| A2 | Removed |62.325|16.045|

Across 2,800 intervals per build, the control is 62.197 FPS/16.078 ms and the candidate
is 70.576 FPS/14.169 ms: 11.872% less frame time and 13.472% more presentation throughput.
Combined p95 is 20.898 versus 18.153 ms. This isolates the count shortcut after the
dependency repair. It remains a bounded virtual-clock scripted Training result;
it establishes no original-producer migration, 100 FPS target, FSR or FG benefit.
The earlier 9b21565-versus-4fb4222 numbers remain historical measurements of those
specific executables. Private final receipts are reviewer-performance.json and
reviewer-perf-{old-A1,new-B1,new-B2,old-A2} under local/p2b.

Separate validation-enabled final control and candidate runs each complete 3,200
presentations/13,889 scenes with zero VUID, synchronization or host-exception
messages. All 30 authoritative color and temporal capture files at 801/1801/2101/
2102/2801/3001 match byte-for-byte. The same 30 candidate files also match the
pre-integration 9b21565 captures. Positive stationary, W movement and D turn
coverage and numeric bounds are unchanged. See reviewer-native-validation.json
and reviewer-validate-{old100,new100}.

The final candidate also completes 2,200 presentations/7,742 reported scenes at
50% scale with the same published packs and lighting, zero validation/sync/host
exceptions and 1,720x720 diagnostic images. Frames 801/1801 have 14,250/14,240 valid
static pixels and maximum 0.0000611-pixel motion. W movement at 2101 has 12,252
finite, nonzero-motion pixels. Native counters include 626,805 authenticated TL
lighting draws, two fixture lights and 1,475 sun-shadow scenes. This exercises the
integrated reduced-world rendering path; it adds no native near-plane credit.
See reviewer-native50-validation.json and reviewer-validate-new50.

Fresh final checks pass: CMake build/CTest 30/format, enforced web style, launcher
.NET suite, builder/dispatch/function-table tests, all six rebuilt renderer
fixtures, 70 presentation/depth/bridge/sun/world-camera cases, six temporal
scale/jitter cases, camera/source/capture/campaign checks and the three-scale
shadow regression. Shader compilation exactly reproduces the three canonical
authored headers. The private guard-removed CPU fixture fails its rejection
assertion while the production adapter fixture passes. Other style categories
remain report-only. No standalone spirv-val result is claimed.

The scoped optimization and integrated shadow repair are reviewed; #107 remains
partial and must stay draft. Native near-plane positive acceptance remains open;
supported positive zoom is fixture-only. No Stage 3 closure, release, SDK/pack
format change, public setting, FSR/P3/FG enablement or original-producer bypass
follows from this result.


## Total CPU and GPU utilization during live Training

At the owner's request, a separate pair records one-second Windows PDH samples
alongside presentation timing. CPU is total system busy time across all 16
logical processors of the Ryzen 7 9700X. GPU is total RX 9070 engine activity
across all processes: aggregate process instances per physical engine, then use
the busiest engine as the overall percentage, following
[Windows Task Manager's definition](https://devblogs.microsoft.com/directx/gpus-in-the-task-manager/).
DXGI enumeration verifies the RX 9070 LUID (0:0x12E10); the iGPU is a separate
adapter and is excluded from this GPU figure. This is not game-only CPU usage,
shader occupancy, GPU clock/power or VRAM usage.

The same final candidate and exact guard-only control, published full-pack
profile and uncapped virtual-clock Training route are used. Only samples whose
latest presented frame is 800–2199 are summarized, excluding menus/loading and
teardown. Both runs finish 2,200 presentations / 7,689 scenes without competing
games/compilers or timeouts. All 23 before / 20 after live samples have valid
CPU and GPU data. Peaks are sampled one-second peaks, not instantaneous maxima.

| Measurement | Guard-only control | Candidate |
| --- | ---: | ---: |
| Total CPU, average | 18.28% | 18.16% |
| Total CPU, sampled peak | 23.54% | 24.61% |
| RX 9070 overall GPU, average | 12.78% | 11.53% |
| RX 9070 overall GPU, sampled peak | 14.53% | 12.07% |
| Presentation throughput in this monitored pair | 61.60 FPS | 70.27 FPS |

A logical CPU reaches approximately 98.44% in both runs; low total CPU usage
alone cannot rule out a single-thread limit. This counter is system-wide and
does not establish which process owns that busy CPU. Similar total CPU load
with different throughput is not a game-only CPU-cycle measurement.

This is one monitored sample per build, separate from the repeated ABBA result
above. Percentages include other processes and monitoring overhead; PDH query
and parsing average about 7.2 ms per one-second sample. The original sampler
attempt exited on a transient PDH_CSTATUS_INVALID_DATA at startup and supplied
no utilization result. The revised sampler primes the counters and retains
invalid samples as missing rather than filling them with zero. The completed
pair has no missing GPU samples.

Raw private CSVs are `local/p2b/usage-before-control-r2.csv` and
`usage-after-candidate-r2.csv`; method, adapter identity and numerical summaries
are in `total-utilization-summary.json` and `utilization-adapters.json`. Each
run also retains its source hash, frame times and contention checks. Monitoring
is a development diagnostic; no runtime, launcher setting or driver was changed.
