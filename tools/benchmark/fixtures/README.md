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

The scored scene now replays `c1mp1-8v8-reference.json`: 16 different
chassis (Mad Cat, Thor, Vulture, Avatar, Owens, Strider, Daishi, Shadow Cat
against Black Hawk, Bushwacker, Champion, Cauldron-Born, Puma, Sunder,
Supernova, Orion), recorded with the command above into
`local/benchmark/reference-16/match-7.jsonl` (SHA-256
`003521ae20a0e503cc7b9946e050a89e0b9037c9aca365572dd5ad40bf5d2f54` on
2026-11-26). Each camera shot follows its own `mech`, so every cut shows a
different chassis. The 4v4 notes above describe the original reference.

Use a fresh output directory for each attempt. This scene starts at log time
20 seconds, warms up over [20, 40) (the first frame loads all 16 chassis and
can take over 10 s), and scores [40, 70). The measured
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

## Four-scene suite (step 3, #514)

`suite-benchmark.json` keeps the qualified c1mp1 definition and adds c2mp2 and
c3mp1 4v4 baselines plus c4mp2 stress. The baselines use the same chassis,
stock loadouts and pilot preset as c1mp1. The stress recipe doubles each
side, filling the map's 16 spawn spots (`remote_0` through `remote_15`). The
arena setup accepts at most eight bots per side, and generation verified all
16 spawned.

The three new logs were each generated twice in fresh serial Windows x64
Release processes with separate profiles and log directories. Each pair was
byte identical and ended with a complete terminal record. The generator was
source `0368e1bd905f331d684a0ac2fb12f950dfa7e983`, executable SHA-256
`76065ea217934d601bcb5c0d3fadae508dee760887ecdac5f440ca3d04639953`, MSVC
19.51.36260.0, SDL 3.4.18 and SDL_ttf 3.2.2. The original install's
`zbd/reader.zbd` SHA-256 was
`5e17037f3634480f74265b3e378e4513b84cae518e20bc55cd5c6e9c6683851a`.
The ten `.zbd` archives together fingerprinted as
`c882ddae83e20e6d95f42b9555c3f1dda3f5cb07d9357744844eac931766e851`.
All three logs used seed 7 and began at `state.t=0.033000119030475616`.

| Map | SHA-256 | Bytes | States | State spacing (ms) | Terminal record |
| --- | --- | ---: | ---: | --- | --- |
| c2mp2 | `f0e1f715fcac76ac9785d34a0edaef68e10dba233d9582b6cb8299e9c051e27c` | 53,939,593 | 5,607 | 32.989502–33.004761 | 185.031 s, draw, A/B losses 2/2 |
| c3mp1 | `06628063fa10810716e72f0140720c8bd659e2c22b4d170f45eab23eba972d31` | 34,974,802 | 3,667 | 32.997131–33.004761 | 121.011 s, A wins, losses 3/4 |
| c4mp2 | `e4a7c52fef671a036d88b5b64a0b7d6051c699194b13f3bea3466f6cff9e2645` | 105,104,293 | 5,607 | 32.989502–33.004761 | 185.031 s, B wins, losses 7/5 |

Full-match shots and hits were 644 and 1,048 for c2mp2, 574 and 892 for
c3mp1, and 1,095 and 1,223 for c4mp2.

The baselines start at log times 30 s (`c1mp1`), 102 s (`c2mp2`) and 21 s
(`c3mp1`). Each warms up for 10 s and measures for 30 s. The c2mp2 and c3mp1
cuts use their highest-activity measured windows. The cameras follow surviving
mechs 3, 1 and 4, respectively, with the same seven shot types and timings.
For the new routes, subject selection counts shots and hits within 150 m of
each surviving mech, using the nearest following pose and the lowest ID to
break ties.

The stress candidates were ranked by the mean per-state product of standing
mechs and active recorded rounds plus beams. At nominal measured start
10 s, the top c4mp2 window had a score of 69.96, with 14.61 standing mechs
and 4.70 rounds plus beams on average. The next candidate at 11 s scored 62.74.
The three baseline windows scored 18.39, 17.46 and 52.07 in suite order.
The selected stress route follows mech 10 from the first recorded state
(`t≈0.033 s`), measures `[10.033, 40.033)` and carries warm-up effects across
the boundary. The Windows replay results are recorded in the
[benchmark README](../README.md).
