// Real producer -> Core append -> retained packet -> backend witnesses. No
// hand-built Scene is used to stand in for a FrameRenderer submission.
namespace producer_view_checks {
using Stage = cc_mw3_re::testing::ProducerViewStage;
using Observation = cc_mw3_re::testing::ProducerViewObservation;
using View = ::platform::ProducerView;
using Purpose = ::platform::ProducerPurpose;

// Cleanup cannot throw through another test exception. The group checks this
// flag after its Session destructors, so cleanup errors cannot become a PASS.
bool cleanup_failed = false;

struct Observer final : cc_mw3_re::testing::ProducerViewObserver {
  static constexpr unsigned capacity = 2048;
  std::vector<Observation> produced;
  std::unique_ptr<Observation[]> consumed{new Observation[capacity]};
  std::atomic<unsigned> used{0};
  std::atomic<bool> overflow{false};
  std::optional<Stage> fail;
  std::function<void(const Observation&)> action;
  void producer(const Observation& value) override {
    produced.push_back(value);
    if (action) action(value);
    if (fail && *fail == value.stage) {
      fail.reset();
      throw std::runtime_error("B5 injected producer observation failure");
    }
  }
  void backend(const Observation& value) noexcept override {
    const auto index = used.fetch_add(1);
    if (index < capacity) consumed[index] = value;
    else overflow.store(true);
  }
  std::vector<Observation> rows(Stage stage, bool worker = false) const {
    std::vector<Observation> result;
    if (worker) {
      const auto count = std::min(used.load(), capacity);
      for (unsigned i = 0; i < count; ++i)
        if (consumed[i].stage == stage) result.push_back(consumed[i]);
    } else {
      for (const auto& value : produced)
        if (value.stage == stage) result.push_back(value);
    }
    return result;
  }
};

struct Emission {
  zvid::ProducerPurposeScope purpose;
  zvid::ProducerWorldScope world;
  explicit Emission(Purpose value = Purpose::MainWorld) : purpose(value), world() {
    world.begin_emission();
  }
};

struct Session {
  ::platform::Render3D* prior = zvid::render3d();
  zvid::DrawBuffers old_buffers = zvid::draw_buffers();
  zvid::DeviceState old_device = zvid::device_state();
  ::platform::DrawState old_draw = zvid::draw_state();
  zmth::Projection old_projection = zmth::projection();
  zmth::View old_view = zmth::view();
  zmod::Fog old_fog = zmod::fog();
  ::platform::TLVertex vertices[3] = {
      {24, 24, .5f, .5f, 0xffffffff, 0xff000000, 0, 0},
      {40, 24, .5f, .5f, 0xffffffff, 0xff000000, 1, 0},
      {24, 40, .5f, .5f, 0xffffffff, 0xff000000, 0, 1}};
  Observer observer;
  std::unique_ptr<cc_mw3_re::VulkanFrameRenderer> renderer;
  Session(SDL_Window* window, sdlfe::RendererBackend backend,
          sdlfe::CoreCriticalAssets assets = {}) {
    zvid::set_render3d(nullptr);
    zvid::reset_producer_transport();
    zvid::draw_buffers().tl = vertices;
    zvid::device_state() = {};
    zvid::draw_state() = {};
    zmth::projection() = {};
    auto& p = zmth::projection();
    p.near_z = 1; p.far_z = 100; p.fx_near = p.fy_near = 32;
    p.cx = p.cy = 32;
    zmth::view().camera = {{1, 0, 0, 0, 1, 0, 0, 0, 1, 7, 8, 9}};
    zmod::fog() = {};
    zvid::set_producer_canvas_rect(0, 0, 64, 64);
    zvid::set_producer_camera_rect(0, 0, 64, 64);
    renderer = make_check_renderer(window, backend, {}, assets);
    renderer->set_viewport(0, 0, 64, 64);
    zvid::set_render3d(renderer.get());
    renderer->mission_changed({5, 1});
    require(cc_mw3_re::testing::observe_producer_views(*renderer, &observer),
            "B5 actual Core observer unsupported");
  }
  ~Session() noexcept {
    if (renderer) {
      // Each successful case explicitly finishes its work. If finish failed,
      // observer removal must not retry the same retained Scene during unwind.
      renderer->abandon_producer_work();
      try {
        cc_mw3_re::testing::observe_producer_views(*renderer, nullptr);
      } catch (const std::exception& error) {
        cleanup_failed = true;
        std::fprintf(stderr, "B5 fixture cleanup failed: %s\n", error.what());
      } catch (...) {
        cleanup_failed = true;
        std::fprintf(stderr, "B5 fixture cleanup failed with a nonstandard exception\n");
      }
      zvid::set_render3d(nullptr);
      // The observer remains alive while a failed worker is joined by the
      // renderer destructor, even if removing it could not finish draining.
      renderer.reset();
    }
    zvid::set_render3d(nullptr);
    zvid::reset_producer_transport();
    zvid::draw_buffers() = old_buffers;
    zvid::device_state() = old_device;
    zvid::draw_state() = old_draw;
    zmth::projection() = old_projection;
    zmth::view() = old_view;
    zmod::fog() = old_fog;
    zvid::set_render3d(prior);
  }
  void immediate() { zvid::draw_flat(0xffff, 255, 3, 0, 0); }
  void queued(float id = 24) {
    auto* target = zvid::queue_transparent(6, 3, nullptr);
    require(target != nullptr, "B5 authored producer queue refused");
    std::memcpy(target, vertices, sizeof vertices);
    target[0].sx = id;
  }
  void poison() {
    zmth::projection().fx_near = 99;
    zmth::view().camera.m[9] = 999;
    renderer->set_viewport(0, 0, 256, 256);
  }
  void finish() {
    renderer->drain();
    require(!observer.overflow.load(), "B5 bounded backend observer overflow");
  }
};

struct Environment {
  const char* name;
  std::optional<std::string> old;
  explicit Environment(const char* value) : name(value) {
    if (const auto* prior = std::getenv(name)) old = prior;
  }
  ~Environment() { local_light_test_env(name, old ? old->c_str() : nullptr); }
};

bool throws(const std::function<void()>& operation) {
  try { operation(); } catch (const std::runtime_error&) { return true; }
  return false;
}

void ground_eye(SDL_Window* window, sdlfe::RendererBackend backend,
                const std::function<void(bool, const char*)>& check) {
  using Hook = cc_mw3_re::testing::RigidCaptureTestHook;
  namespace mat = mw34::materials;
  sdlfe::CoreCriticalAssets assets;
  assets.lighting = "normal";
  assets.pom = true;
  Session s(window, backend, assets);
  std::vector<uint32_t> albedo(16, 0xff88aa88);
  // SurfaceKey authenticates the original RGB565 source, not an arbitrary
  // fixture label or the RGBA8 upload-version hash. Match the real upload.
  const auto key = mat::canonical_upload_key(
      4, 4, reinterpret_cast<const uint8_t*>(albedo.data()), 1);
  mw34::materials::set_active_surface_key(key);
  zvid::D3DTexture texture;
  texture.handle = s.renderer->create_named_texture(
      "ggter1", 4, 4, reinterpret_cast<const uint8_t*>(albedo.data()), 1);
  mw34::materials::clear_active_surface_key();
  mat::WorldNormalCache::TextureRecord normal;
  normal.name = "ggter1_n"; normal.width = normal.height = 4;
  normal.pixels32.assign(16, 0xff8080ff);
  normal.hash = mat::normal_hash(normal.pixels32.data(), normal.pixels32.size() * 4);
  Hook::seed_authored_normal(*s.renderer, key, normal);

  std::array<float, 12> positions{-1, -1, 3, 1, -1, 3, 1, 1, 3, -1, 1, 3};
  std::array<float, 12> normals{0, 0, -1, 0, 0, -1, 0, 0, -1, 0, 0, -1};
  std::array<float, 8> uv{0, 0, 1, 0, 1, 1, 0, 1};
  std::array<uint32_t, 4> indices{0, 1, 2, 3};
  zimg::TextureEntry entry{};
  std::strcpy(entry.name, "ggter1"); entry.surface = &texture;
  zmod::Material material{};
  material.alpha = 255; material.flags = 1; material.texture = &entry;
  zmod::Polygon polygon{};
  polygon.flags = 4 | 0x200; polygon.material = &material;
  polygon.vertex_indices = polygon.normal_indices = indices.data(); polygon.uvs = uv.data();
  zmod::Model model{};
  model.vertices = positions.data(); model.normals = normals.data(); model.polygons = &polygon;
  const uint32_t one = 1, four = 4;
  std::memcpy(model.header + 0x10, &one, 4);
  std::memcpy(model.header + 0x14, &four, 4);
  std::memcpy(model.header + 0x18, &four, 4);
  if (!zcls::world_source_epoch())
    require(zcls::invalidate_world_source_proofs() != 0, "Cannot initialize authored source epoch");
  auto source = std::make_shared<zcls::SourceAsset>();
  source->name = "world/t1m1.zbd";
  zcls::WorldSourceIdentity identity;
  identity.kind = "gamez-zbd-v27"; identity.member = "t1m1_ground.zmd";
  identity.sha256 = std::string(64, 'a'); identity.bytes = 4096;
  identity.model_slot = 7; identity.load_epoch = zcls::world_source_epoch();
  source->world = identity; model.world_source_asset = source;
  zcls::Node node{};
  node.model = &model; node.source_asset = source; node.put<int32_t>(0x3c, 7);
  const auto hash = cc_mw3_re::native_mesh_uv_hash(model);
  require(hash.has_value(), "B5 ground source hash missing");
  const auto budget = Hook::surface_budget(*s.renderer);
  auto pack = std::make_shared<mat::SurfaceMaterialPack>();
  pack->version = 1; pack->mesh_uv_hash = *hash;
  pack->decoded_reservation = std::make_shared<mat::SurfaceDecodedReservation>(budget);
  mat::SurfaceMaterialImage height;
  height.name = "ggter1_h"; height.role = mat::surface_role_height;
  height.width = height.height = 4; height.pixels.assign(16, 128);
  height.hash = mat::normal_hash(height.pixels.data(), height.pixels.size() * 4);
  pack->decoded_reservation->grow(height.pixels.size() * sizeof(uint32_t));
  pack->images.push_back(std::move(height));
  auto record = std::make_shared<mat::SurfaceMaterialRecord>();
  record->asset_id = "env:t1m1_ground"; record->material_name = "ggter1";
  record->height_image = 0; record->height_amplitude = record->max_displacement = .25f;
  pack->records.push_back(record); pack->bindings.push_back(0);
  ::platform::prepared::MaterialTarget target;
  target.asset_id = record->asset_id;
  target.source.kind = identity.kind; target.source.member = identity.member;
  target.source.sha256 = identity.sha256; target.source.bytes = identity.bytes;
  target.source.model_slot = identity.model_slot;
  target.mesh_uv_hash = *hash; target.sidecar_path = "env/t1m1_ground.bwsfm1";
  target.sidecar_sha256 = std::string(64, 'b');
  target.polygon_materials.push_back("ggter1"); target.surface_keys.push_back(key); target.pack = pack;
  auto environment = std::make_shared<::platform::prepared::EnvironmentSelection>();
  environment->material_targets[::platform::prepared::environment_region("t1m1")].push_back(target);
  Hook::set_mission_and_environment(*s.renderer, "t1m1", environment);
  const float matrix[12] = {1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0};
  ::platform::ModelDrawContext context{};
  context.node = &node; context.model_to_world = context.model_to_camera = matrix;
  context.near_z = context.clip_near = 1; context.far_z = 100;
  context.fx_near = context.fy_near = 32; context.cx = context.cy = 32;
  context.ordinary = true; context.opacity = 1;
  context.source_vertices = 4; context.source_polygons = 1;
  ::platform::MaterialDrawContext material_context{&model, &material, &entry, 0};
  View expected;
  {
    Emission emission;
    expected = zvid::capture_producer_view();
    s.renderer->begin_model_draw(context);
    s.renderer->begin_material_draw(material_context);
    s.observer.action = [&](const Observation& event) {
      if (event.stage == Stage::exchange) s.poison();
    };
    zvid::draw_textured_white(3, &texture, 0, 1.f, 0);
    s.observer.action = {};
    s.renderer->end_material_draw(); s.renderer->end_model_draw();
  }
  const auto rows = s.observer.rows(Stage::append);
  check(rows.size() == 1 && rows[0].height_binding && rows[0].sun_tl, "ACTUAL_POM_ADMISSION");
  check(rows[0].surface_eye == std::array<float, 4>{7, 8, 9, 1}, "POM_CAPTURED_EYE");
  check(::platform::same_producer_view_bits(rows[0].view, expected), "POM_VIEW_OWNED");
  s.finish();
}
} // namespace producer_view_checks

void check_producer_views(SDL_Window* window, sdlfe::RendererBackend backend) {
  using namespace producer_view_checks;
  require(SDL_SetWindowSize(window, 64, 64) && SDL_SyncWindow(window), SDL_GetError());
  Environment effect("MW34_EFFECT_LIGHTS"), catalog("MW34_EFFECT_LIGHT_CATALOG"),
      fixtures("MW34_FIXTURE_LIGHTS"), combine("MW34_TL_COMBINE");
  local_light_test_env("MW34_EFFECT_LIGHTS", "0");
  local_light_test_env("MW34_FIXTURE_LIGHTS", "0");
  local_light_test_env("MW34_TL_COMBINE", "1");
  unsigned groups = 0, total = 0, assertions = 0;
  const auto check = [&](bool ok, const char* label) {
    ++assertions; ++total; require(ok, label);
  };
  const auto group = [&](const char* name, const std::function<void()>& body) {
    assertions = 0;
    cleanup_failed = false;
    try {
      body();
      require(!cleanup_failed, "B5 fixture cleanup failed; see the retained diagnostic");
      require(assertions > 0, "B5 empty packet group");
    } catch (...) {
      std::fprintf(stderr, "B5_PACKET_GROUP name=%s failed=1 assertions=%u\n", name, assertions);
      throw;
    }
    std::printf("B5_PACKET_GROUP name=%s assertions=%u\n", name, assertions);
    ++groups;
  };
  group("immediate_opaque", [&] {
    Session s(window, backend);
    View expected;
    {
      Emission emission;
      expected = zvid::capture_producer_view();
      s.immediate();
    }
    auto rows = s.observer.rows(Stage::append);
    check(rows.size() == 1 && ::platform::same_producer_view_bits(rows[0].view, expected),
          "IMMEDIATE_OPAQUE_OWNED");
    check(!rows[0].sun_tl && !rows[0].height_binding, "UNLIT_ADMISSION_UNCHANGED");
    const auto outer = s.renderer->exchange_producer_view(expected);
    { Emission nested(Purpose::WorldZoom); s.immediate(); }
    const auto restored = s.observer.rows(Stage::restore, true);
    check(!restored.empty() && ::platform::same_producer_view_bits(restored.back().view, expected),
          "NESTED_PRIOR_VIEW");
    s.renderer->restore_producer_view(outer);
    s.finish();
    s.immediate();
    const auto original = s.observer.rows(Stage::append).back();
    check(!original.view.present &&
              std::memcmp(&original.first_vertex, &rows[0].first_vertex,
                          sizeof(::platform::TLVertex)) == 0,
          "NEUTRAL_TL_BYTES");
    s.finish();
  });
  group("deferred_poison_late", [&] {
    Session s(window, backend);
    View expected;
    zvid::set_render3d(nullptr);
    { Emission emission; expected = zvid::capture_producer_view(); s.queued(); }
    s.poison();
    zvid::set_render3d(s.renderer.get());
    zvid::flush_transparent();
    const auto rows = s.observer.rows(Stage::append);
    check(rows.size() == 1 && ::platform::same_producer_view_bits(rows[0].view, expected),
          "DEFERRED_OWNED_VALUE");
    check(rows[0].first_vertex.sx == 24, "POISONED_VIEW_VALUE");
    s.finish();
    const auto packets = s.observer.rows(Stage::packet, true);
    check(packets.size() == 1 && ::platform::same_producer_view_bits(packets[0].view, expected),
          "WORKER_OWNED_VALUE");
  });
  group("viewport_domains", [&] {
    sdlfe::CoreCriticalAssets assets;
    assets.lighting = "flat";
    Session s(window, backend, assets);
    zvid::set_producer_canvas_rect(10, 20, 128, 64);
    zvid::set_producer_camera_rect(18, 24, 32, 24);
    const mw34::materials::SurfaceKey key{1, 1, 1, 0x12345678};
    const uint8_t pixel[4] = {255, 255, 255, 255};
    mw34::materials::set_active_surface_key(key);
    zvid::D3DTexture texture;
    texture.handle = s.renderer->create_texture(1, 1, pixel, 1);
    mw34::materials::clear_active_surface_key();
    View expected;
    { Emission emission(Purpose::WorldZoom);
      expected = zvid::capture_producer_view();
      zvid::draw_textured_white(3, &texture, 0, 1.f, 1);
    }
    s.poison();
    zvid::flush_overlay();
    const auto rows = s.observer.rows(Stage::append);
    check(rows.size() == 1 && rows[0].view.canvas.width == 128 &&
              rows[0].view.camera_rect.width == 32, "VIEWPORT_DOMAINS");
    check(rows[0].first_vertex.sx == 7 && rows[0].first_vertex.sy == 4,
          "CAPTURED_CANVAS_MAPPING");
    check(rows[0].sun_tl && rows[0].projection[1] == 16 &&
              rows[0].camera_world[3] == 7, "POISONED_VIEW_VALUE");
    // This is a buffered 2D overlay draw, which spans the scene even during a
    // WorldZoom emission; only the zoom camera's 3D geometry gets the zoom rect.
    check(rows[0].scissor_offset == std::array<std::int32_t, 2>{0, 0} &&
              rows[0].scissor_extent == std::array<std::uint32_t, 2>{64, 64},
          "ZOOM_OVERLAY_FULL_SCISSOR");
    check(::platform::same_producer_view_bits(rows[0].view, expected), "ZOOM_VIEW_OWNED");
    { Emission main_world(Purpose::MainWorld); s.immediate(); }
    auto main_rows = s.observer.rows(Stage::append);
    check(main_rows.back().scissor_offset == std::array<std::int32_t, 2>{0, 0} &&
              main_rows.back().scissor_extent == std::array<std::uint32_t, 2>{64, 64},
          "MAIN_WORLD_FULL_SCISSOR");
    ::platform::DrawState hud_state{};
    hud_state.sharp = true;
    { Emission zoom(Purpose::WorldZoom);
      s.renderer->draw(::platform::Primitive::kFan, s.vertices, 3, hud_state); }
    auto hud_rows = s.observer.rows(Stage::append);
    check(hud_rows.back().scissor_offset == std::array<std::int32_t, 2>{0, 0} &&
              hud_rows.back().scissor_extent == std::array<std::uint32_t, 2>{64, 64},
          "HUD_FULL_SCISSOR");
    s.finish();
    ground_eye(window, backend, check);
  });
  group("native_geometry_zoom_scissor", [&] {
    float positions[]{-1, -1, 3, 1, -1, 3, 0, 1, 3};
    std::uint32_t indices[]{2, 1, 0};
    const auto source = cc::geometry::register_resource(
        positions, 3, nullptr, 0,
        {{3, indices, nullptr, nullptr, false, true}});
    cc::geometry::Material material;
    material.color = 0xffffffff;
    const float transform[]{1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0};
    ::platform::ModelDrawContext context{};
    context.model_to_world = context.model_to_camera = transform;
    context.near_z = context.clip_near = 1;
    context.far_z = 100;
    context.fx_near = context.fy_near = 32;
    context.cx = context.cy = 32;
    context.ordinary = true;
    context.opacity = 1;
    for (const char* geometry : {"partial", "cpu-reference"}) {
      sdlfe::CoreCriticalAssets assets;
      assets.geometry = geometry;
      Session s(window, backend, assets);
      zvid::set_producer_canvas_rect(10, 20, 128, 64);
      zvid::set_producer_camera_rect(18, 24, 32, 24);
      {
        Emission emission(Purpose::WorldZoom);
        const auto restore = s.renderer->exchange_producer_view(
            zvid::capture_producer_view());
        check(s.renderer->submit_model_geometry(source, context, {material}, {}) ==
                  cc::geometry::Submission::submitted,
              "WORLD_ZOOM_RIGID_MODEL_NOT_SUBMITTED");
        s.renderer->restore_producer_view(restore);
      }
      s.finish();
      const auto rows = s.observer.rows(Stage::packet, true);
      check(std::any_of(rows.begin(), rows.end(), [](const Observation& row) {
              return row.scissor_offset == std::array<std::int32_t, 2>{4, 4} &&
                     row.scissor_extent == std::array<std::uint32_t, 2>{16, 24};
            }),
            geometry[0] == 'p' ? "GPU_GEOMETRY_ZOOM_SCISSOR" :
                                 "REFERENCE_GEOMETRY_ZOOM_SCISSOR");
    }
  });
  group("neutral_numeric_fallback", [&] {
    Session s(window, backend);
    const uint32_t nan_bits = 0x7fc12345;
    std::memcpy(&zmod::fog().density, &nan_bits, 4);
    zmod::fog().near_range = zmod::fog().far_range = 9;
    zmod::fog().inv_range = 123;
    zmth::projection().inv_near = -0.f;
    zmth::view().camera.m[0] = std::numeric_limits<float>::infinity();
    View expected;
    std::fenv_t saved{};
    std::fegetenv(&saved);
    std::feclearexcept(FE_ALL_EXCEPT);
    std::feraiseexcept(FE_DIVBYZERO);
    const auto flags = std::fetestexcept(FE_ALL_EXCEPT);
    { Emission emission; expected = zvid::capture_producer_view(); s.immediate(); }
    check(std::fetestexcept(FE_ALL_EXCEPT) == flags, "RAW_FOG_FP_STATE");
    std::fesetenv(&saved);
    const auto rows = s.observer.rows(Stage::append);
    check(::platform::same_producer_view_bits(rows.back().view, expected) &&
              rows.back().view.fog.inv_range == 123, "RAW_FOG_BITS");
    auto invalid = expected;
    invalid.record_version = 99;
    const auto prior = s.renderer->exchange_producer_view(expected);
    check(throws([&] { s.renderer->exchange_producer_view(invalid); }), "CORRUPT_PROVENANCE_FAILS");
    const auto restored = s.renderer->exchange_producer_view({});
    check(::platform::same_producer_view_bits(restored.previous, expected), "STRONG_EXCHANGE");
    s.renderer->restore_producer_view(restored);
    s.renderer->reset_producer_work();
    s.renderer->restore_producer_view(prior);
    s.renderer->draw(::platform::Primitive::kFan, s.vertices, 3, {});
    check(!s.observer.rows(Stage::append).back().view.present, "STALE_COOKIE_NO_RESURRECTION");
    s.finish();
    sdlfe::CoreCriticalAssets lit_assets;
    lit_assets.lighting = "flat";
    Session fallback(window, backend, lit_assets);
    const mw34::materials::SurfaceKey key{1, 1, 1, 0x76543210};
    const uint8_t white[4] = {255, 255, 255, 255};
    mw34::materials::set_active_surface_key(key);
    zvid::D3DTexture texture;
    texture.handle = fallback.renderer->create_texture(1, 1, white, 1);
    mw34::materials::clear_active_surface_key();
    zmth::projection().near_z = -1;
    zvid::set_producer_canvas_rect(0, 0, 0, 0, false);
    zvid::set_producer_camera_rect(0, 0, 0, 0, false);
    { Emission emission; zvid::draw_textured_white(3, &texture, 0, 1.f, 0); }
    const auto fallback_rows = fallback.observer.rows(Stage::append);
    check(fallback_rows.size() == 1 && fallback_rows[0].sun_tl &&
              fallback_rows[0].projection[0] == 1 &&
              !fallback_rows[0].view.canvas_available &&
              !fallback_rows[0].view.camera_rect_available,
          "NEUTRAL_NUMERIC_FALLBACK");
    fallback.finish();
  });
  group("append_identity", [&] {
    Session s(window, backend);
    { Emission first; s.immediate(); }
    { Emission second; s.immediate(); }
    const auto rows = s.observer.rows(Stage::append);
    check(rows.size() == 2 && rows.back().scene_draws == 2 &&
              rows[0].view.producer_generation != rows[1].view.producer_generation,
          "APPEND_VIEW_SPLIT");
    s.finish();
  });
  group("backend_combine_identity", [&] {
    Session s(window, backend);
    { Emission first; s.immediate(); }
    { Emission second; s.immediate(); }
    s.finish();
    const auto rows = s.observer.rows(Stage::backend_group, true);
    check(rows.size() == 2 && rows[0].tl_combine && rows[1].tl_combine &&
              rows[0].logical_draws == 1 && rows[1].logical_draws == 1,
          "BACKEND_VIEW_GROUPS");
  });

  const auto folder = std::filesystem::temp_directory_path() /
                      ("b5-packets-" + std::to_string(SDL_GetPerformanceCounter()));
  require(std::filesystem::create_directory(folder), "Cannot create B5 authored light fixture");
  struct Remove { std::filesystem::path path; ~Remove() {
    std::error_code ignored; std::filesystem::remove(path / "lights.bin", ignored);
    std::filesystem::remove(path, ignored);
  }} remove{folder};
  prepared_fixture::Bytes lights;
  lights.value.assign("MWFX1\0\0\0", 8);
  for (unsigned value : {1U, 1U, 1U, 1U, 2U, 123U, 0U}) lights.u32(value);
  for (float value : {10.f, 1.f, 1.f, 1.f, 1.f, 1.f}) lights.f32(value);
  std::ofstream(folder / "lights.bin", std::ios::binary) << lights.value;
  local_light_test_env("MW34_EFFECT_LIGHT_CATALOG", (folder / "lights.bin").string().c_str());
  local_light_test_env("MW34_EFFECT_LIGHTS", "1");
  sdlfe::CoreCriticalAssets lit;
  lit.lighting = "normal";
  group("split_worker_recycle", [&] {
    Session s(window, backend, lit);
    s.renderer->begin_scene();
    View expected;
    { Emission emission;
      expected = zvid::capture_producer_view();
      s.immediate(); s.renderer->flush();
      zvid::draw_state().sharp = true; s.immediate();
      zvid::draw_state().sharp = false; s.immediate();
    }
    s.poison();
    s.renderer->end_scene();
    s.finish();
    const auto staged = s.observer.rows(Stage::local_packet);
    const auto packets = s.observer.rows(Stage::packet, true);
    check(staged.size() >= 3 && packets.size() == staged.size(), "LOCAL_PACKET_WORKER_SPLITS");
    for (const auto& packet : packets)
      check(packet.packet && ::platform::same_producer_view_bits(packet.view, expected),
            "SPLIT_WORKER_VALUE");
    s.renderer->begin_scene();
    { Emission emission(Purpose::WorldZoom); s.immediate(); }
    s.renderer->end_scene(); s.finish();
    check(s.observer.rows(Stage::packet, true).back().view.purpose == Purpose::WorldZoom,
          "RECYCLED_SCENE_FRESH_VALUE");
  });
  group("abandon_no_replay", [&] {
    for (unsigned fault = 0; fault < 4; ++fault) {
      Session s(window, backend, lit);
      // This first real packet is already owned by the worker (or completed by
      // the synchronous backend). Later abandonment must not cancel/replay it.
      { Emission emission; s.immediate(); }
      s.renderer->flush();
      s.renderer->begin_scene();
      View prior;
      {
        Emission emission;
        prior = zvid::capture_producer_view();
        s.immediate(); s.renderer->flush(); // Real pending-local packet.
        s.immediate(); // Real current Scene prefix.
        s.queued();
        if (fault == 0) {
          auto detached = make_check_renderer(window, backend, {}, lit);
          detached->reset_producer_work();
          check(zvid::transparent_queue().count == 1, "DETACHED_OWNER_PRESERVES_QUEUE");
        }
        auto token = s.renderer->exchange_producer_view(prior);
        if (fault == 0) zvid::invalidate_producer_transport(s.renderer.get(), true);
        else s.observer.fail = fault == 1 ? Stage::exchange : Stage::append;
        if (fault == 3) s.observer.fail = Stage::exchange;
        check(throws([&] { if (fault == 3) zvid::flush_transparent(); else s.immediate(); }),
              "INJECTED_PRODUCER_FAILURE");
        s.renderer->restore_producer_view(token);
      }
      const auto abandoned = s.observer.rows(Stage::abandon, true);
      check(!abandoned.empty() && abandoned.back().failed &&
                abandoned.back().scene_draws == 0 && abandoned.back().pending_local_packets == 0 &&
                abandoned.back().upload_receipts == 0 && zvid::transparent_queue().count == 0 &&
                zvid::overlay_list().count == 0,
            fault == 3 ? "ABANDONED_PREFIX_NOT_REPLAYED" : "IMMEDIATE_EXCEPTION_PREFIX_NOT_REPLAYED");
      check(::platform::same_producer_view_bits(abandoned.back().view, prior), "NESTED_PRIOR_VIEW");
      s.finish();
      const auto packets = s.observer.rows(Stage::packet, true);
      check(packets.size() == 1,
            fault == 3 ? "ABANDONED_PREFIX_NOT_REPLAYED" : "IMMEDIATE_EXCEPTION_PREFIX_NOT_REPLAYED");
      check(throws([&] { s.immediate(); }), "FAILURE_LATCH_REQUIRES_RESET");
      s.renderer->reset_producer_work();
      s.renderer->mission_changed({5, 1});
      { Emission emission; s.immediate(); }
      s.finish();
      check(s.observer.rows(Stage::packet, true).size() == 2, "RESET_ONLY_RESUME");
      // Keep the observer alive through the actual destructor's drain path.
      zvid::set_render3d(nullptr);
      s.renderer.reset();
      check(s.observer.rows(Stage::packet, true).size() == 2, "DESTRUCTOR_NO_REPLAY");
    }
  });
  require(groups == 9 && total > 0, "B5 packet group inventory mismatch");
  std::printf("B5_PACKET groups=9 failed=0 assertions=%u\n", total);
}
