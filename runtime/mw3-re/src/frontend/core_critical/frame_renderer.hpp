#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <vector>

#include "frontend/sdl/sdl_render3d.h"
#include "renderer/original_rigid_capture.hpp"
#include "renderer/preload_budget.hpp"
#include "renderer/renderer_bridge_config.hpp"
#include "renderer/texture_source.hpp"
#include "renderer/texture_staging.hpp"
#include "producer_view_test_hook.hpp"

namespace mw34::vkscene {
struct Scene;
}

namespace cc_mw3_re {

struct QualityStatistics {
  // mip_levels counts generated levels below each uploaded base image.
  std::uint64_t fxaa_passes{}, anisotropic_samplers{}, mip_levels{}, menu_ripple_passes{};
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
  // loaded_pages is how many pages are resident now; page_loads is how many
  // page reads from disk happened, so repeated reads of one page show up.
  std::uint64_t world_normal_decoded_bytes{}, world_normal_peak_decoded_bytes{},
      world_normal_loaded_pages{}, world_normal_page_loads{};
  std::uint64_t binding_rejected_mismatch{}, native_fingerprint_evaluations{};
  // Draw-time deferred receipt checks, independent of whether sun lighting runs.
  std::uint64_t deferred_material_admissions{};
  std::uint64_t native_geometry_cache_entries{}, native_geometry_prune_passes{};
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
// Checks only: the prepared skin cache's decoded-byte budget.
void set_skin_cache_budget(VulkanFrameRenderer &renderer, std::size_t bytes);
// Skin texture slots not yet released (queued stale slots and slots without an owner).
std::size_t pending_skin_retirements(VulkanFrameRenderer &renderer);
// The projection {near, ax, ay, cx, cy, far} of the producer scene's last GPU model draw.
std::array<float, 6> last_model_projection(VulkanFrameRenderer &renderer);

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

struct PreloadTestState {
  bool last_preload_stopped{};
  int32_t failed_texture_handle{-1};
  mw34::vkscene::PreloadStopInfo stop_info{};
  std::size_t preload_allocation_attempts{};
  std::size_t preload_allocation_successes{};
  std::size_t stop_log_lines{};
  std::size_t batch_submissions{};
  std::uint64_t peak_batch_bytes{};
  std::size_t pending_count{};
  std::size_t peak_pending_count{};
  std::size_t pending_texture_receipt_observations{};
  std::size_t premature_texture_receipts{};
  std::uint64_t prepared_staged_bytes{};
  std::uint64_t world_normal_staged_bytes{};
  std::uint64_t native_staged_bytes{};
  std::uint64_t tracked_device_local_bytes{};
  std::size_t live_allocation_count{};
  std::vector<std::string> ordered_prepared_assets;
  std::vector<int32_t> ordered_native_handles;
  std::vector<int32_t> completed_texture_handles;
};

void set_preload_fault_injection(
    VulkanFrameRenderer &renderer,
    const mw34::vkscene::PreloadFaultInjection &fault);
void set_preload_batch_cap(VulkanFrameRenderer &renderer, std::uint64_t bytes);
void set_preload_memory_block_cap(VulkanFrameRenderer &renderer, std::uint64_t bytes);
PreloadTestState preload_test_state(VulkanFrameRenderer &renderer);
bool has_texture_receipt(VulkanFrameRenderer &renderer, int32_t handle,
                         bool sharp = false);
bool is_texture_gpu_resident(VulkanFrameRenderer &renderer, int32_t handle,
                             bool sharp = false);
// Texture memory lines printed after mission preloads so far (#518).
std::size_t texture_memory_log_count(VulkanFrameRenderer &renderer);
// The source the renderer recorded for a texture's GPU copy (#518).
mw34::vkscene::TextureSource texture_source(VulkanFrameRenderer &renderer, int32_t handle,
                                            bool sharp = false);
// The storage format of a texture's GPU copy (#518).
mw34::texture_staging::Pack16 texture_format(VulkanFrameRenderer &renderer, int32_t handle,
                                             bool sharp = false);
bool has_partial_texture_cache_entry(VulkanFrameRenderer &renderer,
                                     int32_t handle, bool sharp = false);
bool is_model_geometry_gpu_uploaded(VulkanFrameRenderer &renderer,
                                    std::uint64_t geometry_key);
bool has_partial_model_buffer_entry(VulkanFrameRenderer &renderer,
                                    std::uint64_t geometry_key);
// #496: "video memory full" lines logged so far, and render() calls so far.
std::size_t video_memory_full_log_count(VulkanFrameRenderer &renderer);
std::uint64_t scene_render_frame(VulkanFrameRenderer &renderer);
void free_unused_model_buffers(VulkanFrameRenderer &renderer, std::uint64_t min_age_frames);
void free_unused_textures(VulkanFrameRenderer &renderer, std::uint64_t min_age_frames);
// True while a texture the renderer freed waits for a frame to bring its pixels.
bool texture_awaiting_pixels(VulkanFrameRenderer &renderer, int32_t handle, bool sharp = false);
std::uint64_t shared_texture_staging_size(VulkanFrameRenderer &renderer);
bool shared_texture_staging_mapped(VulkanFrameRenderer &renderer);
} // namespace testing

} // namespace cc_mw3_re
