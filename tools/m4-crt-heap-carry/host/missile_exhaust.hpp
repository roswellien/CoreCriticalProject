#pragma once
#include "visual_clip.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <stdexcept>
#include <vector>

namespace mw34::missiles {
inline constexpr double exhaust_size_scale = 2;
inline constexpr double exhaust_strength_scale = 2;
inline constexpr float light_intensity = 2.2f * float(exhaust_strength_scale);
// Presentation geometry only. The caller authenticates an original live
// rocket body and supplies its exact local-to-camera matrix and projection.
using Matrix = std::array<double, 12>;
using Projection = std::array<float, 6>;
struct Vertex {
    float x, y, z, rhw;
    std::uint32_t color, specular;
    float u, v;
};
static_assert(sizeof(Vertex) == 32);
struct CameraVertex {
    double x, y, z, u, v;
};
inline CameraVertex transform(const Matrix &m, double x, double y, double z, double u, double v) {
    return {m[0] * x + m[1] * y + m[2] * z + m[3], m[4] * x + m[5] * y + m[6] * z + m[7],
            m[8] * x + m[9] * y + m[10] * z + m[11], u, v};
}
inline void triangle(std::vector<Vertex> &out, const std::array<CameraVertex, 3> &input,
                     const Projection &p) {
    const auto clipped = visual_clip::near_triangle(input, p[5],
        [](const CameraVertex& a, const CameraVertex& b, double t) {
            return CameraVertex{a.x + t * (b.x - a.x), a.y + t * (b.y - a.y),
                                a.z + t * (b.z - a.z), a.u + t * (b.u - a.u),
                                a.v + t * (b.v - a.v)};
        });
    const auto count = clipped.size();
    auto add = [&](const CameraVertex &v) {
        const double depth = p[0] / v.z;
        out.push_back({float(v.x * p[1] * depth + p[3]), float(v.y * p[2] * depth + p[4]),
                       float(depth), float(depth), 0xffffffffU, 0xff000000U, float(v.u),
                       float(v.v)});
    };
    for (unsigned i = 1; i + 1 < count; ++i) {
        add(clipped[0]);
        add(clipped[i]);
        add(clipped[i + 1]);
    }
}
inline std::vector<Vertex> flame(const Matrix &m, const Projection &p, double nozzle, double radius,
                                 double body_length, double time, std::uint64_t id) {
    for (double v : m)
        if (!std::isfinite(v))
            throw std::runtime_error("Invalid missile transform");
    for (float v : p)
        if (!std::isfinite(v))
            throw std::runtime_error("Invalid missile projection");
    if (p[0] <= 0 || p[1] == 0 || p[2] == 0 || p[5] <= 0 || !std::isfinite(time) ||
        !std::isfinite(nozzle) || !std::isfinite(radius) || !std::isfinite(body_length) ||
        radius <= 0 || radius > 2 || body_length <= 0 || body_length > 16)
        throw std::runtime_error("Invalid missile exhaust dimensions");
    const double pulse = 1 + .075 * std::sin(time * 89 + double(id % 997));
    const double length = body_length * 2.15 * pulse * exhaust_size_scale,
                 width = std::max(.10, radius * 2.2) * exhaust_size_scale;
    std::vector<Vertex> out;
    out.reserve(36);
    auto quad = [&](const std::array<CameraVertex, 4> &q) {
        triangle(out, {q[0], q[1], q[2]}, p);
        triangle(out, {q[0], q[2], q[3]}, p);
    };
    // Two crossed ribbons retain visible thrust from oblique views. UV padding
    // isolates the flame and nozzle glow in the single authored atlas.
    for (unsigned plane = 0; plane < 2; ++plane) {
        auto vertex = [&](double side, double z, double u, double v) {
            return transform(m, plane ? 0 : side, plane ? side : 0, z, u, v);
        };
        quad({vertex(-width, nozzle, .015625, .0078125), vertex(width, nozzle, .984375, .0078125),
              vertex(width, nozzle + length, .984375, .4921875),
              vertex(-width, nozzle + length, .015625, .4921875)});
    }
    const auto center = transform(m, 0, 0, nozzle, 0, 0);
    const double scale = std::sqrt(m[0] * m[0] + m[4] * m[4] + m[8] * m[8]);
    const double glow = width * 1.5 * scale;
    quad({CameraVertex{center.x - glow, center.y - glow, center.z, .015625, .5078125},
          {center.x + glow, center.y - glow, center.z, .984375, .5078125},
          {center.x + glow, center.y + glow, center.z, .984375, .9921875},
          {center.x - glow, center.y + glow, center.z, .015625, .9921875}});
    return out;
}
inline std::vector<std::uint32_t> texture() {
    std::vector<std::uint32_t> out(64 * 128);
    for (unsigned y = 0; y < 128; ++y)
        for (unsigned x = 0; x < 64; ++x) {
            const double u = (double(x) + .5) / 64 * 2 - 1;
            const double v = (double(y % 64) + .5) / 64;
            double alpha, heat;
            if (y < 64) {
                const double width = .54 * (1 - v) + .04;
                const double d = std::abs(u) / width;
                alpha = std::exp(-d * d * 3.5) * std::pow(1 - v, 1.15) * std::min(1., v * 30);
                heat = std::clamp(1 - v * 1.6 - d * .35, 0., 1.);
            } else {
                const double r2 = u * u + (v * 2 - 1) * (v * 2 - 1);
                alpha = std::exp(-r2 * 7) * std::clamp((1 - r2) * 4, 0., 1.) * .85;
                heat = std::clamp(1 - r2 * 3, 0., 1.);
            }
            if (x == 0 || x == 63 || y % 64 == 0 || y % 64 == 63)
                alpha = 0;
            auto byte = [](double a) { return std::uint32_t(std::clamp(a, 0., 1.) * 255 + .5); };
            out[y * 64 + x] = 255U | (byte(.18 + .8 * heat) << 8) |
                              (byte(.02 + .78 * heat * heat) << 16) |
                              (byte(alpha * exhaust_strength_scale) << 24);
        }
    return out;
}
} // namespace mw34::missiles
