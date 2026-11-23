#pragma once
#include "donor_retarget.hpp"
#include "visual_clip.hpp"
#include <bit>
#include <cstdint>
#include <cstring>
#include <limits>
#include <optional>
#include <set>
#include <string_view>
#include <tuple>
#include <type_traits>
#include <utility>

namespace mw34::weapon_visuals {
// Immutable command snapshots retain this token. Address reuse is insufficient
// to authorize a snapshot from an earlier beam lifetime.
struct Identity {
    unsigned beam{}, actor{}, weapon{}, definition{}, position{}, direction{};
    std::uint64_t generation{};
    bool operator==(const Identity &) const = default;
};
inline bool current(const Identity &snapshot, const Identity &live) {
    return snapshot.beam && snapshot.actor && snapshot.weapon && snapshot.definition &&
           snapshot.position && snapshot.direction && snapshot.generation && snapshot == live;
}

// Shear only the source end of the original segment. Its hit endpoint and its
// transverse geometry stay fixed; this matrix is used only by host rendering.
inline donor::Mat attachment_transform(donor::Vec source, donor::Vec end, donor::Vec muzzle) {
    for (const auto &point : {source, end, muzzle})
        for (double value : point)
            if (!std::isfinite(value) || std::abs(value) > 1000000)
                throw std::runtime_error("Weapon visuals: invalid segment point");
    const auto axis = donor::sub(end, source);
    const double length_squared = donor::dot(axis, axis);
    if (length_squared < 1e-12)
        throw std::runtime_error("Weapon visuals: zero-length segment");
    const auto normal = donor::scale(axis, 1 / length_squared);
    const auto offset = donor::sub(muzzle, source);
    auto result = donor::identity();
    for (unsigned row = 0; row < 3; ++row) {
        for (unsigned column = 0; column < 3; ++column)
            result[row * 4 + column] -= offset[row] * normal[column];
        result[row * 4 + 3] = offset[row] * (1 + donor::dot(source, normal));
    }
    return result;
}

struct Vertex {
    double x{}, y{}, z{}, u{}, v{};
    std::array<double, 4> color{}, fog{};
};
struct TlVertex {
    float x, y, z, rhw;
    std::uint32_t color, specular;
    float u, v;
};
static_assert(sizeof(TlVertex) == 32);
inline std::array<double, 4> channels(std::uint32_t word) {
    return {double(word & 255), double((word >> 8) & 255), double((word >> 16) & 255),
            double(word >> 24)};
}
inline std::uint32_t packed(const std::array<double, 4> &values) {
    std::uint32_t result = 0;
    for (unsigned i = 0; i < 4; ++i) {
        if (!std::isfinite(values[i]))
            throw std::runtime_error("Invalid beam attribute");
        result |= std::uint32_t(std::clamp(values[i], 0., 255.)) << (8 * i);
    }
    return result;
}
inline Vertex interpolate(const Vertex &a, const Vertex &b, double t) {
    Vertex v{a.x + t * (b.x - a.x), a.y + t * (b.y - a.y), a.z + t * (b.z - a.z),
             a.u + t * (b.u - a.u), a.v + t * (b.v - a.v)};
    for (unsigned i = 0; i < 4; ++i) {
        v.color[i] = a.color[i] + t * (b.color[i] - a.color[i]);
        v.fog[i] = a.fog[i] + t * (b.fog[i] - a.fog[i]);
    }
    return v;
}
inline std::vector<TlVertex> project(const std::vector<Vertex> &polygon,
                                     const std::array<float, 6> &p) {
    if (polygon.size() < 3 || polygon.size() > 128)
        throw std::runtime_error("Invalid beam polygon size");
    for (auto f : p)
        if (!std::isfinite(f))
            throw std::runtime_error("Invalid beam projection");
    if (p[0] <= 0 || p[1] == 0 || p[2] == 0 || p[5] <= 0)
        throw std::runtime_error("Invalid beam projection");
    for (const auto &v : polygon)
        for (double f : {v.x, v.y, v.z, v.u, v.v})
            if (!std::isfinite(f))
                throw std::runtime_error("Nonfinite beam vertex");
    std::vector<TlVertex> output;
    for (unsigned i = 1; i + 1 < polygon.size(); ++i) {
        const auto clipped = visual_clip::near_triangle(
            std::array<Vertex, 3>{polygon[0], polygon[i], polygon[i + 1]}, p[5], interpolate);
        auto add = [&](const Vertex &v) {
            const double depth = p[0] / v.z;
            output.push_back({float(v.x * p[1] * depth + p[3]), float(v.y * p[2] * depth + p[4]),
                              float(depth), float(depth), packed(v.color), packed(v.fog),
                              float(v.u), float(v.v)});
        };
        for (unsigned k = 1; k + 1 < clipped.size(); ++k) {
            add(clipped[0]);
            add(clipped[k]);
            add(clipped[k + 1]);
        }
    }
    return output;
}

inline bool arm_retired(std::string_view control, unsigned damage_mask, bool root_hidden,
                        std::optional<bool> mesh_visible, std::optional<bool> control_visible) {
    const unsigned bit = control == "rhand" ? 1U : control == "lhand" ? 2U : 0U;
    return (damage_mask & bit) || (control_visible && !*control_visible) ||
           (!root_hidden && mesh_visible && !*mesh_visible);
}
// Target, scene, role, physical camera, projection, attached/external policy,
// and authenticated original camera producer distinguish views in one frame.
inline std::optional<std::uint32_t> gpu_colour(const std::vector<Vertex> &vertices,
                                               double near_plane, bool modern_view) {
    if (modern_view || vertices.empty())
        return {};
    if (!std::isfinite(near_plane) || near_plane <= 0)
        throw std::runtime_error("Weapon visuals: invalid GPU near plane");
    const auto color = packed(vertices.front().color);
    double magnitude = 1;
    for (const auto &vertex : vertices)
        for (double value : {vertex.x, vertex.y, vertex.z}) {
            if (!std::isfinite(value))
                throw std::runtime_error("Weapon visuals: nonfinite GPU vertex");
            magnitude = std::max(magnitude, std::abs(value));
        }
    const double margin = std::max(1e-4, magnitude * 32 * std::numeric_limits<float>::epsilon());
    for (const auto &vertex : vertices)
        if (vertex.z <= near_plane + margin || packed(vertex.color) != color ||
            packed(vertex.fog) != 0xff000000U)
            return {};
    return color;
}
using View = std::tuple<unsigned, std::uint64_t, unsigned, donor::Mat, std::array<float, 6>,
                        unsigned, unsigned>;
inline auto identity_key(const Identity &id) {
    return std::tuple{id.beam,     id.actor,     id.weapon,    id.definition,
                      id.position, id.direction, id.generation};
}
enum class Status { current, retired, invalid };
template <class Command> struct Composition {
    using Source = std::remove_cvref_t<decltype(std::declval<Command>().weapon_visual)>;
    std::vector<Command> commands;
    std::vector<Source> observations;
    std::vector<Identity> retired;
};
// 57DEC0 compares the signed IEEE words of the first TL vertex's reciprocal
// depth. Preserve existing equal-key order, and sort only this actual flush.
template <class Command> std::int32_t deferred_depth(const Command &command) {
    if (command.kind != Command::Draw || command.vertices.size() < 32)
        throw std::runtime_error("Weapon visuals: non-draw inside deferred flush");
    std::int32_t key;
    std::memcpy(&key, command.vertices.data() + 8, 4);
    return key;
}
template <class Command, class Resolve>
Composition<Command> compose_deferred(const std::vector<Command> &original, Resolve resolve) {
    using Source = typename Composition<Command>::Source;
    Composition<Command> output;
    std::vector<Command> batch;
    std::vector<Source> seeds;
    std::set<std::pair<decltype(identity_key(Identity{})), View>> emitted;
    View view{};
    bool open = false;
    auto status = [&](const Source &source) {
        if (!source || !current(source->identity, source->identity))
            throw std::runtime_error("Weapon visuals: invalid immutable source token");
        const auto state = resolve(source->identity);
        if (state == Status::invalid)
            throw std::runtime_error("Weapon visuals: required live source identity changed");
        if (state == Status::retired)
            output.retired.push_back(source->identity);
        return state;
    };
    auto finish = [&] {
        std::vector<Command> pending;
        bool adapted = false;
        for (const auto &command : batch) {
            if (!command.weapon_visual) {
                pending.push_back(command);
                continue;
            }
            const auto &source = command.weapon_visual;
            if (status(source) == Status::retired)
                continue;
            if (source->view != view)
                throw std::runtime_error("Weapon visuals: source escaped its captured view");
            if (std::find(seeds.begin(), seeds.end(), source) == seeds.end())
                throw std::runtime_error(
                    "Weapon visuals: current source has no complete replacement");
            if (!source->external)
                pending.push_back(command);
        }
        for (const auto &source : seeds) {
            if (status(source) == Status::retired)
                continue;
            if (!emitted.emplace(identity_key(source->identity), source->view).second)
                continue;
            output.observations.push_back(source);
            if (!source->external)
                continue;
            adapted = true;
            for (const auto &command : source->replacement) {
                if (command.weapon_visual || command.weapon_visual_seed ||
                    command.weapon_visual_end)
                    throw std::runtime_error("Weapon visuals: recursive replacement ownership");
                (void)deferred_depth(command);
                pending.push_back(command);
            }
        }
        if (adapted)
            std::stable_sort(pending.begin(), pending.end(), [](const auto &a, const auto &b) {
                return deferred_depth(a) < deferred_depth(b);
            });
        output.commands.insert(output.commands.end(), pending.begin(), pending.end());
        batch.clear();
        seeds.clear();
        open = false;
    };
    for (const auto &command : original) {
        if (command.weapon_visual_seed) {
            if (!command.weapon_visual)
                throw std::runtime_error("Weapon visuals: missing view marker");
            if (command.weapon_visual_end) {
                if (!open || command.weapon_visual->view != view)
                    throw std::runtime_error("Weapon visuals: mismatched deferred view boundary");
                finish();
            } else {
                if (!open) {
                    view = command.weapon_visual->view;
                    open = true;
                }
                if (command.weapon_visual->view != view)
                    throw std::runtime_error("Weapon visuals: mixed deferred view seeds");
                seeds.push_back(command.weapon_visual);
            }
        } else if (open)
            batch.push_back(command);
        else if (command.weapon_visual) {
            if (status(command.weapon_visual) != Status::retired)
                throw std::runtime_error("Weapon visuals: current source outside deferred view");
        } else
            output.commands.push_back(command);
    }
    if (open)
        throw std::runtime_error("Weapon visuals: incomplete deferred view");
    return output;
}
} // namespace mw34::weapon_visuals
