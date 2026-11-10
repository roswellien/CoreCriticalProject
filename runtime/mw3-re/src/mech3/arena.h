#pragma once

#include "gamez/znetwork/znet_session.h"
#include "mech3/arena_setup.h"

// Ours, not the exe's (#287, docs/arena.md): the arena run's session. An
// arena match is a lone host's multiplayer game, but on the in-process
// znet::Hub the tests use, never on a socket: nothing is bound, nothing
// answers a LAN search, and nothing leaves the process.

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
// set, the host's mech handed to the AI as side A's first bot. Nothing
// without one.
void arena_start();

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
