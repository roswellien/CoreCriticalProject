#include "../native-overrides/fixture_light_masks.hpp"
#include "../../../runtime/graphics/fixture_shadow.hpp"
#include <array>
#include <cstdio>
#include <limits>

struct Light { std::array<float, 4> start{}; };
struct Lights { std::array<Light, 64> lights{}; };
unsigned checks{};
void require(bool value) {
    ++checks;
    if (!value)
        throw std::runtime_error("Fixture light sphere result changed");
}
template <class F> void rejects(F fn) {
    bool rejected = false;
    try { fn(); } catch (const std::runtime_error &) { rejected = true; }
    require(rejected);
}
void compare(const mw34::fixture_shadow::Bounds &bounds, const Lights &lights,
             unsigned first, unsigned count) {
    const auto mask = mw34::submission::fixture_light_mask(bounds, lights, first, count);
    for (unsigned i = 0; i < 64; ++i) {
        const auto &s = lights.lights[i].start;
        const bool expected = i >= first && i < count && bounds.overlaps({s[0], s[1], s[2]}, s[3]);
        for (unsigned face = 0; face < 6; ++face)
            require(bool(mask & (std::uint64_t(1) << i)) == expected);
    }
}
int main() {
    Lights lights;
    mw34::fixture_shadow::Bounds bounds;
    bounds.add({-1, -2, -3}); bounds.add({1, 2, 3});
    for (unsigned i = 0; i < 64; ++i)
        lights.lights[i].start = {float(int(i % 9) - 4), float(int(i % 7) - 3), float(i % 5), float(i % 4)};
    for (unsigned count = 0; count <= 64; ++count)
        for (unsigned first = 0; first <= count; ++first)
            compare(bounds, lights, first, count);
    const auto nan = (std::numeric_limits<float>::quiet_NaN)();
    const auto inf = (std::numeric_limits<float>::infinity)();
    for (float radius : {0.f, -1.f, 1.f, inf, nan}) {
        lights.lights[63].start = {1, 2, 3, radius}; compare(bounds, lights, 0, 64);
        lights.lights[63].start[0] = inf; compare(bounds, lights, 0, 64);
        lights.lights[63].start[0] = nan; compare(bounds, lights, 0, 64);
    }
    // Recompute after light motion, bound motion and a new scene's reordered list.
    for (unsigned frame = 0; frame < 128; ++frame) {
        lights.lights[frame % 64].start = {float(frame), -float(frame), 0, 3};
        bounds.low[0] = float(frame) - 2; bounds.high[0] = float(frame) + 2;
        compare(bounds, lights, frame % 32, 64);
    }
    rejects([&] { mw34::submission::fixture_light_mask(bounds, lights, 0, 65); });
    rejects([&] { mw34::submission::fixture_light_mask(bounds, lights, 4, 3); });
    std::printf("%u fixture light mask checks passed\n", checks);
}
