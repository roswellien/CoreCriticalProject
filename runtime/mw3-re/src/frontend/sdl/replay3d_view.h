#pragma once
// #289: mw3 --replay3d's view, the arena match log played back
// in the game's own world. It is the replay's ReplayHooks (replay_hooks.h):
// the game runs its Core frame and draws the world, while this view keeps
// the replay clock, poses one puppet per logged mech (replay_puppet.h),
// starts the logged shots' and hits' effects and sounds, flies or follows
// with its own camera, and draws the shared overlays, panel and seek bar
// (replay_ui.h) over the HUD. Keys and script commands: docs/arena.md.
#include <SDL3/SDL.h>

#include <functional>
#include <memory>
#include <string>

#include "mech3/replay_hooks.h"

namespace mech3::replay {
class ReplayRun;
}

namespace sdlfe {

class FrameRenderer;

class Replay3dView : public mech3::ReplayHooks {
 public:
  // `run` outlives the view; `request_quit` ends the program (the quit box's
  // yes, the script's quit). `script_path` "" for none.
  Replay3dView(const mech3::replay::ReplayRun& run, FrameRenderer* render, const std::string& script_path,
               std::function<void()> request_quit);
  ~Replay3dView() override;
  Replay3dView(const Replay3dView&) = delete;
  Replay3dView& operator=(const Replay3dView&) = delete;

  // False with a message when the script can't be read.
  bool ready(std::string* message) const;
  // The replay's input layer, ahead of the game's (SdlPump::intercept): true
  // when the event was the replay's. While the quit box is open, and for
  // Escape, everything passes through.
  bool handle(const SDL_Event& e);

  void start() override;
  void before_lists(bool quit_box_open) override;
  void after_lists() override;
  void quit() override;
  void place_camera(zcls::Node* camera) override;
  void draw_overlay() override;

 private:
  struct State;
  std::unique_ptr<State> s_;
};

}  // namespace sdlfe
