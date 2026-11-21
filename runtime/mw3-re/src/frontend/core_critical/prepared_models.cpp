#include "prepared_models.hpp"

#include "gamez/zclass/cls_data.h"
#include "gamez/zmodel/gmod_const.h"
#include "renderer/donor_retarget.hpp"
#include "platform/sha256.hpp"
#include "platform/prepared_skins.h"

#include <algorithm>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <set>
#include <string_view>

namespace cc_mw3_re {
namespace {
namespace math = mw34::donor;
using platform::prepared::Batch;
using platform::prepared::Matrix;
using zcls::Node;

const Node *source_root(const Node *node, bool allow_detached_subtree = false) {
    const Node *root = node;
    for (unsigned depth = 0; !root->source_asset_root; ++depth) {
        if (depth >= 64 || root->parent_count() > 1)
            return nullptr;
        // Destroyed parts are attached below the world node after leaving the
        // mech tree. Their highest same-asset node is still a usable visual root.
        if (root->parent_count() == 0)
            return allow_detached_subtree ? root : nullptr;
        if (root->parents[0]->source_asset != node->source_asset)
            return allow_detached_subtree ? root : nullptr;
        root = root->parents[0];
    }
    return root;
}

struct MechAssetKey {
    std::string_view chassis;
    bool distance_lod{};
};

std::optional<MechAssetKey> mech_asset_key(const std::string &asset) {
    constexpr std::string_view prefix = "mech_";
    constexpr std::string_view extension = ".flt";
    const std::string_view name(asset);
    if (!name.starts_with(prefix) || !name.ends_with(extension))
        return std::nullopt;

    auto chassis = name.substr(prefix.size(), name.size() - prefix.size() - extension.size());
    bool distance_lod = false;
    constexpr std::string_view distance_suffix = "_1";
    if (chassis.ends_with(distance_suffix)) {
        chassis.remove_suffix(distance_suffix.size());
        distance_lod = true;
    }
    if (chassis.empty())
        return std::nullopt;
    return MechAssetKey{chassis, distance_lod};
}

std::string_view source_node_name(const Node *node, const Node *root) {
    if (node == root && root->source_asset_root && !root->source_asset_root_name.empty())
        return root->source_asset_root_name;
    return node->name();
}

std::ifstream open(const std::string &path) {
    std::ifstream input(std::filesystem::u8path(path), std::ios::binary);
    if (!input)
        throw std::runtime_error("Cannot open prepared visual payload: " + path);
    return input;
}

Matrix from_native(const float *m) {
    if (!m)
        throw std::runtime_error("Prepared model has no native transform");
    for (int i = 0; i < 12; ++i)
        if (!std::isfinite(m[i]))
            throw std::runtime_error("Prepared model has a nonfinite native transform");
    return {m[0], m[3], m[6], m[9], m[1], m[4], m[7], m[10], m[2], m[5], m[8], m[11], 0, 0, 0, 1};
}

using Poses = std::map<std::string, Matrix>;
struct Hierarchy {
    Poses poses;
    std::map<const Node *, Matrix> nodes;
    std::map<std::string, const Node *> targets;
};

Hierarchy hierarchy(const Node *root) {
    Hierarchy output;
    std::vector<const Node *> pending{root};
    output.nodes.emplace(root, math::identity());
    for (size_t i = 0; i < pending.size(); ++i) {
        if (i >= 4096)
            throw std::runtime_error("Prepared source hierarchy exceeds its node limit");
        const auto *node = pending[i];
        const auto current = output.nodes.at(node);
        const auto name = source_node_name(node, root);
        const auto canonical = root->source_asset->nodes.find(std::string(name));
        if (canonical != root->source_asset->nodes.end() && canonical->second == 1) {
            output.poses.emplace(std::string(name), current);
            output.targets.emplace(std::string(name), node);
        }
        for (int child = 0; child < node->child_count(); ++child) {
            const auto *next = node->children[child];
            if (next->source_asset != root->source_asset || next->source_asset_root)
                continue;
            Matrix local = math::identity();
            if (next->cls() == 5) {
                const auto *data = static_cast<const zcls::Object3d *>(next->data);
                if (!data)
                    throw std::runtime_error("Prepared source control has no class data");
                if (!(data->get<uint32_t>(0) & 8)) {
                    float values[12];
                    std::memcpy(values, data->raw + 0x30, sizeof values);
                    local = from_native(values);
                }
            } else if (next->cls() != 6) {
                throw std::runtime_error("Prepared source hierarchy contains an "
                                         "unsupported transform class");
            }
            if (!output.nodes.emplace(next, math::product(current, local)).second)
                throw std::runtime_error("Prepared source hierarchy is shared or cyclic");
            pending.push_back(next);
        }
    }
    return output;
}

std::runtime_error binding_error(const Node &root, const std::string &name, size_t index,
                                 const char *field, const std::string &reason) {
    // Build context only on failure; ordinary draws keep the existing bounded name lookups.
    const auto role = field ? "batch " + std::to_string(index) + "." + field
                            : "donor reference " + std::to_string(index);
    return std::runtime_error("Prepared source " + root.source_asset->name + " [" + role +
                              "]: " + name + " (" + reason + ")");
}

void require_batch_source(const Node &root, const std::string &name, size_t index,
                          const char *field) {
    if (name.empty())
        return;
    const auto found = root.source_asset->nodes.find(name);
    if (found == root.source_asset->nodes.end())
        throw binding_error(root, name, index, field, "absent");
    if (found->second != 1)
        throw binding_error(root, name, index, field, "count " + std::to_string(found->second));
}

bool batch_frames_present(const Batch &batch, const Poses &poses) {
    for (const auto *name : {&batch.owner, &batch.visibility, &batch.placement_frame,
                             &batch.joint_frame, &batch.anchor_control})
        if (!name->empty() && !poses.count(*name))
            return false;
    return true;
}

Matrix placed(const Matrix &root, const Poses &poses, const Batch &batch) {
    Matrix result = math::product(root, poses.at(batch.owner));
    auto offset = [&](const std::string &frame, const std::array<float, 3> &amount) {
        if (frame.empty())
            return;
        const auto reference = math::product(root, poses.at(frame));
        for (unsigned row = 0; row < 3; ++row)
            for (unsigned col = 0; col < 3; ++col)
                result[row * 4 + 3] += reference[row * 4 + col] * amount[col];
    };
    offset(batch.placement_frame, batch.placement_offset);
    offset(batch.joint_frame, batch.joint_offset);
    if (!batch.anchor_control.empty()) {
        const auto parent = math::product(root, poses.at(batch.placement_frame));
        const auto anchor = math::product(root, poses.at(batch.anchor_control));
        const auto desired = math::point(
            parent, {batch.anchor_position[0], batch.anchor_position[1], batch.anchor_position[2]});
        for (unsigned row = 0; row < 3; ++row)
            result[row * 4 + 3] += desired[row] - anchor[row * 4 + 3];
    }
    return result;
}

math::Rig rig_for(const platform::prepared::Rig &source) {
    math::Rig rig;
    rig.ground_reference = source.ground_reference;
    rig.hip_drop = source.hip_drop;
    rig.walk_x = source.walk_x;
    rig.walk_z = source.walk_z;
    for (const auto &bone : source.bones)
        rig.bones.push_back({bone.name, bone.control, bone.parent, bone.rest});
    for (const auto &reference : source.references)
        rig.reference.emplace(reference.name, reference.rest);
    return rig;
}

math::Pose donor_pose(const math::Rig &rig, const Poses &poses) {
    const auto axis = math::axis(), inverse_axis = math::inverse(axis);
    Poses display;
    for (const auto &[name, matrix] : poses)
        if (rig.reference.count(name))
            display.emplace(name, math::product(math::product(axis, matrix), inverse_axis));
    // Detached controls are reconstructed only for the visual solver. Actual
    // visibility still comes from native draws; no reconstructed control is
    // emitted.
    for (const auto &[name, reference] : rig.reference)
        if (!display.count(name)) {
            const std::string side = name.front() == 'l' ? "l" : name.front() == 'r' ? "r" : "";
            std::string ancestor = "torso";
            if (!side.empty()) {
                if (name.rfind(side + "toe", 0) == 0)
                    ancestor = side + "foot";
                else if (name == side + "hand")
                    ancestor = side + "arm";
                else if (name == side + "foot")
                    ancestor = side + "calf";
                else if (name == side + "calf")
                    ancestor = side + "thigh";
                else if (name == side + "thigh")
                    ancestor = "hip";
            }
            if (!display.count(ancestor))
                ancestor = "torso";
            if (!display.count(ancestor) || !rig.reference.count(ancestor))
                throw std::runtime_error("Prepared donor rig has no surviving torso frame");
            display.emplace(name,
                            math::product(math::product(display.at(ancestor),
                                                        math::inverse(rig.reference.at(ancestor))),
                                          reference));
        }
    return math::retarget(rig, display, math::locomotion(rig, display));
}

} // namespace

std::optional<Matrix> original_headlight_socket(const platform::ModelDrawContext &context,
                                                const std::string &attachment,
                                                std::vector<std::uintptr_t> *ancestry) {
    if (ancestry)
        ancestry->clear();
    const auto *node = static_cast<const Node *>(context.node);
    if (!node || !node->source_asset || !context.model_to_world || !context.ordinary ||
        context.morphing || context.overlay || context.opacity != 1 || attachment.empty())
        return std::nullopt;
    const auto *root = source_root(node);
    if (!root)
        return std::nullopt;
    const auto live = hierarchy(root);
    const auto socket = live.poses.find(attachment);
    if (socket == live.poses.end())
        return std::nullopt;
    if (ancestry) {
        const auto it = live.targets.find(attachment);
        if (it != live.targets.end()) {
            const Node *curr = it->second;
            std::set<const Node *> seen;
            while (curr && seen.insert(curr).second) {
                ancestry->push_back(reinterpret_cast<std::uintptr_t>(curr));
                if (curr == root || curr->parent_count() != 1 ||
                    curr->parents[0]->source_asset != root->source_asset)
                    break;
                curr = curr->parents[0];
            }
        }
    }
    const auto root_world =
        math::product(from_native(context.model_to_world), math::inverse(live.nodes.at(node)));
    return math::product(root_world, socket->second);
}

PreparedModels::PreparedModels(const sdlfe::CoreCriticalAssets &options,
                               const std::vector<PreparedMaterialBinding> &materials) {
    if (!options.textures.empty()) {
        auto input = open(options.textures);
        named_ = platform::prepared::read_textures(input);
    }
    std::set<std::string> selected;
    std::map<std::pair<std::string, std::string>, std::string> normals;
    std::map<std::pair<std::string, std::string>, std::string> surface_materials;
    surface_budget_ = options.environment && options.environment->surface_budget
                          ? options.environment->surface_budget
                          : std::make_shared<mw34::materials::SurfaceDecodedBudget>();
    if (options.environment) {
        for (const auto &[region, targets] : options.environment->material_targets)
            for (const auto &target : targets)
                if (target.pack && (!target.pack->decoded_reservation ||
                                    target.pack->decoded_reservation->budget() != surface_budget_))
                    throw std::runtime_error("Foreign decoded target ownership domain");
    }
    for (const auto &binding : materials)
        if (!surface_materials.emplace(std::make_pair(binding.chassis, binding.lod), binding.path)
                 .second)
            throw std::runtime_error("Duplicate prepared surface-material selection");
    for (const auto &binding : options.normals)
        if (!normals.emplace(std::make_pair(binding.chassis, binding.lod), binding.path).second)
            throw std::runtime_error("Duplicate prepared normal-map selection");
    for (const auto &binding : options.models) {
        if (binding.chassis.empty() || binding.chassis.size() > 32 ||
            binding.chassis.find_first_not_of("abcdefghijklmnopqrstuvwxyz0123456789_") !=
                std::string::npos ||
            (binding.lod != "0" && binding.lod != "1"))
            throw std::runtime_error("--cc-model requires a lowercase chassis ID and LOD 0 or 1");
        Model model;
        model.distance_lod = (binding.lod == "1");
        model.source_asset = "mech_" + binding.chassis + (binding.lod == "1" ? "_1.flt" : ".flt");
        for (const auto &skin : options.skins) {
            if (skin.chassis != binding.chassis || skin.lod != binding.lod)
                continue;
            if (skin.index < 1 || skin.index > 135 || skin.path.empty() ||
                !model.skins.emplace(skin.index, skin.path).second)
                throw std::runtime_error("Invalid or duplicate prepared skin selection");
        }
        int32_t catalog_index = static_cast<int32_t>(platform::prepared::base_skin_count(binding.chassis));
        for (const auto &skin : *platform::prepared::configured_skin_catalog())
            if (skin.chassis == binding.chassis) {
                if (!model.skins.emplace(catalog_index++, skin.textures[model.distance_lod ? 1 : 0]).second)
                    throw std::runtime_error("Prepared catalog skin overrides a selected skin index");
            }
        if (!selected.insert(model.source_asset).second)
            throw std::runtime_error("Duplicate prepared model selection");
        const auto mat = surface_materials.find({binding.chassis, binding.lod});
        const auto source_sha = mat == surface_materials.end()
                                    ? std::string{}
                                    : platform::integrity::sha256_file(
                                          std::filesystem::u8path(binding.mesh));
        auto geometry = open(binding.mesh), textures = open(binding.textures);
        model.mesh = platform::prepared::read_mesh(geometry);
        model.textures = platform::prepared::read_textures(textures);
        platform::prepared::validate_bindings(model.mesh, model.textures);
        const auto normal = normals.find({binding.chassis, binding.lod});
        if (normal != normals.end()) {
            auto input = open(normal->second);
            model.normals = platform::prepared::read_normals(input, model.textures);
            normals.erase(normal);
            std::fprintf(stderr, "Prepared normals loaded: %s, %zu images\n",
                         model.source_asset.c_str(), model.normals.images.size());
        }
        if (mat != surface_materials.end()) {
            const auto sidecar_bytes = std::filesystem::file_size(
                std::filesystem::u8path(mat->second));
            if (sidecar_bytes < 32 || sidecar_bytes > mw34::materials::max_surface_sidecar_bytes)
                throw std::runtime_error("Prepared height sidecar byte budget exceeded");
            const auto sidecar_sha = platform::integrity::sha256_file(
                std::filesystem::u8path(mat->second));
            auto input = open(mat->second);
            std::vector<std::string> batch_materials;
            batch_materials.reserve(model.mesh.batches.size());
            for (std::size_t b = 0; b < model.mesh.batches.size(); ++b) {
                if (b < model.textures.bindings.size()) {
                    const auto img_idx = model.textures.bindings[b];
                    if (img_idx < model.textures.images.size())
                        batch_materials.push_back(model.textures.images[img_idx].name);
                    else
                        batch_materials.push_back({});
                } else {
                    batch_materials.push_back({});
                }
            }
            const uint64_t uv_hash = mw34::materials::compute_mesh_uv_hash(
                model.mesh.batches, 0, model.mesh.batches.size());
            const std::string expected_asset_id =
                binding.chassis + (binding.lod == "1" ? ":distance" : ":close");
            model.surface_materials = std::make_shared<mw34::materials::SurfaceMaterialPack>(
                mw34::materials::read_surface_materials(
                    input, expected_asset_id, uv_hash, batch_materials,
                    sidecar_bytes,
                    mw34::materials::max_surface_sidecar_bytes, surface_budget_));
            model.height_bindings.resize(model.mesh.batches.size());
            for (std::size_t b = 0; b < model.mesh.batches.size(); ++b) {
                if (model.normals.bindings.empty() ||
                    model.normals.bindings[b] == platform::prepared::no_normal)
                    continue; // Metadata-only and normal-Off remain compatible.
                const auto &image = model.textures.images.at(model.textures.bindings[b]);
                const auto &normal_image = model.normals.images.at(model.normals.bindings[b]);
                const mw34::materials::SurfaceKey albedo{
                    image.width, image.height, 1,
                    mw34::materials::normal_hash(image.pixels.data(), image.pixels.size() * 2)};
                model.height_bindings[b] = mw34::materials::resolve_height_binding(
                    model.surface_materials, b, source_sha, sidecar_sha, albedo, normal_image.width,
                    normal_image.height, normal_image.hash);
            }
            if (platform::integrity::sha256_file(std::filesystem::u8path(binding.mesh)) !=
                    source_sha ||
                platform::integrity::sha256_file(std::filesystem::u8path(mat->second)) != sidecar_sha)
                throw std::runtime_error("Prepared height source changed during admission");
            surface_materials.erase(mat);
            std::fprintf(stderr, "Prepared surface materials loaded: %s, %zu records\n",
                         model.source_asset.c_str(), model.surface_materials->records.size());
        }
        // Mesh colors are diagnostics from preparation. As in Core Critical's
        // existing adapter, a bound albedo supplies the final material color.
        for (auto &batch : model.mesh.batches)
            batch.color = 0xffffffff;
        if (model.mesh.version == 4) {
            const auto rig = rig_for(model.mesh.rig);
            std::set<std::string> names;
            for (const auto &bone : rig.bones)
                names.insert(bone.name);
            for (const char *name : {"Pelvis", "Torso_Twist", "Upperarm_Left", "Upperarm_Right",
                                     "Forearm_Left", "Forearm_Right", "Thigh_Left", "Thigh_Right",
                                     "Calf_Left", "Calf_Right", "Foot0_Left", "Foot0_Right"})
                if (!names.count(name))
                    throw std::runtime_error("Prepared donor rig is missing a required joint");
            for (const char *name : {"hip", "torso", "larm", "rarm", "lfoot", "rfoot", "lthigh",
                                     "rthigh", "lcalf", "rcalf"})
                if (!rig.reference.count(name))
                    throw std::runtime_error(
                        "Prepared donor rig is missing a required source reference");
        }
        std::fprintf(stderr, "Prepared model loaded: %s, BWMESH%u, %zu batches, %zu materials\n",
                     model.source_asset.c_str(), model.mesh.version, model.mesh.batches.size(),
                     model.textures.images.size());
        models_.push_back(std::move(model));
    }
    if (!surface_materials.empty())
        throw std::runtime_error("A prepared surface-material selection has no matching model/LOD");
    if (!normals.empty())
        throw std::runtime_error("A prepared normal-map selection has no matching model/LOD");
    if (options.lighting != "off" && models_.empty())
        throw std::runtime_error("Prepared lighting requires at least one --cc-model selection");
    if (options.lighting == "normal" && options.normals.empty())
        throw std::runtime_error("Normal lighting requires --cc-model-normals");
}

const platform::prepared::Image *PreparedModels::named_texture(const char *name) const {
    if (name)
        for (const auto &image : named_.images)
            if (image.name == name)
                return &image;
    return nullptr;
}

std::shared_ptr<const platform::prepared::Textures>
PreparedModels::resolve_skin(const std::string &source_asset, int32_t index) const {
    const auto *model = model_for_asset(source_asset);
    if (!model || index == 0)
        return {};
    const auto found = model->skins.find(index);
    if (found != model->skins.end() && !model->failed_skins.count(index)) {
        try {
            auto textures = skin_cache_.resolve(found->second, model->mesh);
            if (model->logged_skins.insert(index).second)
                std::fprintf(stderr, "Prepared skin selected: %s index %d\n", model->source_asset.c_str(), index);
            return textures;
        } catch (const std::exception &) {
            model->failed_skins.insert(index);
        }
    }
    if (!model->warned_skin_fallback) {
        std::fprintf(stderr, "Prepared skin fallback: %s index %d missing or invalid; using primary\n",
                     model->source_asset.c_str(), index);
        model->warned_skin_fallback = true;
    }
    return {};
}

const PreparedModels::Model *
PreparedModels::model_for_asset(const std::string &source_asset) const {
    for (const auto &model : models_)
        if (model.source_asset == source_asset)
            return &model;

    const auto requested = mech_asset_key(source_asset);
    if (!requested)
        return nullptr;

    const Model *closest = nullptr;
    for (const auto &model : models_) {
        const auto candidate = mech_asset_key(model.source_asset);
        if (!candidate || candidate->chassis != requested->chassis)
            continue;
        if (!closest || candidate->distance_lod == requested->distance_lod)
            closest = &model;
    }
    return closest;
}

PreparedTextureResources
PreparedModels::resources_for_assets(const std::vector<std::string> &source_assets) const {
    PreparedTextureResources resources;
    std::set<std::string> seen_source_assets;
    std::set<const Model *> seen_models;
    std::set<const platform::prepared::Image *> seen_textures;
    std::set<const platform::prepared::NormalImage *> seen_normals;

    for (const auto &source_asset : source_assets) {
        if (source_asset.empty() || !seen_source_assets.insert(source_asset).second)
            continue;
        // Share exact draw selection semantics so mission warmup prepares only
        // models that subsequent in-mission draws can actually select.
        const Model *selected = model_for_asset(source_asset);
        if (!selected)
            continue;
        ++resources.matched_source_assets;
        if (!seen_models.insert(selected).second)
            continue;

        // Mixed-bone models use a per-frame deformation path, so immutable
        // buffer warmup must not select any batch from those models.
        const bool mixed_bone_model = selected->mesh.version == 4 &&
            std::any_of(selected->mesh.batches.begin(), selected->mesh.batches.end(),
                        [](const auto &batch) { return !batch.donor_indices.empty(); });
        if (!mixed_bone_model)
            for (const auto &batch : selected->mesh.batches)
                resources.rigid_batches.push_back(&batch);

        for (std::size_t batch_index = 0; batch_index < selected->mesh.batches.size();
             ++batch_index) {
            const auto texture_index = selected->textures.bindings.at(batch_index);
            const auto *texture = &selected->textures.images.at(texture_index);
            if (seen_textures.insert(texture).second)
                resources.textures.push_back(texture);

            if (!selected->normals.bindings.empty()) {
                const auto normal_index = selected->normals.bindings.at(batch_index);
                if (normal_index != platform::prepared::no_normal) {
                    const auto *normal = &selected->normals.images.at(normal_index);
                    if (seen_normals.insert(normal).second)
                        resources.normals.push_back(normal);
                }
            }
        }
    }
    return resources;
}

PreparedModelDraw PreparedModels::draw(const platform::ModelDrawContext &context,
                                       bool rigid_only) const {
    sdlfe::CpuInterval interval(cpu_profile_ ? &cpu_statistics_.selection_ticks : nullptr);
    if (cpu_profile_)
        ++cpu_statistics_.calls;
    PreparedModelDraw output;
    const auto *node = static_cast<const Node *>(context.node);
    if (!node || !node->source_asset || !context.ordinary || context.morphing || context.overlay ||
        !std::isfinite(context.opacity) || context.opacity < 0.f || context.opacity > 1.f)
        return output;
    if (!node->model || node->model->count(0x14) != node->source_model_vertices)
        return output;
    const Model *selected = model_for_asset(node->source_asset->name);
    if (!selected)
        return output;
    // Admission must not run mixed-bone vertex deformation merely to discover
    // that this early GPU route cannot consume it.
    if (rigid_only && selected->mesh.version == 4)
        for (const auto &batch : selected->mesh.batches)
            if (!batch.donor_indices.empty())
                return output;
    const auto *root = source_root(node, true);
    if (!root)
        return output; // ambiguous ancestry keeps the ordinary native geometry
    const auto live = hierarchy(root);
    const auto requested_asset = mech_asset_key(node->source_asset->name);
    const auto selected_asset = mech_asset_key(selected->source_asset);
    const bool cross_lod_fallback =
        requested_asset && selected_asset && requested_asset->chassis == selected_asset->chassis &&
        requested_asset->distance_lod != selected_asset->distance_lod;
    const auto &references = selected->mesh.rig.references;
    const bool missing_live_rig_frame = std::any_of(
        references.begin(), references.end(), [&](const auto &reference) {
            return !live.poses.count(reference.name);
        });
    bool missing_live_batch_frame = false;
    for (const auto &batch : selected->mesh.batches)
        missing_live_batch_frame |= !batch_frames_present(batch, live.poses);

    // A detached subtree and a cross-LOD selection can legitimately lack frames
    // required by the selected geometry. Decide those cases before strict source
    // binding checks, which remain authoritative for exact attached models.
    if (cross_lod_fallback && (missing_live_rig_frame || missing_live_batch_frame)) {
        // Native distance geometry can be untextured. Report the declined
        // replacement once per selected model instead of silently drawing it flat.
        if (!selected->warned_cross_lod_fallback) {
            std::fprintf(stderr,
                         "Prepared model fallback: %s cannot use %s (missing live frames); "
                         "retaining native geometry, which may be untextured. "
                         "Load a matching prepared LOD.\n",
                         node->source_asset->name.c_str(), selected->source_asset.c_str());
            selected->warned_cross_lod_fallback = true;
        }
        return output;
    }
    if (!root->source_asset_root && (missing_live_rig_frame || missing_live_batch_frame))
        return output;

    for (size_t b = 0; b < selected->mesh.batches.size(); ++b) {
        const auto &batch = selected->mesh.batches[b];
        require_batch_source(*root, batch.owner, b, "owner");
        require_batch_source(*root, batch.visibility, b, "visibility");
        require_batch_source(*root, batch.placement_frame, b, "placement_frame");
        require_batch_source(*root, batch.joint_frame, b, "joint_frame");
        require_batch_source(*root, batch.anchor_control, b, "anchor_control");
    }
    for (size_t r = 0; r < references.size(); ++r) {
        const auto &name = references[r].name;
        const auto &nodes = root->source_asset->nodes;
        const auto found = nodes.find(name);
        if (found != nodes.end()) {
            if (found->second != 1)
                throw binding_error(*root, name, r, nullptr,
                                    "count " + std::to_string(found->second));
            continue; // Canonical-present detached controls retain the existing solver behavior.
        }
        const bool toe = name == "ltoe01" || name == "ltoe02" || name == "ltoe03" ||
                         name == "rtoe01" || name == "rtoe02" || name == "rtoe03";
        if (selected->mesh.version != 4 || !selected->distance_lod || !toe)
            throw binding_error(*root, name, r, nullptr, "absent");

        // Original distance trees omit these donor-only toes. Mandatory fields above
        // already reject any batch using an absent toe; only visual solver references
        // can reach this exception. Do not infer LOD from the source name spelling.
        const char *foot = name.front() == 'l' ? "lfoot" : "rfoot";
        for (const char *anchor : {foot, "torso"}) {
            const auto canonical = nodes.find(anchor);
            if (canonical == nodes.end())
                throw binding_error(*root, name, r, nullptr,
                                    std::string("dependency ") + anchor + " absent");
            if (canonical->second != 1)
                throw binding_error(*root, name, r, nullptr,
                                    std::string("dependency ") + anchor + " count " +
                                        std::to_string(canonical->second));
            bool rest_found = false;
            for (const auto &reference : references)
                rest_found |= reference.name == anchor;
            if (!rest_found)
                throw binding_error(*root, name, r, nullptr,
                                    std::string("dependency ") + anchor + " rest absent");
        }
    }
    const auto inverse_node = math::inverse(live.nodes.at(node));
    const auto root_camera = math::product(from_native(context.model_to_camera), inverse_node);
    const auto root_world = math::product(from_native(context.model_to_world), inverse_node);
    math::Pose donor;
    if (selected->mesh.version == 4) {
        sdlfe::CpuInterval retarget(cpu_profile_ ? &cpu_statistics_.retarget_ticks : nullptr);
        donor = donor_pose(rig_for(selected->mesh.rig), live.poses);
    }
    output.replace = true;
    const auto skin_owner = resolve_skin(selected->source_asset, node->prepared_skin_index);
    const auto &textures = skin_owner ? *skin_owner : selected->textures;
    for (size_t index = 0; index < selected->mesh.batches.size(); ++index) {
        const auto &batch = selected->mesh.batches[index];
        const auto &visibility = batch.visibility.empty() ? batch.owner : batch.visibility;
        if (visibility != source_node_name(node, root) ||
            !live.poses.count(batch.owner))
            continue;
        PreparedBatchDraw draw;
        draw.batch = &batch;
        draw.texture_owner = skin_owner;
        draw.texture = &textures.images.at(textures.bindings[index]);
        if (!skin_owner && index < selected->height_bindings.size())
            draw.height_binding = selected->height_bindings[index];
        if (!selected->normals.bindings.empty()) {
            const auto normal = selected->normals.bindings[index];
            if (normal != platform::prepared::no_normal)
                draw.normal = &selected->normals.images.at(normal);
        }
        if (!skin_owner && selected->surface_materials && !selected->surface_materials->bindings.empty()) {
            const auto sm_index = selected->surface_materials->bindings[index];
            if (sm_index != ::mw34::materials::no_surface_material &&
                sm_index < selected->surface_materials->records.size())
                draw.surface_material = selected->surface_materials->records[sm_index].get();
        }
        if (selected->mesh.version != 4) {
            draw.camera = placed(root_camera, live.poses, batch);
            draw.world = placed(root_world, live.poses, batch);
        } else {
            const auto camera = math::product(root_camera, math::inverse(math::axis()));
            const auto world = math::product(root_world, math::inverse(math::axis()));
            if (batch.donor_indices.empty()) {
                draw.camera = math::product(camera, donor.world.at(batch.donor_bone));
                draw.world = math::product(world, donor.world.at(batch.donor_bone));
            } else {
                sdlfe::CpuInterval deform(cpu_profile_ ? &cpu_statistics_.deform_ticks : nullptr);
                draw.camera = camera;
                draw.world = world;
                draw.deformed = batch.vertices;
                for (size_t vertex = 0; vertex < draw.deformed.size(); ++vertex) {
                    auto &value = draw.deformed[vertex];
                    const auto &bone = donor.world.at(batch.donor_indices[vertex]);
                    const auto position = math::point(bone, {value[0], value[1], value[2]});
                    const auto inverse = math::inverse(bone);
                    const auto normal = math::unit(
                        {inverse[0] * value[3] + inverse[4] * value[4] + inverse[8] * value[5],
                         inverse[1] * value[3] + inverse[5] * value[4] + inverse[9] * value[5],
                         inverse[2] * value[3] + inverse[6] * value[4] + inverse[10] * value[5]});
                    for (unsigned axis = 0; axis < 3; ++axis) {
                        value[axis] = float(position[axis]);
                        value[axis + 3] = float(normal[axis]);
                    }
                }
            }
        }
        output.batches.push_back(std::move(draw));
    }
    return output;
}

bool PreparedModels::has_binding(const platform::ModelDrawContext &context) const {
    const auto *node = static_cast<const Node *>(context.node);
    if (!node || !node->source_asset)
        return false;
    return model_for_asset(node->source_asset->name) != nullptr;
}

std::optional<Matrix>
PreparedModels::donor_headlight_socket(const platform::ModelDrawContext &context,
                                       const std::string &bone_name,
                                       std::vector<std::uintptr_t> *ancestry) const {
    if (ancestry)
        ancestry->clear();
    const auto *node = static_cast<const Node *>(context.node);
    if (!node || !node->source_asset || !context.model_to_world || !context.ordinary ||
        context.morphing || context.overlay || context.opacity != 1 || bone_name.empty())
        return std::nullopt;
    const auto *root = source_root(node);
    if (!root)
        return std::nullopt;
    const Model *selected = model_for_asset(node->source_asset->name);
    if (!selected || selected->mesh.version != 4 || selected->mesh.rig.bones.empty())
        return std::nullopt;
    int bone_index = -1;
    for (std::size_t i = 0; i < selected->mesh.rig.bones.size(); ++i) {
        const auto &b = selected->mesh.rig.bones[i];
        if (b.name == bone_name || b.control == bone_name) {
            bone_index = static_cast<int>(i);
            break;
        }
    }
    if (bone_index < 0)
        return std::nullopt;
    const auto live = hierarchy(root);
    const auto it_node = live.nodes.find(node);
    if (it_node == live.nodes.end())
        return std::nullopt;
    if (ancestry) {
        const auto &ctrl = selected->mesh.rig.bones[static_cast<std::size_t>(bone_index)].control;
        const auto it = live.targets.find(!ctrl.empty() ? ctrl : bone_name);
        if (it != live.targets.end()) {
            const Node *curr = it->second;
            std::set<const Node *> seen;
            while (curr && seen.insert(curr).second) {
                ancestry->push_back(reinterpret_cast<std::uintptr_t>(curr));
                if (curr == root || curr->parent_count() != 1 ||
                    curr->parents[0]->source_asset != root->source_asset)
                    break;
                curr = curr->parents[0];
            }
        }
    }
    const auto rig = rig_for(selected->mesh.rig);
    const auto donor = donor_pose(rig, live.poses);
    if (static_cast<std::size_t>(bone_index) >= donor.world.size())
        return std::nullopt;
    const auto root_world =
        math::product(from_native(context.model_to_world), math::inverse(it_node->second));
    const auto world = math::product(root_world, math::inverse(math::axis()));
    return math::product(world, donor.world.at(static_cast<std::size_t>(bone_index)));
}

} // namespace cc_mw3_re
