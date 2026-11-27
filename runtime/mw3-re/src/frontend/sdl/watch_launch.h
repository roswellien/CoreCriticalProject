#pragma once
#include <SDL3/SDL.h>

#include <memory>
#include <optional>
#include <string>

#include "frontend/sdl/arena_benchmark.h"
#include "frontend/sdl/gpu_hud.h"
#include "mech3/app_engine.h"
#include "mech3/arena.h"
#include "mech3/arena_setup.h"
#include "mech3/replay_log.h"
#include "mech3/replay_run.h"

namespace mech3 {
class MultiplayerGame;
}
namespace zgame {
class State;
}

// Ours (#287, #289; docs/arena.md): the arena match and the replay viewers
// as mw3 launches them, out of mw3_main.cpp so it keeps only the calls, each
// at the place in the start its block had.
namespace sdlfe {

class SdlPump;
class FrameRenderer;

// The watch options as parsed.
struct WatchArgs {
  // --arena SETUP.json, an AI bot match on the setup's map, hosted
  // in-process (its map is the mission). The run, once its setup is read;
  // shared so Args stays copyable.
  std::string arena_path;
  std::shared_ptr<mech3::arena::ArenaRun> arena;
  std::string replay_path;    // --replay LOG, the top-down replay viewer
  std::string replay_script;  // --replay-script FILE: drives it for tests (replay_view.h)
  // --replay3d LOG, the match played back in the game's own world; the run
  // once its log is read (after the install is mounted).
  std::string replay3d_path;
  std::shared_ptr<mech3::replay::ReplayRun> replay3d;
  // --arena-catalog DIR: the arena runner's lists and pictures written there
  // (arena_catalog.h), then the run ends.
  std::string catalog_dir;
  std::string benchmark_path, benchmark_scene, benchmark_output;
  std::string benchmark_resolution, benchmark_window_mode;
  bool benchmark_strict = false;
  std::optional<size_t> benchmark_strict_capture;
  std::vector<std::string> benchmark_packs;
  std::shared_ptr<benchmark::Run> benchmark_run;
  // Either watched run: the host's seat is a spectator's.
  bool watched_match() const { return !arena_path.empty() || !replay3d_path.empty(); }
};

// One command-line option, at argv[*i]: true when it is a watch option,
// *i moved past its value.
bool parse_watch_option(WatchArgs& w, int argc, char** argv, int* i);

// After parsing: what --replay, --replay3d and --arena refuse (`replay` and
// `arena` the other options given), then the arena's setup file. False, with
// the message printed, is exit 2 before anything starts. The setup's map
// becomes *mission, so the start takes the headless path, and the sound goes
// off.
bool check_watch_options(WatchArgs& w, const mech3::replay::ReplayFlags& replay,
                         const mech3::arena::Flags& arena, std::string* mission, bool* nosound);

// With the install mounted: --replay runs its viewer and nothing else;
// --arena reads the map's spawn spots, every pilot preset and makes the
// log; --replay3d reads its log, refused (exit 2) unless its map is a
// shipped multiplayer map and every chassis is known, and only then makes
// that map *mission. -1 to go on, else the exit code.
int watch_after_mount(WatchArgs& w, int seed, std::string* mission);

// --arena and --replay3d: a lone host's session on the in-process hub, never
// the ENet transport. False, with the message printed, is exit 1 (the run is
// gone).
bool open_watch_session(WatchArgs& w, int seed, int frame_ms, bool headless);

// The watch run's hooks off and its session shut, before SDL goes.
void close_watch(WatchArgs& w);

// --replay3d, once the window and the pump exist: the 3D view made, set as
// the replay's hooks and put ahead of the game's input. False (exit 2) when
// its script can't be read. A watched --arena match (not `hidden`) gets the
// spectator camera (arena_camera_view.h) the same way. watch_detach() undoes
// either before the window goes.
bool watch_attach(const WatchArgs& w, SdlPump& pump, FrameRenderer* render, SDL_Window* window, bool hidden);
void watch_detach(SdlPump& pump);

// --arena and --replay3d: respawn off (a downed mech stays down) and the
// host a spectator with no mech.
void watch_seat(const WatchArgs& w, mech3::MultiplayerGame* game, mech3::GameEngine::Launch* launch);

// The mission clock as the Core state starts: --arena's is the setup's
// minutes plus 10 s (the stock end starts 3 s before its clock runs out, and
// the arena's own end must count the result first), else `net_minutes`.
void start_watch_clock(const WatchArgs& w, int net_minutes);

// --replay3d shows the game's own quit box and HUD art, so it takes the Core
// Critical HUD (sharp art, text at the window's density) unless the player
// chose a HUD (`mode_chosen`: --cc-hud or mw3.cfg's cc_hud=). The art is the
// installed HUD pack, when there is one: the Core Critical launcher installs
// it as %LOCALAPPDATA%/MW3Remaster/mods/com.mw3remaster.hud.
void watch_default_hud(const WatchArgs& w, bool mode_chosen, HudOptions* hud);

// --arena: whether the run is over, the match decided and its fade gone
// from the mission (`state` the app's current state).
bool watch_run_over(const WatchArgs& w, const zgame::State* state);

}  // namespace sdlfe
