// Host-only loading feedback: progress text, OS event pumping and per-phase timing.
// A checkpoint only calls the frontend's observer (which pumps window messages and
// draws the loading mark). No game callback may ever run from a checkpoint.
//
// Everything is thread_local: decoders also run on renderer worker threads, where
// no observer is installed, so their checkpoints are free no-ops.
#pragma once

#include <array>
#include <cfenv>
#include <chrono>
#include <cstdio>
#include <functional>
#include <string>

namespace platform::loading {
using Clock = std::chrono::steady_clock;

struct Progress {
  bool active = false;
  std::string text;
  int percent = -1;  // Unknown work is activity, never a fabricated percentage.
};
inline thread_local Progress progress;
inline thread_local std::function<void(const Progress&)> observer;
inline thread_local unsigned depth = 0;
inline thread_local bool notifying = false;
inline thread_local Clock::time_point next_update;
// The longest time a loading session went without the observer pumping messages.
// Windows marks a window "Not responding" after about 5 s without pumping.
inline thread_local Clock::time_point last_notified;
inline thread_local long long longest_unpumped_ms = 0;
// Static initialisation runs at process entry, so this is the origin of startup timings.
inline const Clock::time_point process_origin = Clock::now();
inline long long since_process_start_ms() {
  return std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - process_origin)
      .count();
}

// UI and host library calls must not leak rounding modes or FP flags into game code.
class HostFpScope {
 public:
  HostFpScope() {
    std::fegetenv(&environment_);
    std::feholdexcept(&discarded_);
  }
  ~HostFpScope() { std::fesetenv(&environment_); }

 private:
  std::fenv_t environment_{};
  std::fenv_t discarded_{};
};

// Called often from long loops. It is rate-limited to about 30 updates a second.
inline void checkpoint(bool force = false) noexcept {
  if (!observer || notifying || (!progress.active && !force)) return;
  const auto now = Clock::now();
  if (!force && now < next_update) return;
  next_update = now + std::chrono::milliseconds(33);
  if (progress.active) {
    const auto unpumped =
        std::chrono::duration_cast<std::chrono::milliseconds>(now - last_notified).count();
    if (unpumped > longest_unpumped_ms) longest_unpumped_ms = unpumped;
  }
  HostFpScope fp;
  notifying = true;
  try {
    observer(progress);
  } catch (...) {
    std::fprintf(stderr, "mw3: loading display failed; continuing load\n");
  }
  notifying = false;
  last_notified = Clock::now();
}

// New text or fraction. Shown at the next throttled checkpoint (at most every 33 ms), so a
// load that reports many lines a second does not redraw or pump for each one.
inline void report(const char* text, int percent = -1) {
  progress.text = text ? text : "Loading";
  progress.percent = percent < 0 ? -1 : percent > 100 ? 100 : percent;
  checkpoint();
}

// Keeps the current text; only the fraction changes.
inline void report_percent(int percent) {
  progress.percent = percent < 0 ? -1 : percent > 100 ? 100 : percent;
  checkpoint();
}

enum class Work { texture, normal, mesh, bwtex, restore, cache_read, cache_write, count };
struct Counter {
  unsigned long long calls = 0;
  unsigned long long bytes = 0;
  unsigned long long hits = 0;  // disk-cache hits, where the work has a cache
  long long microseconds = 0;
};
inline thread_local std::array<Counter, static_cast<unsigned>(Work::count)> counters;
inline constexpr const char* work_names[] = {"texture-rgba", "normal-decode", "prepared-mesh",
                                             "prepared-bwtex", "saved-game-restore",
                                             "cache-read", "cache-write"};

// Times one piece of work into the current thread's counters.
class Measure {
 public:
  explicit Measure(Work work, unsigned long long bytes = 0) : work_(work), bytes_(bytes) {
    checkpoint();
  }
  ~Measure() {
    auto& counter = counters[static_cast<unsigned>(work_)];
    ++counter.calls;
    counter.bytes += bytes_;
    counter.hits += hit;
    counter.microseconds +=
        std::chrono::duration_cast<std::chrono::microseconds>(Clock::now() - start_).count();
    checkpoint();
  }
  Measure(const Measure&) = delete;
  Measure& operator=(const Measure&) = delete;
  bool hit = false;

 private:
  Work work_;
  unsigned long long bytes_;
  Clock::time_point start_ = Clock::now();
};

// A user-visible load (startup, a mission). Nested sessions merge into the outer one.
// `label` is the text the loading display and the launcher show.
class Session {
 public:
  Session(const char* name, const char* label) : name_(name), outer_(depth++ == 0) {
    if (!outer_) return;
    counters = {};
    longest_unpumped_ms = 0;
    last_notified = Clock::now();
    progress.active = true;
    progress.text = label ? label : "Loading";
    progress.percent = -1;
    checkpoint(true);  // A session always shows at once.
    HostFpScope fp;
    std::printf("mw3: phase begin %s\n", name_);
  }
  ~Session() {
    --depth;
    if (!outer_) return;
    {
      HostFpScope fp;
      const auto elapsed =
          std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - start_).count();
      std::printf("mw3: phase end %s %lld ms (longest unpumped %lld ms)\n", name_,
                  static_cast<long long>(elapsed), longest_unpumped_ms);
      for (unsigned i = 0; i < counters.size(); ++i) {
        const auto& counter = counters[i];
        if (counter.calls)
          std::printf("mw3: work %s calls=%llu hits=%llu bytes=%llu ms=%lld\n", work_names[i],
                      counter.calls, counter.hits, counter.bytes, counter.microseconds / 1000);
      }
    }
    progress.active = false;
    checkpoint(true);
  }
  Session(const Session&) = delete;
  Session& operator=(const Session&) = delete;

 private:
  const char* name_;
  bool outer_;
  Clock::time_point start_ = Clock::now();
};

// A timed step inside a session, logged as "mw3: phase <name> <ms> ms".
class Phase {
 public:
  explicit Phase(const char* name) : name_(name) { checkpoint(); }
  ~Phase() {
    HostFpScope fp;
    const auto elapsed =
        std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - start_).count();
    std::printf("mw3: phase %s %lld ms\n", name_, static_cast<long long>(elapsed));
  }
  Phase(const Phase&) = delete;
  Phase& operator=(const Phase&) = delete;

 private:
  const char* name_;
  Clock::time_point start_ = Clock::now();
};
}  // namespace platform::loading
