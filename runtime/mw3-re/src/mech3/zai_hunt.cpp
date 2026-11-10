#include "mech3/zai_hunt.h"

#include <cmath>
#include <memory>

#include "gamez/znetwork/znet_object.h"
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
std::unique_ptr<HuntNet> g_hunt_net;
}  // namespace

// Ours (#287).
HuntNet::HuntNet(const float point[3]) : CompiledNet(znet::alloc_id(500, 500, 600), 1) {
  copy3(fallback, point);
  auto* step = new HuntBehaviour();
  brain_hooks().on_new(0xc, step);
  elems.assign(1, step);
}

HuntNet* make_hunt_net(const float fallback[3]) {
  g_hunt_net = std::make_unique<HuntNet>(fallback);
  return g_hunt_net.get();
}
HuntNet* hunt_net() { return g_hunt_net.get(); }
void free_hunt_net() { g_hunt_net.reset(); }

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
    b.controls->set_throttle(0.0f);
    return;
  }
  const bool toward_enemy = goal.rule == HuntRule::kContact;
  float waypoint[3];
  const float reach = b.params.get<float>(0x28);
  const bool by_grid = nav.step(v, in.pos, goal.at, toward_enemy, reach, dt, waypoint);
  nav_drive(b, v, in.pos, by_grid ? waypoint : goal.at, &turn);
}

}  // namespace mech3::ai
