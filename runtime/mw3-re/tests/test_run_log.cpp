// Checks for RunLog (#521) with real pipes and files: a line printed just before
// a fast exit, and a line still missing its newline, both reach the log through
// log::drain before the program would end. A program of its own, because an
// open RunLog takes over this process's stdout and stderr.
#include "frontend/sdl/log.h"
#include "frontend/sdl/run_log.h"

#include <chrono>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>
#include <thread>

namespace {
std::string text_of(const std::filesystem::path& path) {
  std::ifstream in(path, std::ios::binary);
  std::stringstream all;
  all << in.rdbuf();
  return all.str();
}
}  // namespace

int main() {
  namespace fs = std::filesystem;
  const fs::path dir = fs::path(MW3_TEST_TMP) / "run_log_drain";
  std::error_code ec;
  fs::remove_all(dir, ec);
  fs::create_directories(dir, ec);
  std::string failure;
  {
    sdlfe::RunLog log;
    if (!log.open(dir.string(), "drain")) {
      std::fprintf(stderr, "cannot open the log in %s\n", dir.string().c_str());
      return 1;
    }
    // Quiet for longer than the drain's 20 ms first, so a drain timed from the reader's last activity
    // would return before reading what comes next.
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    sdlfe::log::line(sdlfe::log::Level::error, "mw3: the last words before _Exit\n");
    std::printf("mw3: a line still missing its newline");
    sdlfe::log::drain();
    const std::string now = text_of(dir / "drain.log");
    const std::string problems = text_of(dir / "drain-problems.log");
    if (now.find("] E mw3: the last words before _Exit\n") == std::string::npos)
      failure = "the last line before the exit is not in the log";
    else if (now.find("] I mw3: a line still missing its newline\n") == std::string::npos)
      failure = "the line missing its newline was not written out";
    else if (problems.find("] E mw3: the last words before _Exit\n") == std::string::npos)
      failure = "the E line is not in the problems log";
  }
  // The log is closed here: this process's stdout is the console (or the log's file) again.
  if (!failure.empty()) {
    std::fprintf(stderr, "%s\n", failure.c_str());
    return 1;
  }
  std::puts("RunLog drain checks passed");
  return 0;
}
