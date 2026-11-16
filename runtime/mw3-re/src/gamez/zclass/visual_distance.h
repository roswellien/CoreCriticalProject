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

// Scale render-only authored distance ranges with the visual far plane. Keeping
// the scale local to rendering leaves the camera's simulation clip untouched.
inline float visual_distance_scale(float authored_far, unsigned requested_far,
                                   bool qualifying_world_camera) {
  if (!(authored_far > 0.0f)) return 1.0f;
  return visual_far(authored_far, requested_far, qualifying_world_camera) /
         authored_far;
}

struct SquaredFadeRange {
  float near_squared;
  float far_squared;
  float interpolation_factor;
};

inline SquaredFadeRange scale_squared_fade_range(float near_squared,
                                                 float far_squared,
                                                 float interpolation_factor,
                                                 float distance_scale) {
  const float scale_squared = distance_scale * distance_scale;
  return {near_squared * scale_squared, far_squared * scale_squared,
          interpolation_factor / scale_squared};
}

inline bool visual_far_corners_need_update(bool clip_changed, float render_far,
                                           float cached_corner_z) {
  return clip_changed || cached_corner_z != -render_far;
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
