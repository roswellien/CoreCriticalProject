# The AI arena (ours, #287)

A test tool, not part of play: AI bots fight each other in a multiplayer match
on one computer, so changes to the AI can be measured. Nothing here runs in the
campaign, Instant Action or a normal multiplayer game.

## The hunt order (`mech3/zai_hunt`)

Stock MW3 moves its AI along route nets the designers laid by hand for each
campaign mission (ai.md sections 8 to 10). Multiplayer maps ship none, so a bot
placed there would have nowhere to go. The hunt order gives it a goal:

1. the nearest enemy its sensors have a contact on;
2. else the place where it last saw an enemy, until it comes within 30 m;
3. else a fallback point the arena sets for the whole map (the middle of the
   map's spawn spots), where it stands and waits.

It walks there by the walkability grid (`zai_nav`, lancemate-pathing.md) when
the straight way is blocked, and straight otherwise. The grid is behind bug
fixes, as the lancemates' is; the arena refuses `--original`.

The hunt doesn't fight. Its net allows an attack, so once an enemy is within
the pilot's attack range the stock engage gate (ai.md 17.3) pushes the stock
fight on top, with the stock targeting, firing and weapon choice. When that
fight ends the hunt runs again.

All bots share one hunt net, as the game's lancemates share one formation net;
each bot's goal, last-seen place and grid way live in its own order.

## Running a match

```sh
mw3 GAME_DIR --arena setup.json --seed 7 --frame-ms 33 --hidden -nofmv
```

`--seed` and `--frame-ms` are required, so a match log can be repeated. The
host is a spectator with no mech; nothing is bound to a socket and nothing
leaves the process. With `--hidden` and no screenshots the match draws
nothing; without `--hidden` a window follows one bot, and the camera-cycle
key moves the view to the next bot still standing.

The run ends once the match is decided: one side with no mech standing loses,
both at once is a draw, and at the time limit the side with more standing
wins. It prints the result, for example
`arena: winner A, time 1:22, lost A 0 B 1`, and exits 0.

A run exits 2 before anything starts when the setup has a bad value (the
message names the field), the map or a preset can't be found in the game
files, the match log already exists, or an option the arena can't use was
given: `--host`, `--join`, `--net-upnp`, `--original`, `--mission` (and
`--fly`), `--net-minutes`, `--net-soak`, `--net-drive`, `--frames`, `--fire`,
`--net-walk`, `--net-ahead`, `--briefing` or `--lab-mech`.

## The setup file

```json
{
  "map": "c1mp1",
  "minutes": 5,
  "out": "D:/arena-runs/test",
  "sides": [
    [{"mech": "madcat", "preset": {"world": "c1", "mission": "ia1", "record": "Enemy_01"}}],
    [{"mech": "madcat", "preset": {"world": "c1", "mission": "ia1", "record": "Enemy_01"}}]
  ]
}
```

- `map`: a multiplayer lobby map id (`c1mp1` and so on).
- `minutes`: the time limit, 1 to 600.
- `out`: the folder the match log is written to (made if missing).
- `sides`: two lists of 1 to 8 bots. Each bot names a chassis (`mech`, the
  roster name) and a pilot preset: an AI record shipped in the game's files,
  named by its world, mission reader and record. Only the name goes in the
  setup; the values are read from the player's own install.

The seed picks where the sides start: one of the map's three most separated
pairs of spawn spots, and which end each side takes. Each side then fills the
free spots nearest its end.

## The match log

`<out>/match-<seed>.jsonl`, one JSON object a line, flushed as each line is
written. Mechs are named by their index in setup order (side A first), and
times are game seconds from the match's first frame.

- `start`: the map, minutes, seed, frame time, the sides and the mech ids.
- `state`: ten times a second, every mech's position, heading, speed, torso
  and arms, animation, whether it is jumping, fallen or standing, heat, part
  health, target and AI order.
- `shot`: a mech fired a weapon. A missile or bullet counts once per launch;
  a beam (lasers, PPCs) once when it turns on, however long it is held.
- `hit`: a mech took damage, with the attacker and the amount.
- `destroyed`: a mech was killed, counted when its death starts, not when its
  fall ends.
- `end`: the winner, the time and the mechs lost per side.

A run stopped early leaves a log with no `end` line; delete it before running
the same seed again, since an existing log is never overwritten.

## Repeating a match

The same seed and frame time play the same match, byte for byte, when the run
is `--hidden` with no screenshots and on the same build. Drawing the scene
changes how a match plays out (#294), so a watched match can differ from the
same seed run hidden. The bots' update order is shuffled each frame from the
seed, so neither side always sees the other a frame late; another compiler
or standard library may shuffle differently.
