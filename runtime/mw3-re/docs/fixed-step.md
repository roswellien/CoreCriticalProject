# Fixed simulation step (#485)

MechWarrior 3's simulation was tuned for about 30 frames a second: damping
tables, suspension, collision responses, gait blends and timers all assume a
frame of about 1/30 s. Run with shorter frames, many of them drift (#520: the
Harassers in Operation 2 Mission 1 ride nose-down and stall at 144 fps). So the
mission frame runs its simulation in fixed steps of exactly 1/30 s and draws
once per real frame, blending what it draws between the last two steps.

## What runs where

Each drawn mission frame (`CoreState::frame`, Mech3.exe 1.2 @ 0x00481e70) runs
zero or more steps, then draws once.

**Per step** (the frame time reads 1/30 s): the input poll and the command
callbacks it fires; the action lists (`lists_update`: the player, mechs,
vehicles, turrets, sequences, effect animations, mission objects);
`world_tick` (sensors, missions, the pilot, the camera, an arena spectator's
camera); the cameras' part of the draw (below); the viewed mech's missile
lock and its arms aimed at the reticle's point (`hud_step`); the clock copies
`sync_frame_step` makes for the mech, weapon and hit modules; and the step log.

The HUD's frame (`hud_update`, 0x0040fac0) holds two pieces of simulation.
It runs the missile lock (`HudReticle::aim_state` and its 0.6 s wait), which
decides whether the weapons fire locked, and it ends by pointing the player's
arms at the reticle's aim point (`hud_handoff`, 0x0041cd40), which the mech
update picks each step (`player_frame`). The original ran it in each frame's
draw, so once a step at its 30 fps. Left in the drawn frame, the aim matched at
30 fps and up (a draw always falls between two steps) but not below: a frame
of two steps ran the second with the arms still on the point before, and in
c2m1 a shot hit 0.1 mm apart at step 1316 at 50 and 100 ms frames. The lock's
wait counted drawn frames' time, so a lock could come a step apart between
frame rates. So with the fixed step both run once a step, after
`prepare_cameras`, in the original's order (`hud_step`: `Hud::lock_step`, then
the aim), and the drawn frame's HUD update leaves them out (`hud_in_steps`).
The zoom window's light, which read the reticle's state right after the lock's
aim state set it, reads it as the last step's aim state left it
(`state_seen`). The rest of the
HUD's frame stays in the drawn frame: its 2D parts draw themselves as they
update (the radar's blips are blitted in `HudRadar::update`). One input of the
lock still comes from the drawn frame: whether the reticle is over the target
reads TARGET's bracket where it was last drawn, which the HUD places as it
draws, so with the reticle at the bracket's very edge the answer can differ by
a pixel's worth between frame rates.

The pocket commander's pick request (`PocketControls` +0x184) is set by the
panel's buttons and read by `pocket_frame` in the step; the original cleared it
in the drawn frame after its one pass (`pocket_draw`). With the fixed step each
pass clears it itself, so a frame of two steps doesn't skip the second's
picking. The mission's first frame (`start_mission`'s dummy frame) runs on one
step's time and moves the clock's totals on by that step, not by its measured
30 ms sleep, so the steps' clock starts a whole step after the one before it.

A 3D replay (`--replay3d`) runs as before #485, one pass of the lists a drawn
frame with the replay's hooks around it: it simulates nothing (every mech is
posed from the log's time), and its clock, its stop and its benchmark go by
the drawn frame (`replay_hooks.h`).

**Per drawn frame** (the frame time reads the real frame): shadows, the scene
draw, weather, sound, the HUD and the message box, model effects drawn with the
scene (smoke puffs), and the frame's timing in `mw3_main.cpp`.

Not in the mission frame and unchanged: menus, briefing, mech lab, editors,
debug views and the stand-alone replay viewer.

## Drawing between steps

At 144 fps about five frames are drawn per step. Without blending, everything
would move in 30 Hz jumps. `gamez/zclass/interp` keeps each object3d's local
transform (data +0x30) and, while valid, its cached world transform (+0x60)
after every step. Before a frame is drawn it writes each moved node's blend at
`alpha`, how far the frame is towards the next step: position and per-row scale
in a straight line, rotation by quaternion slerp. A node that moved more than
50 m in one step (spawned, placed, a camera cut) is drawn where it is.

Cameras are no object3d: the player's view places its camera in the world
each step (`PlayerView::place`, a position and three angles), so `interp`
records and blends cameras too, through their own setters, angles the short
way round; a turn past 90 degrees in a step is a cut, drawn where it is. Without
this the outside world moved in 30 Hz jumps at any frame rate while the
cockpit model in front of it was blended (#485's shot check: at 7 ms frames
the world changed only on every fifth frame). A camera given a whole matrix is
drawn as it is.

The draw also works out from each camera's place what the simulation reads
afterward: the camera's matrices and world position, the horizon moved to it,
and the zone list the weapons' casts and the turrets start from. From a blended
camera those would differ with the frame rate, so each draw puts every camera's
whole data, the horizon and the zone list back as it found them, and after
each step `prepare_cameras` runs that part of the draw's set-up
(`zcls::camera_prepare`, taken out of `render_world`) for the cameras the last
draw drew, from their exact places, as the original's draw after each of its
frames did. Below 30 fps, when a frame runs two steps, the step between them
gets it too. A return from the pause menu keeps the cameras the last mission
frame drew (`interp::clear(true)`); before the mission's first draw, when no
draw has named its cameras yet, it prepares the cameras on the engine's camera
list (list 8) that have a world and a window with area, which stands in for the
set a draw would draw.

The reticle's zoom window places its camera itself, during the draw (0x004436c0:
at the player camera, turned to the reticle point, in its zone), so it would
follow the drawn (blended) view, and the last camera prepared leaves its zone
list for the weapons' casts. So the HUD places it in each step from the exact
view (`HudZoomWindow::place_camera_pose`, called by `prepare_cameras` through
`interp::set_step_camera_placer` just before it prepares that camera), and each
draw's own placing of it is always put back. Other cameras a draw moves (the
debug and arena cameras, the HUD's MFD views, which draw one model, not the
world) keep their new place, as before; none of them is prepared for the steps.

The camera's move in a draw (`horizon_follow`) also runs the class lists'
frame update (`frame_update`, 0x004f7f70): the sequences and animates by the
timer's dt, then the changed nodes brought current. Between steps that dt is
the drawn frame's, and the sequences and animates are simulation, so a frame
drawn between steps (`set_drawing_between_steps`) runs only the changed nodes;
the steps advance them once each, in `prepare_cameras`. And the changed nodes
are brought current at the end of each step (`settle_world_caches` starts with
`update_changed`), so no draw takes a simulation change off that list and
builds it from blended parents.

Before
the draw every node's local transform, world cache and its data flags word
(the stale flag, and the "local from the angles" flag a node update clears)
are kept, and right after it each node gets them back exactly; a node the draw
moved itself (a camera) keeps its new transform with its cache stale. So the
draws never reach the simulation. The game reads a cached world matrix
whether or not it is marked stale (a vehicle's turret turn reads its turret's),
and the original's draw rebuilt the stale ones after each frame; so at the end
of each step `settle_world_caches` rebuilds them from the exact transforms,
once a step however many frames are drawn. Before this, c2m3 ran differently
at 7 and 33 ms frames: a Harasser's turret turned against a matrix the last
draw had rebuilt from its blended hull. The picture is
up to one step (33 ms) behind the newest simulation state, the usual cost of
this method: at exactly 30 fps each frame shows the step before the newest
(`alpha` 0), where the original drew the newest.

A move marks a node and its subtree changed (node flag 0x2000000, 0x004fb600),
skipping a child that already has the mark, and the renderers clear it on the
nodes they walk. The original cleared it once a frame, after the frame's moves.
Here the draws' clearing is given back (`restore`), and each step's
`settle_world_caches` clears it on every active node in the world tree, so a
frame of two steps and no draw between them (below 30 fps) still marks the
children at the second step's moves. The renderers also refresh each node's
bounding sphere (+0x64..+0x70) and its "sphere stale" bit (+0x2c bit 0) from the
blended place; those are read only by the renderers (the line and sphere queries
work from the node's box and the matrix stack), so they stay as the draw left them.

## Input

The poll runs once at the start of each step, as the original reads input at
30 fps, because it fires the game's command callbacks (fire, target and so on),
which are simulation work. Nothing is lost between steps: the SDL host sums the
mouse's motion between reads and latches buttons pressed in between
(`frontend/sdl/sdl_input.cpp`).

A drawn frame follows none, one or several polls, so drawn-frame code that
checks a key for a fresh press uses `key_pressed_this_frame`, which keeps every
plain key pressed at any poll since the mission frame began (`frame_keys_begin`;
state 1, or 5 for a tap pressed and let go within one poll): the multiplayer
quit box's Escape, Y and N (`quit_box.cpp`), and Escape's stop in the three
drawing paths. Read as the raw state, a press counted on every frame between
two steps at 60 fps and up (the box toggled open and shut) and could be missed
below 30.

The rest of the drawn frame's input, the windows' clicks (`Window::update`), a
command's state (the editor's 0x9b) and every key, reads through
`zin::DrawnFrameInput`, alive for the mission frame's drawing: the keys', the
mouse buttons' and the joystick buttons' states as one poll for the whole frame
would leave them. Each poll keeps its presses and releases (`zin::poll`), and
the view is the last poll's state with every one of the frame's edges added, or
with no poll in the frame the last poll's aged as the next poll would (a press
held, a release up). At one poll a frame it is the polled state itself. After
the frame the polled states come back, except where the drawing changed them.
The SDL host's own command states (`command_state`) latch presses at the host.
The menus poll once a drawn frame and are unchanged.

## Random numbers

The game draws every random number from one MSVCRT-compatible generator
(`crt/msvc_rand`). Drawn-frame code would use more of them at higher frame
rates and so change the simulation's rolls, and runs at different rates could
never match. In fixed mode the drawn-frame part of `CoreState::frame` runs
inside `crt::DrawnFrameRandom`, which switches `msvc_rand()` to a second state
seeded alongside the first. What decides the generator is where the call runs,
not which file it is in. Callers as of #485:

| Caller | Runs |
|---|---|
| `zeffect/zeff_anim_init.cpp` `anim_init` | step |
| `zmodel/gmod_puff.cpp` puff spread | drawn frame |
| `zrender/zrndr_prim2d.cpp` `jitter` | drawn frame |
| `zrender/zrndr_tint.cpp` `finish_init` | load time |
| `zsound/zsnd_cd.cpp` `cue_track` | step (mission scripts) or drawn frame |
| `zsound/zsnd_grp.cpp` `pick` | step or drawn frame (only picks a sound) |
| `ztwod/twod_weather.cpp` | drawn frame |
| `zweapon/zweapon.cpp`, `zwep_beam.cpp`, `zwep_shot.cpp` | step |
| `mech3/app_hooks.cpp` `cursor_pos` | step (input poll) |
| `mech3/app_mech.cpp` salvage, `mech3/app_mission.cpp` `action_field` | step |
| `mech3/hud.cpp` `Hud::add_static` | drawn frame |
| `mech3/mech.cpp`, `mech_parts.cpp`, `mech_move.cpp`, `mech_skin.cpp`, `mech_skis.cpp`, `mech_fieldbase_cut.cpp`, `weapon.cpp`, `zai_brain.cpp` | step |

A sound or HUD pick that runs in the drawn frame only changes what is heard or
shown, never the simulation.

## Frame counters

The engine's frame number (`zcls::frames().frame`, exe 0x0072f338) still goes
up once per drawn world frame, as the original's camera draw counts it; the
materials' texture cycles, the camera's sound listener and the debug views use
it. A second counter, `zcls::frames().step`, goes up at the start of each step
(`poll_and_run_lists`). Simulation work the original timed "once a frame"
counts steps: the vehicles' and turrets' frame numbers, the mech's sunlight
shade turns, the network collision check and the texture scroll
(`model_scroll_tick`). On the drawn-frame counter these ran once per drawn
frame, so at 15 fps (two steps a frame) the horizon scrolled at half speed.
The nodes' changed stamps (node +0xc4: changed until then, `frames().expiry`)
count steps too: the shots' static hits (`zwep_shot.cpp`, the static-only
queries in `cls_di.cpp`) read them, so a node is static once unchanged for 160
steps (5.3 s, as at the exe's 30 fps) at any frame rate; the static lighting
bake (`gmod_draw.cpp`) reads the same stamps. On drawn frames a shot fired at
20 fps found other static hits than at 30 (#485's c2m1 runs).

## Tests

The whole-mission tests drive the game through `GameEngine::on_present` and
count its calls as the game's ticks. Their clock (`FakeClock`) moves on each
time the game reads it, so a drawn frame runs one step or several depending on
how busy the scene is. A test that counts ticks makes a `PresentOnSteps`
(tests/program_harness.h): the engine made in it then calls `on_present` after
each mission step (`after_each_step` in `fixed_step.h`) instead of after each
frame drawn in a mission, so each call is exactly 1/30 s. Outside a mission
(menus, loading, the fade in) it still runs after each frame drawn. Such tests
stop on their step count (`pump.stop`), the pump's pass limit only a ceiling.
`MW3_VARIABLE_STEP=1` runs the whole test program with one step per drawn frame,
as `--variable-step` does.

## Switches

- `--variable-step`: one simulation step per drawn frame with the frame's own
  time, as before #485, for side-by-side comparison.
- `--frame-ms N`: each drawn frame is N ms of game clock; the 1/30 s steps run
  underneath, so `--frame-ms 7` simulates exactly like a 144 fps player and
  repeats (scripted inputs such as `--tap DIK@N` still count drawn frames). The step is exactly 1/30 s, so a `--frame-ms 33` run (0.033 s
  frames) runs no step on about one frame in a hundred.
- `--step-log FILE`: one record per step (a hash of every object's local
  transform, a mech's limbs under their live nodes included, then each
  vehicle's position, forward row and supports in the air). Runs that simulate
  alike write the same file at any frame rate.
