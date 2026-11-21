#include "check.h"
#include "frontend/sdl/sdl_input.h"
#include "frontend/sdl/sdl_loading.h"
#include "platform/loading.hpp"
#include <cfenv>
#include <chrono>
#include <string>
#include <thread>

TEST(loading_progress_nested_lifetime_and_fp) {
  using namespace platform::loading;
  const auto previous = std::move(observer);
  std::vector<Progress> events;
  observer = [&](const Progress& state) {
    events.push_back(state);
    std::fesetround(FE_DOWNWARD);
    std::feraiseexcept(FE_INVALID);
    checkpoint(true);  // An observer must never recursively reenter itself.
  };
  std::fenv_t original;
  std::fegetenv(&original);
  std::fesetround(FE_TOWARDZERO);
  std::feclearexcept(FE_ALL_EXCEPT);
  {
    Session outer("fixture", "Loading fixture");
    report("Textures", 30);
    report_percent(45);  // a fraction alone keeps the text
    EXPECT(progress.text == "Textures");
    EXPECT(progress.percent == 45);
    { Session inner("nested", "Nested"); report("Models", 80); }
    EXPECT(progress.active);
    EXPECT(progress.percent == 80);
  }
  EXPECT(!events.empty());
  EXPECT(events.front().active);
  EXPECT(!events.back().active);
  EXPECT(std::fegetround() == FE_TOWARDZERO);
  EXPECT(std::fetestexcept(FE_INVALID) == 0);
  std::fesetenv(&original);
  observer = previous;
}

TEST(loading_reports_share_the_redraw_throttle) {
  using namespace platform::loading;
  const auto previous = std::move(observer);
  unsigned redraws = 0;
  std::string last_text;
  observer = [&](const Progress& state) {
    ++redraws;
    last_text = state.text;
  };
  {
    Session load("throttle-fixture", "Loading fixture");
    const unsigned at_start = redraws;  // the session itself always shows
    EXPECT(at_start == 1);
    for (int line = 0; line < 2000; ++line) report("A load line", line % 100);
    // 2000 lines in a few milliseconds: a handful of redraws, not one per line.
    EXPECT(redraws - at_start <= 3);
    std::this_thread::sleep_for(std::chrono::milliseconds(40));
    report("Last line", 99);
    EXPECT(last_text == "Last line");
  }
  EXPECT(!progress.active);
  observer = previous;
}

TEST(loading_long_work_pumps_and_retains_safe_events) {
  EXPECT(SDL_Init(SDL_INIT_VIDEO | SDL_INIT_EVENTS));
  SDL_Window* window = SDL_CreateWindow("Loading fixture", 640, 240, SDL_WINDOW_HIDDEN);
  EXPECT(window != nullptr);
  if (!window) { SDL_Quit(); return; }
  sdlfe::SdlInput input;
  SDL_Event key{};
  key.type = SDL_EVENT_KEY_DOWN;
  key.key.scancode = SDL_SCANCODE_W;
  key.key.down = true;
  input.on_event(key);
  EXPECT(input.key_down(0x11));
  const auto music = SDL_RegisterEvents(1);
  unsigned ticks = 0;
  {
    sdlfe::LoadingDisplay display(window, &input, true);
    platform::loading::Session load("long-fixture", "Loading fixture");
    SDL_PushEvent(&key);
    SDL_Event event{};
    event.type = SDL_EVENT_WINDOW_FOCUS_LOST;
    SDL_PushEvent(&event);
    event.type = SDL_EVENT_JOYSTICK_REMOVED;
    SDL_PushEvent(&event);
    event.type = music;
    SDL_PushEvent(&event);
    event.type = SDL_EVENT_QUIT;
    SDL_PushEvent(&event);
    // Longer than Windows' ordinary hung-window threshold. This loop represents
    // synchronous decode work, without running the application's message pump.
    const auto end = SDL_GetTicks() + 5500;
    while (SDL_GetTicks() < end) {
      platform::loading::checkpoint();
      SDL_Delay(10);
      ++ticks;
    }
    EXPECT(ticks > 100);
    // Windows calls a window hung after about 5 s without messages; stay far below that.
    EXPECT(platform::loading::longest_unpumped_ms < 500);
    EXPECT(!input.key_down(0x11));
    EXPECT(!SDL_HasEvent(SDL_EVENT_KEY_DOWN));
    EXPECT(SDL_HasEvent(SDL_EVENT_WINDOW_FOCUS_LOST));
    EXPECT(SDL_HasEvent(SDL_EVENT_JOYSTICK_REMOVED));
    EXPECT(SDL_HasEvent(music));
    EXPECT(SDL_HasEvent(SDL_EVENT_QUIT));
  }
  EXPECT(!input.key_down(0x11));
  SDL_DestroyWindow(window);
  SDL_Quit();
}

TEST(loading_mark_original_clockwise_timing) {
  for (unsigned section = 0; section < 4; ++section) {
    EXPECT(sdlfe::loading_mark_light(section * 700 + 280, section) > .999f);
    EXPECT(sdlfe::loading_mark_light(section * 700 + 640, section) == 0);
    EXPECT(sdlfe::loading_mark_light(section * 700, section) == 0);
  }
  EXPECT(sdlfe::loading_mark_light(2800 + 280, 0) > .999f);
}
