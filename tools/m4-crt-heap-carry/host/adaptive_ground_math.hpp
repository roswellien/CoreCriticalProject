#pragma once

#include "adaptive_ground_inputs.hpp"
#include <bit>
#include <cfenv>
#include <cmath>
#include <stdexcept>
#include <utility>

// Scoped to function bodies so including this header does not change the
// surrounding native host's floating-point compilation policy.
#if defined(__clang__)
#define MW34_ADAPTIVE_PRECISE _Pragma("clang fp contract(off)") _Pragma("clang fp reassociate(off)")
#else
#define MW34_ADAPTIVE_PRECISE
#endif

namespace mw34::adaptive_ground {
namespace detail {

inline double squared_distance(const Point &a, const Point &b) {
    MW34_ADAPTIVE_PRECISE
    const float x = float(double(a[0]) - b[0]);
    const float y = float(double(a[1]) - b[1]);
    const float z = float(double(a[2]) - b[2]);
    if (!std::isfinite(x) || !std::isfinite(y) || !std::isfinite(z))
        throw std::runtime_error("Adaptive ground distance exceeds its numeric contract");
    return (double(x) * x + double(y) * y) + double(z) * z;
}

inline float approximate_radius(float squared) {
    if (!std::isfinite(squared) || squared < 0)
        throw std::runtime_error("Adaptive ground radius exceeds its numeric contract");
    const auto word = (std::bit_cast<std::uint32_t>(squared) >> 1) + 0x1fc00000U;
    return std::bit_cast<float>(word);
}

inline Point triangle_centroid(const Point &a, const Point &b, const Point &c) {
    MW34_ADAPTIVE_PRECISE
    Point center{};
    for (unsigned axis = 0; axis < 3; ++axis) {
        const float pair = float(double(a[axis]) + b[axis]);
        const float sum = float(double(pair) + c[axis]);
        center[axis] = float(double(sum) * std::bit_cast<float>(0x3eaaaaaaU));
    }
    return center;
}

inline void require_finite(float value) {
    if (!std::isfinite(value))
        throw std::runtime_error("Adaptive ground input is not finite");
}

inline void validate(const Input &input, Limits limits) {
    if (input.guest_control_word != 0x023f || std::fegetround() != FE_TONEAREST)
        throw std::runtime_error("Adaptive ground requires the audited nearest/53-bit FP domain");
    if (input.vertices.size() < 3 || input.vertices.size() > maximum_source_vertices ||
        input.extra_uv_layers >= 8 || input.lights.size() > maximum_lights ||
        limits.vertices <= input.vertices.size() || limits.vertices > 1024 ||
        limits.triangles < input.vertices.size() || limits.triangles > 2048)
        throw std::runtime_error("Adaptive ground input exceeds its capacity contract");
    const auto &p = input.projection;
    for (float value : {p.near_scale, p.center_x, p.center_y, p.scale_x, p.scale_y, p.inverse_x,
                        p.inverse_y, input.depth_bias_scale})
        require_finite(value);
    if (p.near_scale <= 0 || p.scale_x == 0 || p.scale_y == 0 || p.inverse_x == 0 ||
        p.inverse_y == 0)
        throw std::runtime_error("Adaptive ground projection is outside its contract");
    for (float value : input.colored_rgb)
        require_finite(value);
    for (const auto &vertex : input.vertices) {
        for (float value : vertex.screen)
            require_finite(value);
        if (vertex.screen[2] <= 0)
            throw std::runtime_error("Adaptive ground input depth must be positive");
        for (unsigned layer = 0; layer <= input.extra_uv_layers; ++layer)
            for (float value : vertex.uv[layer])
                require_finite(value);
        for (float value : {vertex.ambient, vertex.fog, vertex.colored_ambient})
            require_finite(value);
        for (float value : vertex.modulation)
            require_finite(value);
    }
    for (const auto &light : input.lights) {
        if (!light.active || (light.flags & 0x50U) != 0x50U)
            continue;
        for (float value : light.position)
            require_finite(value);
        for (float value : light.color)
            require_finite(value);
        for (float value : {light.diffuse, light.ambient, light.inner_radius, light.outer_radius,
                            light.inner_squared, light.outer_squared, light.inverse_span})
            require_finite(value);
        if (light.inner_radius < 0 || light.outer_radius < light.inner_radius ||
            light.inner_squared < 0 || light.outer_squared < light.inner_squared ||
            light.inverse_span < 0)
            throw std::runtime_error("Adaptive ground light radius is outside its contract");
    }
}

class Preparation {
  public:
    Preparation(const Input &input, Limits limits) : input_(input), limits_(limits) {
        validate(input, limits);
        result_.identity = input.identity;
        result_.vertices.reserve(limits.vertices);
        result_.triangles.reserve(limits.triangles);
    }

    Result run() {
        MW34_ADAPTIVE_PRECISE
        const unsigned count = unsigned(input_.vertices.size());
        // With no flagged lights the original returns before inverse projection.
        for (unsigned index = 0; index < input_.lights.size(); ++index) {
            const auto &light = input_.lights[index];
            if (light.active && (light.flags & 0x50U) == 0x50U)
                result_.selected_lights.push_back(index);
        }
        if (result_.selected_lights.empty())
            return std::move(result_);
        unproject();
        result_.centroid = centroid(count);
        float extent = 0;
        for (const auto &vertex : result_.vertices) {
            const double squared = distance(vertex.camera, result_.centroid);
            if (squared > extent)
                extent = float(squared);
        }
        const float radius = approximate_radius(extent);
        for (std::size_t index = 0; index < result_.selected_lights.size();) {
            const auto &light = input_.lights[result_.selected_lights[index]];
            const double reach = double(light.outer_radius) + radius;
            if (reach * reach <= distance(light.position, result_.centroid)) {
                result_.selected_lights[index] = result_.selected_lights.back();
                result_.selected_lights.pop_back();
            } else {
                ++index;
            }
        }
        if (result_.selected_lights.empty())
            return std::move(result_);
        initialize_attributes();
        for (unsigned index = 0; index < count; ++index) {
            Triangle triangle;
            triangle.vertices = {index, (index + 1) % count, count};
            triangle.neighbors = {-1, int((index + 1) % count), int((index + count - 1) % count)};
            triangle.active = true;
            result_.triangles.push_back(triangle);
        }
        for (unsigned pass = 0; pass < 6; ++pass) {
            const unsigned before = unsigned(result_.triangles.size());
            for (unsigned index = 0; index < before; ++index)
                refine(index);
        }
        project(count);
        result_.prepared = true;
        return std::move(result_);
    }

  private:
    const Input &input_;
    Limits limits_;
    Result result_;

    double distance(const Point &a, const Point &b) {
        MW34_ADAPTIVE_PRECISE
        for (unsigned axis = 0; axis < 3; ++axis)
            result_.distance_delta[axis] = float(double(a[axis]) - b[axis]);
        result_.distance_written = true;
        return squared_distance(a, b);
    }

    float maximum_distance(const Point &center, const std::array<unsigned, 3> &corners) {
        MW34_ADAPTIVE_PRECISE
        float maximum = 0;
        // Refinement reverses the initial bound's subtraction direction. The
        // squared value agrees, but the original shared delta scratch does not.
        for (unsigned index : corners) {
            const double squared = distance(center, result_.vertices.at(index).camera);
            if (squared > maximum)
                maximum = float(squared);
        }
        return maximum;
    }

    void unproject() {
        MW34_ADAPTIVE_PRECISE
        const auto &p = input_.projection;
        for (const auto &source : input_.vertices) {
            Vertex vertex;
            const double depth = double(p.near_scale) / source.screen[2];
            vertex.camera[0] = float((double(source.screen[0]) - p.center_x) * p.inverse_x * depth);
            vertex.camera[2] = float(depth);
            vertex.camera[1] =
                float((double(source.screen[1]) - p.center_y) * p.inverse_y * vertex.camera[2]);
            for (float value : vertex.camera)
                require_finite(value);
            result_.vertices.push_back(vertex);
        }
    }

    Point centroid(unsigned count) const {
        MW34_ADAPTIVE_PRECISE
        Point center{};
        for (unsigned axis = 0; axis < 3; ++axis) {
            center[axis] =
                float(double(result_.vertices[0].camera[axis]) + result_.vertices[1].camera[axis]);
            for (unsigned index = 2; index < count; ++index)
                center[axis] = float(double(center[axis]) + result_.vertices[index].camera[axis]);
        }
        const double reciprocal = 1.0 / count;
        // The first multiply retains the value above its FSTS float store.
        center[0] = float(reciprocal * center[0]);
        center[1] = float(double(float(reciprocal)) * center[1]);
        center[2] = float(double(float(reciprocal)) * center[2]);
        return center;
    }

    void illuminate(Vertex &vertex) {
        MW34_ADAPTIVE_PRECISE
        vertex.lit = vertex.base;
        for (unsigned index : result_.selected_lights) {
            const auto &light = input_.lights[index];
            const double squared = distance(light.position, vertex.camera);
            if (squared >= light.outer_squared)
                continue;
            double power = double(light.diffuse) + light.ambient;
            if (light.inner_squared < float(squared)) {
                const double ramp =
                    (double(light.outer_radius) - approximate_radius(float(squared))) *
                    light.inverse_span;
                power = (ramp * ramp) * float(power);
            }
            for (unsigned channel = 0; channel < 3; ++channel)
                vertex.lit[channel] =
                    float(double(light.color[channel]) * power + vertex.lit[channel]);
        }
        for (float value : vertex.lit)
            require_finite(value);
    }

    void initialize_attributes() {
        MW34_ADAPTIVE_PRECISE
        const unsigned count = unsigned(input_.vertices.size());
        for (unsigned index = 0; index < count; ++index) {
            const auto &source = input_.vertices[index];
            auto &vertex = result_.vertices[index];
            vertex.screen = source.screen;
            vertex.uv = source.uv;
            vertex.fog = source.fog;
            const float ambient =
                input_.varying_ambient ? source.ambient : input_.vertices[0].ambient;
            vertex.base.fill(float(1.0 - ambient));
            if (input_.colored_ambient) {
                const double scale =
                    double(source.colored_ambient) * std::bit_cast<float>(0x3b808081U);
                for (unsigned channel = 0; channel < 3; ++channel)
                    vertex.base[channel] =
                        float(double(scale) * input_.colored_rgb[channel] + vertex.base[channel]);
            }
            for (auto &channel : vertex.base)
                if (channel < 0)
                    channel = 0;
            vertex.modulation = source.modulation;
            illuminate(vertex);
        }
        Vertex center;
        center.camera = result_.centroid;
        center.uv = result_.vertices[0].uv;
        center.fog = result_.vertices[0].fog;
        center.base = result_.vertices[0].base;
        center.modulation = result_.vertices[0].modulation;
        for (unsigned index = 1; index < count; ++index) {
            const auto &vertex = result_.vertices[index];
            for (unsigned layer = 0; layer <= input_.extra_uv_layers; ++layer)
                for (unsigned axis = 0; axis < 2; ++axis)
                    center.uv[layer][axis] =
                        float(double(center.uv[layer][axis]) + vertex.uv[layer][axis]);
            center.fog = float(double(center.fog) + vertex.fog);
            for (unsigned channel = 0; channel < 3; ++channel) {
                center.base[channel] = float(double(center.base[channel]) + vertex.base[channel]);
                center.modulation[channel] =
                    float(double(center.modulation[channel]) + vertex.modulation[channel]);
            }
        }
        const float reciprocal = float(1.0 / count);
        for (unsigned layer = 0; layer <= input_.extra_uv_layers; ++layer)
            for (auto &coordinate : center.uv[layer])
                coordinate = float(double(coordinate) * reciprocal);
        center.fog = float(double(center.fog) * reciprocal);
        for (unsigned channel = 0; channel < 3; ++channel) {
            center.base[channel] = float(double(center.base[channel]) * reciprocal);
            center.modulation[channel] = float(double(center.modulation[channel]) * reciprocal);
        }
        illuminate(center);
        result_.vertices.push_back(center);
    }

    void refine(unsigned index) {
        MW34_ADAPTIVE_PRECISE
        auto &triangle = result_.triangles[index];
        if (!triangle.active)
            return;
        const auto &a = result_.vertices[triangle.vertices[0]].camera;
        const auto &b = result_.vertices[triangle.vertices[1]].camera;
        const auto &c = result_.vertices[triangle.vertices[2]].camera;
        const Point center = triangle_centroid(a, b, c);
        const float squared = maximum_distance(center, triangle.vertices);
        bool useful = false;
        if (squared >= 10) {
            const float radius = approximate_radius(squared);
            for (unsigned light_index : result_.selected_lights) {
                const auto &light = input_.lights[light_index];
                const double separation = distance(light.position, center);
                const double outer_reach = double(light.outer_radius) + radius;
                const double inner_reach = double(light.inner_radius) - radius;
                if (separation < outer_reach * outer_reach &&
                    (inner_reach < 0 || inner_reach * inner_reach < separation)) {
                    useful = true;
                    break;
                }
            }
        }
        if (!useful) {
            triangle.active = false;
            return;
        }
        unsigned edge = 0;
        float longest = float(distance(a, b));
        const double second = distance(b, c);
        if (longest < second) {
            longest = float(second);
            edge = 1;
        }
        if (distance(c, a) > longest)
            edge = 2;
        split(index, edge);
    }

    void relink(int index, unsigned previous, unsigned replacement) {
        if (index < 0)
            return;
        for (auto &neighbor : result_.triangles.at(unsigned(index)).neighbors)
            if (neighbor == int(previous)) {
                neighbor = int(replacement);
                return;
            }
        throw std::runtime_error("Adaptive ground adjacency is not reciprocal");
    }

    void split(unsigned index, unsigned edge) {
        MW34_ADAPTIVE_PRECISE
        auto &triangle = result_.triangles[index];
        const unsigned following = (edge + 1) % 3, other = (edge + 2) % 3;
        const int adjacent = triangle.neighbors[edge];
        const unsigned needed = adjacent < 0 ? 1U : 2U;
        if (result_.vertices.size() == limits_.vertices ||
            result_.triangles.size() + needed > limits_.triangles)
            throw std::runtime_error("Adaptive ground refinement exceeds its scratch capacity");
        const auto &a = result_.vertices[triangle.vertices[edge]];
        const auto &b = result_.vertices[triangle.vertices[following]];
        Vertex vertex;
        for (unsigned axis = 0; axis < 3; ++axis) {
            vertex.camera[axis] = float((double(a.camera[axis]) + b.camera[axis]) * 0.5);
            vertex.base[axis] = float((double(a.base[axis]) + b.base[axis]) * 0.5);
            vertex.modulation[axis] =
                float((double(a.modulation[axis]) + b.modulation[axis]) * 0.5);
        }
        for (unsigned layer = 0; layer <= input_.extra_uv_layers; ++layer)
            for (unsigned axis = 0; axis < 2; ++axis)
                vertex.uv[layer][axis] =
                    float((double(a.uv[layer][axis]) + b.uv[layer][axis]) * 0.5);
        vertex.fog = float((double(a.fog) + b.fog) * 0.5);
        vertex.boundary = adjacent < 0;
        illuminate(vertex);
        const unsigned midpoint = unsigned(result_.vertices.size());
        result_.vertices.push_back(vertex);
        const unsigned created_index = unsigned(result_.triangles.size());
        Triangle created{{midpoint, triangle.vertices[following], triangle.vertices[other]},
                         {-1, triangle.neighbors[following], int(index)},
                         true};
        triangle.vertices[following] = midpoint;
        relink(created.neighbors[1], index, created_index);
        triangle.neighbors[following] = int(created_index);
        result_.triangles.push_back(created);
        if (adjacent < 0)
            return;
        auto &neighbor = result_.triangles.at(unsigned(adjacent));
        unsigned corner = 0;
        while (corner < 3 && neighbor.vertices[corner] != created.vertices[1])
            ++corner;
        if (corner == 3)
            throw std::runtime_error("Adaptive ground neighbor does not share the split edge");
        const unsigned next = (corner + 1) % 3, last = (corner + 2) % 3;
        const unsigned extra_index = unsigned(result_.triangles.size());
        Triangle extra{{midpoint, neighbor.vertices[next], neighbor.vertices[last]},
                       {int(index), neighbor.neighbors[next], adjacent},
                       neighbor.active};
        neighbor.vertices[next] = midpoint;
        relink(extra.neighbors[1], unsigned(adjacent), extra_index);
        neighbor.neighbors[next] = int(extra_index);
        triangle.neighbors[edge] = int(extra_index);
        result_.triangles[created_index].neighbors[0] = adjacent;
        neighbor.neighbors[corner] = int(created_index);
        result_.triangles.push_back(extra);
    }

    void project(unsigned count) {
        MW34_ADAPTIVE_PRECISE
        const auto &p = input_.projection;
        for (unsigned index = count; index < result_.vertices.size(); ++index) {
            auto &vertex = result_.vertices[index];
            const double inverse = double(p.near_scale) / vertex.camera[2];
            vertex.screen[2] = float(inverse);
            vertex.screen[0] = float(double(vertex.camera[0]) * p.scale_x * inverse + p.center_x);
            vertex.screen[1] =
                float(double(vertex.camera[1]) * p.scale_y * vertex.screen[2] + p.center_y);
        }
        const float bias = float(double(input_.depth_bias) * input_.depth_bias_scale + 1.0);
        for (auto &vertex : result_.vertices)
            vertex.screen[2] = float(double(bias) * vertex.screen[2]);
        const auto &center = result_.vertices[count];
        for (unsigned index = count + 1; index < result_.vertices.size(); ++index) {
            auto &vertex = result_.vertices[index];
            if (!vertex.boundary)
                continue;
            const float x = float(double(vertex.screen[0]) - center.screen[0]);
            const float y = float(double(vertex.screen[1]) - center.screen[1]);
            const double squared = double(x) * x + double(y) * y;
            if (squared == 0)
                continue;
            const double inverse = 1.0 / approximate_radius(float(squared));
            vertex.screen[0] = float(inverse * x + vertex.screen[0]);
            vertex.screen[1] = float(inverse * y + vertex.screen[1]);
        }
        for (const auto &vertex : result_.vertices)
            for (float value : vertex.screen)
                require_finite(value);
    }
};

} // namespace detail

inline Result prepare(const Input &input, Limits limits = {}) {
    return detail::Preparation(input, limits).run();
}

} // namespace mw34::adaptive_ground

#undef MW34_ADAPTIVE_PRECISE
