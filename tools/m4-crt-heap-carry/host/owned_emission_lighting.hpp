#pragma once
#include "draw_emissions.hpp"
#include "fixture_lighting.hpp"
#include "owned_emission.hpp"
#include <algorithm>
#include <map>
#include <tuple>

namespace mw34::emission {
// This path is independent of normal-map admission and uses no texture sampler.
inline std::uint32_t capture(const Record &material, float (&fog)[4],
                             submission::DrawEmissions &emissions, bool enabled) {
    if (!enabled)
        return submission::DrawEmissions::none;
    fog[3] = 1.f + material.strength;
    return emissions.capture({float(material.regions.size()), material.strength, 0, 0},
                             material.regions);
}

// Only draws in this submitted scene can contribute. No actor or scenery cache
// retains an anchor after its exterior owner disappears or changes appearance.
template <class Draws>
std::vector<fixtures::MovingLight> moving_lights(const Draws &draws, const Point &eye,
                                                 float strength, bool enabled) {
    if (!enabled)
        return {};
    using Key = std::tuple<std::uint32_t, std::string, std::string, std::string>;
    struct Candidate {
        float distance;
        fixtures::MovingLight light;
    };
    std::map<Key, Candidate> candidates;
    constexpr std::size_t limit = 4096;
    for (const auto &draw : draws) {
        const auto &instance = draw.owned_emission_instance;
        if (!instance || !instance->material)
            continue;
        const auto &material = *instance->material;
        for (const auto &anchor : material.anchors) {
            if (anchor.radius <= 0 || anchor.intensity <= 0 || strength <= 0)
                continue;
            Point position{};
            for (unsigned row = 0; row < 3; ++row) {
                position[row] = instance->world[row * 4 + 3];
                for (unsigned col = 0; col < 3; ++col)
                    position[row] += instance->world[row * 4 + col] * anchor.position[col];
            }
            if (!std::all_of(position.begin(), position.end(),
                             [](float v) { return std::isfinite(v); }))
                throw std::runtime_error("Owned emission anchor world position is not finite");
            fixtures::MovingLight selected;
            selected.light.start = {position[0], position[1], position[2], anchor.radius};
            selected.light.end = {position[0], position[1], position[2],
                                  float(effects::LightKind::point)};
            selected.light.color = {anchor.color[0], anchor.color[1], anchor.color[2],
                                    anchor.intensity * strength};
            const Key key{instance->root, instance->owner, material.id, anchor.id};
            candidates.try_emplace(key, Candidate{effects::distance2(eye, position), selected});
            if (candidates.size() > limit) {
                const auto farthest = std::max_element(
                    candidates.begin(), candidates.end(), [](const auto &a, const auto &b) {
                        return std::tie(a.second.distance, a.first) <
                               std::tie(b.second.distance, b.first);
                    });
                candidates.erase(farthest);
            }
        }
    }
    std::vector<fixtures::MovingLight> result;
    result.reserve(candidates.size());
    for (const auto &[key, candidate] : candidates)
        result.push_back(candidate.light);
    return result;
}
} // namespace mw34::emission
