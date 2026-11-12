#pragma once

#include "effect_light_ranking.hpp"
#include "headlight_catalog.hpp"

#include <optional>

namespace mw34::headlights {

inline std::optional<effects::Candidate> spotlight(const Lamp &lamp,
                                                   const std::array<double, 16> &world,
                                                   double envelope, std::uint64_t source) {
    if (!(envelope > 0 && envelope <= 1) || !source ||
        (lamp.space != "guest_node" && lamp.space != "donor_bone"))
        return std::nullopt;

    std::array<double, 3> position{}, direction{};
    for (unsigned row = 0; row < 3; ++row) {
        position[row] = world[row * 4 + 3];
        for (unsigned col = 0; col < 3; ++col) {
            position[row] += world[row * 4 + col] * lamp.position[col];
            direction[row] += world[row * 4 + col] * lamp.direction[col];
        }
        if (!(std::abs(position[row]) <= std::numeric_limits<float>::max()))
            return std::nullopt;
    }
    const auto length = std::hypot(direction[0], direction[1], direction[2]);
    if (!(length > 0) || !std::isfinite(length))
        return std::nullopt;

    effects::Candidate candidate{};
    for (unsigned axis = 0; axis < 3; ++axis) {
        candidate.light.start[axis] = float(position[axis]);
        candidate.light.end[axis] = float(direction[axis] / length);
        candidate.light.color[axis] = lamp.color[axis];
    }
    candidate.light.start[3] = lamp.range;
    candidate.light.end[3] = 2;
    candidate.light.color[3] = float(lamp.intensity * envelope);
    constexpr double radians_per_degree = 0.017453292519943295;
    candidate.cone = {float(std::cos(lamp.inner_angle * radians_per_degree)),
                      float(std::cos(lamp.outer_angle * radians_per_degree)), 1, 0};
    candidate.source = source;
    return candidate;
}

} // namespace mw34::headlights
