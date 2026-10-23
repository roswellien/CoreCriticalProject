# Native draw submission performance

This follows the [resource warmup work](resource-warmup-performance-2026-10-22.md).
It advances the native scene construction and Vulkan submission boundary, without
changing translated gameplay, shaders, lighting, shadow coverage or asset quality.
Strict acceptance remains **131/144**. Broader campaign, mission reload, combat
and sustained visible-play validation remain open.

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
