#include "frame_renderer.hpp"
#include "crt/msvc_rand.h"
#include "frontend/sdl/cpu_interval.h"
#include "gamez/zclass/cls_zbd.h"
#include "gamez/zclass/class.h"
#include "gamez/zclass/cls_node.h"
#include "gamez/zclass/list.h"
#include "gamez/zclass/visual_distance.h"
#include "gamez/zimage/zimg_texture.h"
#include "gamez/zinput/zinput.h"
#include "gamez/zmath/zmth_matrix.h"
#include "gamez/zmodel/gmod_fog.h"
#include "gamez/zmodel/gmod_fogcalc.h"
#include "gamez/zutil/ztimer.h"
#include "gamez/zutil/zutl_path.h"
#include "gamez/zvideo/zvid_ddd3d.h"
#include "native_staging_budget.hpp"
#include "prepared_draw.hpp"
#include "prepared_draw_cache.hpp"
#include "prepared_models.hpp"
#include "render_worker.hpp"
#include "renderer/campaign_sun_settings.hpp"
#include "renderer/effect_light_observations.hpp"
#include "renderer/flare_alpha.hpp"
#include "renderer/effect_lighting_stage.inc"
#include "renderer/geometry/reference.hpp"
#include "renderer/headlight_original_binding.hpp"
#include "renderer/headlight_spotlight.hpp"
#include "renderer/material_normals.hpp"
#include "renderer/mech_headlights.hpp"
#include "renderer/resource_timing.hpp"
#include "gamez/zmodel/gmod_geometry.h"
#include "gamez/zmodel/gmod_const.h"
#include "renderer/native_surface_identity.hpp"
#include "renderer/native_fixture_sources.hpp"
#include "renderer/fixture_observation_emission.hpp"
#include "platform/prepared_visuals.h"
#include "platform/sha256.hpp"
#include "renderer/surface_detail_bindings.hpp"
#include <filesystem>
#include <functional>
#include <fstream>

namespace mw34::materials {
void set_active_surface_key(const SurfaceKey &key);
void clear_active_surface_key();
bool get_active_surface_key(SurfaceKey *out);
} // namespace mw34::materials

#include "frontend/sdl/sdl_child.h"
#include "platform/wsi_surface.hpp"
#include "platform/wsi_win32_dxgi.hpp"
#include "vk_scene.hpp"
#include <SDL3/SDL_vulkan.h>

#undef DrawState // Win32's DrawState macro conflicts with platform::DrawState.

#include <algorithm>
#include <array>
#include <atomic>
#include <cfenv>
#include <charconv>
#include <cstdarg>
#include <cmath>
#include <chrono>
#include <unordered_set>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <exception>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace cc_mw3_re {
namespace {

namespace vk = mw34::vkscene;
using ::platform::DrawState;
using ::platform::Primitive;
using ::platform::TLVertex;

// Wall durations on the calling CPU thread, including waits inside the measured
// operation. Disabled intervals do not read a clock or change rendering inputs.
using sdlfe::cpu_profile_requested;
using sdlfe::CpuInterval;

class VisualFloatScope {
public:
  VisualFloatScope() {
    if (std::fegetenv(&saved_) != 0)
      throw std::runtime_error(
          "Cannot preserve the native floating-point environment");
  }
  ~VisualFloatScope() { std::fesetenv(&saved_); }

private:
  std::fenv_t saved_;
};


// One process-local, opt-in run. Fixed storage prevents diagnostic tracking or
// formatting from growing with scene size. It owns no native source pointers.
struct FixtureTraceRecord {
  std::array<char, 8192> bytes{};
  std::size_t size{};
  bool valid{true};
  void append(const char* format, ...) {
    if(!valid) return;
    va_list arguments;
    va_start(arguments,format);
    const int count=std::vsnprintf(bytes.data()+size,bytes.size()-size,format,arguments);
    va_end(arguments);
    if(count<0 || std::size_t(count)>=bytes.size()-size) { valid=false; return; }
    size+=std::size_t(count);
  }
  void quoted(const char* data,std::size_t count,std::size_t limit=192) {
    if(!data) { append("null"); return; }
    append("\"");
    for(std::size_t index=0;index<std::min(count,limit);++index) {
      const unsigned char value=static_cast<unsigned char>(data[index]);
      if(value=='\"' || value=='\\') append("\\%c",value);
      else if(value<32 || value>126) append("\\u%04x",unsigned(value));
      else append("%c",value);
    }
    append("\"");
  }
  void text(const char* field,const char* data,std::size_t count,std::size_t limit=192) {
    append(",\"%s\":",field);
    quoted(data,count,limit);
    if(data && count>limit) append(",\"%s_truncated\":true",field);
  }
  void text(const char* field,const std::string& value,std::size_t limit=192) {
    text(field,value.empty() ? nullptr : value.data(),value.size(),limit);
  }
  void hash(const char* field,std::uint64_t value) {
    append(",\"%s\":\"%016llx\"",field,(unsigned long long)value);
  }
  void scalar(float value) {
    if(!std::isfinite(value)) { append("null"); return; }
    char storage[48];
    const auto result=std::to_chars(storage,storage+sizeof storage,value,
        std::chars_format::general,std::numeric_limits<float>::max_digits10);
    if(result.ec!=std::errc{}) { append("null"); return; }
    append("%.*s",int(result.ptr-storage),storage);
  }
  void floats(const char* field,const float* values,std::size_t count,bool available) {
    append(",\"%s\":",field);
    if(!available) { append("null"); return; }
    append("[");
    for(std::size_t index=0;index<count;++index) {
      if(index) append(",");
      scalar(values[index]);
    }
    append("]");
  }
  void key(const char* field,const mw34::materials::SurfaceKey* value) {
    append(",\"%s\":",field);
    if(!value || !value->width || !value->height || !value->hash) { append("null"); return; }
    append("{\"width\":%u,\"height\":%u,\"format\":%u,\"hash\":\"%016llx\"}",
        value->width,value->height,value->format,(unsigned long long)value->hash);
  }
};
std::uint64_t fixture_trace_hash(const void* data,std::size_t bytes,
                               std::uint64_t value=0xcbf29ce484222325ULL) {
  const auto* source=static_cast<const unsigned char*>(data);
  for(std::size_t index=0;index<bytes;++index) value=(value^source[index])*0x100000001b3ULL;
  return value;
}
struct FixtureTraceRun {
  static constexpr std::size_t maximum_records=1024,maximum_observations=4096,maximum_bytes=512*1024,summary_reserve=512;
  const bool enabled=[] {
    const auto* value=std::getenv("MW34_TRACE_FIXTURE_SOURCES");
    return value && std::strcmp(value,"1")==0;
  }();
  std::array<std::uint64_t,maximum_records> seen{};
  std::size_t records{},observations{},bytes{},duplicates{},oversized{};
  bool stopped{},summarized{},native_control{};
  bool open() const { return enabled && !stopped; }
  bool claim() {
    if(!open()) return false;
    if(observations==maximum_observations) { stopped=true; finish("observation_limit"); return false; }
    ++observations;
    return true;
  }
  void finish(const char* reason) {
    if(!enabled || summarized) return;
    summarized=true;
    char storage[summary_reserve];
    const int length=std::snprintf(storage,sizeof storage,
        "[NATIVE_FIXTURE_SOURCE] {\"schema\":\"mw34.fixture-source.v1\",\"type\":\"summary\","
        "\"reason\":\"%s\",\"records\":%zu,\"bytes_before_summary\":%zu,\"duplicates\":%zu,"
        "\"oversized\":%zu,\"observations\":%zu,\"record_limit\":%zu,"
        "\"observation_limit\":%zu,\"byte_limit\":%zu,\"native_control\":%s}\n",
        reason,records,bytes,duplicates,oversized,observations,maximum_records,maximum_observations,maximum_bytes,
        native_control ? "true":"false");
    if(length>0 && std::size_t(length)<sizeof storage && std::size_t(length)<=maximum_bytes-bytes)
      bytes+=std::fwrite(storage,1,std::size_t(length),stderr);
  }
  void submit(FixtureTraceRecord& record) {
    if(!open()) return;
    if(!record.valid) { ++oversized; stopped=true; finish("record_buffer_limit"); return; }
    const auto signature=fixture_trace_hash(record.bytes.data(),record.size);
    if(std::find(seen.begin(),seen.begin()+records,signature)!=seen.begin()+records) {
      ++duplicates;
      if(observations==maximum_observations) { stopped=true; finish("observation_limit"); }
      return;
    }
    const auto length=record.size+1;
    if(records==maximum_records || length>maximum_bytes-summary_reserve-bytes) {
      stopped=true;
      finish(records==maximum_records ? "record_limit" : "byte_limit");
      return;
    }
    // Share stderr's FILE lock with native renderer diagnostics. A separate
    // buffered stdout stream can split a JSON line around their writes even
    // when both OS handles ultimately target the same merged log file.
    record.bytes[record.size++]='\n';
    const auto written=std::fwrite(record.bytes.data(),1,record.size,stderr);
    bytes+=written;
    if(written!=record.size) {
      stopped=true;
      finish("diagnostic_write_error");
      return;
    }
    seen[records++]=signature;
    if(records==maximum_records) { stopped=true; finish("record_limit"); }
    else if(observations==maximum_observations) { stopped=true; finish("observation_limit"); }
  }
  ~FixtureTraceRun() {
    if(!enabled || summarized) return;
    try { VisualFloatScope preserve; finish("process_exit"); } catch(...) {}
  }
};
FixtureTraceRun& fixture_trace_run() {
  static FixtureTraceRun state;
  return state;
}

vk::Renderer::Quality parse_quality(const sdlfe::CoreCriticalQuality &quality) {
  vk::Renderer::Quality result{1, 1, 1, false};
  if (quality.antialiasing == "fxaa")
    result.fxaa = true;
  else if (quality.antialiasing == "ssaa2")
    result.samples_x = 2;
  else if (quality.antialiasing == "ssaa4")
    result.samples_x = result.samples_y = 2;
  else if (quality.antialiasing != "off")
    throw std::runtime_error("--cc-aa supports off, fxaa, ssaa2 or ssaa4");
  if (quality.anisotropy != "1" && quality.anisotropy != "2" &&
      quality.anisotropy != "4" && quality.anisotropy != "8" &&
      quality.anisotropy != "16")
    throw std::runtime_error("--cc-af supports 1, 2, 4, 8 or 16");
  result.anisotropy = unsigned(std::stoi(quality.anisotropy));
  return result;
}

mw34::sun::Settings parse_lighting(const sdlfe::CoreCriticalAssets &options) {
  mw34::sun::Settings result;
  if (options.lighting != "off" && options.lighting != "flat" &&
      options.lighting != "normal")
    throw std::runtime_error("--cc-lighting supports off, flat or normal");
  auto number = [](const std::string &text, float low, float high) {
    char *end = nullptr;
    const float value = std::strtof(text.c_str(), &end);
    if (end == text.c_str() || *end || !std::isfinite(value) || value < low ||
        value > high)
      throw std::runtime_error(
          "Invalid --cc-sun angle (azimuth -360..360, elevation 1..89)");
    return value;
  };
  result.azimuth = number(options.sun_azimuth, -360, 360);
  result.elevation = number(options.sun_elevation, 1, 89);
  result.enabled = options.lighting != "off" || options.geometry != "legacy";
  const auto diagnostic_config =
      cc_mw3_re::RendererBridgeConfig::from_diagnostic_env(
          false, !options.sun_shadows_explicit);
  result.shadows = options.sun_shadows_explicit
                       ? options.sun_shadows
                       : diagnostic_config.sun_shadows;
  if (options.lighting == "off")
    result.shadows = false;
  if (options.lighting == "off" && options.geometry != "legacy") {
    result.strength = 0;
    result.ambient = 1;
    result.ambient_color = {1, 1, 1};
  }
  result.normals = options.lighting == "normal";
  result.normal_strength = result.ground_normal_strength =
      result.normals ? 1.f : 0.f;
  // Native sky/weather/shadow production is not part of prepared-model
  // lighting.
  result.weather_enabled = false;
  return result;
}

bool parse_modern_flare_style(const sdlfe::CoreCriticalAssets &assets) {
  if (assets.flare_style != "modern" && assets.flare_style != "original")
    throw std::runtime_error("--cc-flare-style supports modern or original");
  return assets.flare_style == "modern";
}

vk::Renderer::WindowSurface
sdl_surface(SDL_Window *window,
            const std::shared_ptr<cc_mw3_re::platform::SdlWindowStateTracker>
                &tracker) {
  vk::Renderer::WindowSurface source;
  source.extensions = cc_mw3_re::platform::get_instance_extensions();
  source.create = [window](VkInstance instance) {
    return cc_mw3_re::platform::create_surface(window, instance);
  };
  source.destroy = [](VkInstance instance, VkSurfaceKHR surface) {
    cc_mw3_re::platform::destroy_surface(instance, surface);
  };
  source.is_visible = [tracker](cc_mw3_re::platform::NativeWindowHandle w) {
    if (!w)
      return false;
    if (tracker) {
      if (tracker->is_owner_thread()) {
        tracker->sample_owner();
        return tracker->current_state().visible;
      }
      return tracker->worker_visible();
    }
    return true;
  };
  source.get_drawable_size =
      [tracker](cc_mw3_re::platform::NativeWindowHandle w, long *width,
                long *height) {
        if (!w) {
          if (width)
            *width = 0;
          if (height)
            *height = 0;
          return;
        }
        if (tracker) {
          if (tracker->is_owner_thread()) {
            tracker->sample_owner();
            const auto &state = tracker->current_state();
            if (width)
              *width = state.drawable_width;
            if (height)
              *height = state.drawable_height;
          } else {
            const auto state = tracker->worker_state();
            if (width)
              *width = state.drawable_width;
            if (height)
              *height = state.drawable_height;
          }
          return;
        }
        if (width)
          *width = 0;
        if (height)
          *height = 0;
      };
  return source;
}

constexpr unsigned no_binding = std::numeric_limits<unsigned>::max();

struct Texture {
  unsigned width{}, height{};
  std::uint64_t version{};
  unsigned scene_index = no_binding;
  unsigned sharp_index = no_binding;
  bool held_copy{};
  // Rebuild synthetic alpha from each original RGBA upload on named reload.
  bool generated_rgba{};
  const ::platform::prepared::Image *replacement{};
  unsigned source_width{}, source_height{};
  std::vector<std::uint32_t> pixels;
  std::string name;
  mw34::materials::SurfaceKey surface_key{};
  std::optional<mw34::materials::SurfaceKey> fixture_visual_key;
  std::uint64_t group_load_epoch{0};
};

struct LoggedFlareTexture {
  std::string name;
  int32_t handle = -1;
};

std::vector<uint32_t> image_pixels(const ::platform::prepared::Image &image,
                                   const uint8_t *source = nullptr,
                                   unsigned source_width = 0,
                                   unsigned source_height = 0) {
  std::vector<uint32_t> pixels(image.pixels.size());
  for (unsigned y = 0; y < image.height; ++y)
    for (unsigned x = 0; x < image.width; ++x) {
      const auto value = image.pixels[std::size_t(y) * image.width + x];
      unsigned alpha = 255;
      if (source) {
        const auto sx = std::min(source_width - 1,
                                 unsigned((uint64_t(x) * 2 + 1) * source_width /
                                          (uint64_t(image.width) * 2)));
        const auto sy = std::min(
            source_height - 1, unsigned((uint64_t(y) * 2 + 1) * source_height /
                                        (uint64_t(image.height) * 2)));
        alpha = source[(std::size_t(sy) * source_width + sx) * 4 + 3];
      }
      pixels[std::size_t(y) * image.width + x] =
          alpha == 0 ? 0
                     : ((value >> 11) * 255 / 31) |
                           (((value >> 5) & 63) * 255 / 63) << 8 |
                           ((value & 31) * 255 / 31) << 16 | alpha << 24;
    }
  return pixels;
}

cc::geometry::Mode parse_geometry(const std::string &mode) {
  if (mode == "legacy")
    return cc::geometry::Mode::legacy;
  if (mode == "partial")
    return cc::geometry::Mode::partial;
  if (mode == "gpu")
    return cc::geometry::Mode::gpu;
  if (mode == "cpu-reference")
    return cc::geometry::Mode::cpu_reference;
  throw std::runtime_error(
      "--cc-geometry supports legacy, partial, gpu or cpu-reference");
}

sdlfe::CoreCriticalAssets
sanitize_prepared_assets(sdlfe::CoreCriticalAssets assets) {
  if (assets.models.empty()) {
    assets.lighting = "off";
    assets.normals.clear();
  }
  return assets;
}

class FrameRenderer;
} // namespace

struct RigidCaptureSeal {
  private:
    friend FrameRenderer;
    static std::shared_ptr<const CapturedNativeRigid> seal(
        std::shared_ptr<const cc::geometry::Resource> resource,
        std::vector<CapturedNativeRigidRange> ranges,
        std::weak_ptr<const int> renderer_owner,
        std::uint64_t world_source_epoch,
        std::uint64_t group_load_epoch) {
      return std::shared_ptr<const CapturedNativeRigid>(new CapturedNativeRigid(
          std::move(resource), std::move(ranges), std::move(renderer_owner),
          world_source_epoch, group_load_epoch));
    }
};

namespace {

class FrameRenderer final : public VulkanFrameRenderer {
public:
  explicit FrameRenderer(SDL_Window *window, sdlfe::RendererBackend backend,
                         const sdlfe::CoreCriticalQuality &quality,
                         const sdlfe::CoreCriticalAssets &assets,
                         std::size_t local_staging_budget = staging::native_budget_bytes)
      : window_(window),
        window_state_tracker_(
            backend == sdlfe::RendererBackend::core_critical_wsi
                ? std::make_shared<cc_mw3_re::platform::SdlWindowStateTracker>(window)
                : nullptr),
        native_window_(backend == sdlfe::RendererBackend::core_critical_wsi
                           ? cc_mw3_re::platform::get_window_native_handle(window)
                           : static_cast<cc_mw3_re::platform::NativeWindowHandle>(
                                 cc_mw3_re::platform::get_window_hwnd(window))),
        hwnd_(cc_mw3_re::platform::get_window_hwnd(window)),
        native_wsi_(backend == sdlfe::RendererBackend::core_critical_wsi),
        quality_(parse_quality(quality)), lighting_(parse_lighting(assets)),
        modern_flare_style_(parse_modern_flare_style(assets)),
        base_lighting_(lighting_), campaign_enabled_(assets.lighting != "off"),
        sun_explicit_(assets.sun_explicit),
        environment_(assets.environment),
        bridge_config_(configure_bridge(backend, quality, assets)),
        prepared_(sanitize_prepared_assets(assets), assets.materials),
        geometry_mode_(parse_geometry(assets.geometry)),
        geometry_debug_(assets.geometry_debug_normals),
        prepared_cache_enabled_(bridge_config_.prepared_cache),
        local_staging_budget_(local_staging_budget) {
    if (!local_staging_budget_ || local_staging_budget_ > staging::native_budget_bytes)
      throw std::invalid_argument("Invalid local light staging budget");
    if (geometry_debug_ && geometry_mode_ == cc::geometry::Mode::legacy)
      throw std::runtime_error(
          "Geometry normal debug requires an explicit geometry mode");
    if (!native_wsi_ && !hwnd_) {
      throw std::runtime_error(
          "Direct3D presentation requires a Win32 window handle");
    }
    if (backend == sdlfe::RendererBackend::sdl)
      throw std::runtime_error(
          "The Core Critical factory requires a Vulkan backend");
    // Admit catalog paths and headers before native mission callbacks start.
    // World pixel payloads remain lazy; failures here reach the window's normal
    // initialization error boundary instead of unwinding legacy game loaders.
    if (lighting_.normals || bridge_config_.water_detail ||
        bridge_config_.cloud_detail)
      surface_normals_load();
    local_lights_load();
    initialize_renderer();
    if (assets.render_thread) {
      worker_ = std::make_unique<RenderWorker>(8, staging::native_budget_bytes, [] {
        // Process only synchronous window messages, without consuming
        // input or reentering the game. DXGI may send one while waiting.
        cc_mw3_re::platform::pump_presentation_messages();
      });
      std::fprintf(stderr,
                   "Core Critical render worker: enabled (8 jobs, 1024 MiB)\n");
    }
    std::vector<zcls::ZbdSourceRequest> requests;
    const auto groups = ::platform::prepared::collect_material_target_sources(
        environment_.get(),
        bridge_config_.parallax_materials && lighting_.normals);
    requests.reserve(groups.size());
    for (const auto &group : groups) {
      zcls::ZbdSourceRequest request;
      request.member = group.member;
      request.sha256 = group.sha256;
      request.bytes = group.bytes;
      request.model_slots.insert(group.model_slots.begin(),
                                 group.model_slots.end());
      requests.push_back(std::move(request));
    }
    observation_session_ = zcls::observe_zbd_sources(std::move(requests));
  }

  bool ok() const override { return true; }
  void attach_editor(sdlfe::EditorUiSource* source) override {
    require_editor_producer();
    if (source == editor_source_) return;
    detach_editor();
    editor_source_ = source;
  }
  void detach_editor() override {
    require_editor_producer();
    if (!editor_source_ && !editor_present_active_) return;

    // A failed worker makes drain() rethrow its stored exception. Still retire
    // the editor while its borrowed CPU owner and Vulkan context are alive.
    std::exception_ptr failure;
    try {
      drain(); // Completes retained light packets, then joins all renderer jobs.
    } catch (...) {
      failure = std::current_exception();
    }
    try {
      if (renderer_)
        renderer_->detach_editor();
    } catch (...) {
      if (!failure)
        failure = std::current_exception();
    }
    editor_present_active_ = false;
    editor_source_ = nullptr;
    if (failure) {
      try {
        std::rethrow_exception(failure);
      } catch (const std::exception &error) {
        std::fprintf(stderr, "Core editor best-effort detach: %s\n", error.what());
      } catch (...) {
        std::fprintf(stderr, "Core editor best-effort detach: non-standard exception\n");
      }
      std::fflush(stderr);
    }
  }
  std::uint64_t presentation_count() const override {
    if (worker_)
      worker_->drain();
    return presented_frames_.load();
  }
  void drain() override {
    if (!producer_failed_) {
      flush();
      complete_local_light_packets();
    }
    if (worker_)
      worker_->drain();
  }
  bool observe_producer_views(testing::ProducerViewObserver* observer) override {
    drain();
    producer_observer_ = observer;
    renderer_->producer_view_observer = observer;
    return true;
  }
  ::platform::ProducerViewRestoreToken exchange_producer_view(
      const ::platform::ProducerView& view) override {
    require_producer_live();
    validate_producer_view(view);
    testing::ProducerViewObservation observation{};
    observation.stage = testing::ProducerViewStage::exchange;
    observation.view = view;
    if (producer_observer_) producer_observer_->producer(observation);
    ::platform::ProducerViewRestoreToken token{};
    token.previous = producer_view_;
    token.receiver_cookie = reinterpret_cast<std::uintptr_t>(this);
    token.reset_generation = producer_reset_generation_;
    token.active = true;
    producer_view_ = view;
    return token;
  }
  void restore_producer_view(const ::platform::ProducerViewRestoreToken& token) noexcept override {
    if (!token.active || token.receiver_cookie != reinterpret_cast<std::uintptr_t>(this) ||
        token.reset_generation != producer_reset_generation_ || producer_failed_)
      return;
    producer_view_ = token.previous;
    if (producer_observer_) {
      testing::ProducerViewObservation observation{};
      observation.stage = testing::ProducerViewStage::restore;
      observation.view = producer_view_;
      producer_observer_->backend(observation);
    }
  }
  void abandon_producer_work() noexcept override {
    clear_producer_work(true);
    zvid::invalidate_producer_transport(this, true);
  }
  void reset_producer_work() noexcept override {
    clear_producer_work(false);
    zvid::invalidate_producer_transport(this, false);
  }
  SceneBindingStatistics scene_binding_statistics() override {
    if (worker_)
      worker_->drain();
    std::lock_guard<std::mutex> lock(recycle_mutex_);
    return {true, scene_.textures.size(), scene_.order.size(),
            scene_.draws.size(), recycled_scenes_.size()};
  }
  QualityStatistics quality_statistics() const override {
    if (worker_)
      worker_->drain();
    return {retired_quality_.fxaa_passes + renderer_->fxaa_passes,
            retired_quality_.anisotropic_samplers + renderer_->af_samplers,
            retired_quality_.mip_levels + renderer_->mip_levels_uploaded};
  }
  AssetStatistics asset_statistics() const override {
    if (worker_)
      worker_->drain();
    return {prepared_batches_,
            retired_model_draws_ + renderer_->model_draws,
            cpu_clipped_triangles_,
            named_textures_,
            retired_model_uploads_ + renderer_->model_uploads,
            retired_lit_draws_ + renderer_->sun_world_draws +
                renderer_->sun_model_draws + renderer_->sun_tl_draws,
            retired_normal_draws_ + renderer_->normal_draws,
            retired_geometry_buffers_ + renderer_->retired_model_buffers,
            gpu_prepared_vertices_,
            early_prepared_models_,
            prepared_cpu_fallback_batches_,
            surface_normals_.cache.world_bytes,
            surface_normals_.peak_decoded_bytes,
            std::uint64_t(
                std::count_if(surface_normals_.cache.pages.begin(),
                              surface_normals_.cache.pages.end(),
                              [](const auto &page) { return page.loaded; })),
            binding_rejected_mismatch_,
            native_fingerprint_evaluations_,
            deferred_material_admissions_,
            std::uint64_t(native_geometry_.size()),
            native_geometry_prune_passes_};
  }
  // Capacity the current producer Scene retains from earlier packets (adopted from the pool).
  std::size_t retained_scene_capacity_bytes() const {
    const auto terms = packet_byte_terms(scene_);
    return terms.vertices + terms.color_depth + terms.draws + terms.order + terms.textures +
           terms.clears;
  }
  static testing::PacketByteBreakdown packet_byte_breakdown_for_test(const vk::Scene &scene) {
    const auto terms = packet_byte_terms(scene);
    return {terms.geometry, terms.lit_normals, terms.raw_fog, checked_packet_total(terms)};
  }
  testing::StagingTestState staging_state_for_test() {
    return {staging_peak_bytes_,        staging_early_completions_, staging_early_log_lines_,
            staging_first_flush_bytes_, staging_first_flush_packets_,
            recycled_scene_count_for_test(), retained_scene_capacity_bytes()};
  }
  testing::NamedTextureTestState named_texture_state_for_test(
      int32_t handle) const {
    const auto &entry = textures_.at(std::size_t(handle));
    return {entry.width, entry.height, entry.source_width, entry.source_height,
            entry.generated_rgba, entry.pixels};
  }
#include "geometry_frame_adapter.inc"
#include "geometry_reference_adapter.inc"
#include "prepared_gpu_adapter.inc"
#include "renderer/surface_normals_stage.inc"
private:
#include "renderer/local_light_runtime.inc"
public:
  int32_t surface_normal_texture(int normal_index) {
    const auto found = surface_normal_textures_.find(normal_index);
    if (found != surface_normal_textures_.end()) {
      return found->second;
    }
    const auto &norm_img = surface_normal_image(normal_index);
    mw34::timing::ScopedDuration upload_timer(
        producer_resource_timing_.page_upload_target());
    const auto handle = create_texture(
        int(norm_img.width), int(norm_img.height),
        reinterpret_cast<const uint8_t *>(norm_img.pixels32.data()), 1);
    surface_normal_textures_.emplace(normal_index, handle);
    return handle;
  }

  std::shared_ptr<const ::platform::DeferredMaterialBinding>
  capture_deferred_material_binding(int32_t texture) override {
    VisualFloatScope preserve;
    if (texture < 0 || std::size_t(texture) >= textures_.size())
      return {};
    const bool normal_admission = lighting_.normals &&
        (!bridge_config_.native_material_sidecar.empty() ||
         (bridge_config_.parallax_materials && environment_ &&
          !environment_->material_targets.empty()));
    const auto fixture = capture_fixture_polygon(texture);
    if (!normal_admission && !fixture)
      return {};
    if (normal_admission)
      surface_normals_load(); // Reset can make a deferred draw first.
    const auto &key = textures_[texture].surface_key;
    auto receipt = std::make_shared<NativeDeferredBinding>();
    receipt->owner = material_binding_owner_;
    receipt->key = textures_[texture].surface_key;
    receipt->epoch = group_load_epoch_;
    receipt->version = textures_[texture].version;
    receipt->texture = texture;
    receipt->fixture = fixture;
    if (normal_admission) {
      receipt->surface_parameters = native_surface_parameters(key, texture);
      receipt->height_binding = native_height_binding(key, texture);
      receipt->normal_index = surface_normal_index(receipt->key, true, texture);
    }
    return receipt;
  }
  void begin_deferred_material_draw(
      std::shared_ptr<const ::platform::DeferredMaterialBinding> receipt)
      override {
    deferred_material_binding_ = std::move(receipt);
  }
  void end_deferred_material_draw() noexcept override {
    deferred_material_binding_.reset();
  }
  void invalidate_material_geometry() noexcept override {
    native_context_.fingerprint_computed = false;
    native_context_.fingerprint.reset();
  }
  bool wants_material_context() const override {
    return fixture_producer_enabled() || fixture_trace_run().open() ||
           (lighting_.normals &&
            (!bridge_config_.native_material_sidecar.empty() ||
             (bridge_config_.parallax_materials && environment_ &&
              !environment_->material_targets.empty()) ||
             bridge_config_.trace_native_bindings));
  }
  bool wants_model_context() const override {
    return !prepared_.empty() || wants_material_context();
  }
  void
  begin_material_draw(const ::platform::MaterialDrawContext &context) override {
    native_context_.material = context;
    native_context_.material_active = true;
    if(fixture_trace_run().open()) fixture_trace_native("native-material",context,-1,nullptr);
  }
  void end_material_draw() noexcept override {
    native_context_.material = {};
    native_context_.material_active = false;
  }
  bool replaces_model_geometry() const override {
    return suppress_model_draws_;
  }
  void end_model_draw() noexcept override {
    suppress_model_draws_ = false;
    native_context_ = {};
    if(fixture_trace_run().open()) fixture_trace_pose_ = {};
  }
  void begin_model_draw(const ::platform::ModelDrawContext &context) override {
    // Visual retargeting/fog must not leak exception flags or rounding state
    // into the native polygon producer that resumes after this callback.
    VisualFloatScope float_scope;
    suppress_model_draws_ = false;
    native_context_ = {};
    if (wants_material_context()) {
      native_context_.node = static_cast<const zcls::Node *>(context.node);
      native_context_.model =
          native_context_.node ? native_context_.node->model : nullptr;
      native_context_.epoch = group_load_epoch_;
      native_context_.height_eligible = native_ground_eligible(context);
    }
    fixture_model_scope(context);
    if(fixture_trace_run().open()) fixture_trace_model(context);
    ensure_extent();
    const auto draws = prepared_.draw(context);
    if (!draws.replace)
      return;
    if (scene_.hud && !scene_.draws.empty()) {
      flush();
      ensure_extent();
    }
    scene_.hud = false;
    for (const auto &draw : draws.batches)
      emit_prepared(draw, context);
    suppress_model_draws_ = true;
  }
  const char *driver_name() const override {
    return native_wsi_ ? "Core Critical Vulkan/SDL WSI"
                       : "Core Critical Vulkan/DXGI";
  }
  void set_shape(const sdlfe::FrameShape *shape) override { shape_ = shape; }
  // Typed mission-change callback from the native missions object: owns the
  // canonical mission ID and the resolved campaign lighting/policy. Unknown or
  // failed identities clear any prior state (no stale profile).
  void mission_changed(const ::platform::MissionIdentity &identity) override {
    VisualFloatScope fp_guard;
    // Drop unsubmitted CPU work before the old drain path can publish it. The
    // metadata notification restores identity after invalidation; a detached
    // renderer must never touch another receiver's queue.
    clear_producer_work(false);
    if (zvid::render3d() == this)
      zvid::producer_mission_changed(identity);
    // Drain packets queued for the previous mission before switching state.
    drain();
    // The workers are idle now: release the capacity that recycled Scenes (and the one drain may
    // have adopted into scene_) kept from the previous mission, so this mission's packets are not
    // charged for it.
    // clear_producer_work(false) above already dropped the unsubmitted producer Scene and the
    // pending packets (and ended any open scene state), so this only discards what drain() may
    // have adopted from the pool: a mission change never discards unflushed draws here.
    scene_ = {};
    invalidate_scene_bindings();
    release_recycled_scenes();
    local_lights_clear();
    staging_early_logged_ = false;
    staging_first_flush_pending_ = true;
    const auto id = mw34::campaign::canonical_mission_id(identity.world_index,
                                                         identity.number);
    mw34::campaign::ResolvedMissionLighting resolved{};
    if (!id.empty())
      resolved = mw34::campaign::resolve_mission_lighting(id);
    lighting_ = mw34::campaign::mission_sun_settings(
        base_lighting_, resolved, campaign_enabled_, sun_explicit_,
        environment_.get(), id);
    display_hdr_ = window_hdr_enabled();
    if (renderer_)
      renderer_->update_lighting_settings(display_lighting());
    const bool identity_changed =
        identity.world_index != current_mission_identity_.world_index ||
        identity.number != current_mission_identity_.number;
    current_mission_identity_ = identity;
    if (id != current_mission_id_ || identity_changed) {
      current_mission_id_ = id;
      current_mission_lighting_ = resolved;
      if (lighting_.enabled && identity.world_index >= 0 &&
          identity.number > 0 && !resolved.has_profile)
        std::fprintf(stderr,
                     "[MISSION_CHANGED] warning=unknown-mission world_index=%d "
                     "number=%d; configured stock lighting restored\n",
                     identity.world_index, identity.number);
      else if (lighting_.enabled)
        std::fprintf(
            stderr,
            "[MISSION_CHANGED] id=%s world_index=%d number=%d has_profile=%d\n",
            current_mission_id_.c_str(), static_cast<int>(identity.world_index),
            static_cast<int>(identity.number), resolved.has_profile ? 1 : 0);
    } else {
      current_mission_lighting_ = resolved;
    }
    preload_mission_normal_textures();
    first_world_preload_pending_ = true;
  }
  void reset_scene_resources() override {
    // Clear pending preload before the empty mission callback so scene teardown
    // does not warm old mission textures right before resetting them.
    surface_normals_.preload_pending = false;
    prepared_preload_pending_ = false;
    // Reset the owned mission identity/result via the callback with the empty
    // identity before the scene resources are reset.
    mission_changed(::platform::MissionIdentity{});
    first_world_preload_pending_ = false;
    prepared_preload_pending_ = true;
    reset_pending_ = true;
    ++group_load_epoch_;
    for (const auto &[index, handle] : surface_normal_textures_)
      textures_.at(handle) = {};
    surface_normal_textures_.clear();
    surface_normals_ = SurfaceNormalState{};
    deferred_material_binding_.reset();
    native_context_ = {};
    logged_first_normal_trace_ = false;
    if (bridge_config_.trace_native_bindings)
      std::fprintf(stderr,
                   "[SURFACE_EPOCH_RESET] epoch=%llu decoded_bytes=%llu "
                   "normal_handles=%zu\n",
                   (unsigned long long)group_load_epoch_,
                   (unsigned long long)surface_normals_.cache.world_bytes,
                   surface_normal_textures_.size());
  }

  ~FrameRenderer() override {
    try {
      detach_editor();
    } catch (...) {
      std::fprintf(stderr, "Core editor detach failed during renderer shutdown\n");
      std::fflush(stderr);
      std::_Exit(3);
    }
    try {
      drain();
    } catch (const std::exception &error) {
      std::fprintf(stderr, "Core Critical render worker shutdown: %s\n",
                   error.what());
    }
    local_lights_report();
    if (worker_) {
      worker_->stop();
      const auto statistics = worker_->statistics();
      std::fprintf(
          stderr,
          "Render worker: %zu submitted, %zu completed, %zu peak jobs, "
          "%zu peak bytes, %zu producer waits\n",
          statistics.submitted, statistics.completed, statistics.peak_jobs,
          statistics.peak_bytes, statistics.waits);
      std::fprintf(stderr,
                   "Local light staging: peak %zu bytes of %zu, %zu early completions\n",
                   staging_peak_bytes_, local_staging_budget_, staging_early_completions_);
      worker_.reset(); // All later summary reads and destruction belong to this
                       // thread.
    }
    if (cpu_profile_) {
      const double milliseconds = 1000.0 / SDL_GetPerformanceFrequency();
      std::fprintf(stderr,
                   "CPU renderer profile (includes warmup): %llu presents, "
                   "%llu GPU sharp draws, "
                   "%llu render calls, render %.4f ms, "
                   "transport %.4f ms\n",
                   static_cast<unsigned long long>(presented_frames_.load()),
                   static_cast<unsigned long long>(gpu_sharp_draws_),
                   static_cast<unsigned long long>(render_calls_),
                   render_ticks_ * milliseconds,
                   transport_ticks_ * milliseconds);
      const auto &models = prepared_.cpu_statistics();
      std::fprintf(stderr,
                   "CPU prepared profile (includes warmup, nested intervals): "
                   "%llu calls, "
                   "selection %.4f ms, retarget %.4f ms, deform %.4f ms, "
                   "emission %.4f ms, TL append %.4f ms\n",
                   static_cast<unsigned long long>(models.calls),
                   models.selection_ticks * milliseconds,
                   models.retarget_ticks * milliseconds,
                   models.deform_ticks * milliseconds,
                   prepared_emit_ticks_ * milliseconds,
                   append_ticks_ * milliseconds);
      if (worker_render_ticks_ || worker_present_ticks_)
        std::fprintf(stderr,
                     "CPU worker profile: render %.4f ms, present %.4f ms\n",
                     worker_render_ticks_ * milliseconds,
                     worker_present_ticks_ * milliseconds);
      std::fprintf(stderr,
                   "CPU prepared vertices: %llu vertices, stage %.4f ms, "
                   "assembly %.4f ms\n",
                   static_cast<unsigned long long>(prepared_cpu_.vertices),
                   prepared_cpu_.stage_ticks * milliseconds,
                   prepared_cpu_.assembly_ticks * milliseconds);
    }
    if (geometry_mode_ != cc::geometry::Mode::legacy)
      std::fprintf(
          stderr,
          "Prepared geometry: %llu GPU vertices, %llu reference CPU vertices, "
          "%llu early models, %llu CPU fallback batches\n",
          (unsigned long long)gpu_prepared_vertices_,
          (unsigned long long)prepared_reference_vertices_,
          (unsigned long long)early_prepared_models_,
          (unsigned long long)prepared_cpu_fallback_batches_);
    if (geometry_mode_ != cc::geometry::Mode::legacy)
      std::fprintf(
          stderr,
          "Geometry handoff: %llu submitted models, %llu CPU vertex "
          "preparations skipped, %llu CPU polygon preparations skipped, %llu "
          "unsupported models, %llu CPU 3D draw calls observed\n",
          (unsigned long long)geometry_statistics_.submitted_models,
          (unsigned long long)geometry_statistics_.skipped_vertices,
          (unsigned long long)geometry_statistics_.skipped_polygons,
          (unsigned long long)geometry_statistics_.unsupported_models,
          (unsigned long long)geometry_statistics_.cpu_draw_calls);
    const auto quality = quality_statistics();
    std::fprintf(
        stderr,
        "%s: %llu draws, %llu resident presents, %llu FXAA passes, %llu AF "
        "samplers, %llu mip "
        "levels\n",
        driver_name(),
        static_cast<unsigned long long>(retired_draws_ + renderer_->draws),
        static_cast<unsigned long long>(retired_presents_ +
                                        renderer_->resident_presents),
        static_cast<unsigned long long>(quality.fxaa_passes),
        static_cast<unsigned long long>(quality.anisotropic_samplers),
        static_cast<unsigned long long>(quality.mip_levels));
    const auto assets = asset_statistics();
    if (lighting_.normals)
      std::fprintf(
          stderr,
          "World normal pages: %llu decoded bytes, %llu peak decoded bytes, "
          "%llu loaded pages (536870912-byte limit)\n",
          (unsigned long long)assets.world_normal_decoded_bytes,
          (unsigned long long)assets.world_normal_peak_decoded_bytes,
          (unsigned long long)assets.world_normal_loaded_pages);
    const auto &cache = prepared_draw_cache_.statistics();
    if (cache.hits || cache.misses || cache.bypasses)
      std::fprintf(stderr,
                   "Prepared staging cache: %llu hits, %llu misses, %llu "
                   "bypasses, %zu bytes\n",
                   (unsigned long long)cache.hits,
                   (unsigned long long)cache.misses,
                   (unsigned long long)cache.bypasses, cache.bytes);
    if (assets.prepared_batches || assets.named_textures)
      std::fprintf(
          stderr,
          "Prepared visuals: %llu batches, %llu GPU model draws, %llu "
          "CPU-clipped "
          "triangles, %llu named texture uploads\n",
          static_cast<unsigned long long>(assets.prepared_batches),
          static_cast<unsigned long long>(assets.gpu_model_draws),
          static_cast<unsigned long long>(assets.cpu_clipped_triangles),
          static_cast<unsigned long long>(assets.named_textures));
    if (lighting_.enabled)
      std::fprintf(
          stderr,
          "Prepared materials: %llu per-pixel draws, %llu normal-map draws\n",
          static_cast<unsigned long long>(assets.lit_draws),
          static_cast<unsigned long long>(assets.normal_draws));
    cc_mw3_re::platform::unregister_window_handle(native_window_);
  }

  void capture_next(const char *path) override { capture_path_ = path; }
  void viewport(int *x, int *y, int *width, int *height) const override {
    *x = viewport_[0];
    *y = viewport_[1];
    *width = viewport_[2];
    *height = viewport_[3];
  }
  void set_viewport(int x, int y, int width, int height) override {
    if (width < 1 || height < 1) {
      throw std::runtime_error("Invalid mw3-re viewport");
    }
    viewport_ = {x, y, width, height};
  }

  void prepare_canvas_textures(const std::vector<int32_t> &handles) override {
      std::vector<vk::TextureRef> references;
      for (const auto handle : handles) {
          const auto &entry = textures_.at(handle);
          references.push_back({std::uint64_t(handle) * 2 + 2,
                                entry.version,
                                entry.width,
                                entry.height,
                                vk::TexFormat::rgba8888,
                                {},
                                {}});
      }
      const auto prepare = [this, &references] {
          // Return the failure as data: letting it escape a worker job permanently
          // stops that worker, including the CPU compositor's subsequent uploads.
          try {
              renderer_->prepare_canvas_textures(references);
              return std::exception_ptr{};
          } catch (...) {
              return std::current_exception();
          }
      };
      const auto failure = worker_ ? worker_->call(prepare) : prepare();
      if (failure)
          std::rethrow_exception(failure);
  }

  int32_t create_texture(int width, int height, const uint8_t *rgba,
                         uint8_t) override {
    if (width <= 0 || height <= 0 || unsigned(width) > texture_limit_ ||
        unsigned(height) > texture_limit_) {
      throw std::runtime_error("Invalid mw3-re texture size");
    }
    const auto free =
        std::find_if(textures_.begin(), textures_.end(),
                     [](const Texture &entry) { return entry.pixels.empty(); });
    const auto handle = int32_t(free - textures_.begin());
    if (free == textures_.end()) {
      textures_.emplace_back();
    }
    auto &entry = textures_[handle];
    entry.width = unsigned(width);
    entry.height = unsigned(height);
    mw34::materials::SurfaceKey active_key{};
    if (mw34::materials::get_active_surface_key(&active_key)) {
      entry.surface_key = active_key;
    }
    entry.group_load_epoch = group_load_epoch_;
    update_texture(handle, width, height, rgba);
    return handle;
  }

  void update_texture(int32_t handle, int width, int height,
                      const uint8_t *rgba) override {
    auto &entry = textures_.at(handle);
    // Refresh from the original texel producer on every upload. An arbitrary
    // RGBA update has no authenticated 16-bit source identity and must not keep
    // a normal binding merely because it reuses the same renderer handle.
    mw34::materials::SurfaceKey source_key{};
    mw34::materials::get_active_surface_key(&source_key);
    std::vector<uint32_t> replacement;
    std::vector<std::uint8_t> generated;
    if (entry.replacement) {
      if (!rgba || unsigned(width) != entry.source_width ||
          unsigned(height) != entry.source_height)
        throw std::runtime_error(
            "Named texture reload changed its source dimensions");
      replacement = image_pixels(*entry.replacement, rgba, entry.source_width,
                                 entry.source_height);
      rgba = reinterpret_cast<const uint8_t *>(replacement.data());
      width = int(entry.width);
      height = int(entry.height);
      ++named_textures_;
    } else if (entry.generated_rgba) {
      if (!rgba || unsigned(width) != entry.source_width ||
          unsigned(height) != entry.source_height)
        throw std::runtime_error(
            "Generated flare reload changed its source dimensions");
      generated = mw34::flare::generate_rgba(entry.name, entry.width,
                                             entry.height, rgba);
      rgba = generated.data();
    }
    if (!rgba || unsigned(width) != entry.width ||
        unsigned(height) != entry.height) {
      throw std::runtime_error("Invalid mw3-re texture upload");
    }
    if (entry.scene_index != no_binding || entry.sharp_index != no_binding) {
      flush();
    }
    entry.pixels.resize(std::size_t(width) * height);
    std::memcpy(entry.pixels.data(), rgba,
                entry.pixels.size() * sizeof(std::uint32_t));
    entry.surface_key = source_key;
    entry.group_load_epoch = group_load_epoch_;
    entry.version = ++texture_version_;
    entry.fixture_visual_key.reset();
    // Preload any matching world normal page once the texture's source identity
    // is published. No reference to entry is used after this point in case
    // later texture allocations reallocate textures_.
    if (source_key.hash != 0)
      prepared_preload_pending_ = true;
    if (lighting_.normals && source_key.hash != 0) {
      VisualFloatScope float_scope;
      preload_surface_normal(source_key);
    }
  }

  int32_t create_named_texture(const char *name, int width, int height,
                               const uint8_t *rgba, uint8_t type) override {
    mw34::materials::SurfaceKey active_key{};
    mw34::materials::get_active_surface_key(&active_key);
    const auto *replacement = prepared_.named_texture(name);
    const bool generate_flare = modern_flare_style_ && name &&
                                mw34::flare::is_texture(name);
    if (generate_flare) {
      if (!rgba || width <= 0 || height <= 0 ||
          unsigned(width) > texture_limit_ || unsigned(height) > texture_limit_)
        throw std::runtime_error("Invalid mw3-re texture size or flare input");
      const auto pixels = mw34::flare::generate_rgba(
          name, unsigned(width), unsigned(height), rgba);
      const auto handle = create_texture(width, height, pixels.data(), type);
      auto &entry = textures_[handle];
      entry.generated_rgba = true;
      entry.name = name;
      entry.source_width = unsigned(width);
      entry.source_height = unsigned(height);
      entry.surface_key = active_key;
      entry.group_load_epoch = group_load_epoch_;
      // Generated and plain named textures are excluded from the prepared
      // replacement upload count.
      return handle;
    }
    if (!replacement) {
      int32_t handle = create_texture(width, height, rgba, type);
      auto &entry = textures_[handle];
      if (name)
        entry.name = name;
      entry.surface_key = active_key;
      entry.group_load_epoch = group_load_epoch_;
      return handle;
    }
    if (!rgba || width <= 0 || height <= 0)
      throw std::runtime_error("Invalid named texture input");
    const auto pixels =
        image_pixels(*replacement, rgba, unsigned(width), unsigned(height));
    const auto handle =
        create_texture(int(replacement->width), int(replacement->height),
                       reinterpret_cast<const uint8_t *>(pixels.data()), type);
    auto &entry = textures_[handle];
    entry.replacement = replacement;
    entry.source_width = unsigned(width);
    entry.source_height = unsigned(height);
    if (name)
      entry.name = name;
    entry.surface_key = active_key;
    entry.group_load_epoch = group_load_epoch_;
    ++named_textures_;
    return handle;
  }

  void release_texture(int32_t handle) override {
    auto &entry = textures_.at(handle);
    if (entry.scene_index != no_binding || entry.sharp_index != no_binding) {
      flush();
    }
    entry = {};
  }

  void clear(bool color, uint8_t red, uint8_t green, uint8_t blue) override {
    ensure_extent();
    if (color && lighting_.enabled && lighting_.suppress_sky)
      append_clear(true, 0, 0, 0);
    else
      append_clear(color, red, green, blue);
  }

  void set_fog_color(uint8_t red, uint8_t green, uint8_t blue) override {
    fog_ = {red / 255.0f, green / 255.0f, blue / 255.0f};
  }
  void begin_scene() override {
    begin_scene_housekeeping();
    // HUD source textures update during play. Bulk warmup belongs to loading
    // and this first world scene, after late player and IA assets arrive.
    if (first_world_preload_pending_) {
      prepared_preload_pending_ = true;
      if (lighting_.normals)
        surface_normals_.preload_pending = true;
      preload_mission_normal_textures();
      first_world_preload_pending_ = false;
    }
    local_lights_begin();
  }
  void begin_canvas_scene() override {
    begin_scene_housekeeping();
    // Finish the preceding world's packets before dropping its snapshot. A
    // canvas has no world projection, but observed effects must survive it.
    local_active_ = false;
    local_native_.clear();
  }
  void end_scene() override {
    flush();
    complete_local_light_packets();
    local_active_ = false;
  }

  void draw(Primitive primitive, const TLVertex *vertices, int count,
            const DrawState &state) override {
    require_producer_live();
    if (state.blend && state.unsupported_blend)
      throw std::runtime_error(
          "Unsupported MW3 alpha blend factor pair: SRCBLEND=" +
          std::to_string(state.source_blend) + " DESTBLEND=" +
          std::to_string(state.destination_blend));
    // Only the explicitly marked 2D compositor may supply CPU vertices in
    // strict mode. Depth-always also occurs in 3D overlays, so it cannot
    // identify a HUD exemption.
    if (count > 0 && !state.sharp &&
        geometry_mode_ != cc::geometry::Mode::legacy) {
      ++geometry_statistics_.cpu_draw_calls;
      if (geometry_mode_ == cc::geometry::Mode::gpu)
        throw std::runtime_error(
            "Strict GPU geometry: CPU 3D draw is not implemented");
    }
    if (suppress_model_draws_)
      return;
    if (state.texture >= 0 &&
        std::size_t(state.texture) < textures_.size() &&
        deferred_material_binding_ &&
        validated_deferred_binding(textures_[state.texture].surface_key,
                                   state.texture))
      ++deferred_material_admissions_;
    local_lights_observe(vertices, count, state);
    append_draw(primitive, vertices, count, state,
                state.sharp || (state.depth_always &&
                                !authenticated_deferred_world_draw()));
  }

  void clear_depth_rect(int left, int top, int right, int bottom) override {
    if (right <= left || bottom <= top)
      return;
    const float l = float(left), t = float(top), r = float(right),
                b = float(bottom);
    const TLVertex vertices[] = {{l, t, 0, 1, 0, 0xff000000, 0, 0},
                                 {r, t, 0, 1, 0, 0xff000000, 0, 0},
                                 {r, b, 0, 1, 0, 0xff000000, 0, 0},
                                 {l, b, 0, 1, 0, 0xff000000, 0, 0}};
    DrawState state{};
    state.blend = state.depth_write = state.depth_always = true;
    // Preserve the inherited rasterized depth-only operation and its fractional
    // viewport coverage, without treating it as a color/HUD composition
    // boundary.
    append_draw(Primitive::kFan, vertices, 4, state, scene_.hud, true);
  }

private:
  void begin_scene_housekeeping() {
    if (!scene_.draws.empty())
      flush();
    complete_local_light_packets();
    ensure_extent();
    // Cleanup once per scene instead of scanning the preloaded cache per draw.
    prune_native_geometry();
    const bool hdr_enabled = window_hdr_enabled();
    if (hdr_enabled != display_hdr_) {
      drain();
      display_hdr_ = hdr_enabled;
      renderer_->update_lighting_settings(display_lighting());
    }
  }

  void require_producer_live() const {
    if (producer_failed_ || producer_generation_exhausted_)
      throw std::runtime_error("Core producer requires explicit reset after abandonment");
  }
  static void validate_producer_view(const ::platform::ProducerView& view) {
    const bool original = view.purpose == ::platform::ProducerPurpose::Original;
    const bool known = original || view.purpose == ::platform::ProducerPurpose::MainWorld ||
                       view.purpose == ::platform::ProducerPurpose::WorldZoom;
    if (view.record_version != ::platform::kProducerViewRecordVersion || !known ||
        view.present == original ||
        (view.present && (!view.producer_generation || !view.mission_epoch)) ||
        (!view.present && (view.producer_generation || view.mission_epoch)))
      throw std::runtime_error("Invalid Core producer view provenance");
    // No numeric policy: original NaNs and stale inverses are owned data.
  }
  VkRect2D producer_scissor(bool hud = false) const {
    const VkRect2D full_scene{{0, 0}, {scene_.width, scene_.height}};
    if (hud || !producer_view_.present ||
        producer_view_.purpose != ::platform::ProducerPurpose::WorldZoom ||
        !producer_view_.camera_rect_available)
      return full_scene;

    auto viewport = viewport_;
    if (producer_view_.canvas_available)
      viewport = {producer_view_.canvas.x, producer_view_.canvas.y,
                  producer_view_.canvas.width, producer_view_.canvas.height};
    if (viewport[2] <= 0 || viewport[3] <= 0 ||
        producer_view_.camera_rect.width <= 0 ||
        producer_view_.camera_rect.height <= 0 ||
        scene_.width > std::uint32_t(std::numeric_limits<std::int32_t>::max()) ||
        scene_.height > std::uint32_t(std::numeric_limits<std::int32_t>::max())) {
      static std::atomic_flag invalid_world_zoom_scissor_logged = ATOMIC_FLAG_INIT;
      if (!invalid_world_zoom_scissor_logged.test_and_set())
        std::fprintf(stderr,
                     "Core renderer: invalid WorldZoom scissor inputs; "
                     "using full scene (logged once)\n");
      return full_scene;
    }

    // Match canvas_to_render: transform both edges with integer truncation,
    // then derive the size. Mapping a size alone can grow fractional edges.
    const auto map_edge = [](std::int64_t coordinate, std::int32_t origin,
                             std::uint32_t scene_extent,
                             std::int32_t viewport_extent) {
      return (coordinate - origin) * std::int64_t(scene_extent) /
             viewport_extent;
    };
    const auto clamp_edge = [](std::int64_t edge, std::uint32_t extent) {
      return std::clamp<std::int64_t>(edge, 0, extent);
    };
    const auto& rect = producer_view_.camera_rect;
    const auto left = clamp_edge(
        map_edge(rect.x, viewport[0], scene_.width, viewport[2]), scene_.width);
    const auto top = clamp_edge(
        map_edge(rect.y, viewport[1], scene_.height, viewport[3]), scene_.height);
    const auto right = clamp_edge(
        map_edge(std::int64_t(rect.x) + rect.width, viewport[0], scene_.width,
                 viewport[2]), scene_.width);
    const auto bottom = clamp_edge(
        map_edge(std::int64_t(rect.y) + rect.height, viewport[1], scene_.height,
                 viewport[3]), scene_.height);
    return {{std::int32_t(left), std::int32_t(top)},
            {std::uint32_t(right - left), std::uint32_t(bottom - top)}};
  }
  void clear_producer_work(bool failed) noexcept {
    const auto previous_view = producer_view_;
    scene_ = {};
    pending_local_packets_.clear();
    pending_local_bytes_ = 0;
    submitted_textures_.clear();
    invalidate_scene_bindings();
    deferred_material_binding_.reset();
    native_context_ = {};
    suppress_model_draws_ = false;
    local_active_ = false;
    producer_view_ = {};
    resident_width_ = resident_height_ = 0;
    if (producer_reset_generation_ == std::numeric_limits<std::uint64_t>::max())
      producer_generation_exhausted_ = true;
    else
      ++producer_reset_generation_;
    producer_failed_ = failed || producer_generation_exhausted_;
    if (producer_observer_) {
      testing::ProducerViewObservation observation{};
      observation.stage = failed ? testing::ProducerViewStage::abandon : testing::ProducerViewStage::reset;
      observation.failed = producer_failed_;
      observation.view = previous_view;
      observation.scene_draws = scene_.draws.size();
      observation.pending_local_packets = pending_local_packets_.size();
      observation.upload_receipts = submitted_textures_.size();
      producer_observer_->backend(observation);
    }
  }
  static testing::ProducerViewObservation producer_draw_observation(
      const vk::Draw& draw, const vk::Scene& scene, std::uint64_t packet) {
    testing::ProducerViewObservation observation{};
    observation.view = draw.producer_view;
    observation.packet = packet;
    observation.first = draw.first;
    observation.count = draw.count;
    observation.scissor_offset = {draw.scissor.offset.x, draw.scissor.offset.y};
    observation.scissor_extent = {draw.scissor.extent.width,
                                  draw.scissor.extent.height};
    observation.sun_tl = bool(draw.sun_tl);
    observation.height_binding = bool(draw.height_binding);
    observation.surface_eye = draw.surface_eye;
    if (draw.sun_tl) {
      observation.camera_world = draw.sun_tl->camera_world;
      observation.projection = draw.sun_tl->projection;
    }
    const auto offset = std::size_t(draw.first) * sizeof(TLVertex);
    if (draw.count && offset <= scene.vertices.size() &&
        scene.vertices.size() - offset >= sizeof(TLVertex))
      std::memcpy(&observation.first_vertex, scene.vertices.data() + offset, sizeof(TLVertex));
    return observation;
  }
  void observe_producer_draw(const vk::Draw& draw) {
    if (!producer_observer_) return;
    auto observation = producer_draw_observation(draw, scene_, 0);
    observation.stage = testing::ProducerViewStage::append;
    observation.scene_draws = scene_.draws.size();
    observation.pending_local_packets = pending_local_packets_.size();
    producer_observer_->producer(observation);
  }
  void observe_producer_packet(const vk::Scene& scene, std::uint64_t packet, bool local) {
    if (!producer_observer_) return;
    for (const auto& draw : scene.draws) {
      auto observation = producer_draw_observation(draw, scene, packet);
      observation.stage = local ? testing::ProducerViewStage::local_packet : testing::ProducerViewStage::packet;
      observation.scene_draws = scene.draws.size();
      observation.pending_local_packets = pending_local_packets_.size();
      producer_observer_->producer(observation);
    }
  }
  void observe_worker_packet(const vk::Scene& scene, std::uint64_t packet) noexcept {
    if (!producer_observer_) return;
    for (const auto& draw : scene.draws) {
      auto observation = producer_draw_observation(draw, scene, packet);
      observation.stage = testing::ProducerViewStage::packet;
      producer_observer_->backend(observation);
    }
  }

  int32_t prepared_normal(const ::platform::prepared::NormalImage &image) {
    const auto found = prepared_normals_.find(&image);
    if (found != prepared_normals_.end())
      return found->second;
    const auto handle = create_texture(
        int(image.width), int(image.height),
        reinterpret_cast<const uint8_t *>(image.pixels.data()), 1);
    prepared_normals_.emplace(&image, handle);
    return handle;
  }

  void append_draw(Primitive primitive, const TLVertex *vertices, int count,
                   const DrawState &state, bool hud, bool depth_only = false) {
    VisualFloatScope float_scope;
    require_producer_live();
    validate_producer_view(producer_view_);
    zmth::Projection projection{};
    const float* camera = nullptr;
    auto viewport = viewport_;
    if (producer_view_.present) {
      static_assert(sizeof(projection) == sizeof(producer_view_.projection), "projection storage");
      std::memcpy(&projection, &producer_view_.projection, sizeof projection);
      camera = producer_view_.camera;
      if (producer_view_.canvas_available)
        viewport = {producer_view_.canvas.x, producer_view_.canvas.y,
                    producer_view_.canvas.width, producer_view_.canvas.height};
    } else {
      projection = zmth::projection();
      camera = zmth::view().camera.m;
    }
    CpuInterval interval(cpu_profile_ ? &append_ticks_ : nullptr);
    if (count <= 0) {
      return;
    }
    ensure_extent();
    if (!scene_.draws.empty() && scene_.hud != hud) {
      flush();
      ensure_extent();
    }
    scene_.hud = hud;
    const unsigned first = unsigned(scene_.vertices.size() / sizeof(TLVertex));
    const auto add = [&](TLVertex vertex) {
      vertex.sx =
          (vertex.sx - viewport[0]) * scene_.width / float(viewport[2]);
      vertex.sy =
          (vertex.sy - viewport[1]) * scene_.height / float(viewport[3]);
      if (vertex.rhw <= 0) {
        vertex.rhw = 1;
      }
      const auto *bytes = reinterpret_cast<const unsigned char *>(&vertex);
      scene_.vertices.insert(scene_.vertices.end(), bytes,
                             bytes + sizeof(TLVertex));
    };
    if (primitive == Primitive::kFan) {
      for (int i = 1; i + 1 < count; ++i) {
        add(vertices[0]);
        add(vertices[i]);
        add(vertices[i + 1]);
      }
    } else if (primitive == Primitive::kStrip) {
      for (int i = 0; i + 2 < count; ++i) {
        add(vertices[i + (i & 1)]);
        add(vertices[i + 1 - (i & 1)]);
        add(vertices[i + 2]);
      }
    } else if (primitive == Primitive::kPoints) {
      for (int i = 0; i < count; ++i) {
        TLVertex a = vertices[i], b = a, c = a, d = a;
        b.sx += 1;
        c.sy += 1;
        d.sx += 1;
        d.sy += 1;
        add(a);
        add(b);
        add(c);
        add(b);
        add(d);
        add(c);
      }
    } else {
      throw std::runtime_error("Unsupported mw3-re draw primitive");
    }
    const unsigned drawn =
        unsigned(scene_.vertices.size() / sizeof(TLVertex)) - first;
    if (!drawn) {
      return;
    }
    if (state.wireframe) {
      throw std::runtime_error(
          "Wireframe is unavailable in the Vulkan Training trial");
    }

    vk::Draw draw{};
    draw.producer_view = producer_view_;
    draw.native_sky = state.native_sky;
    draw.depth_only = depth_only;
    draw.first = first;
    draw.count = drawn;
    draw.texture =
        state.texture < 0 ? -1 : int(bind_texture(state.texture, state.sharp));
    // Built from this draw's owned producer view (projection/camera/viewport above), never
    // from the live global camera, so queued draws keep the view they were recorded with.
    auto capture_tl_view = [&]() {
      auto tl = std::make_shared<mw34::sun::Tl>();
      const auto &proj = projection;
      if (proj.near_z > 0 && proj.fx_near > 0 && proj.fy_near > 0 &&
          viewport[2] > 0 && viewport[3] > 0) {
        tl->projection = {
            proj.near_z,
            proj.fx_near * float(scene_.width) / float(viewport[2]),
            proj.fy_near * float(scene_.height) / float(viewport[3]),
            (proj.cx - float(viewport[0])) * float(scene_.width) /
                float(viewport[2]),
            (proj.cy - float(viewport[1])) * float(scene_.height) /
                float(viewport[3]),
            proj.far_z > 0 ? proj.far_z : 1000.0f};
        const float *m = camera;
        tl->camera_world = {m[0], m[3],  m[6], m[9], m[1], m[4],
                            m[7], m[10], m[2], m[5], m[8], m[11]};
      } else {
        tl->projection = {1.0f,
                          float(scene_.width),
                          float(scene_.height),
                          float(scene_.width) * .5f,
                          float(scene_.height) * .5f,
                          1000.0f};
        tl->camera_world = {1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0};
      }
      return tl;
    };
    // Native sky keeps its unlit TL material role. The owned view is only
    // for intentional campaign/profile sky shading in apply_atmosphere.
    if (lighting_.enabled && state.native_sky)
      draw.sky_view = capture_tl_view();
    // Fixed-function translucent effects and multiply passes retain their
    // original unlit output. Applying the world sun equation to their texture
    // and vertex colour turns emissive beams and flashes into dark shadows.
    if (lighting_.enabled && !state.native_sky && state.texture >= 0) {
      const auto &tex_entry = textures_.at(state.texture);
      const auto key = tex_entry.surface_key;
      const auto epoch = tex_entry.group_load_epoch;
      const auto tex_name = tex_entry.name;
      if (epoch == group_load_epoch_ && key.hash != 0) {
        const bool apply_sun_lighting = !state.blend && !state.multiply;
        int norm_idx = lighting_.normals && apply_sun_lighting
                           ? deferred_surface_normal_index(key, state.texture)
                           : -1;
        if (norm_idx >= 0) {
          const bool first_normal_handle =
              surface_normal_textures_.find(norm_idx) ==
              surface_normal_textures_.end();
          int norm_handle = surface_normal_texture(norm_idx);
          mw34::timing::ScopedDuration upload_timer(
              first_normal_handle
                  ? producer_resource_timing_.page_upload_target()
                  : nullptr);
          draw.normal_texture = int(bind_texture(norm_handle, false));
        } else {
          draw.normal_texture = -1;
        }
        if (apply_sun_lighting)
          draw.sun_tl = capture_tl_view();
        const auto &proj = projection;
        if (lighting_.normals && apply_sun_lighting) {
          draw.surface_parameters =
              deferred_surface_parameters(key, state.texture);
          if (draw.surface_parameters[3] > .5f && proj.near_z > 0 &&
              proj.fx_near > 0 && proj.fy_near > 0 && viewport[2] > 0 &&
              viewport[3] > 0) {
            const auto &eye = draw.sun_tl->camera_world;
            draw.surface_eye = {eye[3], eye[7], eye[11], 1.f};
          }
        }
        if (apply_sun_lighting) {
          auto norms = std::make_shared<std::vector<std::array<float, 3>>>(
              drawn, std::array<float, 3>{0, 0, 0});
          draw.lit_normals = std::move(norms);
        }
        if (norm_idx >= 0 && !logged_first_normal_trace_) {
          logged_first_normal_trace_ = true;
          std::fprintf(
              stderr,
              "[SURFACE_NORMAL_TRACE] First authenticated surface "
              "normal bound: "
              "name=%s key={w=%u, h=%u, fmt=%u, hash=0x%llx} slot=%d "
              "normal_slot=%d normal_index=%d catalog=%s "
              "uv_transform=[1,0,0,0,1,0] sampler_address=[%d,%d] "
              "proj=[near=%f, fx_near=%f, fy_near=%f, cx=%f, cy=%f] "
              "viewport=[%d,%d,%d,%d] scene=[%u,%u] v0=[sx=%f, sy=%f, "
              "sz=%f, rhw=%f, u=%f, v=%f]\n",
              tex_name.c_str(), key.width, key.height, key.format,
              (unsigned long long)key.hash, draw.texture, draw.normal_texture,
              norm_idx,
              surface_normals_.cache.authored.count(key) ? "authored" : "world",
              state.address_u, state.address_v, proj.near_z, proj.fx_near,
              proj.fy_near, proj.cx, proj.cy, viewport[0], viewport[1],
              viewport[2], viewport[3], scene_.width, scene_.height,
              vertices[0].sx, vertices[0].sy, vertices[0].sz, vertices[0].rhw,
              vertices[0].tu, vertices[0].tv);
        }
      }
    }
    if (state.texture >= 0 &&
        (bridge_config_.water_detail || bridge_config_.cloud_detail)) {
      // draw is value-initialized per submission, so no earlier draw can leak
      // a detail role/image; a miss preserves this draw's ordinary normal map.
      surface_normals_load();
      const auto &key = textures_.at(std::size_t(state.texture)).surface_key;
      if (const auto *binding = mw34::detail::find_binding(
              surface_normals_.detail_bindings, key, scene_.detail_settings)) {
        draw.detail_role = binding->role;
        if (binding->normal_index < 0)
          throw std::runtime_error(
              "Validated surface detail role lost its normal image");
        const bool first_normal_handle =
            surface_normal_textures_.find(binding->normal_index) ==
            surface_normal_textures_.end();
        const int32_t normal_handle =
            surface_normal_texture(binding->normal_index);
        mw34::timing::ScopedDuration upload_timer(
            first_normal_handle
                ? producer_resource_timing_.page_upload_target()
                : nullptr);
        draw.normal_texture = int(bind_texture(normal_handle, false));
      }
    }
    const bool sharp = state.sharp && state.filter == ::platform::TextureFilter::kDefault &&
                       state.texture >= 0 &&
                       !textures_.at(state.texture).held_copy;
    draw.sampler = (state.address_u == 3 ? 3U : 1U) << 4 |
                   (state.address_v == 3 ? 3U : 1U) << 8 |
                   (state.filter == ::platform::TextureFilter::kNearest ? 0U :
                    state.filter == ::platform::TextureFilter::kLinear ? 3U :
                    state.sharp && !sharp ? 0U : 3U);
    if (!hud)
      draw.sampler |= 0x10000U;
    const auto flare = state.flare_diagnostic;
    if (flare.slot >= 0 && flare.slot < 4 && state.texture >= 0 &&
        logged_flare_count_ < logged_flare_textures_.size()) {
      const auto &entry = textures_.at(state.texture);
      const auto end = logged_flare_textures_.begin() + logged_flare_count_;
      const auto logged = std::find_if(
          logged_flare_textures_.begin(), end,
          [&](const LoggedFlareTexture &key) {
            if (entry.name.empty())
              return key.name.empty() && key.handle == state.texture;
            return key.name == entry.name;
          });
      if (logged == end) {
        logged_flare_textures_[logged_flare_count_++] = {entry.name, state.texture};
        const char *queue = "immediate";
        if (state.queue == ::platform::DrawQueue::Transparent)
          queue = "transparent";
        else if (state.queue == ::platform::DrawQueue::Overlay)
          queue = "overlay";
        std::fprintf(
            stderr,
            "[FLARE_TEXTURE] slot=%d name=\"%s\" uploaded=%ux%u replacement=%s %s "
            "half_size_screen_px=%g half_size_target_px=[%g,%g] sampler=0x%x "
            "queue=%s source=%ux%u viewport=%dx%d target=%ux%u hud=%d\n",
            flare.slot, entry.name.empty() ? "<unknown>" : entry.name.c_str(),
            entry.width, entry.height, entry.replacement ? "yes" : "no",
            mw34::flare::generated_field(entry.generated_rgba),
            flare.half_size_pixels,
            flare.half_size_pixels * scene_.width / float(viewport[2]),
            flare.half_size_pixels * scene_.height / float(viewport[3]),
            draw.sampler, queue,
            entry.replacement ? entry.source_width : entry.width,
            entry.replacement ? entry.source_height : entry.height,
            viewport[2], viewport[3], scene_.width, scene_.height, int(hud));
      }
    }
    // D3DBLEND factors; 14 is ours: ONE, ONE through a reverse subtract (vk_scene's pipeline).
    uint8_t source_factor = 5, destination_factor = 6;
    if (state.multiply)
      source_factor = 1, destination_factor = 3;
    else if (state.brighten)
      source_factor = 9, destination_factor = 2;
    else if (state.subtract)
      source_factor = vk::kReverseSubtractBlend, destination_factor = 2;
    else if (state.additive)
      source_factor = 2, destination_factor = 2;
    draw.key = {uint8_t(state.blend || state.multiply),
                source_factor,
                destination_factor,
                1,
                uint8_t(state.depth_always ? 8 : 7),
                uint8_t(state.depth_write),
                1,
                0};
    // Final draw policy is known here. Ineligible passes never ask for new
    // height provenance, including deferred packets captured in model scope.
    if (lighting_.enabled && lighting_.normals && state.texture >= 0 &&
        native_ground_draw_eligible(state, hud, depth_only, geometry_debug_,
                                    primitive == Primitive::kPoints)) {
      const auto &slot = textures_.at(state.texture);
      draw.height_binding = deferred_height_binding(slot.surface_key, state.texture);
      if (draw.height_binding) {
        // projection is selected from the producing view above.
        if (!(projection.near_z > 0) || !(projection.fx_near > 0) ||
            !(projection.fy_near > 0) || !(projection.far_z > projection.near_z) ||
            !std::isfinite(projection.near_z) || !std::isfinite(projection.fx_near) ||
            !std::isfinite(projection.fy_near) || !std::isfinite(projection.far_z) ||
            !std::isfinite(projection.cx) || !std::isfinite(projection.cy) ||
            viewport[2] <= 0 || viewport[3] <= 0)
          throw std::runtime_error("POM native ground requires a valid native projection");
        const float *m = camera;
        const ::platform::prepared::Matrix camera_to_world{
            m[0], m[3], m[6], m[9], m[1], m[4], m[7], m[10],
            m[2], m[5], m[8], m[11], 0, 0, 0, 1};
        draw.surface_eye = native_height_eye(camera_to_world);
      }
    }
    draw.push.target[0] = float(scene_.width);
    draw.push.target[1] = float(scene_.height);
    std::copy(fog_.begin(), fog_.end(), draw.push.fog);
    draw.push.mode[0] = 2 | (draw.texture >= 0 ? 4 : 0) | (state.fog ? 16 : 0);
    if (sharp)
      draw.push.mode[0] |= 64;
    constexpr unsigned texture = 2U << 8;
    constexpr unsigned diffuse = 0;
    draw.push.mode[1] = draw.texture < 0     ? 2 | diffuse
                        : state.color_select ? 2 | texture
                                             : 4 | texture;
    draw.push.mode[2] = draw.texture < 0
                            ? 2 | diffuse
                            : (state.alpha_modulate ? 4 : 2) | texture;
    draw.scissor = producer_scissor(hud);
    if (native_ground_draw_eligible(state, hud, depth_only, geometry_debug_,
                                    primitive == Primitive::kPoints))
      apply_fixture_observation(draw, deferred_fixture_observation(state.texture));
    if (!scene_.order.empty() && !scene_.order.back().clear) {
      auto &previous = scene_.draws.back();
      if (!previous.model && previous.depth_only == draw.depth_only &&
          previous.native_sky == draw.native_sky &&
          ::platform::same_producer_view_bits(previous.producer_view, draw.producer_view) &&
          previous.texture == draw.texture &&
          previous.normal_texture == draw.normal_texture &&
          bool(previous.sun_tl) == bool(draw.sun_tl) &&
          (!draw.sun_tl ||
           (previous.sun_tl->camera_world == draw.sun_tl->camera_world &&
            previous.sun_tl->projection == draw.sun_tl->projection)) &&
          bool(previous.sky_view) == bool(draw.sky_view) &&
          (!draw.sky_view ||
           (previous.sky_view->camera_world == draw.sky_view->camera_world &&
            previous.sky_view->projection == draw.sky_view->projection)) &&
          bool(previous.lit_normals) == bool(draw.lit_normals) &&
          bool(previous.raw_fog) == bool(draw.raw_fog) &&
          previous.surface_parameters == draw.surface_parameters &&
          previous.surface_eye == draw.surface_eye &&
          previous.emission_index == draw.emission_index &&
          mw34::materials::same_height_binding(previous.height_binding, draw.height_binding) &&
          previous.sampler == draw.sampler &&
          previous.key.packed() == draw.key.packed() &&
          std::memcmp(&previous.push, &draw.push, sizeof(draw.push)) == 0) {
        if (previous.lit_normals && draw.lit_normals) {
          auto merged_normals =
              std::make_shared<std::vector<std::array<float, 3>>>(
                  *previous.lit_normals);
          merged_normals->insert(merged_normals->end(),
                                 draw.lit_normals->begin(),
                                 draw.lit_normals->end());
          previous.lit_normals = std::move(merged_normals);
        }
        // Raw fog is attached only to CPU-clipped prepared draws, which are pushed directly and
        // never built here, so today this branch cannot see two raw-fog draws. Merge it exactly
        // like the normals anyway: a merged draw whose raw_fog stayed short would throw
        // "Clipped raw-fog range mismatch" at submit.
        if (previous.raw_fog && draw.raw_fog) {
          auto merged_fog = std::make_shared<std::vector<std::array<float, 4>>>(*previous.raw_fog);
          merged_fog->insert(merged_fog->end(), draw.raw_fog->begin(), draw.raw_fog->end());
          previous.raw_fog = std::move(merged_fog);
        }
        previous.count += drawn;
        observe_producer_draw(previous);
        return;
      }
    }
    scene_.order.push_back({false, unsigned(scene_.draws.size())});
    scene_.draws.push_back(std::move(draw));
    observe_producer_draw(scene_.draws.back());
    if (sharp)
      ++gpu_sharp_draws_;
  }

#include "frame_submission.inc"

  bool read_back(std::vector<uint32_t> *argb, int *width,
                 int *height) override {
    std::vector<uint8_t> bgra;
    unsigned w = 0, h = 0;
    flush();
    complete_local_light_packets();
    const auto capture = [&] { renderer_->capture_fullres_bgra(bgra, w, h); };
    if (worker_)
      worker_->call(capture);
    else
      capture();
    if (bgra.empty()) {
      return false;
    }
    const mw34::display::Samples samples{quality_.samples_x,
                                         quality_.samples_y};
    *width = int(w / samples.x);
    *height = int(h / samples.y);
    if (samples.x == 1 && samples.y == 1) {
      argb->resize(std::size_t(w) * h);
      std::memcpy(argb->data(), bgra.data(), bgra.size());
      return true;
    }
    argb->assign(std::size_t(*width) * *height, 0);
    // Match the resident presenter's integer-grid SSAA resolve. The game-facing
    // readback and held frame keep their output dimensions and alpha contract.
    for (int y = 0; y < *height; ++y)
      for (int x = 0; x < *width; ++x) {
        std::uint32_t pixel = 0;
        for (unsigned channel = 0; channel < 4; ++channel) {
          unsigned sum = 0;
          for (unsigned sy = 0; sy < samples.y; ++sy)
            for (unsigned sx = 0; sx < samples.x; ++sx)
              sum += bgra[((y * samples.y + sy) * w + x * samples.x + sx) * 4 +
                          channel];
          const unsigned count = samples.x * samples.y;
          pixel |= ((sum + count / 2) / count) << (channel * 8);
        }
        (*argb)[std::size_t(y) * *width + x] = pixel;
      }
    return true;
  }

  bool hold_frame() override {
    return read_back(&held_, &held_width_, &held_height_);
  }
  bool restore_frame() override {
    ensure_extent();
    if (held_.empty() || unsigned(held_width_) != scene_.width ||
        unsigned(held_height_) != scene_.height) {
      return false;
    }
    const auto rgba = rgba_copy(held_);
    const auto handle =
        create_texture(held_width_, held_height_,
                       reinterpret_cast<const uint8_t *>(rgba.data()), 1);
    textures_[handle].held_copy = true;
    const auto old_view = viewport_;
    set_viewport(0, 0, held_width_, held_height_);
    const float w = float(held_width_), h = float(held_height_);
    const TLVertex quad[] = {{0, 0, 0, 1, 0xffffffff, 0, 0, 0},
                             {w, 0, 0, 1, 0xffffffff, 0, 1, 0},
                             {w, h, 0, 1, 0xffffffff, 0, 1, 1},
                             {0, h, 0, 1, 0xffffffff, 0, 0, 1}};
    DrawState copy{};
    copy.sharp = true;
    copy.texture = handle;
    copy.address_u = copy.address_v = 3;
    copy.depth_always = true;
    copy.depth_write = false;
    draw(Primitive::kFan, quad, 4, copy);
    release_texture(handle);
    viewport_ = old_view;
    return true;
  }
  void drop_frame() override { held_.clear(); }

#include "frame_presentation.inc"

private:
  int32_t prepared_texture(const ::platform::prepared::Image &image) {
    const auto found = prepared_textures_.find(&image);
    if (found != prepared_textures_.end()) {
      // PreparedModels owns this immutable image across mission resource
      // resets. A real draw republishes its value identity in the new epoch.
      textures_.at(found->second).group_load_epoch = group_load_epoch_;
      return found->second;
    }
    const auto pixels = image_pixels(image);
    const auto handle =
        create_texture(int(image.width), int(image.height),
                       reinterpret_cast<const uint8_t *>(pixels.data()), 1);
    // The prepared reader preserves a declared hash without checking it. This
    // immutable slot gets an exact key from its complete visible RGB565 plane.
    textures_.at(handle).surface_key = prepared_fixture_key(image);
    prepared_textures_.emplace(&image, handle);
    return handle;
  }

  std::shared_ptr<const vk::ModelGeometry>
  prepared_geometry(const ::platform::prepared::Batch &batch) {
    const auto found = prepared_geometry_.find(&batch);
    if (found != prepared_geometry_.end())
      return found->second;
    auto geometry = std::make_shared<vk::ModelGeometry>();
    geometry->key = 0x4343000000000000ULL + prepared_geometry_.size() + 1;
    geometry->vertices.reserve(batch.vertices.size());
    for (const auto &vertex : batch.vertices)
      geometry->vertices.push_back({vertex[0], vertex[1], vertex[2], vertex[3],
                                    vertex[4], vertex[5], vertex[6],
                                    vertex[7]});
    geometry->hash = 0xcbf29ce484222325ULL;
    const auto *bytes =
        reinterpret_cast<const uint8_t *>(geometry->vertices.data());
    for (size_t i = 0; i < geometry->vertices.size() * sizeof(vk::ModelVertex);
         ++i) {
      geometry->hash ^= bytes[i];
      geometry->hash *= 0x100000001b3ULL;
    }
    prepared_geometry_.emplace(&batch, geometry);
    return geometry;
  }

  void emit_prepared(const PreparedBatchDraw &source,
                     const ::platform::ModelDrawContext &context) {
    VisualFloatScope guard;
    CpuInterval interval(cpu_profile_ ? &prepared_emit_ticks_ : nullptr);
    if (geometry_mode_ != cc::geometry::Mode::legacy &&
        source.deformed.empty()) {
      emit_gpu_prepared(source, context, prepared_fog());
      return;
    }
    if (geometry_mode_ == cc::geometry::Mode::gpu)
      throw std::runtime_error(
          "Strict GPU geometry: prepared deformation is not implemented");
    if (geometry_mode_ != cc::geometry::Mode::legacy)
      ++prepared_cpu_fallback_batches_;
    const auto staged = prepared_draw_cache_.get(
        source, context, viewport_, scene_.width, scene_.height,
        prepared_geometry(*source.batch), lighting_.enabled,
        cpu_profile_ ? &prepared_cpu_ : nullptr, prepared_cache_enabled_);
    auto draw = staged->draw;
    draw.producer_view = producer_view_;
    draw.scissor = producer_scissor();
    const auto texture = prepared_texture(*source.texture);
    apply_surface_material(draw, source, lighting_.normals, bridge_config_.parallax_materials,
                           group_load_epoch_, textures_.at(texture).version);
    draw.first = unsigned(scene_.vertices.size() / sizeof(TLVertex));
    draw.texture = int(bind_texture(texture, false));
    if (source.normal && lighting_.normals)
      draw.normal_texture =
          int(bind_texture(prepared_normal(*source.normal), false));
    scene_.vertices.insert(scene_.vertices.end(), staged->vertices.begin(),
                           staged->vertices.end());
    cpu_clipped_triangles_ += staged->clipped_triangles;
    if (draw.count) {
      apply_fixture_observation(draw, capture_fixture_prepared(source, texture));
      scene_.order.push_back({false, unsigned(scene_.draws.size())});
      scene_.draws.push_back(std::move(draw));
      observe_producer_draw(scene_.draws.back());
      ++prepared_batches_;
    }
  }
  bool window_hdr_enabled() const {
    return SDL_GetBooleanProperty(SDL_GetWindowProperties(window_),
                                  SDL_PROP_WINDOW_HDR_ENABLED_BOOLEAN, false);
  }

  mw34::sun::Settings display_lighting() const {
    return mw34::sun::display_ambient(lighting_, campaign_enabled_, display_hdr_);
  }

  void require_editor_producer() const {
    if (SDL_GetCurrentThreadID() != editor_thread_)
      throw std::logic_error("Core editor routing requires its producer thread");
  }

  void initialize_renderer() {
    if (renderer_) {
      // A normal scene reset retires the old device's owner on the producer.
      // Never turn a failed editor/device lifetime into automatic recovery.
      if (renderer_->editor_gpu_statistics().failed)
        throw std::runtime_error("Core editor failure prevents renderer reset");
      renderer_->detach_editor();
      editor_present_active_ = false;
    }
    display_hdr_ = window_hdr_enabled();
    auto source = native_wsi_ ? sdl_surface(window_, window_state_tracker_)
                              : vk::Renderer::WindowSurface{};
    renderer_ = std::make_unique<vk::Renderer>(
        vk::Renderer::ColorTarget::rgba8, std::move(source), quality_,
        !prepared_.empty() || geometry_mode_ != cc::geometry::Mode::legacy ||
            lighting_.enabled,
        display_lighting(), geometry_mode_ != cc::geometry::Mode::legacy,
        bridge_config_);
    renderer_->producer_view_observer = producer_observer_;
    texture_limit_ = renderer_->max_texture_dimension(native_window_);
    if (!native_wsi_ && !renderer_->dxgi_presenting()) {
      throw std::runtime_error("Core Critical DXGI transport is unavailable");
    }
  }

  void ensure_extent() {
    require_producer_live();
    if (reset_pending_) {
      drain();
      retired_draws_ += renderer_->draws;
      retired_presents_ += renderer_->resident_presents;
      retired_quality_ = quality_statistics();
      retired_model_draws_ += renderer_->model_draws;
      retired_model_uploads_ += renderer_->model_uploads;
      retired_lit_draws_ += renderer_->sun_world_draws +
                            renderer_->sun_model_draws +
                            renderer_->sun_tl_draws;
      retired_normal_draws_ += renderer_->normal_draws;
      retired_geometry_buffers_ += renderer_->retired_model_buffers;
      initialize_renderer();
      submitted_textures_.clear();
      window_bound_ = false;
      resident_width_ = resident_height_ = 0;
      scene_ = {};
      invalidate_scene_bindings();
      present_window_width_ = present_window_height_ = 0;
      reset_pending_ = false;
    }
    scene_.detail_settings = surface_detail_settings();
    scene_.detail_time = mw34::detail::presentation_time(
        detail_frame_++, bridge_config_.detail_fixed_time);
    if (scene_.width) {
      return;
    }
    int width = 0, height = 0;
    if (native_wsi_ && window_state_tracker_) {
      const auto state = window_state_tracker_->sample_and_get();
      width = state.drawable_width;
      height = state.drawable_height;
    } else {
      SDL_GetWindowSizeInPixels(window_, &width, &height);
    }
    if (width <= 0 || height <= 0) {
      width = resident_width_ ? int(resident_width_) : 640;
      height = resident_height_ ? int(resident_height_) : 480;
    }
    const auto fit = sdlfe::fit_rect(float(width), float(height),
                                     shape_ ? *shape_ : sdlfe::FrameShape{});
    scene_.width = unsigned(std::max(1.0f, fit.w));
    scene_.height = unsigned(std::max(1.0f, fit.h));
    scene_.has_depth = true;
    if (scene_.width != resident_width_ || scene_.height != resident_height_) {
      if (worker_)
        worker_->drain();
      append_clear(true, 0, 0, 0);
    }
  }

  void append_clear(bool color, uint8_t red, uint8_t green, uint8_t blue) {
    vk::Clear clear{color ? 3U : 2U,
                    {red / 255.f, green / 255.f, blue / 255.f, 1},
                    0,
                    {{{0, 0}, {scene_.width, scene_.height}}}};
    scene_.order.push_back({true, unsigned(scene_.clears.size())});
    scene_.clears.push_back(std::move(clear));
  }

  void prune_native_geometry() {
    ++native_geometry_prune_passes_;
    for (auto iterator = native_geometry_.begin();
         iterator != native_geometry_.end();) {
      if (iterator->second.source.expired())
        iterator = native_geometry_.erase(iterator);
      else
        ++iterator;
    }
  }

  std::shared_ptr<const vk::ModelGeometry> native_model_geometry(const std::shared_ptr<const cc::geometry::Resource> &source) {
    const auto found = native_geometry_.find(source->identity);
    if (found != native_geometry_.end() &&
        !found->second.source.expired() && found->second.geometry)
      return found->second.geometry;
    // Cache misses still reclaim dead snapshots before allocating replacements.
    prune_native_geometry();
    auto &cached = native_geometry_[source->identity];
    if (!cached.geometry) {
      cached.source = source;
      auto geometry = std::make_shared<vk::ModelGeometry>();
      geometry->key = 0x4700000000000000ULL | source->identity;
      geometry->vertices = source->vertices;
      geometry->indices = source->indices;
      geometry->source = source;
      geometry->hash = 0xcbf29ce484222325ULL;
      const auto hash = [&](const void *data, std::size_t bytes) {
        const auto *input = static_cast<const unsigned char *>(data);
        for (std::size_t i = 0; i < bytes; ++i) {
          geometry->hash ^= input[i];
          geometry->hash *= 0x100000001b3ULL;
        }
      };
      hash(geometry->vertices.data(),
           geometry->vertices.size() * sizeof(vk::ModelVertex));
      hash(geometry->indices.data(),
           geometry->indices.size() * sizeof(std::uint32_t));
      cached.geometry = std::move(geometry);
    }
    return cached.geometry;
  }

  void preload_native_model_geometry() {
    VisualFloatScope guard;
    if (!renderer_ || (geometry_mode_ != cc::geometry::Mode::gpu &&
                       geometry_mode_ != cc::geometry::Mode::partial))
      return;
    std::unordered_set<const zcls::ListItem *> visited_items;
    std::unordered_set<zmod::Model *> seen_models;
    for (const zcls::ListItem *item = zcls::list_head(zcls::kAllNodes);
         item; item = item->next) {
      if (!visited_items.insert(item).second)
        throw std::runtime_error("Cycle detected in node list");
      if (item->removable != 0 || !item->node || !item->node->model)
        continue;
      // Prepared-owned nodes never enter the native GPU draw path.
      ::platform::ModelDrawContext binding_context;
      binding_context.node = item->node;
      if (prepared_.has_binding(binding_context))
        continue;
      auto &model = *item->node->model;
      if (!seen_models.insert(&model).second)
        continue;
      if (!zmod::rigid_source_supported(model, zmod::RigidGeometryEligibility{}))
        continue;
      if (model.render_geometry) {
        bool materials_match = model.render_materials.size() == model.count(0x10);
        if (materials_match) {
          for (size_t index = 0; index < model.render_materials.size(); ++index) {
            if (model.render_materials[index] != model.polygons[index].material) {
              materials_match = false;
              break;
            }
          }
        }
        if (!materials_match) {
          model.invalidate_render_geometry();
        }
      }
      if (!model.render_geometry) {
        auto registered = zmod::register_rigid_source(model);
        model.render_geometry = std::move(registered.resource);
        model.render_materials = std::move(registered.original_materials);
      }
      const auto geometry = native_model_geometry(model.render_geometry);
      renderer_->preload_model_geometry(*geometry);
    }
  }

  static std::vector<std::string> live_node_source_assets() {
    // Canonical list membership is required because node_alloc adds nodes
    // to kAllNodes but does not set the world-file kNodeLive bit (which is only
    // set for world-file slots by cls_zbd.cpp). Iterating kAllNodes directly
    // captures all live nodes, including MechLib nodes created with object3d_create.
    std::vector<std::string> source_assets;
    std::set<std::string> seen_source_assets;
    std::unordered_set<const zcls::ListItem *> visited_items;

    for (const zcls::ListItem *item = zcls::list_head(zcls::kAllNodes);
         item != nullptr; item = item->next) {
      if (!visited_items.insert(item).second) {
        throw std::runtime_error("Malformed cycle detected in kAllNodes list");
      }
      if (item->removable != 0 || item->node == nullptr) {
        continue;
      }
      const auto &source_asset = item->node->source_asset;
      if (!source_asset || source_asset->name.empty()) {
        continue;
      }
      if (seen_source_assets.insert(source_asset->name).second) {
        source_assets.push_back(source_asset->name);
      }
    }
    return source_assets;
  }

  std::uint64_t preload_texture_handle(int32_t handle) {
    const std::uint64_t texture_key = std::uint64_t(handle) * 2 + 1;
    const auto &entry = textures_.at(std::size_t(handle));
    const unsigned texture_width = entry.width;
    const unsigned texture_height = entry.height;
    const std::uint64_t texture_version = entry.version;
    const std::array<std::uint64_t, 3> receipt_stamp{
        texture_version, texture_width, texture_height};
    const auto existing_receipt = submitted_textures_.find(texture_key);
    if (existing_receipt != submitted_textures_.end() &&
        existing_receipt->second == receipt_stamp)
      return 0;

    // Upload one transient texture payload at a time without mutating scene
    // bindings or building an all-textures Scene packet.
    const std::uint64_t staged_bytes =
        std::uint64_t(entry.pixels.size()) * sizeof(std::uint32_t);
    vk::TextureRef texture_ref{texture_key,
                               texture_version,
                               texture_width,
                               texture_height,
                               vk::TexFormat::rgba8888,
                               {},
                               entry.pixels};
    renderer_->preload_texture(texture_ref);
    submitted_textures_[texture_key] = receipt_stamp;
    return staged_bytes;
  }

  // Upload matching world normal maps, live-mission prepared model textures,
  // and current-epoch native CPU albedo textures to the GPU after mission loading
  // has finished or at the first scene boundary when late actor assets arrive,
  // so camera turns do not stall on lazy Vulkan image and mip creation.
  void preload_mission_normal_textures() {
    VisualFloatScope guard;
    const bool preload_world_normals = surface_normals_.preload_pending &&
                                       lighting_.enabled && lighting_.normals;
    const bool preload_prepared_assets =
        prepared_preload_pending_ && !prepared_.empty();
    if (!surface_normals_.preload_pending && !prepared_preload_pending_) {
      return;
    }
    if (!renderer_ || producer_failed_) {
      surface_normals_.preload_pending = false;
      prepared_preload_pending_ = false;
      return;
    }
    // The preload settles and records on renderer_ (command pool, fence, queue,
    // texture/model caches and shared staging) from this producer thread. A
    // present packet still queued for the menu, briefing or previous mission
    // would use the same objects on the render worker, so finish those first.
    // Draining here covers every caller, not just the ones that drain already.
    if (worker_)
      worker_->drain();
    if (reset_pending_)
      ensure_extent();
    preload_native_model_geometry();

    // Snapshot original native CPU albedo texture slots before allocating any
    // new normal or prepared texture handles, preventing recursion or dangling
    // references across textures_ reallocations.
    const std::size_t source_texture_count = textures_.size();
    std::vector<int32_t> native_handles;
    std::vector<mw34::materials::SurfaceKey> mission_source_keys;
    native_handles.reserve(source_texture_count);
    if (preload_world_normals)
      mission_source_keys.reserve(source_texture_count);
    for (std::size_t slot_index = 0; slot_index < source_texture_count;
         ++slot_index) {
      const auto &slot = textures_[slot_index];
      if (!slot.pixels.empty() && slot.group_load_epoch == group_load_epoch_ &&
          slot.surface_key.hash != 0) {
        native_handles.push_back(static_cast<int32_t>(slot_index));
        if (preload_world_normals)
          mission_source_keys.push_back(slot.surface_key);
      }
    }

    std::vector<int> unique_normal_indices;
    if (preload_world_normals) {
      surface_normals_load();

      std::set<int> seen_normal_indices;
      for (const auto &source_key : mission_source_keys) {
        const auto authored = surface_normals_.cache.bindings.find(source_key);
        if (authored != surface_normals_.cache.bindings.end() &&
            authored->second < 0)
          continue;
        mw34::timing::ScopedDuration decode_timer(
            producer_resource_timing_.page_decode_target());
        const int normal_index =
            surface_normals_.cache.surface_normal_index(source_key, true);
        surface_normals_.peak_decoded_bytes =
            std::max(surface_normals_.peak_decoded_bytes,
                     surface_normals_.cache.world_bytes);
        if (normal_index >= 0 && seen_normal_indices.insert(normal_index).second)
          unique_normal_indices.push_back(normal_index);
      }
    }

    PreparedTextureResources prepared_resources;
    if (preload_prepared_assets) {
      prepared_resources =
          prepared_.resources_for_assets(live_node_source_assets());
    }

    // Create normal and prepared texture handles outside any active
    // source-upload scope.
    struct ActiveKeyGuard {
      mw34::materials::SurfaceKey saved_key{};
      bool had_active_key{false};
      ActiveKeyGuard() {
        had_active_key = mw34::materials::get_active_surface_key(&saved_key);
        if (had_active_key)
          mw34::materials::clear_active_surface_key();
      }
      ~ActiveKeyGuard() {
        if (had_active_key)
          mw34::materials::set_active_surface_key(saved_key);
        else
          mw34::materials::clear_active_surface_key();
      }
    } active_key_guard;

    // Warm current-epoch native CPU albedo handles before normal or prepared handles.
    std::uint64_t native_staged_bytes = 0;
    for (const int32_t handle : native_handles) {
      native_staged_bytes += preload_texture_handle(handle);
    }

    for (const int normal_index : unique_normal_indices) {
      const int32_t normal_handle = surface_normal_texture(normal_index);
      preload_texture_handle(normal_handle);
    }

    std::size_t selected_normal_count = 0;
    std::uint64_t prepared_staged_bytes = 0;
    if (preload_prepared_assets) {
      // Geometry allocation can exceed a frame even when texture receipts are warm.
      if (geometry_mode_ == cc::geometry::Mode::gpu ||
          geometry_mode_ == cc::geometry::Mode::partial) {
        for (const auto *batch : prepared_resources.rigid_batches) {
          const auto geometry = prepared_geometry(*batch);
          renderer_->preload_model_geometry(*geometry);
        }
      }
      for (const auto *image : prepared_resources.textures) {
        const int32_t texture_handle = prepared_texture(*image);
        prepared_staged_bytes += preload_texture_handle(texture_handle);
      }
      selected_normal_count =
          (lighting_.enabled && lighting_.normals)
              ? prepared_resources.normals.size()
              : 0;
      if (lighting_.enabled && lighting_.normals) {
        for (const auto *normal : prepared_resources.normals) {
          const int32_t normal_handle = prepared_normal(*normal);
          prepared_staged_bytes += preload_texture_handle(normal_handle);
        }
      }
    }

    if (producer_resource_timing_.enabled) {
      std::fprintf(
          stderr,
          "[RESOURCE_TIMING] owner=producer stage=prepared_preload "
          "source_assets=%zu albedos=%zu normals=%zu staged_bytes=%llu "
          "native_textures=%zu native_staged_bytes=%llu\n",
          prepared_resources.matched_source_assets,
          prepared_resources.textures.size(), selected_normal_count,
          static_cast<unsigned long long>(prepared_staged_bytes),
          native_handles.size(),
          static_cast<unsigned long long>(native_staged_bytes));
    }

    surface_normals_.preload_pending = false;
    prepared_preload_pending_ = false;
  }

  unsigned bind_texture(int handle, bool sharp) {
    auto &entry = textures_.at(handle);
    if (entry.pixels.empty()) {
      throw std::runtime_error("mw3-re draw references a released texture");
    }
    const auto key = std::uint64_t(handle) * 2 + unsigned(sharp) + 1;
    unsigned &index = sharp ? entry.sharp_index : entry.scene_index;
    if (index != no_binding) {
      if (!scene_.texture_slot_matches(index, key, entry.version, entry.width,
                                      entry.height)) {
        throw std::runtime_error(
            "Producer Scene texture binding mismatch: handle=" +
            std::to_string(handle) + " sharp=" + std::to_string(sharp) +
            " slot=" + std::to_string(index) +
            " textures=" + std::to_string(scene_.textures.size()) +
            " key=" + std::to_string(key) +
            " version=" + std::to_string(entry.version) +
            " extent=" + std::to_string(entry.width) + "x" +
            std::to_string(entry.height));
      }
      return index;
    }
    const auto w = entry.width;
    const auto h = entry.height;
    vk::TextureRef ref{key, entry.version, w, h, vk::TexFormat::rgba8888, {},
                       {}};
    const auto current = submitted_textures_.find(ref.key);
    if (current == submitted_textures_.end() ||
        current->second != std::array<std::uint64_t, 3>{ref.hash, w, h}) {
      // Held readback is already straight RGBA at the output extent. Its
      // nearest SSAA sampling must preserve alpha-zero RGB as well.
      ref.pixels32 = entry.pixels;
    }
    index = unsigned(scene_.textures.size());
    scene_.textures.push_back(std::move(ref));
    return index;
  }

  static std::vector<uint32_t> rgba_copy(const std::vector<uint32_t> &argb) {
    std::vector<uint32_t> rgba;
    rgba.reserve(argb.size());
    for (const auto pixel : argb) {
      rgba.push_back((pixel & 0xff00ff00U) | ((pixel & 255U) << 16) |
                     ((pixel >> 16) & 255U));
    }
    return rgba;
  }

  void save_capture() {
    std::vector<uint32_t> pixels;
    int width = 0, height = 0;
    if (!read_back(&pixels, &width, &height)) {
      throw std::runtime_error("Core Critical frame capture had no pixels");
    }
    auto *surface = SDL_CreateSurfaceFrom(
        width, height, SDL_PIXELFORMAT_ARGB8888, pixels.data(), width * 4);
    if (!surface) {
      throw std::runtime_error(SDL_GetError());
    }
    const bool saved = SDL_SaveBMP(surface, capture_path_.c_str());
    SDL_DestroySurface(surface);
    if (!saved) {
      throw std::runtime_error(SDL_GetError());
    }
    capture_path_.clear();
  }

  sdlfe::EditorUiSource *editor_source_{};
  const SDL_ThreadID editor_thread_ = SDL_GetCurrentThreadID();
  bool editor_present_active_{};
  SDL_Window *window_;
  std::shared_ptr<cc_mw3_re::platform::SdlWindowStateTracker>
      window_state_tracker_;
  cc_mw3_re::platform::NativeWindowHandle native_window_;
  HWND hwnd_;
  const bool native_wsi_;
  const vk::Renderer::Quality quality_;
  mw34::sun::Settings lighting_;
  const bool modern_flare_style_;
  bool display_hdr_ = false;
  const mw34::sun::Settings base_lighting_;
  const bool campaign_enabled_, sun_explicit_;
  std::shared_ptr<const ::platform::prepared::EnvironmentSelection>
      environment_;
  std::shared_ptr<const zcls::ZbdObservationSession> observation_session_;
  // Owned current-mission state: canonical mission ID plus resolved campaign
  // lighting/policy. The profile pointer refers only to the static campaign
  // profile database (no borrowed native pointers).
  ::platform::MissionIdentity current_mission_identity_{};
  std::string current_mission_id_;
  mw34::campaign::ResolvedMissionLighting current_mission_lighting_{};
  // Validate the original request before sanitizing or loading prepared models.
  const RendererBridgeConfig bridge_config_;
  PreparedModels prepared_;
  const cc::geometry::Mode geometry_mode_;
  const bool geometry_debug_;
  cc::geometry::Statistics geometry_statistics_;
  struct NativeGeometry {
    std::weak_ptr<const cc::geometry::Resource> source;
    std::shared_ptr<const vk::ModelGeometry> geometry;
  };
  std::map<std::uint64_t, NativeGeometry> native_geometry_;
  std::uint64_t native_geometry_prune_passes_{};
  std::unique_ptr<vk::Renderer> renderer_;
  // Declared after renderer_: join before destroying the backend, including
  // unwinding. Only the producer accesses textures and builds the next scene.
  std::unique_ptr<RenderWorker> worker_;
  // Submission number of the last queued resident present (0 = none), so the producer keeps at
  // most one presented frame in flight.
  std::size_t last_present_job_ = 0;
  std::mutex recycle_mutex_;
  std::vector<vk::Scene> recycled_scenes_;
  std::map<std::uint64_t, std::array<std::uint64_t, 3>> submitted_textures_;
  const sdlfe::FrameShape *shape_{};
  vk::Scene scene_{};
  ::platform::ProducerView producer_view_{};
  std::uint64_t producer_reset_generation_{1}, producer_packet_id_{};
  bool producer_failed_{}, producer_generation_exhausted_{};
  testing::ProducerViewObserver* producer_observer_{};
  std::array<int, 4> viewport_{0, 0, 640, 480};
  std::array<float, 3> fog_{};
  std::vector<Texture> textures_;
  std::vector<uint32_t> held_;
  std::string capture_path_;
  std::uint64_t texture_version_{}, retired_draws_{}, retired_presents_{};
  std::atomic<std::uint64_t> presented_frames_{}, resident_draws_{};
  std::uint64_t retired_geometry_buffers_{};
  QualityStatistics retired_quality_{};
  std::map<const ::platform::prepared::Image *, int32_t> prepared_textures_;
  std::map<const ::platform::prepared::NormalImage *, int32_t>
      prepared_normals_;
  std::map<const ::platform::prepared::Batch *,
           std::shared_ptr<const vk::ModelGeometry>>
      prepared_geometry_;
  std::uint64_t group_load_epoch_{1};
  std::map<int, int32_t> surface_normal_textures_;
  bool prepared_preload_pending_{true};
  bool first_world_preload_pending_{false};
  bool logged_first_normal_trace_{false};
  // Names survive handle reuse/reloads; unknown names use the upload handle.
  // Stop after four distinct flare textures, with no growing set or log spam.
  std::array<LoggedFlareTexture, 4> logged_flare_textures_{};
  std::size_t logged_flare_count_{};
  std::uint64_t deferred_material_admissions_{};
  std::uint64_t prepared_batches_{}, retired_model_draws_{},
      cpu_clipped_triangles_{}, named_textures_{};
  bool suppress_model_draws_{};
  std::uint64_t retired_model_uploads_{};
  std::uint64_t retired_lit_draws_{}, retired_normal_draws_{};
  unsigned texture_limit_{}, resident_width_{}, resident_height_{};
  int held_width_{}, held_height_{};
  int32_t present_window_width_{}, present_window_height_{};
  bool window_bound_{}, presented_{}, reported_resident_{}, reset_pending_{};
  const bool cpu_profile_ = cpu_profile_requested();
  mw34::timing::ProducerResourceTiming producer_resource_timing_{};
  std::uint64_t render_ticks_{}, transport_ticks_{};
  std::uint64_t detail_frame_{};
  std::uint64_t worker_render_ticks_{}, worker_present_ticks_{};
  std::uint64_t gpu_sharp_draws_{}, render_calls_{};
  std::uint64_t prepared_emit_ticks_{}, append_ticks_{};
  PreparedDrawCpuStatistics prepared_cpu_;
  std::uint64_t gpu_prepared_vertices_{}, prepared_reference_vertices_{},
      early_prepared_models_{}, prepared_cpu_fallback_batches_{};
  const bool prepared_cache_enabled_;
  const std::size_t local_staging_budget_;
  PreparedDrawCache prepared_draw_cache_;
};

} // namespace

RendererBridgeConfig configure_bridge(sdlfe::RendererBackend backend,
                                      const sdlfe::CoreCriticalQuality &quality,
                                      const sdlfe::CoreCriticalAssets &assets) {
  if (assets.pom &&
      (backend != sdlfe::RendererBackend::core_critical_dxgi &&
       backend != sdlfe::RendererBackend::core_critical_wsi))
    throw std::runtime_error(
        "--cc-pom 1 requires a Core Critical Vulkan backend");
  if (assets.pom && assets.lighting != "normal")
    throw std::runtime_error("--cc-pom 1 requires --cc-lighting normal");
  const bool water_detail_requested =
      assets.water_detail_explicit && assets.water_detail;
  const bool cloud_detail_requested =
      assets.cloud_detail_explicit && assets.cloud_detail;
  if ((water_detail_requested || cloud_detail_requested) &&
      assets.lighting != "normal") {
    std::string flags;
    if (water_detail_requested)
      flags = "--cc-water-detail 1";
    if (cloud_detail_requested) {
      if (!flags.empty())
        flags += " and ";
      flags += "--cc-cloud-detail 1";
    }
    throw std::runtime_error("Surface detail (" + flags +
                             ") requires --cc-lighting normal");
  }
  auto config = RendererBridgeConfig::from_diagnostic_env(
      !assets.dynamic_lighting_explicit, !assets.sun_shadows_explicit);
  config.environment_packs_explicit = assets.environment_packs_explicit;
  if (assets.environment_packs_explicit) {
    // The launcher's selected environment packs own normal-map inputs. Stale
    // development paths must not add catalogs outside that selection.
    config.surface_normal_catalog.clear();
    config.world_normal_manifest.clear();
  }
  if (assets.sun_shadows_explicit)
    config.sun_shadows = assets.sun_shadows;
  if (assets.dynamic_lighting_explicit) {
    // The launcher's explicit choice owns this run, including the diagnostic
    // environment fallback, so stale development variables cannot re-enable it.
    config.effect_lights = false;
    config.effect_light_catalog.clear();
    config.fixture_lights = false;
    config.mech_headlights = false;
    config.stock_headlights.clear();
    config.headlight_bindings.clear();
  }
  const bool dynamic_lighting_allowed =
      !assets.dynamic_lighting_explicit || assets.dynamic_lighting;
  if (assets.effect_lights && dynamic_lighting_allowed) {
    config.effect_lights = true;
    config.effect_light_catalog = assets.effect_light_catalog;
  }
  if (assets.dynamic_lighting_explicit)
    config.fixture_lights = assets.fixture_lights && dynamic_lighting_allowed;
  else if (assets.fixture_lights)
    config.fixture_lights = true;
  if (assets.mech_headlights && dynamic_lighting_allowed) {
    config.mech_headlights = true;
    config.stock_headlights = assets.stock_headlights;
    config.headlight_bindings = assets.headlight_bindings;
  }
  config.parallax_materials = assets.pom;
  // These explicit launch options own surface detail for this session. They
  // are not inferred from development environment variables.
  config.water_detail = assets.water_detail_explicit && assets.water_detail;
  config.cloud_detail = assets.cloud_detail_explicit && assets.cloud_detail;
  if (assets.environment) {
    std::fprintf(stderr,
                 "Environment renderer catalogs: %zu authored, %zu world\n",
                 assets.environment->authored_manifests.size(),
                 assets.environment->world_manifests.size());
    config.environment_authored_manifests =
        assets.environment->authored_manifests;
    config.environment_world_manifests = assets.environment->world_manifests;
  }
  config.dxgi_present = (backend != sdlfe::RendererBackend::core_critical_wsi);
  config.window_mode = "windowed";
  // Tinted world draws reuse mode.z for tint weight; keeping world scale at
  // 100% prevents them from entering coverage replay, where mode.z is alpha op.
  config.world_scale_percent = 100;
  config.remaster_width = 0;
  config.remaster_height = 0;
  config.vsync = true;
  config.temporal_inputs = false;
  config.gpu_models = (assets.geometry != "legacy");
  config.geometry = assets.geometry;
  config.render_thread = assets.render_thread;
  config.geometry_debug_normals = assets.geometry_debug_normals;

  // Quality
  if (!zcls::is_supported_view_distance(quality.draw_distance))
    throw std::runtime_error(
        "--cc-draw-distance supports only 800, 1200, 1600, 2400 or 3200");
  config.draw_distance = quality.draw_distance;
  config.antialiasing = quality.antialiasing;
  config.anisotropy = quality.anisotropy;
  if (quality.antialiasing == "fxaa") {
    config.fxaa = true;
    config.samples_x = 1;
    config.samples_y = 1;
  } else if (quality.antialiasing == "ssaa2") {
    config.fxaa = false;
    config.samples_x = 2;
    config.samples_y = 1;
  } else if (quality.antialiasing == "ssaa4") {
    config.fxaa = false;
    config.samples_x = 2;
    config.samples_y = 2;
  } else if (quality.antialiasing != "off") {
    throw std::runtime_error("--cc-aa supports off, fxaa, ssaa2 or ssaa4");
  }
  if (quality.anisotropy != "1" && quality.anisotropy != "2" &&
      quality.anisotropy != "4" && quality.anisotropy != "8" &&
      quality.anisotropy != "16") {
    throw std::runtime_error("--cc-af supports 1, 2, 4, 8 or 16");
  }
  config.af_level = unsigned(std::stoi(quality.anisotropy));

  // Lighting
  config.lighting = assets.lighting;
  if (assets.lighting != "off" && assets.lighting != "flat" &&
      assets.lighting != "normal")
    throw std::runtime_error("--cc-lighting supports off, flat or normal");
  auto number = [](const std::string &text, float low, float high) {
    char *end = nullptr;
    const float value = std::strtof(text.c_str(), &end);
    if (end == text.c_str() || *end || !std::isfinite(value) || value < low ||
        value > high)
      throw std::runtime_error(
          "Invalid --cc-sun angle (azimuth -360..360, elevation 1..89)");
    return value;
  };
  config.sun_azimuth = number(assets.sun_azimuth, -360.0f, 360.0f);
  config.sun_elevation = number(assets.sun_elevation, 1.0f, 89.0f);
  config.sun = assets.lighting != "off" || assets.geometry != "legacy";
  config.sun_normals = (assets.lighting == "normal");
  config.normal_maps_enabled = (assets.lighting == "normal");

  if (assets.lighting == "off" && config.sun_shadows) {
    std::fprintf(stderr,
                 "Sun shadows requested without sun lighting; sun shadows are disabled\n");
    config.sun_shadows = false;
  }

  if (!config.sun &&
      (config.effect_lights || config.fixture_lights || config.mech_headlights)) {
    std::fprintf(stderr,
                 "Dynamic lights requested without sun lighting; effect, "
                 "fixture, and mech headlights are disabled\n");
    config.effect_lights = false;
    config.effect_light_catalog.clear();
    config.fixture_lights = false;
    config.mech_headlights = false;
    config.stock_headlights.clear();
    config.headlight_bindings.clear();
  }

  // Other defaults
  config.fixture_shadows = false;
  config.fixture_atlas_reuse = true;
  config.fixture_atlas_tracked = false;
  config.fixture_atlas_audit = false;
  config.shadow_batch = false;

  return config;
}

std::unique_ptr<VulkanFrameRenderer>
make_renderer(SDL_Window *window, sdlfe::RendererBackend backend,
              const sdlfe::CoreCriticalQuality &quality,
              const sdlfe::CoreCriticalAssets &assets) {
  return std::make_unique<FrameRenderer>(window, backend, quality, assets);
}

namespace testing {
bool observe_producer_views(VulkanFrameRenderer& renderer, ProducerViewObserver* observer) {
    return renderer.observe_producer_views(observer);
}
std::unique_ptr<VulkanFrameRenderer> make_renderer_with_staging_budget(
    SDL_Window *window, sdlfe::RendererBackend backend, const sdlfe::CoreCriticalQuality &quality,
    const sdlfe::CoreCriticalAssets &assets, std::size_t local_staging_budget) {
    return std::make_unique<FrameRenderer>(window, backend, quality, assets, local_staging_budget);
}

testing::PacketByteBreakdown testing::packet_byte_breakdown(const mw34::vkscene::Scene &scene) {
    return FrameRenderer::packet_byte_breakdown_for_test(scene);
}
testing::StagingTestState testing::staging_state(VulkanFrameRenderer &renderer) {
    auto *typed = dynamic_cast<FrameRenderer *>(&renderer);
    if (!typed)
        throw std::runtime_error("Renderer is not a FrameRenderer");
    return typed->staging_state_for_test();
}

testing::NamedTextureTestState testing::named_texture_state(
    VulkanFrameRenderer &renderer, int32_t handle) {
    auto *typed = dynamic_cast<FrameRenderer *>(&renderer);
    if (!typed)
        throw std::runtime_error("Renderer is not a FrameRenderer");
    return typed->named_texture_state_for_test(handle);
}

struct RigidCaptureTestAccess {
    static FrameRenderer &impl(VulkanFrameRenderer &renderer) {
        auto *typed = dynamic_cast<FrameRenderer *>(&renderer);
        if (!typed)
            throw std::runtime_error("Renderer is not a FrameRenderer");
        return *typed;
    }
    static std::shared_ptr<const CapturedNativeRigid> capture(
        VulkanFrameRenderer &renderer, const zcls::Node &node,
        const ::platform::ModelDrawContext &context,
        const zmod::RigidGeometryEligibility &eligibility, std::size_t maximum_owned_bytes) {
        return impl(renderer).capture_original_rigid(
            node, context, eligibility, maximum_owned_bytes);
    }
    static bool validate(VulkanFrameRenderer &renderer, const CapturedNativeRigid &captured) {
        return impl(renderer).validate_captured_original_rigid(captured);
    }
    static std::vector<NativeGroundRangeAdmission> baseline_admissions(
        VulkanFrameRenderer &renderer,
        const std::shared_ptr<const cc::geometry::Resource> &resource,
        const ::platform::ModelDrawContext &context,
        const std::vector<cc::geometry::Material> &materials) {
        return impl(renderer).native_geometry_admissions(resource, context, materials);
    }
    static std::shared_ptr<mw34::materials::SurfaceDecodedBudget> surface_budget(
        VulkanFrameRenderer &renderer) {
        return impl(renderer).prepared_.surface_budget();
    }
    static void set_mission_and_environment(
        VulkanFrameRenderer &renderer, std::string mission_id,
        std::shared_ptr<const ::platform::prepared::EnvironmentSelection> environment) {
        auto &r = impl(renderer);
        r.current_mission_id_ = std::move(mission_id);
        r.environment_ = std::move(environment);
    }
    static void seed_authored_normal(VulkanFrameRenderer &renderer,
                                     const mw34::materials::SurfaceKey &key,
                                     mw34::materials::WorldNormalCache::TextureRecord record) {
        auto &r = impl(renderer);
        r.surface_normals_.loaded = true;
        const int idx = int(r.surface_normals_.cache.textures.size());
        r.surface_normals_.cache.textures.push_back(std::move(record));
        r.surface_normals_.cache.register_authored(key, idx);
    }
    static void seed_authored_no_normal(VulkanFrameRenderer &renderer,
                                        const mw34::materials::SurfaceKey &key) {
        auto &r = impl(renderer);
        r.surface_normals_.loaded = true;
        r.surface_normals_.cache.register_authored(key, -1);
    }
    static void mutate_normal_record(VulkanFrameRenderer &renderer, int index,
                                     std::uint32_t width, std::uint32_t height,
                                     std::uint64_t hash,
                                     std::vector<std::uint32_t> pixels) {
        auto &rec = impl(renderer).surface_normals_.cache.textures.at(std::size_t(index));
        rec.width = width;
        rec.height = height;
        rec.hash = hash;
        rec.pixels32 = std::move(pixels);
    }
    static void advance_group_epoch(VulkanFrameRenderer &renderer) {
        ++impl(renderer).group_load_epoch_;
    }
    static std::uint64_t group_epoch(const VulkanFrameRenderer &renderer) {
        return impl(const_cast<VulkanFrameRenderer &>(renderer)).group_load_epoch_;
    }
    static void set_slot_surface_key(VulkanFrameRenderer &renderer, int handle,
                                     const mw34::materials::SurfaceKey &key) {
        impl(renderer).textures_.at(std::size_t(handle)).surface_key = key;
    }
    static void set_slot_version(VulkanFrameRenderer &renderer, int handle,
                                 std::uint64_t version) {
        impl(renderer).textures_.at(std::size_t(handle)).version = version;
    }
    static void set_slot_group_epoch(VulkanFrameRenderer &renderer, int handle,
                                     std::uint64_t epoch) {
        impl(renderer).textures_.at(std::size_t(handle)).group_load_epoch = epoch;
    }
    static void set_slot_pixels(VulkanFrameRenderer &renderer, int handle,
                                unsigned width, unsigned height,
                                std::vector<std::uint32_t> pixels) {
        auto &slot = impl(renderer).textures_.at(std::size_t(handle));
        slot.width = width;
        slot.height = height;
        slot.pixels = std::move(pixels);
    }
};

std::shared_ptr<const CapturedNativeRigid> RigidCaptureTestHook::capture_original_rigid(
    VulkanFrameRenderer &renderer, const zcls::Node &node,
    const ::platform::ModelDrawContext &context, const zmod::RigidGeometryEligibility &eligibility,
    std::size_t maximum_owned_bytes) {
    return RigidCaptureTestAccess::capture(
        renderer, node, context, eligibility, maximum_owned_bytes);
}

bool RigidCaptureTestHook::validate_captured_original_rigid(
    VulkanFrameRenderer &renderer, const CapturedNativeRigid &captured) {
    return RigidCaptureTestAccess::validate(renderer, captured);
}

std::vector<NativeGroundRangeAdmission> RigidCaptureTestHook::native_geometry_admissions(
    VulkanFrameRenderer &renderer, const std::shared_ptr<const cc::geometry::Resource> &resource,
    const ::platform::ModelDrawContext &context,
    const std::vector<cc::geometry::Material> &materials) {
    return RigidCaptureTestAccess::baseline_admissions(renderer, resource, context, materials);
}

std::shared_ptr<mw34::materials::SurfaceDecodedBudget> RigidCaptureTestHook::surface_budget(
    VulkanFrameRenderer &renderer) {
    return RigidCaptureTestAccess::surface_budget(renderer);
}

void RigidCaptureTestHook::set_mission_and_environment(
    VulkanFrameRenderer &renderer, std::string mission_id,
    std::shared_ptr<const ::platform::prepared::EnvironmentSelection> environment) {
    RigidCaptureTestAccess::set_mission_and_environment(
        renderer, std::move(mission_id), std::move(environment));
}

void RigidCaptureTestHook::seed_authored_normal(
    VulkanFrameRenderer &renderer, const mw34::materials::SurfaceKey &key,
    mw34::materials::WorldNormalCache::TextureRecord record) {
    RigidCaptureTestAccess::seed_authored_normal(renderer, key, std::move(record));
}

void RigidCaptureTestHook::seed_authored_no_normal(
    VulkanFrameRenderer &renderer, const mw34::materials::SurfaceKey &key) {
    RigidCaptureTestAccess::seed_authored_no_normal(renderer, key);
}

void RigidCaptureTestHook::mutate_normal_record(
    VulkanFrameRenderer &renderer, int index, std::uint32_t width, std::uint32_t height,
    std::uint64_t hash, std::vector<std::uint32_t> pixels) {
    RigidCaptureTestAccess::mutate_normal_record(
        renderer, index, width, height, hash, std::move(pixels));
}

void RigidCaptureTestHook::advance_group_epoch(VulkanFrameRenderer &renderer) {
    RigidCaptureTestAccess::advance_group_epoch(renderer);
}

std::uint64_t RigidCaptureTestHook::group_epoch(const VulkanFrameRenderer &renderer) {
    return RigidCaptureTestAccess::group_epoch(renderer);
}

void RigidCaptureTestHook::set_slot_surface_key(
    VulkanFrameRenderer &renderer, int handle, const mw34::materials::SurfaceKey &key) {
    RigidCaptureTestAccess::set_slot_surface_key(renderer, handle, key);
}

void RigidCaptureTestHook::set_slot_version(
    VulkanFrameRenderer &renderer, int handle, std::uint64_t version) {
    RigidCaptureTestAccess::set_slot_version(renderer, handle, version);
}

void RigidCaptureTestHook::set_slot_group_epoch(
    VulkanFrameRenderer &renderer, int handle, std::uint64_t epoch) {
    RigidCaptureTestAccess::set_slot_group_epoch(renderer, handle, epoch);
}

void RigidCaptureTestHook::set_slot_pixels(
    VulkanFrameRenderer &renderer, int handle, unsigned width, unsigned height,
    std::vector<std::uint32_t> pixels) {
    RigidCaptureTestAccess::set_slot_pixels(renderer, handle, width, height, std::move(pixels));
}
} // namespace testing

} // namespace cc_mw3_re
