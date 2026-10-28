# Big Lake sun on/off benchmark — 2026-10-16

Directional sunlight plus ambient fill costs **2.7% average FPS** on this matched
Big Lake route. Average frame time rises **0.221 ms (2.8%)**. This measures the
whole optional lighting path, including its host capture/uniform work and GPU
shaders; it does not isolate GPU shader time or establish whole-game performance.

| Mode | Average FPS | Mean frame time | 1% low FPS |
| --- | ---: | ---: | ---: |
| Sun off | 124.85 | 8.010 ms | 37.47 |
| Sun on | 121.50 | 8.231 ms | 36.75 |

Run order: off1, on1, on2, off2. Individual averages: off 124.26 / 125.44 FPS;
on 121.27 / 121.72 FPS. Both pairs show a decrease with sunlight enabled.
The 1% low decreases about 1.9%; this is a limited two-run sample per mode.

## Method and matching checks

Ryzen 7 9700X / Radeon RX 9070. Same current sun executable in both arms, SHA256
`e34358483eefe78add184c5765a236d48eda7b449a03ac9bca912539c08895bc`.
3440×1440, FXAA, AF16, draw1200/fog1100, GPU world/models/HUD, fast binding,
CPU projection bypass0 and the same frozen original-model/texture assets.
Sun preset: azimuth225°, elevation35°, direct0.85, ambient0.30.

Four fresh private Big Lake original-menu/input-route runs, 1800 presented frames
each. Virtual simulation clock50ms gives repeatable simulation input; FPS is
actual host throughput, not the virtual simulation rate. These are not live-clock
gameplay results. Every interval ending at frames600–1799 is included:1200 samples
per run,2400 per mode. Startup and final image capture are outside that window.
No slow samples inside the window are discarded. Mean FPS is reciprocal mean
frame time; 1% low is reciprocal mean of each run's slowest12 intervals, averaged
between its two runs.

Optional draw/projection/geometry diagnostics and performance overlay are disabled;
the GPU world's required world log and frame timing remain enabled equally.
All1800 per-frame scene counts match across all four runs. Final original-world
geometry/cache counters match across modes, sunlight counters are active only
when enabled, and repeated final native-resolution captures match byte-for-byte
within each mode. Sun on/off images intentionally differ in illumination.
This supplies scene-consistency evidence, not every-frame pixel/semantic proof.
Vulkan validation layers are unavailable. No validation-layer coverage is claimed.

These fresh same-executable numbers should not be subtracted from the earlier
Remaster/alpha benchmark to infer a cross-build gain. Only the within-session
sun-on/off difference is the result of this experiment.

## Evidence and handoff

Local evidence under `C:/Users/jcbla/MW34SunTests/big-lake-r1/`:
`run-sun-benchmark.py`, `sun-benchmark-progress.log`, `sun-benchmark-results.json`,
and `runs/bench-sun-{off,on}-{1,2}/` with configuration, timings, world counters,
captures and native logs. All runs reach their intentional1800-frame budget;
this is not normal-quit or mission-completion credit.

Original pilot/registry/Mission2 save hashes and public launcher profiles match
their protected baselines. No game/build remains running, no code/defaults were
changed, and no commit was made. Acceptance stays131/144.

This is an addendum to [the rendering handoff](rendering-handoff-2026-10-16.md).
Normal mapping, cast shadows, local lights and bounced GI remain unimplemented;
their cost is not represented by this sunlight result. Development returns to
the user's requested pause after this benchmark.
