#pragma once

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
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

template<class Reader>
Fit read(Reader& bytes) {
    std::uint32_t count{};
    bytes(&count, sizeof(count));
    if (count < 4 || count > 4096) {
        throw std::runtime_error("Orion guard fit: invalid sample count");
    }

    Fit fit;
    for (auto& shift : fit.shifts) {
        bytes(shift.data(), shift.size() * sizeof(float));
        for (float value : shift) {
            if (!std::isfinite(value) || std::abs(value) > 0.5f) {
                throw std::runtime_error("Orion guard fit: invalid shift");
            }
        }
    }
    fit.samples.resize(count);
    for (auto& sample : fit.samples) {
        bytes(sample.key.data(), sample.key.size() * sizeof(float));
        bytes(sample.weights.data(), sample.weights.size() * sizeof(float));
        for (float feature : sample.key) {
            if (!std::isfinite(feature) || std::abs(feature) > 16.0f) {
                throw std::runtime_error("Orion guard fit: invalid pose feature");
            }
        }
        for (float weight : sample.weights) {
            if (!std::isfinite(weight) || weight < 0.0f || weight > 1.0f) {
                throw std::runtime_error("Orion guard fit: invalid sample weight");
            }
        }
    }
    return fit;
}

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
