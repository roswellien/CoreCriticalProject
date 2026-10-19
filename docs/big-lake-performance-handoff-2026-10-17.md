# Big Lake performance: summary, recommendation and handoff (2026-10-17)

Scope: the Big Lake Sun Tests host (`C:/Users/jcbla/MW34SunTests/big-lake-r1/shadow-r1/host`), launched by
`Play MW3 - Big Lake Sun Tests.cmd` (`tools/remaster-launcher/play_big_lake_sun.ps1`, profile
`local/remaster/big-lake-sun-tests.json`). Acceptance stays 131/144; nothing here is committed.

## Work done this session (performance)

| Change | Script (ordered host edits) | Effect |
|---|---|---|
| Environment lookups cached; roster name set | `apply_perf_env_cache.py` | stress replay 10.85 → 6.91 ms |
| Performance overlay stops allocating full-screen host buffers | `apply_overlay_no_host_target.py` | 6.91 → 5.9–6.6 ms |
| Guest-call dispatch skips the hook chain for unhooked addresses; inline guest load | `apply_dispatch_fast.py` (must be last) | → 5.10 / 5.14 ms |

- Captures are pixel-identical to the earlier runs (test cases `models-r2-ovl` and `models-r2-disp`).
- Launcher additions: `-ProfileOut <file> -ProfileFrom N` runs the host sampling profiler, and mech normal
  strength defaults to 3.4 (4x).
- Big Lake now uses the current registry meshes and textures (`assets/models-r2`).
- Details are in `docs/big-lake-mech-shadows-2026-10-16.md`.

Double-buffering the renderer was tried and reverted. Fence waits measured about 0.01 ms per frame in the stress
replay. The earlier "22% driver waits" were teardown at exit, not frame time.

## Latest live run (user, `play-runs/20261017-142423-569`, current build eb8d0bd7)

- 184 s and 12,047 mission frames: mean 13.1 ms (76 fps), median 13.0, p95 17.3, p99 21.2. Nine frames over
  33 ms during the mission (38–206 ms), and loading spikes at mission start.
- Per-frame load in the mission: 900–2,070 transformed-lit (TL) draws, about 2,000 haze-routed draws,
  30–120 replacement-mech parts, and 11 3D scenes per frame. The heaviest stretch, with 119 mech parts, reached
  15.8 ms median / 21.1 ms p95.
- The scripted stress replay (`-Script local/gpu-projection-watch-r1/frozen/input-script.txt`, frames
  1750+) is **not representative**:

  | | Guest calls per frame | TL draws per frame | 3D scenes per frame | Frame time |
  |---|---|---|---|---|
  | Stress replay | ≈ 93k | ≈ 380 | 7 | 5.0 ms |
  | Live play | ≈ 92k | ≈ 1,500 | 11 | 13 ms |

  The replay also runs on a 50 ms virtual clock. With a similar call count, the extra ~8 ms in live play
  follows the larger TL/scene workload. That is game-side CPU vertex work inside the lifted bodies, the host's
  per-TL-draw capture/haze/submission path, or both. No profile of live-like load exists yet.
- Only Mad Cat, Thor, Vulture and Bushwacker were upgraded. Six instances kept original models (distance
  meshes and chassis the Big Lake host lacks).

## Recommendation

Focus on the two items the user chose, in this order:

1. **Terrain on the GPU.** The terrain the original game transforms and lights on the CPU every frame (TL
   draws: green in `-PathDebug`) becomes resident GPU geometry, drawn with the existing world/sun shaders and
   the game's camera. It must keep the original terrain data, culling, LOD/tile choice and draw order, and fall
   back visibly rather than silently.
   The existing `MW34_GPU_WORLD` / world-fast-binding path already does this for world meshes and is the
   model to follow.
2. **Pipelining.** Overlap the guest simulation of frame N+1 with host rendering and presentation of frame N.
   The guest's D3D/DirectDraw calls are synchronous: locks, readbacks, `GetAttachedSurface` and HUD
   compositing read back results. So this needs the scene recorded into host-owned command data during
   the guest frame, then submitted and presented on a render thread. Determinism and the frame-budget/virtual
   clock harness must keep working.

First step for either one: a reproducible **live-like** benchmark, either an input recorder producing
`MW34_INPUT_SCRIPT` files, or a scripted route into a multi-mech fight. Add a profile of that load split into
guest bodies vs host TL/scene work. Without it, gains cannot be predicted or verified.

## Expected uplift (estimate, to be confirmed by the live-like profile)

The basis: about 8 ms of the 13 ms live frame follows the TL/scene load that the replay doesn't have.

- **Terrain on the GPU** removes most of that per-frame CPU transform and the host's per-draw capture and
  routing for terrain. Estimate: 3–6 ms saved in heavy combat, i.e. 13 → 7–10 ms (≈ 76 → 100–140 fps). It
  likely helps the 1% lows the most.
- **Pipelining** hides whichever is smaller, the host render/present work or the guest frame. After terrain
  moves to the GPU, that is probably 1–3 ms more (≈ +10–30%). Its main value is steadier frame pacing.
- **Combined:** roughly 1.5–2x in heavy live combat (≈ 110–150 fps from 76), with a pessimistic case of
  about 1.2x if most of the extra cost turns out to be game logic inside the lifted bodies. The light stress
  replay (already 5 ms) would gain little.

## Handoff prompt for the next agent

> You are taking over performance work on the MW3 recompilation's Big Lake test host. First read
> `CLAUDE.md`, `docs/big-lake-performance-handoff-2026-10-17.md` and
> `docs/big-lake-mech-shadows-2026-10-16.md` (sections from "Performance with many mechs" onward).
> Project rules apply: preserve original gameplay (no interpreter/original-code fallback, no faked
> services), keep original media/generated code local, protect other running jobs (check for a running
> `entry_commandline` / game before launching anything), and do not commit unless the user asks.
>
> Your task is **investigation and planning only**. Do not implement yet. Produce a written plan, as a new doc
> in `docs/`, for two items:
>
> 1. **Terrain on the GPU:**
>    - Find where the original game transforms and lights terrain on the CPU and emits TL draws: the per-frame
>      terrain path, the tiler around 0x4f5c80/0x4f61b0/0x49bfd0, and the host's TL capture
>      (`sun_tl_capture_stage.inc`, `world_*` stages, `vk_scene.hpp`).
>    - Measure how much of the TL draw count and frame time is terrain.
>    - Design how terrain could become resident GPU geometry driven by the game's own camera, tile choice and
>      culling. Use the existing GPU world/world-fast-binding path as the reference.
>    - Spell out how correctness is checked: pixel comparison with current captures, and an exact match of
>      game state and collision behaviour.
> 2. **Pipelining:**
>    - Map every point where the guest frame waits on host rendering results: locks, readbacks,
>      `fetch_resident`, HUD/menu compositing, present, and the virtual clock and frame budget.
>    - Propose a design where the host records the scene during the guest frame and submits and presents it on
>      another thread while the guest computes the next frame.
>    - List what must stay synchronous.
>
> Before planning, build a reproducible live-like benchmark. Live play runs ~13 ms/frame with ~1,500 TL draws
> and 11 scenes per frame, while the existing scripted replay (5 ms, ~380 TL draws, 7 scenes) is too light.
> Options: an input recorder that writes `MW34_INPUT_SCRIPT` files, or a scripted route into the user's saved
> 10-mech Instant Action fight.
>
> Profile it with the launcher's `-ProfileOut`/`-ProfileFrom`, symbolizing with
> `local/tools/llvm-21.1.8/.../llvm-symbolizer.exe` against
> `shadow-r1/host/build/entry_commandline.exe`. Report the split between recompiled guest bodies, host
> TL/scene work, and dispatch.
>
> Deliverable:
> - the plan doc, with the measured breakdown, design, risks, verification steps and an estimated frame-time
>   gain for each item;
> - a short summary to the user recommending which to implement first.
>
> Build workflow reminders: host edits are ordered `tools/remaster-launcher/apply_*.py` scripts applied to
> `shadow-r1/host/host-source`. `apply_dispatch_fast.py` must stay the last edit. After a build
> (`shadow-r1/host/build.ps1`), update `executable_sha256` in `local/remaster/big-lake-sun-tests.json`.
