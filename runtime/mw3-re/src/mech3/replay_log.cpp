#include "mech3/replay_log.h"

#include <algorithm>
#include <cmath>

#include <nlohmann-json/json.hpp>

#include "mech3/arena_log.h"

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

MechPose read_pose(const Json& m) {
  MechPose p;
  p.id = m.value("id", -1);
  p.pos = vec3(m.value("pos", Json()));
  p.heading = m.value("heading", 0.0f);
  if (m.contains("torso")) p.twist = m.at("torso").value("twist", 0.0f);
  p.heat = m.value("heat", 0.0f);
  p.standing = m.value("standing", true);
  p.target = m.value("target", -1);
  for (const Json& part : list(m, "parts"))
    p.parts.push_back(
        {part.value("id", -1), part.value("armor", 0.0f), part.value("internal", 0.0f), part.value("destroyed", false)});
  if (m.contains("ai")) {
    const Json& ai = m.at("ai");
    p.order = ai.value("order", "");
    p.has_goal = ai.contains("goal");
    if (p.has_goal) p.goal = vec3(ai.at("goal"));
    p.at = ai.value("at", -1);
    for (const Json& c : list(ai, "contacts")) p.contacts.push_back({c.value("id", -1), c.value("seen", false)});
  }
  return p;
}

Event read_event(const Json& r) {
  Event e;
  e.t = r.value("t", 0.0f);
  e.type = r.value("type", "");
  e.id = r.value("id", -1);
  e.by = r.value("by", -1);
  e.weapon = r.value("weapon", "");
  e.beam = r.value("beam", false);
  e.muzzle = vec3(r.value("muzzle", Json()));
  e.dir = vec3(r.value("dir", Json()));
  e.code = r.value("code", "");
  e.target = r.value("target", -1);
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

std::string replay_refusal(const ReplayFlags& f) {
  if (f.arena) return "--replay: --arena is refused (a replay plays a log, it runs no match)";
  if (f.host) return "--replay: --host is refused (a replay opens no network)";
  if (f.join) return "--replay: --join is refused (a replay opens no network)";
  if (f.net_upnp) return "--replay: --net-upnp is refused (a replay opens no network)";
  if (f.fly) return "--replay: --fly is refused (a replay plays no mission)";
  if (f.mission) return "--replay: --mission is refused (the log names its map)";
  return "";
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
    for (const Json& m : list(start, "mechs")) {
      MechInfo info;
      info.id = m.value("id", -1);
      info.side = m.value("side", 0);
      if (info.id >= 0 && info.id < static_cast<int>(chassis.size())) info.chassis = chassis[info.id];
      mechs_.push_back(info);
    }
    for (const Json& r : read.records) {
      const std::string type = r.value("type", "");
      const float t = r.value("t", 0.0f);
      if (type == "state") {
        State s;
        s.t = t;
        for (const Json& m : list(r, "mechs")) s.mechs.push_back(read_pose(m));
        for (const Json& round : list(r, "rounds"))
          s.rounds.push_back(
              {round.value("id", -1), round.value("by", -1), round.value("weapon", ""), vec3(round.value("pos", Json()))});
        for (const Json& beam : list(r, "beams"))
          s.beams.push_back({beam.value("by", -1), beam.value("weapon", ""), vec3(beam.value("from", Json())),
                             vec3(beam.value("to", Json()))});
        states_.push_back(std::move(s));
      } else if (type == "shot" || type == "hit") {
        fire_.push_back(read_event(r));
      } else if (type == "destroyed") {
        float& at = history_[r.value("id", -1)].destroyed_at;
        at = std::min(at, t);
      } else if (type == "decision") {
        history_[r.value("id", -1)].decisions.push_back(read_event(r));
      } else if (type == "round_end") {
        round_end_at_[r.value("round", -1)] = t;
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
  }
  if (!ended) duration_ = states_.empty() ? 0.0f : states_.back().t;
  return true;
}

const MechInfo* ReplayLog::info_of(int id) const {
  for (const MechInfo& info : mechs_)
    if (info.id == id) return &info;
  return nullptr;
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
    }
    RouteAt route;
    Event decision;
    const auto h = history_.find(was.id);
    if (h != history_.end()) {
      if (h->second.destroyed_at <= t) pose.standing = false;
      if (const RouteAt* r = last_at_or_before(h->second.routes, t)) route = *r;
      if (const Event* d = last_at_or_before(h->second.decisions, t)) decision = *d;
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
