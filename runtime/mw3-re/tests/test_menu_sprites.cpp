// HD menu stage D checks: menu text and sprites as GPU quads at output scale
// (frontend/sdl/menu_sprites.h, gpu_hud_menu_sprites.cpp). Headless: a
// recording renderer stands in for Vulkan and a software replay of its quads
// is compared with what the CPU blit16 writes into the 16-bit canvas.
#include <algorithm>
#include <array>
#include <cfenv>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

#if defined(_WIN32)
#include <io.h>
#else
#include <unistd.h>
#endif

#include <SDL3/SDL.h>

#include "frontend/sdl/gpu_hud.h"
#include "frontend/sdl/menu_sprites.h"
#include "frontend/sdl/sdl_render3d.h"
#include "frontend/sdl/sdl_twod_host.h"
#include "gamez/zimage/zimg_library.h"
#include "gamez/zrender/zrndr_blit.h"
#include "gamez/ztwod/twod_host.h"
#include "gamez/zutil/zutl_path.h"
#include "gamez/zvideo/zvid_format.h"
#include "platform/prepared_hud.h"

namespace {
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
// Captures stderr to a file for the bounded-logging checks, restoring it even
// when an assertion throws.
class StderrCapture {
 public:
  explicit StderrCapture(const std::filesystem::path& path) {
#if defined(_WIN32)
    file_ = _wfopen(path.c_str(), L"w+b");
#else
    file_ = std::fopen(path.c_str(), "w+b");
#endif
    require(file_ != nullptr, "Cannot create the diagnostic capture");
    std::fflush(stderr);
    saved_ = fd_dup(fd_number(stderr));
    if (saved_ < 0 || fd_dup2(fd_number(file_), fd_number(stderr)) < 0) {
      if (saved_ >= 0) fd_close(saved_);
      std::fclose(file_);
      throw std::runtime_error("Cannot redirect diagnostics");
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
    std::fflush(stderr);
    std::rewind(file_);
    std::string result;
    for (int character; (character = std::fgetc(file_)) != EOF;)
      result += static_cast<char>(character);
    return result;
  }

 private:
  std::FILE* file_{};
  int saved_ = -1;
};
size_t occurrences(const std::string& text, const std::string& needle) {
  size_t found = 0;
  for (size_t at = text.find(needle); at != std::string::npos; at = text.find(needle, at + 1))
    ++found;
  return found;
}

// Records draws and texture uploads instead of rendering them.
class Recorder : public sdlfe::FrameRenderer {
 public:
  struct Draw {
    platform::Primitive primitive;
    std::vector<platform::TLVertex> vertices;
    platform::DrawState state;
  };
  struct Upload {
    int width;
    int height;
    std::vector<uint32_t> pixels;
  };
  std::vector<Draw> draws;
  std::vector<Upload> uploads;
  bool allocation_fails = false;
  int x = 0, y = 0, w = 1, h = 1;
  bool ok() const override { return true; }
  void capture_next(const char*) override {}
  void set_shape(const sdlfe::FrameShape*) override {}
  void flush() override {}
  void viewport(int* a, int* b, int* c, int* d) const override {
    *a = x;
    *b = y;
    *c = w;
    *d = h;
  }
  void set_viewport(int a, int b, int c, int d) override {
    x = a;
    y = b;
    w = c;
    h = d;
  }
  int32_t create_texture(int width, int height, const uint8_t* pixels, uint8_t) override {
    if (allocation_fails) return -1;
    Upload upload{width, height, std::vector<uint32_t>(size_t(width) * height)};
    std::memcpy(upload.pixels.data(), pixels, upload.pixels.size() * 4);
    uploads.push_back(std::move(upload));
    return int(uploads.size() - 1);
  }
  void release_texture(int32_t) override {}
  void update_texture(int32_t, int, int, const uint8_t*) override {
    throw std::runtime_error("Menu sprites must not update textures in place");
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

// A text host stand-in: says which images hold text and hands back a fixed
// output-scale raster for them.
class MenuTestHost : public ztwod::Host {
 public:
  const zimg::Texture* text_image = nullptr;
  std::shared_ptr<const platform::HudImage> raster;
  float requested_density = 0;
  bool raster_throws = false;
  std::shared_ptr<const platform::HudImage> hud_text_image(const zimg::Texture* image,
                                                           float density, uint16_t) override {
    if (image != text_image) return {};
    requested_density = density;
    if (raster_throws) throw std::runtime_error("synthetic raster failure");
    return raster;
  }
  bool is_text_image(const zimg::Texture* image) override { return image == text_image; }
};
class ScopedHost {
 public:
  explicit ScopedHost(ztwod::Host* host) : saved_(&ztwod::host()) { ztwod::set_host(host); }
  ~ScopedHost() { ztwod::set_host(saved_); }

 private:
  ztwod::Host* saved_;
};
class ScopedTarget {
 public:
  ScopedTarget() : saved_(zrndr::target2d()) {}
  ~ScopedTarget() { zrndr::target2d() = saved_; }

 private:
  zrndr::Target2D saved_;
};

uint32_t expand_565(uint16_t colour) {
  return ((colour >> 11) * 255 / 31) | (((colour >> 5) & 63) * 255 / 63) << 8 |
         ((colour & 31) * 255 / 31) << 16 | 0xff000000u;
}

// Software replay of the recorded quads at `scale` output pixels per canvas
// pixel: each output pixel centre is mapped into the quad, its UV interpolated
// and the nearest texel composited (premultiplied over), as a GPU would with
// nearest sampling. `canvas` holds the expanded starting colours.
std::vector<uint32_t> replay(const Recorder& recorder, int canvas_width, int canvas_height,
                             int scale, const std::vector<uint16_t>& canvas) {
  const int output_width = canvas_width * scale, output_height = canvas_height * scale;
  std::vector<uint32_t> output(size_t(output_width) * output_height);
  for (int oy = 0; oy < output_height; ++oy)
    for (int ox = 0; ox < output_width; ++ox)
      output[size_t(oy) * output_width + ox] =
          expand_565(canvas[size_t(oy / scale) * canvas_width + ox / scale]);
  for (const auto& draw : recorder.draws) {
    require(draw.primitive == platform::Primitive::kFan && draw.vertices.size() == 4 &&
                draw.state.texture >= 0,
            "Menu sprite was not one textured quad");
    const auto& first = draw.vertices[0];
    const auto& opposite = draw.vertices[2];
    const auto& upload = recorder.uploads.at(size_t(draw.state.texture));
    for (int oy = 0; oy < output_height; ++oy)
      for (int ox = 0; ox < output_width; ++ox) {
        const float cx = (ox + .5f) / scale, cy = (oy + .5f) / scale;
        if (cx < first.sx || cx >= opposite.sx || cy < first.sy || cy >= opposite.sy) continue;
        const float u =
            first.tu + (cx - first.sx) / (opposite.sx - first.sx) * (opposite.tu - first.tu);
        const float v =
            first.tv + (cy - first.sy) / (opposite.sy - first.sy) * (opposite.tv - first.tv);
        const int tx = std::clamp(int(std::floor(u * upload.width)), 0, upload.width - 1);
        const int ty = std::clamp(int(std::floor(v * upload.height)), 0, upload.height - 1);
        const uint32_t texel = upload.pixels[size_t(ty) * upload.width + tx];
        const unsigned alpha = texel >> 24;
        auto& destination = output[size_t(oy) * output_width + ox];
        uint32_t mixed = 0xff000000u;
        for (int shift = 0; shift < 24; shift += 8) {
          const unsigned source_channel = (texel >> shift) & 255;
          const unsigned destination_channel = (destination >> shift) & 255;
          mixed |= std::min(255u, source_channel +
                                      (destination_channel * (255 - alpha) + 127) / 255)
                   << shift;
        }
        destination = mixed;
      }
  }
  return output;
}
// The CPU canvas scaled up by whole pixels: what upscaled presentation shows.
std::vector<uint32_t> upscale(const std::vector<uint16_t>& canvas, int width, int height,
                              int scale) {
  std::vector<uint32_t> output(size_t(width) * scale * height * scale);
  for (int oy = 0; oy < height * scale; ++oy)
    for (int ox = 0; ox < width * scale; ++ox)
      output[size_t(oy) * width * scale + ox] =
          expand_565(canvas[size_t(oy / scale) * width + ox / scale]);
  return output;
}
sdlfe::HudOptions menu_options() {
  sdlfe::HudOptions options;
  options.mode = "core-critical";
  return options;
}
std::vector<uint16_t> starting_canvas(int width, int height) {
  std::vector<uint16_t> canvas(size_t(width) * height);
  for (size_t at = 0; at < canvas.size(); ++at) canvas[at] = uint16_t(0x0841 * (at % 7) + 0x2104);
  return canvas;
}

void policy_checks() {
  require(sdlfe::menu_sprites_allowed_by(nullptr) && sdlfe::menu_sprites_allowed_by("1") &&
              sdlfe::menu_sprites_allowed_by(""),
          "Stage D was off without being turned off");
  for (const char* off : {"0", "off", "OFF", "false", "No"})
    require(!sdlfe::menu_sprites_allowed_by(off), "MW3_HD_MENU_SPRITES did not turn stage D off");
  require(std::string(sdlfe::kMenuSpritesEnvironment) == "MW3_HD_MENU_SPRITES",
          "The documented escape hatch name changed");

  require(sdlfe::menu_presentation_scale(640, 480, 640, 480) == 1, "1x menu scale");
  require(sdlfe::menu_presentation_scale(640, 480, 1920, 1440) == 3, "3x menu scale");
  require(sdlfe::menu_presentation_scale(640, 480, 1920, 1080) == 2.25f,
          "16:9 output must scale the 4:3 menu by its height");
  require(sdlfe::menu_presentation_scale(1147, 480, 1920, 1080) == 2.25f,
          "A wide canvas must scale text with the centred 4:3 menu");
  require(sdlfe::menu_presentation_scale(640, 480, 1280, 1440) == 2,
          "A tall output must scale the 4:3 menu by its width");
  require(sdlfe::menu_presentation_scale(640, 480, 320, 240) == 1,
          "Menu text was rasterised below its native size");
  require(sdlfe::menu_presentation_scale(0, 480, 1920, 1080) == 1, "Invalid sizes must give 1");

  using sdlfe::menu_sprite_alpha;
  require(menu_sprite_alpha(true, 0, false, 0, 0) == 0 &&
              menu_sprite_alpha(true, 3, false, 0, 0) == 0,
          "blit16 skips alphas 0..3");
  require(menu_sprite_alpha(true, 4, false, 0, 0) == 4 &&
              menu_sprite_alpha(true, 251, false, 0, 0) == 251,
          "blit16 blends alphas 4..251");
  require(menu_sprite_alpha(true, 252, false, 0, 0) == 255 &&
              menu_sprite_alpha(true, 255, false, 0, 0) == 255,
          "blit16 writes alphas from 0xfc opaque");
  require(menu_sprite_alpha(false, 0, true, 0x1234, 0x1234) == 0 &&
              menu_sprite_alpha(false, 0, true, 0x1235, 0x1234) == 255,
          "Colour key changed");
  require(menu_sprite_alpha(false, 0, false, 0x1234, 0x1234) == 255,
          "An unkeyed image dropped its key-coloured pixels");
  // The alpha plane wins over the key flag, as in blit16.
  require(menu_sprite_alpha(true, 200, true, 0x1234, 0x1234) == 200,
          "The key was applied to an alpha-plane image");

  using platform::TextureFilter;
  using sdlfe::menu_sprite_filter;
  using sdlfe::MenuSpriteSource;
  require(menu_sprite_filter(MenuSpriteSource::kOutputText, false) == TextureFilter::kNearest &&
              menu_sprite_filter(MenuSpriteSource::kNative, true) == TextureFilter::kNearest &&
              menu_sprite_filter(MenuSpriteSource::kNative, false) == TextureFilter::kLinear &&
              menu_sprite_filter(MenuSpriteSource::kArtwork, false) == TextureFilter::kLinear,
          "Menu sampling policy changed");

  platform::HudImage native;
  native.width = 8;
  native.height = 4;
  using sdlfe::menu_sprite_quad;
  const auto exact = menu_sprite_quad(5, 6, 2, 1, 6, 4, 8, 4, native, TextureFilter::kNearest);
  require(exact.x0 == 5 && exact.y0 == 6 && exact.x1 == 9 && exact.y1 == 9 && exact.u0 == .25f &&
              exact.u1 == .75f && exact.v0 == .25f && exact.v1 == 1,
          "Nearest crop must map exactly onto the source pixels");
  const auto inset = menu_sprite_quad(5, 6, 2, 1, 6, 4, 8, 4, native, TextureFilter::kLinear);
  require(inset.x0 == 5 && inset.x1 == 9 && inset.u0 == .25f + .0625f &&
              inset.u1 == .75f - .0625f && inset.v0 == .25f + .125f && inset.v1 == 1,
          "Linear crop must inset interior edges by half a texel and leave the border");
  platform::HudImage artwork;
  artwork.width = 64;
  artwork.height = 32;
  artwork.u0 = .5f;
  artwork.u1 = 1;
  const auto high = menu_sprite_quad(0, 0, 0, 0, 4, 4, 8, 4, artwork, TextureFilter::kLinear);
  require(high.u0 == .5f && std::fabs(high.u1 - (.75f - .5f / 64)) < 1e-6f && high.v1 == 1,
          "Artwork UVs must follow its own rectangle and texel size");
}

// A keyed 16-bit sprite sheet: two 3x3 frames side by side, key 0xf81f.
struct Sheet {
  std::array<uint16_t, 6 * 3> pixels{0xf800, 0xf81f, 0x07e0, 0x001f, 0xffff, 0x0400,
                                     0xf81f, 0x7bef, 0xf81f, 0x1111, 0x2222, 0x3333,
                                     0x4444, 0xf81f, 0x5555, 0x6666, 0x7777, 0x8888};
  zimg::Texture texture{};
  Sheet() {
    texture.width = texture.width_again = 6;
    texture.height = 3;
    texture.pixels = pixels.data();
    texture.flags = zimg::kTwoBytes | zimg::kAlpha;
  }
};

void placement_checks() {
  constexpr int width = 12, height = 10, pitch = width * 2;
  for (const int scale : {1, 3}) {
    for (const bool text : {true, false}) {
      Sheet sheet;
      MenuTestHost host;
      host.text_image = text ? &sheet.texture : nullptr;  // no raster: native text path
      ScopedHost scoped_host(&host);
      ScopedTarget scoped_target;
      const zrndr::BlitRect frame{0, 0, 3, 3}, partial{2, 0, 5, 3};
      auto paint = [&] {
        zrndr::blit16(&sheet.texture, 4, 2, 0xf81f, &frame);
        zrndr::blit16(&sheet.texture, -1, 7, 0xf81f, &partial);   // clipped left and bottom
        zrndr::blit16(&sheet.texture, 10, -1, 0xf81f, nullptr);   // clipped right and top
      };
      const auto initial = starting_canvas(width, height);
      auto baseline = initial;
      zrndr::target2d() = {reinterpret_cast<uint8_t*>(baseline.data()), width, height, pitch, 6};
      paint();
      auto shadow = initial;
      zrndr::target2d() = {reinterpret_cast<uint8_t*>(shadow.data()), width, height, pitch, 6};
      Recorder recorder;
      sdlfe::GpuHud hud(recorder, menu_options());
      hud.begin(shadow.data(), width, height, pitch, height * scale);
      hud.set_menu_presentation(float(scale));
      require(hud.menu_presentation_active(), "Menu presentation did not start");
      paint();
      require(hud.finish(), "Menu sprites fell back to CPU composition");
      require(shadow == baseline, "Stage D changed the CPU compatibility canvas");
      require(recorder.draws.size() == 3 && recorder.uploads.size() == 1,
              "One sheet must upload once and draw three quads");
      const auto expected_filter =
          text ? platform::TextureFilter::kNearest : platform::TextureFilter::kLinear;
      for (const auto& draw : recorder.draws)
        require(draw.state.filter == expected_filter, "Menu sprite sampled with the wrong filter");
      const auto& clipped = recorder.draws[1].vertices;
      require(clipped[0].sx == 0 && clipped[0].sy == 7 && clipped[2].sx == 2 && clipped[2].sy == 10,
              "Clipped menu sprite quad moved");
      if (text) {
        require(replay(recorder, width, height, scale, initial) ==
                    upscale(baseline, width, height, scale),
                "Menu sprite quads did not reproduce the CPU blit at output scale");
      } else {
        // Same placement; the interior crop edge (u = 2/6) is inset for linear sampling.
        require(std::fabs(clipped[0].tu - (3.f / 6 + .5f / 6)) < 1e-6f,
                "Linear crop of a sprite sheet can bleed into its neighbour");
      }
    }
  }
}

void alpha_and_palette_checks() {
  constexpr int width = 6, height = 3, pitch = width * 2;
  uint16_t colours[] = {0xf800, 0x07e0, 0x001f, 0xffff, 0x8410, 0x0000};
  uint8_t alpha[] = {0, 3, 4, 128, 251, 252};
  zimg::Texture blended{};
  blended.width = blended.width_again = 6;
  blended.height = 1;
  blended.pixels = colours;
  blended.alpha = alpha;
  blended.flags = zimg::kTwoBytes;
  MenuTestHost host;
  ScopedHost scoped_host(&host);
  ScopedTarget scoped_target;
  const auto initial = starting_canvas(width, height);
  {
    auto baseline = initial;
    zrndr::target2d() = {reinterpret_cast<uint8_t*>(baseline.data()), width, height, pitch, 6};
    zrndr::blit16(&blended, 0, 1, 0, nullptr);
    auto shadow = initial;
    zrndr::target2d() = {reinterpret_cast<uint8_t*>(shadow.data()), width, height, pitch, 6};
    Recorder recorder;
    sdlfe::GpuHud hud(recorder, menu_options());
    hud.begin(shadow.data(), width, height, pitch, height);
    hud.set_menu_presentation(1);
    zrndr::blit16(&blended, 0, 1, 0, nullptr);
    require(hud.finish(), "Alpha menu sprite fell back");
    require(shadow == baseline, "Stage D changed the CPU alpha blend");
    require(recorder.draws.size() == 1 && hud.frame_stats().resolved_regions == 0,
            "An alpha-plane menu image was not drawn as one source quad");
    const auto& texels = recorder.uploads.at(0).pixels;
    const unsigned expected_alpha[] = {0, 0, 4, 128, 251, 255};
    for (int column = 0; column < 6; ++column)
      require((texels[size_t(column)] >> 24) == expected_alpha[column],
              "Alpha thresholds differ from blit16");
    // Blended pixels agree with the CPU's RGB565 blend within one 565 step.
    const auto gpu = replay(recorder, width, height, 1, initial);
    const auto cpu = upscale(baseline, width, height, 1);
    for (size_t at = 0; at < gpu.size(); ++at)
      for (int shift = 0; shift < 24; shift += 8) {
        const int difference = int((gpu[at] >> shift) & 255) - int((cpu[at] >> shift) & 255);
        // One RGB565 red/blue step is 8.2; blit16 also divides by 256, not 255.
        require(std::abs(difference) <= 10, "GPU alpha blend left the CPU blend's quantization");
      }
  }
  {
    // Without stage D the same blit stays on stage B's resolved regions.
    auto shadow = initial;
    zrndr::target2d() = {reinterpret_cast<uint8_t*>(shadow.data()), width, height, pitch, 6};
    Recorder recorder;
    auto options = menu_options();
    options.menu_sprites = false;
    sdlfe::GpuHud hud(recorder, options);
    hud.begin(shadow.data(), width, height, pitch, height * 3);
    hud.set_menu_presentation(3);
    require(!hud.menu_presentation_active(), "Turned-off stage D still started");
    zrndr::blit16(&blended, 0, 1, 0, nullptr);
    require(hud.finish() && hud.frame_stats().resolved_regions > 0,
            "Turning stage D off changed the earlier alpha path");
  }
  {
    // Indexed, keyed by palette index 2.
    // Only three entries are valid; the rest keep the CPU blit's out-of-range read in bounds.
    std::array<uint16_t, 16> palette{0xf800, 0x07e0, 0x001f};
    uint8_t indices[] = {0, 2, 1, 2, 0, 1};
    zimg::Texture indexed{};
    indexed.width = indexed.width_again = 3;
    indexed.height = 2;
    indexed.pixels = indices;
    indexed.palette = palette.data();
    indexed.palette_count = 3;
    indexed.flags = zimg::kAlpha;
    auto baseline = initial;
    zrndr::target2d() = {reinterpret_cast<uint8_t*>(baseline.data()), width, height, pitch, 6};
    zrndr::blit16(&indexed, 2, 0, 2, nullptr);
    auto shadow = initial;
    zrndr::target2d() = {reinterpret_cast<uint8_t*>(shadow.data()), width, height, pitch, 6};
    host.text_image = &indexed;  // nearest, so replay is exact
    Recorder recorder;
    sdlfe::GpuHud hud(recorder, menu_options());
    hud.begin(shadow.data(), width, height, pitch, height * 3);
    hud.set_menu_presentation(3);
    zrndr::blit16(&indexed, 2, 0, 2, nullptr);
    require(hud.finish(), "Indexed menu sprite fell back");
    require(replay(recorder, width, height, 3, initial) == upscale(baseline, width, height, 3),
            "Palette colour key differs from blit16 at 3x");
    host.text_image = nullptr;

    // An index past the palette falls back visibly; the CPU blit still runs.
    indices[4] = 9;
    hud.begin(shadow.data(), width, height, pitch, height * 3);
    hud.set_menu_presentation(3);
    zrndr::blit16(&indexed, 2, 0, 2, nullptr);
    require(!hud.finish() && hud.frame_stats().fallback &&
                hud.frame_stats().shadow_reasons.count("invalid image palette") == 1,
            "A bad palette index did not fall back to CPU composition");
  }
}

void source_selection_checks(const std::filesystem::path& directory) {
  constexpr int width = 16, height = 8, pitch = width * 2;
  uint16_t pixels[] = {0xf800, 0x07e0, 0x001f, 0xf81f, 0xffff, 0x0841};
  zimg::Texture sprite{};
  sprite.width = sprite.width_again = 3;
  sprite.height = 2;
  sprite.pixels = pixels;
  sprite.flags = zimg::kTwoBytes | zimg::kAlpha;
  // Artwork registered for the sprite's identity (key pixel counts as 0).
  const std::vector<uint16_t> identity_pixels{0xf800, 0x07e0, 0x001f, 0, 0xffff, 0x0841};
  const uint64_t identity = platform::hud_identity(3, 2, identity_pixels);
  const auto sprites = directory / "ui" / "sprites";
  std::filesystem::create_directories(sprites);
  char name[32];
  std::snprintf(name, sizeof name, "%016llx.rgba", static_cast<unsigned long long>(identity));
  {
    std::ofstream file(sprites / name, std::ios::binary);
    const uint32_t header_size[2] = {12, 8};
    const float uv[4] = {0, 0, 1, 1};
    file.write("MW3H", 4);
    file.write(reinterpret_cast<const char*>(header_size), sizeof header_size);
    file.write(reinterpret_cast<const char*>(uv), sizeof uv);
    const std::vector<uint8_t> rgba(12 * 8 * 4, 255);
    file.write(reinterpret_cast<const char*>(rgba.data()), std::streamsize(rgba.size()));
  }
  MenuTestHost host;
  ScopedHost scoped_host(&host);
  ScopedTarget scoped_target;
  std::vector<uint16_t> shadow(size_t(width) * height);
  zrndr::target2d() = {reinterpret_cast<uint8_t*>(shadow.data()), width, height, pitch, 6};

  // Registered artwork.
  {
    Recorder recorder;
    auto options = menu_options();
    options.artwork = {directory.string()};
    sdlfe::GpuHud hud(recorder, options);
    hud.begin(shadow.data(), width, height, pitch, height * 4);
    hud.set_menu_presentation(4);
    zrndr::blit16(&sprite, 1, 1, 0xf81f, nullptr);
    require(hud.finish() && hud.frame_stats().artwork_hits == 1, "Menu artwork did not hit");
    require(recorder.uploads.size() == 1 && recorder.uploads[0].width == 12 &&
                recorder.draws[0].state.filter == platform::TextureFilter::kLinear,
            "Menu artwork was not sampled from its high-resolution texture");
    const auto& quad = recorder.draws[0].vertices;
    require(quad[0].sx == 1 && quad[0].sy == 1 && quad[2].sx == 4 && quad[2].sy == 3,
            "Menu artwork changed the game's position or size");
  }
  // Output-scale text: the host's raster, sampled nearest, in the source rectangle.
  {
    auto raster = std::make_shared<platform::HudImage>();
    raster->width = 9;
    raster->height = 6;
    raster->pixels.assign(54, 0xff00ff00u);
    host.text_image = &sprite;
    host.raster = raster;
    Recorder recorder;
    auto options = menu_options();
    options.artwork = {directory.string()};
    sdlfe::GpuHud hud(recorder, options);
    for (int frame = 0; frame < 3; ++frame) {
      hud.begin(shadow.data(), width, height, pitch, height * 3);
      hud.set_menu_presentation(3);
      zrndr::blit16(&sprite, 2, 3, 0xf81f, nullptr);
      require(hud.finish(), "Menu text frame fell back");
    }
    require(host.requested_density == 3 && hud.frame_stats().text_hits == 1 &&
                hud.frame_stats().artwork_hits == 0,
            "Menu text did not use the output-scale raster at the menu scale");
    require(recorder.uploads.size() == 1 && recorder.draws.size() == 3,
            "Unchanged menu text was uploaded again");
    require(recorder.draws[0].state.filter == platform::TextureFilter::kNearest,
            "Output-scale text must be sampled nearest");
    const auto& quad = recorder.draws[0].vertices;
    require(quad[0].sx == 2 && quad[0].sy == 3 && quad[2].sx == 5 && quad[2].sy == 5 &&
                quad[0].tu == 0 && quad[2].tu == 1,
            "Output-scale text quad moved");
    // A raster failure keeps the native pixels, logs once and does not blank.
    host.raster_throws = true;
    StderrCapture diagnostics(directory / "raster.log");
    for (int frame = 0; frame < 2; ++frame) {
      hud.begin(shadow.data(), width, height, pitch, height * 3);
      hud.set_menu_presentation(3);
      zrndr::blit16(&sprite, 2, 3, 0xf81f, nullptr);
      require(hud.finish() && hud.frame_stats().text_hits == 0,
              "A text raster failure blanked the text or fell back");
    }
    require(occurrences(diagnostics.text(), "menu text raster failed") == 1,
            "Text raster failure was not logged exactly once");
    host.raster_throws = false;
    host.text_image = nullptr;
  }
  // Native pixels: misses are logged once per identity, then capped; no re-upload.
  {
    Recorder recorder;
    auto options = menu_options();
    options.artwork = {directory.string()};
    options.text = false;
    sdlfe::GpuHud hud(recorder, options);
    StderrCapture diagnostics(directory / "misses.log");
    pixels[0] = 0x1234;  // a different identity: not registered
    for (int frame = 0; frame < 3; ++frame) {
      hud.begin(shadow.data(), width, height, pitch, height * 2);
      hud.set_menu_presentation(2);
      zrndr::blit16(&sprite, 0, 0, 0xf81f, nullptr);
      require(hud.finish(), "Native menu sprite fell back");
    }
    require(recorder.uploads.size() == 1, "An unchanged native sprite was uploaded every frame");
    pixels[1] = 0x4321;
    hud.begin(shadow.data(), width, height, pitch, height * 2);
    hud.set_menu_presentation(2);
    zrndr::blit16(&sprite, 0, 0, 0xf81f, nullptr);
    require(hud.finish() && recorder.uploads.size() == 2,
            "Changed sprite pixels were not uploaded");
    for (int distinct = 0; distinct < 80; ++distinct) {
      pixels[2] = uint16_t(0x0100 + distinct);
      hud.begin(shadow.data(), width, height, pitch, height * 2);
      hud.set_menu_presentation(2);
      zrndr::blit16(&sprite, 0, 0, 0xf81f, nullptr);
      require(hud.finish(), "Native menu sprite fell back");
    }
    const auto log = diagnostics.text();
    require(occurrences(log, "no menu artwork for identity") == 64 &&
                occurrences(log, "further menu artwork misses are not logged") == 1,
            "Artwork misses were not logged once per identity with a bound");
    pixels[0] = 0xf800;
    pixels[1] = 0x07e0;
    pixels[2] = 0x001f;
  }
  // Texture allocation failure falls back to CPU composition with a reason.
  {
    Recorder recorder;
    recorder.allocation_fails = true;
    auto options = menu_options();
    options.text = false;
    sdlfe::GpuHud hud(recorder, options);
    hud.begin(shadow.data(), width, height, pitch, height * 2);
    hud.set_menu_presentation(2);
    zrndr::blit16(&sprite, 0, 0, 0xf81f, nullptr);
    require(!hud.finish() &&
                hud.frame_stats().shadow_reasons.count("texture allocation failed") == 1,
            "A texture allocation failure did not fall back visibly");
  }
  // Observation frames never draw stage D, and the guest FP state survives a draw.
  {
    Recorder recorder;
    sdlfe::GpuHud hud(recorder, menu_options());
    require(hud.begin_observation(shadow.data(), width, height, pitch, height * 2),
            "Observation did not start");
    hud.set_menu_presentation(2);
    require(!hud.menu_presentation_active() && !hud.wants_source_alpha_images(),
            "Stage D started on an observation-only frame");
    hud.cancel();
    const int previous_round = std::fegetround();
    std::fesetround(FE_DOWNWARD);
    std::feclearexcept(FE_ALL_EXCEPT);
    hud.begin(shadow.data(), width, height, pitch, height * 2);
    hud.set_menu_presentation(2.5f);
    zrndr::blit16(&sprite, 0, 0, 0xf81f, nullptr);
    require(hud.finish(), "Menu sprite fell back");
    require(std::fegetround() == FE_DOWNWARD && std::fetestexcept(FE_ALL_EXCEPT) == 0,
            "Stage D changed the guest floating-point state");
    std::fesetround(previous_round);
    // The next frame starts with stage D off until the presenter opts in again.
    hud.begin(shadow.data(), width, height, pitch, height * 2);
    require(!hud.menu_presentation_active(), "Stage D leaked into the next frame");
    hud.cancel();
  }
}

// Two-colour fonts: FontText draws white text, then tints each row's white
// pixels (twod_wintext.cpp). The output-scale raster must carry that tint.
void gradient_text_checks(const char* fonts) {
  const auto saved = zutl::mounts();
  zutl::mounts() = {};
  zutl::mount(fonts);
  zvid::set_pixel_format(5, 6, 5);
  sdlfe::SdlTwodHost host(nullptr, nullptr, nullptr);
  host.enable_hud_text(true);
  auto* image = host.image_new(48, 24);
  image->flags |= zimg::kAlpha;
  auto* pixels = static_cast<uint16_t*>(image->pixels);
  std::fill_n(pixels, 48 * 24, uint16_t(0));
  const auto font = host.CreateFontA(-18, 0, 0, 0, 700, 0, 0, 0, 0, 4, 0, 1, 0, "Arial");
  require(font != 0, "Gradient fixture font is unavailable");
  const auto dc = host.image_dc(image);
  host.SelectObject(dc, font);
  host.SetTextColor(dc, 0xffffff);
  host.SetBkMode(dc, 1);
  ztwod::Rect box{2, 2, 46, 22};
  host.DrawTextA(dc, "MW", -1, &box, 0);
  require(host.is_text_image(image), "Drawn text was not reported as text");
  const auto plain = host.hud_text_image(image, 3, 0);
  require(plain != nullptr, "Plain text did not rasterise");
  // Tint like FontText::render: rows 0..11 red, 12..23 blue.
  const uint16_t white = zvid::pack_bytes(0xff, 0xff, 0xff);
  for (int row = 0; row < 24; ++row)
    for (int column = 0; column < 48; ++column)
      if (pixels[row * 48 + column] == white)
        pixels[row * 48 + column] = row < 12 ? 0xf800 : 0x001f;
  const auto tinted = host.hud_text_image(image, 3, 0);
  require(tinted && tinted != plain, "Two-colour text lost its output-scale raster");
  unsigned red_top = 0, blue_bottom = 0, wrong = 0;
  for (unsigned y = 0; y < tinted->height; ++y)
    for (unsigned x = 0; x < tinted->width; ++x) {
      const uint32_t pixel = tinted->pixels[size_t(y) * tinted->width + x];
      if ((pixel >> 24) != 255) continue;
      const unsigned red = pixel & 255, green = (pixel >> 8) & 255, blue = (pixel >> 16) & 255;
      if (y < 36 && red == 255 && green == 0 && blue == 0) ++red_top;
      else if (y >= 36 && red == 0 && green == 0 && blue == 255) ++blue_bottom;
      else ++wrong;
    }
  require(red_top > 0 && blue_bottom > 0 && wrong == 0,
          "Output-scale text did not follow the row tint");
  require(host.hud_text_image(image, 3, 0) == tinted, "Unchanged tinted text was rasterised again");
  // Any other edit keeps the native image rather than stale text.
  pixels[0] = 0x1234;
  require(!host.hud_text_image(image, 3, 0), "Edited text pixels were replaced by stale text");
  host.DeleteDC(dc);
  host.DeleteObject(font);
  host.texture_free(image);
  zutl::mounts() = saved;
}
}  // namespace

int main(int argc, char** argv) {
  const auto directory =
      std::filesystem::temp_directory_path() /
      ("mw3-menu-sprites-" + std::to_string(SDL_GetPerformanceCounter()));
  try {
    policy_checks();
    placement_checks();
    alpha_and_palette_checks();
    source_selection_checks(directory);
    if (argc == 3 && std::string(argv[1]) == "--fonts")
      gradient_text_checks(argv[2]);
    else
      require(argc == 1, "usage: mw3menu_sprite_checks [--fonts DIR]");
    std::filesystem::remove_all(directory);
    std::puts("HD menu stage D placement, key/alpha, source, cache, fallback and log checks "
              "passed");
    return 0;
  } catch (const std::exception& error) {
    std::error_code ignored;
    std::filesystem::remove_all(directory, ignored);
    std::fprintf(stderr, "HD menu stage D check failed: %s\n", error.what());
    return 1;
  }
}
