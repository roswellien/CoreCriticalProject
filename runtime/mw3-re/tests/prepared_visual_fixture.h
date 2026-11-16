#pragma once
#include "platform/prepared_visuals.h"
#include "platform/render3d.h"
#include <cstring>
#include <string>
#include <vector>
#include <array>
#include <memory>
#include <map>
#include <stdexcept>
#include "gamez/zclass/cls_data.h"
#include "gamez/zclass/cls_util.h"
#include "gamez/zclass/object3d.h"
#include "gamez/zmodel/gmod_const.h"
namespace prepared_fixture {
struct Bytes {
    std::string value;
    void u32(uint32_t n) {
        for (unsigned i = 0; i < 4; ++i)
            value += char(n >> (i * 8));
    }
    void u64(uint64_t n) {
        u32(uint32_t(n));
        u32(uint32_t(n >> 32));
    }
    void f32(float n) {
        uint32_t bits;
        std::memcpy(&bits, &n, 4);
        u32(bits);
    }
    void f64(double n) {
        uint64_t bits;
        std::memcpy(&bits, &n, 8);
        u64(bits);
    }
    void name(const char *text) {
        std::string n(text);
        n.resize(32);
        value += n;
    }
    void matrix() {
        for (int i = 0; i < 16; ++i)
            f64(i % 5 == 0 ? 1 : 0);
    }
};
inline std::string mesh(unsigned version, uint32_t color = 0xffffffff,
                        std::array<float, 3> normal = {0, 0, 1}, bool mirrored_uv = false,
                        bool degenerate_uv = false, bool rank_one_uv = false,
                        const std::string &batch_owner = "control",
                        const std::string &batch_visibility = "panel") {
    Bytes out;
    out.value = std::string("BWMESH") + char('0' + version) + '\0';
    out.u32(1);
    if (version == 4) {
        out.u32(1);
        out.u32(1);
        out.u32(0);
        for (int i = 0; i < 5; ++i)
            out.f64(0);
        out.name("joint");
        out.name("control");
        out.u32(0xffffffff);
        out.matrix();
        out.name("control");
        out.matrix();
    }
    out.name(batch_owner.c_str());
    if (version != 1)
        out.name(batch_visibility.c_str());
    const int placements = version == 3 ? 1 : version == 5 ? 2 : version == 6 ? 3 : 0;
    for (int i = 0; i < placements; ++i) {
        out.name("control");
        out.f32(0);
        out.f32(0);
        out.f32(0);
    }
    if (version == 4)
        out.u32(0);
    out.u32(3);
    out.u32(color);
    for (const auto &vertex : {platform::prepared::Vertex{-1, -1, 2, 0, 0, 1, 0, 0},
                               platform::prepared::Vertex{1, -1, 2, 0, 0, 1, 1, 0},
                               platform::prepared::Vertex{0, 1, 2, 0, 0, 1, .5f, 1}})
        for (unsigned i = 0; i < vertex.size(); ++i) {
            float value = vertex[i];
            if (i >= 3 && i < 6)
                value = normal[i - 3];
            if (i == 6 && mirrored_uv)
                value = 1.f - value;
            if (i >= 6 && degenerate_uv)
                value = 0;
            if (i == 7 && rank_one_uv)
                value = 0;
            out.f32(value);
        }
    return out.value;
}
inline std::string textures() {
    Bytes out;
    out.value.assign("BWTEX1\0\0", 8);
    out.u32(1);
    out.u32(1);
    out.u32(0);
    out.name("authored");
    out.u32(2);
    out.u32(1);
    out.u64(0);
    out.value += char(0);
    out.value += char(0xf8);
    out.value += char(0xe0);
    out.value += char(7);
    return out.value;
}
inline std::string normals(uint32_t rgba = 0xffff8080, bool absent = false) {
    Bytes out;
    out.value.assign("BWNRM2\0\0", 8);
    out.u32(1);
    out.u32(absent ? 0 : 1);
    out.u32(absent ? platform::prepared::no_normal : 0);
    if (!absent) {
        out.name("authored");
        out.u32(1);
        out.u32(1);
        uint64_t hash = 0xcbf29ce484222325ULL;
        for (unsigned shift = 0; shift < 32; shift += 8) {
            hash ^= uint8_t(rgba >> shift);
            hash *= 0x100000001b3ULL;
        }
        out.u64(hash);
        out.u32(rgba);
    }
    return out.value;
}
inline void write_fixture_matrix(Bytes &out, double x = 0, double y = 0, double z = 0) {
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
inline std::string build_valid_v4_mesh(const std::string &toe_name = "",
                                       const std::string &batch_owner = "control",
                                       const std::string &batch_visibility = "panel",
                                       double toe_x = 0.5, double toe_y = 0.2, double toe_z = -0.1,
                                       const std::string &omitted_rest = "") {
    Bytes out;
    out.value = std::string("BWMESH4\0", 8);
    out.u32(1); // 1 batch

    struct BoneDef {
        std::string name;
        std::string control;
        double x, y, z;
    };
    std::vector<BoneDef> bone_defs = {{"Pelvis", "", 0, 0, 2},
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
        std::string name;
        double x, y, z;
    };
    std::vector<RefDef> ref_defs = {
        {"hip", 0, 0, 2},      {"torso", 0, 0, 2},   {"larm", -1, 0, 2},     {"rarm", 1, 0, 2},
        {"lfoot", -0.5, 0, 0}, {"rfoot", 0.5, 0, 0}, {"lthigh", -0.5, 0, 2}, {"rthigh", 0.5, 0, 2},
        {"lcalf", -0.5, 0, 1}, {"rcalf", 0.5, 0, 1}};

    uint32_t donor_bone_idx = 0;
    if (!toe_name.empty()) {
        std::string bone_name = "Toe0_" + toe_name;
        bone_defs.push_back({bone_name, toe_name, toe_x, toe_y, toe_z});
        ref_defs.insert(ref_defs.begin(), {toe_name, toe_x, toe_y, toe_z});
        donor_bone_idx = static_cast<uint32_t>(bone_defs.size() - 1);
    }

    out.u32(static_cast<std::uint32_t>(bone_defs.size()));
    out.u32(static_cast<std::uint32_t>(ref_defs.size() -
        (omitted_rest.empty() ? 0 : 1)));
    out.u32(0); // flags
    out.f64(0); // hip_drop
    out.f64(0);
    out.f64(0); // walk_x
    out.f64(0);
    out.f64(0); // walk_z

    for (const auto &b : bone_defs) {
        out.name(b.name.c_str());
        out.name(b.control.c_str());
        out.u32(0xffffffff);
        write_fixture_matrix(out, b.x, b.y, b.z);
    }

    for (const auto &r : ref_defs) {
        if (r.name == omitted_rest)
            continue;
        out.name(r.name.c_str());
        write_fixture_matrix(out, r.x, r.y, r.z);
    }

    out.name(batch_owner.c_str());
    out.name(batch_visibility.c_str());
    out.u32(donor_bone_idx);
    out.u32(3);          // 3 vertices
    out.u32(0xffffffff); // color
    for (int i = 0; i < 3; ++i) {
        // Keep the historical no-toe fixture bytes; toe cases need a real UV triangle.
        const platform::prepared::Vertex triangle[3] = {
            {0, .8f, -.6f, -1, 0, 0, 0, 0},
            {0, -.8f, -.6f, -1, 0, 0, 1, 0},
            {0, 0, .6f, -1, 0, 0, .5f, 1}};
        const platform::prepared::Vertex old_vertex{
            0, 0, i == 0 ? 1.f : 0.f, 0, 0, 1, 0, 0};
        for (float value : toe_name.empty() ? old_vertex : triangle[i])
            out.f32(value);
    }
    return out.value;
}

// Complete original-control witness. The omitted toe is the only absent reference.
// This is test-owned state, never a source identity registered by production.
struct DonorTree {
    std::unique_ptr<zcls::Node, int (*)(zcls::Node *)> root{zcls::object3d_create(),
                                                        zcls::tree_destroy};
    std::map<std::string, zcls::Node *> controls;
    std::vector<zcls::Node *> nodes;
    std::shared_ptr<zcls::SourceAsset> asset = std::make_shared<zcls::SourceAsset>();
    zmod::Model model{};
    std::array<float, 12> frame{1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 4};
    std::string toe;

    DonorTree(const std::string &toe_name, bool full) : toe(toe_name) {
        if (!root)
            throw std::runtime_error("Donor fixture root allocation failed");
        asset->name = "mech_authored_1.flt";
        zcls::node_set_name(root.get(), "actor");
        root->source_asset = asset;
        root->source_asset_root = true;
        nodes.push_back(root.get());
        asset->nodes["actor"] = 1;
        auto *control = add("control", root.get());
        add("panel", control);
        struct Rest { const char *name; float x, y, z; };
        // Donor coordinates map to original coordinates (-y,z,-x).
        for (const auto &rest : {Rest{"hip", 0, 0, 2}, Rest{"torso", 0, 0, 2},
                 Rest{"larm", -1, 0, 2}, Rest{"rarm", 1, 0, 2},
                 Rest{"lfoot", -.5f, 0, 0}, Rest{"rfoot", .5f, 0, 0},
                 Rest{"lthigh", -.5f, 0, 2}, Rest{"rthigh", .5f, 0, 2},
                 Rest{"lcalf", -.5f, 0, 1}, Rest{"rcalf", .5f, 0, 1}}) {
            auto *node = add(rest.name, root.get());
            const float matrix[12]{1, 0, 0, 0, 1, 0, 0, 0, 1, -rest.y, rest.z, -rest.x};
            zcls::object3d_set_matrix(node, matrix);
        }
        if (full) {
            auto *node = add(toe.c_str(), controls.at(toe.front() == 'l' ? "lfoot" : "rfoot"));
            // Analytic toe offset: donor (.1,.2,-.1), original (-.2,-.1,-.1).
            const float matrix[12]{1, 0, 0, 0, 1, 0, 0, 0, 1, -.2f, -.1f, -.1f};
            zcls::object3d_set_matrix(node, matrix);
        }
        const std::uint32_t count = 3;
        std::memcpy(model.header + 0x14, &count, sizeof count);
        controls.at("panel")->model = &model;
        controls.at("panel")->source_model_vertices = count;
    }
    DonorTree(const DonorTree &) = delete;
    DonorTree &operator=(const DonorTree &) = delete;
    ~DonorTree() { controls.at("panel")->model = nullptr; }
    zcls::Node *add(const char *name, zcls::Node *parent) {
        auto *node = zcls::object3d_create();
        if (!node)
            throw std::runtime_error("Donor fixture node allocation failed");
        if (zcls::object3d_add_child(parent, node) != 0) {
            zcls::tree_destroy(node);
            throw std::runtime_error("Donor fixture hierarchy failed");
        }
        zcls::node_set_name(node, name);
        node->source_asset = asset;
        nodes.push_back(node);
        controls.emplace(name, node);
        asset->nodes[name] = 1;
        return node;
    }
    void pose_foot() {
        auto *foot = controls.at(toe.front() == 'l' ? "lfoot" : "rfoot");
        const float z = toe.front() == 'l' ? .5f : -.5f;
        const float matrix[12]{0, 1, 0, -1, 0, 0, 0, 0, 1, .25f, .1f, z - .2f};
        zcls::object3d_set_matrix(foot, matrix);
    }
    platform::ModelDrawContext context() const {
        platform::ModelDrawContext context;
        context.node = controls.at("panel");
        context.ordinary = true;
        context.source_vertices = 3;
        context.source_polygons = 1;
        context.model_to_camera = context.model_to_world = frame.data();
        context.near_z = context.clip_near = .1f;
        context.far_z = 10;
        context.fx_near = context.fy_near = 50;
        context.cx = context.cy = 32;
        return context;
    }
    std::string raw_state() const {
        std::string result;
        for (const auto *node : nodes) {
            result.append(reinterpret_cast<const char *>(node->raw), sizeof node->raw);
            result.append(reinterpret_cast<const char *>(
                              static_cast<const zcls::Object3d *>(node->data)->raw), 0x90);
        }
        return result;
    }
};

inline std::string donor_materials(std::uint64_t mesh_hash,
                                   const char *asset_id = "authored:distance") {
    Bytes out;
    out.value.assign("BWSFM1\0\0", 8);
    out.u32(1); out.u32(1); out.u32(1); out.u32(1);
    out.u64(mesh_hash);
    out.u32(0);
    auto text = [&](const char *name) {
        out.u32(static_cast<std::uint32_t>(std::strlen(name)));
        out.value += name;
    };
    text(asset_id); text("authored");
    out.u32(0); out.u32(0xffffffff);
    out.f32(.5f); out.f32(.05f); out.f32(.05f); out.u32(1);
    for (float value : {1.f, 1.f, 0.f, 0.f}) out.f32(value);
    out.u32(1); out.u32(1);
    for (float value : {0.f, 0.f, 1.f, 1.f, 0.f, 0.f, 0.f, 0.f,
                       0.f, 0.f, .7f, .04f, 0.f}) out.f32(value);
    text("toe_height"); out.u32(1); out.u32(2); out.u32(2);
    const unsigned char pixels[16]{32,0,0,255,96,0,0,255,160,0,0,255,224,0,0,255};
    std::uint64_t hash = 0xcbf29ce484222325ULL;
    for (auto value : pixels) { hash ^= value; hash *= 0x100000001b3ULL; }
    out.u64(hash);
    out.value.append(reinterpret_cast<const char *>(pixels), sizeof pixels);
    return out.value;
}
} // namespace prepared_fixture
