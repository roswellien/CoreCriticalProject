// Project-authored host presentation statistics. No guest clock or state changes.
#pragma once
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <functional>
#include <vector>

namespace mw34::performance {
struct Metrics {
    double average_fps{}, low_fps{}, high_fps{}, average_ms{};
    std::size_t samples{};
};

// Ten seconds of presentation intervals. Ignore nonpositive clock samples.
// A suspension longer than the window starts a fresh window rather than
// presenting loading/minimization time as current gameplay performance.
class Window {
    struct Interval { double end, seconds; };
    std::deque<Interval> intervals;
    double previous{};
    bool started{};
public:
    void reset() { intervals.clear(); previous = 0; started = false; }
    void sample(double now) {
        if (!std::isfinite(now)) return;
        if (!started) { previous = now; started = true; return; }
        const double dt = now - previous;
        if (dt <= 0) return;
        previous = now;
        while (!intervals.empty() && now - intervals.front().end >= 10.0)
            intervals.pop_front();
        if (dt > 10.0) { intervals.clear(); return; }
        intervals.push_back({now, dt});
        // Bound storage even for an uncapped synthetic presenter.
        if (intervals.size() > 65536) intervals.pop_front();
    }
    Metrics metrics() const {
        if (intervals.empty()) return {};
        std::vector<double> times;
        times.reserve(intervals.size());
        double sum = 0;
        for (const auto &i : intervals) { sum += i.seconds; times.push_back(i.seconds); }
        std::sort(times.begin(), times.end(), std::greater<double>());
        const std::size_t count = (times.size() + 99) / 100;
        double slow = 0;
        for (std::size_t i = 0; i < count; ++i) slow += times[i];
        return {times.size() / sum, count / slow, 1.0 / times.back(),
                sum * 1000.0 / times.size(), times.size()};
    }
};

struct Overlay {
    bool on = [] { const char *e = std::getenv("MW34_PERF_OVERLAY"); return e && std::strcmp(e, "1") == 0; }();
    static constexpr unsigned buffer_height = 80;
    Window window;
    double shown = -1;
    char text[4][48]{};
    unsigned box_w{}, box_h{};
    void reset() {
        window.reset(); shown = -1;
        std::memset(text, 0, sizeof text);
        box_w = box_h = 0;
    }
        static const std::uint8_t *glyph(char c) {
            static const std::uint8_t g[][8] = {{'0', 0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E},
                                                {'1', 0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E},
                                                {'2', 0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F},
                                                {'3', 0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E},
                                                {'4', 0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02},
                                                {'5', 0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E},
                                                {'6', 0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E},
                                                {'7', 0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08},
                                                {'8', 0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E},
                                                {'9', 0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C},
                                                {'.', 0, 0, 0, 0, 0, 0x0C, 0x0C},
                                                {'F', 0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10},
                                                {'P', 0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10},
                                                {'S', 0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E},
                                                {'A', 0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11},
                                                {'V', 0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04},
                                                {'G', 0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F},
                                                {'M', 0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11},
                                                {'X', 0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11},
                                                {'L', 0x10,0x10,0x10,0x10,0x10,0x10,0x1F},
                                                {'O', 0x0E,0x11,0x11,0x11,0x11,0x11,0x0E},
                                                {'W', 0x11,0x11,0x11,0x15,0x15,0x15,0x0A},
                                                {'H', 0x11,0x11,0x11,0x1F,0x11,0x11,0x11},
                                                {'I', 0x0E,0x04,0x04,0x04,0x04,0x04,0x0E},
                                                {'R', 0x1E,0x11,0x11,0x1E,0x14,0x12,0x11},
                                                {'E', 0x1F,0x10,0x10,0x1E,0x10,0x10,0x1F},
                                                {'T', 0x1F,0x04,0x04,0x04,0x04,0x04,0x04},
                                                {'%', 0x19,0x19,0x02,0x04,0x08,0x13,0x13},
                                                {':', 0,0x0C,0x0C,0,0x0C,0x0C,0},
                                                {'-', 0,0,0,0x1F,0,0,0},
                                                {' ', 0, 0, 0, 0, 0, 0, 0}};
            for (const auto &e : g)
                if (e[0] == std::uint8_t(c))
                    return e + 1;
            return g[sizeof(g) / sizeof(g[0]) - 1] + 1;
        }

    void draw(std::uint16_t *px, unsigned w, unsigned h) {
        box_w = box_h = 0;
        if (!on || !px || !w || !h) return;
        const double now = std::chrono::duration<double>(std::chrono::steady_clock::now().time_since_epoch()).count();
        window.sample(now);
        if (shown < 0 || now - shown >= 0.25) {
            shown = now;
            const auto m = window.metrics();
            if (m.samples) {
                std::snprintf(text[0], sizeof text[0], "AVG FPS: %.1f", m.average_fps);
                std::snprintf(text[1], sizeof text[1], "1%% LOW FPS: %.1f", m.low_fps);
                std::snprintf(text[2], sizeof text[2], "HIGH FPS: %.1f", m.high_fps);
                std::snprintf(text[3], sizeof text[3], "AVG FRAME TIME: %.2f MS", m.average_ms);
            } else {
                std::snprintf(text[0], sizeof text[0], "AVG FPS: --");
                std::snprintf(text[1], sizeof text[1], "1%% LOW FPS: --");
                std::snprintf(text[2], sizeof text[2], "HIGH FPS: --");
                std::snprintf(text[3], sizeof text[3], "AVG FRAME TIME: -- MS");
            }
        }
        const unsigned sc = w >= 400 ? 2 : 1;
        std::size_t len = 0;
        for (const auto &line : text) len = std::max(len, std::strlen(line));
        box_w = std::min(unsigned((len * 6 + 4) * sc), w);
        box_h = std::min(40 * sc, h);
        for (unsigned y = 0; y < box_h; ++y)
            std::fill_n(px + std::size_t(y) * w, box_w, std::uint16_t(0));
        for (unsigned line = 0; line < 4; ++line)
            for (unsigned i = 0; text[line][i]; ++i) {
                const auto *g = glyph(text[line][i]);
                for (unsigned r = 0; r < 7; ++r)
                    for (unsigned c = 0; c < 5; ++c)
                        if (g[r] & (0x10 >> c))
                            for (unsigned dy = 0; dy < sc; ++dy)
                                for (unsigned dx = 0; dx < sc; ++dx) {
                                    const unsigned x = (2 + i * 6 + c) * sc + dx,
                                                   y = (2 + line * 10 + r) * sc + dy;
                                    if (x < box_w && y < box_h) px[std::size_t(y) * w + x] = 0xFFE0;
                                }
            }
    }
};
} // namespace mw34::performance
