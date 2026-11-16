#pragma once

#include <memory>
#include <string>
#include <vector>

#include "gamez/znetwork/znet_session.h"
#include "mech3/arena_setup.h"

// Ours, not the exe's (#287, docs/arena.md): the arena run's session. An
// arena match is a lone host's multiplayer game, but on the in-process
// znet::Hub the tests use, never on a socket: nothing is bound, nothing
// answers a LAN search, and nothing leaves the process.

namespace mech3 {
struct Mech;
}

namespace mech3::arena {

// Room for every spawn spot: 16 bots fill 16 (the host's seat has no mech).
constexpr uint32_t kArenaPlayers = 16;

// zNetwork up on a new endpoint of `hub`, and a session hosted on it as
// player "Arena". The endpoint, or null when hosting failed. The hub must
// outlive the session: call znet::shutdown() before the hub goes.
znet::Transport* arena_open_session(znet::Hub& hub);

// The match this run plays, set by mw3 --arena (and the tests) before the
// engine starts and cleared after it; null outside an arena run, so the
// arena's hooks do nothing in any other game. Not owned.
void set_arena_setup(const Setup* setup);
const Setup* arena_setup();
// The open match log for this run (create_arena_log's), with the frame time
// for the start line (the seed is the arena's, set_arena_seed); not owned.
// Null (the default, and every non-arena run) writes nothing. The log
// itself: arena_log.h.
void set_arena_log(std::FILE* file, int32_t frame_ms);

// At the first Core frame (app_states, after nav_prebuild): with a match
// set, every bot made in its spawn spot (the host is a spectator with no
// mech: launch_spectator), then the view put on the first. Nothing without one.
void arena_start();

// The spectator's view (#287 step 3b, a minimal follow camera): the godseye
// camera on one standing bot. When it falls the view moves to the next
// standing bot in setup order; arena_view_next (the camera-cycle key in a
// match) moves it on by hand. world().player follows the viewed bot for the
// HUD only; weapon_world().player and world().mission_player stay null so no
// player-only rule (sensor range, beam snap, arm restriction) runs for anyone.
// The viewed bot, null without one.
Mech* arena_viewed_mech();
// The next standing bot after the viewed one; false outside a match.
bool arena_view_next();

// Each Core frame (CoreState::update), with a match set and started: the
// match end. One side with no mech standing (Mech::active) loses, both at
// once is a draw; at the setup's time limit the side with more standing wins,
// equal is a draw, counted at that frame. Once decided: the result line on
// stdout, the stock end marked done so its clock can't end the match again,
// and net_game_over's fade to the exit, once.
void arena_tick();

// How a match ended; `decided` false while it runs.
struct Result {
  bool decided = false;
  int winner = -1;  // 0 side A, 1 side B, -1 a draw
  float time = 0;   // seconds of game time from the first Core frame
  int lost[2] = {};  // mechs destroyed per side
  bool failed = false;  // the match could not start (no spawn spots, no bot made); the run exits 1
};
// The result is set (decided) kAftermathSeconds after the frame that settles
// it, the match logged on meanwhile so a replay shows the last fall; its
// time stays the settling frame's.
inline constexpr float kAftermathSeconds = 5.0f;
const Result& arena_result();
// Game seconds since the first Core frame (the log's and the result's clock);
// 0 before a match starts.
float arena_match_time();
// The result line, as printed: "arena: winner A, time 1:22, lost A 0 B 1"
// ("winner draw" for a draw).
std::string arena_result_line(const Result& result);

// The match's seed (--seed), which picks where the sides start. Set with the
// setup; 0 until then.
void set_arena_seed(int64_t seed);
int64_t arena_seed();

// Ours (#287): a match nobody watches (--hidden, no screenshots) draws
// nothing and views no bot (arena_viewed_mech stays null). Drawing changes how a match plays out (a single frame drawn early
// can change a bot's steering minutes later; battletech-specs research
// mw3-ai/order-bias), so a hidden match must not depend on where the view is.
void set_arena_headless(bool on);
bool arena_headless();

// How many of the map's most separated spot pairs the seed chooses among.
constexpr int kAnchorChoices = 3;

// Each bot's spawn spot, in setup order (side A then side B). The two sides
// start at opposite ends: every pair of spots ranked by distance apart, the
// seed picks one of the kAnchorChoices farthest pairs (seed % 3) and which
// end is side A's ((seed / 3) % 2). Each side then takes the free spots
// nearest its own end, side A first; equal distances go to the lower spot
// number. `spots` are remote_0 .. remote_15's positions (docs/arena.md;
// research: battletech-specs/research/mw3-ai/spawn-spots.md).
std::vector<int> arena_spawn_spots(const float spots[kSpawnSpots][3], int side_a, int side_b, int64_t seed);

// A bot's AI params: the preset's, placed at `pos` facing `yaw` (the spawn
// spot's), on team side + 1, with the chassis' first loadout (+0xbc = 0),
// engaging on (+0x3c = 1), always awake (+0x88 = 1: a stock pilot sleeps,
// frozen, while its nearest enemy is past its sight range) and on any enemy,
// not only the player (+0x8c = 0; zai_brain.cpp's wake-up check), and never
// the player's lancemate (+0xcd bits 0 and 1 off: side A shares the host
// mech's team, and a lancemate follows the player instead of hunting).
void arena_bot_params(const Bot& bot, int side, const float pos[3], float yaw, ai::AiParams* params);

// One mech in the match. `id` is its index in setup order, the id the match
// log uses (never a handle, which changes between runs).
struct ArenaMech {
  Mech* mech = nullptr;
  int id = 0;
  int side = 0;  // 0 side A, 1 side B
  int spot = 0;  // its remote_ spawn spot
};
// The match's mechs in setup order; empty outside a match.
const std::vector<ArenaMech>& arena_mechs();
// Mech::anim_state values the arena reads, as the stock files name them
// (mech_damage.cpp, mech_move.cpp): the death animation, and lying fallen on
// the back or the front.
constexpr int kAnimDead = 10, kAnimFallenBack = 12, kAnimFallenFront = 13;

// Whether a mech still counts in the match: active and not in its death
// animation. Stock clears Mech::active only once the death fall ends, a few
// seconds after the kill; take_damage and program_pilot_alive already treat
// the dead state (anim_state 10) as dead, so the result, the log and the view
// hand-off count the kill when it happens.
bool arena_standing(const Mech* mech);
// For the tests: the AI params a mech's brain runs on (null when it is not on
// AI controls), and whether the hunt net is still made (a mission's end frees it).
const ai::AiParams* arena_brain_params(const Mech* mech);
bool arena_hunt_net_held();

// One mw3 --arena run, from the command line to the exit: what the program's
// main needs, in the order it needs it. Every failure is a message for
// stderr; nothing is set until open() succeeds, and the destructor clears
// whatever open() set, so the arena's hooks stay off in any later run.
class ArenaRun {
 public:
  ArenaRun() = default;
  ArenaRun(const ArenaRun&) = delete;
  ArenaRun& operator=(const ArenaRun&) = delete;
  ~ArenaRun();

  // Before anything starts: the options refused, then the setup file read.
  bool read_setup(const std::string& path, const Flags& flags, std::string* message);
  // With the install mounted: the map's spawn spots and the presets read from
  // the player's files, then the match log made (never over an old one).
  bool read_game_files(int64_t seed, std::string* message);
  // Before the engine runs: the in-process session opened and the match set,
  // with the seed and frame time a log must repeat and whether anyone watches.
  bool open(int64_t seed, int32_t frame_ms, bool headless, std::string* message);

  const Setup& setup() const { return setup_; }
  const std::string& log_path() const { return log_path_; }

 private:
  std::string path_;
  Setup setup_;
  LogFile log_;
  std::string log_path_;
  std::unique_ptr<znet::Hub> hub_;  // outlives the engine: znet::shutdown() first
};

}  // namespace mech3::arena
