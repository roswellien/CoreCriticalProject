#include "gamez/zmodel/gmod_fog.h"

#include <algorithm>

#include "gamez/zclass/visual_distance.h"

#include "gamez/zrender/zrndr_fog.h"

namespace zmod {

namespace {
Fog g_fog;
// The innermost active extended-view copy and its far ratio; null/1 at the original range.
Fog* g_render_fog = nullptr;
float g_render_scale = 1.0f;
float g_render_far = 0.0f;  // the active copy's visual far plane; 0 at the original range

// How far before the visual far plane linear fog must already have started. World geometry stops
// at that plane, and the owner's playtests found it pops in visibly unless the fog begins about
// 200 units before it at 1200 and about 100 units before it at 1600.
float fog_cover_band(float visual_far) { return visual_far > 1200.0f ? 100.0f : 200.0f; }

// Stretch only the distance interval by the visual/authored far ratio. On/off, mode, colour and
// the altitude taper stay as authored. Always built from the authored fog, never from an outer
// copy, so the HUD zoom view (drawn inside the main world render) is not scaled twice.
Fog scaled_fog(const Fog& source, float scale, float visual_far) {
  Fog copy = source;
  copy.near_range *= scale;
  copy.far_range *= scale;
  // Linear fog that reaches the edge of the view must hide where world geometry ends: it is full
  // at the visual far plane and starts at the cover band before it. A mission whose fog already
  // ends well short of the edge (a deliberately foggy map) keeps its own scaled interval.
  const float cover_start = visual_far - fog_cover_band(visual_far);
  const bool fog_reaches_edge = copy.far_range >= cover_start;
  if (copy.linear && fog_reaches_edge) {
    copy.near_range = cover_start;
    copy.far_range = visual_far;
  }
  copy.near_sq = copy.near_range * copy.near_range;
  copy.far_sq = copy.far_range * copy.far_range;
  const float range = copy.far_range - copy.near_range;
  // A collapsed interval keeps the inverse its setters left behind (as the original does); scale
  // that kept value with the interval so the copy stays consistent with the authored fog.
  if (range != 0.0f)
    copy.inv_range = 1.0f / range;
  else
    copy.inv_range /= scale;
  if (!copy.linear) copy.density /= scale;
  return copy;
}

// Setters always write the authored state (as the original game does); an active copy then
// follows it, so gameplay readers and the render copy never disagree.
void refresh_render_fog() {
  if (g_render_fog) *g_render_fog = scaled_fog(g_fog, g_render_scale, g_render_far);
}
}  // namespace

Fog& fog() { return g_fog; }
const Fog& render_fog() { return g_render_fog ? *g_render_fog : g_fog; }

ScopedRenderFog::ScopedRenderFog(float authored_far, float visual_far) {
  if (!(authored_far > 0.0f) || !(visual_far > authored_far)) return;
  previous_ = g_render_fog;
  previous_scale_ = g_render_scale;
  previous_far_ = g_render_far;
  g_render_scale = visual_far / authored_far;
  g_render_far = visual_far;
  copy_ = scaled_fog(g_fog, g_render_scale, g_render_far);
  g_render_fog = &copy_;
  active_ = true;
}

ScopedRenderFog::~ScopedRenderFog() {
  if (!active_) return;
  g_render_fog = previous_;
  g_render_scale = previous_scale_;
  g_render_far = previous_far_;
  // Fog set while this inner scope was active must reach the outer copy too.
  refresh_render_fog();
}

// Mech3.exe 1.2 @ 0x00526b80
void fog_set_on(int32_t on) {
  g_fog.on = on;
  refresh_render_fog();
}

// Mech3.exe 1.2 @ 0x00526ce0
void fog_set_linear(int32_t linear) {
  g_fog.linear = linear;
  refresh_render_fog();
}

// Mech3.exe 1.2 @ 0x00526cd0
void fog_set_density(float density) {
  g_fog.density = density;
  refresh_render_fog();
}

// Mech3.exe 1.2 @ 0x00526cf0
void fog_set_color(const float rgb[3]) {
  for (int i = 0; i < 3; ++i) g_fog.color[i] = rgb[i];
  refresh_render_fog();
  zrndr::device_fog_color(rgb);
}

// Mech3.exe 1.2 @ 0x00526ba0. The inverse keeps its old value when the range is empty.
void fog_set_near(float range) {
  g_fog.near_range = range;
  g_fog.near_sq = range * range;
  if (g_fog.far_range - range != 0.0f) g_fog.inv_range = 1.0f / (g_fog.far_range - range);
  refresh_render_fog();
}

// Mech3.exe 1.2 @ 0x00526c00
void fog_set_far(float range) {
  g_fog.far_range = range;
  g_fog.far_sq = range * range;
  if (range - g_fog.near_range != 0.0f) g_fog.inv_range = 1.0f / (range - g_fog.near_range);
  refresh_render_fog();
}

// Mech3.exe 1.2 @ 0x00526c50
void fog_set_alt_high(float alt) {
  g_fog.alt_high = alt;
  if (alt - g_fog.alt_low != 0.0f) g_fog.inv_alt = 1.0f / (alt - g_fog.alt_low);
  refresh_render_fog();
}

// Mech3.exe 1.2 @ 0x00526c90
void fog_set_alt_low(float alt) {
  g_fog.alt_low = alt;
  if (g_fog.alt_high - alt != 0.0f) g_fog.inv_alt = 1.0f / (g_fog.alt_high - alt);
  refresh_render_fog();
}

// Mech3.exe 1.2 @ 0x00526de0
void fog_apply() { zrndr::set_fog_color(g_fog.color); }

void fog_frame_fill(uint8_t* r, uint8_t* g, uint8_t* b) {
  const auto byte = [](float v) { return static_cast<uint8_t>(std::clamp(v, 0.0f, 1.0f) * 255.0f); };
  *r = g_fog.on ? byte(g_fog.color[0]) : 0;
  *g = g_fog.on ? byte(g_fog.color[1]) : 0;
  *b = g_fog.on ? byte(g_fog.color[2]) : 0;
}

}  // namespace zmod
