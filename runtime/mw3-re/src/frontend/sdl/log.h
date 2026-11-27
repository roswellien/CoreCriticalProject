#pragma once
// Ours (#521): leveled log lines. Everything mw3 prints goes through RunLog
// (run_log.h), which stamps each line with seconds since launch and a level:
// I unless the line starts with a level marker, which MW3_LOG writes. Only W
// and E lines are problems (mw3-problems.log, the launcher's clean-exit report). MW3_LOG also counts repeats per call site: the first 10
// print, then the 16th, 32nd, 64th and every later power of two; each site's
// skipped total is printed after every health line and at exit.
#include <atomic>
#include <cstdarg>
#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>

namespace sdlfe::log {

// The two bytes that start a line with a chosen level: kMarker then 'I', 'W'
// or 'E'. RunLog takes them off before the console and the files.
constexpr char kMarker = '\x02';

enum class Level : char { info = 'I', warn = 'W', error = 'E' };

struct Site {
  const char* file;
  int line;
  std::atomic<uint64_t> calls{0};
  std::atomic<uint64_t> skipped{0};
  uint64_t skipped_reported = 0;  // read and written only by the report functions
  Site* next = nullptr;
};

// Every site that has printed once, newest first.
inline std::atomic<Site*> g_sites{nullptr};

// The first 10 calls print, then each power of two from 16.
constexpr bool prints(uint64_t call) { return call <= 10 || (call & (call - 1)) == 0; }

inline bool count(Site& site) {
  const uint64_t call = site.calls.fetch_add(1, std::memory_order_relaxed) + 1;
  if (call == 1) {
    Site* head = g_sites.load(std::memory_order_relaxed);
    do site.next = head;
    while (!g_sites.compare_exchange_weak(head, &site, std::memory_order_release, std::memory_order_relaxed));
  }
  if (prints(call)) return true;
  site.skipped.fetch_add(1, std::memory_order_relaxed);
  return false;
}

inline const char* base_name(const char* path) {
  const char* name = path;
  for (const char* p = path; *p; ++p)
    if (*p == '/' || *p == '\\') name = p + 1;
  return name;
}

// One whole line, marker first, in a single write so threads don't interleave.
inline void vprint(Level level, const char* fmt, va_list args) {
  char buf[2048];
  buf[0] = kMarker, buf[1] = static_cast<char>(level);
  int n = std::vsnprintf(buf + 2, sizeof buf - 3, fmt, args);
  if (n < 0) n = 0;
  size_t len = 2 + (static_cast<size_t>(n) < sizeof buf - 3 ? static_cast<size_t>(n) : sizeof buf - 4);
  if (buf[len - 1] != '\n') buf[len++] = '\n';
  std::FILE* out = level == Level::info ? stdout : stderr;
  std::fwrite(buf, 1, len, out);
  std::fflush(out);
}

#if defined(__GNUC__)
__attribute__((format(printf, 3, 4)))
#endif
inline void print(Site& site, Level level, const char* fmt, ...) {
  if (!count(site)) return;
  va_list args;
  va_start(args, fmt);
  vprint(level, fmt, args);
  va_end(args);
}

// A line with a chosen level and no repeat counting (one-off lines).
#if defined(__GNUC__)
__attribute__((format(printf, 2, 3)))
#endif
inline void line(Level level, const char* fmt, ...) {
  va_list args;
  va_start(args, fmt);
  vprint(level, fmt, args);
  va_end(args);
}

// "<file>:<line> <skipped since the last report>" for each site that skipped
// lines since the last report; `all` gives every site's total instead.
inline std::vector<std::string> skipped_lines(bool all) {
  std::vector<std::string> out;
  for (Site* s = g_sites.load(std::memory_order_acquire); s; s = s->next) {
    const uint64_t total = s->skipped.load(std::memory_order_relaxed);
    const uint64_t shown = all ? total : total - s->skipped_reported;
    s->skipped_reported = total;
    if (shown == 0) continue;
    out.push_back(std::string(base_name(s->file)) + ":" + std::to_string(s->line) + " " + std::to_string(shown));
  }
  return out;
}

inline uint64_t skipped_total() {
  uint64_t total = 0;
  for (Site* s = g_sites.load(std::memory_order_acquire); s; s = s->next) total += s->skipped.load(std::memory_order_relaxed);
  return total;
}

}  // namespace sdlfe::log

// MW3_LOG(W, "mw3: texture %s failed\n", name): level I, W or E.
#define MW3_LOG(level, ...)                                                              \
  do {                                                                                   \
    static ::sdlfe::log::Site mw3_log_site_{__FILE__, __LINE__};                         \
    ::sdlfe::log::print(mw3_log_site_, ::sdlfe::log::mw3_level_##level, __VA_ARGS__);    \
  } while (0)

namespace sdlfe::log {
constexpr Level mw3_level_I = Level::info, mw3_level_W = Level::warn, mw3_level_E = Level::error;
}
