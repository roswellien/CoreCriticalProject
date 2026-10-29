# Current lighting performance and doubled world-normal strength

Recorded 2026-10-18. User-requested performance review of the existing native
lighting preview, with terrain/world-object normal strength doubled. This is a
configuration and measurement change; no renderer, original game code, model
geometry, simulation clock, asset bank or executable is rebuilt or replaced.
Formal acceptance remains 131/144.

## Strength change

Both `Play MW3 - Sky and Water Preview.cmd` and
`Play MW3 - Normal Mapping Preview.cmd`, including their sunrise/midday wrappers,
now select `MW34_SUN_GROUND_NORMAL_STRENGTH=2`, previously 1. The parameter covers
registered terrain and original textured world/object draws. Replacement-model
normal strength stays 1. Original mechs rendered through the original textured
object path share that path's strength. Dedicated water and cloud settings remain
0.45 and 0.35. Unknown/unregistered materials gain no invented normal map.

The two local profiles and their source-snapshot metadata record the change.
Frozen pre-change profiles are retained with the benchmark evidence. Regular
Play and standalone Big Lake settings are unchanged.

The corrected 1,200-frame strength check preserves every original
frame/draw-count/hash triple. The changed-pixel bounds at frame1190 are
`(1,289)–(3440,764)`, within the terrain/object region of this view. Sky, foreground
water and the replacement player mech remain unchanged in that comparison.

## Hardware and current graphics

- Ryzen 7 9700X, 8 cores / 16 logical processors; approximately32GB system RAM.
- Radeon RX9070, driver32.0.31035.1003; Windows11 Pro build26300.
- Current sky/water host SHA-256:
  `b6d5ea85f0c0c4f2fec5ece30ac015d59e901cff071cb98a6b9ddbab840408a0`.
- 3440×1440, FXAA, AF16, scenery distance1200 and fog distance1100, sunset preset,
  current upgraded textures and model registrations. Sun shadows are disabled
  in this profile. These results do not measure a shadow-enabled configuration.

## Method

Use existing frame-time and world-path counters, independent copied test pilots
and registries, and the established Campaign1, Training and Instant Action input
routes. Each matched comparison uses a consistent50ms diagnostic simulation
step; frame-time numbers come from the host's monotonic wall clock, not that
simulation clock. Strength1 and2 run in A–B–B–A order for each scenario. Initial
menus/loading/asset warmup are excluded from the steady measurement window.

The water phase is fixed consistently across matched runs; the real-clock
presentation check uses moving water. Setup/warmup stalls are retained separately
and are not folded into steady render-throughput figures.

Timed runs disable screenshots, expensive original draw hashing, material
binding tracing and sampling/scoped profiling. Verification captures/hashes and
diagnostic profiling are separate runs. The original frame-time logger and
world/model logs remain enabled; this is not a zero-instrumentation benchmark.

The repeatable matrix renders offscreen with the window hidden. It exercises
the native scene renderer but excludes swapchain presentation; reciprocal mean
frame time is therefore **render throughput**, not measured interactive display
FPS. Visible-window checks are reported separately. Every bounded run ends at
the expected diagnostic frame-budget stop, not a mission-completion or normal
quit assertion. Fixed inputs do not reproduce arbitrary user combat or a full
campaign playthrough.

An initial setup accidentally let inherited profile settings overwrite the
resolved sunset elevation/sky-auto values. Those runs are rejected and retained
under `lighting-performance-20261018-r1`; no performance conclusion uses them.
The corrected setup resolves the preset after profile bindings and lives under
`C:/Users/jcbla/MW34SunTests/lighting-performance-20261018-r2/`.

## Results

The repeated offscreen matrix shows no consistent cost from increasing world
normal strength. Each entry below averages two equal-length runs. Throughput
is the reciprocal of average frame time, not displayed FPS.

| Route | Strength 1, mean ms | Strength 2, mean ms | Throughput 1 / 2 |
| --- | ---: | ---: | ---: |
| Campaign 1 Mission 1 | 17.467 | 17.455 | 57.3 / 57.3 |
| Training | 7.475 | 7.538 | 133.8 / 132.7 |
| Original-model Instant Action | 9.79 | 8.63 | 102.2 / 115.9 |

Training varies more between repeats than the strength comparison. The Instant
Action difference does not establish that stronger normals improve performance.
That route uses an original chassis, with no replacement model queued; its late
measurement window contains a distant TL view, not high-poly combat.

A separate Big Lake route queues Mad Cat and Bushwacker replacements. Its live
traversal window, frames 1001–1500, measures 14.71 / 12.69 ms at strength 1 / 2,
with p99 37.29 / 37.72 ms and 9 / 7 frames above 33.33 ms. This is one pair,
insufficient for a strength-related speedup claim. The later scripted sequence
reaches mission failure; it is excluded explicitly, with the original window
and raw records retained. These tests do not cover all 15 models simultaneously.

Visible Vulkan presentation checks use the real simulation clock and moving
water, at strength 2 and the same resolution/settings:

| Route | Displayed FPS | Mean ms | p95 ms | p99 ms |
| --- | ---: | ---: | ---: | ---: |
| C1M1, 1,999 measured frames | 51.5 | 19.43 | 23.08 | 26.95 |
| Big Lake, 1,399 measured frames | 109.6 | 9.13 | 13.27 | 16.84 |

These are different workloads and clock modes from the offscreen matrix. Big
Lake's real-clock run remains in live traversal, with a living Mad Cat visible
at the final capture. C1 records one frame above 33.33 ms; Big Lake records none.

C1 peak process working set is approximately 3,352 MiB at both strengths;
resident normal texture bytes remain 29,630,464. This is process RAM, not VRAM.
The separate geometry profile reports 99,354 replacement GPU vertices and 28 GPU
batches per frame, zero CPU replacement vertices and zero near fallback vertices.
The measured C1 world window builds no new immutable geometry. Original TL world
and haze work remain substantial; terrain CPU removal is still unfinished.

Setup and warmup take approximately 33–45 seconds across the three main routes,
including scripted menus and asset initialization. Individual pre-measurement
frames reach approximately 9.3 seconds. These are retained separately and are
not claimed as pure loading-time measurements or steady gameplay performance.

## Background replay capture investigation

The existing automatic instant-replay video buffer defaults on when
`MW34_INSTANT_REPLAY` is absent. The main matrix therefore includes that current
default. Disabling explicit screenshots did not disable this buffer.

Source inspection and local symbolized samples show full-frame GPU readback,
byte-buffer reallocation/copies and asynchronous video queue submission from
`photo_replay_on_present`. The observed child encoder uses software libx264,
ultrafast, at 3440×1440 and 60 fps. Each raw BGRA frame is about 19.8 MB. This
identifies substantial capture work, not an exact percentage of steady frame
time: the sampling output includes teardown and is excluded from timing results.
Recorded host CPU time also excludes the child encoder. This finding concerns
the video buffer, not the separate game-state replay system.

Two replay-disabled controls complete at 11.13 and 10.94 ms mean, respectively
(89.8 and 91.4 frames/s throughput), with p99 17.98 and 17.46 ms and no measured
frames above 33.33 ms. Their average is 11.04 ms versus 17.455 ms for the two
current-strength replay-enabled runs: approximately **37% less frame time** or
**58% greater offscreen throughput**. The C1 world/model submission counters
must be compared alongside timings; these are sequential diagnostic controls,
not randomized or interleaved on/off trials. They support a substantial replay
capture cost in this scene, not a universal interactive FPS gain. All four runs
have identical measured world/model, sky, haze, mesh-reuse and scene counters.

The isolated replay-on retry stalled in the menu before reaching gameplay and
is excluded; the comparison uses the two completed main-matrix replay-on runs.
The no-replay controls use separate scratch capture directories and explicitly
set `MW34_INSTANT_REPLAY=0`; graphics, strength, preset, fixed-clock input and
measurement frames otherwise match. Neither interactive launcher has had its
replay setting changed. A next optimization should remove synchronous full-frame
readbacks/copies from normal presentation and evaluate hardware encoding or an
explicit user-controlled capture setting, then repeat visible on/off checks.

## Additional controls and limits

Disabling only sky/water detail measures 19.11 ms in a single C1 control and does
not recover performance. The flags also change material routing, so this does
not isolate a shader-only cost. No GPU timestamp or definitive GPU/CPU bottleneck
split is claimed.

A 1720×720 probe was rejected by the supported-resolution check. Separate hidden
1920×1440, AF1 and isolated-DVR probes stopped making frame progress; only their
owned native processes were stopped after checks. They have no valid timing
result and are excluded. Their causes remain unresolved; they do not establish
that those settings caused the stalls. Completed frame-budget stops are expected
diagnostic exits, not crashes or completed missions.

Raw timing, settings, hardware, symbolized samples and world-counter records
remain local under the corrected evidence directory. No renderer optimization
or executable change is included in this configuration/measurement work.

## Subsequent launcher change: replay video is opt-in

After reviewing these measurements, the user requested that automatic video
capture be disabled by default and offered explicitly in MW3 Launcher. The
existing Photo & Replay checkbox now defaults off and states: “Enabling the
rolling 60-second video buffer has a 30–35% performance impact; the actual cost
varies by system and scene.” The inaccurate hardware-acceleration/zero-impact
claim is removed. The requested 30–35% UI estimate does not replace the measured
approximately 37% frame-time reduction above.

Old settings without a replay-video settings version load with capture off,
preserving unrelated options. Once saved in the updated launcher, explicit
on/off choices persist. Both installed launcher locations have been updated and
their current saved replay choices set off. Regular native/lighting-preview and
standalone Big Lake launch scripts also default off, independent of an inherited
environment or old profile. An explicit `-InstantReplay 1` argument enables
capture; the GUI passes its selected value. Native binaries are unchanged and
depend on this explicit launch setting. Other photo/game-state replay features
and manual recording are not disabled by this video-buffer setting.

Validation: Debug WPF build succeeds with zero warnings/errors. Isolated C#
settings checks cover fresh/missing settings, old true-default migration without
changing resolution, and saved opt-in/opt-out reloads. Synthetic launch-boundary
checks confirm default/explicit-off/explicit-on reach the child environment as
0/0/1 even with an old profile and inherited value of 1. Big Lake script syntax
parses successfully. Both installed launcher DLL hashes match. These checks do
not add native-game acceptance credit; the prior native on/off measurements
remain the runtime evidence. Local fixtures and old launcher backup are under
`C:/Users/jcbla/MW34SunTests/replay-option-20261018/`. No game binary rebuild,
simulation change or commit is included.
