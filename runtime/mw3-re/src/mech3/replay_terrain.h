#pragma once
#include <cstdint>
#include <string>
#include <vector>

// Ours (#289): an arena map seen from above, for the replay viewer. Built
// from the world's own triangles (world_mesh.h's load_world, the loader
// mw3view uses), not from the game engine, so a replay needs no match and no
// mission. Heights from raw triangles can differ a little from the AI's walk
// grid; this is for orientation only.
namespace mech3::replay {

struct Terrain {
  // Cell (col, row) covers x from x0 + col * cell and z down from
  // z_top - row * cell: row 0 is the top of the picture (the largest z), as
  // the viewer draws it with z up the screen.
  float x0 = 0, z_top = 0, cell = 1;
  int width = 0, height = 0;
  std::vector<float> heights;  // width * height, meters
  std::vector<uint8_t> rgba;   // width * height * 4: height colors times hill shade
  std::vector<uint8_t> outline;  // width * height, 1 where the ground steps more than 3 m
  std::string error;           // empty on success
};

// The largest side of the grid in cells; a bigger box gets bigger cells.
constexpr int kMaxTerrainCells = 4096;

// `map` is the start line's lobby map id ("c1mp1"); `box` is min x, min z,
// max x, max z of what to show (grown by 100 m), or min > max for the whole
// world. Needs the install mounted (zutl). On failure, `error` says why and
// the rest is empty.
Terrain build_terrain(const std::string& map, const float box[4]);

// Walls and cliffs (outline cells) drawn near-black in rgba, as every picture
// of the terrain shows them (the viewer's texture, the arena catalog's).
void darken_outline(Terrain* terrain);

}  // namespace mech3::replay
