#pragma once

#include "frontend/sdl/cpu_interval.h"
#include "frontend/sdl/sdl_render3d.h"
#include "platform/prepared_visuals.h"
#include "renderer/surface_materials.hpp"
#include "prepared_skin_cache.hpp"

#include <optional>

namespace cc_mw3_re {

std::optional<::platform::prepared::Matrix>
original_headlight_socket(const ::platform::ModelDrawContext &context,
                          const std::string &attachment,
                          std::vector<std::uintptr_t> *ancestry = nullptr);

struct PreparedBatchDraw {
    const ::platform::prepared::Batch *batch{};
    const ::platform::prepared::Image *texture{};
    std::shared_ptr<const ::platform::prepared::Textures> texture_owner;
    const ::platform::prepared::NormalImage *normal{};
    const ::mw34::materials::SurfaceMaterialRecord *surface_material{};
    std::shared_ptr<const ::mw34::materials::HeightBinding> height_binding;
    ::platform::prepared::Matrix camera{}, world{};
    // Mixed-bone seams follow the existing CPU visual deformation contract.
    // Their per-frame vertices are submitted as TL data, never cached as
    // immutable geometry.
    std::vector<::platform::prepared::Vertex> deformed;
};
struct PreparedModelDraw {
    bool replace{};
    std::vector<PreparedBatchDraw> batches;
};
struct PreparedTextureResources {
    std::vector<const ::platform::prepared::Batch *> rigid_batches;
    std::size_t matched_source_assets{};
    std::vector<const ::platform::prepared::Image *> textures;
    std::vector<const ::platform::prepared::NormalImage *> normals;
};

using PreparedMaterialBinding = sdlfe::PreparedMaterialBinding;

class PreparedModels {
  public:
    struct CpuStatistics {
        std::uint64_t calls{}, selection_ticks{}, retarget_ticks{}, deform_ticks{};
    };
    const CpuStatistics &cpu_statistics() const { return cpu_statistics_; }
    explicit PreparedModels(const sdlfe::CoreCriticalAssets &options,
                            const std::vector<PreparedMaterialBinding> &materials = {});
    bool empty() const { return models_.empty(); }
    struct LoadedAssets {
        std::size_t lods{}, normals{}, materials{}, skins{};
    };
    LoadedAssets loaded_assets() const;
    std::uint64_t surface_decoded_bytes() const { return surface_budget_->used(); }
    const std::shared_ptr<::mw34::materials::SurfaceDecodedBudget> &surface_budget() const {
        return surface_budget_;
    }
    bool has_binding(const ::platform::ModelDrawContext &context) const;
    const ::platform::prepared::Image *named_texture(const char *name) const;
    PreparedTextureResources
    resources_for_assets(const std::vector<std::string> &source_assets) const;
    // Also used by a future mission preloader; draw uses the identical cache.
    std::shared_ptr<const ::platform::prepared::Textures>
    resolve_skin(const std::string &source_asset, int32_t index) const;
    void clear_skin_cache() const {
        skin_cache_.clear();
        warned_skin_eviction_ = false;
    }
    void set_skin_cache_budget_for_test(std::size_t bytes) const { skin_cache_.set_budget(bytes); }
    std::size_t skin_cache_budget() const { return skin_cache_.budget(); }
    std::size_t skin_cache_bytes() const { return skin_cache_.bytes(); }
    std::size_t skin_cache_evictions() const { return skin_cache_.evictions(); }
    std::size_t skin_texture_loads() const { return skin_cache_.loads(); }
    PreparedModelDraw draw(const ::platform::ModelDrawContext &context,
                           bool rigid_only = false, bool lab_preview = false) const;
    std::optional<::platform::prepared::Matrix>
    donor_headlight_socket(const ::platform::ModelDrawContext &context,
                           const std::string &bone_name,
                           std::vector<std::uintptr_t> *ancestry = nullptr) const;

  private:
    struct Model {
        std::string source_asset;
        bool distance_lod{};
        mutable bool warned_cross_lod_fallback{};
        mutable bool logged_guard_clearance{};
        mutable bool warned_skin_fallback{};
        mutable std::set<int32_t> logged_skins;
        std::map<int32_t, std::string> skins;
        mutable std::set<int32_t> failed_skins;
        ::platform::prepared::Mesh mesh;
        ::platform::prepared::Textures textures;
        ::platform::prepared::Normals normals;
        std::shared_ptr<::mw34::materials::SurfaceMaterialPack> surface_materials;
        std::vector<std::shared_ptr<const ::mw34::materials::HeightBinding>> height_bindings;
    };
    const Model *model_for_asset(const std::string &source_asset) const;
    ::platform::prepared::Textures named_;
    std::vector<Model> models_;
    mutable PreparedSkinCache skin_cache_;
    mutable bool warned_skin_eviction_{};
    const bool cpu_profile_ = sdlfe::cpu_profile_requested();
    mutable CpuStatistics cpu_statistics_;
    std::shared_ptr<::mw34::materials::SurfaceDecodedBudget> surface_budget_;
};

} // namespace cc_mw3_re
