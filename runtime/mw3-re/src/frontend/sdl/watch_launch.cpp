#include "frontend/sdl/watch_launch.h"

#include <cstdio>

#include "frontend/sdl/replay_view.h"
#include "gamez/zgame/zgameapp.h"
#include "mech3/app_states.h"
#include "mech3/mission.h"
#include "mech3/pilot.h"

namespace sdlfe {

bool parse_watch_option(WatchArgs& w, int argc, char** argv, int* i) {
  const std::string s = argv[*i];
  const bool has_value = *i + 1 < argc;
  if (!has_value) return false;
  if (s == "--arena") w.arena_path = argv[++*i];
  else if (s == "--replay") w.replay_path = argv[++*i];
  else if (s == "--replay-script") w.replay_script = argv[++*i];
  else return false;
  return true;
}

bool check_watch_options(WatchArgs& w, const mech3::replay::ReplayFlags& replay,
                         const mech3::arena::Flags& arena, std::string* mission, bool* nosound) {
  if (!w.replay_path.empty()) {
    const std::string message = mech3::replay::replay_refusal(replay);
    if (!message.empty()) {
      std::fprintf(stderr, "mw3: %s\n", message.c_str());
      return false;
    }
  }
  if (!w.arena_path.empty()) {
    w.arena = std::make_shared<mech3::arena::ArenaRun>();
    std::string message;
    if (!w.arena->read_setup(w.arena_path, arena, &message)) {
      std::fprintf(stderr, "mw3: %s\n", message.c_str());
      return false;
    }
    *mission = w.arena->setup().map;
    *nosound = true;  // a match runs unattended: the silent stand-in, never the speakers
  }
  return true;
}

int watch_after_mount(WatchArgs& w, int seed) {
  // --replay: the viewer and nothing else: no engine, mission, match or network.
  if (!w.replay_path.empty()) return run_replay(w.replay_path, w.replay_script);
  // --arena: never over an old log; a failure exits 2 before the engine starts.
  if (w.arena) {
    std::string message;
    if (!w.arena->read_game_files(seed, &message)) {
      std::fprintf(stderr, "mw3: %s\n", message.c_str());
      return 2;
    }
    std::printf("mw3: arena on %s, the log %s\n", w.arena->setup().map.c_str(), w.arena->log_path().c_str());
  }
  return -1;
}

bool open_watch_session(WatchArgs& w, int seed, int frame_ms, bool headless) {
  // The run outlives run(), whose engine is gone before its shutdown.
  if (!w.arena) return true;
  std::string message;
  if (!w.arena->open(seed, frame_ms, headless, &message)) {
    std::fprintf(stderr, "mw3: %s\n", message.c_str());
    w.arena.reset();
    return false;
  }
  return true;
}

void close_watch(WatchArgs& w) { w.arena.reset(); }

void watch_seat(const WatchArgs& w, mech3::MultiplayerGame* game, mech3::GameEngine::Launch* launch) {
  if (w.arena_path.empty()) return;
  game->b8c = 0;  // +0x8c, net_pilot_respawn's switch
  launch->spectator = true;
}

void start_watch_clock(const WatchArgs& w, int net_minutes) {
  const int clock_minutes = w.arena ? w.arena->setup().minutes : net_minutes;
  const float arena_margin = w.arena_path.empty() ? 0.0f : 10.0f;
  if (clock_minutes > 0)
    mech3::missions().clock = clock_minutes * 60.0f + arena_margin, mech3::missions().clock_down = 1;
}

bool watch_run_over(const WatchArgs& w, const zgame::State* state) {
  if (w.arena_path.empty() || !mech3::arena::arena_result().decided) return false;
  return state != &mech3::states().core && state != &mech3::states().fade && state != &mech3::states().pause;
}

}  // namespace sdlfe
