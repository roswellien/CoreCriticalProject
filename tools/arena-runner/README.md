# Arena runner

Sets up, runs and rewatches AI bot matches in the MW3 runtime's arena, so
changes to the AI can be measured over many matches. A developer tool, not
part of the game. The full guide, including how to test an AI change, is
[runtime/mw3-re/docs/arena.md](../../runtime/mw3-re/docs/arena.md).

Tested on Windows only. Needs Python 3.11 or later (tkinter comes with it), a MechWarrior 3 install
and a built `mw3.exe` from `runtime/mw3-re`
([building.md](../../runtime/mw3-re/docs/building.md)).

The window, for people:

```sh
python tools/arena-runner/arena_runner.py
```

The command line, for scripts and agents (no window):

```sh
python tools/arena-runner/run_batch.py tools/arena-runner/examples/2v2-c1mp1.json --exe PATH/mw3.exe --game GAME_DIR
```

`--exe` and `--game` are needed only the first time; both tools keep them in
`%LOCALAPPDATA%/CoreCritical/arena-runner/settings.json`. Batches, logs and
`results.json` go to `runs/` beside it.

The runner's setup file (not the game's own `--arena` setup) names the map,
how many matches (1 to 10, all run at once) and each side's mechs (1 to 8),
each with a chassis, the index of one of its stock loadouts and a pilot
record (`world/mission/record`). `run_batch.py` prints one line per match and writes
`results.json` into the batch folder; its keys and exit codes are in the
guide. The window's
Save setup writes one; [examples/](examples/) has one to copy. The lists of
maps, mechs, loadouts and pilots the game offers are in `catalog/catalog.json`
in the same folder, written by `mw3 GAME_DIR --arena-catalog DIR` the first
time either tool runs.

Tests: `python -m unittest discover tools/arena-runner/tests`.
