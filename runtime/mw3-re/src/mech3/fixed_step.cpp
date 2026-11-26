#include "mech3/fixed_step.h"

#include <algorithm>

namespace mech3 {

namespace {
bool g_enabled = true;
}  // namespace

int FixedStep::feed(double frame_seconds) {
  const double counted = std::clamp(frame_seconds, 0.0, kMaxFrameSeconds);
  pending_seconds_ += counted;
  int steps = 0;
  // A tiny allowance, so 30 frames of exactly 1/30 s each run 30 steps even
  // when the sum lands a rounding error below a whole step.
  const double whole_step = kStepSeconds - 1e-9;
  while (pending_seconds_ >= whole_step) {
    pending_seconds_ = std::max(0.0, pending_seconds_ - kStepSeconds);
    ++steps;
  }
  return steps;
}

float FixedStep::alpha() const {
  return static_cast<float>(std::clamp(pending_seconds_ / kStepSeconds, 0.0, 1.0));
}

void FixedStep::reset() { pending_seconds_ = 0; }

bool fixed_step_enabled() { return g_enabled; }
void set_fixed_step_enabled(bool on) { g_enabled = on; }

FixedStep& mission_fixed_step() {
  static FixedStep step;
  return step;
}

}  // namespace mech3
