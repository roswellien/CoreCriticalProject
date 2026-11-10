#include "mech3/zai_hunt.h"

#include <cmath>

namespace mech3::ai {

namespace {
void copy3(float out[3], const float in[3]) {
  out[0] = in[0], out[1] = in[1], out[2] = in[2];
}
}  // namespace

// Ours (#287).
HuntGoal pick_hunt_goal(const HuntInput& in) {
  HuntGoal g;
  if (in.has_contact) {
    copy3(g.at, in.contact);
    g.rule = HuntRule::kContact;
    return g;
  }
  if (in.has_last_seen) {
    const float d = std::hypot(in.last_seen[0] - in.pos[0], in.last_seen[2] - in.pos[2]);
    if (d > kHuntReached) {
      copy3(g.at, in.last_seen);
      g.rule = HuntRule::kLastSeen;
      return g;
    }
    g.drop_last_seen = true;
  }
  copy3(g.at, in.fallback);
  g.rule = HuntRule::kFallback;
  return g;
}

}  // namespace mech3::ai
