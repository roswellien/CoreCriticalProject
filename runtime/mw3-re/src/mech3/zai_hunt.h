#pragma once

#include "mech3/zai_attack.h"
#include "mech3/zai_brain.h"
#include "mech3/zai_steps.h"

// Ours, not the exe's (#287, docs/arena.md): the hunt order that arena bots
// run on multiplayer maps, which ship no AI route nets. A bot walks toward the
// nearest enemy it knows of, by the grid (zai_nav), and the stock engage gate
// and fight take over in range. Nothing outside the arena uses it.

namespace mech3::ai {

// What the goal is picked from. Places are world x, y, z.
struct HuntInput {
  float pos[3] = {};          // the bot
  bool has_contact = false;   // the nearest enemy contact, when there is one
  float contact[3] = {};
  bool has_last_seen = false;  // where the last enemy it had was seen
  float last_seen[3] = {};
  float fallback[3] = {};     // the caller's point when nothing is known
};

enum class HuntRule { kContact, kLastSeen, kFallback };

struct HuntGoal {
  float at[3] = {};
  HuntRule rule = HuntRule::kFallback;
  bool drop_last_seen = false;  // the bot has reached the last-seen place
};

// A last-seen place counts as reached within this flat distance (m).
constexpr float kHuntReached = 30.0f;

// The contact, else the last-seen place until the bot is within
// kHuntReached of it, else the fallback point.
HuntGoal pick_hunt_goal(const HuntInput& in);

// One bot's hunt, owned by its order. Keeps what one bot needs between
// frames: the last enemy's last-seen place and its grid way.
class HuntState : public BehaviourState {
 public:
  HuntState(Order* o, Behaviour* b) : BehaviourState(o, b) {}
  void run(float dt) override;

  HuntGoal goal;                // this frame's, for the match log and the tests
  bool has_last_seen = false;
  float last_seen[3] = {};
  NavWay nav;
  float turn = 0;               // kept frame to frame, as the follow's crumbs
};

// The hunt's one step: every order on the hunt net runs a HuntState.
struct HuntBehaviour : Behaviour {
  BehaviourState* make_state(Order& o) override { return new HuntState(&o, this); }
};

// One net shared by every bot, as the game shares one formation net. It holds
// no bot's data, only the fallback point for the whole map. Its id is znet's
// first free in 500..599: 300..399 are the vehicles' own nets, 400..499 the
// net editor's.
class HuntNet : public CompiledNet {
 public:
  explicit HuntNet(const float fallback[3]);
  HuntBehaviour* step() const { return static_cast<HuntBehaviour*>(elems[0]); }

  float fallback[3] = {};
};

// The shared net: made at an arena mission's start. znet owns it, so the
// mission's end (znet::clear) frees it too: hunt_net() is null from then on,
// free_hunt_net() is safe either way, and making one frees any still held.
HuntNet* make_hunt_net(const float fallback[3]);
HuntNet* hunt_net();
void free_hunt_net();

}  // namespace mech3::ai
