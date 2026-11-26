#pragma once
#include <SDL3/SDL.h>

#include <string>

#include "mech3/arena_camera.h"
#include "mech3/spectator_camera_hooks.h"

// Ours (#529, docs/arena.md "Watching a match"): the watched arena match's
// spectator camera as the window drives it. Made by watch_attach for
// mw3 --arena without --hidden, and only then: a hidden match keeps the
// game's own view and its byte-for-byte log.
//
// It reads the keyboard and mouse ahead of the game (SdlPump::intercept),
// keeps its own real-time clock (SDL_GetTicksNS, so the camera's motion does
// not depend on the frame rate or the match's step), and each frame asks the
// arena where the mechs are (arena_camera_view) and writes the scene camera.
namespace sdlfe {

class ArenaCameraView : public mech3::SpectatorCameraHooks {
  public:
    explicit ArenaCameraView(SDL_Window *window) : window_(window) {}
    // The camera's input layer: true when the event was the camera's and the
    // game must not see it.
    bool handle(const SDL_Event &event);
    void place_camera(zcls::Node *camera) override;

  private:
    // Lets go of every held key and the mouse look (focus lost).
    void release_input();
    void set_looking(bool on);
    // The window's title: the mode, the followed mech and the keys.
    void show_caption();
    // The free camera from where the view is now, for a fly key or the mouse
    // look in an automatic mode.
    void take_control();

    SDL_Window *window_ = nullptr;
    mech3::arena_camera::Camera camera_;
    bool held_[SDL_SCANCODE_COUNT] = {};
    bool looking_ = false;
    bool match_live_ = false; // the last frame had a match to watch
    float look_dx_ = 0, look_dy_ = 0, zoom_ = 0;
    uint64_t last_ns_ = 0;
    std::string caption_;
};

} // namespace sdlfe
