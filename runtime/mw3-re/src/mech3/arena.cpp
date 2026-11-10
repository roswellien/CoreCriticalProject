#include "mech3/arena.h"

#include <cstdio>
#include <cstring>
#include <string>

#include "mech3/app_mech.h"
#include "mech3/mech.h"
#include "mech3/mech_control.h"
#include "mech3/mech_net.h"
#include "mech3/zai_hunt.h"
#include "mech3/zrdraiv.h"

namespace mech3::arena {

namespace {
const Setup* g_setup = nullptr;

// The hunt's fallback point: the mean of the map's 16 spawn spots, roughly
// the middle of where anyone can be. False when the map lacks one (the
// setup check refuses such maps, so only a broken install gets here).
bool spawn_spots_mean(float out[3]) {
  const NetCalls& calls = net_calls();
  if (!calls.spawn_point) return false;
  float sum[3] = {};
  for (int spot = 0; spot < kSpawnSpots; ++spot) {
    const std::string name = "remote_" + std::to_string(spot);
    float pos[3], yaw = 0;
    if (!calls.spawn_point(name.c_str(), pos, &yaw)) return false;
    for (int axis = 0; axis < 3; ++axis) sum[axis] += pos[axis];
  }
  for (int axis = 0; axis < 3; ++axis) out[axis] = sum[axis] / kSpawnSpots;
  return true;
}
}  // namespace

// Ours (#287): what --host does (mw3_main.cpp), with the hub's endpoint in
// place of the ENet transport, so the arena can never be found or joined.
znet::Transport* arena_open_session(znet::Hub& hub) {
  znet::Transport* endpoint = hub.endpoint();
  znet::session() = znet::Session{};
  znet::initialise(endpoint);
  znet::SessionDesc desc;
  desc.name = "Arena";
  desc.max_players = kArenaPlayers;
  if (!znet::host_session(desc, "Arena")) return nullptr;
  return endpoint;
}

void set_arena_setup(const Setup* setup) { g_setup = setup; }
const Setup* arena_setup() { return g_setup; }

// Ours (#287): the side A team is 1 and side B's 2, as team 0 is no one's
// ally or enemy (AiTarget::set_team).
bool arena_hand_host_to_ai(const Bot& bot) {
  auto* host = static_cast<Mech*>(mission_player_mech());
  if (!host || !bot.params_read) return false;
  float fallback[3];
  if (!spawn_spots_mean(fallback)) return false;
  // znet owns the net and the mission's end frees it, so a match never
  // walks on a net made for the one before.
  ai::HuntNet* net = ai::make_hunt_net(fallback);
  if (!net) return false;
  ai::AivRecord record;
  std::memcpy(record.raw, bot.params.data(), bot.params.size());
  const int32_t side_a_team = 1;
  record.put<int32_t>(0x18, side_a_team);  // AiParams::team()
  // The old PlayerControls are left as they are, not freed: the input's
  // command callback and the mission end still reach them through
  // player_controls_instance().
  void* controls = program_make_ai_mech_controls(static_cast<ai::AiNet*>(net), &record);
  if (!controls) return false;
  program_mech_set_controls(host, controls);
  host->set_team(side_a_team);
  return true;
}

HostState arena_host_state() {
  HostState state;
  auto* host = static_cast<Mech*>(mission_player_mech());
  if (!host) return state;
  state.team_mask = host->team;
  auto* controls = dynamic_cast<AiControls*>(host->controls);
  const ai::Brain* brain = controls ? controls->brain.get() : nullptr;
  if (!brain) return state;
  state.on_ai = true;
  // The brain's own order, then the stack a fight or other order pushes.
  state.hunting = dynamic_cast<const ai::HuntState*>(brain->order.state.get()) != nullptr;
  for (const ai::Order& order : brain->orders)
    if (dynamic_cast<const ai::HuntState*>(order.state.get())) state.hunting = true;
  return state;
}

bool arena_hunt_net_held() { return ai::hunt_net() != nullptr; }

void arena_start() {
  if (!g_setup || g_setup->sides[0].empty()) return;
  if (!arena_hand_host_to_ai(g_setup->sides[0].front()))
    std::fprintf(stderr, "mw3: arena: the host's mech could not be handed to the AI\n");
}

}  // namespace mech3::arena
