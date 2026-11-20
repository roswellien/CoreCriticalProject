#pragma once

#include <array>
#include <cstdint>
#include <filesystem>
#include <functional>
#include <memory>
#include <vector>

#include "gamez/zimage/zimg_library.h"
#include "gamez/zrender/zrndr_blit.h"

namespace platform {

namespace detail {
// Internal row worker pool, exposed so asset-free tests can inject render failures.
class MenuBackgroundWorkers {
 public:
  using WorkerWakeupHook = void (*)(void*);

  explicit MenuBackgroundWorkers(unsigned worker_count = 0,
                                 WorkerWakeupHook worker_wakeup_hook = nullptr,
                                 void* worker_wakeup_context = nullptr);
  ~MenuBackgroundWorkers();
  MenuBackgroundWorkers(const MenuBackgroundWorkers&) = delete;
  MenuBackgroundWorkers& operator=(const MenuBackgroundWorkers&) = delete;

  void run(unsigned row_count, const std::function<void(unsigned, unsigned)>& render_rows);
  unsigned thread_count() const;

 private:
  struct Impl;
  std::unique_ptr<Impl> impl_;
};
}  // namespace detail

struct MenuBackgroundImage {
  unsigned width{}, height{}, source_width{}, source_height{};
  std::vector<uint8_t> rgb;
};

struct MenuBackgroundOutputSize {
  unsigned width{}, height{};
  double fit_scale{}, compose_scale{};
};

struct MenuBackgroundLayerRect {
  float x{}, y{}, width{}, height{};
};

struct MenuBackgroundUvRect {
  float u0{}, v0{}, u1{}, v1{};
};

// Destination in output pixels: uniformly scaled and centered, with excess
// cropped by the render target. Invalid dimensions are rejected.
MenuBackgroundLayerRect menu_background_cover_rect(int frame_width, int frame_height,
                                                    int output_width, int output_height);
// Source offsets and spans use the supplied game texture dimensions, or the
// image's source dimensions when omitted. The half-HD-texel offset
// matches sample()'s integer-centered bilinear convention on GPU samplers. The half texel is
// that of the BOUND texture (texture_width x texture_height), which is a filtered, smaller copy
// of the image when the GPU upload was downsampled; zero means the image's own size.
MenuBackgroundUvRect menu_background_uv_rect(const MenuBackgroundImage &image, int64_t source_x,
                                             int64_t source_y, int frame_width, int frame_height,
                                             unsigned game_width = 0, unsigned game_height = 0,
                                             unsigned texture_width = 0,
                                             unsigned texture_height = 0);
// Extend the recorded scroll mapping outside its original destination, so a
// covering background cannot crop/move native controls or their correction maps.
MenuBackgroundUvRect menu_background_extend_uv(const MenuBackgroundUvRect& uv,
                                               const MenuBackgroundLayerRect& frame_rectangle,
                                               const MenuBackgroundLayerRect& cover_rectangle);

// kGain and kAdded are only the values no map pass can represent: a non-finite gain (or one
// above kMenuBackgroundMaximumGain, which classification already limits for both paths), or
// non-finite added light or added light beyond one full 8-bit channel.
enum class MenuBackgroundGpuStatus { kReady, kMapping, kGain, kAdded };
const char* menu_background_gpu_status_name(MenuBackgroundGpuStatus status);

// The real menu art both brightens (gain above 1) and darkens added-light pixels (negative
// deltas). Each map below is a frame-sized RGBA8 texture drawn as its own blended pass, in this
// order, so every part of the range stays an exact UNORM value:
//   kAttenuate  destination * map             gain up to 1
//   kBoost      destination + destination*map  gain from 1 to 2 (map = gain - 1)
//   kBoostHigh  destination + destination*map  gain from 2 to 4 (map = gain / 2 - 1)
//   kAdd        destination + map              positive added light
//   kSubtract   destination - map              negative added light
//   kOverlay    alpha blend                    native artwork that is not background
// A pixel's gain is attenuate * (1 + boost) * (1 + boost_high), so gains up to
// kMenuBackgroundMaximumGain need no clamping. The CPU compositor clamps only once at the end;
// the passes clamp after each step, which gives the same result because a pixel has either a
// gain (all factors >= 0) or added light, never both.
enum MenuBackgroundGpuMap : unsigned {
  kMenuGpuAttenuate,
  kMenuGpuBoost,
  kMenuGpuBoostHigh,
  kMenuGpuAdd,
  kMenuGpuSubtract,
  kMenuGpuOverlay,
  kMenuGpuMapCount
};
// The 5x5 gain is limited to this for the CPU and GPU paths alike. A larger ratio only arises
// over near-black original pixels, where the +4 bias of the ratio dominates.
constexpr float kMenuBackgroundMaximumGain = 4.f;

struct MenuBackgroundGpuLayers {
  std::array<std::vector<uint32_t>, kMenuGpuMapCount> maps;
  // A map whose every pixel is the identity for its pass (0 for boosts, added and subtracted
  // light; the overlay is always drawn) does not need its pass.
  std::array<bool, kMenuGpuMapCount> used{};
  // Each map's own revision changes only when its pixels change, so a frame that changes the
  // gain alone uploads one texture rather than six.
  std::array<uint64_t, kMenuGpuMapCount> map_revisions{};
  MenuBackgroundUvRect uv;
  MenuBackgroundGpuStatus status = MenuBackgroundGpuStatus::kMapping;
  // UV-only changes need another quad, but no texture upload. A revision
  // identifies the complete maps, never an unsupported partial result.
  uint64_t revision = 0;
};

// Output resolution follows the frame's uniform window fit, subject to an
// optional height cap. A zero cap leaves the full fit uncapped.
MenuBackgroundOutputSize menu_background_output_size(int frame_width, int frame_height,
                                                     int window_width, int window_height,
                                                     unsigned maximum_height);

// The composed texture is presented across the original frame rectangle,
// independently of its CPU composition resolution.
MenuBackgroundLayerRect menu_background_layer_rect(int frame_width, int frame_height);

MenuBackgroundImage load_menu_background(const std::filesystem::path& path);
// Area filtering suppresses scrolling shimmer without requiring a mipmap API.
// The original image remains available to the CPU compositor.
// The height limit for the GPU upload: twice the window's height, else twice the display's, else
// the full image height (no filtering). Zero or negative sizes mean "unknown".
unsigned menu_background_upload_height(int window_height, int display_height,
                                       unsigned image_height);
MenuBackgroundImage menu_background_upload_image(const MenuBackgroundImage &image,
                                                 unsigned maximum_height);

// Reconstructs the original scrolling image under native controls, tint and
// glow pixels. The result is presentation state and never touches simulation
// or guest-owned buffers.
bool compose_menu_background(const MenuBackgroundImage& image, const zimg::Texture* source,
                             const std::vector<zrndr::MenuBackgroundBlit>& blits,
                             const uint16_t* pixels, int width, int height, int pitch,
                             bool rgb565, unsigned output_width, unsigned output_height,
                             std::vector<uint32_t>* output);

enum class PreparedMenuTextureAction { kCreate, kUpdate, kReuse };

// Keep the GPU texture synchronized with the cached CPU composition. A cache
// hit only allows reuse when the texture still exists at the composed size.
PreparedMenuTextureAction prepared_menu_texture_action(bool cache_hit, bool texture_exists,
                                                       int texture_width, int texture_height,
                                                       unsigned output_width,
                                                       unsigned output_height);

// Reuses composition scratch storage and worker threads across frames, and
// retains the last output while every input that affects it remains identical.
class PreparedMenuBackgroundComposer {
 public:
  PreparedMenuBackgroundComposer();
  ~PreparedMenuBackgroundComposer();
  PreparedMenuBackgroundComposer(const PreparedMenuBackgroundComposer&) = delete;
  PreparedMenuBackgroundComposer& operator=(const PreparedMenuBackgroundComposer&) = delete;

  bool compose(const MenuBackgroundImage& image, const zimg::Texture* source,
               const std::vector<zrndr::MenuBackgroundBlit>& blits, const uint16_t* pixels,
               int width, int height, int pitch, bool rgb565, unsigned output_width,
               unsigned output_height, std::vector<uint32_t>* output, bool* cache_hit = nullptr);
  // Shares classification, gain math and input comparison with the CPU path;
  // never samples the HD image or allocates output-sized storage.
  bool prepare_gpu(const MenuBackgroundImage& image, const zimg::Texture* source,
                   const std::vector<zrndr::MenuBackgroundBlit>& blits, const uint16_t* pixels,
                   int width, int height, int pitch, bool rgb565,
                   MenuBackgroundGpuLayers* layers, bool* cache_hit = nullptr);
  void invalidate_cache();
  // The size of the texture the GPU path samples (the filtered upload); 0 means the image's own.
  void set_bound_texture_size(unsigned width, unsigned height);
  unsigned thread_count() const;

 private:
  bool prepare(const MenuBackgroundImage& image, const zimg::Texture* source,
               const std::vector<zrndr::MenuBackgroundBlit>& blits, const uint16_t* pixels,
               int width, int height, int pitch, bool rgb565, unsigned output_width,
               unsigned output_height, std::vector<uint32_t>* output,
               MenuBackgroundGpuLayers* layers, bool* cache_hit);
  struct Impl;
  std::unique_ptr<Impl> impl_;
  unsigned bound_texture_width_ = 0, bound_texture_height_ = 0;
};

}  // namespace platform
