// #287 (docs/arena.md): the arena run. The setup file and every refusal are
// game-free; reading the map's spawn spots and the presets needs the
// player's game files and skips itself without them.
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <string>

#include "check.h"
#include "gamez/zutil/zutl_path.h"
#include "mech3/arena_setup.h"
#include "mech3/mech_names.h"
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
}  // namespace

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
