#pragma once
// #289 (plan step 4): the replay puppet's checks inside a running arena
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

}  // namespace replay_game
