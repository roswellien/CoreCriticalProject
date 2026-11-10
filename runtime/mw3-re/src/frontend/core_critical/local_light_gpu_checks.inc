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
      fixtures_env("MW34_FIXTURE_LIGHTS"),
      sun_shadows_env("MW34_SUN_SHADOWS"),
      fixture_shadows_env("MW34_FIXTURE_SHADOWS");
  const auto path = std::filesystem::temp_directory_path() /
                    ("mw34-wp04a-" + std::to_string(SDL_GetTicksNS()) + ".bin");
  struct Restore {
    std::function<void()> f;
    ~Restore() { f(); }
  } restore{[&] {
    mw34::materials::clear_active_surface_key();
    zmod::light_list() = old_list;
    zmth::projection() = old_projection;
    zmth::view() = old_view;
    std::error_code ignored;
    std::filesystem::remove(path, ignored);
  }};
  {
    std::ofstream f(path, std::ios::binary);
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
    u32(1);
    u32(1);
    u32(1);
    u32(1);
    u32(2);
    u32(123);
    u32(0);
    scalar(10);
    scalar(1);
    scalar(1);
    scalar(1);
    scalar(1);
    scalar(1);
    f.flush();
    require(bool(f), "Could not write local-light fixture catalog");
  }
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
                    bool ambient_only = false) {
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
    auto renderer = make_check_renderer(window, backend, {}, assets);
    renderer->mission_changed({5, 1});
    renderer->set_viewport(0, 0, 32, 32);
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
      mw34::materials::set_active_surface_key({1, 1, 1, 123});
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
    return pixels.at(16 * 32 + 16);
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
  // Multi-frame sun and fixture shadow execution across mission transition
  // (advances world_frame_ and world_generation_ on live FrameRenderer).
  {
    data = original;
    local_light_test_env("MW34_EFFECT_LIGHTS", "1");
    local_light_test_env("MW34_FIXTURE_LIGHTS", "1");
    local_light_test_env("MW34_SUN_SHADOWS", "1");
    local_light_test_env("MW34_FIXTURE_SHADOWS", "1");
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
    for (int f = 0; f < 2; ++f) {
      renderer->clear(true, 0, 0, 0);
      renderer->begin_scene();
      quad(*renderer, 4, 28, .5f, 0xffffffff, state);
      renderer->end_scene();
    }
    std::vector<uint32_t> pixels;
    int w = 0, h = 0;
    require(renderer->read_back(&pixels, &w, &h) && w == 32 && h == 32,
            "Shadowed multi-frame readback failed on outdoor mission");
    require(pixels.at(16 * 32 + 16) != off,
            "Shadowed outdoor mission frame produced unlit receiver");
    // Transition to sealed underground mission c2m2 ({1, 2}): suppresses
    // directional sun shadows while preserving local fixture shadows and
    // advancing world_generation_.
    renderer->mission_changed({1, 2});
    renderer->clear(true, 0, 0, 0);
    renderer->begin_scene();
    quad(*renderer, 4, 28, .5f, 0xffffffff, state);
    renderer->end_scene();
    require(renderer->read_back(&pixels, &w, &h) && w == 32 && h == 32,
            "Shadowed readback failed after sealed mission transition");
    require(pixels.at(16 * 32 + 16) != off,
            "Sealed mission fixture shadow frame produced unlit receiver");
    local_light_test_env("MW34_SUN_SHADOWS", "0");
    local_light_test_env("MW34_FIXTURE_SHADOWS", "0");
  }
  // Occlusion must survive split scene batches in one frame, but a removed
  // occluder must not leave its shadow in the following frame.
  {
    data = original;
    data.put<float>(0xc, -3);
    data.put<float>(0x14, 0);
    data.put<float>(0x9c, 8);
    local_light_test_env("MW34_EFFECT_LIGHTS", "1");
    local_light_test_env("MW34_FIXTURE_LIGHTS", "1");
    local_light_test_env("MW34_SUN_SHADOWS", "1");
    local_light_test_env("MW34_FIXTURE_SHADOWS", "1");
    sdlfe::CoreCriticalAssets assets{};
    assets.lighting = "flat";
    auto renderer = make_check_renderer(window, backend, {}, assets);
    renderer->mission_changed({5, 1});
    renderer->set_viewport(0, 0, 32, 32);
    const uint8_t grey[4] = {128, 128, 128, 255};
    mw34::materials::set_active_surface_key({1, 1, 1, 456});
    platform::DrawState receiver_state{};
    receiver_state.texture = renderer->create_texture(1, 1, grey, 1);
    mw34::materials::clear_active_surface_key();
    // An offscreen occluder lies between the front-facing receiver and the
    // light, without covering the sampled pixel in the camera view.
    platform::DrawState occluder_state{};
    occluder_state.texture = receiver_state.texture;
    auto center_pixel = [&] {
      std::vector<uint32_t> pixels;
      int w = 0, h = 0;
      require(renderer->read_back(&pixels, &w, &h) && w == 32 && h == 32,
              "Retained-caster readback failed");
      return pixels.at(16 * 32 + 16);
    };
    auto batch = [&](bool occluder, bool receiver) {
      renderer->begin_scene();
      if (occluder) {
        const platform::TLVertex vertices[] = {
            {-16, 8, 1.f, 1, 0xffffffff, 0, 0, 0},
            {0, 8, 1.f, 1, 0xffffffff, 0, 1, 0},
            {0, 24, 1.f, 1, 0xffffffff, 0, 1, 1},
            {-16, 24, 1.f, 1, 0xffffffff, 0, 0, 1}};
        renderer->draw(platform::Primitive::kFan, vertices, 4, occluder_state);
      }
      if (receiver)
        quad(*renderer, 4, 28, .5f, 0xffffffff, receiver_state);
      renderer->end_scene();
    };
    // mode 0: receiver only. mode 1: occluder+receiver in ONE batch (combined).
    // mode 2: occluder in batch 1 only, receiver in batches 2 and 3 (split,
    // same original frame, ended by present()).
    auto frame = [&](int mode) {
      renderer->clear(true, 0, 0, 0);
      if (mode == 1)
        batch(true, true);
      else if (mode == 2) {
        batch(true, false);
        batch(false, true);
        batch(false, true);
      } else
        batch(false, true);
      renderer->present(); // Ends the original frame (hidden/capture early returns).
      return center_pixel();
    };
    const auto base = frame(0);
    const auto combined = frame(1);
    require(combined != base,
            "Fixture occluder did not shadow the receiver (not shadow-sensitive)");
    const auto split = frame(2);
    require(split == combined,
            "Split BeginScene batches in one frame lost the retained shadow caster");
    require(frame(0) == base,
            "Next frame kept a stale occluder shadow from the prior frame");
    renderer->mission_changed({1, 2}); // New world_generation_ invalidates casters.
    const auto base2 = frame(0);
    const auto combined2 = frame(1);
    require(combined2 != base2,
            "Sealed mission lost fixture shadow sensitivity");
    require(frame(2) == combined2,
            "Mission generation reset broke retained casters within the new frame");
    batch(true, false);
    renderer->mission_changed({1, 2});
    require(frame(0) == base2,
            "Mission generation reset without present retained an anonymous TL caster");
    zcls::Node scope_a{}, scope_b{};
    const auto scoped_occluder = [&](const zcls::Node *owner) {
      platform::ModelDrawContext context{};
      context.node = owner;
      context.ordinary = true;
      renderer->begin_model_draw(context);
      const platform::TLVertex vertices[] = {
          {-16, 8, 1.f, 1, 0xffffffff, 0, 0, 0},
          {0, 8, 1.f, 1, 0xffffffff, 0, 1, 0},
          {0, 24, 1.f, 1, 0xffffffff, 0, 1, 1},
          {-16, 24, 1.f, 1, 0xffffffff, 0, 0, 1}};
      renderer->draw(platform::Primitive::kFan, vertices, 4, occluder_state);
      renderer->end_model_draw();
    };
    renderer->clear(true, 0, 0, 0);
    renderer->begin_scene();
    scoped_occluder(&scope_a);
    scoped_occluder(&scope_b);
    renderer->retire_headlight_node(reinterpret_cast<std::uintptr_t>(&scope_a));
    quad(*renderer, 4, 28, .5f, 0xffffffff, receiver_state);
    renderer->end_scene();
    require(center_pixel() == combined2,
            "TL coalescing merged different shadow source lifetimes");
    renderer->present();
    local_light_test_env("MW34_SUN_SHADOWS", "0");
    local_light_test_env("MW34_FIXTURE_SHADOWS", "0");
    data = original;
  }
  // Model-consumer caster lifetime: native model geometry submitted through
  // submit_model_geometry must follow the same fixture-shadow lifetime rules
  // as the TL occluder above. Same fixture light (x=-3, z=0, diffuse 8,
  // radius 10) and authentic grey receiver at z=2; the model occluder is a
  // two-sided unit square placed at world z=1 between light and receiver,
  // projecting offscreen-left exactly like the TL occluder.
  {
    data = original;
    data.put<float>(0xc, -3);
    data.put<float>(0x14, 0);
    data.put<float>(0x9c, 8);
    local_light_test_env("MW34_EFFECT_LIGHTS", "1");
    local_light_test_env("MW34_FIXTURE_LIGHTS", "1");
    local_light_test_env("MW34_SUN_SHADOWS", "1");
    local_light_test_env("MW34_FIXTURE_SHADOWS", "1");
    sdlfe::CoreCriticalAssets assets{};
    assets.geometry = "partial";
    assets.lighting = "flat";
    auto renderer = make_check_renderer(window, backend, {}, assets);
    renderer->mission_changed({5, 1});
    renderer->set_viewport(0, 0, 32, 32);
    const uint8_t grey[4] = {128, 128, 128, 255};
    mw34::materials::set_active_surface_key({1, 1, 1, 456});
    platform::DrawState receiver_state{};
    receiver_state.texture = renderer->create_texture(1, 1, grey, 1);
    mw34::materials::clear_active_surface_key();
    // Two-sided square, local x/y ±0.5 at z=0, two triangles.
    const float square[12] = {-0.5f, -0.5f, 0, 0.5f, -0.5f, 0,
                              0.5f,  0.5f,  0, -0.5f, 0.5f,  0};
    const std::uint32_t square_indices[6] = {0, 1, 2, 0, 2, 3};
    const auto make_square = [&] {
      return cc::geometry::register_resource(
          square, 4, nullptr, 0, {{6, square_indices, nullptr, nullptr, false, true}});
    };
    const auto g1 = make_square();
    const auto g2 = make_square();
    const auto shared = make_square();

    std::array<float, 12> model_matrix{1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0};
    zcls::Node owner_a{}, owner_b{};
    auto context_for = [&](const void *owner, float tx, float tz) {
      model_matrix[9] = tx;
      model_matrix[11] = tz;
      platform::ModelDrawContext context{};
      context.node = owner;
      context.model_to_world = context.model_to_camera = model_matrix.data();
      context.ordinary = true;
      context.near_z = context.clip_near = 1;
      context.far_z = 100;
      context.fx_near = context.fy_near = 16;
      context.cx = context.cy = 16;
      return context;
    };
    const std::vector<cc::geometry::Material> materials{{}};
    const cc::geometry::Fog no_fog{};
    auto submit = [&](const std::shared_ptr<const cc::geometry::Resource> &resource,
                      const void *owner, float tx, float tz) {
      require(renderer->submit_model_geometry(resource, context_for(owner, tx, tz),
                                              materials, no_fog) ==
                  cc::geometry::Submission::submitted,
              "Native model occluder submission rejected");
    };
    // One frame: model batch, optional between-batches hook, receiver batch,
    // then present() ends the frame.
    auto frame = [&](const std::function<void()> &models,
                     const std::function<void()> &between = nullptr) {
      renderer->clear(true, 0, 0, 0);
      renderer->begin_scene();
      models();
      renderer->end_scene();
      if (between)
        between();
      renderer->begin_scene();
      quad(*renderer, 4, 28, .5f, 0xffffffff, receiver_state);
      renderer->end_scene();
      renderer->present();
      std::vector<uint32_t> pixels;
      int w = 0, h = 0;
      require(renderer->read_back(&pixels, &w, &h) && w == 32 && h == 32,
              "Model-caster receiver readback failed");
      return pixels.at(16 * 32 + 16);
    };
    const auto no_models = [] {};
    const auto g1_in_light = [&] { submit(g1, &owner_a, -1.5f, 1.f); };
    const auto base = frame(no_models);
    const auto combined = frame(g1_in_light);
    require(combined != base,
            "Model occluder did not shadow the receiver (not shadow-sensitive)");
    // 1: same owner moves the same geometry out of all fixture ranges within
    // the same frame; the receiver must revert to the no-occluder base.
    const auto moved_out = frame([&] {
      submit(g1, &owner_a, -1.5f, 1.f);
      submit(g1, &owner_a, 100.f, 1.f);
    });
    require(moved_out == base,
            "Model moved out of light range in the same frame kept a stale shadow");
    // 2: same owner replaces G1 with distinct G2 at an irrelevant location;
    // G1 stays owned by this fixture, so this is not a weak-ref eviction.
    const auto replaced = frame([&] {
      submit(g1, &owner_a, -1.5f, 1.f);
      submit(g2, &owner_a, 100.f, 1.f);
    });
    require(replaced == base,
            "Replaced model geometry kept the previous caster's shadow");
    // 4: two distinct owners share one geometry resource; retiring one must
    // not delete the other owner's caster.
    const auto shared_shadow = frame([&] {
      submit(shared, &owner_a, -1.5f, 1.f);
      submit(shared, &owner_b, -1.5f, 1.f);
    });
    require(shared_shadow != base,
            "Shared-geometry model occluder lost shadow sensitivity");
    const auto other_survives = frame(
        [&] {
          submit(shared, &owner_a, -1.5f, 1.f);
          submit(shared, &owner_b, -1.5f, 1.f);
        },
        [&] {
          renderer->retire_headlight_node(reinterpret_cast<std::uintptr_t>(&owner_b));
        });
    require(other_survives == shared_shadow,
            "Retiring one shared-geometry owner deleted the other owner's caster");
    // 3: explicit producer-node retirement between batches (the generic
    // node-deletion notification node_delete issues) must invalidate the
    // model shadow source; the next receiver must not see the old shadow.
    const auto retired = frame(g1_in_light, [&] {
      renderer->retire_headlight_node(reinterpret_cast<std::uintptr_t>(&owner_a));
    });
    require(retired == base,
            "Retired model owner kept its shadow on the next receiver");
    const auto previous_renderer = zvid::render3d();
    zvid::set_render3d(renderer.get());
    Restore restore_renderer{[&] { zvid::set_render3d(previous_renderer); }};
    zmod::Model native_model{};
    const std::uint32_t uses = 2;
    const auto native_model_removal = [&](bool drop) {
      std::memcpy(native_model.header + 0xc, &uses, sizeof uses);
      owner_a.model = &native_model;
      owner_a.set_flags(owner_a.flags() | 1u);
      return frame(g1_in_light, [&] {
        require((drop ? zcls::node_drop_model(&owner_a)
                      : zcls::node_set_model(&owner_a, nullptr)) == 0,
                "Native model removal failed");
      });
    };
    require(native_model_removal(false) == base,
            "node_set_model(nullptr) bypassed shadow retirement");
    require(native_model_removal(true) == base,
            "node_drop_model bypassed shadow retirement");
    auto *released_owner = zcls::node_alloc();
    const auto released = frame(
        [&] { submit(g1, released_owner, -1.5f, 1.f); },
        [&] {
          require(zcls::node_release(released_owner) == 0,
                  "Native node release failed");
        });
    require(released == base, "node_release bypassed shadow retirement");
    // 5: a null-node model with fixture shadows enabled must fail visibly
    // instead of silently collapsing identity (unshadowed diagnostics keep
    // allowing null nodes; only the shadowed path requires a source identity).
    bool null_rejected = false;
    try {
      renderer->clear(true, 0, 0, 0);
      renderer->begin_scene();
      renderer->submit_model_geometry(g1, context_for(nullptr, -1.5f, 1.f),
                                      materials, no_fog);
      renderer->end_scene();
      renderer->present();
    } catch (const std::runtime_error &e) {
      null_rejected = std::string_view(e.what()).find(
                          "Fixture shadows require a model source identity") == 0;
    }
    renderer->drain();
    require(null_rejected,
            "Null-node model with fixture shadows enabled did not fail visibly");
    // 6: a mission generation reset without present()/frame advance must
    // invalidate the model shadow, isolating generation from frame expiry.
    renderer->mission_changed({1, 2});
    renderer->clear(true, 0, 0, 0);
    renderer->begin_scene();
    submit(g1, &owner_a, -1.5f, 1.f);
    renderer->end_scene();             // Caster submitted; frame not advanced.
    renderer->mission_changed({5, 1}); // Generation reset without present().
    const auto after_reset = frame(no_models);
    require(after_reset == base,
            "Mission generation reset without present kept a stale model shadow");
    local_light_test_env("MW34_SUN_SHADOWS", "0");
    local_light_test_env("MW34_FIXTURE_SHADOWS", "0");
    data = original;
  }
  // Budget rejection must retain the scene. Retrying the same unchanged
  // submission must reject again, rather than silently succeeding after loss.
  {
    sdlfe::CoreCriticalAssets assets{};
    assets.lighting = "flat";
    auto renderer = make_check_renderer(window, backend, {}, assets);
    renderer->mission_changed({5, 1});
    renderer->set_viewport(0, 0, 32, 32);
    const std::vector<uint8_t> pixels(std::size_t(4096) * 4096 * 4, 128);
    platform::DrawState first{}, second{};
    first.texture = renderer->create_texture(4096, 4096, pixels.data(), 1);
    second.texture = renderer->create_texture(4096, 4096, pixels.data(), 1);
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
