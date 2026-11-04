# Training performance attribution: November 3, 2026

The inline adaptive-ground producer improved repeated Training throughput by
4.24%; the worker experiment still has no demonstrated speedup. Follow-up
attribution measures draw preparation, fence waits and GPU command intervals
for the pinned Training workload. Full fidelity and shipping gates remain open.

This continues the ordered tests in [PR 186](https://github.com/roswellien/MW3Recomp-Private/pull/186),
whose reference document is pinned to commit
`f4fbd3dbbc4684e0ddf9177b6a12d36c33bef2d7`. The implementation remains in
[draft PR 184](https://github.com/roswellien/MW3Recomp-Private/pull/184),
with [issue 183](https://github.com/roswellien/MW3Recomp-Private/issues/183) open.
No new native execution boundary is advanced by this report: it documents live
native Training, not mission completion, real-time validation or SDK integration.

## Controls and provenance

The clean host is built from `63934e8584d715eaa8ba1960ad3203d2a06d9c82`.
Its executable SHA-256 is
`32b115a8a4e2716a89133fb034d999cca7e01a71ec6152b5bcac0fc0a036ce71`.
The translated module is unchanged. All comparisons use the same scripted
Training input, 3440x1440 output, RX 9070 Vulkan/DXGI presentation, FXAA, 16x AF,
100% world scale, temporal inputs and jitter enabled, lighting enabled, and
VSYNC requested off. Simulation uses a fixed 16.666667 ms clock. Measurement
covers frames 801 through 2200, using timestamps 800 through 2200.

Content is the historical published runtime 1.0.46 and identical 13-pack
selection. Fresh catalog verification returned HTTP 403; this is not a claim
that this selection is the newest published content. Preserve it for matched
comparisons and start a separate cohort when updating content.

Private captures, probes, original-derived analysis and full receipts remain
local. Run identifiers below locate those receipts; they are not release names.
No runtime, pack, launcher, default setting or published artifact changes here.

## Capture-free baseline and repeated inline comparison

The two baseline runs `cpu183-t0-r6-a` and `cpu183-t0-r6-b` measured 78.84 and
79.19 FPS, a 0.45% spread. Two subsequent off/inline ABBA sets used the same
clean executable, with no captures or diagnostic spans. Each mode has four
runs. Values below average the per-run statistics, rather than pooling frames.

| Mode | FPS | Mean ms | p95 ms | p99 ms | Main CPU ms/frame |
| --- | --- | --- | --- | --- | --- |
| Off | 79.101 | 12.642 | 14.970 | 17.396 | 11.292 |
| Inline | 82.456 | 12.128 | 14.353 | 16.606 | 10.878 |

Set 1 improved FPS by 4.03% and reduced main CPU time by 2.60%; set 2 improved
FPS by 4.45% and reduced main CPU time by 4.70%. Both improved p95 and p99.
This passes the investigative threshold of at least 3% FPS improvement,
lower main CPU in both sets and no greater than 3% p95/p99 regression. It is
not a shipping gate. Each inline run consumed 8,702 refinements; all runs have
the same 1,400 measured camera-history tuples and input identity.

The receipt is `local/t2-r6-final-receipt.json`; runs are
`cpu183-t2-r6-s1-{a1,b1,b2,a2}` and `cpu183-t2-r6-s2-{a1,b1,b2,a2}`,
in off/inline/inline/off order. CPU uses cumulative thread counters sampled
at 1 Hz and interpolated at the endpoints. The earlier repeated two-worker
regression remains documented in [the implementation report](parallel-adaptive-ground.md).

## CPU attribution and its limits

The Windows CPU recorder was blocked by policy. No policy or driver was
changed. A private external sampler measured instruction residency with
infrequent full stacks, validated against busy/sleep/parent fixtures and an
exact host code/unwind symbol map. The 2 ms and 5 ms runs contain 4,664 and
2,103 instruction samples, with 146 and 66 full stacks; neither truncated
the observed stacks. Measured throughput penalties were approximately 3.1%
and 2.2%. These runs are attribution evidence, separate from lean timings.

Memory helpers occupy roughly 10–11% of sampled instructions. Other observed
work includes fixture-shadow preparation, per-draw capture, and substantial
host/CRT/OS code. Some instructions in known modules remain unclassified.
Sample shares are not exact CPU milliseconds, and nested stack categories
must not be added together. These results justify coarse disjoint scopes,
not a claim that one translated game function is the entire bottleneck.

## Post-restart wait attribution

After a machine restart, otherwise matched runs cluster near 60 FPS while
the display reports 60 Hz, despite VSYNC requested off. Keep these results
separate from the earlier 79–82 FPS cohort. A private diagnostic host adds
hardware-clock wall scopes around existing operations, including unchanged
fence waits, queue submissions, DXGI Present and keyed-mutex acquisition.
It adds no GPU timestamps or new waits. Its SHA-256 is
`4ec20f8ca8c598a008bb0b98a883ace5e06c737c9dda54803e4526ecb65eb908`.

The disabled observer control `cpu183-budget-r3-control` measured 59.964 FPS;
the enabled offset-0 run `cpu183-budget-r3-o0` measured 59.969 FPS. This
display-paced comparison cannot establish negligible CPU overhead. The
enabled run sampled one frame in 16: 88 frames, with disjoint scopes summing
to each measured frame and TSC/QPC calibration spread below 0.007%.

| Disjoint scope | Wall ms per sampled frame |
| --- | --- |
| Existing fence waits | 4.947 |
| Draw capture | 4.037 |
| Other | 2.129 |
| Mesh work excluding nested scopes | 1.614 |
| Adaptive work excluding nested scopes | 1.308 |
| Callback work excluding draw capture | 1.278 |
| Renderer work excluding nested scopes | 0.500 |
| Fixture-shadow preparation | 0.480 |
| Scene ingest | 0.232 |
| Instrumented queue submissions | 0.112 |
| DXGI Present call | 0.070 |
| DXGI keyed-mutex acquisition | 0.019 |

These are wall times including observer overhead, not per-scope CPU times.
Draw capture averages approximately 2,980 calls per sampled frame. Together
with callback work it accounts for about 5.31 ms. Existing fence waits account
for about 4.95 ms; their location does not prove whether GPU work, presentation
backpressure or another queue dependency caused the wait. Direct Present
duration alone does not explain the 60 FPS ceiling.

The shifted-offset repeat `cpu183-budget-r3-o8-retry` completed at 59.711 FPS.
Its 87 sampled frames (809 through 2185) independently show 4.693 ms in fence
waits, 4.076 ms in draw capture and 1.291 ms in callback work. All 12 scopes
conserve measured frame time; calibration spread is below 0.005%. The offset
changes the expected sample count, so completeness is checked against the
specific frame set rather than requiring 88 samples in both runs.

The separate enabled-observer run `cpu183-budget-r3-fidelity` completed 2,200
frames and matched all 15 sampled color/depth/motion/validity/metadata artifacts
exactly. This checks sampled rendering fidelity, not every guest-memory access.
One offset-8 attempt was stopped before Training
because another compiler started; exclude it from results. Source inspection
must account for existing buffer/state reuse before proposing draw batching.
The queue-submission scope covers calls in `vk_scene.hpp`; submissions in the
world-resolution and temporal include files remain in their enclosing scopes.
It is not a complete count or total cost of every queue submission.

## Fence isolation follow-up

A second private host distinguishes the 15 existing fence/idle call sites
without changing their arguments, order or results. Relative to the previous
diagnostic source, only the probe header and wait labels in `vk_scene.hpp`
change. Removing those labels reproduces the prior renderer source exactly.
The seven-object build retains the unchanged translated module; executable
SHA-256 is `ff0e92a1209ec0feec64b612b515d7cae3bb4f07ffde3b5ff38330d5e92e429f`.
A fixture checks scope conservation, nesting, wall-wait attribution, separate
CPU counters, wait-call arguments/count/result, and FP/LastError preservation.

The disabled control `cpu183-budget-r4-control-retry` and the two enabled runs
`cpu183-budget-r4-o0`/`cpu183-budget-r4-o8` each completed 2,200 Training frames.
Their measured 1,400 camera-history tuples, inputs and settings match except
for diagnostic output/offset. Results stay in the post-restart paced cohort.

| Measurement | Offset 0 | Offset 8 |
| --- | --- | --- |
| Sampled frames | 88 | 87 |
| `Renderer::settle()` wall ms/frame | 4.697 | 4.889 |
| `settle()` waits/frame | 8.239 | 8.287 |
| Resident-presentation fence wall ms/frame | 0.000724 | 0.000654 |
| Measured-window FPS | 59.540 | 59.965 |

All 27 disjoint scopes conserve each sampled frame; clock-calibration spread
is below 0.006%. The control measured 59.966 FPS. Display pacing and varying
system CPU activity prevent an uncapped performance or negligible-overhead
claim. The original control attempt was stopped at frame 1,669 when the release
compiler started; it is excluded. Full receipts are
`local/r4-wall-budget-final.json`, `local/r4-timing-summary.json`,
`local/r4-matched-controls.json` and `local/r4-diagnostic-provenance.json`.
The separate enabled-observer run `cpu183-budget-r4-fidelity` completed 2,200
frames and matched all 15 reference color/depth/motion/validity/metadata artifacts.
Its scope CSV contains all 88 expected sampled frames with 27 valid scopes
each and exact conservation. This is sampled rendering fidelity, not a waiver
of the unresolved inline stack-memory contract below.

Almost all measured fence-wait time is at `settle()`, which waits before
reusing scene command-pool, upload, vertex and descriptor resources. The
sampled readback, capture, initialization and device-idle wait sites had no
calls. The resident-presentation fence had one call per sampled frame and
negligible measured duration. This locates the CPU wait; it does not prove
that all of the elapsed time is scene GPU execution or rule out indirect
presentation/queue backpressure.

Source inspection shows that scene rendering, world reconstruction/target
transfers and temporal commands use the same command pool and scene fence.
The world path can submit shading, reconstruction and coverage separately;
temporal input work adds further submissions. These ownership rules require
the existing waits before resetting or overwriting reusable resources. Do not
remove the waits without replacing that protection.

## GPU stage timings

A private host adapts the existing `GpuWorkProfile` helper under
`tools/remaster-launcher/native-overrides/`. It brackets 12 command-buffer
recording paths with Vulkan timestamp pairs and uses separate query banks for
scene and present resources. Collection follows the existing completed fences
and checks query availability. The RX 9070 queue reports 64 valid timestamp
bits and a 10 ns period. The command intervals measure GPU time between the
recorded stages. [Vulkan timestamp queries](https://docs.vulkan.org/samples/latest/samples/api/timestamp_queries/README.html)

The private build uses source commit `3667fc8a675fcbd1ee6d91ac57f4199910aadd47`,
seven host objects and the unchanged translated module. Its executable SHA-256
is `4d572e4c1ecaa3d1ded3a1d4a20c87b965add47bf6512ef12ca2c92205c51e1d`.
Source checks verified identical wait, submission and resource-reset calls.
The adapted fixture passed 53 checks covering query-bank reuse, unavailable
results, FP and LastError preservation, and a separate check confirmed the
expected 22 ns duration across timestamp wraparound.

`cpu183-gpu-r5-o0` and `cpu183-gpu-r5-o8` each recorded 12,984 intervals across
all 1,400 measured frames, with matching per-frame stage counts. The four
frames with zero temporal submissions coincide with camera-history transitions.
The 100% scale workload exercised the stages below. Reduced-resolution world
reconstruction requires a separate cohort.

| GPU interval sum per measured frame | Offset 0 | Offset 8 |
| --- | --- | --- |
| Scene rendering | 0.773 ms | 0.780 ms |
| Temporal commands | 0.301 ms | 0.296 ms |
| HUD scene | 0.255 ms | 0.252 ms |
| Vulkan resident-present copy | 0.063 ms | 0.063 ms |
| Total recorded intervals | 1.392 ms | 1.391 ms |

On the exact frames sampled by the CPU observer, the GPU interval sums were
1.398 and 1.393 ms, while `settle()` took 4.470 and 4.274 ms of host wall time.
Draw capture and callbacks took another 5.68 and 5.72 ms of disjoint host wall
time. The GPU spans can overlap and include stalls within the instrumented
Vulkan commands. The DXGI copy, queue delays outside the timestamp pairs and display scheduling
require separate measurements. The two clocks and different interval boundaries
prevent assigning the difference to a specific driver or queue operation.

The same-binary control `cpu183-gpu-r5-control` retained the wall observer and
disabled GPU queries. All three runs completed 2,200 frames with identical
inputs, settings apart from the observers, and measured camera-history tuples.
Measured-window throughput stayed near 59.97 FPS. Main CPU time was 12.30 ms/frame
in the control and 11.77/12.20 ms in the enabled runs. Display pacing and differing
system activity limit the comparison to attribution. Receipts are
`local/r5-gpu-stage-summary.json`, `local/r5-wall-budget-final.json`,
`local/r5-timing-summary.json` and `local/r5-gpu-provenance.json`.

The separate `cpu183-gpu-r5-fidelity` run enabled the GPU observer and confirmed
the Khronos validation layer was active. It completed 2,200 frames with all
15 reference artifacts byte-identical and zero validation VUID or synchronization
hazard messages. The fixture, logs and raw query output remain local.

The measured priority is host draw preparation and submission sequencing.
An experiment combining compatible scene and temporal commands should preserve
their barriers and resource lifetimes, then compare fence counts, main CPU time,
frame-time tails and the same fidelity artifacts. Measure throughput on an
uncapped cohort and preserve the existing temporal-history contract.

## Resident scene pairing experiment

A private prototype recorded an eligible resident scene and its single-view
temporal replay in one Vulkan command buffer. A GPU barrier orders the replay
after scene uploads and writes. A separate validation run completed 2,200 frames
with 3,738 paired submissions, all 15 sampled artifacts byte-identical, and zero
Vulkan VUID or synchronization hazard messages. An initial attempt exited
in the menu and a second was interrupted. Both were excluded.

The same executable ran off/on/on/off on the pinned RX 9070 Training profile.
All four runs completed 2,200 frames and matched measured camera-history tuples
and input hashes. Timing covers frames 801–2200. Scope counts and waits use
88 sampled frames per run. Values below average the two runs per mode.

| Measure | Off | Paired |
| --- | ---: | ---: |
| Instrumented submissions per sampled frame | 9.23 | 6.69 |
| Scene-fence waits per sampled frame | 8.24 | 5.70 |
| Scene-fence wall ms per sampled frame | 4.87 | 4.97 |
| Main CPU ms per frame | 11.68 | 11.42 |
| p95 frame ms | 17.44 | 17.93 |
| p99 frame ms | 18.25 | 18.82 |
| FPS | 59.96 | 59.97 |

Both paired runs removed 2.53 submissions and waits per sampled frame.
The main CPU comparison changed direction between the two pairs, and p95
worsened in both. The display-paced run establishes fewer submissions and
waits, with an inconclusive CPU benefit and no measured throughput gain.
Keep this prototype private and prioritize draw preparation for the next
experiment. Receipts are `local/scene-pair-final.json` and
`local/cpu183-scene-pair-fidelity-resume-validation.json`.

## Draw preparation attribution

Two private diagnostic runs separated draw preparation into disjoint wall
scopes. Both completed 2,200 frames on the pinned RX 9070 Training profile
and matched all 1,400 measured camera-history tuples. The scopes sampled
one frame in 16 at offsets 0 and 8, with 88 and 87 samples respectively.

| Draw scope, wall ms per sampled frame | Offset 0 | Offset 8 |
| --- | ---: | ---: |
| Effect observation | 1.438 | 1.420 |
| World and temporal capture | 1.024 | 1.023 |
| Sun and sky capture | 1.022 | 1.012 |
| Remaining draw capture | 0.711 | 0.719 |
| Command append and merging | 0.126 | 0.125 |
| Vertex preparation and copy | 0.117 | 0.117 |

The measured draw scope totaled about 4.4 ms per sampled frame, including
observer overhead. The top three scopes accounted for about 78% of that
total. Effect observation runs fixture maintenance and material
classification before skipping effect work for ordinary non-emitting world draws. Measure
those costs separately before changing fixture invalidation or the material
cache. The capture path already reuses state snapshots and merges adjacent
triangle commands. Receipts are in `local/draw-profile-wall-summary.json`.

## Fidelity qualification and remaining gates

The separate inline validation run `cpu183-t2-inline-fidelity-r6-resume2`
completed 2,200 frames. All 15 sampled color, depth, motion, validity and
metadata artifacts matched the reference byte for byte. Numerical checks
covered 104 calls, 9,129 packets and 5,283 vertices without a mismatch.
The enclosing mesh State matched exactly. Empty x87 ST4/ST5 payload bytes
differ at some boundaries while integer registers, flags and FP control/status
match; these payloads are not live x87 arguments.

An expanded audit checked 64,735 original memory ranges across 2,366 records,
with no missing original range. It found 3,182 differing range comparisons in
two overlapping stack snapshots at 1,591 callback boundaries. Thus the count
does not represent 3,182 independent memory defects. Other compared memory
ranges and adaptive-return ranges match. Some differing bytes map to caller
temporary slots; complete callback and continuation liveness remains
unresolved. Do not claim complete memory equivalence or waive these bytes
solely because the sampled images agree.

Keep adaptive ground off by default and PR 184 in draft. Resolve the stack
contract, remaining worker scheduling/capacity tests, setting-validation
deviations and real-time/transition coverage before declaring issue 183
complete. FSR, DLSS, XeSS and frame generation still require their own motion,
resource, HUD, exposure and presentation validation.
