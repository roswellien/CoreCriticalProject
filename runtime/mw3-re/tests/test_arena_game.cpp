// #287 and #289: the arena and the replay on the real game, run headless as
// mw3 --arena runs them. They were in test_program.cpp, whose fake window,
// clock and mounts guard they share through program_harness.h.
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <functional>
#include <map>
#include <set>
#include <string>
#include <tuple>
#include <vector>

#include "check.h"
#include "gamez/zreader/zreader.h"
#include "gamez/znetwork/znet_object.h"
#include "gamez/znetwork/znet_session.h"
#include "gamez/zutil/zutl_path.h"
#include "mech3/app.h"
#include "mech3/app_engine.h"
#include "mech3/app_mech.h"
#include "mech3/app_states.h"
#include "mech3/app_view.h"
#include "mech3/arena.h"
#include "mech3/arena_catalog.h"
#include "mech3/arena_log.h"
#include "mech3/mech_control.h"
#include "mech3/mech_names.h"
#include "mech3/mission.h"
#include "mech3/mission_world.h"
#include "mech3/mp_lobby.h"
#include "mech3/options.h"
#include "mech3/pilot.h"
#include "mech3/replay_terrain.h"
#include "mech3/zai_brain.h"
#include "mech3/zai_params.h"
#include "mech3/zrdraiv.h"
#include "platform/silent_sound.h"
#include "arena_counts.h"
#include "program_harness.h"
#include "replay_game.h"

namespace {
// #287: an arena match run headless, as mw3 --arena runs it, from a setup's
// JSON text. `on_core` sees each Core frame (from 1); the run stops after
// `max_core_frames` of them, when `stop` says so, or when the mission ends.
struct ArenaRunResult {
  int core_frames = 0;
  bool setup_read = false;
  std::string log_path;  // the run's match log, as mw3 --arena writes it (seed 1, 16 ms)
};
ArenaRunResult arena_headless_run(const std::string& json, int max_core_frames,
                                  const std::function<void(int)>& on_core,
                                  const std::function<bool()>& stop = nullptr) {
  ArenaRunResult result;
  SavedMounts keep;
  zutl::mounts() = zutl::Mounts{};
  zutl::mount(MW3_GAME_DIR);
  zutl::set_write_dir(temp_dir("arena_run_write"));
  mech3::arena::Setup setup;
  std::string error;
  result.setup_read = mech3::arena::parse_arena_setup(json, &setup, &error) &&
                      mech3::arena::read_arena_game_files(&setup, &error);
  if (!result.setup_read) {
    std::printf("  arena: %s\n", error.c_str());
    return result;
  }
  mech3::reset_states();
  reset_process_state();
  mech3::missions() = mech3::Missions{};
  mech3::mech_types_forget();
  mech3::player_controls_instance() = nullptr;
  mech3::options() = mech3::Options{};
  FakeWindow window;
  FakeAlert alert;
  FakeClock clock;
  FakeScreen screen;
  platform::SilentSoundOutput sound;
  mech3::MountFiles files;
  mech3::Platform p;
  p.window = &window, p.alert = &alert, p.clock = &clock, p.movie_clock = &fast_movie_clock(), p.screen = &screen, p.sound = &sound, p.files = &files;
  znet::Hub hub;
  EXPECT(mech3::arena::arena_open_session(hub) != nullptr);
  // A fresh log each run (the arena never writes over one).
  static int s_run = 0;
  setup.out = temp_dir("arena_run_log") + "/" + std::to_string(++s_run);
  std::filesystem::remove_all(setup.out);
  mech3::arena::LogFile log = mech3::arena::create_arena_log(setup, 1, &result.log_path, &error);
  EXPECT(log != nullptr);
  mech3::arena::set_arena_setup(&setup);
  mech3::arena::set_arena_log(log.get(), 16);
  mech3::arena::set_arena_seed(1);
  {
    mech3::GameEngine engine(p, "mech3.exe -nofmv");
    engine.quiet = true;
    mech3::Mech3App app(&engine);
    mech3::set_app(&app);
    EXPECT(app.init_instance());
    mech3::MultiplayerGame game(nullptr);
    game.x70 = 1 << 30;
    game.b8c = 0;
    mech3::GameEngine::Launch l;
    l.spectator = true;  // the host's seat has no mech (#287 step 3b)
    // The setup's world, as mw3 --arena finds it (mw3_main.cpp: the dir among mission_dir).
    l.index = -1;
    for (int32_t i = 0; i < 9; ++i)
      if (setup.dir == mech3::mission_dir(i)) l.index = i;
    EXPECT(l.index >= 0);
    l.number = setup.number, l.type = 3, l.multi = &game;
    engine.set_launch(l);
    mech3::program_net_debug_lobby();
    app.post_intro_ = &mech3::states().load;
    bool left_core = false;
    engine.on_present = [&](int) {
      if (app.current() != &mech3::states().core) {
        left_core = left_core || result.core_frames > 0;
        return;
      }
      ++result.core_frames;
      on_core(result.core_frames);
    };
    CountingPump pump;
    pump.limit = max_core_frames + 2600;
    pump.stop = [&] { return result.core_frames >= max_core_frames || left_core || (stop && stop()); };
    app.run(pump);
    mech3::missions().cleanup(false);
    app.stop_game();
    app.exit_instance();
    mech3::set_app(nullptr);
  }
  mech3::arena::set_arena_setup(nullptr);
  mech3::arena::set_arena_log(nullptr, 0);
  log.reset();
  znet::shutdown();
  zrdr::close_archives(true);
  mech3::reset_states();
  reset_process_state();
  mech3::missions() = mech3::Missions{};
  mech3::mech_types_forget();
  mech3::options() = mech3::Options{};
  return result;
}

std::string arena_bot_json(const char* mech) {
  return std::string(R"({"mech": ")") + mech +
         R"(", "preset": {"world": "c1", "mission": "ia1", "record": "Enemy_01"}})";
}
}  // namespace

// #287 step 3b (docs/arena.md): an arena match on c1mp1 as mw3 --arena starts
// it (the hub's session, respawn off, the host a spectator): the Core state
// is reached with no player mech at all, every fighter is a bot on AI
// controls, the view follows one of them, and 300 frames later the mission
// ends with nothing broken.
TEST(arena_spectator_launch_has_no_player_mech_headless) {
  if (!have_game()) return;
  const std::string bot =
      R"({"mech": "madcat", "preset": {"world": "c1", "mission": "mp1", "record": "remote_1"}})";
  int player_frames = 0, unviewed_frames = 0, mechs = 0, bots_on_ai = 0;
  const auto run = arena_headless_run(
      R"({"map": "c1mp1", "minutes": 10, "out": "arena-out", "sides": [[)" + bot + "], [" + bot + "]]}", 300,
      [&](int frame) {
        if (mech3::mech_mission_player()) ++player_frames;  // world().mission_player
        mech3::Mech* viewed = mech3::arena::arena_viewed_mech();
        if (!viewed || mech3::program_view_mech() != viewed) ++unviewed_frames;
        if (frame == 1) {
          mechs = static_cast<int>(mech3::arena::arena_mechs().size());
          for (const auto& entry : mech3::arena::arena_mechs())
            if (mech3::arena::arena_brain_params(entry.mech)) ++bots_on_ai;
        }
      });
  std::printf("  arena spectator: core frames %d, frames with a player mech %d, frames off a viewed bot %d, "
              "mechs %d, on AI %d\n",
              run.core_frames, player_frames, unviewed_frames, mechs, bots_on_ai);
  EXPECT(run.setup_read);
  EXPECT(run.core_frames >= 300);
  EXPECT(player_frames == 0);
  EXPECT(unviewed_frames == 0);
  EXPECT(mechs == 2 && bots_on_ai == 2);
  EXPECT(mech3::arena::arena_viewed_mech() == nullptr);  // cleared with the match
  EXPECT(!mech3::arena::arena_hunt_net_held());  // the mission's end freed it
}

// #287: a match nobody watches (mw3 --arena --hidden) views no bot at all, so
// the camera never touches one, and still runs with every bot on AI.
TEST(arena_hidden_match_views_no_bot_headless) {
  if (!have_game()) return;
  int viewed_frames = 0, player_frames = 0, bots_on_ai = 0;
  mech3::arena::set_arena_headless(true);
  const auto run = arena_headless_run(
      R"({"map": "c1mp1", "minutes": 10, "out": "arena-out", "sides": [[)" + arena_bot_json("madcat") + "], [" +
          arena_bot_json("madcat") + "]]}",
      300, [&](int frame) {
        if (mech3::arena::arena_viewed_mech()) ++viewed_frames;
        if (mech3::program_view_mech()) ++player_frames;  // the camera's mech
        if (frame == 1)
          for (const auto& entry : mech3::arena::arena_mechs())
            if (mech3::arena::arena_brain_params(entry.mech)) ++bots_on_ai;
      });
  mech3::arena::set_arena_headless(false);
  std::printf("  arena hidden: core frames %d, viewed %d, camera on a mech %d, on AI %d\n", run.core_frames,
              viewed_frames, player_frames, bots_on_ai);
  EXPECT(run.setup_read && run.core_frames >= 300);
  EXPECT(viewed_frames == 0 && player_frames == 0);
  EXPECT(bots_on_ai == 2);
}

// #287 criterion 11: every bot's brain runs on its preset's params, with only
// the arena's own changes (place, team, loadout, engaging, any-enemy wake-up).
TEST(arena_bot_params_match_the_preset_headless) {
  if (!have_game()) return;
  const std::string json = R"({"map": "c1mp1", "minutes": 10, "out": "arena-out", "sides": [[)" +
                           arena_bot_json("madcat") + "," + arena_bot_json("thor") + "], [" +
                           arena_bot_json("vulture") + "," + arena_bot_json("owens") + "]]}";
  int mechs_seen = 0, mismatched = 0, wrong_side = 0, bots_marked = 0;
  const auto run = arena_headless_run(json, 5, [&](int frame) {
    if (frame != 1) return;
    // The run's setup, its presets as read from the game files before launch.
    const mech3::arena::Setup& setup = *mech3::arena::arena_setup();
    const auto& mechs = mech3::arena::arena_mechs();
    mechs_seen = static_cast<int>(mechs.size());
    for (const auto& entry : mechs) {
      const int index = entry.side == 0 ? entry.id : entry.id - static_cast<int>(setup.sides[0].size());
      const mech3::ai::AiParams* live = mech3::arena::arena_brain_params(entry.mech);
      if (!live) {
        ++mismatched;
        continue;
      }
      mech3::ai::AivRecord expected;
      const mech3::arena::Bot& bot = setup.sides[entry.side][static_cast<size_t>(index)];
      const float pos[3] = {live->get<float>(0x08), live->get<float>(0x0c), live->get<float>(0x10)};
      mech3::arena::arena_bot_params(bot, entry.side, pos, live->get<float>(0x14), &expected);
      for (int off = mech3::ai::AiParams::kBegin; off < mech3::ai::AiParams::kEnd; ++off)
        if (live->raw[off] != expected.raw[off]) {
          std::printf("  arena params: mech %d byte +0x%02x live %02x preset %02x\n", entry.id, off, live->raw[off],
                      expected.raw[off]);
          ++mismatched;
        }
      // The preset's pilot name and radio voice reach the bot too.
      const auto same_text = [](const char* a, const char* b) {
        return (!a && !b) || (a && b && std::strcmp(a, b) == 0);
      };
      if (!same_text(live->pilot, expected.pilot) || !same_text(live->sound_tag, expected.sound_tag)) ++mismatched;
      if (live->team() != entry.side + 1 || live->get<int32_t>(0x3c) != 1 || live->get<int32_t>(0x88) != 1 ||
          live->get<int32_t>(0x8c) != 0 || (live->raw[0xcd] & 3) != 0)
        ++wrong_side;
      if (arena_counts::is_bot(entry.mech)) ++bots_marked;
    }
  });
  std::printf("  arena params: mechs %d, mismatched bytes %d, wrong overrides %d, bots marked %d\n", mechs_seen,
              mismatched, wrong_side, bots_marked);
  EXPECT(run.setup_read && run.core_frames >= 1);
  EXPECT(mechs_seen == 4 && mismatched == 0 && wrong_side == 0 && bots_marked == 4);
}

// #287 runner: a campaign pilot whose record starts it powered down (c1 m1's
// owens_01, an ambush; +0xcc bit 5) still hunts in the arena: no mission
// script would ever power it up.
TEST(arena_campaign_preset_bot_is_not_powered_down_headless) {
  if (!have_game()) return;
  const std::string owens =
      R"({"mech": "thor", "preset": {"world": "c1", "mission": "m1", "record": "owens_01"}})";
  const int five_seconds = 5 * 1000 / 16;
  const auto run = arena_headless_run(
      R"({"map": "c1mp1", "minutes": 10, "out": "arena-out", "sides": [[)" + owens + "], [" + owens + "]]}",
      five_seconds, [](int) {});
  EXPECT(run.setup_read);
  const mech3::arena::LogRead log = mech3::arena::read_arena_log(run.log_path);
  std::string order;
  for (const auto& r : log.records)
    if (r.value("type", "") == "state" && r.value("t", 0.0) > 3.0) {
      order = r["mechs"][0]["ai"].value("order", "");
      break;
    }
  std::printf("  campaign preset bot's order at 3 s: %s\n", order.c_str());
  EXPECT(order == "hunt" || order == "fight");
}

// #287 runner: a setup's loadout reaches the bot (+0xbc, so create_ai_mech
// builds that config) and the log's start line.
TEST(arena_bot_gets_the_setup_loadout_headless) {
  if (!have_game()) return;
  const std::string thor1 =
      R"({"mech": "thor", "loadout": 1, "preset": {"world": "c1", "mission": "ia1", "record": "Enemy_01"}})";
  int live_loadout = -1;
  const auto run = arena_headless_run(
      R"({"map": "c1mp1", "minutes": 10, "out": "arena-out", "sides": [[)" + thor1 + "], [" +
          arena_bot_json("madcat") + "]]}",
      3, [&](int frame) {
        if (frame != 1) return;
        for (const auto& entry : mech3::arena::arena_mechs())
          if (entry.id == 0)
            if (const mech3::ai::AiParams* p = mech3::arena::arena_brain_params(entry.mech))
              live_loadout = p->get<int32_t>(0xbc);
      });
  EXPECT(run.setup_read);
  EXPECT(live_loadout == 1);
  const mech3::arena::LogRead log = mech3::arena::read_arena_log(run.log_path);
  EXPECT(!log.records.empty() && log.records.front()["sides"][0][0].value("loadout", -1) == 1 &&
         log.records.front()["sides"][1][0].value("loadout", -1) == 0);
}

// #287: a 1v1 on c1mp1 for up to three minutes of game time: the two bots
// leave their spots, meet and fire on each other.
TEST(arena_1v1_c1mp1_bots_meet_and_fire_headless) {
  if (!have_game()) return;
  const std::string json = R"({"map": "c1mp1", "minutes": 3, "out": "arena-out", "sides": [[)" +
                           arena_bot_json("madcat") + "], [" + arena_bot_json("madcat") + "]]}";
  int standing[2] = {0, 0};
  float start_gap = 0, closest_gap = 1e30f;
  const auto gap = [] {
    const auto& mechs = mech3::arena::arena_mechs();
    if (mechs.size() != 2) return -1.0f;
    float a[3], b[3];
    if (!mech3::program_vehicle_centre(mechs[0].mech, a) || !mech3::program_vehicle_centre(mechs[1].mech, b))
      return -1.0f;
    return std::sqrt((a[0] - b[0]) * (a[0] - b[0]) + (a[2] - b[2]) * (a[2] - b[2]));
  };
  // Until the result is out: a side down, then the aftermath.
  const auto one_down = [] { return mech3::arena::arena_result().decided; };
  const int three_minutes = 3 * 60 * 1000 / 16;  // the fake clock's 16 ms frames
  const auto run = arena_headless_run(
      json, three_minutes,
      [&](int frame) {
        if (frame == 1) {
          arena_counts::begin();
          start_gap = gap();
        }
        const float now = gap();
        if (now >= 0) closest_gap = std::min(closest_gap, now);
        standing[0] = standing[1] = 0;
        for (const auto& entry : mech3::arena::arena_mechs())
          standing[entry.side] += arena_counts::standing(entry.mech) ? 1 : 0;
      },
      one_down);
  arena_counts::end();
  std::printf("  arena 1v1 c1mp1: core frames %d, gap %.0f m -> closest %.0f m, shots A %d B %d, hits on A %d B %d, "
              "standing A %d B %d\n",
              run.core_frames, start_gap, closest_gap, arena_counts::shots(0), arena_counts::shots(1),
              arena_counts::hits(0), arena_counts::hits(1), standing[0], standing[1]);
  EXPECT(run.setup_read && run.core_frames > 0);
  EXPECT(closest_gap < start_gap);
  EXPECT(arena_counts::shots(0) > 0 && arena_counts::shots(1) > 0);
  // Both fire; at least one lands. A one-sided 1v1 is a real outcome (the
  // per-frame update order, update_entities, changes which seed gives one).
  EXPECT(arena_counts::hits(0) + arena_counts::hits(1) > 0);
  // The match end: decided on the frame a side lost its last mech, its
  // winner the side still standing.
  const mech3::arena::Result& result = mech3::arena::arena_result();
  std::printf("  %s\n", mech3::arena::arena_result_line(result).c_str());
  EXPECT(result.decided);
  EXPECT(result.winner == (standing[0] > standing[1] ? 0 : standing[1] > standing[0] ? 1 : -1));
  EXPECT(result.lost[0] == 1 - standing[0] && result.lost[1] == 1 - standing[1]);

  // The match log: a start line naming the setup, state lines ten a second,
  // the shots, hits and the kill, and an end line agreeing with the result.
  const mech3::arena::LogRead log = mech3::arena::read_arena_log(run.log_path);
  int states = 0, shot_lines = 0, hit_lines = 0, destroyed_lines = 0;
  // #289: by the end line every beam shot has its beam_end and every round a
  // state line listed has its round_end.
  int beam_shots = 0, beam_ends = 0;
  std::set<int> rounds_listed, rounds_ended;
  for (const auto& record : log.records) {
    const std::string type = record.value("type", "");
    beam_shots += type == "shot" && record.value("beam", false);
    beam_ends += type == "beam_end";
    if (type == "round_end") rounds_ended.insert(record.value("round", -1));
    if (type == "state" && record.contains("rounds"))
      for (const auto& round : record["rounds"]) rounds_listed.insert(round.value("id", -1));
    states += type == "state";
    shot_lines += type == "shot";
    hit_lines += type == "hit";
    destroyed_lines += type == "destroyed";
  }
  std::printf("  log: %zu lines, %d state, %d shot, %d hit, %d destroyed, complete %d\n", log.records.size(), states,
              shot_lines, hit_lines, destroyed_lines, log.complete);
  EXPECT(log.opened && log.bad_lines == 0 && log.complete);
  std::printf("  beams %d shot, %d ended; rounds %zu listed, %zu ended\n", beam_shots, beam_ends, rounds_listed.size(),
              rounds_ended.size());
  EXPECT(beam_shots == beam_ends && rounds_listed == rounds_ended);
  EXPECT(!log.records.empty() && log.records.front().value("type", "") == "start");
  EXPECT(!log.records.empty() && log.records.front().value("map", "") == "c1mp1");
  EXPECT(shot_lines == arena_counts::shots(0) + arena_counts::shots(1));
  EXPECT(hit_lines == arena_counts::hits(0) + arena_counts::hits(1));
  EXPECT(destroyed_lines == result.lost[0] + result.lost[1]);
  // A state line every 0.1 s of the match and its aftermath, give or take the last.
  EXPECT(std::abs(states - static_cast<int>((result.time + mech3::arena::kAftermathSeconds) / 0.1f)) <= 2);
  if (log.complete) {
    const auto& end = log.records.back();
    EXPECT(end.value("winner", "") == (result.winner == 0 ? "A" : result.winner == 1 ? "B" : "draw"));
  }
  // No mech ever targets its own side (criterion 4).
  int own_side_targets = 0;
  for (const auto& record : log.records) {
    if (record.value("type", "") != "state") continue;
    for (const auto& mech : record["mechs"]) {
      const int target = mech.value("target", -1);
      if (target < 0) continue;
      for (const auto& other : record["mechs"])
        if (other.value("id", -2) == target && other.value("side", -1) == mech.value("side", -2)) ++own_side_targets;
    }
  }
  EXPECT(own_side_targets == 0);
}

// #287 step 3b (Q5): with no player in the arena, each AMS judges hostile by
// its own mech's side. A 1v1 on c1mp1, both bots' AMS switched on at frame
// 30; LRM10 salvos fired from 400 m at both, tagged as side B's shots
// (hostile to side A, as a side B mech's fire is tagged). Side A's AMS
// engages them (rounds spent); side B's leaves its own side's missiles be.
// The stock rule (the player's team) is mission_c1m1_ams_shoots_down_incoming_missiles_headless.
TEST(arena_ams_engages_the_enemy_side_missiles_headless) {
  if (!have_game()) return;
  const std::string json = R"({"map": "c1mp1", "minutes": 3, "out": "arena-out", "sides": [[)" +
                           arena_bot_json("madcat") + "], [" + arena_bot_json("madcat") + "]]}";
  int32_t fitted[2] = {}, before[2] = {}, after[2] = {};
  int fired = 0;
  const auto run = arena_headless_run(json, 600, [&](int frame) {
    const auto& mechs = mech3::arena::arena_mechs();
    if (mechs.size() != 2) return;
    bool on = false;
    for (int side = 0; side < 2; ++side) {
      void* mech = mechs[static_cast<size_t>(side)].mech;
      if (frame == 30) {
        mech3::program_mech_ams_set(mech, true);
        mech3::program_mech_ams(mech, &fitted[side], &on, &before[side]);
      }
      if (frame >= 40 && frame <= 400 && frame % 60 == 40) fired += mech3::program_fire_at(mech, "LRM10", 5, 400.0f);
      if (frame == 600) mech3::program_mech_ams(mech, &fitted[side], &on, &after[side]);
    }
  });
  std::printf("  arena AMS: %d missiles fired, side A rounds %d -> %d, side B rounds %d -> %d\n", fired, before[0],
              after[0], before[1], after[1]);
  EXPECT(run.setup_read && run.core_frames >= 600);
  EXPECT(fired == 70);
  EXPECT(after[0] < before[0]);   // side A's AMS shot side B's missiles down
  EXPECT(after[1] == before[1]);  // side B's never fired on its own side's
}

// #287 criterion 10: a state line's pose fields read back from the log equal
// the mech's live values on the frame it was written.
TEST(arena_log_pose_matches_live_headless) {
  if (!have_game()) return;
  const std::string json = R"({"map": "c1mp1", "minutes": 3, "out": "arena-out", "sides": [[)" +
                           arena_bot_json("madcat") + "], [" + arena_bot_json("madcat") + "]]}";
  // Frames 380..400 (about 6 s in at 16 ms): both walking. The live pose of
  // mech 0 on each, read straight from the mech, is matched with the state
  // line the log wrote on the same frame (one every 0.1 s).
  std::vector<nlohmann::json> live;
  const auto run = arena_headless_run(json, 401, [&](int frame) {
    if (frame >= 380 && frame <= 400) live.push_back(arena_counts::live_pose(0));
  });
  EXPECT(run.setup_read && run.core_frames >= 400);
  const mech3::arena::LogRead log = mech3::arena::read_arena_log(run.log_path);
  EXPECT(log.opened && !log.complete);  // stopped mid-match: no end line
  int compared = 0;
  for (const auto& record : log.records) {
    if (record.value("type", "") != "state") continue;
    for (const auto& pose : live) {
      if (record.value("t", -1.0) != pose.value("t", -2.0)) continue;
      nlohmann::json written = record["mechs"][0];
      // The live pose reads #287's anim index and t; version 2's phase, cps,
      // weight and limp are checked by arena_log_detail_c1mp1_4v4_headless.
      for (const char* field : {"phase", "cps", "weight", "limp"}) written["anim"].erase(field);
      for (const char* field : {"pos", "heading", "torso", "arms", "anim", "jumping", "fallen", "heat"}) {
        if (written[field] != pose["mech"][field])
          std::printf("  t %.3f %s: log %s, live %s\n", pose.value("t", 0.0), field, written[field].dump().c_str(),
                      pose["mech"][field].dump().c_str());
        EXPECT(written[field] == pose["mech"][field]);
      }
      ++compared;
    }
  }
  std::printf("  pose: %zu live frames, %d state lines compared\n", live.size(), compared);
  EXPECT(compared >= 2);
}

namespace {
// #289: a log with everything steps 1 and 3 added taken out, as the detail
// switch off writes it.
std::vector<nlohmann::json> without_detail(const std::vector<nlohmann::json>& records) {
  std::vector<nlohmann::json> kept;
  for (nlohmann::json record : records) {
    const std::string type = record.value("type", "");
    if (type == "round_end" || type == "beam_end" || type == "route" || type == "decision" || type == "action" ||
        type == "voice")
      continue;
    if (type == "shot")
      for (const char* field : {"weapon", "beam", "target", "locked", "muzzle", "dir"}) record.erase(field);
    if (type == "hit") {
      record.erase("weapon");
      record.erase("at");
    }
    if (type == "start")
      for (nlohmann::json& mech : record["mechs"]) mech.erase("voice");
    if (type == "state") {
      record.erase("rounds");
      record.erase("beams");
      for (nlohmann::json& mech : record["mechs"]) {
        mech["ai"].erase("at");
        mech["ai"].erase("contacts");
        for (const char* field : {"phase", "cps", "weight", "limp"}) mech["anim"].erase(field);
      }
    }
    kept.push_back(std::move(record));
  }
  return kept;
}

std::string file_text(const std::string& path) {
  std::ifstream in(path, std::ios::binary);
  return std::string(std::istreambuf_iterator<char>(in), std::istreambuf_iterator<char>());
}

bool is_missile(const std::string& weapon) {
  for (const char* part : {"LRM", "SRM", "MRM", "Streak", "ATM", "Missile", "lrm", "srm", "mrm", "streak"})
    if (weapon.find(part) != std::string::npos) return true;
  return false;
}
}  // namespace

// #289 step 2 criterion 5: the replay viewer's terrain from the player's
// install, the whole c1 world (the worst case, as no spawn spots are known
// here to frame on) in under 3 s, with real relief and walls outlined; an
// unknown map fails with a message.
TEST(replay_terrain_c1mp1) {
  if (!have_game()) return;
  SavedMounts keep;
  zutl::mounts() = zutl::Mounts{};
  zutl::mount(MW3_GAME_DIR);
  const float whole_world[4] = {1, 1, 0, 0};
  const auto started = std::chrono::steady_clock::now();
  const mech3::replay::Terrain terrain = mech3::replay::build_terrain("c1mp1", whole_world);
  const double seconds = std::chrono::duration<double>(std::chrono::steady_clock::now() - started).count();
  float low = 1e30f, high = -1e30f;
  for (const float y : terrain.heights) low = std::min(low, y), high = std::max(high, y);
  int outlined = 0;
  for (const uint8_t o : terrain.outline) outlined += o;
  std::printf("  terrain: %s %dx%d cells of %.2f m in %.2f s, heights %.1f..%.1f, %d outlined\n",
              terrain.error.c_str(), terrain.width, terrain.height, terrain.cell, seconds, low, high, outlined);
  EXPECT(terrain.error.empty() && terrain.width > 0 && terrain.height > 0);
  EXPECT(seconds < 3.0);
  EXPECT(high - low > 10.0f && outlined > 0);
  EXPECT(terrain.rgba.size() == terrain.heights.size() * 4);
  const mech3::replay::Terrain unknown = mech3::replay::build_terrain("zz9mp1", whole_world);
  EXPECT(!unknown.error.empty() && unknown.heights.empty());
}

// #289 on the real game: a puppet posed from a live
// arena mech's state record each sampled frame puts its feet and hip where
// the live mech's are; it takes off a lost arm and keeps it off through a
// rebuild; a destroyed puppet plays its collapse and never dies; jumping and
// landing leave its armor and action queue alone. The puppet is on team 0,
// so no bot shoots at it.
TEST(replay_puppet_follows_a_live_mech_headless) {
  if (!have_game()) return;
  const std::string json = R"({"map": "c1mp1", "minutes": 3, "out": "arena-out", "sides": [[)" +
                           arena_bot_json("madcat") + "], [" + arena_bot_json("madcat") + "]]}";
  arena_headless_run(json, 60, [](int) {});  // the warm-up (#302)
  constexpr int kFrames = 1200;
  replay_game::PuppetProbe probe;
  arena_headless_run(json, kFrames, [&](int frame) { probe.frame(frame, kFrames - 1); });
  const replay_game::PuppetResults& r = probe.results();
  std::printf("  puppet: made in %.1f ms; %d samples, feet within 5 cm in %d, angles in %d, worst %.3f m\n",
              r.create_ms, r.samples, r.close_feet, r.close_angles, r.worst);
  std::printf("  puppet: arm off %d, kept off %d, collapsed %d, never died %d, armor kept %d\n", r.part_off,
              r.kept_off, r.collapsed, r.never_died, r.armor_kept);
  EXPECT(r.made && r.samples >= 10);
  EXPECT(r.close_feet == r.samples && r.close_angles == r.samples);
  EXPECT(r.part_off && r.kept_off);
  EXPECT(r.collapsed && r.never_died && r.armor_kept);
}

// #289 on the real game: with a replay's hooks set for
// 60 frames in the middle of an arena match, no mech is updated (none moves
// and no gait clip runs), the game time is the replay's clock every frame,
// the frame clock is real time again after each frame, and the hooks run
// once a frame each.
TEST(replay_frame_branch_simulates_nothing_headless) {
  if (!have_game()) return;
  const std::string json = R"({"map": "c1mp1", "minutes": 3, "out": "arena-out", "sides": [[)" +
                           arena_bot_json("madcat") + "], [" + arena_bot_json("madcat") + "]]}";
  arena_headless_run(json, 60, [](int) {});  // the warm-up (#302)
  replay_game::FrameProbe probe(200, 60);
  arena_headless_run(json, 300, [&](int frame) { probe.frame(frame); });
  const replay_game::FrameResults& r = probe.results();
  std::printf("  replay frames: %d, moved %d, off clock %d, clock not real %d, hooks %d/%d\n", r.frames,
              r.mechs_moved, r.time_off_clock, r.clock_not_real, r.before, r.after);
  EXPECT(r.frames == 60 && r.mechs_moved == 0 && r.time_off_clock == 0 && r.clock_not_real == 0);
  EXPECT(r.before == 60 && r.after == 60);
  // The control: the same frames without the hooks, where the bots move.
  replay_game::FrameProbe control(200, 60, false);
  arena_headless_run(json, 300, [&](int frame) { control.frame(frame); });
  std::printf("  control frames: %d, moved %d\n", control.results().frames, control.results().mechs_moved);
  EXPECT(control.results().mechs_moved > 50);
}

// #289 step 1 (criteria 2 to 6) on the real game: a c1mp1 4v4 logs shots of
// every kind with their rounds and beams, routes, contacts in and out of
// sight and decisions with reasons; the same seed writes the same bytes; and
// with the detail switch off the match plays out the same, line for line.
TEST(arena_log_detail_c1mp1_4v4_headless) {
  if (!have_game()) return;
  const std::string side =
      arena_bot_json("madcat") + ", " + arena_bot_json("madcat") + ", " + arena_bot_json("orion") + ", " + arena_bot_json("orion");
  const std::string json =
      R"({"map": "c1mp1", "minutes": 3, "out": "arena-out", "sides": [[)" + side + "], [" + side + "]]}";
  const int ninety_seconds = 90 * 1000 / 16;  // the fake clock's 16 ms frames
  // Each run empties the temp log folder, so each log is read before the next run.
  // A warm-up match first: after other tests, something they leave behind
  // changes the first match in the process (mw3 itself plays one per process;
  // issue #302).
  arena_headless_run(json, ninety_seconds, [](int) {});
  const auto run_on = arena_headless_run(json, ninety_seconds, [](int) {});
  const std::string bytes_on = file_text(run_on.log_path);
  const mech3::arena::LogRead log = mech3::arena::read_arena_log(run_on.log_path);
  const auto run_again = arena_headless_run(json, ninety_seconds, [](int) {});
  const std::string bytes_again = file_text(run_again.log_path);
  mech3::arena::set_arena_log_detail(false);
  const auto run_off = arena_headless_run(json, ninety_seconds, [](int) {});
  mech3::arena::set_arena_log_detail(true);
  const std::string bytes_off = file_text(run_off.log_path);
  const mech3::arena::LogRead off = mech3::arena::read_arena_log(run_off.log_path);
  EXPECT(run_on.setup_read && run_again.setup_read && run_off.setup_read);
  std::printf("  log sizes: detail on %zu bytes, off %zu bytes\n", bytes_on.size(), bytes_off.size());
  EXPECT(!bytes_on.empty() && bytes_on == bytes_again);  // criterion 6: same seed, same bytes

  EXPECT(log.error.empty() && off.error.empty() && !log.records.empty());
  if (log.records.empty()) return;
  EXPECT(log.records[0].value("version", 0) == 2);  // criterion 1
  // Criterion 6: the additions taken out, the detail-on log is the detail-off one.
  const std::vector<nlohmann::json> stripped = without_detail(log.records);
  EXPECT(stripped.size() == off.records.size());
  size_t first_difference = 0;
  while (first_difference < stripped.size() && first_difference < off.records.size() &&
         stripped[first_difference] == off.records[first_difference])
    ++first_difference;
  if (first_difference < stripped.size())
    std::printf("  first difference at record %zu: %s\n", first_difference, stripped[first_difference].dump().c_str());
  EXPECT(stripped == off.records);

  // Criteria 2 to 5, walking the detail-on log in order.
  const size_t mech_count = log.records[0]["mechs"].size();
  int beam_shots = 0, ballistic_shots = 0, missile_shots = 0;
  std::map<std::string, int> shots_by_weapon, followed_by_weapon;
  struct PendingShot {
    double t;
    int id;
    std::string weapon;
  };
  std::vector<PendingShot> round_shots;
  std::map<std::pair<int, std::string>, int> beams_open;
  int beam_mismatches = 0, bad_beam_ends = 0, round_ends = 0, moved_rounds = 0;
  std::map<int, nlohmann::json> last_round_pos;
  std::set<int> routed;
  bool seen_true = false, seen_false = false;
  std::map<std::string, int> codes;
  int decisions = 0, unexplained_changes = 0;
  std::vector<double> last_decision_t(mech_count, -1.0);
  nlohmann::json previous_state;
  for (const nlohmann::json& record : log.records) {
    const std::string type = record.value("type", "");
    const double t = record.value("t", 0.0);
    if (type == "shot") {
      for (const char* field : {"weapon", "beam", "target", "locked", "muzzle", "dir"}) EXPECT(record.contains(field));
      const std::string weapon = record.value("weapon", "");
      ++shots_by_weapon[weapon];
      if (record.value("beam", false)) {
        ++beam_shots;
        ++beams_open[{record.value("id", -1), weapon}];
      } else {
        ++(is_missile(weapon) ? missile_shots : ballistic_shots);
        round_shots.push_back({t, record.value("id", -1), weapon});
      }
    } else if (type == "beam_end") {
      int& open = beams_open[{record.value("id", -1), record.value("weapon", "")}];
      if (open <= 0) ++bad_beam_ends;
      else --open;
    } else if (type == "hit") {
      EXPECT(record.contains("weapon"));
    } else if (type == "round_end") {
      ++round_ends;
    } else if (type == "route") {
      routed.insert(record.value("id", -1));
    } else if (type == "decision") {
      ++decisions;
      ++codes[record.value("code", "")];
      const int id = record.value("id", -1);
      if (id >= 0 && static_cast<size_t>(id) < mech_count) last_decision_t[id] = t;
    } else if (type == "state") {
      // Every open beam has exactly its entries in this state line.
      std::map<std::pair<int, std::string>, int> drawn;
      for (const nlohmann::json& beam : record["beams"]) ++drawn[{beam.value("by", -1), beam.value("weapon", "")}];
      for (const auto& [key, open] : beams_open)
        if (open != (drawn.count(key) ? drawn[key] : 0)) ++beam_mismatches;
      for (const auto& [key, count] : drawn)
        if (!beams_open.count(key)) ++beam_mismatches;
      for (const nlohmann::json& round : record["rounds"]) {
        const int id = round.value("id", -1);
        if (last_round_pos.count(id) && last_round_pos[id] != round["pos"]) ++moved_rounds;
        last_round_pos[id] = round["pos"];
        for (PendingShot& shot : round_shots)
          if (shot.id == round.value("by", -2) && shot.weapon == round.value("weapon", "") && t > shot.t &&
              t <= shot.t + 0.2) {
            ++followed_by_weapon[shot.weapon];
            shot.id = -1;  // counted once
            break;
          }
      }
      for (const nlohmann::json& mech : record["mechs"]) {
        for (const nlohmann::json& contact : mech["ai"].value("contacts", nlohmann::json::array()))
          (contact.value("seen", false) ? seen_true : seen_false) = true;
        EXPECT(mech["ai"].contains("at"));
      }
      // Each order or target change since the last state line has a decision.
      if (!previous_state.is_null())
        for (size_t i = 0; i < mech_count && i < record["mechs"].size(); ++i) {
          const nlohmann::json& before = previous_state["mechs"][i];
          const nlohmann::json& now = record["mechs"][i];
          const bool changed = before["target"] != now["target"] || before["ai"].value("order", "") != now["ai"].value("order", "");
          if (changed && !(last_decision_t[i] > previous_state.value("t", 0.0))) ++unexplained_changes;
        }
      previous_state = record;
    }
  }
  int other = codes["order_other"] + codes["target_other"];
  std::printf("  shots: beam %d, ballistic %d, missile %d; rounds moved %d, ended %d\n", beam_shots, ballistic_shots,
              missile_shots, moved_rounds, round_ends);
  for (const auto& [weapon, count] : shots_by_weapon)
    std::printf("    %s: %d shots, %d seen in flight\n", weapon.c_str(), count, followed_by_weapon[weapon]);
  std::printf("  decisions %d:", decisions);
  for (const auto& [code, count] : codes) std::printf(" %s %d", code.c_str(), count);
  std::printf("\n  routes for %zu of %zu bots; contacts seen %d, unseen %d\n", routed.size(), mech_count, seen_true,
              seen_false);
  EXPECT(beam_shots > 0 && ballistic_shots > 0 && missile_shots > 0);
  // Every round weapon that fired is seen in flight by its shooter at least
  // once: the shot hook found its rounds (fast rounds that land inside one
  // state period never show, so not every shot is).
  for (const auto& [weapon, count] : shots_by_weapon)
    if (followed_by_weapon[weapon] == 0 && count >= 5 && !weapon.empty()) {
      bool is_beam_weapon = false;
      for (const auto& [key, open] : beams_open)
        if (key.second == weapon) is_beam_weapon = true;
      if (!is_beam_weapon) std::printf("  never seen in flight: %s\n", weapon.c_str());
      EXPECT(is_beam_weapon);
    }
  EXPECT(moved_rounds > 0 && round_ends > 0);
  EXPECT(beam_mismatches == 0 && bad_beam_ends == 0);
  EXPECT(routed.size() == mech_count);
  // `seen` is the sensors' detect bit, cleared only by shutdown, passive radar
  // or ECM, none of which a plain match uses; so only a detected one is sure.
  EXPECT(seen_true);
  EXPECT(codes["hunt_contact"] + codes["hunt_last_seen"] + codes["hunt_fallback"] > 0);
  EXPECT(codes["engage"] > 0 && codes["target_volley"] > 0);
  EXPECT(decisions > 0 && other * 2 < decisions);
  EXPECT(unexplained_changes == 0);

  // #289 step 3 (version 2): each new field is written at least once.
  int actions = 0, hits_at = 0, round_ends_at = 0, voices = 0, voices_tagged = 0, phased = 0, blended = 0;
  for (const nlohmann::json& mech : log.records[0]["mechs"])
    if (mech.contains("voice")) ++voices_tagged;
  for (const nlohmann::json& record : log.records) {
    const std::string type = record.value("type", "");
    if (type == "action") ++actions;
    if (type == "voice") ++voices;
    if (type == "hit" && record.contains("at")) ++hits_at;
    if (type == "round_end" && record.contains("at") && record.contains("terrain")) ++round_ends_at;
    if (type == "state")
      for (const nlohmann::json& mech : record["mechs"]) {
        const nlohmann::json& anim = mech["anim"];
        EXPECT(anim.contains("phase") && anim.contains("cps") && anim.contains("weight") && anim.contains("limp"));
        if (anim.value("phase", 0.0) > 0.0) ++phased;
        if (anim.value("weight", 0.0) > 0.0) ++blended;
      }
  }
  std::printf("  version 2: actions %d, hits with at %d, round ends with at %d, voices %d (%d tagged), phased %d, blended %d\n",
              actions, hits_at, round_ends_at, voices, voices_tagged, phased, blended);
  EXPECT(hits_at > 0 && round_ends_at > 0 && phased > 0 && blended > 0);
  EXPECT(actions > 0);
  // Voice lines and tags come only from bots with a radio voice; the stock
  // enemy presets the arena uses have none (checked 2026-11-13), so none here.
}

// #287: the time limit ends the match by it, and a match that reaches it goes
// to the side with more mechs standing, equal a draw. Whether the 2v2 is
// still on at one minute depends on the fight, so the rule is checked either
// way: ended by elimination before it, or at it with the winner by count.
TEST(arena_time_limit_decides_by_mechs_standing_headless) {
  if (!have_game()) return;
  const std::string bot = arena_bot_json("madcat");
  const std::string json = R"({"map": "c4mp1", "minutes": 1, "out": "arena-out", "sides": [[)" + bot + "," + bot +
                           "], [" + bot + "," + bot + "]]}";
  const int two_minutes = 2 * 60 * 1000 / 16;  // past the limit: the end, not the frame count, stops it
  const auto run = arena_headless_run(json, two_minutes, [](int) {});
  const mech3::arena::Result& result = mech3::arena::arena_result();
  std::printf("  core frames %d, %s\n", run.core_frames, mech3::arena::arena_result_line(result).c_str());
  EXPECT(run.setup_read && run.core_frames < two_minutes);
  EXPECT(result.decided && result.time < 61.0f);
  const int standing[2] = {2 - result.lost[0], 2 - result.lost[1]};
  const bool by_time = standing[0] > 0 && standing[1] > 0;
  if (by_time) {
    EXPECT(result.time >= 60.0f);
    EXPECT(result.winner == (standing[0] > standing[1] ? 0 : standing[1] > standing[0] ? 1 : -1));
  } else {
    EXPECT(result.winner == (standing[0] > 0 ? 0 : standing[1] > 0 ? 1 : -1));
  }
}

// #287 runner: --arena-catalog's files, from the install alone. The ten
// arena maps (t1mp1 has no 16 spots), the 19 mechs with their 58 stock
// loadouts (the dfn files' 62 less Bushwacker's four training ones), the
// game's own names, the pilot presets, and pictures sized as their JSON says.
TEST(arena_catalog_lists_the_game_headless) {
  if (!have_game()) return;
  SavedMounts keep;
  zutl::mounts() = zutl::Mounts{};
  zutl::mount(MW3_GAME_DIR);
  const std::string dir = temp_dir("arena_catalog");
  std::filesystem::remove_all(dir);
  std::string error;
  const auto t0 = std::chrono::steady_clock::now();
  EXPECT(mech3::arena::write_arena_catalog(dir, &error));
  const double seconds = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
  std::printf("  arena catalog: %.1f s %s\n", seconds, error.c_str());
  const nlohmann::json c = nlohmann::json::parse(file_text(dir + "/catalog.json"), nullptr, false);
  EXPECT(c.is_object() && c.value("version", 0) == 1);
  if (!c.is_object()) return;
  std::set<std::string> maps;
  for (const auto& m : c["maps"]) maps.insert(m.value("id", ""));
  EXPECT(maps.size() == 10 && maps.count("c1mp1") && maps.count("c3mp1") && !maps.count("t1mp1"));
  size_t loadouts = 0;
  for (const auto& m : c["mechs"]) loadouts += m["loadouts"].size();
  EXPECT(c["mechs"].size() == 19 && loadouts == 58);
  for (const auto& m : c["mechs"]) {
    if (m.value("id", "") != "thor") continue;
    const auto& primary = m["loadouts"][0];
    EXPECT(primary.value("name", "") == "Primary" && !primary["weapons"].empty());
    EXPECT(m.value("picture", false) && std::filesystem::file_size(dir + "/mechs/thor.ppm") > 0);
  }
  bool enemy_01 = false;
  for (const auto& p : c["presets"])
    if (p.value("world", "") == "c1" && p.value("mission", "") == "ia1" && p.value("record", "") == "Enemy_01")
      enemy_01 = p["numbers"].value("attack_m", 0.0) > 0;
  EXPECT(enemy_01);
  // The picture's PPM header matches its placement file.
  std::ifstream ppm(dir + "/terrain/c3mp1.ppm", std::ios::binary);
  std::string magic;
  int width = 0, height = 0;
  ppm >> magic >> width >> height;
  const nlohmann::json place = nlohmann::json::parse(file_text(dir + "/terrain/c3mp1.json"), nullptr, false);
  EXPECT(magic == "P6" && place.is_object() && width == place.value("width", -1) && height == place.value("height", -1));
}
