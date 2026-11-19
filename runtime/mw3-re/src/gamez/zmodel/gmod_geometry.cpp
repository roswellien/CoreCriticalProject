#include "gamez/zmodel/gmod_geometry.h"

#include "gamez/zclass/cls_node.h"
#include "gamez/zmath/zmth_matrix.h"
#include "gamez/zmodel/gmod_const.h"
#include "gamez/zmodel/gmod_draw.h"
#include "gamez/zmodel/gmod_fog.h"
#include "gamez/zvideo/zvid_ddd3d.h"
#include "platform/render3d.h"

#include <algorithm>
#include <array>
#include <cfenv>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>
#include <stdexcept>

namespace zmod {
namespace {
class PreserveFloat {
  public:
    PreserveFloat() {
        if (std::fegetenv(&saved_) != 0)
            throw std::runtime_error("Cannot preserve geometry FP state");
    }
    ~PreserveFloat() { std::fesetenv(&saved_); }

  private:
    std::fenv_t saved_;
};

bool raw_model_header_supported(const Model &model,
                                const RigidGeometryEligibility &eligibility) noexcept {
    // Light-bearing/morph/facade producers still have independent effect contracts.
    if (model.count(0) != 0 || model.count(0x1c) || model.count(0x20) || !model.count(0x10) ||
        !model.vertices || !model.polygons || eligibility.overlay || eligibility.second_pass ||
        eligibility.opacity != 1.f)
        return false;
    float scroll_u{}, scroll_v{};
    std::memcpy(&scroll_u, model.header + 0x28, 4);
    std::memcpy(&scroll_v, model.header + 0x2c, 4);
    return scroll_u == 0 && scroll_v == 0;
}

bool raw_polygon_supported(const Polygon &polygon) noexcept {
    const auto *material = polygon.material;
    if (!material || material->alpha != 255 || (material->flags & 4) || polygon.priority ||
        (polygon.flags & 255) < 3 || (polygon.flags & 255) > 64)
        return false;
    if (material->flags & 1) {
        if (!material->texture || !material->texture->surface || !polygon.uvs)
            return false;
        const auto *texture = static_cast<const zvid::D3DTexture *>(material->texture->surface);
        if (texture->type != 1 || texture->handle < 0 ||
            (texture->address_u != 1 && texture->address_u != 3) ||
            (texture->address_v != 1 && texture->address_v != 3))
            return false;
    }
    return true;
}

bool source_supported(Model &model) {
    const RigidGeometryEligibility eligibility{
        draw_state().overlay != 0, draw_state().second_pass != 0, draw_state().opacity};
    if (!raw_model_header_supported(model, eligibility))
        return false;
    for (std::uint32_t index = 0; index < model.count(0x10); ++index) {
        const auto &polygon = model.polygons[index];
        const auto *material = polygon.material;
        if (model.render_geometry && (model.render_materials.size() != model.count(0x10) ||
                                      model.render_materials[index] != material))
            model.invalidate_render_geometry();
        if (!raw_polygon_supported(polygon))
            return false;
    }
    return true;
}

void add_checked_bytes(std::size_t &total, std::size_t count, std::size_t elem_size,
                       const char *overflow_msg) {
    if (elem_size != 0 && count > std::numeric_limits<std::size_t>::max() / elem_size)
        throw std::runtime_error(overflow_msg);
    const std::size_t bytes = count * elem_size;
    if (bytes > std::numeric_limits<std::size_t>::max() - total)
        throw std::runtime_error(overflow_msg);
    total += bytes;
}

std::uint32_t float_bits(float value) noexcept {
    std::uint32_t bits{};
    std::memcpy(&bits, &value, sizeof(bits));
    return bits;
}

bool is_nonfinite_or_subnormal(float value) noexcept {
    const std::uint32_t bits = float_bits(value);
    const std::uint32_t exponent = bits & 0x7f800000u;
    const std::uint32_t mantissa = bits & 0x007fffffu;
    if (exponent == 0x7f800000u)
        return true;
    if (exponent == 0u && mantissa != 0u)
        return true;
    return !std::isfinite(value);
}

bool is_positive_normal(float value) noexcept {
    if (is_nonfinite_or_subnormal(value))
        return false;
    const std::uint32_t bits = float_bits(value);
    return (bits & 0x80000000u) == 0u && (bits & 0x7f800000u) != 0u && value > 0.f;
}

double add_up(double left, double right) noexcept {
    const double sum = left + right;
    if (!std::isfinite(sum))
        return std::numeric_limits<double>::infinity();
    return std::nextafter(sum, std::numeric_limits<double>::infinity());
}

double mul_up(double left, double right) noexcept {
    const double product = left * right;
    if (!std::isfinite(product))
        return std::numeric_limits<double>::infinity();
    return std::nextafter(product, std::numeric_limits<double>::infinity());
}

// Native GPU submission clips every triangle at the far plane, whereas the
// legacy CPU clipper only rejects polygons whose corners are all >= far_z when
// clip.mask & 0x20 and never cuts crossing polygons. Admit stock geometry only
// when every corner of its source AABB is provably < far_z across all finite
// float multiply/add/FMA orders, rounding modes and intermediate FTZ states.
bool far_plane_safe(const cc::geometry::Resource &resource,
                    const platform::ModelDrawContext &context, float clip_far, const platform::Render3D &renderer) {
    if (!resource.source_bounds_valid || !context.model_to_camera)
        return false;
    if (!is_positive_normal(clip_far) || !is_positive_normal(context.far_z) ||
        float_bits(clip_far) != float_bits(context.far_z) || clip_far != context.far_z)
        return false;
    constexpr double kMaxSafeMagnitude = 0.25 * double(std::numeric_limits<float>::max());
    if (double(clip_far) > kMaxSafeMagnitude)
        return false;
    const std::array<float, 3> coeff{context.model_to_camera[2], context.model_to_camera[5],
                                     context.model_to_camera[8]};
    const float translation = context.model_to_camera[11];
    if (is_nonfinite_or_subnormal(translation))
        return false;
    const double trans = double(translation);
    const double trans_abs = std::abs(trans);
    if (trans_abs > kMaxSafeMagnitude)
        return false;
    std::array<double, 3> axis_max{};
    std::array<double, 3> axis_abs{};
    for (std::size_t axis = 0; axis < 3; ++axis) {
        const float min_coord = resource.source_min[axis];
        const float max_coord = resource.source_max[axis];
        if (is_nonfinite_or_subnormal(coeff[axis]) || is_nonfinite_or_subnormal(min_coord) ||
            is_nonfinite_or_subnormal(max_coord) || !(min_coord <= max_coord))
            return false;
        const double c = double(coeff[axis]);
        const double lo = double(min_coord);
        const double hi = double(max_coord);
        if (std::abs(c) > kMaxSafeMagnitude || std::abs(lo) > kMaxSafeMagnitude ||
            std::abs(hi) > kMaxSafeMagnitude)
            return false;
        const double prod_lo = mul_up(c, lo);
        const double prod_hi = mul_up(c, hi);
        axis_max[axis] = c >= 0.0 ? prod_hi : prod_lo;
        const double raw_abs = std::max(std::abs(c * lo), std::abs(c * hi));
        if (!std::isfinite(axis_max[axis]) || !std::isfinite(raw_abs) ||
            raw_abs > kMaxSafeMagnitude)
            return false;
        axis_abs[axis] = std::nextafter(raw_abs, std::numeric_limits<double>::infinity());
    }
    const double support_sum =
        add_up(add_up(axis_max[0], axis_max[1]), add_up(axis_max[2], trans));
    const double abs_sum =
        add_up(add_up(axis_abs[0], axis_abs[1]), add_up(axis_abs[2], trans_abs));
    if (!std::isfinite(support_sum) || !std::isfinite(abs_sum) || abs_sum > kMaxSafeMagnitude)
        return false;
    constexpr double kFloatEpsilon = double(std::numeric_limits<float>::epsilon());
    constexpr double kFloatMinNormal = double(std::numeric_limits<float>::min());
    const double margin = add_up(mul_up(64.0 * kFloatEpsilon, abs_sum), 64.0 * kFloatMinNormal);
    const double max_camera_z = add_up(support_sum, margin);
    if (!std::isfinite(max_camera_z)) return false;
    if (max_camera_z < double(clip_far)) return true;
    // Camera Z never exceeds length(eye). In an authenticated world projection
    // the hardware far plane therefore clips only samples this renderer already
    // discards. Keep every source/FP bound above and the legacy rule elsewhere.
    const unsigned radius = renderer.opaque_world_range();
    if (!radius || double(radius) > double(clip_far)) return false;
    const auto view = zvid::capture_producer_view();
    const auto &p = view.projection;
    return view.present && (view.purpose == platform::ProducerPurpose::MainWorld ||
                            view.purpose == platform::ProducerPurpose::WorldZoom) &&
           p.far_z == context.far_z && p.near_z == context.near_z &&
           p.fx_near == context.fx_near && p.fy_near == context.fy_near &&
           p.cx == context.cx && p.cy == context.cy;

}
} // namespace

bool rigid_source_supported(const Model &model, const RigidGeometryEligibility &eligibility) {
    PreserveFloat preserve;
    if (!raw_model_header_supported(model, eligibility))
        return false;
    const std::uint32_t polygon_count = model.count(0x10);
    for (std::uint32_t index = 0; index < polygon_count; ++index) {
        if (!raw_polygon_supported(model.polygons[index]))
            return false;
    }
    return true;
}

std::size_t preflight_rigid_source_bytes(const Model &model) {
    PreserveFloat preserve;
    const std::uint32_t position_count = model.count(0x14);
    const std::uint32_t normal_count = model.count(0x18);
    const std::uint32_t polygon_count = model.count(0x10);
    if (!model.vertices || !model.polygons || !position_count || position_count > 1'000'000 ||
        !polygon_count || polygon_count > 1'000'000)
        throw std::runtime_error("Geometry registration exceeds supported source bounds");
    std::size_t total_vertices = 0;
    std::size_t total_indices = 0;
    std::vector<cc::geometry::Vertex> poly_vertices;
    poly_vertices.reserve(64);
    for (std::uint32_t polygon_index = 0; polygon_index < polygon_count; ++polygon_index) {
        const auto &polygon = model.polygons[polygon_index];
        const std::uint32_t count = polygon.flags & 255u;
        if (!polygon.vertex_indices || count < 3 || count > 64)
            throw std::runtime_error("Invalid geometry polygon");
        if (total_vertices > 1'000'000 - count)
            throw std::runtime_error("Geometry corner budget exceeded");
        const auto *material = polygon.material;
        if (!material)
            throw std::runtime_error("Invalid geometry polygon");
        const bool textured = (material->flags & 1) != 0;
        if (textured && !polygon.uvs)
            throw std::runtime_error("Invalid geometry polygon");
        const bool has_normals = (polygon.flags & 0x200u) != 0;
        const bool strip = (polygon.flags & 0x400u) != 0;
        poly_vertices.clear();
        for (std::uint32_t corner = count; corner-- > 0;) {
            const auto index = polygon.vertex_indices[corner];
            if (index >= position_count)
                throw std::runtime_error("Geometry position index outside resource");
            cc::geometry::Vertex vertex{};
            vertex.x = model.vertices[3 * index];
            vertex.y = model.vertices[3 * index + 1];
            vertex.z = model.vertices[3 * index + 2];
            if (textured) {
                vertex.u = polygon.uvs[2 * corner];
                vertex.v = polygon.uvs[2 * corner + 1];
            }
            if (has_normals) {
                if (!polygon.normal_indices || !model.normals)
                    throw std::runtime_error("Geometry normal index outside resource");
                const auto normal = polygon.normal_indices[corner];
                if (normal >= normal_count)
                    throw std::runtime_error("Geometry normal index outside resource");
                vertex.nx = model.normals[3 * normal];
                vertex.ny = model.normals[3 * normal + 1];
                vertex.nz = model.normals[3 * normal + 2];
            }
            const std::array<float, 8> attributes{vertex.x,  vertex.y,  vertex.z, vertex.nx,
                                                  vertex.ny, vertex.nz, vertex.u, vertex.v};
            for (float value : attributes) {
                const std::uint32_t bits = float_bits(value);
                if (!std::isfinite(value) || (bits & 0x7f800000u) == 0x7f800000u)
                    throw std::runtime_error("Nonfinite registered geometry");
            }
            poly_vertices.push_back(vertex);
        }
        if (!has_normals) {
            std::array<float, 3> flat{};
            for (std::uint32_t triangle = 2; triangle < count; ++triangle) {
                std::uint32_t i0 = 0, i1 = triangle - 1, i2 = triangle;
                if (strip) {
                    const auto first = triangle - 2;
                    i0 = first + (first & 1U);
                    i1 = first + 1 - (first & 1U);
                }
                const auto &a = poly_vertices[i0];
                const auto &b = poly_vertices[i1];
                const auto &c = poly_vertices[i2];
                const float ax = b.x - a.x, ay = b.y - a.y, az = b.z - a.z;
                const float bx = c.x - a.x, by = c.y - a.y, bz = c.z - a.z;
                const std::array<float, 3> normal{az * by - ay * bz, ax * bz - az * bx,
                                                  ay * bx - ax * by};
                if (strip) {
                    for (std::uint32_t idx : {i0, i1, i2}) {
                        poly_vertices[idx].nx += normal[0];
                        poly_vertices[idx].ny += normal[1];
                        poly_vertices[idx].nz += normal[2];
                    }
                } else if (flat == std::array<float, 3>{}) {
                    flat = normal;
                }
            }
            for (std::uint32_t corner = 0; corner < count; ++corner) {
                auto &vertex = poly_vertices[corner];
                if (!strip) {
                    vertex.nx = flat[0];
                    vertex.ny = flat[1];
                    vertex.nz = flat[2];
                }
                const float length = std::sqrt(vertex.nx * vertex.nx + vertex.ny * vertex.ny +
                                               vertex.nz * vertex.nz);
                if (!std::isfinite(length))
                    throw std::runtime_error("Geometry normal exceeds finite range");
            }
        }
        total_vertices += count;
        total_indices += std::size_t(count - 2) * 3u;
    }
    std::size_t retained_bytes = sizeof(cc::geometry::Resource);
    add_checked_bytes(retained_bytes, total_vertices, sizeof(cc::geometry::Vertex),
                      "Retained geometry byte count overflow");
    add_checked_bytes(retained_bytes, total_indices, sizeof(std::uint32_t),
                      "Retained geometry byte count overflow");
    add_checked_bytes(retained_bytes, polygon_count, sizeof(cc::geometry::Range),
                      "Retained geometry byte count overflow");
    add_checked_bytes(retained_bytes, polygon_count, sizeof(cc::geometry::Material),
                      "Retained geometry byte count overflow");
    add_checked_bytes(retained_bytes, polygon_count, sizeof(const Material *),
                      "Retained geometry byte count overflow");
    return retained_bytes;
}

RegisteredRigidSource register_rigid_source(const Model &model) {
    PreserveFloat preserve;
    (void)preflight_rigid_source_bytes(model);
    const std::uint32_t polygon_count = model.count(0x10);
    std::vector<cc::geometry::Polygon> polygons;
    std::vector<const Material *> material_sources;
    polygons.reserve(polygon_count);
    material_sources.reserve(polygon_count);
    for (std::uint32_t index = 0; index < polygon_count; ++index) {
        const auto &polygon = model.polygons[index];
        const auto slot = index;
        material_sources.push_back(polygon.material);
        polygons.push_back({polygon.flags & 255, polygon.vertex_indices,
                            (polygon.flags & 0x200) ? polygon.normal_indices : nullptr,
                            (polygon.material->flags & 1) ? polygon.uvs : nullptr,
                            bool(polygon.flags & 0x400), bool(polygon.flags & 0x100), slot});
    }
    auto resource = cc::geometry::register_resource(
        model.vertices, model.count(0x14), model.normals, model.count(0x18), polygons);
    return {std::move(resource), std::move(material_sources)};
}

std::vector<cc::geometry::Material> copy_rigid_materials(
    const Model &model, const cc::geometry::Resource &resource) {
    PreserveFloat preserve;
    if (!model.polygons)
        throw std::runtime_error("Geometry model polygons missing");
    const std::uint32_t polygon_count = model.count(0x10);
    std::vector<cc::geometry::Material> materials;
    materials.reserve(resource.ranges.size());
    for (const auto &range : resource.ranges) {
        if (range.polygon >= polygon_count || !model.polygons[range.polygon].material)
            throw std::runtime_error("Geometry range polygon outside source model");
        const auto &source = *model.polygons[range.polygon].material;
        cc::geometry::Material material;
        material.color = 0xff000000;
        unsigned shift = 16;
        for (float channel : {source.r, source.g, source.b}) {
            if (!std::isfinite(channel))
                throw std::runtime_error("Nonfinite geometry material");
            material.color |= std::uint32_t(std::clamp(channel, 0.f, 255.f)) << shift;
            shift -= 8;
        }
        if (source.flags & 1) {
            if (!source.texture || !source.texture->surface)
                throw std::runtime_error("Textured geometry material missing surface");
            const auto &texture = *static_cast<const zvid::D3DTexture *>(source.texture->surface);
            material.texture = texture.handle;
            material.address_u = std::uint8_t(texture.address_u);
            material.address_v = std::uint8_t(texture.address_v);
        }
        materials.push_back(material);
    }
    return materials;
}

bool submit_geometry(zcls::Node &node) {
    auto *renderer = zvid::render3d();
    if (!renderer || renderer->geometry_mode() == cc::geometry::Mode::legacy)
        return false;
    PreserveFloat preserve;
    auto &model = *node.model;
    const auto unsupported = [&] {
        renderer->note_cpu_model_geometry();
        if (renderer->geometry_mode() == cc::geometry::Mode::gpu)
            throw std::runtime_error("Strict GPU geometry: unsupported model family");
        return false;
    };
    auto &stack = zmth::matrix_stack();
    if (!stack.top) return unsupported();
    const auto &projection = zmth::projection();
    platform::ModelDrawContext context;
    context.node = &node;
    context.model_to_world = stack.below().m;
    context.model_to_camera = stack.matrix().m;
    context.near_z = projection.near_z;
    context.clip_near = draw_state().clip.near_z;
    context.far_z = projection.far_z;
    context.fx_near = projection.fx_near;
    context.fy_near = projection.fy_near;
    context.cx = projection.cx;
    context.cy = projection.cy;
    context.opacity = draw_state().opacity;
    const Lighting& tint = lighting();
    if (tint.tint_on) {
      std::copy_n(tint.tint, 3, context.damage_tint_rgb);
      context.damage_tint_weight = tint.tint_weight;
    }
    context.ordinary = model.count(0) == 0;
    context.morphing = model.count(0x20) != 0;
    context.overlay = draw_state().overlay != 0;
    context.source_vertices = model.count(0x14);
    context.source_polygons = model.count(0x10);
    const auto &source_fog = render_fog();
    cc::geometry::Fog fog_state;
    fog_state.enabled = source_fog.on != 0;
    std::copy_n(render_fog_color(), 3, fog_state.color.begin());
    fog_state.near_range = source_fog.near_range;
    fog_state.inverse_range = source_fog.inv_range;
    fog_state.low_altitude = source_fog.alt_low;
    fog_state.inverse_altitude = source_fog.inv_alt;
    const auto edge = render_fog_edge();
    fog_state.edge_start = edge.start;
    fog_state.edge_inverse_range = edge.inverse_range;
    // Prepared assets own their materials. Admit their rigid draw before stock
    // registration and all native vertex/polygon loops, retaining effect-bearing
    // producers until their side effects have an explicit GPU contract.
    if (context.ordinary && !context.morphing && !context.overlay && !model.count(0x1c) &&
        !draw_state().second_pass) {
        if (zvid::submit_prepared_geometry_for_current_view(renderer, context,
                                                             fog_state) ==
            cc::geometry::Submission::submitted)
            return true;
    }
    // Stock model packets do not carry sky state; keep the original TL producer.
    if (zvid::draw_state().native_sky) {
        // Static baking also indexes cached normals with vertex shading off.
        if (model.count(0x14) > std::uint32_t(kModelVerts) ||
            model.count(0x18) > std::uint32_t(kModelVerts))
            throw std::runtime_error("Legacy model draw buffer capacity exceeded");
        return unsupported();
    }
    if (!source_supported(model))
        return unsupported();
    if (!model.render_geometry) {
        auto registered = register_rigid_source(model);
        model.render_geometry = std::move(registered.resource);
        model.render_materials = std::move(registered.original_materials);
    }
    if (!far_plane_safe(*model.render_geometry, context, draw_state().clip.far_z, *renderer)) {
        // Static baking also indexes cached normals with vertex shading off.
        if (model.count(0x14) > std::uint32_t(kModelVerts) ||
            model.count(0x18) > std::uint32_t(kModelVerts))
            throw std::runtime_error("Legacy model draw buffer capacity exceeded");
        return unsupported();
    }
    const auto materials = copy_rigid_materials(model, *model.render_geometry);
    if (zvid::submit_model_geometry_for_current_view(
            renderer, model.render_geometry, context, materials, fog_state) !=
        cc::geometry::Submission::submitted)
        return unsupported();
    return true;
}
} // namespace zmod
