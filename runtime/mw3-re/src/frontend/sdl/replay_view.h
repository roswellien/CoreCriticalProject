#pragma once
#include <string>

namespace sdlfe {

// Ours (#289 step 2): `mw3 GAME_DIR --replay <log>`, an arena match log played
// back on the map seen from above, in its own SDL window (docs/arena.md,
// Watching a match). Runs with the install mounted and nothing else started:
// no engine, mission, match or network. Returns the process exit code: 0 when
// the window is closed, 2 when the log is refused.
//
// `script_path`, when not empty, is a test script that drives the viewer
// through its own event queue, in a hidden window, so the controls can be
// checked without input to the desktop. One command a line, run in order:
//   wait SECONDS          let replay time run: SECONDS * 60 frames of 1/60 s
//                         each at the current speed, so a script plays the same
//                         however fast the machine draws
//   key NAME              space, left, right, comma, period, 1 to 5, escape
//   click X Y             a left click at window pixel X Y
//   drag X0 Y0 X1 Y1      a left drag
//   wheel X Y STEPS       wheel steps at X Y (positive zooms in)
//   shot FILE.bmp         save the window as it is now
//   quit                  close the viewer
// The 3D replay (--replay3d) reads the same script, plus:
//   seek SECONDS          jump to that replay time
//   camera X Y Z YAW PITCH  place the free camera
//   follow ID             follow mech ID from behind (-1 lets go)
int run_replay(const std::string& log_path, const std::string& script_path = "");

}  // namespace sdlfe
