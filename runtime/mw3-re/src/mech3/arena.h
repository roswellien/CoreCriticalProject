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

// Room for every spawn spot: the host plus 15 bots fill 16.
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

// At the first Core frame (app_states, after nav_prebuild): with a match
// set, the host's mech handed to the AI as side A's first bot, then every
// other bot made in its spawn spot. Nothing without one.
void arena_start();

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
// The result line, as printed: "arena: winner A, time 1:22, lost A 0 B 1"
// ("winner draw" for a draw).
std::string arena_result_line(const Result& result);

// The spot the host's mech spawns at (a lone host is player 1, remote_1).
constexpr int kHostSpot = 1;

// Each bot's spawn spot, in setup order (side A then side B; side A's first
// is the host's mech, at kHostSpot). Side A's other bots take the free spots
// nearest the host's, side B's the farthest from it; equal distances go to
// the lower spot number. `spots` are remote_0 .. remote_15's positions.
std::vector<int> arena_spawn_spots(const float spots[kSpawnSpots][3], int side_a, int side_b);

// A bot's AI params: the preset's, placed at `pos` facing `yaw` (the spawn
// spot's), on team side + 1, with the chassis' first loadout (+0xbc = 0),
// engaging on (+0x3c = 1), always awake (+0x88 = 1: a stock pilot sleeps,
// frozen, while its nearest enemy is past its sight range) and on any enemy,
// not only the player (+0x8c = 0; zai_brain.cpp's wake-up check).
void arena_bot_params(const Bot& bot, int side, const float pos[3], float yaw, ai::AiParams* params);

// One mech in the match. `id` is its index in setup order, the id the match
// log uses (never a handle, which changes between runs).
struct ArenaMech {
  Mech* mech = nullptr;
  int id = 0;
  int side = 0;  // 0 side A, 1 side B
  int spot = 0;  // its remote_ spawn spot
};
// The match's mechs, the host's first; empty outside a match.
const std::vector<ArenaMech>& arena_mechs();
// The AI params a mech's brain runs on; null when it is not on AI controls.
const ai::AiParams* arena_brain_params(const Mech* mech);

// The host's mech (the mission player's) on AI controls over the hunt net,
// with `bot`'s preset params, on team 1. Its PlayerControls stay with
// player_controls_instance(), which the mission end frees as before. False
// when there is no host mech, no preset or no spawn spots.
bool arena_hand_host_to_ai(const Bot& bot);

// The host's mech as the tests (and later the match log) see it: on AI
// controls with a brain, its team, and whether any of its orders is running
// the hunt.
struct HostState {
  bool on_ai = false;
  uint32_t team_mask = 0;  // AiTarget::team: one bit per team, team 1 is 1 << 1
  bool hunting = false;
};
HostState arena_host_state();
// Whether the hunt net is still made (the mission's end frees it).
bool arena_hunt_net_held();

}  // namespace mech3::arena
