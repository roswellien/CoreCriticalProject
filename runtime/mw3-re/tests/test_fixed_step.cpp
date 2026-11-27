#include "check.h"
#include "gamez/zinput/zinput.h"
#include "mech3/fixed_step.h"

// #485 (docs/fixed-step.md): the mission simulation runs whole 1/30 s steps,
// so the same stretch of time gives the same steps however it is cut up.

namespace {
// Steps run for `seconds` of frames `frame_seconds` long.
int steps_over(double seconds, double frame_seconds) {
  mech3::FixedStep step;
  int total = 0;
  const int frames = static_cast<int>(seconds / frame_seconds + 0.5);
  for (int i = 0; i < frames; ++i) total += step.feed(frame_seconds);
  return total;
}
}  // namespace

TEST(fixed_step_runs_the_same_steps_at_30_60_144_and_240_hz) {
  EXPECT(steps_over(10.0, 1.0 / 30.0) == 300);
  EXPECT(steps_over(10.0, 1.0 / 60.0) == 300);
  EXPECT(steps_over(10.0, 1.0 / 240.0) == 300);
  // 1440 frames of 1/144 s are exactly 10 s.
  EXPECT(steps_over(10.0, 1.0 / 144.0) == 300);
}

TEST(fixed_step_caps_a_long_frame_at_four_steps) {
  mech3::FixedStep step;
  EXPECT(step.feed(1.0) == 3);  // 0.125 s counted: three whole steps, a part left
  EXPECT(step.feed(0.0) == 0);
  mech3::FixedStep fresh;
  EXPECT(fresh.feed(0.03) == 0);
  EXPECT(fresh.feed(5.0) == 4);  // 0.03 + 0.125 s: four steps at most from one frame's cap
}

TEST(fixed_step_alpha_and_reset) {
  mech3::FixedStep step;
  EXPECT(step.feed(1.0 / 60.0) == 0);
  EXPECT(step.alpha() > 0.49f && step.alpha() < 0.51f);
  EXPECT(step.feed(1.0 / 60.0) == 1);
  EXPECT(step.alpha() < 0.01f);
  step.feed(0.02);
  step.reset();
  EXPECT(step.alpha() == 0.0f);
  EXPECT(step.feed(0.0) == 0);
}

TEST(fixed_step_negative_frame_time_counts_as_none) {
  mech3::FixedStep step;
  EXPECT(step.feed(-1.0) == 0);
  EXPECT(step.alpha() == 0.0f);
}

// A drawn frame's code reads the buttons as one poll for the frame would leave
// them (zin::DrawnFrameInput): a press from an earlier of two polls is still a
// press, a frame with no poll sees a press once (then held) and a release once
// (then up), and after the frame the polls' own states come back.
TEST(fixed_step_drawn_frame_input_is_one_poll_a_frame) {
  constexpr int kKey = 0x1c;  // Enter
  zin::reset_state();
  zin::State& s = zin::state();
  // Two polls in the frame: pressed at the first, held at the second.
  zin::frame_input_begin();
  s.keys[kKey].state = zin::kPressed, s.mouse.left = zin::kPressed;
  zin::poll(false);
  s.keys[kKey].state = zin::kHeld, s.mouse.left = zin::kHeld;
  zin::poll(false);
  {
    zin::DrawnFrameInput view;
    EXPECT((zin::key_state(kKey) & zin::kPressed) != 0);
    EXPECT((s.mouse.left & zin::kPressed) != 0);
  }
  EXPECT(s.keys[kKey].state == zin::kHeld && s.mouse.left == zin::kHeld);
  // A frame with no poll after a press: held, not pressed again.
  zin::frame_input_begin();
  s.keys[kKey].state = zin::kPressed;
  {
    zin::DrawnFrameInput view;
    EXPECT(zin::key_state(kKey) == zin::kHeld);
  }
  EXPECT(s.keys[kKey].state == zin::kPressed);
  // One poll with a tap (pressed and let go): read as polled.
  zin::frame_input_begin();
  s.keys[kKey].state = zin::kPressed | zin::kReleased;
  zin::poll(false);
  {
    zin::DrawnFrameInput view;
    EXPECT(zin::key_state(kKey) == (zin::kPressed | zin::kReleased));
  }
  // A frame with no poll after a release: up.
  zin::frame_input_begin();
  {
    zin::DrawnFrameInput view;
    EXPECT(zin::key_state(kKey) == 0);
  }
  zin::reset_state();
}
