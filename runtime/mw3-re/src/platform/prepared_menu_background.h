#pragma once

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
// Source offsets are in original-image pixels. The half-HD-texel offset
// matches sample()'s integer-centered bilinear convention on GPU samplers.
MenuBackgroundUvRect menu_background_uv_rect(const MenuBackgroundImage& image,
                                             int64_t source_x, int64_t source_y,
                                             int frame_width, int frame_height);
// Extend the recorded scroll mapping outside its original destination, so a
// covering background cannot crop/move native controls or their correction maps.
MenuBackgroundUvRect menu_background_extend_uv(const MenuBackgroundUvRect& uv,
                                               const MenuBackgroundLayerRect& frame_rectangle,
                                               const MenuBackgroundLayerRect& cover_rectangle);

enum class MenuBackgroundGpuStatus { kReady, kMapping, kGain, kAdded };
const char* menu_background_gpu_status_name(MenuBackgroundGpuStatus status);

struct MenuBackgroundGpuLayers {
  std::vector<uint32_t> overlay, gain, added;
  MenuBackgroundUvRect uv;
  MenuBackgroundGpuStatus status = MenuBackgroundGpuStatus::kMapping;
  // UV-only changes need another quad, but no texture upload. A revision
  // identifies the three complete maps, never an unsupported partial result.
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
  unsigned thread_count() const;

 private:
  bool prepare(const MenuBackgroundImage& image, const zimg::Texture* source,
               const std::vector<zrndr::MenuBackgroundBlit>& blits, const uint16_t* pixels,
               int width, int height, int pitch, bool rgb565, unsigned output_width,
               unsigned output_height, std::vector<uint32_t>* output,
               MenuBackgroundGpuLayers* layers, bool* cache_hit);
  struct Impl;
  std::unique_ptr<Impl> impl_;
};

}  // namespace platform
