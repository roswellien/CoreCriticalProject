#pragma once

#include <array>
#include <cstdlib>
#include <cstring>
#include <stdexcept>

namespace mw34::native_static {

// Development-only producer. Unsupported source/material states keep their
// existing recompiled producer; invalid configuration must not silently enable it.
inline bool enabled() {
    static const bool value = [] {
        const char *text = std::getenv("MW34_GPU_STATIC_PRODUCER");
        if (!text || !*text || !std::strcmp(text, "0"))
            return false;
        if (!std::strcmp(text, "1"))
            return true;
        throw std::runtime_error("MW34_GPU_STATIC_PRODUCER must be 0 or 1");
    }();
    return value;
}

// Immutable per-instance inputs to the recovered vertex-fog calculation.
// Distance: start radius, squared start/end radii, inverse distance span.
// Height: upper/lower heights, inverse height span, active flag.
// Height row maps original camera-space positions to original world height.
struct alignas(16) Fog {
    std::array<float, 4> distance{}, height{}, height_row{};
};
static_assert(sizeof(Fog) == 48);

} // namespace mw34::native_static
