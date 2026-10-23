# Native resource warmup and Training hitches

Implemented after the user reported FPS slowly climbing and intermittent large
drops with lighting installed. The selected dev host keeps the previous display
settings cache and performance monitor. This advances native resource preparation
before the first world frame; original gameplay, shaders, lights, shadows,
resolution and filtering remain unchanged. Strict acceptance stays **131/144**.

## Diagnosis

Recent user sessions select the expected monitor host, with replay off. Several
large stalls coincide with mesh misses, but existing QPC counters place only
0.43 ms of a 307 ms frame inside world snapshot/decode work. A separate,
diagnostic-only host adds bounded CPU scopes around actual preparation calls.
On the moving route, a late pipeline creation takes 118 ms, and normal-page
reads/validation account for additional first-use delays. Individual model-buffer
allocations are below 1 ms in that diagnostic; fence waits are below about 2.1 ms.
Those are CPU scopes, not GPU timestamp measurements or proof of every user hitch.

The monitor itself adds about 0.69 ms/frame in the initial off/on/on/off warm
comparison. Its existing GPU overlay allocated and cleared full-size CPU color
and depth arrays even though it requests neither upload nor readback.

## Selected implementation

- At the first world normal binding, check live, unlocked resident texture
  surfaces through the existing version/content matching path. Load and validate
  their needed normal pages there, rather than on later first visibility. Keep
  authored exclusions, material roles, page validation and the existing memory
  budgets. This prepares the first mission after launch, not every future mission
  automatically; mission re-entry and broader campaign coverage remain open.
- Remember successfully created pipeline-state configurations in a bounded
  64-entry numeric recipe in user storage. Prepare those known states at renderer
  initialization on subsequent launches. Unknown states still use the real
  on-demand Vulkan creation path, then become learnable. No shaders, driver
  binaries, original media or translated code are stored in the recipe. Invalid
  optional recipes are rejected/ignored; actual required pipeline failures remain
  visible. Writes occur during renderer shutdown, outside the frame loop.
- Remove the monitor's unused CPU color/depth buffers. Reset its measurement
  window on the gameplay/menu transition so an initial loading pause does not
  depress gameplay statistics for the next ten seconds. This reset is a reporting
  correction and must not be counted as a rendering speedup.

The launcher supplies `MW34_NORMAL_PREWARM=1`, `MW34_PIPELINE_WARMUP=1` and a
per-user `cache/pipeline-warmup-v1` directory. Internal diagnostic controls can
disable either warmup independently. Monitoring and rolling video replay remain
separate saved choices. Existing settings are preserved, including the user's
current draw-distance choice.

`apply_pipeline_warmup.py` reproduces the selected patch on a modern private host
that already has the current monitor adapter. The older maintained renderer
template lacks modern normal resources and is intentionally rejected rather than
silently replaced. Its failed installation attempt made no adapter writes.

## Matched normal-page comparison

Both conditions use the same candidate executable, learned pipeline recipe,
monitor enabled, 3440×1440, FXAA, AF16, draw distance 1600 and fog 1100. Only
normal prewarming changes. Runs execute off/on/on/off on the same scripted
Training route, with copied pilot/config/registry data and a fixed diagnostic
guest clock. Measure real host intervals at frames 400–2699, excluding the initial
mission-loading frame. Each condition contributes 4,600 intervals. Profiling and
captures are off. The window is hidden, so FPS is equivalent render throughput,
not a displayed-FPS claim.

| Post-loading Training metric | Demand loading | Normal warmup |
| --- | ---: | ---: |
| Average equivalent FPS | 71.46 | 72.24 |
| Mean frame interval | 13.99 ms | 13.84 ms |
| 1% low equivalent FPS | 22.83 | 28.51 |
| Worst interval | 151.47 ms | 75.11 ms |
| Intervals above 50 ms | 12 / 4,600 | 8 / 4,600 |

The prominent frame-1163 hitch is 142.93–151.47 ms in controls and 74.44–75.11 ms
with warmup. Frame 1168 drops from 70.42–73.34 ms to 32.97–33.10 ms. The average
FPS difference is small; the clear improvement is first-use stalls and 1% lows.
The 1% low uses the reciprocal of the mean of the slowest ceiling-one-percent
intervals, matching the monitor's definition, over this longer test window.

By route end, world-normal residency rises from 186,294,272 to 255,418,368 bytes,
about **66 MiB extra**, within the unchanged 512 MiB world-normal budget. Initial
mission-load intervals average about 0.3 seconds longer across these runs;
startup varies with driver and OS caches. This trades bounded loading work and
memory for fewer later stalls, not reduced fidelity.

A separate comparison against the previous monitor executable measures averages
around 73.5 versus 72.0 equivalent FPS across different repeated cohorts. There
is **no demonstrated substantial average-FPS increase** from this update. The
matched same-executable test above isolates the normal warmup effect; do not
present the larger display-cache gain from the earlier task as a new gain here.

## Validation, rejected trial and deployment

The selected executable is
`local/remaster/gpu-native-resource-warmup-r3/build/entry_commandline.exe`, SHA-256
`02e328354eeb5b49ad288f5619b765655c0f0263d30d4f9ba2a650ce73cb729b`.
Relative to the monitor predecessor, six host files differ: `vk_scene.hpp`,
`gpu_hud.inc`, `surface_normals_stage.inc`, `vdd.inc`, `performance_monitor.hpp`
and the new `pipeline_warmup.hpp`. Generated game-object inputs are unchanged.

The selected build's separate 2,800-frame fidelity run matches all original draw
records, including full diagnostic rows, and all four full-size captures at
frames 1250, 1500, 1900 and 2500 are byte-identical to the predecessor. All four
normal-warmup timing runs also match non-timing world counters. Diagnostic budget
exits are expected exit 1 and are not normal-shutdown evidence.

Pipeline recipe checks cover valid/invalid fields, malformed/truncated/duplicate
records, optional disable, invalid flags, persistence and no frame-loop writes.
Monitor checks cover reset epochs as well as its prior statistical/pixel bounds.
Launcher checks cover absolute user-cache bindings and normal-warmup activation;
the full launcher suite and 12 prepared mech/environment tests pass.

A shadow-culling trial cached eight transformed box corners across six plane
tests. It preserved 120,000 differential frustum decisions and captured pixels,
but its repeated timing runs did not improve throughput. It is **not installed**;
public shadow sources were restored. Private r4 artifacts and the differential
fixture remain for inspection. No lights, shadow faces, casters or atlas sizes
were removed.

The dev launcher's normal profile selects the verified r3 host, and current
launcher sources were published self-contained after checking they remained
unchanged during publication. Exact host compatibility admissions preserve the
reviewed resource formats; no wildcard is added. Previous launcher binaries,
profile and settings are retained under the evidence directory for rollback.
The known Training pipeline recipe seeds user storage only when absent; existing
user recipes are preserved. No signed update package, upload or commit is made.

Private evidence: `local/work-ahead/performance-next-20261022/`, especially
`matched-normal-summary.json`, `normal-prewarm-abba.json`,
`preparation-summary.json`, `selected-fidelity.json`, `source-pins.json`,
`launcher-source-pins.json` and per-run inputs/logs. The next remaining targets
are on-demand GPU texture upload/mipmap work and sustained heavy TL draw
submission. New GPU-pass measurements are needed before a larger lighting change.

Final normal-launch smoke test: session `c15f9028315c4e2c97a61cd030ff89de`
prepares all 11 packs, launches the selected r3 hash with both warmup flags and
the per-user recipe directory, reports 11 known pipeline states prepared before
rendering, plays the intro and reaches the enhanced menu. Normal Alt+F4 shutdown
returns `ExitProcess(0)` and coordinator exit 0. Saved settings remain
byte-for-byte unchanged, with replay off. The launcher is left open and ready.
