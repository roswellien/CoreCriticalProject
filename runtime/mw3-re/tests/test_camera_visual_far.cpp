#include "check.h"

#include "gamez/zclass/camera.h"
#include "gamez/zclass/cls_data.h"
#include "gamez/zmath/zmth_matrix.h"
#include "gamez/zmodel/gmod_cull.h"
#include "gamez/zmodel/gmod_draw.h"
#include "gamez/zmodel/gmod_init.h"
#include "gamez/zmodel/gmod_light.h"
#include "gamez/zvideo/zvid_ddd3d.h"

#include <cmath>
#include <memory>

namespace {
constexpr float kAuthoredFar = 800.0f;

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
  zcls::Partition partition{};
  zcls::Partition* rows[1] = {&partition};
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
    camera.put(0xd8, 1.0f);
    camera.put(0xdc, 1.0f);
    EXPECT(zcls::camera_set_clip(&camera_node, 1.0f, kAuthoredFar) == 0);
    window.put<int32_t>(8, zmod::walk_state().screen_w);
    window.put<int32_t>(12, zmod::walk_state().screen_h);
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
  EXPECT(fixture.camera.get<float>(0x110) == 0.0f);
  for (int i = 0; i < 3; ++i) EXPECT(fixture.camera.floats(0xc4)[i] == 0.0f);

  const CameraFrame frames[] = {
      {1200, {10.0f, 30.0f, 20.0f}, 0.0f, 0.0f, 1.0f, 0.8f},
      {1200, {80.0f, 45.0f, -40.0f}, 0.2f, 0.7f, 1.0f, 0.8f},
      {1600, {80.0f, 45.0f, -40.0f}, -0.1f, -0.5f, 0.9f, 0.6f},
      {800, {-20.0f, 25.0f, 60.0f}, 0.1f, 0.3f, 0.9f, 0.6f}};
  for (const auto& frame : frames) {
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
    EXPECT(zcls::render_world(&fixture.camera_node, 0) == 0);
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
  EXPECT(fixture.observed_passes == 4);
}
