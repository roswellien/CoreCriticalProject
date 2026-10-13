# Session summary: native host to live menu, Training, quit and intro video (2026-10-12/13)

This session followed the faithful modernization plan (local reference: `docs/faithful-modernization-plan.md`). The original MechWarrior 3 code runs through native recompilation, connected to modern platform services and Vulkan.

**What this does not change:**
- The accepted M4 count stays **131/144**. These are executed native runs, not acceptance.
- Strict acceptance v6 still fails on the pinned `docs/m4-startup-plan.md` hash. It awaits the user's decision: re-run those reviews, or change the criterion.
- Nothing was committed.

All work lives in `tools/m4-crt-heap-carry/`, the single integrated native x64 host. Detail is in that directory's `README.md`, especially the section "To the live menu and into Training". The execution map is in [e0-application-execution-path.md](e0-application-execution-path.md).

## Execution reached (all native, in one host process)

| Boundary | Evidence (local, git-ignored) |
| --- | --- |
| MSVCRT, MFC42 and MSVCP50 attach, all 144 game initializers, `WinMain` → `AfxWinMain` → `InitInstance` | earlier runs, `mfc-run-1..92` |
| Main window, virtual display, Direct3D 6 HAL device, DirectSound, DirectInput, MCI CD audio, intro sequence | `mfc-run-93..121` |
| **Live main menu**, animated, responding to input | `mfc-run-124`; `reports/m4-crt-attach/live-menu-r1` |
| Training pilot screen, then Accept, then the mission loader thread (a guest thread), then the briefing map | `mfc-run-126..132` |
| **Live Training 1 3D frames**: Direct3D scenes rendered by Vulkan, with the game's own HUD on top | `mfc-run-137`; `live-training-r1` |
| Training steps: start-up (S), turning (Right-Arrow), accelerate and walk out of the hangar | `mfc-run-159..161`; `live-training-r2`, `r3` |
| **Interactive play by the user**: Training loads, start-up and walking work | the user's report (see defects below) |
| **Full normal shutdown**: Quit → confirm → settings saved → CRT `exit` → `ExitProcess(0)` with `DLL_PROCESS_DETACH`; host exit code 0 | `mfc-run-186` |
| **Intro cinematic decoded** by the game's own Indeo IV50 codec, running as recompiled code | hidden runs at 06:01–06:05; `intro-video-r1` |

## Main components added or changed

### Graphics: Vulkan

- **Scene renderer (`vk_scene.hpp`).** Adapted from `tools/vulkan-probe/replay.cpp`; the graphics-lane files were not modified.
  - It renders the Direct3D 6 provider's recorded scenes.
  - Colour is R5G6B5 and depth D16, matching the game's 16-bit formats. Both round-trip through guest memory, so the game's 2D HUD and Flip work unchanged.
  - The fixed-function shaders (`d3d_scene.vert/.frag`, compiled to `d3d_scene_*.h`) cover texture-stage ops, flat or Gouraud shading, perspective-correct or affine UV, specular, vertex fog and alpha test.
  - Pipelines are cached per blend, depth and cull state. Any render state that isn't modelled stops typed instead of being ignored.
- **Direct3D 6 provider (`d3d_provider.inc`).**
  - Devices start from the D3D6 default render and texture-stage states, and legacy states are translated to stage 0.
  - Z-buffer clears are honoured.
  - Draws share state snapshots, and textures are versioned through every API write path.
- **Vulkan swapchain presenter.**
  - FIFO present mode, so Flip waits for the vertical blank as `DDFLIP_WAIT` did.
  - The swapchain lives on a host-owned child window that is disabled and hit-test transparent.
  - It uses whichever adapter can present to the window. On the dev machine that is the integrated GPU, while scenes render on the discrete RX 9070; the discrete GPU cannot present to that display.
  - The game's MFC thread hooks are suspended while host rendering or presentation runs.
  - GDI remains for 8-bit frames and for `MW34_PRESENT=gdi`.
- **Virtual `SetDisplayMode`.** Shows the cooperative window at the mode size, integer-scaled, as exclusive DirectDraw did. It is never activated during scripted runs, and `MW34_HIDE_WINDOW=1` keeps it hidden.

### Platform services (`mfc_stage.hpp`, `vdd.inc`, `win_bridge.inc`)

- **Guest threads (`CreateThread`).** Each runs to completion on a full context switch:
  - its own State, x87 state, host CW/MXCSR, stack, TEB exception list, TLS values and last error;
  - `DLL_THREAD_ATTACH`/`DETACH` for the loaded modules;
  - mutex ownership tracked per guest thread.

  Anything that schedule cannot honour stops typed.
- **Shutdown.**
  - `ExitProcess` runs the DLL detaches natively.
  - `FreeLibrary` of a dynamic module runs its native detach and unmaps it.
  - Also added: `UnregisterClassA`, `TlsFree` with guest-freed slots shadowed as Windows does, the CRT `HeapDestroy`, guest-level `SetUnhandledExceptionFilter`, and `CloseHandle` on pseudo-handles and search handles.
- **Registry overlay.** The host registry is read-only. The game's writes go to `MW3/mw34-registry.txt` and are read before the real registry; the host registry is never modified.
- **Input.**
  - Real DirectInput by default.
  - `MW34_INPUT_SCRIPT` stands in for the player for automated tests. It supports frame-numbered events and `+MS` events timed from the first 3D scene, delivered both as buffered records and in the immediate keyboard state. Under a script the cursor is virtual.
- **Other new services.** `CreateDirectoryA` (confined to the game folder), `DuplicateSoundBuffer`, `EvictManagedTextures`, `MsgWaitForMultipleObjects`, `GetStdHandle`, `GetFileType`, the locale functions (`GetStringType*`, `LCMapString*`, `GetLocaleInfo*`), environment blocks, and `GetSystemInfo` in its 32-bit view.
- **Teardown.** COM proxies are released children-first, and reference ownership is tracked per guest interface pointer. This fixed two exit crashes.

### Intro video: staged Indeo IV50 codec

- **`rebase_image.py`** rebases the install's `Ir50_32.dll` to 0x11000000, as the loader would once `Mech3Msg.dll` holds 0x10000000. The output is local only, under `local/mw3-staged/derived/`.
- **Lifted and driven natively.** The closure mode `ir50` (`mfc_closure.py`) found 2,583 functions, all lifted. The codec runs through its `DriverProc` with msvfw32's ICM protocol: `ICLocate`, `ICSendMessage`, `ICDecompress`, `ICClose`, and `DefDriverProc`.
- **Services added for the codec's own CRT:**
  - `HeapCreate` heaps,
  - `VirtualAlloc`/`VirtualFree` in a guest arena,
  - named page-file sections,
  - `LMEM_MOVEABLE` local memory,
  - its CRT startup services.
- **Off switch:** set `MW34_STAGED_CODEC=0`.

### Recompiler and lifting fixes

- **x87 `FPATAN` (gameplay-visible).** remill lowered it to `atan(st1/st0)`, losing the quadrant, so angles came out 180° off in half the plane. It is now exact: `x87_bridges.py` rewrites it to a bridge running the host `fpatan` on both operands, and 57 game functions were re-lifted (`lifts-r57`). This is the likely cause of the user-reported camera flip and leg animation; **not yet re-verified in play**.
- **x87 `FPREM`** now runs the host `fprem` until C2 clears. Remaining x87 handling:
  - FSCALE factors computed exactly;
  - INT3 padding becomes a typed trap;
  - remill's MMX/x87 aliasing values take the zero representative.
- **MMX `PADDUSB`/`PADDUSW`.** remill had these semantics only in their SSE forms, so I added the MMX forms. `local/tools/remill-mmx-build/` holds the repaired semantics plus the four encodings, selected by `MW34_SEMANTICS=mmx` with its own SHA-256 pin.
  - The rebuild procedure reproduces the pinned semantics byte for byte.
  - Nine sampled game functions re-lift to identical IR.
- **Closure and lifting.**
  - Jump tables: an unreachable slot 0 and negative indices.
  - MSVCRT data-pointer roots; repairs r2–r5.
  - Direct tail-JMP calls no longer bind a second return word.
  - Page-crossing guest accesses are split.
  - Additional exact LLVM integer intrinsics are admitted (`abs`, `bswap`, min/max, saturating ops, and vector forms).

### Performance

The 3D phase went from about 2.6 to about 13 fps, and a 700-frame Training run from 9 min 41 s to about 51 s. Measured with a new opt-in sampling profiler (`MW34_PROFILE`, `MW34_PROFILE_FROM`, with caller unwinding) and a linker PDB.
- `guest_memory_cached.cpp`: a native-host implementation of `GuestMemory` with a direct-mapped page→region cache. Its interface and faults are unchanged, and the pinned `runtime/memory/guest_memory.cpp` is untouched.
- Exact memory-contract fast paths, plus direct pointers through the cache.
- Bulk, page-chunked guest copies, including blits, fills and DIB synchronization.
- An exact game-import lookup table.
- A cheap FPU exception-clear path.
- A bounded service log.

### Tools and launcher

- `Play-MW3.cmd` (repository root) and `tools/m4-crt-heap-carry/play.ps1` run the built host interactively, or with `-Script`, `-Frames` and `-Dump`.
- The executable size bound for worker identity was raised to 256 MB, since the codec objects push the executable to about 153 MB.

## How to build and run (local install required)

```powershell
powershell -File tools/m4-crt-heap-carry/build.ps1 -Levels O2   # needs the local lift reports and staged images
Play-MW3.cmd                                                    # interactive; log: reports/m4-crt-attach/play-*.err
```

**Lift run loop:**
1. `mfc_closure.py`
2. `lift_closure.py` → `lifts-rN`
3. Append "dir sha" to the dispatch-args list.
4. `gen_mfc_dispatch.py`
5. Build.

Lift reports used this session: r51–r62, plus the earlier ones. All lift reports live under `reports/m4-crt-attach/` and are git-ignored.

## Fidelity limitations and known defects

- **Camera and legs.** The user observed the camera reversing direction when leaving the starting bunker, and the 'Mech legs kicking far behind it. These are attributed to the FPATAN quadrant bug, now fixed but **awaiting the user's re-test**.
- **Frame rate.** About 13 fps in heavy Training scenes; menus and light scenes are faster. Simulation remains wall-clock-faithful.
- **Not yet exercised natively:**
  - the remaining Training steps (follow the instructor, crouch, reverse, waypoints),
  - weapons and targeting (the probe was inconclusive),
  - AI and collision under controlled original/native comparison.
- **Platform-level deviations:**
  - Guest threads run to completion and are not preempted.
  - Concurrent file-mapping views share one address.
  - 16-bit dithering is not reproduced.
  - Cull winding is unverified.
  - FYL2X and F2XM1 carry one extra rounding.
- **Files written into the game folder:** the game writes `MW3/mech3.out`, `mech3.err` and its configs, and the overlay writes `MW3/mw34-registry.txt`.

## Next concrete blockers

1. The user re-tests the camera and legs after the FPATAN fix. Then audit remill's remaining x87 semantics for similar discrepancies.
2. Run the remaining Training steps and weapons in play, and fix the stops they surface.
3. Set up original/native comparisons for physics, AI, weapons and timing, following plan E4.
4. Frame rate: per-access contract overhead and the cost of lifted x87 code.
5. Acceptance lane: the user's v6 decision, then the authorized chain.

## Commit guidance for the agent updating GitHub

Follow `CONTRIBUTING.md` and `docs/legal.md`, and inspect `git diff --cached` before committing.

**Safe to commit** (project-authored):
- `tools/m4-crt-heap-carry/`:
  - `*.hpp`, `*.inc`, `*.cpp`, `*.py`, `*.ps1`, `README.md`, `native/CMakeLists.txt`,
  - `d3d_scene.vert`, `d3d_scene.frag` and the generated `d3d_scene_*.h` (SPIR-V of project shaders),
  - `guest_memory_cached.cpp`, `vk_scene.hpp`, `rebase_image.py`.
- `Play-MW3.cmd`.
- Docs: this file and `docs/e0-application-execution-path.md`.

**Do not commit:**
- **Generated dispatch tables:** `tools/m4-crt-heap-carry/mfc_entries.inc`, `mfc_routers.inc` and `mfc_objects.txt`. They come from local lift reports and are meaningless without them. Treat them as generated translation artefacts.
- **Ignored local directories:** `reports/` (frames, lift reports, logs), `local/` (staged DLLs, the rebased codec, `remill-mmx-build`), `MW3/` (including `mw34-registry.txt`), and `build/`.
- **Any `.dll`/`.exe`/media.** The `.gitignore` blocks most of these, but check anyway.

**Also preserve the other pre-existing uncommitted changes in the worktree** (docs and graphics-trace tools from other writers). Commit only what is intended.
