#include "mech3/replay_log.h"

#include <algorithm>
#include <cmath>
#include <set>

#include <nlohmann-json/json.hpp>

#include "mech3/arena_log.h"
#include "mech3/arena_setup.h"

namespace mech3::replay {

namespace {

using Json = nlohmann::json;

constexpr float kPi = 3.14159265f;

Vec3 vec3(const Json& j) {
  Vec3 v;
  if (!j.is_array() || j.size() < 3) return v;
  v.x = j[0].get<float>(), v.y = j[1].get<float>(), v.z = j[2].get<float>();
  return v;
}

float lerp(float a, float b, float f) { return a + (b - a) * f; }
Vec3 lerp(const Vec3& a, const Vec3& b, float f) { return {lerp(a.x, b.x, f), lerp(a.y, b.y, f), lerp(a.z, b.z, f)}; }
// Between two angles the short way round, so a heading crossing ±pi doesn't
// spin the long way.
float lerp_angle(float a, float b, float f) {
  float d = std::fmod(b - a, 2 * kPi);
  if (d > kPi) d -= 2 * kPi;
  if (d < -kPi) d += 2 * kPi;
  return a + d * f;
}

// A list field, empty when the record lacks it (never operator[] on a const
// record: a missing key there is undefined behavior).
const Json& list(const Json& record, const char* key) {
  static const Json kEmpty = Json::array();
  const auto it = record.find(key);
  return it != record.end() && it->is_array() ? *it : kEmpty;
}

// A log is untrusted input: a position must be a real number inside the
// world, 100 km being far beyond any MW3 map.
constexpr float kWorldLimit = 100000.0f;
bool in_world(const Vec3& v) {
  const auto ok = [](float c) { return std::isfinite(c) && std::abs(c) <= kWorldLimit; };
  return ok(v.x) && ok(v.y) && ok(v.z);
}

// A voice tag names sound files, so only plain short names pass.
bool valid_voice(const std::string& tag) {
  if (tag.empty() || tag.size() > 16) return false;
  for (const char c : tag) {
    const bool letter_digit_or_underscore = std::isalnum(static_cast<unsigned char>(c)) || c == '_';
    if (!letter_digit_or_underscore) return false;
  }
  return true;
}

// The one-shot leg actions the log names (mech_data.cpp action_name, 1..8).
bool known_action(const std::string& name) {
  static const std::set<std::string> kNames = {"fallf",  "fallb",  "landf",     "landb",
                                               "getupf", "getupb", "collapsel", "collapser"};
  return kNames.count(name) > 0;
}

constexpr int kAnimSlots = 13;   // Mech::anims
constexpr int kLastPartId = 15;  // part ids run 1..15
constexpr int kLastVoiceEvent = 15;

// When a log has no phase (version 1, or detail off), the gait advances one
// loop per this many meters walked: a rough stride, enough to keep feet moving.
constexpr float kFallbackStride = 8.0f;

// False when the mech's position is unusable; out-of-range fields are reset
// to their defaults and counted in *skipped.
bool read_pose(const Json& m, MechPose* out, int* skipped) {
  MechPose& p = *out;
  p.id = m.value("id", -1);
  p.pos = vec3(m.value("pos", Json()));
  if (!in_world(p.pos)) return false;
  p.heading = m.value("heading", 0.0f);
  p.speed = m.value("speed", 0.0f);
  if (m.contains("torso")) {
    p.twist = m.at("torso").value("twist", 0.0f);
    p.pitch = m.at("torso").value("pitch", 0.0f);
  }
  const Json& arms = list(m, "arms");
  for (size_t i = 0; i < 2 && i < arms.size(); ++i) {
    if (!arms[i].is_object()) continue;
    p.has_arm[i] = true;
    p.arm_yaw[i] = arms[i].value("yaw", 0.0f);
    p.arm_pitch[i] = arms[i].value("pitch", 0.0f);
  }
  if (m.contains("anim")) {
    const Json& anim = m.at("anim");
    p.anim = anim.value("index", -1);
    if (p.anim >= kAnimSlots || p.anim < -1) {
      p.anim = -1;
      ++*skipped;
    }
    p.has_phase = anim.contains("phase");
    p.phase = anim.value("phase", 0.0f);
    p.cps = anim.value("cps", 0.0f);
    p.weight = anim.value("weight", 0.0f);
    p.limp = anim.value("limp", -1);
  }
  p.jumping = m.value("jumping", false);
  p.fallen = m.value("fallen", false);
  p.heat = m.value("heat", 0.0f);
  p.standing = m.value("standing", true);
  p.target = m.value("target", -1);
  for (const Json& part : list(m, "parts")) {
    const int id = part.value("id", -1);
    if (id < 1 || id > kLastPartId) {
      ++*skipped;
      continue;
    }
    p.parts.push_back({id, part.value("armor", 0.0f), part.value("internal", 0.0f), part.value("destroyed", false)});
  }
  if (m.contains("ai")) {
    const Json& ai = m.at("ai");
    p.order = ai.value("order", "");
    p.has_goal = ai.contains("goal");
    if (p.has_goal) p.goal = vec3(ai.at("goal"));
    p.at = ai.value("at", -1);
    for (const Json& c : list(ai, "contacts")) p.contacts.push_back({c.value("id", -1), c.value("seen", false)});
  }
  // What reaches the game's animation code: an infinite or NaN angle, phase
  // or rate would index the clip's keys far out of range (a read past the
  // array), so each out-of-range value is reset and counted.
  const auto keep = [&](float* v, float lo, float hi, float fallback) {
    if (std::isfinite(*v) && *v >= lo && *v <= hi) return;
    *v = fallback;
    ++*skipped;
  };
  constexpr float kMaxAngle = 100.0f;  // radians; the game's own stay within a few turns
  keep(&p.heading, -kMaxAngle, kMaxAngle, 0.0f);
  keep(&p.twist, -kMaxAngle, kMaxAngle, 0.0f);
  keep(&p.pitch, -kMaxAngle, kMaxAngle, 0.0f);
  keep(&p.speed, -1000.0f, 1000.0f, 0.0f);
  for (int i = 0; i < 2; ++i) {
    keep(&p.arm_yaw[i], -kMaxAngle, kMaxAngle, 0.0f);
    keep(&p.arm_pitch[i], -kMaxAngle, kMaxAngle, 0.0f);
  }
  keep(&p.phase, 0.0f, 1.0f, 0.0f);
  keep(&p.cps, 0.0f, 100.0f, 0.0f);
  keep(&p.weight, 0.0f, 1.0f, 0.0f);
  keep(&p.heat, -1e6f, 1e6f, 0.0f);
  return true;
}

float wrap01(float x) { return x - std::floor(x); }

Event read_event(const Json& r, int* skipped) {
  Event e;
  e.t = r.value("t", 0.0f);
  e.type = r.value("type", "");
  e.id = r.value("id", -1);
  e.by = r.value("by", -1);
  e.weapon = r.value("weapon", "");
  e.beam = r.value("beam", false);
  e.muzzle = vec3(r.value("muzzle", Json()));
  e.dir = vec3(r.value("dir", Json()));
  // The 3D view starts effects at these: never past the world or infinite.
  const bool dir_ok = std::isfinite(e.dir.x) && std::isfinite(e.dir.y) && std::isfinite(e.dir.z) &&
                      std::abs(e.dir.x) <= 2 && std::abs(e.dir.y) <= 2 && std::abs(e.dir.z) <= 2;
  if (r.contains("muzzle") && (!in_world(e.muzzle) || !dir_ok)) {
    e.muzzle = {}, e.dir = {};
    ++*skipped;
  }
  e.code = r.value("code", "");
  e.target = r.value("target", -1);
  if (r.contains("at")) {
    e.at = vec3(r.at("at"));
    e.has_at = in_world(e.at);
    if (!e.has_at) ++*skipped;  // a hit without a point is drawn at the target's center
  }
  e.terrain = r.value("terrain", false);
  e.name = r.value("name", "");
  e.event = r.value("event", -1);
  e.dropped = r.value("dropped", false);
  return e;
}

void grow(float box[4], const Vec3& v) {
  box[0] = std::min(box[0], v.x), box[1] = std::min(box[1], v.z);
  box[2] = std::max(box[2], v.x), box[3] = std::max(box[3], v.z);
}

// The last entry of a by-time list at or before t, null before the first.
template <typename T>
const T* last_at_or_before(const std::vector<T>& by_time, float t) {
  const auto after =
      std::upper_bound(by_time.begin(), by_time.end(), t, [](float value, const T& item) { return value < item.t; });
  return after == by_time.begin() ? nullptr : &*(after - 1);
}

}  // namespace

bool parse_pose(const std::string& record_text, MechPose* out) {
  const Json record = Json::parse(record_text, nullptr, false);
  if (!record.is_object()) return false;
  int skipped = 0;
  try {
    return read_pose(record, out, &skipped);
  } catch (const Json::exception&) {
    return false;
  }
}

namespace {
// What both viewers refuse, the message naming `viewer`.
std::string refusal_for(const char* viewer, const ReplayFlags& f) {
  const std::string v = viewer;
  if (f.arena) return v + ": --arena is refused (a replay plays a log, it runs no match)";
  if (f.host) return v + ": --host is refused (a replay opens no network)";
  if (f.join) return v + ": --join is refused (a replay opens no network)";
  if (f.net_upnp) return v + ": --net-upnp is refused (a replay opens no network)";
  if (f.fly) return v + ": --fly is refused (a replay plays no mission)";
  if (f.mission) return v + ": --mission is refused (the log names its map)";
  return "";
}
}  // namespace

std::string replay_refusal(const ReplayFlags& f) { return refusal_for("--replay", f); }

std::string replay3d_refusal(const ReplayFlags& f) {
  if (f.replay) return "--replay3d: --replay is refused (one viewer at a time)";
  if (f.play_original) return "--replay3d: --original is refused (its quit box needs the bug fixes)";
  return refusal_for("--replay3d", f);
}

bool ReplayLog::load(const std::string& path, std::string* error) {
  arena::LogRead read = arena::read_arena_log(path);
  if (!read.opened) {
    *error = "cannot open " + path;
    return false;
  }
  if (!read.error.empty() || read.records.empty()) {
    *error = path + ": " + (read.error.empty() ? std::string("empty log") : read.error);
    return false;
  }
  bool ended = false;
  // The reader checks only the start line; a field of the wrong type further
  // on (a hand-edited or damaged log) throws, and is refused like a bad start.
  try {
    const Json& start = read.records.front();
    map_ = start.value("map", "");
    // Mech ids are their index in setup order, side A first (docs/arena.md).
    std::vector<std::string> chassis;
    for (const Json& side : list(start, "sides"))
      for (const Json& bot : side) chassis.push_back(bot.value("mech", ""));
    // A log is untrusted: a start line the arena could never write is refused
    // before anything is built from it.
    const Json& start_mechs = list(start, "mechs");
    if (start_mechs.size() > static_cast<size_t>(2 * arena::kMaxBotsPerSide)) {
      *error = path + ": more mechs than an arena match holds";
      return false;
    }
    std::set<int> ids;
    for (const Json& m : start_mechs) {
      MechInfo info;
      info.id = m.value("id", -1);
      info.side = m.value("side", 0);
      info.voice = m.value("voice", "");
      if (!ids.insert(info.id).second) {
        *error = path + ": mech id " + std::to_string(info.id) + " appears twice";
        return false;
      }
      if (info.side != 0 && info.side != 1) {
        *error = path + ": mech " + std::to_string(info.id) + " has a side other than 0 or 1";
        return false;
      }
      if (m.contains("voice") && !valid_voice(info.voice)) {
        *error = path + ": mech " + std::to_string(info.id) + " has a voice tag that is not a plain name";
        return false;
      }
      if (info.id >= 0 && info.id < static_cast<int>(chassis.size())) info.chassis = chassis[info.id];
      mechs_.push_back(info);
    }
    for (const Json& r : read.records) {
      const std::string type = r.value("type", "");
      const float t = r.value("t", 0.0f);
      if (type == "state") {
        State s;
        s.t = t;
        for (const Json& m : list(r, "mechs")) {
          MechPose pose;
          if (read_pose(m, &pose, &skipped_)) s.mechs.push_back(std::move(pose));
          else ++skipped_;
        }
        for (const Json& round : list(r, "rounds")) {
          RoundAt at{round.value("id", -1), round.value("by", -1), round.value("weapon", ""),
                     vec3(round.value("pos", Json()))};
          if (in_world(at.pos)) s.rounds.push_back(std::move(at));
          else ++skipped_;
        }
        for (const Json& beam : list(r, "beams")) {
          BeamAt at{beam.value("by", -1), beam.value("weapon", ""), vec3(beam.value("from", Json())),
                    vec3(beam.value("to", Json()))};
          if (in_world(at.from) && in_world(at.to)) s.beams.push_back(std::move(at));
          else ++skipped_;
        }
        states_.push_back(std::move(s));
      } else if (type == "shot" || type == "hit") {
        fire_.push_back(read_event(r, &skipped_));
      } else if (type == "action") {
        Event e = read_event(r, &skipped_);
        if (known_action(e.name)) history_[e.id].actions.push_back(std::move(e));
        else ++skipped_;
      } else if (type == "voice") {
        // Arena bots have no radio voice, so no replay plays chatter (#289,
        // 2026-11-14); the lines are only checked.
        if (r.value("event", -1) < 0 || r.value("event", -1) > kLastVoiceEvent) ++skipped_;
      } else if (type == "destroyed") {
        float& at = history_[r.value("id", -1)].destroyed_at;
        at = std::min(at, t);
      } else if (type == "decision") {
        history_[r.value("id", -1)].decisions.push_back(read_event(r, &skipped_));
      } else if (type == "round_end") {
        round_end_at_[r.value("round", -1)] = t;
        // Version 2: where it struck, shown as an impact like a hit.
        Event impact = read_event(r, &skipped_);
        if (impact.has_at) fire_.push_back(std::move(impact));
      } else if (type == "beam_end") {
        beam_ends_.push_back({t, r.value("id", -1), r.value("weapon", "")});
      } else if (type == "route") {
        RouteAt route;
        route.t = t;
        for (const Json& p : list(r, "points")) route.points.push_back(vec3(p));
        history_[r.value("id", -1)].routes.push_back(std::move(route));
      } else if (type == "end") {
        duration_ = t;
        ended = true;
      }
    }
  } catch (const Json::exception& e) {
    *error = path + ": a damaged line (" + e.what() + ")";
    return false;
  }
  // The log is written in time order; sort anyway so a lookup by time holds.
  const auto by_t = [](const auto& a, const auto& b) { return a.t < b.t; };
  std::stable_sort(states_.begin(), states_.end(), by_t);
  std::stable_sort(fire_.begin(), fire_.end(), by_t);
  std::stable_sort(beam_ends_.begin(), beam_ends_.end(), by_t);
  for (auto& [id, h] : history_) {
    std::stable_sort(h.routes.begin(), h.routes.end(), by_t);
    std::stable_sort(h.decisions.begin(), h.decisions.end(), by_t);
    std::stable_sort(h.actions.begin(), h.actions.end(), by_t);
  }
  derive_from_states();
  if (!ended) duration_ = states_.empty() ? 0.0f : states_.back().t;
  return true;
}

const MechInfo* ReplayLog::info_of(int id) const {
  for (const MechInfo& info : mechs_)
    if (info.id == id) return &info;
  return nullptr;
}

void ReplayLog::derive_from_states() {
  struct Seen {
    Vec3 pos;
    float walked = 0;
    bool fallen = false;
    std::set<int> live;  // part ids not yet destroyed
  };
  std::map<int, Seen> seen;  // by mech id, from its previous state line
  std::set<int> has_actions;
  for (const auto& [id, h] : history_)
    if (!h.actions.empty()) has_actions.insert(id);
  for (State& s : states_) {
    for (MechPose& pose : s.mechs) {
      const auto found = seen.find(pose.id);
      std::set<int> live;
      for (const Part& part : pose.parts)
        if (!part.destroyed) live.insert(part.id);
      if (found == seen.end()) {
        seen[pose.id] = {pose.pos, 0.0f, pose.fallen, live};
        continue;
      }
      Seen& was = found->second;
      const float dx = pose.pos.x - was.pos.x, dz = pose.pos.z - was.pos.z;
      was.walked += std::sqrt(dx * dx + dz * dz);
      pose.walked = was.walked;
      MechHistory& h = history_[pose.id];
      // A part lost: destroyed since, or gone from the line altogether.
      for (const int id : was.live) {
        if (live.count(id)) continue;
        Event lost;
        lost.t = s.t, lost.type = "part_lost", lost.id = pose.id, lost.part = id;
        h.parts_lost.push_back(lost);
      }
      // A log with no action lines (version 1, or detail off) still shows a
      // fall and a get-up, from the "fallen" flag's edges.
      if (!has_actions.count(pose.id) && pose.fallen != was.fallen) {
        Event action;
        action.t = s.t, action.type = "action", action.id = pose.id;
        action.name = pose.fallen ? "fallf" : "getupf";
        h.actions.push_back(action);
      }
      was.pos = pose.pos, was.fallen = pose.fallen, was.live = std::move(live);
    }
  }
}

std::vector<int> ReplayLog::parts_lost_by(int id, float t) const {
  std::vector<int> lost;
  const auto h = history_.find(id);
  if (h == history_.end()) return lost;
  for (const Event& e : h->second.parts_lost)
    if (e.t <= t) lost.push_back(e.part);
  return lost;
}

size_t ReplayLog::state_before(float t) const {
  const auto after = std::upper_bound(states_.begin(), states_.end(), t,
                                      [](float value, const State& s) { return value < s.t; });
  return after == states_.begin() ? 0 : static_cast<size_t>(after - states_.begin()) - 1;
}

Frame ReplayLog::frame_at(float t) const {
  Frame frame;
  frame.t = t;
  if (states_.empty()) return frame;
  const size_t i = state_before(t);
  const State& before = states_[i];
  const State& after = i + 1 < states_.size() ? states_[i + 1] : before;
  const float span = after.t - before.t;
  const float f = span > 0 ? std::clamp((t - before.t) / span, 0.0f, 1.0f) : 0.0f;

  for (const MechPose& was : before.mechs) {
    MechPose pose = was;
    for (const MechPose& next : after.mechs) {
      if (next.id != was.id) continue;
      pose.pos = lerp(was.pos, next.pos, f);
      pose.heading = lerp_angle(was.heading, next.heading, f);
      pose.twist = lerp_angle(was.twist, next.twist, f);
      pose.pitch = lerp_angle(was.pitch, next.pitch, f);
      for (int arm = 0; arm < 2; ++arm) {
        pose.arm_yaw[arm] = lerp_angle(was.arm_yaw[arm], next.arm_yaw[arm], f);
        pose.arm_pitch[arm] = lerp_angle(was.arm_pitch[arm], next.arm_pitch[arm], f);
      }
      pose.speed = lerp(was.speed, next.speed, f);
      pose.walked = lerp(was.walked, next.walked, f);
    }
    // The gait's place in its loop: run on from the earlier line at its
    // rate, or, with no phase in the log, from the distance walked.
    if (pose.has_phase) pose.phase = wrap01(was.phase + was.cps * (t - before.t));
    else pose.phase = wrap01(pose.walked / kFallbackStride);
    RouteAt route;
    Event decision;
    const auto h = history_.find(was.id);
    if (h != history_.end()) {
      if (h->second.destroyed_at <= t) pose.standing = false;
      if (const RouteAt* r = last_at_or_before(h->second.routes, t)) route = *r;
      if (const Event* d = last_at_or_before(h->second.decisions, t)) decision = *d;
      if (const Event* a = last_at_or_before(h->second.actions, t)) {
        pose.action = a->name;
        pose.action_elapsed = t - a->t;
      }
    }
    frame.mechs.push_back(std::move(pose));
    frame.routes.push_back(std::move(route));
    frame.last_decision.push_back(std::move(decision));
  }

  // A round in both lines moves between them; one only in the earlier line
  // stays where it was last seen until its round_end.
  for (const RoundAt& was : before.rounds) {
    RoundAt round = was;
    bool found = false;
    for (const RoundAt& next : after.rounds)
      if (next.id == was.id) round.pos = lerp(was.pos, next.pos, f), found = true;
    if (!found) {
      const auto end = round_end_at_.find(was.id);
      if (end != round_end_at_.end() && end->second <= t) continue;
    }
    frame.rounds.push_back(round);
  }

  // A beam held in the earlier line, unless its beam_end came since.
  const auto ends_from = std::upper_bound(beam_ends_.begin(), beam_ends_.end(), before.t,
                                          [](float value, const BeamEnd& e) { return value < e.t; });
  for (const BeamAt& beam : before.beams) {
    bool ended = false;
    for (auto e = ends_from; e != beam_ends_.end() && e->t <= t; ++e)
      if (e->by == beam.by && e->weapon == beam.weapon) ended = true;
    if (!ended) frame.beams.push_back(beam);
  }

  // Shots and hits in (t - kRecent, t].
  const auto recent_from = std::upper_bound(fire_.begin(), fire_.end(), t - kRecent,
                                            [](float value, const Event& e) { return value < e.t; });
  for (auto e = recent_from; e != fire_.end() && e->t <= t; ++e) frame.recent.push_back(*e);
  return frame;
}

std::vector<Event> ReplayLog::fire_between(float after, float until) const {
  std::vector<Event> out;
  const auto from = std::upper_bound(fire_.begin(), fire_.end(), after,
                                     [](float value, const Event& e) { return value < e.t; });
  for (auto e = from; e != fire_.end() && e->t <= until; ++e) out.push_back(*e);
  return out;
}

std::vector<Vec3> ReplayLog::trail(int id, float t, float seconds) const {
  std::vector<Vec3> points;
  const auto from = std::lower_bound(states_.begin(), states_.end(), t - seconds,
                                     [](const State& s, float value) { return s.t < value; });
  for (auto s = from; s != states_.end() && s->t <= t; ++s)
    for (const MechPose& p : s->mechs)
      if (p.id == id) points.push_back(p.pos);
  return points;
}

void ReplayLog::bounds(float box[4]) const {
  box[0] = box[1] = 1e30f;
  box[2] = box[3] = -1e30f;
  for (const State& s : states_) {
    for (const MechPose& p : s.mechs) {
      grow(box, p.pos);
      if (p.has_goal) grow(box, p.goal);
    }
    for (const RoundAt& r : s.rounds) grow(box, r.pos);
    for (const BeamAt& b : s.beams) grow(box, b.from), grow(box, b.to);
  }
  for (const auto& [id, h] : history_)
    for (const RouteAt& route : h.routes)
      for (const Vec3& p : route.points) grow(box, p);
}

}  // namespace mech3::replay
