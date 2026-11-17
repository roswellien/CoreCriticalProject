#include "check.h"

#include "frontend/sdl/draw_distance_option.h"
#include "gamez/zclass/camera.h"
#include "gamez/zclass/cls_data.h"
#include "gamez/zmodel/gmod_fog.h"
#include "mech3/mech_lod.h"

#include <cmath>
#include <cstdint>
#include <cstring>
#include <iterator>
#include <limits>

namespace {
mech3::Mech* g_lod_test_target = nullptr;

mech3::Mech* lod_test_player_target(mech3::Mech&) {
  return g_lod_test_target;
}

uint32_t mech_detail(unsigned selected_far, float distance, bool targeted,
                     bool has_contact = true) {
  const unsigned previous_far = zcls::visual_far_request();
  zcls::set_visual_far_request(selected_far);
  mech3::World& mech_world = mech3::world();
  mech3::Mech* previous_player = mech_world.mission_player;
  mech3::LodCalls& calls = mech3::lod_calls();
  const mech3::LodCalls previous_calls = calls;
  const int32_t previous_spent = mech3::lod_spent();

  mech3::Mech player;
  mech3::Mech mech;
  mech3::MechData data;
  mech3::ai::Contact contact;
  data.range_sq[0] = std::numeric_limits<float>::max();
  data.range_sq[1] = 0.0f;
  mech.pilot = &data;
  contact.dist2 = distance * distance;
  mech.player_contact = has_contact ? &contact : nullptr;
  player.target = targeted ? &contact : nullptr;
  mech_world.mission_player = &player;
  g_lod_test_target = targeted ? &mech : nullptr;
  calls = mech3::LodCalls{};
  calls.player_target = lod_test_player_target;
  mech3::lod_spent() = 0;

  mech3::lod_update(mech);
  const uint32_t detail = mech.detail;

  mech3::lod_spent() = previous_spent;
  calls = previous_calls;
  mech_world.mission_player = previous_player;
  g_lod_test_target = nullptr;
  zcls::set_visual_far_request(previous_far);
  return detail;
}
}  // namespace

TEST(view_distance_cli_options) {
  unsigned distance = 0;
  EXPECT(sdlfe::parse_draw_distance("800", &distance) && distance == 800);
  EXPECT(sdlfe::parse_draw_distance("1200", &distance) && distance == 1200);
  EXPECT(sdlfe::parse_draw_distance("1600", &distance) && distance == 1600);
  EXPECT(sdlfe::parse_draw_distance("2400", &distance) && distance == 2400);
  EXPECT(sdlfe::parse_draw_distance("3200", &distance) && distance == 3200);
  EXPECT(!sdlfe::parse_draw_distance("1000", &distance));
  EXPECT(!sdlfe::parse_draw_distance("0800", &distance));
  EXPECT(!sdlfe::parse_draw_distance("", &distance));
  EXPECT(!sdlfe::parse_draw_distance("1200junk", &distance));
  EXPECT(!sdlfe::parse_draw_distance(nullptr, &distance));
}

TEST(view_distance_controls_far_mech_detail) {
  constexpr unsigned distances[] = {799, 801, 1199, 1201, 1599, 1601, 2399, 2401, 3199, 3201};
  constexpr unsigned settings[] = {800, 1200, 1600, 2400, 3200};
  EXPECT(zcls::visual_far_request() == zcls::kDefaultVisualFar);
  for (const unsigned selected_far : settings) {
    for (const unsigned distance : distances) {
      const uint32_t expected_detail = distance < selected_far ? 0x10u : 0u;
      EXPECT(mech_detail(selected_far, static_cast<float>(distance), false) ==
             expected_detail);
    }
    EXPECT(mech_detail(selected_far, static_cast<float>(selected_far + 1), true) ==
           0x10u);
    EXPECT(mech_detail(selected_far, 0.0f, false, false) == 0u);
  }
}

TEST(view_distance_policy_and_authored_clip) {
  EXPECT(zcls::visual_far(800.0f, 800, true) == 800.0f);
  EXPECT(zcls::visual_far(800.0f, 1200, true) == 1200.0f);
  EXPECT(zcls::visual_far(2000.0f, 1200, true) == 2000.0f);
  EXPECT(zcls::visual_far(800.0f, 1600, false) == 800.0f);

  zcls::Camera camera{};
  camera.put(0xb0, 1.0f);
  camera.put(0xb4, 800.0f);
  const float reader_far = zcls::visual_far(camera.get<float>(0xb4), 1200, true);
  EXPECT(reader_far == 1200.0f);
  EXPECT(camera.get<float>(0xb4) == 800.0f);
}

TEST(view_distance_scales_render_lod_ranges_only) {
  struct Case {
    unsigned requested_far;
    float expected_scale;
  };
  constexpr Case cases[] = {{800, 1.0f}, {1200, 1.5f}, {1600, 2.0f}};
  constexpr float authored_tree_lod_far = 400.0f;
  for (const auto& test : cases) {
    const float scale =
        zcls::visual_distance_scale(800.0f, test.requested_far, true);
    EXPECT(scale == test.expected_scale);
    EXPECT(zcls::visual_distance_scale(800.0f, test.requested_far, false) ==
           1.0f);
    EXPECT(zcls::visual_distance_scale(1800.0f, test.requested_far, true) ==
           1.0f);
    EXPECT(authored_tree_lod_far * scale == 400.0f * test.expected_scale);
  }
  EXPECT(zcls::visual_distance_scale(0.0f, 1600, true) == 1.0f);

  EXPECT(zcls::visual_far_corners_need_update(true, 800.0f, 0.0f));
  EXPECT(zcls::visual_far_corners_need_update(false, 1200.0f, -800.0f));
  EXPECT(!zcls::visual_far_corners_need_update(false, 1200.0f, -1200.0f));
  EXPECT(zcls::visual_far_corners_need_update(false, 800.0f, -1200.0f));

  zcls::Camera camera{};
  camera.put(0xb4, 800.0f);
  (void)zcls::visual_distance_scale(camera.get<float>(0xb4), 1600, true);
  EXPECT(camera.get<float>(0xb4) == 800.0f);
}

TEST(view_distance_scales_partition_fade_ranges) {
  constexpr float near_squared = 25.0f;
  constexpr float far_squared = 100.0f;
  constexpr float interpolation_factor = 1.0f / 75.0f;

  const float world_scale = zcls::visual_distance_scale(800.0f, 1600, true);
  const zcls::SquaredFadeRange expanded = zcls::scale_squared_fade_range(
      near_squared, far_squared, interpolation_factor, world_scale);
  EXPECT(expanded.near_squared == 100.0f);
  EXPECT(expanded.far_squared == 400.0f);
  EXPECT(std::abs(expanded.interpolation_factor - 1.0f / 300.0f) < 1e-8f);

  const float other_camera_scale =
      zcls::visual_distance_scale(800.0f, 1600, false);
  const zcls::SquaredFadeRange unchanged = zcls::scale_squared_fade_range(
      near_squared, far_squared, interpolation_factor, other_camera_scale);
  EXPECT(unchanged.near_squared == near_squared);
  EXPECT(unchanged.far_squared == far_squared);
  EXPECT(unchanged.interpolation_factor == interpolation_factor);
}

TEST(view_distance_scoped_fog) {
  const zmod::Fog saved = zmod::fog();
  zmod::Fog initial{};
  initial.on = 1;
  initial.linear = 1;
  initial.color[0] = 0.2f;
  initial.color[1] = 0.4f;
  initial.color[2] = 0.6f;
  initial.near_range = 100.0f;
  initial.near_sq = 10000.0f;
  initial.far_range = 700.0f;
  initial.far_sq = 490000.0f;
  initial.inv_range = 1.0f / 600.0f;
  initial.alt_high = 80.0f;
  initial.alt_low = 20.0f;
  initial.inv_alt = 1.0f / 60.0f;
  initial.density = 0.75f;
  zmod::fog() = initial;
  {
    zmod::Fog short_fog = initial;
    short_fog.far_range = 600.0f;
    short_fog.far_sq = 360000.0f;
    short_fog.inv_range = 1.0f / 500.0f;
    zmod::fog() = short_fog;
    zmod::ScopedRenderFog identity_scope(800.0f, 800.0f);
    EXPECT(std::memcmp(&zmod::render_fog(), &short_fog, sizeof(short_fog)) == 0);
  }
  zmod::fog() = initial;
  {
    zmod::ScopedRenderFog scope(800.0f, 1600.0f);
    const zmod::Fog& render = zmod::render_fog();
    EXPECT(render.on == initial.on && render.linear == initial.linear);
    EXPECT(std::memcmp(render.color, initial.color, sizeof(initial.color)) == 0);
    EXPECT(render.near_range == 200.0f && render.near_sq == 40000.0f);
    EXPECT(render.far_range == 1400.0f && render.far_sq == 1960000.0f);
    EXPECT(std::abs(render.inv_range - 1.0f / 1200.0f) < 1e-9f);
    EXPECT(render.alt_high == initial.alt_high && render.alt_low == initial.alt_low &&
           render.inv_alt == initial.inv_alt);
    EXPECT(zmod::fog().far_range == initial.far_range);
  }
  initial.linear = 0;
  zmod::fog() = initial;
  {
    zmod::ScopedRenderFog scope(800.0f, 1600.0f);
    EXPECT(zmod::render_fog().linear == 0);
    EXPECT(zmod::render_fog().density == 0.375f);
  }
  EXPECT(zmod::render_fog().far_range == initial.far_range);
  zmod::fog() = saved;
}

TEST(view_distance_tiler_capacity) {
  static zcls::SceneWalk walk{};
  const size_t ring_capacity = std::size(walk.rings);
  const size_t cells_per_ring = std::size(walk.rings[0].cell);
  EXPECT(ring_capacity == 256);
  EXPECT(cells_per_ring == 128);
  for (size_t ring = 0; ring < ring_capacity; ++ring) {
    walk.rings[ring].count = 0;
    for (size_t cell = 0; cell < cells_per_ring; ++cell) {
      auto& output = walk.rings[ring].cell[walk.rings[ring].count++];
      output.x = static_cast<int32_t>(ring);
      output.z = static_cast<int32_t>(cell);
    }
    EXPECT(walk.rings[ring].count == static_cast<int32_t>(cells_per_ring));
  }
}

// The HUD zoom view renders inside the main world render, so its fog scope nests. Each scope
// must scale the authored fog by its own ratio, and fog set during a scope (a world node pushes
// fog while being drawn) must reach both the authored state and every active copy.
TEST(view_distance_nested_fog_and_setters) {
  const zmod::Fog saved = zmod::fog();
  zmod::Fog initial{};
  initial.on = 1;
  initial.linear = 1;
  initial.near_range = 100.0f;
  initial.near_sq = 10000.0f;
  initial.far_range = 700.0f;
  initial.far_sq = 490000.0f;
  initial.inv_range = 1.0f / 600.0f;
  zmod::fog() = initial;
  {
    zmod::ScopedRenderFog world(800.0f, 1600.0f);
    EXPECT(zmod::render_fog().far_range == 1400.0f);
    {
      zmod::ScopedRenderFog zoom(800.0f, 1200.0f);
      // Scaling the authored 700 by 1.5 reaches the 1200 view's table start, covering the edge.
      EXPECT(zmod::render_fog().near_range == 1050.0f && zmod::render_fog().far_range == 1200.0f);
      zmod::fog_set_far(800.0f);
      zmod::fog_set_on(0);
      EXPECT(zmod::fog().far_range == 800.0f && zmod::fog().on == 0);
      EXPECT(zmod::render_fog().far_range == 1200.0f && zmod::render_fog().on == 0);
    }
    // The outer copy follows what was set while the zoom scope was active.
    EXPECT(zmod::render_fog().far_range == 1600.0f && zmod::render_fog().on == 0);
  }
  EXPECT(&zmod::render_fog() == &zmod::fog());
  EXPECT(zmod::fog().far_range == 800.0f && zmod::fog().on == 0);
  zmod::fog() = saved;
}

// Linear fog at the geometry edge uses the playtested starts. Deliberately foggy maps keep
// their scaled interval, and gameplay readers keep the authored fog.
TEST(view_distance_fog_covers_geometry_edge) {
  const zmod::Fog saved = zmod::fog();
  zmod::Fog edge{};
  edge.on = 1;
  edge.linear = 1;
  edge.near_range = 300.0f;
  edge.far_range = 800.0f;
  edge.inv_range = 1.0f / 500.0f;
  zmod::fog() = edge;
  {
    zmod::ScopedRenderFog scope(800.0f, 1200.0f);
    const zmod::Fog& render = zmod::render_fog();
    EXPECT(render.near_range == 1050.0f && render.far_range == 1200.0f);
    EXPECT(render.near_sq == 1102500.0f && render.far_sq == 1440000.0f);
    EXPECT(render.inv_range == 1.0f / 150.0f);
  }
  {
    zmod::ScopedRenderFog scope(800.0f, 1600.0f);
    EXPECT(zmod::render_fog().near_range == 1450.0f && zmod::render_fog().far_range == 1600.0f);
  }
  EXPECT(zmod::fog().near_range == 300.0f && zmod::fog().far_range == 800.0f);
  // Fog authored beyond the original far plane still ends at the visual far plane.
  zmod::fog().far_range = 950.0f;
  {
    zmod::ScopedRenderFog scope(800.0f, 1200.0f);
    EXPECT(zmod::render_fog().near_range == 1050.0f && zmod::render_fog().far_range == 1200.0f);
  }
  // A deliberately foggy map (fog ends at 300 of 800) keeps its proportionally scaled interval.
  zmod::fog().near_range = 50.0f;
  zmod::fog().far_range = 300.0f;
  {
    zmod::ScopedRenderFog scope(800.0f, 1600.0f);
    EXPECT(zmod::render_fog().near_range == 100.0f && zmod::render_fog().far_range == 600.0f);
  }
  zmod::fog() = saved;
}

TEST(view_distance_exact_fog_start_table) {
  constexpr zcls::ViewDistanceOption expected[] = {
      {800, 700}, {1200, 1050}, {1600, 1450}, {2400, 2250}, {3200, 3050}};
  EXPECT(std::size(zcls::kViewDistanceOptions) == std::size(expected));
  const zmod::Fog saved = zmod::fog();
  zmod::Fog edge{};
  edge.on = 1;
  edge.linear = 1;
  edge.near_range = 300.0f;
  edge.far_range = 800.0f;
  zmod::fog() = edge;
  for (size_t index = 0; index < std::size(zcls::kViewDistanceOptions); ++index) {
    const auto& option = zcls::kViewDistanceOptions[index];
    EXPECT(index < std::size(expected));
    if (index >= std::size(expected)) continue;
    EXPECT(option.view_distance == expected[index].view_distance);
    EXPECT(option.fog_start == expected[index].fog_start);
    EXPECT(zcls::is_supported_view_distance(option.view_distance));
    const float visual_far = static_cast<float>(option.view_distance);
    EXPECT(zcls::fog_start_for_view_distance(visual_far) == expected[index].fog_start);
    zmod::ScopedRenderFog scope(800.0f, visual_far);
    EXPECT(zmod::render_fog().near_range == expected[index].fog_start);
    EXPECT(zmod::render_fog().far_range == visual_far);
  }
  EXPECT(!zcls::is_supported_view_distance(1000));
  EXPECT(zcls::fog_start_for_view_distance(1000.0f) == 850.0f);
  EXPECT(zmod::fog().near_range == edge.near_range && zmod::fog().far_range == edge.far_range);
  zmod::fog() = saved;
}

// A collapsed near == far interval keeps its previous inverse range; the extended copy scales it.
TEST(view_distance_collapsed_fog_interval) {
  const zmod::Fog saved = zmod::fog();
  zmod::Fog collapsed{};
  collapsed.on = 1;
  collapsed.linear = 1;
  collapsed.near_range = collapsed.far_range = 500.0f;
  collapsed.inv_range = 1.0f / 400.0f;  // left behind by an earlier, non-empty interval
  zmod::fog() = collapsed;
  {
    zmod::ScopedRenderFog scope(800.0f, 1600.0f);
    EXPECT(zmod::render_fog().near_range == 1000.0f && zmod::render_fog().far_range == 1000.0f);
    EXPECT(zmod::render_fog().inv_range == 1.0f / 800.0f);
  }
  EXPECT(zmod::fog().inv_range == 1.0f / 400.0f);
  zmod::fog() = saved;
}
