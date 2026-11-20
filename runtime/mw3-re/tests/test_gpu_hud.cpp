#include <algorithm>
#include <array>
#include <cfenv>
#include <cmath>
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
#include "frontend/sdl/sdl_input.h"
#include "frontend/sdl/sdl_render3d.h"
#include "frontend/sdl/sdl_platform.h"
#include "frontend/sdl/sdl_twod_host.h"
#include "gamez/zimage/zimg_library.h"
#include "gamez/zrender/zrndr_blur.h"
#include "gamez/zrender/zrndr_ripple.h"
#include "gamez/zrender/zrndr_span.h"
#include "gamez/zrender/zrndr_tint.h"
#include "gamez/ztwod/twod.h"
#include "gamez/zutil/zutl_path.h"
#include "gamez/zvideo/zvid_ddd3d.h"
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
  struct ImageRecord {
    int width;
    int height;
    std::vector<uint32_t> pixels;
  };
  std::vector<Draw> draws;
  std::vector<std::vector<uint32_t>> images;
  std::vector<ImageRecord> image_records;
  std::vector<int> released;
  bool flushed = false;
  bool allocation_fails = false;
  bool preflight_throws = false;
  int x = 3, y = 4, w = 5, h = 6;
  bool ok() const override { return true; }
  void capture_next(const char*) override {}
  void set_shape(const sdlfe::FrameShape*) override {}
  void flush() override { flushed = true; }
  void prepare_canvas_textures(const std::vector<int32_t>&) override {
    if (preflight_throws) throw std::runtime_error("Synthetic HUD preflight failure");
  }
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
    image_records.push_back({width, height, copy});
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
  // With an alpha plane the same bad index still falls back, but the CPU blit must still draw:
  // the native shadow is the fallback's output, so skipping it would drop the image entirely.
  uint8_t opaque_alpha[] = {255, 255, 255, 255};
  zimg::Texture indexed_alpha = indexed;
  indexed_alpha.alpha = opaque_alpha;
  shadow[2 * 8 + 1] = 0;
  shadow[3 * 8 + 2] = 0;
  require(hud.begin_observation(shadow.data(), 8, 6, 16, 18), "Observation did not start");
  zrndr::blit16(&indexed_alpha, 1, 2, 0, nullptr);
  require(!hud.finish() && hud.frame_stats().shadow_reasons.count("invalid image palette") == 1,
          "Bad palette index under an alpha plane did not fall back");
  require(shadow[2 * 8 + 1] == 0xf800 && shadow[3 * 8 + 2] == 0x07e0,
          "Bad palette index under an alpha plane skipped the CPU blit");
  zrndr::target2d() = {};
}

uint32_t expand_565(uint16_t colour) {
  return ((colour >> 11) * 255 / 31) | (((colour >> 5) & 63) * 255 / 63) << 8 |
         ((colour & 31) * 255 / 31) << 16 | 0xff000000u;
}

void replay_recorder_draws(const Recorder& recorder, int width, int height,
                           std::vector<uint32_t>& canvas) {
  require(int(canvas.size()) == width * height, "Replay canvas size mismatch");
  for (const auto& draw : recorder.draws) {
    if (draw.primitive == platform::Primitive::kFan) {
      require(draw.vertices.size() == 4, "Expected 4-vertex fan quad in replay");
      const int x0 = int(std::lround(draw.vertices[0].sx));
      const int y0 = int(std::lround(draw.vertices[0].sy));
      const int x1 = int(std::lround(draw.vertices[2].sx));
      const int y1 = int(std::lround(draw.vertices[2].sy));
      const float u0 = draw.vertices[0].tu;
      const float v0 = draw.vertices[0].tv;
      const float u1 = draw.vertices[2].tu;
      const float v1 = draw.vertices[2].tv;
      for (int y = std::max(0, y0); y < std::min(height, y1); ++y) {
        for (int x = std::max(0, x0); x < std::min(width, x1); ++x) {
          uint32_t src_rgba = 0;
          if (draw.state.texture >= 0) {
            const auto& img = recorder.image_records.at(size_t(draw.state.texture));
            float u = u0 + (float(x - x0) + 0.5f) / float(x1 - x0) * (u1 - u0);
            float v = v0 + (float(y - y0) + 0.5f) / float(y1 - y0) * (v1 - v0);
            if (draw.state.address_u == 1) u = u - std::floor(u);
            if (draw.state.address_v == 1) v = v - std::floor(v);
            const int tx = std::clamp(int(u * img.width), 0, img.width - 1);
            const int ty = std::clamp(int(v * img.height), 0, img.height - 1);
            src_rgba = img.pixels[size_t(ty) * img.width + tx];
          } else {
            const uint32_t argb = draw.vertices[0].diffuse;
            src_rgba = (argb & 0xff00ff00u) | ((argb >> 16) & 0xffu) | ((argb & 0xffu) << 16);
          }
          const unsigned alpha = src_rgba >> 24;
          if (alpha == 0) continue;
          if (alpha == 255) {
            canvas[size_t(y) * width + x] = src_rgba;
          } else {
            const uint32_t dst_rgba = canvas[size_t(y) * width + x];
            uint32_t out = 0xff000000u;
            for (int shift = 0; shift < 24; shift += 8) {
              const unsigned s_ch = (src_rgba >> shift) & 0xffu;
              const unsigned d_ch = (dst_rgba >> shift) & 0xffu;
              const unsigned blended =
                  std::min(255u, s_ch + (d_ch * (255u - alpha) + 127u) / 255u);
              out |= blended << shift;
            }
            canvas[size_t(y) * width + x] = out;
          }
        }
      }
    } else if (draw.primitive == platform::Primitive::kStrip) {
      require(draw.state.texture < 0, "Strip replay requires untextured pixel geometry");
      // Pixel batches join quads with degenerate triangles. Rasterize the strip itself so
      // connectors cannot be mistaken for pixels, including when one pixel covers 3x3 samples.
      for (size_t index = 2; index < draw.vertices.size(); ++index) {
        const auto& first = draw.vertices[index - 2];
        const auto& second = draw.vertices[index - 1];
        const auto& third = draw.vertices[index];
        const auto edge = [](const platform::TLVertex& start, const platform::TLVertex& end,
                             float x, float y) {
          return (end.sx - start.sx) * (y - start.sy) -
                 (end.sy - start.sy) * (x - start.sx);
        };
        const float area = edge(first, second, third.sx, third.sy);
        if (area == 0.f) continue;
        const int left =
            std::max(0, int(std::floor(std::min({first.sx, second.sx, third.sx}))));
        const int top =
            std::max(0, int(std::floor(std::min({first.sy, second.sy, third.sy}))));
        const int right =
            std::min(width, int(std::ceil(std::max({first.sx, second.sx, third.sx}))));
        const int bottom =
            std::min(height, int(std::ceil(std::max({first.sy, second.sy, third.sy}))));
        const uint32_t argb = first.diffuse;
        const uint32_t rgba =
            (argb & 0xff00ff00u) | ((argb >> 16) & 0xffu) | ((argb & 0xffu) << 16);
        require((rgba >> 24) == 255, "Strip replay requires opaque pixel geometry");
        for (int y = top; y < bottom; ++y) {
          for (int x = left; x < right; ++x) {
            const float first_edge = edge(first, second, x + .5f, y + .5f);
            const float second_edge = edge(second, third, x + .5f, y + .5f);
            const float third_edge = edge(third, first, x + .5f, y + .5f);
            const bool inside = area > 0.f
                                    ? first_edge >= 0.f && second_edge >= 0.f && third_edge >= 0.f
                                    : first_edge <= 0.f && second_edge <= 0.f && third_edge <= 0.f;
            if (inside) canvas[size_t(y) * width + x] = rgba;
          }
        }
      }
    }
  }
}

class CursorTestHost : public ztwod::Host {
 public:
  zimg::Texture* screen_grab_rect(int32_t, ztwod::Rect* r, zimg::Texture* into) override {
    const zrndr::Target2D& t = zrndr::target2d();
    if (!t.base || !r || !into || !into->pixels) return nullptr;
    ztwod::Rect c = *r;
    if (c.left < 0) c.left = 0;
    if (c.top < 0) c.top = 0;
    if (c.right > int32_t(t.width)) c.right = int32_t(t.width);
    if (c.bottom > int32_t(t.height)) c.bottom = int32_t(t.height);
    if (c.right <= c.left || c.bottom <= c.top) return nullptr;
    const int w = c.right - c.left, h = c.bottom - c.top;
    if (into->width < w || into->height < h) return nullptr;
    for (int y = 0; y < h; ++y) {
      std::memcpy(static_cast<uint16_t*>(into->pixels) + size_t(y) * into->width,
                  t.base + size_t(c.top + y) * t.pitch + size_t(c.left) * 2, size_t(w) * 2);
    }
    *r = c;
    return into;
  }
};

struct LegacyObserver final : zrndr::DrawObserver {
  unsigned fallbacks = 0;
  std::string last_reason;
  void image(const zimg::Texture*, int32_t, int32_t, uint16_t, const zrndr::BlitRect*) override {}
  void pixel(const uint16_t*, uint16_t) override {}
  void span(const uint16_t*, uint32_t, uint16_t) override {}
  void framebuffer_write(const void*, const char* operation) override {
    ++fallbacks;
    last_reason = operation ? operation : "";
  }
};

struct ScopedStageBGlobals {
  zrndr::Target2D saved_target = zrndr::target2d();
  zrndr::FinishTarget saved_finish_target = zrndr::finish_target();
  zrndr::TintState saved_tint = zrndr::tint_state();
  zrndr::FinishMachine saved_machine = zrndr::finish_machine();
  zrndr::LayerCover saved_cover = zrndr::layer_cover();
  ztwod::Host* saved_host = &ztwod::host();
  std::fenv_t saved_fenv{};
  ScopedStageBGlobals() { std::fegetenv(&saved_fenv); }
  ~ScopedStageBGlobals() {
    zrndr::set_draw_observer(nullptr);
    zrndr::target2d() = saved_target;
    zrndr::finish_target() = saved_finish_target;
    zrndr::tint_state() = saved_tint;
    zrndr::finish_machine() = saved_machine;
    zrndr::layer_cover() = saved_cover;
    ztwod::set_host(saved_host);
    zvid::set_pixel_format(5, 6, 5);
    std::fesetenv(&saved_fenv);
  }
};

void stage_b_primitive_checks(const std::filesystem::path& directory) {
  ScopedStageBGlobals globals_guard;
  require(zrndr::kCursorUsesMenuLogicalTransform,
          "Cursor logical menu transform policy constant changed");

  // 0. DrawObserver default resolved_region delegates to framebuffer_write for legacy observers.
  {
    LegacyObserver legacy;
    uint16_t dummy = 0;
    legacy.resolved_region(&dummy, 1, 1, 2, "legacy delegate check");
    require(legacy.fallbacks == 1 && legacy.last_reason == "legacy delegate check",
            "DrawObserver::resolved_region did not delegate to framebuffer_write by default");
  }

  // 0b. ScopedMuteDrawObserver: nested mutes restore the original observer, and an observer
  //     installed inside a muted scope survives the scope's exit instead of being replaced by
  //     the stale saved pointer.
  {
    LegacyObserver original, installed_inside;
    zrndr::set_draw_observer(&original);
    {
      zrndr::ScopedMuteDrawObserver outer;
      {
        zrndr::ScopedMuteDrawObserver inner;
        require(zrndr::draw_observer() == nullptr, "Nested mute did not clear the observer");
      }
      require(zrndr::draw_observer() == nullptr, "Inner mute exit unmuted the outer scope");
    }
    require(zrndr::draw_observer() == &original, "Nested mutes did not restore the observer");
    {
      zrndr::ScopedMuteDrawObserver mute;
      zrndr::set_draw_observer(&installed_inside);
    }
    require(zrndr::draw_observer() == &installed_inside,
            "Observer installed inside a muted scope was overwritten on scope exit");
    zrndr::set_draw_observer(nullptr);
  }

  sdlfe::HudOptions options;
  options.mode = "core-critical";
  options.text = false;

  // 1. Alpha edge values (0,3,4,7,8,251,252,255), green signed down-rounding, source/dest extremes,
  //    palette index vs color key, alpha-over-key precedence, and representative green alpha glow
  //    artwork on a padded-pitch canvas.
  {
    constexpr int width = 10, height = 7, pitch_px = 12, pitch_bytes = 24;
    std::vector<uint16_t> initial(size_t(pitch_px) * height);
    for (int y = 0; y < height; ++y)
      for (int x = 0; x < pitch_px; ++x)
        initial[size_t(y) * pitch_px + x] =
            (x & 1) ? uint16_t(0xffffu) : uint16_t((15u << 11) | (40u << 5) | 20u);
    initial[3] = uint16_t(63u << 5);  // max green dest for signed down-rounding check

    uint16_t alpha_pixels[16] = {
        0xf800, 0x07e0, 0x001f, 0x0000, 0xffff, 0xf81f, 0x07ff, 0xffe0,
        0x1234, 0x5678, 0x9abc, 0xdef0, 0x0000, 0xffff, 0xf800, 0x07e0};
    uint8_t alpha_plane[16] = {0, 3, 4, 7, 8, 128, 251, 252, 255, 0, 4, 251, 252, 3, 8, 255};
    zimg::Texture alpha_img{};
    alpha_img.width = 8;
    alpha_img.height = 2;
    alpha_img.width_again = 8;
    alpha_img.pixels = alpha_pixels;
    alpha_img.alpha = alpha_plane;
    alpha_img.flags = zimg::kAlpha | zimg::kTwoBytes;  // kAlpha must be ignored when alpha != null

    // Keyed palette image: non-magenta palette[0] so unkeyed index 0 is valid; index 2 is keyed.
    uint16_t palette[4] = {0x1234, 0x07e0, 0xf800, 0x001f};
    uint8_t pal_indices[4] = {0, 1, 2, 3};
    zimg::Texture pal_keyed{};
    pal_keyed.width = 4;
    pal_keyed.height = 1;
    pal_keyed.width_again = 4;
    pal_keyed.pixels = pal_indices;
    pal_keyed.palette = palette;
    pal_keyed.palette_count = 4;
    pal_keyed.flags = zimg::kAlpha;  // key is palette index 2 (not color 0xf800)

    // Alpha-over-key palette image: includes opaque magenta (0xf81f) resolved via post-alpha path.
    uint16_t pal_with_magenta[4] = {0xf81f, 0x07e0, 0xf800, 0x001f};
    uint8_t pal_alpha[4] = {3, 4, 251, 255};
    zimg::Texture pal_alpha_img = pal_keyed;
    pal_alpha_img.palette = pal_with_magenta;
    pal_alpha_img.alpha = pal_alpha;  // alpha plane takes precedence over index key

    // Representative menu/lab green glow artwork: drawn as an ordinary alpha-blended Image.
    uint16_t glow_pixels[6] = {0x07e0, 0x07e0, 0x03e0, 0x07e0, 0x05e0, 0x07e0};
    uint8_t glow_alpha[6] = {0, 64, 140, 220, 252, 3};
    zimg::Texture glow_img{};
    glow_img.width = 3;
    glow_img.height = 2;
    glow_img.width_again = 3;
    glow_img.pixels = glow_pixels;
    glow_img.alpha = glow_alpha;
    glow_img.flags = zimg::kTwoBytes;

    zrndr::BlitRect neg_crop{-1, -1, 7, 2};
    auto draw_scene = [&] {
      zrndr::blit16(&alpha_img, 0, 0, 0xf800, nullptr);
      zrndr::blit16(&alpha_img, -2, 1, 0xffff, &neg_crop);
      zrndr::blit16(&pal_keyed, 1, 3, 2, nullptr);
      zrndr::blit16(&pal_alpha_img, 2, 4, 1, nullptr);
      zrndr::blit16(&glow_img, 5, 4, 0, nullptr);
    };

    auto baseline = initial;
    zrndr::target2d() = {reinterpret_cast<uint8_t*>(baseline.data()), width, height, pitch_bytes, 6};
    draw_scene();

    auto shadow = initial;
    Recorder recorder;
    sdlfe::GpuHud hud(recorder, options);
    zrndr::target2d() = {reinterpret_cast<uint8_t*>(shadow.data()), width, height, pitch_bytes, 6};

    std::fesetround(FE_DOWNWARD);
    std::feclearexcept(FE_ALL_EXCEPT);
    std::feraiseexcept(FE_OVERFLOW);
    const int expected_except = std::fetestexcept(FE_ALL_EXCEPT);

    hud.begin(shadow.data(), width, height, pitch_bytes, height * 2);
    draw_scene();
    // Mutate BOTH source and shadow buffer after callbacks but before finish() to prove owned snapshots.
    const auto shadow_after_draws = shadow;
    alpha_pixels[2] = 0x1111;
    glow_pixels[1] = 0xf800;
    std::fill(shadow.begin(), shadow.end(), uint16_t(0x0000));
    require(hud.finish(), "Alpha/palette/glow scene fell back instead of emitting GPU quads");
    require(std::fegetround() == FE_DOWNWARD &&
                std::fetestexcept(FE_ALL_EXCEPT) == expected_except,
            "Stage B alpha/palette/glow draws polluted guest FP state");
    alpha_pixels[2] = 0x001f;
    glow_pixels[1] = 0x07e0;

    require(shadow_after_draws == baseline,
            "Observer changed CPU shadow pixels for alpha/palette/glow blits");
    require(hud.frame_stats().resolved_regions > 0 && !hud.frame_stats().fallback,
            "Alpha blits did not record resolved regions");
    unsigned nearest_draws = 0;
    for (const auto& draw : recorder.draws) {
      if (draw.state.texture >= 0 && draw.state.filter == platform::TextureFilter::kNearest) {
        require(draw.state.sharp && draw.vertices.size() == 4 &&
                    draw.vertices[0].sx >= 0.f && draw.vertices[2].sx <= float(width) &&
                    draw.vertices[0].sy >= 0.f && draw.vertices[2].sy <= float(height),
                "Resolved region quad lacked nearest filter, sharp flag, or logical bounds");
        ++nearest_draws;
      }
    }
    require(nearest_draws == hud.frame_stats().resolved_regions,
            "Emitted nearest-filtered resolved quads did not match resolved_regions count");

    std::vector<uint32_t> replayed(size_t(width) * height);
    for (int y = 0; y < height; ++y)
      for (int x = 0; x < width; ++x)
        replayed[size_t(y) * width + x] = expand_565(initial[size_t(y) * pitch_px + x]);
    replay_recorder_draws(recorder, width, height, replayed);
    for (int y = 0; y < height; ++y) {
      for (int x = 0; x < width; ++x) {
        require(replayed[size_t(y) * width + x] == expand_565(baseline[size_t(y) * pitch_px + x]),
                "Replayed GPU quads differed from expanded CPU RGB565 alpha/palette/glow output");
      }
    }

    // Separately verify that an unkeyed opaque magenta palette entry still triggers "unkeyed layer erase".
    {
      Recorder mag_recorder;
      sdlfe::GpuHud mag_hud(mag_recorder, options);
      auto mag_shadow = initial;
      zrndr::target2d() = {reinterpret_cast<uint8_t*>(mag_shadow.data()), width, height,
                           pitch_bytes, 6};
      zimg::Texture mag_pal = pal_keyed;
      mag_pal.palette = pal_with_magenta;  // index 0 is 0xf81f, key is 2 -> unkeyed magenta
      mag_hud.begin(mag_shadow.data(), width, height, pitch_bytes, height * 2);
      zrndr::blit16(&mag_pal, 1, 3, 2, nullptr);
      require(!mag_hud.finish() &&
                  mag_hud.frame_stats().shadow_reasons.count("unkeyed layer erase") == 1 &&
                  mag_recorder.draws.empty(),
              "Unkeyed magenta palette entry did not trigger unkeyed layer erase fallback");
    }

    // Observation-only mode validates/counts resolved regions without allocating or uploading.
    Recorder obs_recorder;
    sdlfe::GpuHud obs_hud(obs_recorder, options);
    auto obs_shadow = initial;
    zrndr::target2d() = {reinterpret_cast<uint8_t*>(obs_shadow.data()), width, height, pitch_bytes,
                         6};
    require(obs_hud.begin_observation(obs_shadow.data(), width, height, pitch_bytes, height * 2),
            "Observation did not start for alpha scene");
    draw_scene();
    require(obs_hud.finish() && !obs_hud.frame_stats().fallback &&
                obs_hud.frame_stats().resolved_regions == hud.frame_stats().resolved_regions &&
                obs_recorder.images.empty() && obs_recorder.draws.empty() &&
                obs_shadow == baseline,
            "Observation-only alpha scene allocated resources or differed from baseline");
  }

  // 1b. RGB555 alpha threshold (<= 7 skipped, >= 252 opaque) CPU result + GPU fallback check.
  {
    constexpr int width = 8, height = 2, pitch_bytes = 16;
    std::array<uint16_t, 16> initial{};
    initial.fill(0x7fff);
    uint16_t src555[8] = {0x7c00, 0x03e0, 0x001f, 0x7c1f, 0x03ff, 0x7fe0, 0x0000, 0x4210};
    uint8_t alpha555[8] = {0, 3, 4, 7, 8, 128, 251, 252};
    zimg::Texture tex555{};
    tex555.width = tex555.width_again = 8;
    tex555.height = 1;
    tex555.pixels = src555;
    tex555.alpha = alpha555;
    tex555.flags = zimg::kTwoBytes;

    auto baseline = initial;
    zrndr::target2d() = {reinterpret_cast<uint8_t*>(baseline.data()), width, height, pitch_bytes, 5};
    zrndr::blit16(&tex555, 0, 0, 0, nullptr);
    // In RGB555 (format == 5), alphas 0, 3, 4, 7 are all <= 7 and must be skipped; 8..251 blend; 252 is opaque.
    require(baseline[0] == 0x7fff && baseline[1] == 0x7fff && baseline[2] == 0x7fff &&
                baseline[3] == 0x7fff && baseline[4] != 0x7fff && baseline[7] == 0x4210,
            "RGB555 CPU alpha thresholds (<=7 skipped, >=252 opaque) changed");

    auto shadow = initial;
    Recorder recorder;
    sdlfe::GpuHud hud(recorder, options);
    zrndr::target2d() = {reinterpret_cast<uint8_t*>(shadow.data()), width, height, pitch_bytes, 5};
    hud.begin(shadow.data(), width, height, pitch_bytes, height);
    zrndr::blit16(&tex555, 0, 0, 0, nullptr);
    require(!hud.finish() && hud.frame_stats().fallback &&
                hud.frame_stats().shadow_reasons.count("RGB555 target") == 1 &&
                recorder.draws.empty() && shadow == baseline,
            "RGB555 alpha blit did not preserve exact CPU shadow and fall back cleanly");
  }

  // 2. Opaque full 16-bit copies across actual clipped dimensions (odd vs even clipped rows*width,
  //    width 1 odd/even heights, crops, y-clipping, non-full x-offset, and offscreen no-op).
  {
    struct FullCopyCase {
      int target_w;
      int target_h;
      int img_h;
      int dst_x;
      int dst_y;
      bool use_crop;
      zrndr::BlitRect crop;
    };
    const FullCopyCase cases[] = {
        {3, 3, 3, 0, 0, false, {}},               // 3x3 full = 9 px (odd -> copies 8, leaves 9th)
        {3, 3, 1, 0, 1, false, {}},               // 3x1 full at y=1 = 3 px (odd -> copies 2)
        {3, 3, 2, 0, 1, false, {}},               // 3x2 full at y=1 = 6 px (even -> copies all 6)
        {3, 4, 4, 0, 0, true, {0, 1, 3, 4}},      // 3x4 cropped to 3x3 = 9 px (odd -> copies 8)
        {3, 4, 4, 0, -2, false, {}},              // 3x4 clipped at y=-2 -> 3x2 = 6 px (even -> copies 6)
        {3, 4, 4, 0, -1, false, {}},              // 3x4 clipped at y=-1 -> 3x3 = 9 px (odd -> copies 8)
        {1, 3, 3, 0, 0, false, {}},               // 1x3 full = 3 px (odd, width 1 -> copies 2 rows)
        {1, 2, 2, 0, 0, false, {}},               // 1x2 full = 2 px (even, width 1 -> copies 2 rows)
        {1, 1, 1, 0, 0, false, {}},               // 1x1 full = 1 px (odd -> 0 dwords copied, no-op)
        {3, 3, 3, 1, 0, false, {}},               // x=1 clipped to 2x3 (not full -> copies all 6)
        {3, 3, 3, 0, 5, false, {}},               // completely offscreen (no-op)
    };
    for (const auto& tc : cases) {
      const int pitch_bytes = tc.target_w * 2;
      std::vector<uint16_t> initial(size_t(tc.target_w) * tc.target_h, 0x001f);
      std::vector<uint16_t> src_px(size_t(tc.target_w) * tc.img_h);
      for (size_t i = 0; i < src_px.size(); ++i) src_px[i] = uint16_t(0xf800u + i);
      zimg::Texture tex{};
      tex.width = tex.width_again = tc.target_w;
      tex.height = tc.img_h;
      tex.pixels = src_px.data();
      tex.flags = zimg::kTwoBytes;

      auto baseline = initial;
      zrndr::target2d() = {reinterpret_cast<uint8_t*>(baseline.data()), uint32_t(tc.target_w),
                           uint32_t(tc.target_h), uint32_t(pitch_bytes), 6};
      zrndr::blit16(&tex, tc.dst_x, tc.dst_y, 0, tc.use_crop ? &tc.crop : nullptr);

      auto shadow = initial;
      Recorder recorder;
      sdlfe::GpuHud hud(recorder, options);
      zrndr::target2d() = {reinterpret_cast<uint8_t*>(shadow.data()), uint32_t(tc.target_w),
                           uint32_t(tc.target_h), uint32_t(pitch_bytes), 6};
      hud.begin(shadow.data(), tc.target_w, tc.target_h, pitch_bytes, tc.target_h);
      zrndr::blit16(&tex, tc.dst_x, tc.dst_y, 0, tc.use_crop ? &tc.crop : nullptr);
      const bool finished = hud.finish();
      const bool any_changed = baseline != initial;
      require(! hud.frame_stats().fallback && finished == any_changed,
              "Full/partial unkeyed blit unexpected fallback or empty-draw status");
      require(shadow == baseline, "Full/partial unkeyed blit shadow differed from baseline");

      std::vector<uint32_t> replayed(initial.size(), expand_565(0x001f));
      replay_recorder_draws(recorder, tc.target_w, tc.target_h, replayed);
      for (size_t i = 0; i < baseline.size(); ++i) {
        require(replayed[i] == expand_565(baseline[i]),
                "Replayed full/partial unkeyed blit mismatched CPU output");
      }
    }
  }

  // The opaque fast path copies contiguous words, including padding, rather
  // than rows. Keep it on the CPU until replay models that original quirk.
  {
    constexpr int width = 3, height = 3, pitch_pixels = 5;
    std::array<uint16_t, pitch_pixels * height> source_pixels{};
    for (size_t i = 0; i < source_pixels.size(); ++i)
      source_pixels[i] = uint16_t(0x2000 + i);
    zimg::Texture source{};
    source.width = width;
    source.width_again = pitch_pixels;
    source.height = height;
    source.pixels = source_pixels.data();
    source.flags = zimg::kTwoBytes;
    std::array<uint16_t, pitch_pixels * height> baseline{}, shadow{};
    zrndr::target2d() = {reinterpret_cast<uint8_t*>(baseline.data()), width, height,
                         pitch_pixels * 2, 6};
    zrndr::blit16(&source, 0, 0, 0, nullptr);
    Recorder recorder;
    sdlfe::GpuHud hud(recorder, options);
    zrndr::target2d() = {reinterpret_cast<uint8_t*>(shadow.data()), width, height,
                         pitch_pixels * 2, 6};
    hud.begin(shadow.data(), width, height, pitch_pixels * 2, height);
    zrndr::blit16(&source, 0, 0, 0, nullptr);
    require(!hud.finish() && shadow == baseline && recorder.draws.empty() &&
                hud.frame_stats().shadow_reasons.count("padded full blit") == 1,
            "Padded opaque fast copy did not preserve CPU output and request fallback");
  }

  // 3. Ripple (interior, clipped + persistent scratch) and tint (MMX tail + scalar pair spill).
  {
    zvid::set_pixel_format(5, 6, 5);
    constexpr int width = 12, height = 10, pitch_bytes = 24;
    std::vector<uint16_t> initial(size_t(width) * height);
    for (size_t i = 0; i < initial.size(); ++i)
      initial[i] = uint16_t(((i * 7 & 31) << 11) | ((i * 11 & 63) << 5) | (i * 3 & 31));

    const int32_t clip_rect[4] = {1, 1, 10, 9};
    const int32_t tint_mmx_rect[4] = {1, 1, 8, 4};     // count = 7 -> MMX tints 4, leaves 3 tail
    const int32_t tint_scalar_rect[4] = {2, 5, 7, 7};  // count = 5 -> scalar tints (5>>1)+1 = 3 pairs = 6 px

    auto run_effects = [&](std::vector<uint16_t>& buf) {
      zrndr::target2d() = {reinterpret_cast<uint8_t*>(buf.data()), width, height, pitch_bytes, 6};
      zrndr::set_finish_target(buf.data(), width, height, pitch_bytes);
      zrndr::ripple_state().scratch.assign(size_t(width) * height, 0x7befu);
      // Interior ripple
      zrndr::ripple(6, 5, 1, 3, 1, 2.0f, 0.5f, nullptr, zrndr::X87::k24);
      // Clipped ripple (reads outside clip preserve persistent scratch values)
      zrndr::ripple(2, 2, 1, 3, 2, 2.0f, 1.0f, clip_rect, zrndr::X87::k24);
      // No-op ripple (inner == outer)
      zrndr::ripple(5, 5, 2, 2, 1, 2.0f, 0.0f, nullptr, zrndr::X87::k24);
      // MMX tint
      zrndr::finish_machine().mmx = true;
      zrndr::finish_machine().format = 6;
      zrndr::tint(0xf800, tint_mmx_rect, 0.5, false);
      zrndr::finish();
      // Scalar tint (spills past count)
      zrndr::finish_machine().mmx = false;
      zrndr::tint(0x07e0, tint_scalar_rect, 0.25, false);
      zrndr::finish();
      zrndr::tint_clear();
      zrndr::finish_machine().mmx = true;
    };

    auto baseline = initial;
    run_effects(baseline);

    auto shadow = initial;
    Recorder recorder;
    sdlfe::GpuHud hud(recorder, options);
    zrndr::target2d() = {reinterpret_cast<uint8_t*>(shadow.data()), width, height, pitch_bytes, 6};
    hud.begin(shadow.data(), width, height, pitch_bytes, height);
    run_effects(shadow);
    require(hud.finish(), "Ripple and tint sequence fell back instead of emitting GPU quads");
    require(shadow == baseline, "Observer changed ripple/tint CPU shadow");

    std::vector<uint32_t> replayed(size_t(width) * height);
    for (size_t i = 0; i < initial.size(); ++i) replayed[i] = expand_565(initial[i]);
    replay_recorder_draws(recorder, width, height, replayed);
    for (size_t i = 0; i < baseline.size(); ++i) {
      require(replayed[i] == expand_565(baseline[i]),
              "Replayed ripple/tint GPU quads differed from expanded CPU RGB565 output");
    }
  }

  // 4. Cursor draw, hotspot/center, screen-edge clipping, save-under grab, move and restore
  //    (including over unkeyed magenta 0xf81f background pixels, at 1x and scaled output height).
  {
    CursorTestHost test_host;
    ztwod::set_host(&test_host);
    constexpr int width = 8, height = 8, pitch_bytes = 16;
    std::vector<uint16_t> initial(size_t(width) * height);
    for (size_t i = 0; i < initial.size(); ++i) initial[i] = uint16_t(0x1000 + i * 17);
    initial[0] = 0xf81f;  // unkeyed magenta in background must not trigger layer erase on restore
    initial[size_t(4) * width + 4] = 0xf81f;

    uint16_t cursor_px[9] = {0,      0xffff, 0,      0xffff, 0xf800,
                             0xffff, 0,      0xffff, 0};
    zimg::Texture cursor_tex{};
    cursor_tex.width = cursor_tex.height = cursor_tex.width_again = 3;
    cursor_tex.pixels = cursor_px;
    cursor_tex.flags = zimg::kAlpha | zimg::kTwoBytes;

    auto run_cursor_sequence = [&](std::vector<uint16_t>& buf, sdlfe::GpuHud* hud,
                                   int output_height) {
      zrndr::target2d() = {reinterpret_cast<uint8_t*>(buf.data()), width, height, pitch_bytes, 6};
      if (hud) hud->begin(buf.data(), width, height, pitch_bytes, output_height);
      ztwod::Cursor cursor(nullptr, 1);
      cursor.center = 1;  // hotspot at center (3/2 = 1, 1)
      cursor.set_cursor_image(&cursor_tex);
      // Frame 1: move to top-left edge (0, 0) -> top-left at (-1, -1), clipped to 2x2
      cursor.set_pos(0, 0);
      cursor.draw();
      // Frame 2: erase at (0, 0), move to interior (4, 4) -> top-left at (3, 3), draw
      cursor.erase();
      cursor.set_pos(4, 4);
      cursor.draw();
      // Frame 3: erase at (4, 4), move completely offscreen (-5, -5), draw & erase (no-op)
      cursor.erase();
      cursor.set_pos(-5, -5);
      cursor.erase();
      if (hud) require(hud->finish(), "Cursor sequence fell back instead of using GPU quads");
    };

    auto baseline = initial;
    run_cursor_sequence(baseline, nullptr, height);
    require(baseline == initial, "Cursor erase did not restore exact initial CPU canvas");

    for (int out_h : {height, height * 3}) {
      auto shadow = initial;
      Recorder recorder;
      sdlfe::GpuHud hud(recorder, options);
      run_cursor_sequence(shadow, &hud, out_h);
      require(shadow == baseline, "Observed cursor sequence changed CPU shadow");
      // Verify emitted cursor draw and restore quad logical coordinates match at 1x and 3x density:
      // Draw 0: clipped cursor draw at (0,0)..(2,2)
      // Draw 1: clipped cursor restore at (0,0)..(2,2) (nearest filter)
      // Draw 2: interior cursor draw at (3,3)..(6,6)
      // Draw 3: interior cursor restore at (3,3)..(6,6) (nearest filter)
      require(recorder.draws.size() == 4, "Cursor sequence emitted unexpected draw count");
      require(recorder.draws[0].vertices[0].sx == 0.f && recorder.draws[0].vertices[0].sy == 0.f &&
                  recorder.draws[0].vertices[2].sx == 2.f && recorder.draws[0].vertices[2].sy == 2.f &&
                  recorder.draws[1].state.filter == platform::TextureFilter::kNearest &&
                  recorder.draws[1].vertices[0].sx == 0.f && recorder.draws[1].vertices[2].sx == 2.f &&
                  recorder.draws[2].vertices[0].sx == 3.f && recorder.draws[2].vertices[0].sy == 3.f &&
                  recorder.draws[2].vertices[2].sx == 6.f && recorder.draws[2].vertices[2].sy == 6.f &&
                  recorder.draws[3].state.filter == platform::TextureFilter::kNearest &&
                  recorder.draws[3].vertices[0].sx == 3.f && recorder.draws[3].vertices[2].sx == 6.f,
              "Cursor draw/restore logical quad coordinates or filter changed across output scales");

      std::vector<uint32_t> replayed(size_t(width) * height);
      for (size_t i = 0; i < initial.size(); ++i) replayed[i] = expand_565(initial[i]);
      replay_recorder_draws(recorder, width, height, replayed);
      for (size_t i = 0; i < baseline.size(); ++i) {
        require(replayed[i] == expand_565(baseline[i]),
                "Replayed cursor draw/restore sequence differed from CPU output");
      }
    }

    // A host that reports a crop wider than the save-under buffer (as if the buffer were sized
    // to a clipped area) must not make grab_at move rows past the end of that buffer: the
    // capture is left exactly as the host packed it.
    {
      struct OversizedCropHost : CursorTestHost {
        zimg::Texture* screen_grab_rect(int32_t, ztwod::Rect* r, zimg::Texture* into) override {
          if (!r || !into || !into->pixels) return nullptr;
          auto* pixels = static_cast<uint16_t*>(into->pixels);
          for (int32_t i = 0; i < into->pixel_count; ++i) pixels[i] = uint16_t(0x4000 + i);
          r->left += 1;
          r->top += 1;
          r->right += 2;  // two columns past the cursor, so past the buffer's row width
          return into;
        }
      } oversized_host;
      ztwod::set_host(&oversized_host);
      auto screen = initial;
      zrndr::target2d() = {reinterpret_cast<uint8_t*>(screen.data()), width, height, pitch_bytes,
                           6};
      ztwod::Cursor cursor(nullptr, 1);
      cursor.set_cursor_image(&cursor_tex);
      cursor.set_pos(4, 4);
      bool capture_left_as_packed = cursor.under != nullptr;
      if (capture_left_as_packed) {
        const auto* pixels = static_cast<const uint16_t*>(cursor.under->pixels);
        for (int32_t i = 0; i < cursor.under->pixel_count; ++i)
          capture_left_as_packed = capture_left_as_packed && pixels[i] == uint16_t(0x4000 + i);
      }
      require(capture_left_as_packed,
              "Cursor grab_at relocated rows for a crop larger than the save-under buffer");
      ztwod::set_host(&test_host);
    }
  }

  // 5. Fallbacks: LayerCover active, RGB555 target, malformed regions, region allocation failure,
  //    region count & byte budget overflow, preflight failure, and bounded reason keys/diagnostics
  //    (<= 32 + "other", including first-use logging in observation mode without polluting lifetime stats).
  {
    constexpr int width = 8, height = 6, pitch_bytes = 16;
    std::array<uint16_t, 48> shadow{};
    shadow.fill(0x2222);

    // LayerCover active with resolved_region -> rejected and falls back.
    {
      Recorder recorder;
      sdlfe::GpuHud hud(recorder, options);
      std::array<uint8_t, 48> cover_a{};
      std::array<uint16_t, 48> cover_c{};
      zrndr::layer_cover() = {cover_a.data(), cover_c.data(), 0xf81f};
      zrndr::target2d() = {reinterpret_cast<uint8_t*>(shadow.data()), width, height, pitch_bytes, 6};
      hud.begin(shadow.data(), width, height, pitch_bytes, height);
      zrndr::observe_resolved_region(shadow.data(), 2, 2, pitch_bytes, "overlay resolved region");
      require(!hud.finish() &&
                  hud.frame_stats().shadow_reasons.count("overlay resolved region") == 1 &&
                  recorder.draws.empty(),
              "Resolved region allowed while LayerCover was active");
      zrndr::layer_cover() = {};
    }

    // Malformed regions (zero dimensions, bad pitch, out-of-bounds) and null/empty operation name.
    {
      Recorder recorder;
      sdlfe::GpuHud hud(recorder, options);
      zrndr::target2d() = {reinterpret_cast<uint8_t*>(shadow.data()), width, height, pitch_bytes, 6};
      hud.begin_observation(shadow.data(), width, height, pitch_bytes, height);
      zrndr::observe_resolved_region(shadow.data(), 0, 2, pitch_bytes, "zero width");
      zrndr::observe_resolved_region(shadow.data(), 2, 0, pitch_bytes, nullptr);
      zrndr::observe_resolved_region(shadow.data(), 2, 2, pitch_bytes + 2, "bad pitch");
      zrndr::observe_resolved_region(shadow.data() + 7, 2, 1, pitch_bytes, "out of bounds");
      zrndr::observe_resolved_region(shadow.data(), 1, 1, pitch_bytes, nullptr);
      require(!hud.finish() && hud.frame_stats().shadow_reasons.count("zero width") == 1 &&
                  hud.frame_stats().shadow_reasons.count("unknown write") == 1 &&
                  hud.frame_stats().shadow_reasons.count("bad pitch") == 1 &&
                  hud.frame_stats().shadow_reasons.count("out of bounds") == 1 &&
                  hud.frame_stats().resolved_regions == 1,
              "Malformed resolved regions did not record fallback reasons");
    }

    // A region starting in row padding (pitch wider than the visible width) must be refused
    // before the unsigned width/height limits are computed, so it can never wrap into a huge
    // accepted size.
    {
      constexpr int padded_pitch_bytes = 20;  // 8 visible pixels + 2 padding pixels per row
      std::array<uint16_t, 60> padded{};
      Recorder recorder;
      sdlfe::GpuHud hud(recorder, options);
      zrndr::target2d() = {reinterpret_cast<uint8_t*>(padded.data()), width, height,
                           padded_pitch_bytes, 6};
      // Observation mode keeps counting every refusal, so both padding starts are checked.
      const bool observing =
          hud.begin_observation(padded.data(), width, height, padded_pitch_bytes, height);
      zrndr::observe_resolved_region(padded.data() + 8, 1, 1, padded_pitch_bytes, "row padding");
      zrndr::observe_resolved_region(padded.data() + 19, 1, 1, padded_pitch_bytes, "row padding");
      const bool observed_drawing = hud.finish();
      const auto& reasons = hud.frame_stats().shadow_reasons;
      const auto padding_reason = reasons.find("row padding");
      const bool both_refused = padding_reason != reasons.end() && padding_reason->second == 2;
      require(observing && !observed_drawing && both_refused &&
                  hud.frame_stats().resolved_regions == 0 && recorder.draws.empty(),
              "Resolved region starting in row padding was not refused");
    }

    // Resolved region texture allocation failure (Recorder::allocation_fails) falls back cleanly
    // without throwing out of blit16 and without leaving partial draws.
    {
      Recorder failing_recorder;
      failing_recorder.allocation_fails = true;
      sdlfe::GpuHud hud(failing_recorder, options);
      auto alpha_shadow = shadow;
      uint16_t src_px[4] = {0xf800, 0x07e0, 0x001f, 0xffff};
      uint8_t src_al[4] = {128, 128, 128, 128};
      zimg::Texture alpha_tex{};
      alpha_tex.width = alpha_tex.width_again = 2;
      alpha_tex.height = 2;
      alpha_tex.pixels = src_px;
      alpha_tex.alpha = src_al;
      alpha_tex.flags = zimg::kTwoBytes;

      auto expected_shadow = shadow;
      zrndr::target2d() = {reinterpret_cast<uint8_t*>(expected_shadow.data()), width, height,
                           pitch_bytes, 6};
      zrndr::blit16(&alpha_tex, 0, 0, 0, nullptr);

      zrndr::target2d() = {reinterpret_cast<uint8_t*>(alpha_shadow.data()), width, height,
                           pitch_bytes, 6};
      hud.begin(alpha_shadow.data(), width, height, pitch_bytes, height);
      zrndr::blit16(&alpha_tex, 0, 0, 0, nullptr);
      require(!hud.finish() && hud.frame_stats().fallback &&
                  hud.frame_stats().shadow_reasons.count("texture allocation failed") == 1 &&
                  failing_recorder.draws.empty() && alpha_shadow == expected_shadow,
              "Resolved region texture allocation failure threw mid-blit or left partial draws");
    }

    // Per-frame resolved region count budget (kMaxFrameResolvedRegions = 4096) and byte budget
    // (kMaxFrameResolvedBytes = 32 MiB) tested via observation without GPU allocations.
    {
      Recorder recorder;
      sdlfe::GpuHud hud(recorder, options);
      zrndr::target2d() = {reinterpret_cast<uint8_t*>(shadow.data()), width, height, pitch_bytes, 6};
      require(hud.begin_observation(shadow.data(), width, height, pitch_bytes, height),
              "Observation did not start for region count budget test");
      for (uint64_t i = 0; i < sdlfe::GpuHud::kMaxFrameResolvedRegions; ++i) {
        zrndr::observe_resolved_region(shadow.data(), 1, 1, pitch_bytes, "alpha blit");
      }
      require(!hud.frame_stats().fallback &&
                  hud.frame_stats().resolved_regions == sdlfe::GpuHud::kMaxFrameResolvedRegions,
              "Resolved region count budget failed before reaching kMaxFrameResolvedRegions");
      zrndr::observe_resolved_region(shadow.data(), 1, 1, pitch_bytes, "alpha blit");
      require(!hud.finish() && hud.frame_stats().fallback &&
                  hud.frame_stats().shadow_reasons.count("resolved region budget exceeded") == 1 &&
                  recorder.images.empty() && recorder.draws.empty(),
              "Exceeding kMaxFrameResolvedRegions did not trigger resolved region budget exceeded");

      // Byte budget: 1024x1024 target (4 MiB per full resolved region); 8 regions = 32 MiB ok, 9th fails.
      constexpr int big_w = 1024, big_h = 1024, big_pitch = 2048;
      uint16_t dummy_base = 0;
      zrndr::target2d() = {reinterpret_cast<uint8_t*>(&dummy_base), big_w, big_h, big_pitch, 6};
      require(hud.begin_observation(&dummy_base, big_w, big_h, big_pitch, big_h),
              "Observation did not start for byte budget test");
      for (int i = 0; i < 8; ++i) {
        zrndr::observe_resolved_region(&dummy_base, big_w, big_h, big_pitch, "alpha blit");
      }
      require(!hud.frame_stats().fallback && hud.frame_stats().resolved_regions == 8,
              "32 MiB resolved region byte budget rejected within-budget regions");
      zrndr::observe_resolved_region(&dummy_base, 1, 1, big_pitch, "alpha blit");
      require(!hud.finish() && hud.frame_stats().fallback &&
                  hud.frame_stats().shadow_reasons.count("resolved region budget exceeded") == 1,
              "Exceeding 32 MiB resolved region byte budget did not fall back");
    }

    // Preflight failure in finish() catches exception and selects fallback before submitting draws.
    {
      Recorder recorder;
      recorder.preflight_throws = true;
      sdlfe::GpuHud hud(recorder, options);
      zrndr::target2d() = {reinterpret_cast<uint8_t*>(shadow.data()), width, height, pitch_bytes, 6};
      hud.begin(shadow.data(), width, height, pitch_bytes, height);
      zrndr::observe_resolved_region(shadow.data(), 2, 2, pitch_bytes, "alpha blit");
      require(!hud.finish() && hud.frame_stats().fallback &&
                  hud.frame_stats().shadow_reasons.count("texture preflight failed") == 1 &&
                  recorder.draws.empty(),
              "Preflight exception in GpuHud::finish escaped or submitted partial draws");
    }

    // Bounded reason keys (<= 32 distinct reasons + "other") and once-per-reason stderr diagnostic
    // across both observation_only and normal HUD frames, without observation polluting lifetime stats.
    {
      Recorder recorder;
      StderrCapture capture(directory / "bounded-reasons.log");
      {
        sdlfe::GpuHud hud(recorder, options);
        zrndr::target2d() = {reinterpret_cast<uint8_t*>(shadow.data()), width, height, pitch_bytes,
                             6};
        // First, observe an unknown reason twice across two observed frames: must log once,
        // and must NOT enter lifetime compatibility counters printed at destructor.
        for (int pass = 0; pass < 2; ++pass) {
          require(hud.begin_observation(shadow.data(), width, height, pitch_bytes, height),
                  "Observation did not start");
          zrndr::observe_framebuffer_write(shadow.data(), "observed_only_reason");
          require(!hud.finish(), "Observed unknown write did not fall back");
        }
        // Now trigger 40 distinct reasons in normal mode: 31 new reasons + "other" (since 1 slot
        // in logged_shadow_reasons_ was used by "observed_only_reason").
        for (int i = 0; i < 40; ++i) {
          hud.begin(shadow.data(), width, height, pitch_bytes, height);
          const std::string reason = "synthetic_reason_" + std::to_string(i);
          zrndr::observe_framebuffer_write(shadow.data(), reason.c_str());
          require(!hud.finish(), "Synthetic reason did not fall back");
        }
        // Repeat reason 0 and an overflow reason to ensure neither prints a second time.
        hud.begin(shadow.data(), width, height, pitch_bytes, height);
        zrndr::observe_framebuffer_write(shadow.data(), "synthetic_reason_0");
        require(!hud.finish(), "Repeated reason 0 did not fall back");

        hud.begin_observation(shadow.data(), width, height, pitch_bytes, height);
        for (int i = 0; i < 40; ++i) {
          const std::string reason = "obs_reason_" + std::to_string(i);
          zrndr::observe_framebuffer_write(shadow.data(), reason.c_str());
        }
        require(!hud.finish() && hud.frame_stats().shadow_reasons.size() == 33 &&
                    hud.frame_stats().shadow_reasons.at("other") == 8,
                "Per-frame shadow_reasons map exceeded 32 keys + other");
      }
      const std::string log_text = capture.text();
      size_t first_use_lines = 0;
      for (size_t pos = 0;
           (pos = log_text.find("GPU HUD: using native shadow composition for ", pos)) !=
           std::string::npos;
           pos += 45) {
        ++first_use_lines;
      }
      require(first_use_lines == 33,
              "First-use fallback diagnostic log was not bounded to 32 reasons + other");
      require(
          log_text.find("GPU HUD: using native shadow composition for observed_only_reason\n") !=
              std::string::npos,
          "Observation mode did not log first-use diagnostic for unknown write");
      require(log_text.find("GPU HUD compatibility: observed_only_reason") == std::string::npos,
              "Observation mode polluted in-mission lifetime compatibility counters");
    }
  }
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

void part1_live_menu_checks(const std::filesystem::path& directory) {
  ScopedStageBGlobals globals_guard;
  CursorTestHost test_host;
  ztwod::set_host(&test_host);
  zvid::set_pixel_format(5, 6, 5);

  class LiveMenuRecorder : public Recorder {
   public:
    unsigned updates = 0;
    unsigned creates = 0;
    unsigned preflights = 0;
    unsigned clears = 0;
    unsigned presents = 0;
    bool fail_next_create = false;
    bool throw_next_preflight = false;
    const sdlfe::FrameShape* current_shape = nullptr;
    void set_shape(const sdlfe::FrameShape* s) override { current_shape = s; }
    int32_t create_texture(int width, int height, const uint8_t* pixels, uint8_t type) override {
      ++creates;
      if (fail_next_create) {
        fail_next_create = false;
        return -1;
      }
      return Recorder::create_texture(width, height, pixels, type);
    }
    void update_texture(int32_t handle, int width, int height, const uint8_t* pixels) override {
      auto& image = images.at(size_t(handle));
      require(image.size() == size_t(width) * height,
              "Live menu updated a texture at the wrong size");
      std::memcpy(image.data(), pixels, image.size() * 4);
      image_records.at(size_t(handle)).pixels = image;
      ++updates;
    }
    void prepare_canvas_textures(const std::vector<int32_t>& textures) override {
      ++preflights;
      require(!textures.empty(), "Live menu preflighted an empty texture list");
      if (throw_next_preflight) {
        throw_next_preflight = false;
        throw std::runtime_error("Synthetic live menu preflight failure");
      }
    }
    void clear(bool, uint8_t, uint8_t, uint8_t) override {
      ++clears;
      draws.clear();
    }
    void present() override { ++presents; }
  };

  struct EnvGuard {
    std::string name;
    std::string old_value;
    bool had_old = false;
    explicit EnvGuard(const char* key) : name(key) {
      if (const char* v = SDL_getenv(key)) {
        had_old = true;
        old_value = v;
      }
    }
    void set(const char* val) {
      if (val)
        SDL_setenv_unsafe(name.c_str(), val, 1);
      else
        SDL_unsetenv_unsafe(name.c_str());
    }
    ~EnvGuard() {
      if (had_old)
        SDL_setenv_unsafe(name.c_str(), old_value.c_str(), 1);
      else
        SDL_unsetenv_unsafe(name.c_str());
    }
  } env_guard("MW3_MENU_GPU");
  env_guard.set(nullptr);

  // 1. Primitive-by-primitive and combined menu CPU-vs-replay equality at 1x and 3x output scales,
  //    including opaque magenta (0xf81f) validity in menu mode and scaled pixel strips.
  {
    constexpr int width = 16, height = 12, pitch_bytes = 32;
    std::vector<uint16_t> bg_pixels(size_t(width) * height);
    for (int y = 0; y < height; ++y)
      for (int x = 0; x < width; ++x)
        bg_pixels[size_t(y) * width + x] =
            uint16_t(((x + 2) << 11) | (((y * 2 + 5) & 63) << 5) | ((x + y) & 31));
    zimg::Texture bg_tex{};
    bg_tex.width = bg_tex.width_again = width;
    bg_tex.height = height;
    bg_tex.pixels = bg_pixels.data();
    bg_tex.flags = zimg::kTwoBytes;

    // Unkeyed image containing opaque magenta 0xf81f (valid in menus, not a layer erase).
    uint16_t unkeyed_px[4] = {0xf81f, 0x07e0, 0x001f, 0xffff};
    zimg::Texture unkeyed_tex{};
    unkeyed_tex.width = unkeyed_tex.width_again = 2;
    unkeyed_tex.height = 2;
    unkeyed_tex.pixels = unkeyed_px;
    unkeyed_tex.flags = zimg::kTwoBytes;

    // Keyed 16-bit image.
    uint16_t keyed_px[4] = {0x0000, 0xf800, 0xffe0, 0x0000};
    zimg::Texture keyed_tex{};
    keyed_tex.width = keyed_tex.width_again = 2;
    keyed_tex.height = 2;
    keyed_tex.pixels = keyed_px;
    keyed_tex.flags = zimg::kAlpha | zimg::kTwoBytes;

    // Palette-keyed image (key is index 1, includes opaque magenta at index 2).
    uint16_t pal_colors[4] = {0x07ff, 0x1234, 0xf81f, 0xf800};
    uint8_t pal_idx[4] = {0, 1, 2, 3};
    zimg::Texture pal_tex{};
    pal_tex.width = pal_tex.width_again = 2;
    pal_tex.height = 2;
    pal_tex.pixels = pal_idx;
    pal_tex.palette = pal_colors;
    pal_tex.palette_count = 4;
    pal_tex.flags = zimg::kAlpha;

    // Alpha-plane image (triggers per-row resolved_region snapshots for 4..251).
    uint16_t alpha_px[6] = {0xf800, 0x07e0, 0x001f, 0xffff, 0xf81f, 0x07ff};
    uint8_t alpha_al[6] = {0, 3, 64, 180, 252, 255};
    zimg::Texture alpha_tex{};
    alpha_tex.width = alpha_tex.width_again = 3;
    alpha_tex.height = 2;
    alpha_tex.pixels = alpha_px;
    alpha_tex.alpha = alpha_al;
    alpha_tex.flags = zimg::kTwoBytes;

    // Cursor image.
    uint16_t cursor_px[9] = {0, 0xffff, 0, 0xffff, 0xf800, 0xffff, 0, 0xffff, 0};
    zimg::Texture cursor_tex{};
    cursor_tex.width = cursor_tex.height = cursor_tex.width_again = 3;
    cursor_tex.pixels = cursor_px;
    cursor_tex.flags = zimg::kAlpha | zimg::kTwoBytes;

    const int32_t tint_rect[4] = {1, 8, 9, 11};

    auto run_primitive_case = [&](int kind, std::vector<uint16_t>& buf) {
      zrndr::target2d() = {reinterpret_cast<uint8_t*>(buf.data()), width, height, pitch_bytes, 6};
      zrndr::set_finish_target(buf.data(), width, height, pitch_bytes);
      // Quadrant background blits covering the 16x12 canvas.
      zrndr::BlitRect q0{0, 0, 8, 6}, q1{8, 0, 16, 6}, q2{0, 6, 8, 12}, q3{8, 6, 16, 12};
      zrndr::blit16(&bg_tex, 0, 0, 0, &q0);
      zrndr::blit16(&bg_tex, 8, 0, 0, &q1);
      zrndr::blit16(&bg_tex, 0, 6, 0, &q2);
      zrndr::blit16(&bg_tex, 8, 6, 0, &q3);

      if (kind == 0 || kind == 6) {
        zrndr::blit16(&unkeyed_tex, 1, 1, 0, nullptr);
        zrndr::blit16(&keyed_tex, 4, 1, 0x0000, nullptr);
        zrndr::blit16(&pal_tex, 7, 1, 1, nullptr);
      }
      if (kind == 1 || kind == 6) {
        zrndr::blit16(&alpha_tex, 10, 1, 0, nullptr);
      }
      if (kind == 2 || kind == 6) {
        zrndr::line16(1, 4, 6, 4, 0xf81f);  // opaque magenta line in menu
        zrndr::line16(2, 5, 5, 7, 0xffff);
      }
      if (kind == 3 || kind == 6) {
        zrndr::span_state().dest = zrndr::target2d().base + 6 * pitch_bytes + 8 * 2;
        zrndr::span_fill16(0xf81f, 4);  // opaque magenta span in menu
        zrndr::span_state().dest = zrndr::target2d().base + 7 * pitch_bytes + 8 * 2;
        zrndr::span_fill16(0x07e0, 5);
      }
      if (kind == 4 || kind == 6) {
        zrndr::ripple_state().scratch.assign(size_t(width) * height, 0x0000u);
        zrndr::ripple(5, 6, 1, 3, 1, 2.0f, 0.5f, nullptr, zrndr::X87::k24);
        zrndr::finish_machine().mmx = true;
        zrndr::finish_machine().format = 6;
        zrndr::tint(0x001f, tint_rect, 0.5, false);
        zrndr::finish();
        zrndr::tint_clear();
      }
      if (kind == 5 || kind == 6) {
        ztwod::Cursor cursor(nullptr, 1);
        cursor.center = 1;
        cursor.set_cursor_image(&cursor_tex);
        cursor.set_pos(3, 3);
        cursor.draw();
        cursor.erase();
        cursor.set_pos(12, 9);
        cursor.draw();
      }
    };

    sdlfe::HudOptions hud_opts;
    hud_opts.mode = "core-critical";
    hud_opts.text = false;

    for (int kind = 0; kind <= 6; ++kind) {
      std::vector<uint16_t> baseline(size_t(width) * height, 0);
      run_primitive_case(kind, baseline);

      for (int scale : {1, 3}) {
        std::vector<uint16_t> shadow(size_t(width) * height, 0);
        LiveMenuRecorder recorder;
        sdlfe::GpuHud hud(recorder, hud_opts);
        require(hud.begin_menu(shadow.data(), width, height, pitch_bytes, height * scale, false),
                "GpuHud::begin_menu failed to start for menu primitive check");
        run_primitive_case(kind, shadow);
        require(shadow == baseline,
                "Live menu recording altered CPU shadow buffer pixels");
        require(hud.seal_menu() && hud.menu_sealed() && !hud.frame_stats().fallback,
                "GpuHud::seal_menu failed or fell back on valid menu primitive fixture");
        require(recorder.draws.empty(),
                "GpuHud::seal_menu submitted draws before present_16 clear");

        const int out_w = width * scale, out_h = height * scale;
        const platform::MenuBackgroundLayerRect dest{0.f, 0.f, float(out_w), float(out_h)};
        require(hud.submit_menu(&dest, true), "GpuHud::submit_menu failed on sealed menu");
        require(!hud.menu_sealed() && !recorder.draws.empty(),
                "GpuHud::submit_menu left menu sealed or emitted no draws");

        std::vector<uint32_t> replayed(size_t(out_w) * out_h, expand_565(0));
        replay_recorder_draws(recorder, out_w, out_h, replayed);
        for (int y = 0; y < out_h; ++y) {
          for (int x = 0; x < out_w; ++x) {
            const uint16_t expected_565 =
                baseline[size_t(y / scale) * width + size_t(x / scale)];
            if (replayed[size_t(y) * out_w + x] != expand_565(expected_565))
              std::fprintf(stderr,
                           "Menu replay: kind=%d scale=%d at %d,%d expected=%08x actual=%08x\n",
                           kind, scale, x, y, expand_565(expected_565),
                           replayed[size_t(y) * out_w + x]);
            require(replayed[size_t(y) * out_w + x] == expand_565(expected_565),
                    "Replayed live menu GPU draws mismatched CPU output at 1x or 3x scale");
          }
        }
      }
    }

    // 2. Idle frame cache stability: two identical menu frames must perform zero creates and
    //    zero updates on the second frame, and budget eviction must never evict current-frame
    //    references.
    {
      LiveMenuRecorder idle_recorder;
      sdlfe::GpuHud hud(idle_recorder, hud_opts);
      std::vector<uint16_t> shadow(size_t(width) * height, 0);

      require(hud.begin_menu(shadow.data(), width, height, pitch_bytes, height, false),
              "Idle check frame 1 failed to begin");
      run_primitive_case(6, shadow);
      require(hud.seal_menu() && hud.submit_menu(nullptr, true),
              "Idle check frame 1 failed to seal or submit");
      const unsigned creates_after_frame_1 = idle_recorder.creates;
      const unsigned updates_after_frame_1 = idle_recorder.updates;
      require(creates_after_frame_1 > 0 && updates_after_frame_1 == 0,
              "Idle check frame 1 did not create initial textures");

      std::fill(shadow.begin(), shadow.end(), uint16_t(0));
      require(hud.begin_menu(shadow.data(), width, height, pitch_bytes, height, false),
              "Idle check frame 2 failed to begin");
      run_primitive_case(6, shadow);
      require(hud.seal_menu() && hud.submit_menu(nullptr, true),
              "Idle check frame 2 failed to seal or submit");
      require(idle_recorder.creates == creates_after_frame_1 &&
                  idle_recorder.updates == updates_after_frame_1 &&
                  idle_recorder.released.empty(),
              "Equal idle menu frame created, updated, or evicted GPU textures");

      // Budget protection: limit cache to 4 resources, then emit 6 distinct resolved regions in
      // one frame. None of the 6 current-frame references may be evicted during that frame.
      LiveMenuRecorder budget_recorder;
      sdlfe::GpuHud budget_hud(budget_recorder, hud_opts);
      budget_hud.set_resource_cache_limits(4, 1024 * 1024);
      zrndr::target2d() = {reinterpret_cast<uint8_t*>(shadow.data()), width, height, pitch_bytes,
                           6};
      require(budget_hud.begin_menu(shadow.data(), width, height, pitch_bytes, height, false),
              "Budget check frame 1 failed to begin");
      for (int i = 0; i < 6; ++i) {
        shadow[size_t(i)] = uint16_t(0x1000 + i * 111);
        zrndr::observe_resolved_region(shadow.data() + i, 1, 1, pitch_bytes, "budget region");
      }
      require(budget_hud.cached_resource_count() == 6 && budget_recorder.released.empty(),
              "Resource cache budget evicted a texture referenced in the current frame");
      require(budget_hud.seal_menu() && budget_hud.submit_menu(nullptr, true),
              "Budget check frame 1 failed to submit");

      // Next frame: emit 1 new distinct region; older unreferenced entries must now be evicted
      // down to the limit of 4.
      require(budget_hud.begin_menu(shadow.data(), width, height, pitch_bytes, height, false),
              "Budget check frame 2 failed to begin");
      require(budget_hud.cached_resource_count() == 4 && budget_recorder.released.size() == 2,
              "Resource cache did not evict prior-frame excess down to budget at frame boundary");
      shadow[0] = uint16_t(0x7777);
      zrndr::observe_resolved_region(shadow.data(), 1, 1, pitch_bytes, "budget region");
      require(budget_hud.cached_resource_count() == 4 && budget_recorder.released.size() == 3,
              "Resource cache did not evict oldest prior-frame entry on new insertion");
      require(budget_hud.seal_menu() && budget_hud.submit_menu(nullptr, true),
              "Budget check frame 2 failed to submit");
    }

    // 3. Full SdlScreen2D live GPU menu lifecycle with HD background quad, skipping original
    //    background blits, bypassing the 3-map Stage C classifier, and verifying fallbacks.
    {
      const auto hd_path = directory / "live-menu-background.rgb";
      std::ofstream file(hd_path, std::ios::binary);
      const uint8_t header[24] = {'M', 'W', 'H', 'D', 'B', 'G', '1', 0, 32, 0, 0, 0,
                                  24,  0,   0,   0,   16,  0,   0,   0, 12, 0, 0, 0};
      std::vector<uint8_t> hd_rgb(32 * 24 * 3);
      for (size_t i = 0; i < 32 * 24; ++i) {
        hd_rgb[i * 3 + 0] = uint8_t((i * 5) & 0xff);
        hd_rgb[i * 3 + 1] = uint8_t((i * 9 + 40) & 0xff);
        hd_rgb[i * 3 + 2] = uint8_t((i * 13 + 80) & 0xff);
      }
      file.write(reinterpret_cast<const char*>(header), sizeof header);
      file.write(reinterpret_cast<const char*>(hd_rgb.data()), hd_rgb.size());
      file.close();

      zrndr::set_menu_background_source(&bg_tex);
      sdlfe::HudOptions screen_opts;
      screen_opts.mode = "core-critical";
      screen_opts.text = false;
      screen_opts.menu_background = hd_path.string();
      sdlfe::FrameShape shape;
      shape.fit = true;
      shape.frame_w = width;
      shape.frame_h = height;

      LiveMenuRecorder screen_recorder;
      sdlfe::SdlScreen2D screen(&screen_recorder, screen_opts, nullptr, &shape);
      require(screen_recorder.creates == 1,
              "SdlScreen2D did not upload HD background texture once at construction");

      std::vector<uint16_t> frame_buf(size_t(width) * height, 0);
      auto draw_full_menu_frame = [&]() {
        screen_recorder.draws.clear();
        zrndr::begin_menu_background_frame();
        std::fill(frame_buf.begin(), frame_buf.end(), uint16_t(0));
        screen.begin_menu_observation(frame_buf.data(), width, height, pitch_bytes);
        run_primitive_case(6, frame_buf);
        screen.finish_menu_observation();
      };
      auto require_current_shadow = [&]() {
        require(screen_recorder.draws.size() == 1,
                "Rejected menu frame did not use one complete shadow texture");
        const int handle = screen_recorder.draws.front().state.texture;
        require(handle >= 0, "Rejected menu frame has no shadow texture");
        const auto& uploaded = screen_recorder.image_records.at(size_t(handle));
        require(uploaded.width == width && uploaded.height == height,
                "Rejected menu frame uploaded the wrong shadow dimensions");
        for (size_t index = 0; index < frame_buf.size(); ++index) {
          const uint32_t pixel = uploaded.pixels[index];
          // The compatibility upload expands channels by bit replication. Recovering 565
          // checks exact shadow contents independently of the GPU path's 8-bit expansion.
          const uint16_t native = uint16_t(((pixel & 255) >> 3) << 11 |
                                            (((pixel >> 8) & 255) >> 2) << 5 |
                                            (((pixel >> 16) & 255) >> 3));
          require((pixel >> 24) == 255 && native == frame_buf[index],
                  "Rejected menu frame uploaded a blank, stale or inferred shadow pixel");
        }
      };

      // Default (MW3_MENU_GPU unset) and invalid values must remain OFF and use legacy Stage C path.
      env_guard.set(nullptr);
      draw_full_menu_frame();
      require(!zrndr::draw_observer() && !shape.menu_layout_active,
              "Unset MW3_MENU_GPU enabled live menu recording or active menu layout by default");
      screen.present_16(frame_buf.data(), width, height, pitch_bytes, true);
      require(screen_recorder.draws.size() == 4 && screen_recorder.draws[1].state.multiply &&
                  screen_recorder.draws[2].state.additive && !shape.menu_layout_active,
              "Unset MW3_MENU_GPU did not keep legacy 4-pass Stage C menu background composition");

      env_guard.set("invalid");
      draw_full_menu_frame();
      require(!zrndr::draw_observer() && !shape.menu_layout_active,
              "Invalid MW3_MENU_GPU enabled live menu recording or active menu layout");

      // Explicitly set MW3_MENU_GPU=1 to enable live GPU menu replay and shared menu layout.
      env_guard.set("1");
      draw_full_menu_frame();
      require(shape.menu_layout_active,
              "MW3_MENU_GPU=1 did not mark shared FrameShape::menu_layout_active during menu frame");
      // finish_menu_observation sealed the command list without drawing before present_16 clear.
      require(screen_recorder.draws.empty(),
              "finish_menu_observation drew before present_16 cleared the frame");
      screen.present_16(frame_buf.data(), width, height, pitch_bytes, true);
      // Draw 0 must be the HD background quad (texture 0, linear filter, repeat address mode),
      // followed by the ordered foreground primitives (> 1 draw total, and NOT the 4-pass
      // multiply/additive classifier maps).
      require(screen_recorder.draws.size() > 4 && screen_recorder.draws[0].state.texture == 0 &&
                  screen_recorder.draws[0].state.filter == platform::TextureFilter::kLinear &&
                  screen_recorder.draws[0].state.address_u == 1 &&
                  !screen_recorder.draws[1].state.multiply &&
                  !screen_recorder.draws[2].state.additive && shape.menu_layout_active,
              "Live GPU menu did not draw HD background quad followed by ordered foreground quads");
      // GameEngine::video_flip also calls this after present through its cleanup scope.
      screen.cancel_menu_observation();
      require(shape.menu_layout_active,
              "Engine flip cleanup changed the input transform of the visible menu");

      const unsigned creates_after_live_1 = screen_recorder.creates;
      const unsigned updates_after_live_1 = screen_recorder.updates;
      draw_full_menu_frame();
      screen.present_16(frame_buf.data(), width, height, pitch_bytes, true);
      require(screen_recorder.creates == creates_after_live_1 &&
                  screen_recorder.updates == updates_after_live_1,
              "Second identical live GPU menu frame created or updated textures");

      // 3a. Escape hatch MW3_MENU_GPU=0 forces legacy path and clears menu_layout_active;
      //     MW3_MENU_GPU=1 re-enables live path.
      env_guard.set("0");
      draw_full_menu_frame();
      require(!zrndr::draw_observer() && !shape.menu_layout_active,
              "MW3_MENU_GPU=0 still attached a live menu draw observer or kept menu_layout_active");
      screen.present_16(frame_buf.data(), width, height, pitch_bytes, true);
      require(!shape.menu_layout_active,
              "MW3_MENU_GPU=0 present_16 enabled menu_layout_active");
      env_guard.set("1");
      draw_full_menu_frame();
      screen.present_16(frame_buf.data(), width, height, pitch_bytes, true);
      require(screen_recorder.draws.size() > 4 && !screen_recorder.draws[1].state.multiply &&
                  shape.menu_layout_active,
              "MW3_MENU_GPU=1 did not use the live GPU menu replay path");

      // 3a'. The live begin path opts each recorded menu frame into HD menu stage D, so text and
      //      sprites are drawn from output-scale sources. GpuHud reports that state through
      //      wants_source_alpha_images(), which is true only while stage D is active.
      screen.begin_menu_observation(frame_buf.data(), width, height, pitch_bytes);
      require(zrndr::draw_observer() && zrndr::draw_observer()->wants_source_alpha_images(),
              "Live GPU menu begin did not opt the frame into HD menu stage D");
      screen.cancel_menu_observation();

      // 3b. Late background blit after a foreground draw is rejected rather than reordered,
      //     falling back to the complete CPU frame (1 draw) while keeping menu_layout_active.
      zrndr::begin_menu_background_frame();
      std::fill(frame_buf.begin(), frame_buf.end(), uint16_t(0));
      screen.begin_menu_observation(frame_buf.data(), width, height, pitch_bytes);
      zrndr::target2d() = {reinterpret_cast<uint8_t*>(frame_buf.data()), width, height, pitch_bytes,
                           6};
      zrndr::blit16(&unkeyed_tex, 1, 1, 0, nullptr);
      zrndr::blit16(&bg_tex, 0, 0, 0, nullptr);  // late background blit after foreground!
      screen.finish_menu_observation();
      screen.present_16(frame_buf.data(), width, height, pitch_bytes, true);
      require(screen_recorder.draws.size() == 1 && shape.menu_layout_active,
              "Late menu background blit after foreground was reordered instead of falling back");
      require_current_shadow();

      // 3c. Partial background blit (does not cover full frame) is rejected and falls back cleanly.
      zrndr::begin_menu_background_frame();
      std::fill(frame_buf.begin(), frame_buf.end(), uint16_t(0));
      screen.begin_menu_observation(frame_buf.data(), width, height, pitch_bytes);
      zrndr::target2d() = {reinterpret_cast<uint8_t*>(frame_buf.data()), width, height, pitch_bytes,
                           6};
      zrndr::BlitRect half_rect{0, 0, width / 2, height};
      zrndr::blit16(&bg_tex, 0, 0, 0, &half_rect);
      zrndr::blit16(&unkeyed_tex, 1, 1, 0, nullptr);
      screen.finish_menu_observation();
      screen.present_16(frame_buf.data(), width, height, pitch_bytes, true);
      require(screen_recorder.draws.size() == 1 && shape.menu_layout_active,
              "Partial menu background blit did not select safe CPU fallback");
      require_current_shadow();

      // 3d. Unknown write mid-frame selects complete current CPU frame fallback before drawing.
      zrndr::begin_menu_background_frame();
      std::fill(frame_buf.begin(), frame_buf.end(), uint16_t(0));
      screen.begin_menu_observation(frame_buf.data(), width, height, pitch_bytes);
      run_primitive_case(0, frame_buf);
      zrndr::observe_framebuffer_write(frame_buf.data(), "unsupported menu effect");
      frame_buf[5 * width + 3] = 0x1234;
      screen.finish_menu_observation();
      screen.present_16(frame_buf.data(), width, height, pitch_bytes, true);
      require(screen_recorder.draws.size() == 1 && shape.menu_layout_active,
              "Unknown menu framebuffer write did not fall back to a single CPU frame draw");
      require_current_shadow();
      const unsigned fallback_creates = screen_recorder.creates;
      const unsigned fallback_updates = screen_recorder.updates;
      zrndr::begin_menu_background_frame();
      std::fill(frame_buf.begin(), frame_buf.end(), uint16_t(0));
      screen.begin_menu_observation(frame_buf.data(), width, height, pitch_bytes);
      run_primitive_case(0, frame_buf);
      zrndr::observe_framebuffer_write(frame_buf.data(), "unsupported menu effect");
      frame_buf[5 * width + 3] = 0x1234;
      screen.finish_menu_observation();
      screen.present_16(frame_buf.data(), width, height, pitch_bytes, true);
      require_current_shadow();
      require(screen_recorder.creates == fallback_creates &&
                  screen_recorder.updates == fallback_updates,
              "Equal idle CPU fallback frame uploaded another texture");

      // 3e. Lifecycle cancellation: begin_overlay_16 preempts an active menu recording without
      //     observer competition and resets menu_layout_active, and --cc-menu-background-renderer
      //     cpu forces CPU composition with menu_layout_active false.
      zrndr::begin_menu_background_frame();
      screen.begin_menu_observation(frame_buf.data(), width, height, pitch_bytes);
      require(zrndr::draw_observer() != nullptr && shape.menu_layout_active,
              "Live menu recording did not attach observer or set menu_layout_active");
      screen.begin_overlay_16(frame_buf.data(), width, height, pitch_bytes);
      require(!shape.menu_layout_active,
              "begin_overlay_16 did not clear menu_layout_active on mission overlay preemption");
      screen.cancel_overlay_16();
      require(zrndr::draw_observer() == nullptr && !shape.menu_layout_active,
              "Overlay preemption left a dangling draw observer or stale menu_layout_active");

      sdlfe::HudOptions cpu_opts = screen_opts;
      cpu_opts.menu_background_renderer = "cpu";
      env_guard.set("1");
      LiveMenuRecorder cpu_recorder;
      sdlfe::SdlScreen2D cpu_screen(&cpu_recorder, cpu_opts, nullptr, &shape);
      zrndr::begin_menu_background_frame();
      cpu_screen.begin_menu_observation(frame_buf.data(), width, height, pitch_bytes);
      require(zrndr::draw_observer() == nullptr && !shape.menu_layout_active,
              "--cc-menu-background-renderer cpu did not disable live GPU menu recording");
      run_primitive_case(0, frame_buf);
      cpu_screen.finish_menu_observation();
      cpu_screen.present_16(frame_buf.data(), width, height, pitch_bytes, true);
      require(cpu_recorder.draws.size() == 1 && !shape.menu_layout_active,
              "--cc-menu-background-renderer cpu did not use single-pass CPU composition");
      env_guard.set(nullptr);
      zrndr::set_menu_background_source(nullptr);
    }
  }

  // 4. Uniform centered 4:3 menu layout (square native pixels anchored at centered 640x480
  //    dialog_origin) and shared SdlInput / SdlZinHost / SdlScreen2D policy across 640x480 and
  //    wide 1147x480 native menu canvases, resizes, fit=false, mission transitions, env=0/unset/cpu,
  //    and unknown-write native fallback.
  {
    struct LayoutCase {
      int frame_w, frame_h;
      int canvas_w, canvas_h;
      int win_w, win_h;
      bool fit;
      float expected_dialog_x, expected_dialog_y, expected_dialog_w, expected_dialog_h;
    };
    const LayoutCase cases[] = {
        {640, 480, 0, 0, 1280, 960, true, 0.f, 0.f, 1280.f, 960.f},
        {640, 480, 0, 0, 1920, 1080, true, 240.f, 0.f, 1440.f, 1080.f},
        {640, 480, 0, 0, 3440, 1440, true, 760.f, 0.f, 1920.f, 1440.f},
        {3440, 1440, 1147, 480, 3440, 1440, true, 760.f, 0.f, 1920.f, 1440.f},
        {3440, 1440, 1147, 480, 1920, 1080, true, 240.f, 0.f, 1440.f, 1080.f},
        {1147, 480, 0, 0, 3440, 1440, true, 760.f, 0.f, 1920.f, 1440.f},
        {3440, 1440, 1147, 480, 3440, 1440, false, 760.f, 0.f, 1920.f, 1440.f},
    };
    for (const auto& lc : cases) {
      sdlfe::FrameShape shape;
      shape.frame_w = lc.frame_w;
      shape.frame_h = lc.frame_h;
      shape.canvas_w = lc.canvas_w;
      shape.canvas_h = lc.canvas_h;
      shape.fit = lc.fit;
      shape.menu_layout_active = true;

      const int client_width = shape.client_w();
      const int client_height = shape.client_h();
      const int dialog_width =
          client_width < sdlfe::kMenuLogicalWidth ? client_width : sdlfe::kMenuLogicalWidth;
      const int dialog_height =
          client_height < sdlfe::kMenuLogicalHeight ? client_height : sdlfe::kMenuLogicalHeight;
      const int dialog_origin_x = (client_width - dialog_width) / 2;
      const int dialog_origin_y = (client_height - dialog_height) / 2;
      const float expected_scale = lc.expected_dialog_w / float(dialog_width);

      const auto menu_fit = sdlfe::menu_fit_rect(float(lc.win_w), float(lc.win_h), shape);
      require(std::fabs(menu_fit.x - (lc.expected_dialog_x - float(dialog_origin_x) * expected_scale)) <
                      1e-4f &&
                  std::fabs(menu_fit.y - (lc.expected_dialog_y - float(dialog_origin_y) * expected_scale)) <
                      1e-4f &&
                  std::fabs(menu_fit.w - float(client_width) * expected_scale) < 1e-4f &&
                  std::fabs(menu_fit.h - float(client_height) * expected_scale) < 1e-4f,
              "menu_fit_rect did not expand full canvas uniformly around centered 4:3 dialog_origin");

      // One native pixel horizontally and vertically must have the exact same output scale.
      const float scale_x = menu_fit.w / float(client_width);
      const float scale_y = menu_fit.h / float(client_height);
      require(std::fabs(scale_x - scale_y) < 1e-5f &&
                  std::fabs(scale_x - expected_scale) < 1e-5f,
              "menu_fit_rect horizontal and vertical native pixel scales were not uniform");

      // Central 640x480 dialog origin and opposite corner map to the expected centered 4:3 window rect.
      float dialog_wx0 = 0.f, dialog_wy0 = 0.f, dialog_wx1 = 0.f, dialog_wy1 = 0.f;
      sdlfe::menu_frame_to_window(float(dialog_origin_x), float(dialog_origin_y), float(lc.win_w),
                                  float(lc.win_h), shape, &dialog_wx0, &dialog_wy0);
      sdlfe::menu_frame_to_window(float(dialog_origin_x + dialog_width),
                                  float(dialog_origin_y + dialog_height), float(lc.win_w),
                                  float(lc.win_h), shape, &dialog_wx1, &dialog_wy1);
      require(std::fabs(dialog_wx0 - lc.expected_dialog_x) < 1e-4f &&
                  std::fabs(dialog_wy0 - lc.expected_dialog_y) < 1e-4f &&
                  std::fabs(dialog_wx1 - (lc.expected_dialog_x + lc.expected_dialog_w)) < 1e-4f &&
                  std::fabs(dialog_wy1 - (lc.expected_dialog_y + lc.expected_dialog_h)) < 1e-4f,
              "Centered 640x480 dialog bounds did not map to centered 4:3 window rectangle");

      int cur_win_w = lc.win_w, cur_win_h = lc.win_h;
      bool in_mission_state = false;
      sdlfe::SdlInput input;
      input.shape = &shape;
      input.window_size = [&](int* w, int* h) {
        *w = cur_win_w;
        *h = cur_win_h;
      };
      input.in_mission = [&]() { return in_mission_state; };
      sdlfe::SdlZinHost zin_host(&input, client_width, client_height);

      int32_t cw = 0, ch = 0;
      zin_host.client_size(&cw, &ch);
      require(cw == client_width && ch == client_height,
              "Menu SdlZinHost changed original game client_size coordinates");

      // Central dialog_origin in canvas maps to top-left of centered 4:3 rect in window.
      int32_t sx = dialog_origin_x, sy = dialog_origin_y;
      zin_host.client_to_screen(&sx, &sy);
      require(sx == int32_t(std::lround(lc.expected_dialog_x)) &&
                  sy == int32_t(std::lround(lc.expected_dialog_y)),
              "Menu client_to_screen did not map dialog_origin to centered 4:3 origin");

      // Points across the entire native canvas (including wide 1147x480 corners that extend past
      // the 4:3 dialog and central dialog points) roundtrip through client_to_screen -> screen_to_client.
      for (int32_t cx :
           {0, dialog_origin_x, client_width / 2, dialog_origin_x + dialog_width - 1, client_width - 1}) {
        for (int32_t cy :
             {0, dialog_origin_y, client_height / 2, dialog_origin_y + dialog_height - 1, client_height - 1}) {
          int32_t wx = cx, wy = cy;
          zin_host.client_to_screen(&wx, &wy);
          if (cx >= dialog_origin_x && cx < dialog_origin_x + dialog_width &&
              cy >= dialog_origin_y && cy < dialog_origin_y + dialog_height) {
            require(wx >= int32_t(lc.expected_dialog_x) &&
                        wx <= int32_t(lc.expected_dialog_x + lc.expected_dialog_w) &&
                        wy >= int32_t(lc.expected_dialog_y) &&
                        wy <= int32_t(lc.expected_dialog_y + lc.expected_dialog_h),
                    "Central 640x480 dialog coordinate mapped outside centered 4:3 window area");
          }
          int32_t rx = wx, ry = wy;
          zin_host.screen_to_client(&rx, &ry);
          require(std::abs(rx - cx) <= 1 && std::abs(ry - cy) <= 1,
                  "Menu client_to_screen / screen_to_client roundtrip drifted by > 1 canvas pixel");
        }
      }

      // Relative mouse motion scale in menu matches uniform 1 / expected_scale (640 / expected_dialog_w).
      const float expected_mickey = float(dialog_width) / lc.expected_dialog_w;
      require(std::fabs(input.motion_scale() - expected_mickey) < 1e-5f,
              "Menu SdlInput::motion_scale did not use uniform 4:3 pixel scale");

      // Dynamic window resize updates menu input mapping immediately.
      cur_win_w = 1920;
      cur_win_h = 1080;
      int32_t resized_x = dialog_origin_x, resized_y = dialog_origin_y;
      zin_host.client_to_screen(&resized_x, &resized_y);
      require(resized_x == 240 && resized_y == 0,
              "Menu input transform did not track window resize to 1920x1080");

      // When menu_layout_active is false (env=0/unset/cpu/diagnostic), SdlInput and SdlZinHost
      // use the raw world shape without applying menu_frame_shape.
      cur_win_w = lc.win_w;
      cur_win_h = lc.win_h;
      shape.menu_layout_active = false;
      if (lc.frame_w == 3440 && lc.frame_h == 1440 && lc.win_w == 3440 && lc.win_h == 1440) {
        int32_t raw_x = dialog_origin_x, raw_y = dialog_origin_y;
        zin_host.client_to_screen(&raw_x, &raw_y);
        const int32_t expected_raw_x =
            lc.fit ? int32_t(std::lround(float(dialog_origin_x) * 3440.f / float(client_width)))
                   : dialog_origin_x * 3440 / client_width;
        require(raw_x == expected_raw_x &&
                    std::fabs(input.motion_scale() - float(client_width) / 3440.f) < 1e-5f,
                "Disabled menu_layout_active still applied 4:3 menu input transform");
      }

      // Switching to in-mission restores the full ultrawide frame even when menu_layout_active is true.
      shape.menu_layout_active = true;
      in_mission_state = true;
      if (lc.frame_w == 3440 && lc.frame_h == 1440 && lc.win_w == 3440 && lc.win_h == 1440 && lc.fit) {
        int32_t mx = 0, my = 0;
        zin_host.client_to_screen(&mx, &my);
        require(mx == 0 && my == 0 &&
                    std::fabs(input.motion_scale() - float(client_width) / 3440.f) < 1e-5f,
                "Menu 4:3 transform leaked into in-mission ultrawide input mapping");
      }
    }

    // 4b. Paired presentation & input agreement on unknown-write native CPU fallback (no HD background
    //     required) when MW3_MENU_GPU=1 vs MW3_MENU_GPU=0/unset, plus destructor cleanup.
    {
      constexpr int canvas_w = 1147, canvas_h = 480, pitch_bytes = canvas_w * 2;
      std::vector<uint16_t> wide_frame(size_t(canvas_w) * canvas_h, uint16_t(0x07e0));
      sdlfe::FrameShape shared_shape;
      shared_shape.frame_w = 3440;
      shared_shape.frame_h = 1440;
      shared_shape.canvas_w = canvas_w;
      shared_shape.canvas_h = canvas_h;
      shared_shape.fit = true;

      sdlfe::SdlInput input;
      input.shape = &shared_shape;
      input.window_size = [](int* w, int* h) {
        *w = 3440;
        *h = 1440;
      };
      input.in_mission = []() { return false; };
      sdlfe::SdlZinHost zin_host(&input, canvas_w, canvas_h);

      sdlfe::HudOptions native_opts;
      native_opts.mode = "core-critical";
      native_opts.text = false;
      LiveMenuRecorder fallback_recorder;
      {
        sdlfe::SdlScreen2D screen(&fallback_recorder, native_opts, nullptr, &shared_shape);

        // With MW3_MENU_GPU=1, force an unknown-write native fallback on a 1147x480 menu canvas.
        // Screen presentation and SdlInput must both stay on the uniform menu transform.
        env_guard.set("1");
        screen.begin_menu_observation(wide_frame.data(), canvas_w, canvas_h, pitch_bytes);
        require(shared_shape.menu_layout_active,
                "begin_menu_observation did not activate shared menu_layout_active");
        zrndr::target2d() = {reinterpret_cast<uint8_t*>(wide_frame.data()), canvas_w, canvas_h,
                             pitch_bytes, 6};
        zrndr::observe_framebuffer_write(wide_frame.data(), "wide menu native fallback");
        screen.finish_menu_observation();
        screen.present_16(wide_frame.data(), canvas_w, canvas_h, pitch_bytes, true);
        require(fallback_recorder.draws.size() == 1 && shared_shape.menu_layout_active,
                "Unknown-write native fallback under MW3_MENU_GPU=1 lost shared menu_layout_active");
        const auto& fallback_quad = fallback_recorder.draws[0].vertices;
        const auto expected_fit =
            sdlfe::menu_fit_rect(float(canvas_w), float(canvas_h), shared_shape, canvas_w, canvas_h);
        require(std::fabs(fallback_quad[0].sx - expected_fit.x) < 1e-3f &&
                    std::fabs(fallback_quad[0].sy - expected_fit.y) < 1e-3f &&
                    std::fabs(fallback_quad[2].sx - (expected_fit.x + expected_fit.w)) < 1e-3f &&
                    std::fabs(fallback_quad[2].sy - (expected_fit.y + expected_fit.h)) < 1e-3f,
                "Native CPU fallback under MW3_MENU_GPU=1 did not draw into the uniform menu canvas rect");
        int32_t dialog_x = (canvas_w - 640) / 2, dialog_y = 0;
        zin_host.client_to_screen(&dialog_x, &dialog_y);
        require(dialog_x == 760 && dialog_y == 0,
                "Input mapping disagreed with uniform menu presentation after native CPU fallback");

        // With MW3_MENU_GPU=0, both presentation and input revert to the legacy world shape.
        env_guard.set("0");
        screen.begin_menu_observation(wide_frame.data(), canvas_w, canvas_h, pitch_bytes);
        require(!shared_shape.menu_layout_active,
                "MW3_MENU_GPU=0 did not clear shared menu_layout_active");
        screen.finish_menu_observation();
        screen.present_16(wide_frame.data(), canvas_w, canvas_h, pitch_bytes, true);
        require(fallback_recorder.draws.size() == 1 && !shared_shape.menu_layout_active,
                "MW3_MENU_GPU=0 native presentation kept menu_layout_active");
        const auto& legacy_quad = fallback_recorder.draws[0].vertices;
        require(legacy_quad[0].sx == 0.f && legacy_quad[0].sy == 0.f &&
                    legacy_quad[2].sx == float(canvas_w) && legacy_quad[2].sy == float(canvas_h),
                "MW3_MENU_GPU=0 native presentation changed legacy full-viewport quad");
        int32_t legacy_x = (canvas_w - 640) / 2, legacy_y = 0;
        zin_host.client_to_screen(&legacy_x, &legacy_y);
        require(legacy_x == int32_t(std::lround(float((canvas_w - 640) / 2) * 3440.f / float(canvas_w))),
                "MW3_MENU_GPU=0 input did not match legacy world-shape mapping");

        // Re-activate before destruction to verify ~SdlScreen2D clears stale menu_layout_active.
        env_guard.set("1");
        screen.begin_menu_observation(wide_frame.data(), canvas_w, canvas_h, pitch_bytes);
        require(shared_shape.menu_layout_active, "Menu layout did not re-activate before destruction");
      }
      require(!shared_shape.menu_layout_active,
              "SdlScreen2D destructor left stale menu_layout_active on shared FrameShape");
      env_guard.set(nullptr);
    }
  }
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
    stage_b_primitive_checks(directory);
    part1_live_menu_checks(directory);
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
