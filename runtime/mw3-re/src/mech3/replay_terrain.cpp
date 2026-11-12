#include "mech3/replay_terrain.h"

#include <algorithm>
#include <cmath>

#include "mech3/arena_setup.h"
#include "mech3/world_mesh.h"

namespace mech3::replay {

namespace {

constexpr float kMargin = 100.0f;    // meters shown around the logged box
constexpr float kStepOutline = 3.0f;  // meters between neighbors that count as a wall or cliff
constexpr float kNoHeight = -1e30f;

// Every visible ground or building triangle drawn top-down into the grid,
// keeping the highest surface in each cell (a roof over the floor under it).
void rasterize(const viewer::Vertex& a, const viewer::Vertex& b, const viewer::Vertex& c, Terrain* t) {
  const float ax = a.pos[0], az = a.pos[2], bx = b.pos[0], bz = b.pos[2], cx = c.pos[0], cz = c.pos[2];
  const float area = (bx - ax) * (cz - az) - (cx - ax) * (bz - az);
  if (std::abs(area) < 1e-6f) return;  // seen edge-on from above: a wall, drawn by the outline instead
  const float min_x = std::min({ax, bx, cx}), max_x = std::max({ax, bx, cx});
  const float min_z = std::min({az, bz, cz}), max_z = std::max({az, bz, cz});
  const int col0 = std::max(0, static_cast<int>(std::floor((min_x - t->x0) / t->cell)));
  const int col1 = std::min(t->width - 1, static_cast<int>(std::floor((max_x - t->x0) / t->cell)));
  const int row0 = std::max(0, static_cast<int>(std::floor((t->z_top - max_z) / t->cell)));
  const int row1 = std::min(t->height - 1, static_cast<int>(std::floor((t->z_top - min_z) / t->cell)));
  for (int row = row0; row <= row1; ++row) {
    const float z = t->z_top - (static_cast<float>(row) + 0.5f) * t->cell;
    for (int col = col0; col <= col1; ++col) {
      const float x = t->x0 + (static_cast<float>(col) + 0.5f) * t->cell;
      // Barycentric weights of the cell's center in the triangle.
      const float wb = ((x - ax) * (cz - az) - (cx - ax) * (z - az)) / area;
      const float wc = ((bx - ax) * (z - az) - (x - ax) * (bz - az)) / area;
      const float wa = 1.0f - wb - wc;
      if (wa < 0 || wb < 0 || wc < 0) continue;
      const float y = wa * a.pos[1] + wb * b.pos[1] + wc * c.pos[1];
      float& cell = t->heights[static_cast<size_t>(row) * t->width + col];
      cell = std::max(cell, y);
    }
  }
}

// Low ground dark green, high ground light brown.
void height_color(float f, uint8_t rgb[3]) {
  static const float kLow[3] = {46, 74, 42}, kHigh[3] = {196, 176, 136};
  for (int i = 0; i < 3; ++i) rgb[i] = static_cast<uint8_t>(kLow[i] + (kHigh[i] - kLow[i]) * f);
}

// The usual GIS hill shade: light from the northwest (azimuth 315 degrees,
// 45 degrees up), from the slope between the cell's neighbors.
float hill_shade(const Terrain& t, int col, int row) {
  const auto h = [&](int c, int r) {
    c = std::clamp(c, 0, t.width - 1), r = std::clamp(r, 0, t.height - 1);
    return t.heights[static_cast<size_t>(r) * t.width + c];
  };
  const float dx = (h(col + 1, row) - h(col - 1, row)) / (2 * t.cell);
  const float dz = (h(col, row - 1) - h(col, row + 1)) / (2 * t.cell);  // row up is +z
  const float slope = std::atan(std::sqrt(dx * dx + dz * dz));
  const float aspect = std::atan2(dz, -dx);
  const float zenith = 45.0f * 0.0174533f, azimuth = (360.0f - 315.0f + 90.0f) * 0.0174533f;
  const float shade = std::cos(zenith) * std::cos(slope) + std::sin(zenith) * std::sin(slope) * std::cos(azimuth - aspect);
  return std::clamp(0.35f + 0.65f * shade, 0.0f, 1.0f);
}

}  // namespace

Terrain build_terrain(const std::string& map, const float box[4]) {
  Terrain t;
  std::string dir;
  int32_t number = 0;
  // Only a known world folder reaches a path, so a log can't send the loader elsewhere.
  if (!arena::split_map(map, &dir, &number)) {
    t.error = "unknown map " + map;
    return t;
  }
  viewer::Scene scene;
  const std::string load_error = viewer::load_world("zbd", dir, scene);
  if (!load_error.empty()) {
    t.error = load_error;
    return t;
  }
  float x_min = box[0], z_min = box[1], x_max = box[2], z_max = box[3];
  if (x_min > x_max || z_min > z_max) x_min = scene.min[0], z_min = scene.min[2], x_max = scene.max[0], z_max = scene.max[2];
  x_min -= kMargin, z_min -= kMargin, x_max += kMargin, z_max += kMargin;
  const float longest = std::max(x_max - x_min, z_max - z_min);
  t.cell = std::max(1.0f, longest / static_cast<float>(kMaxTerrainCells));
  t.width = std::max(1, static_cast<int>(std::ceil((x_max - x_min) / t.cell)));
  t.height = std::max(1, static_cast<int>(std::ceil((z_max - z_min) / t.cell)));
  t.x0 = x_min, t.z_top = z_max;
  const size_t cells = static_cast<size_t>(t.width) * t.height;
  t.heights.assign(cells, kNoHeight);
  for (const viewer::Batch& batch : scene.batches) {
    if (batch.marker || batch.sky) continue;  // bounds markers and the sky aren't ground
    for (size_t v = 0; v + 2 < batch.vertices.size(); v += 3)
      rasterize(batch.vertices[v], batch.vertices[v + 1], batch.vertices[v + 2], &t);
  }
  float low = 1e30f, high = -1e30f;
  for (const float y : t.heights)
    if (y != kNoHeight) low = std::min(low, y), high = std::max(high, y);
  if (low > high) low = high = 0;
  for (float& y : t.heights)
    if (y == kNoHeight) y = low;  // nothing there: the lowest ground seen
  t.rgba.resize(cells * 4);
  t.outline.assign(cells, 0);
  const float range = std::max(high - low, 1.0f);
  for (int row = 0; row < t.height; ++row)
    for (int col = 0; col < t.width; ++col) {
      const size_t i = static_cast<size_t>(row) * t.width + col;
      uint8_t rgb[3];
      height_color((t.heights[i] - low) / range, rgb);
      const float shade = hill_shade(t, col, row);
      for (int k = 0; k < 3; ++k) t.rgba[i * 4 + k] = static_cast<uint8_t>(rgb[k] * shade);
      t.rgba[i * 4 + 3] = 255;
      const float here = t.heights[i];
      const bool right = col + 1 < t.width && std::abs(t.heights[i + 1] - here) > kStepOutline;
      const bool below = row + 1 < t.height && std::abs(t.heights[i + t.width] - here) > kStepOutline;
      if (right || below) t.outline[i] = 1;
    }
  return t;
}

}  // namespace mech3::replay
