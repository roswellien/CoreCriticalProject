#pragma once

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <limits>
#include <stdexcept>
#include <vector>

namespace mw34::orion_guard {

using PoseKey = std::array<float, 24>;

struct Sample {
    PoseKey key{};
    std::array<float, 2> weights{};
};

struct Fit {
    std::array<std::array<float, 3>, 2> shifts{};
    std::vector<Sample> samples;
};

inline std::array<float, 2> weights(const Fit& fit, const PoseKey& key) {
    for (float feature : key) {
        if (!std::isfinite(feature)) {
            throw std::invalid_argument("Orion guard fit: nonfinite live pose");
        }
    }

    struct Neighbor {
        float distance{std::numeric_limits<float>::infinity()};
        const Sample* sample{};
    };
    std::array<Neighbor, 4> nearest{};
    for (const auto& sample : fit.samples) {
        float distance = 0.0f;
        for (std::size_t axis = 0; axis < key.size(); ++axis) {
            const float delta = key[axis] - sample.key[axis];
            distance += delta * delta;
        }
        for (std::size_t slot = 0; slot < nearest.size(); ++slot) {
            if (distance < nearest[slot].distance) {
                std::move_backward(nearest.begin() + slot, nearest.end() - 1, nearest.end());
                nearest[slot] = {distance, &sample};
                break;
            }
        }
    }

    std::array<float, 2> result{};
    if (nearest.front().distance > 0.20f) {
        return result;
    }
    // Use the largest nearby clearance requirement. Leave zero-offset
    // standing and walking samples in their approved position.
    for (const auto& neighbor : nearest) {
        if (!neighbor.sample) {
            continue;
        }
        for (std::size_t side = 0; side < result.size(); ++side) {
            result[side] = std::max(result[side], neighbor.sample->weights[side]);
        }
    }
    for (float& value : result) {
        if (value > 0.0f) {
            value = std::min(value + 0.025f, 1.0f);
        }
    }
    return result;
}

} // namespace mw34::orion_guard
