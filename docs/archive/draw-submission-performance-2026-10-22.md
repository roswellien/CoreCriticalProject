# Native draw submission performance

This follows the [resource warmup work](resource-warmup-performance-2026-10-22.md).
It advances the native scene construction and Vulkan submission boundary, without
changing translated gameplay, shaders, lighting, shadow coverage or asset quality.
Strict acceptance remains **131/144**. Broader campaign, mission reload, combat
and sustained visible-play validation remain open.

## October 23: earlier command batching, performance revision 6

Revision 6 moves compatible lit world-triangle batching ahead of repeated host
scene preparation. Every original per-call validation, logging, geometry,
lighting/effect capture and suppression decision still runs. Exact vertex bytes,
triangle order and immutable bindings are retained. Clears, scene boundaries,
models, HUD/zoom, unlit routing, indexed draws and fixture-proof commands remain
barriers. The source adapter is `tools/remaster-launcher/apply_early_triangle_commands.py`;
the authored helper and fixture are `native-overrides/early_triangle_commands.hpp`
and `tests/early_triangle_commands_checks.cpp` in the same tools directory.
The helper passes 96,028 ownership, byte-preservation, topology and barrier checks.

These are visible, uncapped moving Training tests on Ryzen 7 9700X / Radeon
RX 9070, 3440x1440, FXAA, AF16, fog 1100 and full existing lighting/shadows.
Replay and the overlay are off. Each setting has two controls and two candidate
runs in before/after/after/before order; timing excludes image capture/profiling.
The fixed diagnostic guest clock is identical within each comparison block;
interactive simulation timing is unchanged. Competing render/game processes
prevent admission, including Blender. Warm frames are 1200–2699; heavy frames
are 1200–1844. Compare within each block, not across the two settings.

| Draw distance / metric | Revision 5 | Revision 6 |
| --- | ---: | ---: |
| 3200: warm average FPS | 85.53 | 92.73 |
| 3200: warm 1% low FPS | 41.18 | 48.54 |
| 3200: warm mean frame interval | 11.692 ms | 10.784 ms |
| 3200: heavy average FPS | 62.26 | 71.53 |
| 1600: warm average FPS | 117.06 | 132.30 |
| 1600: warm 1% low FPS | 54.23 | 65.57 |
| 1600: heavy average FPS | 80.30 | 95.92 |

At the user's current 3200 setting, warmed throughput improves 8.4%, heavy
throughput 14.9% and warmed 1% lows 17.9%. Both candidate heavy means beat both
controls at each setting. All 2,800 original draw rows and seven full-resolution
images match at each setting, fourteen images total; final GPU draw counts match.
At 1600, renderer preparation records fall 5,051,626 -> 1,669,734 while final GPU
draws stay 717,752. At 3200, records fall 6,981,677 -> 3,527,832 while GPU draws
stay 1,179,646. This removes repeated CPU preparation and makes no measured
whole-game RAM/VRAM claim. Shaders, shadow resolution, textures, gameplay and the
translated module are unchanged. Broad campaign/combat/hardware coverage remains
open. Bounded frame-budget exit 1 is not normal-quit or mission-completion evidence.

Private evidence is `D:/MW3EarlyTriangleCommands-20261023-r1`; release assembly
is `D:/MW3PerformanceUpdate-20261023-r6`. The timestamped signed native hash is
`9032ffbc5b3e4bd5d6ee63ff8147f37809491b6079f73869fb109129727f717a`.
Only `mfc_stage.hpp`, `d3d_provider.inc` and the new helper change from revision 5.
Development selects this build with `MW34_EARLY_TRIANGLE_COMMANDS=1`; all user
quality settings and installed asset bindings are preserved. The weaker camera,
ownership, light-mask and GPU shadow-clipping experiments are excluded.

The signed [revision-6 update](https://playtest.corecritical.dev/updates/mw3-performance-20261023-r6/MW3PerformanceUpdate.zip)
is published under Setup as a ZIP containing the `.mw3update`, matching precompiled
payload and instructions. Minimum launcher is 1.0.27, sequence 2026102309. Real
verification, installation, activation, full validation and rollback passed from
the retained 1.0.27 installer, current 1.0.28 installer and previous performance
revision 5. Original inputs are verified; no compiler or regeneration is needed.
All five remote objects match full local readback hashes; both Setup catalogs
retain the 1.0.28 installer, ISO, English patch and every asset-pack row. The full
1.0.28 installer itself still contains revision 5; apply the optional update for
revision 6. The separate remote Op1M1 surface-arena report remains unresolved.

The remaining sections retain the earlier October 22 late-batching investigation.

## Diagnosis and implementation

A fresh CPU sample profile of the selected warmup host finds expensive frames
with roughly 4,000 lit TL draws. Scene construction repeatedly grows large draw
and vertex arrays; the renderer submits a separate Vulkan draw for each original
draw. Texture preparation still contains first-use work, but the earlier upload
measurements do not establish it as the main sustained throughput bottleneck.

The selected change:

- Reserves scene draw, order and converted-vertex storage from captured command
  counts, with a host allocation bound check. Moves completed draw records into
  storage instead of copying their lighting/material/function state.
- Combines only adjacent complete TL triangle lists with contiguous vertices and
  identical effective pipeline, texture/sampler descriptors, push constants,
  scissor and, when lit, normal descriptors and the entire 912-byte lighting block.
  Clears, model draws, points, incomplete primitives and state changes stop a run.
  Primitive order and every logical draw remain intact. Existing diagnostic draw
  and lighting counters continue counting logical draws.
- Assigns exact consecutive uniform-run IDs in CPU memory, rather than hashing
  or numerically comparing floats. Equal IDs guarantee byte-identical inputs;
  recurring values in separate runs can conservatively receive different IDs.
  No uniform comparison reads GPU upload memory. The scene-local extra state is
  one previous uniform and one integer per draw.

`apply_submission_optimization.py` installs the authored adapter changes on the
modern warmup host. It validates all anchors before writing, and pins the four
reviewed TL shader headers. Shader revisions require rechecking the batching
contract. `MW34_TL_COMBINE=0` disables combining for diagnosis; invalid values
fail visibly. The selected launcher profile explicitly enables it.

The renderer still builds its existing per-scene texture descriptors. No
persistent descriptor cache, lighting reduction, shadow omission, texture
downscaling, simulation-rate change or production fallback was introduced.

## Matched Training comparison

Reference is resource-warmup r3, SHA-256
`02e328354eeb5b49ad288f5619b765655c0f0263d30d4f9ba2a650ce73cb729b`.
Candidate is submission r3, SHA-256
`608c41b14d8ecfb7f27ffef1624663cd6d092ea77bc4dd89247260f8f9af8ef9`.
Among final comparison runs the order is reference/candidate/candidate/reference.
Both use normal prewarm, the same learned pipeline recipe, monitor on, replay off,
3440x1440, FXAA, AF16, draw distance 1600, fog distance 1100 and full lighting.
Each run has independent copied pilot/config/registry data and the same scripted
Training route. The diagnostic guest clock is fixed at 16.666667 ms; measurements
use real host frame intervals. Profiling and image capture are off for timings.

The window is hidden: these FPS values are **equivalent render throughput**, not
displayed gameplay FPS. Results are local to this machine and route. Fresh
reference measurements differ from the earlier warmup study; compare within this
matched cohort rather than combining its absolute numbers with older results.

| Frames 400–2699, pooled two runs each | Before | After |
| --- | ---: | ---: |
| Average equivalent FPS | 76.98 | 81.67 |
| Mean frame interval | 12.99 ms | 12.25 ms |
| 1% low equivalent FPS | 29.73 | 31.17 |
| Worst interval | 75.51 ms | 74.63 ms |
| Intervals above 50 ms | 8 / 4,600 | 8 / 4,600 |

Average throughput improves about **6.1%**; the 1% low improves about **4.9%**.
Each candidate run is faster than either reference run in this cohort. The 1%
low is the reciprocal of the mean of the slowest ceiling-one-percent intervals.
In the later 1200–2699 window, pooled averages are 87.27 to 91.87 equivalent FPS
and 1% lows are 38.46 to 41.02. These are alternate windows of the same runs,
not additional independent repetitions.

Each monitor-on candidate run retains 5,060,558 logical draws but submits
722,785 GPU draws: 4,337,773 adjacent TL draws combined, about **85.7% fewer GPU
draw commands**. This does not mean 85.7% higher FPS. Substantial CPU/game work
remains, and the approximately 75 ms first-use hitch is essentially unchanged.
This is a modest sustained-throughput improvement, not restoration of the full
user-reported 60–200 FPS range.

## Verification and rejected trials

The selected candidate's separate monitor-off fidelity run matches all 2,800
complete original draw-log rows against the warmup reference. Full-resolution
captures at frames 1250, 1500, 1900 and 2500 are byte-identical. This covers the
tested route and views, not every campaign/material/zoom/combat combination.
All 2,800 non-timing world-counter rows also match across the four timing runs.
Diagnostic frame-budget exits are expected exit 1 and do not prove normal quit.

The uniform-run fixture exercises every bit of a 912-byte block, 14,592 changed
and restored transitions, signed zero, NaN payloads and scene reset. The installer
reproduces the selected adapter bytes exactly, is idempotent, and rejects changed
shaders or malformed renderer anchors before any writes. The full launcher suite
and 12 prepared mech/environment tests pass. The first launcher-suite attempt
correctly stopped at its active-game update guard while the fidelity run was
still open; the rerun after game closure passes without changing that guard.

An initial batching prototype compared uniforms in mapped upload memory and
regressed badly. A second kept full CPU copies and gave a smaller gain. Neither
is selected. The final bounded uniform-run implementation removes those reads
and copies; all private prototype artifacts and timing evidence remain intact.

Only `d3d_provider.inc` and `vk_scene.hpp` differ from the warmup host, plus the
new authored `exact_uniform_runs.hpp`. All other pinned host files and the
translated object list remain unchanged. Exact successor admissions were added
to the existing reviewed pack/resource compatibility sets; no wildcard was added.
The dev launcher preserves the current shared 1.0.19-preview sources and existing
settings. Previous binaries and profile are retained for rollback. No signed
update package, upload or commit is made.

Private evidence: `local/work-ahead/performance-submission-20261022/`, especially
`matched-summary.json`, `fidelity.json`, `adapter-final-checks.json`,
`baseline-profile/analysis.json`, per-run inputs/logs, launcher checks, publication
and deployment hashes. Remaining work includes first-use GPU texture/mipmap
preparation and fixture-shadow CPU work; GPU-pass measurements are needed before
claiming a GPU bottleneck or selecting a larger lighting change.

Final normal-launch smoke test: session `8582874a50074053bf68f9da20beacdc`
prepares the selected 11-pack configuration and starts the exact selected host
after 122 seconds of preparation. The intro and enhanced menu render normally;
the runtime reports 11 known pipeline states prepared, FXAA, AF16 and the existing
fixture shadows. Normal Alt+F4 returns `ExitProcess(0)` and coordinator exit 0.
Saved settings are byte-for-byte unchanged, including replay off. The updated
launcher is left open and ready.
