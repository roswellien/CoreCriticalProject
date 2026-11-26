#pragma once
#include "sun_lighting.hpp"
#include <chrono>
#include <cstdint>

#include <optional>

namespace mw34::detail {
// Presentation-only state. No guest clock queries or simulation writes.
struct Settings {
  bool water{}, clouds{};
  float water_strength{.45f}, cloud_strength{.35f}, scale{.06f}, speed{.025f};
};
inline bool enabled(unsigned role, const Settings &detail_settings) {
  // Transport roles are 1: water, 2: surf, 3: clouds. Unknown roles remain
  // disabled; this predicate does not infer a role from a texture name.
  return (role == 1 || role == 2)
             ? detail_settings.water && detail_settings.water_strength > 0
         : role == 3
             ? detail_settings.clouds && detail_settings.cloud_strength > 0
             : false;
}
inline double
presentation_time(std::uint64_t frame,
                  std::optional<double> fixed_time = std::nullopt,
                  std::optional<double> replay_time = std::nullopt) {
  if (replay_time) return *replay_time;
  // Call this from one presentation thread. Cache one steady-clock
  // sample per supplied frame number so every draw in that frame shares phase.
  // The optional fixed time is also sampled once; neither path advances or
  // reads the guest simulation clock.
  using Clock = std::chrono::steady_clock;
  static const auto start = Clock::now();
  if (fixed_time.has_value())
    return *fixed_time;
  static std::uint64_t previous_frame = ~std::uint64_t{};
  static double seconds{};
  if (previous_frame != frame) {
    seconds = std::chrono::duration<double>(Clock::now() - start).count();
    previous_frame = frame;
  }
  return seconds;
}
inline void uniform(sun::Uniform &uniform_block, unsigned role,
                    const Settings &detail_settings, double seconds) {
  // Disabled detail leaves the caller's block untouched. The caller must
  // initialize or clear per-draw detail fields before reusing a uniform block.
  if (!enabled(role, detail_settings))
    return;
  // Integer periodic frequencies in the water tile share this 2000-second
  // phase cycle. Wrapping cannot cause a visible jump, even after long play.
  uniform_block.detail = {float(role),
                          role == 3 ? detail_settings.cloud_strength
                                    : detail_settings.water_strength,
                          detail_settings.scale, 0};
  // Speed is relative to the default; the shader's offsets wrap in full tiles.
  const double travel = seconds * detail_settings.speed;
  uniform_block.detail_motion = {float(travel - std::floor(travel / 50) * 50),
                                 0, 0, 0};
}
} // namespace mw34::detail
