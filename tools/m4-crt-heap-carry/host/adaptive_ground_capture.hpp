#pragma once

#include "adaptive_ground_inputs.hpp"
#include <algorithm>
#include <bit>
#include <cfenv>
#include <cmath>
#include <span>
#include <stdexcept>

namespace mw34::adaptive_ground {

struct SourceCorner {
    Point camera{};
    std::array<float, 2> uv{};
};

struct ClipBounds {
    float near_plane{}, far_plane{}, left{}, top{}, right{}, bottom{};
};

struct UnlitCorner {
    SourceCorner source;
    float baked_ambient{}, fog{};
    Point modulation{};
};

// The caller's initial projection retains the unrounded reciprocal for both
// axes. The generated-vertex projection deliberately rounds it before Y.
inline Point source_projection(const SourceCorner &corner, const Projection &projection) {
#if defined(__clang__)
#pragma clang fp contract(off)
#pragma clang fp reassociate(off)
#endif
    const double inverse = double(projection.near_scale) / corner.camera[2];
    return {float(double(projection.scale_x) * corner.camera[0] * inverse + projection.center_x),
            float(double(corner.camera[1]) * projection.scale_y * inverse + projection.center_y),
            float(inverse)};
}

// Only the audited baked-ambient prelude is reconstructed. The caller must
// establish that noise/colored/other directional-light branches are absent;
// the original prelude still executes and its actual inputs must match later.
inline Input reconstruct_baked(Input common, std::span<const UnlitCorner> corners) {
#if defined(__clang__)
#pragma clang fp contract(off)
#pragma clang fp reassociate(off)
#endif
    if (!common.vertices.empty() || common.colored_ambient || common.extra_uv_layers ||
        corners.size() < 3 || corners.size() > maximum_source_vertices)
        throw std::runtime_error("Unsupported adaptive baked-ambient reconstruction");
    common.varying_ambient = true;
    common.vertices.reserve(corners.size());
    for (const auto &corner : corners) {
        if (!std::isfinite(corner.baked_ambient))
            throw std::runtime_error("Nonfinite adaptive baked ambient");
        SourceVertex vertex;
        vertex.screen = source_projection(corner.source, common.projection);
        vertex.uv[0] = corner.source.uv;
        const float ambient = float(1.0 - double(corner.baked_ambient));
        vertex.ambient = std::clamp(ambient, 0.0f, 1.0f);
        vertex.fog = corner.fog;
        vertex.modulation = corner.modulation;
        common.vertices.push_back(vertex);
    }
    return common;
}

inline bool same_words(std::span<const float> first, std::span<const float> second) {
    if (first.size() != second.size())
        return false;
    for (unsigned index = 0; index < first.size(); ++index)
        if (std::bit_cast<std::uint32_t>(first[index]) !=
            std::bit_cast<std::uint32_t>(second[index]))
            return false;
    return true;
}

// A hash or approximate comparison cannot authorize a result. Padding is not
// part of the contract: compare each typed field, including signed zero bits.
inline bool same_input(const Input &first, const Input &second) {
    if (first.identity != second.identity || first.vertices.size() != second.vertices.size() ||
        first.lights.size() != second.lights.size() ||
        first.guest_control_word != second.guest_control_word ||
        first.extra_uv_layers != second.extra_uv_layers ||
        first.varying_ambient != second.varying_ambient ||
        first.colored_ambient != second.colored_ambient || first.depth_bias != second.depth_bias ||
        !same_words(first.colored_rgb, second.colored_rgb) ||
        !same_words(first.identity.camera.projection, second.identity.camera.projection) ||
        std::bit_cast<std::uint32_t>(first.identity.camera.far_clip) !=
            std::bit_cast<std::uint32_t>(second.identity.camera.far_clip))
        return false;
    const auto projection = [](const Input &input) {
        const auto &p = input.projection;
        return std::array{p.near_scale, p.center_x,  p.center_y,  p.scale_x,
                          p.scale_y,    p.inverse_x, p.inverse_y, input.depth_bias_scale};
    };
    if (!same_words(projection(first), projection(second)))
        return false;
    for (unsigned index = 0; index < first.vertices.size(); ++index) {
        const auto &a = first.vertices[index], &b = second.vertices[index];
        if (!same_words(a.screen, b.screen) || !same_words(a.modulation, b.modulation) ||
            !same_words(std::array{a.ambient, a.fog, a.colored_ambient},
                        std::array{b.ambient, b.fog, b.colored_ambient}))
            return false;
        for (unsigned layer = 0; layer < a.uv.size(); ++layer)
            if (!same_words(a.uv[layer], b.uv[layer]))
                return false;
    }
    for (unsigned index = 0; index < first.lights.size(); ++index) {
        const auto &a = first.lights[index], &b = second.lights[index];
        if (a.active != b.active || a.flags != b.flags || !same_words(a.position, b.position) ||
            !same_words(a.color, b.color) ||
            !same_words(std::array{a.diffuse, a.ambient, a.inner_radius, a.outer_radius,
                                   a.inner_squared, a.outer_squared, a.inverse_span},
                        std::array{b.diffuse, b.ambient, b.inner_radius, b.outer_radius,
                                   b.inner_squared, b.outer_squared, b.inverse_span}))
            return false;
    }
    return true;
}

// Equal corner counts do not establish that clipping left the polygon alone.
// Require every source position and UV in the original reversed corner order.
inline bool matches_unclipped_source(std::span<const SourceCorner> source, const Input &input,
                                     const ClipBounds &bounds) {
    if (source.size() != input.vertices.size() || source.size() < 3 ||
        source.size() > maximum_source_vertices || input.extra_uv_layers ||
        input.guest_control_word != 0x023f || std::fegetround() != FE_TONEAREST)
        return false;
    for (float value : {bounds.near_plane, bounds.far_plane, bounds.left, bounds.top, bounds.right,
                        bounds.bottom})
        if (!std::isfinite(value))
            return false;
    if (bounds.near_plane <= 0 || bounds.far_plane <= bounds.near_plane ||
        bounds.right <= bounds.left || bounds.bottom <= bounds.top)
        return false;
    for (unsigned index = 0; index < source.size(); ++index) {
        const auto &corner = source[index];
        for (float value : corner.camera)
            if (!std::isfinite(value))
                return false;
        if (corner.camera[2] <= bounds.near_plane || corner.camera[2] >= bounds.far_plane)
            return false;
        const auto screen = source_projection(corner, input.projection);
        if (!(screen[0] > bounds.left && screen[0] < bounds.right && screen[1] > bounds.top &&
              screen[1] < bounds.bottom))
            return false;
        for (unsigned axis = 0; axis < 3; ++axis)
            if (std::bit_cast<std::uint32_t>(screen[axis]) !=
                std::bit_cast<std::uint32_t>(input.vertices[index].screen[axis]))
                return false;
        for (unsigned axis = 0; axis < 2; ++axis)
            if (!std::isfinite(corner.uv[axis]) ||
                std::bit_cast<std::uint32_t>(corner.uv[axis]) !=
                    std::bit_cast<std::uint32_t>(input.vertices[index].uv[0][axis]))
                return false;
    }
    return true;
}

} // namespace mw34::adaptive_ground
