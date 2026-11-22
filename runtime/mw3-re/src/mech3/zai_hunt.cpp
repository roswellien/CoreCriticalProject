#include "mech3/zai_hunt.h"

#include <cmath>

#include "gamez/znetwork/znet_object.h"
#include "gamez/zutil/zfix.h"
#include "mech3/zai_target.h"

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

namespace {
// znet owns the net: a mission's end (znet::clear, mission.cpp) deletes every
// object under id 10000, this one included. So the net is kept as a pointer
// with its id, and counts only while znet still holds it, as
// BrainHooks::formation_net does.
HuntNet* g_hunt_net = nullptr;
int32_t g_hunt_id = -1;
}  // namespace

// Ours (#287).
HuntNet::HuntNet(const float point[3]) : CompiledNet(znet::alloc_id(500, 500, 600), 1) {
  copy3(fallback, point);
  auto* step = new HuntBehaviour();
  brain_hooks().on_new(0xc, step);
  elems.assign(1, step);
}

HuntNet* hunt_net() { return g_hunt_net && znet::find(g_hunt_id) == g_hunt_net ? g_hunt_net : nullptr; }

void free_hunt_net() {
  delete hunt_net();
  g_hunt_net = nullptr;
}

HuntNet* make_hunt_net(const float fallback[3]) {
  free_hunt_net();
  g_hunt_net = new HuntNet(fallback);
  g_hunt_id = g_hunt_net->get_id();
  return g_hunt_net;
}

// Ours (#287): toward the goal by the grid when the straight way is blocked,
// else straight at it; stopped once at the fallback point with nothing known.
// The engage gate (zai_brain.cpp, may_engage) pushes the stock fight on top
// once an enemy is in attack range, and this runs again when that ends.
void HuntState::run(float dt) {
  BrainHooks& h = brain_hooks();
  Brain& b = *order->owner;
  const zgame::Handle v = b.controls->vehicle();
  auto* net = dynamic_cast<HuntNet*>(order->net ? order->net->net() : nullptr);
  if (!net) {
    order->pop();
    return;
  }

  HuntInput in;
  h.position(v, in.pos);
  const Contact* enemy = h.pick(v, kEnemy);
  const zgame::Handle enemy_vehicle = enemy ? h.contact_vehicle(enemy) : 0;
  if (enemy_vehicle) {
    in.has_contact = true;
    h.position(enemy_vehicle, in.contact);
    has_last_seen = true;
    copy3(last_seen, in.contact);
  }
  in.has_last_seen = has_last_seen;
  copy3(in.last_seen, last_seen);
  copy3(in.fallback, net->fallback);

  goal = pick_hunt_goal(in);
  if (goal.drop_last_seen) has_last_seen = false;

  const bool resting = goal.rule == HuntRule::kFallback &&
                       std::hypot(goal.at[0] - in.pos[0], goal.at[2] - in.pos[2]) <= kHuntReached;
  if (resting) {
    // The controls keep their last turn, so a bot that arrives turning would
    // spin on the spot.
    b.controls->set_throttle(0.0f);
    b.controls->set_turn(0.0f);
    return;
  }
  const bool toward_enemy = goal.rule == HuntRule::kContact;
  float waypoint[3];
  // The preset's arrival distance (+0x28, squared at read, as zai_attack.cpp's
  // follow state uses it): the grid counts a waypoint reached within it.
  const float reach = b.params.get<float>(0x28);
  // The grid is ours behind the improved AI switch, as the follow state's
  // (zai_attack.cpp); an arena run turns it on (mw3_main.cpp), so in a match it is on.
  by_grid = zfix::options().improved_ai && nav.step(v, in.pos, goal.at, toward_enemy, reach, dt, waypoint);
  copy3(steer_to, by_grid ? waypoint : goal.at);
  nav_drive(b, v, in.pos, steer_to, &turn);
}

}  // namespace mech3::ai
