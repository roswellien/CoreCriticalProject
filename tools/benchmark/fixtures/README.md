# Arena graphics benchmark reference (step 1, #514)

`c1mp1-4v4-reference.json` is an authored arena setup: c1mp1, three-minute
limit, four bots on each side (two Mad Cats and two Orions), stock loadout 0,
and the shipped c1/ia1 `Enemy_01` pilot preset. These chassis and presets are
available in the arena catalog. The fixed seed is **7**, with **33 ms** hidden
updates. Screenshots are off (no `--shot` option).

Run from the repository root, with the locally built executable:

```powershell
& local/benchmark/build/Release/mw3.exe GAME_DIR --arena tools/benchmark/fixtures/c1mp1-4v4-reference.json --seed 7 --frame-ms 33 --hidden -nofmv --arena-record-every-update --write-dir local/benchmark/reference-write --no-import --no-mods --no-launcher --no-vfw-helper
```

The install is read-only. The explicit write directory keeps settings and
runtime output inside the worktree. The log is
`local/benchmark/reference/match-7.jsonl`; the arena refuses to overwrite it.
For a repeat, first move the previous log to another ignored local folder.
Never commit generated logs, catalog exports or game media.

## Expected SHA-256 and summary

Observed on 2026-11-26, Windows x64 Release, MSVC 19.51.36260.0,
SDL 3.4.18 and SDL_ttf 3.2.2. Two fresh executable runs of the command above
produced byte-identical logs.

- SHA-256: `73c806026cea91abd99ec16f20f8a3d1cab70510718bae15c5896280436596f7`
- Size: **50,647,064 bytes**.
- States: **5,413**, from `t=0.033000119030475616` to
  `t=178.6289825439453` seconds.
- Observed state spacing: **32.989501953125 to 33.0047607421875 ms**.
- Result: **A wins**, losses **A=3, B=4**; end record `t=178.629` seconds,
  including the five-second aftermath.
- Events: 604 shots, 833 hits, 462 round ends, 130 beam ends, seven destroyed
  mechs and seven actions.

This is an observed checksum, not a portable golden hash: determinism is
promised only for the same build and hidden/no-screenshot settings. Compiler,
library or simulation changes can change the reference and require an explicitly
regenerated local recording. The headless test harness has its own startup and
clock history, so its checksum can differ from the executable's reference.

## Verification

`arena_record_every_update_c1mp1_4v4_headless` reads this fixture, records twice
with seed 7 and 33 ms updates, compares every byte, checks strictly increasing
update timestamps and complete pose/round/beam state, and loads the result with
`mech3/replay_log`. It also compares omitted and explicit-false recording
settings byte for byte and checks the default version-2 record shape and
nominal 100 ms cadence. Logs created by this test are temporary.

The recording advances arena capture fidelity for later replay benchmarks;
it does not measure renderer performance or establish native gameplay progress.

## Real-time playback (step 2, #514)

Build the Windows mw3 target with MW3_CORE_CRITICAL_VULKAN=ON and SDL3
and SDL3_ttf available. Run from the repository root with the frozen log
above and the installed launcher's NativePreview folder.

```powershell
python -B tools/benchmark/run.py --launcher-runtime "LAUNCHER_DIR/NativePreview" --out local/benchmark/c1mp1-play
```

The runner reads the saved Play settings and active packs from MW3Remaster's
settings.json. For a different install, add --game-dir GAME_DIR. Override
resolution and presentation with --resolution WxH and --window-mode
windowed, fullscreen, or borderless. Fullscreen modes use the desktop's size,
which must match the requested resolution.

Other per-run overrides are --aa, --af, --draw-distance, --fog-distance,
--flare-style, --active-packs (comma-separated IDs in priority order), and
--dynamic-lighting, --shadows, --headlights, --water-detail and --cloud-detail
(each on or off). The render worker, Vulkan WSI, IMMEDIATE presentation,
v-sync off and disk cache off are benchmark requirements. Updated MW3 Mechs
takes priority over MW5 on shared chassis. The planner reports pack
compatibility exclusions. It writes generated catalogs and the launch plan to
the isolated profile under local/benchmark.

Use a fresh output directory for each attempt. This scene starts at log time
30 seconds, warms up over [30, 40), and scores [40, 70). The measured
span contains 593 shots and hits, with the heaviest fighting from 45 to 55 seconds.

The sequence follows mech ID 3, an Orion that survives the full span. Among
survivors it had the most shots and hits within 150 meters (593), based on
event positions and the nearest following pose snapshot. The camera cuts
are chase 8 s, orbit 7 s, side 5 s, high 5 s, front 5 s, low 5 s, and chase
5 s. Chase is 40 meters behind the mech and orbit is 60 meters out at
28 degrees per second. Within each shot the camera uses interpolated replay
poses. The renderer uses the same recorded fight time for effects.

For an authored alternative, set the scene camera to
`{"mode":"track","file":"c1mp1-camera.json","sha256":"..." }` and provide the
file's SHA-256. Key times are relative to playback start and the track must
cover the whole span. Keep recording files and run outputs in local storage.
