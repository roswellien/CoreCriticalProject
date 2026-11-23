#pragma once

// Ours (#287, the arena's spectator seat): a spectator's launch makes no
// player mech. launch_player then does only the work that does not need one
// (the session's player data, the pilot save, the camera that is the sound
// listener), the Core state does not leave for the menu over the missing
// vehicle, and the player tick skips its vehicle calls. Set by
// GameEngine::set_launch from Launch::spectator; false for every other launch.
//
// A header of its own, with no includes, so files whose headers clash with
// mission_launch.h's mech headers (app_states.cpp with pilot.h) can use it.
// Defined in mission_launch.cpp.

namespace mech3 {

void set_launch_spectator(bool spectator);
bool launch_spectator();

}  // namespace mech3
