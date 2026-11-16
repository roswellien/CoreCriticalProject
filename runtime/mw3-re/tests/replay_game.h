#pragma once
// #289: the replay puppet's checks inside a running arena
// match. They live in test_replay_game.cpp, which can include the mech
// headers (test_program.cpp's own Handle type clashes with them); the arena
// harness in test_program.cpp calls frame() from each Core frame.
#include <memory>

namespace replay_game {

struct PuppetResults {
  bool made = false;
  double create_ms = 0;
  int samples = 0, close_feet = 0, close_angles = 0;
  float worst = 0;  // meters, the largest foot or hip difference seen
  bool part_off = false, kept_off = false;
  bool collapsed = false, never_died = true, armor_kept = false;
};

class PuppetProbe {
 public:
  PuppetProbe();
  ~PuppetProbe();
  // Each Core frame, from 1. The probe frees its puppets at `last_frame`,
  // before the mission ends.
  void frame(int frame, int last_frame);
  const PuppetResults& results() const;

 private:
  struct State;
  std::unique_ptr<State> s_;
};

// #289: the 3D replay's frame branch in a running arena match.
// From `from` for `frames` Core frames a test ReplayHooks is set, stepping a
// replay clock of its own; the probe checks nothing is simulated meanwhile.
struct FrameResults {
  int frames = 0;          // frames run with the hooks set
  int mechs_moved = 0;     // frames where any arena mech moved or its gait ran
  int time_off_clock = 0;  // frames where game time was not the replay clock
  int clock_not_real = 0;  // frames where the frame clock was not real time after the frame
  int before = 0, after = 0;  // the hooks' calls
};

class FrameProbe {
 public:
  // `hooks_on` false makes it a control run: the same checks, nothing set.
  FrameProbe(int from, int frames, bool hooks_on = true);
  ~FrameProbe();
  void frame(int frame);
  const FrameResults& results() const;

 private:
  struct State;
  std::unique_ptr<State> s_;
};

}  // namespace replay_game
