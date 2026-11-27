// The game's health lines for playtest reports (#521): a summary every minute
// of play, events printed at once, and the setup header lines the launcher reads.
//
// Pure logic only (no SDL or Vulkan includes), so CTest checks it without a GPU
// and the same formatting is used by the game and by the shared format sample
// (tests/fixtures/game_header_lines.txt) the launcher's checks read too.
//
// Every time passed in is wall seconds since process start (process_seconds()),
// so lines printed by the main thread and the render worker sort together.
#pragma once

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <functional>
#include <limits>
#include <string>
#include <utility>
#include <vector>

namespace sdlfe {

// Wall seconds since the first call; main calls it once at startup to fix the origin.
inline double process_seconds() {
  static const auto origin = std::chrono::steady_clock::now();
  return std::chrono::duration<double>(std::chrono::steady_clock::now() - origin).count();
}

// The one percentile rule (nearest rank, rounded up) the health line, the
// --frame-times summary and the arena benchmark all use, so one run's figures
// agree wherever they're printed. `sorted` must be non-empty and ascending.
template <class Sorted>
auto nearest_rank(const Sorted& sorted, std::size_t percent) {
  const std::size_t rank = (sorted.size() * percent + 99) / 100;
  return sorted[rank == 0 ? 0 : rank - 1];
}

constexpr double kHitchMs = 100.0;
constexpr double kHealthLineSeconds = 60.0;

struct FrameSummary {
  std::size_t frames = 0;
  double p50 = 0, p95 = 0, p99 = 0, max = 0;
  unsigned hitches = 0;
};

// A fixed ring of frame times. Nothing is allocated after construction: the
// sort copy is reserved up front too, since it runs once a minute in play.
class FrameWindow {
 public:
  // 60 s at 1,000 fps: 240 KB each for the ring and the sort copy.
  explicit FrameWindow(std::size_t capacity = 60000) : ring_(capacity), sorted_(capacity) {}

  void add(double ms) {
    ring_[head_] = static_cast<float>(ms);
    head_ = (head_ + 1) % ring_.size();
    count_ = std::min(count_ + 1, ring_.size());
    if (ms > kHitchMs) ++hitches_;
  }

  // The figures since the last summary, then an empty window.
  FrameSummary take_summary() {
    FrameSummary s;
    s.frames = count_;
    s.hitches = hitches_;
    if (count_) {
      std::copy_n(ring_.begin(), count_, sorted_.begin());
      std::sort(sorted_.begin(), sorted_.begin() + std::ptrdiff_t(count_));
      const Slice slice{sorted_.data(), count_};
      s.p50 = nearest_rank(slice, 50);
      s.p95 = nearest_rank(slice, 95);
      s.p99 = nearest_rank(slice, 99);
      s.max = sorted_[count_ - 1];
    }
    clear();
    return s;
  }

  void clear() { head_ = count_ = 0, hitches_ = 0; }

 private:
  struct Slice {
    const float* data;
    std::size_t n;
    std::size_t size() const { return n; }
    float operator[](std::size_t i) const { return data[i]; }
  };
  std::vector<float> ring_, sorted_;
  std::size_t head_ = 0, count_ = 0;
  unsigned hitches_ = 0;
};

enum class HealthEvent { hitch, video_memory, alloc_failed, count };

// Keeps events from flooding the log. Each kind has its own slot, so a kind
// checked on the render worker (alloc_failed) never blocks one checked on the
// main thread. Hitches use a quiet-spell rule instead of a plain interval: one
// prints only after 60 s with no hitch at all, so a stuttering game can't crowd
// the minute summaries out of the launcher's last-20-lines cut; the summary's
// hitches= still counts every one.
class EventLimiter {
 public:
  bool allow(HealthEvent kind, double now) {
    auto& last = last_[std::size_t(kind)];
    if (kind == HealthEvent::hitch) {
      const double previous = last.exchange(now);
      return now - previous >= kHitchQuietSeconds;
    }
    double previous = last.load();
    while (now - previous >= kIntervalSeconds)
      if (last.compare_exchange_weak(previous, now)) return true;
    return false;
  }

 private:
  static constexpr double kIntervalSeconds = 10.0;
  static constexpr double kHitchQuietSeconds = 60.0;
  std::array<std::atomic<double>, std::size_t(HealthEvent::count)> last_{
      {-1e18, -1e18, -1e18}};
};

constexpr std::size_t kMaxHealthHeaps = 16;

// One video memory heap, as the renderer reports it for the health line, the
// setup header and the memory table. used/budget are the driver's figures when
// driver_figures is set (VK_EXT_memory_budget); otherwise used is the game's
// own tracked allocations and budget is 0, since a heap's size isn't a budget.
struct HeapFigures {
  unsigned index = 0;
  uint64_t size_bytes = 0, used_bytes = 0, budget_bytes = 0;
  bool device_local = false, driver_figures = false;
};

// What the renderer reports for the health line (FrameRenderer::health).
struct HealthSnapshot {
  std::array<HeapFigures, kMaxHealthHeaps> heaps{};
  std::size_t heap_count = 0;
  uint64_t skins = 0, page_loads = 0, worker_waits = 0;
  uint64_t mem_recoveries = 0, models_skipped = 0, textures_swapped = 0, preload_stops = 0;
};

// Once-per-session state the Vulkan renderer keeps across its own rebuilds:
// FrameRenderer makes a new vk::Renderer at every mission start, so these live
// in one object FrameRenderer owns and hands to each renderer it builds.
struct HealthSession {
  std::atomic<bool> renderer_header_printed{false};
  std::atomic<bool> memory_table_printed{false};
  std::atomic<unsigned> memory_table_log_count{0};
  EventLimiter limiter;
};

constexpr double kVideoMemoryFirePercent = 90.0;
constexpr double kVideoMemoryRearmPercent = 80.0;

struct FrameResult {
  bool hitch_event = false;  // print a hitch event for this frame
  double frame_ms = 0;
  bool line_due = false;  // print the minute summary now
};

// The main thread's side: counts frames while a mission is on screen, decides
// when the minute line and the events print. Times come from the caller, so a
// check can drive it with fake ones.
class GameHealth {
 public:
  // `counted`: a mission frame was drawn. Every other present (pause screen,
  // menus, loading) clears the previous time, so the first frame after a pause
  // or alt-tab starts a new delta instead of recording the whole pause.
  FrameResult frame(double now, bool in_mission, bool counted) {
    FrameResult result;
    if (in_mission && !was_in_mission_) {  // a mission starts: a fresh window
      window_.clear();
      next_line_at_ = now + kHealthLineSeconds;
      mission_started_at_ = now;
    }
    was_in_mission_ = in_mission;
    if (!in_mission || !counted) {
      previous_ = -1;
      return result;
    }
    if (previous_ >= 0) {
      result.frame_ms = (now - previous_) * 1000.0;
      window_.add(result.frame_ms);
      result.hitch_event = result.frame_ms > kHitchMs && limiter_.allow(HealthEvent::hitch, now);
    }
    previous_ = now;
    if (now >= next_line_at_) {
      result.line_due = true;
      next_line_at_ = now + kHealthLineSeconds;
    }
    return result;
  }

  FrameSummary take_summary() { return window_.take_summary(); }
  // When the current (or last) mission started, or -1 before any.
  double mission_started_at() const { return mission_started_at_; }

  // Edge-triggered per heap: fires on crossing 90% of budget and re-arms only
  // below 80%, so a card sitting near its budget logs once, not every 10 s.
  // Returns the heap to report, or -1.
  int video_memory_crossing(const HealthSnapshot& snapshot, double now, uint64_t test_budget_bytes) {
    int fired = -1;
    for (std::size_t i = 0; i < snapshot.heap_count && i < kMaxHealthHeaps; ++i) {
      const auto& heap = snapshot.heaps[i];
      const uint64_t budget = test_budget_bytes ? test_budget_bytes : heap.budget_bytes;
      if (!heap.device_local || !budget || (!heap.driver_figures && !test_budget_bytes)) continue;
      const double percent = 100.0 * double(heap.used_bytes) / double(budget);
      if (percent < kVideoMemoryRearmPercent) armed_[i] = true;
      // Disarmed only when reported, so a heap that crossed while another
      // was reported (or the limiter held it back) reports on a later check.
      if (percent >= kVideoMemoryFirePercent && armed_[i] && fired < 0 &&
          limiter_.allow(HealthEvent::video_memory, now)) {
        armed_[i] = false;
        fired = int(i);
      }
    }
    return fired;
  }

  // The display header block prints once per run, from the first frame after
  // the window is shown.
  bool take_display_header() { return !display_header_printed_.exchange(true); }

 private:
  FrameWindow window_;
  EventLimiter limiter_;
  double previous_ = -1, next_line_at_ = 0, mission_started_at_ = -1;
  bool was_in_mission_ = false;
  std::array<bool, kMaxHealthHeaps> armed_ = [] {
    std::array<bool, kMaxHealthHeaps> a{};
    a.fill(true);
    return a;
  }();
  std::atomic<bool> display_header_printed_{false};
};

constexpr double kMiB = 1024.0 * 1024.0;

inline uint64_t to_mib(uint64_t bytes) { return uint64_t(double(bytes) / kMiB + 0.5); }

// Appends to `out` like snprintf, never past its end.
template <class... Args>
void append(std::string& out, const char* format, Args... args) {
  char buffer[256];
  const int n = std::snprintf(buffer, sizeof buffer, format, args...);
  if (n > 0) out.append(buffer, std::min<std::size_t>(std::size_t(n), sizeof buffer - 1));
}

// mw3: health t=<s> frames=<n> p50=<ms> p95=<ms> p99=<ms> max=<ms> hitches=<n>
//   heap<i>=<used MiB>/<budget MiB|n/a> ... ram_mib=<n> [renderer counters]
// The renderer fields are left out when the backend has no health() (sdl).
inline std::string format_health_line(double t, const FrameSummary& s, const HealthSnapshot* snapshot,
                                      uint64_t ram_mib) {
  std::string line;
  append(line, "mw3: health t=%.0f frames=%zu p50=%.2f p95=%.2f p99=%.2f max=%.2f hitches=%u", t, s.frames,
         s.p50, s.p95, s.p99, s.max, s.hitches);
  if (snapshot)
    for (std::size_t i = 0; i < snapshot->heap_count && i < kMaxHealthHeaps; ++i) {
      const auto& heap = snapshot->heaps[i];
      if (heap.driver_figures)
        append(line, " heap%zu=%llu/%llu", i, (unsigned long long)to_mib(heap.used_bytes),
               (unsigned long long)to_mib(heap.budget_bytes));
      else
        append(line, " heap%zu=%llu/n/a", i, (unsigned long long)to_mib(heap.used_bytes));
    }
  append(line, " ram_mib=%llu", (unsigned long long)ram_mib);
  if (snapshot)
    append(line,
           " skins=%llu page_loads=%llu worker_waits=%llu mem_recoveries=%llu models_skipped=%llu "
           "textures_swapped=%llu preload_stops=%llu",
           (unsigned long long)snapshot->skins, (unsigned long long)snapshot->page_loads,
           (unsigned long long)snapshot->worker_waits, (unsigned long long)snapshot->mem_recoveries,
           (unsigned long long)snapshot->models_skipped, (unsigned long long)snapshot->textures_swapped,
           (unsigned long long)snapshot->preload_stops);
  return line;
}

inline std::string format_hitch_event(double ms, double t) {
  std::string line;
  append(line, "mw3: health event hitch ms=%.0f t=%.0f", ms, t);
  return line;
}

inline std::string format_video_memory_event(std::size_t heap, uint64_t used_bytes, uint64_t budget_bytes,
                                             double t) {
  std::string line;
  const unsigned percent = budget_bytes ? unsigned(100.0 * double(used_bytes) / double(budget_bytes)) : 0;
  append(line, "mw3: health event video_memory heap%zu=%llu/%llu MiB pct=%u t=%.0f", heap,
         (unsigned long long)to_mib(used_bytes), (unsigned long long)to_mib(budget_bytes), percent, t);
  return line;
}

// kind: "model" or "texture base level", as log_video_memory_full names them.
inline std::string format_alloc_failed_event(const char* kind, uint64_t bytes, double t) {
  std::string line;
  append(line, "mw3: health event alloc_failed kind=%s bytes=%llu t=%.0f", kind, (unsigned long long)bytes, t);
  return line;
}

// --- Setup header lines (ReportHeader.cs reads these; keep the two in step
// through tests/fixtures/game_header_lines.txt). ---

// A Vulkan version packed as VK_MAKE_API_VERSION: variant 3 bits, major 7,
// minor 10, patch 12.
inline std::string vulkan_api_version_text(uint32_t raw) {
  std::string text;
  append(text, "%u.%u.%u", (raw >> 22) & 0x7Fu, (raw >> 12) & 0x3FFu, raw & 0xFFFu);
  return text;
}

// The driver version, decoded the vendor's way, with the raw value in hex so
// a report can be checked against the vendor's own numbering.
inline std::string vulkan_driver_version_text(uint32_t vendor_id, uint32_t raw) {
  std::string text;
  if (vendor_id == 0x10DE)  // NVIDIA packs 10.8.8.6 bits
    append(text, "%u.%u.%u.%u", (raw >> 22) & 0x3FFu, (raw >> 14) & 0xFFu, (raw >> 6) & 0xFFu, raw & 0x3Fu);
  else if (vendor_id == 0x8086)  // Intel on Windows: major.minor in 18.14 bits
    append(text, "%u.%u", raw >> 14, raw & 0x3FFFu);
  else
    text = vulkan_api_version_text(raw);
  append(text, " (0x%08X)", raw);
  return text;
}

// The renderer's block: device, API and driver versions, and one line per heap
// with driver budget figures (a heap's size isn't a budget, so heaps without
// them are left out).
inline std::vector<std::string> renderer_header_lines(const std::string& device_name, uint32_t api_version,
                                                      uint32_t vendor_id, uint32_t driver_version,
                                                      const std::vector<HeapFigures>& heaps) {
  std::vector<std::string> lines;
  lines.push_back("mw3: header vulkan_device=" + device_name);
  lines.push_back("mw3: header vulkan_api_version=" + vulkan_api_version_text(api_version));
  lines.push_back("mw3: header vulkan_driver_version=" + vulkan_driver_version_text(vendor_id, driver_version));
  for (const auto& heap : heaps) {
    if (!heap.driver_figures) continue;
    std::string line;
    append(line, "mw3: header heap index=%u size_bytes=%llu budget_bytes=%llu device_local=%d", heap.index,
           (unsigned long long)heap.size_bytes, (unsigned long long)heap.budget_bytes, heap.device_local ? 1 : 0);
    lines.push_back(line);
  }
  return lines;
}

// The display block. window_mode is windowed, borderless or hidden (the game
// has no exclusive fullscreen to report).
inline std::vector<std::string> display_header_lines(int width, int height, const char* window_mode,
                                                     int refresh_hz, bool hdr) {
  std::vector<std::string> lines(4);
  append(lines[0], "mw3: header resolution=%dx%d", width, height);
  append(lines[1], "mw3: header window_mode=%s", window_mode);
  append(lines[2], "mw3: header refresh_hz=%d", refresh_hz);
  append(lines[3], "mw3: header hdr=%d", hdr ? 1 : 0);
  return lines;
}

inline void print_lines(std::FILE* out, const std::vector<std::string>& lines) {
  for (const auto& line : lines) std::fprintf(out, "%s\n", line.c_str());
  std::fflush(out);
}

// The main loop's side of the health lines, called once per present. Every
// outside thing it needs comes in through these hooks, so a check can drive
// it with a fake clock and fake renderer figures.
struct HealthHooks {
  std::function<double()> now;                     // process_seconds() in the game
  std::function<bool()> in_mission;                // a mission is on screen
  std::function<bool()> window_ready;              // shown, or a hidden run
  std::function<void()> print_display_header;      // once, when window_ready
  std::function<bool(HealthSnapshot&)> renderer;   // FrameRenderer::health
  std::function<uint64_t()> ram_mib;               // process RAM, read only for a line
  std::function<void(int)> stall;                  // test switch: SDL_Delay
  std::function<void(const std::string&)> print;  // one line on stdout
  std::function<void()> flush;
};

class HealthReporter {
 public:
  // test_stall_ms: MW3_TEST_STALL_MS, one stall 30 s into the first mission (0 is off).
  HealthReporter(HealthHooks hooks, int test_stall_ms) : hooks_(std::move(hooks)), stall_ms_(test_stall_ms) {}

  void frame(bool drew_scene) {
    if (hooks_.window_ready() && health_.take_display_header()) hooks_.print_display_header();
    const bool in_mission = hooks_.in_mission();
    double now = hooks_.now();
    const double started = health_.mission_started_at();
    if (stall_ms_ && !stalled_ && in_mission && drew_scene && started >= 0 && now - started >= 30) {
      stalled_ = true;
      hooks_.stall(stall_ms_);
      now = hooks_.now();
    }
    const auto result = health_.frame(now, in_mission, drew_scene);
    if (result.hitch_event) hooks_.print(format_hitch_event(result.frame_ms, now));
    // Video memory is checked once a second of play, from the renderer's copy.
    const bool memory_check_due = in_mission && drew_scene && now >= next_memory_check_at_;
    HealthSnapshot snapshot;
    const bool have_snapshot = (memory_check_due || result.line_due) && hooks_.renderer(snapshot);
    bool printed = result.hitch_event;
    if (memory_check_due) {
      next_memory_check_at_ = now + 1;
      const int heap = have_snapshot ? health_.video_memory_crossing(snapshot, now, 0) : -1;
      if (heap >= 0) {
        const auto& figures = snapshot.heaps[std::size_t(heap)];
        hooks_.print(format_video_memory_event(std::size_t(heap), figures.used_bytes, figures.budget_bytes, now));
        printed = true;
      }
    }
    if (result.line_due) {
      hooks_.print(format_health_line(now, health_.take_summary(), have_snapshot ? &snapshot : nullptr,
                                      hooks_.ram_mib()));
      printed = true;
    }
    if (printed) hooks_.flush();
  }

 private:
  HealthHooks hooks_;
  GameHealth health_;
  int stall_ms_ = 0;
  bool stalled_ = false;
  double next_memory_check_at_ = 0;
};

}  // namespace sdlfe
