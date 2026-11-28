#pragma once
#include "gamez/zclass/cls_node.h"
#include "gamez/zimage/zimg_texture.h"
#include "gamez/zimage/zimg_library.h"
#include "gamez/zmodel/gmod_const.h"
#include "gamez/zvideo/zvid_ddd3d.h"
#include "platform/prepared_visuals.h"
#include "surface_materials.hpp"
#include <cfenv>
#include <cmath>
#include <cstdint>
#include <optional>

namespace cc_mw3_re {
// Canonical BWSFM1 batch/vertex stream, built from original source corners.
// Positions and UVs are read before camera projection or clipping; pointers are
// borrowed only for this call. No native pointers enter a render packet.
inline std::optional<uint64_t> native_mesh_uv_hash(const zmod::Model &m) {
#if defined(__BYTE_ORDER__) && __BYTE_ORDER__ != __ORDER_LITTLE_ENDIAN__
#error "Native BWSFM1 identity requires a little-endian host"
#endif
  constexpr uint64_t kFnvOffset = 0xcbf29ce484222325ull;
  constexpr uint64_t kFnvPrime = 0x100000001b3ull;
  const uint32_t polygon_count = m.count(0x10);
  const uint32_t position_count = m.count(0x14);
  const uint32_t normal_count = m.count(0x18);
  if (m.polygons == nullptr || m.vertices == nullptr)
    return std::nullopt;
  if (polygon_count == 0 || polygon_count > 4096)
    return std::nullopt;
  if (position_count == 0 || position_count > 1048576)
    return std::nullopt;
  uint64_t h = kFnvOffset;
  auto fold_bytes = [&h, kFnvPrime](const void *p, std::size_t n) {
    const auto *b = static_cast<const unsigned char *>(p);
    for (std::size_t i = 0; i < n; ++i) {
      h ^= b[i];
      h *= kFnvPrime;
    }
  };
  auto fold_u32 = [&fold_bytes](uint32_t v) { fold_bytes(&v, sizeof v); };
  fold_u32(polygon_count);
  for (uint32_t pi = 0; pi < polygon_count; ++pi) {
    const zmod::Polygon &poly = m.polygons[pi];
    const uint32_t corner_count = poly.flags & 0xffu;
    if (corner_count < 3 || corner_count > 64)
      return std::nullopt;
    if (poly.vertex_indices == nullptr)
      return std::nullopt;
    const bool per_corner_normals = (poly.flags & 0x200u) != 0u;
    if (per_corner_normals && (poly.normal_indices == nullptr ||
                               m.normals == nullptr || normal_count == 0))
      return std::nullopt;
    const bool textured =
        poly.material != nullptr && (poly.material->flags & 0x1u) != 0u;
    if (textured && poly.uvs == nullptr)
      return std::nullopt;
    fold_u32(corner_count);
    for (uint32_t c = 0; c < corner_count; ++c) {
      const uint32_t vi = poly.vertex_indices[c];
      if (vi >= position_count)
        return std::nullopt;
      float rec[8];
      const float *xyz = m.vertices + static_cast<std::size_t>(vi) * 3u;
      rec[0] = xyz[0];
      rec[1] = xyz[1];
      rec[2] = xyz[2];
      if (per_corner_normals) {
        const uint32_t ni = poly.normal_indices[c];
        if (ni >= normal_count)
          return std::nullopt;
        const float *n = m.normals + static_cast<std::size_t>(ni) * 3u;
        rec[3] = n[0];
        rec[4] = n[1];
        rec[5] = n[2];
      } else {
        rec[3] = 0.0f;
        rec[4] = 0.0f;
        rec[5] = 0.0f;
      }
      if (textured) {
        rec[6] = poly.uvs[c * 2u + 0u];
        rec[7] = poly.uvs[c * 2u + 1u];
      } else {
        rec[6] = 0.0f;
        rec[7] = 0.0f;
      }
      for (float f : rec)
        if (!std::isfinite(f))
          return std::nullopt;
      fold_bytes(rec, sizeof rec);
    }
  }
  return h;
}

// Only this synchronous scope borrows native producer objects. The result below
// owns values and an image alias, never a Node, Model or SourceAsset map.
struct NativeGroundHeightInput {
  const zcls::Node *node{};
  const zmod::Model *model{};
  ::platform::MaterialDrawContext material{};
  mw34::materials::SurfaceKey key{}, slot_key{};
  int texture{-1}, normal_index{-1};
  std::uint32_t normal_width{}, normal_height{};
  std::uint64_t normal_hash{};
  std::uint64_t source_epoch{}, producer_epoch{}, slot_epoch{}, current_group_epoch{};
  std::uint64_t texture_version{}, current_texture_version{};
  bool enabled{}, eligible{};
};

class NativeGroundFloatScope {
public:
  NativeGroundFloatScope() {
    if (std::fegetenv(&saved_) != 0)
      throw std::runtime_error("Cannot preserve native ground floating-point state");
  }
  ~NativeGroundFloatScope() { std::fesetenv(&saved_); }
private:
  std::fenv_t saved_;
};

inline bool native_ground_eligible(const ::platform::ModelDrawContext &context) {
  NativeGroundFloatScope preserve;
  return context.ordinary && !context.morphing && !context.overlay && context.opacity == 1.f;
}

inline bool native_ground_draw_eligible(const ::platform::DrawState &state, bool hud,
                                        bool depth_only, bool debug, bool points) {
  return !hud && !depth_only && !debug && !points && !state.native_sky &&
         !state.sharp && !state.blend && !state.multiply && !state.depth_always &&
         state.depth_write && !state.alpha_modulate && !state.color_select && !state.wireframe;
}

inline bool native_ground_material_eligible(const zmod::Material &material) {
  return material.alpha == 255 &&
         !(material.texture && material.texture->image &&
           (static_cast<const zimg::Texture *>(material.texture->image)->flags & 2)) &&
         !(material.texture && material.texture->surface &&
           static_cast<const zvid::D3DTexture *>(material.texture->surface)->type != 1);
}

inline bool native_ground_source_candidate(
    const ::platform::prepared::MaterialTarget &target, const zcls::SourceAsset *source) {
  return source && source->world && source->world->member == target.source.member &&
         source->world->model_slot == target.source.model_slot;
}

// Selection does not depend on a texel key. A different original slot or a
// known library source remains ordinary even if its image is shared.
inline const ::platform::prepared::MaterialTarget *select_native_ground_target(
    const std::vector<::platform::prepared::MaterialTarget> &targets,
    const zcls::Node *node, const zmod::Model *model) {
  if (!node)
    return nullptr;
  const ::platform::prepared::MaterialTarget *selected{};
  for (const auto &target : targets) {
    const bool candidate = native_ground_source_candidate(target, node->source_asset.get()) ||
        (model && native_ground_source_candidate(target, model->world_source_asset.get()));
    if (!candidate)
      continue;
    if (selected)
      throw std::runtime_error("Ambiguous native ground source target");
    selected = &target;
  }
  const auto unknown_origin = [](const zcls::SourceAsset *source) {
    return !source || (!source->world && source->name.empty());
  };
  if (!selected && unknown_origin(node->source_asset.get()) &&
      (!model || unknown_origin(model->world_source_asset.get()))) {
    // A raw original slot can only trigger visible rejection. It cannot supply
    // the missing immutable member/container identity required by the guard.
    // Streamed targets use normal-only shading for these unproven nodes. Raw
    // slot collisions across ordinary scene nodes cannot authorize a binding.
    const auto raw_slot = node->get<std::int32_t>(0x3c);
    for (const auto &target : targets)
      if (target.streamed_bindings.empty() && raw_slot >= 0 &&
          std::uint32_t(raw_slot) == target.source.model_slot)
        throw std::runtime_error("Possible selected native ground has no source owner");
  }
  return selected;
}

inline std::shared_ptr<const mw34::materials::HeightBinding> admit_native_ground_height(
    const ::platform::prepared::MaterialTarget &target, const NativeGroundHeightInput &input,
    const std::shared_ptr<mw34::materials::SurfaceDecodedBudget> &budget,
    const mw34::materials::StreamedHeightCache *cache = nullptr) {
  NativeGroundFloatScope preserve;
  if (!input.enabled || !input.eligible)
    return {};
  const auto reject = [](const char *reason) { throw std::runtime_error(reason); };
  if (!input.model || !input.model->polygons || input.material.model != input.model ||
      input.material.polygon >= input.model->count(0x10))
    reject("Native ground original polygon scope mismatch");
  const auto polygon_index = input.material.polygon;
  const auto &polygon = input.model->polygons[polygon_index];
  const auto *material = polygon.material;
  if (!material || input.material.material != material ||
      input.material.texture_entry != material->texture)
    reject("Native ground material object mismatch");
  if (!native_ground_material_eligible(*material))
    return {};
  if (!input.node || input.node->model != input.model ||
      !input.node->source_asset ||
      input.node->source_asset != input.model->world_source_asset ||
      !input.node->source_asset->world)
    reject("Native ground source owner mismatch");
  const auto &source = *input.node->source_asset->world;
  if (source.kind != target.source.kind || source.member != target.source.member ||
      source.sha256 != target.source.sha256 || source.bytes != target.source.bytes ||
      source.model_slot != target.source.model_slot || source.kind != "gamez-zbd-v27" ||
      source.member.empty() || !source.bytes || !source.load_epoch ||
      source.sha256.size() != 64 ||
      source.sha256.find_first_not_of("0123456789abcdef") != std::string::npos ||
      source.load_epoch != input.source_epoch)
    reject("Native ground source identity/epoch mismatch");
  const auto polygon_count = input.model->count(0x10);
  if (target.polygon_materials.size() != polygon_count ||
      target.surface_keys.size() != polygon_count)
    reject("Native ground target polygon cardinality mismatch");
  // Never reuse the diagnostic fingerprint: producer arrays can be mutated
  // without replacing their immutable source owner.
  const auto fingerprint = native_mesh_uv_hash(*input.model);
  if (!fingerprint || *fingerprint != target.mesh_uv_hash)
    reject("Native ground whole original mesh/UV mismatch");
  const auto &pack = target.pack;
  const bool streamed = !target.streamed_bindings.empty();
  if (streamed && (target.streamed_bindings.size() != polygon_count || pack))
    reject("Native ground streamed polygon cardinality mismatch");
  // EnvironmentPackCache performs canonical path and before/after file SHA
  // authentication before publishing this immutable owner. This helper does no
  // file IO; a manually constructed target is only a synthetic guard fixture.
  if (!streamed && (target.sidecar_path.empty() || target.sidecar_sha256.size() != 64 ||
      target.sidecar_sha256.find_first_not_of("0123456789abcdef") != std::string::npos ||
      !pack || !pack->decoded_reservation || pack->decoded_reservation->budget() != budget ||
      !budget || (pack->version != 1 && pack->version != 2) ||
      pack->mesh_uv_hash != target.mesh_uv_hash ||
      pack->bindings.size() != polygon_count))
    reject("Native ground cached sidecar identity/budget mismatch");
  if (!streamed)
    for (const auto &record : pack->records)
      if (!record || record->asset_id != target.asset_id)
        reject("Native ground cached pack asset mismatch");
  for (std::uint32_t index = 0; index < polygon_count; ++index) {
    const auto *ordered = input.model->polygons[index].material;
    if (!ordered)
      reject("Native ground ordered material is missing");
    std::string name = "untextured";
    if (ordered->flags & 1) {
      const auto *texture = ordered->texture;
      if (streamed && (ordered->flags & 4)) {
        if (target.streamed_bindings[index])
          reject("Native ground animated material has a streamed height binding");
        // The cycle mutates the live frame pointer. Check the original GameZ
        // texture slot for ordered provenance on this unbound polygon.
        const auto &directory = zimg::textures();
        if (!ordered->cycle || directory.count <= 0 || directory.count > zimg::kMaxTextures ||
            ordered->texture_index >= std::uint32_t(directory.count))
          reject("Native ground animated material has an invalid original texture index");
        texture = &directory.entries[ordered->texture_index];
      }
      if (!texture || !std::memchr(texture->name, 0, 20))
        reject("Native ground ordered material name is invalid");
      name = texture->name;
    }
    if (name != target.polygon_materials[index])
      reject("Native ground ordered material name mismatch");
    if (streamed)
      continue;
    const auto record_index = pack->bindings[index];
    if (record_index != mw34::materials::no_surface_material &&
        (record_index >= pack->records.size() || !pack->records[record_index] ||
         pack->records[record_index]->asset_id != target.asset_id ||
         pack->records[record_index]->material_name != name ||
         (pack->records[record_index]->height_image != mw34::materials::no_surface_image &&
          (!target.surface_keys[index] || !(ordered->flags & 1)))))
      reject("Native ground cached record identity mismatch");
  }
  mw34::materials::StreamedHeightCache::Image image;
  if (streamed) {
    const auto &binding = target.streamed_bindings[polygon_index];
    if (!binding || !cache || !(image = cache->find(binding->image)))
      return {};
  } else {
    const auto record_index = pack->bindings[polygon_index];
    if (record_index == mw34::materials::no_surface_material ||
        pack->records[record_index]->height_image == mw34::materials::no_surface_image)
      return {};
  }
  if (!(material->flags & 1) || !material->texture || !material->texture->surface ||
      !target.surface_keys[polygon_index] ||
      !(input.key == *target.surface_keys[polygon_index]) || !(input.key == input.slot_key) ||
      input.texture < 0 ||
      static_cast<const zvid::D3DTexture *>(material->texture->surface)->handle != input.texture ||
      input.producer_epoch != input.current_group_epoch ||
      input.slot_epoch != input.current_group_epoch ||
      input.texture_version != input.current_texture_version || input.normal_index < 0)
    reject("Native ground current texture/normal admission mismatch");
  if (!input.key.width || !input.key.height || input.key.format != 1)
    reject("Native ground height requires opaque complete albedo identity");
  std::shared_ptr<mw34::materials::HeightBinding> snapshot;
  if (streamed) {
    if (!input.key.hash || !input.normal_hash ||
        input.key.width != image->width || input.key.height != image->height ||
        input.normal_width != image->width || input.normal_height != image->height)
      reject("Native ground streamed map resolution/identity mismatch");
    const auto &binding = *target.streamed_bindings[polygon_index];
    snapshot = std::make_shared<mw34::materials::HeightBinding>();
    snapshot->material.asset_id = target.asset_id;
    snapshot->material.material_name = target.polygon_materials[polygon_index];
    snapshot->material.height_image = binding.image;
    snapshot->material.height_reference = 0.5f;
    snapshot->material.height_amplitude = binding.amplitude;
    snapshot->material.max_displacement = binding.amplitude;
    snapshot->retained_decoded_bytes = image->pixels.size();
    snapshot->image = std::move(image);
    snapshot->source_sha256 = source.sha256;
    snapshot->sidecar_sha256 = target.sidecar_sha256;
    snapshot->mesh_uv_hash = target.mesh_uv_hash;
    snapshot->image_version = 2;
    snapshot->streamed_image = true;
    snapshot->source_batch = polygon_index;
    snapshot->albedo = input.key;
    snapshot->normal_width = input.normal_width;
    snapshot->normal_height = input.normal_height;
    snapshot->normal_hash = input.normal_hash;
  } else {
    auto resolved = mw34::materials::resolve_height_binding(
        pack, polygon_index, source.sha256, target.sidecar_sha256, input.key,
        input.normal_width, input.normal_height, input.normal_hash);
    if (!resolved)
      reject("Native ground selected height record is missing");
    snapshot = std::make_shared<mw34::materials::HeightBinding>(*resolved);
  }
  snapshot->world_source = mw34::materials::HeightWorldSource{
      source.kind, source.member, source.bytes, source.load_epoch, source.model_slot};
  snapshot->sidecar_path = target.sidecar_path;
  snapshot->producer_epoch = input.producer_epoch;
  snapshot->texture_version = input.texture_version;
  return snapshot;
}

struct NativeGroundRangeAdmission {
  std::uint32_t polygon{};
  int normal_index{-1};
  std::array<float, 4> surface_parameters{};
  std::shared_ptr<const mw34::materials::HeightBinding> height_binding;
};

// Both early emitters consume this completed vector. No scene commands are
// appended until every original polygon's admission has succeeded.
template <typename Range, typename Resolve>
inline std::vector<NativeGroundRangeAdmission> admit_native_ground_ranges(
    const Range &ranges, std::uint32_t polygon_count, Resolve resolve) {
  std::vector<NativeGroundRangeAdmission> admitted;
  admitted.reserve(ranges.size());
  for (std::size_t index = 0; index < ranges.size(); ++index) {
    if (ranges[index].polygon >= polygon_count)
      throw std::runtime_error("Native ground range is not an original polygon");
    auto value = resolve(index, ranges[index].polygon);
    value.polygon = ranges[index].polygon;
    admitted.push_back(std::move(value));
  }
  return admitted;
}
} // namespace cc_mw3_re
