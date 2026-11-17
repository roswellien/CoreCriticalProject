#pragma once

#include "frontend/core_critical/renderer/surface_materials.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <filesystem>
#include <istream>
#include <map>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

// Project-authored prepared visual payloads. These readers contain no assets
// and operate independently of SDL, Vulkan, game memory and the original file
// formats.
namespace platform::prepared {

using Matrix = std::array<double, 16>;
using Vertex = std::array<float, 8>; // position xyz, normal xyz, UV

struct Bone {
    std::string name, control;
    int32_t parent = -1;
    Matrix rest{};
};
struct Reference {
    std::string name;
    Matrix rest{};
};
struct Rig {
    bool ground_reference = false;
    double hip_drop = 0;
    std::array<double, 2> walk_x{}, walk_z{};
    std::vector<Bone> bones;
    std::vector<Reference> references;
};
struct Batch {
    std::string owner, visibility, placement_frame, joint_frame, anchor_control;
    std::array<float, 3> placement_offset{}, joint_offset{}, anchor_position{};
    uint32_t color = 0xffffffff;
    uint32_t donor_bone = 0xffffffff;
    std::vector<Vertex> vertices;
    std::vector<uint32_t> donor_indices;
};
struct Mesh {
    unsigned version = 0;
    Rig rig;
    std::vector<Batch> batches;
};
struct Image {
    std::string name;
    unsigned width = 0, height = 0;
    uint64_t hash = 0;
    std::vector<uint16_t> pixels; // RGB565; alpha belongs to the source material
};
struct Textures {
    std::vector<uint32_t> bindings;
    std::vector<Image> images;
};

constexpr uint32_t no_normal = 0xffffffff;
struct NormalImage {
    std::string name;
    unsigned width = 0, height = 0;
    uint64_t hash = 0;
    std::vector<uint32_t> pixels; // linear RGBA8; alpha retains its authored meaning
};
struct Normals {
    std::vector<uint32_t> bindings; // per batch, image index or explicit no_normal
    std::vector<NormalImage> images;
};

Mesh read_mesh(std::istream &input);
Textures read_textures(std::istream &input);
Normals read_normals(std::istream &input, const Textures &textures);
void validate_bindings(const Mesh &mesh, const Textures &textures);
mw34::materials::SurfaceMaterialPack
validate_surface_materials(std::istream &input, const std::string &expected_asset_id,
                           uint64_t expected_mesh_uv_hash,
                           const std::vector<std::string> &expected_batch_materials);

// Owned, validated optional pack resources. Selection never enables a stage.
enum class EnvironmentRole {
  water,
  surf,
  cloud,
  effects,
  lighting,
  ground_materials,
  surface_materials
};
struct MissionAmbientOverride {
  std::array<float, 3> color{};
  float strength{};
};
struct MissionSkyOverride {
  std::array<float, 3> tint{};
  float brightness{};
};
struct MissionSkyGlowOverride {
  std::array<float, 3> color{};
  float strength{};
  float focus{};
};
struct MissionHorizonOverride {
  float low{};
  float high{};
};
// Expectations exported from canonical source bytes before rendering. The
// logical container is deliberately not a pack path or a launch argument.
struct MaterialTargetSource {
  std::string kind, member, sha256;
  std::uint64_t bytes{};
  std::uint32_t model_slot{};
  bool operator==(const MaterialTargetSource &other) const {
    return std::tie(kind, member, sha256, bytes, model_slot) ==
           std::tie(other.kind, other.member, other.sha256, other.bytes, other.model_slot);
  }
};
struct MaterialTarget {
  std::string asset_id, sidecar_path, sidecar_sha256;
  MaterialTargetSource source;
  std::uint64_t mesh_uv_hash{};
  std::vector<std::string> polygon_materials;
  std::vector<std::optional<mw34::materials::SurfaceKey>> surface_keys;
  std::shared_ptr<const mw34::materials::SurfaceMaterialPack> pack;
};
inline bool require_material_target_source(const MaterialTarget &target,
                                           const MaterialTargetSource *actual,
                                           bool height_enabled) {
  if (!height_enabled)
    return false;
  if (!actual || !(*actual == target.source))
    throw std::runtime_error("Native height target requires canonical gamez producer provenance");
  return true;
}
struct EnvironmentSelection {
  std::shared_ptr<mw34::materials::SurfaceDecodedBudget> surface_budget;
  std::map<std::string, std::string> banks;
  std::map<std::string, std::map<EnvironmentRole, std::string>> resources;
  std::map<EnvironmentRole, std::string> detail_digests;
  std::map<std::string, MissionAmbientOverride> mission_ambient;
  std::map<std::string, MissionSkyOverride> mission_sky;
  std::map<std::string, MissionSkyGlowOverride> mission_sky_glow;
  std::map<std::string, MissionHorizonOverride> mission_horizon;
  std::vector<std::string> authored_manifests, world_manifests, regions;
  std::map<std::string, std::vector<MaterialTarget>> material_targets;
  std::string identity;
};
struct MaterialTargetSourceGroup {
  std::string member, sha256;
  std::uint64_t bytes{};
  std::vector<std::uint32_t> model_slots;
  bool operator==(const MaterialTargetSourceGroup &other) const {
    return std::tie(member, sha256, bytes, model_slots) ==
           std::tie(other.member, other.sha256, other.bytes, other.model_slots);
  }
};
namespace detail {
inline bool validate_canonical_member(const std::string &member) {
  if (member.empty() || member.front() == '/' || member.front() == '\\')
    return false;
  if (member.find(':') != std::string::npos)
    return false;
  std::size_t start = 0;
  while (start <= member.size()) {
    const std::size_t slash = member.find('/', start);
    const std::string segment = slash == std::string::npos
                                    ? member.substr(start)
                                    : member.substr(start, slash - start);
    if (segment.empty() || segment == "." || segment == "..")
      return false;
    for (char c : segment) {
      const auto uc = static_cast<unsigned char>(c);
      if (uc <= 0x20 || uc >= 0x7f || (c >= 'A' && c <= 'Z') || c == '\\')
        return false;
    }
    if (slash == std::string::npos)
      break;
    start = slash + 1;
    if (start == member.size())
      return false;
  }
  return true;
}
inline bool validate_canonical_sha256(const std::string &sha) {
  if (sha.size() != 64)
    return false;
  for (char c : sha) {
    if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f')))
      return false;
  }
  return true;
}
} // namespace detail
inline std::vector<MaterialTargetSourceGroup>
collect_material_target_sources(const EnvironmentSelection *selection,
                                bool enabled) {
  if (!enabled || !selection || selection->material_targets.empty())
    return {};
  constexpr std::uint64_t max_producer_source_bytes = 512ULL * 1024 * 1024;
  std::map<std::string, MaterialTargetSourceGroup> groups;
  for (const auto &[region, targets] : selection->material_targets) {
    for (const auto &target : targets) {
      const auto &src = target.source;
      if (src.kind != "gamez-zbd-v27")
        throw std::runtime_error("Unsupported material target source kind");
      if (!detail::validate_canonical_member(src.member))
        throw std::runtime_error("Invalid canonical relative material target source member: " + src.member);
      if (!detail::validate_canonical_sha256(src.sha256))
        throw std::runtime_error("Invalid canonical SHA-256 for material target source");
      if (src.bytes < 1 || src.bytes > max_producer_source_bytes)
        throw std::runtime_error("Material target source bytes out of bounds (1..512MiB)");
      if (src.model_slot >= 1048576)
        throw std::runtime_error("Material target source model_slot exceeds 1048575");
      auto it = groups.find(src.member);
      if (it == groups.end()) {
        MaterialTargetSourceGroup group;
        group.member = src.member;
        group.sha256 = src.sha256;
        group.bytes = src.bytes;
        group.model_slots.push_back(src.model_slot);
        groups.emplace(src.member, std::move(group));
      } else {
        if (it->second.sha256 != src.sha256 || it->second.bytes != src.bytes) {
          throw std::runtime_error("Conflicting digest or size for source member: " + src.member);
        }
        it->second.model_slots.push_back(src.model_slot);
      }
    }
  }
  std::vector<MaterialTargetSourceGroup> result;
  result.reserve(groups.size());
  for (auto &[member, group] : groups) {
    std::sort(group.model_slots.begin(), group.model_slots.end());
    group.model_slots.erase(
        std::unique(group.model_slots.begin(), group.model_slots.end()),
        group.model_slots.end());
    result.push_back(std::move(group));
  }
  return result;
}
EnvironmentSelection
load_environment_packs(const std::vector<std::string> &roots);
std::string environment_region(const std::string &mission);
// Revalidates content before a hit; corruption cannot reuse an older admission.
class EnvironmentPackCache {
public:
  explicit EnvironmentPackCache(
      std::uint64_t max_decoded_bytes = mw34::materials::max_surface_sidecar_bytes)
      : surface_budget_(std::make_shared<mw34::materials::SurfaceDecodedBudget>(max_decoded_bytes)) {
    selection_.surface_budget = surface_budget_;
  }
  const EnvironmentSelection &resolve(const std::vector<std::string> &roots);
  std::uint64_t hits() const { return hits_; }
  std::uint64_t generation() const { return generation_; }

private:
  std::shared_ptr<mw34::materials::SurfaceDecodedBudget> surface_budget_;
  std::map<std::pair<std::string, std::string>,
           std::weak_ptr<const mw34::materials::SurfaceMaterialPack>> surface_cache_;
  EnvironmentSelection selection_;
  std::uint64_t hits_{}, generation_{};
};

} // namespace platform::prepared
