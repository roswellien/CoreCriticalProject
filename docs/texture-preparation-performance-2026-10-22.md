# MW3 texture preparation performance

The next optimization prepares catalog-matched resident world textures during
the first mission load. It reduces a repeatable first-use hitch while retaining
the current resolution, textures, normal maps, lighting, shadows and gameplay.
This follows the resource-warmup and draw-submission updates. Formal acceptance
remains **131/144**; broader campaign, mission reload and sustained play remain open.

## Before and after

Three runs per setting, 6,900 measured intervals per condition, frames 400-2699:

| Metric | Preparation off | Preparation on |
| --- | ---: | ---: |
| Average equivalent FPS | 78.28 | 80.10 |
| 1% low equivalent FPS | 28.55 | 32.53 |
| Mean frame interval | 12.77 ms | 12.48 ms |
| Worst frame interval | 74.60 ms | 62.17 ms |
| Intervals above 50 ms | 12 / 6,900 | 9 / 6,900 |
| Target frame 1163, mean | 74.14 ms | 37.89 ms |

The target hitch consistently drops from 73-75 ms to about 38 ms. Overall 1% lows
improve about **14%**, and the worst interval falls about **17%**. Other hitches
remain around 54-62 ms. This improves smoothness; it does not eliminate all stalls.

These are **hidden-window equivalent render-throughput measurements**, not
displayed gameplay FPS. The small average difference, about 2.3%, is sensitive
to run variation. In the later frames 1200-2699, pooled averages are 89.34 versus
89.85 equivalent FPS: essentially unchanged. The initial two-run comparison had
that later window about 2% slower with preparation; an additional on/off pair
did not establish a persistent warmed-up throughput regression. All six timing
runs are retained; no run was discarded.

## What caused the hitch

A separate diagnostic build measures CPU phases and completed GPU timestamps.
At frame 1163, its 75.32 ms interval includes:

- 14.02 ms in CPU-side image allocation and setup.
- 17.61 ms in CPU staging conversion/copies.
- 1.86 ms of GPU upload/mipmap work across that frame's scenes.
- 2.81 ms of CPU fence waits.

The scene-construction scope totals 44.72 ms and includes several of those CPU
phases; these numbers must not all be added together. Other game/host work also
contributes. GPU timestamps cover model/texture transfers and mip generation in
the upload interval, a pre-main interval including target transitions, FXAA and
shadows, and the main draw interval. Results are collected after the existing
scene fence completes; timestamp wrap width and device period are respected.

Other large frames show the same texture preparation pattern. This supports
moving resource preparation earlier; it does not establish sustained GPU saturation.
Instrumentation stays in the private diagnostic host and is not installed.

## Selected implementation and cost

At the first eligible world scene, use the existing material cache's full-content
matching and surface identity checks to find already-resident world textures.
Require a live, unlocked 16-bit texture surface, matching version, dimensions,
pitch, backing address and format. Exclude render-target, back-buffer, primary
and depth surfaces. Synchronize existing producers before reads and recheck the
version. Deduplicate matching normal textures and skip resources already bound
in the scene or current in the GPU cache.

Append preparation-only texture references to the normal scene upload path.
They emit no new draw and use the existing conversion, mip generation and resource
validation. A **256 MiB nominal RGBA8 full-mip-chain budget** bounds additional
preparations. Over-budget resources keep their original on-demand path and quality.
Invalid required catalog indices and invalid flag values fail visibly.

Training prepares **115 albedo and 115 normal textures**, totaling about
**204.7 MiB of additional mip data** at that point, below the cap. Some resources
are prepared before they would be encountered, so RAM/VRAM residency increases.
Staging buffers and driver allocation overhead are additional; this nominal budget
is not a measured cap on total process RAM or VRAM. Peak RAM/VRAM was not profiled.

The initial mission-load interval averages 5.70 seconds off versus 5.89 seconds
on: approximately **0.19 seconds longer** in this cohort. This is separate from
launcher pack preparation. The current implementation prepares only the first
mission per process; subsequent missions retain normal on-demand behavior.

The launcher enables `MW34_TEXTURE_PREWARM=1`. Setting it to 0 disables this
preparation for diagnosis. Existing display caching, pipeline/normal-page warmup,
draw batching and performance-monitor behavior remain intact.

## Method and validation

All timing runs use the same executable, scripted Training route, independent
copied pilot/config/registry data, normal-page warmup and learned pipeline recipe.
Settings: 3440x1440, FXAA, AF16, draw distance 1600, fog distance 1100, full lighting,
monitor on and replay off. The diagnostic guest clock is fixed at 16.666667 ms;
measurements use real host intervals. Captures and profiling are off for timings.
Run order is on/off/off/on/off/on. The last pair checks the warmed-up variation.

A separate monitor-off fidelity run matches all 2,800 original draw count/hash
records and four full-resolution captures at frames 1250, 1500, 1900 and 2500.
Captures are byte-identical to the installed draw-submission predecessor. Complete
diagnostic draw rows match except the intentional mip-preparation counter: its
final value changes from 8,354 to 9,619 because more resources were prepared.
All non-timing world-counter rows match across the timing runs. Budget exit 1
is expected for the diagnostic runner and is not normal-shutdown evidence.

The asset-free fixture checks unchanged source pixels, current GPU resources,
stale surface identities, dead/locked surfaces, render-target exclusions,
menu/view gating, synchronization changing a version, invalid normal indices,
disable/invalid flags and the exact 256 MiB boundary. The authored installer
reproduces the candidate bytes, is idempotent, and rejects malformed anchors
before writes. The full launcher suite and 12 prepared-pack checks pass.

The selected native host is `gpu-native-texture-warmup-r1`, SHA-256
`17f9a1c3bb601c39f3355220b27ded29d709bbeaf770cc91acbadf499acada49`.
Only `d3d_provider.inc` and `surface_normals_stage.inc` differ from predecessor
`608c41b14d8ecfb7f27ffef1624663cd6d092ea77bc4dd89247260f8f9af8ef9`,
plus the new authored `surface_texture_warmup.inc`. Shaders, other pinned host
sources and the translated object list are unchanged. Exact compatibility
admissions preserve reviewed resource readers; no wildcard was added.

The dev launcher retains the current shared 1.0.19-preview sources, including
the controller work and its pinned runtime. Existing settings are preserved.
Previous launcher binaries/profile are retained for rollback. No signed update
package or commit is made. Only this authored report is intended for Drive upload;
game media, generated game code and raw evidence stay local.

Private evidence: `local/work-ahead/performance-textures-20261022/`, including
`matched-summary-final.json`, `diagnostic-summary.json`, `fidelity.json`, adapter
and source checks, per-run inputs/logs, launcher checks and deployment hashes.
Next targets are the other first-use stalls and fixture-shadow CPU work; their
resource identities and costs need separate measurement before implementation.

Final normal-launch smoke test: session `bba2b8c9173b4d789272caf1197ed41d`
prepares the 11-pack configuration, starts the exact selected host after 122
seconds of pack preparation and renders the intro and enhanced menu. FXAA,
AF16 and fixture shadows remain enabled. Normal Alt+F4 returns `ExitProcess(0)`
and coordinator exit 0. The selected texture-preparation flag is enabled;
saved settings are byte-identical, including replay off. The updated launcher
is left open and ready.
