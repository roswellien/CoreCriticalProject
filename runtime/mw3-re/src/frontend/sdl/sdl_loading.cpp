#include "frontend/sdl/sdl_loading.h"
#include "frontend/sdl/sdl_child.h"
#include "frontend/sdl/sdl_input.h"

#include <algorithm>
#include <cmath>
#include <cstdio>

#if defined(_WIN32)
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#endif

namespace sdlfe {
namespace {
bool SDLCALL keep_loading_event(void*, SDL_Event* event) {
  const auto type = event->type;
  return !((type >= SDL_EVENT_KEY_DOWN && type <= SDL_EVENT_KEYMAP_CHANGED) ||
      (type >= SDL_EVENT_MOUSE_MOTION && type <= SDL_EVENT_MOUSE_WHEEL) ||
      (type >= SDL_EVENT_JOYSTICK_AXIS_MOTION && type <= SDL_EVENT_JOYSTICK_BUTTON_UP) ||
      (type >= SDL_EVENT_GAMEPAD_AXIS_MOTION && type <= SDL_EVENT_GAMEPAD_BUTTON_UP) ||
      (type >= SDL_EVENT_FINGER_DOWN && type <= SDL_EVENT_FINGER_CANCELED));
}

// The exact authored paths in CoreCriticalLoadingMark.xaml. Circular arcs are
// tessellated once into the 64px software mark; no asset files are required.
struct Point { float x, y; };
struct Section { Point points[9]; Point arc_center; unsigned arc_at; };
constexpr Section sections[] = {
  {{{677,61},{929,61},{1229,550},{1229,571},{847,571},{677,412},{677,61}}, {630.464792f,632.135128f}, 4},
  {{{1229,677},{1229,698},{925,1180},{677,1180},{677,847},{850,677},{1229,677}}, {630.666459f,626.822338f}, 4},
  {{{19,677},{402,677},{575,847},{575,1180},{320,1180},{19,698},{19,677}}, {621.333541f,626.822338f}, 1},
  {{{328,61},{578,61},{578,412},{406,571},{19,571},{19,550},{328,61}}, {622.410963f,632.573494f}, 2}
};
// Point containment against the path with its SVG small, counterclockwise circular arc.
bool inside(float x, float y, const Section& section) {
  Point polygon[40];
  unsigned count = 0;
  for (unsigned i = 0; i < 7; ++i) {
    polygon[count++] = section.points[i];
    if (i != section.arc_at) continue;
    const auto a = section.points[i], b = section.points[i + 1], c = section.arc_center;
    float start = std::atan2(a.y - c.y, a.x - c.x);
    float end = std::atan2(b.y - c.y, b.x - c.x);
    while (end > start) end -= 6.283185307f;
    for (unsigned j = 1; j < 24; ++j) {
      const float angle = start + (end - start) * j / 24;
      polygon[count++] = {c.x + 225 * std::cos(angle), c.y + 225 * std::sin(angle)};
    }
  }
  bool contained = false;
  for (unsigned i = 0, j = count - 1; i < count; j = i++) {
    const auto a = polygon[i], b = polygon[j];
    if ((a.y > y) != (b.y > y) && x < (b.x - a.x) * (y - a.y) / (b.y - a.y) + a.x)
      contained = !contained;
  }
  return contained;
}
}  // namespace

void pump_loading_events() {
  SDL_PumpEvents();
  SDL_FilterEvents(keep_loading_event, nullptr);
}

float loading_mark_light(Uint64 milliseconds, unsigned section) {
  const float time = static_cast<float>(milliseconds % 2800) - section * 700.0f;
  if (time < 0 || time >= 640) return 0;
  const float position = time < 280 ? time / 280 : (640 - time) / 360;
  return (1 - std::cos(position * 3.141592654f)) * .5f;
}

LoadingDisplay::LoadingDisplay(SDL_Window* parent, SdlInput* input, bool hidden)
    : parent_(parent), input_(input), hidden_(hidden), previous_(std::move(platform::loading::observer)) {
#if defined(_WIN32)
  BOOL enabled = TRUE;
  if (SystemParametersInfoW(SPI_GETCLIENTAREAANIMATION, 0, &enabled, 0)) animate_ = enabled != FALSE;
#endif
  platform::loading::observer = [this](const auto& progress) { update(progress); };
}

LoadingDisplay::~LoadingDisplay() {
  close();
  platform::loading::observer = std::move(previous_);
}

void LoadingDisplay::close() {
  if (renderer_) SDL_DestroyRenderer(renderer_);
  if (window_) SDL_DestroyWindow(window_);
  renderer_ = nullptr;
  window_ = nullptr;
}

void LoadingDisplay::update(const platform::loading::Progress& progress) {
  if (progress.active || active_) pump_loading_events();
  if (active_ != progress.active) {
    input_->discard_loading_input();
    active_ = progress.active;
    began_ = SDL_GetTicks();
  }
  if (!progress.active) {
    close();
    set_ready_status("");
    return;
  }
  std::string status = progress.text;
  if (progress.percent >= 0) status += " (" + std::to_string(progress.percent) + "%)";
  set_ready_status(status);
  if (hidden_ || failed_ || (SDL_GetWindowFlags(parent_) & SDL_WINDOW_MINIMIZED)) return;
  if (!window_) {
    int width = 0, height = 0;
    SDL_GetWindowSize(parent_, &width, &height);
    window_ = SDL_CreatePopupWindow(parent_, (width - 440) / 2, (height - 120) / 2,
        440, 120, SDL_WINDOW_TOOLTIP | SDL_WINDOW_NOT_FOCUSABLE);
    if (window_) renderer_ = SDL_CreateRenderer(window_, "software");
    if (!renderer_) {
      std::fprintf(stderr, "mw3: loading animation unavailable: %s; progress remains in log\n", SDL_GetError());
      close();
      failed_ = true;
      return;
    }
  }
  SDL_SetRenderDrawColor(renderer_, 25, 23, 20, 255);
  SDL_RenderClear(renderer_);
  // Cache coverage once. Only four opacity values and 4096 pixels change per redraw.
  static const auto mask = [] {
    std::array<unsigned char, 64 * 64> pixels{};
    for (unsigned y = 0; y < 64; ++y)
      for (unsigned x = 0; x < 64; ++x)
        for (unsigned s = 0; s < 4; ++s)
          if (inside((x + .5f) * 1254 / 64, (y + .5f) * 1254 / 64, sections[s]))
            pixels[y * 64 + x] = static_cast<unsigned char>(s + 1);
    return pixels;
  }();
  const Uint64 elapsed = SDL_GetTicks() - began_;
  for (unsigned y = 0; y < 64; ++y) {
    for (unsigned x = 0; x < 64; ++x) {
      const auto section = mask[y * 64 + x];
      if (!section) continue;
      const float light = animate_ ? loading_mark_light(elapsed, section - 1) : .45f;
      const float gradient = static_cast<float>(y) / 64;
      const unsigned char base[] = {static_cast<unsigned char>(197 - 33 * gradient),
          static_cast<unsigned char>(144 - 41 * gradient), static_cast<unsigned char>(67 - 24 * gradient)};
      const float radius = std::min(1.0f, std::hypot((x - 32.0f) / 51, (y - 27.0f) / 51));
      const unsigned char lit[] = {static_cast<unsigned char>(255 - 40 * radius),
          static_cast<unsigned char>(246 - 112 * radius), static_cast<unsigned char>(197 - 152 * radius)};
      SDL_SetRenderDrawColor(renderer_, static_cast<Uint8>(base[0] + (lit[0] - base[0]) * light),
          static_cast<Uint8>(base[1] + (lit[1] - base[1]) * light),
          static_cast<Uint8>(base[2] + (lit[2] - base[2]) * light), 255);
      SDL_RenderPoint(renderer_, 18.0f + x, 24.0f + y);
    }
  }
  SDL_SetRenderDrawColor(renderer_, 255, 226, 180, 255);
  // Clip long original load messages to the available text area.
  const std::string label = status.substr(0, 39);
  SDL_RenderDebugText(renderer_, 104, 39, label.c_str());
  if (progress.percent >= 0) {
    SDL_SetRenderDrawColor(renderer_, 87, 63, 34, 255);
    SDL_FRect bar{104, 72, 312, 3};
    SDL_RenderFillRect(renderer_, &bar);
    SDL_SetRenderDrawColor(renderer_, 255, 213, 111, 255);
    bar.w *= progress.percent / 100.0f;
    SDL_RenderFillRect(renderer_, &bar);
  }
  SDL_RenderPresent(renderer_);
}
}  // namespace sdlfe
