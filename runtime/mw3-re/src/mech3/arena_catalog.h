#pragma once

#include <string>

// Ours (#287, docs/arena.md "Arena runner"): `mw3 GAME --arena-catalog DIR`
// writes what the arena runner's window offers, read from the player's own
// game files, so its lists never drift from what the game can run:
//
//   DIR/catalog.json      maps, mechs with their stock loadouts, pilot presets
//   DIR/terrain/<map>.ppm and <map>.json   each map seen from above, placed
//   DIR/mechs/<mech>.ppm  the mech lab's picture of each chassis
//
// Nothing here is committed: the files hold the game's own data and stay on
// the player's machine (docs/legal.md). PPM because tkinter reads it with no
// add-ons and SDL3 writes no PNG.
namespace mech3::arena {

// Needs the install mounted (zutl), nothing else: no window, engine or
// mission. False with *error naming what could not be written.
bool write_arena_catalog(const std::string& dir, std::string* error);

}  // namespace mech3::arena
