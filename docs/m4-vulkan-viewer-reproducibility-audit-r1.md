# M4 Vulkan viewer reproducibility audit r1

Historical audit note, 2026-10-11 continuation: this document and the viewer
foundation are now tracked in commit `5d86c74`. Its clean-checkout/untracked
findings below refer to the then-current `d20e936` snapshot. No fresh viewer
build is claimed by this note. See the [current work review](m4-claude-work-review-2026-10-11.md)
and [live integration strategy](faithful-modernization-plan.md).

Recorded 2026-10-11. This audit asks whether another developer could build, launch and
check the windowed Vulkan replay viewer in `tools/vulkan-windowed/`. Nothing was installed.
No source, CMake, script, capture or configuration file was changed. No receipt, ledger or
acceptance file under `reports/` was written. It adds no initializer, startup or rendering
credit. It does not repeat the DirectDraw/COM analysis or the
[presenter extraction review](m4-vulkan-presenter-extraction-review-r1.md).

**Scope of the viewer.** The viewer is a standalone x64 Win32 Vulkan program. It loads one
saved scene package, which is either a captured MW3 Training scene interval or an authored
test scene. It redraws that fixed scene into a resizable window. It does not start, launch or
render the game. It runs no game logic, input or timing, and it is not a live renderer.

Labels used below:

- **Verified:** I ran this or checked it directly on this machine on 2026-10-11. Outputs went
  only to the session scratch directory outside the repository.
- **Documented:** it is stated in an existing README, document or script, but I did not run it
  in this audit.
- **Inferred:** I worked it out from reading code, with no run and no explicit documentation.

## Summary

| Question | Answer |
| --- | --- |
| Builds from the current working tree? | **Verified.** It builds with CMake 4.3.1-msvc1 (bundled with VS 18), MSVC 19.51 at `/W4 /WX` and glslang 15.3.0. The SPIR-V output is byte-identical to both existing local builds. |
| Authored self-test (no game data needed)? | **Verified.** `verify_ordered.py` passed with 719 presentations, 4 swapchain generations, 4 pixel-exact witnesses and 0 validation messages. |
| Captured-scene replay? | **Verified, run manually rather than through `run.ps1`.** The package is byte-identical to the 2026-10-10 accepted package. The raster equals the accepted offscreen reference. All 4 presented witnesses match the CPU oracle exactly, with 0 validation messages. |
| Builds from a clean checkout of `HEAD` (`d20e936`)? | **No (verified from git).** The viewer directory, its SCN4 command include, the launcher and the viewer document are untracked. The SCN4-capable `replay_scene.hpp` is uncommitted. |
| Reproducible on another machine? | **Only with material handed over outside git.** The local Vulkan tools, the ignored captures and the admitted `MW3/Mech3.exe` are all required. See [Gaps](#gaps-that-block-reproduction). |
| Historical receipts re-verifiable today? | **No.** Every accepted run pinned `run.ps1`, `package_replay.py` and `verify_capture.py`, and all three have changed since then. `verify.py` would reject those receipts. |

## Required tools, SDKs, drivers and assets

| Requirement | Exact value seen here | Where it is required | Status |
| --- | --- | --- | --- |
| OS | Windows 11 x64 (10.0.26200) | `CMakeLists.txt` fails with `FATAL_ERROR` when not `WIN32` | Verified |
| C++ toolchain | Visual Studio 18 2026 Community, MSVC 14.51 (`cl` 19.51.36256), Windows SDK 10.0.26100.0 | C++20, `/W4 /WX /EHsc`, links `user32` | Verified (scratch build) |
| CMake | ≥ 3.24. The bundled copy is `C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe` (4.3.1-msvc1) | README assumes "CMake on PATH" | Verified. CMake is **not** on PATH in a normal shell here (see F1). |
| Vulkan headers | Khronos `Vulkan-Headers` tag `v1.4.321`, commit `2cd90f9d20df57eac214c148f3aed885372ddcfe`, at ignored `local/tools/vulkan-headers-v1.4.321` | `-DVULKAN_HEADERS` (`find_path ... REQUIRED`) | Verified (commit and `VK_HEADER_VERSION 321`). Provenance is documented in `tools/vulkan-probe/README.md`. |
| glslangValidator | 15.3.0 from LunarG SDK 1.4.321.0, at ignored `local/tools/vulkan-sdk-portable/Bin/glslangValidator.exe` | `-DGLSLANG_VALIDATOR`. Compiles `tools/vulkan-probe/replay.{vert,frag}` in smooth and flat variants into 4 `.spv` files | Verified |
| Khronos validation layer | `VkLayer_khronos_validation.dll` + `.json` (API 1.4.321) in the same `Bin`. DLL SHA-256 `e67f0dd9…0f12c8` | **Mandatory at run time.** The viewer requests `VK_LAYER_KHRONOS_validation` plus synchronization validation, and instance creation fails without it (`viewer.cpp:160`). | Verified. The hash matches `docs/vulkan-raster-prototype.md`. |
| SDK installer (provenance only) | `local/tools/vulkansdk-1.4.321.0.exe`, SHA-256 `14ebc56e…0042a9` | The portable `Bin` was extracted from its embedded 7z because a normal install needed admin rights and rolled back | Verified (hash). The extraction procedure is documented, not scripted (see G3). |
| Vulkan loader | `C:\Windows\System32\vulkan-1.dll`, loaded at run time with `LOAD_LIBRARY_SEARCH_SYSTEM32` | No import library is needed | Verified (present) |
| GPU and driver | AMD Radeon RX 9070. Needs a graphics+present queue, Win32 surface, `VK_KHR_surface_maintenance1` or `VK_EXT_surface_maintenance1` (instance), `VK_KHR_swapchain` + `VK_KHR/EXT_swapchain_maintenance1` with the `swapchainMaintenance1` feature (device), RGBA8 color attachment + blend, D32_SFLOAT depth, an RGBA/BGRA8 UNORM surface format with transfer-dst/src usage, blit support and host-coherent readback memory | `viewer.cpp:120–260`, `presenter.hpp` | Verified on this GPU only. Other vendors are untested (see G6). |
| Python | `C:/Python314/python.exe` (3.14.7). Standard library only on the viewer path. Pillow is imported only by `describe_capture.py main()`, which this path does not call. | `run.ps1:19` hard-codes the path | Verified |
| Windows PowerShell | 5.1 (`powershell.exe`). The launcher names it explicitly. | `Launch Vulkan Replay.cmd` | Documented. The accepted receipts record `5.1.26100.9444`. |
| Captured scene (captured-scene path only) | Ignored `reports/graphics-trace/20261009-055506-103` (44 MB: 589 draws, 643 payloads, `preview/vulkan-0.5.ppm`, `sources/`, `binaries/`). Alternate: `…/20261009-061307-498` (9.4 MB, 140 draws). | `run.ps1 -CaptureRun` | Verified (present, and both snapshot all trace sources and binaries) |
| Admitted game executable (captured-scene path only) | `MW3/Mech3.exe` with SHA-256 `95bc2c11…d916bf` (MW3 U.S. 1.2) | `verify_filtering.py` → `graphics-trace/verify.py:27` re-hashes it. **The file is only hashed and never executed.** | Verified by reading the code. The viewer README does not mention it (see G2). |
| Environment variables | `VK_LAYER_PATH` → the portable `Bin`. `VK_IMPLICIT_LAYER_PATH` → an empty directory, which shields the run from implicit overlay layers. | Set and restored by `run.ps1:61–62,103–104`. `verify_ordered.py:36` uses `local/tools/empty-implicit-layers`. | Verified. Nothing has to be set globally, and no `VULKAN_SDK` is needed. |

## Clean-checkout state

**Verified from `git ls-files` / `git status`.** The table shows what the viewer needs and
whether each item is committed in `HEAD`:

| Path | In `HEAD`? |
| --- | --- |
| `tools/vulkan-windowed/` (`CMakeLists.txt`, `viewer.cpp`, `presenter.hpp`, `run.ps1`, `verify.py`, `verify_ordered.py`, `README.md`) | **Untracked** |
| `Launch Vulkan Replay.cmd` | **Untracked** |
| `docs/vulkan-windowed-replay.md` | **Untracked** |
| `tools/vulkan-probe/ordered_commands.inc` (included by `viewer.cpp:772`) | **Untracked** |
| `tools/vulkan-probe/verify_ordered_commands.py` (oracle for `verify_ordered.py`) | **Untracked** |
| `tools/vulkan-probe/replay_scene.hpp` (SCN4 reader) | Tracked, **modified, uncommitted** |
| `tools/vulkan-probe/replay.vert`, `replay.frag` | Tracked, unchanged |
| `tools/graphics-trace/package_replay.py`, `verify_capture.py` | Tracked, **modified, uncommitted** |
| `tools/graphics-trace/verify_filtering.py`, `verify.py` | Tracked |
| `local/`, `build/`, `reports/`, `MW3/` | Ignored by `.gitignore`, so never in a checkout |

A clean checkout therefore has no viewer to build. The first reproduction step for anyone else
is for the owner to commit or otherwise hand over the files above (see G1). Every command below
assumes the current working tree.

The CI workflow (`.github/workflows/build.yml`) does not build or test any Vulkan tool.

## Configure and build

The documented commands come from `tools/vulkan-windowed/README.md`. Run them from the
repository root in PowerShell:

```powershell
cmake -S tools/vulkan-windowed -B build/vulkan-windowed -A x64 -DVULKAN_HEADERS="$PWD/local/tools/vulkan-headers-v1.4.321/include" -DGLSLANG_VALIDATOR="$PWD/local/tools/vulkan-sdk-portable/Bin/glslangValidator.exe"
cmake --build build/vulkan-windowed --config Release
```

**Verified.** These exact arguments succeeded with only `-B` changed to a scratch directory and
`cmake` invoked by full path:

```powershell
$cmake = "C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe"
& $cmake -S tools/vulkan-windowed -B <scratch>/vw-build -A x64 -DVULKAN_HEADERS="$PWD/local/tools/vulkan-headers-v1.4.321/include" -DGLSLANG_VALIDATOR="$PWD/local/tools/vulkan-sdk-portable/Bin/glslangValidator.exe"
& $cmake --build <scratch>/vw-build --config Release
```

Expected output: CMake reports `Building for: Visual Studio 18 2026`, then generates the four
`replay*.spv` files, then `mw34_vulkan_windowed.vcxproj -> …\Release\mw34_vulkan_windowed.exe`.
Both exit codes are 0. The MSB8029 warning seen here appeared only because the scratch
directory is under `%TEMP%`, and it does not occur under `build/`. The four SPIR-V hashes match
`build/vulkan-windowed/` and `build/vulkan-windowed-commands/` exactly.

Build layout notes:

- **Verified.** `run.ps1` expects a multi-config layout, `<BuildDirectory>/Release/mw34_vulkan_windowed.exe`,
  with the `.spv` files in `<BuildDirectory>` itself. A Ninja or single-config build would put
  the executable somewhere else and fail the launcher's existence check.
- **Verified.** The default `build/vulkan-windowed/Release/mw34_vulkan_windowed.exe` (2026-10-09 20:47)
  is older than the current `viewer.cpp` (2026-10-10 05:38) and lacks SCN4 ordered-command
  support. `docs/vulkan-windowed-replay.md` already states this. It still replays SCN3 capture
  packages. `build/vulkan-windowed-commands/` holds the current-source build used for the
  2026-10-10 runs.
- **Verified.** The default build's cache has an empty `CMAKE_GENERATOR_PLATFORM`, so it was
  configured without `-A x64` and the VS default (x64) applied. `-commands` was configured with
  `-A x64`. Both produce x64.

## Launch

The documented launch is to double-click `Launch Vulkan Replay.cmd`. It runs
`powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File tools\vulkan-windowed\run.ps1`
using the default capture and `build/vulkan-windowed`. The window stays open until Escape or
close.

Scripted equivalents (**Documented**, and not run in this audit because `run.ps1` always writes
a new run under `reports/vulkan-windowed/`):

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/vulkan-windowed/run.ps1 -AutoCloseSeconds 6 -SelfTest
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/vulkan-windowed/run.ps1 -AutoCloseSeconds 2
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/vulkan-windowed/run.ps1 -AutoCloseSeconds 6 -SelfTest -BuildDirectory build/vulkan-windowed-commands
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/vulkan-windowed/run.ps1 -CaptureRun reports/graphics-trace/20261009-061307-498 -AutoCloseSeconds 2
```

`run.ps1` performs these steps (**Verified by reading**; I ran steps 1, 2 and 4 by hand):

1. `verify_filtering.py <capture>` checks the trace and capture identity, including the
   `MW3/Mech3.exe` hash, and the legacy filtering evidence.
2. `package_replay.py <capture>/frame <out>/scene.replay --filter-source legacy` writes an
   `MW34SCN3` package and `scene.json`.
3. It SHA-256-pins about 668 inputs: the executable, `.spv` files, viewer and oracle sources,
   validation DLL, capture manifest and every capture `*.bin`. The pins go to `launch.json`.
4. It sets `VK_LAYER_PATH` and an empty `VK_IMPLICIT_LAYER_PATH`, then runs
   `mw34_vulkan_windowed.exe <scene.replay> <shader-dir> <out>/replay.ppm <seconds> [self-test]`.
5. It parses `WINDOWED_RESULT:`, re-hashes every pin, writes `report.json`, then runs
   `verify.py <run>`, which writes `presentation-verification.json`.

The viewer's command line is
`mw34_vulkan_windowed.exe scene.replay shader-directory output.ppm [auto-close-seconds 0..600] [self-test]`.
`0` means "stay open until closed". `self-test` requires at least 4 seconds, starts at
640 × 480 instead of 960 × 720, and scripts resize → minimize → restore → Escape.

## Tests and replay checks

### A. Authored ordered-command self-test (needs no capture and no game)

```powershell
C:/Python314/python.exe -B tools/vulkan-windowed/verify_ordered.py build/vulkan-windowed-commands <fresh-output-dir>
```

**Verified** against the scratch build. The output directory must not already exist
(`mkdir(exist_ok=False)`). The script needs `local/tools/empty-implicit-layers` to exist and be
empty. It opens a window for about 6 seconds and has a 30-second timeout. A successful run
prints:

```json
{ "passed": true, "witnesses": 4,
  "result": { "presented_frames": 719, "swapchain_generations": 4, "present_fence_waits": 719,
              "render_passes": 720, "draws_per_pass": 2, "scene_width": 8, "scene_height": 8,
              "self_test": true, "window_destroyed": true, "minimize_observed": true,
              "restore_observed": true, "escape_observed": true, "validation_messages": 0,
              "resources_released": true, "live_gameplay": false } }
```

The output directory then holds `verification.json`, `run.txt`, `replay.ppm` (8 × 8, which
must equal the CPU oracle) and at least 4 `replay.ppm.presented-*.ppm` witnesses. The presented
frame count depends on timing (719 here, 740 in the 2026-10-10 receipt). Only the invariants
are checked: `render_passes = presented_frames + 1` and `present_fence_waits = presented_frames`.

### B. Captured-scene replay (needs the captures and `MW3/Mech3.exe`)

The full check is the `run.ps1 -SelfTest` command above followed by its automatic `verify.py`
step (**Documented**). A successful run prints `Windowed Vulkan replay: reports/vulkan-windowed/<run-id>`,
then:

```
Presentation extension: VK_KHR_swapchain_maintenance1
Device: <GPU name>
WINDOW_VISIBLE: true
SWAPCHAIN: {"generation":1,...}  (×4 in self-test)
WINDOWED_RESULT: {...,"draws_per_pass":589,"scene_width":640,"scene_height":480,...,"validation_messages":0,...,"live_gameplay":false}
PASS: windowed replay draws=589; offset=0.5; sampling=captured; scale=1; depth=d32; color=rgba8; zero validation warnings/errors including teardown; equivalence unproven
```

That output is followed by `verify.py`'s JSON `{"passed": true, "presented_frames": N, "witnesses": 4, "output": ".../presentation-verification.json"}`.
The run directory should contain `report.json` with `"passed": true`, no `failure.txt`, and a
`presentation-verification.json` that records `offscreen_reference_exact: true`, every witness
with `mismatched_pixels: 0` and both negative controls rejected.

**Verified equivalent, without `run.ps1`.** I ran steps 1, 2 and 4 by hand with every output
in the scratch directory. Both verifiers exited 0. The viewer printed the lines above with 743
presentations, 4 generations and 0 validation messages. Using `verify.py`'s own `ppm` and
`check_pixels` functions read-only, I confirmed three things:

- `replay.ppm` equals the capture's `preview/vulkan-0.5.ppm`.
- All four witnesses match the aspect-fit oracle, including the 853 × 480 letterbox at
  `[106, 0, 640, 480]`.
- The `scene.replay` package is byte-identical to the one in the accepted run
  `reports/vulkan-windowed/20261010-054054-018-4da93ce7`.

I did not run `verify.py` on a new run, so the input-pinning and receipt steps were not
exercised.

### C. Re-verifying an existing receipt

```powershell
C:/Python314/python.exe -B tools/vulkan-windowed/verify.py reports/vulkan-windowed/<run-id>
```

**Inferred, and expected to fail today.** I hashed the recorded inputs read-only and did not
run the command. Every accepted run has changed inputs. The 2026-10-09 runs have 5 changed
files: `viewer.cpp`, `replay_scene.hpp`, `run.ps1`, `package_replay.py` and `verify_capture.py`.
The 2026-10-10 run has 3: `run.ps1`, `package_replay.py` and `verify_capture.py`. `verify.py`
would raise `Executed input changed`. This is intended tamper detection. It also means the
historical receipts show the past result and cannot be re-confirmed against the current tree
(see G4). If an existing `presentation-verification.json` differs, `verify.py` refuses to
overwrite it.

## Common failures and diagnosis

The launcher runs hidden. **Every launcher failure is silent on screen**, so open the newest
`reports/vulkan-windowed/<run-id>/failure.txt` first, then `run.txt`.

| Symptom | Cause | Evidence | Fix or diagnosis |
| --- | --- | --- | --- |
| F1. `cmake` not recognized | CMake is only bundled with VS, not on PATH | Verified here | Use a VS Developer PowerShell or call the bundled `cmake.exe` by full path |
| `Could NOT find VULKAN_HEADERS` / `GLSLANG_VALIDATOR` at configure | `local/tools/...` missing, or the `-D` paths are wrong | Inferred (`find_* REQUIRED`) | Recreate the local tools (G3) and pass absolute paths with `$PWD` |
| Build stops on a warning | `/W4 /WX` | Documented | Use the same MSVC (14.51). Newer compilers may add warnings. |
| `Resolve-Path … build/vulkan-windowed` before any run directory is created | Build directory missing. `run.ps1:20` resolves it before the friendlier check at line 34. | Inferred | Build first, or pass `-BuildDirectory` |
| `Build the Vulkan windowed viewer first` | Executable not at `<BuildDirectory>/Release/` | `run.ps1:34` | Use a multi-config VS generator and `--config Release` |
| `Cannot find path …/frame/manifest.json` | Pin list out of step with the capture layout | Historical runs `20261009-204411`, `-204433` | Fixed in the current `run.ps1`. Seeing it again means mismatched script and capture versions. |
| `Captured filtering evidence rejected.` | `verify_filtering.py` failed. Likely causes: `MW3/Mech3.exe` missing or not the admitted hash ("Game identity mismatch"), or a changed capture | Inferred from `graphics-trace/verify.py:27–40` | Run `C:/Python314/python.exe -B tools/graphics-trace/verify_filtering.py <capture>` directly to see the exception |
| `Captured scene profile rejected.` | `package_replay.py` / `verify_capture.py` rejected the payloads | `run.ps1:42` | Run `package_replay.py` directly with `--filter-source legacy` |
| `Vulkan loader unavailable` | No `vulkan-1.dll` in System32 | `viewer.cpp:88` | Install or repair the GPU driver (outside this audit) |
| `create instance (validation required): -6`/`-7`, or a loader `VALIDATION:` line about missing extensions | Validation layer not found (`VK_LAYER_PATH` unset when the executable runs directly), or the ICD lacks the requested surface-maintenance extension | Historical run `20261009-204641`: `VK_EXT_surface_maintenance1 not supported` | Run through `run.ps1`/`verify_ordered.py`, or set both environment variables by hand. Current code chooses KHR or EXT automatically. |
| `No graphics/present queue with swapchain maintenance1` | Driver lacks `swapchainMaintenance1` | `viewer.cpp:236` | Update the driver or use another GPU. There is no fallback path. |
| `Validation warnings/errors: N`, nonzero exit | Any validation or synchronization message, including at teardown | Historical run `20261009-204717` (acquire/layout hazard, since fixed) | Read the `VALIDATION:` lines in `run.txt`. Implicit overlay layers are excluded by the empty implicit path. |
| `Get-FileHash … not recognized` | Old launcher in a restricted child host | Historical run `20261009-205133` | Fixed. The current script hashes with .NET. |
| `A windowed replay input changed during execution: …` | A pinned file was edited while the viewer was open | Historical run `20261009-211015` (4.4 M presentations, then `replay_scene.hpp` changed) | Do not edit viewer, probe or graphics-trace sources while an interactive launch is open |
| Linker error `cannot open … mw34_vulkan_windowed.exe` | Viewer still running, so the executable is locked | Documented (reason for `build/vulkan-windowed-commands`) | Close the viewer, or build into another directory and pass `-BuildDirectory` |
| `Existing verification receipt differs` | `verify.py` re-run over a receipt it would now compute differently | `verify.py:161` | Preserve the receipt and make a fresh run |
| `verify_ordered.py`: `FileExistsError` | The output directory already exists | Inferred | Use a new output directory |

## Gaps that block reproduction

| ID | Gap | Effect on another developer | Suggested remedy (not applied) |
| --- | --- | --- | --- |
| G1 | The viewer, launcher, viewer document, `ordered_commands.inc`, `verify_ordered_commands.py`, and the current versions of `replay_scene.hpp`, `package_replay.py` and `verify_capture.py` are not committed | A clean checkout cannot build the viewer at all | Commit them as one unit, or publish a source bundle with hashes |
| G2 | The captured-scene path needs the proprietary `MW3/Mech3.exe` (hash-checked, never run) and ignored captures that cannot be regenerated deterministically (live Training timing, dgVoodoo configuration, trace DLL build). The viewer README lists "local captures" but not the game executable. | Captured-scene replay cannot be reproduced without a user-owned MW3 1.2 install plus the exact capture directories, handed over privately | State the `Mech3.exe` requirement in the viewer README. Give the capture IDs and SHA-256 of `frame/capture.jsonl` as the handover key. Treat path A as the portable smoke test. |
| G3 | The local Vulkan toolchain has no script: header clone, SDK download, 7z extraction to `vulkan-sdk-portable`, and creating `local/tools/empty-implicit-layers` | Manual setup, and wrong versions are possible | Add a bootstrap script that checks the documented commit and installer, validation-DLL and glslang hashes |
| G4 | Historical receipts pin files that have changed since, so `verify.py` cannot re-confirm any accepted run against the current tree | Past acceptance cannot be checked independently today | Make a fresh run after G1 lands, or verify against a tagged revision |
| G5 | `C:/Python314/python.exe` is hard-coded, and so is the VS multi-config `Release/` layout | Fails on machines with another Python location or generator | Add a `-Python` parameter or `py -3`, and document the generator requirement |
| G6 | Only one GPU and driver tested (AMD RX 9070, KHR maintenance1). The EXT path is untested, and no driver version is recorded in receipts. | Unknown portability to NVIDIA, Intel or older drivers | Record the driver version and `apiVersion` in `run.txt`, and test a second vendor |
| G7 | The default launcher executable is stale compared with the current `viewer.cpp` (no SCN4 support) | The double-click launcher does not run the current source | Rebuild `build/vulkan-windowed` when no viewer is open |
| G8 | The README says "CMake on PATH" and the hidden launcher shows no errors | Confusing first-run failures | Point to the VS Developer PowerShell, and mention `failure.txt` in the README |
| G9 | Not in CI | Regressions surface only on the owner's machine | Add at least a configure-and-build job on a Windows runner with the pinned headers and glslang. A GPU run would need a self-hosted runner. |

## What this audit ran

Everything was read-only for the repository. Outputs went to the session scratch directory,
outside the repository:

1. Read `tools/vulkan-windowed/*`, `Launch Vulkan Replay.cmd`, the related `tools/vulkan-probe`
   and `tools/graphics-trace` scripts, `docs/vulkan-windowed-replay.md`,
   `docs/vulkan-raster-prototype.md`, `.gitignore`, the CI workflow, and both existing
   `CMakeCache.txt` files.
2. Checked tool versions and hashes: CMake, glslang, validation-layer manifest and DLL, SDK
   installer, header commit, Python.
3. Configured and built the viewer into scratch (exit 0) and compared SPIR-V hashes.
4. `verify_ordered.py <scratch-build> <scratch-out>`: passed.
5. `verify_filtering.py` and `package_replay.py` on capture `20261009-055506-103` into scratch:
   both exit 0. Viewer `self-test` for 6 seconds on that package: exit 0, 0 validation messages.
   Oracle comparison done read-only with `verify.py` helpers.
6. Read-only SHA-256 comparison of the recorded input pins for five accepted runs against the
   current files.

Not done: `run.ps1`, the double-click launcher, and `verify.py` on a new run, because all three
write under `reports/`. Also not done: any game launch, capture, install, or source or
configuration edit.
