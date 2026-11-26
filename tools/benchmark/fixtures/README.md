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
