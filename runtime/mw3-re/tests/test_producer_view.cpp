#include "check.h"
#include "platform/render3d.h"
#include "gamez/zclass/camera.h"
#include "gamez/zclass/cls_data.h"
#include "gamez/zclass/window.h"
#include "gamez/zerror/zerr.h"
#include "gamez/zmath/zmth_matrix.h"
#include "gamez/zimage/zimg_library.h"
#include "gamez/zimage/zimg_texture.h"
#include "gamez/zmodel/gmod_clip2d.h"
#include "gamez/zmodel/gmod_draw.h"
#include "gamez/zmodel/gmod_cull.h"
#include "gamez/zmodel/gmod_fog.h"
#include "gamez/zmodel/gmod_init.h"
#include "gamez/zmodel/gmod_light.h"
#include "gamez/zrender/zrndr_draw.h"
#include "gamez/zrender/zrndr_fog.h"
#include "gamez/zvideo/zvid_ddd3d.h"

#include <array>
#include <cfenv>
#include <cstdio>
#include <cstring>
#include <functional>
#include <memory>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <vector>
#if defined(_M_X64) || defined(_M_IX86) || defined(__SSE__)
#include <xmmintrin.h>
#endif

namespace {
using platform::ProducerPurpose;
using platform::ProducerView;
struct CpuCase {
  const char* name;
  unsigned assertions = 0;
  explicit CpuCase(const char* n) : name(n) {}
  void check(bool value, const char* label) {
    ++assertions;
    if (!value) std::printf("B5_ASSERT %s\n", label);
    EXPECT(value);
  }
  ~CpuCase() { std::printf("B5_CPU name=%s assertions=%u\n", name, assertions); }
};
bool bits(float a, float b) {
  uint32_t x, y;
  std::memcpy(&x, &a, 4); std::memcpy(&y, &b, 4);
  return x == y;
}
bool same_record(const ProducerView& a, const ProducerView& b) {
  // All scalar storage in these two frozen subobjects is declared (21 and14
  // four-byte words). Do not compare the padded whole ProducerView object.
  return a.record_version == b.record_version && a.purpose == b.purpose &&
      a.present == b.present && a.producer_generation == b.producer_generation &&
      a.mission_epoch == b.mission_epoch && a.mission.world_index == b.mission.world_index &&
      a.mission.number == b.mission.number &&
      std::memcmp(&a.projection, &b.projection, sizeof(a.projection)) == 0 &&
      std::memcmp(a.camera, b.camera, sizeof(a.camera)) == 0 && bits(a.clip_near, b.clip_near) &&
      a.canvas_available == b.canvas_available && a.camera_rect_available == b.camera_rect_available &&
      a.canvas.x == b.canvas.x && a.canvas.y == b.canvas.y &&
      a.canvas.width == b.canvas.width && a.canvas.height == b.canvas.height &&
      a.camera_rect.x == b.camera_rect.x && a.camera_rect.y == b.camera_rect.y &&
      a.camera_rect.width == b.camera_rect.width && a.camera_rect.height == b.camera_rect.height &&
      std::memcmp(&a.fog, &b.fog, sizeof(a.fog)) == 0 && a.draw_state_fog == b.draw_state_fog;
}
template <typename F> bool throws(F operation) {
  try { operation(); } catch (const std::runtime_error&) { return true; }
  return false;
}
struct Draw {
  ProducerView view;
  platform::DrawState state;
  std::vector<platform::TLVertex> vertices;
};
struct Receipt : platform::DeferredMaterialBinding {};
struct Sink : platform::Render3D {
  ProducerView current{}, expected_prior{};
  uint64_t generation = 1;
  bool throw_exchange = false, throw_material = false, throw_capture = false,
       throw_dispatch = false, failed = false, expect_prior = false,
       restored_before_abandon = false, suppress = false;
  unsigned exchanges = 0, restores = 0, abandons = 0, resets = 0, multi_calls = 0;
  std::vector<Draw> observed, pending, completed;
  std::function<void()> during_dispatch;
  platform::ProducerViewRestoreToken exchange_producer_view(const ProducerView& view) override {
    ++exchanges;
    if (throw_exchange) throw std::runtime_error("exchange failure");
    platform::ProducerViewRestoreToken token;
    token.previous = current;
    token.receiver_cookie = reinterpret_cast<std::uintptr_t>(this);
    token.reset_generation = generation;
    token.active = true;
    current = view;
    return token;
  }
  void restore_producer_view(const platform::ProducerViewRestoreToken& token) noexcept override {
    if (token.active && token.receiver_cookie == reinterpret_cast<std::uintptr_t>(this) &&
        token.reset_generation == generation) {
      ++restores;
      current = token.previous;
    }
  }
  void abandon_producer_work() noexcept override {
    ++abandons;
    restored_before_abandon = !expect_prior || same_record(current, expected_prior);
    pending.clear(); current = {}; failed = true; ++generation;
  }
  void reset_producer_work() noexcept override {
    ++resets; pending.clear(); current = {}; failed = false; ++generation;
  }
  std::shared_ptr<const platform::DeferredMaterialBinding>
  capture_deferred_material_binding(int32_t) override {
    if (throw_capture) throw std::runtime_error("material capture failure");
    return std::make_shared<Receipt>();
  }
  void begin_deferred_material_draw(std::shared_ptr<const platform::DeferredMaterialBinding>) override {
    if (throw_material) throw std::runtime_error("material begin failure");
  }
  bool replaces_model_geometry() const override { return suppress; }
  void draw(platform::Primitive, const platform::TLVertex* vertices, int count,
            const platform::DrawState& state) override {
    if (failed) throw std::runtime_error("sink requires reset");
    Draw d{current, state, std::vector<platform::TLVertex>(vertices, vertices + count)};
    observed.push_back(d); pending.push_back(d);
    // Keep the active callable alive if a nested test clears the installed one.
    if (during_dispatch) { auto operation = during_dispatch; operation(); }
    if (throw_dispatch) throw std::runtime_error("dispatch failure after CPU append");
  }
  void draw_multi(platform::Primitive primitive, const uint32_t* vertices, int sets,
                  int count, const platform::DrawState& state) override {
    ++multi_calls;
    platform::Render3D::draw_multi(primitive, vertices, sets, count, state);
  }
  void drain() override {
    if (!failed) completed.insert(completed.end(), pending.begin(), pending.end());
    pending.clear();
  }
  int32_t create_texture(int, int, const uint8_t*, uint8_t) override { return 0; }
  void release_texture(int32_t) override {}
  void update_texture(int32_t, int, int, const uint8_t*) override {}
  void set_viewport(int, int, int, int) override {}
  void clear(bool, uint8_t, uint8_t, uint8_t) override {}
  void begin_scene() override {}
  void end_scene() override {}
  void set_fog_color(uint8_t, uint8_t, uint8_t) override {}
  void present() override { drain(); }
};
struct Emission {
  zvid::ProducerPurposeScope request;
  zvid::ProducerWorldScope world;
  explicit Emission(ProducerPurpose purpose) : request(purpose), world() { world.begin_emission(); }
};
struct Fixture {
  std::fenv_t fp{};
#if defined(_M_X64) || defined(_M_IX86) || defined(__SSE__)
  unsigned mxcsr = _mm_getcsr();
#endif
  platform::Render3D* old_renderer = zvid::render3d();
  platform::DrawState old_draw = zvid::draw_state();
  zvid::DeviceState old_device = zvid::device_state();
  zvid::DrawBuffers old_buffers = zvid::draw_buffers();
  zmth::Projection old_projection = zmth::projection();
  zmth::View old_view = zmth::view();
  zmth::MatrixStack old_stack = zmth::matrix_stack();
  zmod::Fog old_fog = zmod::fog();
  zmod::DrawState old_model_draw = zmod::draw_state();
  zmod::WalkState old_model_walk = zmod::walk_state();
  zmod::Lighting old_lighting = zmod::lighting();
  zmod::LightList old_lights = zmod::light_list();
  zmod::LightHooks old_light_hooks = zmod::light_hooks();
  zmod::Zones old_zones = zmod::zones();
  zmod::ViewPolygon old_polygon = zmod::view_polygon();
  zcls::SceneWalk old_walk = zcls::scene_walk();
  zcls::WorldRenderHooks old_hooks = zcls::world_render_hooks();
  std::array<platform::TLVertex, 64> old_flat{};
  std::array<uint32_t, 64 * (6 + 2 * (1 + zmod::kShadowSets))> old_multi{};
  ProducerView old_metadata{};
  platform::TLVertex vertices[3] = {{1, 2, .25f, .25f, 0xff123456u, 0xab010203u, .1f, .2f},
      {3, 4, .25f, .25f, 0xff234567u, 0xbc020304u, .3f, .4f},
      {5, 6, .25f, .25f, 0xff345678u, 0xcd030405u, .5f, .6f}};
  zvid::WorkRecord work[3]{};
  zmod::ShadowSets shadows{};
  Sink sink;
  Fixture() {
    std::fegetenv(&fp);
    zvid::set_render3d(nullptr);
    // Metadata is new ownership state: isolate it with explicit reset, never
    // resurrect a queue receipt/cookie from a prior test after invalidation.
    try { Emission e(ProducerPurpose::MainWorld); old_metadata = zvid::capture_producer_view(); }
    catch (const std::runtime_error&) {}
    zvid::reset_producer_transport();
    std::memcpy(old_flat.data(), zvid::flat_buffer(), sizeof(old_flat));
    std::memcpy(old_multi.data(), zvid::multi_buffer(), sizeof(old_multi));
    zvid::draw_state() = {}; zvid::device_state() = {};
    zvid::draw_buffers() = {vertices, work, &shadows};
    zvid::set_render3d(&sink);
    zvid::set_producer_canvas_rect(0, 0, 800, 600);
    zvid::set_producer_camera_rect(0, 0, 800, 600);
    zmod::draw_state().clip.near_z = 1;
    zmod::fog() = {}; zmth::projection() = {}; zmth::view() = {};
    zmth::projection().near_z = 1; zmth::projection().far_z = 100;
    zmth::projection().fx_near = 2; zmth::projection().fy_near = 3;
    zmth::view().camera.m[0] = zmth::view().camera.m[4] = zmth::view().camera.m[8] = 1;
    zmth::reset_stack();
    zcls::world_render_hooks() = {};
    zcls::scene_walk() = {};
    zmod::light_hooks() = {};
    zmod::draw_state().shadows = 0;
    zmod::zones().mode = 0;
  }
  ~Fixture() {
    zvid::set_render3d(nullptr); zvid::reset_producer_transport();
    zvid::producer_mission_changed(old_metadata.mission);
    zvid::set_producer_canvas_rect(old_metadata.canvas.x, old_metadata.canvas.y,
        old_metadata.canvas.width, old_metadata.canvas.height, old_metadata.canvas_available);
    zvid::set_producer_camera_rect(old_metadata.camera_rect.x, old_metadata.camera_rect.y,
        old_metadata.camera_rect.width, old_metadata.camera_rect.height, old_metadata.camera_rect_available);
    zvid::draw_state() = old_draw; zvid::device_state() = old_device;
    zvid::draw_buffers() = old_buffers;
    std::memcpy(zvid::flat_buffer(), old_flat.data(), sizeof(old_flat));
    std::memcpy(const_cast<uint32_t*>(zvid::multi_buffer()), old_multi.data(), sizeof(old_multi));
    zmth::projection() = old_projection; zmth::view() = old_view; zmth::matrix_stack() = old_stack;
    zmod::fog() = old_fog; zmod::draw_state() = old_model_draw; zmod::walk_state() = old_model_walk;
    zmod::lighting() = old_lighting; zmod::light_list() = old_lights;
    zmod::light_hooks() = old_light_hooks; zmod::zones() = old_zones;
    zmod::view_polygon() = old_polygon;
    zcls::scene_walk() = old_walk; zcls::world_render_hooks() = old_hooks;
    zvid::set_render3d(old_renderer);
    std::fesetenv(&fp);
#if defined(_M_X64) || defined(_M_IX86) || defined(__SSE__)
    _mm_setcsr(mxcsr);
#endif
  }
  void point(float id = 1, int alpha = 255) {
    const float v[3] = {id, 2, .25f}; zvid::draw_point(v, 0xffffu, alpha);
  }
  platform::TLVertex* queue(float id, float depth = .25f, const zvid::D3DTexture* texture = nullptr) {
    auto* out = zvid::queue_transparent(6, 3, texture);
    if (out) { std::memcpy(out, vertices, sizeof(vertices)); out[0].sx = id; out[0].sz = depth; }
    return out;
  }
};
// Isolate real texture teardown from any other test's live image resources.
// Only the authored temporary entry/cookie is freed; old libraries/palettes are
// held by value and restored without touching their files or allocations.
struct TextureIsolation {
  std::unique_ptr<zimg::TextureTable> table = std::make_unique<zimg::TextureTable>(zimg::textures());
  zimg::TextureHooks hooks = zimg::texture_hooks();
  std::vector<zimg::Library*> world = std::move(zimg::library_list(0));
  std::vector<zimg::Library*> images = std::move(zimg::library_list(1));
  std::vector<uint16_t*> palettes = std::move(zimg::state().palettes);
  TextureIsolation() {
    zimg::textures() = {}; zimg::texture_hooks() = {};
    zimg::library_list(0).clear(); zimg::library_list(1).clear(); zimg::state().palettes.clear();
  }
  ~TextureIsolation() {
    zimg::textures() = *table; zimg::texture_hooks() = hooks;
    zimg::library_list(0) = std::move(world); zimg::library_list(1) = std::move(images);
    zimg::state().palettes = std::move(palettes);
  }
};
struct CameraFixture {
  zcls::Node camera_node{}, window_node{}, world_node{};
  zcls::Camera camera{};
  zcls::Window window{};
  zcls::World world{};
  zcls::Partition partition{};
  zcls::Partition* rows[1] = {&partition};
  CameraFixture() {
    camera_node.put<int32_t>(0x34, 1); camera_node.data = &camera;
    window_node.put<int32_t>(0x34, 3); window_node.data = &window;
    world_node.put<int32_t>(0x34, 2); world_node.data = &world;
    camera.nodes[0] = &world_node; camera.nodes[1] = &window_node;
    camera.put<float>(0xb0, 1); camera.put<float>(0xb4, 100);
    camera.put<float>(0x18, 30);
    camera.put<float>(0xe8, 1); camera.put<float>(0xec, .8f);
    camera.put<float>(0x1d4, 2); camera.put<float>(0x1d8, 3);
    camera.put<int32_t>(0xf8, 1); camera.put<int32_t>(0x138, 1);
    window.put<int32_t>(8, 160); window.put<int32_t>(12, 120);
    world.rows = rows;
    world.put<float>(0x34, -500); world.put<float>(0x38, -500);
    world.put<float>(0x44, 500); world.put<float>(0x48, 500);
    world.put<float>(0x64, 1000); world.put<float>(0x68, 1000);
    world.put<float>(0x74, .001f); world.put<float>(0x78, .001f);
    world.put<int32_t>(0x88, 1); world.put<int32_t>(0x8c, 1);
    // Empty authored cell: camera traversal still runs, then puffers can emit.
    partition.put<uint32_t>(4, 0);
  }
  void update(const float* offset = nullptr) {
    zmth::Mat34 local{}; zmth::push(&local);
    zcls::camera_update_offset(&camera_node, offset); zmth::pop();
  }
};
}  // namespace

TEST(b5_view_header_identity) {
  CpuCase c(__func__); Fixture f;
  std::printf("B5_LAYOUT view_bytes=%zu sidecar_bytes=%zu\n", sizeof(ProducerView),
      (zvid::TransparentQueue::kMaxPolys + size_t(zvid::OverlayList::kMax)) * sizeof(ProducerView));
  c.check(std::is_trivially_copyable<ProducerView>::value &&
          std::is_aggregate<platform::MissionIdentity>::value, "NEUTRAL_HEADER_ABI");
  for (int type : {1, 4}) {
    auto id = platform::make_mission_identity(type, 7, 3, true);
    c.check(id.world_index == 7 && id.number == 3, "CAMPAIGN_TRAINING_IDENTITY");
  }
  for (int type : {0, 2, 3, 5}) {
    auto id = platform::make_mission_identity(type, 7, 3, true);
    c.check(id.world_index == -1 && id.number == 0, "NONCAMPAIGN_IDENTITY");
  }
  c.check(platform::make_mission_identity(1, 7, 3, false).world_index == -1, "FAILED_IDENTITY");
  zvid::producer_mission_changed({7, 3});
  Emission e(ProducerPurpose::MainWorld); f.point();
  c.check(f.sink.observed.back().view.mission.world_index == 7 &&
          f.sink.observed.back().view.mission.number == 3, "MISSION_CAPTURE");
}

TEST(b5_view_deferred_late_attach) {
  CpuCase c(__func__); Fixture f;
  ProducerView expected;
  zvid::set_render3d(nullptr);
  {
    Emission e(ProducerPurpose::MainWorld);
    zmth::view().camera.m[9] = 37;
    zmod::fog().on = 0;
    expected = zvid::capture_producer_view();
    auto* vertices = f.queue(41);
    c.check(vertices != nullptr, "DEFERRED_QUEUE_ADMISSION");
  }
  zmth::view().camera.m[9] = -99; zmth::projection().fx_near = 999;
  zmod::fog().near_range = 123; zvid::set_producer_canvas_rect(9, 8, 7, 6);
  zvid::set_render3d(&f.sink); zvid::flush_transparent();
  c.check(f.sink.observed.size() == 1 && same_record(f.sink.observed[0].view, expected),
          "DEFERRED_OWNED_VALUE");
  c.check(!f.sink.observed[0].view.draw_state_fog && f.sink.observed[0].state.texture == -1,
          "UNTEXTURED_LIGHTING_OFF_CAPTURE");
  c.check(bits(f.sink.observed[0].vertices[0].sx, 41) &&
          f.sink.observed[0].vertices[1].diffuse == f.vertices[1].diffuse &&
          f.sink.observed[0].vertices[1].specular == f.vertices[1].specular, "DEFERRED_TL_BYTES");
  c.check(zvid::transparent_queue().count == 0 && zvid::transparent_queue().vertex_count == 0,
          "DEFERRED_CONSUMED");
}

TEST(b5_view_immediate_scope) {
  CpuCase c(__func__); Fixture f;
  Emission main(ProducerPurpose::MainWorld);
  auto expected = zvid::capture_producer_view();
  f.point(1);
  c.check(same_record(f.sink.observed.back().view, expected), "IMMEDIATE_OPAQUE_OWNED");
  {
    Emission zoom(ProducerPurpose::WorldZoom); f.point(2);
    c.check(f.sink.observed.back().view.purpose == ProducerPurpose::WorldZoom &&
        f.sink.observed.back().view.producer_generation != expected.producer_generation,
        "NESTED_TYPED_PURPOSE");
  }
  f.point(3);
  c.check(same_record(f.sink.observed.back().view, expected), "NESTED_EMISSION_RESTORED");
  {
    const zvid::ProducerWorldScope original(true); f.point(4);
    c.check(!f.sink.observed.back().view.present, "UNTYPED_SUBTREE_ORIGINAL");
  }
  const float mask[9] = {0,0,.5f, 1,0,.5f, 0,1,.5f};
  zvid::clear_fan(mask, 3);
  c.check(!f.sink.observed.back().view.present && f.sink.observed.back().state.blend &&
      !f.sink.observed.back().state.fog, "CLEAR_MASK_ORIGINAL");
  zvid::set_native_sky(true); f.point(5);
  c.check(f.sink.observed.back().state.native_sky, "SKY_CLASSIFICATION_UNCHANGED");
  zvid::set_native_sky(false);
  f.shadows.count = 1;
  zvid::D3DTexture base{}, shadow{}; base.handle = 3; shadow.handle = 4;
  f.shadows.texture[0] = &shadow;
  for (auto& w : f.work) w.color[0] = w.color[1] = w.color[2] = 255;
  const auto before = f.sink.observed.size(); zvid::draw_shadowed(3, &base);
  c.check(f.sink.multi_calls == 2 && f.sink.observed.size() == before + 2, "MULTI_PASS_COUNT");
  c.check(f.sink.observed[before].view.purpose == ProducerPurpose::MainWorld &&
      f.sink.observed[before+1].view.purpose == ProducerPurpose::MainWorld &&
      f.sink.observed[before+1].state.multiply && !f.sink.observed[before+1].view.draw_state_fog,
      "MULTI_IMMEDIATE_OWNED");
  c.check(!f.sink.current.present && f.sink.restores == f.sink.exchanges, "IMMEDIATE_PRIOR_RESTORED");
}

TEST(flare_diagnostic_survives_sorted_queues_and_restores_scope) {
  Fixture f;
  zvid::D3DTexture texture{};
  texture.handle = 7;
  texture.type = 4;
  {
    const zvid::FlareDiagnosticScope outer(0, 16);
    EXPECT(f.queue(10, .75f, &texture) != nullptr);
    {
      const zvid::FlareDiagnosticScope inner(1, 8);
      EXPECT(f.queue(20, .25f, &texture) != nullptr);
      zvid::draw_textured_white(3, &texture, 0, .5f, 1);
    }
    EXPECT(zvid::draw_state().flare_diagnostic.slot == 0);
    EXPECT(bits(zvid::draw_state().flare_diagnostic.half_size_pixels, 16));
  }
  EXPECT(zvid::draw_state().flare_diagnostic.slot == -1);
  // Flush under a different live label: the queue must retain each producer's
  // value and attach the actual queue, rather than inheriting this scope.
  {
    const zvid::FlareDiagnosticScope unrelated(3, 99);
    zvid::flush_transparent();
    zvid::flush_overlay();
  }
  EXPECT(f.sink.observed.size() == 3);
  if (f.sink.observed.size() == 3) {
    const auto &near_draw = f.sink.observed[0];
    const auto &far_draw = f.sink.observed[1];
    const auto &overlay = f.sink.observed[2];
    EXPECT(bits(near_draw.vertices[0].sx, 20) && bits(far_draw.vertices[0].sx, 10));
    EXPECT(near_draw.state.flare_diagnostic.slot == 1 && far_draw.state.flare_diagnostic.slot == 0);
    EXPECT(bits(near_draw.state.flare_diagnostic.half_size_pixels, 8));
    EXPECT(bits(far_draw.state.flare_diagnostic.half_size_pixels, 16));
    EXPECT(near_draw.state.queue == platform::DrawQueue::Transparent);
    EXPECT(far_draw.state.queue == platform::DrawQueue::Transparent);
    EXPECT(overlay.state.queue == platform::DrawQueue::Overlay);
    EXPECT(overlay.state.flare_diagnostic.slot == 1);
  }
  EXPECT(f.queue(30) != nullptr);
  zvid::flush_transparent();
  EXPECT(f.sink.observed.back().state.flare_diagnostic.slot == -1);
  f.point();
  EXPECT(f.sink.observed.back().state.queue == platform::DrawQueue::Immediate);
  EXPECT(f.sink.observed.back().state.flare_diagnostic.slot == -1);
  try {
    const zvid::FlareDiagnosticScope failing(2, 24);
    throw std::runtime_error("scope unwind");
  } catch (const std::runtime_error&) {}
  EXPECT(zvid::draw_state().flare_diagnostic.slot == -1);
}

TEST(flare_sprite_clipping_is_distinct_from_unavailable_device) {
  Fixture f;
  const int32_t old_active = zrndr::device_fog().active;
  zrndr::device_fog().active = 1;
  auto &clip = zmod::draw_state().clip;
  const float edge = 100;
  clip.side_04 = clip.side_08 = 0;
  std::memcpy(&clip.side_1c, &edge, sizeof(edge));
  std::memcpy(&clip.side_20, &edge, sizeof(edge));
  const float positions[][3] = {{110, 50, .99f}, {-11, 50, .99f},
                                 {50, 110, .99f}, {50, -11, .99f}};
  for (const auto &position : positions)
    EXPECT(zrndr::draw_sprite(position, nullptr, 10, .5f, 0) == zrndr::SpriteDrawResult::Clipped);
  const float center[3] = {50, 50, .99f};
  EXPECT(zrndr::draw_sprite(center, nullptr, .5f, .5f, 0) == zrndr::SpriteDrawResult::Clipped);
  zrndr::device_fog().active = 0;
  EXPECT(zrndr::draw_sprite(center, nullptr, 10, .5f, 0) == zrndr::SpriteDrawResult::Unavailable);
  zrndr::device_fog().active = old_active;
  EXPECT(f.sink.observed.empty() && zvid::transparent_queue().count == 0);
}

TEST(b5_view_canvas_camera) {
  CpuCase c(__func__); Fixture f; CameraFixture camera;
  zvid::set_render3d(nullptr);
  zvid::set_producer_canvas_rect(10, 20, 800, 600);
  zcls::window_set_origin(&camera.window_node, 31, 47);
  zcls::window_set_size(&camera.window_node, 160, 120);
  camera.update(); zmod::set_camera(&camera.camera);
  Emission e(ProducerPurpose::WorldZoom);
  const float offset[3] = {100, 0, -200}; camera.update(offset);
  const auto expected = zvid::capture_producer_view(); f.queue(9);
  c.check(expected.canvas_available && expected.canvas.x == 10 && expected.canvas.width == 800 &&
          expected.camera_rect_available && expected.camera_rect.x == 31 &&
          expected.camera_rect.y == 47 && expected.camera_rect.width == 160,
          "CANVAS_CAMERA_DISTINCT");
  c.check(std::memcmp(expected.camera, zmth::view().camera.m, sizeof(expected.camera)) == 0 &&
          (bits(expected.camera[9], 100) && bits(expected.camera[11], -200)), "ALREADY_ADJUSTED_CAMERA");
  camera.update(); zvid::set_producer_camera_rect(0, 0, 4, 4);
  zvid::set_producer_canvas_rect(0, 0, 3, 3);
  zvid::set_render3d(&f.sink); zvid::flush_transparent();
  c.check(same_record(f.sink.observed.back().view, expected), "VIEWPORT_POISON_OWNED");
}

TEST(b5_view_neutral_bits) {
  CpuCase c(__func__); Fixture f;
  const uint32_t special[] = {0x80000000u, 0x7fc12345u, 0x7f800000u, 0xff800000u};
  // Fill every float, not just a representative near/far field. Layout matches
  // are pinned in the capture implementation and the immutable header ABI TU.
  std::array<uint32_t, 21> projection_bits{};
  std::array<uint32_t, 12> camera_bits{};
  for (size_t i=0;i<projection_bits.size();++i) projection_bits[i]=special[i%4];
  for (size_t i=0;i<camera_bits.size();++i) camera_bits[i]=special[(i+1)%4];
  std::memcpy(&zmth::projection(), projection_bits.data(), sizeof(zmth::Projection));
  std::memcpy(zmth::view().camera.m, camera_bits.data(), sizeof(camera_bits));
  zmod::fog().on = 1; zmod::fog().linear = 1;
  zmod::fog().near_range = zmod::fog().far_range = 7;
  zmod::fog().inv_range = 91; zmod::fog().alt_high = zmod::fog().alt_low = 4;
  zmod::fog().inv_alt = -83;
  std::memcpy(&zmod::fog().density, &special[1], 4);
  for (int i=0;i<3;++i) std::memcpy(&zmod::fog().color[i], &special[i], 4);
  const auto authored = zmod::fog();
  zvid::set_producer_canvas_rect(0,0,0,0,false);
  zvid::set_producer_camera_rect(0,0,0,0,false);
  Emission e(ProducerPurpose::MainWorld);
  zmod::fog().on = 0; zvid::draw_state().fog = false;
  std::fesetround(FE_DOWNWARD); std::feclearexcept(FE_ALL_EXCEPT); std::feraiseexcept(FE_INEXACT);
  const int flags = std::fetestexcept(FE_ALL_EXCEPT), rounding = std::fegetround();
  const auto value = zvid::capture_producer_view();
  c.check(std::fetestexcept(FE_ALL_EXCEPT) == flags && std::fegetround() == rounding,
          "NEUTRAL_COPY_FP_STATE");
  c.check(std::memcmp(&value.projection, projection_bits.data(), sizeof(value.projection)) == 0 &&
      std::memcmp(value.camera, camera_bits.data(), sizeof(value.camera)) == 0, "RAW_PROJECTION_CAMERA_BITS");
  c.check(std::memcmp(&value.fog, &authored, sizeof(authored)) == 0 && !value.draw_state_fog,
          "RAW_FOG_BITS");
  c.check(!value.canvas_available && !value.camera_rect_available && value.present,
          "UNAVAILABLE_DOMAIN_NOT_CORRUPTION");
  c.check(throws([] { zvid::ProducerPurposeScope bad(static_cast<ProducerPurpose>(99)); }),
          "CORRUPT_PURPOSE_REJECTED");
  c.check(same_record(zvid::capture_producer_view(), value), "BAD_PURPOSE_STRONG_GUARANTEE");
}

TEST(b5_view_sorted_domains) {
  CpuCase c(__func__); Fixture f; CameraFixture camera;
  struct Context {
    Fixture* f;
    std::vector<int> trace;
    bool callback_original = false, flush_original = true;
  } context{&f, {}, false, true};
  auto& hooks = zcls::world_render_hooks(); hooks.ctx = &context;
  hooks.world_sounds = [](void* p, zcls::Node*) { static_cast<Context*>(p)->trace.push_back(0); };
  hooks.begin_scene = [](void* p) { static_cast<Context*>(p)->trace.push_back(1); };
  hooks.puffers = [](void* p) {
    auto& x = *static_cast<Context*>(p); x.trace.push_back(2);
    x.f->queue(11, .2f); x.f->queue(12, .2f); x.f->queue(13, .1f);
    zvid::draw_flat(0xffffu, 255, 3, 0, 1);
  };
  hooks.flush_transparent = [](void* p) {
    auto& x = *static_cast<Context*>(p); x.trace.push_back(3);
    x.flush_original = x.flush_original && !zvid::capture_producer_view().present;
    zvid::flush_transparent();
  };
  hooks.after_scene = [](void* p, float) {
    auto& x = *static_cast<Context*>(p); x.trace.push_back(4);
    x.callback_original = !zvid::capture_producer_view().present;
    x.f->queue(33);
  };
  hooks.flush_overlay = [](void* p) {
    static_cast<Context*>(p)->trace.push_back(5); zvid::flush_overlay();
  };
  hooks.end_scene = [](void* p) { static_cast<Context*>(p)->trace.push_back(6); };
  {
    const zvid::ProducerPurposeScope request(ProducerPurpose::MainWorld);
    c.check(zcls::render_world(&camera.camera_node, 1) == 0, "ACTUAL_WORLD_WALK");
  }
  const std::vector<int> expected_trace{0,1,2,3,4,3,5,6};
  c.check(context.trace == expected_trace && context.callback_original && context.flush_original,
          "ORIGINAL_CALLBACK_ORDER_SCOPE");
  c.check(f.sink.observed.size() == 5, "SORTED_DOMAIN_DRAW_COUNT");
  if (f.sink.observed.size() == 5) {
    c.check(bits(f.sink.observed[0].vertices[0].sx, 13) &&
            bits(f.sink.observed[1].vertices[0].sx, 12) &&
            bits(f.sink.observed[2].vertices[0].sx, 11), "SORTED_TIE_ORDER");
    c.check(f.sink.observed[0].view.present && f.sink.observed[1].view.present &&
            f.sink.observed[2].view.present && !f.sink.observed[3].view.present &&
            f.sink.observed[4].view.present, "SORTED_SLOT_DOMAINS");
    c.check(f.sink.observed[0].view.producer_generation == f.sink.observed[4].view.producer_generation,
            "OVERLAY_STORED_VIEW_NOT_RECAPTURED");
    c.check(f.sink.observed[0].vertices[1].diffuse == f.vertices[1].diffuse &&
            f.sink.observed[0].vertices[1].specular == f.vertices[1].specular, "SORTED_NEUTRAL_TL_BYTES");
  }
  c.check(zvid::transparent_queue().order[0] == 0 && zvid::overlay_list().count == 0,
          "SECOND_FLUSH_ORIGINAL_ORDER_STORAGE");
}

TEST(b5_view_nested_failure) {
  CpuCase c(__func__); Fixture f;
  {
    Emission main(ProducerPurpose::MainWorld);
    const auto prior = zvid::capture_producer_view();
    bool nested_restored = false;
    f.sink.during_dispatch = [&] {
      f.sink.during_dispatch = {};
      { Emission zoom(ProducerPurpose::WorldZoom); f.point(2); }
      nested_restored = same_record(f.sink.current, prior);
    };
    f.point(1);
    c.check(nested_restored && !f.sink.current.present, "NESTED_PRIOR_VIEW");
  }
  // Exchange and dispatch failures both see an earlier CPU prefix and queued
  // deferred work. This verifies the real producer->owner abort boundary, not
  // Core's later Scene/pending-local/posted-job implementation.
  for (int mode : {0, 1}) {
    zvid::reset_producer_transport();
    f.sink.completed.clear(); f.sink.observed.clear();
    {
      Emission main(ProducerPurpose::MainWorld);
      f.point(10); f.sink.drain();  // Already completed ownership must survive.
      f.point(11); f.queue(12);
      f.sink.current = zvid::capture_producer_view();
      f.sink.expected_prior = f.sink.current; f.sink.expect_prior = true;
      f.sink.throw_exchange = mode == 0; f.sink.throw_dispatch = mode == 1;
      c.check(throws([&] { f.point(13); }), "IMMEDIATE_FAILURE_PROPAGATED");
      f.sink.throw_exchange = f.sink.throw_dispatch = false;
      c.check(f.sink.restored_before_abandon, "NESTED_PRIOR_VIEW_BEFORE_ABANDON");
      f.sink.drain();
      c.check(f.sink.completed.size() == 1 && f.sink.pending.empty() &&
              zvid::transparent_queue().count == 0 && zvid::overlay_list().count == 0,
              "IMMEDIATE_EXCEPTION_PREFIX_NOT_REPLAYED");
      c.check(throws([&] { f.point(14); }), "CAPTURE_FAILURE_LATCH_BLOCKS_DISPATCH");
    }
    zvid::reset_producer_transport(); f.sink.expect_prior = false;
    { Emission resumed(ProducerPurpose::MainWorld); f.point(15); }
    c.check(!f.sink.failed && f.sink.pending.size() == 1, "EXPLICIT_RESET_ONLY_RESUME");
  }
  zvid::reset_producer_transport();
  {
    Emission main(ProducerPurpose::MainWorld);
    f.point(20); zvid::D3DTexture texture{}; texture.handle = 7;
    f.queue(21, .2f, &texture); zvid::draw_flat(0xffffu, 255, 3, 0, 1);
    f.sink.current = zvid::capture_producer_view();
    f.sink.expected_prior = f.sink.current; f.sink.expect_prior = true;
    f.sink.throw_material = true;
    c.check(throws([] { zvid::flush_transparent(); }), "MATERIAL_BEGIN_FAILURE_PROPAGATED");
    f.sink.throw_material = false;
    c.check(f.sink.restored_before_abandon && f.sink.pending.empty() &&
            zvid::transparent_queue().count == 0 && zvid::overlay_list().count == 0,
            "ABANDONED_PREFIX_NOT_REPLAYED");
  }
  zvid::reset_producer_transport();
  {
    Emission stale(ProducerPurpose::MainWorld);
    zvid::reset_producer_transport();
    c.check(throws([&] { stale.world.begin_emission(); }), "RESET_SCOPE_COOKIE_REJECTED");
  }
  c.check(!zvid::capture_producer_view().present, "STALE_SCOPE_NOT_RESURRECTED");
}

TEST(b5_view_reset_abandon) {
  CpuCase c(__func__); Fixture f;
  zvid::producer_mission_changed({2,3});
  uint64_t first_epoch;
  { Emission main(ProducerPurpose::MainWorld); first_epoch = zvid::capture_producer_view().mission_epoch; f.queue(1); }
  zvid::producer_mission_changed({2,3});
  c.check(zvid::transparent_queue().count == 0, "REPEATED_MISSION_CLEARS_QUEUE");
  {
    Emission main(ProducerPurpose::MainWorld); const auto value = zvid::capture_producer_view();
    c.check(value.mission_epoch != first_epoch && value.mission.number == 3, "REPEATED_MISSION_NEW_EPOCH");
  }
  zvid::producer_mission_changed({});
  {
    Emission main(ProducerPurpose::MainWorld); f.queue(2);
    c.check(zvid::capture_producer_view().mission.world_index == -1, "EMPTY_MISSION_NO_STALE_ID");
    zvid::D3DTexture texture{}; texture.handle = 8; f.sink.throw_capture = true;
    const auto count = zvid::transparent_queue().count;
    const auto vertices = zvid::transparent_queue().vertex_count;
    c.check(throws([&] { f.queue(3, .5f, &texture); }), "ADMISSION_FAILURE_PROPAGATED");
    c.check(zvid::transparent_queue().count == count &&
            zvid::transparent_queue().vertex_count == vertices, "TRANSACTIONAL_NO_PUBLICATION");
    f.sink.suppress = true;
    c.check(f.queue(4, .5f, &texture) == nullptr, "SUPPRESSION_PRECEDES_CAPTURE");
    f.sink.suppress = false; f.sink.throw_capture = false;
  }
  zvid::flush_transparent();
  c.check(f.sink.observed.size() == 1 && bits(f.sink.observed[0].vertices[0].sx, 2), "SLOT_REUSE_NO_STALE_RECEIPT");
  auto& queue = zvid::transparent_queue();
  queue.count = zvid::TransparentQueue::kMaxPolys;
  c.check(zvid::queue_transparent(6,3,nullptr) == nullptr &&
          queue.count == zvid::TransparentQueue::kMaxPolys, "POLYGON_BOUND_NO_PUBLICATION");
  queue.count = 0; queue.vertex_count = zvid::TransparentQueue::kMaxVerts;
  c.check(zvid::queue_transparent(6,3,nullptr) == nullptr && queue.vertex_count == zvid::TransparentQueue::kMaxVerts,
          "VERTEX_BOUND_NO_PUBLICATION");
  queue.vertex_count = 0;
  {
    Emission main(ProducerPurpose::MainWorld); f.queue(5);
    auto& overlays = zvid::overlay_list(); overlays.count = zvid::OverlayList::kMax;
    zvid::draw_flat(0xffffu, 255, 3, 0, 1);
    c.check(overlays.count == zvid::OverlayList::kMax, "OVERLAY_BOUND_NO_PUBLICATION");
    overlays.count = 0;
  }
  Sink detached;
  zvid::invalidate_producer_transport(&detached, false);
  c.check(queue.count == 1, "DETACHED_OWNER_CANNOT_RESET_PRODUCER");
  zvid::set_render3d(nullptr);
  {
    TextureIsolation images;
    struct Witness { bool released = false, cleared_before_release = false; } witness;
    auto& table = zimg::textures(); table.count = 1;
    table.entries[0].state = 1; table.entries[0].surface = &witness;
    zimg::texture_hooks().release = [](void* pointer) {
      auto& w = *static_cast<Witness*>(pointer); w.released = true;
      w.cleared_before_release = zvid::transparent_queue().count == 0 && zvid::overlay_list().count == 0;
    };
    c.check(zimg::textures_free() == 0 && witness.released && witness.cleared_before_release,
            "TEARDOWN_BEFORE_TEXTURE_RELEASE");
  }
  c.check(queue.count == 0 && zvid::overlay_list().count == 0, "NULL_RENDERER_TEARDOWN_CLEARS");
  zvid::reset_producer_transport(); zvid::set_render3d(&f.sink);
  {
    Emission main(ProducerPurpose::MainWorld); f.queue(6);
  }
  zvid::flush_transparent();
  c.check(bits(f.sink.observed.back().vertices[0].sx, 6), "RESET_REUSE_OWNED_VALUE");
}
