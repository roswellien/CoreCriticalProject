#pragma once

#include "gamez/zmodel/gmod_geometry.h"
#include "platform/prepared_visuals.h"
#include "platform/render3d.h"
#include "renderer/geometry/resource.hpp"
#include "renderer/material_normals.hpp"
#include "renderer/native_surface_identity.hpp"
#include "renderer/surface_materials.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>
#include <type_traits>
#include <vector>

namespace cc_mw3_re {

struct RigidCaptureSeal;
class VulkanFrameRenderer;

struct CapturedRgbaImage {
    std::uint32_t width{}, height{};
    std::vector<std::uint32_t> pixels32;
};

struct CapturedNativeRigidRange {
    std::uint32_t polygon{}, material_slot{};
    cc::geometry::Material material{};
    std::shared_ptr<const CapturedRgbaImage> albedo_image;
    std::shared_ptr<const CapturedRgbaImage> normal_image;
    int texture_handle{-1};
    mw34::materials::SurfaceKey albedo_key{};
    std::uint64_t texture_version{}, texture_group_epoch{};
    int normal_index{-1};
    std::uint32_t normal_width{}, normal_height{};
    std::uint64_t normal_hash{};
    std::array<float, 4> surface_parameters{};
    std::shared_ptr<const mw34::materials::HeightBinding> height_binding;
};

class CapturedNativeRigid final {
  public:
    CapturedNativeRigid(const CapturedNativeRigid &) = delete;
    CapturedNativeRigid &operator=(const CapturedNativeRigid &) = delete;
    CapturedNativeRigid(CapturedNativeRigid &&) = delete;
    CapturedNativeRigid &operator=(CapturedNativeRigid &&) = delete;

    const std::shared_ptr<const cc::geometry::Resource> &resource() const noexcept {
        return resource_;
    }
    const std::vector<CapturedNativeRigidRange> &ranges() const noexcept { return ranges_; }
    const std::weak_ptr<const int> &renderer_owner() const noexcept { return renderer_owner_; }
    std::uint64_t world_source_epoch() const noexcept { return world_source_epoch_; }
    std::uint64_t group_load_epoch() const noexcept { return group_load_epoch_; }

  private:
    friend struct RigidCaptureSeal;
    CapturedNativeRigid(std::shared_ptr<const cc::geometry::Resource> resource,
                        std::vector<CapturedNativeRigidRange> ranges,
                        std::weak_ptr<const int> renderer_owner,
                        std::uint64_t world_source_epoch,
                        std::uint64_t group_load_epoch)
        : resource_(std::move(resource)),
          ranges_(std::move(ranges)),
          renderer_owner_(std::move(renderer_owner)),
          world_source_epoch_(world_source_epoch),
          group_load_epoch_(group_load_epoch) {}

    std::shared_ptr<const cc::geometry::Resource> resource_;
    std::vector<CapturedNativeRigidRange> ranges_;
    std::weak_ptr<const int> renderer_owner_;
    std::uint64_t world_source_epoch_{};
    std::uint64_t group_load_epoch_{};
};

static_assert(!std::is_default_constructible_v<CapturedNativeRigid>);
static_assert(!std::is_copy_constructible_v<CapturedNativeRigid>);
static_assert(!std::is_move_constructible_v<CapturedNativeRigid>);

namespace testing {
struct RigidCaptureTestAccess;

struct RigidCaptureTestHook {
    static std::shared_ptr<const CapturedNativeRigid> capture_original_rigid(
        VulkanFrameRenderer &renderer, const zcls::Node &node,
        const ::platform::ModelDrawContext &context,
        const zmod::RigidGeometryEligibility &eligibility, std::size_t maximum_owned_bytes);
    static bool validate_captured_original_rigid(
        VulkanFrameRenderer &renderer, const CapturedNativeRigid &captured);
    static std::vector<NativeGroundRangeAdmission> native_geometry_admissions(
        VulkanFrameRenderer &renderer,
        const std::shared_ptr<const cc::geometry::Resource> &resource,
        const ::platform::ModelDrawContext &context,
        const std::vector<cc::geometry::Material> &materials);
    static std::shared_ptr<mw34::materials::SurfaceDecodedBudget> surface_budget(
        VulkanFrameRenderer &renderer);
    static void set_mission_and_environment(
        VulkanFrameRenderer &renderer, std::string mission_id,
        std::shared_ptr<const ::platform::prepared::EnvironmentSelection> environment);
    static void seed_authored_normal(VulkanFrameRenderer &renderer,
                                     const mw34::materials::SurfaceKey &key,
                                     mw34::materials::WorldNormalCache::TextureRecord record);
    static void seed_authored_no_normal(VulkanFrameRenderer &renderer,
                                        const mw34::materials::SurfaceKey &key);
    static void mutate_normal_record(VulkanFrameRenderer &renderer, int index,
                                     std::uint32_t width, std::uint32_t height,
                                     std::uint64_t hash,
                                     std::vector<std::uint32_t> pixels);
    static void advance_group_epoch(VulkanFrameRenderer &renderer);
    static std::uint64_t group_epoch(const VulkanFrameRenderer &renderer);
    static void set_slot_surface_key(VulkanFrameRenderer &renderer, int handle,
                                     const mw34::materials::SurfaceKey &key);
    static void set_slot_version(VulkanFrameRenderer &renderer, int handle,
                                 std::uint64_t version);
    static void set_slot_group_epoch(VulkanFrameRenderer &renderer, int handle,
                                     std::uint64_t epoch);
    static void set_slot_pixels(VulkanFrameRenderer &renderer, int handle,
                                unsigned width, unsigned height,
                                std::vector<std::uint32_t> pixels);
};
} // namespace testing

} // namespace cc_mw3_re
