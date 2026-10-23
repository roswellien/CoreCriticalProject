#include "../native-overrides/shadow_clip_reuse.hpp"

#include <array>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
using mw34::fixture_shadow::Bounds;
using mw34::fixture_shadow::Clip;
using mw34::fixture_shadow::Point;

// Preserve the original recording loop as an independent reference: each plane
// reconstructs and transforms all eight corners, including after all becomes
// false. The optimized helper must retain its strict comparison and sum order.
bool original_outside(const Clip& clip, const Bounds& bounds) {
    bool outside = false;
    for (unsigned plane = 0; plane < 6; ++plane) {
        bool all = true;
        for (unsigned corner = 0; corner < 8; ++corner) {
            std::array<float, 4> p{
                (corner & 1) ? bounds.high[0] : bounds.low[0],
                (corner & 2) ? bounds.high[1] : bounds.low[1],
                (corner & 4) ? bounds.high[2] : bounds.low[2], 1};
            std::array<float, 4> q{};
            for (unsigned r = 0; r < 4; ++r)
                for (unsigned c = 0; c < 4; ++c)
                    q[r] += clip[r * 4 + c] * p[c];
            const float d = plane == 0 ? q[0] + q[3]
                            : plane == 1 ? q[3] - q[0]
                            : plane == 2 ? q[1] + q[3]
                            : plane == 3 ? q[3] - q[1]
                            : plane == 4 ? q[2]
                                         : q[3] - q[2];
            all &= d < 0;
        }
        if (all) {
            outside = true;
            break;
        }
    }
    return outside;
}

struct Random {
    std::uint32_t state = 0x65a29031U;
    std::uint32_t next() {
        state ^= state << 13;
        state ^= state >> 17;
        state ^= state << 5;
        return state;
    }
    float range(float low, float high) {
        return low + (high - low) * float(next() >> 8) / 16777216.0f;
    }
};

struct Checks {
    std::uint64_t decisions{}, ordered_lists{}, accepted{}, rejected{};

    void compare(const Clip& clip, const std::vector<Bounds>& boxes) {
        std::vector<std::size_t> expected, actual;
        expected.reserve(boxes.size());
        actual.reserve(boxes.size());
        for (std::size_t i = 0; i < boxes.size(); ++i) {
            const bool before = original_outside(clip, boxes[i]);
            const bool after = mw34::shadow_clip_reuse::outside(clip, boxes[i]);
            ++decisions;
            if (before != after)
                throw std::runtime_error("Shadow clip decision differs at case " +
                                         std::to_string(decisions) + ", caster " +
                                         std::to_string(i));
            if (!before) {
                expected.push_back(i);
                ++accepted;
            } else {
                ++rejected;
            }
            if (!after)
                actual.push_back(i);
        }
        // IDs stay in the input/map traversal order, including duplicate boxes.
        if (expected != actual)
            throw std::runtime_error("Ordered shadow caster acceptance differs");
        ++ordered_lists;
    }
};
} // namespace

int main() {
    try {
        std::vector<Bounds> boxes;
        Random random;
        const std::array<float, 7> scales{0, 0.000001f, 0.1f, 1, 128, 100000, 1e25f};
        for (float scale : scales) {
            for (unsigned i = 0; i < 512; ++i) {
                Bounds box;
                for (unsigned axis = 0; axis < 3; ++axis) {
                    box.low[axis] = random.range(-2, 2) * scale;
                    box.high[axis] = box.low[axis] + random.range(0, 0.5f) * scale;
                }
                boxes.push_back(box);
            }
        }

        // Points, flat boxes, exact boundaries, neighboring floats, and signed
        // zero exercise the strict d < 0 rule rather than a tolerant cull.
        const std::array<float, 12> boundaries{
            -128, -1, -0.1f, -0.0f, 0.0f, 0.1f,
            std::nextafter(0.1f, 0.0f), std::nextafter(0.1f, 1.0f),
            1, std::nextafter(128.0f, 0.0f), 128, std::nextafter(128.0f, 256.0f)};
        for (float x : boundaries)
            for (float y : boundaries)
                for (float z : boundaries)
                    boxes.push_back(Bounds{{x, y, z}, {x, y, z}});
        boxes.push_back(Bounds{{-128, -128, 0.1f}, {128, 128, 128}});
        boxes.push_back(Bounds{{-1, 0, -1}, {1, 0, 1}});
        boxes.push_back(boxes.front()); // Duplicate caster IDs must remain ordered.

        const float inf = std::numeric_limits<float>::infinity();
        const float nan = std::numeric_limits<float>::quiet_NaN();
        const std::array<float, 6> unusual{inf, -inf, nan, 1e30f, -1e30f, -0.0f};
        for (float value : unusual)
            for (unsigned axis = 0; axis < 3; ++axis) {
                Bounds box{{-1, -1, -1}, {1, 1, 1}};
                box.low[axis] = value;
                boxes.push_back(box);
                box = Bounds{{-1, -1, -1}, {1, 1, 1}};
                box.high[axis] = value;
                boxes.push_back(box);
            }

        Checks checks;
        const std::array<Point, 4> eyes{
            Point{0, 0, 0}, Point{100000, -10000, 0.125f},
            Point{-100, 200, -300}, Point{-0.0f, 0.0f, -0.0f}};
        const std::array<std::array<float, 2>, 3> ranges{{
            {0.1f, 128}, {0.01f, 16}, {1, 4096}}};
        for (const auto& eye : eyes)
            for (const auto& planes : ranges)
                for (unsigned side = 0; side < 6; ++side)
                    checks.compare(mw34::fixture_shadow::face(
                                       eye, side, planes[0], planes[1]), boxes);

        // Arbitrary coefficients prevent accidentally relying on the current
        // cube faces' sparse matrices. Exceptional inputs preserve the original
        // comparison outcome; they are not claimed as valid scene geometry.
        for (unsigned i = 0; i < 24; ++i) {
            Clip clip{};
            for (auto& coefficient : clip)
                coefficient = random.range(-4, 4);
            checks.compare(clip, boxes);
        }
        checks.compare(Clip{}, boxes);
        for (float value : unusual)
            for (unsigned entry = 0; entry < 16; ++entry) {
                auto clip = mw34::fixture_shadow::face(Point{}, 4, 0.1f, 128);
                clip[entry] = value;
                checks.compare(clip, boxes);
            }
        if (!checks.accepted || !checks.rejected)
            throw std::runtime_error("Shadow clip fixture did not cover both outcomes");
        std::cout << "shadow clip reuse decisions=" << checks.decisions
                  << " ordered_lists=" << checks.ordered_lists
                  << " accepted=" << checks.accepted << " rejected=" << checks.rejected
                  << " failures=0\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
