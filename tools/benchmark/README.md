# Arena graphics benchmark

The four-scene suite measures successful Vulkan present throughput during native arena
replay. It also reports process startup, scene loading, frame-time tails, and 1% low FPS.
The scene recipes, lighting, weather and camera sequences are in
[fixtures](fixtures/README.md). Run
these commands in PowerShell from the repository root.

## Build

Use Visual Studio 2026 with C++ x64 tools, a Windows SDK with DXC, Vulkan headers and
`glslangValidator`, and the SDL 3.4.18 and SDL_ttf 3.2.2 development packages. Set
these paths to the corresponding local inputs. The launcher runtime should be the
installed Play launcher's `NativePreview` directory.

```powershell
$game = 'D:/Projects/MW34Recomp/local/controls-investigation-2026-10-18-r3/game'
$launcher = 'C:/path/to/Core Critical Launcher/NativePreview'
$deps = 'C:/path/to/extracted/SDL-packages'
$headers = 'C:/path/to/Vulkan-Headers/include'
$glslang = 'C:/path/to/glslangValidator.exe'
$dxc = 'C:/Program Files (x86)/Windows Kits/10/bin/10.0.26100.0/x64/dxc.exe'
$cmake = 'C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'

& $cmake -S runtime/mw3-re -B local/benchmark/build -G 'Visual Studio 18 2026' -A x64 `
  "-DMW3_GAME_DIR=$game" -DMW3_CORE_CRITICAL_VULKAN=ON "-DMW3_VULKAN_HEADERS=$headers" `
  "-DGLSLANG=$glslang" "-DDXC=$dxc" "-DSDL3_DIR=$deps/SDL3-3.4.18/cmake" `
  "-DSDL3_ttf_DIR=$deps/SDL3_ttf-3.2.2/cmake"
& $cmake --build local/benchmark/build --config Release --target mw3
```

## Freeze the logs

Use fresh output directories. Each freezer invocation generates twice, in serial, with
separate writable profiles and log directories. It verifies byte identity and the emitted
timestamps, and writes the canonical log and a provenance receipt.

```powershell
foreach ($recipe in 'scene1-c1mp1-2v2', 'scene2-c2mp2-4v4', 'scene3-c3mp1-6v6', 'scene4-c4mp2-8v8') {
  python -B tools/benchmark/freeze.py --game-dir $game --seed 7 `
    --setup tools/benchmark/fixtures/$recipe.json --out local/benchmark/freeze/$recipe
}
```

Compare the emitted digests with `fixtures/suite-benchmark.json`. Use the qualified
recordings for both arms. Each recording takes about 15 to 45 s.
If a new generator or install changes a digest, qualify the new workload under a
new definition and use `--definition` in every invocation. Keep that materialized
definition and the logs under `local/benchmark/`, with log paths relative to the
definition. The original single-scene runner still defaults to `c1mp1-benchmark.json`.

## Condition and run the suites

Use one machine and a fixed desktop resolution, window mode, power configuration, and
set of installed packs. Keep the replay in focus and wait for each command to return
before starting the next. The runner reads the saved Play settings and packs under
`%LOCALAPPDATA%\MW3Remaster`. It puts each process in a fresh writable profile and sets
`MW3_DISK_CACHE=0`, so decoded assets load cold in every scene. It also sets
`MW3_DIGEST_CACHE_DIR` to `local/benchmark/digest-cache`, which only remembers the
SHA-256 of each environment pack file by its file identity, size and times. The first
scene of a new cache hashes about 29 GB of packs (about 100 s); every later scene and
arm reuses the digests (about 4 s). A rewritten pack file is hashed again.
The cache is shared on purpose so both arms of a block reuse it; use
`--digest-cache PATH` for another folder or `--digest-cache off` to hash in every scene. A1 first runs a separate c1mp1 replay to condition the GPU. Its
results are stored under `A1/conditioning` and excluded from the comparison.

```powershell
$common = @('-B', 'tools/benchmark/run.py', '--launcher-runtime', $launcher,
  '--game-dir', $game, '--resolution', '3440x1440', '--window-mode', 'borderless',
  '--suite')
$exeA = 'local/benchmark/build/Release/mw3.exe'
$exeB = $exeA  # Use the other build's executable for a build comparison.

python @common --run-label smoke --exe $exeA --out local/benchmark/smoke
python @common --run-label A1 --exe $exeA --out local/benchmark/A1
python @common --run-label B1 --exe $exeB --out local/benchmark/B1
python @common --run-label B2 --exe $exeB --out local/benchmark/B2
python @common --run-label A2 --exe $exeA --out local/benchmark/A2
```

Use a fresh output root for another run. For a setting comparison, change that setting
in both B commands only. For example, use `--flare-style original` in A and
`--flare-style modern` in B, then declare `--setting flare_style_modern` below.
The declared keys are the effective keys in `summary.json`. Repeat `--dependent KEY`
for settings that necessarily change with the primary setting. Each arm must use
one consistent primary value across all scenes, and the two values must differ.

## Compare

```powershell
python -B tools/benchmark/compare.py local/benchmark/A1 local/benchmark/B1 `
  local/benchmark/B2 local/benchmark/A2 --out local/benchmark/comparison.json
```

The four arguments can also be paths to their `suite.json` manifests. Run each suite
at its final location and keep the profiles and scene output at the absolute paths
recorded in the launch plans. The comparator checks the
recorded timestamps, native results, frame CSV hashes, effective settings, and ordered
pack identities before it scores the block. For an A/A or build-only comparison, omit
`--setting`. The command prints a readable report and writes a JSON report. It exits
with status 2 if the inputs fail validation. A valid noisy block reports
`inconclusive`. After checking run conditions, repeat it as a fresh block.

Each scene weights its two runs equally within each arm, even when the renderers
present different numbers of frames. The overall score weights the four scene ratios
equally with a geometric mean. Verdicts use mean frame time. Negative changes are
faster. A change must exceed 5% and the applicable spread. A within-arm spread greater
than 5% in any scene makes the full block inconclusive.

## Launcher Run benchmark button

The launcher's Settings & Steam page has a **Run Benchmark** button for players. It runs
`player.py` with the bundled planner Python (`Tools/PlannerPython`), the installed
`Planner` folder and the installed `NativePreview` runtime. The installer copies
`player.py`, `run.py`, `freeze.py` and the suite and recipe fixtures into a `Benchmark`
folder. The coordinator reads the saved Play settings and active packs the same way as
`run.py`, so the run uses what Play would launch.

The reference logs come from the player's original install and never ship. On the first
run, the coordinator generates each scene's log with `freeze.py`, which records twice
and requires byte-identical logs. It freezes the hash in that scene's `freeze.json`.
The logs are stored under `%LOCALAPPDATA%\Core Critical Benchmark\references\KEY`.
KEY is derived from the game executable, the install's `.zbd` archives and the recipes.
Later runs reuse a frozen log only when its bytes still match. A changed log stops the
run and names the folder to delete.

The digests in `suite-benchmark.json` belong to the build that qualified the suite.
Determinism is proven only for one build on one machine, so a different digest only
warns. Each report is compared only with the player's own newest earlier report that
has the same KEY and effective settings.

The coordinator prints progress lines that start with `BENCHMARK-EVENT ` followed by JSON.
Results go under `results/TIMESTAMP/`, with `report.json` beside the suite output. The
report lists average FPS, 1% low FPS, and p95 and p99 frame times for each scene. The
overall figures pool the measured frames from all four scenes, using the native formulas.
If a scene loses window focus, the native summary records the reason. The launcher then
reports that the run was stopped and not scored, and asks the player to keep the game
in front. The button requires a game executable that supports `--arena-record-every-update`
and `--benchmark-scene`. Release 1.0.58 lacks both options, so the button reports that
the game needs an update.

## Developer strict playback

Use `--strict` for single-scene repeatability or renderer parity checks. Each recorded
`state.t` in `[scene start, scene start + warm-up + measured)` gets one resident worker
present. The replay uses the recorded time and consecutive tick deltas, with the first
delta measured from the scene start. Startup and fade are outside this sequence. The
final tick must complete before the run can succeed.

```powershell
python tools/benchmark/run.py --launcher-runtime $launcher --exe $exeA --scene c1mp1 `
  --strict --strict-capture 12 --out local/benchmark/strict-a
python tools/benchmark/run.py --launcher-runtime $launcher --exe $exeA --scene c1mp1 `
  --strict --out local/benchmark/strict-b
python tools/benchmark/strict_compare.py local/benchmark/strict-a local/benchmark/strict-b
```

The native flags are `--benchmark-strict` and `--benchmark-strict-capture TICK`, used
with the existing benchmark flags. Tick indices start at zero. Omit the capture flag to
record hashes only. With a capture, `tick-N.png` contains the selected swapchain image.

`strict.json` records each completed tick's index, recorded time in seconds, and
FNV-1a 64-bit hash of the full swapchain image after the resident blit and before WSI
presentation. The hash covers tightly packed BGRA8 bytes in image row order, including
alpha and any letterbox pixels. RGBA swapchain formats are reordered to BGRA with no
color conversion. Strict playback requires transfer-source support and an 8-bit BGRA or
RGBA Vulkan swapchain. The desktop compositor and scanout are outside the capture.

A missing worker receipt, failed acquire or present, or swapchain change fails the run.
The result retains completed ticks and records the failure reason. `strict_compare.py`
accepts result directories or `strict.json` files and exits 0 for matching ticks, 1 for
the first difference, or 2 for invalid or incompatible input. Use the same scene,
settings, packs, resolution, GPU and driver for repeatability checks. Strict runs are
unscored, and `compare.py` rejects them from A-B-B-A.

### Limitations

Worker waits during pre-arm startup and fade frames can be unbounded. If the app
throws mid-frame, producer work may remain unflushed. Losing window focus
invalidates a strict run.

## Stress qualification

Use the freezer's `candidate_windows` to select a log start 10 s before each candidate's
measured start. For a route at the beginning of the recording, omit `start_seconds` to
begin at the first recorded state. Copy the c4mp2 scene into a separate local definition,
fix its relative log path, and replay it with `run.py --scene c4mp2 --definition PATH`.
Keep the camera, profile settings and playback duration fixed across candidates.

Use the native summary's `measured_effects` and `video_memory_pressure` fields to inspect
the activity and allocation failures. On Windows, sample
`Win32_PerfFormattedData_GPUPerformanceCounters_GPUProcessMemory.DedicatedUsage` for the
game PID during each diagnostic replay. Compare the samples across candidate routes.
Use fresh processes without a sampler for the scored A-B-B-A block.

## Windows validation

### Load time

Before this change each scene spent about 94 s of a 144 to 150 s start rehashing the
environment packs, because `MW3_DISK_CACHE=0` also turned off the remembered pack
digests. The 2026-11-26 four-scene smoke took 786 s for 2 min of measured play
(about 195 s per scene). With the digest cache, measured on 2026-11-27 on the same
RX 9070 machine, packs and settings:

| Phase per scene | Before | After |
| --- | ---: | ---: |
| Environment pack registration | 93.7 to 94.7 s | 3.6 to 4.1 s (103 s once, filling a new cache) |
| Window and renderer start | 12.0 to 14.9 s | 12.3 to 13.7 s |
| Mission load | 22.8 to 31.0 s | 30.8 to 36.1 s |
| Process start to measured scene | 144.1 to 150.9 s | 68.5 to 73.9 s |

The 2026-11-27 smoke of the new suite (`local/benchmark/smoke2`, digest cache already
filled) completed all four scenes, each valid with zero memory pressure counters, in
583 s against 786 s before, with twice the measured play. Each process start reached
its measured scene in 51 to 69 s; pack registration took 2.4 s in each.

| Scene | Start to scene (s) | Scene load (s) | Measured presents | Wall time (s) |
| --- | ---: | ---: | ---: | ---: |
| c1mp1 | 50.6 | 30.4 | 619 | 108.8 |
| c2mp2 | 63.3 | 43.3 | 587 | 161.7 |
| c3mp1 | 64.9 | 44.3 | 837 | 164.2 |
| c4mp2 | 69.3 | 46.5 | 293 | 148.1 |

The c4mp2 renderer reported 52 replay headlight lamps at its peak; the other scenes
report none, as intended. Captured frames confirmed dawn and rain in c1mp1, mid-day in
c2mp2 with the fight in clear view in seven frames from 5 s to 90 s, dawn in c3mp1,
and night, rain and lit headlights in c4mp2.

Measured play per suite went from 2 min to 4 min 20 s (40, 80, 80 and 60 s).

### Frame rate on 2026-11-27

The frame rates in this smoke are not comparable with 2026-11-26. On 2026-11-27 the
old c2mp2 scene and log, replayed by the merged step 3 executable, averaged 7.3 FPS
where it averaged 47.7 FPS the day before; this build gave 6.6 FPS on the same
replay. The machine itself had slowed: the desktop compositor held about 21.9 GB of
video memory earlier that day. Rerun the smoke and the scene 1 frame-time check after
a restart before scoring a block.
