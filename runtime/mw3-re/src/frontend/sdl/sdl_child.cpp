#include "frontend/sdl/sdl_child.h"
#include "platform/loading.hpp"

#include <string>

#if defined(_WIN32)
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <io.h>
#include <windows.h>
#include <psapi.h>
#elif defined(__APPLE__)
#include <mach/mach.h>
#else
#include <unistd.h>
#endif

#include <cstdio>

namespace sdlfe {

SDL_Process* start_child(const char* const* args) {
#if defined(_WIN32)
  if (!GetConsoleWindow()) {
    const SDL_PropertiesID p = SDL_CreateProperties();
    SDL_SetPointerProperty(p, SDL_PROP_PROCESS_CREATE_ARGS_POINTER, const_cast<char**>(args));
    SDL_SetNumberProperty(p, SDL_PROP_PROCESS_CREATE_STDIN_NUMBER, SDL_PROCESS_STDIO_APP);
    SDL_SetNumberProperty(p, SDL_PROP_PROCESS_CREATE_STDOUT_NUMBER, SDL_PROCESS_STDIO_APP);
    SDL_SetBooleanProperty(p, SDL_PROP_PROCESS_CREATE_BACKGROUND_BOOLEAN, true);
    SDL_Process* proc = SDL_CreateProcessWithProperties(p);
    SDL_DestroyProperties(p);
    return proc;
  }
#endif
  return SDL_CreateProcess(args, true);
}

namespace {
std::string g_ready_file;
bool g_ready = false;
bool g_menu_ready = false;
std::string g_last_status;
}  // namespace
void set_ready_file(const std::string& path) {
  g_ready_file = path;
  g_ready = g_menu_ready = false;
  g_last_status.clear();
}
void set_ready_status(const std::string& text) {
  // Loads report many times a second; rewrite the file only when the text changes.
  if (g_ready_file.empty() || (!text.empty() && text == g_last_status)) return;
  g_last_status = text;
  const std::string path = g_ready_file + ".status";
  if (text.empty()) {
    std::remove(path.c_str());
    return;
  }
  const std::string tmp = path + ".new";  // whole lines only: written aside, then moved over
  if (std::FILE* f = std::fopen(tmp.c_str(), "wb")) {
    std::fwrite(text.data(), 1, text.size(), f);
    std::fclose(f);
    std::remove(path.c_str());
    std::rename(tmp.c_str(), path.c_str());
  }
}
void mark_menu_ready() {
  if (g_menu_ready) return;
  g_menu_ready = true;
  std::printf("mw3: timing main menu presented at %lld ms since process start\n",
              platform::loading::since_process_start_ms());
  if (!g_ready_file.empty()) {
    const std::string path = g_ready_file + ".menu";
    if (std::FILE* file = std::fopen(path.c_str(), "wb")) std::fclose(file);
  }
}
void mark_ready() {
  if (g_ready) return;
  g_ready = true;
  // Every run, with or without a ready file: this line also goes to mw3-problems.log (log_lines.h), and the
  // launcher counts only problems stamped after it, on the game's own clock (GameProblemsLog.cs).
  std::printf("mw3: first frame shown at %lld ms since process start%s\n",
              platform::loading::since_process_start_ms(), g_ready_file.empty() ? "" : " (the launcher told)");
  if (g_ready_file.empty()) return;
  set_ready_status("");
  if (std::FILE* f = std::fopen(g_ready_file.c_str(), "wb")) std::fclose(f);
}

size_t resident_kb() {
#if defined(_WIN32)
  PROCESS_MEMORY_COUNTERS c{};
  if (!K32GetProcessMemoryInfo(GetCurrentProcess(), &c, sizeof c)) return 0;
  return static_cast<size_t>(c.WorkingSetSize / 1024);
#elif defined(__APPLE__)
  mach_task_basic_info info{};
  mach_msg_type_number_t n = MACH_TASK_BASIC_INFO_COUNT;
  if (task_info(mach_task_self(), MACH_TASK_BASIC_INFO, reinterpret_cast<task_info_t>(&info), &n) != KERN_SUCCESS) return 0;
  return static_cast<size_t>(info.resident_size / 1024);
#else
  long pages = 0, rss = 0;
  std::FILE* f = std::fopen("/proc/self/statm", "r");
  if (!f) return 0;
  const bool ok = std::fscanf(f, "%ld %ld", &pages, &rss) == 2;
  std::fclose(f);
  return ok ? static_cast<size_t>(rss) * static_cast<size_t>(sysconf(_SC_PAGESIZE)) / 1024 : 0;
#endif
}

}  // namespace sdlfe
