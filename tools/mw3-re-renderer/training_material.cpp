#include "training_material.hpp"

#include "vk_scene.hpp"

#include <charconv>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <stdexcept>

namespace cc_mw3_re {
namespace {

namespace vk = mw34::vkscene;

std::array<float, 12> row_vectors_to_rows(const float *matrix) {
    return {matrix[0], matrix[3],  matrix[6], matrix[9], matrix[1], matrix[4],
            matrix[7], matrix[10], matrix[2], matrix[5], matrix[8], matrix[11]};
}

float transform(const std::array<float, 12> &matrix, const float *vertex, int row) {
    const auto *values = matrix.data() + row * 4;
    return ((values[0] * vertex[0] + values[1] * vertex[1]) + values[2] * vertex[2]) + values[3];
}

bool close(float left, float right, float tolerance) {
    return std::isfinite(left) && std::isfinite(right) && std::abs(left - right) <= tolerance;
}

} // namespace

TrainingMaterial::TrainingMaterial(const sdlfe::CoreCriticalOptions &options)
    : node(options.node), texture(options.texture), probe(options.list_surfaces) {
    const auto &mode = options.lighting;
    enabled = mode == "flat" || mode == "normal";
    if (!enabled) {
        if (!mode.empty() && mode != "off") {
            throw std::runtime_error("--cc-lighting must be off, flat or normal");
        }
        if (!node.empty() || !texture.empty() || !options.albedo_hash.empty() ||
            !options.normal_map.empty()) {
            throw std::runtime_error("A material selection requires --cc-lighting flat or normal");
        }
        return;
    }

    const auto &hash = options.albedo_hash;
    const auto result = std::from_chars(hash.data(), hash.data() + hash.size(), albedo_hash, 16);
    if (node.empty() || node.size() > 24 || texture.empty() || texture.size() > 20 ||
        hash.size() != 16 || result.ec != std::errc{} || result.ptr != hash.data() + hash.size()) {
        throw std::runtime_error(
            "Lighting requires --cc-node, --cc-texture and --cc-albedo-hash (16 hex digits)");
    }
    if (mode == "flat") {
        if (!options.normal_map.empty()) {
            throw std::runtime_error("--cc-normal-map requires --cc-lighting normal");
        }
        return;
    }

    if (options.normal_map.empty()) {
        throw std::runtime_error("--cc-lighting normal requires --cc-normal-map");
    }
    std::ifstream input(std::filesystem::u8path(options.normal_map), std::ios::binary);
    constexpr std::string_view expected_magic{"BWNRM2\0\0", 8};
    char magic[expected_magic.size()]{};
    if (!input.read(magic, sizeof(magic)) ||
        std::string_view(magic, sizeof(magic)) != expected_magic) {
        throw std::runtime_error("Expected a BWNRM2 normal-map sidecar");
    }
    input.seekg(0);
    auto pack = mw34::materials::read_normals(input, {texture});
    if (pack.images.size() != 1 || pack.bindings[0] != 0) {
        throw std::runtime_error(
            "Expected one bound normal image for the selected Training texture");
    }
    auto &normal = pack.images[0];
    normal_width = normal.width;
    normal_height = normal.height;
    normal_pixels = std::move(normal.pixels);
}

std::string_view node_name(const platform::ModelSurface &surface) {
    return {surface.node_name, strnlen(surface.node_name, 24)};
}

std::string_view texture_name(const platform::ModelSurface &surface) {
    return {surface.texture_name, strnlen(surface.texture_name, 20)};
}

std::shared_ptr<const vk::ModelInstance>
model_for_draw(const platform::ModelSurface &surface, platform::Primitive primitive,
               const platform::TLVertex *vertices, int count, const std::array<int, 4> &viewport,
               unsigned width, unsigned height) {
    if (count < 3 || count != surface.count || !surface.positions ||
        (primitive != platform::Primitive::kFan && primitive != platform::Primitive::kStrip)) {
        return {};
    }
    const auto camera = row_vectors_to_rows(surface.model_to_camera);
    const float *const a = surface.positions + 3 * surface.vertex_indices[count - 1];
    const float *const b = surface.positions + 3 * surface.vertex_indices[count - 2];
    const float *const c = surface.positions + 3 * surface.vertex_indices[count - 3];
    const std::array<float, 3> face{(a[1] - b[1]) * (c[2] - b[2]) - (a[2] - b[2]) * (c[1] - b[1]),
                                    (a[2] - b[2]) * (c[0] - b[0]) - (a[0] - b[0]) * (c[2] - b[2]),
                                    (a[0] - b[0]) * (c[1] - b[1]) - (a[1] - b[1]) * (c[0] - b[0])};
    std::vector<vk::ModelVertex> polygon;
    polygon.reserve(count);
    for (int i = 0; i < count; ++i) {
        const int source = count - 1 - i;
        const float *position = surface.positions + 3 * surface.vertex_indices[source];
        const float *normal = surface.normal_indices && surface.normals
                                  ? surface.normals + 3 * surface.normal_indices[source]
                                  : face.data();
        const float z = transform(camera, position, 2);
        if (!(z > surface.near_z && z < surface.far_z)) {
            return {};
        }
        const float depth = surface.near_z / z;
        const float x = (surface.fx_near * transform(camera, position, 0)) * depth + surface.cx;
        const float y = (surface.fy_near * transform(camera, position, 1)) * depth + surface.cy;
        const auto &actual = vertices[i];
        // An ordinary clipped, split or depth-biased draw must stay ordinary.
        if (!close(actual.sx, x, .02f) || !close(actual.sy, y, .02f) ||
            !close(actual.sz, depth, .00001f) || !close(actual.rhw, depth, .00001f)) {
            return {};
        }
        const float length = std::hypot(normal[0], normal[1], normal[2]);
        if (!std::isfinite(length) || length <= 0) {
            return {};
        }
        polygon.push_back({position[0], position[1], position[2], normal[0] / length,
                           normal[1] / length, normal[2] / length, actual.tu, actual.tv});
    }

    auto mesh = std::make_shared<vk::ModelGeometry>();
    for (int i = 0; i + 2 < count; ++i) {
        if (primitive == platform::Primitive::kFan) {
            mesh->vertices.insert(mesh->vertices.end(),
                                  {polygon[0], polygon[i + 1], polygon[i + 2]});
        } else {
            mesh->vertices.insert(mesh->vertices.end(),
                                  {polygon[i + (i & 1)], polygon[i + 1 - (i & 1)], polygon[i + 2]});
        }
    }
    mesh->hash = mw34::materials::normal_hash(mesh->vertices.data(),
                                              mesh->vertices.size() * sizeof(vk::ModelVertex));
    mesh->key = mesh->hash;

    auto model = std::make_shared<vk::ModelInstance>();
    const auto world = row_vectors_to_rows(surface.model_to_world);
    std::array<double, 16> homogeneous{};
    std::copy(world.begin(), world.end(), homogeneous.begin());
    homogeneous[15] = 1;
    try {
        model->sun_normal = mw34::sun::normal_matrix(homogeneous);
    } catch (const std::runtime_error &) {
        return {};
    }
    model->sun_world = world;
    model->geometry = std::move(mesh);
    model->camera = camera;
    const float sx = float(width) / viewport[2], sy = float(height) / viewport[3];
    // Core Critical's model shader adds a half-pixel. The SDL TL control does not.
    model->projection = {surface.near_z,
                         surface.fx_near * sx,
                         surface.fy_near * sy,
                         (surface.cx - viewport[0]) * sx - .5f,
                         (surface.cy - viewport[1]) * sy - .5f,
                         surface.far_z};
    model->world = model->sun_eligible = true;
    return model;
}

} // namespace cc_mw3_re
