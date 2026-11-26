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
    case SDL_SCANCODE_W: case SDL_SCANCODE_A: case SDL_SCANCODE_S:
    case SDL_SCANCODE_D: case SDL_SCANCODE_Q: case SDL_SCANCODE_E:
      return true;
    default:
      return false;
  }
}

bool is_shift(SDL_Scancode code) { return code == SDL_SCANCODE_LSHIFT || code == SDL_SCANCODE_RSHIFT; }

}  // namespace

void ArenaCameraView::release_input() {
  for (bool& key : held_) key = false;
  looking_ = false;
}

void ArenaCameraView::take_control() {
  if (camera_.mode() != cam::Mode::Free) camera_.toggle_free();
}

bool ArenaCameraView::handle(const SDL_Event& event) {
  if (event.type == SDL_EVENT_WINDOW_FOCUS_LOST) {
    release_input();
    return false;  // the game's own handling of it goes on
  }
  switch (event.type) {
    case SDL_EVENT_KEY_DOWN: {
      const SDL_Scancode code = event.key.scancode;
      if (is_fly_key(code)) {
        held_[code] = true;
        take_control();
        return true;
      }
      if (is_shift(code)) {
        held_[code] = true;
        return false;  // the game may read Shift too; it moves nothing for a spectator
      }
      const bool shift = (event.key.mod & SDL_KMOD_SHIFT) != 0;
      switch (event.key.key) {
        case SDLK_C: camera_.cycle(shift ? -1 : 1); return true;
        case SDLK_V: camera_.toggle_free(); return true;
        case SDLK_1: camera_.set_mode(cam::Mode::Chase); return true;
        case SDLK_2: camera_.set_mode(cam::Mode::Cockpit); return true;
        case SDLK_3: camera_.set_mode(cam::Mode::Orbit); return true;
        case SDLK_4: camera_.set_mode(cam::Mode::Overhead); return true;
        case SDLK_5: camera_.set_mode(cam::Mode::Free); return true;
        case SDLK_TAB:
          if (shift) mech3::arena::arena_view_previous();
          else mech3::arena::arena_view_next();
          return true;
        case SDLK_RIGHTBRACKET: mech3::arena::arena_view_next(); return true;
        case SDLK_LEFTBRACKET: mech3::arena::arena_view_previous(); return true;
        case SDLK_EQUALS: case SDLK_KP_PLUS: zoom_ += 1; return true;
        case SDLK_MINUS: case SDLK_KP_MINUS: zoom_ -= 1; return true;
        // Escape (the quit box) and every other key go to the game.
        default: return false;
      }
    }
    case SDL_EVENT_KEY_UP:
      if (is_shift(event.key.scancode)) {
        held_[event.key.scancode] = false;
        return false;
      }
      if (!is_fly_key(event.key.scancode)) return false;
      held_[event.key.scancode] = false;
      return true;
    case SDL_EVENT_MOUSE_BUTTON_DOWN:
      if (event.button.button != SDL_BUTTON_RIGHT) return false;
      looking_ = true;
      take_control();
      return true;
    case SDL_EVENT_MOUSE_BUTTON_UP:
      if (event.button.button != SDL_BUTTON_RIGHT) return false;
      looking_ = false;
      return true;
    case SDL_EVENT_MOUSE_MOTION:
      if (!looking_) return false;
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

void ArenaCameraView::place_camera(zcls::Node* camera) {
  if (!camera || mech3::arena::arena_headless()) return;
  const uint64_t now = SDL_GetTicksNS();
  const float dt = last_ns_ ? static_cast<float>(static_cast<double>(now - last_ns_) * 1e-9) : 0.0f;
  last_ns_ = now;

  cam::Subject subject;
  cam::Action action;
  if (!mech3::arena::arena_camera_view(&subject, &action)) return;

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
  if (!window_) return;
  std::string caption = std::string("MechWarrior 3 arena - ") + cam::mode_name(camera_.mode());
  int id = 0;
  std::string label;
  if (camera_.mode() != cam::Mode::Free && camera_.mode() != cam::Mode::Orbit &&
      mech3::arena::arena_viewed_label(&id, &label))
    caption += ": mech " + std::to_string(id) + " (" + label + ")";
  caption += "  |  C mode, 1-5 pick, Tab mech, V free, right mouse look, WASD QE fly, wheel zoom";
  if (caption == caption_) return;
  caption_ = caption;
  SDL_SetWindowTitle(window_, caption_.c_str());
}

}  // namespace sdlfe
