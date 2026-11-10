#pragma once

// Ours, not the exe's (#287, docs/arena.md): the hunt order that arena bots
// run on multiplayer maps, which ship no AI route nets. A bot walks toward the
// nearest enemy it knows of, by the grid (zai_nav), and the stock engage gate
// and fight take over in range. Nothing outside the arena uses it.

namespace mech3::ai {

// What the goal is picked from. Places are world x, y, z.
struct HuntInput {
  float pos[3] = {};          // the bot
  bool has_contact = false;   // the nearest enemy contact, when there is one
  float contact[3] = {};
  bool has_last_seen = false;  // where the last enemy it had was seen
  float last_seen[3] = {};
  float fallback[3] = {};     // the caller's point when nothing is known
};

enum class HuntRule { kContact, kLastSeen, kFallback };

struct HuntGoal {
  float at[3] = {};
  HuntRule rule = HuntRule::kFallback;
  bool drop_last_seen = false;  // the bot has reached the last-seen place
};

// A last-seen place counts as reached within this flat distance (m).
constexpr float kHuntReached = 30.0f;

// The contact, else the last-seen place until the bot is within
// kHuntReached of it, else the fallback point.
HuntGoal pick_hunt_goal(const HuntInput& in);

}  // namespace mech3::ai
