#include "frontend/core_critical/renderer/geometry/resource.hpp"
#include "gamez/zclass/cls_node.h"
#include "gamez/zmath/zmth_matrix.h"
#include "gamez/zmodel/gmod_const.h"
#include "gamez/zmodel/gmod_draw.h"
#include "gamez/zmodel/gmod_geometry.h"
#include "gamez/zvideo/zvid_ddd3d.h"

#include <cfenv>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string_view>
#include <utility>

void require(bool value, const char *message) {
    if (!value)
        throw std::runtime_error(message);
}

struct Renderer : platform::Render3D {
    cc::geometry::Mode mode = cc::geometry::Mode::partial;
    std::shared_ptr<const cc::geometry::Resource> submitted;
    unsigned legacy_draws{}, unsupported{};
    bool accept = true;
    bool prepared = false;
    cc::geometry::Submission submit_prepared_geometry(const platform::ModelDrawContext &context,
                                                      const cc::geometry::Fog &) override {
      if (!prepared) return cc::geometry::Submission::unsupported;
      require(context.source_vertices == 3 && context.source_polygons == 1,
              "Early prepared source work was not accounted for");
      return cc::geometry::Submission::submitted;
    }
    cc::geometry::Mode geometry_mode() const override { return mode; }
    cc::geometry::Submission submit_model_geometry(
        std::shared_ptr<const cc::geometry::Resource> source, const platform::ModelDrawContext &,
        const std::vector<cc::geometry::Material> &materials, const cc::geometry::Fog &) override {
        require(materials.size() == source->ranges.size(), "Material ownership missing");
        std::fesetround(FE_DOWNWARD);
        std::feraiseexcept(FE_INVALID);
        if (!accept)
            return cc::geometry::Submission::unsupported;
        submitted = std::move(source);
        return cc::geometry::Submission::submitted;
    }
    void note_cpu_model_geometry() override { ++unsupported; }
    int32_t create_texture(int, int, const uint8_t *, uint8_t) override { return 0; }
    void release_texture(int32_t) override {}
    void update_texture(int32_t, int, int, const uint8_t *) override {}
    void set_viewport(int, int, int, int) override {}
    void clear(bool, uint8_t, uint8_t, uint8_t) override {}
    void begin_scene() override {}
    void end_scene() override {}
    void draw(platform::Primitive, const platform::TLVertex *, int,
              const platform::DrawState &) override {
        ++legacy_draws;
    }
    void set_fog_color(uint8_t, uint8_t, uint8_t) override {}
    void present() override {}
};

struct MaterialOrdinalRenderer : Renderer {
    zcls::Node *expected_node{};
    std::vector<const zmod::Material *> expected_materials;
    std::vector<uint32_t> expected_colors;
    bool throw_after_submission{};

    cc::geometry::Submission submit_model_geometry(
        std::shared_ptr<const cc::geometry::Resource> source,
        const platform::ModelDrawContext &context,
        const std::vector<cc::geometry::Material> &materials,
        const cc::geometry::Fog &fog) override {
        const auto count = expected_materials.size();
        const auto &model = *expected_node->model;
        require(context.node == expected_node && source == model.render_geometry &&
                    source->source_vertices == 3 && context.source_vertices == 3 &&
                    source->source_polygons == count && context.source_polygons == count,
                "Repeated-material producer lost source ownership or counts");
        require(source->ranges.size() == count && materials.size() == count,
                "Repeated-material original polygon range/material count changed");
        require(source->vertices.size() == count * 3 && source->indices.size() == count * 3,
                "Repeated-material triangle corner/index count changed");
        require(model.render_materials == expected_materials,
                "Repeated-material producer changed original material pointers");
        for (std::size_t index = 0; index < count; ++index) {
            const auto &range = source->ranges[index];
            require(range.polygon == index && range.material_slot == index &&
                        range.first == index * 3 && range.count == 3 &&
                        model.render_materials[range.material_slot] ==
                            model.polygons[range.polygon].material &&
                        materials[index].color == expected_colors[index],
                    "Repeated-material original polygon/slot/material correspondence changed");
            for (std::size_t corner = 0; corner < 3; ++corner) {
                const auto offset = index * 3 + corner;
                const float *position = model.vertices + (2 - corner) * 3;
                const auto &vertex = source->vertices[offset];
                require(source->indices[offset] == offset && vertex.x == position[0] &&
                            vertex.y == position[1] && vertex.z == position[2],
                        "Repeated-material triangle corner order changed");
            }
        }
        const auto result = Renderer::submit_model_geometry(source, context, materials, fog);
        if (throw_after_submission)
            throw std::runtime_error("Authored material callback failure");
        return result;
    }
};

void check_material_ordinals(std::uint32_t polygon_count, bool force_outer_unwind = false) {
    float source_positions[]{-1, -1, 3, 1, -1, 3, 0, 1, 3};
    const float original_positions[]{-1, -1, 3, 1, -1, 3, 0, 1, 3};
    uint32_t source_indices[]{0, 1, 2};
    zmod::Material first{}, second{}, replacement{};
    first.alpha = second.alpha = replacement.alpha = 255;
    first.r = second.g = replacement.b = 255;
    std::vector<zmod::Polygon> source_polygons(polygon_count);
    MaterialOrdinalRenderer recorder;
    const unsigned first_count = polygon_count == 3 ? 2 : 3;
    for (unsigned index = 0; index < polygon_count; ++index) {
        auto &source_polygon = source_polygons[index];
        source_polygon.flags = 3;
        source_polygon.vertex_indices = source_indices;
        source_polygon.material = index < first_count ? &first : &second;
        recorder.expected_materials.push_back(source_polygon.material);
        recorder.expected_colors.push_back(index < first_count ? 0xffff0000 : 0xff00ff00);
    }
    zmod::Model source_model{};
    source_model.vertices = source_positions;
    source_model.polygons = source_polygons.data();
    for (const auto [offset, value] :
         {std::pair{8, 3U}, std::pair{0x10, polygon_count}, std::pair{0x14, 3U}})
        std::memcpy(source_model.header + offset, &value, sizeof value);
    zcls::Node source_node{};
    source_node.model = &source_model;
    recorder.expected_node = &source_node;
    // Declared after recorder, so its pointer is restored before recorder dies.
    struct FixtureState {
        platform::Render3D *renderer = zvid::render3d();
        std::fenv_t environment{};
        FixtureState() {
            require(std::fegetenv(&environment) == 0, "Cannot preserve material fixture FP state");
        }
        ~FixtureState() {
            zvid::set_render3d(renderer);
            std::fesetenv(&environment);
        }
    } restore;
    zvid::set_render3d(&recorder);
    std::fesetround(FE_UPWARD);
    std::feclearexcept(FE_ALL_EXCEPT);
    std::feraiseexcept(FE_DIVBYZERO);
    require(zmod::submit_geometry(source_node), "Repeated-material producer rejected source");
    require(std::fegetround() == FE_UPWARD && std::fetestexcept(FE_ALL_EXCEPT) == FE_DIVBYZERO,
            "Repeated-material success leaked FP state");
    const auto original_resource = recorder.submitted;
    const auto original_indices = original_resource->indices;
    require(zmod::submit_geometry(source_node) && recorder.submitted == original_resource,
            "Repeated-material unchanged source rebuilt its immutable cache");
    source_polygons.back().material = &replacement;
    recorder.expected_materials.back() = &replacement;
    recorder.expected_colors.back() = 0xff0000ff;
    require(zmod::submit_geometry(source_node) && recorder.submitted != original_resource &&
                recorder.submitted->identity != original_resource->identity &&
                original_resource->indices == original_indices &&
                original_resource->ranges.size() == polygon_count,
            "Repeated-material pointer mutation failed immutable cache invalidation");
    for (unsigned index = 0; index < polygon_count; ++index)
        require(original_resource->ranges[index].polygon == index &&
                    original_resource->ranges[index].material_slot == index,
                "Repeated-material pending resource was overwritten");
    recorder.throw_after_submission = true;
    bool callback_failed = false;
    try {
        zmod::submit_geometry(source_node);
    } catch (const std::runtime_error &error) {
        callback_failed = std::string_view(error.what()) == "Authored material callback failure";
    }
    require(callback_failed && std::fegetround() == FE_UPWARD &&
                std::fetestexcept(FE_ALL_EXCEPT) == FE_DIVBYZERO &&
                !std::memcmp(source_positions, original_positions, sizeof source_positions) &&
                source_indices[0] == 0 && source_indices[1] == 1 && source_indices[2] == 2,
            "Repeated-material callback/source preservation failed");
    if (force_outer_unwind)
        throw std::runtime_error("Authored material fixture unwind");
}

int main() try {
    float positions[]{-1, -1, 3, 1, -1, 3, 0, 1, 3};
    uint32_t indices[]{0, 1, 2};
    zmod::Material material{};
    material.alpha = 255;
    material.r = 255;
    zmod::Polygon polygon{};
    polygon.flags = 3;
    polygon.vertex_indices = indices;
    polygon.material = &material;
    zmod::Model model{};
    model.vertices = positions;
    model.polygons = &polygon;
    auto set = [&](int offset, uint32_t value) { std::memcpy(model.header + offset, &value, 4); };
    set(8, 3);
    set(0x10, 1);
    set(0x14, 3);
    zcls::Node node{};
    node.model = &model;
    zmth::Mat34 base{{1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0}};
    zmth::matrix_stack() = {};
    zmth::matrix_stack().slot[0] = &base;
    zmth::matrix_stack().identity[0] = 1;
    zmth::view().view = base;
    auto &projection = zmth::projection();
    projection.near_z = 1;
    projection.far_z = 10;
    projection.fx_near = projection.fy_near = 16;
    projection.cx = projection.cy = 16;
    zmod::draw_state() = {};
    zmod::draw_state().clip.near_z = 1;
    Renderer renderer;
    zvid::set_render3d(&renderer);
    auto &buffers = zmod::draw_buffers();
    std::memset(buffers.cam, 0x5a, sizeof buffers.cam);
    std::memset(buffers.normals, 0x6b, sizeof buffers.normals);
    auto &work = zmod::clip2d();
    std::memset(work.tl, 0x7c, sizeof work.tl);
    const auto before = buffers;
    const auto before_work = work;
    renderer.prepared = true;
    require(zmod::draw_model(&node, 0x3f) == 0 && !model.render_geometry && !renderer.submitted &&
                renderer.legacy_draws == 0 &&
                !std::memcmp(before.cam, buffers.cam, sizeof buffers.cam) &&
                !std::memcmp(before.normals, buffers.normals, sizeof buffers.normals) &&
                !std::memcmp(before_work.tl, work.tl, sizeof work.tl),
            "Prepared early handoff still registered stock geometry or ran CPU producer loops");
    renderer.prepared = false;
    require(zmod::draw_model(&node, 0x3f) == 0, "Original model return changed");
    require(renderer.submitted && renderer.legacy_draws == 0,
            "Early owned submission was bypassed");
    require(!std::memcmp(before.cam, buffers.cam, sizeof buffers.cam) &&
                !std::memcmp(before.normals, buffers.normals, sizeof buffers.normals) &&
                !std::memcmp(before_work.tl, work.tl, sizeof work.tl),
            "CPU transform/normal/polygon output was still produced");
    require(zmth::matrix_stack().top == 0, "Original matrix stack did not unwind");
    const auto original = renderer.submitted;
    require(original->indices.size() == 3 && original->vertices[0].y == 1,
            "Corner ordering was not normalized");
    require(zmod::draw_model(&node, 0x3f) == 0 && renderer.submitted == original,
            "Unchanged source rebuilt immutable geometry");
    positions[0] = -2;
    model.invalidate_render_geometry();
    require(zmod::draw_model(&node, 0x3f) == 0 && renderer.submitted != original &&
                renderer.submitted->identity != original->identity && original->vertices[2].x == -1,
            "Changed source reused or overwrote a pending immutable resource");
    std::fesetround(FE_UPWARD);
    std::feclearexcept(FE_ALL_EXCEPT);
    std::feraiseexcept(FE_DIVBYZERO);
    zmth::Mat34 camera = base;
    zmth::matrix_stack().top = 1;
    zmth::matrix_stack().slot[1] = &camera;
    require(zmod::submit_geometry(node), "Direct early handoff rejected authored geometry");
    require(std::fegetround() == FE_UPWARD && std::fetestexcept(FE_ALL_EXCEPT) == FE_DIVBYZERO,
            "Rendering callback leaked FP environment");
    std::fenv_t before_material_fixtures{};
    require(std::fegetenv(&before_material_fixtures) == 0,
            "Cannot preserve material fixture caller FP state");
    unsigned material_failures = 0;
    for (unsigned polygon_count : {3U, 14U}) {
        const auto *prior_renderer = zvid::render3d();
        std::fesetround(FE_TOWARDZERO);
        std::feclearexcept(FE_ALL_EXCEPT);
        std::feraiseexcept(FE_OVERFLOW);
        const auto prior_round = std::fegetround();
        const auto prior_flags = std::fetestexcept(FE_ALL_EXCEPT);
        try {
            check_material_ordinals(polygon_count);
            require(zvid::render3d() == prior_renderer && std::fegetround() == prior_round &&
                        std::fetestexcept(FE_ALL_EXCEPT) == prior_flags,
                    "Material fixture success changed caller renderer/FP state");
            bool unwound = false;
            try {
                check_material_ordinals(polygon_count, true);
            } catch (const std::runtime_error &error) {
                unwound = std::string_view(error.what()) == "Authored material fixture unwind";
            }
            require(unwound && zvid::render3d() == prior_renderer &&
                        std::fegetround() == prior_round &&
                        std::fetestexcept(FE_ALL_EXCEPT) == prior_flags,
                    "Material fixture unwind changed caller renderer/FP state");
            std::cout << "Material ordinal fixture " << polygon_count << ": passed\n";
        } catch (const std::exception &error) {
            ++material_failures;
            std::cerr << "Material ordinal fixture " << polygon_count << ": " << error.what()
                      << '\n';
        }
    }
    std::fesetenv(&before_material_fixtures);
    zvid::set_render3d(&renderer);
    require(material_failures == 0, "Original polygon material identity regression");
    std::cout << "Material fixture renderer/FP restoration and outer unwind pass\n";
    std::fesetround(FE_TONEAREST);
    zmth::matrix_stack().top = 0;
    material.alpha = 100;
    renderer.mode = cc::geometry::Mode::gpu;
    bool rejected = false;
    try {
        zmod::draw_model(&node, 0x3f);
    } catch (const std::runtime_error &) {
        rejected = true;
    }
    require(rejected && renderer.unsupported == 1 && zmth::matrix_stack().top == 0,
            "Strict GPU mode silently used CPU geometry or failed to unwind");
    material.alpha = 255;
    renderer.mode = cc::geometry::Mode::partial;
    renderer.accept = false;
    require(!zmod::submit_geometry(node), "Unsupported backend was reported as submitted");
    bool bad_index = false;
    indices[0] = 999;
    try {
        cc::geometry::register_resource(positions, 3, nullptr, 0,
                                        {{3, indices, nullptr, nullptr, false, false}});
    } catch (const std::runtime_error &) {
        bad_index = true;
    }
    require(bad_index, "Registration accepted an out-of-bounds index");
    float strip_positions[]{-1, -1, 3, 1, -1, 3, -1, 1, 3, 1, 1, 3};
    uint32_t strip_indices[]{0, 1, 2, 3};
    const auto strip = cc::geometry::register_resource(
        strip_positions, 4, nullptr, 0, {{4, strip_indices, nullptr, nullptr, true, false}});
    require(strip->indices == std::vector<uint32_t>{0, 1, 2, 2, 1, 3} && strip->ranges[0].two_sided,
            "Registered strip changed legacy winding or two-sided behavior");
    zvid::set_render3d(nullptr);
    std::cout << "Early geometry handoff, skipped CPU loops, immutable revisions, FP and strict "
                 "rejection pass\n";
    return 0;
} catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
}
