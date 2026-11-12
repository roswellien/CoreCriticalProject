#pragma once
#include <string>
#include <vector>

// Ours (#289): an arena match log (docs/arena.md) read for the replay viewers.
// The log is read once and turned into plain values, so the viewer never sees
// JSON (mw3core keeps the JSON library private). frame_at(t) is a pure
// function of t: seeking backward then forward gives the same frame.
namespace mech3::replay {

// Which command-line options came with --replay. A replay reads a log and
// draws it; it opens no network, plays no mission and runs no match.
struct ReplayFlags {
  bool arena = false, host = false, join = false, net_upnp = false, mission = false, fly = false;
};
// "" when the run may go on, else the message naming the option.
std::string replay_refusal(const ReplayFlags& flags);

struct Vec3 {
  float x = 0, y = 0, z = 0;
};

struct Part {
  int id = -1;
  float armor = 0, internal = 0;
  bool destroyed = false;
};

struct Contact {
  int id = -1;
  bool seen = false;  // the sensors detect it now (not line of sight)
};

// What the start line says about one mech.
struct MechInfo {
  int id = -1;
  int side = 0;
  std::string chassis;  // the roster name, e.g. "madcat"
};

// One mech in one state line, or between two of them.
struct MechPose {
  int id = -1;
  Vec3 pos;
  float heading = 0;  // radians, the hull
  float twist = 0;    // radians, the torso against the hull
  float heat = 0;
  bool standing = true;
  int target = -1;
  std::string order;  // "hunt", "fight", "other" or "" (no AI)
  bool has_goal = false;
  Vec3 goal;
  int at = -1;  // the waypoint index in its latest route, -1 with none
  std::vector<Contact> contacts;
  std::vector<Part> parts;
};

struct RoundAt {
  int id = -1, by = -1;
  std::string weapon;
  Vec3 pos;
};

struct BeamAt {
  int by = -1;
  std::string weapon;
  Vec3 from, to;
};

// A shot, hit, destroyed or decision line. Fields a type lacks keep their
// defaults.
struct Event {
  float t = 0;
  std::string type;
  int id = -1;      // the mech it is about (the shooter, the one hit)
  int by = -1;      // hit: the attacker
  std::string weapon;
  bool beam = false;
  Vec3 muzzle, dir;  // shot
  std::string code;  // decision
  int target = -1;   // decision
};

struct RouteAt {
  float t = -1;  // -1: no route line yet
  std::vector<Vec3> points;
};

struct Frame {
  float t = 0;
  std::vector<MechPose> mechs;        // in log order
  std::vector<RoundAt> rounds;
  std::vector<BeamAt> beams;
  std::vector<RouteAt> routes;        // per mech, aligned with `mechs`
  std::vector<Event> last_decision;   // per mech; type "" when none yet
  std::vector<Event> recent;          // shots and hits in (t - kRecent, t]
};

// How long a shot streak or a hit spark stays drawn.
constexpr float kRecent = 0.3f;

class ReplayLog {
 public:
  // False with *error from the log reader (missing, damaged or unversioned).
  bool load(const std::string& path, std::string* error);

  const std::string& map() const { return map_; }
  const std::vector<MechInfo>& mechs() const { return mechs_; }
  // The end line's time, else the last state line's (a log stopped early).
  float duration() const { return duration_; }
  Frame frame_at(float t) const;
  // A mech's positions from its state lines in [t - seconds, t], oldest first.
  std::vector<Vec3> trail(int mech_index, float t, float seconds) const;
  // Every position the log holds (mechs, rounds, beams, routes, goals), as
  // min x, min z, max x, max z; min > max when there are none.
  void bounds(float box[4]) const;

 private:
  struct State {
    float t = 0;
    std::vector<MechPose> mechs;
    std::vector<RoundAt> rounds;
    std::vector<BeamAt> beams;
  };
  struct RoundEnd {
    float t = 0;
    int round = -1;
  };
  struct Route {
    float t = 0;
    int id = -1;
    std::vector<Vec3> points;
  };
  struct BeamEnd {
    float t = 0;
    int by = -1;
    std::string weapon;
  };
  // The last state line at or before t (0 before the first).
  size_t state_before(float t) const;

  std::string map_;
  std::vector<MechInfo> mechs_;
  float duration_ = 0;
  std::vector<State> states_;
  std::vector<Event> events_;  // shots, hits, destroyed and decisions, by time
  std::vector<RoundEnd> round_ends_;
  std::vector<BeamEnd> beam_ends_;
  std::vector<Route> routes_;
};

}  // namespace mech3::replay
