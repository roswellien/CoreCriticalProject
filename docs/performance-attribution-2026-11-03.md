# Training performance attribution: November 3, 2026

The inline adaptive-ground producer improved repeated Training throughput by
4.24%; the worker experiment still has no demonstrated speedup. Follow-up
attribution identifies substantial draw preparation and existing fence waits.
These findings do not establish GPU execution duration, complete fidelity, or
readiness to enable the feature.

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
| Queue submission | 0.112 |
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
Next isolate the particular fence path and its submission dependency, then
consider maintained GPU timestamps if actual GPU duration is still missing.

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
