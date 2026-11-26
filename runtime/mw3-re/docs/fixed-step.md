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
vehicles, turrets, sequences, effect animations, mission objects); the replay
hooks around them; `world_tick` (sensors, missions, the pilot, the camera); the
clock copies `sync_frame_step` makes for the mech, weapon and hit modules; and
the step log.

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
50 m in one step (spawned, placed, a camera cut) is drawn where it is. Right
after the draw the exact transforms go back, and every world cache that was
stale before the draw is marked stale again (the draw rebuilds those from the
blended chain), so the simulation never reads a blended value. The picture is
up to one step (33 ms) behind the newest simulation state, the usual cost of
this method.

## Input

The poll runs once at the start of each step, as the original reads input at
30 fps, because it fires the game's command callbacks (fire, target and so on),
which are simulation work. Nothing is lost between steps: the SDL host sums the
mouse's motion between reads and latches buttons pressed in between
(`frontend/sdl/sdl_input.cpp`).

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

## Switches

- `--variable-step`: one simulation step per drawn frame with the frame's own
  time, as before #485, for side-by-side comparison.
- `--frame-ms N`: each drawn frame is N ms of game clock; the 1/30 s steps run
  underneath, so `--frame-ms 7` plays exactly like a 144 fps player and
  repeats. The step is exactly 1/30 s, so a `--frame-ms 33` run (0.033 s
  frames) runs no step on about one frame in a hundred.
- `--step-log FILE`: one record per step (a hash of every object's local
  transform, then each vehicle's position, forward row and supports in the
  air). Runs that simulate alike write the same file at any frame rate.
