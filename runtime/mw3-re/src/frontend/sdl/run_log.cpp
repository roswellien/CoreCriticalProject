#include "frontend/sdl/run_log.h"

#include <atomic>
#include <chrono>
#include <cstdio>
#include <filesystem>
#include <mutex>
#include <string>
#include <system_error>
#include <thread>

#include "frontend/sdl/log_lines.h"
#include "frontend/sdl/log_start.h"
#include "platform/loading.hpp"

#if defined(_WIN32)
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <fcntl.h>
#include <io.h>
#include <windows.h>
#else
#include <fcntl.h>
#include <unistd.h>
#endif

namespace sdlfe {

namespace {
#if defined(_WIN32)
int fd_dup(int fd) { return _dup(fd); }
int fd_dup2(int from, int to) { return _dup2(from, to); }
int fd_pipe(int p[2]) { return _pipe(p, 1 << 16, _O_BINARY); }
void fd_private(int) {}  // _dup2 onto 1 and 2 also sets the std handles a child inherits
long fd_read(int fd, char* b, unsigned n) { return _read(fd, b, n); }
void fd_write(int fd, const char* b, long n) { (void)_write(fd, b, static_cast<unsigned>(n)); }
void fd_close(int fd) { _close(fd); }
int fd_open_null() { return _open("NUL", _O_WRONLY | _O_BINARY); }
int fd_of(std::FILE* f) { return _fileno(f); }
std::wstring wide(const std::string& u8) {
  std::wstring w(static_cast<size_t>(MultiByteToWideChar(CP_UTF8, 0, u8.c_str(), -1, nullptr, 0)), L'\0');
  if (!w.empty()) MultiByteToWideChar(CP_UTF8, 0, u8.c_str(), -1, w.data(), static_cast<int>(w.size()));
  if (!w.empty()) w.pop_back();
  return w;
}
std::FILE* open_file(const std::string& path, const char* mode) {
  return _wfopen(wide(path).c_str(), mode[0] == 'a' ? L"ab" : L"wb");
}
// No console: how the launcher starts the game (CreateNoWindow).
bool no_console() { return GetConsoleWindow() == nullptr; }
#else
int fd_dup(int fd) { return dup(fd); }
int fd_dup2(int from, int to) { return dup2(from, to); }
int fd_pipe(int p[2]) { return pipe(p); }
long fd_read(int fd, char* b, unsigned n) { return static_cast<long>(read(fd, b, n)); }
void fd_write(int fd, const char* b, long n) {
  while (n > 0) {
    const ssize_t w = write(fd, b, static_cast<size_t>(n));
    if (w <= 0) return;
    b += w, n -= w;
  }
}
void fd_close(int fd) { close(fd); }
int fd_open_null() { return ::open("/dev/null", O_WRONLY); }
int fd_of(std::FILE* f) { return fileno(f); }
void fd_private(int fd) { fcntl(fd, F_SETFD, FD_CLOEXEC); }  // not in the programs mw3 starts
std::FILE* open_file(const std::string& path, const char* mode) { return std::fopen(path.c_str(), mode[0] == 'a' ? "ab" : "wb"); }
bool no_console() { return false; }
#endif

double seconds_since_launch() { return platform::loading::since_process_start_ms() / 1000.0; }

// The last start's file moved to <old>; tried several times, as a file just
// closed can be held for a moment (log_start.h). Returns how it went.
LogStart move_aside(const std::string& path, const std::string& old, int tries) {
  namespace fs = std::filesystem;
  std::error_code ec;
  const bool exists = fs::exists(fs::u8path(path), ec);
  return log_start(
      exists, tries,
      [&]() -> unsigned long {
#if defined(_WIN32)
        return MoveFileExW(wide(path).c_str(), wide(old).c_str(), MOVEFILE_REPLACE_EXISTING) ? 0 : GetLastError();
#else
        std::error_code move_error;
        fs::rename(path, old, move_error);
        return move_error ? static_cast<unsigned long>(move_error.value()) : 0;
#endif
      },
      [] { std::this_thread::sleep_for(std::chrono::milliseconds(50)); });
}

// A restarted run (sdl_restart.h; restart_into names the process it comes from) waits for that process to be
// gone before it moves the logs (2 s at most). Returns whether it restarted, and says how in `note`.
bool wait_for_restart_parent(std::string& note) {
#if defined(_WIN32)
  wchar_t from[32] = L"";
  if (GetEnvironmentVariableW(wide(kRestartedFromEnv).c_str(), from, 32) == 0) return false;
  SetEnvironmentVariableW(wide(kRestartedFromEnv).c_str(), nullptr);  // this start's alone, not its children's
  DWORD waited_ms = 0;
  bool was_alive = false;
  if (HANDLE p = OpenProcess(SYNCHRONIZE, FALSE, static_cast<DWORD>(wcstoul(from, nullptr, 10)))) {
    const DWORD t0 = GetTickCount();
    was_alive = WaitForSingleObject(p, 2000) != WAIT_FAILED;
    waited_ms = GetTickCount() - t0;
    CloseHandle(p);
  }
  char text[160];
  std::snprintf(text, sizeof text, "mw3: started again from process %ls (%s, %lu ms)", from,
                was_alive ? "waited for its end" : "already gone", static_cast<unsigned long>(waited_ms));
  note = text;
  return true;
#else
  (void)note;
  return false;
#endif
}
}  // namespace

// stdout and stderr each through a pipe; a thread per pipe stamps what comes
// (log_lines.h), passes the text to the console's handle and the lines to the logs.
struct RunLog::Impl {
  std::FILE* file = nullptr;
  std::FILE* problems = nullptr;
  ProblemsCap problems_cap{1u << 20};
  std::mutex lock;  // the files, the stampers' partial lines
  struct Tee {
    int fd = -1, console = -1, read = -1;
    std::atomic<bool> busy{false};               // a chunk read and not yet written out
    std::atomic<long long> last_active_ms{0};   // when it last read or wrote (since launch)
    std::thread thread;
    LineStamper stamper{'I'};
  } tees[2];
  std::string path;
  bool log_only = false;  // no console: the files are the only output

  // The files, under `lock`. The console is written by the caller outside it, so a console nobody reads
  // only holds up its own stream.
  void write_files(const LogOutput& out) {
    if (!out.log.empty()) {
      std::fwrite(out.log.data(), 1, out.log.size(), file);
      std::fflush(file);
    }
    if (problems && !out.problems.empty()) {
      const std::string kept = problems_cap.take(out.problems, seconds_since_launch());
      if (!kept.empty()) {
        std::fwrite(kept.data(), 1, kept.size(), problems);
        std::fflush(problems);
      }
    }
  }

  // One chunk (or, at `end`, what is left) stamped and written. A failure here (out of memory) loses that
  // chunk, never the game: the raw bytes go to the log unstamped instead.
  void take(Tee& t, const char* data, size_t n, bool end) {
    try {
      LogOutput out;
      {
        std::lock_guard<std::mutex> g(lock);
        if (end) t.stamper.flush(seconds_since_launch(), out);
        else t.stamper.feed(data, n, seconds_since_launch(), out);
        write_files(out);
      }
      if (t.console >= 0 && !out.console.empty())
        fd_write(t.console, out.console.data(), static_cast<long>(out.console.size()));
    } catch (...) {
      if (n > 0 && file) std::fwrite(data, 1, n, file);
    }
  }

  void pass(Tee& t) {
    char buf[4096];
    for (;;) {
      const long n = fd_read(t.read, buf, sizeof buf);
      if (n <= 0) break;
      t.busy = true;
      t.last_active_ms = platform::loading::since_process_start_ms();
      take(t, buf, static_cast<size_t>(n), false);
      t.last_active_ms = platform::loading::since_process_start_ms();
      t.busy = false;
    }
    take(t, nullptr, 0, true);
  }

  // The crash handler's and the fast exits' wait (log::drain): until both readers have been quiet for 20 ms,
  // or `max_ms`. Bytes already in a pipe end a reader's read at once, so 20 ms of quiet means they are written.
  // It only reads two atomics and sleeps: no lock, no allocation, no call on the pipes (a peek on a handle
  // whose read is blocked waits behind that read), so a crashed thread holding any of those can't block it.
  // A line printed without its newline stays in the reader until more comes.
  void drain(unsigned max_ms) {
    const long long until = platform::loading::since_process_start_ms() + max_ms;
    for (;;) {
      const long long now = platform::loading::since_process_start_ms();
      bool quiet = true;
      for (Tee& t : tees)
        if (t.read >= 0 && (t.busy || now - t.last_active_ms < 20)) quiet = false;
      if (quiet || now >= until) return;
#if defined(_WIN32)
      Sleep(5);
#else
      usleep(5000);
#endif
    }
  }
};

namespace {
std::atomic<RunLog::Impl*> g_open_log{nullptr};
}

bool RunLog::open(const std::string& dir, const std::string& name, bool problems) {
  std::string restart_note;
  const bool restarted = wait_for_restart_parent(restart_note);
  const std::string log = dir + "/" + name + ".log", old = dir + "/" + name + ".old.log";
  // The last start's log is never emptied: when it cannot be moved this start's lines are appended to it,
  // after a line that says so (log_start.h).
  const LogStart start = move_aside(log, old, log_start_tries(restarted));
  auto impl = std::make_unique<Impl>();
  impl->file = open_file(log, log_start_mode(start));
  if (!impl->file) return false;
  if (problems) {
    // Moved aside like the main log, with as many tries: a restart's old problems log is held for a moment
    // too. Unlike the main log it always starts empty, even when the move fails: kept, the last start's
    // lines (stamped by its own clock) would read to the launcher as this start's problems from play, and
    // every one of them is also in the main log, which is never emptied.
    const std::string problems_log = dir + "/" + name + "-problems.log";
    move_aside(problems_log, dir + "/" + name + "-problems.old.log", log_start_tries(restarted));
    impl->problems = open_file(problems_log, "w");
  }
  impl->path = log;
  impl->log_only = no_console();
  std::fflush(stdout);
  std::fflush(stderr);
#if defined(_WIN32)
  // With no console stdout and stderr have no handle to copy from: given the null device first, so the pipes
  // below have a stream to take over.
  if (impl->log_only) {
    if (_fileno(stdout) < 0) (void)std::freopen("NUL", "w", stdout);
    if (_fileno(stderr) < 0) (void)std::freopen("NUL", "w", stderr);
  }
#endif
  std::FILE* streams[2] = {stdout, stderr};
  for (int i = 0; i < 2; ++i) {
    Impl::Tee& t = impl->tees[i];
    int p[2];
    if (fd_pipe(p) != 0) continue;
    t.fd = fd_of(streams[i]);
    // Unmarked lines are I on both streams: the game and the original code print everyday facts on stderr
    // ("launched the madcat", draw counts, stock data reports), seen in every run. Only lines given W or E
    // (log.h) are problems, so a clean exit offers a report only for those.
    t.stamper = LineStamper('I');
    t.console = impl->log_only ? -1 : fd_dup(t.fd);  // -1: the log only
    t.read = p[0];
    fd_private(t.read);
    if (t.console >= 0) fd_private(t.console);
    fd_dup2(p[1], t.fd);
    fd_close(p[1]);
    Impl* self = impl.get();
    t.thread = std::thread([self, &t] { self->pass(t); });
  }
  std::setvbuf(stdout, nullptr, _IONBF, 0);
  std::setvbuf(stderr, nullptr, _IONBF, 0);
  impl_ = std::move(impl);
  path_ = log;
  g_open_log = impl_.get();
  log::g_drain = &run_log_drain;  // also turns on MW3_LOG's level markers
  if (start.append) std::printf("\n%s\n", log_start_note(start, name + ".old.log").c_str());
  if (restarted) std::printf("%s; the last log moved at try %d\n", restart_note.c_str(), start.moved ? start.tries : 0);
  return true;
}

void run_log_drain(unsigned max_ms) {
  // No fflush: a thread that crashed inside printf may hold the stream's lock, and stdout and stderr are
  // unbuffered while the log is open (open), so nothing waits in them.
  if (RunLog::Impl* open = g_open_log.load()) open->drain(max_ms);
}

RunLog::RunLog() = default;

RunLog::~RunLog() {
  if (!impl_) return;
  // Each call site's total of lines MW3_LOG held back, the last lines of the log (log.h).
  for (const auto& site : log::skipped_lines(true)) std::printf("mw3: log skipped at exit %s\n", site.c_str());
  log::g_drain = nullptr;
  g_open_log = nullptr;
  std::fflush(stdout);
  std::fflush(stderr);
  for (Impl::Tee& t : impl_->tees) {
    if (t.fd < 0) continue;
    // The console's handle back closes the pipe's last writer: the thread
    // reads what is left, then the end.
    // With no console the null device takes the pipe's place: the stream keeps a valid handle (reopening one
    // whose handle was closed ends the process with the CRT's invalid-parameter fast fail).
    if (t.console >= 0) {
      fd_dup2(t.console, t.fd);
    } else {
      const int null_device = fd_open_null();
      if (null_device >= 0) {
        fd_dup2(null_device, t.fd);
        fd_close(null_device);
      } else {
        fd_close(t.fd);
      }
    }
    if (t.thread.joinable()) t.thread.join();
    fd_close(t.read);
    if (t.console >= 0) fd_close(t.console);
  }
  std::fclose(impl_->file);
  if (impl_->problems) std::fclose(impl_->problems);
#if defined(_WIN32)
  // With no console what is printed after the run (main's restart lines, sdl_restart.cpp) still goes to the
  // log, unstamped, as a plain file: the restart then starts the new process with no standard handles.
  if (impl_->log_only && _wfreopen(wide(impl_->path).c_str(), L"a", stdout)) {
    _dup2(_fileno(stdout), 2);
    std::setvbuf(stdout, nullptr, _IONBF, 0);
    std::setvbuf(stderr, nullptr, _IONBF, 0);
  }
#endif
}

}  // namespace sdlfe
