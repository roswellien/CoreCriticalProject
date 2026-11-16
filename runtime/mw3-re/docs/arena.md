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

`--seed` and `--frame-ms` are required, so a match log can be repeated; the
seed is a whole number, 0 or more. The host is a spectator with no mech;
nothing is bound to a socket and nothing leaves the process. A match plays
without sound, watched or not. Every bot walks the grid (the Improved AI
upgrade) whatever `mw3.cfg` says, so a setup and seed play the same match on
any machine. With `--hidden` and no screenshots the match draws
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
`--net-walk`, `--net-ahead`, `--briefing` or `--lab-mech`. A match that
can't start (the map's spawn spots can't be read, or a side has no bot that
could be made) prints why and exits 1.

A match log grows by every mech's state ten times a second: a few minutes of
4v4 is tens of megabytes, and the viewers read a whole log into memory.

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

### What the replay viewers read (#289)

The start line carries `"version": 2` (1 before the 3D replay). The log
reader reads versions 1 and 2 and refuses a log with no version (one written
before #289) or another version, with a message saying which; it keeps
fields it doesn't know, so a later version can add fields.

- `shot` also names the `weapon`, whether it is a `beam`, the shooter's AI
  `target` (a mech id, -1 for none), whether the weapon had a `locked` lock,
  and the `muzzle` and aim `dir`.
- `hit` also names the `weapon`.
- `state` also lists `rounds`: every bullet or missile an arena mech fired
  that is still flying, with its `id`, its shooter (`by`), `weapon` and
  `pos`. A round gets its id the first state line it is in and keeps it.
  One that lands within a tenth of a second never shows; a viewer draws it
  from its shot's muzzle and direction and its hit. Extra rounds a weapon
  spawns on its own (an LB-X's spread) aren't listed; their hits are.
- `round_end`: a round left the air, with its `round` id and last logged
  `pos`.
- `state` also lists `beams`: every beam an arena mech holds on, with `by`,
  `weapon`, `from` (the muzzle) and `to` (as far as the beam reached).
- `beam_end`: a beam turned off (`id`, `weapon`). Each beam `shot` has one.
  Rounds and beams still open when the match ends get their `round_end` or
  `beam_end` just before the `end` line.
- Each mech's `ai` also has `at`, the index in its latest `route` line's
  `points` of the waypoint it is heading for (-1 with no route), and `contacts`: the enemy mechs its sensors know, nearest first,
  each with `seen`, whether its sensors detect it now. The game clears that
  only for a shut-down mech, two passive radars or ECM, not for walls or
  hills, so it is not line of sight; the log runs no sight test of its own.
- `route`: a bot's route changed (a new order, or a path found again), with
  its waypoints as `points`; empty when its order walks without one.
- `decision`: a bot changed its order or target, with a `code`, and the new
  `target` for a target change. Order codes: `hunt_contact`,
  `hunt_last_seen` and `hunt_fallback` (it went back to hunting, by that goal
  rule), `engage` (the hunt gave way to the game's fight) and `order_other`.
  Target codes: `target_volley` (its weapons planner took the best-scored
  contact), `target_lost` (its target left the sensors and they picked
  another or none) and `target_other`. The `_other` codes mean the change
  came from somewhere the log doesn't name yet.

Version 2 adds what the 3D replay poses mechs and starts effects from:

- Each mech in the start line has its pilot's `voice` tag.
- Each mech's `state` record also has its `speed` (forward positive), the
  torso's `pitch`, each arm's aim `yaw` and `pitch`, and under `anim` the
  gait clip's `phase` (0 to 1), its cycles a second `cps`, the blend
  `weight` and the `limp` slot playing (-1 for none). While an action plays
  (a fall, a get-up), `limp` and these anim fields can still hold the last
  gait's values; the action line says what plays.
- `action`: a mech's fall, landing, get-up or collapse started, with its
  `name`: `fallf`, `fallb`, `landf`, `landb`, `getupf`, `getupb`,
  `collapsel` or `collapser`.
- `voice`: a bot's radio line, with its radio `event` (0 to 15), and
  `dropped` when the game skipped it as too soon after the last.
- `hit` and `round_end` also give `at`, where the round struck, and
  `terrain`, whether it struck the ground rather than a mech.

`mech3::arena::set_arena_log_detail(false)` leaves all of this out except the
version, and the match then reads and logs nothing new; the tests use it to show
the additions change nothing (`arena_log_detail_c1mp1_4v4_headless`).

## Watching a match (#289)

```sh
mw3 GAME_DIR --replay <out>/match-<seed>.jsonl
```

A window plays the log back on the map seen from above. Nothing of the match
runs: no engine, mission, network or bots, so a replay shows exactly what
the log holds. It exits 2 before any window for a log the reader refuses
(missing, damaged or without a version), and with `--arena`, `--host`,
`--join`, `--net-upnp`, `--mission` or `--fly`.

- The ground is the map's own triangles from the install, shaded by height
  and lit from the northwest; dark lines mark steps over 3 m (walls,
  cliffs). It is drawn for orientation and can differ a little from what the
  AI walks on. A map that can't be loaded gives gray ground with a message
  at the top; the replay still plays.
- Each mech is a dot in its side's color (A blue, B red) with its id, a white
  arrow where the legs walk, a shaded wedge where the torso points, the last
  10 seconds of its trail, and an X once destroyed. Rounds are small dots,
  beams lines, shots a short streak from the muzzle, hits a flash.

Controls:

- Drag to pan; the mouse wheel zooms about the cursor.
- Space plays or pauses (at the end, plays again from the start); Left and
  Right jump 5 seconds; `<` and `>` (the `,` and `.` keys) halve or double
  the speed, 0.25x to 8x; click or drag the bar at the bottom to seek.
- 1 to 5 switch the overlays: 1 routes, 2 target lines, 3 hunt goals,
  4 radar contacts (solid detected now, dashed known but not detected),
  5 the last decision reason under each mech.
- Click a mech for its panel: chassis, side, heat, target, order, last
  reason and each part's armor and internal structure; click elsewhere to
  close it. F12 saves the window as `replay-<time>.bmp` beside the log;
  Escape closes the viewer.

`--replay-script FILE` drives the viewer from a file of commands, in a hidden
window, for tests: `wait SECONDS`, `key K` and `keyup K` (`space`, `left`,
`right`, `comma`, `period`, `escape`, `enter`, `f12`, `1` to `5`, `a` to
`z`), `click X Y`, `drag X1 Y1 X2 Y2`, `wheel X Y NOTCHES`, `shot FILE.bmp`,
`seek SECONDS`, `camera X Y Z YAW PITCH`, `follow ID` and `quit`
(`src/frontend/sdl/replay_ui.h`). Scripted runs step a fixed 1/60 s a frame.
Input, seeks and camera moves take effect the next frame, so a `shot`
shows the frame before the commands after it. The top-down viewer ignores
`camera` and `follow`.

## Watching a match in 3D (#289)

```sh
mw3 GAME_DIR --replay3d <out>/match-<seed>.jsonl
```

The match plays back in the game itself, on its map, with each logged mech
drawn as the game's own mech. Nothing of the match is simulated: no AI,
weapons, damage, missions or sensors run. Each frame every mech is posed
from the log with the game's own animation code (the walk and run clips at
the logged phase, falls, get-ups and collapses as the log's action lines
say, torso and arm aims), lost arms and legs are hidden, and each logged
shot and hit starts that weapon's own fire or impact effect and sound.
Version 1 logs play too, with a walk guessed from the distance moved.

It exits 2 before the game starts for a log the reader refuses, a map that
isn't a multiplayer map in the install, a chassis it doesn't know, and with
`--replay`, `--original` or anything `--replay` refuses.

Controls (the quit box's own keys work while it is open):

- Space, Left and Right, `<` and `>`, 1 to 5, the seek bar and the mech
  panel as in the top-down viewer. Each mech has a ring at its feet in its
  side's color and its id above it.
- The camera starts behind the first mech. Hold the right mouse button and
  move the mouse to look; W, A, S and D fly, Q and E go down and up; the
  mouse wheel changes the flying speed. Left-click a mech to follow it from
  behind and open its panel; flying or looking lets it go.
- F12 saves `replay3d-<time>.bmp` (beside the script with `--replay-script`,
  else in the current folder).
- Escape opens the game's quit box and pauses the replay; N goes back, Y
  ends the program. The replay takes the Core Critical HUD (`--cc-hud
  core-critical`, with the installed HUD pack's art when it is found) unless
  `--cc-hud` or `cc_hud=` in `mw3.cfg` says otherwise.
- Beams and rounds in flight are the game's own: each weapon's beam node
  and projectile model, with its flight animation, placed where the log
  puts them each frame. They are never fired, so they deal no damage.

- The replay plays at the screen's shape (widescreen on a wide screen),
  whatever mission resolution is saved, and leaves the saved one as it was.

Limits: no radio chatter plays (the log records it). A seek starts no
effects for the span it skips, and effects already playing run on. Every hit
plays the weapon's default ground impact, even on a mech. The longer view
and fog distance of the old Core Critical host isn't in this runtime, so the
replay shows the map's own fog. A mech is
picked by its label's point on the screen, not its shape. The camera goes
through hills.

## Repeating a match

The same seed and frame time play the same match, byte for byte, when the run
is `--hidden` with no screenshots and on the same build. Drawing the scene
changes how a match plays out (#294), so a watched match can differ from the
same seed run hidden. The bots' update order is shuffled each frame from the
seed, so neither side always sees the other a frame late; another compiler
or standard library may shuffle differently. The first match in a process can
also differ from later ones with the same seed (#302); a fresh `mw3` run per
match, as above, is not affected.
