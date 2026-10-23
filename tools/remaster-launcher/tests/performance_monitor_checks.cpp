#include "../native-overrides/performance_monitor.hpp"
#include <cassert>
#include <limits>

int main() {
    using namespace mw34::performance;
    Window w;
    assert(w.metrics().samples == 0);
    double now = 0;
    w.sample(now);
    for (int i = 0; i < 99; ++i) w.sample(now += .01);
    w.sample(now += .05);
    auto m = w.metrics();
    assert(m.samples == 100);
    assert(std::abs(m.average_fps - 100.0 / 1.04) < 1e-8);
    assert(std::abs(m.average_ms - 10.4) < 1e-8);
    assert(std::abs(m.low_fps - 20.0) < 1e-8);
    assert(std::abs(m.high_fps - 100.0) < 1e-8);
    w.sample(now); // No zero/negative/nonfinite intervals.
    w.sample(now - 1);
    w.sample(std::numeric_limits<double>::infinity());
    assert(w.metrics().samples == 100);
    w.sample(now += .02); // 101 samples: mean of the slowest two, not percentile reciprocal.
    assert(std::abs(w.metrics().low_fps - 2.0 / .07) < 1e-8);
    w.sample(now += 11);
    assert(w.metrics().samples == 0);
    w.sample(now += .02);
    assert(std::abs(w.metrics().average_fps - 50) < 1e-8);
    for (int i = 0; i < 1000; ++i) w.sample(now += .02);
    assert(w.metrics().samples >= 499 && w.metrics().samples <= 501);
    assert(std::abs(w.metrics().low_fps - 50) < 1e-8);
    w.reset();
    assert(w.metrics().samples == 0);
    w.sample(now += 50); // Loading before a new measurement epoch is excluded.
    w.sample(now += .01);
    assert(std::abs(w.metrics().average_fps - 100) < 1e-8);
    // Disabled overlay has no measurement or pixel work. Small targets stay bounded.
    Overlay overlay;
    overlay.on = false;
    std::uint16_t pixels[64];
    std::fill_n(pixels, 64, 0x1234);
    overlay.draw(pixels, 8, 8);
    assert(overlay.window.metrics().samples == 0 && overlay.box_w == 0);
    for (auto p : pixels) assert(p == 0x1234);
    overlay.on = true;
    overlay.draw(pixels + 1, 7, 8);
    assert(pixels[0] == 0x1234 && pixels[57] == 0x1234);
    assert(overlay.box_w == 7 && overlay.box_h == 8);
}
