#pragma once
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "mech3/replay_log.h"

// Ours (#289, docs/arena.md): a replay puppet, one logged mech drawn as the
// game's own mech. It is made by the AI mech path (skin, team masks and
// placing are the game's) on ReplayControls, so no pilot steers it, and the
// game's loop never updates it (the replay keeps it off update_entities).
// Each frame set() poses it from the log with the game's own animation
// code: the gait clip at the logged phase, or the logged action, then the
// torso, hip, legs and arms. The log wins over root motion: the position is
// written from it after the animation.
namespace mech3 {
struct Mech;
}

namespace mech3::replay {

class Puppet {
 public:
  // Null with *error when the chassis is unknown or the mech can't be made.
  static std::unique_ptr<Puppet> create(const std::string& chassis, int side, const MechPose& start,
                                        std::string* error);
  ~Puppet();
  Puppet(const Puppet&) = delete;
  Puppet& operator=(const Puppet&) = delete;

  // Pose it as `pose`, `lost` the part ids lost by then (ReplayLog::
  // parts_lost_by). `dt` is the replay time since the last set (at least
  // 1/240 s is used: the skis divide by it). `live` is a play forward (not a
  // seek): a part lost now flies off with the game's own effects, and a
  // mech destroyed now plays its death effect; a seek only hides lost parts.
  void set(const MechPose& pose, const std::vector<int>& lost, float dt, bool live = false);
  // Deleted and made again at `pose` (a seek backward, where lost parts
  // must come back).
  bool rebuild(const MechPose& pose, std::string* error);

  Mech* mech() const { return mech_; }
  // The part ids this puppet has taken off.
  const std::vector<int>& detached() const { return detached_; }

  // Whether the game takes off the part `id` when it is destroyed: arms and
  // hands (2, 3, 9, 10), thighs, calves and feet (4, 5, 11..14). Torso, side
  // torsos, head and hip kill the mech instead, shown by its fall.
  static bool detachable(int id);

 private:
  Puppet() = default;
  bool make(const MechPose& start, std::string* error);
  void free_mech();
  void place(const MechPose& pose);
  void detach(int id);
  void blow_off(int id);
  void explode(const std::string& action);
  void stop_effects();
  void play_action(const MechPose& pose, float dt);
  void play_gait(const MechPose& pose, float dt);

  int32_t roster_ = -1;
  std::string chassis_;
  int side_ = 0;
  Mech* mech_ = nullptr;
  std::string name_;
  std::string action_;  // the action being played, "" none
  std::vector<int> detached_;
  bool limp_started_ = false;
  bool was_standing_ = true;  // for the death effect: played once, as it falls
};

}  // namespace mech3::replay
