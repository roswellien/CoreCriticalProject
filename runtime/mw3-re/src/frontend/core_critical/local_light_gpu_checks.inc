void local_light_test_env(const char *name, const char *value) {
#ifdef _WIN32
  _putenv_s(name, value ? value : "");
#else
  if (value)
    setenv(name, value, 1);
  else
    unsetenv(name);
#endif
}
// Qwen test structure integrated against the actual native/renderer ABI.
void check_local_light_gpu(SDL_Window *window, sdlfe::RendererBackend backend) {
  const auto old_list = zmod::light_list();
  const auto old_projection = zmth::projection();
  const auto old_view = zmth::view();
  const auto old_clock = ztimer::state();
  struct Env {
    const char *name;
    std::optional<std::string> prior;
    explicit Env(const char *n) : name(n) {
      if (const char *v = std::getenv(n))
        prior = v;
    }
    ~Env() {
      if (prior)
        local_light_test_env(name, prior->c_str());
      else
        local_light_test_env(name, nullptr);
    }
  } catalog_env("MW34_EFFECT_LIGHT_CATALOG"), enabled_env("MW34_EFFECT_LIGHTS"),
      fixtures_env("MW34_FIXTURE_LIGHTS");
  const auto path = std::filesystem::temp_directory_path() /
                    ("mw34-wp04a-" + std::to_string(SDL_GetTicksNS()) + ".bin");
  const auto pack_path = std::filesystem::path(path.string() + ".pack");
  struct Restore {
    std::function<void()> f;
    ~Restore() { f(); }
  } restore{[&] {
    mw34::materials::clear_active_surface_key();
    zmod::light_list() = old_list;
    zmth::projection() = old_projection;
    zmth::view() = old_view;
    ztimer::state() = old_clock;
    std::error_code ignored;
    std::filesystem::remove(path, ignored);
    std::filesystem::remove(pack_path, ignored);
  }};
  auto write_catalog = [&](const std::filesystem::path &catalog_path,
                           uint32_t emitter_hash, uint32_t entry_count = 1,
                           float intensity = 1) {
    std::ofstream f(catalog_path, std::ios::binary);
    auto u32 = [&](uint32_t n) {
      for (unsigned i = 0; i < 4; ++i)
        f.put(char(n >> (i * 8)));
    };
    auto scalar = [&](float n) {
      uint32_t bits;
      std::memcpy(&bits, &n, 4);
      u32(bits);
    };
    f.write("MWFX1\0\0\0", 8);
    u32(entry_count);
    for (uint32_t i = 0; i < entry_count; ++i) {
      u32(1);
      u32(1);
      u32(1);
      u32(2);
      u32(emitter_hash + i);
      u32(0);
      scalar(10);
      scalar(intensity);
      scalar(1);
      scalar(1);
      scalar(1);
      scalar(1);
    }
    f.flush();
    require(bool(f), "Could not write local-light fixture catalog");
  };
  write_catalog(path, 123);
  write_catalog(pack_path, 789);
  auto environment =
      std::make_shared<platform::prepared::EnvironmentSelection>();
  environment->resources["fixture-region"]
                        [platform::prepared::EnvironmentRole::effects] =
      pack_path.string();
  local_light_test_env("MW34_EFFECT_LIGHT_CATALOG", path.string().c_str());
  zmth::projection() = {};
  auto &projection = zmth::projection();
  projection.near_z = 1;
  projection.fx_near = projection.fy_near = 16;
  projection.cx = projection.cy = 16;
  projection.far_z = 100;
  const float camera[12] = {1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0};
  std::memcpy(zmth::view().camera.m, camera, sizeof camera);
  zcls::Light data{};
  data.put<uint32_t>(0xb0, 0x202);
  data.put<float>(0xb8, 10);
  data.put<float>(0x9c, 2);
  data.put<float>(0xa4, 1);
  data.put<float>(0xa8, 1);
  data.put<float>(0xac, 1);
  data.put<float>(0x14, 1);
  const auto original = data;
  zcls::Node node{};
  node.put<int32_t>(0x34, 9);
  node.data = &data;
  zmod::light_list() = {};
  zmod::light_list().count = 1;
  zmod::light_list().list[0].data = &data;
  zmod::light_list().list[0].node = &node;
  auto render = [&](bool enabled, bool mutate, bool weapon_source = false,
                    bool sharp_source = false,
                    bool overlay_before_emitter = false,
                    bool ambient_only = false,
                    bool canvas_transition = false,
                    bool pack_source = false) {
    data = original;
    if (ambient_only) {
      data.put<float>(0x9c, 0);
      data.put<float>(0xa0, 2);
    }
    const auto expected_source = data;
    local_light_test_env("MW34_EFFECT_LIGHTS", enabled ? "1" : "0");
    local_light_test_env("MW34_FIXTURE_LIGHTS",
                         enabled && !weapon_source ? "1" : "0");
    sdlfe::CoreCriticalAssets assets{};
    assets.lighting = "flat";
    assets.environment = environment;
    auto renderer = make_check_renderer(window, backend, {}, assets);
    renderer->mission_changed({5, 1});
    renderer->set_viewport(0, 0, 32, 32);
    if (canvas_transition) {
      // Loading has selected t1m1, but its world camera does not exist yet.
      // Exercise the actual menu/loading compositor, rather than a direct
      // renderer call that could miss the frontend's scene classification.
      const auto world_projection = zmth::projection();
      zmth::projection() = {};
      const auto canvas_projection = zmth::projection();
      const auto canvas_view = zmth::view();
      const auto canvas_clock = ztimer::state();
      zmod::LightList canvas_lights;
      std::memcpy(&canvas_lights, &zmod::light_list(), sizeof canvas_lights);
      const auto canvas_source = data;
      const auto native_target = zrndr::target2d();
      auto *const native_observer = zrndr::draw_observer();
      require(native_observer == nullptr,
              "Canvas check would replace an active native draw observer");
      Restore restore_target{[&] {
        zrndr::target2d() = native_target;
        zrndr::set_draw_observer(native_observer);
      }};
      auto require_native_state = [&] {
        require(!std::memcmp(&zmth::projection(), &canvas_projection,
                             sizeof canvas_projection) &&
                    !std::memcmp(&zmth::view(), &canvas_view, sizeof canvas_view) &&
                    !std::memcmp(&zmod::light_list(), &canvas_lights,
                                 sizeof canvas_lights) &&
                    !std::memcmp(&ztimer::state(), &canvas_clock,
                                 sizeof canvas_clock) &&
                    !std::memcmp(data.raw, canvas_source.raw, sizeof data.raw),
                "Canvas presentation mutated native world-light state");
      };
      auto preserve_float_state = [&](const char *operation, auto draw_canvas,
                                      bool assert_preserved = true) {
        std::fenv_t saved;
        require(std::fegetenv(&saved) == 0,
                "Cannot save canvas floating-point environment");
        Restore restore_float{[&] { std::fesetenv(&saved); }};
        require(std::fesetround(FE_DOWNWARD) == 0,
                "Cannot set canvas floating-point rounding control");
        std::feclearexcept(FE_ALL_EXCEPT);
        std::feraiseexcept(FE_DIVBYZERO);
        const auto before_rounding = std::fegetround();
        const auto before_flags = std::fetestexcept(FE_ALL_EXCEPT);
        draw_canvas();
        const auto after_rounding = std::fegetround();
        const auto after_flags = std::fetestexcept(FE_ALL_EXCEPT);
        std::fprintf(stderr,
                     "[CANVAS_FP] operation=%s round_before=%d flags_before=0x%x "
                     "round_after=%d flags_after=0x%x\n",
                     operation, before_rounding, before_flags,
                     after_rounding, after_flags);
        require(after_rounding == before_rounding,
                "Canvas presentation changed native floating-point rounding");
        if (assert_preserved)
          require(after_flags == before_flags,
                  "Canvas presentation changed native floating-point flags");
        return after_flags;
      };
      // Keep the real screen's first presentation cold. A separate renderer
      // measures the shared operations so the failure can be attributed before
      // changing either the canvas hook or the existing frontend boundary.
      int baseline_canvas_flags = FE_DIVBYZERO;
      {
        auto probe_renderer = make_check_renderer(window, backend, {}, assets);
        probe_renderer->mission_changed({5, 1});
        probe_renderer->set_viewport(0, 0, 32, 32);
        const std::vector<uint8_t> rgba(32 * 32 * 4, 255);
        platform::DrawState canvas_state{};
        canvas_state.texture =
            probe_renderer->create_texture(32, 32, rgba.data(), 1);
        canvas_state.address_u = canvas_state.address_v = 3;
        canvas_state.depth_write = false;
        canvas_state.depth_always = canvas_state.sharp = true;
        baseline_canvas_flags |= preserve_float_state("probe-clear", [&] {
          probe_renderer->clear(true, 0, 0, 0);
        }, false);
        preserve_float_state("probe-begin-canvas", [&] {
          probe_renderer->begin_canvas_scene();
        });
        baseline_canvas_flags |= preserve_float_state("probe-draw", [&] {
          quad(*probe_renderer, 0, 32, 1, 0xffffffff, canvas_state);
        }, false);
        baseline_canvas_flags |= preserve_float_state("probe-end", [&] {
          probe_renderer->end_scene();
        }, false);
        baseline_canvas_flags |= preserve_float_state("probe-present", [&] {
          probe_renderer->present();
        }, false);
        baseline_canvas_flags |= preserve_float_state("probe-readback", [&] {
          std::vector<uint32_t> pixels;
          int width = 0, height = 0;
          require(probe_renderer->read_back(&pixels, &width, &height),
                  "Canvas FP probe readback failed");
        }, false);
      }
      auto read_canvas = [&] {
        std::vector<uint32_t> pixels;
        int width = 0, height = 0;
        require(renderer->read_back(&pixels, &width, &height) &&
                    width == 32 && height == 32 && pixels.size() == 32u * 32u,
                "Loading canvas readback was empty or had the wrong size");
        return pixels;
      };
      std::vector<uint16_t> canvas(32 * 32, 0xf800);
      sdlfe::HudOptions hud_options;
      hud_options.mode = "core-critical";
      sdlfe::SdlScreen2D screen(renderer.get(), hud_options);
      // Unchanged renderer stages can raise flags, including synchronous
      // submission. Compare their measured effects exactly; the new canvas
      // hook still requires the original flags unchanged.
      const auto screen_flags = preserve_float_state("screen-present-16", [&] {
        screen.present_16(canvas.data(), 32, 32, 32 * 2, true);
      }, false);
      require(screen_flags == baseline_canvas_flags,
              "Loading canvas FP flags differ from its renderer-stage baseline");
      const auto loading_pixels = read_canvas();
      require(loading_pixels.front() == 0xffff0000 &&
                  loading_pixels.at(16 * 32 + 16) == 0xffff0000 &&
                  loading_pixels.back() == 0xffff0000,
              "Loading canvas lost its RGB565 pixels");
      require_native_state();

      // A recorded HUD span must reach GpuHud::finish, not the CPU shadow
      // fallback, with the same missing world projection.
      zrndr::target2d().format = 6;
      preserve_float_state("screen-gpu-hud", [&] {
        screen.begin_overlay_16(canvas.data(), 32, 32, 32 * 2);
        auto *observer = zrndr::draw_observer();
        require(observer != nullptr, "GPU HUD did not begin observation");
        observer->span(canvas.data() + 16 * 32, 32, 0x07e0);
        screen.overlay_16(canvas.data(), 32, 32, 32 * 2, true, 0xf81f,
                          nullptr, nullptr);
      });
      const auto hud_pixels = read_canvas();
      require(hud_pixels.at(16 * 32 + 16) == 0xff00ff00 &&
                  hud_pixels.front() == 0xffff0000,
              "GPU HUD canvas lost its recorded span or underlying pixels");
      require(zrndr::draw_observer() == native_observer,
              "GPU HUD retained its draw observer after composition");
      require_native_state();

      bool rejected_world_projection = false;
      try {
        renderer->begin_scene();
      } catch (const std::runtime_error &error) {
        rejected_world_projection =
            std::string(error.what()) == "Local lights: invalid projection";
      }
      require(rejected_world_projection,
              "World scene accepted the loading canvas's invalid projection");
      require_native_state();
      zmth::projection() = world_projection;
    }
    const uint8_t grey[4] = {128, 128, 128, 255};
    // Synthetic authenticated receiver identity; distinct from catalog emitter.
    mw34::materials::set_active_surface_key({1, 1, 1, 456});
    platform::DrawState state{};
    state.texture = renderer->create_texture(1, 1, grey, 1);
    mw34::materials::clear_active_surface_key();
    renderer->clear(true, 0, 0, 0);
    renderer->begin_scene();
    if (mutate) {
      data.put<float>(0x9c, 0);
      data.put<float>(0x14, 1000);
    }
    quad(*renderer, 4, 28, .5f, 0xffffffff, state);
    if (overlay_before_emitter) {
      platform::DrawState overlay = state;
      overlay.depth_always = true;
      overlay.depth_write = false;
      quad(*renderer, 28, 30, .5f, 0xffffffff, overlay);
    }
    if (weapon_source) {
      const uint8_t white[4] = {255, 255, 255, 255};
      mw34::materials::set_active_surface_key(
          {1, 1, 1, pack_source ? 789u : 123u});
      const auto emitter = renderer->create_texture(1, 1, white, 1);
      mw34::materials::clear_active_surface_key();
      platform::DrawState source{};
      source.texture = emitter;
      source.depth_write = false;
      source.sharp = sharp_source;
      // The sprite never covers the sampled receiver pixel.
      quad(*renderer, 24, 28, .8f, 0xffffffff, source);
    }
    renderer->end_scene();
    std::vector<uint32_t> pixels;
    int w = 0, h = 0;
    require(renderer->read_back(&pixels, &w, &h) && w == 32 && h == 32,
            "Local-light receiver readback failed");
    if (!mutate)
      require(!std::memcmp(data.raw, expected_source.raw, sizeof data.raw),
              "Local-light renderer mutated native source");
    const auto receiver = pixels.at(16 * 32 + 16);
    if (canvas_transition && weapon_source) {
      // The canvas must drop the world snapshot without erasing the observed
      // emitter's lifetime. No new emitter is submitted in the next world view.
      const std::vector<uint16_t> canvas(32 * 32, 0xf800);
      sdlfe::SdlScreen2D screen(renderer.get());
      screen.present_16(canvas.data(), 32, 32, 32 * 2, true);
      renderer->clear(true, 0, 0, 0);
      renderer->begin_scene();
      quad(*renderer, 4, 28, .5f, 0xffffffff, state);
      renderer->end_scene();
      require(renderer->read_back(&pixels, &w, &h) && w == 32 && h == 32,
              "World view after canvas lost its receiver readback");
      require(pixels.at(16 * 32 + 16) == receiver,
              "Canvas transition discarded an observed effect's lifetime");
    }
    return receiver;
  };
  const auto off = render(false, false), on = render(true, false),
             copied = render(true, true);
  require(on != off, "Native fixture did not change the GPU receiver");
  require(
      copied == on,
      "Native light source changed after BeginScene altered the owned packet");
  const auto weapon = render(true, false, true);
  require(weapon != off,
          "Authenticated emitter did not illuminate the receiver");
  require(render(true, false, true, false, true) == weapon,
          "Overlay submission omitted a later emitter from earlier receivers");
  require(render(true, false, false, false, false, true) == on,
          "Ambient-only native source was discarded or changed intensity");
  require(render(true, false, true, true) == off,
          "HUD sprite incorrectly admitted as an emitter");
  require(render(true, false, false, false, false, false, true) == on,
          "World fixture lighting did not resume after a loading canvas");
  require(render(true, false, true, false, false, false, true) == weapon,
          "World effect lighting did not resume after a loading canvas");
  const auto pack_weapon =
      render(true, false, true, false, false, false, false, true);
  require(pack_weapon != off,
          "Selected pack-only emitter did not illuminate the receiver");
  require(pack_weapon == weapon,
          "Pack emitter did not retain the base emitter's lighting contract");

  // Admission must fail before a game callback can observe a partial catalog.
  // Repeat the same selected path in two regions to exercise source dedup too.
  auto catalog_renderer = [&](const std::filesystem::path &selected_path) {
    auto selected =
        std::make_shared<platform::prepared::EnvironmentSelection>();
    for (const char *region : {"fixture-region", "second-region"})
      selected->resources[region]
                         [platform::prepared::EnvironmentRole::effects] =
          selected_path.string();
    sdlfe::CoreCriticalAssets assets{};
    assets.lighting = "flat";
    assets.environment = selected;
    return make_check_renderer(window, backend, {}, assets);
  };
  auto rejects_catalog = [&](const std::filesystem::path &selected_path,
                             const char *expected_error) {
    bool rejected = false;
    try {
      auto renderer = catalog_renderer(selected_path);
    } catch (const std::runtime_error &error) {
      rejected = std::string(error.what()) == expected_error;
    }
    require(rejected, "Selected effects catalog did not reject its invalid source");
  };
  const auto missing_path = std::filesystem::path(pack_path.string() + ".missing");
  require(!std::filesystem::exists(missing_path),
          "Missing effects-catalog fixture unexpectedly exists");
  rejects_catalog(missing_path, "Selected pack effect light catalog missing");
  {
    std::ofstream malformed(pack_path, std::ios::binary | std::ios::trunc);
    malformed.write("bad", 3);
    malformed.flush();
    require(bool(malformed), "Could not write malformed effects-catalog fixture");
  }
  rejects_catalog(pack_path, "Invalid effect-light material catalog");
  write_catalog(pack_path, 123, 1, 2);
  rejects_catalog(pack_path, "Conflicting effect-light material catalog entry");
  write_catalog(pack_path, 123);
  {
    auto duplicate = catalog_renderer(pack_path);
    require(duplicate->ok(), "Equal base/pack emitter definitions were rejected");
  }
  write_catalog(path, 123, 8192);
  write_catalog(pack_path, 10000);
  rejects_catalog(pack_path, "Combined effect-light material catalog exceeds limit");
  // A disabled local-light stage must not attempt to open either missing file.
  local_light_test_env("MW34_EFFECT_LIGHTS", "0");
  local_light_test_env("MW34_EFFECT_LIGHT_CATALOG", missing_path.string().c_str());
  {
    auto disabled = catalog_renderer(missing_path);
    require(disabled->ok(), "Disabled local lighting opened catalog sources");
  }
  write_catalog(path, 123);
  write_catalog(pack_path, 789);
  local_light_test_env("MW34_EFFECT_LIGHTS", "1");
  local_light_test_env("MW34_EFFECT_LIGHT_CATALOG", path.string().c_str());

  // A fade can begin a generic scene with a valid old projection before the
  // next world's camera builds its light list. Retire actual native storage,
  // then exercise that Begin and a new mission's positive GPU receiver.
  for (const bool retire_world_first : {true, false}) {
    auto saved_nodes = std::move(zcls::nodes());
    auto saved_lists = std::move(zcls::lists());
    const auto saved_frames = zcls::frames();
    const auto saved_immediate = zcls::immediate_delete();
    const auto saved_lights = zmod::light_list();
    zcls::nodes() = {};
    zcls::nodes().block_size = 16;
    zcls::lists() = {};
    zcls::lists().chunk_size = 16;
    zcls::frames() = {};
    zcls::immediate_delete() = 1;
    std::vector<zcls::Node *> owned;
    Restore restore_native{[&] {
      zmod::build_light_list(nullptr, nullptr, 0);
      for (auto *node : owned)
        if (node)
          zcls::node_release(node);
      zcls::lists() = std::move(saved_lists);
      zcls::nodes() = std::move(saved_nodes);
      zcls::frames() = saved_frames;
      zcls::immediate_delete() = saved_immediate;
      zmod::light_list() = saved_lights;
    }};
    zmod::build_light_list(nullptr, nullptr, 0);
    auto make_world = [&] {
      auto *light = zcls::light_create();
      owned.push_back(light);
      *static_cast<zcls::Light *>(light->data) = original;
      auto *world = zcls::world_create();
      owned.push_back(world);
      auto *world_data = static_cast<zcls::World *>(world->data);
      world_data->lights = new zcls::Node *[1]{light};
      world_data->light_data = new void *[1]{light->data};
      world_data->put<int32_t>(0xa0, 1);
      return std::pair{world, light};
    };
    auto retire = [&](zcls::Node *node, bool world) {
      const auto before = zcls::node_live();
      const auto result = world ? zcls::world_delete(node)
                                : zcls::node_release(node);
      if (zcls::node_live() == before - 1)
        for (auto *&item : owned)
          if (item == node)
            item = nullptr;
      require(result == 0 && zcls::node_live() == before - 1,
              "Native GPU lifetime fixture did not retire its allocation");
    };
    local_light_test_env("MW34_EFFECT_LIGHTS", "1");
    local_light_test_env("MW34_FIXTURE_LIGHTS", "1");
    sdlfe::CoreCriticalAssets assets{};
    assets.lighting = "flat";
    auto renderer = make_check_renderer(window, backend, {}, assets);
    renderer->mission_changed({5, 1});
    renderer->set_viewport(0, 0, 32, 32);
    const uint8_t grey[4] = {128, 128, 128, 255};
    mw34::materials::set_active_surface_key({1, 1, 1, 456});
    platform::DrawState state{};
    state.texture = renderer->create_texture(1, 1, grey, 1);
    mw34::materials::clear_active_surface_key();
    auto receiver_pixel = [&] {
      renderer->clear(true, 0, 0, 0);
      renderer->begin_scene();
      quad(*renderer, 4, 28, .5f, 0xffffffff, state);
      renderer->end_scene();
      std::vector<uint32_t> pixels;
      int width = 0, height = 0;
      require(renderer->read_back(&pixels, &width, &height) &&
                  width == 32 && height == 32,
              "Native lifetime GPU receiver readback failed");
      return pixels.at(16 * 32 + 16);
    };
    const auto empty_training = receiver_pixel();
    const auto old_world = make_world();
    require(zmod::world_build_lights(old_world.first, 0) == 0,
            "Native old-world light build failed");
    require(receiver_pixel() != empty_training,
            "Native old-world fixture did not illuminate the GPU receiver");
    if (retire_world_first)
      retire(old_world.first, true);
    else
      retire(old_world.second, false);
    const auto &retired = zmod::light_list();
    require(retired.count == 0 && retired.in_count == 0 && retired.any == 0 &&
                !retired.nodes && !retired.data,
            "Native retirement left a borrowed GPU light cache");
    require(receiver_pixel() == empty_training,
            "Generic Begin retained a retired world's native light");
    if (retire_world_first)
      retire(old_world.second, false);
    else
      retire(old_world.first, true);

    renderer->mission_changed({1, 1});
    const auto empty_campaign = receiver_pixel();
    const auto fresh_world = make_world();
    require(zmod::world_build_lights(fresh_world.first, 0) == 0,
            "Native fresh-world light build failed");
    require(receiver_pixel() != empty_campaign,
            "Fresh mission's native fixture did not illuminate the GPU receiver");
  }

  // Use a small check-only allowance to exercise real rejection without a
  // production-sized allocation. Two 128-square RGBA payloads fill it before
  // scene metadata. Budget rejection must retain the scene. Retrying the same unchanged
  // submission must reject again, rather than silently succeeding after loss.
  {
    sdlfe::CoreCriticalAssets assets{};
    assets.lighting = "flat";
    auto renderer = make_check_renderer(window, backend, {}, assets, 128u * 1024u);
    renderer->mission_changed({5, 1});
    renderer->set_viewport(0, 0, 32, 32);
    const std::vector<uint8_t> pixels(std::size_t(128) * 128 * 4, 128);
    platform::DrawState first{}, second{};
    first.texture = renderer->create_texture(128, 128, pixels.data(), 1);
    second.texture = renderer->create_texture(128, 128, pixels.data(), 1);
    renderer->clear(true, 0, 0, 0);
    renderer->begin_scene();
    quad(*renderer, 4, 28, .5f, 0xffffffff, first);
    quad(*renderer, 4, 28, .5f, 0xffffffff, second);
    auto rejects_budget = [&] {
      try {
        renderer->end_scene();
      } catch (const std::runtime_error &e) {
        return std::string(e.what()).find("staging exceeds budget") !=
               std::string::npos;
      }
      return false;
    };
    require(rejects_budget(), "Oversized local-light view was not rejected");
    require(rejects_budget(),
            "Rejected local-light view lost its retained payloads");
  }
}
