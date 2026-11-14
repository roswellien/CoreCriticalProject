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

bool source_supported(Model &model) {
    // Light-bearing/morph/facade producers still have independent effect contracts.
    if (model.count(0) != 0 || model.count(0x1c) || model.count(0x20) || !model.count(0x10) ||
        !model.vertices || !model.polygons || draw_state().overlay || draw_state().second_pass ||
        draw_state().opacity != 1.f)
        return false;
    float scroll_u{}, scroll_v{};
    std::memcpy(&scroll_u, model.header + 0x28, 4);
    std::memcpy(&scroll_v, model.header + 0x2c, 4);
    if (scroll_u != 0 || scroll_v != 0)
        return false;
    for (std::uint32_t index = 0; index < model.count(0x10); ++index) {
        const auto &polygon = model.polygons[index];
        const auto *material = polygon.material;
        if (model.render_geometry && (model.render_materials.size() != model.count(0x10) ||
                                      model.render_materials[index] != material))
            model.invalidate_render_geometry();
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
    }
    return true;
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
                    const platform::ModelDrawContext &context, float clip_far) noexcept {
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
    return std::isfinite(max_camera_z) && max_camera_z < double(clip_far);
}
} // namespace

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
    context.ordinary = model.count(0) == 0;
    context.morphing = model.count(0x20) != 0;
    context.overlay = draw_state().overlay != 0;
    context.source_vertices = model.count(0x14);
    context.source_polygons = model.count(0x10);
    const auto &source_fog = fog();
    cc::geometry::Fog fog_state;
    fog_state.enabled = source_fog.on != 0;
    std::copy_n(source_fog.color, 3, fog_state.color.begin());
    fog_state.near_range = source_fog.near_range;
    fog_state.inverse_range = source_fog.inv_range;
    fog_state.low_altitude = source_fog.alt_low;
    fog_state.inverse_altitude = source_fog.inv_alt;
    // Prepared assets own their materials. Admit their rigid draw before stock
    // registration and all native vertex/polygon loops, retaining effect-bearing
    // producers until their side effects have an explicit GPU contract.
    if (context.ordinary && !context.morphing && !context.overlay && !model.count(0x1c) &&
        !draw_state().second_pass && context.opacity == 1.f &&
        renderer->submit_prepared_geometry(context, fog_state) ==
            cc::geometry::Submission::submitted)
      return true;
    if (!source_supported(model))
        return unsupported();
    if (!model.render_geometry) {
        std::vector<cc::geometry::Polygon> polygons;
        std::vector<const Material *> material_sources;
        polygons.reserve(model.count(0x10));
        for (std::uint32_t index = 0; index < model.count(0x10); ++index) {
            const auto &polygon = model.polygons[index];
            const auto slot = index;
            material_sources.push_back(polygon.material);
            polygons.push_back({polygon.flags & 255, polygon.vertex_indices,
                                (polygon.flags & 0x200) ? polygon.normal_indices : nullptr,
                                (polygon.material->flags & 1) ? polygon.uvs : nullptr,
                                bool(polygon.flags & 0x400), bool(polygon.flags & 0x100), slot});
        }
        model.render_geometry = cc::geometry::register_resource(
            model.vertices, model.count(0x14), model.normals, model.count(0x18), polygons);
        model.render_materials = std::move(material_sources);
    }
    if (!far_plane_safe(*model.render_geometry, context, draw_state().clip.far_z)) {
        // Static baking also indexes cached normals with vertex shading off.
        if (model.count(0x14) > std::uint32_t(kModelVerts) ||
            model.count(0x18) > std::uint32_t(kModelVerts))
            throw std::runtime_error("Legacy model draw buffer capacity exceeded");
        return unsupported();
    }
    std::vector<cc::geometry::Material> materials;
    materials.reserve(model.render_geometry->ranges.size());
    for (const auto &range : model.render_geometry->ranges) {
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
            const auto &texture = *static_cast<const zvid::D3DTexture *>(source.texture->surface);
            material.texture = texture.handle;
            material.address_u = std::uint8_t(texture.address_u);
            material.address_v = std::uint8_t(texture.address_v);
        }
        materials.push_back(material);
    }
    if (renderer->submit_model_geometry(model.render_geometry, context, materials, fog_state) !=
        cc::geometry::Submission::submitted)
        return unsupported();
    return true;
}
} // namespace zmod
