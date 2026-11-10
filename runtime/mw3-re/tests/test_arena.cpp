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
#include "mech3/weapon.h"
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
bool g_counting = false;
decltype(mech3::WeaponCalls::net_event) g_kept_shot = nullptr;
decltype(mech3::DamageCalls::controls_hit) g_kept_hit = nullptr;

int side_of(const void* mech) {
  for (const ArenaMech& entry : arena_mechs())
    if (entry.mech == mech) return entry.side;
  return -1;
}
}  // namespace

namespace arena_counts {
void begin() {
  for (int side = 0; side < kSides; ++side) g_shots[side] = g_hits[side] = 0;
  g_counting = true;
  g_kept_shot = mech3::weapon_calls().net_event;
  mech3::weapon_calls().net_event = [](auto owner, int32_t kind, mech3::Weapon* w) {
    const int side = side_of(owner);
    if (side >= 0) ++g_shots[side];
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
        {"fallen", m.anim_state == 12 || m.anim_state == 13},
        {"heat", round3(m.heat)},
    };
  }
  return pose;
}

bool standing(const mech3::Mech* mech) { return mech->active; }
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
                        {&Flags::frames, "--frames"}};
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

// Q3: side A's other bots take the free spots nearest the host's (spot 1),
// side B's the farthest; equal distances go to the lower spot number.
TEST(arena_spawn_spots_by_distance) {
  float spots[kSpawnSpots][3] = {};
  // Spot n at x = |n - 1| * 10, so spot 0 and 2 tie at 10 m, 3 is 20 m ...
  // except 15 and 14, put at 1000 m and 1000 m (a tie at the far end).
  for (int spot = 0; spot < kSpawnSpots; ++spot) spots[spot][0] = static_cast<float>((spot > 1 ? spot - 1 : 1 - spot) * 10);
  spots[14][0] = spots[15][0] = 1000.0f;
  const std::vector<int> two_two = arena_spawn_spots(spots, 2, 2);
  EXPECT((two_two == std::vector<int>{1, 0, 14, 15}));
  const std::vector<int> three_one = arena_spawn_spots(spots, 3, 1);
  EXPECT((three_one == std::vector<int>{1, 0, 2, 14}));
  const std::vector<int> full = arena_spawn_spots(spots, 8, 8);
  EXPECT(full.size() == 16 && full[0] == 1);
  std::vector<int> sorted = full;
  std::sort(sorted.begin(), sorted.end());
  for (int spot = 0; spot < kSpawnSpots; ++spot) EXPECT(sorted[static_cast<size_t>(spot)] == spot);
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
    out << R"({"type":"start","map":"c1mp1"})" << "\n";
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
