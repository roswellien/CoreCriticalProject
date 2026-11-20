// HD menu stage D: menu text and sprites drawn from output-resolution sources.
// The pure policy is in menu_sprites.h; this file applies it inside GpuHud.
// Kept apart from gpu_hud.cpp so the stage can be reviewed (and merged with
// the live menu switch) as one block.
#include <algorithm>
#include <cctype>
#include <cfenv>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <string>

#include "frontend/sdl/gpu_hud.h"
#include "frontend/sdl/menu_sprites.h"
#include "gamez/zimage/zimg_library.h"
#include "gamez/ztwod/twod_host.h"

namespace sdlfe {
namespace {
// Same contract as gpu_hud.cpp's FloatScope: HUD arithmetic runs with
// round-to-nearest and must leave the guest's x87/SSE state as it found it.
class MenuFloatScope {
 public:
  MenuFloatScope() {
    std::feholdexcept(&saved_);
    std::fesetround(FE_TONEAREST);
  }
  ~MenuFloatScope() { std::fesetenv(&saved_); }

 private:
  std::fenv_t saved_{};
};
// Premultiplied RGBA from RGB565, identical to gpu_hud.cpp's rgba() so a menu
// image and a HUD image of the same pixels share one cached texture.
uint32_t premultiplied_rgba(uint16_t colour, unsigned alpha) {
  const unsigned red = (colour >> 11) * 255 / 31;
  const unsigned green = ((colour >> 5) & 63) * 255 / 63;
  const unsigned blue = (colour & 31) * 255 / 31;
  return (red * alpha + 127) / 255 | ((green * alpha + 127) / 255) << 8 |
         ((blue * alpha + 127) / 255) << 16 | alpha << 24;
}
// FNV-1a over 32-bit values, as gpu_hud.cpp folds the sources_ cache hash.
void fold_word(uint64_t& hash, uint32_t value) {
  for (int i = 0; i < 4; ++i) {
    hash ^= uint8_t(value >> (8 * i));
    hash *= 0x100000001b3ULL;
  }
}
// Distinct artwork misses logged before going quiet: a menu shows a few dozen
// distinct images, so this names every miss on one screen without flooding.
constexpr size_t kMaxLoggedArtworkMisses = 64;
}  // namespace

bool menu_sprites_allowed_by(const char* environment_value) {
  if (!environment_value) return true;
  std::string value(environment_value);
  for (char& character : value)
    character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
  const bool turned_off = value == "0" || value == "off" || value == "false" || value == "no";
  return !turned_off;
}

bool menu_sprites_allowed_by_environment() {
  static const bool allowed = [] {
    const bool result = menu_sprites_allowed_by(std::getenv(kMenuSpritesEnvironment));
    if (!result)
      std::fprintf(stderr, "GPU HUD: HD menu text and sprites are off (%s=0)\n",
                   kMenuSpritesEnvironment);
    return result;
  }();
  return allowed;
}

float menu_presentation_scale(int canvas_width, int canvas_height, int output_width,
                              int output_height) {
  if (canvas_width <= 0 || canvas_height <= 0 || output_width <= 0 || output_height <= 0)
    return 1;
  // The menu's logical 4:3 dialog; a smaller canvas (tests, odd modes) is the dialog itself.
  const int dialog_width = std::min(640, canvas_width);
  const int dialog_height = std::min(480, canvas_height);
  const float horizontal = float(output_width) / float(dialog_width);
  const float vertical = float(output_height) / float(dialog_height);
  return std::max(1.f, std::min(horizontal, vertical));
}

platform::TextureFilter menu_sprite_filter(MenuSpriteSource source, bool native_is_text) {
  switch (source) {
    case MenuSpriteSource::kOutputText:
      return platform::TextureFilter::kNearest;
    case MenuSpriteSource::kArtwork:
      return platform::TextureFilter::kLinear;
    case MenuSpriteSource::kNative:
      return native_is_text ? platform::TextureFilter::kNearest : platform::TextureFilter::kLinear;
  }
  return platform::TextureFilter::kNearest;
}

MenuSpriteQuad menu_sprite_quad(int64_t destination_x, int64_t destination_y, int64_t left,
                                int64_t top, int64_t right, int64_t bottom, int source_width,
                                int source_height, const platform::HudImage& image,
                                platform::TextureFilter filter) {
  MenuSpriteQuad quad;
  quad.x0 = float(destination_x);
  quad.y0 = float(destination_y);
  quad.x1 = float(destination_x + (right - left));
  quad.y1 = float(destination_y + (bottom - top));
  // One source pixel's share of the sampled texture's UV rectangle.
  const float source_u = (image.u1 - image.u0) / float(source_width);
  const float source_v = (image.v1 - image.v0) / float(source_height);
  quad.u0 = image.u0 + float(left) * source_u;
  quad.u1 = image.u0 + float(right) * source_u;
  quad.v0 = image.v0 + float(top) * source_v;
  quad.v1 = image.v0 + float(bottom) * source_v;
  if (filter == platform::TextureFilter::kLinear && image.width > 0 && image.height > 0) {
    const float half_texel_u = 0.5f / float(image.width);
    const float half_texel_v = 0.5f / float(image.height);
    if (left > 0) quad.u0 += half_texel_u;
    if (right < source_width) quad.u1 -= half_texel_u;
    if (top > 0) quad.v0 += half_texel_v;
    if (bottom < source_height) quad.v1 -= half_texel_v;
    // A one-texel crop keeps its centre rather than inverting.
    if (quad.u1 < quad.u0) quad.u0 = quad.u1 = (quad.u0 + quad.u1) / 2;
    if (quad.v1 < quad.v0) quad.v0 = quad.v1 = (quad.v0 + quad.v1) / 2;
  }
  return quad;
}

unsigned menu_sprite_alpha(bool has_alpha_plane, uint8_t alpha_plane_value, bool keyed,
                           uint16_t compared_value, uint16_t key) {
  if (has_alpha_plane) {
    // blit16 skips alphas 0..3 (RGB565) and writes 0xfc..0xff unblended.
    if (alpha_plane_value <= 3) return 0;
    if (alpha_plane_value >= 0xfc) return 255;
    return alpha_plane_value;
  }
  if (keyed && compared_value == key) return 0;
  return 255;
}

void GpuHud::set_menu_presentation(float menu_scale) {
  if (!target_ || observation_only_) return;
  if (!options_.menu_sprites || !menu_sprites_allowed_by_environment()) return;
  MenuFloatScope scope;
  const bool usable_scale = std::isfinite(menu_scale) && menu_scale > 0;
  menu_presentation_.active = true;
  menu_presentation_.scale = usable_scale ? std::max(1.f, menu_scale) : 1.f;
}

bool GpuHud::wants_source_alpha_images() const {
  return menu_presentation_.active && target_ != nullptr && !observation_only_;
}

void GpuHud::log_menu_artwork_miss(uint64_t identity, int width, int height) {
  if (artwork_.empty()) {
    if (!menu_artwork_miss_limit_logged_)
      std::fprintf(stderr,
                   "GPU HUD: no menu/HUD artwork pack loaded; menu images use native pixels\n");
    menu_artwork_miss_limit_logged_ = true;
    return;
  }
  if (logged_menu_artwork_misses_.count(identity)) return;
  if (logged_menu_artwork_misses_.size() >= kMaxLoggedArtworkMisses) {
    if (!menu_artwork_miss_limit_logged_)
      std::fprintf(stderr, "GPU HUD: further menu artwork misses are not logged\n");
    menu_artwork_miss_limit_logged_ = true;
    return;
  }
  logged_menu_artwork_misses_.insert(identity);
  std::fprintf(stderr,
               "GPU HUD: no menu artwork for identity %016llx (%dx%d); using native pixels\n",
               static_cast<unsigned long long>(identity), width, height);
}

bool GpuHud::draw_menu_sprite(const zimg::Texture* source, uint16_t key, int64_t destination_x,
                              int64_t destination_y, int64_t left, int64_t top, int64_t right,
                              int64_t bottom) {
  // Stage C owns the scrolling background image; leave it to that path.
  if (source == zrndr::menu_background_source()) return false;
  MenuFloatScope scope;
  const int width = source->width, height = source->height;
  const size_t count = size_t(width) * height;
  const bool has_alpha_plane = source->alpha != nullptr;
  const bool keyed = !has_alpha_plane && (source->flags & zimg::kAlpha) != 0;

  // First pass: validate, and build the artwork identity and the content hash.
  // The identity is the HUD pack contract (tools/vulkan-hud/build_hires_pack.py):
  // RGB565 where the pixel is drawn at all, 0 where it is fully transparent.
  std::vector<uint16_t> identity_pixels(count);
  uint64_t content_hash = 0xcbf29ce484222325ULL;
  fold_word(content_hash, uint32_t(width));
  fold_word(content_hash, uint32_t(height));
  for (int row = 0; row < height; ++row)
    for (int column = 0; column < width; ++column) {
      const size_t at = size_t(row) * source->width_again + column;
      unsigned index = 0;
      if (source->palette) {
        index = static_cast<const uint8_t*>(source->pixels)[at];
        // blit16 would read past the palette; a GPU texel cannot vouch for that colour.
        if (index >= unsigned(source->palette_count)) {
          record_shadow_reason("invalid image palette");
          return true;
        }
      }
      const uint16_t pixel = source->palette ? source->palette[index]
                                             : static_cast<const uint16_t*>(source->pixels)[at];
      const uint16_t compared = source->palette ? uint16_t(index) : pixel;
      unsigned raw_alpha = has_alpha_plane ? source->alpha[at] : 255;
      if (keyed && compared == key) raw_alpha = 0;
      identity_pixels[size_t(row) * width + column] = raw_alpha ? pixel : 0;
      fold_word(content_hash, uint32_t(pixel) | raw_alpha << 16);
    }

  std::shared_ptr<const platform::HudImage> selected;
  MenuSpriteSource kind = MenuSpriteSource::kNative;
  if (options_.text) {
    try {
      selected = ztwod::host().hud_text_image(source, menu_presentation_.scale, key);
      if (selected) kind = MenuSpriteSource::kOutputText;
    } catch (const std::exception& error) {
      // The native image still shows the text; the reason is logged once.
      selected = nullptr;
      if (!menu_text_failure_logged_)
        std::fprintf(stderr, "GPU HUD: menu text raster failed (%s); using native pixels\n",
                     error.what());
      menu_text_failure_logged_ = true;
    }
  }
  bool native_is_text = false;
  if (!selected) {
    native_is_text = ztwod::host().is_text_image(source);
    const uint64_t identity = platform::hud_identity(width, height, identity_pixels);
    const auto found = artwork_.find(identity);
    if (found != artwork_.end()) {
      selected = found->second;
      kind = MenuSpriteSource::kArtwork;
    } else if (!native_is_text) {
      log_menu_artwork_miss(identity, width, height);
    }
  }
  if (!selected) {
    const auto cached = sources_.find(source);
    if (cached != sources_.end() && cached->second.hash == content_hash) {
      selected = cached->second.image;
    } else {
      // Second pass only when the pixels changed: the texture is built once
      // per distinct content, so an unchanged image is never re-uploaded.
      auto native = std::make_shared<platform::HudImage>();
      native->width = unsigned(width);
      native->height = unsigned(height);
      native->pixels.resize(count);
      for (int row = 0; row < height; ++row)
        for (int column = 0; column < width; ++column) {
          const size_t at = size_t(row) * source->width_again + column;
          const unsigned index =
              source->palette ? static_cast<const uint8_t*>(source->pixels)[at] : 0;
          const uint16_t pixel = source->palette ? source->palette[index]
                                                 : static_cast<const uint16_t*>(source->pixels)[at];
          const uint16_t compared = source->palette ? uint16_t(index) : pixel;
          const uint8_t plane = has_alpha_plane ? source->alpha[at] : 255;
          const unsigned alpha = menu_sprite_alpha(has_alpha_plane, plane, keyed, compared, key);
          native->pixels[size_t(row) * width + column] = premultiplied_rgba(pixel, alpha);
        }
      selected = native;
      sources_[source] = {content_hash, selected};
    }
  }

  int handle = -1;
  try {
    handle = texture(selected);
  } catch (...) {
    record_shadow_reason("texture allocation failed");
    return true;
  }
  const auto filter = menu_sprite_filter(kind, native_is_text);
  const auto quad = menu_sprite_quad(destination_x, destination_y, left, top, right, bottom, width,
                                     height, *selected, filter);
  rectangle(quad.x0, quad.y0, quad.x1, quad.y1, 0xffffffffu, handle, quad.u0, quad.v0, quad.u1,
            quad.v1, filter);
  ++images_;
  ++frame_stats_.images;
  if (kind == MenuSpriteSource::kOutputText) {
    ++text_hits_;
    ++frame_stats_.text_hits;
  } else if (kind == MenuSpriteSource::kArtwork) {
    ++hits_;
    ++frame_stats_.artwork_hits;
  }
  return true;
}

}  // namespace sdlfe
