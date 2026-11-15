// #289 step 3 (docs/arena.md): the replay reader's version 2 fields, its
// fallbacks for logs without them, and how it treats a damaged or hostile
// log. Game-free: every log here is written by the test.
#include <cmath>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

#include "check.h"
#include "mech3/replay_log.h"

namespace {
using mech3::replay::Frame;
using mech3::replay::ReplayLog;

std::string write_log(const char* name, const std::string& text) {
  const std::string dir = std::string(MW3_TEST_TMP) + "/" + name;
  std::error_code ec;
  std::filesystem::remove_all(dir, ec);
  std::filesystem::create_directories(dir, ec);
  const std::string path = dir + "/match-1.jsonl";
  std::ofstream out(path, std::ios::binary | std::ios::trunc);
  out << text;
  return path;
}

// True when it loaded; *error says why not.
bool load(ReplayLog* log, const char* name, const std::string& text, std::string* error) {
  return log->load(write_log(name, text), error);
}

const std::string kStart =
    R"({"type":"start","version":2,"map":"c1mp1","sides":[[{"mech":"madcat"}],[{"mech":"orion"}]],"mechs":[{"id":0,"side":0},{"id":1,"side":1}]})"
    "\n";

// One mech's state record. `anim` is the anim object's text.
std::string mech(int id, float x, bool fallen, const std::string& anim, const std::string& parts) {
  return R"({"id":)" + std::to_string(id) + R"(,"pos":[)" + std::to_string(x) +
         R"(,0,0],"heading":0,"speed":4,"torso":{"twist":0,"pitch":0.2},"arms":[{"yaw":0.1,"pitch":0},null],"anim":)" +
         anim + R"(,"jumping":false,"fallen":)" + (fallen ? "true" : "false") + R"(,"parts":)" + parts + "}";
}

std::string state(float t, const std::string& mechs) {
  return R"({"type":"state","t":)" + std::to_string(t) + R"(,"mechs":[)" + mechs + R"(],"rounds":[],"beams":[]})" +
         "\n";
}

const std::string kParts = R"([{"id":1,"armor":1,"internal":1,"destroyed":false},{"id":9,"armor":1,"internal":1,"destroyed":false}])";
const std::string kArmGone = R"([{"id":1,"armor":1,"internal":1,"destroyed":false},{"id":9,"armor":0,"internal":0,"destroyed":true}])";
const std::string kPhased = R"({"index":2,"t":0.5,"phase":0.9,"cps":3.0,"weight":0.25,"limp":-1})";
const std::string kUnphased = R"({"index":2,"t":0.5})";

// A version 2 log: mech 0 walks, falls at 1.0, lies 5 s, gets up at 6.0.
std::string v2_log() {
  std::string text = kStart;
  for (int i = 0; i <= 80; ++i) {
    const float t = i * 0.1f;
    const bool down = t >= 1.0f && t < 6.0f;
    text += state(t, mech(0, t * 4, down, kPhased, t >= 2.0f ? kArmGone : kParts) + "," +
                         mech(1, 50, false, kPhased, kParts));
  }
  text += R"({"type":"action","t":1.0,"id":0,"name":"fallf"})" "\n";
  text += R"({"type":"action","t":6.0,"id":0,"name":"getupf"})" "\n";
  text += R"({"type":"hit","t":2.0,"id":0,"by":1,"weapon":"AC","damage":3,"at":[8,2,0]})" "\n";
  text += R"({"type":"end","t":8.0,"winner":"A","lost":[]})" "\n";
  return text;
}
}  // namespace

// The version 2 fields come through, and between lines the phase runs on at
// its rate and wraps.
TEST(replay_v2_round_trip_and_phase_wrap) {
  ReplayLog log;
  std::string error;
  EXPECT(load(&log, "replay_v2", v2_log(), &error));
  const Frame f = log.frame_at(0.15f);
  EXPECT(f.mechs.size() == 2);
  const auto& m = f.mechs[0];
  EXPECT(m.has_phase && m.anim == 2 && std::abs(m.weight - 0.25f) < 1e-4f && m.limp == -1);
  EXPECT(std::abs(m.pitch - 0.2f) < 1e-4f && m.has_arm[0] && !m.has_arm[1] && std::abs(m.arm_yaw[0] - 0.1f) < 1e-4f);
  EXPECT(std::abs(m.phase - 0.05f) < 1e-3f);  // 0.9 + 3 loops/s * 0.05 s, wrapped
  EXPECT(std::abs(log.frame_at(0.12f).mechs[0].phase - 0.96f) < 1e-3f);
  EXPECT(log.skipped() == 0);
  const Frame hit = log.frame_at(2.1f);
  bool found = false;
  for (const auto& e : hit.recent)
    if (e.type == "hit" && e.has_at && e.at.x == 8.0f) found = true;
  EXPECT(found);
}

// The same frame whatever was asked before it.
TEST(replay_v2_seek_order_does_not_matter) {
  ReplayLog log;
  std::string error;
  EXPECT(load(&log, "replay_seek", v2_log(), &error));
  const Frame a = log.frame_at(3.33f);
  log.frame_at(7.9f);
  log.frame_at(0.0f);
  const Frame b = log.frame_at(3.33f);
  EXPECT(a.mechs[0].phase == b.mechs[0].phase && a.mechs[0].action == b.mechs[0].action &&
         a.mechs[0].action_elapsed == b.mechs[0].action_elapsed && a.mechs[0].pos.x == b.mechs[0].pos.x);
}

// A fall, a 5 s lie and a get-up; a seek into the lie lands on the fall with
// its elapsed time unclamped, for the puppet to hold its last frame.
TEST(replay_v2_fall_lie_get_up) {
  ReplayLog log;
  std::string error;
  EXPECT(load(&log, "replay_fall", v2_log(), &error));
  EXPECT(log.frame_at(0.9f).mechs[0].action.empty());
  const auto lying = log.frame_at(4.0f).mechs[0];
  EXPECT(lying.action == "fallf" && std::abs(lying.action_elapsed - 3.0f) < 1e-3f && lying.fallen);
  const auto up = log.frame_at(6.5f).mechs[0];
  EXPECT(up.action == "getupf" && std::abs(up.action_elapsed - 0.5f) < 1e-3f);
}

// A part destroyed in a state line is lost from that line's time.
TEST(replay_v2_part_loss) {
  ReplayLog log;
  std::string error;
  EXPECT(load(&log, "replay_parts", v2_log(), &error));
  EXPECT(log.parts_lost_by(0, 1.95f).empty());
  const std::vector<int> lost = log.parts_lost_by(0, 2.05f);
  EXPECT(lost.size() == 1 && lost[0] == 9);
  EXPECT(log.parts_lost_by(1, 8.0f).empty());
  // A part gone from the line altogether counts too.
  std::string text = kStart + state(0, mech(0, 0, false, kPhased, kParts)) +
                     state(0.1f, mech(0, 0, false, kPhased, R"([{"id":1,"armor":1,"internal":1,"destroyed":false}])"));
  ReplayLog gone;
  EXPECT(load(&gone, "replay_parts_gone", text, &error));
  EXPECT(gone.parts_lost_by(0, 0.1f).size() == 1);
}

// A log without phase or action lines (version 1, or detail off): phase from
// distance walked, falls from the "fallen" edges.
TEST(replay_fallbacks_without_v2_fields) {
  std::string text = kStart;
  for (int i = 0; i <= 30; ++i) {
    const float t = i * 0.1f;
    text += state(t, mech(0, t * 4, t >= 1.0f && t < 2.0f, kUnphased, kParts));
  }
  ReplayLog log;
  std::string error;
  EXPECT(load(&log, "replay_fallback", text, &error));
  const auto m = log.frame_at(0.5f).mechs[0];
  EXPECT(!m.has_phase && m.weight == 0.0f && m.limp == -1);
  EXPECT(std::abs(m.phase - 2.0f / 8.0f) < 1e-3f);  // 2 m walked, one loop per 8 m
  EXPECT(log.frame_at(1.5f).mechs[0].action == "fallf");
  EXPECT(log.frame_at(2.5f).mechs[0].action == "getupf");
  // A version 1 start line reads the same way.
  std::string v1 = text;
  v1.replace(v1.find("\"version\":2"), 11, "\"version\":1");
  ReplayLog old;
  EXPECT(load(&old, "replay_v1", v1, &error));
  EXPECT(old.frame_at(1.5f).mechs[0].action == "fallf");
}

// A start line the arena could never write is refused with a reason.
TEST(replay_refuses_hostile_start_lines) {
  const auto refused = [](const char* name, const std::string& start, const char* reason) {
    ReplayLog log;
    std::string error;
    const bool loaded = load(&log, name, start + "\n" + state(0, ""), &error);
    return !loaded && error.find(reason) != std::string::npos;
  };
  std::string many = R"({"type":"start","version":2,"map":"m","sides":[],"mechs":[)";
  for (int i = 0; i < 17; ++i) many += (i ? "," : "") + std::string(R"({"id":)") + std::to_string(i) + R"(,"side":0})";
  many += "]}";
  EXPECT(refused("replay_many", many, "more mechs"));
  EXPECT(refused("replay_dup", R"({"type":"start","version":2,"map":"m","mechs":[{"id":0,"side":0},{"id":0,"side":1}]})",
                 "appears twice"));
  EXPECT(refused("replay_side", R"({"type":"start","version":2,"map":"m","mechs":[{"id":0,"side":2}]})", "side"));
  EXPECT(refused("replay_voice",
                 R"({"type":"start","version":2,"map":"m","mechs":[{"id":0,"side":0,"voice":"../x"}]})", "voice"));
}

// Out-of-range values are skipped and counted, never passed on.
TEST(replay_skips_bad_values) {
  std::string text = kStart;
  text += state(0, mech(0, 0, false, R"({"index":40,"t":0})",
                        R"([{"id":99,"armor":1,"internal":1,"destroyed":false},{"id":1,"armor":1,"internal":1,"destroyed":false}])") +
                       "," + mech(1, 1e9f, false, kPhased, kParts));
  text += R"({"type":"action","t":0.0,"id":0,"name":"dance"})" "\n";
  text += R"({"type":"voice","t":0.0,"id":0,"event":99})" "\n";
  text += R"({"type":"hit","t":0.0,"id":0,"by":1,"weapon":"AC","damage":1,"at":[1e9,0,0]})" "\n";
  ReplayLog log;
  std::string error;
  EXPECT(load(&log, "replay_skip", text, &error));
  const Frame f = log.frame_at(0.0f);
  EXPECT(f.mechs.size() == 1);  // the far-away mech is dropped
  EXPECT(f.mechs[0].anim == -1 && f.mechs[0].parts.size() == 1 && f.mechs[0].action.empty());
  EXPECT(f.recent.size() == 1 && !f.recent[0].has_at);
  EXPECT(log.skipped() == 6);  // anim, part 99, far mech, action, voice, hit point
}
