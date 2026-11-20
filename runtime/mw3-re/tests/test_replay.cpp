// #289 step 3 (docs/arena.md): the replay reader's version 2 fields, its
// fallbacks for logs without them, and how it treats a damaged or hostile
// log. Every log here is written by the test; the run and frame tests at the
// end (replay3d_run_*, replay_frame_*, replay_log_*) are the ones that need
// the game's files or open a session.
#include <cmath>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

#include "check.h"
#include "gamez/znetwork/znet_session.h"
#include "gamez/zutil/zutl_path.h"
#include "mech3/replay_log.h"
#include "mech3/replay_run.h"

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
  // Every line logs phase 0.9 at 3 loops/s, which its rate doesn't reach, so
  // between lines the phase blends from the run-on (1.05 at 0.15 s) to the
  // next line's run back (0.75), the short way round: 0.9 at the middle.
  EXPECT(std::abs(m.phase - 0.9f) < 1e-3f);
  // 0.12 s: 0.96 run on, 0.66 run back, a fifth of the way: 0.90.
  EXPECT(std::abs(log.frame_at(0.12f).mechs[0].phase - 0.9f) < 1e-3f);
  // Past the end line (8.0) the gait holds still: no walking in place.
  const mech3::replay::MechPose past_end = log.frame_at(9.0f).mechs[0];
  EXPECT(std::abs(past_end.phase - log.frame_at(8.0f).mechs[0].phase) < 1e-4f);
  EXPECT(past_end.cps == 0.0f && past_end.speed == 0.0f);
  EXPECT(log.skipped() == 0);
  const Frame hit = log.frame_at(2.1f);
  bool found = false;
  for (const auto& e : hit.recent)
    if (e.type == "hit" && e.has_at && e.at.x == 8.0f) found = true;
  EXPECT(found);
}

// A clip change between lines (walk to run): the next clip has its own loop,
// so the phase only runs on from the earlier line, with no blend.
TEST(replay_v2_phase_no_blend_across_clips) {
  const std::string run = R"({"index":3,"t":0.5,"phase":0.2,"cps":3.0,"weight":0.25,"limp":-1})";
  const std::string text = kStart + state(0, mech(0, 0, false, kPhased, kParts)) +
                           state(0.1f, mech(0, 0, false, run, kParts));
  ReplayLog log;
  std::string error;
  EXPECT(load(&log, "replay_clips", text, &error));
  // 0.9 + 3 * 0.05 = 1.05, wrapped: 0.05.
  EXPECT(std::abs(log.frame_at(0.05f).mechs[0].phase - 0.05f) < 1e-3f);
}

// Walking backward logs a negative rate: it is kept, and the phase runs back.
TEST(replay_v2_phase_runs_back_when_walking_backward) {
  const std::string back = R"({"index":5,"t":0.5,"phase":0.5,"cps":-1.0,"weight":0.25,"limp":-1})";
  const std::string text = kStart + state(0, mech(0, 0, false, back, kParts));
  ReplayLog log;
  std::string error;
  EXPECT(load(&log, "replay_backward", text, &error));
  const auto m = log.frame_at(0.1f).mechs[0];
  EXPECT(m.cps < 0.0f && std::abs(m.phase - 0.4f) < 1e-3f);
}

// A line whose type isn't text, first or last, refuses the log with a message:
// the reader must not throw.
TEST(replay_refuses_a_type_that_is_not_text) {
  ReplayLog first, last;
  std::string error;
  EXPECT(!load(&first, "replay_type_first", R"({"type":5})" "\n", &error) && !error.empty());
  error.clear();
  const std::string text = kStart + state(0, mech(0, 0, false, kPhased, kParts)) + R"({"type":5})" "\n";
  EXPECT(!load(&last, "replay_type_last", text, &error) && error.find("damaged line") != std::string::npos);
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

// #289: --replay3d refuses what --replay does, --replay itself
// and --original; a log's map must be a multiplayer map.
TEST(replay3d_refusals) {
  using mech3::replay::ReplayFlags;
  ReplayFlags f;
  f.replay3d = true;
  EXPECT(mech3::replay::replay3d_refusal(f).empty());
  const auto refused_for = [](ReplayFlags flags, const char* option) {
    return mech3::replay::replay3d_refusal(flags).find(option) != std::string::npos;
  };
  ReplayFlags g = f;
  g.replay = true;
  EXPECT(refused_for(g, "--replay is"));
  g = f, g.play_original = true;
  EXPECT(refused_for(g, "--original"));
  g = f, g.arena = true;
  EXPECT(refused_for(g, "--replay3d: --arena"));
  g = f, g.host = true;
  EXPECT(refused_for(g, "--host"));
  g = f, g.mission = true;
  EXPECT(refused_for(g, "--mission"));
  EXPECT(mech3::replay::replay_map_refusal("c1mp1").empty());
  EXPECT(!mech3::replay::replay_map_refusal("c1m1").empty());   // a campaign mission
  EXPECT(!mech3::replay::replay_map_refusal("c1ia1").empty());  // Instant Action
  EXPECT(!mech3::replay::replay_map_refusal("zz9mp1").empty()); // no such world
  EXPECT(!mech3::replay::replay_map_refusal("").empty());
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

// Infinite or out-of-range angles, phases, rates and blend weights never
// reach the game's animation code (an infinite phase indexed past a clip's
// keys), nor an infinite muzzle the effects.
TEST(replay_resets_non_finite_values) {
  std::string text = kStart;
  // 1e39 is past a float's range: the reader's float is infinite.
  const std::string bad_anim = R"({"index":2,"t":0.5,"phase":1e39,"cps":-500,"weight":7,"limp":-1})";
  std::string bad = mech(0, 0, false, bad_anim, kParts);
  bad.replace(bad.find(R"("heading":0)"), 11, R"("heading":1e39)");
  text += state(0, bad);
  text += R"({"type":"shot","t":0.0,"id":0,"weapon":"AC","muzzle":[1e39,0,0],"dir":[0,0,1]})" "\n";
  ReplayLog log;
  std::string error;
  EXPECT(load(&log, "replay_non_finite", text, &error));
  const Frame f = log.frame_at(0.0f);
  EXPECT(f.mechs.size() == 1);
  const auto& m = f.mechs[0];
  EXPECT(std::isfinite(m.heading) && m.heading == 0.0f);
  EXPECT(m.phase == 0.0f && m.cps == 0.0f && m.weight == 0.0f);
  EXPECT(f.recent.size() == 1 && f.recent[0].muzzle.x == 0.0f);
  EXPECT(log.skipped() == 5);  // heading, phase, cps, weight, muzzle
}

namespace {
bool have_game() { return std::filesystem::exists(std::string(MW3_GAME_DIR) + "/Mech3Msg.dll"); }

std::string temp_dir(const char* name) {
  const std::string d = std::string(MW3_TEST_TMP) + "/" + name;
  std::error_code ec;
  std::filesystem::remove_all(d, ec);
  std::filesystem::create_directories(d, ec);
  return d;
}

struct SavedMounts {
  zutl::Mounts saved = zutl::mounts();
  ~SavedMounts() { zutl::mounts() = saved; }
};
}  // namespace

// #289: --replay3d's run reads a log on a shipped map and opens
// the in-process session with no bots; a log on a map the game lacks, or with
// an unknown chassis, is refused; closing shuts the session.
TEST(replay3d_run_reads_opens_and_closes_headless) {
  if (!have_game()) return;
  SavedMounts keep;
  zutl::mounts() = zutl::Mounts{};
  zutl::mount(MW3_GAME_DIR);
  const auto write = [](const char* name, const std::string& map, const std::string& mech) {
    const std::string path = temp_dir(name) + "/match-1.jsonl";
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    out << R"({"type":"start","version":2,"map":")" << map << R"(","sides":[[{"mech":")" << mech
        << R"("}],[]],"mechs":[{"id":0,"side":0}]})" "\n"
        << R"({"type":"state","t":0,"mechs":[{"id":0,"pos":[0,0,0],"heading":0}]})" "\n";
    return path;
  };
  std::string message;
  {
    mech3::replay::ReplayRun run;
    EXPECT(run.read(write("replay3d_ok", "c1mp1", "madcat"), &message));
    if (!message.empty()) std::printf("  replay3d: %s\n", message.c_str());
    EXPECT(run.map() == "c1mp1" && run.log().mechs().size() == 1);
    EXPECT(run.open(&message) && znet::active());
  }
  EXPECT(!znet::active());  // the session went with the run
  mech3::replay::ReplayRun missing_map;
  EXPECT(!missing_map.read(write("replay3d_map", "c1mp9", "madcat"), &message) &&
         message.find("not in the game files") != std::string::npos);
  mech3::replay::ReplayRun campaign;
  EXPECT(!campaign.read(write("replay3d_campaign", "c1m1", "madcat"), &message) &&
         message.find("not a multiplayer map") != std::string::npos);
  mech3::replay::ReplayRun chassis;
  EXPECT(!chassis.read(write("replay3d_chassis", "c1mp1", "notamech"), &message) &&
         message.find("unknown chassis") != std::string::npos);
}

namespace {
// #289 step 2: a small hand-written log with every line type the replay reads.
std::string replay_test_log(bool with_end) {
  std::string text =
      R"({"type":"start","version":1,"map":"c1mp1","sides":[[{"mech":"madcat"}],[{"mech":"orion"}]],"mechs":[{"id":0,"side":0},{"id":1,"side":1}]})"
      "\n"
      R"({"type":"state","t":0.0,"mechs":[{"id":0,"pos":[0,0,0],"heading":3.0,"torso":{"twist":0},"ai":{"order":"hunt","goal":[50,0,50],"at":0,"contacts":[{"id":1,"seen":true}]}},{"id":1,"pos":[10,0,0],"heading":0,"standing":true}],"rounds":[{"id":0,"by":0,"weapon":"AC","pos":[0,0,0]}],"beams":[{"by":1,"weapon":"L","from":[10,0,0],"to":[0,0,0]}]})"
      "\n"
      R"({"type":"shot","t":0.0,"id":1,"weapon":"L","beam":true,"muzzle":[10,1,0],"dir":[-1,0,0]})"
      "\n"
      R"({"type":"beam_end","t":0.05,"id":1,"weapon":"L"})"
      "\n"
      R"({"type":"route","t":0.05,"id":0,"points":[[1,0,1],[2,0,2]]})"
      "\n"
      R"({"type":"decision","t":0.08,"id":0,"code":"engage"})"
      "\n"
      R"({"type":"state","t":0.1,"mechs":[{"id":0,"pos":[2,0,0],"heading":-3.0},{"id":1,"pos":[10,0,0],"heading":0}],"rounds":[{"id":0,"by":0,"weapon":"AC","pos":[4,0,0]}],"beams":[]})"
      "\n"
      R"({"type":"hit","t":0.12,"id":1,"by":0,"weapon":"AC","damage":1.0})"
      "\n"
      R"({"type":"round_end","t":0.15,"round":0,"pos":[4,0,0]})"
      "\n"
      R"({"type":"destroyed","t":0.18,"id":1,"by":0})"
      "\n"
      R"({"type":"state","t":0.2,"mechs":[{"id":0,"pos":[4,0,0],"heading":-3.0},{"id":1,"pos":[10,0,0],"heading":0,"standing":false}],"rounds":[],"beams":[]})"
      "\n";
  if (with_end) text += R"({"type":"end","t":0.25,"winner":"A","lost":[0,1]})" "\n";
  return text;
}

mech3::replay::ReplayLog replay_load(const std::string& text) {
  const std::string path = temp_dir("replay_log") + "/match-1.jsonl";
  {
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    out << text;
  }
  mech3::replay::ReplayLog log;
  std::string error;
  EXPECT(log.load(path, &error));
  if (!error.empty()) std::printf("  replay: %s\n", error.c_str());
  return log;
}
}  // namespace

// #289 step 2 criterion 2: mechs between two state lines, angles the short
// way, the same frame for the same time whatever was asked before.
TEST(replay_frame_interpolates_and_repeats) {
  const mech3::replay::ReplayLog log = replay_load(replay_test_log(true));
  EXPECT(log.mechs().size() == 2 && log.mechs()[1].chassis == "orion" && log.mechs()[1].side == 1);
  EXPECT(log.map() == "c1mp1" && std::abs(log.duration() - 0.25f) < 1e-4f);
  const mech3::replay::Frame mid = log.frame_at(0.05f);
  EXPECT(mid.mechs.size() == 2 && std::abs(mid.mechs[0].pos.x - 1.0f) < 1e-4f);
  EXPECT(std::abs(mid.mechs[0].heading - 3.1416f) < 0.01f);  // across +-pi, not through 0
  EXPECT(mid.mechs[0].order == "hunt" && mid.mechs[0].has_goal && mid.mechs[0].contacts.size() == 1);
  const mech3::replay::Frame first = log.frame_at(0.15f);
  log.frame_at(0.02f);
  const mech3::replay::Frame again = log.frame_at(0.15f);
  EXPECT(first.mechs.size() == again.mechs.size() && first.mechs[0].pos.x == again.mechs[0].pos.x &&
         first.rounds.size() == again.rounds.size() && first.recent.size() == again.recent.size());
  float box[4];
  log.bounds(box);
  EXPECT(box[0] == 0.0f && box[2] == 50.0f && box[3] == 50.0f);
  EXPECT(log.trail(0, 0.2f, 10.0f).size() == 3);
}

// #289 step 2 criterion 3: rounds and beams start and stop at their lines;
// routes, decisions, hits and deaths show from their times.
TEST(replay_frame_follows_the_events) {
  const mech3::replay::ReplayLog log = replay_load(replay_test_log(true));
  EXPECT(log.frame_at(0.04f).beams.size() == 1);
  EXPECT(log.frame_at(0.06f).beams.empty());  // its beam_end came at 0.05
  const mech3::replay::Frame flying = log.frame_at(0.12f);
  EXPECT(flying.rounds.size() == 1 && flying.rounds[0].pos.x == 4.0f);  // held at its last place
  EXPECT(log.frame_at(0.16f).rounds.empty());                          // its round_end came at 0.15
  EXPECT(log.frame_at(0.04f).routes[0].t < 0 && log.frame_at(0.06f).routes[0].points.size() == 2);
  EXPECT(log.frame_at(0.07f).last_decision[0].type.empty());
  EXPECT(log.frame_at(0.09f).last_decision[0].code == "engage");
  EXPECT(log.frame_at(0.17f).mechs[1].standing && !log.frame_at(0.19f).mechs[1].standing);
  EXPECT(log.frame_at(0.13f).recent.size() == 2);  // the shot at 0 and the hit at 0.12
  const mech3::replay::Frame hit = log.frame_at(0.35f);
  EXPECT(hit.recent.size() == 1 && hit.recent[0].type == "hit" && hit.recent[0].by == 0);
  EXPECT(log.frame_at(0.5f).recent.empty());
}

// #289 step 2: a log stopped before its end line plays to its last state line;
// a missing log and refused options are named.
TEST(replay_log_without_end_and_refusals) {
  const mech3::replay::ReplayLog log = replay_load(replay_test_log(false));
  EXPECT(std::abs(log.duration() - 0.2f) < 1e-4f);
  mech3::replay::ReplayLog missing;
  std::string error;
  EXPECT(!missing.load(temp_dir("replay_missing") + "/none.jsonl", &error) && !error.empty());
  // A wrong-typed field after the start line is refused with a message, not a crash.
  const std::string damaged_path = temp_dir("replay_damaged") + "/match-1.jsonl";
  {
    std::ofstream out(damaged_path, std::ios::binary | std::ios::trunc);
    out << replay_test_log(true) << R"({"type":"state","t":"soon","mechs":[]})" << "\n";
  }
  mech3::replay::ReplayLog damaged;
  error.clear();
  EXPECT(!damaged.load(damaged_path, &error) && error.find("damaged line") != std::string::npos);
  mech3::replay::ReplayFlags flags;
  EXPECT(mech3::replay::replay_refusal(flags).empty());
  flags.arena = true;
  EXPECT(mech3::replay::replay_refusal(flags).find("--arena") != std::string::npos);
  flags = {};
  flags.join = true;
  EXPECT(mech3::replay::replay_refusal(flags).find("--join") != std::string::npos);
  flags = {};
  flags.mission = flags.fly = true;  // --fly sets the mission too
  EXPECT(mech3::replay::replay_refusal(flags).find("--fly") != std::string::npos);
}
