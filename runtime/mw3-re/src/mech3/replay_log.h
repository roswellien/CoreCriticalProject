#pragma once
#include <map>
#include <string>
#include <vector>

// Ours (#289): an arena match log (docs/arena.md) read for the replay viewers.
// The log is read once and turned into plain values, so the viewer never sees
// JSON (mw3core keeps the JSON library private). frame_at(t) is a pure
// function of t: seeking backward then forward gives the same frame.
namespace mech3::replay {

// Which command-line options came with --replay or --replay3d. A replay
// reads a log and draws it; it opens no network, plays no mission and runs
// no match.
struct ReplayFlags {
  bool arena = false, host = false, join = false, net_upnp = false, mission = false, fly = false;
  bool replay = false, replay3d = false;  // which viewers were asked for
  // --original: the 3D replay's quit box keys need the bug fixes on
  // (quit_box.cpp), which it turns off.
  bool play_original = false;
};
// "" when the run may go on, else the message naming the option.
std::string replay_refusal(const ReplayFlags& flags);
// The same for --replay3d: everything --replay refuses, --replay itself and
// --original.
std::string replay3d_refusal(const ReplayFlags& flags);

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
  std::string voice;    // version 2: the radio voice tag, "" for none
};

// One mech in one state line, or between two of them.
struct MechPose {
  int id = -1;
  Vec3 pos;
  float heading = 0;  // radians, the hull
  float twist = 0;    // radians, the torso against the hull
  float pitch = 0;    // radians, the torso
  float speed = 0;    // m/s forward
  bool has_arm[2] = {};
  float arm_yaw[2] = {}, arm_pitch[2] = {};
  int anim = -1;           // the gait slot, 0..12; -1 unknown or out of range
  float phase = 0;         // 0..1 through the gait loop
  float cps = 0;           // loops a second
  bool has_phase = false;  // false (v1 or detail off): phase comes from distance walked
  float weight = 0;        // the gait blend's weight
  int limp = -1;           // the limping leg, -1 none
  bool jumping = false, fallen = false;
  float walked = 0;  // meters walked since the first state line (the phase fallback)
  // The latest action at or before the frame (fallf .. collapser), "" none,
  // and seconds since it started, unclamped: the puppet knows its length and
  // decides when it holds or ends.
  std::string action;
  float action_elapsed = 0;
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
  bool has_at = false;  // version 2 hit or round end: where it struck
  Vec3 at;
  bool terrain = false;
  std::string name;      // action: fallf .. collapser
  int event = -1;        // voice: the radio event, 0..15
  bool dropped = false;  // voice: the game skipped it (MINDELAY)
  int part = -1;         // part_lost: the part id, 1..15
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

// One state line's mech record, as JSON text, read as the log reader reads
// it; false when it is not one or its position is unusable. For the tests,
// which pose a puppet from a live mech's record.
bool parse_pose(const std::string& record_text, MechPose* out);

// How long a shot streak or a hit spark stays drawn.
constexpr float kRecent = 0.3f;

class ReplayLog {
 public:
  // False with *error from the log reader (missing, damaged or unversioned).
  bool load(const std::string& path, std::string* error);

  const std::string& map() const { return map_; }
  const std::vector<MechInfo>& mechs() const { return mechs_; }
  // The start line's entry for a mech id, null when it has none.
  const MechInfo* info_of(int id) const;
  // The end line's time, else the last state line's (a log stopped early).
  float duration() const { return duration_; }
  Frame frame_at(float t) const;
  // A mech's positions from its state lines in [t - seconds, t], oldest first.
  std::vector<Vec3> trail(int id, float t, float seconds) const;
  // The part ids a mech had lost by t (destroyed or gone from its state
  // lines), in the order they went.
  std::vector<int> parts_lost_by(int id, float t) const;
  // The shots and hits (round ends included) with after < t <= until, by
  // time: what the 3D view starts effects for, frame by frame.
  std::vector<Event> fire_between(float after, float until) const;
  // Values skipped as out of range (a damaged or hand-made log).
  int skipped() const { return skipped_; }
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
  struct BeamEnd {
    float t = 0;
    int by = -1;
    std::string weapon;
  };
  // What the log says about one mech over time, each list by time, so a
  // frame finds the latest entry at or before t by binary search.
  struct MechHistory {
    std::vector<RouteAt> routes;
    std::vector<Event> decisions;
    std::vector<Event> actions;     // derived from "fallen" when the log has no action lines
    std::vector<Event> parts_lost;
    float destroyed_at = 1e30f;
  };
  // After load: each pose's distance walked, each mech's lost parts, and,
  // for a mech with no action lines, falls and get-ups from "fallen".
  void derive_from_states();
  // The last state line at or before t (0 before the first).
  size_t state_before(float t) const;

  std::string map_;
  std::vector<MechInfo> mechs_;
  float duration_ = 0;
  std::vector<State> states_;
  std::vector<Event> fire_;  // shots and hits, by time
  std::map<int, float> round_end_at_;
  std::vector<BeamEnd> beam_ends_;  // by time
  std::map<int, MechHistory> history_;  // by mech id
  int skipped_ = 0;
};

}  // namespace mech3::replay
