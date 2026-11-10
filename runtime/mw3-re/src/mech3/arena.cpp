#include "mech3/arena.h"

#include <algorithm>
#include <cstdio>
#include <cstring>
#include <deque>
#include <string>

#include "mech3/app_mech.h"
#include "mech3/mech.h"
#include "mech3/mech_control.h"
#include "mech3/mech_net.h"
#include "mech3/zai_attack.h"
#include "mech3/zai_hunt.h"
#include "mech3/zrdraiv.h"

namespace mech3::arena {

namespace {
const Setup* g_setup = nullptr;
std::vector<ArenaMech> g_mechs;
// The bots' names, kept for the match: a mech may hold its name's pointer.
std::deque<std::string> g_names;

// The map's 16 spawn spots (remote_0 .. remote_15): their places and yaws.
// False when the map lacks one (the setup check refuses such maps, so only a
// broken install gets here).
bool read_spawn_spots(float pos[kSpawnSpots][3], float yaw[kSpawnSpots]) {
  const NetCalls& calls = net_calls();
  if (!calls.spawn_point) return false;
  for (int spot = 0; spot < kSpawnSpots; ++spot) {
    const std::string name = "remote_" + std::to_string(spot);
    if (!calls.spawn_point(name.c_str(), pos[spot], &yaw[spot])) return false;
  }
  return true;
}

// The hunt's fallback point: the mean of the spawn spots, roughly the middle
// of where anyone can be.
void spawn_spots_mean(const float pos[kSpawnSpots][3], float out[3]) {
  float sum[3] = {};
  for (int spot = 0; spot < kSpawnSpots; ++spot)
    for (int axis = 0; axis < 3; ++axis) sum[axis] += pos[spot][axis];
  for (int axis = 0; axis < 3; ++axis) out[axis] = sum[axis] / kSpawnSpots;
}

float squared_distance(const float a[3], const float b[3]) {
  float sum = 0;
  for (int axis = 0; axis < 3; ++axis) sum += (a[axis] - b[axis]) * (a[axis] - b[axis]);
  return sum;
}

// The host's mech on AI controls over the hunt net.
bool hand_host_to_ai(const Bot& bot, ai::HuntNet* net, const float pos[3], float yaw) {
  auto* host = static_cast<Mech*>(mission_player_mech());
  if (!host || !bot.params_read || !net) return false;
  ai::AivRecord record;
  const int side_a = 0;
  arena_bot_params(bot, side_a, pos, yaw, &record);
  // The old PlayerControls are left as they are, not freed: the input's
  // command callback and the mission end still reach them through
  // player_controls_instance().
  void* controls = program_make_ai_mech_controls(static_cast<ai::AiNet*>(net), &record);
  if (!controls) return false;
  program_mech_set_controls(host, controls);
  host->set_team(record.team());
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

// A match's mechs die with its mission, so the list is emptied whenever a
// match is set or cleared: nothing reads a mech the last mission freed
// before arena_start fills the list again at the first Core frame.
void set_arena_setup(const Setup* setup) {
  g_setup = setup;
  g_mechs.clear();
  g_names.clear();
}
const Setup* arena_setup() { return g_setup; }

// Ours (#287)
std::vector<int> arena_spawn_spots(const float spots[kSpawnSpots][3], int side_a, int side_b) {
  std::vector<int> free_spots;
  for (int spot = 0; spot < kSpawnSpots; ++spot)
    if (spot != kHostSpot) free_spots.push_back(spot);
  const float* host = spots[kHostSpot];
  // Nearest first, the lower spot first on a tie.
  std::stable_sort(free_spots.begin(), free_spots.end(), [&](int a, int b) {
    return squared_distance(spots[a], host) < squared_distance(spots[b], host);
  });
  std::vector<int> chosen;
  if (side_a <= 0) return chosen;
  chosen.push_back(kHostSpot);
  const int side_a_others = side_a - 1;
  for (int i = 0; i < side_a_others; ++i) chosen.push_back(free_spots[i]);
  free_spots.erase(free_spots.begin(), free_spots.begin() + side_a_others);
  // Farthest first, the lower spot first on a tie.
  std::stable_sort(free_spots.begin(), free_spots.end(), [&](int a, int b) {
    return squared_distance(spots[a], host) > squared_distance(spots[b], host);
  });
  for (int i = 0; i < side_b; ++i) chosen.push_back(free_spots[i]);
  return chosen;
}

// Ours (#287): the side A team is 1 and side B's 2, as team 0 is no one's
// ally or enemy (AiTarget::set_team).
void arena_bot_params(const Bot& bot, int side, const float pos[3], float yaw, ai::AiParams* params) {
  std::memcpy(params->raw, bot.params.data(), bot.params.size());
  params->put<float>(0x08, pos[0]);
  params->put<float>(0x0c, pos[1]);
  params->put<float>(0x10, pos[2]);
  params->put<float>(0x14, yaw);
  params->put<int32_t>(0x18, side + 1);  // AiParams::team()
  params->put<int32_t>(0xbc, 0);         // the configuration create_ai_mech builds: the first
  params->put<int32_t>(0x3c, 1);         // may_engage's switch
  // Always awake (Brain::frame skips its sleep check at +0x88 == 1): a stock
  // pilot sleeps, and its mech stands frozen, while its nearest enemy is past
  // its sight range (+0x1c), which on a multiplayer map is from the start. The
  // hunt is what brings a bot within sight, so it must run from the first frame.
  params->put<int32_t>(0x88, 1);
  params->put<int32_t>(0x8c, 0);  // any enemy, not only the player
}

// Ours (#287)
bool arena_hand_host_to_ai(const Bot& bot) {
  float pos[kSpawnSpots][3], yaw[kSpawnSpots];
  if (!read_spawn_spots(pos, yaw)) return false;
  float fallback[3];
  spawn_spots_mean(pos, fallback);
  // znet owns the net and the mission's end frees it, so a match never
  // walks on a net made for the one before.
  return hand_host_to_ai(bot, ai::make_hunt_net(fallback), pos[kHostSpot], yaw[kHostSpot]);
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

const std::vector<ArenaMech>& arena_mechs() { return g_mechs; }

const ai::AiParams* arena_brain_params(const Mech* mech) {
  auto* controls = mech ? dynamic_cast<AiControls*>(mech->controls) : nullptr;
  const ai::Brain* brain = controls ? controls->brain.get() : nullptr;
  return brain ? &brain->params : nullptr;
}

// Ours (#287)
void arena_start() {
  // What a run before this one in the same process left behind.
  g_mechs.clear();
  g_names.clear();
  ai::nav_frame_reset();
  if (!g_setup || g_setup->sides[0].empty()) return;

  float pos[kSpawnSpots][3], yaw[kSpawnSpots];
  if (!read_spawn_spots(pos, yaw)) {
    std::fprintf(stderr, "mw3: arena: the map's spawn spots could not be read\n");
    return;
  }
  float fallback[3];
  spawn_spots_mean(pos, fallback);
  ai::HuntNet* net = ai::make_hunt_net(fallback);
  const std::vector<Bot>& side_a = g_setup->sides[0];
  const std::vector<Bot>& side_b = g_setup->sides[1];
  if (!hand_host_to_ai(side_a.front(), net, pos[kHostSpot], yaw[kHostSpot])) {
    std::fprintf(stderr, "mw3: arena: the host's mech could not be handed to the AI\n");
    return;
  }
  const std::vector<int> spots =
      arena_spawn_spots(pos, static_cast<int>(side_a.size()), static_cast<int>(side_b.size()));
  ArenaMech host;
  host.mech = static_cast<Mech*>(mission_player_mech());
  host.id = 0, host.side = 0, host.spot = kHostSpot;
  g_mechs.push_back(host);

  int id = 0;
  for (int side = 0; side < kSides; ++side) {
    const std::vector<Bot>& bots = g_setup->sides[side];
    for (size_t i = 0; i < bots.size(); ++i, ++id) {
      if (id == 0) continue;  // the host's mech, made by the launch
      const int spot = spots[static_cast<size_t>(id)];
      ai::AivRecord record;
      arena_bot_params(bots[i], side, pos[spot], yaw[spot], &record);
      g_names.push_back("arena_" + std::string(side == 0 ? "a" : "b") + "_" + std::to_string(i));
      auto* mech = static_cast<Mech*>(
          program_create_ai_mech(bots[i].mech, g_names.back().c_str(), static_cast<ai::AiNet*>(net), &record));
      if (!mech) {
        std::fprintf(stderr, "mw3: arena: bot %d (%s) could not be made\n", id, bots[i].mech_name.c_str());
        continue;
      }
      mech->arena_bot = true;
      mech->set_team(side + 1);
      ArenaMech entry;
      entry.mech = mech, entry.id = id, entry.side = side, entry.spot = spot;
      g_mechs.push_back(entry);
    }
  }
}

}  // namespace mech3::arena
