#pragma once
#include <map>
#include <set>
#include <string>
#include <vector>

#include "gamez/zrender/zrndr_blit.h"
#include "platform/prepared_hud.h"
#include "platform/render3d.h"

namespace sdlfe {
class FrameRenderer;
struct HudOptions {
  std::string mode = "original";
  std::vector<std::string> artwork;
  std::string menu_background;
  std::string menu_background_renderer = "gpu";
  bool text = true;
  // Diagnostic only: count what the menu draws without changing it. Off by default.
  bool observe_menu = false;
  // HD menu stage D (menu_sprites.h). Also off when MW3_HD_MENU_SPRITES=0.
  bool menu_sprites = true;
};
// An instance-owned HUD draw list. The original canvas remains a CPU shadow
// for native reads; display uses owned GPU images and ordered primitives.
class GpuHud final : public zrndr::DrawObserver {
 public:
  static constexpr uint64_t kMaxFrameResolvedBytes = 32ULL * 1024 * 1024;
  static constexpr uint64_t kMaxFrameResolvedRegions = 4096;
  static constexpr size_t kMaxReasonKeys = 32;

  struct FrameStats {
    uint64_t images{};
    uint64_t text_hits{};
    uint64_t resolved_regions{};
    // HD menu stage D: images drawn from a registered high-resolution artwork pack.
    uint64_t artwork_hits{};
    bool fallback{};
    std::map<std::string, uint64_t> shadow_reasons;
  };

  GpuHud(FrameRenderer& renderer, const HudOptions& options);
  ~GpuHud() override;
  void begin(const uint16_t* target, int width, int height, int pitch, int output_height);
  // Records menu coverage without uploading textures or submitting GPU draws.
  bool begin_observation(const uint16_t* target, int width, int height, int pitch, int output_height);
  bool finish();
  void cancel();
  const FrameStats& frame_stats() const { return frame_stats_; }
  void image(const zimg::Texture*, int32_t x, int32_t y, uint16_t key,
             const zrndr::BlitRect*) override;
  void pixel(const uint16_t* destination, uint16_t colour) override;
  void span(const uint16_t* destination, uint32_t count, uint16_t colour) override;
  void resolved_region(const uint16_t* destination, uint32_t width, uint32_t height,
                       uint32_t pitch_bytes, const char* operation) override;
  void framebuffer_write(const void* target, const char* operation) override;

  // HD menu stage D (gpu_hud_menu_sprites.cpp, menu_sprites.h). Called after a
  // begin for a menu frame: until the frame ends, menu text and sprites are
  // drawn from output-resolution sources (text re-rasterised at menu_scale,
  // registered artwork, else the native image) instead of native pixels, and
  // blit16 reports alpha-plane images as images rather than resolved regions.
  // Does nothing when HudOptions::menu_sprites is false or MW3_HD_MENU_SPRITES
  // is 0. The presenter passes menu_presentation_scale() for the frame.
  void set_menu_presentation(float menu_scale);
  bool menu_presentation_active() const { return menu_presentation_.active; }
  bool wants_source_alpha_images() const override;

 private:
  // HD menu stage D state for the current frame; begin_frame resets it.
  struct MenuPresentation {
    bool active{};
    float scale{1};
  };
  // Draws one menu image for stage D. Returns false when the ordinary image
  // path should draw it instead (the menu background source, owned by stage C).
  bool draw_menu_sprite(const zimg::Texture* source, uint16_t key, int64_t destination_x,
                        int64_t destination_y, int64_t left, int64_t top, int64_t right,
                        int64_t bottom);
  void log_menu_artwork_miss(uint64_t identity, int width, int height);
  MenuPresentation menu_presentation_;
  std::set<uint64_t> logged_menu_artwork_misses_;
  bool menu_artwork_miss_limit_logged_{};
  bool menu_text_failure_logged_{};

  struct Resource {
    std::shared_ptr<const platform::HudImage> image;
    int texture;
    uint64_t used;
  };
  struct Source {
    uint64_t hash;
    std::shared_ptr<const platform::HudImage> image;
  };
  struct Command {
    int texture;
    unsigned first, count;
    platform::Primitive primitive;
    bool sharp;
    platform::TextureFilter filter{platform::TextureFilter::kDefault};
  };
  void begin_frame(const uint16_t* target, int width, int height, int pitch, int output_height,
                   bool observation_only);
  bool position(const uint16_t* pointer, int& x, int& y) const;
  int texture(const std::shared_ptr<const platform::HudImage>& image);
  void rectangle(float x0, float y0, float x1, float y1, uint32_t colour, int texture = -1,
                 float u0 = 0, float v0 = 0, float u1 = 1, float v1 = 1,
                 platform::TextureFilter filter = platform::TextureFilter::kDefault);
  void append(platform::TLVertex vertex, int texture, platform::Primitive primitive, bool sharp,
              platform::TextureFilter filter = platform::TextureFilter::kDefault);
  void record_shadow_reason(const char* operation);
  FrameRenderer& renderer_;
  HudOptions options_;
  platform::HudArtwork artwork_;
  std::map<uint64_t, std::string> artwork_roots_;
  std::map<const platform::HudImage*, Resource> resources_;
  std::map<const zimg::Texture*, Source> sources_;
  std::vector<platform::TLVertex> vertices_;
  std::vector<Command> commands_;
  const uint16_t* target_{};
  int width_{}, height_{}, pitch_{};
  float density_{1};
  uint64_t frame_{}, layers_{}, images_{}, hits_{}, text_hits_{}, points_{}, spans_{},
      resolved_regions_{};
  uint64_t resource_bytes_{};
  uint64_t frame_resolved_bytes_{};
  uint64_t frame_resolved_regions_{};
  bool shadow_layer_{};
  bool observation_only_{};
  uint64_t observed_draws_{};
  FrameStats frame_stats_;
  uint64_t shadow_layers_{};
  std::map<std::string, uint64_t> shadow_reasons_;
  std::set<std::string> logged_shadow_reasons_;
};
}  // namespace sdlfe
