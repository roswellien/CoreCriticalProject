#include "mech3/arena.h"

#include <algorithm>
#include <cstdio>
#include <cstring>
#include <deque>
#include <string>

#include "mech3/app_mech.h"
#include "mech3/app_view.h"
#include "mech3/arena_log.h"
#include "mech3/mech.h"
#include "mech3/mech_control.h"
#include "mech3/mech_lod.h"
#include "mech3/mech_net.h"
#include "mech3/weapon.h"
#include "mech3/zai_attack.h"
#include "mech3/zai_hunt.h"
#include "mech3/zrdraiv.h"

namespace mech3::arena {

namespace {
const Setup* g_setup = nullptr;
std::vector<ArenaMech> g_mechs;
// The bots' names, kept for the match: a mech may hold its name's pointer.
std::deque<std::string> g_names;
// The match's clock and result: started at the first Core frame.
bool g_started = false;
float g_start_time = 0;
int64_t g_seed = 0;
Result g_result;

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

// The bot the spectator's view follows (an index into g_mechs), -1 for none.
int g_viewed = -1;

// The view on g_mechs[index]: the godseye camera (3) on it, and the HUD's
// player pointer (world().player) with it, never the mission player. The
// weapons' own player (weapon_world().player) stays null: it changes how the
// player's weapons fire (a wider beam-snap cone on a wide view, cone_cos; one
// arm's weapons in a side view, arm_restriction), so a viewed bot would fire
// differently from the rest.
void view_mech(int index) {
  Mech* mech = g_mechs[static_cast<size_t>(index)].mech;
  g_viewed = index;
  program_view_attach(*mech);
  program_view_set_camera(3);
  world().player = mech;
}

// The view's bot cleared, so no pointer outlives the match's mechs.
void view_clear() {
  if (g_viewed >= 0) world().player = nullptr;
  g_viewed = -1;
}

// The first standing bot after `from` in setup order, wrapping round; -1
// when none stands.
int next_standing(int from) {
  const int count = static_cast<int>(g_mechs.size());
  for (int step = 1; step <= count; ++step) {
    const int index = (from + step + count) % count;
    if (g_mechs[static_cast<size_t>(index)].mech->active) return index;
  }
  return -1;
}

// Each frame: a fallen viewed bot hands the view on.
void view_follow() {
  const bool viewed_standing = g_viewed >= 0 && g_mechs[static_cast<size_t>(g_viewed)].mech->active;
  if (viewed_standing) return;
  const int next = next_standing(g_viewed < 0 ? -1 : g_viewed);
  if (next >= 0 && next != g_viewed) view_mech(next);
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
  if (g_started && !g_result.decided) log_match_stop();  // the shot and hit hooks off
  g_setup = setup;
  lod_calls().same_detail_for_all = false;  // stock until a match starts
  world().arena_side_a_team = 0, world().arena_side_a_enemies = 0;  // the AMS's stock rule
  world().arena_spectating = false;
  view_clear();
  g_mechs.clear();
  g_names.clear();
  g_started = false;
  // The last match's result stays readable after it is cleared; a new one starts blank.
  if (setup) g_result = Result{};
}

const Result& arena_result() { return g_result; }
void set_arena_seed(int64_t seed) { g_seed = seed; }
float arena_match_time() { return g_started ? world().time - g_start_time : 0.0f; }

// Ours (#287)
std::string arena_result_line(const Result& result) {
  const char* winner = result.winner == 0 ? "A" : result.winner == 1 ? "B" : "draw";
  const int whole_seconds = static_cast<int>(result.time);
  char line[96];
  std::snprintf(line, sizeof line, "arena: winner %s, time %d:%02d, lost A %d B %d", winner, whole_seconds / 60,
                whole_seconds % 60, result.lost[0], result.lost[1]);
  return line;
}

// Ours (#287)
void arena_tick() {
  if (!g_setup || !g_started || g_result.decided || g_mechs.empty()) return;
  view_follow();
  int standing[kSides] = {};
  int lost[kSides] = {};
  for (const ArenaMech& entry : g_mechs) {
    if (entry.mech->active) ++standing[entry.side];
    else ++lost[entry.side];
  }
  const float match_time = world().time - g_start_time;
  log_match_frame(match_time, g_mechs);
  const bool out_of_time = match_time >= static_cast<float>(g_setup->minutes) * 60.0f;
  const bool side_wiped_out = standing[0] == 0 || standing[1] == 0;
  if (!side_wiped_out && !out_of_time) return;

  g_result.decided = true;
  g_result.time = match_time;
  g_result.lost[0] = lost[0];
  g_result.lost[1] = lost[1];
  // Elimination and the time limit both come down to who has more standing:
  // a wiped-out side has none.
  if (standing[0] > standing[1]) g_result.winner = 0;
  else if (standing[1] > standing[0]) g_result.winner = 1;
  else g_result.winner = -1;
  std::printf("%s\n", arena_result_line(g_result).c_str());
  std::fflush(stdout);
  log_match_end(g_result);

  // The stock end (net_mech_tick) would end the match again when its clock
  // runs out: marked ended already, with its exit time never reached.
  const NetCalls& calls = net_calls();
  if (NetGameFields* game = calls.game ? calls.game() : nullptr) {
    if (game->end_state) *game->end_state = 3;
    if (game->end_time) *game->end_time = 3.4e38f;
  }
  if (calls.game_over) calls.game_over();
  else net_game_over();
}
const Setup* arena_setup() { return g_setup; }

// Ours (#287)
std::vector<int> arena_spawn_spots(const float spots[kSpawnSpots][3], int side_a, int side_b, int64_t seed) {
  // Every pair of spots, farthest apart first; a tie keeps the lower spots first.
  struct Pair {
    int first, second;
    float apart;
  };
  std::vector<Pair> pairs;
  for (int a = 0; a < kSpawnSpots; ++a)
    for (int b = a + 1; b < kSpawnSpots; ++b) pairs.push_back({a, b, squared_distance(spots[a], spots[b])});
  std::stable_sort(pairs.begin(), pairs.end(), [](const Pair& x, const Pair& y) { return x.apart > y.apart; });
  // The seed picks the pair and which end is side A's, the same way every
  // run, so a match replays exactly.
  const uint64_t pick = static_cast<uint64_t>(seed < 0 ? -seed : seed);
  const Pair& ends = pairs[pick % kAnchorChoices];
  const bool flipped = (pick / kAnchorChoices) % 2 == 1;
  const int side_ends[kSides] = {flipped ? ends.second : ends.first, flipped ? ends.first : ends.second};

  std::vector<int> chosen;
  bool taken[kSpawnSpots] = {};
  const int counts[kSides] = {side_a, side_b};
  for (int side = 0; side < kSides; ++side) {
    // The free spots nearest this side's end (the end itself first, at 0).
    std::vector<int> free_spots;
    for (int spot = 0; spot < kSpawnSpots; ++spot)
      if (!taken[spot]) free_spots.push_back(spot);
    const float* end = spots[side_ends[side]];
    std::stable_sort(free_spots.begin(), free_spots.end(), [&](int a, int b) {
      return squared_distance(spots[a], end) < squared_distance(spots[b], end);
    });
    for (int i = 0; i < counts[side] && i < static_cast<int>(free_spots.size()); ++i) {
      chosen.push_back(free_spots[static_cast<size_t>(i)]);
      taken[free_spots[static_cast<size_t>(i)]] = true;
    }
  }
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
  // Never the player's lancemate: +0xcd bit 0 makes a pilot one, bit 1 makes
  // it one while it is the player's ally (sensors.cpp, AiTarget +0xbc bit 4).
  // A preset with bit 1 would have a bot fall in behind a player (the stock
  // follow) instead of hunting.
  params->raw[0xcd] = static_cast<uint8_t>(params->raw[0xcd] & ~0x3u);
}

// Ours (#287)
Mech* arena_viewed_mech() {
  return g_viewed >= 0 ? g_mechs[static_cast<size_t>(g_viewed)].mech : nullptr;
}

// Ours (#287)
bool arena_view_next() {
  if (!g_started || g_mechs.empty()) return false;
  const int next = next_standing(g_viewed);
  if (next < 0) return false;
  view_mech(next);
  return true;
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
  view_clear();
  world().arena_side_a_team = 0, world().arena_side_a_enemies = 0;
  world().arena_spectating = !world().mission_player;
  set_update_order_seed(static_cast<uint32_t>(g_seed));  // the update order replays with the match
  g_mechs.clear();
  g_names.clear();
  g_result = Result{};
  g_started = false;
  ai::nav_frame_reset();
  if (!g_setup || g_setup->sides[0].empty()) return;
  g_start_time = world().time;

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
  const std::vector<int> spots =
      arena_spawn_spots(pos, static_cast<int>(side_a.size()), static_cast<int>(side_b.size()), g_seed);
  // Every fighter is an ordinary bot: the host's seat has no mech
  // (launch_spectator), so no player-only rule runs for anyone.
  for (int side = 0; side < kSides; ++side) {
    const std::vector<Bot>& bots = g_setup->sides[side];
    for (size_t i = 0; i < bots.size(); ++i) {
      const int id = side == 0 ? static_cast<int>(i) : static_cast<int>(side_a.size() + i);
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
      mech->set_team(record.team());
      // Side A's masks stand in for the missing player's in the AMS and the
      // shots' hostile tag (World::arena_side_a_team).
      if (side == 0 && world().arena_side_a_team == 0) {
        world().arena_side_a_team = mech->team;
        world().arena_side_a_enemies = mech->enemies;
      }
      ArenaMech entry;
      entry.mech = mech, entry.id = id, entry.side = side, entry.spot = spot;
      g_mechs.push_back(entry);
    }
  }
  // Every mech at the same detail, whatever its distance from the view
  // (mech_lod.h, LodCalls::same_detail_for_all).
  lod_calls().same_detail_for_all = true;
  g_started = true;
  if (!g_mechs.empty()) view_follow();
  log_match_start(*g_setup, g_mechs);
}

}  // namespace mech3::arena
