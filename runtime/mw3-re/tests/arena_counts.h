#pragma once

#include <nlohmann-json/json.hpp>

// #287: what the headless arena runs in test_program.cpp count about a
// match's mechs. Defined in test_arena.cpp, which can include mech.h (the
// program tests' own Handle type clashes with it).

namespace mech3 {
struct Mech;
}

namespace arena_counts {

// From begin() to end(): every shot fired and hit taken by an arena mech,
// counted per side through the weapon and damage calls the game makes.
void begin();
void end();
int shots(int side);
int hits(int side);

// Mech `id`'s pose read straight from the mech, rounded as the log rounds:
// {"t": the match time, "mech": {pos, heading, torso, arms, anim, jumping,
// fallen, heat}}. Independent of the log's own code, so a test can check the
// log against it.
nlohmann::json live_pose(int id);

bool standing(const mech3::Mech* mech);  // arena_standing: not destroyed or dying
bool is_bot(const mech3::Mech* mech);    // Mech::arena_bot

}  // namespace arena_counts
