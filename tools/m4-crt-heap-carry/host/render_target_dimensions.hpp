#pragma once

#include <array>
#include <cmath>
#include <optional>

namespace mw34::render_target {

// Values from one main-thread observation of the existing renderer. A pending
// request has no authoritative effective raster yet, so it cannot identify jobs.
inline std::optional<std::array<unsigned, 6>>
current_dimensions(std::array<unsigned, 2> guest, std::array<unsigned, 2> requested_guest,
                   std::array<unsigned, 4> raster, float scale, float requested_scale,
                   bool initialized, bool frontend) {
    if (!initialized || frontend || guest != requested_guest || !std::isfinite(scale) ||
        !std::isfinite(requested_scale) || scale <= 0 || scale != requested_scale)
        return {};
    for (unsigned dimension : guest)
        if (!dimension)
            return {};
    for (unsigned dimension : raster)
        if (!dimension)
            return {};
    return std::array{guest[0], guest[1], raster[0], raster[1], raster[2], raster[3]};
}

} // namespace mw34::render_target
