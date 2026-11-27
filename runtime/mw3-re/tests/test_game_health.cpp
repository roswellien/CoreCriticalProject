// Checks for the game's health lines (#521): the shared percentile rule, the
// frame window, event limits, line formats, driver-version decoding and the
// header lines the launcher reads (compared with the shared format sample).
#include "frontend/sdl/game_health.h"

#include <cstdio>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
using namespace sdlfe;

void require(bool condition, const std::string& message) {
  if (!condition) throw std::runtime_error(message);
}

void nearest_rank_rule() {
  // The arena benchmark's own case (test_arena_benchmark.cpp): intervals 500, 1400, 950...
  const std::vector<double> three{500, 950, 1400};
  require(nearest_rank(three, 50) == 950, "p50 of three is the second");
  require(nearest_rank(three, 95) == 1400 && nearest_rank(three, 99) == 1400, "p95 and p99 of three are the last");
  const std::vector<double> one{7};
  require(nearest_rank(one, 50) == 7 && nearest_rank(one, 100) == 7, "one value is every percentile");
  std::vector<double> hundred;
  for (int i = 1; i <= 100; ++i) hundred.push_back(i);
  require(nearest_rank(hundred, 95) == 95 && nearest_rank(hundred, 99) == 99, "nearest rank rounds up");
  require(nearest_rank(hundred, 100) == 100, "p100 is the max");
  std::vector<double> two_hundred;
  for (int i = 1; i <= 200; ++i) two_hundred.push_back(i);
  require(nearest_rank(two_hundred, 99) == 198, "p99 of 200 is the 198th");
}

void frame_window() {
  FrameWindow window(8);
  for (double ms : {10.0, 20.0, 150.0, 30.0}) window.add(ms);
  const auto s = window.take_summary();
  require(s.frames == 4 && s.hitches == 1, "hitches only over 100 ms");
  require(s.p50 == 20 && s.max == 150, "summary figures");
  require(window.take_summary().frames == 0, "a summary empties the window");
  FrameWindow small(2);
  for (double ms : {1.0, 2.0, 3.0}) small.add(ms);
  require(small.take_summary().frames == 2, "the ring keeps its capacity");
}

void limiter() {
  EventLimiter l;
  require(l.allow(HealthEvent::video_memory, 0), "first event prints");
  require(!l.allow(HealthEvent::video_memory, 9.9), "one per 10 s");
  require(l.allow(HealthEvent::alloc_failed, 5), "kinds don't block each other");
  require(l.allow(HealthEvent::video_memory, 10), "again after 10 s");
}

void hitch_quiet_spell() {
  GameHealth h;
  double now = 0;
  h.frame(now, true, true);
  unsigned events = 0, counted = 0;
  // A 150 ms hitch every 10 s for 5 minutes, 10 ms frames between.
  while (now < 300) {
    for (int i = 0; i < 1000; ++i) {
      now += 0.01;
      const auto r = h.frame(now, true, true);
      events += r.hitch_event;
      if (r.line_due) counted += h.take_summary().hitches;
    }
    now += 0.15;
    const auto r = h.frame(now, true, true);
    events += r.hitch_event;
    if (r.line_due) counted += h.take_summary().hitches;
  }
  counted += h.take_summary().hitches;
  require(events == 1, "stuttering prints one hitch event, got " + std::to_string(events));
  require(counted >= 29, "every hitch is counted, got " + std::to_string(counted));
  h.frame(now += 0.01, true, false);  // paused through a quiet minute: no frame, no hitch
  now += 61;
  for (int i = 0; i < 100; ++i) h.frame(now += 0.01, true, true);
  require(h.frame(now += 0.2, true, true).hitch_event, "a hitch after a quiet spell prints again");
}

void pause_and_mission_start() {
  GameHealth h;
  h.frame(0, true, true);
  h.frame(0.01, true, true);
  h.frame(0.02, true, false);  // pause: uncounted presents
  h.frame(30, true, false);
  const auto resumed = h.frame(30.01, true, true);
  require(!resumed.hitch_event && resumed.frame_ms == 0, "resume starts a new delta");
  h.frame(30.02, true, true);
  auto s = h.take_summary();
  require(s.hitches == 0 && s.max < 20, "a pause is not a frame");
  h.frame(31, false, false);  // back to the menus, then a new mission
  h.frame(32, true, true);
  h.frame(32.016, true, true);
  require(h.take_summary().frames == 1, "a mission start restarts the window");
  GameHealth timed;
  timed.frame(0, true, true);
  require(!timed.frame(59.9, true, true).line_due && timed.frame(60, true, true).line_due, "a line every 60 s");
}

void video_memory_edge() {
  GameHealth h;
  HealthSnapshot s;
  s.heap_count = 1;
  s.heaps[0] = {0, 2000, 0, 1000, true, true};
  auto at = [&](uint64_t used, double now) {
    s.heaps[0].used_bytes = used;
    return h.video_memory_crossing(s, now, 0);
  };
  require(at(500, 0) == -1, "below 90% is quiet");
  require(at(950, 1) == 0, "crossing 90% fires");
  require(at(850, 20) == -1 && at(950, 40) == -1, "no re-fire above 80%");
  require(at(700, 60) == -1 && at(950, 80) == 0, "re-arms below 80%");
  require(h.video_memory_crossing(s, 100, 100) == -1, "already fired, with the test budget too");
  // Two heaps crossing together: the second reports on a later check, not never.
  GameHealth two;
  HealthSnapshot both;
  both.heap_count = 2;
  both.heaps[0] = {0, 2000, 950, 1000, true, true};
  both.heaps[1] = {1, 2000, 950, 1000, true, true};
  require(two.video_memory_crossing(both, 0, 0) == 0, "first heap reports");
  require(two.video_memory_crossing(both, 5, 0) == -1, "limiter holds the second back");
  require(two.video_memory_crossing(both, 10, 0) == 1, "second heap reports once the limiter allows");
}

// The main loop's reporter, with a fake clock and renderer: the display header
// once, one stall 30 s into the mission, the memory check at most once a
// second, a line every 60 s, and one flush per printed batch.
void reporter() {
  double clock = 0;
  bool in_mission = false, shown = false;
  int headers = 0, stalls = 0, renderer_reads = 0, flushes = 0;
  std::vector<std::string> lines;
  HealthHooks hooks;
  hooks.now = [&] { return clock; };
  hooks.in_mission = [&] { return in_mission; };
  hooks.window_ready = [&] { return shown; };
  hooks.print_display_header = [&] { ++headers; };
  hooks.renderer = [&](HealthSnapshot& s) {
    ++renderer_reads;
    s.heap_count = 1;
    s.heaps[0] = {0, 2000, 950, 1000, true, true};
    return true;
  };
  hooks.ram_mib = [] { return uint64_t(512); };
  hooks.stall = [&](int ms) {
    ++stalls;
    clock += ms / 1000.0;
  };
  hooks.print = [&](const std::string& line) { lines.push_back(line); };
  hooks.flush = [&] { ++flushes; };
  HealthReporter r(std::move(hooks), 250);
  r.frame(false);  // hidden window, menus: nothing
  require(headers == 0 && lines.empty(), "nothing before the window is ready");
  shown = true;
  r.frame(false);
  r.frame(false);
  require(headers == 1, "the display header prints once");
  in_mission = true;
  for (int i = 0; i < 6100; ++i) {  // 61 s of 10 ms frames
    clock += 0.01;
    r.frame(true);
  }
  require(stalls == 1, "one stall 30 s into the mission");
  require(renderer_reads >= 60 && renderer_reads <= 63, "memory checked about once a second, got " +
                                                             std::to_string(renderer_reads));
  std::size_t hitch = 0, memory = 0, health = 0;
  for (const auto& line : lines) {
    hitch += line.rfind("mw3: health event hitch", 0) == 0;
    memory += line.rfind("mw3: health event video_memory", 0) == 0;
    health += line.rfind("mw3: health t=", 0) == 0;
  }
  require(hitch == 1 && memory == 1 && health == 1, "one hitch, one memory event and one line in 61 s");
  require(flushes == 3, "one flush per printed batch, got " + std::to_string(flushes));
}

void formats() {
  FrameSummary f{3600, 6.94, 8.5, 12.25, 140, 2};
  HealthSnapshot s;
  s.heap_count = 2;
  s.heaps[0] = {0, 12884901888ull, 3221225472ull, 11811160064ull, true, true};
  s.heaps[1] = {1, 33285996544ull, 104857600ull, 0, false, false};
  s.skins = 4, s.page_loads = 12, s.worker_waits = 3, s.mem_recoveries = 1, s.models_skipped = 0,
  s.textures_swapped = 2, s.preload_stops = 0;
  require(format_health_line(61.4, f, &s, 2048) ==
              "mw3: health t=61 frames=3600 p50=6.94 p95=8.50 p99=12.25 max=140.00 hitches=2 heap0=3072/11264 "
              "heap1=100/n/a ram_mib=2048 skins=4 page_loads=12 worker_waits=3 mem_recoveries=1 models_skipped=0 "
              "textures_swapped=2 preload_stops=0",
          "health line: " + format_health_line(61.4, f, &s, 2048));
  require(format_health_line(5, f, nullptr, 9) ==
              "mw3: health t=5 frames=3600 p50=6.94 p95=8.50 p99=12.25 max=140.00 hitches=2 ram_mib=9",
          "health line without a renderer");
  require(format_hitch_event(250.4, 45) == "mw3: health event hitch ms=250 t=45", "hitch event");
  require(format_video_memory_event(0, 943718400ull, 1048576000ull, 12) ==
              "mw3: health event video_memory heap0=900/1000 MiB pct=90 t=12",
          "video memory event");
  require(format_alloc_failed_event("texture base level", 4194304, 70) ==
              "mw3: health event alloc_failed kind=texture base level bytes=4194304 t=70",
          "alloc event");
}

void driver_versions() {
  const auto nvidia = vulkan_driver_version_text(0x10DE, 0x8E8A4000u);
  require(nvidia == "570.41.0.0 (0x8E8A4000)", "NVIDIA decode: " + nvidia);
  const auto intel = vulkan_driver_version_text(0x8086, (101u << 14) | 6559u);
  require(intel == "101.6559 (0x0019599F)", "Intel decode: " + intel);
  const uint32_t amd_raw = (2u << 22) | (0u << 12) | 299u;
  const auto amd = vulkan_driver_version_text(0x1002, amd_raw);
  require(amd == "2.0.299 (0x0080012B)", "standard decode: " + amd);
  for (const auto& text : {nvidia, intel, amd, vulkan_driver_version_text(0x10DE, 0xFFFFFFFFu)})
    require(text.size() <= 80, "driver text fits the launcher's 80 characters");
}

void header_matches_shared_sample() {
  std::vector<std::string> lines = renderer_header_lines(
      "NVIDIA GeForce RTX 5070", (1u << 22) | (4u << 12) | 312u, 0x10DE, 0x8E8A4000u,
      {{0, 12884901888ull, 0, 11811160064ull, true, true},
       {1, 33285996544ull, 0, 16642998272ull, false, true},
       {2, 268435456ull, 0, 0, true, false}});  // no driver figures: left out
  for (auto& line : display_header_lines(2560, 1080, "borderless", 144, false)) lines.push_back(line);
  std::ifstream sample(MW3_HEADER_SAMPLE);
  require(bool(sample), std::string("can't open ") + MW3_HEADER_SAMPLE);
  std::vector<std::string> expected;
  for (std::string line; std::getline(sample, line);)
    if (!line.empty()) expected.push_back(line.back() == '\r' ? line.substr(0, line.size() - 1) : line);
  require(lines.size() == expected.size(), "header line count matches the shared sample");
  for (std::size_t i = 0; i < lines.size(); ++i)
    require(lines[i] == expected[i], "header line " + std::to_string(i) + ": " + lines[i] + " != " + expected[i]);
}

}  // namespace

int main() {
  try {
    nearest_rank_rule();
    frame_window();
    limiter();
    hitch_quiet_spell();
    pause_and_mission_start();
    video_memory_edge();
    reporter();
    formats();
    driver_versions();
    header_matches_shared_sample();
    std::puts("Game health checks passed");
    return 0;
  } catch (const std::exception& error) {
    std::fprintf(stderr, "%s\n", error.what());
    return 1;
  }
}
