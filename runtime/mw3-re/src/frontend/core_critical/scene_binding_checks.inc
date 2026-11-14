void check_scene_bindings(SDL_Window *window, sdlfe::RendererBackend backend) {
  cc_mw3_re::checks::check_scene_binding_slots();
  const auto folder = std::filesystem::temp_directory_path() /
                      ("cc-scene-bindings-" +
                       std::to_string(SDL_GetPerformanceCounter()));
  require(std::filesystem::create_directory(folder),
          "Cannot create Scene binding fixture directory");
  const auto old_projection = zmth::projection();
  const auto old_view = zmth::view();
  const auto old_fog = zmod::fog();
  struct Restore {
    std::function<void()> action;
    ~Restore() { action(); }
  } restore{[&] {
    zmth::projection() = old_projection;
    zmth::view() = old_view;
    zmod::fog() = old_fog;
    std::error_code ignored;
    for (const auto *name : {"mesh.bin", "textures.bin", "normals.bin",
                             "lights.bin"})
      std::filesystem::remove(folder / name, ignored);
    std::filesystem::remove(folder, ignored);
  }};
  struct Environment {
    const char *name;
    std::optional<std::string> prior;
    explicit Environment(const char *value) : name(value) {
      if (const char *old = std::getenv(name))
        prior = old;
    }
    ~Environment() {
      local_light_test_env(name, prior ? prior->c_str() : nullptr);
    }
  } catalog_env("MW34_EFFECT_LIGHT_CATALOG"),
      enabled_env("MW34_EFFECT_LIGHTS"), fixtures_env("MW34_FIXTURE_LIGHTS");
  prepared_fixture::Bytes catalog;
  catalog.value.assign("MWFX1\0\0\0", 8);
  for (unsigned value : {1U, 1U, 1U, 1U, 2U, 123U, 0U})
    catalog.u32(value);
  for (float value : {10.f, 1.f, 1.f, 1.f, 1.f, 1.f})
    catalog.f32(value);
  std::ofstream(folder / "lights.bin", std::ios::binary) << catalog.value;
  std::ofstream(folder / "mesh.bin", std::ios::binary)
      << prepared_fixture::mesh(2);
  std::ofstream(folder / "textures.bin", std::ios::binary)
      << prepared_fixture::textures();
  std::ofstream(folder / "normals.bin", std::ios::binary)
      << prepared_fixture::normals(0xffd980d9);
  local_light_test_env("MW34_EFFECT_LIGHT_CATALOG",
                       (folder / "lights.bin").string().c_str());
  local_light_test_env("MW34_EFFECT_LIGHTS", "1");
  local_light_test_env("MW34_FIXTURE_LIGHTS", "0");
  zmth::projection() = {};
  auto &projection = zmth::projection();
  projection.near_z = 1;
  projection.fx_near = projection.fy_near = 16;
  projection.cx = projection.cy = 32;
  projection.far_z = 100;
  const float identity_matrix[12] = {1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0};
  std::memcpy(zmth::view().camera.m, identity_matrix, sizeof identity_matrix);
  zmod::fog() = {};
  require(SDL_SetWindowSize(window, 64, 64) && SDL_SyncWindow(window),
          SDL_GetError());

  std::unique_ptr<zcls::Node, int (*)(zcls::Node *)> root(
      zcls::object3d_create(), zcls::tree_destroy);
  auto *control = zcls::object3d_create(), *panel = zcls::object3d_create();
  require(root && control && panel, "Cannot create Scene binding source nodes");
  require(zcls::object3d_add_child(root.get(), control) == 0 &&
              zcls::object3d_add_child(control, panel) == 0,
          "Cannot link Scene binding source nodes");
  zcls::node_set_name(root.get(), "actor");
  zcls::node_set_name(control, "control");
  zcls::node_set_name(panel, "panel");
  auto source_identity = std::make_shared<zcls::SourceAsset>();
  source_identity->name = "mech_authored.flt";
  source_identity->nodes = {{"actor", 1}, {"control", 1}, {"panel", 1}};
  root->source_asset = control->source_asset = panel->source_asset =
      source_identity;
  root->source_asset_root = true;
  zmod::Model source_model{};
  const uint32_t source_count = 3;
  std::memcpy(source_model.header + 0x14, &source_count, sizeof source_count);
  panel->model = &source_model;
  panel->source_model_vertices = source_count;
  Restore model_pointer{[&] { panel->model = nullptr; }};
  float matrix[12];
  std::memcpy(matrix, identity_matrix, sizeof matrix);
  platform::ModelDrawContext context{};
  context.node = panel;
  context.model_to_camera = context.model_to_world = matrix;
  context.near_z = context.clip_near = .1f;
  context.far_z = 100;
  context.fx_near = context.fy_near = 320;
  context.cx = context.cy = 32;
  context.ordinary = true;

  unsigned scenarios = 0;
  std::vector<std::string> failures;
  for (const char *mode : {"legacy", "cpu-reference"}) {
    try {
    sdlfe::CoreCriticalAssets assets{};
    assets.geometry = mode;
    assets.lighting = "normal";
    assets.textures = (folder / "textures.bin").u8string();
    assets.models.push_back(
        {"authored", "0", (folder / "mesh.bin").u8string(), assets.textures});
    assets.normals.push_back(
        {"authored", "0", (folder / "normals.bin").u8string()});
    auto renderer = make_check_renderer(window, backend, {}, assets);
    renderer->mission_changed({5, 1});
    renderer->set_viewport(0, 0, 64, 64);
    auto *previous_renderer = zvid::render3d();
    Restore render_binding{[&] { zvid::set_render3d(previous_renderer); }};
    zvid::set_render3d(renderer.get());
    auto observe = [&] {
      const auto state = renderer->scene_binding_statistics();
      require(state.supported, "Scene binding observation is unsupported");
      return state;
    };
    auto submit = [&] {
      if (std::string_view(mode) == "legacy") {
        renderer->begin_model_draw(context);
        require(renderer->replaces_model_geometry(),
                "Legacy Scene binding fixture was not admitted");
        renderer->end_model_draw();
      } else {
        require(renderer->submit_prepared_geometry(context, {}) ==
                    cc::geometry::Submission::submitted,
                "CPU-reference Scene binding fixture was not admitted");
      }
    };
    auto read = [&] {
      std::vector<uint32_t> pixels;
      int width = 0, height = 0;
      require(renderer->read_back(&pixels, &width, &height) && width == 64 &&
                  height == 64 && pixels.size() == 64 * 64,
              "Scene binding fixture readback failed");
      return pixels;
    };
    renderer->clear(true, 0, 0, 0);
    renderer->begin_scene();
    submit();
    renderer->end_scene();
    const auto expected = read();
    require((expected.at(20 * 64 + 23) & 0x00ffffff) != 0,
            "Scene binding visible prepared oracle is empty");
    require(renderer->asset_statistics().normal_draws > 0,
            "Scene binding fixture did not reach normal lighting");
    {
      auto flat_assets = assets;
      flat_assets.lighting = "flat";
      auto flat = make_check_renderer(window, backend, {}, flat_assets);
      flat->mission_changed({5, 1});
      flat->set_viewport(0, 0, 64, 64);
      zvid::set_render3d(flat.get());
      flat->clear(true, 0, 0, 0);
      flat->begin_scene();
      if (std::string_view(mode) == "legacy") {
        flat->begin_model_draw(context);
        require(flat->replaces_model_geometry(),
                "Flat Scene binding response control was not admitted");
        flat->end_model_draw();
      } else {
        require(flat->submit_prepared_geometry(context, {}) ==
                    cc::geometry::Submission::submitted,
                "Flat CPU-reference response control was not admitted");
      }
      flat->end_scene();
      std::vector<uint32_t> pixels;
      int width = 0, height = 0;
      require(flat->read_back(&pixels, &width, &height) && width == 64 &&
                  height == 64 && pixels != expected,
              "Authored normal map did not change visible pixel response");
      zvid::set_render3d(renderer.get());
      ++scenarios;
    }

    const uint8_t green[4] = {0, 255, 0, 255};
    const auto handle = renderer->create_texture(1, 1, green, 1);
    platform::DrawState world{};
    world.texture = handle;
    platform::DrawState sharp = world;
    sharp.sharp = true;
    // Local staging retains all four packets until EndScene. A drain makes
    // their storage available deterministically, regardless of worker timing.
    auto warm = [&] {
      renderer->clear(true, 0, 0, 0);
      renderer->begin_scene();
      for (bool hud : {false, true, false, true})
        quad(*renderer, 80, 90, .5f, 0xffffffff, hud ? sharp : world);
      renderer->end_scene();
      const auto warmed = observe();
      require(warmed.recycled_scenes >= 3,
              "Scene binding fixture did not warm reusable packet storage");
    };
    warm();
    renderer->begin_scene(); // Same extent, deliberately no clear.
    const auto before = observe();
    require(before.commands == 0 && before.draws == 0 && before.textures == 0 &&
                before.recycled_scenes >= 2,
            "Scene binding orphan precondition was not reached");
    matrix[11] = 1000; // Every authored vertex lies beyond the far clip.
    submit();
    matrix[11] = 0;
    const auto orphan = observe();
    const unsigned expected_refs = std::string_view(mode) == "legacy" ? 2 : 1;
    require(orphan.commands == 0 && orphan.draws == 0 &&
                orphan.textures == expected_refs,
            "Clipped Scene binding fixture did not create texture-only refs");
    std::fprintf(stderr,
                 "scene-bindings: mode=%s pool=%llu clipped_refs=%llu "
                 "commands=%llu draws=%llu\n",
                 mode, static_cast<unsigned long long>(before.recycled_scenes),
                 static_cast<unsigned long long>(orphan.textures),
                 static_cast<unsigned long long>(orphan.commands),
                 static_cast<unsigned long long>(orphan.draws));
    renderer->end_scene(); // Empty flush, then recycled-storage adoption.
    const auto adopted = observe();
    require(adopted.textures == 0 && adopted.commands == 0 &&
                adopted.draws == 0 &&
                adopted.recycled_scenes < orphan.recycled_scenes,
            "Scene binding fixture did not adopt reusable storage");
    renderer->begin_scene();
    submit(); // Pre-fix: cached slots refer to the discarded orphan Scene.
    renderer->end_scene();
    require(read() == expected,
            "Recycled Scene changed prepared albedo or normal response");
    ++scenarios;

    // BeginScene completes/adopts without flushing when there are no draws.
    // This boundary independently covers adoption's own invalidation instead
    // of letting the empty EndScene flush mask a missing adoption reset.
    warm();
    renderer->begin_scene();
    const auto pool = observe();
    require(pool.recycled_scenes > 0 && pool.commands == 0,
            "Direct adoption fixture has no reusable storage");
    matrix[11] = 1000;
    submit();
    matrix[11] = 0;
    const auto direct_orphan = observe();
    require(direct_orphan.commands == 0 && direct_orphan.draws == 0 &&
                direct_orphan.textures == expected_refs,
            "Direct adoption did not create texture-only refs");
    renderer->begin_scene();
    const auto direct_adopted = observe();
    require(direct_adopted.textures == 0 &&
                direct_adopted.recycled_scenes < direct_orphan.recycled_scenes,
            "Direct orphan adoption precondition was not reached");
    submit();
    renderer->end_scene();
    require(read() == expected,
            "Direct orphan adoption changed albedo or normal response");
    ++scenarios;

    // No-op completion/readback must retain the last frame and be repeatable.
    renderer->drain();
    renderer->drain();
    require(read() == expected, "No-op completion changed Scene pixels");
    require(renderer->hold_frame() && renderer->restore_frame(),
            "Scene binding held-frame restoration failed");
    require(read() == expected, "Held-frame restoration changed Scene pixels");
    ++scenarios;

    // Both numeric slots belong to the packet that captured them. Later
    // same-handle uploads cannot change an older queued packet's pixels.
    const uint8_t red[4] = {255, 0, 0, 255};
    renderer->clear(true, 0, 0, 0);
    renderer->begin_scene();
    quad(*renderer, 2, 12, .5f, 0xffffffff, world);
    renderer->update_texture(handle, 1, 1, red);
    quad(*renderer, 20, 30, .5f, 0xffffffff, sharp);
    renderer->end_scene();
    auto queued = read();
    require(queued.at(6 * 64 + 6) == 0xff00ff00 &&
                queued.at(24 * 64 + 24) == 0xffff0000,
            "Queued old/new texture versions or ordinary/sharp slots changed");
    renderer->begin_scene();
    quad(*renderer, 20, 30, .5f, 0xffffffff, sharp);
    renderer->end_scene();
    require(read() == queued, "Omitted-payload texture reuse changed pixels");
    ++scenarios;

    // Mutation after a command-empty bind must drop that unused snapshot,
    // including its cached slot, before updating or releasing the handle.
    auto clipped = [&] {
      renderer->begin_scene();
      matrix[11] = 1000;
      submit();
      matrix[11] = 0;
      const auto state = observe();
      require(state.commands == 0 && state.draws == 0 && state.textures > 0,
              "Empty-scene mutation precondition was not reached");
    };
    // The authored prepared albedo and this public handle are distinct. Use
    // the CPU-reference native range to bind the mutable public handle.
    if (std::string_view(mode) == "cpu-reference") {
      auto resource = std::make_shared<cc::geometry::Resource>();
      resource->identity = 309;
      resource->vertices = {{-1, -1, 2, 0, 0, 1, 0, 0},
                            {1, -1, 2, 0, 0, 1, 1, 0},
                            {0, 1, 2, 0, 0, 1, .5f, 1}};
      resource->indices = {0, 1, 2};
      resource->ranges = {{0, 3, 0, true, 0}};
      platform::ModelDrawContext native = context;
      native.node = nullptr;
      cc::geometry::Material material;
      material.texture = handle;
      // The earlier sharp red quad wrote depth .5 at (23,20). This
      // reference triangle projects to (16,16),(48,16),(32,48) at depth .05,
      // so clear the independent mutation oracle before its empty bind.
      renderer->clear(true, 0, 0, 0);
      renderer->flush();
      const auto update_background = read();
      require(update_background.at(20 * 64 + 23) == 0xff000000 &&
                  update_background.at(32 * 64 + 32) == 0xff000000,
              "Empty-scene mutation baseline clear failed");
      auto bind_clipped = [&] {
        renderer->begin_scene();
        matrix[11] = 1000;
        require(renderer->submit_model_geometry(resource, native, {material}, {}) ==
                    cc::geometry::Submission::submitted,
                "Mutable CPU-reference fixture was not admitted");
        matrix[11] = 0;
        const auto state = observe();
        require(state.commands == 0 && state.draws == 0 && state.textures == 1,
                "Mutable texture-only reference was not reached");
      };
      bind_clipped();
      renderer->update_texture(handle, 1, 1, green);
      require(observe().textures == 0,
              "Empty-scene upload retained a stale texture snapshot");
      require(renderer->submit_model_geometry(resource, native, {material}, {}) ==
                  cc::geometry::Submission::submitted,
              "Updated CPU-reference fixture was not admitted");
      renderer->end_scene();
      const auto updated_pixels = read();
      std::fprintf(stderr,
                   "scene-bindings: update pixel23,20 baseline=%08x after=%08x "
                   "pixel32,32=%08x reference_depth=%.3f prior_quad_depth=%.3f\n",
                   update_background.at(20 * 64 + 23),
                   updated_pixels.at(20 * 64 + 23),
                   updated_pixels.at(32 * 64 + 32), context.near_z / 2.f, .5f);
      require((updated_pixels.at(20 * 64 + 23) & 0x00ff00) != 0,
              "Empty-scene update lost current texture pixels");
      bind_clipped();
      renderer->release_texture(handle);
      require(observe().textures == 0,
              "Empty-scene release retained a stale texture snapshot");
      renderer->end_scene();
      ++scenarios;
    }
    clipped();
    renderer->reset_scene_resources();
    renderer->mission_changed({5, 1});
    renderer->clear(true, 0, 0, 0);
    renderer->begin_scene();
    submit();
    renderer->end_scene();
    require(read() == expected,
            "Renderer recreation reused stale Scene bindings or upload receipts");
    ++scenarios;
    } catch (const std::exception &error) {
      failures.push_back(std::string(mode) + ": " + error.what());
      std::fprintf(stderr, "scene-bindings: mode=%s FAIL: %s\n", mode,
                   error.what());
      matrix[11] = 0;
    }
  }
  if (!failures.empty())
    throw std::runtime_error("Scene binding scenarios failed: " +
                             failures.front());
  require(scenarios == 13, "Scene binding fixture lost a scenario");
  std::fprintf(stderr, "scene-bindings: scenarios=%u passed\n", scenarios);
}
