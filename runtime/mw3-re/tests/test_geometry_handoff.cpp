#include "frontend/core_critical/renderer/geometry/resource.hpp"
#include "gamez/zclass/cls_node.h"
#include "gamez/zmath/zmth_matrix.h"
#include "gamez/zmodel/gmod_const.h"
#include "gamez/zmodel/gmod_draw.h"
#include "gamez/zmodel/gmod_geometry.h"
#include "gamez/zmodel/gmod_fog.h"
#include "gamez/zmodel/gmod_fogcalc.h"
#include "gamez/zvideo/zvid_ddd3d.h"

#include <array>
#include <cfenv>
#include <cmath>
#include <cstring>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string_view>
#include <utility>

#if defined(_M_X64) || defined(_M_IX86) || defined(__SSE__)
#include <xmmintrin.h>
#define GEOMETRY_TEST_MXCSR 1
#endif

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

namespace {
unsigned far_cases = 0;

// Draw-model writes these shared buffers even when its early handoff succeeds.
// Keep each fixture independent, including exceptions from strict GPU mode.
struct FarState {
    platform::Render3D *renderer = zvid::render3d();
    zmth::MatrixStack stack = zmth::matrix_stack();
    zmth::View view = zmth::view();
    zmth::Projection projection = zmth::projection();
    zmod::DrawState state = zmod::draw_state();
    zmod::DrawTable table = zmod::draw_table();
    zmod::DrawHooks hooks = zmod::draw_hooks();
    zmod::DrawBuffers buffers = zmod::draw_buffers();
    zmod::Clip2D clip2d = zmod::clip2d();
    zmod::Clip3dBuffers clip3d = zmod::clip3d_buffers();
    zmod::Lighting lighting = zmod::lighting();
    zmod::LightList lights = zmod::light_list();
    zcls::Frames frames = zcls::frames();
    zmod::Fog fog = zmod::fog();
    zmod::FogCalc fog_calc = zmod::fog_calc();
    zvid::DeviceState device = zvid::device_state();
    std::fenv_t environment{};
#ifdef GEOMETRY_TEST_MXCSR
    unsigned mxcsr = _mm_getcsr();
#endif
    FarState() {
        require(std::fegetenv(&environment) == 0, "Cannot preserve far fixture FP state");
    }
    ~FarState() {
        zvid::set_render3d(renderer);
        zmth::matrix_stack() = stack;
        zmth::view() = view;
        zmth::projection() = projection;
        zmod::draw_state() = state;
        zmod::draw_table() = table;
        zmod::draw_hooks() = hooks;
        zmod::draw_buffers() = buffers;
        zmod::clip2d() = clip2d;
        zmod::clip3d_buffers() = clip3d;
        zmod::lighting() = lighting;
        zmod::light_list() = lights;
        zcls::frames() = frames;
        zmod::fog() = fog;
        zmod::fog_calc() = fog_calc;
        zvid::device_state() = device;
        std::fesetenv(&environment);
#ifdef GEOMETRY_TEST_MXCSR
        _mm_setcsr(mxcsr);
#endif
    }
};

struct FarRenderer : Renderer {
    unsigned submissions = 0;
    cc::geometry::Submission submit_model_geometry(
        std::shared_ptr<const cc::geometry::Resource> source,
        const platform::ModelDrawContext &context,
        const std::vector<cc::geometry::Material> &materials,
        const cc::geometry::Fog &fog) override {
        ++submissions;
        return Renderer::submit_model_geometry(std::move(source), context, materials, fog);
    }
};

struct LegacyEmission {
    int primitive;
    void *texture;
    std::vector<zmod::TLVertex> vertices;
    std::vector<std::array<float, 3>> camera;
};

struct FarFixture {
    FarRenderer renderer;
    FarState restore;
    zmth::Mat34 world{{1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0}};
    zmth::Mat34 camera = world;
    std::vector<float> positions{-1, -1, 3, 1, -1, 3, 0, 1, 3};
    std::vector<float> normals;
    std::array<uint32_t, 4> indices{{0, 1, 2, 3}};
    std::array<float, 8> uvs{{0, 0, 1, 0, 1, 1, 0, 1}};
    std::array<float, 12> colors{};
    zvid::D3DTexture texture{};
    zimg::TextureEntry entry{};
    zmod::Material material{};
    zmod::Polygon polygon{};
    zmod::Model model{};
    zcls::Node node{};
    std::vector<LegacyEmission> emissions;

    FarFixture() {
        std::fesetround(FE_TONEAREST);
        std::feclearexcept(FE_ALL_EXCEPT);
        zmth::matrix_stack() = {};
        zmth::matrix_stack().slot[0] = &world;
        zmth::matrix_stack().identity[0] = 1;
        zmth::matrix_stack().slot[1] = &camera;
        zmth::view().view = world;
        zmth::projection() = {};
        auto &projection = zmth::projection();
        projection.near_z = 1;
        projection.far_z = 10;
        projection.fx_near = projection.fy_near = 16;
        projection.cx = projection.cy = 16;
        zmod::draw_state() = {};
        zmod::draw_state().clip.near_z = 1;
        zmod::draw_state().clip.far_z = 10;
        zmod::draw_hooks() = {};
        zmod::fog().on = 0;
        zmod::lighting().tint_on = 0;
        material.alpha = 255;
        material.r = 255;
        polygon.flags = 3 | 0x100;
        polygon.vertex_indices = indices.data();
        polygon.material = &material;
        polygon.uvs = uvs.data();
        polygon.colors = colors.data();
        model.vertices = positions.data();
        model.polygons = &polygon;
        count(8, 0); // No lighting, fog, morph or static-bake effects.
        count(0x10, 1);
        count(0x14, 3);
        node.model = &model;
        texture.handle = 7;
        entry.surface = &texture;
        material.texture = &entry;
        zmod::draw_table() = {};
        auto &table = zmod::draw_table();
        table.ctx = this;
        table.flat = [](void *ctx, uint32_t, int32_t, int32_t count, int32_t, int32_t) {
            static_cast<FarFixture *>(ctx)->record(count, nullptr);
        };
        table.lit = [](void *ctx, uint32_t, const float *, uint32_t, int32_t,
                       int32_t count, int32_t, int32_t) {
            static_cast<FarFixture *>(ctx)->record(count, nullptr);
        };
        table.textured = [](void *ctx, int32_t count, void *texture, float, int32_t) {
            static_cast<FarFixture *>(ctx)->record(count, texture);
        };
        zvid::set_render3d(&renderer);
    }
    FarFixture(const FarFixture &) = delete;
    FarFixture &operator=(const FarFixture &) = delete;
    void count(int offset, uint32_t value) {
        std::memcpy(model.header + offset, &value, sizeof value);
    }
    void depths(float a, float b, float c) {
        positions[2] = a;
        positions[5] = b;
        positions[8] = c;
        model.invalidate_render_geometry();
    }
    void record(int32_t count, void *texture) {
        require(count >= 3 && count <= zmod::kPolyVerts, "Invalid legacy callback count");
        LegacyEmission emission{zvid::device_state().primitive, texture, {}, {}};
        for (int i = 0; i < count; ++i) {
            emission.vertices.push_back(zmod::clip2d().tl[i]);
            const float *position = zmod::clip3d_buffers().cam[i];
            emission.camera.push_back({position[0], position[1], position[2]});
        }
        emissions.push_back(std::move(emission));
    }
    void submit(bool expected) {
        ++far_cases;
        zmth::matrix_stack().top = 1;
        zmth::matrix_stack().slot[1] = &camera;
        const auto calls = renderer.submissions;
        const auto unsupported = renderer.unsupported;
        const int rounding = std::fegetround();
        const int flags = std::fetestexcept(FE_ALL_EXCEPT);
#ifdef GEOMETRY_TEST_MXCSR
        const unsigned mxcsr = _mm_getcsr();
#endif
        const bool submitted = zmod::submit_geometry(node);
        if (submitted != expected)
            std::cerr << "Far admission expected=" << expected << " actual=" << submitted
                      << " submission calls=" << renderer.submissions - calls << '\n';
        require(submitted == expected, "Far admission result changed");
        require(renderer.submissions == calls + unsigned(expected) &&
                    renderer.unsupported == unsupported + unsigned(!expected),
                "Far admission emitted or accounted more than once");
        require(model.render_geometry && model.render_materials ==
                    std::vector<const zmod::Material *>{polygon.material},
                "Far admission lost registered geometry/material source identity");
        require(std::fegetround() == rounding && std::fetestexcept(FE_ALL_EXCEPT) == flags,
                "Far admission leaked rounding or exception state");
#ifdef GEOMETRY_TEST_MXCSR
        require(_mm_getcsr() == mxcsr, "Far admission leaked MXCSR state");
#endif
    }
    void draw(uint32_t mask) {
        ++far_cases;
        zmth::matrix_stack().top = 0;
        emissions.clear();
        require(zmod::draw_model(&node, mask) == 0 && zmth::matrix_stack().top == 0,
                "Far model draw return or matrix unwind changed");
    }
};

void check_far_cache_and_prepared() {
    FarFixture fixture;
    const auto before = zmod::draw_buffers();
    const auto before_work = zmod::clip2d();
    fixture.draw(0x3f);
    require(fixture.renderer.submissions == 1 && fixture.emissions.empty() &&
                !std::memcmp(&before, &zmod::draw_buffers(), sizeof before) &&
                !std::memcmp(&before_work, &zmod::clip2d(), sizeof before_work),
            "Safe full-mask model no longer skips CPU preparation");
    const auto original = fixture.model.render_geometry;
    fixture.submit(true);
    require(fixture.model.render_geometry == original, "Safe cached resource was rebuilt");
    fixture.positions[2] = 12;
    fixture.submit(true); // Source mutators must explicitly invalidate the owned snapshot.
    require(original->vertices[2].z == 3, "Pending resource borrowed mutable source positions");
    fixture.model.invalidate_render_geometry();
    fixture.submit(false);
    const auto declined = fixture.model.render_geometry;
    require(declined != original && declined->identity != original->identity &&
                original->vertices[2].z == 3,
            "Far-sensitive invalidation overwrote or reused an immutable resource");
    fixture.submit(false);
    require(fixture.model.render_geometry == declined, "Decline discarded the registered cache");
    zmod::Material replacement = fixture.material;
    fixture.polygon.material = &replacement;
    fixture.submit(false);
    require(fixture.model.render_geometry != declined &&
                fixture.model.render_materials[0] == &replacement,
            "Far decline failed to publish changed material identity");

    FarFixture prepared;
    prepared.depths(10, 10, 10);
    prepared.renderer.prepared = true;
    prepared.draw(0x20);
    require(!prepared.model.render_geometry && prepared.renderer.submissions == 0 &&
                prepared.renderer.unsupported == 0 && prepared.emissions.empty(),
            "At-far prepared submission lost precedence over stock registration");
}

void check_far_planes_and_rounding() {
    const float below = std::nextafter(10.f, 0.f);
    const float above = std::nextafter(10.f, std::numeric_limits<float>::infinity());
    for (int rounding : {FE_TONEAREST, FE_DOWNWARD, FE_UPWARD, FE_TOWARDZERO}) {
        FarFixture fixture;
        require(std::fesetround(rounding) == 0, "Cannot select authored rounding mode");
        std::feraiseexcept(FE_DIVBYZERO);
        fixture.submit(true);
        for (float depth : {below, 10.f, above, 12.f}) {
            fixture.depths(depth, depth, depth);
            fixture.submit(false);
            fixture.submit(false);
        }
    }
    const float invalid[]{0.f, -0.f, -1.f, std::numeric_limits<float>::infinity(),
                          -std::numeric_limits<float>::infinity(),
                          std::numeric_limits<float>::quiet_NaN(),
                          std::numeric_limits<float>::denorm_min()};
    for (float plane : invalid) {
        FarFixture fixture;
        zmth::projection().far_z = plane;
        fixture.submit(false);
        zmth::projection().far_z = 10;
        zmod::draw_state().clip.far_z = plane;
        fixture.submit(false);
        zmth::projection().far_z = plane;
        fixture.submit(false);
    }
    FarFixture mismatch;
    zmod::draw_state().clip.far_z = 11;
    mismatch.submit(false);
    zmod::draw_state().clip.far_z = below;
    mismatch.submit(false);
    mismatch.renderer.mode = cc::geometry::Mode::cpu_reference;
    mismatch.submit(false);
}

void check_far_transforms() {
    struct TransformCase { float x, y, z, translation; bool safe; };
    const TransformCase cases[]{
        {1, 0, 0, 5, true}, {1, 0, 0, 9, false},
        {-1, 0, 0, 5, true}, {-1, 0, 0, 9, false},
        {2, -.5f, .25f, 4, true}, {2, -.5f, .25f, 8, false},
        {0, 0, -2, 14, true}, {0, 0, -2, 16, false},
        {0, 0, 1, 8, false}, {0, 0, 1, -8, true}};
    FarFixture fixture;
    for (const auto &test : cases) {
        fixture.camera.m[2] = test.x;
        fixture.camera.m[5] = test.y;
        fixture.camera.m[8] = test.z;
        fixture.camera.m[11] = test.translation;
        fixture.submit(test.safe);
    }
    // Exact arithmetic gives z=9. Reassociation at float precision can reach far.
    for (int rounding : {FE_TONEAREST, FE_DOWNWARD, FE_UPWARD, FE_TOWARDZERO}) {
        FarFixture cancellation;
        for (unsigned i = 0; i < 3; ++i) {
            cancellation.positions[3 * i] = 16777216.f;
            cancellation.positions[3 * i + 1] = 16777216.f;
            cancellation.positions[3 * i + 2] = 9;
        }
        cancellation.camera.m[2] = 1;
        cancellation.camera.m[5] = -1;
        require(std::fesetround(rounding) == 0, "Cannot select cancellation rounding mode");
        cancellation.submit(false);
    }
    const float uncertain[]{std::numeric_limits<float>::infinity(),
                            std::numeric_limits<float>::quiet_NaN(),
                            std::numeric_limits<float>::denorm_min(),
                            -std::numeric_limits<float>::denorm_min()};
    for (int coefficient : {2, 5, 8, 11}) {
        for (float value : uncertain) {
            FarFixture nonnormal;
            nonnormal.camera.m[coefficient] = value;
            nonnormal.submit(false);
        }
    }
    FarFixture overflow;
    overflow.submit(true);
    overflow.camera.m[8] = std::numeric_limits<float>::max();
    overflow.submit(false);
    overflow.camera.m[8] = 1;
    overflow.camera.m[11] = -std::numeric_limits<float>::max();
    overflow.submit(false);
}

void check_far_subnormals() {
#ifdef GEOMETRY_TEST_MXCSR
    // Registration reads reverse corners: zero first, subnormal later, zero last.
    // DAZ makes floating min/max comparisons alone lose that middle corner.
    for (unsigned flush : {0u, 0x40u, 0x8040u}) {
        for (uint32_t bits : {1u, 0x80000001u}) {
            FarFixture fixture;
            fixture.positions[0] = fixture.positions[3] = fixture.positions[6] = 0;
            std::memcpy(&fixture.positions[3], &bits, sizeof bits);
            _mm_setcsr((_mm_getcsr() & ~0x8040u) | flush);
            const char *phase = "fresh subnormal";
            try {
                fixture.submit(false);
                phase = "cached subnormal";
                fixture.submit(false);
                fixture.positions[3] = 0;
                fixture.model.invalidate_render_geometry();
                phase = "invalidated zero";
                fixture.submit(true);
            } catch (...) {
                uint32_t source_bits{}, registered_bits{};
                std::memcpy(&source_bits, &fixture.positions[3], sizeof source_bits);
                if (fixture.model.render_geometry)
                    std::memcpy(&registered_bits, &fixture.model.render_geometry->vertices[1].x,
                                sizeof registered_bits);
                std::cerr << "Subnormal phase=" << phase << " requested bits=0x" << std::hex
                          << bits << " source bits=0x" << source_bits << " registered bits=0x"
                          << registered_bits << " flush=0x" << flush << " MXCSR=0x"
                          << _mm_getcsr() << std::dec << '\n';
                throw;
            }
        }
    }
#else
    std::cout << "Far subnormal MXCSR cases unavailable on this architecture\n";
#endif
}

void check_far_strict_and_capacity() {
    FarFixture strict;
    strict.depths(8, 12, 12);
    strict.renderer.mode = cc::geometry::Mode::gpu;
    std::fesetround(FE_UPWARD);
    std::feraiseexcept(FE_DIVBYZERO);
    const auto before_flags = std::fetestexcept(FE_ALL_EXCEPT);
    const auto before_matrix = strict.world;
    bool rejected = false;
    try {
        strict.draw(0x20);
    } catch (const std::runtime_error &) {
        rejected = true;
    }
    require(rejected && strict.renderer.unsupported == 1 &&
                strict.renderer.submissions == 0 && strict.emissions.empty() &&
                zmth::matrix_stack().top == 0 && std::fegetround() == FE_UPWARD &&
                std::fetestexcept(FE_ALL_EXCEPT) == before_flags &&
                !std::memcmp(&before_matrix, &strict.world, sizeof before_matrix),
            "Far strict rejection lost accounting, matrix unwind or caller FP state");

    for (bool oversized_normals : {false, true}) {
        FarFixture fixture;
        const uint32_t count = zmod::kModelVerts + 1;
        if (oversized_normals) {
            fixture.normals.resize(count * 3, 0);
            fixture.model.normals = fixture.normals.data();
            fixture.count(0x18, count);
            zmod::draw_state().vertex_shading = 1;
        } else {
            fixture.positions.resize(count * 3, 0);
            fixture.model.vertices = fixture.positions.data();
            fixture.count(0x14, count);
        }
        fixture.submit(true);
        fixture.depths(8, 12, 12);
        const auto before = zmod::draw_buffers();
        const auto work = zmod::clip2d();
        bool capacity_error = false;
        ++far_cases;
        try {
            // Direct submit keeps the RED control safe even with old production.
            zmod::submit_geometry(fixture.node);
        } catch (const std::runtime_error &error) {
            capacity_error = std::string_view(error.what()).find("capacity") !=
                             std::string_view::npos;
        }
        require(capacity_error && fixture.renderer.submissions == 1 &&
                    !std::memcmp(&before, &zmod::draw_buffers(), sizeof before) &&
                    !std::memcmp(&work, &zmod::clip2d(), sizeof work),
                "Far-unsafe oversized source did not reject before legacy buffers");
        if (oversized_normals) {
            zmod::draw_state().vertex_shading = 0;
            // Bounded normal storage can still use the ordinary CPU producer.
            fixture.count(0x18, zmod::kModelVerts);
            fixture.model.invalidate_render_geometry();
            fixture.submit(false);
        }
    }

    // Static baking indexes the normal cache independently of vertex shading.
    // Keep the direct-submit failure first so an old-guard RED run never enters
    // its unsafe CPU producer; the repaired guard also protects real draw_model.
    for (int shading : {0, 1}) {
        FarFixture fixture;
        const uint32_t count = zmod::kModelVerts + 1;
        fixture.normals.resize(count * 3, 0);
        fixture.normals[(count - 1) * 3 + 2] = 1;
        fixture.model.normals = fixture.normals.data();
        fixture.count(0x18, count);
        fixture.count(8, 1); // Lit, ordinary source with no_sun clear.
        fixture.polygon.flags = 3 | 0x200; // One-sided indexed normals.
        std::array<uint32_t, 3> normal_indices{{count - 1, count - 1, count - 1}};
        fixture.polygon.normal_indices = normal_indices.data();
        zmod::draw_state().vertex_shading = shading;
        zmod::draw_state().static_lights = 1;
        zmod::lighting().mask_base = 1;
        zmod::lighting().mask = &zmod::lighting().mask_base;
        zcls::Light sun{};
        sun.put<uint32_t>(0xb0, 0x108); // Static, directed, no range restriction.
        sun.put<float>(0x9c, 1);
        auto &lights = zmod::light_list();
        lights = {};
        lights.any = lights.count = 1;
        lights.directed = 0;
        lights.list[0].data = &sun;
        lights.list[0].full = lights.list[0].reach = 1;
        zcls::frames().update_frame = 1;
        zcls::frames().frame = 1;
        fixture.node.put<uint32_t>(0xc0, 0);
        fixture.node.put<uint32_t>(0xc4, 0);
        fixture.submit(true); // Safe-inside oversized sources stay accelerated.
        fixture.depths(8, 12, 12);
        const auto before = zmod::draw_buffers();
        const auto work = zmod::clip2d();
        for (bool actual_draw : {false, true}) {
            bool capacity_error = false;
            ++far_cases;
            try {
                if (actual_draw) {
                    zmth::matrix_stack().top = 0;
                    zmod::draw_model(&fixture.node, 0x20);
                } else {
                    zmod::submit_geometry(fixture.node);
                }
            } catch (const std::runtime_error &error) {
                capacity_error = std::string_view(error.what()).find("capacity") !=
                                 std::string_view::npos;
            }
            require(capacity_error && fixture.renderer.submissions == 1 &&
                        fixture.emissions.empty() &&
                        !std::memcmp(&before, &zmod::draw_buffers(), sizeof before) &&
                        !std::memcmp(&work, &zmod::clip2d(), sizeof work) &&
                        (!actual_draw || zmth::matrix_stack().top == 0) &&
                        fixture.node.get<uint32_t>(0xc0) == 0,
                    "Far-unsafe indexed normals reached CPU preparation or static bake");
        }
    }
}

void check_far_legacy_fans() {
    for (uint32_t mask : {0u, 0x20u}) {
        for (const auto depths : {std::array<float, 4>{8, 12, 12, 12},
                                  std::array<float, 4>{10, 10, 10, 10},
                                  std::array<float, 4>{12, 12, 12, 12}}) {
            FarFixture fixture;
            fixture.positions = {-1, -1, depths[0], 1, -1, depths[1],
                                  1, 1, depths[2], -1, 1, depths[3]};
            fixture.model.vertices = fixture.positions.data();
            fixture.count(0x14, 4);
            fixture.polygon.flags = 4 | 0x100;
            const unsigned expected = mask && depths[0] >= 10 ? 0 : 1;
            for (int cached = 0; cached < 2; ++cached) {
                const auto unsupported = fixture.renderer.unsupported;
                zmod::draw_state().clip.mask = mask ^ 0x20u;
                fixture.draw(mask);
                require(fixture.renderer.submissions == 0 &&
                            fixture.renderer.unsupported == unsupported + 1 &&
                            fixture.emissions.size() == expected &&
                            fixture.model.render_geometry &&
                            fixture.model.render_materials[0] == &fixture.material,
                        "Original far polygon rejection or once-only CPU emission changed");
                if (expected) {
                    const auto &emission = fixture.emissions[0];
                    require(emission.primitive == 6 && emission.vertices.size() == 4,
                            "Crossing original n-gon was split or clipped at far");
                    for (unsigned corner = 0; corner < 4; ++corner) {
                        const float *position = fixture.positions.data() + 3 * (3 - corner);
                        require(emission.camera[corner] ==
                                    std::array<float, 3>{position[0], position[1], position[2]} &&
                                    emission.vertices[corner].sz == 1.f / position[2],
                                "Original fan lost far-side corners or reversed ordering");
                    }
                }
            }
        }
    }
}

void check_far_legacy_strips() {
    for (uint32_t mask : {0u, 0x20u}) {
        FarFixture fixture;
        // First split triangle is wholly beyond far; the second crosses it.
        fixture.positions = {1, -1, 12, -1, -1, 12, 1, 1, 12, -1, 1, 8};
        fixture.model.vertices = fixture.positions.data();
        fixture.count(0x14, 4);
        fixture.polygon.flags = 4 | 0x400;
        fixture.material.flags = 1;
        for (int cached = 0; cached < 2; ++cached) {
            fixture.draw(mask);
            require(fixture.renderer.submissions == 0 && fixture.emissions.size() == 1,
                    "Far-sensitive textured strip bypassed original CPU emission");
            const auto &emission = fixture.emissions[0];
            require(emission.texture == &fixture.texture &&
                        emission.primitive == (mask ? 6 : 5) &&
                        emission.vertices.size() == (mask ? 3u : 4u),
                    "Textured strip split/rejection policy changed");
            const unsigned split_indices[]{1, 2, 3};
            for (unsigned corner = 0; corner < emission.vertices.size(); ++corner) {
                const unsigned source = mask ? split_indices[corner] : 3 - corner;
                const float *position = fixture.positions.data() + 3 * source;
                require(emission.camera[corner] ==
                            std::array<float, 3>{position[0], position[1], position[2]} &&
                            emission.vertices[corner].tu == fixture.uvs[2 * source] &&
                            emission.vertices[corner].tv == fixture.uvs[2 * source + 1],
                        "Textured split strip lost parity, far-side corners or UV ownership");
            }
        }
    }
}

void check_far_regressions() {
    struct Group { const char *name; void (*run)(); };
    const Group groups[]{
        {"safe/cache/prepared identity", check_far_cache_and_prepared},
        {"planes/rounding/nextafter", check_far_planes_and_rounding},
        {"transforms/cancellation/magnitude", check_far_transforms},
        {"subnormal registration/DAZ", check_far_subnormals},
        {"strict unwind/capacity", check_far_strict_and_capacity},
        {"original legacy polygon fans", check_far_legacy_fans},
        {"original legacy textured strips", check_far_legacy_strips}};
    unsigned failures = 0;
    for (const auto &group : groups) {
        const unsigned before = far_cases;
        try {
            group.run();
            std::cout << "Far regression " << group.name << ": passed ("
                      << far_cases - before << " cases)\n";
        } catch (const std::exception &error) {
            ++failures;
            std::cerr << "Far regression " << group.name << ": " << error.what() << '\n';
        }
    }
    std::cout << "Far regression groups: " << std::size(groups) - failures << "/"
              << std::size(groups) << ", cases attempted: " << far_cases << '\n';
    require(failures == 0, "Native far coverage regression");
}
} // namespace

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
    zmod::draw_state().clip.far_z = 10;
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
    check_far_regressions();
    return 0;
} catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
}
