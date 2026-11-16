// #287 (docs/arena.md): the arena run. The setup file and every refusal are
// game-free; reading the map's spawn spots and the presets needs the
// player's game files and skips itself without them.
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <memory>
#include <string>
#include <vector>

#include "arena_counts.h"
#include "check.h"
#include "gamez/znetwork/znet_session.h"
#include "gamez/zutil/zutl_path.h"
#include "mech3/app_mech.h"
#include "mech3/arena.h"
#include "mech3/arena_log.h"
#include "mech3/arena_setup.h"
#include "mech3/mech.h"
#include "mech3/mech_anim.h"
#include "mech3/mech_parts.h"
#include "mech3/mech_names.h"
#include "mech3/mech_net.h"
#include "mech3/replay_log.h"
#include "mech3/replay_run.h"
#include "mech3/weapon.h"
#include "mech3/zai_nav.h"
#include "mech3/zai_params.h"

namespace {
using namespace mech3::arena;

bool have_game() { return std::filesystem::exists(std::string(MW3_GAME_DIR) + "/Mech3Msg.dll"); }

std::string temp_dir(const char* name) {
  const std::string d = std::string(MW3_TEST_TMP) + "/" + name;
  std::error_code ec;
  std::filesystem::remove_all(d, ec);
  std::filesystem::create_directories(d, ec);
  return d;
}

// One bot per side, both on c1mp1's own remote_1 record as their preset (a
// record every multiplayer reader ships, so the game-file tests can read it).
std::string setup_json(const std::string& map = "c1mp1", const std::string& side_a = "",
                       const std::string& extra = "") {
  const std::string bot =
      R"({"mech": "madcat", "preset": {"world": "c1", "mission": "mp1", "record": "remote_1"}})";
  return R"({"map": ")" + map + R"(", "minutes": 10, "out": "arena-out", "sides": [[)" +
         (side_a.empty() ? bot : side_a) + "], [" + bot + "]]" + extra + "}";
}

std::string refused(const std::string& json) {
  Setup s;
  std::string error;
  return parse_arena_setup(json, &s, &error) ? std::string() : error;
}

bool starts_with(const std::string& s, const char* prefix) { return s.rfind(prefix, 0) == 0; }

struct SavedMounts {
  zutl::Mounts saved = zutl::mounts();
  ~SavedMounts() { zutl::mounts() = saved; }
};

int g_shots[kSides], g_hits[kSides];
mech3::arena::ShotStarts g_shot_starts;
bool g_counting = false;
decltype(mech3::WeaponCalls::net_event) g_kept_shot = nullptr;
decltype(mech3::DamageCalls::controls_hit) g_kept_hit = nullptr;

// The match log stops at its end line, while the bots fire on until the run
// exits: count only what the log can see, the frames before the result.
int side_of(const void* mech) {
  if (mech3::arena::arena_result().decided) return -1;
  for (const ArenaMech& entry : arena_mechs())
    if (entry.mech == mech) return entry.side;
  return -1;
}
}  // namespace

namespace arena_counts {
void begin() {
  for (int side = 0; side < kSides; ++side) g_shots[side] = g_hits[side] = 0;
  g_shot_starts.clear();
  g_counting = true;
  g_kept_shot = mech3::weapon_calls().net_event;
  mech3::weapon_calls().net_event = [](auto owner, int32_t kind, mech3::Weapon* w) {
    const int side = side_of(owner);
    if (side >= 0 && g_shot_starts.report(w) == ShotStarts::Report::kNewShot) ++g_shots[side];
    if (g_kept_shot) g_kept_shot(owner, kind, w);
  };
  g_kept_hit = mech3::damage_calls().controls_hit;
  mech3::damage_calls().controls_hit = [](mech3::Mech& m, auto* def, auto* coll, float damage, auto attacker) {
    const int side = side_of(&m);
    if (side >= 0) ++g_hits[side];
    if (g_kept_hit) g_kept_hit(m, def, coll, damage, attacker);
    else if (m.controls) m.controls->on_hit(attacker);
  };
}
void end() {
  if (!g_counting) return;
  g_counting = false;
  mech3::weapon_calls().net_event = g_kept_shot;
  mech3::damage_calls().controls_hit = g_kept_hit;
}
int shots(int side) { return g_shots[side]; }
int hits(int side) { return g_hits[side]; }
nlohmann::json live_pose(int id) {
  const auto round3 = [](float value) { return std::round(static_cast<double>(value) * 1000.0) / 1000.0; };
  nlohmann::json pose = {{"t", round3(mech3::arena::arena_match_time())}};
  for (const auto& entry : mech3::arena::arena_mechs()) {
    if (entry.id != id) continue;
    const mech3::Mech& m = *entry.mech;
    float at[3] = {};
    mech3::program_vehicle_centre(const_cast<mech3::Mech*>(&m), at);
    const float yaw = 2.0f * std::atan2(m.orientation[2], m.orientation[0]);
    nlohmann::json arms = nlohmann::json::array();
    for (int side = 0; side < 2; ++side)
      arms.push_back(m.arms[side] ? nlohmann::json{{"yaw", round3(m.arms[side]->aim_yaw)},
                                                   {"pitch", round3(m.arms[side]->aim_pitch)}}
                                  : nlohmann::json(nullptr));
    const mech3::MechAnim* anim = m.anims[m.anim_index];
    pose["mech"] = {
        {"pos", {round3(at[0]), round3(at[1]), round3(at[2])}},
        {"heading", round3(yaw)},
        {"torso", {{"twist", round3(m.torso->yaw)}, {"pitch", round3(m.torso->pitch)}}},
        {"arms", arms},
        {"anim", {{"index", m.anim_index}, {"t", round3(anim ? anim->t : 0.0f)}}},
        {"jumping", m.airborne()},
        {"fallen", m.anim_state == mech3::arena::kAnimFallenBack || m.anim_state == mech3::arena::kAnimFallenFront},
        {"heat", round3(m.heat)},
    };
  }
  return pose;
}

bool standing(const mech3::Mech* mech) { return mech3::arena::arena_standing(mech); }
bool is_bot(const mech3::Mech* mech) { return mech->arena_bot; }
}  // namespace arena_counts

TEST(arena_setup_reads_a_good_setup) {
  Setup s;
  std::string error;
  EXPECT(parse_arena_setup(setup_json("c3mp3"), &s, &error));
  EXPECT(error.empty());
  EXPECT(s.map == "c3mp3" && s.dir == "c3" && s.number == 3);
  EXPECT(s.minutes == 10 && s.out == "arena-out");
  EXPECT(s.sides[0].size() == 1 && s.sides[1].size() == 1);
  EXPECT(s.sides[0][0].mech == mech3::mech_index("madcat"));
  EXPECT(s.sides[1][0].preset.world == "c1" && s.sides[1][0].preset.mission == "mp1");
  EXPECT(s.sides[1][0].preset.record == "remote_1");
  EXPECT(!s.sides[0][0].params_read);
}

TEST(arena_setup_takes_eight_a_side) {
  std::string eight;
  for (int i = 0; i < 8; ++i)
    eight += std::string(i ? ", " : "") +
             R"({"mech": "thor", "preset": {"world": "c2", "mission": "ia1", "record": "x"}})";
  Setup s;
  std::string error;
  EXPECT(parse_arena_setup(setup_json("c1mp1", eight), &s, &error));
  EXPECT(s.sides[0].size() == 8);
}

TEST(arena_setup_refuses_more_than_eight_a_side) {
  std::string nine;
  for (int i = 0; i < 9; ++i)
    nine += std::string(i ? ", " : "") +
            R"({"mech": "thor", "preset": {"world": "c2", "mission": "ia1", "record": "x"}})";
  EXPECT(starts_with(refused(setup_json("c1mp1", nine)), "sides[0]: 9 bots"));
}

TEST(arena_setup_refuses_bad_maps) {
  EXPECT(starts_with(refused(setup_json("c9mp1")), "map: unknown map"));
  EXPECT(starts_with(refused(setup_json("c1m2")), "map: unknown map"));
  EXPECT(starts_with(refused(setup_json("c1mp")), "map: unknown map"));
  EXPECT(starts_with(refused(setup_json("mp1")), "map: unknown map"));
  EXPECT(starts_with(refused(R"({"minutes": 10})"), "map:"));
}

TEST(arena_setup_refuses_unknown_mechs) {
  const std::string notmech =
      R"({"mech": "notmech", "preset": {"world": "c1", "mission": "mp1", "record": "remote_1"}})";
  EXPECT(starts_with(refused(setup_json("c1mp1", notmech)), "sides[0][0].mech: unknown mech \"notmech\""));
  const std::string nonsense =
      R"({"mech": "toaster", "preset": {"world": "c1", "mission": "mp1", "record": "remote_1"}})";
  EXPECT(starts_with(refused(setup_json("c1mp1", nonsense)), "sides[0][0].mech: unknown mech"));
  EXPECT(starts_with(refused(setup_json("c1mp1", R"({"preset": {}})")), "sides[0][0].mech:"));
}

TEST(arena_setup_refuses_bad_presets) {
  EXPECT(starts_with(refused(setup_json("c1mp1", R"({"mech": "madcat"})")), "sides[0][0].preset:"));
  EXPECT(starts_with(
      refused(setup_json("c1mp1", R"({"mech": "madcat", "preset": {"world": "c9", "mission": "ia1", "record": "x"}})")),
      "sides[0][0].preset.world:"));
  EXPECT(starts_with(
      refused(setup_json("c1mp1", R"({"mech": "madcat", "preset": {"world": "c1", "mission": "zz", "record": "x"}})")),
      "sides[0][0].preset.mission:"));
  EXPECT(starts_with(
      refused(setup_json("c1mp1", R"({"mech": "madcat", "preset": {"world": "c1", "mission": "ia1"}})")),
      "sides[0][0].preset.record:"));
}

TEST(arena_setup_refuses_bad_minutes_out_and_sides) {
  EXPECT(starts_with(refused(R"({"map": "c1mp1", "minutes": 0, "out": "o", "sides": [[], []]})"), "minutes:"));
  EXPECT(starts_with(refused(R"({"map": "c1mp1", "minutes": 1.5, "out": "o", "sides": [[], []]})"), "minutes:"));
  EXPECT(starts_with(refused(R"({"map": "c1mp1", "minutes": 5, "sides": [[], []]})"), "out:"));
  EXPECT(starts_with(refused(R"({"map": "c1mp1", "minutes": 5, "out": "o", "sides": [[]]})"), "sides:"));
  EXPECT(starts_with(refused(R"({"map": "c1mp1", "minutes": 5, "out": "o", "sides": [[], []]})"), "sides[0]:"));
  EXPECT(starts_with(refused("not json"), "setup:"));
}

TEST(arena_setup_refuses_a_missing_file) {
  Setup s;
  std::string error;
  EXPECT(!read_arena_setup(temp_dir("arena_setup_missing") + "/none.json", &s, &error));
  EXPECT(starts_with(error, "setup: cannot read"));
}

TEST(arena_refusals_pass_a_plain_arena_run) {
  Flags f;
  f.seed = f.frame_ms = true;
  EXPECT(arena_refusal(f).empty());
}

TEST(arena_refusals_name_every_refused_option) {
  struct Case {
    bool Flags::*flag;
    const char* option;
  };
  const Case cases[] = {{&Flags::host, "--host"},           {&Flags::join, "--join"},
                        {&Flags::net_upnp, "--net-upnp"},   {&Flags::original, "--original"},
                        {&Flags::mission, "--mission"},     {&Flags::net_minutes, "--net-minutes"},
                        {&Flags::net_soak, "--net-soak"},   {&Flags::net_drive, "--net-drive"},
                        {&Flags::frames, "--frames"},       {&Flags::fire, "--fire"},
                        {&Flags::net_walk, "--net-walk"},   {&Flags::net_ahead, "--net-ahead"},
                        {&Flags::briefing, "--briefing"},   {&Flags::lab_mech, "--lab-mech"}};
  for (const Case& c : cases) {
    Flags f;
    f.seed = f.frame_ms = true;
    f.*c.flag = true;
    const std::string message = arena_refusal(f);
    EXPECT(message.find(c.option) != std::string::npos);
  }
}

TEST(arena_refusals_need_a_seed_and_a_frame_time) {
  Flags f;
  f.frame_ms = true;
  EXPECT(arena_refusal(f).find("--seed") != std::string::npos);
  f.frame_ms = false, f.seed = true;
  EXPECT(arena_refusal(f).find("--frame-ms") != std::string::npos);
}

TEST(arena_setup_log_is_created_once) {
  Setup s;
  s.out = temp_dir("arena_setup_log") + "/runs";
  std::string path, error;
  {
    LogFile f = create_arena_log(s, 7, &path, &error);
    EXPECT(f != nullptr);
    EXPECT(path.find("match-7.jsonl") != std::string::npos);
    std::fputs("kept", f.get());
  }
  LogFile again = create_arena_log(s, 7, &path, &error);
  EXPECT(again == nullptr);
  EXPECT(starts_with(error, "out:") && error.find("already exists") != std::string::npos);
  std::ifstream kept(path);
  std::string text;
  std::getline(kept, text);
  EXPECT(text == "kept");  // the existing file left as it is
}

TEST(arena_setup_game_files_read_the_map_and_presets) {
  if (!have_game()) return;
  SavedMounts keep;
  zutl::mounts() = zutl::Mounts{};
  zutl::mount(MW3_GAME_DIR);
  Setup s;
  std::string error;
  EXPECT(parse_arena_setup(setup_json(), &s, &error));
  EXPECT(read_arena_game_files(&s, &error));
  if (!error.empty()) std::printf("  arena: %s\n", error.c_str());
  EXPECT(error.empty());
  EXPECT(s.sides[0][0].params_read && s.sides[1][0].params_read);
  // The same record read the same way: one copy each, equal bytes.
  EXPECT(s.sides[0][0].params == s.sides[1][0].params);
  // Every lobby map has its 16 spots.
  for (const char* map : {"c1mp1", "c1mp2", "c2mp1", "c2mp2", "c3mp1", "c3mp2", "c3mp3", "c3mp4", "c4mp1", "c4mp2"}) {
    EXPECT(parse_arena_setup(setup_json(map), &s, &error));
    EXPECT(read_arena_game_files(&s, &error));
  }
}

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

TEST(arena_setup_game_files_refuse_a_map_without_16_spots) {
  if (!have_game()) return;
  SavedMounts keep;
  zutl::mounts() = zutl::Mounts{};
  zutl::mount(MW3_GAME_DIR);
  Setup s;
  std::string error;
  EXPECT(parse_arena_setup(setup_json("t1mp1"), &s, &error));
  EXPECT(!read_arena_game_files(&s, &error));
  EXPECT(error.find("16 remote_") != std::string::npos);
  EXPECT(parse_arena_setup(setup_json("c1mp7"), &s, &error));
  EXPECT(!read_arena_game_files(&s, &error));
  EXPECT(starts_with(error, "map: unknown map"));
}

TEST(arena_setup_game_files_refuse_an_unknown_preset) {
  if (!have_game()) return;
  SavedMounts keep;
  zutl::mounts() = zutl::Mounts{};
  zutl::mount(MW3_GAME_DIR);
  const std::string no_record =
      R"({"mech": "madcat", "preset": {"world": "c1", "mission": "mp1", "record": "no_such_record"}})";
  Setup s;
  std::string error;
  EXPECT(parse_arena_setup(setup_json("c1mp1", no_record), &s, &error));
  EXPECT(!read_arena_game_files(&s, &error));
  EXPECT(starts_with(error, "sides[0][0].preset: no record"));
  const std::string no_reader =
      R"({"mech": "madcat", "preset": {"world": "c1", "mission": "m9", "record": "x"}})";
  EXPECT(parse_arena_setup(setup_json("c1mp1", no_reader), &s, &error));
  EXPECT(!read_arena_game_files(&s, &error));
  EXPECT(starts_with(error, "sides[0][0].preset: cannot read"));
}

// Criterion 6: the arena's session runs on the in-process hub. The ENet
// transport lives in the SDL front end, which this suite does not link, so
// the check is that zNetwork's transport is the hub's endpoint and nothing else.
TEST(arena_session_uses_the_hub) {
  znet::Hub hub;
  znet::Transport* endpoint = arena_open_session(hub);
  EXPECT(endpoint != nullptr);
  EXPECT(znet::session().transport == endpoint);
  EXPECT(znet::active() && znet::is_host() && znet::local_id() == 1);
  EXPECT(znet::session().desc.max_players == kArenaPlayers);
  znet::shutdown();
  EXPECT(!znet::session().initialised);
}

// A bot is made as a local mech, so the network would send its state, its
// shots and its death as the host player's; marked, nothing goes out for it
// (net_send_event's every kind). An unmarked mech still queues its part
// damage for the next state, so the session is live.
TEST(arena_bot_sends_no_net_events) {
  znet::Hub hub;
  EXPECT(arena_open_session(hub) != nullptr);
  mech3::NetCalls kept = mech3::net_calls();
  mech3::net_calls() = mech3::NetCalls{};
  mech3::net_start();
  auto host = std::make_unique<mech3::Mech>();
  auto bot = std::make_unique<mech3::Mech>();
  bot->arena_bot = true;
  const int part = 3;
  mech3::net_send_event(*host, 0x15, part);
  mech3::net_send_event(*bot, 0x15, part);
  EXPECT(host->net_damaged == 1u << part);
  EXPECT(bot->net_damaged == 0);
  EXPECT(mech3::net_send_event(*bot, 0xf, 0) == 0);
  EXPECT(mech3::net_send_event(*bot, 0x13, 0) == 0);
  mech3::net_end();
  mech3::net_calls() = kept;
  znet::shutdown();
}

// The sides start at opposite ends: the seed picks one of the three farthest
// spot pairs (seed % 3) and which end is side A's ((seed / 3) % 2); each side
// takes the free spots nearest its end, ties to the lower spot number
// (research/mw3-ai/spawn-spots.md).
TEST(arena_spawn_spots_at_opposite_ends) {
  // Spots on a line, spot n at x = 10 n. The farthest pairs: (0, 15) at
  // 150 m, then (0, 14) and (1, 15) at 140 m, in that order.
  float spots[kSpawnSpots][3] = {};
  for (int spot = 0; spot < kSpawnSpots; ++spot) spots[spot][0] = static_cast<float>(spot * 10);
  EXPECT((arena_spawn_spots(spots, 2, 2, 0) == std::vector<int>{0, 1, 15, 14}));
  EXPECT((arena_spawn_spots(spots, 2, 2, 3) == std::vector<int>{15, 14, 0, 1}));  // the ends swapped
  // The second pair: side B's end is 14, with 13 and 15 tied next to it.
  EXPECT((arena_spawn_spots(spots, 2, 2, 1) == std::vector<int>{0, 1, 14, 13}));
  // The third: side A's end is 1, with 0 and 2 tied next to it.
  EXPECT((arena_spawn_spots(spots, 2, 2, 2) == std::vector<int>{1, 0, 15, 14}));
  EXPECT((arena_spawn_spots(spots, 3, 1, 0) == std::vector<int>{0, 1, 2, 15}));
  // A full match uses every spot once; the same seed always gives the same.
  const std::vector<int> full = arena_spawn_spots(spots, 8, 8, 5);
  EXPECT(full == arena_spawn_spots(spots, 8, 8, 5));
  std::vector<int> sorted = full;
  std::sort(sorted.begin(), sorted.end());
  EXPECT(sorted.size() == 16);
  for (size_t spot = 0; spot < sorted.size(); ++spot) EXPECT(sorted[spot] == static_cast<int>(spot));
}

// A bot's params are the preset's but for its place, team, loadout and the
// three switches the arena sets (criterion 11's other half, game-free).
// #287 criterion 12: a log with no end line reads as incomplete; a line that
// does not parse is counted and skipped; a field the reader does not know is
// kept in its record.
TEST(arena_log_reader_reports_incomplete_logs) {
  const std::string path = temp_dir("arena_log_reader") + "/match-1.jsonl";
  {
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    out << R"({"type":"start","version":1,"map":"c1mp1"})" << "\n";
    out << "{not json\n";
    out << R"({"type":"state","t":0.1,"mechs":[],"future_field":7})" << "\n";
  }
  LogRead read = read_arena_log(path);
  EXPECT(read.opened && read.records.size() == 2 && read.bad_lines == 1 && !read.complete);
  EXPECT(read.records.size() == 2 && read.records[1].value("future_field", 0) == 7);
  {
    std::ofstream out(path, std::ios::binary | std::ios::app);
    out << R"({"type":"end","winner":"A","t":82.1,"lost":[0,1]})" << "\n";
  }
  read = read_arena_log(path);
  EXPECT(read.complete && read.records.size() == 3);
  EXPECT(!read_arena_log(path + ".missing").opened);
}

// #289 criterion 1: a log with no format version, or one this build doesn't
// know, is refused with a message naming it; versions 1 and 2 read.
TEST(arena_log_reader_refuses_missing_or_unknown_version) {
  const std::string path = temp_dir("arena_log_version") + "/match-1.jsonl";
  const auto read_with_start = [&](const char* start_line) {
    {
      std::ofstream out(path, std::ios::binary | std::ios::trunc);
      out << start_line << "\n";
      out << R"({"type":"end","winner":"A","t":1.0,"lost":[0,1]})" << "\n";
    }
    return read_arena_log(path);
  };
  LogRead read = read_with_start(R"({"type":"start","map":"c1mp1"})");
  EXPECT(read.opened && read.records.empty() && !read.complete);
  EXPECT(read.error.find("format version (a log from before") != std::string::npos);
  read = read_with_start(R"({"type":"start","version":3,"map":"c1mp1"})");
  EXPECT(read.records.empty() && read.error.find("format version 3") != std::string::npos);
  EXPECT(read.error.find("versions 1 and 2") != std::string::npos);
  read = read_with_start(R"({"type":"start","version":0,"map":"c1mp1"})");
  EXPECT(read.records.empty() && read.error.find("format version 0") != std::string::npos);
  read = read_with_start(R"(not json)");
  EXPECT(read.records.empty() && read.error.find("no readable start line") != std::string::npos);
  read = read_with_start(R"({"type":"start","version":1,"map":"c1mp1"})");
  EXPECT(read.error.empty() && read.records.size() == 2 && read.complete);
  read = read_with_start(R"({"type":"start","version":2,"map":"c1mp1"})");
  EXPECT(read.error.empty() && read.records.size() == 2 && read.complete);
}

// #289 criterion 3, game-free: rounds keep their ids across state lines and
// end once; a reused slot ends the old round; a round that never reached a
// state line, or a slot the hook never recorded, writes nothing.
TEST(arena_round_book_keeps_ids_and_ends_rounds) {
  int slots[4] = {};
  int owners[2] = {};  // two shooters' scene nodes
  const void* a = &owners[0];
  const void* b = &owners[1];
  const auto seen = [](const void* slot, float age, float x, const void* owner) {
    return RoundSeen{slot, age, {x, 0, 0}, owner};
  };
  const auto run = [&] {
    RoundBook book;
    std::vector<nlohmann::json> walks, ended_all;
    const auto walk = [&](const std::vector<RoundSeen>& flying) {
      std::vector<nlohmann::json> ended;
      walks.push_back(book.walk(flying, &ended));
      for (nlohmann::json& record : ended) ended_all.push_back(record);
      return ended;
    };
    book.shot(&slots[0], a, 2, "LRM20");
    book.shot(&slots[1], b, 3, "AC10");
    // The first walk: both get ids, in walk order; slots[2] was never recorded.
    walk({seen(&slots[1], 0.05f, 1, b), seen(&slots[0], 0.05f, 2, a), seen(&slots[2], 0.05f, 3, a)});
    // slots[0] is gone: it ends once at its last position.
    EXPECT(walk({seen(&slots[1], 0.15f, 4, b)}).size() == 1);
    // slots[1] reused by a shot the hook never saw (its age went down): ends.
    EXPECT(walk({seen(&slots[1], 0.01f, 5, b)}).size() == 1);
    // A round fired and gone between two walks: no record at all.
    book.shot(&slots[3], a, 1, "MG");
    EXPECT(walk({}).empty());
    // A slot reused by a recorded shot ends the old round with its id.
    book.shot(&slots[0], a, 2, "LRM20");
    walk({seen(&slots[0], 0.05f, 6, a)});
    book.shot(&slots[0], b, 3, "SRM6");
    const std::vector<nlohmann::json> reused = walk({seen(&slots[0], 0.02f, 7, b)});
    EXPECT(reused.size() == 1);
    // Reused by another shooter the hook never saw, though older: ends, and
    // the stranger's round is not listed as ours.
    book.shot(&slots[2], a, 1, "MG");
    walk({seen(&slots[2], 0.05f, 8, a)});
    EXPECT(walk({seen(&slots[2], 0.2f, 9, b)}).size() == 1);
    // A round with no id yet whose slot a stranger took: forgotten, no record.
    book.shot(&slots[3], a, 1, "MG");
    EXPECT(walk({seen(&slots[3], 0.05f, 10, b)}).empty());
    return std::make_pair(walks, ended_all);
  };
  const auto first = run();
  const auto second = run();
  EXPECT(first == second);  // the same calls give the same ids and records
  const std::vector<nlohmann::json>& walks = first.first;
  const std::vector<nlohmann::json>& ended = first.second;
  EXPECT(walks.size() == 9 && walks[0].size() == 2);
  EXPECT(walks[0][0]["id"] == 0 && walks[0][0]["by"] == 3 && walks[0][1]["id"] == 1 && walks[0][1]["by"] == 2);
  EXPECT(walks[1].size() == 1 && walks[1][0]["id"] == 0 && walks[1][0]["pos"][0] == 4.0);
  EXPECT(walks[2].empty());  // the reused slot's new round is not ours
  EXPECT(ended.size() == 5);  // the SRM6 round ends when slots[2]'s walk leaves it out
  EXPECT(ended[3]["round"] == 3 && ended[3]["pos"][0] == 7.0);
  EXPECT(ended[4]["round"] == 4 && ended[4]["pos"][0] == 8.0);
  EXPECT(walks[7].empty() && walks[8].empty());
  EXPECT(ended[0]["type"] == "round_end" && ended[0]["round"] == 1 && ended[0]["pos"][0] == 2.0);
  EXPECT(ended[1]["round"] == 0 && ended[1]["pos"][0] == 4.0);
  EXPECT(ended[2]["round"] == 2 && ended[2]["pos"][0] == 6.0);
  EXPECT(walks[5].size() == 1 && walks[5][0]["id"] == 3 && walks[5][0]["weapon"] == "SRM6");
}

// #289 criterion 2, game-free: a beam reports a new shot when it turns on,
// held while it stays on, and ended once when it stops.
TEST(arena_shot_starts_reports_beam_end) {
  static mech3::WeaponType type;
  static mech3::WeaponManager manager(nullptr);
  zwep::WeaponDef def{};
  def.type = &type;
  using Report = ShotStarts::Report;
  ShotStarts starts;
  {
    mech3::BeamWeapon beam(&def, nullptr, &manager);
    beam.firing = true;
    EXPECT(starts.report(&beam) == Report::kNewShot);
    EXPECT(starts.report(&beam) == Report::kHeld);
    beam.firing = false;
    EXPECT(starts.report(&beam) == Report::kEnded);
    EXPECT(starts.report(&beam) == Report::kHeld);  // a second stop report is not a second end
  }
  EXPECT(starts.report(nullptr) == Report::kNewShot);
}

// #289 criterion 4, game-free: a route line only when the bot's follower
// changed (a new order's, or none) or found a path again.
TEST(arena_route_change_rule) {
  mech3::ai::nav::Follower hunt_follower, fight_follower;
  RouteSeen last;
  EXPECT(!route_changed(last, nullptr));  // no follower, as before
  EXPECT(route_changed(last, &hunt_follower));
  EXPECT(!route_changed(last, &hunt_follower));
  ++hunt_follower.paths;
  EXPECT(route_changed(last, &hunt_follower));
  ++hunt_follower.repaths;
  EXPECT(route_changed(last, &hunt_follower));
  ++hunt_follower.waypoints;  // walking on along the same path is no change
  EXPECT(!route_changed(last, &hunt_follower));
  EXPECT(route_changed(last, &fight_follower));
  EXPECT(route_changed(last, nullptr));
}

// #289 criterion 7: the AI's decision note is set only while an arena match
// is logged with detail on, so no other game runs anything new.
TEST(arena_decision_note_is_unset_outside_a_match) {
  using mech3::ai::decision_note;
  std::FILE* file = std::tmpfile();
  EXPECT(file != nullptr);
  set_arena_log(file, 16);
  const Setup setup;
  const std::vector<ArenaMech> mechs;
  EXPECT(decision_note() == nullptr);
  log_match_start(setup, mechs);
  EXPECT(decision_note() != nullptr);
  log_match_end(Result{});
  EXPECT(decision_note() == nullptr);
  log_match_start(setup, mechs);
  EXPECT(decision_note() != nullptr);
  log_match_stop();
  EXPECT(decision_note() == nullptr);
  set_arena_log_detail(false);
  log_match_start(setup, mechs);
  EXPECT(decision_note() == nullptr);
  log_match_stop();
  set_arena_log_detail(true);
  set_arena_log(nullptr, 0);
  if (file) std::fclose(file);
}

// #289 criterion 5, game-free: a decision record for each order or target
// change and for no other frame, with the reason noted since the last frame
// or the fallback.
TEST(arena_decision_book_follows_the_rules) {
  using mech3::ai::Decision;
  int hunt = 0, fight = 0;
  const OrderKey hunting{&hunt, 1}, fighting{&fight, 2};
  DecisionBook book;
  EXPECT(book.frame(hunting, -1, "contact").empty());  // the baseline
  EXPECT(book.frame(hunting, -1, "contact").empty());
  // A note with no change gives nothing, and is gone by the next change.
  book.note(Decision::kEngage);
  EXPECT(book.frame(hunting, -1, "contact").empty());
  std::vector<nlohmann::json> records = book.frame(fighting, -1, nullptr);
  EXPECT(records.size() == 1 && records[0]["code"] == "order_other");
  // Back to the hunt: its goal rule is the reason.
  records = book.frame(hunting, -1, "last_seen");
  EXPECT(records.size() == 1 && records[0]["code"] == "hunt_last_seen");
  // Engage noted: the order change says so; a target change with it, the order first.
  book.note(Decision::kEngage);
  book.note(Decision::kTargetVolley);
  records = book.frame(fighting, 5, nullptr);
  EXPECT(records.size() == 2 && records[0]["code"] == "engage");
  EXPECT(records.size() == 2 && records[1]["code"] == "target_volley" && records[1]["target"] == 5);
  book.note(Decision::kTargetLost);
  records = book.frame(fighting, 6, nullptr);
  EXPECT(records.size() == 1 && records[0]["code"] == "target_lost" && records[0]["target"] == 6);
  records = book.frame(fighting, -1, nullptr);
  EXPECT(records.size() == 1 && records[0]["code"] == "target_other" && records[0]["target"] == -1);
  // The same state at a different stack depth is a new order.
  records = book.frame(OrderKey{&fight, 3}, -1, nullptr);
  EXPECT(records.size() == 1 && records[0]["code"] == "order_other");
}

TEST(arena_bot_params_change_only_the_arena_fields) {
  Bot bot;
  for (size_t i = 0; i < bot.params.size(); ++i) bot.params[i] = static_cast<uint8_t>(i * 7 + 1);
  bot.params_read = true;
  const float pos[3] = {1.5f, 2.5f, 3.5f};
  mech3::ai::AiParams params;
  arena_bot_params(bot, 1, pos, 0.25f, &params);
  EXPECT(params.get<float>(0x08) == 1.5f && params.get<float>(0x0c) == 2.5f && params.get<float>(0x10) == 3.5f);
  EXPECT(params.get<float>(0x14) == 0.25f);
  EXPECT(params.team() == 2);
  EXPECT(params.get<int32_t>(0xbc) == 0 && params.get<int32_t>(0x3c) == 1);
  EXPECT(params.get<int32_t>(0x88) == 1 && params.get<int32_t>(0x8c) == 0);
  // Never a lancemate: +0xcd's low two bits off, its other bits kept.
  EXPECT((params.raw[0xcd] & 3) == 0 && (params.raw[0xcd] & ~3) == (bot.params[0xcd] & ~3));
  const auto changed = [](int off) {
    const int fields[] = {0x08, 0x0c, 0x10, 0x14, 0x18, 0x3c, 0x88, 0x8c, 0xbc};
    for (int field : fields)
      if (off >= field && off < field + 4) return true;
    return off == 0xcd;
  };
  int other_bytes_differ = 0;
  for (int off = mech3::ai::AiParams::kBegin; off < mech3::ai::AiParams::kEnd; ++off)
    if (!changed(off) && params.raw[off] != bot.params[static_cast<size_t>(off)]) ++other_bytes_differ;
  EXPECT(other_bytes_differ == 0);
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
