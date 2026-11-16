#include "check.h"

#include "frontend/sdl/draw_distance_option.h"
#include "gamez/zclass/camera.h"
#include "gamez/zclass/cls_data.h"
#include "gamez/zmodel/gmod_fog.h"

#include <array>
#include <cmath>
#include <cstring>

TEST(view_distance_cli_options) {
  unsigned distance = 0;
  EXPECT(sdlfe::parse_draw_distance("800", &distance) && distance == 800);
  EXPECT(sdlfe::parse_draw_distance("1200", &distance) && distance == 1200);
  EXPECT(sdlfe::parse_draw_distance("1600", &distance) && distance == 1600);
  EXPECT(!sdlfe::parse_draw_distance("2400", &distance));
  EXPECT(!sdlfe::parse_draw_distance("3200", &distance));
  EXPECT(!sdlfe::parse_draw_distance("1200junk", &distance));
  EXPECT(!sdlfe::parse_draw_distance(nullptr, &distance));
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
    zmod::ScopedRenderFog identity_scope(800.0f, 800.0f);
    EXPECT(std::memcmp(&zmod::render_fog(), &initial, sizeof(initial)) == 0);
  }
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
  zcls::SceneWalk walk{};
  const size_t ring_capacity = std::size(walk.rings);
  const size_t cells_per_ring = std::size(walk.rings[0].cell);
  EXPECT(ring_capacity >= 100);
  EXPECT(cells_per_ring >= 60);
  for (size_t ring = 0; ring < 100; ++ring) {
    for (size_t cell = 0; cell < 60; ++cell) {
      auto& output = walk.rings[ring].cell[walk.rings[ring].count++];
      output.x = static_cast<int32_t>(ring);
      output.z = static_cast<int32_t>(cell);
    }
    EXPECT(walk.rings[ring].count == 60);
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
      // 700 x 1.5 = 1050 (not 700 x 2 x 1.5) reaches the 1200 view's cover band, so it covers the edge.
      EXPECT(zmod::render_fog().near_range == 1000.0f && zmod::render_fog().far_range == 1200.0f);
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

// Linear fog that reaches the edge of an extended view covers where world geometry ends: full at
// the visual far plane, starting about 200 units before it at 1200 and 100 units before it at
// 1600. Fog that ends well short of the edge keeps its scaled interval. The authored fog that
// gameplay reads never changes.
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
    EXPECT(render.near_range == 1000.0f && render.far_range == 1200.0f);
    EXPECT(render.near_sq == 1000000.0f && render.far_sq == 1440000.0f);
    EXPECT(render.inv_range == 1.0f / 200.0f);
  }
  {
    zmod::ScopedRenderFog scope(800.0f, 1600.0f);
    EXPECT(zmod::render_fog().near_range == 1500.0f && zmod::render_fog().far_range == 1600.0f);
  }
  EXPECT(zmod::fog().near_range == 300.0f && zmod::fog().far_range == 800.0f);
  // Fog authored beyond the original far plane still ends at the visual far plane.
  zmod::fog().far_range = 950.0f;
  {
    zmod::ScopedRenderFog scope(800.0f, 1200.0f);
    EXPECT(zmod::render_fog().near_range == 1000.0f && zmod::render_fog().far_range == 1200.0f);
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
