#include "../../../tests/prepared_visual_fixture.h"
#include "gamez/zclass/cls_util.h"
#include "gamez/zclass/object3d.h"
#include "gamez/zmodel/gmod_draw.h"
#include "prepared_draw_cache.hpp"
#include "prepared_models.hpp"
#include "renderer/normal_codec.hpp"
#include "renderer/surface_materials.hpp"
#include "renderer/native_surface_identity.hpp"
#include "renderer/geometry/resource.hpp"

#include <array>
#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <functional>
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
                bool(a.draw.lit_normals) == bool(b.draw.lit_normals),
            "Cached clipping metadata changed");
    if (a.draw.sun_tl)
        require(a.draw.sun_tl->camera_world == b.draw.sun_tl->camera_world &&
                    a.draw.sun_tl->projection == b.draw.sun_tl->projection &&
                    *a.draw.lit_normals == *b.draw.lit_normals,
                "Cached clipped normals changed");
}
void checks() {
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
                         clipped.draw.lit_normals->capacity() * sizeof(std::array<float, 3>);
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

static void write_fixture_matrix(prepared_fixture::Bytes &out, double x = 0, double y = 0,
                                 double z = 0) {
    for (int i = 0; i < 16; ++i) {
        if (i == 3)
            out.f64(x);
        else if (i == 7)
            out.f64(y);
        else if (i == 11)
            out.f64(z);
        else
            out.f64(i % 5 == 0 ? 1 : 0);
    }
}

static std::string build_valid_v4_mesh() {
    prepared_fixture::Bytes out;
    out.value = std::string("BWMESH4\0", 8);
    out.u32(1); // 1 batch

    struct BoneDef {
        const char *name;
        const char *control;
        double x, y, z;
    };
    const std::vector<BoneDef> bone_defs = {{"Pelvis", "", 0, 0, 2},
                                            {"Torso_Twist", "torso", 0, 0, 2},
                                            {"Upperarm_Left", "larm", -1, 0, 2},
                                            {"Upperarm_Right", "rarm", 1, 0, 2},
                                            {"Forearm_Left", "", -1, 0, 1},
                                            {"Forearm_Right", "", 1, 0, 1},
                                            {"Thigh_Left", "lthigh", -0.5, 0, 2},
                                            {"Thigh_Right", "rthigh", 0.5, 0, 2},
                                            {"Calf_Left", "lcalf", -0.5, 0, 1},
                                            {"Calf_Right", "rcalf", 0.5, 0, 1},
                                            {"Foot0_Left", "lfoot", -0.5, 0, 0},
                                            {"Foot0_Right", "rfoot", 0.5, 0, 0}};
    struct RefDef {
        const char *name;
        double x, y, z;
    };
    const std::vector<RefDef> ref_defs = {
        {"hip", 0, 0, 2},      {"torso", 0, 0, 2},   {"larm", -1, 0, 2},     {"rarm", 1, 0, 2},
        {"lfoot", -0.5, 0, 0}, {"rfoot", 0.5, 0, 0}, {"lthigh", -0.5, 0, 2}, {"rthigh", 0.5, 0, 2},
        {"lcalf", -0.5, 0, 1}, {"rcalf", 0.5, 0, 1}};

    out.u32(static_cast<std::uint32_t>(bone_defs.size()));
    out.u32(static_cast<std::uint32_t>(ref_defs.size()));
    out.u32(0); // flags
    out.f64(0); // hip_drop
    out.f64(0);
    out.f64(0); // walk_x
    out.f64(0);
    out.f64(0); // walk_z

    for (const auto &b : bone_defs) {
        out.name(b.name);
        out.name(b.control);
        out.u32(0xffffffff);
        write_fixture_matrix(out, b.x, b.y, b.z);
    }

    for (const auto &r : ref_defs) {
        out.name(r.name);
        write_fixture_matrix(out, r.x, r.y, r.z);
    }

    out.name("control");
    out.name("panel");
    out.u32(0);          // donor_bone index 0
    out.u32(3);          // 3 vertices
    out.u32(0xffffffff); // color
    for (int i = 0; i < 3; ++i) {
        out.f32(0);
        out.f32(0);
        out.f32(i == 0 ? 1.0f : 0.0f);
        out.f32(0);
        out.f32(0);
        out.f32(1.0f);
        out.f32(0);
        out.f32(0);
    }
    return out.value;
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
        check_native_ground_height_admission();
        std::puts("Prepared staging cache invalidation, bytes, ownership, "
                  "materials and budget checks passed");
        return 0;
    } catch (const std::exception &error) {
        std::fprintf(stderr, "Prepared staging: %s\n", error.what());
        return 1;
    }
}
