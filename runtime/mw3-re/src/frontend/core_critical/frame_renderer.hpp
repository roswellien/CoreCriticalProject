#pragma once

#include <cstddef>
#include <cstdint>
#include <memory>
#include <vector>

#include "frontend/sdl/sdl_render3d.h"
#include "renderer/original_rigid_capture.hpp"
#include "renderer/renderer_bridge_config.hpp"
#include "producer_view_test_hook.hpp"

namespace mw34::vkscene {
struct Scene;
}

namespace cc_mw3_re {

struct QualityStatistics {
  // mip_levels counts generated levels below each uploaded base image.
  std::uint64_t fxaa_passes{}, anisotropic_samplers{}, mip_levels{};
};
struct AssetStatistics {
  std::uint64_t prepared_batches{}, gpu_model_draws{}, cpu_clipped_triangles{};
  // Prepared replacement upload events only; plain and generated named
  // textures are excluded.
  std::uint64_t named_textures{};
  std::uint64_t geometry_uploads{};
  std::uint64_t lit_draws{}, normal_draws{};
  std::uint64_t retired_geometry_buffers{};
  std::uint64_t gpu_prepared_vertices{}, early_prepared_models{},
      prepared_cpu_fallback_batches{};
  // Decoded world-page pixels only; excludes authored catalogs and GPU copies.
  std::uint64_t world_normal_decoded_bytes{}, world_normal_peak_decoded_bytes{},
      world_normal_loaded_pages{};
  std::uint64_t binding_rejected_mismatch{}, native_fingerprint_evaluations{};
  // Draw-time deferred receipt checks, independent of whether sun lighting runs.
  std::uint64_t deferred_material_admissions{};
};

// Read-only authored-check observation, sampled on the producer after the
// render worker drains. Unsupported implementations must say so explicitly.
struct SceneBindingStatistics {
  bool supported{};
  std::uint64_t textures{}, commands{}, draws{}, recycled_scenes{};
};

class VulkanFrameRenderer : public sdlfe::FrameRenderer {
public:
  // Successful visible presentations, including SUBOPTIMAL, across scene
  // resets.
  virtual std::uint64_t presentation_count() const = 0;
  virtual QualityStatistics quality_statistics() const = 0;
  virtual AssetStatistics asset_statistics() const = 0;
  virtual cc::geometry::Statistics geometry_statistics() const = 0;
  virtual SceneBindingStatistics scene_binding_statistics() { return {}; }
  virtual bool observe_producer_views(testing::ProducerViewObserver*) { return false; }
};

RendererBridgeConfig configure_bridge(
    sdlfe::RendererBackend backend = sdlfe::RendererBackend::core_critical_dxgi,
    const sdlfe::CoreCriticalQuality &quality = {},
    const sdlfe::CoreCriticalAssets &assets = {});

std::unique_ptr<VulkanFrameRenderer> make_renderer(
    SDL_Window *window,
    sdlfe::RendererBackend backend = sdlfe::RendererBackend::core_critical_dxgi,
    const sdlfe::CoreCriticalQuality &quality = {},
    const sdlfe::CoreCriticalAssets &assets = {});

namespace testing {
struct NamedTextureTestState {
  unsigned width{}, height{}, source_width{}, source_height{};
  bool generated_rgba{};
  std::vector<std::uint32_t> pixels;
};
NamedTextureTestState named_texture_state(VulkanFrameRenderer &renderer,
                                          int32_t handle);

struct StagingTestState {
  std::size_t peak_bytes{}, early_completions{}, early_log_lines{};
  // Pending bytes/packets seen at the first local-light flush after the last mission change.
  std::size_t first_flush_pending_bytes{}, first_flush_pending_packets{};
  std::size_t recycled_scenes{}, retained_scene_bytes{};
  // Packets larger than the whole allowance that were staged alone instead of failing, and the
  // warning lines written for them (at most one per mission).
  std::size_t oversized_packets{}, oversized_log_lines{};
};
StagingTestState staging_state(VulkanFrameRenderer &renderer);
// True when the lighting the renderer submits equals its configured stock lighting
// (no mission campaign profile applied).
bool display_lighting_is_stock(VulkanFrameRenderer &renderer);

// The geometry, lit-normal and raw-fog terms and the checked total of one packet's byte count.
struct PacketByteBreakdown {
  std::size_t geometry{}, lit_normals{}, raw_fog{}, total{};
};
PacketByteBreakdown packet_byte_breakdown(const mw34::vkscene::Scene &scene);

// Exercise the real retained-packet rejection path without allocating a full
// production allowance. Normal frontend construction always uses the native cap.
std::unique_ptr<VulkanFrameRenderer> make_renderer_with_staging_budget(
    SDL_Window *window, sdlfe::RendererBackend backend, const sdlfe::CoreCriticalQuality &quality,
    const sdlfe::CoreCriticalAssets &assets, std::size_t local_staging_budget);
} // namespace testing

} // namespace cc_mw3_re
