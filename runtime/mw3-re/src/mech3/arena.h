#pragma once

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
// The open match log for this run (create_arena_log's), with its seed and
// frame time for the start line; not owned. Null (the default, and every
// non-arena run) writes nothing. The log itself: arena_log.h.
void set_arena_log(std::FILE* file, int64_t seed, int32_t frame_ms);

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
};
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
// The AI params a mech's brain runs on; null when it is not on AI controls.
const ai::AiParams* arena_brain_params(const Mech* mech);

// Whether the hunt net is still made (the mission's end frees it).
bool arena_hunt_net_held();

}  // namespace mech3::arena
