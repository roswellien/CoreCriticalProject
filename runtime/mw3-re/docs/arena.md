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
seed is a whole number from 0 to 2147483647. The host is a spectator with no mech;
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
  setup; the values are read from the player's own install. A bot may also
  give `loadout`, which of its chassis' stock loadouts it gets: 0 (the
  first, and the default) up to one less than the count, in the order the
  mech lab lists them (Primary, Alternate A ...). A player's saved loadouts
  and the training ones can't be picked, so a setup plays the same on any
  install.

Whatever the preset says, a bot is awake from the start, engages any enemy,
is no one's lancemate and starts powered up: a campaign record can start its
mech shut down as an ambush (+0xcc bit 5) that only the mission's script
would power up, and the arena runs no script (`arena_bot_params`).

The seed picks where the sides start: one of the map's three most separated
pairs of spawn spots, and which end each side takes. Each side then fills the
free spots nearest its end.

## The match log

`<out>/match-<seed>.jsonl`, one JSON object a line, flushed as each line is
written. Mechs are named by their index in setup order (side A first), and
times are game seconds from the match's first frame.

- `start`: the map, minutes, seed, frame time, the sides (each bot with its
  `loadout`) and the mech ids.
- `state`: ten times a second, every mech's position, heading, speed, torso
  and arms, animation, whether it is jumping, fallen or standing, heat, part
  health, target and AI order.
- `shot`: a mech fired a weapon. A missile or bullet counts once per launch;
  a beam (lasers, PPCs) once when it turns on, however long it is held.
- `hit`: a mech took damage, with the attacker and the amount.
- `destroyed`: a mech was killed, counted when its death starts, not when its
  fall ends.
- `end`: the winner, the time and the mechs lost per side. The match is
  logged for 5 more seconds after its result is settled (so a replay shows
  the last mech fall and burn), so the `end` line's `t` is 5 s later than the
  time in the printed `arena: winner ...` line.

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
- With no mech selected, who aims at whom is drawn (orange lines) and each
  mech's planned route faintly (yellow), with a word beside each mech's id
  for what it is doing this moment:
  first how it moves: closing in (walking at an enemy its radar knows of,
  seen now or remembered), searching (going to where it last saw one),
  roaming (no enemy known: the map's middle), or, once the game's own
  combat AI has taken over (only after the game's attack checks pass), its
  move: moving to range, circling, orbiting, veering, holding range,
  following, jump dodge, heading back or breaking off; then ", firing" when
  it shot in the last 2 seconds. A mech closing in can shoot too, so
  "closing in, firing" at close range is normal. The panel says which AI
  is steering. In the 3D view a farther mech's label is drawn smaller.
  Click a mech to see
  its own picture: its planned route bright (the big dot its next
  waypoint), its goal (a white X), its radar contacts (green, solid
  detected now, dashed remembered) and its target, with the others' target
  lines and every other route faint. Once the selected mech is destroyed,
  the target lines are full again and the routes all faint.
- 1 to 5 switch those lines: 1 route, 2 target, 3 goal, 4 radar, 5 the
  doing words. H shows or hides the key to the colors at the top left.
- The selected mech's panel says in sentences what it is doing now, its
  last change of orders or target and how long ago (decisions are logged
  only when they change), its target and how far, where it is going, what
  its radar holds, its heat, and only the parts that took damage (armor
  and structure left); a destroyed mech shows only its damage. Click
  elsewhere to close it. Text, boxes and the seek bar grow with the
  window's height. F12 saves the window as `replay-<time>.bmp` beside the log;
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
say, torso and arm aims), and each logged shot and hit starts that weapon's
own fire or impact effect and sound. An arm or leg lost while the replay
plays is blown off by the game's own code: it flies away as debris with its
explosion and leaves a smoking stump; a mech destroyed while it plays bursts
with the game's death effect for its fall (forward, backward or a collapse),
except a mech killed by a lost leg, which the game shows with the leg's
explosion alone. The Elemental's lost parts are only hidden.
None of it deals damage. A seek past a loss only hides the lost part.
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

## Arena runner

A developer window that sets up, runs and rewatches matches with no setup
file or command typed (`tools/arena-runner/`, Python's tkinter, nothing to
install):

```sh
python tools/arena-runner/arena_runner.py
```

The first start asks for the game folder and the built `mw3.exe` and keeps
them in `%LOCALAPPDATA%/CoreCritical/arena-runner/settings.json`.

- **Setup:** every arena map as a picture of its terrain; 1 to 10 matches,
  all started at once; and each side's mechs: the chassis (with the mech
  lab's picture of it), one of its stock loadouts (its weapons, ammo, armor,
  speed, heat sinks and jump jets shown) and a pilot. Eight pilots come first
  under plain names (`pilots.json`), then every enemy record in the game's
  missions; each shows a line of what its numbers mean (attack range, bursts,
  how long it presses an attack, when it breaks off, aim error). Setups can
  be saved and loaded.
- **Running:** one small map per match, its mechs drawn from the match log
  as the game writes it, each tile showing its result when it ends. The
  matches run hidden, many times faster than real time, so the maps are a
  quick look; the replays are for watching. Stop all ends every match.
- **Results:** wins per side, draws, stuck matches and the average time to a
  win, and a row per match with its seed, result, time and losses, to open in
  the top-down or 3D replay or to copy its command line.

Each match gets its own random seed (all different in a batch, since a log
is named by its seed) and runs until a side is wiped out. The setup's time
limit is 15 minutes; a match still going then shows as stuck. Each match
also runs with its own write folder, made from a copy of the player's
`settings.reg`, so ten at once never race on the player's settings or
`mw3.log`; its copied command line, with that folder, replays it byte for
byte. The write folder is searched before the install, so files a mod left
in the player's usual one are not seen by these matches.

Batches are written to `%LOCALAPPDATA%/CoreCritical/arena-runner/runs/<date-time>/`:
the setup, the logs and each match's write folder.

### The catalog

The window's lists come from the game itself, so they never drift from what
that build can run:

```sh
mw3 GAME_DIR --arena-catalog DIR
```

It runs alone (not with `--arena`, `--replay` or `--replay3d`), needs only the
install, takes a few seconds and writes:

- `catalog.json`: the arena maps (those with 16 spawn spots) with the
  lobby's names; every chassis with its stock loadouts (the mech lab's names,
  weapons by part, ammo, armor, walk and run speed, heat sinks, jump jets);
  and every enemy pilot record in the game's mission readers with the numbers
  behind the runner's summary line.
- `terrain/<map>.ppm` and `<map>.json`: the map from above as the top-down
  replay draws it, framed on its 16 spawn spots with 300 m more each way (a
  multiplayer map is a part of its campaign world, which shares its files),
  at most 1024 pixels on its long side, and where it sits
  (`x0`, `z_top`, meters per pixel `cell`, `width`, `height`).
- `mechs/<mech>.ppm`: the mech lab's green picture of each chassis
  (`icon_<mech>_green`); the Elemental has none.

The files hold the game's own data and stay on the player's machine. The
runner keeps them in its folder and makes them again whenever `mw3.exe`
changes, or when its Reload game lists button is pressed (after a mod is
turned on or off, or the game files change, which the exe can't show).
