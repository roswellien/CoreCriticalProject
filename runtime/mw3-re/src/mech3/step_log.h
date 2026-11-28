#pragma once
#include <string>

// Ours (#485): mw3 --step-log <file>. One record per simulation step: a hash
// of every object3d's local transform (the node table's live ones and the
// children hung under them outside it, a mech's limbs), then a line per vehicle that
// moved in the step (its world position, its forward row and how many of its
// supports are in the air). Two runs that simulate alike write the same file
// whatever their frame rate, so a byte compare shows it (docs/fixed-step.md).
namespace mech3 {

struct BasicVehicle;

bool step_log_open(const std::string& path);
bool step_log_on();
// From vehicle_move, once the vehicle has stepped.
void step_log_vehicle(const BasicVehicle& v);
// At the end of each simulation step (world_tick).
void step_log_end_step();

}  // namespace mech3
