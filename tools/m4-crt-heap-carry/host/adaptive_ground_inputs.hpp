#pragma once

#include "camera_history.hpp"
#include <array>
#include <cstdint>
#include <vector>

namespace mw34::adaptive_ground {

using Point = std::array<float, 3>;
using TextureCoordinates = std::array<std::array<float, 2>, 8>;

// Native prelude attributes occupy 64 records before the extra-UV globals.
// The selected-light pointer table has 128 entries before triangle scratch.
inline constexpr unsigned maximum_source_vertices = 64;
inline constexpr unsigned maximum_lights = 128;

// These are CPU values, never references to live guest memory or renderer state.
// A render submission is distinct from both a simulation tick and a presentation.
struct FrameIdentity {
    temporal::Snapshot camera;
    // Conservative existing lifetime counters cover every heap retirement and
    // map/protect change during a mesh invocation. They are not persistent
    // surface identities and do not establish temporal motion correspondence.
    std::uint64_t source_epoch{}, heap_release_serial{}, memory_generation{};
    std::uint32_t source_node{}, mesh{}, polygon{}, material{}, device{};
    std::array<std::uint32_t, 4> clip_rectangle{};
    bool operator==(const FrameIdentity &) const = default;
};

struct SourceVertex {
    // The legacy producer supplies rounded, unjittered screen X/Y/depth.
    // Inverse-projecting these values is part of the numerical contract.
    Point screen{};
    TextureCoordinates uv{};
    float ambient{}, fog{}, colored_ambient{};
    Point modulation{};
};

struct Light {
    Point position{}, color{};
    float diffuse{}, ambient{}, inner_radius{}, outer_radius{}, inner_squared{}, outer_squared{},
        inverse_span{};
    std::uint32_t flags{};
    bool active{};
};

struct Projection {
    float near_scale{}, center_x{}, center_y{}, scale_x{}, scale_y{}, inverse_x{}, inverse_y{};
};

struct Input {
    FrameIdentity identity;
    std::vector<SourceVertex> vertices;
    std::vector<Light> lights;
    Projection projection;
    Point colored_rgb{};
    float depth_bias_scale{};
    std::int32_t depth_bias{};
    std::uint16_t guest_control_word{0x023f};
    unsigned extra_uv_layers{};
    bool varying_ambient{}, colored_ambient{};
};

struct Vertex {
    Point camera{}, screen{};
    TextureCoordinates uv{};
    float fog{};
    Point base{}, modulation{}, lit{};
    bool boundary{};
};

struct Triangle {
    std::array<unsigned, 3> vertices{};
    std::array<int, 3> neighbors{};
    bool active{};
    bool operator==(const Triangle &) const = default;
};

struct Limits {
    unsigned vertices{1024}, triangles{2048};
};

struct Result {
    FrameIdentity identity;
    std::vector<Vertex> vertices;
    std::vector<Triangle> triangles;
    std::vector<unsigned> selected_lights;
    // The centroid is written before the no-light return, but is not counted
    // as a vertex until preparation continues. Keep that effect explicit.
    Point centroid{};
    Point distance_delta{};
    bool distance_written{};
    bool prepared{};
};

} // namespace mw34::adaptive_ground
