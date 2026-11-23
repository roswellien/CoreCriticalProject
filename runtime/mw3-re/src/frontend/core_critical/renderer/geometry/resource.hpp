#pragma once

#include <algorithm>
#include <array>
#include <atomic>
#include <cmath>
#include <cstdint>
#include <limits>
#include <memory>
#include <stdexcept>
#include <vector>

// Runtime-neutral, owned geometry. No engine pointers survive registration.
namespace cc::geometry {

enum class Mode { legacy, partial, gpu, cpu_reference };
enum class Submission { unsupported, submitted };

struct Vertex {
    float x, y, z, nx, ny, nz, u, v;
};
static_assert(sizeof(Vertex) == 32);

struct Range {
    std::uint32_t first{}, count{}, polygon{};
    bool two_sided{};
    std::uint32_t material_slot{};
};

struct Resource {
    std::uint64_t identity{};
    std::uint32_t source_vertices{};
    std::uint32_t source_polygons{};
    bool source_bounds_valid{};
    std::array<float, 3> source_min{std::numeric_limits<float>::infinity(),
                                    std::numeric_limits<float>::infinity(),
                                    std::numeric_limits<float>::infinity()};
    std::array<float, 3> source_max{-std::numeric_limits<float>::infinity(),
                                    -std::numeric_limits<float>::infinity(),
                                    -std::numeric_limits<float>::infinity()};
    std::vector<Vertex> vertices;
    std::vector<std::uint32_t> indices;
    std::vector<Range> ranges;
};

// Borrowed registration inputs are consumed synchronously, once per resource
// revision. Packets contain Resource ownership, never these source pointers.
// Adapters provide GameZ corner order; registration reverses it for the GPU.
// Missing normals use GameZ's negative-cross convention. Authored normals are
// retained. A second runtime must translate to these same input conventions.
struct Polygon {
    std::uint32_t count{};
    const std::uint32_t *positions{};
    const std::uint32_t *normals{};
    const float *uv{};
    bool strip{}, two_sided{};
    std::uint32_t material_slot{std::numeric_limits<std::uint32_t>::max()};
};

std::shared_ptr<const Resource> register_resource(const float *positions,
                                                  std::uint32_t position_count,
                                                  const float *normals, std::uint32_t normal_count,
                                                  const std::vector<Polygon> &polygons);

struct Material {
    // Adapter-local renderer handle, resolved to an owned binding at submission.
    std::int32_t texture{-1};
    std::uint32_t color{0xffffffff};
    std::uint8_t address_u{1}, address_v{1};
};

struct Fog {
    bool enabled{};
    std::array<float, 3> color{};
    float near_range{}, inverse_range{}, low_altitude{}, inverse_altitude{};
    float edge_start{}, edge_inverse_range{};
    bool active() const { return enabled || edge_inverse_range > 0.f; }
};

// Keep the three linear factors separate and unclamped through clipping/interpolation.
// Clamping a crossing triangle's endpoints first leaves visibility at the far cut.
inline std::array<float, 3> fog_factors(const Fog &fog, float distance, float height) {
    return {fog.enabled ? (distance - fog.near_range) * fog.inverse_range : 0.f,
            fog.enabled ? 1.f - (height - fog.low_altitude) * fog.inverse_altitude : 0.f,
            (distance - fog.edge_start) * fog.edge_inverse_range};
}

inline float fog_amount(const std::array<float, 3> &factors) {
    const float mission = std::clamp(factors[0], 0.f, 1.f) * std::clamp(factors[1], 0.f, 1.f);
    const float edge = std::clamp(factors[2], 0.f, 1.f);
    return 1.f - (1.f - mission) * (1.f - edge);
}

// Float operations mirror the geometry shaders, with clamping at the final sample.
inline float fog_amount(const Fog &fog, float distance, float height) {
    return fog_amount(fog_factors(fog, distance, height));
}

struct Statistics {
    std::uint64_t submitted_models{}, skipped_vertices{}, skipped_polygons{}, unsupported_models{};
    std::uint64_t cpu_draw_calls{};
};

} // namespace cc::geometry
