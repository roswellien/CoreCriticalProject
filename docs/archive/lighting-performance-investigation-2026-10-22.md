# Lighting performance investigation: Training

Investigated 2026-10-22 after the user reported new hitches with the installed
lighting packs, including Training. This is measurement and source inspection.
No playable host, shader, asset pack, simulation or launcher setting is changed.
The execution boundary remains the existing native Training update/render path;
the work identifies its rendering costs. Acceptance remains **131/144**.

## Current build and method

The latest completed user session, `b18ddc1ef9d04d10857b349da14195fc`, selects
`local/remaster/gpu-native-lower-horizon-r1/build/entry_commandline.exe`, SHA-256
`b1a3edb7ed84daf399fa4bb5f3ed246a9d718470e5f6b0fac4fc16e4961af1b6`.
The host runs on the Radeon RX 9070. Its installed lighting, normal, water,
cloud, fixture and environment bindings were reused. Replay capture is already
off; the previous model-path/name caches are present in the source.

The repeatable Training route uses independent copied pilots/configuration and
registry data, ordinary scripted input to skip the intro, and turns/movement
from the existing Training route. No user pilot is used for the runs. Rendering
is 3440x1440, FXAA, AF16, scenery 1600 and fog 1100. The diagnostic simulation
step is 16.666667 ms. Elapsed frame times use the host wall clock.

Four unprofiled runs execute in full / shadows-off / shadows-off / full order.
Only `MW34_FIXTURE_SHADOWS` changes in the controls: fixture illumination,
materials, geometry and remaining settings are retained. This isolates cost;
turning shadows off is **not** the proposed optimization. The normal launcher
continues to enable its existing shadows and quality settings.

Each run reaches the expected 2800-frame diagnostic budget. Measure frames
1200 through 2699, giving 1500 intervals per run and 3000 per condition.
Initial loading and menu time are excluded. Hashing, screenshots, geometry
scopes and sampling profiling are off during those timing runs. Existing
frame/world/model logs remain, so these are not zero-instrumentation results.
The window is hidden: these measure native render throughput, excluding
swapchain presentation, rather than displayed interactive FPS.

The older route initially consumed input during the now-working intro and
stayed in menus. Those runs are retained and excluded. A later menu-only run
was stopped by checking its owned PID and command line. None supplies gameplay
or performance evidence. All successful bounded runs exit at the intentional
frame-budget fault; these are not normal-quit or mission-completion tests.

## Measured results

| Condition | Mean frame | p95 | p99 | Frames over 33.33 ms |
| --- | ---: | ---: | ---: | ---: |
| Current full lighting | 17.460 ms | 27.069 ms | 30.083 ms | 9 / 3000 |
| Fixture shadows off, diagnostic only | 15.448 ms | 22.259 ms | 25.280 ms | 2 / 3000 |

Full-run means are 17.415 and 17.506 ms; control means are 15.453 and 15.444 ms.
The difference is **2.012 ms**, about **11.5%** of the full frame. This bounds
the entire fixture-shadow path's measured cost in this scene; an optimization
of one part cannot claim to recover that whole amount. No FPS improvement is
implemented or promoted. This does not quantify the complete before/after pack
installation regression; older measurements use different hosts and workloads.

All 2800 present rows match across all four runs after excluding the two timing
fields. These are world/render counters, not pixel hashes or a complete game
state comparison. No image equivalence is claimed for the shadows-off controls.

The measured route submits 435-4136 lit original TL draws per frame, averaging
1481, plus about 60 resident-world and 16 replacement-model draws. It averages
7.83 3D scene submissions per frame. There are no new immutable geometry builds
or mesh misses in the measured window. Several slow frames occur at the same
route positions in both conditions, including frame 1260. Shadows explain part
of the cost, not every hitch. Neither condition has a measured frame over 50 ms
in this window; larger user-observed hitches are not reproduced by this route.

A separate stationary Training sampling run places 19.38% of main-thread
samples in `Renderer::record_fixture_shadows` and 2.80% in
`prepare_fixture_shadows`. Sampling includes blocked/outside-executable time;
these percentages are not GPU timings or an exact CPU execution-time split.
The sampled run is not included in the timing table.

A second sampling run on the moving route, starting at frame 400, records
8154 of 29601 samples in retained caller stacks through
`Renderer::remaster_setting` (27.55%). Most of these instruction pointers are
inside UCRT, rather than the game's executable. The profiler records only its
300 most common stacks, so this is a recorded-stack fraction, not an exhaustive
inclusive-call measurement. This window includes some pre-measurement work;
the separate warm-window profile starts at frame 1200 and records **7410 of
20128 samples (36.81%)** in retained caller stacks through that same accessor.
The cost therefore persists in warmed Training gameplay. In this moving warm
profile, shadow recording accounts for 4.56% of leaf samples and preparation
1.31%; the stationary profile's larger fractions must not be substituted for
the moving workload. These profile runs are excluded from the timing table.
The lookup stack fractions are evidence for the first candidate, not a promise
that caching recovers that fraction of unprofiled frame time.

Source inspection explains why this is a candidate: `remaster_width()` parses
both environment variables on every call, and `remaster_height()` calls it and
parses height again. Widescreen/HUD helpers call these accessors repeatedly.
`is_admitted_world_name` also calls `getenv` for a fixed terrain flag. This is
separate from the earlier model-roster cache fix, which is still present.

## Optimization priorities without reducing fidelity

1. **Cache launch-fixed display settings.** Read and validate the exact width
   and height once, retaining the current absent/incomplete/invalid-value and
   AA/AF checks. Reuse those integers in HUD/aspect helpers. Cache the fixed
   terrain-admission flag separately. Confirm no live setting path depends on
   changing these environment variables; real target/window changes still need
   their normal handling. This removes lookups and parsing, with no changed
   shader, texture, geometry, resolution or projection formula. Measure an
   isolated candidate and require exact full-quality image/draw comparisons.
2. **Remove redundant fixture-shadow culling math.** In
   `tools/remaster-launcher/native-overrides/fixture_shadow_stage.inc`,
   `record_fixture_shadows` repeats the same eight box-corner clip transforms
   for each of six plane tests. Compute each corner once per light face and
   reuse it, retaining the same arithmetic order and clipping decisions.
   Cache the light/caster radius rejection across the six faces as well.
   Preserve every caster, light, face, atlas resolution and alpha-test rule.
   The private host's file is byte-identical to that maintained template.
3. **Reuse unchanged shadow work with explicit invalidation.** The current
   path reconstructs TL casters, scans model vertices for bounds, builds
   temporary vectors and redraws the fixture atlas during scene submissions.
   Exact cached bounds and light/caster lists can avoid repeated work. Reusing
   atlas depth requires tracking light identity/slot, geometry/pose/transform,
   alpha texture and sampler, destruction, mission generation, retained casters
   and newly arriving split-scene casters. Moving shadows must remain current;
   updating every other frame is not a fidelity-preserving substitute.
4. **Reuse scene and descriptor allocations; avoid redundant bindings.**
   `vk_scene.hpp` resets the descriptor pool and rebuilds color/normal descriptor
   tables each scene. `d3d_provider.inc` builds vectors and expands primitives
   into captured triangles. Reserve/reuse owned storage and cache descriptors
   against resource generations and fence lifetimes. Keep draw order, flat
   shading's provoking vertex, depth, blending and surface-read semantics.
   These address the heavy TL submission stretches that remain with shadows off.
5. **Move first-use preparation out of active play.** Pipeline variants are
   created synchronously on a draw miss with a null `VkPipelineCache`;
   normal pages are read/validated on first use. Prewarm the exact required
   pipelines and prefetch required mission pages during loading, within existing
   memory limits and integrity checks. A persistent driver-compatible pipeline
   cache can reduce repeat compilation. These are source-backed hitch candidates,
   not a demonstrated explanation of frame 1260. See Khronos's
   [pipeline management sample](https://docs.vulkan.org/samples/latest/samples/performance/pipeline_cache/README.html).
6. **Measure GPU passes before a larger lighting rewrite.** Add bounded GPU
   timestamp measurements around fixture depth, main lighting and presentation
   to resolve the currently missing GPU attribution. If fragment lighting is
   dominant, conservative per-draw or tiled light lists could skip lights that
   provably cannot contribute, preserving original list order. Keep the light
   count, radii, shadow sampling and normal textures. See Khronos's
   [timestamp example](https://docs.vulkan.org/samples/latest/samples/api/timestamp_queries/README.html).

The first implementation candidate should cache the display accessors, whose
cost is confirmed in the warm profile, followed by the small shadow-culling change
in an isolated host. Verify identical settings, culling decisions and matched
full-quality captures, then measure the same route without profiling. Include light-face and
radius boundaries, alpha cutouts, moving mechs, destruction, mission reload and
retained off-camera casters. A speedup remains unproven until that candidate
passes. Original AI, physics, simulation timing and render producers retain
their contracts; removing guest work needs separate ownership evidence.

Local evidence and reproduced source snapshots are under
`local/work-ahead/lighting-performance-20261022/`, including `comparison.json`,
per-run inputs/settings/timings and symbolized profiling. Original media and
generated game code remain local. Nothing committed.

## Implemented display cache and measured result

The first candidate above is now implemented in the isolated native host
`local/remaster/gpu-native-display-cache-r1/`. Width and height are read and
validated once per process, then reused by the existing rendering helpers.
The validation, projection arithmetic, resolution, shaders, lighting, shadows,
textures and original simulation are unchanged. Environment variables are fixed
at launch; this does not replace actual window/target resize handling.
The fixed terrain flag and shadow optimizations remain future work.

The existing `apply_perf_env_cache.py` installer now provides `--display-only`
with exact source anchors, repeat-application checks and rejection of unexpected
source. It reproduces the tested private host patch. Only `vk_scene.hpp` changed
among the predecessor's 121 host files; translated object inputs are unchanged.
Twenty valid/invalid display configurations produced identical accessor values
or errors against the predecessor, including AA/AF requirements and boundaries.

Unprofiled, full-quality Training runs in candidate/baseline/candidate order
used the same scripted route, guest diagnostic clock and launch environment.
The warm measurement window was frames 1200 through 2699. Presentation was
hidden, so these are equivalent render-throughput figures, not measured monitor
FPS or a claim that every mission has returned to the former 60–200 FPS range.

| Warm Training measurement | Predecessor | Display cache |
| --- | ---: | ---: |
| Samples | 1,500 | 3,000 across two runs |
| Mean frame interval | 17.541 ms | 11.126 ms |
| Equivalent throughput | 57.01 FPS | 89.88 FPS |
| 99th percentile interval | 29.960 ms | 23.707 ms |
| Intervals above 33.33 ms | 3 | 0 |

This is **57.66% higher throughput and 36.57% less frame time** for this route.
All 2,800 non-timing world/render counters matched in each timing run. Separate
fidelity runs matched all 2,800 original frame/draw-count/hash records, and
four 3440×1440 captures at frames 1250, 1500, 1900 and 2500 were byte-identical.
The fixed-clock/budget benchmark is separate from normal launch/quit testing;
its expected budget termination does not establish a normal game exit.

The candidate executable SHA-256 is
`f5cde368f9d1bc6f109180015d4d8e2984a5551a8efdc1d67b9af5c0b54206f2`.
Pack compatibility admits this exact successor only where its unchanged
predecessor resource readers were already reviewed. No wildcard admission was
added. Launcher checks and all 12 prepared mech/environment pack tests passed;
the launcher was published self-contained for Windows x64.

The normal `local/remaster/launcher.json` now selects this candidate. Previous
profile, settings and installed launcher files are retained under the private
evidence directory for rollback. The profile backup is
`launcher-profile-before-display-cache.json`; the old native host remains intact.
Replay stays off and all 11 packs and full-quality graphics stay enabled.
Evidence includes `display-cache-source-pins.json`,
`display-settings-results.json`, `display-cache-comparison.json` and
`display-cache-verification.json`. This advances the existing native render
execution path; acceptance remains **131/144**, with no new native-game credit.

Normal launcher smoke test completed in session
`2800a93dc72c46a5aff11f29b0f79fb8`: all 11 packs prepared, the candidate started
at 3440×1440, played the intro and reached the enhanced main menu. Closing the
game normally returned native exit 0. Saved launcher settings were byte-identical
to their pre-deployment backup. This smoke test does not substitute for the
controlled Training measurements or establish performance across other missions.
