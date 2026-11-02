#pragma once
#include "camera_history.hpp"
#include "world_binding.hpp"
#include <type_traits>
#include <vector>

namespace mw34::temporal {
inline bool jitter_enabled() {
    static const bool value = [] {
        const char *setting = std::getenv("MW34_TEMPORAL_JITTER");
        if (!setting || !*setting || !std::strcmp(setting, "0"))
            return false;
        if (std::strcmp(setting, "1"))
            throw std::runtime_error("MW34_TEMPORAL_JITTER must be 0 or 1");
        if (!enabled())
            throw std::runtime_error("Temporal jitter requires temporal inputs");
        return true;
    }();
    return value;
}
struct StaticSource {
    std::uint64_t epoch{}, texture_version{}, frame{}, load_epoch{};
    bool previous_static{};
    std::shared_ptr<const mw34::world::SourceCharge> charge;
    std::uint32_t node{}, mesh{}, polygon{}, texture{};
    std::uint32_t cell_owner{}, cell{}, record{}, route{};
    std::array<unsigned, 3> offset{};
    std::shared_ptr<const mw34::world::SourceBytes> mesh_bytes, node_bytes;
    std::array<float, 12> world{};
    bool unchanged(const StaticSource &previous) const {
        return load_epoch == previous.load_epoch && cell_owner == previous.cell_owner &&
               cell == previous.cell && record == previous.record && route == previous.route &&
               offset == previous.offset && epoch == previous.epoch && node == previous.node &&
               mesh == previous.mesh && polygon == previous.polygon &&
               texture == previous.texture && texture_version == previous.texture_version &&
               world == previous.world && mesh_bytes && mesh_bytes == previous.mesh_bytes &&
               node_bytes && node_bytes == previous.node_bytes;
    }
};
inline float halton(unsigned index, unsigned base) {
    float result = 0, weight = 1;
    while (index) {
        weight /= float(base);
        result += weight * float(index % base);
        index /= base;
    }
    return result;
}
inline std::array<float, 2> jitter(unsigned phase, unsigned output_width, unsigned internal_width) {
    if (!output_width || !internal_width)
        throw std::runtime_error("Invalid jitter dimensions");
    const double ratio = double(output_width) / internal_width;
    const unsigned count = unsigned(std::ceil(8 * ratio * ratio));
    const unsigned index = phase % count + 1;
    return {halton(index, 2) - .5f, halton(index, 3) - .5f};
}
using Matrix = std::array<float, 12>;
inline Matrix camera_world(const Snapshot &view) {
    Matrix result{};
    for (unsigned row = 0; row < 3; ++row)
        for (unsigned col = 0; col < 4; ++col)
            result[row * 4 + col] = std::bit_cast<float>(view.camera[col * 3 + row]);
    return result;
}
inline Matrix inverse_affine(const Matrix &matrix) {
    const double a = matrix[0], b = matrix[1], c = matrix[2], d = matrix[4], e = matrix[5],
                 f = matrix[6], g = matrix[8], h = matrix[9], i = matrix[10];
    const double determinant = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g);
    if (!std::isfinite(determinant) || std::abs(determinant) < 1e-12)
        throw std::runtime_error("Singular temporal camera");
    const double inverse[9]{(e * i - f * h) / determinant, (c * h - b * i) / determinant,
                            (b * f - c * e) / determinant, (f * g - d * i) / determinant,
                            (a * i - c * g) / determinant, (c * d - a * f) / determinant,
                            (d * h - e * g) / determinant, (b * g - a * h) / determinant,
                            (a * e - b * d) / determinant};
    Matrix result{};
    for (unsigned row = 0; row < 3; ++row) {
        double translation = 0;
        for (unsigned col = 0; col < 3; ++col) {
            result[row * 4 + col] = float(inverse[row * 3 + col]);
            translation -= inverse[row * 3 + col] * matrix[col * 4 + 3];
        }
        result[row * 4 + 3] = float(translation);
    }
    return result;
}
inline Matrix previous_from_current(const Snapshot &current, const Snapshot &previous) {
    const auto current_world = camera_world(current);
    auto previous_linear = camera_world(previous);
    std::array<double, 3> displacement{};
    for (unsigned axis = 0; axis < 3; ++axis) {
        // Subtract the stored origins before reducing to GPU float precision.
        // Adding an absolute map origin to each fragment can move a visible
        // point behind the previous near plane through cancellation alone.
        displacement[axis] = double(current_world[axis * 4 + 3]) -
                             double(previous_linear[axis * 4 + 3]);
        previous_linear[axis * 4 + 3] = 0;
    }
    const auto inverse_linear = inverse_affine(previous_linear);
    Matrix result{};
    for (unsigned row = 0; row < 3; ++row) {
        for (unsigned col = 0; col < 3; ++col) {
            double coefficient = 0;
            for (unsigned axis = 0; axis < 3; ++axis)
                coefficient += double(inverse_linear[row * 4 + axis]) *
                               double(current_world[axis * 4 + col]);
            result[row * 4 + col] = float(coefficient);
        }
        double translation = 0;
        for (unsigned axis = 0; axis < 3; ++axis)
            translation += double(inverse_linear[row * 4 + axis]) * displacement[axis];
        result[row * 4 + 3] = float(translation);
    }
    return result;
}
} // namespace mw34::temporal
