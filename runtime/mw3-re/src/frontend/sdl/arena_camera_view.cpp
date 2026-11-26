#include "frontend/sdl/arena_camera_view.h"

#include <cmath>
#include <string>

#include "gamez/zclass/camera.h"
#include "mech3/arena.h"

namespace sdlfe {
namespace {

namespace cam = mech3::arena_camera;

constexpr float kPi = 3.14159265358979f;

bool is_fly_key(SDL_Scancode code) {
    switch (code) {
    case SDL_SCANCODE_W:
    case SDL_SCANCODE_A:
    case SDL_SCANCODE_S:
    case SDL_SCANCODE_D:
    case SDL_SCANCODE_Q:
    case SDL_SCANCODE_E:
        return true;
    default:
        return false;
    }
}

bool is_shift(SDL_Scancode code) {
    return code == SDL_SCANCODE_LSHIFT || code == SDL_SCANCODE_RSHIFT;
}

} // namespace

void ArenaCameraView::release_input() {
    for (bool &key : held_)
        key = false;
    set_looking(false);
    last_ns_ = 0; // after a pause or lost focus, the next frame starts from a standstill
    look_dx_ = look_dy_ = zoom_ = 0;
}

// While the right button is held the pointer is captured (relative mode), so
// the look keeps turning past the screen's edge.
void ArenaCameraView::set_looking(bool on) {
    if (looking_ == on)
        return;
    looking_ = on;
    if (window_)
        SDL_SetWindowRelativeMouseMode(window_, on);
}

void ArenaCameraView::take_control() {
    if (camera_.mode() != cam::Mode::Free)
        camera_.toggle_free();
}

bool ArenaCameraView::handle(const SDL_Event &event) {
    if (event.type == SDL_EVENT_WINDOW_FOCUS_LOST) {
        release_input();
        return false; // the game's own handling of it goes on
    }
    // Before a match starts and after it ends (loading, the lobby) the input
    // is the game's, and nothing piles up for the next match's first frame.
    // place_camera may stop running after a match (a 2D screen), so the
    // match is asked here too, and anything held is let go when it ends.
    if (match_live_ && mech3::arena::arena_mechs().empty()) {
        release_input();
        camera_.reset();
        match_live_ = false;
    }
    if (!match_live_)
        return false;
    switch (event.type) {
    case SDL_EVENT_KEY_DOWN: {
        const SDL_Scancode code = event.key.scancode;
        // A held key's repeats act once: holding V or C must not flip the mode
        // back and forth, and a held fly key must not undo a mode key.
        const bool repeat = event.key.repeat;
        if (is_fly_key(code)) {
            held_[code] = true;
            if (!repeat)
                take_control();
            return true;
        }
        if (is_shift(code)) {
            held_[code] = true;
            return false; // the game may read Shift too; it moves nothing for a spectator
        }
        const bool shift = (event.key.mod & SDL_KMOD_SHIFT) != 0;
        switch (event.key.key) {
        case SDLK_C:
            if (!repeat)
                camera_.cycle(shift ? -1 : 1);
            return true;
        case SDLK_V:
            if (!repeat)
                camera_.toggle_free();
            return true;
        case SDLK_1:
            if (!repeat)
                camera_.set_mode(cam::Mode::Chase);
            return true;
        case SDLK_2:
            if (!repeat)
                camera_.set_mode(cam::Mode::Cockpit);
            return true;
        case SDLK_3:
            if (!repeat)
                camera_.set_mode(cam::Mode::Orbit);
            return true;
        case SDLK_4:
            if (!repeat)
                camera_.set_mode(cam::Mode::Overhead);
            return true;
        case SDLK_5:
            if (!repeat)
                camera_.set_mode(cam::Mode::Free);
            return true;
        case SDLK_TAB:
            if (repeat)
                return true;
            if (shift)
                mech3::arena::arena_view_previous();
            else
                mech3::arena::arena_view_next();
            return true;
        case SDLK_RIGHTBRACKET:
            if (!repeat)
                mech3::arena::arena_view_next();
            return true;
        case SDLK_LEFTBRACKET:
            if (!repeat)
                mech3::arena::arena_view_previous();
            return true;
        case SDLK_EQUALS:
        case SDLK_KP_PLUS:
            zoom_ += 1;
            return true;
        case SDLK_MINUS:
        case SDLK_KP_MINUS:
            zoom_ -= 1;
            return true;
        // Escape (the quit box) and every other key go to the game.
        default:
            return false;
        }
    }
    case SDL_EVENT_KEY_UP:
        if (is_shift(event.key.scancode)) {
            held_[event.key.scancode] = false;
            return false;
        }
        if (!is_fly_key(event.key.scancode))
            return false;
        held_[event.key.scancode] = false;
        return true;
    case SDL_EVENT_MOUSE_BUTTON_DOWN:
        if (event.button.button != SDL_BUTTON_RIGHT)
            return false;
        set_looking(true);
        take_control();
        return true;
    case SDL_EVENT_MOUSE_BUTTON_UP:
        if (event.button.button != SDL_BUTTON_RIGHT)
            return false;
        set_looking(false);
        return true;
    case SDL_EVENT_MOUSE_MOTION:
        if (!looking_)
            return false;
        look_dx_ += event.motion.xrel;
        look_dy_ += event.motion.yrel;
        return true;
    case SDL_EVENT_MOUSE_WHEEL:
        zoom_ += event.wheel.y;
        return true;
    default:
        return false;
    }
}

void ArenaCameraView::place_camera(zcls::Node *camera) {
    if (!camera || mech3::arena::arena_headless())
        return;
    const uint64_t now = SDL_GetTicksNS();
    const float dt =
        last_ns_ ? static_cast<float>(static_cast<double>(now - last_ns_) * 1e-9) : 0.0f;
    last_ns_ = now;

    cam::Subject subject;
    cam::Action action;
    if (!mech3::arena::arena_camera_view(&subject, &action)) {
        // No match running (loading, or after the end): drop the input so it
        // can't all land on the first frame of the next match, and jump to that
        // match's first view rather than glide from this one.
        camera_.reset();
        last_ns_ = 0; // the next match's first frame starts from a standstill
        if (match_live_)
            release_input();
        match_live_ = false;
        return;
    }

    match_live_ = true;
    const auto key = [&](SDL_Scancode code) { return held_[code] ? 1.0f : 0.0f; };
    cam::Input input;
    input.forward = key(SDL_SCANCODE_W) - key(SDL_SCANCODE_S);
    input.right = key(SDL_SCANCODE_D) - key(SDL_SCANCODE_A);
    input.up = key(SDL_SCANCODE_E) - key(SDL_SCANCODE_Q);
    input.look_dx = look_dx_;
    input.look_dy = look_dy_;
    input.zoom = zoom_;
    input.fast = held_[SDL_SCANCODE_LSHIFT] || held_[SDL_SCANCODE_RSHIFT];
    look_dx_ = look_dy_ = zoom_ = 0;

    const cam::Pose pose = camera_.update(subject, action, input, dt);
    // As the 3D replay places the mission's camera (replay3d_view.cpp): the
    // node's x angle is minus the pitch and its y angle the yaw turned half
    // round, because the game's camera looks down its own -z.
    zcls::camera_set_rotation(camera, -pose.pitch, pose.yaw + kPi, 0.0f);
    zcls::camera_set_position(camera, pose.eye[0], pose.eye[1], pose.eye[2]);
    show_caption();
}

void ArenaCameraView::show_caption() {
    if (!window_)
        return;
    std::string caption = std::string("MechWarrior 3 arena - ") + cam::mode_name(camera_.mode());
    int id = 0;
    std::string label;
    if (camera_.mode() != cam::Mode::Free && camera_.mode() != cam::Mode::Orbit &&
        mech3::arena::arena_viewed_label(&id, &label))
        caption += ": mech " + std::to_string(id) + " (" + label + ")";
    caption += "  |  C mode, 1-5 pick, Tab mech, V free, right mouse look, WASD QE fly, wheel zoom";
    if (caption == caption_)
        return;
    caption_ = caption;
    SDL_SetWindowTitle(window_, caption_.c_str());
}

} // namespace sdlfe
