#pragma once

#include "adaptive_ground_inputs.hpp"
#include <bit>
#include <span>
#include <stdexcept>

namespace mw34::adaptive_ground {

using GuestVertexRecord = std::array<std::uint32_t, 33>;
using GuestTriangleRecord = std::array<std::uint32_t, 7>;
static_assert(sizeof(GuestVertexRecord) == 132 && sizeof(GuestTriangleRecord) == 28);

// Records must first be copied from the CURRENT guest scratch. Preserve slots
// the original does not write, including unused UVs and initial boundary flags.
// Original projection still supplies every screen field after this transfer.
inline void encode_preprojection_vertices(const Result &result, unsigned source_count,
                                          std::span<GuestVertexRecord> records) {
    if (!result.prepared || source_count < 3 || source_count > maximum_source_vertices ||
        result.vertices.size() <= source_count || result.vertices.size() > 1024 ||
        records.size() != result.vertices.size())
        throw std::runtime_error("Adaptive vertex transfer exceeds its contract");
    for (unsigned index = 0; index < records.size(); ++index) {
        const auto &vertex = result.vertices[index];
        auto &record = records[index];
        for (unsigned axis = 0; axis < 3; ++axis) {
            record[axis] = std::bit_cast<std::uint32_t>(vertex.camera[axis]);
            record[23 + axis] = std::bit_cast<std::uint32_t>(vertex.base[axis]);
            record[26 + axis] = std::bit_cast<std::uint32_t>(vertex.modulation[axis]);
            record[29 + axis] = std::bit_cast<std::uint32_t>(vertex.lit[axis]);
        }
        for (unsigned axis = 0; axis < 2; ++axis)
            record[6 + axis] = std::bit_cast<std::uint32_t>(vertex.uv[0][axis]);
        record[22] = std::bit_cast<std::uint32_t>(vertex.fog);
        if (index >= source_count)
            record[32] = std::uint32_t(vertex.boundary);
    }
}

inline void encode_triangles(const Result &result, std::span<GuestTriangleRecord> records,
                             bool restore_active) {
    if (!result.prepared || result.triangles.empty() || result.triangles.size() > 2048 ||
        records.size() != result.triangles.size())
        throw std::runtime_error("Adaptive triangle transfer exceeds its contract");
    for (unsigned index = 0; index < records.size(); ++index) {
        const auto &face = result.triangles[index];
        auto &record = records[index];
        for (unsigned edge = 0; edge < 3; ++edge) {
            record[edge] = face.vertices[edge];
            record[3 + edge] = std::uint32_t(face.neighbors[edge]);
        }
        record[6] = std::uint32_t(restore_active && face.active);
    }
}

} // namespace mw34::adaptive_ground
