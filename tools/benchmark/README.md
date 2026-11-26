# Arena graphics benchmark

The four-scene suite measures successful Vulkan present throughput during native arena
replay. It also reports process startup, scene loading, frame-time tails, and 1% low FPS.
The scene recipes and camera sequences are in [fixtures](fixtures/README.md). Run
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
python -B tools/benchmark/freeze.py --game-dir $game --seed 7 `
  --setup tools/benchmark/fixtures/c1mp1-4v4-reference.json --out local/benchmark/reference
python -B tools/benchmark/freeze.py --game-dir $game --seed 7 `
  --setup tools/benchmark/fixtures/c2mp2-4v4-reference.json --out local/benchmark/c2mp2
python -B tools/benchmark/freeze.py --game-dir $game --seed 7 `
  --setup tools/benchmark/fixtures/c3mp1-4v4-reference.json --out local/benchmark/c3mp1
python -B tools/benchmark/freeze.py --game-dir $game --seed 7 `
  --setup tools/benchmark/fixtures/c4mp2-8v8-stress.json --out local/benchmark/c4mp2
```

Compare the emitted digests with `fixtures/suite-benchmark.json`. Use the qualified
recordings for both arms. The c1mp1 entry pins the step 1 reference recording.
If a new generator or install changes a digest, qualify the new workload under a
new definition and use `--definition` in every invocation. Keep that materialized
definition and the logs under `local/benchmark/`, with log paths relative to the
definition. The original single-scene runner still defaults to `c1mp1-benchmark.json`.

## Condition and run the suites

Use one machine and a fixed desktop resolution, window mode, power configuration, and
set of installed packs. Keep the replay in focus and wait for each command to return
before starting the next. The runner reads the saved Play settings and packs under
`%LOCALAPPDATA%\MW3Remaster`. It puts each process in a fresh writable profile and sets
`MW3_DISK_CACHE=0`. A1 first runs a separate c1mp1 replay to condition the GPU. Its
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

The four-scene diagnostic smoke and both stress candidates ran on an AMD Radeon
RX 9070 with Windows driver `32.0.32029.2010` and Vulkan driver value
`8389024`. The 3440×1440 desktop was at 144 Hz. Borderless mode used the full
3440×1440 window, drawable and internal sizes. Each scene verified Vulkan WSI,
IMMEDIATE mode, the render worker on, v-sync off, and disk cache disabled.
The smoke used the saved Play packs with the planner's compatibility exclusions.
Every scene completed its 10 s warm-up and 30 s measured interval. Validation
checked the frame CSV and effective settings hashes and all four pressure
counters were zero in every scene.

| Scene | Measured presents | Mean frame time (ms) | FPS | Startup (s) | Scene load (s) |
| --- | ---: | ---: | ---: | ---: | ---: |
| c1mp1 | 1,948 | 15.396 | 64.93 | 144.13 | 26.77 |
| c2mp2 | 1,430 | 20.973 | 47.67 | 149.38 | 34.93 |
| c3mp1 | 2,170 | 13.821 | 72.33 | 148.20 | 34.63 |
| c4mp2 | 1,869 | 16.039 | 62.30 | 150.88 | 35.80 |

Both c4mp2 routes peaked at about 5,525 MiB of sampled process dedicated GPU
memory and completed without pressure events. The selected route started
measurement at log time 10.033 s. It had the higher recorded co-occurrence of
standing mechs and rounds plus beams, and averaged 0.99 replay explosions per
measured frame. The 11 s candidate averaged 0.83. The diagnostic smoke and
memory samples are under `local/benchmark/`.

A full serial A/A block used the same Windows build, GPU and window mode with
stock assets (`--active-packs ','` on all four suite commands). The separate
c1mp1 conditioning replay and all 16 scored scenes completed. The comparator
accepted the block and reported **no change**, with a −0.601% overall mean
frame-time change and a 3.250% noise bound. c4mp2 in arm A set that bound.
The comparison is saved at `local/benchmark/aa/comparison.json`.
