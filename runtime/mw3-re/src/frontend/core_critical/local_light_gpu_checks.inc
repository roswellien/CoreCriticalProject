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

  // A small check-only allowance exercises a packet larger than the whole allowance without a
  // production-sized allocation: two 128-square RGBA payloads fill it before scene metadata.
  // The owner's c3m3 crash was such a packet ending the game. It must instead be staged alone,
  // render, warn once per mission and render the same again on the next frame.
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
    auto render_oversized_frame = [&] {
      renderer->clear(true, 0, 0, 0);
      renderer->begin_scene();
      quad(*renderer, 4, 28, .5f, 0xffffffff, first);
      quad(*renderer, 4, 28, .5f, 0xffffffff, second);
      renderer->end_scene();
      std::vector<std::uint32_t> frame;
      int width{}, height{};
      require(renderer->read_back(&frame, &width, &height) && !frame.empty(),
              "Oversized local-light view did not render");
      return frame;
    };
    const auto first_frame = render_oversized_frame();
    const bool drew_quad = std::any_of(first_frame.begin(), first_frame.end(),
                                       [](std::uint32_t pixel) { return (pixel & 0xffffff) != 0; });
    require(drew_quad, "Oversized local-light view rendered no quad");
    const auto second_frame = render_oversized_frame();
    require(second_frame == first_frame,
            "Oversized local-light view rendered differently on the next frame");
    const auto staging = cc_mw3_re::testing::staging_state(*renderer);
    require(staging.oversized_packets == 1,
            "The first frame's texture upload was not staged as one oversized packet");
    require(staging.oversized_log_lines == 1, "Oversized packets were not warned exactly once");
  }
}
// Fixture keys are injected only at the established synthetic native upload
// seam. These authored pixels test backend routing and masks; they do not
// establish original-asset content identity (the private CPU receipt does).
void check_native_fixture_gpu(SDL_Window *window, sdlfe::RendererBackend backend) {
  struct Cleanup {
    std::function<void()> operation;
    ~Cleanup() { operation(); }
  };
  const auto saved_projection = zmth::projection();
  const auto saved_view = zmth::view();
  const auto saved_lights = zmod::light_list();
  const auto saved_clock = ztimer::state();
  std::vector<std::pair<std::string, std::optional<std::string>>> environment;
  for (const char *name : {"MW34_EFFECT_LIGHT_CATALOG", "MW34_EFFECT_LIGHTS", "MW34_FIXTURE_LIGHTS"})
    environment.push_back({name, std::getenv(name) ? std::optional<std::string>(std::getenv(name))
                                                 : std::nullopt});
  const auto catalog_path = std::filesystem::temp_directory_path() /
      ("mw34-native-fixture-" + std::to_string(SDL_GetTicksNS()) + ".bin");
  Cleanup cleanup{[&] {
    mw34::materials::clear_active_surface_key();
    zmth::projection() = saved_projection;
    zmth::view() = saved_view;
    zmod::light_list() = saved_lights;
    ztimer::state() = saved_clock;
    for (const auto &entry : environment)
      local_light_test_env(entry.first.c_str(), entry.second ? entry.second->c_str() : nullptr);
    std::error_code ignored;
    std::filesystem::remove(catalog_path, ignored);
  }};
  {
    std::ofstream stream(catalog_path, std::ios::binary);
    prepared_fixture::Bytes catalog;
    catalog.value.assign("MWFX1\0\0\0", 8);
    catalog.u32(1);
    for (auto word : {1U, 1U, 1U, 2U})
      catalog.u32(word);
    catalog.u64(17); // Valid, unused key; no sprite source can explain a positive receiver.
    for (float scalar : {10.f, 1.f, .25f, 1.f, 1.f, 1.f})
      catalog.f32(scalar);
    stream << catalog.value;
    require(bool(stream), "Cannot create fixture GPU effect catalog");
  }
  local_light_test_env("MW34_EFFECT_LIGHT_CATALOG", catalog_path.string().c_str());
  local_light_test_env("MW34_EFFECT_LIGHTS", "1");
  zmod::light_list() = {};
  zmth::projection() = {};
  auto &projection = zmth::projection();
  projection.near_z = 1;
  projection.fx_near = projection.fy_near = 16;
  projection.cx = projection.cy = 16;
  projection.far_z = 100;
  const std::array<float, 12> identity{1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0};
  std::memcpy(zmth::view().camera.m, identity.data(), sizeof identity);
  using Key = mw34::materials::SurfaceKey;
  const Key lamp_key{512, 512, 1, 0x60f6785ad44b57feULL};
  const Key glow_key{256, 512, 1, 0xc1eea6a84cfc28a3ULL};
  const Key unknown_key{512, 512, 1, 0x60f6785ad44b57ffULL};
  const Key vehicle_key{512, 512, 1, 0x6002a710ed9a5078ULL};
  unsigned cases = 0;
  auto check = [&](bool condition, const char *message) {
    require(condition, message);
    ++cases;
  };
  auto channel_sum = [](std::uint32_t pixel) {
    return int(pixel & 255) + int((pixel >> 8) & 255) + int((pixel >> 16) & 255);
  };
  auto render = [&](const char *mode, Key key, bool enabled, bool deferred, bool split,
                                         bool capacity_control = false, unsigned lifetime_control = 0,
                     std::vector<std::vector<std::uint32_t>>* frames = nullptr) {
    local_light_test_env("MW34_FIXTURE_LIGHTS", enabled ? "1" : "0");
    sdlfe::CoreCriticalAssets assets{};
    assets.lighting = "flat"; // No normals/sidecar/POM prerequisite is permitted.
    assets.geometry = mode;
    auto renderer = make_check_renderer(window, backend, {}, assets,
        capacity_control ? std::optional<std::size_t>(112u * 1024u) : std::nullopt);
    renderer->mission_changed({5, 1});
    renderer->set_viewport(0, 0, 32, 32);
    const std::uint8_t grey[]{128, 128, 128, 255};
    mw34::materials::set_active_surface_key({1, 1, 1, 456});
    platform::DrawState receiver{};
    receiver.texture = renderer->create_texture(1, 1, grey, 1);
    mw34::materials::set_active_surface_key(key);
    platform::DrawState fixture{};
    fixture.texture = renderer->create_texture(1, 1, grey, 1);
    mw34::materials::clear_active_surface_key();
    zvid::D3DTexture texture{};
    texture.handle = fixture.texture;
    texture.type = 1;
    texture.address_u = texture.address_v = 3;
    zimg::TextureEntry texture_entry{};
    texture_entry.surface = &texture;
    zmod::Material material{};
    material.alpha = 255;
    material.flags = 1;
    material.r = material.g = material.b = 255;
    material.texture = &texture_entry;
    // Original corner order faces -Z; screen submission reverses it below.
    float positions[]{1, -1.75f, 2, 1, -.25f, 2, 1.875f, -.25f, 2,
                      1.875f, -1.75f, 2};
    std::uint32_t indices[]{0, 1, 2, 3};
    float uv[]{.2f, .3f, .2f, .7f, .6f, .7f, .6f, .3f};
    zmod::Polygon polygon{};
    polygon.flags = 4;
    polygon.vertex_indices = indices;
    polygon.uvs = uv;
    polygon.material = &material;
    zmod::Model model{};
    model.vertices = positions;
    model.polygons = &polygon;
    const std::uint32_t vertex_count = 4, polygon_count = 1;
    std::memcpy(model.header + 0x14, &vertex_count, 4);
    std::memcpy(model.header + 0x10, &polygon_count, 4);
    cc::geometry::Polygon source_polygon{};
    source_polygon.count = 4;
    source_polygon.positions = indices;
    source_polygon.uv = uv;
    source_polygon.two_sided = true;
    model.render_geometry = cc::geometry::register_resource(positions, 4, nullptr, 0,
                                                           {source_polygon});
    model.render_materials = {&material};
    zcls::Node node{};
    node.put<int32_t>(0x34, 5);
    node.model = &model;
    auto matrix = identity;
    zcls::Node *native_root=nullptr,*native_healthy=nullptr,*native_lamp=nullptr,*native_parent=nullptr;
    mech3::Vehicle native_owner{};
    zmod::Model replacement_model{},shared_model{},unrelated_model{};
    zmod::Material unrelated_material{};
    zmod::Polygon shared_polygon{},unrelated_polygon{};
    shared_polygon.material=&material;
    unrelated_polygon.material=&unrelated_material;
    shared_model.polygons=&shared_polygon;
    unrelated_model.polygons=&unrelated_polygon;
    const bool vehicle_lifetime=lifetime_control>=10 && lifetime_control<=13;
    if(lifetime_control) {
      native_root=zcls::object3d_create();
      native_healthy=zcls::object3d_create();
      native_lamp=zcls::object3d_create();
      zcls::node_set_name(native_healthy,"healthy");
      zcls::node_link(native_root,native_healthy);
      zcls::node_link(native_healthy,native_lamp);
      zcls::node_set_model(native_lamp,&model);
      if(vehicle_lifetime) {
        native_parent=zcls::object3d_create();
        zcls::node_link(native_parent,native_root);
        // Yaw180 keeps the lamp in front of the farther receiver while its
        // authored -Z front cone points toward it. UVs cover only lamp1.
        matrix={-1,0,0,0,1,0,0,0,-1,0,0,4};
        const float lamp_uv[]{.82f,.32f,.82f,.43f,.92f,.43f,.92f,.32f};
        std::copy(std::begin(lamp_uv),std::end(lamp_uv),uv);
        zcls::object3d_set_matrix(native_root,matrix.data());
        native_owner.node=native_root;
        native_owner.transform=zcls::object3d_matrix(native_root);
        native_owner.centroid=native_owner.target_node=native_root;
        zcls::node_tree_bind(native_root,&native_owner,0x80000,0);
        zcls::fixture_vehicle_register(&native_owner,native_root,true,native_owner.transform);
        zcls::fixture_observe_world(native_root,matrix.data());
      }
    }
    Cleanup native_cleanup{[&] {
      for(auto* mapping : {&material,&unrelated_material}) {
        if(mapping->cycle) {
          std::free(mapping->cycle->textures);
          std::free(mapping->cycle);
          mapping->cycle=nullptr;
        }
      }
      if(!lifetime_control) return;
      zcls::fixture_vehicle_unregister(&native_owner);
      if(native_lamp) {
        zcls::node_set_model(native_lamp,nullptr);
        zcls::node_unlink(native_healthy,native_lamp);
        zcls::node_unlist(native_lamp);
        zcls::node_free(native_lamp);
      }
      zcls::node_unlink(native_root,native_healthy);
      zcls::node_unlist(native_healthy);
      zcls::node_free(native_healthy);
      if(native_parent) zcls::node_unlink(native_parent,native_root);
      zcls::node_unlist(native_root);
      zcls::node_free(native_root);
      if(native_parent) { zcls::node_unlist(native_parent); zcls::node_free(native_parent); }
    }};
    platform::ModelDrawContext context{};
    context.node = lifetime_control ? native_lamp : &node;
    context.model_to_world = context.model_to_camera = matrix.data();
    context.ordinary = true;
    context.source_vertices = 4;
    context.source_polygons = 1;
    context.near_z = context.clip_near = 1;
    context.far_z = 100;
    context.fx_near = context.fy_near = 16;
    context.cx = context.cy = 16;
    platform::TLVertex lamp_vertices[]{
        {24, 2, .5f, .5f, 0xffffffff, 0, .2f, .3f},
        {31, 2, .5f, .5f, 0xffffffff, 0, .6f, .3f},
        {31, 14, .5f, .5f, 0xffffffff, 0, .6f, .7f},
        {24, 14, .5f, .5f, 0xffffffff, 0, .2f, .7f}};
    if(vehicle_lifetime) {
      for(unsigned corner=0;corner<4;++corner) {
        lamp_vertices[corner].sx=32-lamp_vertices[corner].sx;
        lamp_vertices[corner].tu=corner==0 || corner==3 ? .82f : .92f;
        lamp_vertices[corner].tv=corner<2 ? .32f : .43f;
      }
    }
    std::vector<std::uint32_t> first;
    const unsigned frame_count=(lifetime_control==8 || lifetime_control==12) ? 4 : (lifetime_control ? 3 : 2);
    for (unsigned frame = 0; frame < frame_count; ++frame) {
      if(lifetime_control && frame==2) {
        if(lifetime_control==1) {
          zcls::node_set_model(native_lamp,nullptr);
          zcls::node_unlink(native_healthy,native_lamp);
          zcls::node_unlist(native_lamp);
          zcls::node_free(native_lamp);
          native_lamp=nullptr;
        } else if(lifetime_control==2) {
          model.invalidate_render_geometry();
        } else if(lifetime_control==3) {
          zcls::node_set_model(native_lamp,&replacement_model);
        } else if(lifetime_control==4) {
          zcls::object3d_set_translation(native_lamp,40,0,0);
        } else if(lifetime_control==5) {
          mw34::materials::set_active_surface_key(unknown_key);
          renderer->update_texture(fixture.texture,1,1,grey);
          mw34::materials::clear_active_surface_key();
        } else if(lifetime_control==6) {
          zcls::fixture_pool_retire(); // Native bulk reset event; keep test storage for cleanup.
        } else if(lifetime_control==7) {
          zcls::invalidate_world_source_proofs(); // Actual load barrier, including failed loads.
        } else if(lifetime_control==8) {
          zcls::node_set_active(native_lamp,0);
        } else if(lifetime_control==9) {
          zmod::cycle_set_on(&model,2);
        } else if(lifetime_control==14) {
          zmod::model_set_scroll(&model,1,.25f,0);
        } else if(lifetime_control==15) {
          zmod::cycle_set_on(&unrelated_model,2);
        } else if(lifetime_control==16) {
          zmod::cycle_set_on(&shared_model,2);
        } else if(lifetime_control==10) {
          native_owner.transform[9]=40;
          const auto saved_stack=zmth::matrix_stack();
          native_owner.entity_moved(); // Parent root is needed by the real callback.
          zmth::matrix_stack()=saved_stack;
        } else if(lifetime_control==11) {
          zcls::fixture_vehicle_state(native_root,false);
        } else if(lifetime_control==12) {
          zcls::node_set_active(native_healthy,0);
        } else if(lifetime_control==13) {
          zcls::fixture_vehicle_unregister(&native_owner);
        }
      }
      if(frame==3 && lifetime_control==8) zcls::node_set_active(native_lamp,1);
      if(frame==3 && lifetime_control==12) zcls::node_set_active(native_healthy,1);
      renderer->clear(true, 0, 0, 0);
      renderer->begin_scene();
      quad(*renderer, 4, 22, vehicle_lifetime ? .1f : 1.f / 3.f, 0xffffffff, receiver);
      if (split)
        renderer->flush(); // Receiver is already in an earlier owned packet.
      for (unsigned copy = 0; copy < (lifetime_control && frame ? 0U :
                                      (capacity_control ? 128U : 1U)); ++copy) {
      std::optional<zcls::FixtureWalkScope> parent_scope,root_scope,healthy_scope,lamp_scope;
      if(lifetime_control) {
        if(native_parent) parent_scope.emplace(native_parent);
        root_scope.emplace(native_root);
        healthy_scope.emplace(native_healthy);
        lamp_scope.emplace(native_lamp);
      }
      if (std::string_view(mode) == "legacy") {
        renderer->begin_model_draw(context);
        renderer->begin_material_draw({&model, &material, &texture_entry, 0});
        if (deferred) {
          auto owned = renderer->capture_deferred_material_binding(fixture.texture);
          renderer->end_material_draw();
          renderer->end_model_draw();
          // A deferred packet must use copied geometry/pose, never these objects.
          const auto saved_x = positions[0];
          positions[0] = 1000;
          node.model = nullptr;
          renderer->begin_deferred_material_draw(std::move(owned));
          renderer->draw(platform::Primitive::kFan, lamp_vertices, 4, fixture);
          renderer->end_deferred_material_draw();
          positions[0] = saved_x;
          node.model = &model;
        } else {
          renderer->draw(platform::Primitive::kFan, lamp_vertices, 4, fixture);
          renderer->end_material_draw();
          renderer->end_model_draw();
        }
      } else {
        cc::geometry::Material owned_material;
        owned_material.texture = fixture.texture;
        owned_material.address_u = owned_material.address_v = 3;
        require(renderer->submit_model_geometry(model.render_geometry, context,
                    {owned_material}, {}) == cc::geometry::Submission::submitted,
                "Native fixture direct source was not submitted");
      }
      }
      if (capacity_control) {
        // Emission payload bytes count toward the staging allowance: 128 copies push this
        // packet past the 112 KiB check allowance. An oversized packet is staged alone instead
        // of ending the game, so the counted bytes show as an oversized packet and the frame
        // still renders.
        renderer->end_scene();
        const auto staging = cc_mw3_re::testing::staging_state(*renderer);
        check(staging.oversized_packets >= 1,
              "Emission payload allocation escaped the staging budget");
        std::vector<std::uint32_t> pixels;
        int width{}, height{};
        check(renderer->read_back(&pixels, &width, &height) && width == 32 && height == 32,
              "Oversized emission payload scene did not render");
        return std::vector<std::uint32_t>{};
      }
      if (split)
        renderer->flush();
      renderer->end_scene();
      std::vector<std::uint32_t> pixels;
      int width{}, height{};
      require(renderer->read_back(&pixels, &width, &height) && width == 32 && height == 32,
              "Native fixture GPU pixel readback failed");
      if(frames) frames->push_back(pixels);
      if (!frame)
        first = pixels;
      else if(!lifetime_control)
        check(pixels == first, "Fresh fixture scene/cache reuse changed the second frame pixels");
    }
    return first;
  };
  for (const char *mode : {"legacy", "partial", "cpu-reference"}) {
    const auto off = render(mode, lamp_key, false, false, false);
    const auto on = render(mode, lamp_key, true, false, false);
    check(channel_sum(off.at(16 * 32 + 14)) > 0,
          "Physical-light control did not render the separate receiver");
    check(channel_sum(on.at(16 * 32 + 14)) > channel_sum(off.at(16 * 32 + 14)),
          "Native fixture did not illuminate the separate receiver with normals/POM off");
    check(channel_sum(on.at(8 * 32 + 27)) > channel_sum(off.at(8 * 32 + 27)),
          "Native fixture lens did not self-illuminate");
    const auto split = render(mode, lamp_key, true, false, true);
    check(split == on, "Late fixture or scene split lost emission payload/earlier receiver lighting");
    const auto unregistered_off = render(mode, unknown_key, false, false, false);
    const auto unregistered_on = render(mode, unknown_key, true, false, false);
    check(unregistered_on == unregistered_off, "Unregistered bright body texture emitted light");
    const auto glow_off = render(mode, glow_key, false, false, false);
    const auto glow_on = render(mode, glow_key, true, false, true);
    check(glow_on.at(16 * 32 + 14) == glow_off.at(16 * 32 + 14),
          "Glow-only material illuminated a separate receiver");
    check(channel_sum(glow_on.at(8 * 32 + 27)) > channel_sum(glow_off.at(8 * 32 + 27)),
          "Glow-only UV lamp did not retain visible self-emission");
    check(channel_sum(glow_off.at(3 * 32 + 25)) > 0,
          "Casing negative sampled an uncovered pixel instead of visible fixture geometry");
    check(glow_on.at(3 * 32 + 25) == glow_off.at(3 * 32 + 25),
          "Masked indicator promoted its unrelated casing to self-emission");
  }
  const auto immediate = render("legacy", lamp_key, true, false, true);
  const auto deferred = render("legacy", lamp_key, true, true, true);
  check(deferred == immediate, "Deferred fixture changed after the native model scope retired");
  const auto vehicle_off = render("legacy", vehicle_key, false, false, false);
  const auto vehicle_on = render("legacy", vehicle_key, true, false, false);
  check(vehicle_on == vehicle_off, "Vehicle without healthy/owned-pose proof emitted a fixture");
  render("legacy", glow_key, true, false, false, true);

  std::vector<std::vector<std::uint32_t>> static_off,vehicle_off_frames;
  render("legacy",lamp_key,false,false,false,false,1,&static_off);
  render("legacy",{32,32,1,0xc71e4fe58b74e99fULL},false,false,false,false,10,&vehicle_off_frames);
  for(unsigned control : {1U,2U,3U,4U,5U,6U,7U,8U,9U,14U,15U,16U}) {
    std::vector<std::vector<std::uint32_t>> frames;
    render("legacy",lamp_key,true,false,true,false,control,&frames);
    const auto receiver=16*32+14;
    check(channel_sum(frames[0].at(receiver))>channel_sum(static_off[0].at(receiver)),
          "Native lifetime positive never illuminated the physical receiver");
    check(frames[1].at(receiver)==frames[0].at(receiver),
          "A mere camera cull retired a valid static fixture");
    check(frames[2].at(receiver)==(control==15 ? frames[0].at(receiver) : static_off[2].at(receiver)),
          "Native mapping/lifetime invalidation was stale or unrelated material activity retired a lamp");
    if(control==8) check(frames[3].at(receiver)==frames[0].at(receiver),
        "Off-camera static activation did not resume the surviving source lifetime");
  }
  for(unsigned control : {10U,11U,12U,13U}) {
    std::vector<std::vector<std::uint32_t>> frames;
    render("legacy",{32,32,1,0xc71e4fe58b74e99fULL},true,false,true,false,control,&frames);
    const auto receiver=16*32+14;
    check(channel_sum(frames[0].at(receiver))>channel_sum(vehicle_off_frames[0].at(receiver)),
          "Registered healthy vehicle front lamp did not illuminate its forward receiver");
    check(channel_sum(frames[0].at(8*32+2))>channel_sum(vehicle_off_frames[0].at(8*32+2)),
          "Registered healthy vehicle UV lens did not self-illuminate");
    check(frames[1].at(receiver)==frames[0].at(receiver),
          "Culling lost the registered vehicle's copied pose lamp");
    check(frames[2].at(receiver)==vehicle_off_frames[2].at(receiver),
          "Off-camera native motion/death/healthy/unregister retained the previous lamp");
    if(control==12) check(frames[3].at(receiver)==frames[0].at(receiver),
        "Off-camera healthy activation did not resume its surviving vehicle lamp");
  }

  std::fprintf(stderr, "[NATIVE_FIXTURE_GPU] cases=%u failures=0\n", cases);
}
