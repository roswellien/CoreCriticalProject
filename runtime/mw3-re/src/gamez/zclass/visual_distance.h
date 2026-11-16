#pragma once

#include <algorithm>

namespace zcls {

constexpr unsigned kDefaultVisualFar = 800;

inline float visual_far(float authored_far, unsigned requested_far,
                        bool qualifying_world_camera) {
  if (!qualifying_world_camera || requested_far <= kDefaultVisualFar)
    return authored_far;
  return std::max(authored_far, static_cast<float>(requested_far));
}

void set_visual_far_request(unsigned requested_far);
unsigned visual_far_request();
float visual_far_for_render(const void* camera, float authored_far);

class ScopedZoomVisualFar {
 public:
  explicit ScopedZoomVisualFar(const void* camera);
  ~ScopedZoomVisualFar();
  ScopedZoomVisualFar(const ScopedZoomVisualFar&) = delete;
  ScopedZoomVisualFar& operator=(const ScopedZoomVisualFar&) = delete;

 private:
  const void* previous_camera_ = nullptr;
  bool active_ = false;
};

}  // namespace zcls
