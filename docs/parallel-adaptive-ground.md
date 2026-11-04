# Parallel adaptive ground preparation

This opt-in native-host path prepares legacy ground polygons on owned CPU jobs.
It preserves the recompiled game's gameplay thread and ordered rendering calls.
It does not implement an upscaler or frame generation. The feature remains off by
default while its performance gate is evaluated.

## Execution boundary

The original mesh routine still transforms its source pool and runs its shading
prelude. At the first admitted `sub_00545720` call, the host copies upcoming
polygons, baked ambient, per-corner RGB/UV, fog, point lights and projection into
owned inputs. Workers run the same authored numerical kernel used by the inline
control. They do not access Stage, live guest memory, GPU resources or callbacks.

Each mesh invocation retains at most 64 completion handles. Nested mesh scopes
retain ordinary execution instead of starting another batch. At the actual
`sub_00547740` boundary, the main thread compares every input word, current
ownership context and required source/material bytes before accepting a result.
A mismatch discards that candidate. Missing current context prevents asynchronous
admission; it does not create a camera epoch or publish history early.

The main thread retains the original routine's prologue, required initial
preparation, actual projection, depth bias, boundary expansion, every actual
triangle callback and epilogue. At the first real refinement helper boundary it
installs computed attributes/topology and temporarily marks completed faces
inactive through the remaining numerical loop. Computed activity is restored
before the original projection. The real callback stack and return path remain
in place; a pending job never invents the outer function's return value.

Transfers use bounded reusable main-thread staging. Vertex staging starts with
CURRENT guest scratch bytes, then overwrites only the kernel's defined fields.
Unused UV slots and initial boundary flags survive; screen fields are left for
original projection. This is not restoration of an oracle's AFTER capture. Both
transfers and their capacities are checked before guest writes. Actual original
callbacks execute once and retain submission order.

## Admission and ownership

The initial family is static type-0 meshes in groups 0/1, the audited baked,
noise-free prelude, no additional UV layers, and a current authenticated world
view at 100% world scale. Full source projection and UV words must agree with the
actual unclipped polygon; matching corner counts alone is insufficient. Other
modes retain ordinary recompiled execution.

Limits are 64 source vertices, 128 input lights, 1,024 generated vertices and
2,048 triangles. The native prelude attribute array ends at the extra-UV globals;
the selected-light pointer array ends at triangle scratch. Counts outside these
contracts are rejected before a partial transfer. Float stores, the guest
nearest/53-bit control word, light thresholds and adjacency order are deliberate.

Job identity copies the current real-render frame, view/target/controller,
camera/load/reset epochs, projection, clip rectangle and effective guest/output/
internal dimensions. Existing heap-release and mapping-generation counters
conservatively invalidate lifetimes during the mesh invocation. They are not
persistent surface identifiers. Required source/material bytes are also checked.
The renderer's const dimension query rejects an uninitialized/frontend target,
a changed guest target or a pending scale request; it does not allocate or wait.

A mesh scope drains its owned handles before releasing storage, including after
a guest exception. Draining also retrieves errors from unused or stale jobs;
normal exit propagates the first error after all jobs finish. During an existing
guest fault it reports a secondary failure without throwing twice. Each job
preserves its worker's FP environment and Windows LastError. No worker retains a
mutable source snapshot or history owner.

## Settings

| Setting | Values | Default |
| --- | --- | --- |
| `MW34_ADAPTIVE_GROUND` | `0`, `1` | `0` |
| `MW34_ADAPTIVE_WORKERS` | `inline`, `1`, `2`, `4` | `2` when opted in |
| `MW34_ADAPTIVE_CHECK` | `0`, `1` | `0` |

`inline` is the same numerical producer at the actual call without lookahead
workers. A requested worker count is capped to reported hardware concurrency;
an unknown hardware count permits one worker. Diagnostics identify the actual
count, which can be three on a three-thread machine. Check mode compares ordered packets and defined effects on frames 801,
849, 1801 and 2101. Its bounded timing spans are diagnostic; they must be disabled
for performance runs. Final counters distinguish accepted candidates from
refinements whose geometry was actually consumed from workers.

## Demonstrated native behavior

A 2,200-frame live native Training run on RX 9070 consumed 8,702 worker-produced
refinements. All 15 sampled color, depth, motion, validity and metadata artifacts
matched the control byte for byte. The sampled numerical check covered 104 calls,
9,129 triangle packets and 5,283 vertices without a mismatch.

The private boundary comparison covered 2,366 original records. Compared numerical
outputs, integer registers, flags and FP control/status agree. Discarded software
ST4/ST5 payload bytes can differ while the x87 stack is empty; they are not live
callback/return arguments. The complete enclosing mesh State agrees byte for
byte. A subsequent expanded inline audit found differences in callback stack
snapshots; their liveness remains unresolved. The earlier comparison does not
establish equality of every captured memory range. See the
[follow-up attribution and fidelity report](performance-attribution-2026-11-03.md).
Captures and original-derived data stay local.

The revision with bulk transfers and narrowed dispatch hooks retained all of
that evidence and recorded 20 interval overlaps among 24 sampled refinements
whose results were actually consumed, on different workers.
The post-review safety revision repeated the 2,200-frame, 15-artifact and
2,366-boundary-record comparisons successfully, with 18 overlaps among 24 sampled
consumed refinements. Overlap counts vary with scheduling; they prove concurrent
useful work, not a speedup.

## Performance gate: failed

Two capture-free, same-executable off/two-worker ABBA sets measured frames
801 through 2200. Each mode has four runs; the table averages the per-run
statistics. No diagnostic spans, captures or periodic frame dumps were enabled.

| Mode | FPS | Median frame ms | p95 frame ms | Main CPU ms/frame | Worker CPU ms/frame | Total CPU | RX 9070 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Off | 78.42 | 12.587 | 15.023 | 11.485 | 0 | 22.00% | 12.64% |
| Two workers | 76.94 | 12.826 | 15.273 | 11.795 | 0.221 | 21.60% | 12.47% |

Two workers reduced FPS by 1.89% and increased main-thread CPU time. The FPS
ranges were 78.12–78.96 off and 76.81–77.08 with two workers. Both ABBA sets
regressed. These measurements demonstrate useful concurrent execution, but not
a throughput improvement. Earlier per-field transfer and bulk-transfer-only
revisions also regressed.

Single scaling controls measured inline 82.36 FPS, one worker 77.11 FPS and four
workers 76.38 FPS. These were preliminary controls. The subsequent
[two repeated off/inline ABBA sets](performance-attribution-2026-11-03.md)
measured a 4.24% inline improvement on the clean post-review host, with fidelity
limitations still open. The measured worker
compute is small relative to the remaining main-thread work. The extra lookahead,
capture and consumption path outweighs its savings in these runs; individual
phase costs still need attribution before another scheduling design is selected.

CPU times use cumulative thread counters sampled at 1 Hz and interpolated at
the measurement endpoints. Total CPU includes the system; GPU utilization is
the RX 9070's strongest aggregated physical engine, including other processes.
Neither utilization metric is an exclusive game cost or a performance gate.

The worker table describes the measured pre-review revision. Subsequent safety
fixes are not represented as a worker performance improvement. Repeated
off/inline checks are now recorded separately; the remaining worker matrix and
forced delayed-job, capacity and temporal transition
coverage remain incomplete. Issue 183 is not complete; keep the PR draft and
the feature off. Lazy setting validation and the supported inline computation
after a speculative mismatch also remain deviations from the approved plan's
startup-validation and ordinary-execution wording. Actual inputs are recaptured;
this is not acceptance of stale results. Resolve these contracts before marking
the work ready. No default setting or published playtest changes follow from
these measurements.

Current validation uses the pinned runtime 1.0.46 and 13-pack selection, identical
Training motion/input, RX 9070 presentation, FXAA/16x AF, 100% world scale and
identical temporal settings. Fresh catalog verification returned HTTP 403 on
2026-11-03; this is the last verified published selection, not a fresh claim that
no newer pack exists. No launcher/runtime/pack update is published by this work.

## Future temporal renderers

Jobs remain unjittered; existing rendering applies jitter. CPU workers do not
own temporal images, presentation or HUD composition. An original render-frame
identity is distinct from simulation ticks and future generated presentations.
This path never advances those owners to manufacture an admissible job.

Adaptive triangle indices are not stable cross-frame surface identities. Parent
polygon and source ownership are retained, but generated ground keeps the
existing conservative motion-validity behavior. Preserving invalid coverage does
not establish FSR, DLSS, XeSS or frame-generation readiness. SDK dispatch, proven
generated-surface motion, exposure, reactive masks and presentation integration
remain separate work.
