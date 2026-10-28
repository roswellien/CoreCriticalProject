# MW3 whole-frame performance investigation

The [next performance update](precompiled-performance-updates-2026-10-22.md)
reduces host service-history bookkeeping, fixes cross-session resource-cache
reuse and delivers the precompiled runtime through `.mw3update`. Measurements
below remain the original world-setting-cache comparison.

The visible Training capture confirms a CPU-side performance problem on this
route. Recorded GPU commands average about 1.29 ms while the diagnostic frame
interval averages 13.64 ms. A repeated lookup of a fixed renderer setting is
one substantial, avoidable cost. Caching it improves the warmed-up visible
benchmark by about 10%, with identical rendered output.

## Measured before and after

Two runs per build, baseline/candidate/candidate/baseline, with profiling and
captures disabled for timing. Primary window: warmed frames 1200-2699,
3,000 intervals per build. This window was selected to investigate sustained
performance separately from first-use stalls.

| Warm Training metric | Before | After |
| --- | ---: | ---: |
| Presented FPS | 80.97 | 89.01 |
| 1% low FPS | 36.83 | 41.36 |
| Mean frame interval | 12.35 ms | 11.24 ms |
| Worst frame interval | 32.25 ms | 29.17 ms |

Average throughput improves **9.9%**, and 1% lows improve **12.3%**. Each
candidate repeat is faster than either baseline repeat. Across the larger
400-2699 window, including remaining first-use hitches, averages are
73.35 to 80.21 FPS and 1% lows are 32.09 to 35.09 FPS. Worst intervals there
are 54.19 to 51.74 ms; the remaining stalls are not eliminated.

These runs have a visible window and submit all 2,800 frames through the
Vulkan swapchain. FPS is measured between presentation calls, rather than
counting monitor scanouts. Conditions: Ryzen 7 9700X, Radeon RX 9070,
3440x1440, FXAA, AF16, draw distance 1600, fog 1100, full existing lighting
and shadows, performance monitor off and replay off. Independent copied
pilot/configuration data and the same Training input script are used.
The diagnostic guest clock stays fixed at 16.666667 ms in both conditions;
real host timestamps measure performance. Interactive gameplay timing is unchanged.

## Where the frame time goes

A separate instrumented baseline captures only frames 1200-2699. Startup,
first-use hitches and shutdown are excluded from the CPU sampling window.
Nested CPU timers charge time exclusively, avoiding double-counting.
The diagnostic has sampling/timer overhead; its absolute frame times are
not substituted for the uninstrumented benchmark above.

| Diagnostic CPU wall-time group | Average |
| --- | ---: |
| Geometry call and its host adapters | 4.69 ms |
| Host API processing | 3.02 ms |
| Other game and uncovered host work | 1.85 ms |
| Scene, renderer and shadow preparation/recording | 3.09 ms |
| Fence, submit, acquire and present calls | 0.69 ms |
| Image/buffer allocation and texture conversion | 0.24 ms |
| GPU query collection | 0.07 ms |
| Accounted frame interval | 13.64 ms |

The geometry group includes original rendering calls and modern wrappers;
it is not a pure original-geometry-body measurement. Host heap allocation
appears within these groups too: about 4.6% of samples reach host operator new.
This is not an allocation-byte or peak RAM/VRAM measurement.

GPU timestamps bracket every recorded command buffer in this renderer,
including the scene work, FXAA where invoked and presentation blits. Their
sum averages **1.29 ms**. GPU execution overlaps CPU work and must not be
added to the CPU frame budget. Display scanout and external compositor work
are outside these command timings. One slow diagnostic frame takes 35.50 ms,
with about 2.13 ms of recorded GPU commands; its geometry-call/adapters and
host API groups alone account for about 22.72 ms.

## The selected fix

Deeper stacks reveal that about **11% of the 13,368 main-thread samples** lead
to the world-mesh admission helper repeatedly reading MW34_GPU_TERRAIN through
the CRT environment lookup. The setting is supplied before process launch and
stays fixed. It was being rediscovered while classifying meshes, rather than
being retained with the other process settings. This host work sits inside
the broad geometry-call group and should not be mistaken for GPU shading cost.

Cache that flag once per process. Keep dynamic world-cell scope, all mesh-name
predicates and the original first-character flag interpretation unchanged.
No original producer, callback, geometry, lighting, shadow or texture is removed.
This improves the native geometry-admission handoff without introducing a
geometry bypass or changing simulation cadence.

Only world_geometry_stage.inc changes from the selected texture-staging and
controller host. The translated object list and every other host source match.
Selected executable SHA-256:
`d52fbf63c9bfbb04344bfa2fe78f81f6a85488011b16ca18144c1f4fb42d53dc`.
The authored installer reproduces the candidate bytes, is idempotent and rejects
an unknown anchor before writes. Seven asset-free process-setting cases exercise
missing/empty flags, retained legacy flag semantics, dynamic scope/name decisions
and the lifetime of the cached launch setting.

## Fidelity and limits

Separate visible verification runs match all **2,800 complete draw-diagnostic
rows** and **seven full-resolution captures**, including the cockpit transition
frames. All 2,800 non-timing per-present world-counter rows match across all four
timing runs. Budget exit 1 is expected for these bounded tests and does not
represent mission completion or normal shutdown.

The diagnostic itself also matches the baseline in all 2,800 draw rows and
seven captures. The full launcher suite and 12 prepared-pack checks pass.
The profiler stays in a private diagnostic host. Its deeper stacks and wider
GPU timing coverage address gaps in the earlier measurements; they add no
production overhead. Existing controller support, texture staging and warmups,
performance-monitor behavior and replay settings are retained. No commit or
signed update package is made. Formal acceptance remains **131/144**.

The deployed launcher also starts the exact selected executable with all 11
packs, reaches the live menu and returns to Ready after a normal exit 0.
The selected profile and saved settings remain byte-identical after that run;
replay and the performance monitor remain off.

Evidence is local under local/work-ahead/performance-framebudget-20261022,
including frame-budget.json, the bounded samples and source identities,
matched-summary.json, per-run inputs, captures, fixture/adapter checks and
source/deployment pins. Only this authored report is intended for Drive upload.

The remaining larger target is the original-render/host-adapter path. Separate
required original side effects from redundant host setup before moving the
handoff earlier. These measurements do not prove that the whole geometry call
can be bypassed, or establish campaign/combat gains. They do establish that
reducing visual fidelity or assuming the GPU needs less work would miss the
main bottleneck on this Training route.
