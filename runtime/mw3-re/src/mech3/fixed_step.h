#pragma once
#include <cstdint>
#include <functional>

// Ours (#485): the mission simulation runs in fixed 1/30 s steps, the original
// frame time its constants were tuned for, however fast frames are drawn.
// Each drawn frame feeds its real time in and runs the whole steps it has
// built up; what is left over is how far the drawn frame is towards the next
// step (alpha), which the scene blending uses (gamez/zclass/interp.h).
// docs/fixed-step.md has the whole picture.
namespace mech3 {

class FixedStep {
 public:
  static constexpr double kStepSeconds = 1.0 / 30.0;
  // The longest real frame counted (the timer's max_dt): a stall runs at most
  // 4 steps, then the game slows down instead of running ever more steps.
  static constexpr double kMaxFrameSeconds = 0.125;

  // Adds a drawn frame's real time and returns how many steps to run now.
  int feed(double frame_seconds);
  // How far the drawn frame is between the last step and the next, 0..1.
  float alpha() const;
  // Drops any time built up (a mission start, back from the pause menu).
  void reset();

 private:
  double pending_seconds_ = 0;
};

// Off with mw3 --variable-step: one simulation step per drawn frame, with the
// frame's own time, as before #485.
bool fixed_step_enabled();
void set_fixed_step_enabled(bool on);

FixedStep& mission_fixed_step();

// For the tests: run after each step a mission runs, so a test can act and
// look once per 1/30 s step (GameEngine::present_per_step). Unset in the game.
std::function<void()>& after_each_step();

}  // namespace mech3
