#include "gamez/zmodel/gmod_fog.h"

#include <algorithm>

#include "gamez/zclass/visual_distance.h"

#include "gamez/zrender/zrndr_fog.h"

namespace zmod {

namespace {
Fog g_fog;
unsigned g_render_fog_distance{};
// The innermost active world-render copy and its far ratio; null/1 outside render scopes.
Fog* g_render_fog = nullptr;
float g_render_scale = 1.0f;
float g_render_far = 0.0f;  // the active copy's visual far plane; 0 only when no scope is active

// Stretch only the distance interval by the visual/authored far ratio. On/off, mode, colour and
// the altitude taper stay as authored. Always built from the authored fog, never from an outer
// copy, so the HUD zoom view (drawn inside the main world render) is not scaled twice.
Fog scaled_fog(const Fog& source, float scale, float visual_far) {
  Fog copy = source;
  if (g_render_fog_distance && source.on && source.linear &&
      source.far_range > source.near_range && source.far_range > 0.0f)
    scale = static_cast<float>(g_render_fog_distance) / source.far_range;
  copy.near_range *= scale;
  copy.far_range *= scale;
  // Preserve proportional haze, including missions that become opaque before the edge.
  // Only an interval ending beyond the cut needs capping. In that case the table is a
  // lower bound on the strong-fog start, avoiding unnecessarily dense replacement fog.
  const float cover_start = zcls::fog_start_for_view_distance(visual_far);
  if (copy.linear && copy.far_range > visual_far) {
    copy.near_range = std::clamp(copy.near_range, cover_start, visual_far);
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

void set_render_fog_distance(unsigned distance) { g_render_fog_distance = distance; }
Fog& fog() { return g_fog; }
const Fog& render_fog() { return g_render_fog ? *g_render_fog : g_fog; }
RenderFogEdge render_fog_edge() {
  if (!g_render_fog) return {};
  const float start = zcls::fog_start_for_view_distance(g_render_far);
  return {start, 1.0f / (g_render_far - start)};
}
bool render_fog_active() { return render_fog().on || g_render_fog != nullptr; }
const float* render_fog_color() { return render_fog().color; }

ScopedRenderFog::ScopedRenderFog(float authored_far, float visual_far) {
  bool supported_identity = false;
  for (const auto& option : zcls::kViewDistanceOptions) {
    if (visual_far == static_cast<float>(option.view_distance)) supported_identity = true;
  }
  const bool covers_authored_edge = visual_far == authored_far && supported_identity;
  if (!(authored_far > 0.0f) || (!(visual_far > authored_far) && !covers_authored_edge)) return;
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
