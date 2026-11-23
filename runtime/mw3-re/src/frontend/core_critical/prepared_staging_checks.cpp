#include "../../../tests/prepared_visual_fixture.h"
#include "gamez/zclass/cls_util.h"
#include "gamez/zclass/object3d.h"
#include "gamez/zmodel/gmod_draw.h"
#include "prepared_draw_cache.hpp"
#include "prepared_models.hpp"
#include "platform/prepared_skins.h"
#include "renderer/normal_codec.hpp"
#include "renderer/fixture_observation_emission.hpp"
#include "renderer/surface_materials.hpp"
#include "renderer/native_surface_identity.hpp"
#include "renderer/geometry/resource.hpp"

#include <array>
#include <atomic>
#include <bit>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <functional>
#include <limits>
#include <sstream>
#include <type_traits>
#if defined(_WIN32)
#include <process.h>
#else
#include <unistd.h>
#endif

namespace {
static_assert(!std::is_copy_constructible<mw34::materials::SurfaceMaterialPack>::value,
              "Deep-copying a decoded pack would duplicate pixels under one reservation");
void require(bool value, const char *message) {
    if (!value)
        throw std::runtime_error(message);
}
void same(const cc_mw3_re::PreparedSubmission &a, const cc_mw3_re::PreparedSubmission &b) {
    require(a.vertices == b.vertices && a.clipped_triangles == b.clipped_triangles &&
                a.draw.count == b.draw.count && a.draw.sampler == b.draw.sampler &&
                !std::memcmp(a.draw.push.mode, b.draw.push.mode, sizeof a.draw.push.mode),
            "Cached prepared bytes or draw count changed");
    require(!std::memcmp(a.draw.push.fog, b.draw.push.fog, sizeof a.draw.push.fog) &&
                !std::memcmp(a.draw.push.target, b.draw.push.target, sizeof a.draw.push.target),
            "Cached fog or target changed");
    require(bool(a.draw.model) == bool(b.draw.model), "Cached GPU admission changed");
    if (a.draw.model) {
        require(a.draw.model->geometry == b.draw.model->geometry &&
                    a.draw.model->camera == b.draw.model->camera &&
                    a.draw.model->projection == b.draw.model->projection &&
                    a.draw.model->sun_world == b.draw.model->sun_world &&
                    a.draw.model->sun_normal == b.draw.model->sun_normal,
                "Cached model instance changed");
    }
    require(bool(a.draw.sun_tl) == bool(b.draw.sun_tl) &&
                bool(a.draw.lit_normals) == bool(b.draw.lit_normals) &&
                bool(a.draw.raw_fog) == bool(b.draw.raw_fog),
            "Cached clipping metadata changed");
    if (a.draw.raw_fog)
        require(*a.draw.raw_fog == *b.draw.raw_fog, "Cached raw fog changed");
    if (a.draw.sun_tl)
        require(a.draw.sun_tl->camera_world == b.draw.sun_tl->camera_world &&
                    a.draw.sun_tl->projection == b.draw.sun_tl->projection &&
                    *a.draw.lit_normals == *b.draw.lit_normals,
                "Cached clipped normals changed");
}
void checks() {
    const float tint_channels[3]{.3f, .7f, .123f};
    const auto packed_tint = cc_mw3_re::pack_damage_tint_rgb(tint_channels);
    for (unsigned channel = 0; channel < 3; ++channel) {
        const float decoded = float((packed_tint >> (channel * 8)) & 255U) / 255.f;
        require(std::abs(decoded - tint_channels[channel]) <= .5f / 255.f + 1e-6f,
                "Packed tint color exceeded half an 8-bit channel step");
    }
    namespace cc = cc_mw3_re;
    platform::prepared::Batch batch;
    batch.color = 0xffe08040;
    batch.vertices = {
        {-1, -1, 2, 0, 0, 1, 0, 0}, {1, -1, 2, 0, 0, 1, 1, 0}, {0, 1, 2, 0, 0, 1, .5f, 1}};
    cc::PreparedBatchDraw source;
    source.batch = &batch;
    source.camera = source.world = mw34::donor::identity();
    auto geometry = std::make_shared<mw34::vkscene::ModelGeometry>();
    platform::ModelDrawContext context;
    int actor_a = 0, actor_b = 0;
    context.node = &actor_a;
    context.near_z = context.clip_near = .1f;
    context.far_z = 100;
    context.fx_near = context.fy_near = 320;
    context.cx = context.cy = 32;
    std::array<int, 4> viewport{0, 0, 64, 64};
    unsigned width = 64, height = 64;
    bool lighting = true;
    zmod::fog() = {};
    zmod::fog().on = 1;
    zmod::fog().near_range = 1;
    zmod::fog().near_sq = 1;
    zmod::fog().far_range = 10;
    zmod::fog().far_sq = 100;
    zmod::fog().inv_range = 1.f / 9;
    zmod::fog().alt_low = 5;
    zmod::fog().alt_high = 10;
    zmod::fog().inv_alt = .2f;
    auto &camera = zmod::fog_calc().camera_to_world;
    std::memset(camera, 0, sizeof camera);
    camera[0][0] = camera[1][1] = camera[2][2] = 1;
    cc::PreparedDrawCache cache;
    cc::PreparedDrawCpuStatistics profile;
    const auto reference = [&] {
        return cc::prepare_draw(source, context, viewport, width, height, geometry, lighting);
    };
    const auto get = [&] {
        return cache.get(source, context, viewport, width, height, geometry, lighting, &profile);
    };
    if (!cc::PreparedDrawCache::supports_control_state()) {
        same(*get(), reference());
        require(cache.statistics().bypasses == 1, "Unsupported FP controls entered cache");
        return;
    }
    const auto first = get();
    same(*first, reference());
    const auto processed = profile.vertices;
    require(get() == first && cache.statistics().hits == 1 && profile.vertices == processed,
            "Unchanged prepared input was recomputed");
    context.damage_tint_rgb[0] = 1.f;
    context.damage_tint_weight = .6f;
    const auto tinted = get();
    same(*tinted, reference());
    require((tinted->draw.push.mode[0] & 128U) &&
                tinted->draw.push.mode[1] == 0x000000ffU &&
                std::bit_cast<float>(tinted->draw.push.mode[2]) == .6f,
            "Prepared cache lost damage tint");
    auto emissive_tinted = *tinted;
    cc_mw3_re::apply_fixture_observation_emission(emissive_tinted.draw.push.fog, .4f);
    require(emissive_tinted.draw.push.fog[3] > 1.f &&
                std::bit_cast<float>(emissive_tinted.draw.push.mode[2]) == .6f,
            "Fixture emission overwrote the independent tint weight");
    context.damage_tint_weight = 0.f;
    context.damage_tint_rgb[0] = 0.f;
    same(*get(), *first);
    require(!(get()->draw.push.mode[0] & 128U), "Prepared cache retained portrait tint");
    context.damage_tint_weight = .6f;
    const auto zero_rgb_tint = get();
    require(zero_rgb_tint->draw.push.mode[1] == 0U &&
                zero_rgb_tint->draw.push.mode[1] != tinted->draw.push.mode[1],
            "Prepared cache reused a tint draw after RGB changed");
    context.damage_tint_rgb[0] = 1.f;
    same(*get(), *tinted);
    context.damage_tint_weight = 1.f;
    same(*get(), reference());
    for (float weight : {-.1f, std::numeric_limits<float>::quiet_NaN(),
                         std::numeric_limits<float>::infinity(),
                         -std::numeric_limits<float>::infinity(), 1.1f}) {
        context.damage_tint_weight = weight;
        for (bool cached : {false, true}) {
            bool rejected = false;
            try {
                if (cached) get();
                else reference();
            } catch (const std::runtime_error &error) {
                rejected = std::string_view(error.what()) == "Model has an invalid native tint weight";
            }
            require(rejected, "Prepared staging/cache accepted an invalid tint weight");
        }
    }
    context.damage_tint_weight = 0.f;
    for (float channel : {-.1f, std::numeric_limits<float>::quiet_NaN(),
                          std::numeric_limits<float>::infinity(), 1.1f}) {
        context.damage_tint_rgb[1] = channel;
        for (bool cached : {false, true}) {
            bool rejected = false;
            try {
                if (cached) get();
                else reference();
            } catch (const std::runtime_error &error) {
                rejected = std::string_view(error.what()) == "Model has an invalid native tint color";
            }
            require(rejected, "Prepared staging/cache accepted an invalid tint color");
        }
    }
    context.damage_tint_rgb[1] = 0.f;
    const auto miss = [&] {
        const auto before = cache.statistics().misses;
        same(*get(), reference());
        require(cache.statistics().misses == before + 1,
                "Changed prepared input reused stale data");
    };
    source.camera[3] += .25;
    miss();
    source.world[7] += .5;
    miss();
    for (auto member : {&platform::ModelDrawContext::near_z, &platform::ModelDrawContext::clip_near,
                        &platform::ModelDrawContext::far_z, &platform::ModelDrawContext::fx_near,
                        &platform::ModelDrawContext::fy_near, &platform::ModelDrawContext::cx,
                        &platform::ModelDrawContext::cy}) {
        context.*member += .01f;
        miss();
    }
    context.opacity = .75f;
    miss();
    ++viewport[0];
    miss();
    ++width;
    miss();
    ++height;
    miss();
    lighting = false;
    miss();
    zmod::fog().color[1] = .5f;
    miss();
    zmod::fog().inv_range = .5f;
    miss();
    camera[3][1] = 2;
    miss();
    zmod::fog().on = 0;
    miss();
    geometry = std::make_shared<mw34::vkscene::ModelGeometry>();
    miss();
    context.node = &actor_b;
    miss();
    const int rounding = std::fegetround();
    std::fesetround(FE_DOWNWARD);
    miss();
    std::fesetround(rounding);
#if defined(_M_X64) || defined(_M_IX86) || defined(__x86_64__) || defined(__i386__)
    const auto rounded = get();
    require(get() == rounded, "Restored rounding did not stabilize the cache fixture");
    const auto controls = _mm_getcsr();
    _mm_setcsr(controls ^ 0x8000U);
    miss();
    _mm_setcsr(controls);
    const auto unflushed = get();
    require(get() == unflushed, "Restored FTZ did not stabilize the cache fixture");
    _mm_setcsr(controls ^ 0x40U);
    miss();
    _mm_setcsr(controls);
#endif
    const auto bypasses = cache.statistics().bypasses;
    source.deformed = batch.vertices;
    same(*get(), reference());
    source.deformed[0][0] += .125f;
    same(*get(), reference());
    require(cache.statistics().bypasses == bypasses + 2,
            "Mutable deformation entered the static cache");
    source.deformed.clear();
    lighting = true;
    source.camera[8] = 1.95;
    miss();
    require(!get()->draw.model && get()->clipped_triangles > 0,
            "Clipped cache fixture did not clip");
    auto alpha_batch = batch;
    alpha_batch.vertices[0][2] = .05f;
    auto alpha_source = source;
    alpha_source.batch = &alpha_batch;
    alpha_source.deformed.clear();
    auto alpha_context = context;
    alpha_context.opacity = .375f;
    const auto alpha_submission = cc::prepare_draw(
        alpha_source, alpha_context, viewport, width, height, geometry, false);
    require(alpha_submission.draw.key.blend && !alpha_submission.draw.key.zwrite &&
                alpha_submission.draw.key.cull == 1 && !alpha_submission.draw.model &&
                alpha_submission.draw.count > 0,
            "Fractional opacity did not blend a clipped prepared draw");
    platform::TLVertex alpha_vertex{};
    std::memcpy(&alpha_vertex, alpha_submission.vertices.data(), sizeof(alpha_vertex));
    require((alpha_vertex.diffuse >> 24) == 96,
            "CPU staged prepared alpha did not include node opacity");
    auto owned =
        cache.get(source, context, viewport, width, height, geometry, lighting, nullptr, false);
    same(*owned, reference());
    cc::PreparedDrawCache bounded(1024 * 1024, 1);
    const auto evicted = bounded.get(source, context, viewport, width, height, geometry, lighting);
    context.node = &actor_a;
    bounded.get(source, context, viewport, width, height, geometry, lighting);
    require(bounded.statistics().entries == 1 && bounded.statistics().bytes <= 1024 * 1024,
            "Prepared cache exceeded its bounds");
    same(*evicted, reference());
    cc::PreparedDrawCache tiny(1, 1);
    tiny.get(source, context, viewport, width, height, geometry, lighting);
    require(tiny.statistics().entries == 0 && tiny.statistics().bytes == 0,
            "Oversized staging entered the prepared cache");
    auto large_batch = batch;
    for (unsigned copy = 1; copy < 128; ++copy)
        large_batch.vertices.insert(large_batch.vertices.end(), batch.vertices.begin(),
                                    batch.vertices.end());
    source.batch = &large_batch;
    const auto clipped = reference();
    require(clipped.draw.lit_normals && !clipped.draw.lit_normals->empty(),
            "Clipped budget fixture has no normal stream");
    const auto payload = clipped.vertices.capacity() + sizeof(cc::PreparedSubmission) +
                         sizeof(*clipped.draw.sun_tl) + sizeof(*clipped.draw.lit_normals) +
                         clipped.draw.lit_normals->capacity() * sizeof(std::array<float, 3>) +
                         sizeof(*clipped.draw.raw_fog) +
                         clipped.draw.raw_fog->capacity() * sizeof(std::array<float, 4>);
    cc::PreparedDrawCache clipped_budget(payload - 1);
    clipped_budget.get(source, context, viewport, width, height, geometry, lighting);
    require(clipped_budget.statistics().entries == 0 && clipped_budget.statistics().bytes == 0,
            "Clipped normal payload escaped the prepared cache byte budget");
    source.batch = &batch;
    const auto valid_far = context.far_z;
    context.far_z = context.near_z;
    bool rejected = false;
    try {
        get();
    } catch (const std::runtime_error &) {
        rejected = true;
    }
    require(rejected, "Cache hid invalid clip planes");
    context.far_z = valid_far;
    same(*get(), reference());
    require(!first->vertices.empty() && !owned->vertices.empty(),
            "Eviction invalidated an owned result");
    {
        // Identical authored fog and geometry can still have different edge bands.
        // This fails if the new render-only band is omitted from the cache signature.
        const auto saved_fog = zmod::fog();
        zmod::fog() = {};
        platform::prepared::Batch edge_batch;
        edge_batch.color = 0xffffffff;
        edge_batch.vertices = {{-1, -1, 0, 0, 0, 1, 0, 0},
                               {1, -1, 0, 0, 0, 1, 1, 0},
                               {0, 1, 0, 0, 0, 1, .5f, 1}};
        cc::PreparedBatchDraw edge_source;
        edge_source.batch = &edge_batch;
        edge_source.camera = edge_source.world = mw34::donor::identity();
        edge_source.camera[11] = 750;
        platform::ModelDrawContext edge_context;
        edge_context.near_z = edge_context.clip_near = 1;
        edge_context.far_z = 800;
        edge_context.fx_near = edge_context.fy_near = 20;
        edge_context.cx = edge_context.cy = 32;
        cc::PreparedDrawCache edge_cache;
        const auto stage_edge = [&] {
            return edge_cache.get(edge_source, edge_context, viewport, width, height, geometry, false);
        };
        std::shared_ptr<const cc::PreparedSubmission> default_cover;
        {
            zmod::ScopedRenderFog scope(800, 800);
            default_cover = stage_edge();
        }
        {
            zmod::ScopedRenderFog scope(800, 1200);
            const auto extended_cover = stage_edge();
            require(extended_cover != default_cover &&
                        extended_cover->vertices != default_cover->vertices &&
                        edge_cache.statistics().misses == 2,
                    "Prepared staging reused fog from another view-distance edge band");
        }
        {
            zmod::ScopedRenderFog scope(800, 3200);
            edge_batch.vertices = {{-500, -100, 3000, 0, 0, 1, 0, 0},
                                   {500, -100, 3000, 0, 0, 1, 1, 0},
                                   {0, 100, 3400, 0, 0, 1, .5f, 1}};
            edge_source.camera = mw34::donor::identity();
            edge_context.far_z = 3200;
            const auto crossing = cc::prepare_draw(edge_source, edge_context, viewport, width,
                                                    height, geometry, false);
            require(!crossing.draw.model && crossing.clipped_triangles == 2,
                    "Crossing prepared fog fixture did not use CPU depth clipping");
            unsigned cut_vertices = 0;
            for (std::size_t offset = 0; offset < crossing.vertices.size();
                 offset += sizeof(platform::TLVertex)) {
                platform::TLVertex vertex;
                std::memcpy(&vertex, crossing.vertices.data() + offset, sizeof vertex);
                if (vertex.sz != 1.f / 3200.f) continue;
                require((vertex.specular >> 24) == 0,
                        "CPU prepared crossing retained visibility at the far cut");
                ++cut_vertices;
            }
            require(cut_vertices == 3, "CPU prepared crossing lost its triangulated cut vertices");
            edge_batch.vertices = {{-1, -1, 1000, 0, 0, 1, 0, 0},
                                   {1, -1, 1000, 0, 0, 1, 1, 0},
                                   {0, 1, 3400, 0, 0, 1, .5f, 1}};
            const auto interior = cc::prepare_draw(edge_source, edge_context, viewport, width,
                                                   height, geometry, false);
            require(!interior.draw.model && interior.draw.raw_fog &&
                        interior.draw.raw_fog->size() == interior.draw.count,
                    "Prepared interior fixture lost its parallel raw fog stream");
            bool negative_edge_factor = false;
            for (const auto &factors : *interior.draw.raw_fog) {
                require(factors[3] == 1.f && factors[0] == 0.f && factors[1] == 0.f,
                        "Prepared fog-off fixture acquired mission fog");
                negative_edge_factor = negative_edge_factor || factors[2] < -1.f;
            }
            require(negative_edge_factor,
                    "Prepared interior edge factors were clamped before rasterisation");
        }
        zmod::fog_set_on(1);
        zmod::fog_set_linear(1);
        zmod::fog_set_near(32);
        zmod::fog_set_far(750);
        zmod::fog_set_alt_low(1000);
        zmod::fog_set_alt_high(1001);
        edge_source.deformed = {{-1, -1, 600, 0, 0, 1, 0, 0},
                                {1, -1, 600, 0, 0, 1, 1, 0},
                                {0, 1, 600, 0, 0, 1, .5f, 1}};
        const auto unscoped = cc::prepare_draw(edge_source, edge_context, viewport, width, height,
                                               geometry, false);
        require(unscoped.draw.raw_fog && unscoped.draw.raw_fog->size() == 3,
                "Unscoped prepared fog lost its raw visibility stream");
        for (std::size_t index = 0; index < edge_source.deformed.size(); ++index) {
            const auto &raw_fog = unscoped.draw.raw_fog->at(index);
            const float visibility = 1.f - zmod::fog_at(edge_source.deformed[index].data());
            require(raw_fog[3] == 2.f && raw_fog[0] == visibility,
                    "Unscoped prepared fog changed fog_at's unquantised visibility");
        }
        zmod::fog() = saved_fog;
    }
}

static std::filesystem::path make_private_staging_dir(const char *prefix) {
    static std::atomic<std::uint32_t> s_seq{0};
    const auto pid =
#if defined(_WIN32)
        ::_getpid();
#else
        ::getpid();
#endif
    const auto seq = ++s_seq;
    const auto tick = std::chrono::high_resolution_clock::now().time_since_epoch().count();
    const auto p = std::filesystem::temp_directory_path() /
                   (std::string(prefix) + "_" + std::to_string(pid) + "_" + std::to_string(seq) +
                    "_" + std::to_string(tick));
    std::filesystem::create_directories(p);
    return p;
}

static void write_u32(std::string &out, std::uint32_t value) {
    for (unsigned i = 0; i < 4; ++i)
        out.push_back(static_cast<char>((value >> (i * 8)) & 0xffU));
}
static void write_u64(std::string &out, std::uint64_t value) {
    write_u32(out, static_cast<std::uint32_t>(value & 0xffffffffU));
    write_u32(out, static_cast<std::uint32_t>((value >> 32) & 0xffffffffU));
}
static void write_f32(std::string &out, float value) {
    std::uint32_t bits;
    std::memcpy(&bits, &value, 4);
    write_u32(out, bits);
}
static void write_str(std::string &out, const std::string &value) {
    write_u32(out, static_cast<std::uint32_t>(value.size()));
    out.append(value);
}

static std::string build_single_batch_bwsfm1(std::uint64_t mesh_hash, const std::string &asset_id,
                                             const std::string &material_name,
                                             float height_amp = -4.0f, float max_disp = 4.0f,
                                             float height_ref = 0.5f, float roughness = 0.7f,
                                             float reflectivity = 0.04f, float metallic = 0.0f) {
    using namespace mw34::materials;
    const std::array<unsigned char, 16> h_pixels{
        32, 0, 0, 255, 96, 0, 0, 255, 160, 0, 0, 255, 224, 0, 0, 255,
    };
    std::string out("BWSFM1\0\0", 8);
    write_u32(out, 1U);        // version
    write_u32(out, 1U);        // batch_count = 1
    write_u32(out, 1U);        // record_count = 1
    write_u32(out, 1U);        // image_count = 1
    write_u64(out, mesh_hash); // mesh_uv_hash

    // Batch 0 -> record 0
    write_u32(out, 0U);

    // Record 0
    write_str(out, asset_id);
    write_str(out, material_name);
    write_u32(out, 0U);               // height_image = 0
    write_u32(out, no_surface_image); // thick_image = none
    write_f32(out, height_ref);
    write_f32(out, height_amp);
    write_f32(out, max_disp);
    write_u32(out, 1U);   // tess_cap
    write_f32(out, 1.0f); // uv_scale[0]
    write_f32(out, 1.0f); // uv_scale[1]
    write_f32(out, 0.0f); // uv_offset[0]
    write_f32(out, 0.0f); // uv_offset[1]
    write_u32(out, surface_address_wrap);
    write_u32(out, surface_address_wrap);
    write_f32(out, 0.0f); // atlas_rect
    write_f32(out, 0.0f);
    write_f32(out, 1.0f);
    write_f32(out, 1.0f);
    write_f32(out, 0.0f); // sss_participation
    write_f32(out, 0.0f);
    write_f32(out, 0.0f);
    write_f32(out, 0.0f);
    write_f32(out, 0.0f); // sss_radius
    write_f32(out, 0.0f); // thickness_scale
    write_f32(out, roughness);
    write_f32(out, reflectivity);
    write_f32(out, metallic);

    // Image 0
    write_str(out, "h_img");
    write_u32(out, surface_role_height);
    write_u32(out, 2U);
    write_u32(out, 2U);
    write_u64(out, normal_hash(h_pixels.data(), h_pixels.size()));
    out.append(reinterpret_cast<const char *>(h_pixels.data()), h_pixels.size());

    return out;
}

static std::string build_valid_v4_mesh(const std::string &toe_name = "",
                                       const std::string &batch_owner = "control",
                                       const std::string &batch_visibility = "panel",
                                       double toe_x = 0.5, double toe_y = 0.2, double toe_z = -0.1) {
    return prepared_fixture::build_valid_v4_mesh(toe_name, batch_owner, batch_visibility, toe_x,
                                                 toe_y, toe_z);
}

void check_prepared_models_surface_materials() {
    const auto temp_dir = make_private_staging_dir("mw34_pm_materials");
    struct Cleanup {
        std::filesystem::path p;
        ~Cleanup() {
            std::error_code ec;
            std::filesystem::remove_all(p, ec);
        }
    } cleanup{temp_dir};

    const auto mesh_path = temp_dir / "mesh.bin";
    const auto v4_mesh_path = temp_dir / "mesh_v4.bin";
    const auto tex_path = temp_dir / "textures.bin";
    const auto mat_path = temp_dir / "materials.bin";

    {
        std::ofstream(mesh_path, std::ios::binary) << prepared_fixture::mesh(2);
        std::ofstream(v4_mesh_path, std::ios::binary) << build_valid_v4_mesh();
        std::ofstream(tex_path, std::ios::binary) << prepared_fixture::textures();
    }

    std::uint64_t mesh_uv_hash = 0;
    {
        std::ifstream mf(mesh_path, std::ios::binary);
        const auto m = platform::prepared::read_mesh(mf);
        mesh_uv_hash = mw34::materials::compute_mesh_uv_hash(m.batches, 0, m.batches.size());
    }

    {
        std::ofstream f(mat_path, std::ios::binary);
        f << build_single_batch_bwsfm1(mesh_uv_hash, "authored:close", "authored", -4.0f, 4.0f,
                                       0.5f);
    }

    std::unique_ptr<zcls::Node, int (*)(zcls::Node *)> root(zcls::object3d_create(),
                                                            zcls::tree_destroy);
    auto *control = zcls::object3d_create(), *panel = zcls::object3d_create(),
         *torso = zcls::object3d_create();
    require(root && control && panel && torso &&
                zcls::object3d_add_child(root.get(), control) == 0 &&
                zcls::object3d_add_child(control, panel) == 0 &&
                zcls::object3d_add_child(root.get(), torso) == 0,
            "Node hierarchy setup failed");
    zcls::node_set_name(root.get(), "actor");
    zcls::node_set_name(control, "control");
    zcls::node_set_name(panel, "panel");
    zcls::node_set_name(torso, "torso");
    auto asset = std::make_shared<zcls::SourceAsset>();
    asset->name = "mech_authored.flt";
    asset->nodes = {{"actor", 1}, {"control", 1}, {"panel", 1}, {"torso", 1}};
    root->source_asset = control->source_asset = panel->source_asset = torso->source_asset = asset;
    root->source_asset_root = true;
    zmod::Model model{};
    const std::uint32_t count = 3;
    std::memcpy(model.header + 0x14, &count, sizeof count);
    panel->model = &model;
    panel->source_model_vertices = count;
    struct ModelPointer {
        zcls::Node *node;
        ~ModelPointer() { node->model = nullptr; }
    } model_pointer{panel};

    std::array<float, 12> matrix{1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0};
    platform::ModelDrawContext context{};
    context.node = panel;
    context.ordinary = true;
    context.source_vertices = count;
    context.source_polygons = 1;
    context.model_to_camera = context.model_to_world = matrix.data();
    context.opacity = 1;
    // The fading submission uses the native clip-plane contract, not just model binding.
    context.near_z = context.clip_near = .1f;
    context.far_z = 100;
    context.fx_near = context.fy_near = 50;
    context.cx = context.cy = 32;

    matrix[9] = 12;
    std::vector<std::uintptr_t> ancestry;
    const auto socket = cc_mw3_re::original_headlight_socket(context, "control", &ancestry);
    require(socket && (*socket)[3] == 12, "Headlight socket lost the native world transform");
    require(ancestry.size() == 2 && ancestry[0] == reinterpret_cast<std::uintptr_t>(control) &&
                ancestry[1] == reinterpret_cast<std::uintptr_t>(root.get()),
            "Headlight socket ancestry chain mismatch");
    require(!cc_mw3_re::original_headlight_socket(context, "missing", &ancestry),
            "Headlight socket accepted an unknown control");
    require(ancestry.empty(), "Unknown control left ancestry non-empty");
    panel->source_asset = std::make_shared<zcls::SourceAsset>(*asset);
    require(!cc_mw3_re::original_headlight_socket(context, "control"),
            "Headlight socket crossed a source asset boundary");
    panel->source_asset = asset;
    matrix[9] = 0;

    sdlfe::CoreCriticalAssets options;
    options.models.push_back({"authored", "0", mesh_path.string(), tex_path.string()});

    auto mat_binding = [](const std::string &c, const std::string &l,
                          const std::filesystem::path &p) {
        return std::vector<cc_mw3_re::PreparedMaterialBinding>{{c, l, p.string()}};
    };

    // The launcher stores explicit --cc-model-materials selections on the
    // runtime options object consumed by FrameRenderer.
    options.materials.push_back({"authored", "0", mat_path.string()});
    cc_mw3_re::PreparedModels launcher_selected(options, options.materials);
    const auto launcher_draw = launcher_selected.draw(context);
    require(launcher_draw.batches.size() == 1 &&
                launcher_draw.batches[0].surface_material != nullptr,
            "Core Critical runtime options did not bind the selected surface materials");

    // Skin switching uses the production selection path, including the Lab's
    // independent node instance and distinct close/distance payloads.
    {
        auto skin_options = options;
        skin_options.models.push_back({"authored", "1", mesh_path.string(), tex_path.string()});
        for (int index = 1; index <= 7; ++index) {
            for (int lod = 0; lod != 2; ++lod) {
                const auto path = temp_dir / ("skin-" + std::to_string(index) + "-" + std::to_string(lod));
                auto bytes = prepared_fixture::textures();
                bytes[bytes.size() - 4] = char(index + lod * 16);
                std::ofstream(path, std::ios::binary) << bytes;
                skin_options.skins.push_back({"authored", std::to_string(lod), path.string(), index});
            }
        }
        const auto catalog_path = temp_dir / "skins.bin";
        prepared_fixture::Bytes catalog;
        catalog.value.assign("BWSKIN1\0", 8);
        catalog.u32(2);
        const auto catalog_text = [&](const std::string &text) {
            catalog.u32(static_cast<uint32_t>(text.size()));
            catalog.value += text;
        };
        for (const auto &text : {std::string("test.paint:sommerset"), std::string("Sommerset"),
                                std::string("authored"), tex_path.string(), tex_path.string()})
            catalog_text(text);
        for (const auto &text : {std::string("com.corecritical.marauder.gunmetal:gunmetal-worn"),
                                std::string("Gun Metal - Worn"), std::string("com.corecritical.marauder:mech"),
                                tex_path.string(), tex_path.string()})
            catalog_text(text);
        std::ofstream(catalog_path, std::ios::binary) << catalog.value;
        const auto prior_catalog = platform::prepared::configured_skin_catalog();
        struct RestoreCatalog {
            std::shared_ptr<const platform::prepared::SkinCatalog> value;
            ~RestoreCatalog() { platform::prepared::configured_skin_catalog() = value; }
        } restore_catalog{prior_catalog};
        platform::prepared::configure_skin_catalog(catalog_path.string());
        require(platform::prepared::configured_skin_catalog()->size() == 2 &&
                    platform::prepared::configured_skin_catalog()->front().chassis == "com.corecritical.marauder:mech",
                "Catalog lost a namespaced added-chassis skin identity");
        cc_mw3_re::PreparedModels skins(skin_options, skin_options.materials);
        require(skins.skin_texture_loads() == 0, "Alternate textures loaded eagerly");
        require(skins.skin_cache_budget() >= 1024ULL * 1024 * 1024,
                "PreparedModels skin cache budget below default");
        cc_mw3_re::PreparedSkinCache default_skin_cache;
        require(default_skin_cache.budget() >= 1024ULL * 1024 * 1024,
                "PreparedSkinCache budget below default");
        const auto primary = skins.draw(context).batches[0].texture;
        for (int lod = 0; lod != 2; ++lod) {
            asset->name = lod ? "mech_authored_1.flt" : "mech_authored.flt";
            for (int index = 1; index <= 7; ++index) {
                panel->prepared_skin_index = index;
                const auto selected = skins.draw(context);
                require(selected.batches.size() == 1 && selected.batches[0].texture_owner &&
                            (selected.batches[0].texture->pixels[0] & 255) == unsigned(index + lod * 16),
                        "Retail skin index selected the wrong LOD texture");
                require(!selected.batches[0].height_binding && !selected.batches[0].surface_material,
                        "Alternate albedo inherited a primary-only material identity");
                const auto repeated = skins.draw(context);
                require(repeated.batches[0].texture == selected.batches[0].texture,
                        "Repeated skin draw decoded a new texture set");
                require(skins.skin_cache_evictions() == 0,
                        "Skin cache evicted entries during reuse");
                panel->prepared_skin_index = 0;
                require(!skins.draw(context).batches[0].texture_owner,
                        "Skin selection leaked into the primary instance state");
            }
        }
        require(skins.skin_texture_loads() == 14, "Retail skin cache did not reuse decodes");
        require(skins.skin_cache_evictions() == 0, "Retail skin cache had evictions during reuse");
        {
            std::ifstream norm_mesh_in(mesh_path, std::ios::binary);
            const auto norm_mesh = platform::prepared::read_mesh(norm_mesh_in);
            const auto canonical_path = tex_path.string();
            const auto noncanonical_path = (tex_path.parent_path() / "." / tex_path.filename()).string();
            require(cc_mw3_re::PreparedSkinCache::normalize_key(noncanonical_path) ==
                        cc_mw3_re::PreparedSkinCache::normalize_key(canonical_path),
                    "normalize_key produced unequal paths");
            const auto first_res = default_skin_cache.resolve(noncanonical_path, norm_mesh);
            const auto second_res = default_skin_cache.resolve_normalized(
                cc_mw3_re::PreparedSkinCache::normalize_key(canonical_path), norm_mesh);
            require(first_res == second_res,
                    "normalize_key and resolve_normalized did not reuse shared_ptr");
            require(default_skin_cache.loads() == 1,
                    "Normalized skin cache resolution did not reuse existing load");
            require(default_skin_cache.evictions() == 0,
                    "Normalized skin cache resolution caused unexpected eviction");
        }
        prepared_fixture::Bytes binding_index;
        binding_index.value = "BWSKIDX1";
        binding_index.u32(1);
        binding_index.u32(8);
        binding_index.value += "authored";
        binding_index.u32(0);
        binding_index.u32(1);
        const auto binding_path = (temp_dir / "skin-1-0").string();
        binding_index.u32(static_cast<uint32_t>(binding_path.size()));
        binding_index.value += binding_path;
        std::istringstream binding_input(binding_index.value);
        const auto compact_bindings = platform::prepared::read_skin_bindings(binding_input);
        auto compact_options = options;
        for (const auto &binding : compact_bindings)
            compact_options.skins.push_back({binding.chassis, std::to_string(binding.lod), binding.path,
                                            static_cast<int32_t>(binding.index)});
        cc_mw3_re::PreparedModels compact_models(compact_options, compact_options.materials);
        asset->name = "mech_authored.flt";
        panel->prepared_skin_index = 1;
        const auto compact_draw = compact_models.draw(context);
        require(compact_draw.batches[0].texture_owner &&
                    (compact_draw.batches[0].texture->pixels[0] & 255) == 1,
                "Compact stock binding index did not reach prepared texture selection");
        auto duplicate_binding = binding_index.value;
        duplicate_binding[8] = 2;
        duplicate_binding += binding_index.value.substr(12);
        auto invalid_lod = binding_index.value;
        invalid_lod[24] = 2;
        auto invalid_skin = binding_index.value;
        invalid_skin[28] = 8;
        for (const auto &bad : {binding_index.value.substr(0, binding_index.value.size() - 1),
                               binding_index.value + "x", duplicate_binding, invalid_lod, invalid_skin}) {
            std::istringstream input(bad);
            bool rejected = false;
            try { platform::prepared::read_skin_bindings(input); }
            catch (const std::exception &) { rejected = true; }
            require(rejected, "Compact binding index accepted malformed or duplicate metadata");
        }
        asset->name = "mech_authored_1.flt";
        panel->prepared_skin_index = 8;
        const auto added_distance = skins.draw(context);
        asset->name = "mech_authored.flt";
        const auto added_close = skins.draw(context);
        require(added_distance.batches[0].texture_owner == added_close.batches[0].texture_owner,
                "Catalog skin shared between LODs decoded twice");
        panel->prepared_skin_index = 999;
        require(skins.draw(context).batches[0].texture == primary,
                "Unknown skin failed to fall back to primary");
        for (const auto index : {-1, 135}) {
            panel->prepared_skin_index = index;
            require(skins.draw(context).batches[0].texture == primary,
                    "Invalid skin failed to fall back to primary");
        }
        const auto absent = temp_dir / "absent-skin";
        const auto corrupt = temp_dir / "corrupt-skin";
        std::ofstream(corrupt) << "bad";
        skin_options.skins.push_back({"authored", "0", absent.string(), 9});
        skin_options.skins.push_back({"authored", "0", corrupt.string(), 10});
        cc_mw3_re::PreparedModels fallbacks(skin_options, skin_options.materials);
        for (const auto index : {9, 10}) {
            panel->prepared_skin_index = index;
            require(!fallbacks.draw(context).batches[0].texture_owner,
                    "Missing/corrupt skin did not fall back to primary");
            require(!fallbacks.draw(context).batches[0].texture_owner,
                    "Failed skin lookup was not stable");
        }
        cc_mw3_re::PreparedSkinCache tiny_cache(1);
        std::ifstream mesh_input(mesh_path, std::ios::binary);
        const auto mesh = platform::prepared::read_mesh(mesh_input);
        auto owned = tiny_cache.resolve(tex_path.string(), mesh);
        std::weak_ptr<const platform::prepared::Textures> old = owned;
        tiny_cache.resolve((temp_dir / "skin-1-0").string(), mesh);
        require(tiny_cache.evictions() == 1, "Tiny cache eviction count mismatch");
        require(!old.expired(), "Eviction invalidated a retained draw");
        owned.reset();
        require(old.expired(), "Eviction retained unused skin pixels");
        require(tiny_cache.loads() == 2, "Tiny cache decode accounting mismatch");
        tiny_cache.clear();
        require(tiny_cache.bytes() == 0, "Skin cache reset retained decoded bytes");
        require(tiny_cache.loads() == 2 && tiny_cache.evictions() == 1,
                "Skin cache clear did not preserve cumulative loads and evictions");
        for (const auto &bad : {catalog.value.substr(0, catalog.value.size() - 1), catalog.value + "x"}) {
            std::istringstream input(bad);
            bool rejected = false;
            try { platform::prepared::read_skin_catalog(input); }
            catch (const std::exception &) { rejected = true; }
            require(rejected, "Catalog accepted truncated or trailing data");
        }
        panel->prepared_skin_index = 0;
        std::puts("Prepared skins: retail both LODs, catalog, lazy cache, reuse, fallback and eviction passed");
    }

    // A resolved height image survives both its source model collection and a
    // queued draw copy. Neither a borrowed pack index nor host texture slot can
    // establish that ownership.
    {
        const auto normal_path = temp_dir / "normals.bin";
        std::ofstream(normal_path, std::ios::binary) << prepared_fixture::normals(0xffff8080);
        auto owned_options = options;
        owned_options.normals.push_back({"authored", "0", normal_path.string()});
        std::shared_ptr<const mw34::materials::HeightBinding> retained;
        std::shared_ptr<mw34::materials::SurfaceDecodedBudget> retained_budget;
        {
            cc_mw3_re::PreparedModels models(owned_options, mat_binding("authored", "0", mat_path));
            retained_budget = models.surface_budget();
            const auto selected = models.draw(context);
            require(selected.batches.size() == 1 && selected.batches[0].height_binding,
                    "Prepared height image was not resolved while its pack was owned");
            const auto &source = selected.batches[0];
            mw34::vkscene::Draw baseline{}, off{}, on{};
            cc_mw3_re::apply_surface_material(baseline, source, true);
            cc_mw3_re::apply_surface_material(off, source, true, false, 7, 11);
            require(!off.height_binding && off.surface_parameters == baseline.surface_parameters &&
                        off.surface_eye == baseline.surface_eye,
                    "Height-Off changed the original normal-only material output");
            cc_mw3_re::apply_surface_material(on, source, true, true, 7, 11);
            retained = on.height_binding;
            require(retained && retained->image == source.height_binding->image &&
                        retained->producer_epoch == 7 && retained->texture_version == 11 &&
                        retained->source_sha256.size() == 64 &&
                        retained->sidecar_sha256.size() == 64 &&
                        retained->mesh_uv_hash == mesh_uv_hash &&
                        retained->material.height_amplitude == -4.f,
                    "Owned draw lost its source/image/chart/epoch metadata");
            require(mw34::materials::height_binding_bytes({retained, retained}, 16) == 16,
                    "Repeated alias owner was charged once per draw instead of once per packet");
            bool rejected = false;
            try {
                (void)mw34::materials::height_binding_bytes({retained}, 15);
            } catch (const std::runtime_error &) {
                rejected = true;
            }
            require(rejected, "Height decoded-owner budget was not checked");
            auto replacement = std::make_shared<mw34::materials::HeightBinding>(*retained);
            replacement->image =
                std::make_shared<const mw34::materials::SurfaceMaterialImage>(*retained->image);
            require(!mw34::materials::same_height_binding(retained, replacement) &&
                        mw34::materials::height_binding_bytes({retained, replacement}, 32) == 32,
                    "A replacement image inherited an older allocation owner");
            rejected = false;
            try {
                (void)mw34::materials::height_binding_bytes({retained, replacement}, 31);
            } catch (const std::runtime_error &) {
                rejected = true;
            }
            require(rejected, "Queued replacement owners exceeded the decoded budget");
            for (unsigned field = 0; field != 6; ++field) {
                auto changed = std::make_shared<mw34::materials::HeightBinding>(*retained);
                switch (field) {
                case 0: ++changed->producer_epoch; break;
                case 1: ++changed->texture_version; break;
                case 2: ++changed->image_version; break;
                case 3: changed->material.uv_scale[0] = -1; break;
                case 4: changed->material.height_amplitude = 0; break;
                case 5: ++changed->albedo.hash; break;
                }
                require(!mw34::materials::same_height_binding(retained, changed),
                        "Coalescing ignored changed height binding state");
            }
            std::istringstream limited(build_single_batch_bwsfm1(
                mesh_uv_hash, "authored:close", "authored"));
            rejected = false;
            try {
                (void)mw34::materials::read_surface_materials(
                    limited, "authored:close", mesh_uv_hash, {"authored"},
                    mw34::materials::max_surface_sidecar_bytes, 15);
            } catch (const std::runtime_error &) {
                rejected = true;
            }
            require(rejected, "Decoded limit was not enforced before the height image allocation");
        }
        require(retained && retained->image->pixels.size() == 4 &&
                    retained->material.material_name == "authored" && retained_budget->used() == 16,
                "Queued height image died with PreparedModels");
        retained.reset();
        require(retained_budget->used() == 0, "Final queued model image did not release its reservation");
        {
            auto selected_environment = std::make_shared<platform::prepared::EnvironmentSelection>();
            selected_environment->surface_budget =
                std::make_shared<mw34::materials::SurfaceDecodedBudget>(16);
            auto shared_options = owned_options;
            shared_options.environment = selected_environment;
            std::shared_ptr<const mw34::materials::HeightBinding> queued;
            {
                cc_mw3_re::PreparedModels current(shared_options, mat_binding("authored", "0", mat_path));
                queued = current.draw(context).batches[0].height_binding;
            }
            bool refused = false;
            try {
                cc_mw3_re::PreparedModels replacement(shared_options,
                                                      mat_binding("authored", "0", mat_path));
            } catch (const std::runtime_error &) {
                refused = true;
            }
            require(refused && selected_environment->surface_budget->used() == 16,
                    "Model reload allocated without charging its queued old owner");
            queued.reset();
            require(selected_environment->surface_budget->used() == 0,
                    "Model queue retirement did not release the shared selection budget");
            cc_mw3_re::PreparedModels replacement(shared_options,
                                                  mat_binding("authored", "0", mat_path));
            require(selected_environment->surface_budget->used() == 16,
                    "Model reload failed to reuse returned decoded capacity");
        }

        // The documented/Python LOD identity is :distance. It must not silently
        // inherit the close material or the native reader's old :far typo.
        const auto distance_path = temp_dir / "distance-materials.bin";
        std::ofstream(distance_path, std::ios::binary)
            << build_single_batch_bwsfm1(mesh_uv_hash, "authored:distance", "authored");
        owned_options.models[0].lod = "1";
        owned_options.normals[0].lod = "1";
        asset->name = "mech_authored_1.flt";
        cc_mw3_re::PreparedModels distance(owned_options,
                                          mat_binding("authored", "1", distance_path));
        const auto distance_draw = distance.draw(context);
        require(distance_draw.batches.size() == 1 && distance_draw.batches[0].height_binding &&
                    distance_draw.batches[0].height_binding->material.asset_id == "authored:distance",
                "Canonical distance LOD source key was not admitted");
        bool rejected = false;
        try {
            cc_mw3_re::PreparedModels wrong(owned_options, mat_binding("authored", "1", mat_path));
        } catch (const std::runtime_error &) {
            rejected = true;
        }
        require(rejected, "Distance LOD inherited the close source key");
        asset->name = "mech_authored.flt";
    }

    // 1. Positive test: PreparedModels loads valid BWSFM1 and exposes it on
    // PreparedBatchDraw
    {
        cc_mw3_re::PreparedModels models(options, mat_binding("authored", "0", mat_path));
        require(models.has_binding(context), "PreparedModels missing binding for authored node");
        require(!models.donor_headlight_socket(context, "torso"),
                "donor_headlight_socket accepted non-v4 mesh");
        require(!models.donor_headlight_socket(context, ""),
                "donor_headlight_socket accepted empty bone name");
        require(!models.donor_headlight_socket({}, "torso"),
                "donor_headlight_socket accepted empty context");
        std::vector<std::uintptr_t> test_ancestry = {1, 2, 3};
        require(!models.donor_headlight_socket(context, "torso", &test_ancestry),
                "donor_headlight_socket accepted non-v4 mesh with ancestry");
        require(test_ancestry.empty(), "donor_headlight_socket failed to clear ancestry");
        const auto draw = models.draw(context);
        require(draw.batches.size() == 1, "Draw batches count mismatch");
        require(draw.batches[0].surface_material != nullptr,
                "surface_material pointer was null on positive draw");
        require(draw.batches[0].surface_material->height_amplitude == -4.0f,
                "height_amplitude mismatch");
        require(draw.batches[0].surface_material->max_displacement == 4.0f,
                "max_displacement mismatch");
        require(draw.batches[0].surface_material->roughness == 0.7f, "Default roughness mismatch");
        require(draw.batches[0].surface_material->reflectivity == 0.04f,
                "Default reflectivity mismatch");
        require(draw.batches[0].surface_material->metallic == 0.0f, "Default metallic mismatch");
        require(draw.batches[0].surface_material->material_name == "authored",
                "material_name mismatch");

        auto fading_context = context;
        fading_context.opacity = 0.375f;
        const auto fading_draw = models.draw(fading_context);
        require(fading_draw.replace && fading_draw.batches.size() == 1,
                "Fractional node opacity declined the prepared model draw");
        const auto fading_submission = cc_mw3_re::prepare_draw(
            fading_draw.batches[0], fading_context, {0, 0, 64, 64}, 64, 64,
            std::make_shared<mw34::vkscene::ModelGeometry>(), false);
        require(fading_submission.draw.key.blend && fading_submission.draw.key.src == 5 &&
                    fading_submission.draw.key.dst == 6 && !fading_submission.draw.key.zwrite &&
                    fading_submission.draw.key.cull == 1 && fading_submission.draw.model &&
                    fading_submission.draw.count == 3 &&
                    !(fading_submission.draw.push.mode[0] & 32U) &&
                    fading_submission.draw.push.mode[2] == 2U &&
                    [&] {
                        float opacity{};
                        const auto bits = fading_submission.draw.push.mode[3];
                        std::memcpy(&opacity, &bits, sizeof(opacity));
                        return opacity == fading_context.opacity;
                    }(),
                "Prepared fade did not select source-alpha blending with native opacity");
        const auto opaque_submission = cc_mw3_re::prepare_draw(
            draw.batches[0], context, {0, 0, 64, 64}, 64, 64,
            std::make_shared<mw34::vkscene::ModelGeometry>(), false);
        float opaque_opacity{};
        const auto opaque_bits = opaque_submission.draw.push.mode[3];
        std::memcpy(&opaque_opacity, &opaque_bits, sizeof(opaque_opacity));
        require(!opaque_submission.draw.key.blend && opaque_submission.draw.key.zwrite &&
                    opaque_submission.draw.key.cull == 1 && opaque_opacity == 1.f,
                "Opaque prepared draw lost depth writes, culling or full opacity");

        std::unique_ptr<zcls::Node, int (*)(zcls::Node *)> world_root(zcls::object3d_create(),
                                                                       zcls::tree_destroy);
        require(world_root && zcls::node_remove_child(root.get(), control) == 0 &&
                    zcls::object3d_add_child(world_root.get(), control) == 0,
                "Detached source subtree setup failed");
        // The detached control still owns the batch, but panel submits its visible geometry.
        auto detached_context = context;
        const auto detached_draw = models.draw(detached_context);
        require(detached_draw.replace && detached_draw.batches.size() == 1,
                "Prepared binding was lost when a detached part crossed into the world tree");
        zcls::node_remove_child(world_root.get(), control);
        require(zcls::object3d_add_child(root.get(), control) == 0,
                "Detached source subtree restore failed");
    }

    // The original root is renamed to "deadmech" during death. Its visual
    // identity must still resolve the root-owned prepared batch.
    {
        const auto root_mesh_path = temp_dir / "root_mesh.bin";
        std::ofstream(root_mesh_path, std::ios::binary)
            << prepared_fixture::mesh(2, 0xffffffff, {0, 0, 1}, false, false, false, "actor",
                                      "actor");
        auto root_options = options;
        root_options.models[0].mesh = root_mesh_path.string();
        cc_mw3_re::PreparedModels root_models(
            root_options, mat_binding("authored", "0", mat_path));

        root->model = &model;
        root->source_model_vertices = count;
        root->source_asset_root_name = "actor";
        zcls::node_set_name(root.get(), "deadmech");
        auto dead_context = context;
        dead_context.node = root.get();
        const auto dead_draw = root_models.draw(dead_context);
        root->model = nullptr;
        zcls::node_set_name(root.get(), "actor");
        root->source_asset_root_name.clear();
        require(dead_draw.replace && dead_draw.batches.size() == 1,
                "Prepared root batch was lost when death renamed the mech node");
    }

    // A recognized mech asset uses the available prepared LOD when its exact
    // full or distance payload was not selected.
    {
        asset->name = "mech_authored_1.flt";
        cc_mw3_re::PreparedModels nearest_lod(options);
        require(nearest_lod.has_binding(context),
                "Prepared LOD fallback was not exposed to the render adapter");
        const auto fallback_draw = nearest_lod.draw(context);
        require(fallback_draw.replace && fallback_draw.batches.size() == 1,
                "Unbound distance LOD did not use its closest prepared model");
        asset->name = "mech_authored.flt";
    }

    // 1b. Positive test: PreparedModels version 4 mesh donor_headlight_socket with ancestry
    {
        matrix[9] = 12;
        sdlfe::CoreCriticalAssets v4_options;
        v4_options.models.push_back({"authored", "0", v4_mesh_path.string(), tex_path.string()});
        cc_mw3_re::PreparedModels v4_models(v4_options);
        std::vector<std::uintptr_t> v4_ancestry;
        const auto v4_socket =
            v4_models.donor_headlight_socket(context, "Torso_Twist", &v4_ancestry);
        require(v4_socket.has_value(), "donor_headlight_socket failed on valid v4 mesh bone");
        require(v4_ancestry.size() == 2 &&
                    v4_ancestry[0] == reinterpret_cast<std::uintptr_t>(torso) &&
                    v4_ancestry[1] == reinterpret_cast<std::uintptr_t>(root.get()),
                "donor_headlight_socket ancestry mismatch");
        require((*v4_socket)[3] == 12, "donor_headlight_socket lost native world transform");
        const auto v4_alias = v4_models.donor_headlight_socket(context, "torso");
        require(v4_alias.has_value() && (*v4_alias)[3] == 12,
                "donor_headlight_socket failed on bone control alias");
        std::vector<std::uintptr_t> pelvis_ancestry = {99};
        const auto pelvis_socket =
            v4_models.donor_headlight_socket(context, "Pelvis", &pelvis_ancestry);
        require(pelvis_socket.has_value(),
                "donor_headlight_socket failed for bone without control target");
        require(pelvis_ancestry.empty(), "bone without control target should have empty ancestry");
        require(!v4_models.donor_headlight_socket(context, "nonexistent"),
                "donor_headlight_socket accepted nonexistent bone");
        matrix[9] = 0;
    }

    // 2. Stock / No-Sidecar Control: surface_material must be nullptr
    {
        cc_mw3_re::PreparedModels stock_models(options);
        const auto stock_draw = stock_models.draw(context);
        require(stock_draw.batches.size() == 1, "Stock draw batches count mismatch");
        require(stock_draw.batches[0].surface_material == nullptr,
                "surface_material must be null for stock model without sidecar");
    }

    // 3. Wrong Asset ID Rejection
    {
        const auto bad_asset_path = temp_dir / "bad_asset.bin";
        {
            std::ofstream f(bad_asset_path, std::ios::binary);
            f << build_single_batch_bwsfm1(mesh_uv_hash, "wrong_chassis:close", "authored");
        }
        bool rejected = false;
        try {
            cc_mw3_re::PreparedModels bad_models(options,
                                                 mat_binding("authored", "0", bad_asset_path));
        } catch (const std::runtime_error &) {
            rejected = true;
        }
        require(rejected, "PreparedModels accepted BWSFM1 with mismatched asset ID");
    }

    // 4. Wrong Mesh UV Hash Rejection
    {
        const auto bad_uv_path = temp_dir / "bad_uv.bin";
        {
            std::ofstream f(bad_uv_path, std::ios::binary);
            f << build_single_batch_bwsfm1(mesh_uv_hash ^ 0xbadULL, "authored:close", "authored");
        }
        bool rejected = false;
        try {
            cc_mw3_re::PreparedModels bad_uv_models(options,
                                                    mat_binding("authored", "0", bad_uv_path));
        } catch (const std::runtime_error &) {
            rejected = true;
        }
        require(rejected, "PreparedModels accepted BWSFM1 with mismatched mesh UV hash");
    }

    // 5. Wrong Material Name Rejection
    {
        const auto bad_mat_path = temp_dir / "bad_mat.bin";
        {
            std::ofstream f(bad_mat_path, std::ios::binary);
            f << build_single_batch_bwsfm1(mesh_uv_hash, "authored:close", "WrongMat");
        }
        bool rejected = false;
        try {
            cc_mw3_re::PreparedModels bad_mat_models(options,
                                                     mat_binding("authored", "0", bad_mat_path));
        } catch (const std::runtime_error &) {
            rejected = true;
        }
        require(rejected, "PreparedModels accepted BWSFM1 with mismatched batch material name");
    }

    // 6. Unmatched Sidecar Selection Rejection
    {
        bool rejected = false;
        try {
            cc_mw3_re::PreparedModels unmatched_models(
                options, mat_binding("unmatched_chassis", "0", mat_path));
        } catch (const std::runtime_error &) {
            rejected = true;
        }
        require(rejected, "PreparedModels accepted unmatched chassis selection");
    }

    // 7. Independent Effect Enablement: metadata populated regardless of lighting
    // setting
    {
        sdlfe::CoreCriticalAssets off_options = options;
        off_options.lighting = "off";
        cc_mw3_re::PreparedModels off_models(off_options, mat_binding("authored", "0", mat_path));
        const auto off_draw = off_models.draw(context);
        require(off_draw.batches.size() == 1, "Off draw batches count mismatch");
        require(off_draw.batches[0].surface_material != nullptr,
                "surface_material metadata must be available when lighting is off");
    }
}

void check_prepared_models_donor_toe_admission() {
    const auto folder = make_private_staging_dir("mw34_pm_toe");
    struct Cleanup {
        std::filesystem::path path;
        ~Cleanup() { std::error_code error; std::filesystem::remove_all(path, error); }
    } cleanup{folder};
    const auto mesh_path = folder / "mesh.bin", texture_path = folder / "textures.bin";
    const auto normal_path = folder / "normals.bin", material_path = folder / "materials.bin";
    auto write = [](const auto &path, const std::string &bytes) {
        std::ofstream output(path, std::ios::binary);
        output.write(bytes.data(), bytes.size());
        require(bool(output), "Could not write donor fixture");
    };
    write(texture_path, prepared_fixture::textures());
    write(normal_path, prepared_fixture::normals());
    auto options = [&](const std::string &chassis = "authored", const std::string &lod = "1") {
        sdlfe::CoreCriticalAssets assets;
        assets.models.push_back({chassis, lod, mesh_path.string(), texture_path.string()});
        return assets;
    };
    unsigned cases = 0;

    // A detached donor limb has no torso placement frame. It must retain its
    // native geometry instead of entering donor_pose and throwing.
    {
        write(mesh_path, prepared_fixture::build_valid_v4_mesh("", "larm", "larm"));
        auto assets = options();
        prepared_fixture::DonorTree tree("", false);
        auto world = std::unique_ptr<zcls::Node, int (*)(zcls::Node *)>(
            zcls::object3d_create(), zcls::tree_destroy);
        auto *limb = tree.controls.at("larm");
        require(world && zcls::node_remove_child(tree.root.get(), limb) == 0 &&
                    zcls::object3d_add_child(world.get(), limb) == 0,
                "Detached donor limb fixture setup failed");
        limb->model = &tree.model;
        limb->source_model_vertices = 3;
        auto context = tree.context();
        context.node = limb;
        cc_mw3_re::PreparedModels models(assets);
        const auto draw = models.draw(context);
        limb->model = nullptr;
        require(!draw.replace && draw.batches.empty(),
                "Detached donor limb without torso did not decline cleanly");
        ++cases;
    }

    // Both cross-LOD directions must decline before strict donor/batch binding
    // when the selected geometry needs a frame absent from the live hierarchy.
    for (const std::string selected_lod : {"0", "1"}) {
        for (const bool missing_batch_frame : {false, true}) {
            const std::string toe = "rtoe02";
            // Isolate each guard: the batch-only case needs a live rig reference,
            // while the rig-only case needs every batch frame to be present.
            const std::string rig_reference = missing_batch_frame ? "control" : toe;
            const std::string batch_owner = missing_batch_frame ? toe : "control";
            write(mesh_path, prepared_fixture::build_valid_v4_mesh(
                rig_reference, batch_owner));
            auto assets = options("authored", selected_lod);
            prepared_fixture::DonorTree tree(toe, false);
            tree.asset->name = selected_lod == "0" ? "mech_authored_1.flt" : "mech_authored.flt";
            const auto raw = tree.raw_state();
            const auto counts = tree.asset->nodes;
            const auto asset_name = tree.asset->name;
            cc_mw3_re::PreparedModels models(assets);
            const auto draw = models.draw(tree.context());
            require(!draw.replace && draw.batches.empty(),
                    "LOD fallback with unresolved donor/batch frame did not decline cleanly");
            require(tree.raw_state() == raw && tree.asset->nodes == counts &&
                        tree.asset->name == asset_name,
                    "Declined LOD fallback mutated native source state");
            ++cases;
        }
    }

    // A BWMESH4 fallback with a complete live donor hierarchy remains usable.
    for (const std::string selected_lod : {"0", "1"}) {
        write(mesh_path, prepared_fixture::build_valid_v4_mesh());
        auto assets = options("authored", selected_lod);
        prepared_fixture::DonorTree tree("", false);
        tree.asset->name = selected_lod == "0" ? "mech_authored_1.flt" : "mech_authored.flt";
        cc_mw3_re::PreparedModels models(assets);
        const auto draw = models.draw(tree.context());
        require(draw.replace && draw.batches.size() == 1,
                "Complete BWMESH4 LOD fallback was declined");
        ++cases;
    }

    for (const std::string toe : {"ltoe01", "ltoe02", "ltoe03", "rtoe01", "rtoe02", "rtoe03"}) {
        const double foot_x = toe.front() == 'l' ? -.5 : .5;
        const auto bytes = prepared_fixture::build_valid_v4_mesh(
            toe, "control", "panel", foot_x + .1, .2, -.1);
        write(mesh_path, bytes);
        std::istringstream input(bytes, std::ios::binary);
        const auto mesh = platform::prepared::read_mesh(input);
        write(material_path, prepared_fixture::donor_materials(
            mw34::materials::compute_mesh_uv_hash(mesh.batches, 0, mesh.batches.size())));
        auto assets = options();
        assets.normals.push_back({"authored", "1", normal_path.string()});
        assets.lighting = "normal";
        cc_mw3_re::PreparedModels models(assets, {{"authored", "1", material_path.string()}});
        prepared_fixture::DonorTree distance(toe, false), full(toe, true);
        platform::prepared::Matrix resting{};
        for (unsigned pose = 0; pose < 2; ++pose) {
            if (pose) { distance.pose_foot(); full.pose_foot(); }
            const auto distance_raw = distance.raw_state(), full_raw = full.raw_state();
            const auto distance_counts = distance.asset->nodes, full_counts = full.asset->nodes;
            const auto expected = models.draw(full.context());
            const auto actual = models.draw(distance.context()); // Baseline RED: absent donor toe.
            require(actual.replace && expected.replace && actual.batches.size() == 1 &&
                        expected.batches.size() == 1, "Donor toe changed native batch visibility");
            const auto &got = actual.batches[0], &want = expected.batches[0];
            require(got.batch == want.batch && got.texture == want.texture && got.normal &&
                        got.normal == want.normal && got.surface_material == want.surface_material &&
                        got.height_binding && got.height_binding == want.height_binding &&
                        got.deformed.empty(), "Donor toe changed batch/normal/POM identity");
            for (unsigned i = 0; i < 16; ++i)
                require(std::isfinite(got.world[i]) && std::isfinite(got.camera[i]) &&
                            std::abs(got.world[i] - want.world[i]) < 1e-5 &&
                            std::abs(got.camera[i] - want.camera[i]) < 1e-5,
                        "Donor toe matrix differs from native full-source witness");
            for (const auto &vertex : got.batch->vertices) {
                const auto actual_point = mw34::donor::point(got.world,
                    {vertex[0], vertex[1], vertex[2]});
                const auto expected_point = mw34::donor::point(want.world,
                    {vertex[0], vertex[1], vertex[2]});
                for (unsigned i = 0; i < 3; ++i)
                    require(std::abs(actual_point[i] - expected_point[i]) < 1e-5,
                            "Donor triangle differs from full-source point witness");
            }
            if (!pose) {
                // Independent analytic rest witness in original axes, with camera z=4.
                require(std::abs(got.world[3] + .2) < 1e-5 &&
                            std::abs(got.world[7] + .1) < 1e-5 &&
                            std::abs(got.world[11] - (4 - foot_x - .1)) < 1e-5,
                        "Rest toe lost its analytic original-axis offset");
                resting = got.world;
            } else
                require(got.world != resting, "Posed-foot witness did not move donor geometry");
            require(distance.raw_state() == distance_raw && full.raw_state() == full_raw &&
                        distance.asset->nodes == distance_counts && full.asset->nodes == full_counts,
                    "Donor admission mutated original node/data/name-count state");
            ++cases;
        }
        // Canonical presence remains valid even after a native toe has detached live.
        distance.asset->nodes[toe] = 1;
        const auto detached = models.draw(distance.context());
        const auto present = models.draw(full.context());
        require(detached.batches.size() == 1 && present.batches.size() == 1,
                "Canonical-present detached toe changed native visibility");
        for (unsigned i = 0; i < 16; ++i)
            require(std::abs(detached.batches[0].world[i] - present.batches[0].world[i]) < 1e-5,
                    "Canonical-present detached toe changed the existing solver");
        ++cases;

        // Canonical-complete close LOD keeps the same geometry and authored material values.
        auto close_assets = assets;
        close_assets.models[0].lod = close_assets.normals[0].lod = "0";
        const auto close_material_path = folder / "close-materials.bin";
        write(close_material_path, prepared_fixture::donor_materials(
            mw34::materials::compute_mesh_uv_hash(mesh.batches, 0, mesh.batches.size()),
            "authored:close"));
        cc_mw3_re::PreparedModels close(close_assets,
            {{"authored", "0", close_material_path.string()}});
        full.asset->name = "mech_authored.flt";
        const auto close_draw = close.draw(full.context());
        require(close_draw.replace && close_draw.batches.size() == 1 &&
                    close_draw.batches[0].batch->vertices == present.batches[0].batch->vertices &&
                    close_draw.batches[0].normal && close_draw.batches[0].height_binding &&
                    close_draw.batches[0].normal->hash == present.batches[0].normal->hash &&
                    close_draw.batches[0].height_binding->image->pixels ==
                        present.batches[0].height_binding->image->pixels,
                "Complete close LOD changed batch/normal/POM content");
        for (unsigned i = 0; i < 16; ++i)
            require(std::abs(close_draw.batches[0].world[i] - present.batches[0].world[i]) < 1e-5,
                    "Complete close LOD changed donor world matrix");
        ++cases;
    }
    auto reject = [&](const sdlfe::CoreCriticalAssets &assets,
                      prepared_fixture::DonorTree &tree, const char *message) {
        const auto raw = tree.raw_state();
        const auto counts = tree.asset->nodes;
        std::string error;
        try {
            cc_mw3_re::PreparedModels models(assets);
            (void)models.draw(tree.context());
        } catch (const std::runtime_error &failure) { error = failure.what(); }
        require(error.find(message) != std::string::npos,
                "Donor negative did not reject at its intended contract");
        require(raw == tree.raw_state() && counts == tree.asset->nodes,
                "Rejected donor admission mutated native source state");
        ++cases;
    };
    auto reject_payload = [&](const sdlfe::CoreCriticalAssets &assets,
                              prepared_fixture::DonorTree &tree, const char *message) {
        const auto raw = tree.raw_state();
        const auto counts = tree.asset->nodes;
        std::string error;
        try {
            cc_mw3_re::PreparedModels models(assets);
            (void)models.draw(tree.context());
        } catch (const std::runtime_error &failure) { error = failure.what(); }
        require(error.find(message) != std::string::npos,
                "Malformed donor payload did not reject at admission");
        require(raw == tree.raw_state() && counts == tree.asset->nodes,
                "Rejected donor payload admission mutated native source state");
        ++cases;
    };
    const std::string toe = "rtoe02";
    const auto valid = prepared_fixture::build_valid_v4_mesh(toe, "control", "panel", .6);
    write(mesh_path, valid);
    for (unsigned count : {0U, 2U}) {
        prepared_fixture::DonorTree tree(toe, false);
        tree.asset->nodes[toe] = count;
        const auto message = "mech_authored_1.flt [donor reference 0]: rtoe02 (count " +
                             std::to_string(count) + ")";
        reject(options(), tree, message.c_str());
    }
    for (const std::string role : {"owner", "visibility"}) {
        write(mesh_path, prepared_fixture::build_valid_v4_mesh(
            toe, role == "owner" ? toe : "control", role == "visibility" ? toe : "panel", .6));
        prepared_fixture::DonorTree tree(toe, false);
        reject(options(), tree, ("mech_authored_1.flt [batch 0." + role +
                                 "]: rtoe02 (absent)").c_str());
    }
    write(mesh_path, valid);
    for (const std::string anchor : {"rfoot", "torso"}) {
        for (int count : {-1, 0, 2}) {
            prepared_fixture::DonorTree tree(toe, false);
            if (count == -1) tree.asset->nodes.erase(anchor);
            else tree.asset->nodes[anchor] = count;
            const auto message = "dependency " + anchor +
                (count == -1 ? " absent" : " count " + std::to_string(count));
            reject(options(), tree, message.c_str());
        }
    }
    for (const std::string rest : {"rfoot", "torso", "rtoe02"}) {
        write(mesh_path, prepared_fixture::build_valid_v4_mesh(
            toe, "control", "panel", .6, .2, -.1, rest));
        prepared_fixture::DonorTree tree(toe, false);
        // The real payload parser rejects a bone whose rest reference was removed.
        reject_payload(options(), tree, "bone names an unknown source control");
    }
    write(mesh_path, valid);
    {
        prepared_fixture::DonorTree tree(toe, false);
        tree.asset->name = "mech_authored.flt";
        reject(options("authored", "0"), tree, "rtoe02 (absent)");
    }
    {
        prepared_fixture::DonorTree tree(toe, false);
        reject(options("authored_1", "0"), tree, "rtoe02 (absent)");
    }
    for (const std::string unsupported : {"head", "ltoe04", "rtoe1", "rtoe02_extra"}) {
        write(mesh_path, prepared_fixture::build_valid_v4_mesh(unsupported));
        prepared_fixture::DonorTree tree(toe, false);
        reject(options(), tree, (unsupported + " (absent)").c_str());
    }
    // BWMESH2 cannot carry donor references; its absent geometry control stays mandatory.
    auto non_donor = prepared_fixture::mesh(2);
    non_donor.replace(12, 32, toe + std::string(32 - toe.size(), '\0'));
    write(mesh_path, non_donor);
    prepared_fixture::DonorTree tree(toe, false);
    reject(options(), tree, "[batch 0.owner]: rtoe02 (absent)");
    std::printf("[DONOR_TOE_CONTRACTS] cases=%u failures=0\n", cases);
}

// Synthetic source and parsed BWSFM1 fixtures exercise the synchronous guard.
// They do not authenticate a real sidecar file: EnvironmentPackCache's existing
// canonical path/before-and-after SHA checks remain the live input precondition.
struct NativeGroundFixture {
    zcls::Node node{};
    zmod::Model model{};
    zvid::D3DTexture texture{};
    zimg::Texture image{};
    std::array<zimg::TextureEntry, 2> entries{};
    std::array<zmod::Material, 2> materials{};
    std::array<zmod::Polygon, 2> polygons{};
    std::array<float, 12> vertices{0, 0, 2, 1, 0, 2, 0, 1, 2, 1, 1, 2};
    std::array<float, 12> normals{0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1};
    std::array<std::uint32_t, 3> triangle{0, 1, 2};
    std::array<std::uint32_t, 4> quad{0, 1, 3, 2};
    std::array<float, 6> triangle_uv{0, 0, 1, 0, 0, 1};
    std::array<float, 8> quad_uv{0, 0, 1, 0, 1, 1, 0, 1};
    std::shared_ptr<mw34::materials::SurfaceDecodedBudget> budget =
        std::make_shared<mw34::materials::SurfaceDecodedBudget>(64);
    std::shared_ptr<mw34::materials::SurfaceMaterialPack> pack;
    platform::prepared::MaterialTarget target;
    cc_mw3_re::NativeGroundHeightInput input;

    NativeGroundFixture() {
        texture.handle = 7;
        texture.type = 1;
        image.flags = 0;
        for (std::size_t index = 0; index < entries.size(); ++index) {
            std::strcpy(entries[index].name, "authored_ground");
            entries[index].surface = &texture;
            entries[index].image = &image;
            materials[index].alpha = 255;
            materials[index].flags = 1;
            materials[index].texture = &entries[index];
            polygons[index].flags = std::uint32_t(index ? 4 : 3) | 0x200;
            polygons[index].vertex_indices = index ? quad.data() : triangle.data();
            polygons[index].normal_indices = polygons[index].vertex_indices;
            polygons[index].uvs = index ? quad_uv.data() : triangle_uv.data();
            polygons[index].material = &materials[index];
        }
        const std::uint32_t polygon_count = 2, vertex_count = 4, normal_count = 4;
        std::memcpy(model.header + 0x10, &polygon_count, 4);
        std::memcpy(model.header + 0x14, &vertex_count, 4);
        std::memcpy(model.header + 0x18, &normal_count, 4);
        model.polygons = polygons.data();
        model.vertices = vertices.data();
        model.normals = normals.data();
        node.model = &model;
        node.put<std::int32_t>(0x3c, 37);
        auto source = std::make_shared<zcls::SourceAsset>();
        source->world = zcls::WorldSourceIdentity{
            "gamez-zbd-v27", "authored/gamez.zbd", std::string(64, 'a'), 4096, 19, 37};
        node.source_asset = model.world_source_asset = source;
        target.asset_id = "authored:ground";
        target.source = {"gamez-zbd-v27", "authored/gamez.zbd", std::string(64, 'a'), 4096, 37};
        target.sidecar_path = "synthetic-only/ground.bwsfm";
        target.sidecar_sha256 = std::string(64, 'b');
        target.polygon_materials = {"authored_ground", "authored_ground"};
        target.surface_keys = {mw34::materials::SurfaceKey{2, 2, 1, 0x1234},
                               mw34::materials::SurfaceKey{2, 2, 1, 0x1234}};
        // Independent pre-render corner stream, not triangulated GPU geometry
        // and not a first observation of the Model under test.
        std::vector<platform::prepared::Batch> expected(2);
        expected[0].vertices = {{0,0,2,0,0,1,0,0}, {1,0,2,0,0,1,1,0},
                                {0,1,2,0,0,1,0,1}};
        expected[1].vertices = {{0,0,2,0,0,1,0,0}, {1,0,2,0,0,1,1,0},
                                {1,1,2,0,0,1,1,1}, {0,1,2,0,0,1,0,1}};
        target.mesh_uv_hash = mw34::materials::compute_mesh_uv_hash(expected, 0, 2);
        auto bytes = build_single_batch_bwsfm1(target.mesh_uv_hash, "authored:ground",
                                               "authored_ground", -3, 4, .25f, .3f, .2f, .1f);
        const std::uint32_t two = 2;
        std::memcpy(bytes.data() + 12, &two, 4);
        bytes.insert(36, 4, '\0'); // Second original polygon shares record/image 0.
        std::istringstream stream(bytes, std::ios::binary);
        auto parsed = mw34::materials::read_surface_materials(
            stream, target.asset_id, target.mesh_uv_hash, target.polygon_materials,
            mw34::materials::max_surface_sidecar_bytes,
            mw34::materials::max_surface_sidecar_bytes, budget);
        pack = std::make_shared<mw34::materials::SurfaceMaterialPack>(std::move(parsed));
        // Additional nonheight fields prove that snapshotting copies the full
        // authored record rather than rebuilding a new default material.
        pack->records[0]->sss_participation = .4f;
        pack->records[0]->sss_tint = {.1f, .2f, .3f};
        pack->records[0]->sss_radius = .5f;
        pack->records[0]->thickness_scale = .6f;
        pack->records[0]->uv_scale = {2, 3};
        pack->records[0]->uv_offset = {.1f, .2f};
        target.pack = pack;
        input.node = &node;
        input.model = &model;
        input.material = {&model, &materials[0], &entries[0], 0};
        input.key = input.slot_key = *target.surface_keys[0];
        input.texture = 7;
        input.normal_index = 3;
        input.normal_width = input.normal_height = 2;
        input.normal_hash = 0x5678;
        input.source_epoch = 19;
        input.producer_epoch = input.slot_epoch = input.current_group_epoch = 23;
        input.texture_version = input.current_texture_version = 29;
        input.enabled = input.eligible = true;
    }
    std::shared_ptr<const mw34::materials::HeightBinding> admit() const {
        return cc_mw3_re::admit_native_ground_height(target, input, budget);
    }
    void change_source(const std::function<void(zcls::WorldSourceIdentity &)> &change) {
        auto source = std::make_shared<zcls::SourceAsset>(*node.source_asset);
        change(*source->world);
        node.source_asset = model.world_source_asset = source;
    }
};

void check_native_ground_height_admission() {
    using namespace mw34::materials;
    namespace cc = cc_mw3_re;
    cc::NativeGroundFloatScope restore_test_fp;
    unsigned cases = 0;
    const auto passed = [&](const char *name) {
        ++cases;
        std::printf("Native ground admission: %s passed\n", name);
    };
    std::shared_ptr<const HeightBinding> retained;
    std::shared_ptr<SurfaceDecodedBudget> retained_budget;
    {
        NativeGroundFixture fixture;
        const auto rounding = std::fegetround();
        std::fesetround(FE_DOWNWARD);
        std::feclearexcept(FE_ALL_EXCEPT);
        std::feraiseexcept(FE_INEXACT);
        const auto flags = std::fetestexcept(FE_ALL_EXCEPT);
        retained = fixture.admit();
        require(std::fegetround() == FE_DOWNWARD && std::fetestexcept(FE_ALL_EXCEPT) == flags,
                "Successful ground guard changed FP state");
        std::fesetround(rounding);
        require(retained && retained->world_source &&
                    retained->world_source->kind == "gamez-zbd-v27" &&
                    retained->world_source->member == "authored/gamez.zbd" &&
                    retained->world_source->bytes == 4096 &&
                    retained->world_source->model_slot == 37 &&
                    retained->world_source->load_epoch == 19 &&
                    retained->source_sha256 == std::string(64, 'a') &&
                    retained->sidecar_sha256 == std::string(64, 'b') &&
                    retained->sidecar_path == fixture.target.sidecar_path &&
                    retained->producer_epoch == 23 && retained->texture_version == 29 &&
                    retained->image_version == 1 && retained->source_batch == 0 &&
                    retained->normal_hash == 0x5678 && retained->normal_width == 2 &&
                    retained->normal_height == 2 && retained->material == *fixture.pack->records[0],
                "Ground snapshot lost source, stamps, normal or full material values");
        require(retained->image->pixels.size() == 4 && fixture.budget->used() == 16 &&
                    height_binding_bytes({retained, fixture.admit()}) == 16,
                "Ground image alias was recharged or lost ownership");
        retained_budget = fixture.budget;
        passed("positive_triangle_quad_full_owned_snapshot_fp");
        auto model_copy = fixture.model;
        fixture.node.model = &model_copy;
        fixture.input.model = &model_copy;
        fixture.input.material.model = &model_copy;
        require(bool(fixture.admit()), "Agreeing immutable model copy was rejected");
        passed("agreeing_model_copy");
    }
    require(retained && retained->image->pixels.size() == 4 && retained_budget->used() == 16,
            "Ground snapshot borrowed destroyed native source storage");
    passed("snapshot_survives_native_source_destruction");
    const std::vector<std::pair<const char *, std::function<void(NativeGroundFixture &)>>> rejects{
        {"missing_node_owner", [](auto &f) { f.node.source_asset.reset(); }},
        {"missing_model_owner", [](auto &f) { f.model.world_source_asset.reset(); }},
        {"different_shared_owner", [](auto &f) { f.model.world_source_asset =
             std::make_shared<const zcls::SourceAsset>(*f.node.source_asset); }},
        {"changed_node_model", [](auto &f) { f.node.model = nullptr; }},
        {"changed_context_model", [](auto &f) { f.input.material.model = nullptr; }},
        {"changed_material_pointer", [](auto &f) { f.input.material.material = &f.materials[1]; }},
        {"changed_texture_pointer", [](auto &f) { f.input.material.texture_entry = &f.entries[1]; }},
        {"changed_polygon", [](auto &f) { f.input.material.polygon = 2; }},
        {"wrong_current_original_polygon", [](auto &f) { f.input.material.polygon = 1; }},
        {"missing_current_material", [](auto &f) { f.polygons[0].material = nullptr; }},
        {"missing_surface_record", [](auto &f) { f.entries[0].surface = nullptr; }},
        {"missing_source_world", [](auto &f) {
             auto source = std::make_shared<zcls::SourceAsset>(*f.node.source_asset);
             source->world.reset(); f.node.source_asset = f.model.world_source_asset = source;
         }},
        {"wrong_kind", [](auto &f) { f.change_source([](auto &s) { s.kind = "library"; }); }},
        {"wrong_member", [](auto &f) { f.change_source([](auto &s) { s.member += ".other"; }); }},
        {"wrong_source_sha", [](auto &f) { f.change_source([](auto &s) { s.sha256[0] = 'c'; }); }},
        {"wrong_source_bytes", [](auto &f) { f.change_source([](auto &s) { ++s.bytes; }); }},
        {"wrong_original_slot", [](auto &f) { f.change_source([](auto &s) { ++s.model_slot; }); }},
        {"stale_source_epoch", [](auto &f) { ++f.input.source_epoch; }},
        {"stale_scope_group", [](auto &f) { ++f.input.producer_epoch; }},
        {"stale_slot_group", [](auto &f) { ++f.input.slot_epoch; }},
        {"stale_texture_version", [](auto &f) { ++f.input.current_texture_version; }},
        {"wrong_texture_handle", [](auto &f) { ++f.texture.handle; }},
        {"wrong_key_hash", [](auto &f) { ++f.input.key.hash; }},
        {"wrong_key_width", [](auto &f) { ++f.input.key.width; }},
        {"wrong_key_height", [](auto &f) { ++f.input.key.height; }},
        {"wrong_key_format", [](auto &f) { ++f.input.key.format; }},
        {"wrong_slot_key", [](auto &f) { ++f.input.slot_key.hash; }},
        {"missing_expected_key", [](auto &f) { f.target.surface_keys[0].reset(); }},
        {"mutated_vertices_after_positive", [](auto &f) { require(bool(f.admit()), "setup");
                                                            f.vertices[0] = .25f; }},
        {"mutated_normals_after_positive", [](auto &f) { require(bool(f.admit()), "setup");
                                                           f.normals[0] = .25f; }},
        {"mutated_uv_after_positive", [](auto &f) { require(bool(f.admit()), "setup");
                                                      f.quad_uv[0] = .25f; }},
        {"noncurrent_ordered_material_name", [](auto &f) { std::strcpy(f.entries[1].name, "other"); }},
        {"wrong_target_cardinality", [](auto &f) { f.target.surface_keys.pop_back(); }},
        {"wrong_pack_cardinality", [](auto &f) { f.pack->bindings.pop_back(); }},
        {"wrong_pack_asset", [](auto &f) { f.pack->records[0]->asset_id = "authored:wrong"; }},
        {"wrong_pack_uv", [](auto &f) { ++f.pack->mesh_uv_hash; }},
        {"wrong_pack_material", [](auto &f) { f.pack->records[0]->material_name = "wrong"; }},
        {"wrong_pack_binding", [](auto &f) { f.pack->bindings[1] = 100; }},
        {"absent_normal", [](auto &f) { f.input.normal_index = -1; }},
        {"absent_normal_hash", [](auto &f) { f.input.normal_hash = 0; }},
        {"absent_normal_dimensions", [](auto &f) { f.input.normal_width = 0; }},
        {"foreign_budget_domain", [](auto &f) { f.budget = std::make_shared<SurfaceDecodedBudget>(64); }},
        {"missing_sidecar_path", [](auto &f) { f.target.sidecar_path.clear(); }},
        {"invalid_sidecar_digest", [](auto &f) { f.target.sidecar_sha256 = "missing"; }}
    };
    for (const auto &[name, change] : rejects) {
        NativeGroundFixture fixture;
        change(fixture);
        const int rounding = std::fegetround();
        std::fesetround(FE_DOWNWARD);
        std::feclearexcept(FE_ALL_EXCEPT);
        std::feraiseexcept(FE_INEXACT);
        const auto flags = std::fetestexcept(FE_ALL_EXCEPT);
        bool rejected = false;
        try { (void)fixture.admit(); } catch (const std::runtime_error &) { rejected = true; }
        require(rejected, name);
        require(std::fegetround() == FE_DOWNWARD && std::fetestexcept(FE_ALL_EXCEPT) == flags,
                "Rejected ground guard changed FP state");
        std::fesetround(rounding);
        passed(name);
    }
    {
        NativeGroundFixture fixture;
        fixture.input.enabled = false;
        fixture.node.source_asset.reset();
        require(!fixture.admit(), "POM Off inspected missing source proof");
        passed("pom_off_missing_proof");
        fixture.target.sidecar_sha256.clear();
        require(!fixture.admit(), "POM Off inspected invalid sidecar proof");
        passed("pom_off_bad_proof");
        fixture.input.enabled = true;
        fixture.input.eligible = false;
        require(!fixture.admit(), "Ineligible draw inspected missing source proof");
        passed("ineligible_missing_proof");
    }
    for (const auto &[name, change] : std::vector<std::pair<const char *,
             std::function<void(platform::ModelDrawContext &)>>> {
             {"nonordinary_policy", [](auto &c) { c.ordinary = false; }},
             {"morph_policy", [](auto &c) { c.morphing = true; }},
             {"overlay_policy", [](auto &c) { c.overlay = true; }},
             {"opacity_policy", [](auto &c) { c.opacity = .5f; }}}) {
        platform::ModelDrawContext context;
        context.ordinary = true;
        change(context);
        require(!cc::native_ground_eligible(context), name);
        passed(name);
    }
    for (const auto &[name, change] : std::vector<std::pair<const char *,
             std::function<void(NativeGroundFixture &)>>> {
             {"nonopaque_material", [](auto &f) { f.materials[0].alpha = 128; }},
             {"alpha_texture", [](auto &f) { f.image.flags |= 2; }},
             {"cutout_texture", [](auto &f) { f.texture.type = 5; }},
             {"alpha4444_texture", [](auto &f) { f.texture.type = 4; }}}) {
        NativeGroundFixture fixture;
        change(fixture);
        fixture.node.source_asset.reset(); // Ineligible policy must not inspect proof.
        const auto rounding = std::fegetround();
        std::fesetround(FE_DOWNWARD);
        std::feclearexcept(FE_ALL_EXCEPT);
        std::feraiseexcept(FE_INEXACT);
        const auto flags = std::fetestexcept(FE_ALL_EXCEPT);
        require(!fixture.admit(), name);
        require(std::fegetround() == FE_DOWNWARD && std::fetestexcept(FE_ALL_EXCEPT) == flags,
                "Ineligible material changed FP state");
        std::fesetround(rounding);
        passed(name);
    }
    for (const auto &[name, change] : std::vector<std::pair<const char *,
             std::function<void(platform::DrawState &)>>> {
             {"blend_pass", [](auto &s) { s.blend = true; }},
             {"multiply_pass", [](auto &s) { s.multiply = true; }},
             {"overlay_depth_pass", [](auto &s) { s.depth_always = true; }},
             {"no_depth_write_pass", [](auto &s) { s.depth_write = false; }},
             {"alpha_modulate_pass", [](auto &s) { s.alpha_modulate = true; }},
             {"shadow_color_select_pass", [](auto &s) { s.color_select = true; }},
             {"sky_pass", [](auto &s) { s.native_sky = true; }},
             {"sharp_2d_pass", [](auto &s) { s.sharp = true; }},
             {"wireframe_pass", [](auto &s) { s.wireframe = true; }}}) {
        platform::DrawState state;
        change(state);
        require(!cc::native_ground_draw_eligible(state, false, false, false, false), name);
        passed(name);
    }
    require(!cc::native_ground_draw_eligible({}, true, false, false, false) &&
                !cc::native_ground_draw_eligible({}, false, true, false, false) &&
                !cc::native_ground_draw_eligible({}, false, false, true, false) &&
                !cc::native_ground_draw_eligible({}, false, false, false, true),
            "HUD/depth-only/debug/point scope was height eligible");
    passed("hud_depth_debug_point_policy");
    {
        NativeGroundFixture fixture;
        std::vector<platform::prepared::MaterialTarget> targets{fixture.target};
        require(cc::select_native_ground_target(targets, &fixture.node, &fixture.model),
                "Selected member/original slot was not selected");
        passed("dispatch_member_original_slot");
        fixture.change_source([](auto &s) { ++s.model_slot; });
        require(!cc::select_native_ground_target(targets, &fixture.node, &fixture.model),
                "Unselected original slot sharing image became a height target");
        passed("dispatch_unselected_slot_shared_image");
        fixture.change_source([](auto &s) { s.member = "other/gamez.zbd"; s.model_slot = 37; });
        require(!cc::select_native_ground_target(targets, &fixture.node, &fixture.model),
                "Unrelated world sharing image became a height target");
        passed("dispatch_unrelated_world_shared_image");
        auto library = std::make_shared<zcls::SourceAsset>();
        library->name = "authored_library";
        fixture.node.source_asset = fixture.model.world_source_asset = library;
        require(!cc::select_native_ground_target(targets, &fixture.node, &fixture.model),
                "Known library sharing image became a height target");
        passed("dispatch_known_library_shared_image");
        require(!cc::select_native_ground_target(targets, nullptr, nullptr),
                "Null unrelated/HUD scope became a height target");
        passed("dispatch_null_scope");
        fixture.node.source_asset.reset();
        fixture.model.world_source_asset.reset();
        bool rejected = false;
        try { (void)cc::select_native_ground_target(targets, &fixture.node, &fixture.model); }
        catch (const std::runtime_error &) { rejected = true; }
        require(rejected, "Raw selected slot failed to reject missing owner");
        passed("dispatch_raw_slot_rejection_only");
    }
    {
        NativeGroundFixture fixture;
        fixture.pack->bindings[0] = no_surface_material;
        require(!fixture.admit(), "Unbound polygon became height-enabled");
        passed("unbound_material");
        fixture.pack->bindings[0] = 0;
        fixture.pack->records[0]->height_image = no_surface_image;
        require(!fixture.admit(), "No-height material became height-enabled");
        passed("no_height_record");
    }
    {
        NativeGroundFixture fixture;
        const auto before = fixture.admit();
        fixture.target.sidecar_sha256[0] = 'c';
        const auto changed_sha = fixture.admit();
        require(!same_height_binding(before, changed_sha), "Sidecar metadata SHA reused snapshot");
        passed("synthetic_sidecar_metadata_sha_equality_only");
        fixture.target.sidecar_path += ".new";
        require(!same_height_binding(changed_sha, fixture.admit()), "Sidecar path reused snapshot");
        passed("synthetic_sidecar_metadata_path_equality_only");
    }
    const std::vector<std::pair<const char *, std::function<void(HeightBinding &)>>> deltas{
        {"snapshot_world_presence", [](auto &b) { b.world_source.reset(); }},
        {"snapshot_world_kind", [](auto &b) { b.world_source->kind += "x"; }},
        {"snapshot_world_member", [](auto &b) { b.world_source->member += "x"; }},
        {"snapshot_world_bytes", [](auto &b) { ++b.world_source->bytes; }},
        {"snapshot_world_slot", [](auto &b) { ++b.world_source->model_slot; }},
        {"snapshot_world_epoch", [](auto &b) { ++b.world_source->load_epoch; }},
        {"snapshot_sidecar_path", [](auto &b) { b.sidecar_path += "x"; }}
    };
    for (const auto &[name, change] : deltas) {
        auto altered = std::make_shared<HeightBinding>(*retained);
        change(*altered);
        require(!same_height_binding(retained, altered), name);
        passed(name);
    }
    require(height_binding_metadata_bytes(*retained) == sizeof(HeightBinding) +
                retained->source_sha256.capacity() + retained->sidecar_sha256.capacity() +
                retained->sidecar_path.capacity() + retained->material.asset_id.capacity() +
                retained->material.material_name.capacity() +
                retained->world_source->kind.capacity() + retained->world_source->member.capacity(),
            "Ground metadata omitted owned source strings");
    passed("packet_source_string_metadata");
    require(height_binding_stamps_match(*retained, 19, 23, 29, retained->albedo) &&
                !height_binding_stamps_match(*retained, 20, 23, 29, retained->albedo) &&
                !height_binding_stamps_match(*retained, 19, 24, 29, retained->albedo) &&
                !height_binding_stamps_match(*retained, 19, 23, 30, retained->albedo),
            "Deferred numeric source/group/version validation failed");
    passed("deferred_numeric_stamps_without_source_pointers");
    {
        NativeGroundFixture fixture;
        std::vector<::cc::geometry::Range> ranges{{0,6,1,false,1}, {6,3,0,false,0}};
        const auto admissions = cc::admit_native_ground_ranges(ranges, 2,
            [&](std::size_t, std::uint32_t polygon) {
                fixture.input.material = {&fixture.model, &fixture.materials[polygon],
                                           &fixture.entries[polygon], polygon};
                cc::NativeGroundRangeAdmission value;
                value.height_binding = fixture.admit();
                value.normal_index = fixture.input.normal_index;
                return value;
            });
        require(admissions.size() == 2 && admissions[0].polygon == 1 &&
                    admissions[0].height_binding->source_batch == 1 &&
                    admissions[1].height_binding->source_batch == 0 &&
                    height_binding_bytes({admissions[0].height_binding,
                                          admissions[1].height_binding}) == 16,
                "Shared GPU/reference admission vector lost original polygon or alias");
        passed("gpu_reference_shared_original_polygon_vector");
        ranges[1].polygon = 2;
        bool rejected = false;
        try { (void)cc::admit_native_ground_ranges(ranges, 2,
                  [](std::size_t, std::uint32_t) { return cc::NativeGroundRangeAdmission{}; }); }
        catch (const std::runtime_error &) { rejected = true; }
        require(rejected, "Out-of-range original polygon was admitted");
        passed("range_original_polygon_rejection");
    }
    {
        // Actual shared native producer helper, with an independently authored
        // world camera. Model position and camera-space translation differ.
        const platform::prepared::Matrix world{
            0, -3, 0, 12, 2, 0, 0, -7, 0, 0, 4, 9, 0, 0, 0, 1};
        const platform::prepared::Matrix world_camera{
            0, 0, 1, 17, 0, 1, 0, -9, -1, 0, 0, 5, 0, 0, 0, 1};
        const auto camera = mw34::donor::product(mw34::donor::inverse(world_camera), world);
        const auto derived = mw34::donor::product(world, mw34::donor::inverse(camera));
        const std::array<float, 4> expected_eye{17, -9, 5, 1};
        require(cc::native_height_eye(derived) == expected_eye &&
                    cc::native_height_eye(world_camera) == expected_eye &&
                    cc::native_height_eye(mw34::donor::identity()) ==
                        std::array<float, 4>{0, 0, 0, 1},
                "Native CPU/GPU/TL camera eye used model position or an invalid origin");
        mw34::vkscene::Draw ground;
        ground.height_binding = retained;
        require(ground.surface_parameters[3] == 0,
                "Native eye fixture unexpectedly has a standalone BRDF sidecar");
        ground.surface_eye = cc::native_height_eye(world_camera);
        auto wrapped_camera = world_camera;
        wrapped_camera[3] += 100;
        wrapped_camera[7] -= 50;
        wrapped_camera[11] += 25;
        const auto wrapped_model_camera = mw34::donor::product(
            mw34::donor::inverse(wrapped_camera), world);
        auto wrapped = ground;
        wrapped.surface_eye = cc::native_height_eye(mw34::donor::product(
            world, mw34::donor::inverse(wrapped_model_camera)));
        require(ground.surface_eye == expected_eye &&
                    wrapped.surface_eye == std::array<float, 4>{117, -59, 30, 1},
                "Native wrapped view lost its own world-space eye");
        mw34::vkscene::Scene packet;
        packet.draws = {ground, wrapped};
        const auto queued = packet;
        packet.draws.clear();
        ground = {};
        wrapped = {};
        require(queued.draws[0].surface_eye == expected_eye &&
                    queued.draws[1].surface_eye == std::array<float, 4>{117, -59, 30, 1},
                "Owned native draw eyes changed after producer packet reuse");
        passed("native_model_view_world_eye_origin_wrapped_no_brdf_ownership");
        for (unsigned invalid = 0; invalid < 7; ++invalid) {
            auto broken = world_camera;
            if (invalid == 0) broken = {};
            if (invalid == 1) broken[8] = 0; // Missing one independent basis axis.
            if (invalid == 2) broken[3] = std::numeric_limits<double>::quiet_NaN();
            if (invalid == 3) broken[5] = std::numeric_limits<double>::infinity();
            if (invalid == 4) broken[11] = 1e40; // Finite double, invalid owned float.
            if (invalid == 5) broken[15] = 0;
            if (invalid == 6) broken[14] = std::numeric_limits<double>::quiet_NaN();
            bool rejected = false;
            try { (void)cc::native_height_eye(broken); }
            catch (const std::runtime_error &) { rejected = true; }
            require(rejected, "Native POM eye admitted a missing/singular/nonfinite camera");
        }
        auto singular_camera = camera;
        for (unsigned column = 0; column < 4; ++column)
            singular_camera[column] = 0;
        bool rejected = false;
        try {
            (void)cc::native_height_eye(mw34::donor::product(
                world, mw34::donor::inverse(singular_camera)));
        } catch (const std::runtime_error &) { rejected = true; }
        require(rejected, "Native model-to-camera inversion accepted a singular basis");
        passed("native_eye_rejects_missing_singular_nonfinite_affine_float_overflow");
    }
    auto model_binding = std::make_shared<HeightBinding>(*retained);
    model_binding->world_source.reset();
    model_binding->sidecar_path.clear();
    require(!model_binding->world_source && same_height_binding(model_binding,
                std::make_shared<const HeightBinding>(*model_binding)),
            "Absent model world identity changed equality");
    passed("model_absent_world_snapshot");
    retained.reset();
    model_binding.reset();
    require(retained_budget->used() == 0, "Last queued ground alias did not return reservation");
    passed("ground_last_alias_release");
    std::printf("Native ground height admission: %u authored cases passed\n", cases);
}

} // namespace

int main() {
    try {
        checks();
        check_prepared_models_surface_materials();
        check_prepared_models_donor_toe_admission();
        check_native_ground_height_admission();
        std::puts("Prepared staging cache invalidation, bytes, ownership, "
                  "materials and budget checks passed");
        return 0;
    } catch (const std::exception &error) {
        std::fprintf(stderr, "Prepared staging: %s\n", error.what());
        return 1;
    }
}
