// Double-precision analytical oracle, independent of the GPU producer/readback.
bool tiled_expected(const mw34::tiled::View &v, const mw34::effects::Light &l, unsigned x,
                    unsigned y) {
  std::array<double, 3> world{}, center{}, translation{};
  double radius = l.start[3];
  for (unsigned i = 0; i < 3; ++i)
    world[i] = l.start[i];
  if (l.end[3] == 1) {
    double length2 = 0;
    for (unsigned i = 0; i < 3; ++i) {
      const double delta = double(l.end[i]) - l.start[i];
      length2 += delta * delta;
      world[i] = (double(l.end[i]) + l.start[i]) / 2;
    }
    radius += std::sqrt(length2) / 2;
  }
  auto length = [](const auto &a) {
    double sum = 0;
    for (double n : a)
      sum += n * n;
    return std::sqrt(sum);
  };
  double gramBound = 0;
  for (unsigned i = 0; i < 3; ++i) {
    translation[i] = v.camera[i * 4 + 3];
    center[i] = translation[i];
    for (unsigned j = 0; j < 3; ++j)
      center[i] += v.camera[i * 4 + j] * world[j];
    double rowSum = 0;
    for (unsigned j = 0; j < 3; ++j) {
      double dot = 0;
      for (unsigned k = 0; k < 3; ++k)
        dot += double(v.camera[i * 4 + k]) * v.camera[j * 4 + k];
      rowSum += std::abs(dot);
    }
    gramBound = std::max(gramBound, rowSum);
  }
  radius *= std::sqrt(gramBound);
  radius += 1e-5 * (1 + length(world) + length(translation) + length(center) + radius);
  if (center[2] + radius < v.depth[0] || center[2] - radius > v.depth[1])
    return false;
  const double left = x * 16, right = std::min((x + 1) * 16, v.extent[0]);
  const double top = y * 16, bottom = std::min((y + 1) * 16, v.extent[1]);
  const auto &p = v.projection;
  const std::array<std::array<double, 3>, 4> planes{{{p[0], 0, p[2] - left},
                                                     {-p[0], 0, right - p[2]},
                                                     {0, p[1], p[3] - top},
                                                     {0, -p[1], bottom - p[3]}}};
  for (const auto &n : planes) {
    double dot = 0;
    for (unsigned i = 0; i < 3; ++i)
      dot += n[i] * center[i];
    if (dot < -radius * length(n))
      return false;
  }
  return true;
}
mw34::vkscene::Scene make_tiled_view_scene(bool enabled, bool second_near = false) {
  using namespace mw34;
  vkscene::Scene scene{};
  scene.width = 64;
  scene.height = 32;
  scene.has_depth = true;
  scene.color.resize(64 * 32);
  scene.depth.resize(64 * 32);
  scene.textures.push_back({1, 1, 1, 1, vkscene::TexFormat::rgb565, {0x7bef}, {}});
  std::vector<platform::TLVertex> vertices;
  for (unsigned view = 0; view < 2; ++view) {
    const float left = view ? 36.f : 4.f, right = left + 24;
    for (auto p : std::array<std::array<float, 2>, 6>{
             {{left, 4}, {right, 4}, {right, 28}, {left, 4}, {right, 28}, {left, 28}}})
      vertices.push_back({p[0], p[1], .5f, .5f, 0xffffffff, 0xff000000, 0, 0});
    vkscene::Draw draw{};
    draw.first = view * 6;
    draw.count = 6;
    draw.texture = 0;
    draw.key = {0, 5, 6, 1, 7, 1, 1, 0};
    draw.scissor = {{0, 0}, {64, 32}};
    draw.push.target[0] = 64;
    draw.push.target[1] = 32;
    draw.push.target[2] = .5f;
    draw.push.mode[0] = 6;
    draw.push.mode[1] = draw.push.mode[2] = 2 | (2 << 8);
    auto camera = std::make_shared<sun::Tl>();
    camera->camera_world = {1, 0, 0, view && !second_near ? 100.f : 0.f, 0, 1, 0, 0, 0, 0, 1, 0};
    camera->projection = {1, 16, 16, view ? 48.f : 16.f, 16, 100};
    draw.sun_tl = camera;
    draw.lit_normals = std::make_shared<const std::vector<std::array<float, 3>>>(
        6, std::array<float, 3>{0, 0, -1});
    scene.draws.push_back(draw);
    scene.order.push_back({false, view});
  }
  scene.vertices.resize(vertices.size() * sizeof(vertices[0]));
  std::memcpy(scene.vertices.data(), vertices.data(), scene.vertices.size());
  if (enabled) {
    scene.effect_lights.params[0] = 1;
    scene.effect_lights.lights[0] = {{0, 0, 1, 2}, {0, 0, 1, 0}, {1, 1, 1, 1}};
  }
  return scene;
}
void check_tiled_view_render() {
  using namespace mw34;
  sun::Settings settings{};
  settings.enabled = true;
  settings.strength = 0;
  settings.ambient = .1f;
  cc_mw3_re::RendererBridgeConfig config{};
  config.effect_lights = true;
  config.effect_light_catalog = "diagnostic-owned-scene";
  vkscene::Renderer renderer(vkscene::Renderer::ColorTarget::rgba8, {},
                             vkscene::Renderer::Quality{1, 1, 1, false}, true, settings, false,
                             config);
  auto off = make_tiled_view_scene(false);
  renderer.render(off);
  auto on = make_tiled_view_scene(true);
  renderer.render(on);
  constexpr unsigned first = 16 * 64 + 16, second = 16 * 64 + 48;
  require(on.color[first] != off.color[first], "Tiled primary receiver did not illuminate");
  require(on.color[second] == off.color[second],
          "Tiled light leaked into translated secondary camera");
  const auto expected = on.color;
  std::swap(on.draws[0], on.draws[1]);
  renderer.render(on);
  require(on.color == expected, "Tiled fragment view offset changed with draw order");
  auto near = make_tiled_view_scene(true, true);
  renderer.render(near);
  require(near.color[second] != off.color[second],
          "Secondary view fixture did not exercise illumination");
  renderer.render(near, true, false); // GPU still owns these view buffers on return.
  auto reused = make_tiled_view_scene(true);
  renderer.render(reused);
  require(reused.color == expected,
          "Tiled asynchronous view buffers were reused before fence or retained stale lights");

  auto degenerate = make_tiled_view_scene(true);
  auto degenerate_camera = std::make_shared<sun::Tl>(*degenerate.draws[0].sun_tl);
  degenerate_camera->camera_world[0] = 1e-8f;
  degenerate.draws[0].sun_tl = degenerate_camera;
  renderer.render(degenerate);
  require(degenerate.color[first] != off.color[first],
          "Degenerate tiled view did not preserve the draw through all-light fallback");
}

void check_tiled_view_budget() {
  using namespace mw34;
  const std::array<float, 12> identity{1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0};
  auto degenerate = identity;
  degenerate[0] = 1e-8f;
  constexpr unsigned all_effect_lights = ~0u - 1;
  bool fallback_reported = false;
  unsigned fallback_logs = 0;
  std::string fallback_reason;
  for (unsigned repeat = 0; repeat < 3; ++repeat) {
    auto draw_view = ~0u;
    mw34::tiled::Mat34 camera{};
    const bool prepared = tiled::try_affine_camera_or_all_lights(
        camera, draw_view, all_effect_lights, fallback_reported,
        [&] { return tiled::compose_affine(identity, tiled::inverse_affine(degenerate)); },
        [&](const char *reason) {
          ++fallback_logs;
          fallback_reason = reason;
        });
    require(!prepared, "Degenerate tiled affine unexpectedly prepared a camera");
    require(draw_view == all_effect_lights,
            "Degenerate tiled affine did not select the all-light fallback");
  }
  require(fallback_logs == 1, "Repeated degenerate tiled draws logged more than once");
  require(fallback_reason == "inverse_affine: result out of bounds",
          "Near-degenerate tiled matrix did not exercise affine overflow handling");

  const auto unchanged_on_failure = [](tiled::ViewBudget &budget, uint64_t length) {
    const auto used = budget.used;
    const auto views = budget.views;
    require(!budget.reserve(length), "Tiled budget accepted an excessive reservation");
    require(budget.used == used && budget.views == views,
            "Failed tiled budget reservation changed state");
  };
  tiled::ViewBudget count{1024 * 1024, 256};
  for (unsigned i = 0; i < 64; ++i) {
    const auto offset = count.reserve(260);
    require(offset && *offset == uint64_t(i) * 512,
            "Tiled budget count/alignment admission mismatch");
  }
  unchanged_on_failure(count, 260);

  const auto wide = tiled::make_view(identity, {1720, -720, 1720, 720}, 1, 100, 3440, 1440);
  tiled::ViewBudget legacy{128ULL * 1024 * 1024, 256};
  unsigned admitted = 0;
  for (unsigned i = 0; i < 27; ++i) {
    const auto used = legacy.used;
    const auto views = legacy.views;
    const auto offset = legacy.reserve(tiled::bytes(wide));
    if (offset) {
      require(*offset % legacy.alignment == 0 && legacy.used <= legacy.range,
              "Tiled byte budget returned an unaligned/out-of-range allocation");
      ++admitted;
    } else {
      require(legacy.used == used && legacy.views == views,
              "Tiled ultrawide budget failure changed state");
    }
  }
  require(admitted == 26, "128 MiB tiled budget did not reject the 27th ultrawide view");
  require(legacy.reserve(4).has_value(), "Failed large reservation poisoned smaller reuse");

  tiled::ViewBudget padding{512, 256};
  require(padding.reserve(260).value() == 0, "Tiled initial reservation offset");
  unchanged_on_failure(padding, 1); // Padding alone fills the remaining space.
  tiled::ViewBudget exact{516, 256};
  require(exact.reserve(260).value() == 0 && exact.reserve(4).value() == 512 &&
              exact.used == 516,
          "Tiled exact aligned byte boundary was rejected");
  unchanged_on_failure(exact, 1);

  tiled::ViewBudget overflow{UINT64_MAX, 256, UINT64_MAX - 1, 1};
  unchanged_on_failure(overflow, 1); // Rounding up itself would overflow uint64_t.
  tiled::ViewBudget addition{UINT64_MAX, 1, 1, 1};
  unchanged_on_failure(addition, UINT64_MAX);
  require(addition.reserve(UINT64_MAX - 1).value() == 1 && addition.used == UINT64_MAX,
          "Tiled checked addition rejected a representable exact limit");
  unchanged_on_failure(addition, 1);
  tiled::ViewBudget zero_alignment{512, 0};
  unchanged_on_failure(zero_alignment, 4);
}

mw34::vkscene::Scene make_tiled_overflow_scene(unsigned light_count) {
  using namespace mw34;
  // Keep the full raster and vertex buffer identical in bulk and serial renders.
  // Each exact projection owns a disjoint 32-pixel stripe, including views 64/65.
  auto scene = make_tiled_view_scene(false);
  const auto prototype = scene.draws.front();
  scene.width = 66 * 32;
  scene.color.assign(scene.width * scene.height, 0);
  scene.depth.assign(scene.width * scene.height, 0);
  scene.draws.clear();
  scene.order.clear();
  std::vector<platform::TLVertex> vertices;
  for (unsigned view = 0; view < 66; ++view) {
    const float left = float(view * 32 + 4), right = left + 24;
    for (auto p : std::array<std::array<float, 2>, 6>{
             {{left, 4}, {right, 4}, {right, 28}, {left, 4}, {right, 28}, {left, 28}}})
      vertices.push_back({p[0], p[1], .5f, .5f, 0xffffffff, 0xff000000, 0, 0});
    auto draw = prototype;
    draw.first = view * 6;
    draw.scissor = {{0, 0}, {scene.width, scene.height}};
    draw.push.target[0] = float(scene.width);
    auto camera = std::make_shared<sun::Tl>();
    camera->camera_world = {1, 0, 0, view % 2 ? 100.f : 0.f, 0, 1, 0, 0, 0, 0, 1, 0};
    camera->projection = {1, 16, 16, float(view * 32 + 16), 16, 100};
    draw.sun_tl = camera;
    scene.draws.push_back(draw);
    scene.order.push_back({false, view});
  }
  scene.vertices.resize(vertices.size() * sizeof(vertices[0]));
  std::memcpy(scene.vertices.data(), vertices.data(), scene.vertices.size());
  const std::array<effects::Light, 6> mixed{{
      {{-.3f, 0, 1, 3}, {-.3f, 0, 1, 0}, {.2f, .05f, .03f, 1}},
      {{-.5f, -.5f, 1, 3}, {.5f, .5f, 1, 1}, {.03f, .2f, .05f, 1}},
      {{0, 0, 1, 3}, {0, 0, 1, 2}, {.05f, .03f, .2f, 1}},
      {{.3f, 0, 1, 3}, {.3f, 0, 1, 0}, {.1f, .06f, .04f, 1}},
      {{.2f, 0, 1, 3}, {0, 0, 1, 2}, {.04f, .1f, .06f, 1}},
      {{-.5f, .5f, 1, 3}, {.5f, -.5f, 1, 1}, {.06f, .04f, .1f, 1}},
  }};
  scene.effect_lights.params[0] = float(light_count);
  for (unsigned i = 0; i < light_count; ++i) {
    scene.effect_lights.lights[i] = mixed[i % mixed.size()];
    scene.effect_lights.lights[i].color[3] = 3.f / float(light_count);
    scene.effect_lights.cones[i] = {.98f, .7f, 1, 0};
  }
  return scene;
}

void check_tiled_overflow_render() {
  using namespace mw34;
  sun::Settings settings{};
  settings.enabled = true;
  settings.strength = 0;
  settings.ambient = .1f;
  cc_mw3_re::RendererBridgeConfig config{};
  config.effect_lights = true;
  config.effect_light_catalog = "diagnostic-owned-scene";
  vkscene::Renderer renderer(vkscene::Renderer::ColorTarget::rgba8, {},
                             vkscene::Renderer::Quality{1, 1, 1, false}, true, settings, false,
                             config);
  auto off = make_tiled_overflow_scene(0);
  renderer.render(off);
  for (unsigned light_count : {6u, 64u}) {
    const auto input = make_tiled_overflow_scene(light_count);
    auto expected = off.color;
    // Every reference render admits only one exact tiled view. It cannot enter
    // the overflow shader path, so disabling that path cannot make this pass.
    for (unsigned view = 0; view < input.draws.size(); ++view) {
      auto serial = input;
      serial.draws = {input.draws[view]};
      serial.order = {{false, 0}};
      renderer.render(serial);
      unsigned illuminated = 0;
      for (unsigned y = 0; y < input.height; ++y)
        for (unsigned x = 0; x < input.width; ++x) {
          const auto pixel = y * input.width + x;
          if (x / 32 == view) {
            expected[pixel] = serial.color[pixel];
            if (serial.color[pixel] != off.color[pixel])
              ++illuminated;
          } else {
            require(serial.color[pixel] == 0,
                    "Serial tiled reference wrote outside its own camera stripe");
          }
        }
      require(view % 2 ? illuminated == 0 : illuminated > 0,
              "Serial tiled reference did not exercise alternating lit/dark views");
    }
    auto bulk = input;
    renderer.render(bulk);
    require(bulk.color == expected,
            "Tiled overflow pixels/masks differ from serial one-view reference");
    auto reversed = input;
    std::reverse(reversed.draws.begin(), reversed.draws.end());
    renderer.render(reversed);
    require(reversed.color == expected,
            "Reversed tiled overflow pixels/masks differ from serial reference");
    renderer.render(reversed, true, false);
    auto reused = input;
    renderer.render(reused);
    require(reused.color == expected, "Tiled overflow async reuse changed lighting");

    auto malformed = input;
    auto invalid = std::make_shared<sun::Tl>(*malformed.draws.back().sun_tl);
    invalid->projection[1] = 0;
    malformed.draws.back().sun_tl = invalid;
    bool rejected = false;
    try {
      renderer.render(malformed);
    } catch (const std::exception &) {
      rejected = true;
    }
    require(rejected, "Malformed projection after tiled overflow was accepted");
    reused = input;
    renderer.render(reused);
    require(reused.color == expected, "Rejected overflow draw poisoned valid render reuse");
  }
  std::fprintf(stderr, "Tiled overflow: 66 exact views, mixed/64 lights, serial reference, "
                       "reverse order, async reuse and malformed recovery passed\n");
}
void check_tiled_gpu() {
  using namespace mw34;
  check_tiled_view_budget();
  {
    const uint8_t rgba[3][4]{{8, 4, 8, 255}, {255, 0, 255, 255}, {0x11, 0x22, 0x33, 0x44}};
    const uint8_t packed[3][2]{{0x21, 0x08}, {0x1f, 0xfc}, {0x23, 0x41}};
    for (unsigned i = 0; i < 3; ++i) {
      const auto key = materials::canonical_upload_key(1, 1, rgba[i], i + 1);
      require(key.hash == materials::normal_hash(packed[i], 2) && key.format == i + 1,
              "Native upload key packed format/hash");
    }
    auto changed = std::array<uint8_t, 4>{0x11, 0x22, 0x33, 0x54};
    require(materials::canonical_upload_key(1, 1, changed.data(), 3).hash !=
                materials::canonical_upload_key(1, 1, rgba[2], 3).hash,
            "Native upload key ignored alpha");
    materials::SurfaceKey original{};
    const bool had = materials::get_active_surface_key(&original);
    const materials::SurfaceKey prior{2, 2, 1, 123}, inner{1, 1, 3, 456};
    {
      materials::ScopedUploadKey outer(prior);
      try {
        materials::ScopedUploadKey nested(inner);
        throw std::runtime_error("scope control");
      } catch (const std::runtime_error &) {
      }
      materials::SurfaceKey restored{};
      require(materials::get_active_surface_key(&restored) && restored == prior,
              "Native upload key exception restoration");
    }
    materials::SurfaceKey restored{};
    require(materials::get_active_surface_key(&restored) == had && (!had || restored == original),
            "Native upload key outer restoration");
  }
  {
    std::vector<uint8_t> large_rgba(8192u * 1024u * 4u, 255);
    const auto large_key = materials::canonical_upload_key(8192, 1024, large_rgba.data(), 1);
    require(large_key.width == 8192 && large_key.height == 1024,
            "Native upload key restricted display-cap-sized texture");

    bool overflow_rejected = false;
    try {
      (void)materials::canonical_upload_key(UINT32_MAX, UINT32_MAX, large_rgba.data(), 1);
    } catch (const std::overflow_error &) {
      overflow_rejected = true;
    }
    require(overflow_rejected, "canonical_upload_key rejects overflow before reading buffer");
  }
  const std::array<float, 12> identity{1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0};
  auto base = tiled::make_view(identity, {32, -32, 32.5f, 24.5f}, 1, 100, 65, 49);
  auto translated = identity;
  translated[3] = -100;
  auto reflected = identity;
  reflected[0] = -1;
  auto skewed = identity;
  skewed[0] = 1.0008f;
  std::vector<tiled::View> views{base,
                                 tiled::make_view(translated, base.projection, 1, 100, 65, 49),
                                 tiled::make_view(reflected, base.projection, 1, 100, 65, 49),
                                 tiled::make_view(skewed, base.projection, 1, 100, 65, 49)};
  effects::Uniform lights{};
  lights.params[0] = 6;
  lights.lights[0] = {{-4, 0, 8, .8f}, {-4, 0, 8, 0}, {1, 1, 1, 1}};
  lights.lights[1] = {{4, 0, 8, 1}, {0, 0, -1, 2}, {1, 1, 1, 1}};
  lights.lights[2] = {{-3, -2, 5, .2f}, {3, 2, 5, 1}, {1, 1, 1, 1}};
  lights.lights[3] = {{0, 0, .9f, .4f}, {0, 0, .9f, 0}, {1, 1, 1, 1}};
  lights.lights[4] = {{0, 0, -5, .1f}, {0, 0, -5, 0}, {1, 1, 1, 1}};
  lights.lights[5] = {{0, 0, 101, .5f}, {0, 0, 101, 0}, {1, 1, 1, 1}};
  vkscene::Renderer renderer;
  {
    auto stretched = identity;
    stretched[0] = 1.0008f;
    auto v = tiled::make_view(stretched, {32, -32, 32, 24}, 1, 100, 65, 49);
    effects::Uniform fx{};
    fx.params[0] = 1;
    fx.lights[0] = {{1, 0, 10, 1}, {1, 0, 10, 0}, {1, 1, 1, 1}};
    auto data = renderer.probe_tiled_lists({v}, fx);
    std::uint32_t offset = (1 * v.extent[2] + 1) * 65;
    require(data[0][offset] == 1 && data[0][offset + 1] == 0,
            "Tiled camera norm bound lost tangent light");
  }
  auto verify = [&](const auto &cameras, const effects::Uniform &fx) {
    const auto data = renderer.probe_tiled_lists(cameras, fx);
    require(data.size() == cameras.size(), "Tiled producer lost a view");
    unsigned populated = 0, empty = 0;
    for (size_t view = 0; view < cameras.size(); ++view) {
      const auto &v = cameras[view];
      require(data[view].size() * 4 == tiled::bytes(v), "Tiled producer readback size");
      for (unsigned y = 0; y < v.extent[3]; ++y)
        for (unsigned x = 0; x < v.extent[2]; ++x) {
          const auto offset = (y * v.extent[2] + x) * 65;
          std::vector<uint32_t> expected;
          for (unsigned i = 0; i < unsigned(fx.params[0]); ++i)
            if (tiled_expected(v, fx.lights[i], x, y))
              expected.push_back(i);
          require(data[view][offset] == expected.size(),
                  "Tiled GPU mask differs from analytical CPU reference");
          for (size_t i = 0; i < expected.size(); ++i)
            require(data[view][offset + 1 + i] == expected[i],
                    "Tiled GPU light order/index mismatch");
          if (expected.empty())
            ++empty;
          else
            ++populated;
        }
    }
    return std::array<unsigned, 2>{populated, empty};
  };
  const auto coverage = verify(views, lights);
  require(coverage[0] > 0 && coverage[1] > 0, "Tiled fixture failed to exercise actual culling");
  std::reverse(views.begin(), views.end());
  verify(views, lights);
  lights.params[0] = 64;
  for (auto &l : lights.lights)
    l = lights.lights[0];
  verify(views, lights);
  lights.params[0] = 0;
  verify(views, lights);
  verify(
      std::vector<tiled::View>{tiled::make_view(identity, {32, -32, 32, 24}, 1, 100, 5120, 2160)},
      lights);
  auto rejects = [&](const auto &cameras, const auto &fx) {
    bool failed = false;
    try {
      renderer.probe_tiled_lists(cameras, fx);
    } catch (const std::exception &) {
      failed = true;
    }
    require(failed, "Malformed or over-budget tiled input was accepted");
  };
  auto malformed = base;
  malformed.extent[2]++;
  rejects(std::vector<tiled::View>{malformed}, lights);
  lights.params[0] = 65;
  rejects(views, lights);
  lights.params[0] = 1;
  lights.lights[0].start[0] = 1e30f;
  rejects(views, lights);
  lights.lights[0] = {{0, 0, 8, 1}, {0, 0, 8, 0}, {1, 1, 1, 1}};
  // One descriptor addresses the complete shared buffer. Valid ultrawide views
  // must not inherit the old 128 MiB software cap on capable devices.
  std::vector<tiled::View> ultrawide;
  for (unsigned i = 0; i < 27; ++i) {
    auto camera = identity;
    camera[3] = float(i * 5);
    ultrawide.push_back(
        tiled::make_view(camera, {1720, -720, 1720, 720}, 1, 100, 3440, 1440));
  }
  require(tiled::bytes(ultrawide.front()) * ultrawide.size() > 128ULL * 1024 * 1024,
          "Ultrawide fixture did not exceed the old shared-buffer cap");
  const auto storage_limits = renderer.probe_tiled_storage_limits();
  require(storage_limits.offset_alignment > 0, "GPU reported zero storage-buffer alignment");
  std::uint64_t wide_bytes = 0;
  for (const auto &view : ultrawide) {
    const auto alignment = storage_limits.offset_alignment;
    wide_bytes = (wide_bytes + alignment - 1) / alignment * alignment;
    wide_bytes += tiled::bytes(view);
  }
  if (wide_bytes <= storage_limits.max_range) {
    const auto wide_coverage = verify(ultrawide, lights);
    require(wide_coverage[0] > 0 && wide_coverage[1] > 0,
            "Ultrawide views did not exercise populated and empty light lists");
    std::reverse(ultrawide.begin(), ultrawide.end());
    verify(ultrawide, lights);
    std::fprintf(stderr, "Tiled ultrawide: 27 views above 128 MiB, exact masks "
                         "and reversed order passed\n");
  } else {
    rejects(ultrawide, lights);
    std::fprintf(stderr, "Tiled ultrawide: hardware range below %llu bytes; "
                         "bounded rejection passed (oversized positive not covered)\n",
                 static_cast<unsigned long long>(wide_bytes));
  }
  const auto large = tiled::make_view(identity, {32, -32, 32, 24}, 1, 100, 5120, 2160);
  rejects(std::vector<tiled::View>(65, large), lights);
  verify(std::vector<tiled::View>{base}, lights); // rejected growth did not poison reuse
  const auto empty = renderer.probe_tiled_lists({}, lights);
  require(empty.empty(), "Empty tiled view retained prior outputs");
  auto singular = identity;
  singular[0] = 0;
  bool failed = false;
  try {
    (void)tiled::inverse_affine(singular);
  } catch (const std::exception &) {
    failed = true;
  }
  require(failed, "Singular tiled model transform accepted");
  const std::array<float, 12> model{0, 0, 2, 13, 0, 3, 0, -7, -4, 0, 0, 19};
  const auto roundtrip = tiled::compose_affine(model, tiled::inverse_affine(model));
  for (unsigned i = 0; i < 12; ++i)
    require(std::abs(roundtrip[i] - identity[i]) < 1e-5f, "Tiled affine inverse/composition");
  std::fprintf(stderr, "Tiled light GPU: exact masks, 64-light ordering, isolated views, maximum "
                       "extent and rejection recovery passed\n");
  check_tiled_view_render();
  check_tiled_overflow_render();
}
