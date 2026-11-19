#include "check.h"

#include "gamez/zclass/camera.h"
#include "gamez/zclass/cls_data.h"
#include "gamez/zmath/zmth_matrix.h"
#include "gamez/zmodel/gmod_cull.h"
#include "gamez/zmodel/gmod_draw.h"
#include "gamez/zmodel/gmod_fog.h"
#include "gamez/zmodel/gmod_init.h"
#include "gamez/zmodel/gmod_light.h"
#include "gamez/zvideo/zvid_ddd3d.h"
#include "mech3/options.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <cstdlib>
#include <iterator>
#include <limits>
#include <memory>
#include <string>
#include <vector>

namespace {
constexpr float kAuthoredFar = 800.0f;
std::vector<std::string> g_visual_far_log_lines;
std::chrono::steady_clock::time_point g_visual_far_test_now{};

std::chrono::steady_clock::time_point visual_far_test_clock_now() {
  return g_visual_far_test_now;
}

void advance_visual_far_test_clock() {
  g_visual_far_test_now += std::chrono::seconds(1);
}

void capture_visual_far_log(const char* line) {
  g_visual_far_log_lines.emplace_back(line);
}

struct VisualFarLogSinkGuard {
  zcls::VisualFarLogSink previous_sink = nullptr;

  VisualFarLogSinkGuard() {
    g_visual_far_log_lines.clear();
    previous_sink = zcls::set_visual_far_log_sink(capture_visual_far_log);
  }

  ~VisualFarLogSinkGuard() {
    zcls::set_visual_far_log_sink(previous_sink);
    g_visual_far_log_lines.clear();
  }
};

struct VisualFarLogClockGuard {
  zcls::VisualFarLogNow previous_clock = nullptr;

  VisualFarLogClockGuard() {
    g_visual_far_test_now = {};
    previous_clock = zcls::set_visual_far_log_clock_for_testing(visual_far_test_clock_now);
  }

  ~VisualFarLogClockGuard() {
    zcls::set_visual_far_log_clock_for_testing(previous_clock);
  }
};

struct CameraFrame {
  unsigned requested_far;
  float position[3];
  float pitch, yaw;
  float horizontal_fov, vertical_fov;
};

void expect_far_state(zcls::Camera& camera, const CameraFrame& frame, float far_z) {
  EXPECT(camera.get<float>(0xb4) == kAuthoredFar);
  EXPECT(camera.get<float>(0x110) == -far_z);
  const float half_width = std::tan(frame.horizontal_fov * 0.5f) * far_z;
  const float half_height = std::tan(frame.vertical_fov * 0.5f) * far_z;
  const float expected_corners[12] = {
      half_width, -half_height, -far_z, -half_width, -half_height, -far_z,
      half_width, half_height, -far_z, -half_width, half_height, -far_z};
  for (int i = 0; i < 12; ++i)
    EXPECT(std::abs(camera.floats(0x108)[i] - expected_corners[i]) < 0.001f);

  // Compute the forward vector from the requested pose, independently of the
  // cached world matrix. A stale direction must not satisfy the plane check.
  const float direction[3] = {-std::sin(frame.yaw) * std::cos(frame.pitch),
                              std::sin(frame.pitch),
                             -std::cos(frame.yaw) * std::cos(frame.pitch)};
  for (int i = 0; i < 3; ++i) {
    EXPECT(std::abs(camera.floats(0x2c)[i] - frame.position[i]) < 0.001f);
    EXPECT(std::abs(camera.floats(0x74)[i] - direction[i]) < 0.00001f);
    const float expected_point = frame.position[i] + direction[i] * far_z;
    EXPECT(std::abs(camera.floats(0xc4)[i] - expected_point) < 0.001f);
  }
}

// An empty authored partition exercises render_world's real VisualRenderScope
// and camera_update without game assets, graphics output or test-only camera APIs.
struct CameraFixture {
  mech3::Rect old_render = mech3::render();
  unsigned old_far = zcls::visual_far_request();
  zmth::MatrixStack old_stack = zmth::matrix_stack();
  zmth::View old_view = zmth::view();
  zmth::Projection old_projection = zmth::projection();
  std::unique_ptr<zcls::SceneWalk> old_walk =
      std::make_unique<zcls::SceneWalk>(zcls::scene_walk());
  zcls::WorldRenderHooks old_hooks = zcls::world_render_hooks();
  zmod::WalkState old_model_walk = zmod::walk_state();
  zmod::DrawState old_draw = zmod::draw_state();
  zmod::Lighting old_lighting = zmod::lighting();
  zmod::LightList old_lights = zmod::light_list();
  zmod::Zones old_zones = zmod::zones();
  zmod::ViewPolygon old_polygon = zmod::view_polygon();
  platform::Render3D* old_renderer = zvid::render3d();
  platform::ProducerView old_metadata{};
  zcls::Node camera_node{}, window_node{}, world_node{};
  zcls::Camera camera{};
  zcls::Window window{};
  zcls::World world{};
  zcls::Partition partitions[25]{};
  zcls::Partition* rows[5]{};
  const CameraFrame* frame = nullptr;
  int observed_passes = 0;

  CameraFixture() {
    {
      zvid::ProducerPurposeScope request(platform::ProducerPurpose::MainWorld);
      zvid::ProducerWorldScope scope;
      scope.begin_emission();
      old_metadata = zvid::capture_producer_view();
    }
    zvid::set_render3d(nullptr);
    zmth::reset_stack();
    zcls::scene_walk().reset();
    zcls::world_render_hooks() = {};
    zmod::walk_state() = {};
    mech3::set_render_origin(0, 0);
    mech3::set_render_size(3440, 1440);
    zmod::draw_state().shadows = 0;
    zmod::zones().mode = 0;

    camera_node.put<int32_t>(0x34, 1);
    camera_node.data = &camera;
    window_node.put<int32_t>(0x34, 3);
    window_node.data = &window;
    world_node.put<int32_t>(0x34, 2);
    world_node.data = &world;
    camera.nodes[0] = &world_node;
    camera.nodes[1] = &window_node;
    for (std::size_t row = 0; row < std::size(rows); ++row)
      rows[row] = &partitions[row * std::size(rows)];
    camera.put(0xd8, 1.0f);
    camera.put(0xdc, 1.0f);
    EXPECT(zcls::camera_set_clip(&camera_node, 1.0f, kAuthoredFar) == 0);
    window.put<int32_t>(8, 3440);
    window.put<int32_t>(12, 1440);
    world.rows = rows;
    world.put(0x34, -2000.0f);
    world.put(0x38, -2000.0f);
    world.put(0x44, 2000.0f);
    world.put(0x48, 2000.0f);
    world.put(0x64, 4000.0f);
    world.put(0x68, 4000.0f);
    world.put(0x74, 1.0f / 4000.0f);
    world.put(0x78, 1.0f / 4000.0f);
    world.put<int32_t>(0x88, 1);
    world.put<int32_t>(0x8c, 1);

    auto& hooks = zcls::world_render_hooks();
    hooks.ctx = this;
    hooks.begin_scene = [](void* context) {
      auto& fixture = *static_cast<CameraFixture*>(context);
      ++fixture.observed_passes;
      const float render_far = static_cast<float>(fixture.frame->requested_far);
      EXPECT(zcls::visual_far_for_render(&fixture.camera, kAuthoredFar) == render_far);
      expect_far_state(fixture.camera, *fixture.frame, render_far);
    };
  }

  ~CameraFixture() {
    zmod::retire_world_lights(&world);
    zcls::set_visual_far_request(old_far);
    zmth::matrix_stack() = old_stack;
    zmth::view() = old_view;
    zmth::projection() = old_projection;
    zcls::scene_walk() = *old_walk;
    zcls::world_render_hooks() = old_hooks;
    zmod::walk_state() = old_model_walk;
    mech3::render() = old_render;
    zmod::draw_state() = old_draw;
    zmod::lighting() = old_lighting;
    zmod::light_list() = old_lights;
    zmod::zones() = old_zones;
    zmod::view_polygon() = old_polygon;
    zvid::set_producer_camera_rect(old_metadata.camera_rect.x, old_metadata.camera_rect.y,
        old_metadata.camera_rect.width, old_metadata.camera_rect.height,
        old_metadata.camera_rect_available);
    zvid::set_render3d(old_renderer);
  }
};
}  // namespace

TEST(view_distance_restores_render_camera_far_state) {
  CameraFixture fixture;
  VisualFarLogClockGuard clock_guard;
  VisualFarLogSinkGuard log_sink_guard;
  zcls::world_render_hooks().begin_scene = [](void* context) {
    auto& fixture = *static_cast<CameraFixture*>(context);
    ++fixture.observed_passes;
    const float render_far = static_cast<float>(fixture.frame->requested_far);
    EXPECT(zcls::visual_far_for_render(&fixture.camera, kAuthoredFar) == render_far);
    expect_far_state(fixture.camera, *fixture.frame, render_far);
    constexpr zcls::ViewDistanceOption expected_edges[] = {
        {800, 700}, {1200, 1050}, {1600, 1450}, {2400, 2250}, {3200, 3050}};
    bool matched = false;
    for (const auto& option : expected_edges) {
      if (option.view_distance != fixture.frame->requested_far) continue;
      EXPECT(zmod::render_fog_edge().start == option.fog_start);
      EXPECT(zmod::render_fog_edge().inverse_range ==
             1.0f / (render_far - option.fog_start));
      matched = true;
    }
    EXPECT(matched);
  };
  EXPECT(fixture.camera.get<float>(0x110) == 0.0f);
  for (int i = 0; i < 3; ++i) EXPECT(fixture.camera.floats(0xc4)[i] == 0.0f);

  const CameraFrame frames[] = {
      {1200, {10.0f, 30.0f, 20.0f}, 0.0f, 0.0f, 1.0f, 0.8f},
      {1200, {80.0f, 45.0f, -40.0f}, 0.2f, 0.7f, 1.0f, 0.8f},
      {1600, {80.0f, 45.0f, -40.0f}, -0.1f, -0.5f, 0.9f, 0.6f},
      {800, {-20.0f, 25.0f, 60.0f}, 0.1f, 0.3f, 0.9f, 0.6f},
      {2400, {-20.0f, 25.0f, 60.0f}, 0.1f, 0.3f, 0.9f, 0.6f},
      {3200, {-20.0f, 25.0f, 60.0f}, 0.1f, 0.3f, 0.9f, 0.6f}};
  for (std::size_t frame_index = 0; frame_index < std::size(frames); ++frame_index) {
    const auto& frame = frames[frame_index];
    fixture.frame = &frame;
    zcls::set_visual_far_request(frame.requested_far);
    EXPECT(zcls::camera_set_position(&fixture.camera_node, frame.position[0],
        frame.position[1], frame.position[2]) == 0);
    EXPECT(zcls::camera_set_rotation(&fixture.camera_node, frame.pitch, frame.yaw, 0.0f) == 0);
    if (fixture.camera.get<float>(0xe8) != frame.horizontal_fov ||
        fixture.camera.get<float>(0xec) != frame.vertical_fov) {
      EXPECT(zcls::camera_set_fov_angles(&fixture.camera_node, frame.horizontal_fov,
          frame.vertical_fov) == 0);
    }
    // render_world constructs the private scope BEFORE its camera_update call.
    // Check immediately on return, before another update could hide bad restoration.
    if (frame_index >= 2) advance_visual_far_test_clock();
    EXPECT(zcls::render_world(&fixture.camera_node, 0) == 0);
    // The first two frames share one logged state; each later request changes it once.
    const std::size_t expected_log_count = frame_index < 2 ? 1 : frame_index;
    EXPECT(g_visual_far_log_lines.size() == expected_log_count);
    EXPECT(zcls::visual_far_for_render(&fixture.camera, kAuthoredFar) == kAuthoredFar);
    expect_far_state(fixture.camera, frame, kAuthoredFar);
    EXPECT(!zcls::visual_far_corners_need_update(false, kAuthoredFar,
        fixture.camera.get<float>(0x110)));
    EXPECT(fixture.camera.get<int32_t>(0xf8) == 0);

    zmth::Mat34 local;
    zmth::push(&local);
    EXPECT(zcls::camera_update(&fixture.camera_node) == 0);
    zmth::pop();
    expect_far_state(fixture.camera, frame, kAuthoredFar);
  }
  EXPECT(g_visual_far_log_lines.size() == 5);
  EXPECT(g_visual_far_log_lines.at(0).find(
             "requested 1200, authored 800, expanded 1.2e+03") != std::string::npos);
  EXPECT(g_visual_far_log_lines.at(0).find(
             "full viewport 1 (window 3440x1440, render 3440x1440)") !=
         std::string::npos);
  EXPECT(g_visual_far_log_lines.at(0).find(
             "extended 1, default-800 fog-only 0; camera main") !=
         std::string::npos);
  EXPECT(g_visual_far_log_lines.at(1).find(
             "requested 1600, authored 800, expanded 1.6e+03") != std::string::npos);
  EXPECT(g_visual_far_log_lines.at(2).find(
             "requested 800, authored 800, expanded 800") != std::string::npos);
  EXPECT(g_visual_far_log_lines.at(2).find(
             "extended 0, default-800 fog-only 1; camera main") !=
         std::string::npos);
  EXPECT(fixture.observed_passes == 6);
}

TEST(default_visual_far_covers_only_full_viewport_fog) {
  CameraFixture fixture;
  VisualFarLogClockGuard clock_guard;
  VisualFarLogSinkGuard log_sink_guard;
  EXPECT(zcls::camera_set_fov_angles(&fixture.camera_node, 1.0f, 0.8f) == 0);
  const zmod::Fog old_fog = zmod::fog();
  zmod::fog_set_on(1);
  zmod::fog_set_linear(1);
  zmod::fog_set_near(300.0f);
  zmod::fog_set_far(800.0f);
  const zmod::Fog authored_fog = zmod::fog();
  zcls::set_visual_far_request(800);

  auto& hooks = zcls::world_render_hooks();
  hooks.begin_scene = [](void* context) {
    auto& fixture = *static_cast<CameraFixture*>(context);
    ++fixture.observed_passes;
    EXPECT(&zmod::render_fog() != &zmod::fog());
    // POPIN-A preserves the authored haze; POPIN-B owns #368's default edge band.
    EXPECT(zmod::render_fog().near_range == 300.0f);
    EXPECT(zmod::render_fog_edge().start == 700.0f);
    EXPECT(zmod::render_fog().far_range == 800.0f);
    EXPECT(zmod::fog().on == 1);
    EXPECT(zmod::fog().linear == 1);
    EXPECT(zmod::fog().near_range == 300.0f);
    EXPECT(zmod::fog().far_range == 800.0f);
  };
  EXPECT(zcls::render_world(&fixture.camera_node, 0) == 0);
  EXPECT(&zmod::render_fog() == &zmod::fog());

  const CameraFrame expanded_frame = {1600, {10.0f, 30.0f, 20.0f},
                                      0.0f, 0.0f, 1.0f, 0.8f};
  advance_visual_far_test_clock();
  fixture.frame = &expanded_frame;
  zcls::set_visual_far_request(expanded_frame.requested_far);
  hooks.begin_scene = [](void* context) {
    auto& fixture = *static_cast<CameraFixture*>(context);
    ++fixture.observed_passes;
    EXPECT(zcls::visual_far_for_render(&fixture.camera, kAuthoredFar) == 1600.0f);
    EXPECT(fixture.camera.get<float>(0x110) == -1600.0f);
    EXPECT(zmod::draw_state().clip.far_z == 1600.0f);
    EXPECT(zmod::render_fog().near_range == 600.0f);
    EXPECT(zmod::render_fog_edge().start == 1450.0f);
    EXPECT(zmod::render_fog().far_range == 1600.0f);
  };
  EXPECT(zcls::render_world(&fixture.camera_node, 0) == 0);
  EXPECT(zcls::visual_far_for_render(&fixture.camera, kAuthoredFar) == kAuthoredFar);

  fixture.window.put<int32_t>(8, 90);
  fixture.window.put<int32_t>(12, 90);
  hooks.begin_scene = [](void* context) {
    auto& fixture = *static_cast<CameraFixture*>(context);
    ++fixture.observed_passes;
    EXPECT(zcls::visual_far_for_render(&fixture.camera, kAuthoredFar) == kAuthoredFar);
    EXPECT(&zmod::render_fog() == &zmod::fog());
  };
  EXPECT(zcls::render_world(&fixture.camera_node, 0) == 0);
  EXPECT(zcls::visual_far_for_render(&fixture.camera, kAuthoredFar) == kAuthoredFar);

  zcls::set_visual_far_request(800);
  fixture.window.put<int32_t>(8, 1720);
  fixture.window.put<int32_t>(12, 720);
  hooks.begin_scene = [](void* context) {
    auto& fixture = *static_cast<CameraFixture*>(context);
    ++fixture.observed_passes;
    EXPECT(&zmod::render_fog() == &zmod::fog());
    EXPECT(zmod::render_fog().near_range == 300.0f);
    EXPECT(zmod::render_fog().far_range == 800.0f);
  };
  {
    zcls::ScopedZoomVisualFar zoom(&fixture.camera);
    EXPECT(zcls::render_world(&fixture.camera_node, 0) == 0);
    EXPECT(&zmod::render_fog() == &zmod::fog());
  }
  EXPECT(fixture.observed_passes == 4);
  EXPECT(g_visual_far_log_lines.size() == 4);
  EXPECT(g_visual_far_log_lines.at(0).find(
             "scoped fog 300..800, mission fog linear 1 on 1") !=
         std::string::npos);
  EXPECT(g_visual_far_log_lines.at(1).find(
             "scoped fog 600..1.6e+03, mission fog linear 1 on 1") !=
         std::string::npos);
  EXPECT(g_visual_far_log_lines.at(3).find(
             "requested 800, authored 800, expanded 800") != std::string::npos);
  EXPECT(g_visual_far_log_lines.at(3).find("camera zoom") != std::string::npos);
  EXPECT(g_visual_far_log_lines.at(3).find(
             "scoped fog 300..800, mission fog linear 1 on 1") !=
         std::string::npos);
  EXPECT(zmod::fog().near_range == authored_fog.near_range);
  EXPECT(zmod::fog().far_range == authored_fog.far_range);
  zmod::fog() = old_fog;
}

TEST(view_distance_log_deduplicates_each_camera_class) {
  CameraFixture fixture;
  VisualFarLogClockGuard clock_guard;
  VisualFarLogSinkGuard log_sink_guard;
  const CameraFrame frame = {1200, {10.0f, 30.0f, 20.0f},
                             0.0f, 0.0f, 1.0f, 0.8f};

  auto render_frame = [&](unsigned requested_far, bool zoom, int32_t viewport_width,
                          int32_t viewport_height) {
    CameraFrame active_frame = frame;
    active_frame.requested_far = requested_far;
    fixture.frame = &active_frame;
    zcls::set_visual_far_request(requested_far);
    EXPECT(zcls::camera_set_position(&fixture.camera_node, active_frame.position[0],
        active_frame.position[1], active_frame.position[2]) == 0);
    EXPECT(zcls::camera_set_rotation(&fixture.camera_node, active_frame.pitch,
        active_frame.yaw, 0.0f) == 0);
    EXPECT(zcls::camera_set_fov_angles(&fixture.camera_node,
        active_frame.horizontal_fov, active_frame.vertical_fov) == 0);
    fixture.window.put<int32_t>(8, viewport_width);
    fixture.window.put<int32_t>(12, viewport_height);
    if (zoom) {
      zcls::ScopedZoomVisualFar zoom_scope(&fixture.camera);
      EXPECT(zcls::render_world(&fixture.camera_node, 0) == 0);
    } else {
      EXPECT(zcls::render_world(&fixture.camera_node, 0) == 0);
    }
  };

  render_frame(1200, false, 3440, 1440);
  render_frame(1200, true, 3440, 1440);
  render_frame(1200, false, 3440, 1440);
  render_frame(1200, true, 3440, 1440);
  EXPECT(g_visual_far_log_lines.size() == 2);
  EXPECT(g_visual_far_log_lines.at(0).find("camera main") != std::string::npos);
  EXPECT(g_visual_far_log_lines.at(1).find("camera zoom") != std::string::npos);

  advance_visual_far_test_clock();
  render_frame(1600, false, 3440, 1440);
  render_frame(1600, true, 3440, 1440);
  render_frame(1600, false, 3440, 1440);
  render_frame(1600, true, 3440, 1440);
  EXPECT(g_visual_far_log_lines.size() == 4);

  advance_visual_far_test_clock();
  render_frame(800, false, 90, 90);
  render_frame(800, false, 90, 90);
  EXPECT(g_visual_far_log_lines.size() == 5);
  render_frame(800, false, 1720, 720);
  render_frame(800, false, 1720, 720);
  EXPECT(g_visual_far_log_lines.size() == 6);
  EXPECT(g_visual_far_log_lines.at(4).find("camera other") != std::string::npos);
  EXPECT(g_visual_far_log_lines.at(4).find("window 90x90") != std::string::npos);
  EXPECT(g_visual_far_log_lines.at(5).find("window 1720x720") != std::string::npos);
}

TEST(view_distance_log_rate_cap_is_deterministic_and_preserves_camera_classes) {
  CameraFixture fixture;
  VisualFarLogClockGuard clock_guard;
  VisualFarLogSinkGuard log_sink_guard;
  const CameraFrame frame = {1200, {10.0f, 30.0f, 20.0f},
                             0.0f, 0.0f, 1.0f, 0.8f};
  auto render_frame = [&](unsigned requested_far, bool zoom, int32_t viewport_width,
                          int32_t viewport_height) {
    CameraFrame active_frame = frame;
    active_frame.requested_far = requested_far;
    fixture.frame = &active_frame;
    zcls::set_visual_far_request(requested_far);
    EXPECT(zcls::camera_set_position(&fixture.camera_node, active_frame.position[0],
        active_frame.position[1], active_frame.position[2]) == 0);
    EXPECT(zcls::camera_set_rotation(&fixture.camera_node, active_frame.pitch,
        active_frame.yaw, 0.0f) == 0);
    EXPECT(zcls::camera_set_fov_angles(&fixture.camera_node,
        active_frame.horizontal_fov, active_frame.vertical_fov) == 0);
    fixture.window.put<int32_t>(8, viewport_width);
    fixture.window.put<int32_t>(12, viewport_height);
    if (zoom) {
      zcls::ScopedZoomVisualFar zoom_scope(&fixture.camera);
      EXPECT(zcls::render_world(&fixture.camera_node, 0) == 0);
    } else {
      EXPECT(zcls::render_world(&fixture.camera_node, 0) == 0);
    }
  };

  // Unseen classes reserve two slots while main-camera states attempt to flood.
  render_frame(1200, false, 3440, 1440);
  for (int index = 0; index < 40; ++index)
    render_frame(index % 2 == 0 ? 1600 : 800, false, 3440, 1440);
  EXPECT(g_visual_far_log_lines.size() == 2);

  // Both new classes still get their first line, filling the four-line cap.
  render_frame(800, true, 90, 90);
  render_frame(800, false, 90, 90);
  EXPECT(g_visual_far_log_lines.size() == zcls::kVisualFarLogLinesPerSecond);
  EXPECT(g_visual_far_log_lines.at(0).find("camera main") != std::string::npos);
  EXPECT(g_visual_far_log_lines.at(2).find("camera zoom") != std::string::npos);
  EXPECT(g_visual_far_log_lines.at(3).find("camera other") != std::string::npos);

  // Four distinct main-camera states fit in one fresh window and all are logged.
  advance_visual_far_test_clock();
  const unsigned main_requests[] = {1200, 1600, 800, 1200};
  for (unsigned requested_far : main_requests)
    render_frame(requested_far, false, 3440, 1440);
  EXPECT(g_visual_far_log_lines.size() ==
         2 * zcls::kVisualFarLogLinesPerSecond);

  // Alternating states beyond the cap cannot add lines in the same window.
  for (int index = 0; index < 40; ++index)
    render_frame(index % 2 == 0 ? 1600 : 800, false, 3440, 1440);
  EXPECT(g_visual_far_log_lines.size() ==
         2 * zcls::kVisualFarLogLinesPerSecond);

  // At the rolling-window boundary, a new main-camera state is admitted again.
  advance_visual_far_test_clock();
  render_frame(1600, false, 3440, 1440);
  EXPECT(g_visual_far_log_lines.size() ==
         2 * zcls::kVisualFarLogLinesPerSecond + 1);
}

TEST(view_distance_virtual_tiler_usage_line_is_logged) {
  CameraFixture fixture;
  VisualFarLogSinkGuard log_sink_guard;
  const CameraFrame frame = {800, {0.0f, 30.0f, 0.0f}, 0.0f, 0.0f, 1.0f, 0.8f};
  fixture.frame = &frame;
  EXPECT(zcls::camera_set_position(&fixture.camera_node, 0.0f, 30.0f, 0.0f) == 0);
  EXPECT(zcls::camera_set_rotation(&fixture.camera_node, 0.0f, 0.0f, 0.0f) == 0);
  EXPECT(zcls::camera_set_fov_angles(&fixture.camera_node, 1.0f, 0.8f) == 0);
  zcls::set_visual_far_request(800);
  EXPECT(zcls::render_world(&fixture.camera_node, 0) == 0);
  fixture.window.put<int32_t>(8, 90);
  fixture.window.put<int32_t>(12, 90);
  {
    zcls::ScopedZoomVisualFar zoom_scope(&fixture.camera);
    EXPECT(zcls::render_world(&fixture.camera_node, 0) == 0);
  }
  EXPECT(zcls::render_world(&fixture.camera_node, 0) == 0);

  fixture.world.put<int32_t>(0x50, 1);
  fixture.world.put<int32_t>(0x54, 5);
  fixture.world.put<int32_t>(0x58, 5);
  fixture.world.put<int32_t>(0x5c, 0);
  fixture.world.put<int32_t>(0x60, 0);
  fixture.world.put<float>(0x34, -2000.0f);
  fixture.world.put<float>(0x38, -2000.0f);
  fixture.world.put<float>(0x44, 2000.0f);
  fixture.world.put<float>(0x48, 2000.0f);
  fixture.world.put<float>(0x64, 4000.0f);
  fixture.world.put<float>(0x68, 4000.0f);
  fixture.world.put<float>(0x6c, -2000.0f);
  fixture.world.put<float>(0x70, -2000.0f);
  fixture.world.put<float>(0x74, 1.0f / 800.0f);
  fixture.world.put<float>(0x78, 1.0f / 800.0f);
  fixture.world.put<int32_t>(0x88, 5);
  fixture.world.put<int32_t>(0x8c, 5);
  for (int32_t row = 0; row < 5; ++row) {
    for (int32_t column = 0; column < 5; ++column) {
      auto& partition = fixture.partitions[row * 5 + column];
      partition.put<uint32_t>(4, 1);
      partition.put<float>(8, static_cast<float>(column * 800 + 400));
      partition.put<float>(0xc, static_cast<float>(row * 800 + 400));
    }
  }
  fixture.window.put<int32_t>(8, 3440);
  fixture.window.put<int32_t>(12, 1440);
  EXPECT(zcls::render_world(&fixture.camera_node, 0) == 0);
  EXPECT(std::any_of(g_visual_far_log_lines.begin(), g_visual_far_log_lines.end(),
      [](const std::string& line) {
        return line.find("mw3: virtual view cells: rings ") == 0 &&
               line.find("max cells per ring ") != std::string::npos;
      }));
}

TEST(view_distance_log_floats_tolerate_animation_and_nan) {
  CameraFixture fixture;
  VisualFarLogClockGuard clock_guard;
  VisualFarLogSinkGuard log_sink_guard;
  const zmod::Fog old_fog = zmod::fog();
  const CameraFrame frame = {800, {10.0f, 30.0f, 20.0f},
                             0.0f, 0.0f, 1.0f, 0.8f};
  zmod::fog_set_on(1);
  zmod::fog_set_linear(0);
  zmod::fog_set_far(700.0f);
  fixture.frame = &frame;
  EXPECT(zcls::camera_set_position(&fixture.camera_node, frame.position[0],
      frame.position[1], frame.position[2]) == 0);
  EXPECT(zcls::camera_set_rotation(&fixture.camera_node, frame.pitch,
      frame.yaw, 0.0f) == 0);
  EXPECT(zcls::camera_set_fov_angles(&fixture.camera_node,
      frame.horizontal_fov, frame.vertical_fov) == 0);
  zcls::set_visual_far_request(800);

  auto render_frame = [&]() {
    EXPECT(zcls::render_world(&fixture.camera_node, 0) == 0);
  };

  zmod::fog_set_near(300.0f);
  render_frame();
  zmod::fog_set_near(300.25f);
  render_frame();
  EXPECT(g_visual_far_log_lines.size() == 1);
  zmod::fog_set_near(300.75f);
  render_frame();
  EXPECT(g_visual_far_log_lines.size() == 2);
  const float not_a_number = std::numeric_limits<float>::quiet_NaN();
  advance_visual_far_test_clock();
  zmod::fog_set_near(not_a_number);
  render_frame();
  render_frame();
  EXPECT(g_visual_far_log_lines.size() == 3);

  zmod::fog() = old_fog;
}

TEST(view_distance_selected_cell_reports_stationary_yaw_transition) {
  CameraFixture fixture;
  VisualFarLogSinkGuard sink;
  struct RestoreSelector {
    ~RestoreSelector() { zcls::set_world_cell_trace(std::getenv("MW3_TRACE_WORLD_CELL")); }
  } restore_selector;
  CameraFrame frame = {800, {0.0f, 20.0f, 0.0f}, 0.0f, 0.0f, 1.6f, 0.8f};
  fixture.frame = &frame;
  // A five-by-five grid with negative Z running forward. The selected cell's
  // small elevated bound is beyond the centre far plane but inside it after yaw.
  auto& world = fixture.world;
  world.put<int32_t>(0x50, 1);
  world.put<int32_t>(0x54, 5);
  world.put<int32_t>(0x58, 5);
  world.put<float>(0x34, -1000.0f);
  world.put<float>(0x38, 1000.0f);
  world.put<float>(0x64, 400.0f);
  world.put<float>(0x68, -400.0f);
  world.put<float>(0x6c, 200.0f);
  world.put<float>(0x70, -200.0f);
  world.put<float>(0x74, 1.0f / 400.0f);
  world.put<float>(0x78, -1.0f / 400.0f);
  world.put<float>(0x7c, -283.0f);
  world.put<int32_t>(0x88, 5);
  world.put<int32_t>(0x8c, 5);
  for (int z = 0; z < 5; ++z) {
    for (int x = 0; x < 5; ++x) {
      auto& p = fixture.partitions[z * 5 + x];
      p.put<uint32_t>(4, 1);
      p.put<float>(8, -1000.0f + 400.0f * x);
      p.put<float>(0xc, 1000.0f - 400.0f * z);
    }
  }
  auto& watched = fixture.partitions[4 * 5 + 2];
  watched.put<uint32_t>(0, 0x100);
  watched.put<float>(0x2c, 20.0f);
  watched.put<float>(0x30, -850.0f);
  watched.put<float>(0x34, 6.0f);
  zcls::set_visual_far_request(800);
  EXPECT(zcls::camera_set_position(&fixture.camera_node, 0, 20, 0) == 0);
  EXPECT(zcls::camera_set_fov_angles(&fixture.camera_node, 1.6f, 0.8f) == 0);
  auto render_at = [&](float yaw) {
    frame.yaw = yaw;
    EXPECT(zcls::camera_set_rotation(&fixture.camera_node, 0, yaw, 0) == 0);
    EXPECT(zcls::render_world(&fixture.camera_node, 0) == 0);
    for (const auto& ring : zcls::scene_walk().rings) {
      for (int i = 0; i < ring.count; ++i) {
        const auto& cell = ring.cell[i];
        if (cell.x == 2 && cell.z == 4 && !cell.wrapped) return true;
      }
    }
    return false;
  };
  auto count_lines = [&](const char* text) {
    return std::count_if(g_visual_far_log_lines.begin(), g_visual_far_log_lines.end(),
        [&](const std::string& line) { return line.find(text) != std::string::npos; });
  };
  zcls::set_world_cell_trace("2,4junk");
  EXPECT(!render_at(0));
  EXPECT(count_lines("mw3: world cell") == 0);
  zcls::set_world_cell_trace("2,4");
  EXPECT(!render_at(0));
  EXPECT(!render_at(0));
  EXPECT(count_lines("world cell (2,4) sphere plane=0x20") == 1);
  EXPECT(count_lines("depth=850.00") == 1);
  EXPECT(render_at(0.65f));
  EXPECT(count_lines("world cell (2,4) selected") == 1);
  {
    zcls::ScopedZoomVisualFar zoom_scope(&fixture.camera);
    EXPECT(!render_at(0));
  }
  EXPECT(count_lines("mw3: world cell") == 2);
  EXPECT(!render_at(3.0f));
  EXPECT(count_lines("world cell (2,4) outside-enumeration") == 1);
}
