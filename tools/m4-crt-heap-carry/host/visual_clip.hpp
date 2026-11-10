#pragma once
#include <array>
#include <cmath>
#include <stdexcept>
#include <vector>

namespace mw34::visual_clip {
// One near-plane kernel for presentation meshes. Attribute interpolation belongs
// to the caller, so clipping cannot replace beam opacity/fog with flame defaults.
template <class Vertex> struct ClippedTriangle {
    std::array<Vertex, 4> vertices{};
    unsigned count{};
    void push_back(const Vertex &vertex) {
        if (count == vertices.size())
            throw std::runtime_error("Visual clip bound exceeded");
        vertices[count++] = vertex;
    }
    unsigned size() const { return count; }
    const Vertex &operator[](unsigned index) const { return vertices[index]; }
};
template <class Vertex, class Interpolate>
ClippedTriangle<Vertex> near_triangle(const std::array<Vertex, 3> &input, double near_plane,
                                      Interpolate interpolate) {
    if (!std::isfinite(near_plane) || near_plane <= 0)
        throw std::runtime_error("Invalid visual near_plane plane");
    ClippedTriangle<Vertex> clipped;
    for (unsigned i = 0; i < 3; ++i) {
        const auto &a = input[i];
        const auto &b = input[(i + 1) % 3];
        if (!std::isfinite(a.z))
            throw std::runtime_error("Nonfinite visual depth");
        const bool inside = a.z >= near_plane, next = b.z >= near_plane;
        if (inside)
            clipped.push_back(a);
        if (inside != next) {
            auto vertex = interpolate(a, b, (near_plane - a.z) / (b.z - a.z));
            vertex.z = near_plane;
            clipped.push_back(vertex);
        }
    }
    return clipped;
}
} // namespace mw34::visual_clip
