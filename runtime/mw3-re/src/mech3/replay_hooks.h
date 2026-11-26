#pragma once

// Ours (#289, docs/arena.md): what a 3D replay changes in the game's own
// frame. Set while mw3 --replay3d plays, null otherwise, so every other run
// takes the stock path. While set:
//  - the Core state starts the replay (its puppets) instead of an arena match;
//  - no entity is updated (update_entities returns at once) and the
//    spectator's stealth entity neither reads input nor moves: the log poses
//    every mech and the replay's camera owns the view;
//  - the frame polls input without the game's command callbacks, so no
//    game command fires (Escape's key state stays live for the quit box);
//  - the action lists run on the replay's step (its speed, 0 paused), so
//    effects and puffs follow the replay, while the UI, sound fades and the
//    quit fade keep real time;
//  - of the world's tick only the camera runs: no sensors, missions or pilot;
//  - the quit box's fade to the lobby ends the program instead.
namespace zcls {
struct Node;
}

namespace mech3 {

class ReplayHooks {
 public:
  virtual ~ReplayHooks() = default;
  // As play starts (in place of the arena's start): the puppets made.
  virtual void start() = 0;
  virtual void scene_load_enter() {}
  // Before the action lists: the frame clock set to the replay's step (real
  // time times the speed, 0 while paused or `quit_box_open`, capped).
  // False when the replay has stopped and no world frame should be submitted.
  virtual bool before_lists(bool quit_box_open) = 0;
  // After them: the real step back on the clock, then the game time set to
  // the replay's, the puppets posed, the log's events shown, the camera.
  virtual void after_lists() = 0;
  virtual void after_frame() {}
  // The quit box answered yes: end the program, not fade to the lobby.
  virtual void quit() = 0;
  // In the world's tick, after the view's frame placed `camera` (the
  // mission's camera node): the replay's own camera written over it.
  virtual void place_camera(zcls::Node* camera) { (void)camera; }
  // The hardware frame's 2D pass, over the HUD and under the quit box.
  virtual void draw_overlay() {}
};

void set_replay_hooks(ReplayHooks* hooks);
ReplayHooks* replay_hooks();

}  // namespace mech3
