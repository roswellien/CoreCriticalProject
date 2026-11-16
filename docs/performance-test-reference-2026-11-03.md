# Performance investigation: references and next tests

Recorded November 3, 2026. Tracking: [issue #185][issue185].

## Recommendation

Measure the current native host's main-thread work before changing its threading
or replacing more geometry producers. Use `telltaleatheist/mw3-re` to understand
and cross-check specific original rendering routines, not as evidence that its
measured bottleneck is ours.

The immediate sequence is:

1. Establish a capture-free, repeatable baseline and verify what executable runs.
2. Attribute main-thread samples to translated computation, guest-memory access,
   host preparation, submission and waits.
3. Repeat the ground **off versus inline** comparison before another worker test.
4. Investigate only the largest remaining measured cost, using the references
   and conditional tests below.

This is the requested research report and test reference, not an implementation
specification or a record of newly executed benchmarks. No runtime execution
boundary advances in this documentation change. No game was launched, external
code imported, benchmark repeated or release produced for this report.

## Evidence and scope

The external source snapshot is
[`bb9af7b22c54c909cec8052595c1fe0bb32773f1`][external]. Local maintained-source
inspection uses `develop` at `23a76fc9ae797d748701f50d5a1d6774c6e0308c`.
Separate experimental results below come from their pinned topic commits; they
must not be treated as features of that `develop` snapshot or a published build.

Labels used here:

- **Recorded measurement:** a result in an existing project report, not rerun here.
- **Source observation:** checked in the named source revision.
- **Hypothesis/proposal:** a question or test that remains to be performed.

### What our existing results establish

| Evidence | Recorded result | Consequence for the next test |
| --- | --- | --- |
| [Parallel adaptive ground, `63934e8`][parallel] | Two capture-free ABBA sets: off 78.42 FPS, two workers 76.94 FPS; main CPU 11.485 versus 11.795 ms/frame; worker CPU 0.221 ms/frame. Both sets regressed. | Moving useful work to workers did not improve throughput. Attribute lookahead, copying, validation, waiting and commit costs before another scheduling design. |
| [Same ground report][parallel] | One inline control reached 82.36 FPS. The repeated off/inline/worker matrix is incomplete. | Inline is a hypothesis worth repeating, not an established improvement. |
| [Static producer, corrected report at `49efefa`][static] | The path executed and sampled graphics matched, but the 0.45% mean improvement was within variation. A later audit found default frame dumps every 30 frames in the timing route. | Do not present those timings as capture-free evidence or assume that moving a small admitted geometry subset to the GPU solves the bottleneck. |
| [October 23 bottleneck evaluation](archive/performance-bottleneck-evaluation-2026-10-23.md) | Its older near-light phase had much higher TL draw and callback counts. Fixture-shadow preparation/recording and per-draw host costs were substantial. Fine-grained timing added significant overhead. | These are candidate categories and a warning about measurement overhead, not current timing values. Do not reuse its frame-phase boundaries without checking the present route. |
| [Texture staging](archive/texture-staging-performance-2026-10-22.md) | Exact conversion tables and contiguous staging reduced some first-use hitches, without a substantial sustained throughput gain. | Do not reimplement the external project's lookup-table optimization as though ours lacks it. Separate cold upload hitches from steady-state frame cost. |

The parallel report's measurements apply to its specified pre-review revision;
later safety fixes were validated for fidelity but not established as faster.
System-wide CPU and busiest-engine GPU utilization include other processes.
They do not substitute for game-process CPU attribution or GPU pass duration.

### What the external results establish

Their [performance report][external-perf] records Release measurements on Apple
silicon/Metal. One scene's hidden-run mean fell from 4.51 to 1.98 ms after
skipping empty overlays, reusing staging buffers and using color-conversion
tables. A proposed dirty rectangle made that workload slower because the HUD
already spanned most of the canvas. They controlled game time, separated loading
from mission frames and distinguished visible VSync pacing from hidden runs.

Those are useful methods and implementation leads. They are not our hardware,
presentation path, scene configuration or enhanced content. A hidden run still
submits GPU work and may encounter resource backpressure; removing presentation
does not by itself isolate pure CPU computation. Their reported frame times are
not a forecast for our runtime.

## External references to keep beside the profiler

All links in this table pin the inspected external commit.

| Reference | What to use it for | Limit |
| --- | --- | --- |
| [Performance report][external-perf] | Repeatable scenes, fixed diagnostic clock, warmup, percentile reporting and separating upload churn from useful work. | Their measurements and workload differ from ours. |
| [`gmod_light.cpp`][external-light]: `draw_projected`, `projected_split`, `projected_light_vertex` | Readable stages for original `0x00547740`, `0x00547160`, `0x00547060`: light filtering, adaptive refinement, vertex attributes, projection and callbacks. | External reconstruction, not an admitted replacement for our guest ABI or FP behavior. |
| [Projected-light/shadow notes][external-shadows] | Explain when refinement happens, its six passes, generated triangle callbacks, light flags and precision-sensitive color behavior. | Validate relevant claims against our pinned original and retained boundary evidence. |
| [`test_shadows.py`][external-shadow-tests] and [`probe_shadows.cpp`][external-shadow-probe] | Compare refinement counts, output packets and light/geometry cases. `probe_sh_md_mesh` exposes vertex/triangle counts. | Requires their test infrastructure and user-supplied game data. The test patches original overflow behavior; agreement there is not unmodified-original equivalence. |
| [`sdl_platform.cpp`][external-overlay] and [`test_sdl_frontend.cpp`][external-overlay-tests] | Empty-overlay handling and exhaustive color-conversion checks, if our profile finds equivalent work. | Our GPU HUD is different; a whole-buffer scan can itself cost time. |
| [`sdl_render3d.cpp`][external-staging]: `map_staging`, `upload`, `end_scene` | Resource reuse and the distinction between conversion, transfer allocation and submission. | SDL cycling is not a drop-in Vulkan resource-lifetime solution. |
| [`mw3_main.cpp`][external-main] | `--frame-ms` and `--frame-times` illustrate separating diagnostic game time from wall-clock measurement. | These flags belong to their executable, not ours. |

Addresses above are **virtual addresses**, for the supported MW3 U.S. retail 1.2
image with SHA-256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
For example, VA `0x00547740` is RVA `0x00147740` at base `0x00400000`.
Do not confuse these with an ASLR-adjusted host address or a translated-DLL RVA.

## Our tools and source boundaries

These relative links resolve in the maintained checkout. Inspect the actual
candidate's source/build receipt before assuming its instrumentation is the same.

| Tool or source | Available behavior | Important limitation |
| --- | --- | --- |
| [Host build guide](../tools/m4-crt-heap-carry/HOST_BUILD.md) | Builds the maintained host and records source/dependency identity, using the existing local translated DLL. | Build a diagnostic candidate on its own topic branch. Do not use an unrecorded historical patch chain for release inputs. |
| [`main_v2.inc`](../tools/m4-crt-heap-carry/host/main_v2.inc): `HostProfiler` | `MW34_PROFILE=<path>` enables roughly millisecond main-thread sampling; `MW34_PROFILE_FROM` sets its starting presentation count. Writes host offsets, outside-module counts/offsets and short caller chains at exit. | Suspends the sampled thread and changes timing. Caller chains preserve host-image addresses, not full translated-DLL stacks. Outside-module detail is limited. It is a triage profiler, not complete exclusive CPU accounting. Resolve offsets with matching binaries/symbols; do not label unknown samples as renderer work. |
| [`vdd.inc`](../tools/m4-crt-heap-carry/host/vdd.inc) | `MW34_FRAME_TIMES=<path>` records presentation number, host milliseconds, scene count and virtual clock. | Verify a nonempty output and expected frame progression. Adjacent timestamps produce intervals; an absent log is a failed measurement. |
| [`mfc_stage.hpp`](../tools/m4-crt-heap-carry/host/mfc_stage.hpp) and `main_v2.inc` | `frame_dump` defaults to 30; `MW34_FRAME_DUMP=0` disables periodic dumps. `MW34_FRAME_BUDGET` bounds the run. | Clearing the environment variable restores the default; it does not disable dumps. Audit explicit screenshot/readback paths too. |
| [Scripted playtest driver](scripted-playtest-driver.md) | Documents `MW34_INPUT_SCRIPT`, `MW34_VIRTUAL_CLOCK`, timing origins and retained tooling gaps. | Its sample script is grammar, not an authenticated Training route. Fixed-clock throughput is not real-time play validation. |
| [`geometry_profile.hpp`](../tools/m4-crt-heap-carry/host/geometry_profile.hpp) | `MW34_GEOMETRY_PROFILE=<path>` records scoped source/emission ticks and geometry counters where wired. | It is not a full-frame decomposition; its CSV is flushed each presentation. Keep it out of final throughput runs and measure its overhead. |
| [`gpu_work_profile.hpp`](../tools/remaster-launcher/native-overrides/gpu_work_profile.hpp) and [its checks](../tools/remaster-launcher/tests/gpu_work_profile_checks.cpp) | Existing design for GPU timestamp regions, existing fence/wait timing and memory-budget sampling. | **Not integrated into maintained `host/` at the inspected develop commit.** Setting `MW34_GPU_WORK_LOG` alone there does nothing. The historical [adapter](../tools/remaster-launcher/apply_gpu_work_profile.py) pins older source hashes; do not bypass them. |
| [Ground source and evidence][parallel], [static producer evidence][static] | Identify the experimental kernels and their measured limits. | Topic-branch evidence; pin the tested revision, not merely the branch name. |
| [Guest-heap lookup change, `6f24a5c`][heap] | Candidate removal of a second region lookup in `heap_partitions.hpp`. | Source change alone is not evidence that heap lookup dominates or that the change improves frame time. |

If deeper attribution is needed, reuse a validated native-process stack profiler
with both host and translated-DLL symbols, or narrowly adapt the existing sampler
on a separate implementation branch. The historical
[`geometry_breakdown_sampler.inc`](../tools/remaster-launcher/native-overrides/geometry_breakdown_sampler.inc)
is a reference only: it has a 16-frame stack limit, hard-coded frame bounds and
dependencies on diagnostic globals. It is not ready-to-enable instrumentation in
the maintained host. Unknown stack samples must stay explicitly unclassified.

## Common controls for every proposed run

1. Record the source SHA, host and translated-DLL SHA-256, build receipt, compiler
   flags, symbols, original-input identity, runtime/pack hashes, hardware/driver,
   presentation backend, resolution, world scale and graphics settings. The
   retained runtime 1.0.46/13-pack selection is a historical baseline, not proof
   that it is still the latest available selection.
2. Reuse the exact retained Training input, clock step/base and configuration.
   Record their hashes. Issue #183's comparison window was frames 801–2200.
   Preserve that definition when reproducing it, verify the corresponding scene
   progression, and define interval endpoint inclusion identically in every run.
   If those private inputs cannot be found, establish a new named baseline rather
   than claiming to reproduce the old one.
3. Use a fresh output directory per run and immutable copied pilot/configuration
   data. Inspect process identities first; do not duplicate a running game/build
   or disturb the protected composer/watcher. No active SQLite inspection.
4. Set `MW34_FRAME_DUMP=0` explicitly. Remove scheduled screenshots, depth/motion
   dumps, replay capture and verbose per-draw logging from timing runs. Confirm
   no periodic image output or readback path remains. Retain only the agreed
   minimal timing/required logs, identically in both conditions.
5. Keep VSync off for uncapped comparisons (`MW34_VSYNC=0`) and verify the actual
   Vulkan/DXGI presentation path. Do not silently substitute hidden, minimized or
   occluded execution for the visible route. Report those modes separately.
6. Separate three cohorts: lean throughput, instrumented attribution, and
   fidelity captures. Pair instrumented and lean controls to estimate observer
   overhead. Never use a capture or profiler run as the final speed claim.
7. Use two ABBA sets initially for each comparison (four runs per condition).
   Report per-run mean, median, p95/p99 and spread, not only pooled FPS. Separate
   first-use hitches from warmed frames and identify any heavy/light phases from
   current counters. Do not add nested inclusive timings or overlapping GPU spans.

No launch command is fabricated here: this checkout does not contain the complete
private issue #183 benchmark inputs. The documented environment controls are
building blocks for its verified harness, not a substitute for that harness.

## Ordered next tests and decision points

### T0 — Make the baseline trustworthy

**Question:** Are we measuring the same native workload without captures or a
display cap? Use the controls above and the existing frame-time log. Run the
unaltered baseline repeatedly before testing an optimization. Verify mission
progression separately with bounded captures and counters.

**Keep:** run identities, exact environment, input/config hashes, completed frame
and scene counts, timing distribution and the observed termination reason.
A budget exit is not normal quit or mission completion.

**Decision:** stop performance comparisons if workload progression differs,
captures remain enabled, logs are missing, a competing process changes the load,
or timing spread is too large to distinguish the proposed gain. Diagnose that
specific cause rather than averaging more inconsistent runs.

### T1 — Locate the current CPU cost and waits

**Question:** Which part of the main-thread frame is expensive now?
Start with the existing sampler, matched symbols and frame-time context. Classify
host/translated code, memory/heap helpers, ground math, per-draw capture, shadow
preparation, command recording, blocking/presentation and unknown samples.
Sample shares are attribution clues, not exact milliseconds or proof a sampled
thread was consuming CPU while blocked.

Add only the missing boundaries that the first profile cannot resolve. For
ground work, measure input capture/lookahead, input comparison, numerical compute,
queue/wait, result transfer and main-thread callbacks separately. Use aggregate
counters for high-frequency helpers; prefer coarse exclusive scopes over a timer
around every guest load or triangle. Preserve guest FP state and LastError.

If blocking or GPU work remains unresolved, wire the existing GPU diagnostic
design into the candidate's actual renderer through a reviewed change. Include
DXGI waits/presentation when active, not only `vkQueuePresentKHR`. Collect queries
after existing completion points; do not add waits to obtain results. Compare
the instrumented candidate's output and overhead against its control first.

**Decision:** publish a ranked frame budget with exclusive measured categories,
sample-only categories, overlap warnings and an explicit unexplained remainder.
Choose T3 by the largest credible cost, not by overall GPU utilization.

### T2 — Separate faster arithmetic from worker overhead

**Question:** Does the same native ground computation help when executed inline?
Use one pinned candidate supporting ordinary execution and inline computation.
Compare `MW34_ADAPTIVE_GROUND=0` against `MW34_ADAPTIVE_GROUND=1` with
`MW34_ADAPTIVE_WORKERS=inline`, with check/capture modes off during timing.
These controls belong to the experimental branch; first confirm they exist and
are exercised in the chosen build.

Repeat the off/inline ABBA matrix before comparing inline with one/two/four
workers. Keep geometry admission, other feature flags, temporal state and
effective worker count recorded. Do not combine an unrelated heap fix or static
producer change into only one condition.

**Fidelity:** use separate runs to compare the existing color/depth/motion/
validity/metadata artifacts, ordered triangle packets, required guest memory,
registers, flags and FP behavior. Extend existing ground checks when a new case
is needed. Revalidate delayed/stale results, capacity rejection, reload and
camera transitions before considering workers ready for wider use.

**Decision:** an inline win that repeats across both sets, exceeds baseline
variation and passes fidelity supports optimizing this numerical boundary. If
workers then regress, focus on capture/validation/transfer overhead; concurrent
execution alone is not success. A marginal gain or inconsistent direction is
inconclusive. Predeclare a practical improvement target and acceptable p95/p99
regression before selecting a shipping candidate.

### T3 — Follow the dominant category, one experiment at a time

| Dominant cost from T1 | Next bounded test | References and required comparison |
| --- | --- | --- |
| Ground refinement arithmetic | Count selected lights, refinement passes/splits, generated vertices/triangles and callbacks per admitted polygon. Compare matching input packets across ordinary and inline paths; use their readable routine as a cross-check. | [External routine][external-light], [notes][external-shadows], [our ground report][parallel]. Same work/output and FP contract before interpreting timings. Offline kernel time alone is not live frame improvement. |
| Guest-memory/heap access | Profile lookup count/caller distribution, then compare an isolated lookup candidate on the same workload. | [Heap change][heap] and existing heap fixture. Preserve bounds, mapping-generation and lifetime validation; never remove checks merely to win a benchmark. |
| Per-triangle capture or repeated shadow preparation | Count draws, vertices/bytes copied, caster/light sets and atlas rebuilds per real frame and scene. Test reuse/batching only where ownership and ordering permit it. | [Older evaluation](archive/performance-bottleneck-evaluation-2026-10-23.md), [native callback evidence](archive/native-call-routing-performance-2026-10-22.md). Check shadow/depth results and callback order; do not assume retained resources are unchanged. |
| HUD conversion or upload churn | Count overlays with no content, converted/uploaded bytes and transfer allocations. Compare cold and warm frames separately. | [External overlay][external-overlay], [staging][external-staging], [our existing staging work](archive/texture-staging-performance-2026-10-22.md). Measure before adding scans or another conversion table. |
| GPU duration or synchronization | Measure scene/shadow/postprocess intervals and CPU fence/acquire/DXGI-present waits; compare a controlled resolution change as a diagnostic. | Existing GPU helper and active renderer. Resolution sensitivity is a clue, not proof; resource rings need validated lifetime/barrier behavior before increasing overlap. |

### T4 — Confirm the selected improvement in actual play

After a candidate wins its lean repeated comparison and passes fidelity, repeat
the affected route with normal real-time pacing and visible presentation, then
exercise a representative near-light/combat scene, rapid camera changes and a
mission transition. Record hitches, input/audio behavior and normal shutdown
where tested. Keep stock and enhanced-content results separate. A synthetic
kernel, saved-scene replay or fixed-clock run cannot establish this coverage.

## What the next test handoff must contain

- The question tested, source/build/input identities and exact compared settings.
- Per-run timings and workload counts, attribution method and measured overhead.
- Which reference above informed the test; any disagreement with it and how that
  was resolved against the original or our validated contract.
- Fidelity results with the named artifacts/fields checked; failures retained,
  unknowns explicit. Private media, generated code and captures remain local.
- A conclusion of improved, regressed or inconclusive, with the next boundary
  justified by measurements. No percentage of project completion.

This report adds no profiler, test harness or runtime dependency. External source
is linked for research, not vendored. Any later code reuse needs provenance and
applicable notices under [the distribution policy](legal.md), and any native
change follows the [PR workflow](github-workflow.md).

[issue185]: https://github.com/roswellien/MW3Recomp-Private/issues/185
[external]: https://github.com/telltaleatheist/mw3-re/tree/bb9af7b22c54c909cec8052595c1fe0bb32773f1
[external-perf]: https://github.com/telltaleatheist/mw3-re/blob/bb9af7b22c54c909cec8052595c1fe0bb32773f1/docs/performance.md
[external-light]: https://github.com/telltaleatheist/mw3-re/blob/bb9af7b22c54c909cec8052595c1fe0bb32773f1/src/gamez/zmodel/gmod_light.cpp#L856
[external-shadows]: https://github.com/telltaleatheist/mw3-re/blob/bb9af7b22c54c909cec8052595c1fe0bb32773f1/docs/render-shadows.md#L292
[external-shadow-tests]: https://github.com/telltaleatheist/mw3-re/blob/bb9af7b22c54c909cec8052595c1fe0bb32773f1/tests/differential/test_shadows.py
[external-shadow-probe]: https://github.com/telltaleatheist/mw3-re/blob/bb9af7b22c54c909cec8052595c1fe0bb32773f1/tests/probe_shadows.cpp
[external-overlay]: https://github.com/telltaleatheist/mw3-re/blob/bb9af7b22c54c909cec8052595c1fe0bb32773f1/src/frontend/sdl/sdl_platform.cpp
[external-overlay-tests]: https://github.com/telltaleatheist/mw3-re/blob/bb9af7b22c54c909cec8052595c1fe0bb32773f1/tests/test_sdl_frontend.cpp
[external-staging]: https://github.com/telltaleatheist/mw3-re/blob/bb9af7b22c54c909cec8052595c1fe0bb32773f1/src/frontend/sdl/sdl_render3d.cpp
[external-main]: https://github.com/telltaleatheist/mw3-re/blob/bb9af7b22c54c909cec8052595c1fe0bb32773f1/src/frontend/sdl/mw3_main.cpp
[parallel]: https://github.com/roswellien/MW3Recomp-Private/blob/63934e8584d715eaa8ba1960ad3203d2a06d9c82/docs/parallel-adaptive-ground.md
[static]: https://github.com/roswellien/MW3Recomp-Private/blob/49efefa0ddf0cab3d880b428daaccf5c3cd0b6bf/docs/native-static-producer.md
[heap]: https://github.com/roswellien/MW3Recomp-Private/blob/6f24a5c32209213f921be06ecd5057dacf391a35/tools/m4-crt-heap-carry/host/heap_partitions.hpp
