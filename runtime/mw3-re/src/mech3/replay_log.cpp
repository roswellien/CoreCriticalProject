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

MechPose read_pose(const Json& m) {
  MechPose p;
  p.id = m.value("id", -1);
  p.pos = vec3(m.value("pos", Json()));
  p.heading = m.value("heading", 0.0f);
  if (m.contains("torso")) p.twist = m["torso"].value("twist", 0.0f);
  p.heat = m.value("heat", 0.0f);
  p.standing = m.value("standing", true);
  p.target = m.value("target", -1);
  if (m.contains("parts"))
    for (const Json& part : m["parts"])
      p.parts.push_back({part.value("id", -1), part.value("armor", 0.0f), part.value("internal", 0.0f),
                         part.value("destroyed", false)});
  if (m.contains("ai")) {
    const Json& ai = m["ai"];
    p.order = ai.value("order", "");
    p.has_goal = ai.contains("goal");
    if (p.has_goal) p.goal = vec3(ai["goal"]);
    p.at = ai.value("at", -1);
    if (ai.contains("contacts"))
      for (const Json& c : ai["contacts"]) p.contacts.push_back({c.value("id", -1), c.value("seen", false)});
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
  const Json& start = read.records.front();
  map_ = start.value("map", "");
  // Mech ids are their index in setup order, side A first (docs/arena.md).
  std::vector<std::string> chassis;
  if (start.contains("sides"))
    for (const Json& side : start["sides"])
      for (const Json& bot : side) chassis.push_back(bot.value("mech", ""));
  if (start.contains("mechs"))
    for (const Json& m : start["mechs"]) {
      MechInfo info;
      info.id = m.value("id", -1);
      info.side = m.value("side", 0);
      if (info.id >= 0 && info.id < static_cast<int>(chassis.size())) info.chassis = chassis[info.id];
      mechs_.push_back(info);
    }
  bool ended = false;
  for (const Json& r : read.records) {
    const std::string type = r.value("type", "");
    const float t = r.value("t", 0.0f);
    if (type == "state") {
      State s;
      s.t = t;
      for (const Json& m : r["mechs"]) s.mechs.push_back(read_pose(m));
      if (r.contains("rounds"))
        for (const Json& round : r["rounds"])
          s.rounds.push_back({round.value("id", -1), round.value("by", -1), round.value("weapon", ""),
                              vec3(round.value("pos", Json()))});
      if (r.contains("beams"))
        for (const Json& beam : r["beams"])
          s.beams.push_back({beam.value("by", -1), beam.value("weapon", ""), vec3(beam.value("from", Json())),
                             vec3(beam.value("to", Json()))});
      states_.push_back(std::move(s));
    } else if (type == "shot" || type == "hit" || type == "destroyed" || type == "decision") {
      events_.push_back(read_event(r));
    } else if (type == "round_end") {
      round_ends_.push_back({t, r.value("round", -1)});
    } else if (type == "beam_end") {
      beam_ends_.push_back({t, r.value("id", -1), r.value("weapon", "")});
    } else if (type == "route") {
      Route route;
      route.t = t;
      route.id = r.value("id", -1);
      for (const Json& p : r.value("points", Json::array())) route.points.push_back(vec3(p));
      routes_.push_back(std::move(route));
    } else if (type == "end") {
      duration_ = t;
      ended = true;
    }
  }
  // The log is written in time order; sort anyway so a lookup by time holds.
  const auto by_t = [](const auto& a, const auto& b) { return a.t < b.t; };
  std::stable_sort(states_.begin(), states_.end(), by_t);
  std::stable_sort(events_.begin(), events_.end(), by_t);
  std::stable_sort(round_ends_.begin(), round_ends_.end(), by_t);
  std::stable_sort(beam_ends_.begin(), beam_ends_.end(), by_t);
  std::stable_sort(routes_.begin(), routes_.end(), by_t);
  if (!ended) duration_ = states_.empty() ? 0.0f : states_.back().t;
  return true;
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
    for (const Event& e : events_) {
      if (e.t > t) break;
      if (e.type == "destroyed" && e.id == was.id) pose.standing = false;
    }
    frame.mechs.push_back(std::move(pose));
  }

  // A round in both lines moves between them; one only in the earlier line
  // stays where it was last seen until its round_end.
  for (const RoundAt& was : before.rounds) {
    RoundAt round = was;
    bool found = false;
    for (const RoundAt& next : after.rounds)
      if (next.id == was.id) round.pos = lerp(was.pos, next.pos, f), found = true;
    if (!found) {
      bool ended = false;
      for (const RoundEnd& end : round_ends_)
        if (end.round == was.id && end.t <= t) ended = true;
      if (ended) continue;
    }
    frame.rounds.push_back(round);
  }

  // A beam held in the earlier line, unless its beam_end came since.
  for (const BeamAt& beam : before.beams) {
    bool ended = false;
    for (const BeamEnd& end : beam_ends_)
      if (end.by == beam.by && end.weapon == beam.weapon && end.t > before.t && end.t <= t) ended = true;
    if (!ended) frame.beams.push_back(beam);
  }

  frame.routes.resize(frame.mechs.size());
  frame.last_decision.resize(frame.mechs.size());
  for (size_t m = 0; m < frame.mechs.size(); ++m) {
    const int id = frame.mechs[m].id;
    for (const Route& route : routes_) {
      if (route.t > t) break;
      if (route.id == id) frame.routes[m] = {route.t, route.points};
    }
    for (const Event& e : events_) {
      if (e.t > t) break;
      if (e.type == "decision" && e.id == id) frame.last_decision[m] = e;
    }
  }
  for (const Event& e : events_) {
    if (e.t > t) break;
    if ((e.type == "shot" || e.type == "hit") && e.t > t - kRecent) frame.recent.push_back(e);
  }
  return frame;
}

std::vector<Vec3> ReplayLog::trail(int mech_index, float t, float seconds) const {
  std::vector<Vec3> points;
  if (mech_index < 0 || mech_index >= static_cast<int>(mechs_.size())) return points;
  const int id = mechs_[mech_index].id;
  for (const State& s : states_) {
    if (s.t > t) break;
    if (s.t < t - seconds) continue;
    for (const MechPose& p : s.mechs)
      if (p.id == id) points.push_back(p.pos);
  }
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
  for (const Route& route : routes_)
    for (const Vec3& p : route.points) grow(box, p);
}

}  // namespace mech3::replay
