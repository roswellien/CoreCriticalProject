#pragma once

#include <cstdint>
#include <cstdio>
#include <string>
#include <unordered_set>
#include <vector>

#include <nlohmann-json/json.hpp>

#include "mech3/arena.h"

namespace mech3 {
struct Weapon;
struct BeamWeapon;
}

// Ours, not the exe's (#287, docs/arena.md): the arena match log, one JSON
// object a line. A "start" line (the setup, seed and frame time), "state"
// lines ten times a second of game time (every mech's pose, heat, parts,
// target and AI order), "shot", "hit" and "destroyed" lines as they happen,
// and an "end" line once the match is decided. Every line is flushed as it
// is written, so a run that stops early leaves a readable log with no end
// line, which the reader reports as incomplete. Ids are each mech's index in
// setup order (ArenaMech::id), never a handle, and times are game seconds
// from the first Core frame, so the same seed writes the same bytes.

namespace mech3::arena {

// Seconds between state lines.
constexpr float kLogStatePeriod = 0.1f;

// The log's format version, in the start line (#289). The reader refuses a
// log without it or with another, so a viewer never misreads one; fields a
// reader doesn't know are still kept, so a later version can add fields.
constexpr int kLogVersion = 1;

// Ours (#289): everything the replay viewers need beyond #287's log (shot
// detail, rounds and beams in flight, routes, contacts, decision reasons),
// on by default. Off, the log is #287's plus the version and the match runs
// no new code at all, so one build can show the additions change nothing:
// matches repeat only on the same build (docs/arena.md, #294).
void set_arena_log_detail(bool on);
bool arena_log_detail();

// Called by the match (arena.cpp): the start line and the shot and hit hooks
// on, at the first Core frame; each frame's state lines when due and the
// destroyed lines of mechs that fell this frame; the end line and the hooks
// off once decided. `now` is game seconds from the first Core frame.
void log_match_start(const Setup& setup, const std::vector<ArenaMech>& mechs);
void log_match_frame(float now, const std::vector<ArenaMech>& mechs);
void log_match_end(const Result& result);
// The hooks off without an end line (a match cleared before it was decided).
void log_match_stop();

// Which weapon reports are new shots. The weapon report hook
// (WeaponCalls::net_event) fires once per projectile, but for a beam also on
// every frame it is held and once when it stops (weapon.cpp, BeamWeapon), so
// a beam counts once, when it turns on. Each counter keeps its own.
struct ShotStarts {
  // What one report is: a new shot, a beam still held, or a beam that just
  // stopped (#289's beam_end).
  enum class Report { kNewShot, kHeld, kEnded };
  Report report(const Weapon* weapon);
  bool is_new_shot(const Weapon* weapon) { return report(weapon) == Report::kNewShot; }
  void clear() { beams_on.clear(); }
  std::unordered_set<const Weapon*> beams_on;
};

// Ours (#289): one round or missile on its weapon def's list, as a state
// line's walk sees it.
struct RoundSeen {
  const void* round = nullptr;  // its pool slot
  float age = 0;                // seconds since it was fired (Projectile::age)
  float pos[3] = {};
};

// Ours (#289): the rounds and beams arena mechs fired. Rounds and beams name
// their shooter by scene node, not by mech, so the shot hook records each one
// as it is fired, and the state lines look them up here. Rounds are kept in
// the order they were fired, so ended rounds come out in the same order on
// every run of a seed (pool addresses differ between runs).
class RoundBook {
 public:
  // A round fired at that pool slot. A round still known at the slot (reused
  // before a state line saw it leave) ends first, as in walk().
  void shot(const void* round, int shooter, std::string weapon);
  // A beam weapon turned on or off. Kept by the weapon, never by its zWeapon
  // beam, which the game may free once it stops.
  void beam_on(const BeamWeapon* weapon, int shooter, std::string name);
  void beam_off(const BeamWeapon* weapon);
  // The state line's "rounds": every known round in `flying` (in its order),
  // each given an id the first time. A round with an id that is no longer
  // flying, or whose age went down (its slot reused by a shot the hook never
  // saw), ends: a "round_end" record (no "t") goes to `ended` and the round is
  // forgotten. One that never got an id lived under a state period and is
  // forgotten with no record. Unknown slots are skipped.
  nlohmann::json walk(const std::vector<RoundSeen>& flying, std::vector<nlohmann::json>* ended);
  void clear();

  struct HeldBeam {
    const BeamWeapon* weapon = nullptr;
    int shooter = -1;
    std::string name;
  };
  const std::vector<HeldBeam>& beams() const { return beams_; }

 private:
  struct Round {
    const void* slot = nullptr;
    int shooter = -1;
    std::string weapon;
    int id = -1;  // -1 until a state line sees it
    float age = 0;
    double pos[3] = {};
    bool done = false;  // this walk: ended or reused
  };
  nlohmann::json end_record(const Round& round) const;
  std::vector<Round> rounds_;
  std::vector<nlohmann::json> ended_by_reuse_;  // from shot(), handed out by the next walk
  std::vector<HeldBeam> beams_;
  int next_id_ = 0;
};

// One mech's state record, as the log writes it at `now`.
nlohmann::json mech_state_record(const ArenaMech& entry, const std::vector<ArenaMech>& mechs);

// A log read back: every line that parsed, in order, and whether it ends with
// an "end" line. Lines that do not parse are counted, not kept; fields the
// reader does not know are kept as they are in each record. A log whose first
// record is not a start line of version kLogVersion is refused: no records,
// and `error` says why.
struct LogRead {
  bool opened = false;
  std::vector<nlohmann::json> records;
  int bad_lines = 0;
  bool complete = false;  // the last record is an "end"
  std::string error;      // empty unless refused
};
LogRead read_arena_log(const std::string& path);

}  // namespace mech3::arena
