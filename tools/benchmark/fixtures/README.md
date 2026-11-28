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
Supernova, Orion), recorded with the command above, `--arena` pointed at that file, into
`local/benchmark/reference-16/match-7.jsonl` (SHA-256
`003521ae20a0e503cc7b9946e050a89e0b9037c9aca365572dd5ad40bf5d2f54` on
2026-11-26). Each camera shot follows its own `mech`, so every cut shows a
different chassis. The 4v4 notes above describe the original reference.

Use a fresh output directory for each attempt. This scene starts at log time
20 seconds, warms up over [20, 40) (the first frame loads all 16 chassis and
can take over 10 s), and scores [40, 70).

The measured span holds 803 shots and hits (267 shots, 536 hits), the
heaviest fighting from 60 to 70 seconds. Each cut follows its own mech, all
alive for their cut: chase Mad Cat 10 s, chase Avatar 8 s, orbit Vulture 7 s,
side Thor 5 s, high Strider 5 s, front Sunder 5 s, low Champion 5 s and chase
Bushwacker 5 s (50 s in all). Chase is 40 meters behind the mech and orbit is
60 meters out at 28 degrees per second. Within each shot the camera uses
interpolated replay poses. The renderer uses the same recorded fight time for
effects.

For an authored alternative, set the scene camera to
`{"mode":"track","file":"c1mp1-camera.json","sha256":"..." }` and provide the
file's SHA-256. Key times are relative to playback start and the track must
cover the whole 50 s span; `c1mp1-camera.json` ends at 40 s and needs
extending first. Keep recording files and run outputs in local storage.

## Four-scene suite (#596)

`suite-benchmark.json` replays four authored recipes. Every scene uses only different
chassis, all with stock loadout 0 and the c1/ia1 `Enemy_01` preset. The sides are
roughly matched by tonnage so the fight lasts through the camera plan.

| Scene | Recipe | Fight | Look | Chassis |
| --- | --- | --- | --- | --- |
| c1mp1 | `scene1-c1mp1-2v2.json` | 2v2 | dawn, rain | Mad Cat, Shadow Cat v Thor, Bushwacker |
| c2mp2 | `scene2-c2mp2-4v4.json` | 4v4 | mid-day | Avatar, Owens, Cauldron-Born, Shadow Cat v Black Hawk, Bushwacker, Strider, Champion |
| c3mp1 | `scene3-c3mp1-6v6.json` | 6v6 | dawn | Mad Cat, Thor, Vulture, Puma, Strider, Black Hawk v Orion, Avatar, Champion, Owens, Shadow Cat, Bushwacker |
| c4mp2 | `scene4-c4mp2-8v8.json` | 8v8 | night, rain, headlights | all 16: Mad Cat, Thor, Vulture, Avatar, Owens, Strider, Daishi, Shadow Cat v Black Hawk, Bushwacker, Champion, Cauldron-Born, Puma, Sunder, Supernova, Orion |

Time of day, weather and headlights are scene fields in the definition, not recipe
fields: they are visual only, so the recorded fight is the same either way.
`time_of_day` borrows a campaign mission's lighting (`dawn` t1m1, `day` c3m1, `dusk`
t1m4, `night` c1m3, as the arena's #507 times of day). `weather: "rain"` adds rain to
a map without weather of its own, with the values of c3mp2's stock rain (100
particles, colour 128 128 172, wind 0.2, gravity 3, alpha gradient 0.5 to 0).
`headlights: true` lights every standing mech's stock headlights at full strength;
`run.py` turns Headlights and Dynamic lighting on for that scene in both arms.

The old c2mp2 setup let the seed start the sides at spots 0, 1, 2, 4 and 9, 10, 11,
14, and the fight piled up against the central plateau's cliff (median hit 15 m from
raised ground, all within 100 m), below a camera that saw nothing. The c2mp2 recipe
now gives every bot a `spot` (an arena setup option: every bot gets one or none, each
spot once): side A starts at 0, 4, 1, 2 in the east and side B at 8, 15, 6, 5 along the
north, all on open floor. Seven candidate layouts were recorded and scored by each
hit's distance to raised ground in the arena catalog's terrain picture (pale tan,
4 m cells). In the chosen layout the measured fight is on open ground north of the
plateau: no hit within 100 m of raised ground, median 180 m.

### Logs

Each log was generated twice in fresh serial Windows x64 Release processes and the
pair was byte identical, with seed 7 and 33 ms updates. Generator source `c4087bc8d5c77c0b14fb9d2c9a72295caea05a73`
plus the uncommitted changes of this PR, executable SHA-256 `ef5a673135dc987b993faa8e1ac7962908cecb1fe7f5b3c74aba2edd7479f1b9`.

| Recipe | SHA-256 | Bytes | States | Terminal record | Shots / hits |
| --- | --- | ---: | ---: | --- | ---: |
| scene1-c1mp1-2v2 | `ed3bbde5034aa86808e36fd5bfad561b8a2c58d15d0295051e7addb04c3c72bd` | 13,459,997 | 2,838 | 93.654 s, B wins, losses 2/0 | 197 / 200 |
| scene2-c2mp2-4v4 | `cad68fa66cad1c02d7ad8a1e893a4eb5adff3074885cae57a87f4c6cbec090b7` | 31,238,185 | 3,443 | 113.619 s, B wins, losses 4/2 | 414 / 439 |
| scene3-c3mp1-6v6 | `af94084a8b6b63ca8ed7b08b11b239234b6becc87b1afe297e303197040381c6` | 42,036,940 | 3,022 | 99.726 s, A wins, losses 2/6 | 590 / 1482 |
| scene4-c4mp2-8v8 | `8e6143b1db68867afe3e6733cac91ee3eb238e2787f2755651ee402ef193f1a1` | 102,691,780 | 5,607 | 185.031 s, B wins, losses 7/4 | 831 / 1579 |

### Windows and cameras

For each log the start and subjects were chosen by this rule. Subjects alternate
sides, two from each. Each must stand through its whole window. A subject's score is
the shots and hits within 150 m of it during its window, using the nearest following
pose. The start is the integer second that maximises the summed subject scores plus
the mean active rounds and beams over the measured span.

| Scene | Log start | Warm-up + measured | Subjects in order | Seconds each |
| --- | ---: | --- | --- | ---: |
| c1mp1 | 36 s | 10 + 40 s | 1, 2, 0, 3 (all four) | 10 |
| c2mp2 | 15 s | 10 + 80 s | 3, 7, 2, 4 | 20 |
| c3mp1 | 4 s | 10 + 80 s | 5, 6, 1, 7 | 20 |
| c4mp2 | 101 s | 10 + 60 s | 0, 8, 2, 15 | 15 |

The warm-up is a wide chase (60 m back, 24 m up) on the first subject. Each subject
then gets a chase 45 m back and 20 m up, a 5 s orbit at 55 m and 28 degrees per
second, and a 5 s front or high angle. The c1mp1 subjects, 10 s each, alternate the
orbit and the angle. The native parser needs shots of 5 to 20 s, a chase first, and
two different angles after the first orbit. The side angle was dropped: on c2mp2
it sat behind a tall structure.
