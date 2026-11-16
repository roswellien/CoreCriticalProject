#include "frontend/sdl/watch_launch.h"

#include <cstdio>
#include <cstdlib>
#include <filesystem>

#include "frontend/sdl/replay3d_view.h"
#include "frontend/sdl/replay_view.h"
#include "frontend/sdl/sdl_platform.h"
#include "mech3/arena_catalog.h"
#include "mech3/replay_hooks.h"
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
  else if (s == "--replay3d") w.replay3d_path = argv[++*i];
  else if (s == "--arena-catalog") w.catalog_dir = argv[++*i];
  else return false;
  return true;
}

bool check_watch_options(WatchArgs& w, const mech3::replay::ReplayFlags& replay,
                         const mech3::arena::Flags& arena, std::string* mission, bool* nosound) {
  if (!w.catalog_dir.empty() && (!w.arena_path.empty() || !w.replay_path.empty() || !w.replay3d_path.empty())) {
    std::fprintf(stderr, "mw3: --arena-catalog runs alone (no --arena, --replay or --replay3d)\n");
    return false;
  }
  if (!w.replay_path.empty()) {
    const std::string message = mech3::replay::replay_refusal(replay);
    if (!message.empty()) {
      std::fprintf(stderr, "mw3: %s\n", message.c_str());
      return false;
    }
  }
  if (!w.replay3d_path.empty()) {
    const std::string message = mech3::replay::replay3d_refusal(replay);
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

int watch_after_mount(WatchArgs& w, int seed, std::string* mission) {
  // --arena-catalog: the files, then the end of the run.
  if (!w.catalog_dir.empty()) {
    std::string message;
    if (!mech3::arena::write_arena_catalog(w.catalog_dir, &message)) {
      std::fprintf(stderr, "mw3: --arena-catalog: %s\n", message.c_str());
      return 1;
    }
    std::printf("mw3: arena catalog written to %s\n", w.catalog_dir.c_str());
    return 0;
  }
  // --replay3d: the log read and checked before anything is made from it.
  if (!w.replay3d_path.empty()) {
    w.replay3d = std::make_shared<mech3::replay::ReplayRun>();
    std::string message;
    if (!w.replay3d->read(w.replay3d_path, &message)) {
      std::fprintf(stderr, "mw3: %s\n", message.c_str());
      w.replay3d.reset();
      return 2;
    }
    *mission = w.replay3d->map();
    std::printf("mw3: replay3d of %s on %s\n", w.replay3d_path.c_str(), mission->c_str());
  }
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
  std::string message;
  if (w.replay3d && !w.replay3d->open(&message)) {
    std::fprintf(stderr, "mw3: %s\n", message.c_str());
    w.replay3d.reset();
    return false;
  }
  if (!w.arena) return true;
  if (!w.arena->open(seed, frame_ms, headless, &message)) {
    std::fprintf(stderr, "mw3: %s\n", message.c_str());
    w.arena.reset();
    return false;
  }
  return true;
}

void close_watch(WatchArgs& w) {
  w.arena.reset();
  w.replay3d.reset();
}

namespace {
std::unique_ptr<Replay3dView> g_view;  // --replay3d's, between watch_attach and watch_detach
}  // namespace

bool watch_attach(const WatchArgs& w, SdlPump& pump, FrameRenderer* render) {
  if (!w.replay3d) return true;
  g_view = std::make_unique<Replay3dView>(*w.replay3d, render, w.replay_script, [&pump] { pump.post_quit(); });
  std::string message;
  if (!g_view->ready(&message)) {
    std::fprintf(stderr, "mw3: %s\n", message.c_str());
    g_view.reset();
    return false;
  }
  mech3::set_replay_hooks(g_view.get());
  pump.intercept = [](const SDL_Event& e) { return g_view && g_view->handle(e); };
  return true;
}

void watch_detach(SdlPump& pump) {
  if (!g_view) return;
  pump.intercept = nullptr;
  if (mech3::replay_hooks() == g_view.get()) mech3::set_replay_hooks(nullptr);
  g_view.reset();  // its puppets freed and its text textures released while the renderer lives
}

void watch_seat(const WatchArgs& w, mech3::MultiplayerGame* game, mech3::GameEngine::Launch* launch) {
  if (!w.watched_match()) return;
  game->b8c = 0;  // +0x8c, net_pilot_respawn's switch
  launch->spectator = true;
}

void start_watch_clock(const WatchArgs& w, int net_minutes) {
  const int clock_minutes = w.arena ? w.arena->setup().minutes : net_minutes;
  const float arena_margin = w.arena_path.empty() ? 0.0f : 10.0f;
  if (clock_minutes > 0)
    mech3::missions().clock = clock_minutes * 60.0f + arena_margin, mech3::missions().clock_down = 1;
}

void watch_default_hud(const WatchArgs& w, bool mode_chosen, HudOptions* hud) {
  if (w.replay3d_path.empty() || mode_chosen) return;
  hud->mode = "core-critical";
  if (!hud->artwork.empty()) return;
  const char* local = std::getenv("LOCALAPPDATA");
  if (!local) return;
  const std::filesystem::path pack = std::filesystem::path(local) / "MW3Remaster/mods/com.mw3remaster.hud";
  std::error_code ec;
  if (std::filesystem::is_directory(pack / "ui/sprites", ec)) hud->artwork = pack.string();
}

bool watch_run_over(const WatchArgs& w, const zgame::State* state) {
  if (w.arena_path.empty() || !mech3::arena::arena_result().decided) return false;
  return state != &mech3::states().core && state != &mech3::states().fade && state != &mech3::states().pause;
}

}  // namespace sdlfe
