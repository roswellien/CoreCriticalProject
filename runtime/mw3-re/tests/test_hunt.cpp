// #287 (docs/arena.md): the arena bots' hunt order. Game-free: the goal choice,
// the net the engage gate asks, and the steering with the grid off (the grid
// reads the mission's real world, so the arena's end-to-end runs cover it).
#include <cmath>
#include <cstring>

#include "check.h"
#include "gamez/znetwork/znet_object.h"
#include "gamez/zutil/zfix.h"
#include "mech3/zai_hunt.h"
#include "mech3/zai_target.h"

namespace {
using namespace mech3::ai;

constexpr zgame::Handle kBot = 1;
constexpr zgame::Handle kEnemyMech = 2;

struct HuntControls : BrainControls {
  float throttle = -1, turn = 0;
  zgame::Handle vehicle() override { return kBot; }
  void stop() override {}
  void smooth(float) override {}
  bool hit_lately() override { return false; }
  void fire(bool) override {}
  bool reversing() override { return false; }
  float throttle_now() override { return throttle; }
  void set_throttle(float t) override { throttle = t; }
  void set_turn(float t) override { turn = t; }
  void set_jump(float) override {}
  void set_jet_forward(float) override {}
  float turn_goal() override { return 0; }
  void aim_started() override {}
};

// The bot at the origin facing +x; the enemy wherever the test puts it.
struct HuntHooks : BrainHooks {
  float bot[3] = {0, 0, 0};
  float enemy_at[3] = {200, 0, 0};
  bool enemy_seen = true;
  Contact contact;
  uint32_t unported(const char*, std::initializer_list<zgame::Arg>) override { return 0; }
  void position(zgame::Handle v, float out[3]) override {
    std::memcpy(out, v == kEnemyMech ? enemy_at : bot, 12);
  }
  void forward(zgame::Handle, float* x, float* z) override { *x = 1, *z = 0; }
  Contact* pick(zgame::Handle, int32_t side) override {
    return side == kEnemy && enemy_seen ? &contact : nullptr;
  }
  zgame::Handle contact_vehicle(const Contact* c) override { return c ? kEnemyMech : 0; }
};

void set3(float out[3], float x, float y, float z) { out[0] = x, out[1] = y, out[2] = z; }
}  // namespace

TEST(arena_hunt_goal_contact_then_last_seen_then_fallback) {
  HuntInput in;
  set3(in.fallback, 500, 0, 500);
  in.has_contact = true;
  set3(in.contact, 100, 0, 0);
  in.has_last_seen = true;
  set3(in.last_seen, 300, 0, 0);
  HuntGoal g = pick_hunt_goal(in);
  EXPECT(g.rule == HuntRule::kContact && g.at[0] == 100);
  in.has_contact = false;
  g = pick_hunt_goal(in);
  EXPECT(g.rule == HuntRule::kLastSeen && g.at[0] == 300 && !g.drop_last_seen);
  in.has_last_seen = false;
  g = pick_hunt_goal(in);
  EXPECT(g.rule == HuntRule::kFallback && g.at[0] == 500 && g.at[2] == 500);
}

TEST(arena_hunt_last_seen_dropped_once_reached) {
  HuntInput in;
  set3(in.fallback, 500, 0, 500);
  in.has_last_seen = true;
  set3(in.last_seen, 20, 0, 0);  // within kHuntReached of the bot at the origin
  const HuntGoal g = pick_hunt_goal(in);
  EXPECT(g.rule == HuntRule::kFallback && g.drop_last_seen);
}

TEST(arena_hunt_net_allows_the_engage_gate) {
  HuntHooks hooks;
  set_brain_hooks(&hooks);
  {
    const float fallback[3] = {0, 0, 0};
    HuntNet* net = make_hunt_net(fallback);
    EXPECT(net && hunt_net() == net && net->allows_attack());
    EXPECT(net->id >= 500 && net->id < 600);

    // The stock gate lets a bot hunting on this net break in to fight, once
    // its engage switch (+0x3c) is on, and not before.
    BuiltinNet start(7, 0);
    AiParams rec;
    Brain b(&start, rec);
    Order& o = b.order;
    o.owner = &b;
    o.net.reset(net->make_part(o));
    o.state.reset(net->step()->make_state(o));
    b.params.put<int32_t>(0x3c, 0);
    EXPECT(!b.may_engage(kBot, net, o.state.get()));
    b.params.put<int32_t>(0x3c, 1);
    EXPECT(b.may_engage(kBot, net, o.state.get()));
    o.state.reset();
    o.net.reset();
    free_hunt_net();
    EXPECT(hunt_net() == nullptr);
  }
  set_brain_hooks(nullptr);
}

// A mission's end runs znet::clear, which deletes every net under id 10000,
// ours included: the hunt net must not be freed a second time afterwards, and
// the next mission must get a fresh one.
TEST(arena_hunt_net_survives_znet_clear) {
  const float fallback[3] = {0, 0, 0};
  make_hunt_net(fallback);
  znet::clear();
  EXPECT(hunt_net() == nullptr);
  free_hunt_net();  // nothing left to free
  EXPECT(hunt_net() == nullptr);

  make_hunt_net(fallback);
  znet::clear();
  HuntNet* next = make_hunt_net(fallback);  // the next mission's
  EXPECT(next && hunt_net() == next && next->allows_attack());
  free_hunt_net();
  EXPECT(hunt_net() == nullptr && znet::find(500) == nullptr);
}

TEST(arena_hunt_drives_to_the_enemy_then_where_it_was_seen) {
  HuntHooks hooks;
  set_brain_hooks(&hooks);
  const bool improved_ai = zfix::options().improved_ai;
  zfix::options().improved_ai = false;  // the grid off: straight at the goal
  {
    const float fallback[3] = {0, 0, -400};
    HuntNet* net = make_hunt_net(fallback);
    BuiltinNet start(7, 0);
    AiParams rec;
    Brain b(&start, rec);
    HuntControls c;
    b.controls = &c;
    Order& o = b.order;
    o.owner = &b;
    o.net.reset(net->make_part(o));
    o.state.reset(net->step()->make_state(o));
    auto* hunt = dynamic_cast<HuntState*>(o.state.get());
    EXPECT(hunt != nullptr);

    // The enemy 200 m dead ahead: full throttle, no turn.
    hunt->run(1.0f / 30);
    EXPECT(hunt->goal.rule == HuntRule::kContact && c.throttle > 0.9f && std::fabs(c.turn) < 0.01f);

    // Lost from the sensors: on to where it was last seen.
    hooks.enemy_seen = false;
    hunt->run(1.0f / 30);
    EXPECT(hunt->goal.rule == HuntRule::kLastSeen && hunt->goal.at[0] == 200 && c.throttle > 0.9f);

    // Standing on that place: dropped, and on to the fallback point behind
    // (-z), which is not ahead, so it turns before it walks.
    set3(hooks.bot, 195, 0, 0);
    hunt->run(1.0f / 30);
    EXPECT(hunt->goal.rule == HuntRule::kFallback && !hunt->has_last_seen && c.throttle == 0.0f && c.turn != 0.0f);

    // At the fallback point: stopped, and no longer turning from the last
    // frame's steering (the controls keep what they were last given).
    set3(hooks.bot, 0, 0, -390);
    hunt->run(1.0f / 30);
    EXPECT(hunt->goal.rule == HuntRule::kFallback && c.throttle == 0.0f && c.turn == 0.0f);

    o.state.reset();
    o.net.reset();
    free_hunt_net();
  }
  zfix::options().improved_ai = improved_ai;
  set_brain_hooks(nullptr);
}
