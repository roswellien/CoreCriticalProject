#pragma once
#include <cstdint>
#include <stdexcept>

namespace mw34::submission {
// Recomputed for every prepared scene, from its current bounds and light list.
// The six cube faces can share these exact sphere-overlap Boolean results.
// Face-plane culling and all shadow draw ordering remain separate and unchanged.
template <class Bounds, class Lights>
std::uint64_t fixture_light_mask(const Bounds &bounds, const Lights &lights,
                                 unsigned first, unsigned count) {
    if (first > count || count > 64)
        throw std::runtime_error("Fixture light mask index outside range");
    std::uint64_t mask{};
    for (unsigned i = first; i < count; ++i) {
        const auto &light = lights.lights[i];
        const bool overlaps = bounds.overlaps(
            {light.start[0], light.start[1], light.start[2]}, light.start[3]);
        mask |= std::uint64_t(overlaps) << i;
    }
    return mask;
}
} // namespace mw34::submission
