#pragma once
#include <SDL3/SDL.h>
#include "platform/loading.hpp"

namespace sdlfe {
class SdlInput;
// Owns only a small software window; never touches the game's GPU command stream.
class LoadingDisplay {
 public:
  LoadingDisplay(SDL_Window* parent, SdlInput* input, bool hidden);
  ~LoadingDisplay();
  void update(const platform::loading::Progress& progress);
 private:
  SDL_Window* parent_;
  SdlInput* input_;
  SDL_Window* window_ = nullptr;
  SDL_Renderer* renderer_ = nullptr;
  bool hidden_, active_ = false, failed_ = false, animate_ = true;
  Uint64 began_ = 0;
  std::function<void(const platform::loading::Progress&)> previous_;
  void close();
};
// Pumps OS messages, discards gameplay input, retains quit/window/device/music events
// for the ordinary game loop after initialization finishes.
void pump_loading_events();
float loading_mark_light(Uint64 milliseconds, unsigned section);
}  // namespace sdlfe
