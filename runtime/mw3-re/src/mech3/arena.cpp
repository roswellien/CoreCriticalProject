#include "mech3/arena.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <string>

#include "gamez/zclass/class.h"
#include "gamez/zmath/zmth_matrix.h"
#include "gamez/zmath/zmth_vector.h"
#include "mech3/app_mech.h"
#include "mech3/arena_camera.h"
#include "mech3/mech_parts.h"
#include "mech3/spectator_camera_hooks.h"
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
#include "platform/render3d.h"

namespace mech3::arena {

// All of the arena's state, for the match a run plays (one at a time). The
// file then reads in order: the view helpers, the session, the setup and
// switches, the frame tick, the match's start, and ArenaRun.
namespace {
const Setup* g_setup = nullptr;  // the run's setup; null outside an arena run
std::vector<ArenaMech> g_mechs;
// The bots' names, kept for the match: a mech may hold its name's pointer.
std::deque<std::string> g_names;
// The match's clock and result: started at the first Core frame.
bool g_started = false;
float g_start_time = 0;
int64_t g_seed = 0;
Result g_result;
Result g_pending;  // the result once settled, published after the aftermath (arena_tick)
bool g_fail_ended = false;  // a match that could not start has been ended (fail_start)
bool g_headless = false;    // --hidden with no screenshots: nothing is drawn
int g_viewed = -1;          // the bot the spectator's view follows (an index into g_mechs), -1 for none

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

// The first standing bot after `from` in setup order (before it with
// `direction` -1), wrapping round; -1 when none stands.
int next_standing(int from, int direction = 1) {
  const int count = static_cast<int>(g_mechs.size());
  for (int step = 1; step <= count; ++step) {
    const int index = ((from + direction * step) % count + count) % count;
    if (arena_standing(g_mechs[static_cast<size_t>(index)].mech)) return index;
  }
  return -1;
}

// Each frame: a fallen viewed bot hands the view on. A match nobody watches
// (arena_headless) views no bot at all: the camera then never touches a
// bot's torso or controls, and no bot is the HUD's world().player.
void view_follow() {
  if (arena_headless()) return;
  const bool viewed_standing = g_viewed >= 0 && arena_standing(g_mechs[static_cast<size_t>(g_viewed)].mech);
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
  g_pending = Result{};
}

const Result& arena_result() { return g_result; }
void set_arena_seed(int64_t seed) { g_seed = seed; }
int64_t arena_seed() { return g_seed; }

void set_arena_headless(bool on) { g_headless = on; }
bool arena_headless() { return g_headless && g_setup != nullptr; }
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

namespace {
// Ends the multiplayer match the arena runs in, so the run can exit. The stock
// end (net_mech_tick) would end it again when its clock runs out: it is marked
// ended already, with its exit time never reached.
void end_stock_match() {
  const NetCalls& calls = net_calls();
  if (NetGameFields* game = calls.game ? calls.game() : nullptr) {
    if (game->end_state) *game->end_state = 3;
    if (game->end_time) *game->end_time = 3.4e38f;
  }
  if (calls.game_over) calls.game_over();
  else net_game_over();
}

// A match that cannot start still ends, with an error, so an unattended
// batch of runs never waits on it. It is only marked here: arena_start runs
// while the Core state is being entered, and the run's end is watched from
// Core's frames (mw3_main.cpp), so the match is ended on its first frame
// (arena_tick).
void fail_start(const char* why) {
  std::fprintf(stderr, "mw3: arena: %s; the match cannot start\n", why);
  g_result = Result{};
  g_result.decided = true, g_result.failed = true;
  g_fail_ended = false;
}
}  // namespace

// Ours (#287)
void arena_tick() {
  if (g_setup && g_result.failed && !g_fail_ended) {
    g_fail_ended = true;
    end_stock_match();
    return;
  }
  if (!g_setup || !g_started || g_result.decided || g_mechs.empty()) return;
  view_follow();
  int standing[kSides] = {};
  int lost[kSides] = {};
  for (const ArenaMech& entry : g_mechs) {
    if (arena_standing(entry.mech)) ++standing[entry.side];
    else ++lost[entry.side];
  }
  const float match_time = world().time - g_start_time;
  log_match_frame(match_time, g_mechs);

  // After the result is settled, the match runs on kAftermathSeconds more,
  // still logged, so a replay shows the last mech fall and burn and the
  // others stop, before the result is published and the run ends (the run
  // exits once g_result.decided is set; watch_launch.cpp).
  if (g_pending.decided) {
    if (match_time < g_pending.time + kAftermathSeconds) return;
    g_result = g_pending;
    std::printf("%s\n", arena_result_line(g_result).c_str());
    std::fflush(stdout);
    Result logged = g_result;
    logged.time = match_time;  // the end line marks where the log stops
    log_match_end(logged);
    end_stock_match();
    return;
  }

  const bool out_of_time = match_time >= static_cast<float>(g_setup->minutes) * 60.0f;
  const bool side_wiped_out = standing[0] == 0 || standing[1] == 0;
  if (!side_wiped_out && !out_of_time) return;

  g_pending.decided = true;
  g_pending.time = match_time;
  g_pending.lost[0] = lost[0];
  g_pending.lost[1] = lost[1];
  // Elimination and the time limit both come down to who has more standing:
  // a wiped-out side has none.
  if (standing[0] > standing[1]) g_pending.winner = 0;
  else if (standing[1] > standing[0]) g_pending.winner = 1;
  else g_pending.winner = -1;
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
  // The preset's pilot name and radio voice; AiParams frees both.
  std::free(params->pilot), params->pilot = bot.pilot.empty() ? nullptr : strdup(bot.pilot.c_str());
  std::free(params->sound_tag), params->sound_tag = bot.voice.empty() ? nullptr : strdup(bot.voice.c_str());
  params->put<float>(0x08, pos[0]);
  params->put<float>(0x0c, pos[1]);
  params->put<float>(0x10, pos[2]);
  params->put<float>(0x14, yaw);
  params->put<int32_t>(0x18, side + 1);  // AiParams::team()
  params->put<int32_t>(0xbc, bot.loadout);  // the configuration create_ai_mech builds: the setup's stock one
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
  // Never powered down at the start: +0xcc bit 5 (p12's second flag) makes
  // create_ai_mech shut the mech down (player.cpp), a campaign ambush that
  // the mission's script powers up later. The arena runs no script, so such
  // a preset's bot would stand shut down all match (5 of the runner's 8
  // short-list pilots did, 2026-11-16).
  constexpr uint8_t kStartsPoweredDown = 0x20;
  params->raw[0xcc] = static_cast<uint8_t>(params->raw[0xcc] & ~kStartsPoweredDown);
}

// Ours (#287)
Mech* arena_viewed_mech() {
  return g_viewed >= 0 ? g_mechs[static_cast<size_t>(g_viewed)].mech : nullptr;
}

// Ours (#287)
bool arena_view_next() {
  if (!g_started || g_mechs.empty() || arena_headless()) return false;
  const int next = next_standing(g_viewed);
  if (next < 0) return false;
  view_mech(next);
  return true;
}

// Ours (#529)
bool arena_view_previous() {
  if (!g_started || g_mechs.empty() || arena_headless()) return false;
  const int previous = next_standing(g_viewed < 0 ? 0 : g_viewed, -1);
  if (previous < 0) return false;
  view_mech(previous);
  return true;
}

namespace {
// `v` scaled to unit length, or `fallback` when it has none.
void unit_or(const float v[3], const float fallback[3], float out[3]) {
  const float length = std::sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]);
  for (int axis = 0; axis < 3; ++axis) out[axis] = length > 1e-6f ? v[axis] / length : fallback[axis];
}
}  // namespace

// Ours (#529). The centre is program_vehicle_centre, the same point the
// arena log records. The heading is Vehicle::forward (flat, kept by the
// game each frame). The torso's look is the mech's yaw times the torso's
// own turn and shake (Torso::shake_q, a const read), applied to the mech's
// forward axis, -z.
bool arena_camera_view(arena_camera::Subject* subject, arena_camera::Action* action) {
  *subject = arena_camera::Subject{};
  *action = arena_camera::Action{};
  if (!g_started || g_mechs.empty()) return false;
  float sum[3] = {};
  float centres[kArenaPlayers][3] = {};
  int standing = 0;
  for (const ArenaMech& entry : g_mechs) {
    if (!arena_standing(entry.mech) || standing >= static_cast<int>(kArenaPlayers)) continue;
    program_vehicle_centre(entry.mech, centres[standing]);
    for (int axis = 0; axis < 3; ++axis) sum[axis] += centres[standing][axis];
    ++standing;
  }
  action->count = standing;
  if (standing > 0) {
    for (int axis = 0; axis < 3; ++axis) action->centre[axis] = sum[axis] / static_cast<float>(standing);
    for (int index = 0; index < standing; ++index) {
      const float dx = centres[index][0] - action->centre[0];
      const float dz = centres[index][2] - action->centre[2];
      action->radius = std::max(action->radius, std::sqrt(dx * dx + dz * dz));
    }
  }
  Mech* mech = arena_viewed_mech();
  if (!mech) return true;
  // A fallen viewed bot stays the subject until view_follow hands the view on,
  // so the camera watches it fall rather than jumping first.
  subject->present = true;
  program_vehicle_centre(mech, subject->centre);
  const float ahead[3] = {0, 0, 1};
  const float flat[3] = {mech->forward.x, 0, mech->forward.z};
  unit_or(flat, ahead, subject->forward);
  float look[3] = {subject->forward[0], 0, subject->forward[2]};
  if (mech->torso) {
    float torso_q[4];
    mech->torso->shake_q(torso_q);
    float turned[4];
    zmth::quat_mul(mech->orientation, torso_q, turned);
    const zmth::Quat q{turned[0], turned[1], turned[2], turned[3]};
    zmth::Vec3 rotated{};
    zmth::quat_rotate(q, zmth::Vec3{0, 0, -1}, rotated);
    const float direction[3] = {rotated.x, rotated.y, rotated.z};
    unit_or(direction, subject->forward, look);
  }
  for (int axis = 0; axis < 3; ++axis) subject->look[axis] = look[axis];
  if (mech->torso && mech->torso->node) zcls::node_world_position(static_cast<zcls::Node*>(mech->torso->node), subject->cockpit);
  else for (int axis = 0; axis < 3; ++axis) subject->cockpit[axis] = subject->centre[axis];
  return true;
}

bool arena_viewed_label(int* id, std::string* label) {
  if (!g_started || g_viewed < 0 || g_viewed >= static_cast<int>(g_mechs.size())) return false;
  const ArenaMech& entry = g_mechs[static_cast<size_t>(g_viewed)];
  *id = entry.id;
  // From the entry: a bot that failed to be made leaves its name in g_names
  // but no entry, so the two lists need not line up.
  *label = entry.name ? entry.name : "";
  return true;
}

bool arena_hunt_net_held() { return ai::hunt_net() != nullptr; }

const std::vector<ArenaMech>& arena_mechs() { return g_mechs; }

bool arena_standing(const Mech* mech) {
  return mech->active && mech->anim_state != kAnimDead;
}

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
  world().arena_spectating = false;
  g_mechs.clear();
  g_names.clear();
  g_result = Result{};
  g_pending = Result{};
  g_started = false;
  if (!g_setup || g_setup->sides[0].empty()) return;
  // Only an arena run is changed from here on: a stock mission keeps its own
  // update order and nav servicing even when it starts with no player mech.
  world().arena_spectating = !world().mission_player;
  set_update_order_seed(static_cast<uint32_t>(g_seed));  // the update order replays with the match
  ai::nav_frame_reset();
  g_start_time = world().time;

  float pos[kSpawnSpots][3], yaw[kSpawnSpots];
  if (!read_spawn_spots(pos, yaw)) return fail_start("the map's spawn spots could not be read");
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
      // Stable: g_names is a deque (push_back never moves its strings) and is
      // cleared only with g_mechs, as the mech itself already holds this pointer.
      entry.name = g_names.back().c_str();
      g_mechs.push_back(entry);
    }
  }
  // Every mech at the same detail, whatever its distance from the view
  // (mech_lod.h, LodCalls::same_detail_for_all).
  lod_calls().same_detail_for_all = true;
  int made[kSides] = {};
  for (const ArenaMech& entry : g_mechs) ++made[entry.side];
  if (made[0] == 0 || made[1] == 0) return fail_start("a side has no bot that could be made");
  g_started = true;
  if (!g_mechs.empty()) view_follow();
  log_match_start(*g_setup, g_mechs);
}

// Ours (#287)
bool ArenaRun::read_setup(const std::string& path, const Flags& flags, std::string* message) {
  path_ = path;
  if (const std::string refused = arena_refusal(flags); !refused.empty()) {
    *message = refused;
    return false;
  }
  std::string error;
  if (!read_arena_setup(path_, &setup_, &error)) {
    *message = "--arena " + path_ + ": " + error;
    return false;
  }
  setup_.record_every_update = setup_.record_every_update || flags.record_every_update;
  return true;
}

// Ours (#287)
bool ArenaRun::read_game_files(int64_t seed, std::string* message) {
  std::string error;
  if (read_arena_game_files(&setup_, &error)) log_ = create_arena_log(setup_, seed, &log_path_, &error);
  if (!log_) {
    *message = "--arena " + path_ + ": " + error;
    return false;
  }
  return true;
}

// Ours (#287): never the ENet transport: no socket is opened.
bool ArenaRun::open(int64_t seed, int32_t frame_ms, bool headless, std::string* message) {
  hub_ = std::make_unique<znet::Hub>();
  if (!arena_open_session(*hub_)) {
    *message = "--arena: the in-process session failed";
    return false;
  }
  set_arena_setup(&setup_);  // the first Core frame makes every bot
  set_arena_seed(seed);      // which ends of the map the sides start at, and the update order
  set_arena_log(log_.get(), frame_ms);
  set_arena_headless(headless);  // nobody watches: draw nothing
  // Before the mission loads, so its first mission_changed lights it (#507).
  const char* lighting = time_of_day_lighting(setup_.time_of_day);
  platform::arena_lighting_mission() = lighting ? lighting : "";
  return true;
}

ArenaRun::~ArenaRun() {
  if (!hub_) return;
  set_arena_setup(nullptr);
  set_arena_log(nullptr, 0);
  set_arena_headless(false);
  platform::arena_lighting_mission().clear();
  znet::shutdown();
  hub_.reset();
}

}  // namespace mech3::arena

// Ours (#529): the spectator camera's hooks (spectator_camera_hooks.h).
namespace mech3 {
namespace {
SpectatorCameraHooks* g_spectator_camera = nullptr;
}  // namespace
void set_spectator_camera_hooks(SpectatorCameraHooks* hooks) { g_spectator_camera = hooks; }
SpectatorCameraHooks* spectator_camera_hooks() { return g_spectator_camera; }
}  // namespace mech3
