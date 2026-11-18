#include "check.h"

#include "frontend/sdl/draw_distance_option.h"
#include "gamez/zclass/camera.h"
#include "gamez/zclass/cls_data.h"
#include "gamez/zmodel/gmod_fog.h"
#include "gamez/zmodel/gmod_fogcalc.h"
#include "frontend/core_critical/renderer/geometry/resource.hpp"
#include "frontend/core_critical/renderer/geometry/reference.hpp"
#include "mech3/mech_lod.h"

#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <iterator>
#include <limits>
#include <vector>

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
      // POPIN-A deliberately replaces #368's narrow interval with proportional mission haze.
      EXPECT(zmod::render_fog().near_range == 150.0f && zmod::render_fog().far_range == 1050.0f);
      EXPECT(zmod::render_fog_edge().start == 1050.0f);
      zmod::fog_set_far(800.0f);
      zmod::fog_set_on(0);
      EXPECT(zmod::fog().far_range == 800.0f && zmod::fog().on == 0);
      EXPECT(zmod::render_fog().far_range == 1200.0f && zmod::render_fog().on == 0);
    }
    // The outer copy follows what was set while the zoom scope was active.
    EXPECT(zmod::render_fog().far_range == 1600.0f && zmod::render_fog().on == 0);
    EXPECT(zmod::render_fog_edge().start == 1450.0f && zmod::render_fog_active());
  }
  EXPECT(&zmod::render_fog() == &zmod::fog());
  EXPECT(zmod::render_fog_edge().inverse_range == 0.0f);
  EXPECT(zmod::fog().far_range == 800.0f && zmod::fog().on == 0);
  zmod::fog() = saved;
}

// POPIN-A deliberately changes #368: the table no longer replaces proportional mission haze.
// Only a mission interval beyond the cut is capped; POPIN-B independently covers the edge.
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
    EXPECT(render.near_range == 450.0f && render.far_range == 1200.0f);
    EXPECT(render.near_sq == 202500.0f && render.far_sq == 1440000.0f);
    EXPECT(render.inv_range == 1.0f / 750.0f);
  }
  {
    zmod::ScopedRenderFog scope(800.0f, 1600.0f);
    EXPECT(zmod::render_fog().near_range == 600.0f && zmod::render_fog().far_range == 1600.0f);
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
    EXPECT(zmod::render_fog().near_range == 300.0f * visual_far / 800.0f);
    EXPECT(zmod::render_fog().far_range == visual_far);
    EXPECT(zmod::render_fog_edge().start == expected[index].fog_start);
    EXPECT(zmod::render_fog_edge().inverse_range ==
           1.0f / (visual_far - expected[index].fog_start));
  }
  EXPECT(!zcls::is_supported_view_distance(1000));
  EXPECT(zcls::fog_start_for_view_distance(1000.0f) == 850.0f);
  EXPECT(zmod::fog().near_range == edge.near_range && zmod::fog().far_range == edge.far_range);
  zmod::fog() = saved;
}

TEST(view_distance_proportional_haze_and_altitude_independent_edge) {
  const zmod::Fog saved = zmod::fog();
  const zmod::FogCalc saved_calc = zmod::fog_calc();
  zmod::fog_calc() = {};
  zmod::fog_calc().camera_to_world[1][1] = 1.0f;
  // Independent hand-derived values: (800*r - 32)/(750 - 32), clamped.
  constexpr float fractions[] = {0.4f, 0.7f, 0.95f, 1.0f};
  constexpr float mission_density[] = {288.0f / 718.0f, 528.0f / 718.0f, 1.0f, 1.0f};
  constexpr float edge_at_95[] = {0.6f, 0.6f, 7.0f / 15.0f, 0.2f, 0.0f};
  for (bool altitude_band : {false, true}) {
    for (bool mission_on : {false, true}) {
      zmod::fog() = {};
      zmod::fog_set_on(mission_on);
      zmod::fog_set_linear(1);
      zmod::fog_set_near(32.0f);
      zmod::fog_set_far(750.0f);
      zmod::fog_set_alt_low(altitude_band ? 80.0f : 1000.0f);
      zmod::fog_set_alt_high(altitude_band ? 100.0f : 1001.0f);
      const zmod::Fog authored = zmod::fog();
      for (size_t option_index = 0; option_index < std::size(zcls::kViewDistanceOptions);
           ++option_index) {
        const float view_distance =
            static_cast<float>(zcls::kViewDistanceOptions[option_index].view_distance);
        zmod::ScopedRenderFog scope(800.0f, view_distance);
        const auto& render = zmod::render_fog();
        const auto edge = zmod::render_fog_edge();
        EXPECT(render.near_range == 32.0f * (view_distance / 800.0f));
        EXPECT(render.far_range == 750.0f * (view_distance / 800.0f));
        EXPECT(std::memcmp(&zmod::fog(), &authored, sizeof(authored)) == 0);
        cc::geometry::Fog reference;
        reference.enabled = mission_on;
        reference.near_range = render.near_range;
        reference.inverse_range = render.inv_range;
        reference.low_altitude = render.alt_low;
        reference.inverse_altitude = render.inv_alt;
        reference.edge_start = edge.start;
        reference.edge_inverse_range = edge.inverse_range;
        EXPECT(reference.active() && zmod::render_fog_active());
        for (size_t sample = 0; sample < std::size(fractions); ++sample) {
          const float distance = view_distance * fractions[sample];
          const float expected_edge = sample == 3 ? 1.0f :
              (sample == 2 ? edge_at_95[option_index] : 0.0f);
          for (float height : {1.0f, 90.0f, 500.0f}) {
            float altitude = 1.0f;
            if (altitude_band && height == 90.0f) altitude = 0.5f;
            if (altitude_band && height == 500.0f) altitude = 0.0f;
            const float mission = mission_on ? mission_density[sample] * altitude : 0.0f;
            const float expected = 1.0f - (1.0f - mission) * (1.0f - expected_edge);
            const float vertex[] = {0.0f, height, distance};
            EXPECT(std::abs(zmod::fog_at(vertex) - expected) < 2e-6f);
            EXPECT(std::abs(zmod::fog_sphere(vertex, 0.0f) - expected) < 2e-6f);
            EXPECT(zmod::fog_sphere(vertex, 10.0f) + 2e-6f >= expected);
            EXPECT(std::abs(cc::geometry::fog_amount(reference, distance, height) - expected) < 2e-6f);
            if (sample == 3) EXPECT(zmod::fog_at(vertex) == 1.0f);
          }
        }
        // The ramp must be present even where proportional haze is already full below 80 m.
        const float middle[] = {0.0f, 500.0f, (edge.start + view_distance) * 0.5f};
        if (altitude_band || !mission_on)
          EXPECT(std::abs(zmod::fog_at(middle) - 0.5f) < 2e-6f);
      }
    }
  }
  EXPECT(zmod::render_fog_edge().inverse_range == 0.0f);
  zmod::fog() = saved;
  zmod::fog_calc() = saved_calc;
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

TEST(view_distance_crossing_triangle_fog_at_cut) {
  const zmod::Fog saved = zmod::fog();
  const zmod::FogCalc saved_calc = zmod::fog_calc();
  zmod::fog_calc() = {};
  zmod::fog_calc().camera_to_world[1][1] = 1.0f;
  constexpr zcls::ViewDistanceOption cases[] = {
      {800, 700}, {1200, 1050}, {1600, 1450}, {2400, 2250}, {3200, 3050}};
  for (const auto& test : cases) {
    const float cut_depth = static_cast<float>(test.view_distance);
    for (bool mission_on : {false, true}) {
      zmod::fog() = {};
      zmod::fog_set_on(mission_on);
      zmod::fog_set_near(32.0f);
      zmod::fog_set_far(750.0f);
      zmod::fog_set_alt_low(80.0f);
      zmod::fog_set_alt_high(100.0f);
      zmod::ScopedRenderFog scope(800.0f, cut_depth);
      const auto edge = zmod::render_fog_edge();
      EXPECT(edge.start == test.fog_start);
      EXPECT(edge.inverse_range == 1.0f / (cut_depth - test.fog_start));
      cc::geometry::Fog reference;
      reference.enabled = mission_on;
      reference.near_range = zmod::render_fog().near_range;
      reference.inverse_range = zmod::render_fog().inv_range;
      reference.low_altitude = 80.0f;
      reference.inverse_altitude = 1.0f / 20.0f;
      reference.edge_start = test.fog_start;
      reference.edge_inverse_range = edge.inverse_range;
      // At 3200 these depths are exactly 3000/3400. The first crossing has x == 0,
      // so interpolating the old endpoint-clamped fog gives exactly 0.5 at the cut.
      std::vector<cc::geometry::ReferenceVertex> triangle(3);
      triangle[0].camera = {0.0f, 400.0f, cut_depth - 200.0f};
      triangle[1].camera = {100.0f, 400.0f, cut_depth - 200.0f};
      triangle[2].camera = {0.0f, 600.0f, cut_depth + 200.0f};
      for (auto& vertex : triangle)
        vertex.fog = cc::geometry::fog_factors(
            reference, std::hypot(vertex.camera[0], vertex.camera[2]), vertex.camera[1]);
      const float previous_cut_fog =
          0.5f * (cc::geometry::fog_amount(triangle[0].fog) +
                  cc::geometry::fog_amount(triangle[2].fog));
      EXPECT(previous_cut_fog == 0.5f);
      const auto clipped = cc::geometry::clip_reference(triangle, cut_depth, false);
      EXPECT(clipped.size() == 4);
      unsigned cut_vertices = 0;
      for (const auto& vertex : clipped) {
        if (vertex.camera[2] != cut_depth) continue;
        EXPECT(vertex.fog[2] >= 1.0f);
        EXPECT(cc::geometry::fog_amount(vertex.fog) == 1.0f);
        EXPECT(zmod::fog_at(vertex.camera.data()) == 1.0f);
        ++cut_vertices;
      }
      EXPECT(cut_vertices == 2);
      // The sphere centre is clear, but its farthest point reaches the cut;
      // the conservative branch must retain per-vertex fog even above the altitude band.
      const float centre[] = {0.0f, 500.0f, cut_depth - 200.0f};
      EXPECT(zmod::fog_at(centre) == 0.0f);
      EXPECT(zmod::fog_sphere(centre, 200.0f) == 1.0f);
      const float middle[] = {0.0f, 500.0f, (test.fog_start + cut_depth) * 0.5f};
      EXPECT(std::abs(zmod::fog_at(middle) - 0.5f) < 1e-6f);
      // A clear centre above the mission band can still have a foggy sphere bottom.
      const float altitude_centre[] = {0.0f, 110.0f, cut_depth * 0.4f};
      const float scale = cut_depth / 800.0f;
      const float expected_sphere = mission_on ?
          0.5f * (288.0f * scale + 20.0f) / (718.0f * scale) : 0.0f;
      EXPECT(zmod::fog_at(altitude_centre) == 0.0f);
      EXPECT(std::abs(zmod::fog_sphere(altitude_centre, 20.0f) - expected_sphere) < 1e-6f);
    }
  }
  // Mission distance must also remain unbounded until after interpolation.
  cc::geometry::Fog mission;
  mission.enabled = true;
  mission.near_range = 3050.0f;
  mission.inverse_range = 1.0f / 150.0f;
  mission.low_altitude = 80.0f;
  mission.inverse_altitude = 1.0f / 20.0f;
  const auto first = cc::geometry::fog_factors(mission, 3000.0f, 0.0f);
  const auto last = cc::geometry::fog_factors(mission, 3400.0f, 0.0f);
  std::array<float, 3> cut{};
  for (unsigned axis = 0; axis < 3; ++axis)
    cut[axis] = first[axis] + 0.5f * (last[axis] - first[axis]);
  EXPECT(cc::geometry::fog_amount(cut) == 1.0f);
  EXPECT(0.5f * (cc::geometry::fog_amount(first) + cc::geometry::fog_amount(last)) == 0.5f);
  zmod::fog() = saved;
  zmod::fog_calc() = saved_calc;
}

TEST(view_distance_unscoped_fog_keeps_original_exponent_approximation) {
  const zmod::Fog saved = zmod::fog();
  const zmod::FogCalc saved_calc = zmod::fog_calc();
  zmod::fog_calc() = {};
  zmod::fog_calc().camera_to_world[1][1] = 1.0f;
  zmod::fog() = {};
  zmod::fog_set_on(1);
  zmod::fog_set_near(100.0f);
  zmod::fog_set_far(800.0f);
  zmod::fog_set_alt_low(20.0f);
  zmod::fog_set_alt_high(80.0f);
  EXPECT(zmod::render_fog_edge().inverse_range == 0.0f);
  // The original bit-exponent sqrt of 90000 is 303.78125, rather than hypot's 300.
  const float ground[] = {0.0f, 0.0f, 300.0f};
  const float middle[] = {0.0f, 50.0f, 300.0f};
  const float above[] = {0.0f, 80.0f, 300.0f};
  const float beyond[] = {0.0f, 0.0f, 900.0f};
  EXPECT(std::abs(zmod::fog_at(ground) - 203.78125f / 700.0f) < 1e-7f);
  EXPECT(std::abs(zmod::fog_at(middle) - 0.5f * 203.78125f / 700.0f) < 1e-7f);
  EXPECT(zmod::fog_at(above) == 0.0f);
  EXPECT(zmod::fog_at(beyond) == 1.0f);
  zmod::fog() = saved;
  zmod::fog_calc() = saved_calc;
}
