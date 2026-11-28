#pragma once
// What test_program.cpp's headless runs and test_arena_game.cpp's arena runs
// both need: the fake window, clock and screen the program gives the engine,
// the mounts guard, and the game-files and temp-folder helpers. It includes
// mech3/mission.h itself (CountingPump's quit cleans the missions up).
#include <cstdint>
#include <filesystem>
#include <functional>
#include <string>
#include <vector>

#include "check.h"
#include "gamez/zutil/zutl_path.h"
#include "mech3/app_engine.h"
#include "mech3/mission.h"
#include "platform/platform.h"

struct SavedMounts {
  zutl::Mounts saved = zutl::mounts();
  ~SavedMounts() { zutl::mounts() = saved; }
};

inline bool have_game() { return std::filesystem::exists(std::string(MW3_GAME_DIR) + "/Mech3Msg.dll"); }

inline std::string temp_dir(const char* name) {
  const std::string d = std::string(MW3_TEST_TMP) + "/" + name;
  std::error_code ec;
  std::filesystem::remove_all(d, ec);
  std::filesystem::create_directories(d, ec);
  return d;
}

// Defined in test_program.cpp: puts the process-wide state back to a new
// process's, between two apps in one process.
void reset_process_state();

// What the program gives the engine, without a window.
struct FakeWindow : platform::Window {
  std::string title;
  bool shown = false;
  uint32_t create(const std::string& t, int, int) override { return title = t, 0x1234; }
  void set_title(const std::string& t) override { title = t; }
  void show() override { shown = true; }
  void client_size(int* w, int* h) override { *w = 640, *h = 480; }
};
struct FakeAlert : platform::Alert {
  std::vector<std::string> shown;
  void abort_message(const std::string& m) override { shown.push_back(m); }
};
struct FakeClock : platform::Clock {
  uint32_t now = 0;
  uint32_t ticks_ms() override { return now += 16; }
};
// Ours (#485, docs/fixed-step.md): for the life of one test, an engine made
// in it calls on_present after each mission step instead of each frame drawn
// in a mission. For the whole-mission tests that count on_present calls as the
// game's ticks: each call is one 1/30 s step, however many steps a drawn frame
// ran (FakeClock's time moves on each time the game reads it, so that varies).
// The fixed step's own tests cover frames that run no step or several.
struct PresentOnSteps {
  PresentOnSteps() { mech3::GameEngine::present_per_step = true; }
  ~PresentOnSteps() { mech3::GameEngine::present_per_step = false; }
  PresentOnSteps(const PresentOnSteps&) = delete;
  PresentOnSteps& operator=(const PresentOnSteps&) = delete;
};
// zFMV's clock in the tests: a second a call, so the movie scripts' waits
// (the Intro's SPLASH, 4 s) pass in a few frames.
struct MovieClock : platform::Clock {
  uint32_t now = 0;
  uint32_t ticks_ms() override { return now += 1000; }
};
inline platform::Clock& fast_movie_clock() {
  static MovieClock c;
  return c;
}
struct FakeScreen : platform::Screen2D {
  int frames = 0;
  void present_16(const uint16_t*, int w, int h, int, bool) override { frames += w == 640 && h == 480; }
};
// Quits after `passes` waits for a message: the loop runs that many passes.
struct CountingPump : platform::MessagePump {
  int passes = 0, limit = 200;
  bool quit = false;
  std::function<void()> on_quit;  // unset: the mission's cleanup
  std::function<bool()> stop;     // set: quits as soon as it says so
  bool peek() override { return ++passes > limit || (stop && stop()); }
  // The quit: a mission still up is cleaned up first, as a debriefing would,
  // while zSound is still there (ExitInstance shuts it down next; a running
  // animation's sounds would be stopped after it).
  bool pump() override {
    if (on_quit) on_quit();
    else mech3::missions().cleanup(false);
    return false;
  }
  void wait(uint32_t) override {}
  void post_quit() override { quit = true; }
};
