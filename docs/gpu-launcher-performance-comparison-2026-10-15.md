# Current alpha versus normal Remaster performance

Measured2026-10-15 on the user's Ryzen7 9700X / Radeon RX9070.
The **pre-repair alpha delivered35.4% lower average FPS** than the normal
Remaster launcher on this tested route. Its average frame time is54.8% higher.
This was a regression in the exact alpha package selected during that benchmark.

Follow-up: [the regression investigation](gpu-alpha-regression-investigation-2026-10-15.md)
isolates the cost to the experimental CPU producer's compilation recipe.
Restoring the optimized original object recovers approximately137FPS while
retaining GPU scenery. The measurements below describe the pre-repair alpha.
The alpha launcher now selects the corrected build.

| Selected launcher build | Mean frame time | Average FPS | 1% low FPS |
| --- | ---: | ---: | ---: |
| Normal: `gpu-native-fog-stock-r1` | 7.292ms | 137.14 | 74.53 |
| Alpha: `gpu-native-fog-alpha-r1` | 11.285ms | 88.61 | 43.36 |

Average FPS is measured frames divided by their total elapsed presentation
time. The1% low is the reciprocal of the mean slowest1% frame intervals.
The percentages use normal Remaster as the baseline:

```text
FPS change = (88.613565 / 137.137970 - 1) * 100 = -35.383640%
Frame-time change = (11.284954 / 7.291927 - 1) * 100 = +54.759569%
```

## Method and repeatability

Four fresh private1800-frame IA movement/yaw runs use normal/alpha/alpha/normal
order. Each measures frames801–1800 inclusive, excluding startup, loading and
the first519 completed3D frames. Both builds enter3D at frame282. There are
1000 measured presentation intervals per run and2000 per build. No slow samples
were removed. All four complete the requested budget and their full1800-frame
scene-count and virtual-clock sequences match. Script and copied settings
hashes match across all four.

| Run order | Build | Mean ms | Average FPS |
| --- | --- | ---: | ---: |
| A1 | Normal | 7.389 | 135.34 |
| B1 | Alpha | 11.273 | 88.70 |
| B2 | Alpha | 11.296 | 88.52 |
| A2 | Normal | 7.195 | 138.99 |

Settings match the launchers:3440x1440, FXAA, AF16, stock800-unit scenery,
original fog with the device-cache repair enabled,39texture banks, seven
replacement models, current GPU HUD pack and local music. Both use GPU model
geometry. Alpha additionally uses raw GPU scenery and fast binding, retaining
the launcher’s world counters and geometry profile logging. Normal has neither
of those optional logs, matching its launcher. Both retain frame-time logging.

No screenshots/readbacks, draw-hash logging, fog tracing, distance tracing or
heavy diagnostic payload captures run during measurement. Scripted virtual time
makes the movement route repeatable; these are warmed presentation timings,
not GPU timestamp measurements or a real-clock campaign traversal. A known
unresolved historical divergence is not diagnosed by matching scene/clock counts.
Earlier matched actual-mode fog tests establish original draw-count/hash
agreement through1000frames; this timing test does not record per-draw hashes.

## Interpretation and limits

This compares the two exact published launcher packages. Original CPU perspective
projection still executes: the alpha's experimental CPU projection bypass is
explicitly0. The alpha also carries the rebuilt original producer and memory
observers from that unfinished experiment. Their individual cost, world binding
cost and renderer cost have not been isolated in this comparison. The result
does not establish a general GPU-offload speedup or slowdown.

The previously reported25% CPU/GPU replacement-model difference used a different
control. Normal Remaster already uses GPU replacement models, so that earlier
percentage is not an additional gain over this normal launcher.

No launcher, executable, graphics setting or acceptance count was changed by
this benchmark. Strict acceptance remains131/144. Other maps, battle workloads,
resolutions and campaign missions need their own measurements.

## Retained evidence

Normal executable SHA256:
`866d6c7ce7e4aa566f9c06fa2b44afaaeb421591f58a44946830476121aba908`.
Alpha executable SHA256:
`7e31ec1df6e1911ece99778360f62fabf0fb9ebf4ce46ba0aea25978b789cd9d`.

`local/gpu-launcher-performance-r1/` retains frozen profiles, the private harness,
four runs with per-frame measurements and protected-file checks, analysis source,
and `results.json` with measurement/metadata hashes and the unrounded results.
Each live run uses private saves/settings. Original media and generated game
code remain local. No compile, concurrent game or additional benchmark was run
during these timings; unrelated existing Python processes were preserved.
