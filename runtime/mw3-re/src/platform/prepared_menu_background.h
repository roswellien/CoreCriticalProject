#pragma once

#include <cstdint>
#include <filesystem>
#include <memory>
#include <vector>

#include "gamez/zimage/zimg_library.h"
#include "gamez/zrender/zrndr_blit.h"

namespace platform {

struct MenuBackgroundImage {
  unsigned width{}, height{}, source_width{}, source_height{};
  std::vector<uint8_t> rgb;
};

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
  void invalidate_cache();
  unsigned thread_count() const;

 private:
  struct Impl;
  std::unique_ptr<Impl> impl_;
};

}  // namespace platform
