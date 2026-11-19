#include <algorithm>
#include <array>
#include <cfenv>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <string>

#if defined(_WIN32)
#include <io.h>
#else
#include <unistd.h>
#endif

#include "frontend/sdl/gpu_hud.h"
#include "frontend/sdl/sdl_render3d.h"
#include "frontend/sdl/sdl_platform.h"
#include "frontend/sdl/sdl_twod_host.h"
#include "gamez/zimage/zimg_library.h"
#include "gamez/zrender/zrndr_blur.h"
#include "gamez/zrender/zrndr_span.h"
#include "gamez/zrender/zrndr_tint.h"
#include "gamez/zutil/zutl_path.h"
#include "gamez/zvideo/zvid_format.h"
#include "platform/prepared_hud.h"

namespace {
int random_calls = 0;
int32_t fixed_random() {
  ++random_calls;
  return 12345;
}
void require(bool value, const char* message) {
  if (!value) throw std::runtime_error(message);
}
#if defined(_WIN32)
int fd_dup(int descriptor) { return _dup(descriptor); }
int fd_dup2(int from, int to) { return _dup2(from, to); }
int fd_number(std::FILE* file) { return _fileno(file); }
void fd_close(int descriptor) { _close(descriptor); }
#else
int fd_dup(int descriptor) { return dup(descriptor); }
int fd_dup2(int from, int to) { return dup2(from, to); }
int fd_number(std::FILE* file) { return fileno(file); }
void fd_close(int descriptor) { close(descriptor); }
#endif
// Restore stderr even when a HUD assertion throws, so failures remain visible.
class StderrCapture {
 public:
  explicit StderrCapture(const std::filesystem::path& path) {
#if defined(_WIN32)
    file_ = _wfopen(path.c_str(), L"w+b");
#else
    file_ = std::fopen(path.c_str(), "w+b");
#endif
    require(file_ != nullptr, "Cannot create HUD diagnostic capture");
    std::fflush(stderr);
    saved_ = fd_dup(fd_number(stderr));
    if (saved_ < 0 || fd_dup2(fd_number(file_), fd_number(stderr)) < 0) {
      if (saved_ >= 0) fd_close(saved_);
      std::fclose(file_);
      throw std::runtime_error("Cannot redirect HUD diagnostics");
    }
  }
  ~StderrCapture() {
    std::fflush(stderr);
    fd_dup2(saved_, fd_number(stderr));
    fd_close(saved_);
    std::fclose(file_);
  }
  StderrCapture(const StderrCapture&) = delete;
  StderrCapture& operator=(const StderrCapture&) = delete;
  std::string text() {
    require(std::fflush(stderr) == 0, "Cannot flush HUD diagnostics");
    std::rewind(file_);
    std::string result;
    for (int c; (c = std::fgetc(file_)) != EOF;) result += static_cast<char>(c);
    require(!std::ferror(file_), "Cannot read HUD diagnostics");
    return result;
  }

 private:
  std::FILE* file_{};
  int saved_ = -1;
};
template <class Function>
void rejects(Function function) {
  bool rejected = false;
  try {
    function();
  } catch (const std::runtime_error&) {
    rejected = true;
  }
  require(rejected, "Malformed HUD input was accepted");
}
class Recorder : public sdlfe::FrameRenderer {
 public:
  struct Draw {
    platform::Primitive primitive;
    std::vector<platform::TLVertex> vertices;
    platform::DrawState state;
  };
  std::vector<Draw> draws;
  std::vector<std::vector<uint32_t>> images;
  std::vector<int> released;
  bool flushed = false;
  bool allocation_fails = false;
  int x = 3, y = 4, w = 5, h = 6;
  bool ok() const override { return true; }
  void capture_next(const char*) override {}
  void set_shape(const sdlfe::FrameShape*) override {}
  void flush() override { flushed = true; }
  void viewport(int* a, int* b, int* c, int* d) const override {
    *a = x;
    *b = y;
    *c = w;
    *d = h;
  }
  void set_viewport(int a, int b, int c, int d) override {
    require(flushed, "HUD changed viewport before flushing world draws");
    x = a;
    y = b;
    w = c;
    h = d;
  }
  int32_t create_texture(int width, int height, const uint8_t* pixels, uint8_t) override {
    if (allocation_fails) return -1;
    std::vector<uint32_t> copy(size_t(width) * height);
    std::memcpy(copy.data(), pixels, copy.size() * 4);
    images.push_back(std::move(copy));
    return int(images.size() - 1);
  }
  void release_texture(int32_t handle) override { released.push_back(handle); }
  void update_texture(int32_t, int, int, const uint8_t*) override {
    throw std::runtime_error("Unexpected texture update");
  }
  void clear(bool, uint8_t, uint8_t, uint8_t) override {}
  void begin_scene() override {}
  void end_scene() override {}
  void draw(platform::Primitive primitive, const platform::TLVertex* vertices, int count,
            const platform::DrawState& state) override {
    draws.push_back({primitive, {vertices, vertices + count}, state});
  }
  void set_fog_color(uint8_t, uint8_t, uint8_t) override {}
  void present() override {}
};
void artwork_checks(const std::filesystem::path& directory) {
  std::filesystem::create_directories(directory);
  const auto path = directory / "0000000000000001.rgba";
  std::array<uint8_t, 36> bytes{};
  std::memcpy(bytes.data(), "MW3H", 4);
  bytes[4] = 2;
  bytes[8] = 1;
  const float uv[] = {.25f, 0, .75f, 1};
  std::memcpy(bytes.data() + 12, uv, sizeof uv);
  const uint8_t pixels[] = {200, 100, 50, 128, 255, 200, 100, 0};
  std::memcpy(bytes.data() + 28, pixels, 8);
  auto write = [&](size_t count) {
    std::ofstream file(path, std::ios::binary);
    file.write(reinterpret_cast<const char*>(bytes.data()), count);
  };
  write(bytes.size());
  auto loaded = platform::load_hud_artwork(directory);
  require(loaded.size() == 1 && loaded.at(1)->pixels == std::vector<uint32_t>{0x80193264, 0},
          "MW3H premultiplication changed");
  require(loaded.at(1)->u0 == .25f && loaded.at(1)->u1 == .75f, "MW3H crop was lost");
  write(35);
  rejects([&] { platform::load_hud_artwork(directory); });
  bytes[4] = 0;
  write(36);
  rejects([&] { platform::load_hud_artwork(directory); });
  bytes[4] = 2;
  bytes[24] = 0;
  bytes[25] = 0;
  bytes[26] = 0x80;
  bytes[27] = 0x7f;
  write(36);
  rejects([&] { platform::load_hud_artwork(directory); });
  uint16_t opaque[] = {0xf800, 0};
  require(platform::hud_identity(2, 1, opaque, 2) == 0xdaa81911a07d967eULL,
          "Private HUD fingerprint contract changed");
  rejects([&] { platform::hud_identity(2, 2, opaque, 2); });

  const auto first_root = directory / "first";
  const auto second_root = directory / "second";
  std::filesystem::create_directories(first_root / "ui" / "sprites");
  std::filesystem::create_directories(second_root / "ui" / "sprites");
  const auto sprite = "ui/sprites/daa81911a07d967e.rgba";
  std::memcpy(bytes.data() + 12, uv, sizeof uv);
  write(bytes.size());
  std::filesystem::copy_file(path, first_root / sprite);
  bytes[28] = 9;
  write(bytes.size());
  std::filesystem::copy_file(path, second_root / sprite);
  Recorder recorder;
  sdlfe::HudOptions options;
  options.mode = "core-critical";
  options.text = false;
  options.artwork = {first_root.string(), second_root.string()};
  StderrCapture diagnostics(directory / "conflict.log");
  {
    sdlfe::GpuHud hud(recorder, options);
    std::array<uint16_t, 2> shadow{};
    zimg::Texture source{};
    source.width = source.width_again = 2;
    source.height = 1;
    source.pixels = opaque;
    source.flags = zimg::kTwoBytes;
    zrndr::target2d() = {reinterpret_cast<uint8_t*>(shadow.data()), 2, 1, 4, 6};
    hud.begin(shadow.data(), 2, 1, 4, 3);
    zrndr::blit16(&source, 0, 0, 0, nullptr);
    require(hud.finish(), "Conflicting HUD artwork did not draw");
    require(recorder.images == std::vector<std::vector<uint32_t>>{{0x80193264, 0}},
            "Conflicting HUD artwork did not keep the first pack's pixels");
    require(recorder.draws.size() == 1 && recorder.draws[0].state.texture == 0,
            "Conflicting HUD artwork did not draw the uploaded winning texture");
    zrndr::target2d() = {};
  }
  const auto expected = "GPU HUD: conflicting identity daa81911a07d967e; keeping " +
                        first_root.string() + ", skipping " + second_root.string();
  require(diagnostics.text().find(expected) != std::string::npos,
          "Conflicting HUD artwork did not report the identity and winning/skipped packs");
}
void drawing_checks() {
  Recorder recorder;
  sdlfe::HudOptions options;
  options.mode = "core-critical";
  options.text = false;
  std::array<uint16_t, 48> baseline{}, shadow{};
  baseline.fill(0xf81f);
  shadow = baseline;
  uint16_t source_pixels[] = {0xf800, 0x07e0, 0x001f, 0};
  zimg::Texture source{};
  source.width = source.height = 2;
  source.width_again = 2;
  source.pixels = source_pixels;
  source.flags = zimg::kAlpha | zimg::kTwoBytes;
  auto target = [&](auto& pixels) {
    zrndr::target2d() = {reinterpret_cast<uint8_t*>(pixels.data()), 8, 6, 16, 6};
  };
  auto paint = [&] {
    zrndr::blit16(&source, -1, 2, 0, nullptr);
    zrndr::line16(1, 1, 4, 1, 0xffff);
    zrndr::span_state().dest = zrndr::target2d().base + 4 * 16;
    zrndr::span_fill16(0x001f, 3);
  };
  target(baseline);
  paint();
  target(shadow);
  {
    sdlfe::GpuHud hud(recorder, options);
    const int previous = std::fegetround();
    std::fesetround(FE_DOWNWARD);
    std::feraiseexcept(FE_INVALID);
    const int flags = std::fetestexcept(FE_ALL_EXCEPT);
    hud.begin(shadow.data(), 8, 6, 16, 18);
    paint();
    require(hud.finish(), "Ordinary native HUD did not use GPU composition");
    require(std::fegetround() == FE_DOWNWARD && std::fetestexcept(FE_ALL_EXCEPT) == flags,
            "GPU HUD polluted native FP state");
    std::feclearexcept(FE_ALL_EXCEPT);
    std::fesetround(previous);
    require(shadow == baseline, "Observing draws changed the native CPU shadow");
    require(recorder.draws.size() == 3 && recorder.draws[0].state.sharp &&
                recorder.draws[1].primitive == platform::Primitive::kStrip &&
                recorder.draws[1].vertices.size() == 22,
            "GPU HUD lost draw ordering or logical pixel coverage");
    const auto& vertices = recorder.draws[0].vertices;
    require(vertices[0].sx == 0 && vertices[0].sy == 2 && vertices[0].tu == .5f &&
                vertices[2].sx == 1 && vertices[2].sy == 4,
            "GPU image clip/crop changed");
    require(recorder.x == 3 && recorder.y == 4 && recorder.w == 5 && recorder.h == 6,
            "HUD did not restore world viewport");
    source_pixels[0] = 0;
    require(recorder.images[0][0] == 0xff0000ff, "GPU texture borrowed native pixels");
    hud.begin(shadow.data(), 8, 6, 16, 18);
    zrndr::observe_framebuffer_write(shadow.data(), "fixture read/write effect");
    require(!hud.finish(), "Read/write effect discarded the CPU compatibility layer");
    require(hud.frame_stats().shadow_reasons.at("fixture read/write effect") == 1,
            "Read/write effect did not report its menu fallback reason");
    const auto draws_before_observation = recorder.draws.size();
    const auto shadow_before_observation = shadow;
    hud.begin_observation(shadow.data(), 8, 6, 16, 18);
    zrndr::blit16(&source, 1, 2, 0, nullptr);
    require(hud.finish(), "Recorded menu image did not pass observation");
    // The previous frame fell back (shadow reason). begin resets the whole counter struct and finish
    // assigns the flag on every path, so this frame must not inherit that fallback.
    require(hud.frame_stats().images == 1 && hud.frame_stats().text_hits == 0 &&
                !hud.frame_stats().fallback && hud.frame_stats().shadow_reasons.empty(),
            "Recorded menu image counters were incorrect or inherited an earlier fallback");
    require(recorder.draws.size() == draws_before_observation && shadow != shadow_before_observation,
            "Menu observation submitted GPU draws or changed CPU blit behavior");
    require(!zrndr::draw_observer(), "Menu observation left a stale draw observer");
    hud.begin_observation(shadow.data(), 8, 6, 16, 18);
    zrndr::observe_framebuffer_write(shadow.data(), "fixture menu ripple");
    require(!hud.finish(), "Unsupported menu write did not request native fallback");
    require(hud.frame_stats().fallback &&
                hud.frame_stats().shadow_reasons.at("fixture menu ripple") == 1 &&
                !zrndr::draw_observer(),
            "Unsupported menu write lost its fallback reason or left a stale observer");
    hud.begin(shadow.data(), 8, 6, 16, 18);
    zrndr::line16(1, 1, 4, 1, 0xffff);
    zrndr::set_finish_target(shadow.data(), 8, 6, 16);
    zrndr::blur(nullptr, 3);
    require(!hud.finish(), "Pause combined blur discarded the CPU compatibility layer");
    baseline = shadow;
    zrndr::noise_table().assign(0x6401, 32);
    target(baseline);
    zrndr::line16(1, 1, 4, 1, 0xffff);
    zrndr::set_finish_target(baseline.data(), 8, 6, 16);
    random_calls = 0;
    zrndr::static_fill(nullptr, 1, 0x001f, 0x07e0, 0xf800, fixed_random);
    const int baseline_calls = random_calls;
    target(shadow);
    hud.begin(shadow.data(), 8, 6, 16, 18);
    zrndr::line16(1, 1, 4, 1, 0xffff);
    zrndr::set_finish_target(shadow.data(), 8, 6, 16);
    random_calls = 0;
    zrndr::static_fill(nullptr, 1, 0x001f, 0x07e0, 0xf800, fixed_random);
    require(
        !hud.finish() && shadow == baseline && random_calls == baseline_calls,
        "Damage static changed native pixels/random calls or discarded compatibility composition");
    hud.begin(shadow.data(), 8, 6, 16, 18);
    source_pixels[0] = 0xf81f;
    source.flags = zimg::kTwoBytes;
    zrndr::blit16(&source, 0, 0, 0, nullptr);
    require(!hud.finish(), "Unkeyed layer erase became opaque magenta");
    hud.begin(shadow.data(), 8, 6, 16, 18);
    hud.cancel();
    require(!zrndr::draw_observer() && !hud.finish(), "Cancelled target left a dangling observer");
    hud.begin(shadow.data(), 8, 6, 16, 18);
    require(!hud.finish(), "Empty list suppressed an unobserved canvas");
  }
  require(recorder.released.size() == recorder.images.size(),
          "HUD GPU textures leaked at shutdown");
  Recorder failing;
  failing.allocation_fails = true;
  {
    sdlfe::GpuHud hud(failing, options);
    hud.begin(shadow.data(), 8, 6, 16, 18);
    source_pixels[0] = 0xf800;
    source.flags = zimg::kAlpha | zimg::kTwoBytes;
    rejects([&] { zrndr::blit16(&source, 0, 0, 0, nullptr); });
    hud.cancel();
    require(failing.draws.empty(), "Texture allocation failure drew an untextured HUD");
  }
  zrndr::target2d() = {};
}

void menu_background_checks(const std::filesystem::path& directory) {
  class MenuRecorder : public Recorder {
   public:
    unsigned updates = 0;
    unsigned creation_attempts = 0;
    unsigned preflight_attempts = 0;
    bool fail_next_texture = false;
    bool throw_next_texture = false;
    bool throw_next_preflight = false;
    int dimension_limit = 16384;
    const sdlfe::FrameShape* shape = nullptr;
    void set_shape(const sdlfe::FrameShape* value) override { shape = value; }
    int32_t create_texture(int width, int height, const uint8_t* pixels, uint8_t type) override {
      ++creation_attempts;
      if (width > dimension_limit || height > dimension_limit)
          throw std::runtime_error("Synthetic device texture size limit");
      if (throw_next_texture) {
          throw_next_texture = false;
          throw std::runtime_error("Synthetic texture allocation failure");
      }
      if (fail_next_texture) {
        fail_next_texture = false;
        return -1;
      }
      return Recorder::create_texture(width, height, pixels, type);
    }
    void prepare_canvas_textures(const std::vector<int32_t> &textures) override {
        ++preflight_attempts;
        require(textures.size() == 4 || textures.size() == 1,
                "Menu did not preflight its image and maps (GPU) or its composed texture (CPU)");
        if (throw_next_preflight) {
            throw_next_preflight = false;
            throw std::runtime_error("Synthetic deferred Vulkan texture allocation failure");
        }
    }
    void update_texture(int32_t handle, int width, int height, const uint8_t* pixels) override {
      auto& image = images.at(size_t(handle));
      require(image.size() == size_t(width) * height, "Menu updated a texture at the wrong size");
      std::memcpy(image.data(), pixels, image.size() * 4);
      ++updates;
    }
  };
  const auto path = directory / "menu-background.rgb";
  {
    std::ofstream file(path, std::ios::binary);
    const uint8_t header[24] = {'M', 'W', 'H', 'D', 'B', 'G', '1', 0,
                                16, 0, 0, 0, 16, 0, 0, 0, 8, 0, 0, 0, 8, 0, 0, 0};
    const std::array<uint8_t, 16 * 16 * 3> image{};
    file.write(reinterpret_cast<const char*>(header), sizeof header);
    file.write(reinterpret_cast<const char*>(image.data()), image.size());
    require(bool(file), "Cannot write synthetic menu image");
  }
  std::array<uint16_t, 64> original{}, frame{};
  original.fill(uint16_t((12 << 11) | (25 << 5) | 12));
  zimg::Texture source{};
  source.width = source.height = source.width_again = 8;
  source.pixels = original.data();
  zrndr::set_menu_background_source(&source);
  zrndr::begin_menu_background_frame();
  zrndr::target2d() = {reinterpret_cast<uint8_t*>(frame.data()), 8, 8, 16, 6};
  zrndr::blit16(&source, 0, 0, 0, nullptr);
  frame.fill(uint16_t((8 << 11) | (16 << 5) | 8));
  sdlfe::HudOptions options;
  options.menu_background = path.string();
  sdlfe::FrameShape shape;
  shape.fit = true;
  shape.frame_w = shape.frame_h = 8;
  MenuRecorder recorder;
  const auto present_preserving_float_state = [&](sdlfe::SdlScreen2D &screen) {
      std::fenv_t saved;
      std::fegetenv(&saved);
      std::fesetround(FE_DOWNWARD);
      std::feclearexcept(FE_ALL_EXCEPT);
      std::feraiseexcept(FE_INVALID | FE_DIVBYZERO);
      const int flags = std::fetestexcept(FE_ALL_EXCEPT);
      screen.present_16(frame.data(), 8, 8, 16, true);
      require(std::fegetround() == FE_DOWNWARD && std::fetestexcept(FE_ALL_EXCEPT) == flags,
              "Menu presentation changed guest rounding or exception flags");
      std::fesetenv(&saved);
  };
  {
    sdlfe::SdlScreen2D screen(&recorder, options, nullptr, &shape);
    require(recorder.images.size() == 1 && recorder.images[0].size() == 256,
            "HD menu image was not uploaded once during screen construction");
    present_preserving_float_state(screen);
    require(recorder.images.size() == 4 && recorder.updates == 0 && recorder.draws.size() == 4,
            "GPU menu did not upload three frame-sized maps and draw four passes");
    require(recorder.shape == &shape && recorder.x == 3 && recorder.y == 4 &&
                recorder.w == 5 && recorder.h == 6,
            "Menu presentation did not restore the world shape and viewport");
    for (size_t index = 1; index < recorder.images.size(); ++index)
      require(recorder.images[index].size() == 64, "GPU menu allocated an output-sized map");
    require(recorder.draws[0].state.filter == platform::TextureFilter::kLinear &&
                recorder.draws[0].state.address_u == 1 &&
                recorder.draws[1].state.filter == platform::TextureFilter::kNearest &&
                recorder.draws[1].state.multiply && recorder.draws[2].state.additive &&
                recorder.draws[3].state.blend,
            "GPU menu lost repeat sampling, exact map sampling or blend order");
    screen.present_16(frame.data(), 8, 8, 16, true);
    require(recorder.images.size() == 4 && recorder.updates == 0,
            "Unchanged GPU menu uploaded textures on a cache hit");
    const auto draws_before_invalid_stride = recorder.draws.size();
    screen.present_16(frame.data(), 8, 8, 15, true);
    require(recorder.draws.size() == draws_before_invalid_stride,
            "Menu read an invalid native stride instead of rejecting it without throwing");
    frame[0] = 0xf81f;
    present_preserving_float_state(screen);
    require(recorder.images.size() == 4 && recorder.updates == 3,
            "Changed GPU menu failed to update its maps or uploaded the immutable HD image");
    const auto before_fallback = recorder.draws.size();
    frame.fill(uint16_t((14 << 11) | (29 << 5) | 14));
    screen.present_16(frame.data(), 8, 8, 16, true);
    require(recorder.draws.size() == before_fallback + 1 && recorder.images.size() == 5,
            "Unsupported GPU gain did not select CPU composition");
  }
  require(recorder.released.size() == recorder.images.size(), "Menu screen leaked GPU resources");
  MenuRecorder cpu;
  options.menu_background_renderer = "cpu";
  {
    sdlfe::SdlScreen2D screen(&cpu, options);
    require(cpu.images.empty(), "Explicit CPU mode uploaded an unused HD texture");
    screen.present_16(frame.data(), 8, 8, 16, true);
    require(cpu.images.size() == 1 && cpu.draws.size() == 1,
            "Explicit CPU mode did not retain the composed-texture path");
  }
  {
    // The Vulkan renderer allocates a stored texture only at flush; the CPU compositor now forces
    // that allocation inside its fallback scope. A deferred failure there must select the native
    // frame, not escape present_16, and must not leave a half-made texture behind.
    MenuRecorder deferred;
    {
      sdlfe::SdlScreen2D screen(&deferred, options);
      deferred.throw_next_preflight = true;
      present_preserving_float_state(screen);
      require(deferred.preflight_attempts == 1,
              "CPU compositor did not preflight its composed texture");
      require(deferred.draws.size() == 1,
              "A deferred CPU-compositor allocation failure did not present the native frame");
    }
    require(deferred.released.size() == deferred.images.size(),
            "A deferred CPU-compositor failure leaked its texture");
  }
  options.menu_background_renderer = "gpu";
  frame.fill(uint16_t((8 << 11) | (16 << 5) | 8));
  for (bool fail_hd_image : {true, false}) {
    MenuRecorder unavailable;
    unavailable.fail_next_texture = fail_hd_image;
    {
      sdlfe::SdlScreen2D screen(&unavailable, options);
      unavailable.fail_next_texture = !fail_hd_image;
      screen.present_16(frame.data(), 8, 8, 16, true);
      require(unavailable.draws.size() == 1,
              "Unavailable GPU menu resources did not select CPU composition");
      const auto attempts = unavailable.creation_attempts;
      screen.present_16(frame.data(), 8, 8, 16, true);
      require(unavailable.creation_attempts == attempts && unavailable.updates == 0,
              "Unavailable GPU menu retried allocation or reuploaded an unchanged CPU fallback");
    }
    require(unavailable.released.size() == unavailable.images.size(),
            "Unavailable GPU menu leaked partial texture resources");
  }
  for (int failure_kind : {0, 1, 2, 3}) {
      MenuRecorder throwing;
      throwing.throw_next_texture = failure_kind == 0;
      if (failure_kind == 3)
          throwing.dimension_limit = 12;
      {
          sdlfe::SdlScreen2D screen(&throwing, options);
          throwing.throw_next_texture = failure_kind == 1;
          throwing.throw_next_preflight = failure_kind == 2;
          present_preserving_float_state(screen);
          require(throwing.draws.size() == 1 && throwing.images.back().size() == 64,
                  "Throwing or over-limit menu allocation did not select the CPU compositor");
          const auto attempts = throwing.creation_attempts;
          const auto preflights = throwing.preflight_attempts;
          present_preserving_float_state(screen);
          require(throwing.creation_attempts == attempts &&
                      throwing.preflight_attempts == preflights,
                  "Menu retried a failed allocation instead of retaining the CPU fallback");
      }
      require(throwing.released.size() == throwing.images.size(),
              "Throwing GPU menu allocation leaked partial resources");
  }
  for (const char *mode : {"cpu", "gpu"}) {
      options.menu_background_renderer = mode;
      MenuRecorder invalid;
      {
          sdlfe::SdlScreen2D screen(&invalid, options);
          source.height = 7;
          present_preserving_float_state(screen);
          require(invalid.draws.size() == 1 &&
                      invalid.images.back()[0] == sdlfe::SdlScreen2D::rgba(frame[0], true),
                  "Mismatched menu inputs threw or failed to present the native frame");
          source.height = 8;
          source.alpha = reinterpret_cast<uint8_t *>(frame.data());
          present_preserving_float_state(screen);
          require(invalid.draws.size() == 2 &&
                      invalid.images.back()[0] == sdlfe::SdlScreen2D::rgba(frame[0], true),
                  "Invalid menu input layout failed to retain native presentation");
          source.alpha = nullptr;
      }
  }
  // A narrow fitted menu exposes a surround even without a real SDL window.
  // Unsupported gain forces fallback while the GPU image is still available.
  shape.frame_w = 4;
  frame.fill(uint16_t((14 << 11) | (29 << 5) | 14));
  std::vector<uint32_t> cpu_pixels;
  std::vector<platform::TLVertex> cpu_vertices;
  for (const char *mode : {"cpu", "gpu"}) {
      options.menu_background_renderer = mode;
      MenuRecorder fallback;
      sdlfe::SdlScreen2D screen(&fallback, options, nullptr, &shape);
      present_preserving_float_state(screen);
      require(fallback.draws.size() == 1,
              "GPU fallback painted a first-blit surround absent from requested CPU mode");
      if (cpu_pixels.empty()) {
          cpu_pixels = fallback.images.back();
          cpu_vertices = fallback.draws.front().vertices;
      } else {
          require(cpu_pixels == fallback.images.back(),
                  "GPU fallback changed CPU composition pixels");
          const auto &vertices = fallback.draws.front().vertices;
          for (size_t index = 0; index < vertices.size(); ++index)
              require(vertices[index].sx == cpu_vertices[index].sx &&
                          vertices[index].sy == cpu_vertices[index].sy,
                      "GPU fallback fitted its frame differently from requested CPU mode");
      }
  }
  zrndr::set_menu_background_source(nullptr);
  zrndr::target2d() = {};
}

void observation_checks() {
  Recorder recorder;
  sdlfe::HudOptions options;
  options.mode = "core-critical";
  options.text = false;
  std::array<uint16_t, 48> shadow{}, baseline{};
  shadow.fill(0x1234);
  baseline = shadow;
  uint16_t pixels[] = {0xf800, 0x07e0, 0x001f, 0xffff};
  zimg::Texture image{};
  image.width = image.width_again = 2;
  image.height = 2;
  image.pixels = pixels;
  image.flags = zimg::kTwoBytes;
  auto set_target = [&](auto& target_pixels) {
    zrndr::target2d() = {reinterpret_cast<uint8_t*>(target_pixels.data()), 8, 6, 16, 6};
  };
  // The CPU result with no observer: observation must leave exactly these pixels.
  set_target(baseline);
  zrndr::blit16(&image, 1, 2, 0, nullptr);
  zrndr::blit16(&image, 4, 0, 0, nullptr);
  set_target(shadow);
  sdlfe::GpuHud hud(recorder, options);
  // Counting continues after the first fallback reason, and an observed frame allocates nothing.
  require(hud.begin_observation(shadow.data(), 8, 6, 16, 18), "Observation did not start");
  zrndr::observe_framebuffer_write(shadow.data(), "fixture reason one");
  zrndr::blit16(&image, 1, 2, 0, nullptr);
  zrndr::observe_framebuffer_write(shadow.data(), "fixture reason two");
  zrndr::blit16(&image, 4, 0, 0, nullptr);
  require(!hud.finish(), "Fallback frame reported support");
  require(hud.frame_stats().images == 2 && hud.frame_stats().fallback &&
              hud.frame_stats().shadow_reasons.at("fixture reason one") == 1 &&
              hud.frame_stats().shadow_reasons.at("fixture reason two") == 1,
          "Counts stopped at the first fallback");
  require(recorder.images.empty() && recorder.draws.empty(),
          "Observation allocated textures or submitted draws");
  require(shadow == baseline, "Observation changed the CPU pixels");
  // An empty observed frame is not a fallback.
  require(hud.begin_observation(shadow.data(), 8, 6, 16, 18), "Observation did not start");
  require(!hud.finish() && !hud.frame_stats().fallback && hud.frame_stats().images == 0,
          "Empty frame counted as a fallback");
  // A target that already owns the draw observer is skipped instead of throwing.
  hud.begin(shadow.data(), 8, 6, 16, 18);
  require(!hud.begin_observation(shadow.data(), 8, 6, 16, 18),
          "Observation started while another target owned the draw observer");
  hud.cancel();
  require(!hud.begin_observation(nullptr, 8, 6, 16, 18) && !zrndr::draw_observer(),
          "Observation with an invalid target did not skip quietly");
  // Only the blit's crop is checked: an unkeyed magenta pixel outside it is no fallback.
  uint16_t erase_outside[] = {0xf81f, 0x07e0, 0x001f, 0xffff};
  zimg::Texture cropped = image;
  cropped.pixels = erase_outside;
  zrndr::BlitRect crop{1, 0, 2, 2};
  require(hud.begin_observation(shadow.data(), 8, 6, 16, 18), "Observation did not start");
  zrndr::blit16(&cropped, 1, 2, 0, &crop);
  require(hud.finish() && !hud.frame_stats().fallback, "Pixels outside the crop caused a fallback");
  require(hud.begin_observation(shadow.data(), 8, 6, 16, 18), "Observation did not start");
  zrndr::blit16(&cropped, 1, 2, 0, nullptr);
  require(!hud.finish() && hud.frame_stats().shadow_reasons.count("unkeyed layer erase") == 1,
          "Visible unkeyed magenta did not fall back");
  // Alpha 0 over magenta is transparent, not an erase.
  uint8_t clear_alpha[] = {0, 255, 255, 255};
  zimg::Texture alpha_image = cropped;
  alpha_image.alpha = clear_alpha;
  require(hud.begin_observation(shadow.data(), 8, 6, 16, 18), "Observation did not start");
  zrndr::blit16(&alpha_image, 1, 2, 0, nullptr);
  require(hud.finish() && !hud.frame_stats().fallback, "Transparent magenta caused a fallback");
  // Palette: an index past the palette inside the crop falls back; one outside it does not.
  uint8_t indices[] = {0, 9, 1, 1};
  uint16_t palette[] = {0xf800, 0x07e0};
  zimg::Texture indexed{};
  indexed.width = indexed.width_again = 2;
  indexed.height = 2;
  indexed.pixels = indices;
  indexed.palette = palette;
  indexed.palette_count = 2;
  zrndr::BlitRect first_column{0, 0, 1, 2};
  require(hud.begin_observation(shadow.data(), 8, 6, 16, 18), "Observation did not start");
  zrndr::blit16(&indexed, 1, 2, 0, &first_column);
  require(hud.finish() && !hud.frame_stats().fallback, "Bad palette index outside the crop fell back");
  require(hud.begin_observation(shadow.data(), 8, 6, 16, 18), "Observation did not start");
  zrndr::blit16(&indexed, 1, 2, 0, nullptr);
  require(!hud.finish() && hud.frame_stats().shadow_reasons.count("invalid image palette") == 1,
          "Bad palette index inside the crop did not fall back");
  zrndr::target2d() = {};
}
void text_checks(const char* fonts) {
  const auto saved = zutl::mounts();
  zutl::mounts() = {};
  zutl::mount(fonts);
  zvid::set_pixel_format(5, 6, 5);
  sdlfe::SdlTwodHost host(nullptr, nullptr, nullptr);
  host.enable_hud_text(true);
  auto* image = host.image_new(64, 32);
  image->flags |= zimg::kAlpha;
  std::fill_n(static_cast<uint16_t*>(image->pixels), 64 * 32, uint16_t(0xf81f));
  const auto font = host.CreateFontA(-16, 0, 0, 0, 400, 0, 0, 0, 0, 4, 0, 1, 0, "Arial");
  require(font != 0, "Text fixture font is unavailable");
  const auto dc = host.image_dc(image);
  host.SelectObject(dc, font);
  host.SetTextColor(dc, 0x0000ff);
  host.SetBkMode(dc, 1);
  ztwod::Rect clip{4, 4, 40, 24};
  host.DrawTextA(dc, "MW3", -1, &clip, 0);
  const auto enhanced = host.hud_text_image(image, 3, 0xf81f);
  require(enhanced && enhanced->width == 192 && enhanced->height == 96,
          "HUD text was not rasterized at output density");
  unsigned antialiased = 0, opaque = 0;
  for (unsigned y = 0; y < 96; ++y)
    for (unsigned x = 0; x < 192; ++x) {
      const auto pixel = enhanced->pixels[y * 192 + x];
      if (x < 12 || x >= 120 || y < 12 || y >= 72)
        require(pixel == 0, "Enhanced text escaped native clip");
      const unsigned alpha = pixel >> 24;
      antialiased += alpha > 0 && alpha < 255;
      opaque += alpha == 255;
      require((pixel & 0xffff00) == 0 && (pixel & 255) == alpha,
              "Enhanced glyph lost premultiplied red");
    }
  require(antialiased > 0 && opaque > 0, "Enhanced glyph lacks antialiased coverage");
  host.DrawTextA(dc, "MW3", -1, &clip, 0);
  require(host.hud_text_image(image, 3, 0xf81f) == enhanced,
          "Unchanged native text accumulated recipes");
  {
    const auto previous_target = zrndr::target2d();
    Recorder recorder;
    sdlfe::HudOptions options;
    options.mode = "core-critical";
    std::array<uint16_t, 64 * 32> shadow{};
    zrndr::target2d() = {reinterpret_cast<uint8_t*>(shadow.data()), 64, 32, 64 * 2, 6};
    sdlfe::GpuHud hud(recorder, options);
    // Text is enabled, yet observation must not rasterise it and must keep the guest's FP state.
    const int previous_round = std::fegetround();
    std::fesetround(FE_DOWNWARD);
    std::feclearexcept(FE_ALL_EXCEPT);
    std::feraiseexcept(FE_INVALID);
    const int previous_flags = std::fetestexcept(FE_ALL_EXCEPT);
    require(hud.begin_observation(shadow.data(), 64, 32, 64 * 2, 96), "Observation did not start");
    zrndr::blit16(image, 0, 0, 0xf81f, nullptr);
    require(hud.finish(), "Recorded menu text did not pass observation");
    require(std::fegetround() == FE_DOWNWARD && std::fetestexcept(FE_ALL_EXCEPT) == previous_flags,
            "Menu text observation changed the guest FP state");
    std::feclearexcept(FE_ALL_EXCEPT);
    std::fesetround(previous_round);
    require(hud.frame_stats().images == 1 && hud.frame_stats().text_hits == 0,
            "Observation counted or rasterised menu text");
    require(recorder.draws.empty() && recorder.images.empty() && !zrndr::draw_observer(),
            "Menu text observation submitted GPU draws, allocated textures or left a stale observer");
    zrndr::target2d() = previous_target;
  }
  host.SetTextColor(dc, 0xff0000);
  host.DrawTextA(dc, "MW3", -1, &clip, 0);
  host.SetTextColor(dc, 0x0000ff);
  host.DrawTextA(dc, "MW3", -1, &clip, 0);
  const auto repainted = host.hud_text_image(image, 3, 0xf81f);
  require(
      repainted && std::count(repainted->pixels.begin(), repainted->pixels.end(), 0xff0000ff) > 10,
      "Intervening text paint changed recipe order");
  static_cast<uint16_t*>(image->pixels)[0] = 0;
  require(!host.hud_text_image(image, 3, 0xf81f),
          "Stale text replaced externally changed native pixels");
  host.DeleteDC(dc);
  host.DeleteObject(font);
  host.texture_free(image);
  zutl::mounts() = saved;
}
}  // namespace
int main(int argc, char** argv) {
  const auto directory =
      std::filesystem::temp_directory_path() /
      std::filesystem::path("mw3-hud-check-" + std::to_string(SDL_GetPerformanceCounter()));
  try {
    artwork_checks(directory);
    drawing_checks();
    menu_background_checks(directory);
    observation_checks();
    if (argc == 3 && std::string(argv[1]) == "--fonts")
      text_checks(argv[2]);
    else
      require(argc == 1, "usage: mw3hud_checks [--fonts DIR]");
    std::filesystem::remove_all(directory);
    std::puts(
        "HUD payload, identity, ordering, ownership, clipping, native shadow and FP checks passed");
    return 0;
  } catch (const std::exception& error) {
    std::filesystem::remove_all(directory);
    std::fprintf(stderr, "HUD check failed: %s\n", error.what());
    return 1;
  }
}
