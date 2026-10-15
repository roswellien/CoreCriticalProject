# Session summary: native host to live menu, Training, quit and intro video (2026-10-12/13)

Latest status: [October 14 native Remaster progress](session-summary-2026-10-14-remaster.md). The results below retain the earlier execution history.

This session followed the [faithful modernization plan](faithful-modernization-plan.md). The original MechWarrior 3 code runs through native recompilation, connected to modern platform services and Vulkan.

**What this does not change:**
- The accepted M4 count stays **131/144**. These are executed native runs, not acceptance.
- Strict acceptance v6 is paused by the user's decision (2026-10-13); the accepted count stays 131/144. Analysis of the v6 failure (`strict-acceptance-v6-r1`, read-only from its completed union database):
  - Of the 2,045 mutable rows in the v6 physical union (sources, docs, build, toolchain, Python; the 11.9 million report/capture rows are immutable and were not rehashed), exactly 7 are stale: the in-place-updated x86 MSVC binaries (Visual Studio updated `cl.exe`, `link.exe`, `ml.exe` and `1033/clui.dll` under MSVC 14.51.36231 to 19.51.36260 at 05:55 on 2026-10-13), `README.md`, `docs/m4-startup-plan.md` and `runtime/CMakeLists.txt`.
  - Nine of the 39 v6 gates pin the old compiler, including the accepted-131 parent and the original-game observer build/prelaunch/execution/validation.
  - Following receipt pins transitively, re-issuing everything that depends on the stale files reaches about 1,000 receipts in about 800 receipt directories, essentially the whole M4 evidence history; the three doc/CMake files alone reach 987. The strict union pins mutable working-tree files, so any doc edit or toolchain update invalidates it.
  - Options recorded for a later decision: restore the pinned files (Visual Studio rollback plus pinned doc/CMake content) and re-run v6 unchanged; amend the criterion (documentation not a physical dependency; toolchain identity updates admitted by byte-identical rebuild); or a full re-run of all affected receipts.
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
| Training 1 steps, deterministic (MW34_VIRTUAL_CLOCK=50): start-up (S), turn to instructor, accelerate (Up-Arrow), maximum speed (THROTTLE0) completed; the mech leaves the bunker, Move Mech next to instructor is completed (input-script-step6.txt), and Following a Mech: follow instructor to the beach becomes active. A variant that walks away fails with the on-screen Fail Actions: Left Mission Boundaries, the mission rule behind the earlier failure | 	raining-steps-r1 (script and frames) |
| **Interactive play by the user**: Training loads, start-up and walking work | the user's report (see defects below) |
| **Full normal shutdown**: Quit → confirm → settings saved → CRT `exit` → `ExitProcess(0)` with `DLL_PROCESS_DETACH`; host exit code 0 | `mfc-run-186` |
| **Intro cinematic decoded** by the game's own Indeo IV50 codec, running as recompiled code | hidden runs at 06:01–06:05; `intro-video-r1` |
| **Instant Action** (Big Lake, Battle vs. Blackhawk): menu → pilot → setup → briefing → live mission. In scripted runs, targeting (E) locked the enemy, Enter cycled the selected weapon and the enemy AI closed from 586 m to 379 m. The point-list primitives drawn after targeting are now rendered. | scripted runs 07:10–07:14 (`play-20261013-071335`) |
| **Weapons fire in Instant Action** (original default bindings, from the game's command table at 0x411150: Space or mouse button 1 = `CMD_TRIGGER1`, Enter = `CMD_NEXT_WEAPON`, backslash = `CMD_FIREMODE`, keypad Enter = `CMD_ALPHASTRIKE`): an ER laser beam is drawn from the arm to the aim point, and the building hit catches fire and collapses. An alpha strike from the 16-ER-laser loadout overheated and destroyed the player's mech within about a second (explosion, debris, MISSION FAILURE); the simulation kept running. | `play-20261013-074249` (beam: frame 915); `play-20261013-073542`; `instant-action-r1` |
| **Complete Instant Action fight played by the user** (12:10-12:12, visible Vulkan window): the user reports it ran well to the end, apart from frame-rate dips. When the game saved its results, the registry-overlay file swap (`MoveFileExA`) failed, a transient sharing/access error, and the host stopped visibly; the pending content matched the saved file, so nothing was lost. The process then lingered in teardown. Fixed: the swap retries transient sharing/lock/access errors for about 2 s and reports the Windows error code, and a fatal stop now ends the process within 15 s (exit code 3) if teardown blocks. | `play-20261013-121028.err` |
| **Interactive Instant Action by the user**: intro video, menu, about a minute of play, then a manual exit through the native shutdown (2,444 frames, `ExitProcess(0)`, all DLLs detached). The user reported the test passed. | `play-20261013-072809.err` |

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
  - It uses a discrete GPU that can present to the window, and otherwise any GPU that can. On the dev machine both rendering and presentation run on the RX 9070, confirmed at 06:14 with 120 of 120 frames. An earlier fallback to the integrated GPU happened only because the RX 9070's monitor was switched off.
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
- **Guest tick clock (engine timing).** The engine clock (`0x575a00`) runs once per main-loop pass. It reads `GetTickCount` and keeps "now" as float32 seconds. The frame step is now minus the previous float, clamped to 0.125 s, and about 100 game sites consume it, so the simulation is variable-step. No 30 fps limiter was found.
  - Defect: with raw Windows uptime the float loses resolution. At this PC's 7-day uptime it is 62.5 ms, so each step is off by up to +/-31 ms and can be zero or negative. Deterministic proof (guest-clock-r1, `MW34_VIRTUAL_CLOCK_BASE_MS=603594948`): the same Training script that otherwise completes its steps runs the mech into the bunker at maximum speed, it is destroyed (MISSION FAILURE), and the game returns to the pilot screen.
  - Fix: `GetTickCount`, `timeGetTime`, message times and DirectInput timestamps now read milliseconds since host start plus 60 s, from the performance counter (1 ms steps). `MW34_GUEST_CLOCK=uptime` restores raw uptime. The deterministic replay with the default virtual clock is unchanged (116/116 frames byte-identical).
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

Second pass, also 2026-10-13. Measured with `MW34_FRAME_TIMES` (frame, host ms, 3D scenes), aligned to the first 3D scene. Training 1 went from about 15 → 9 fps to about 19 → 12 fps over its first 36 s. Instant Action at Big Lake runs at about 20–25 fps.
- Memory checks: the stage's own stack frame, the game image/.data and the guest heap carry about 99% of mission accesses, about 2.9 million per frame. They are now checked inline, as leading disjuncts of the same contract predicate. The region cache (`guest_memory_fast.hpp`) is inline, and the thread guard reads the TEB.
- Scene readback buffers prefer host-cached memory. Uncached readback had cost about 8% of mission time.
- The per-instruction x87 exception clear/test (about 14%) is unchanged. Some lifted sites branch on the fresh exception result (integer-indefinite conversions) or pass computed masks, so a lazy clear would not be exact.

Third pass, also 2026-10-13 (user-approved re-lift for speed). Measured with the deterministic Training benchmark; all builds give byte-identical replays.
- **Merged x87 exception tracking** (`merge_x87.py`, `inline_objects.py --merge-x87`). Per-instruction clear/test plus seven sticky OR updates were about a third of game-code time. They are now merged across straight-line runs: 38,788 of 70,940 brackets. DE becomes hardware-sticky within a run, as approved by the user.
- **Host dispatch:** COM imports go straight to the COM dispatch; rounding-mode changes are skipped when unchanged; lifted-body lookups are cached.
- **Results, frames 700-1150:**
  - normal build 66.3-69.6 ms per frame;
  - merge-only build (`O2-merge`, 156 MB) 50.9-52.5;
  - merged inline build (`O2-inline`, 503 MB) 46.7-48.4, about 21 fps.
- **Default:** `Play-MW3.cmd` now launches the merge-only build (user decision). `-Build O2` selects the unmodified build.
- **Renderer:** not a bottleneck (0.67 ms per scene, 2.9% of 3D time).

### Tools and launcher

- Deterministic scripted runs: `MW34_VIRTUAL_CLOCK=<ms per frame>` (only with an input script) drives every guest time source from one virtual clock. Repeated Training and Instant Action scripts gave byte-identical frames (24/24 and 131/131), so defects can be replayed exactly. Without it, scripted Training runs diverged (for example a heading of 300 degrees versus north after the same key holds).
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

- **Camera and legs.** The user observed the camera reversing direction when leaving the starting bunker, and the 'Mech legs kicking far behind it. These are attributed to the FPATAN quadrant bug, now fixed. Checked natively after the fix (deterministic, MW34_VIRTUAL_CLOCK=50, camera-legs-r1): the chase camera stays behind the mech through the whole bunker exit with no reversal, and the external view (CMD_CYCLE_CAM) shows a regular alternating stride with the legs under the body. The user's own play test is still welcome as confirmation.
- **Frame rate.** About 12 fps in the heaviest outdoor Training scenes and 20–25 fps in Instant Action at Big Lake; menus are faster. Simulation remains wall-clock-faithful.
- **CD music source.** The local MW3 ISO (`MW3/MechWarrior-3_Win_EN_ISO-Version`) is a data-only image without CD-audio tracks; only the Pirate's Moon .bin/.cue carries one audio track. Base-game music therefore needs a rip that includes the audio tracks.
- **CD music.** MCI goes to the real Windows CD-audio driver. With no MW3 disc in a drive (this machine has none), the game logs `zsnd_cd.cpp(405)` MCI errors and plays no music, as the original would. Music needs the user's disc, or a CD-audio service backed by the user's own rip, as a configurable enhancement.
- **Pause while inactive (original behaviour).** The game's main loop (0x58FD70) waits in `MsgWaitForMultipleObjects` while its app object's active flag (+0xD0) is clear, and it ignores the mouse in that state. Activation is real Win32, so hidden scripted runs can stall or ignore scripted mouse input depending on desktop focus. Interactive foreground play is unaffected.
- **Not yet exercised natively:**
  - the remaining Training steps (follow the instructor, crouch, reverse, waypoints),
  - weapon damage and heat values compared with the original (fire, beams, hits, alpha strike and overheat destruction run natively; the alpha-strike explosion debris was replayed deterministically and its draw state inspected: the flat orange shards are textured draws, a 16x16 RGB565 fire texture modulated by a light-yellow vertex colour very close to the camera, through the game's own states. That is game content, not a missing texture; a pixel comparison with the original is still pending (instant-action-r3)),
  - AI and collision under controlled original/native comparison.
- **Platform-level deviations:**
  - Guest threads run to completion and are not preempted.
  - Concurrent file-mapping views share one address.
  - 16-bit dithering is not reproduced.
  - Cull winding is unverified.
  - FYL2X and F2XM1 carry one extra rounding.
  - x87 audit (static, 2026-10-13). Mech3.exe does its trigonometry with x87 instructions; raw byte counts, which include some false matches from data: FSIN 83, FCOS 150, FSINCOS 56, FPATAN 53, FPTAN 11, FPREM 1, FPREM1 3, FYL2XP1 1. In the lifted code, FSIN, FCOS, FPTAN and FPATAN run the literal host instruction through raw-80-bit bridges, with exception flags taken from the host status; FSINCOS arrives as separate sin and cos bridges. The FPREM remainder is exact (a host loop until C2 clears). Its C0/C1/C3 quotient bits come from remill's separately rounded division and `fptosi`, which can be wrong for huge quotients or quotients just below an integer, but the lifted users are CRT `fmod` paths that read only C2. The C2 out-of-range rule (|x| >= 2^63) for FSIN/FCOS/FPTAN is not modelled, which only matters for arguments far outside game angles.
- **Files written into the game folder:** the game writes `MW3/mech3.out`, `mech3.err` and its configs, and the overlay writes `MW3/mw34-registry.txt`.

- **Training 1 mission failure, reproduced deterministically.** Script 	raining-failure-r1/input-script.txt with MW34_VIRTUAL_CLOCK=100 (10 fps of game time) fails at mission 0:27. The mech walks north into the bunker after the scripted turn, the camera passes into the bunker geometry, MISSION FAILURE appears, and the mech explodes against the bunker wall at 0:29. The same script does not fail at 50, 66, 75 or 150 ms per frame; there the mech stays pressed against the structure. This is consistent with a collision edge case at large time steps. Real-time runs at about 13-15 fps hit it intermittently, and the float32 uptime-clock jitter (see Guest tick clock, now fixed) plausibly explains the intermittency. The trigger is the mission script, not an engine fault. Training 1 data (`zbd/t1/reader.zbd`) gives the training steps a `fail` valve with `MSG_OBJ_LEFT_MISSION_BOUNDARIES`, and each segment (`readerm1`-`m4`) has an `inside_t1mN` region with an `out_of_bounds` trigger. At a 0.1 s step the walking mech passes through the bunker wall (camera inside the wall at 0:26) and lands outside the training boundary, so the original mission logic fails the mission. The remaining question, whether the original engine also tunnels through that wall at a 0.1 s step, needs an original run at the same step. Higher frame rates avoid it.

## Next concrete blockers

1. The user re-tests the camera and legs after the FPATAN fix. Then audit remill's remaining x87 semantics for similar discrepancies.
2. Run the remaining Training steps and weapons in play, and fix the stops they surface.
3. Set up original/native comparisons for physics, AI, weapons and timing, following plan E4.
4. Frame rate: the remaining per-access bridge overhead and lifted x87 code. An exact x87 speedup needs lift-time knowledge of which sites use the exception results.
5. Line primitives (`D3DPT_LINELIST`/`LINESTRIP`) still stop visibly. Implement them when a scene uses them.
6. Acceptance lane: the user's v6 decision, then the authorized chain.

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
