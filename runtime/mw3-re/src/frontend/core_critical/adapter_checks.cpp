#include "frame_renderer.hpp"
#include "prepared_models.hpp"

#include "frontend/sdl/sdl_child.h"
#include "frontend/sdl/sdl_platform.h"
#include "gamez/zclass/cls_data.h"
#include "gamez/zclass/camera.h"
#include "gamez/zclass/cls_world.h"
#include "gamez/zclass/cls_util.h"
#include "gamez/zclass/cls_zbd.h"
#include "gamez/zclass/light.h"
#include "gamez/zclass/list.h"
#include "gamez/zclass/object3d.h"
#include "mech3/mech.h"
#include "gamez/zmodel/gmod_init.h"
#include "gamez/zmodel/gmod_draw.h"
#include "gamez/zmodel/gmod_geometry.h"
#include "gamez/zmodel/gmod_light.h"
#include "gamez/zimage/zimg_texture.h"
#include "gamez/zmath/zmth_matrix.h"
#include "gamez/zmodel/gmod_const.h"
#include "gamez/zmodel/gmod_fog.h"
#include "gamez/zmodel/gmod_fogcalc.h"
#include "gamez/zutil/ztimer.h"
#include "gamez/zvideo/zvid_ddd3d.h"
#include "renderer/campaign_environment_policy.hpp"
#include "renderer/campaign_lighting.hpp"
#include "renderer/campaign_sun_settings.hpp"
#include "renderer/effect_light_observations.hpp"
#include "renderer/effect_lighting_stage.inc"
#include "renderer/material_normals.hpp"
#include "renderer/native_surface_identity.hpp"
#include "renderer/native_fixture_geometry.hpp"
#include "renderer/native_fixture_sources.hpp"
#include "renderer/surface_detail.hpp"
#include "renderer/surface_detail_bindings.hpp"
#include "renderer/surface_materials.hpp"
#include "renderer/vk_scene.hpp"
#include "renderer/flare_alpha.hpp"
#include "platform/sha256.hpp"
#include <sstream>
#include <limits>

namespace mw34::materials {
void set_active_surface_key(const SurfaceKey &key);
void clear_active_surface_key();
bool get_active_surface_key(SurfaceKey *out);
} // namespace mw34::materials
#include "tests/prepared_visual_fixture.h"
#include <cfenv>

#include <algorithm>
#include <array>
#include <atomic>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iterator>
#include <optional>
#include <random>
#include <stdexcept>
#include <string_view>

namespace cc_mw3_re::checks {
void check_scene_binding_slots();
}
// Win32 compatibility macros must not rewrite fixture variable names.
#ifdef near
#undef near
#endif
#ifdef far
#undef far
#endif

namespace {
bool threaded_checks = false;
std::unique_ptr<cc_mw3_re::VulkanFrameRenderer>
make_check_renderer(SDL_Window *window, sdlfe::RendererBackend backend,
                    const sdlfe::CoreCriticalQuality &quality = {},
                    sdlfe::CoreCriticalAssets assets = {},
                    std::optional<std::size_t> local_staging_budget = std::nullopt) {
    assets.render_thread = threaded_checks;
    if (local_staging_budget)
        return cc_mw3_re::testing::make_renderer_with_staging_budget(window, backend, quality,
                                                                     assets, *local_staging_budget);
    return cc_mw3_re::make_renderer(window, backend, quality, assets);
}

void require(bool condition, const char *message) {
  if (!condition) {
    throw std::runtime_error(message);
  }
}

#include "local_light_checks.inc"
#include "native_fixture_checks.inc"
#include "owned_rigid_capture_checks.inc"

void quad(platform::Render3D &renderer, float low, float high, float depth,
          uint32_t color, const platform::DrawState &state = {}) {
  const platform::TLVertex vertices[] = {{low, low, depth, 1, color, 0, 0, 0},
                                         {high, low, depth, 1, color, 0, 1, 0},
                                         {high, high, depth, 1, color, 0, 1, 1},
                                         {low, high, depth, 1, color, 0, 0, 1}};
  renderer.draw(platform::Primitive::kFan, vertices, 4, state);
}

#include "local_light_gpu_checks.inc"

void check_menu_background_gpu(SDL_Window *window, sdlfe::RendererBackend backend) {
  platform::MenuBackgroundImage image;
  image.width = image.height = 16;
  image.source_width = image.source_height = 8;
  image.rgb.resize(16 * 16 * 3);
  std::vector<uint32_t> hd_rgba(256);
  for (unsigned y = 0; y < 16; ++y) {
    for (unsigned x = 0; x < 16; ++x) {
      const size_t at = size_t(y) * 16 + x;
      const uint8_t red = uint8_t(30 + (x * 7 + y * 3) % 160);
      const uint8_t green = uint8_t(40 + (x * 3 + y * 9) % 150);
      const uint8_t blue = uint8_t(20 + (x * 5 + y * 5) % 170);
      image.rgb[at * 3] = red;
      image.rgb[at * 3 + 1] = green;
      image.rgb[at * 3 + 2] = blue;
      hd_rgba[at] = 0xff000000u | uint32_t(red) | uint32_t(green) << 8 | uint32_t(blue) << 16;
    }
  }
  // Integer and fractional output densities catch map filtering and half-texel
  // mistakes independently. Padding must never be interpreted as frame pixels.
  for (const auto size : {std::array<int, 2>{32, 32}, std::array<int, 2>{31, 27}}) {
    require(SDL_SetWindowSize(window, size[0], size[1]) && SDL_SyncWindow(window), SDL_GetError());
    auto renderer = make_check_renderer(window, backend);
    renderer->set_viewport(0, 0, 8, 8);
    const auto hd_texture = renderer->create_texture(16, 16,
        reinterpret_cast<const uint8_t*>(hd_rgba.data()), 1);
    require(hd_texture >= 0, "Could not upload synthetic HD menu background");
    // The real menu art both dims and brightens the background, and its added light can lower
    // red and blue. Each tint selects different map passes: 2/3 attenuation only, 3/2 one boost,
    // 7/3 both boosts (gain above 2), each with the same scroll wraps and overlay.
    struct Tint {
      int numerator, denominator;
      bool negative_added_light;
    };
    for (const Tint tint : {Tint{2, 3, false}, Tint{3, 2, true}, Tint{7, 3, true}}) {
    for (bool rgb565 : {true, false}) {
      for (int offset : {0, 7}) {
        constexpr int stride = 10;
        std::vector<uint16_t> source_pixels(8 * stride, 0xf81f);
        std::vector<uint16_t> frame(8 * stride, 0xf81f);
        const auto packed = [rgb565](int red, int green, int blue) {
          return uint16_t((red << (rgb565 ? 11 : 10)) | (green << 5) | blue);
        };
        // Brightened tints start darker so the tinted codes stay inside 5 (or 6) bits.
        const bool brighten = tint.numerator > tint.denominator;
        const int base_red = brighten ? 6 : 12, base_blue = brighten ? 6 : 12;
        const int base_green = brighten ? (rgb565 ? 12 : 6) : 20;
        for (int y = 0; y < 8; ++y)
          for (int x = 0; x < 8; ++x)
            source_pixels[size_t(y) * stride + x] =
                packed(base_red + x % 2, base_green + y % 3, base_blue + y % 2);
        const int offset_y = offset ? 6 : 0;
        for (int y = 0; y < 8; ++y) {
          for (int x = 0; x < 8; ++x) {
            const int sx = (x + offset) % 8, sy = (y + offset_y) % 8;
            frame[size_t(y) * stride + x] =
                packed((base_red + sx % 2) * tint.numerator / tint.denominator,
                       (base_green + sy % 3) * tint.numerator / tint.denominator,
                       (base_blue + sy % 2) * tint.numerator / tint.denominator);
          }
        }
        frame[0] = source_pixels[size_t(offset_y) * stride + offset];
        // A large green delta must be kind 2 rather than a uniformly tinted kind 1 pixel. This
        // also exercises saturation. With negative added light red and blue drop one code
        // (8.2 of 255, inside the classifier's -10 limit), which needs the subtract pass.
        const int glow_x = (1 + offset) % 8, glow_y = (1 + offset_y) % 8;
        const int glow_drop = tint.negative_added_light ? 1 : 0;
        frame[stride + 1] = packed(base_red + glow_x % 2 - glow_drop,
            base_green + glow_y % 3 + (rgb565 ? 24 : 10), base_blue + glow_y % 2 - glow_drop);
        frame[7 * stride + 7] = packed(31, 0, 31);
        zimg::Texture source{};
        source.width = source.height = 8;
        source.width_again = stride;
        source.pixels = source_pixels.data();
        std::vector<zrndr::MenuBackgroundBlit> blits;
        if (offset == 0) {
          blits = {{0, 0, 0, 0, 8, 8}};
        } else {
          blits = {{0, 0, 7, 6, 1, 2}, {1, 0, 0, 6, 7, 2},
                   {0, 2, 7, 0, 1, 6}, {1, 2, 0, 0, 7, 6}};
        }
        platform::PreparedMenuBackgroundComposer composer;
        platform::MenuBackgroundGpuLayers layers;
        require(composer.prepare_gpu(image, &source, blits, frame.data(), 8, 8, stride * 2,
                                     rgb565, &layers) &&
                    layers.status == platform::MenuBackgroundGpuStatus::kReady,
                "Synthetic GPU menu gain/glow/wrap fixture selected the fallback");
        require(layers.used[platform::kMenuGpuBoost] == brighten &&
                    layers.used[platform::kMenuGpuBoostHigh] == (tint.numerator > 2 * tint.denominator) &&
                    layers.used[platform::kMenuGpuSubtract] == tint.negative_added_light,
                "Synthetic GPU menu tint did not select the expected gain and added-light passes");
        sdlfe::MenuBackgroundGpuTextures maps{-1, -1, -1, -1, -1, -1};
        for (unsigned index = 0; index < platform::kMenuGpuMapCount; ++index) {
          if (!layers.used[index]) continue;
          maps[index] = renderer->create_texture(8, 8,
              reinterpret_cast<const uint8_t*>(layers.maps[index].data()), 1);
          require(maps[index] >= 0, "Could not upload synthetic menu maps");
        }
        renderer->clear(true, 0, 0, 0);
        sdlfe::draw_menu_background_gpu(*renderer, hd_texture, maps, layers, {0, 0, 8, 8});
        std::vector<uint32_t> gpu, cpu;
        int width = 0, height = 0;
        require(renderer->read_back(&gpu, &width, &height) && width == size[0] && height == size[1],
                "GPU menu readback lost output dimensions");
        require(platform::compose_menu_background(image, &source, blits, frame.data(), 8, 8,
                    stride * 2, rgb565, unsigned(width), unsigned(height), &cpu) && cpu.size() == gpu.size(),
                "CPU menu reference failed at the same output size");
        // CPU rounds the bilinear sample before gain; hardware rounds after
        // blending. Allow 4/255 per RGB channel for filtering precision, gain
        // UNORM quantization, delta rounding and render-target rounding.
        for (size_t at = 0; at < cpu.size(); ++at) {
          const uint32_t expected = (cpu[at] & 0xff00ff00u) |
              ((cpu[at] & 255u) << 16) | ((cpu[at] >> 16) & 255u);
          require((gpu[at] >> 24) == 255, "GPU menu lost opaque output alpha");
          for (unsigned shift : {0u, 8u, 16u})
            require(std::abs(int((gpu[at] >> shift) & 255u) - int((expected >> shift) & 255u)) <= 4,
                    "GPU/CPU menu pixel mismatch (gain, glow, native overlay or scroll wrap)");
        }
        if (size[0] == 31 && rgb565 && offset == 7 && !brighten) {
          auto flat_image = image;
          const std::vector<uint32_t> flat_rgba(256, 0xff208040u);
          for (size_t at = 0; at < 256; ++at) {
            flat_image.rgb[at * 3] = 64;
            flat_image.rgb[at * 3 + 1] = 128;
            flat_image.rgb[at * 3 + 2] = 32;
          }
          const int32_t flat_texture = renderer->create_texture(16, 16,
              reinterpret_cast<const uint8_t*>(flat_rgba.data()), 1);
          require(flat_texture >= 0, "Could not upload flat menu coverage fixture");
          // Original 1:1 frame aspect fits into 31x27 as a 27x27 rectangle.
          // Only the background extends into the two columns on either side.
          const platform::MenuBackgroundLayerRect fitted{2.f * 8 / 31, 0, 27.f * 8 / 31, 8};
          const platform::MenuBackgroundLayerRect covered{0, -2.f * 8 / 27, 8, 31.f * 8 / 27};
          renderer->clear(true, 0, 0, 0);
          sdlfe::draw_menu_background_gpu(*renderer, flat_texture, maps, layers, fitted, &covered);
          require(renderer->read_back(&gpu, &width, &height) && width == 31 && height == 27,
                  "Cover extension changed output dimensions");
          require(platform::compose_menu_background(flat_image, &source, blits, frame.data(),
                      8, 8, stride * 2, true, 27, 27, &cpu),
                  "CPU menu reference failed at the fitted output size");
          for (int y = 0; y < 27; ++y) {
            for (int x = 0; x < 31; ++x) {
              const uint32_t pixel = gpu[size_t(y) * 31 + x];
              if (x < 2 || x >= 29) {
                require(pixel == 0xff408020u, "Cover extension left a pillar or drew native artwork in it");
              } else {
                const uint32_t reference = cpu[size_t(y) * 27 + x - 2];
                const uint32_t expected = (reference & 0xff00ff00u) |
                    ((reference & 255u) << 16) | ((reference >> 16) & 255u);
                for (unsigned shift : {0u, 8u, 16u})
                  require(std::abs(int((pixel >> shift) & 255u) - int((expected >> shift) & 255u)) <= 4,
                          "Menu cover moved native artwork, lighting or control pixel correspondence");
              }
            }
          }
          renderer->release_texture(flat_texture);
        }
        for (int32_t map : maps)
          if (map >= 0) renderer->release_texture(map);
      }
    }
    }
    renderer->release_texture(hd_texture);
  }
  require(SDL_SetWindowSize(window, 32, 32) && SDL_SyncWindow(window), SDL_GetError());
}

void check_scene(SDL_Window *window, sdlfe::RendererBackend backend) {
  auto renderer = make_check_renderer(window, backend);
  renderer->set_viewport(0, 0, 32, 32);
  renderer->clear(true, 0, 0, 255);
  renderer->begin_scene();
  quad(*renderer, 8, 24, .75f, 0xff00ff00);
  quad(*renderer, 4, 28, .25f, 0xffff0000);
  renderer->end_scene();
  auto pixel = [&](int x, int y) {
    std::vector<uint32_t> pixels;
    int width = 0, height = 0;
    require(renderer->read_back(&pixels, &width, &height) && width == 32 &&
                height == 32,
            "Could not read the Vulkan scene");
    return pixels.at(y * width + x);
  };
  require(pixel(16, 16) == 0xff00ff00 && pixel(6, 6) == 0xffff0000 &&
              pixel(2, 2) == 0xff0000ff,
          "Draw order or reversed depth changed");

  require(renderer->hold_frame(), "Could not hold the composed frame");
  renderer->clear(false, 0, 0, 0);
  const uint8_t yellow[] = {255, 255, 0, 255};
  const uint8_t cyan[] = {0, 255, 255, 255};
  const auto first = renderer->create_texture(1, 1, yellow, 1);
  platform::DrawState textured{};
  textured.texture = first;
  quad(*renderer, 12, 20, .125f, 0xffffffff, textured);
  renderer->release_texture(first);
  require(pixel(16, 16) == 0xffffff00 && pixel(6, 6) == 0xffff0000,
          "Depth-only clear changed color or a released texture lost its "
          "queued draw");
  textured.texture = renderer->create_texture(1, 1, cyan, 1);
  quad(*renderer, 12, 20, .5f, 0xffffffff, textured);
  renderer->release_texture(textured.texture);
  require(pixel(16, 16) == 0xff00ffff, "Reused slot kept stale texture pixels");
  require(renderer->restore_frame() && pixel(16, 16) == 0xff00ff00,
          "Restored frame lost its saved pixels");
  renderer->drop_frame();

  renderer->reset_scene_resources();
  renderer->clear(true, 0, 0, 0);
  textured.texture = renderer->create_texture(1, 1, cyan, 1);
  quad(*renderer, 12, 20, .5f, 0xffffffff, textured);
  renderer->release_texture(textured.texture);
  require(pixel(16, 16) == 0xff00ffff && pixel(6, 6) == 0xff000000,
          "A new scene inherited the previous color or texture");

  renderer->clear(true, 0, 0, 255);
  const uint8_t premultiplied_red[] = {128, 0, 0, 128};
  platform::DrawState hud{};
  hud.texture = renderer->create_texture(1, 1, premultiplied_red, 4);
  hud.address_u = hud.address_v = 3;
  hud.sharp = hud.blend = hud.depth_always = true;
  hud.depth_write = false;
  quad(*renderer, 0, 32, 0, 0xffffffff, hud);
  renderer->release_texture(hud.texture);
  require(pixel(16, 16) == 0xff80007f,
          "The sharp HUD layer lost its premultiplied color or alpha");

  // A cropped 4x1 resource drawn over 13x32 pixels has different X/Y
  // densities. A full-resource/window ratio incorrectly blurs this edge.
  const uint8_t cropped[] = {0, 255, 0, 255, 128, 0,   0, 128,
                             0, 0,   0, 0,   0,   255, 0, 255};
  hud.texture = renderer->create_texture(4, 1, cropped, 4);
  const platform::TLVertex sprite[] = {
      {.25f, 0, 0, 1, 0xffffffff, 0, .25f, 0},
      {13.25f, 0, 0, 1, 0xffffffff, 0, .75f, 0},
      {13.25f, 32, 0, 1, 0xffffffff, 0, .75f, 1},
      {.25f, 32, 0, 1, 0xffffffff, 0, .25f, 1}};
  renderer->clear(true, 0, 0, 255);
  renderer->draw(platform::Primitive::kFan, sprite, 4, hud);
  renderer->release_texture(hud.texture);
  require(pixel(5, 16) == 0xff80007f && pixel(6, 16) == 0xff60009f &&
              pixel(8, 16) == 0xff0000ff,
          "Sharp sprite density, crop or transparent-edge color changed");

  renderer->clear(true, 200, 100, 50);
  const uint8_t shadow_color[] = {128, 255, 128, 128};
  platform::DrawState shadow{};
  shadow.texture = renderer->create_texture(1, 1, shadow_color, 4);
  shadow.multiply = true;
  quad(*renderer, 0, 32, .5f, 0xffffffff, shadow);
  renderer->release_texture(shadow.texture);
  require(pixel(16, 16) == 0xff646419,
          "The multiply blend changed stock color or alpha");

  // Vary reciprocal W so a screen-linear shader would give a different sample.
  platform::TLVertex triangle[] = {{0, 0, .5f, 1, 0xffff0000, 0xff000000, 0, 0},
                                   {32, 0, .5f, .25f, 0xff0000ff, 0, 0, 0},
                                   {0, 32, .5f, .25f, 0xff0000ff, 0, 0, 0}};
  renderer->clear(true, 0, 0, 0);
  renderer->draw(platform::Primitive::kFan, triangle, 3, {});
  require(pixel(8, 8) == 0xffc70038,
          "Diffuse interpolation lost perspective correction");
  for (auto &vertex : triangle)
    vertex.diffuse = 0xffffffff;
  renderer->clear(true, 0, 0, 0);
  platform::DrawState fogged{};
  fogged.fog = true;
  renderer->set_fog_color(0, 0, 0);
  renderer->draw(platform::Primitive::kFan, triangle, 3, fogged);
  require(pixel(8, 8) == 0xffc7c7c7,
          "Fog interpolation lost perspective correction");

  const auto ready =
      "cc-adapter-ready-" + std::to_string(SDL_GetPerformanceCounter());
  require(!std::filesystem::exists(ready), "Ready marker path already exists");
  sdlfe::set_ready_file(ready);
  renderer->present();
  sdlfe::set_ready_file("");
  require(!std::filesystem::remove(ready),
          "A hidden frame signaled first presentation");
  require(renderer->presentation_count() == 0,
          "A hidden frame counted as a presentation");

  if (backend == sdlfe::RendererBackend::core_critical_wsi) {
    require(SDL_ShowWindow(window) && SDL_SyncWindow(window), SDL_GetError());
    require(SDL_MinimizeWindow(window) && SDL_SyncWindow(window),
            SDL_GetError());
    SDL_PumpEvents();
    require((SDL_GetWindowFlags(window) & SDL_WINDOW_MINIMIZED) != 0,
            "The test window did not minimize");
    sdlfe::set_ready_file(ready);
    renderer->present();
    require(!std::filesystem::exists(ready),
            "A minimized frame signaled first presentation");
    require(renderer->presentation_count() == 0,
            "A minimized frame counted as a presentation");
    require(SDL_RestoreWindow(window) && SDL_SyncWindow(window),
            SDL_GetError());
    for (int i = 0; i < 30 && !std::filesystem::exists(ready); ++i) {
      SDL_PumpEvents();
      renderer->present();
      SDL_Delay(10);
    }
    sdlfe::set_ready_file("");
    require(std::filesystem::remove(ready),
            "A restored Vulkan window did not present");
    require(renderer->presentation_count() > 0,
            "A restored frame did not count as a presentation");
    for (int size : {64, 48, 32}) {
      require(SDL_SetWindowSize(window, size, size) && SDL_SyncWindow(window),
              SDL_GetError());
      SDL_PumpEvents();
      const auto before = renderer->presentation_count();
      // Allow transient OUT_OF_DATE results while the window changes size.
      for (int i = 0; i < 30 && renderer->presentation_count() == before; ++i) {
        renderer->present();
        SDL_PumpEvents();
        SDL_Delay(10);
      }
      require(renderer->presentation_count() > before,
              "A resized Vulkan window did not complete a presentation");
    }
    require(pixel(8, 8) == 0xffc7c7c7,
            "Swapchain resizing changed the resident scene");
  }
}

void check_fullscreen_resize(SDL_Window *window,
                             sdlfe::RendererBackend backend) {
  auto renderer = make_check_renderer(window, backend);
  require(SDL_ShowWindow(window) && SDL_SyncWindow(window), SDL_GetError());

  // Draws a scene at the window's current size and waits until it is
  // presented, so each stage rebuilds the frame targets for the new extent
  // as well as the presentation target.
  auto draw_and_present = [&](const char *stage) {
    int width = 0, height = 0;
    SDL_GetWindowSizeInPixels(window, &width, &height);
    renderer->set_viewport(0, 0, width, height);
    renderer->clear(true, 0, 0, 0);
    renderer->begin_scene();
    quad(*renderer, 0, 32, .5f, 0xff204080);
    renderer->end_scene();
    const auto before = renderer->presentation_count();
    for (int attempt = 0;
         attempt < 30 && renderer->presentation_count() == before; ++attempt) {
      SDL_PumpEvents();
      renderer->present();
      SDL_Delay(10);
    }
    require(renderer->presentation_count() > before, stage);
  };

  // A windowed frame first, so the fullscreen switch resizes a presentation
  // target that is already bound rather than creating the first one.
  draw_and_present("The windowed Vulkan presentation target did not present");

  // Match SdlWindow::switch_fullscreen: finish renderer work before SDL can
  // synchronously resize the window and its Vulkan/DXGI presentation target.
  renderer->drain();
  require(SDL_SetWindowFullscreen(window, true) && SDL_SyncWindow(window),
          SDL_GetError());
  SDL_PumpEvents();
  int fullscreen_width = 0, fullscreen_height = 0;
  SDL_GetWindowSizeInPixels(window, &fullscreen_width, &fullscreen_height);
  require((SDL_GetWindowFlags(window) & SDL_WINDOW_FULLSCREEN) != 0 &&
              fullscreen_width > 64 && fullscreen_height > 48,
          "The fullscreen fixture did not reach a desktop-sized drawable");
  draw_and_present("The fullscreen Vulkan presentation target did not present");

  renderer->drain();
  require(SDL_SetWindowFullscreen(window, false) &&
              SDL_SetWindowSize(window, 64, 48) && SDL_SyncWindow(window),
          SDL_GetError());
  SDL_PumpEvents();
  require((SDL_GetWindowFlags(window) & SDL_WINDOW_FULLSCREEN) == 0,
          "The fullscreen fixture did not return to windowed mode");
  draw_and_present("The restored window's Vulkan presentation target did not present");
}

} // namespace

namespace {
void check_quality(SDL_Window *window, sdlfe::RendererBackend backend,
                   const sdlfe::CoreCriticalQuality &quality) {
  require(SDL_SetWindowSize(window, 64, 64) && SDL_SyncWindow(window),
          SDL_GetError());
  for (const auto invalid : {sdlfe::CoreCriticalQuality{"smaa", "1"},
                             sdlfe::CoreCriticalQuality{"fsr4", "1"},
                             sdlfe::CoreCriticalQuality{"off", "0"},
                             sdlfe::CoreCriticalQuality{"off", "3"},
                             sdlfe::CoreCriticalQuality{"off", "16junk"}}) {
    bool rejected = false;
    try {
      auto unsupported = make_check_renderer(window, backend, invalid);
    } catch (const std::exception &error) {
      rejected = std::string_view(error.what()).find("--cc-") == 0;
    }
    require(rejected, "An unsupported quality request was silently accepted");
  }
  auto original = make_check_renderer(window, backend);
  original->set_viewport(0, 0, 64, 64);
  original->clear(true, 0, 0, 0);
  std::vector<uint32_t> original_pixels;
  int original_width = 0, original_height = 0;
  require(
      original->read_back(&original_pixels, &original_width, &original_height),
      "The original-quality renderer did not initialize");
  auto renderer = make_check_renderer(window, backend, quality);
  renderer->set_viewport(0, 0, 64, 64);
  renderer->clear(true, 0, 0, 0);
  std::vector<uint8_t> checker(64 * 64 * 4, 255);
  for (int y = 0; y < 64; ++y)
    for (int x = 0; x < 64; ++x)
      for (int channel = 0; channel < 3; ++channel)
        checker[(y * 64 + x) * 4 + channel] = ((x + y) & 1) ? 255 : 0;
  platform::DrawState filtered{};
  filtered.texture = renderer->create_texture(64, 64, checker.data(), 1);
  const platform::TLVertex tiled[] = {{0, 0, .5f, 1, 0xffffffff, 0, 0, 0},
                                      {64, 0, .5f, 1, 0xffffffff, 0, 16, 0},
                                      {64, 64, .5f, 1, 0xffffffff, 0, 16, 16},
                                      {0, 64, .5f, 1, 0xffffffff, 0, 0, 16}};
  renderer->draw(platform::Primitive::kFan, tiled, 4, filtered);
  renderer->release_texture(filtered.texture);
  std::vector<uint32_t> pixels;
  int width = 0, height = 0;
  require(renderer->read_back(&pixels, &width, &height) && width == 64 &&
              height == 64,
          "Quality readback changed game-facing output dimensions");
  if (quality.anisotropy != "1") {
    const auto value = pixels[32 * 64 + 32] & 255U;
    require(value >= 120 && value <= 135,
            "AF failed to filter the minified checker texture");
    const auto stats = renderer->quality_statistics();
    require(
        stats.anisotropic_samplers > 0 && stats.mip_levels >= 6,
        "World filtering did not create anisotropic samplers and mip levels");
  }

  renderer->clear(true, 0, 0, 0);
  const platform::TLVertex diagonal[] = {{33, 1, .5f, 1, 0xffffffff, 0, 0, 0},
                                         {63, 56, .5f, 1, 0xffffffff, 0, 0, 0},
                                         {33, 63, .5f, 1, 0xffffffff, 0, 0, 0}};
  renderer->draw(platform::Primitive::kFan, diagonal, 3, {});
  renderer->end_scene();
  // A rasterized opaque glyph over the left half must stay byte-exact after AA.
  std::vector<uint8_t> glyph(64 * 64 * 4);
  for (int y = 0; y < 64; ++y)
    for (int x = 0; x < 32; ++x) {
      glyph[(y * 64 + x) * 4 + 1] = x + y / 2 < 28 ? 255 : 0;
      glyph[(y * 64 + x) * 4 + 3] = 255;
    }
  platform::DrawState hud{};
  hud.texture = renderer->create_texture(64, 64, glyph.data(), 4);
  hud.sharp = hud.blend = hud.depth_always = true;
  hud.depth_write = false;
  hud.address_u = hud.address_v = 3;
  quad(*renderer, 0, 64, 0, 0xffffffff, hud);
  renderer->release_texture(hud.texture);
  require(renderer->read_back(&pixels, &width, &height),
          "Quality frame did not read back");
  unsigned intermediate = 0;
  for (int y = 0; y < 64; ++y)
    for (int x = 0; x < 64; ++x) {
      const auto pixel = pixels[y * 64 + x];
      if (x < 32)
        require(pixel == (x + y / 2 < 28 ? 0xff00ff00U : 0xff000000U),
                "World antialiasing changed sharp HUD pixels");
      else if ((pixel & 255U) > 0 && (pixel & 255U) < 255)
        ++intermediate;
    }
  if (quality.antialiasing != "off")
    require(intermediate > 0,
            "World antialiasing did not smooth the authored diagonal");
  if (quality.antialiasing == "fxaa")
    require(renderer->quality_statistics().fxaa_passes >= 2,
            "World FXAA pass did not execute");
  original->clear(true, 1, 2, 3);
  require(
      original->read_back(&original_pixels, &original_width,
                          &original_height) &&
          original_width == 64 && original_height == 64 &&
          original_pixels[0] == 0xff010203,
      "Another renderer's quality changed the original renderer's readback");
  require(original->quality_statistics().fxaa_passes == 0 &&
              original->quality_statistics().anisotropic_samplers == 0,
          "Quality settings leaked between renderer instances");
  original.reset();
  require(renderer->hold_frame(), "Could not hold an antialiased frame");
  renderer->clear(true, 0, 0, 0);
  require(renderer->restore_frame(), "Could not restore an antialiased frame");
  std::vector<uint32_t> restored;
  require(renderer->read_back(&restored, &width, &height) && pixels == restored,
          "Held quality frame did not preserve its resolved pixels");
  const auto hud_passes = renderer->quality_statistics().fxaa_passes;
  renderer->clear_depth_rect(0, 0, 16, 16);
  renderer->end_scene();
  require(
      renderer->read_back(&restored, &width, &height) && pixels == restored &&
          renderer->quality_statistics().fxaa_passes == hud_passes,
      "A depth-only batch after HUD composition dirtied or filtered its color");
  for (const uint8_t alpha : {uint8_t(128), uint8_t(0)}) {
    const uint8_t translucent[] = {64, 32, 16, alpha};
    platform::DrawState straight{};
    straight.texture = renderer->create_texture(1, 1, translucent, 4);
    renderer->clear(true, 0, 0, 0);
    quad(*renderer, 0, 64, .5f, 0xffffffff, straight);
    renderer->release_texture(straight.texture);
    require(renderer->read_back(&restored, &width, &height) &&
                restored[32 * 64 + 32] == (uint32_t(alpha) << 24 | 0x00402010U),
            "The straight-alpha held-frame input was not preserved");
    require(renderer->hold_frame(), "Could not hold straight-alpha pixels");
    renderer->clear(true, 0, 0, 0);
    require(renderer->restore_frame(),
            "Could not restore straight-alpha pixels");
    std::vector<uint32_t> copied;
    require(renderer->read_back(&copied, &width, &height) && copied == restored,
            "Held-frame restore changed straight-alpha or alpha-zero RGB");
  }

  auto depth_clear_case = [&](bool clear_depth) {
    const auto before = renderer->quality_statistics().fxaa_passes;
    renderer->clear(true, 0, 0, 0);
    renderer->draw(platform::Primitive::kFan, diagonal, 3, {});
    renderer->end_scene();
    if (clear_depth)
      renderer->clear_depth_rect(0, 0, 16, 16);
    quad(*renderer, 0, 4, .5f, 0xff000000);
    std::vector<uint32_t> result;
    require(renderer->read_back(&result, &width, &height),
            "Depth-clear frame did not read back");
    if (quality.antialiasing == "fxaa")
      require(renderer->quality_statistics().fxaa_passes - before == 1,
              "A depth-only clear triggered extra world FXAA");
    return result;
  };
  const auto without_depth_clear = depth_clear_case(false);
  require(depth_clear_case(true) == without_depth_clear,
          "A depth-only rectangle clear changed unaffected color pixels");
  const auto previous_stats = renderer->quality_statistics();
  renderer->reset_scene_resources();
  renderer->clear(true, 10, 20, 30);
  require(renderer->read_back(&restored, &width, &height) &&
              restored[0] == 0xff0a141e,
          "A quality scene reload retained old pixels");
  require(renderer->quality_statistics().fxaa_passes >=
              previous_stats.fxaa_passes,
          "Quality counters were lost during scene reload");
  require(SDL_ShowWindow(window) && SDL_SyncWindow(window), SDL_GetError());
  for (const auto size : {std::array{64, 64}, std::array{48, 72}}) {
    require(SDL_SetWindowSize(window, size[0], size[1]) &&
                SDL_SyncWindow(window),
            SDL_GetError());
    SDL_PumpEvents();
    renderer->clear(true, 10, 20, 30);
    const auto before = renderer->presentation_count();
    for (int i = 0; i < 30 && renderer->presentation_count() == before; ++i) {
      renderer->present();
      SDL_PumpEvents();
      SDL_Delay(10);
    }
    require(renderer->presentation_count() > before,
            "Quality presentation did not survive resize");
    require(renderer->read_back(&restored, &width, &height) &&
                width == size[0] && height == size[1],
            "Quality resize changed game-facing readback dimensions");
  }
}
} // namespace

namespace {
std::string surface_metadata(const char *asset, const char *material,
                             uint64_t mesh_hash, float roughness = .7f,
                             float reflectivity = .04f, float metallic = 0.f,
                             bool bound = true) {
  prepared_fixture::Bytes metadata;
  metadata.value.assign("BWSFM1", 6);
  metadata.value.append(2, char(0));
  metadata.u32(1);
  metadata.u32(1);
  metadata.u32(1);
  metadata.u32(0);
  metadata.u64(mesh_hash);
  metadata.u32(bound ? 0 : mw34::materials::no_surface_material);
  auto text = [&](const char *value) {
    metadata.u32(uint32_t(std::strlen(value)));
    metadata.value += value;
  };
  text(asset);
  text(material);
  metadata.u32(0xffffffffU);
  metadata.u32(0xffffffffU);
  metadata.f32(0);
  metadata.f32(0);
  metadata.f32(0);
  metadata.u32(1);
  metadata.f32(1);
  metadata.f32(1);
  metadata.f32(0);
  metadata.f32(0);
  metadata.u32(1);
  metadata.u32(1);
  metadata.f32(0);
  metadata.f32(0);
  metadata.f32(1);
  metadata.f32(1);
  metadata.f32(0);
  metadata.f32(1);
  metadata.f32(1);
  metadata.f32(1);
  metadata.f32(0);
  metadata.f32(0);
  metadata.f32(roughness);
  metadata.f32(reflectivity);
  metadata.f32(metallic);
  return metadata.value;
}

void check_terrain_surface_normals(SDL_Window *window,
                                   sdlfe::RendererBackend backend) {
  const auto folder = std::filesystem::temp_directory_path() /
                      ("cc-terrain-normal-check-" +
                       std::to_string(SDL_GetPerformanceCounter()));
  require(std::filesystem::create_directory(folder),
          "Terrain normal fixture directory already exists");
  struct Files {
    std::filesystem::path folder;
    ~Files() {
      std::error_code error;
      std::filesystem::remove_all(folder, error);
#if defined(_WIN32)
      _putenv_s("MW34_WORLD_NORMALS", "");
#else
      unsetenv("MW34_WORLD_NORMALS");
#endif
    }
  } files{folder};

  // Model fixture so PreparedModels admits per-pixel lighting
  std::ofstream(folder / "mesh.bin", std::ios::binary)
      << prepared_fixture::mesh(2, 0xffff0000);
  std::ofstream(folder / "textures.bin", std::ios::binary)
      << prepared_fixture::textures();
  std::ofstream(folder / "normals.bin", std::ios::binary)
      << prepared_fixture::normals(0xffd980d9);

  // Primary t1m1 ground terrain tile SurfaceKey: ggter1, 128x128, format 1
  // (RGB565), hash 0x6335d0d1f5c866
  const mw34::materials::SurfaceKey t1m1_terrain_key{128, 128, 1,
                                                     0x6335d0d1f5c866ULL};
  const auto page_path = folder / "page-0.bin";
  const auto world_path = folder / "world.txt";

  // Build valid BWSNR2 page containing t1m1_terrain_key and non-neutral normal
  // (0xffd980d9)
  {
    prepared_fixture::Bytes out;
    out.value.assign("BWSNR2\0\0", 8);
    out.u32(1); // 1 key
    out.u32(t1m1_terrain_key.width);
    out.u32(t1m1_terrain_key.height);
    out.u32(t1m1_terrain_key.format);
    out.u32(uint32_t(t1m1_terrain_key.hash & 0xffffffff));
    out.u32(uint32_t(t1m1_terrain_key.hash >> 32));
    out.name("terrain0");

    out.value.append("BWNRM2\0\0", 8);
    out.u32(1); // batches
    out.u32(1); // images count
    out.u32(0); // binding: batch 0 -> image 0
    out.name("terrain0");
    out.u32(1); // width 1
    out.u32(1); // height 1
    uint64_t hash = 0xcbf29ce484222325ULL;
    const uint32_t normal_pixel = 0xffd980d9;
    for (unsigned shift = 0; shift < 32; shift += 8) {
      hash ^= uint8_t(normal_pixel >> shift);
      hash *= 0x100000001b3ULL;
    }
    out.u64(hash);
    out.u32(normal_pixel);

    std::ofstream pf(page_path, std::ios::binary);
    pf.write(out.value.data(), out.value.size());
  }

  // Build manifest
  {
    std::ofstream wf(world_path);
    wf << "MW34SNP1\npage-0.bin\n";
  }

#if defined(_WIN32)
  _putenv_s("MW34_WORLD_NORMALS", world_path.string().c_str());
#else
  setenv("MW34_WORLD_NORMALS", world_path.string().c_str(), 1);
#endif

  sdlfe::CoreCriticalAssets options;
  options.textures = (folder / "textures.bin").u8string();
  options.models.push_back(
      {"authored", "0", (folder / "mesh.bin").u8string(), options.textures});
  options.normals.push_back(
      {"authored", "0", (folder / "normals.bin").u8string()});
  options.lighting = "normal";
  // The screen-aligned fixture faces -Z. Light that face so perturbations
  // affect direct illumination rather than comparing two ambient-only images.
  options.sun_azimuth = "-90";

  auto renderer = make_check_renderer(window, backend, {}, options);
  require(renderer->asset_statistics().world_normal_decoded_bytes == 0,
          "World pages decoded before first material lookup");
#if defined(_WIN32)
  _putenv_s("MW34_WORLD_NORMALS", (folder / "missing.txt").string().c_str());
#else
  setenv("MW34_WORLD_NORMALS", (folder / "missing.txt").string().c_str(), 1);
#endif
  renderer->set_viewport(0, 0, 64, 64);
  renderer->clear(true, 0, 0, 0);

  // Producer active surface key channel
  mw34::materials::set_active_surface_key(t1m1_terrain_key);
  std::vector<uint8_t> green_data(128 * 128 * 4);
  for (size_t i = 0; i < 128 * 128; ++i) {
    green_data[i * 4 + 0] = 34;
    green_data[i * 4 + 1] = 139;
    green_data[i * 4 + 2] = 34;
    green_data[i * 4 + 3] = 255;
  }
  const auto tex =
      renderer->create_named_texture("ggter1", 128, 128, green_data.data(), 1);
  mw34::materials::clear_active_surface_key();
  require(renderer->asset_statistics().world_normal_decoded_bytes == 4 &&
              renderer->asset_statistics().world_normal_peak_decoded_bytes == 4 &&
              renderer->asset_statistics().world_normal_loaded_pages == 1,
          "Authenticated texture admission did not preload its matching world normal page");

  // Preload matching GPU normal textures at the post-load mission callback
  // boundary (empty MissionIdentity covers Instant Action as well) before the
  // first draw without altering decoded bytes, normal binding, or output pixels.
  renderer->mission_changed(platform::MissionIdentity{});
  require(renderer->asset_statistics().world_normal_decoded_bytes == 4 &&
              renderer->asset_statistics().world_normal_peak_decoded_bytes == 4 &&
              renderer->asset_statistics().world_normal_loaded_pages == 1,
          "Mission normal GPU preload altered world normal cache accounting");
  renderer->clear(true, 0, 0, 0);

  platform::DrawState state{};
  state.texture = tex;
  quad(*renderer, 0, 64, .5f, 0xffffffff, state);
  std::vector<uint32_t> pixels;
  int width = 0, height = 0;
  require(renderer->read_back(&pixels, &width, &height),
          "Could not read back terrain normal frame");

  const auto normal_pixels = pixels;
  auto stats = renderer->asset_statistics();
  require(stats.normal_draws > 0, "Terrain surface normal binding test failed "
                                  "with 0 matched normal bindings");
  require(stats.world_normal_decoded_bytes == 4 &&
              stats.world_normal_peak_decoded_bytes == 4 &&
              stats.world_normal_loaded_pages == 1,
          "World page decoded-byte/loaded-page accounting is incorrect");

  // Test3: reject stale bindings on same-handle texture updates
  const auto base_draws = stats.normal_draws;
  require(base_draws > 0, "base normal_draws > 0");
  const auto saved_green = green_data;
  green_data[0] ^= 0xFF;
  green_data[1] ^= 0xFF;
  green_data[2] ^= 0xFF; // edited RGBA
  auto bad_key = t1m1_terrain_key;
  bad_key.hash ^= 1;
  mw34::materials::set_active_surface_key(bad_key);
  renderer->update_texture(tex, 128, 128, green_data.data());
  mw34::materials::clear_active_surface_key();
  renderer->clear(true, 0, 0, 0);
  quad(*renderer, 0, 64, .5f, 0xffffffff, state);
  require(renderer->read_back(&pixels, &width, &height),
          "Could not read back updated surface");
  require(renderer->asset_statistics().normal_draws == base_draws,
          "altered-key same-handle update rejected");
  mw34::materials::clear_active_surface_key();
  renderer->update_texture(tex, 128, 128, green_data.data());
  mw34::materials::clear_active_surface_key();
  renderer->clear(true, 0, 0, 0);
  quad(*renderer, 0, 64, .5f, 0xffffffff, state);
  require(renderer->read_back(&pixels, &width, &height),
          "Could not read back updated surface");
  require(renderer->asset_statistics().normal_draws == base_draws,
          "unauthenticated update rejected");
  green_data = saved_green; // restore original RGBA
  mw34::materials::set_active_surface_key(t1m1_terrain_key);
  renderer->update_texture(tex, 128, 128, green_data.data());
  mw34::materials::clear_active_surface_key();
  renderer->clear(true, 0, 0, 0);
  quad(*renderer, 0, 64, .5f, 0xffffffff, state);
  require(renderer->read_back(&pixels, &width, &height),
          "Could not read back updated surface");
  require(renderer->asset_statistics().normal_draws > base_draws,
          "authenticated update accepted");
  require(pixels == normal_pixels, "pixels equal normal_pixels");

  stats = renderer->asset_statistics();

  // Verify reset_scene_resources invalidates epoch and stale texture slot
  // bindings
  renderer->reset_scene_resources();
  require(renderer->asset_statistics().world_normal_decoded_bytes == 0 &&
              renderer->asset_statistics().world_normal_loaded_pages == 0,
          "Scene reset retained decoded world pages");
  renderer->clear(true, 0, 0, 0);
  quad(*renderer, 0, 64, .5f, 0xffffffff, state);
  require(renderer->read_back(&pixels, &width, &height),
          "Could not read back after reset_scene_resources");
  require(renderer->asset_statistics().normal_draws == stats.normal_draws,
          "Scene reset reused a stale surface normal binding");
  require(renderer->asset_statistics().world_normal_decoded_bytes == 0,
          "Stale texture caused a world-page decode after reset");

  // Recreated native textures must acquire the new epoch and reload the
  // catalog.
  mw34::materials::set_active_surface_key(t1m1_terrain_key);
  state.texture =
      renderer->create_named_texture("ggter1", 128, 128, green_data.data(), 1);
  mw34::materials::clear_active_surface_key();
  renderer->mission_changed(platform::MissionIdentity{});
  renderer->clear(true, 0, 0, 0);
  quad(*renderer, 0, 64, .5f, 0xffffffff, state);
  require(renderer->read_back(&pixels, &width, &height) &&
              pixels == normal_pixels &&
              renderer->asset_statistics().normal_draws > stats.normal_draws &&
              renderer->asset_statistics().world_normal_decoded_bytes == 4,
          "New-epoch texture did not reload its world normal page");

  {
    bool rejected = false;
    try {
      auto missing_renderer = make_check_renderer(window, backend, {}, options);
    } catch (const std::runtime_error &) {
      rejected = true;
    }
    require(rejected, "Configured missing world catalog was not rejected "
                      "before mission callbacks");
#if defined(_WIN32)
    _putenv_s("MW34_WORLD_NORMALS", world_path.string().c_str());
#else
    setenv("MW34_WORLD_NORMALS", world_path.string().c_str(), 1);
#endif
    auto repaired_renderer = make_check_renderer(window, backend, {}, options);
    require(repaired_renderer->asset_statistics().world_normal_decoded_bytes ==
                0,
            "Catalog admission decoded pixels before a material lookup");
  }

  std::vector<uint32_t> flat_pixels;
  std::vector<uint32_t> flat_blended_pixels;
  std::vector<uint32_t> flat_additive_pixels;
  // Flat sun lighting control: normal maps are disabled, but the sun is on.
  {
    auto flat_options = options;
    flat_options.lighting = "flat";
    auto flat_renderer = make_check_renderer(window, backend, {}, flat_options);
    flat_renderer->set_viewport(0, 0, 64, 64);
    flat_renderer->clear(true, 0, 0, 0);
    mw34::materials::set_active_surface_key(t1m1_terrain_key);
    const auto flat_tex = flat_renderer->create_named_texture(
        "ggter1", 128, 128, green_data.data(), 1);
    mw34::materials::clear_active_surface_key();
    platform::DrawState flat_state{};
    flat_state.texture = flat_tex;
    quad(*flat_renderer, 0, 64, .5f, 0xffffffff, flat_state);
    require(flat_renderer->read_back(&pixels, &width, &height),
            "Could not read back flat terrain frame");
    flat_pixels = pixels;
    require(pixels != normal_pixels,
            "Visible terrain normal fixture did not differ from flat lighting");
    require(flat_renderer->asset_statistics().normal_draws == 0,
            "Flat lighting produced non-zero normal draws");
    require(flat_renderer->asset_statistics().world_normal_decoded_bytes == 0,
            "Flat lighting decoded a world normal page");

    auto blended_state = flat_state;
    blended_state.blend = true;
    flat_renderer->clear(true, 0x20, 0x40, 0x60);
    quad(*flat_renderer, 0, 64, .5f, 0xffffffff, blended_state);
    require(flat_renderer->read_back(&flat_blended_pixels, &width, &height),
            "Could not read back blended effect fixture");
    require(flat_blended_pixels[32 * width + 32] == 0xff228b22,
            "Blended effect did not preserve its bright texture colour");

    auto additive_state = flat_state;
    additive_state.blend = true;
    additive_state.additive = true;
    flat_renderer->clear(true, 0x20, 0x40, 0x60);
    quad(*flat_renderer, 0, 64, .5f, 0xffffffff, additive_state);
    require(flat_renderer->read_back(&flat_additive_pixels, &width, &height),
            "Could not read back additive effect fixture");
    require(flat_additive_pixels != flat_blended_pixels,
            "Additive effect blend did not preserve ONE/ONE output");
    require(flat_additive_pixels[32 * width + 32] == 0xff42cb82,
            "Additive effect did not retain its bright ONE/ONE colour");
  }

  // Off lighting control: normal_draws == 0
  {
    sdlfe::CoreCriticalAssets off_options;
    off_options.lighting = "off";
    auto off_renderer = make_check_renderer(window, backend, {}, off_options);
    off_renderer->set_viewport(0, 0, 64, 64);
    off_renderer->clear(true, 0, 0, 0);
    mw34::materials::set_active_surface_key(t1m1_terrain_key);
    const auto off_tex = off_renderer->create_named_texture(
        "ggter1", 128, 128, green_data.data(), 1);
    mw34::materials::clear_active_surface_key();
    platform::DrawState off_state{};
    off_state.texture = off_tex;
    quad(*off_renderer, 0, 64, .5f, 0xffffffff, off_state);
    require(off_renderer->read_back(&pixels, &width, &height),
            "Could not read back off terrain frame");
    require(off_renderer->asset_statistics().normal_draws == 0,
            "Off lighting produced non-zero normal draws");
    require(off_renderer->asset_statistics().world_normal_decoded_bytes == 0,
            "Off lighting decoded a world normal page");

    auto blended_state = off_state;
    blended_state.blend = true;
    off_renderer->clear(true, 0x20, 0x40, 0x60);
    quad(*off_renderer, 0, 64, .5f, 0xffffffff, blended_state);
    require(off_renderer->read_back(&pixels, &width, &height),
            "Could not read back unlit blended effect fixture");
    require(pixels == flat_blended_pixels,
            "Flat sun lighting changed translucent effect colour");

    auto additive_state = off_state;
    additive_state.blend = true;
    additive_state.additive = true;
    off_renderer->clear(true, 0x20, 0x40, 0x60);
    quad(*off_renderer, 0, 64, .5f, 0xffffffff, additive_state);
    require(off_renderer->read_back(&pixels, &width, &height),
            "Could not read back unlit additive effect fixture");
    require(pixels == flat_additive_pixels,
            "Flat sun lighting changed additive effect colour");
  }

  // Exercise the normal-enabled sun path too. The opaque control must be
  // visibly lit so these comparisons cannot pass with lighting disabled.
  {
    const auto before_lit = renderer->asset_statistics();
    renderer->clear(true, 0x20, 0x40, 0x60);
    quad(*renderer, 0, 64, .5f, 0xffffffff, state);
    require(renderer->read_back(&pixels, &width, &height),
            "Could not read back sun-lit opaque control");
    const auto lit_control = renderer->asset_statistics();
    require(lit_control.lit_draws > before_lit.lit_draws &&
                lit_control.normal_draws > before_lit.normal_draws &&
                pixels != flat_blended_pixels,
            "Opaque control did not exercise visible sun and normal lighting");

    auto blended_state = state;
    blended_state.blend = true;
    renderer->clear(true, 0x20, 0x40, 0x60);
    quad(*renderer, 0, 64, .5f, 0xffffffff, blended_state);
    require(renderer->read_back(&pixels, &width, &height) &&
                pixels == flat_blended_pixels,
            "Normal-enabled sun lighting changed translucent effect colour");

    blended_state.additive = true;
    renderer->clear(true, 0x20, 0x40, 0x60);
    quad(*renderer, 0, 64, .5f, 0xffffffff, blended_state);
    require(renderer->read_back(&pixels, &width, &height) &&
                pixels == flat_additive_pixels,
            "Normal-enabled sun lighting changed additive effect colour");
    const auto after_effects = renderer->asset_statistics();
    require(after_effects.lit_draws == lit_control.lit_draws &&
                after_effects.normal_draws == lit_control.normal_draws,
            "Blended effects entered the sun lighting pipeline");
  }
  // Optional content absent: normal mode is neutral, not a synthetic pack.
#if defined(_WIN32)
  _putenv_s("MW34_WORLD_NORMALS", "");
#else
  unsetenv("MW34_WORLD_NORMALS");
#endif
  {
    auto neutral_renderer = make_check_renderer(window, backend, {}, options);
    neutral_renderer->set_viewport(0, 0, 64, 64);
    neutral_renderer->clear(true, 0, 0, 0);
    mw34::materials::set_active_surface_key(t1m1_terrain_key);
    platform::DrawState neutral_state{};
    neutral_state.texture = neutral_renderer->create_named_texture(
        "ggter1", 128, 128, green_data.data(), 1);
    mw34::materials::clear_active_surface_key();
    quad(*neutral_renderer, 0, 64, .5f, 0xffffffff, neutral_state);
    require(
        neutral_renderer->read_back(&pixels, &width, &height) &&
            pixels == flat_pixels &&
            neutral_renderer->asset_statistics().normal_draws == 0 &&
            neutral_renderer->asset_statistics().world_normal_decoded_bytes ==
                0,
        "Missing optional world pack did not remain neutral");
  }
  // A real source model/material scope, authenticated by an authored BWSFM1
  // expectation rather than a first-observed UV cache entry.
  {
    struct NativeEnvironment {
      ~NativeEnvironment() {
#if defined(_WIN32)
        _putenv_s("MW34_NATIVE_MATERIALS", "");
        _putenv_s("MW34_NATIVE_MATERIAL_ID", "");
#else
        unsetenv("MW34_NATIVE_MATERIALS");
        unsetenv("MW34_NATIVE_MATERIAL_ID");
#endif
      }
    } native_environment;
    float positions[]{0, 0, 2, 2, 0, 2, 0, 2, 2};
    float uvs[]{0, 0, 1, 0, 0, 1};
    uint32_t indices[]{0, 1, 2};
    zmod::Material material{};
    material.flags = 1;
    zimg::TextureEntry source_texture{};
    std::strcpy(source_texture.name, "ggter1");
    zvid::D3DTexture device_texture{};
    source_texture.surface = &device_texture;
    material.texture = &source_texture;
    zmod::Polygon polygon{};
    polygon.flags = 3;
    polygon.vertex_indices = indices;
    polygon.uvs = uvs;
    polygon.material = &material;
    zmod::Model source_model{};
    const uint32_t one = 1, three = 3;
    std::memcpy(source_model.header + 0x10, &one, 4);
    std::memcpy(source_model.header + 0x14, &three, 4);
    source_model.polygons = &polygon;
    source_model.vertices = positions;
    const auto native_hash = cc_mw3_re::native_mesh_uv_hash(source_model);
    require(native_hash.has_value(),
            "Authored native source hash was unavailable");
    struct Batch {
      std::vector<std::array<float, 8>> vertices;
    };
    std::vector<Batch> canonical(1);
    for (unsigned corner = 0; corner < 3; ++corner)
      canonical[0].vertices.push_back({positions[corner * 3],
                                       positions[corner * 3 + 1],
                                       positions[corner * 3 + 2], 0, 0, 0,
                                       uvs[corner * 2], uvs[corner * 2 + 1]});
    require(*native_hash ==
                mw34::materials::compute_mesh_uv_hash(canonical, 0, 1),
            "Native source hash does not match the canonical BWSFM1 stream");
    uvs[2] = .75f;
    require(
        cc_mw3_re::native_mesh_uv_hash(source_model) != native_hash,
        "Changed live UV coordinates did not change native source identity");
    uvs[2] = 1;
    indices[0] = 3;
    require(!cc_mw3_re::native_mesh_uv_hash(source_model),
            "Native source hash accepted an out-of-range vertex");
    indices[0] = 0;

    const auto metadata =
        surface_metadata("native:fixture", "ggter1", *native_hash);
    const auto metadata_path = folder / "native-material.bin";
    std::ofstream(metadata_path, std::ios::binary)
        .write(metadata.data(), metadata.size());
#if defined(_WIN32)
    _putenv_s("MW34_WORLD_NORMALS", world_path.string().c_str());
    _putenv_s("MW34_NATIVE_MATERIALS", metadata_path.string().c_str());
    _putenv_s("MW34_NATIVE_MATERIAL_ID", "native:fixture");
#else
    setenv("MW34_WORLD_NORMALS", world_path.string().c_str(), 1);
    setenv("MW34_NATIVE_MATERIALS", metadata_path.string().c_str(), 1);
    setenv("MW34_NATIVE_MATERIAL_ID", "native:fixture", 1);
#endif
    auto checked_renderer = make_check_renderer(window, backend, {}, options);
    checked_renderer->set_viewport(0, 0, 64, 64);
    mw34::materials::set_active_surface_key(t1m1_terrain_key);
    device_texture.handle = checked_renderer->create_named_texture(
        "ggter1", 128, 128, green_data.data(), 1);
    mw34::materials::clear_active_surface_key();
    zcls::Node node{};
    std::strcpy(reinterpret_cast<char *>(node.raw), "nativefixture");
    node.model = &source_model;
    platform::ModelDrawContext model_context;
    model_context.node = &node;
    model_context.ordinary = true;
    platform::MaterialDrawContext material_context;
    material_context.model = &source_model;
    material_context.material = &material;
    material_context.texture_entry = &source_texture;
    auto draw_native = [&] {
      checked_renderer->clear(true, 0, 0, 0);
      checked_renderer->begin_model_draw(model_context);
      checked_renderer->begin_material_draw(material_context);
      platform::DrawState native_state;
      native_state.texture = device_texture.handle;
      const platform::TLVertex triangle[] = {
          {0, 0, .5f, 1, 0xffffffff, 0, 0, 0},
          {64, 0, .5f, 1, 0xffffffff, 0, 1, 0},
          {0, 64, .5f, 1, 0xffffffff, 0, 0, 1}};
      checked_renderer->draw(platform::Primitive::kFan, triangle, 3,
                             native_state);
      checked_renderer->end_material_draw();
      checked_renderer->end_model_draw();
      require(checked_renderer->read_back(&pixels, &width, &height),
              "Could not read native UV fixture");
    };
    draw_native();
    const auto qualified = checked_renderer->asset_statistics();
    require(qualified.normal_draws > 0 &&
                qualified.binding_rejected_mismatch == 0,
            "Correct authored native UV binding was rejected");
    uvs[2] = .75f;
    draw_native();
    require(checked_renderer->asset_statistics().normal_draws ==
                    qualified.normal_draws &&
                checked_renderer->asset_statistics().binding_rejected_mismatch >
                    0,
            "Wrong native mesh_uv_hash was accepted");
    uvs[2] = 1;
    material_context.texture_entry = nullptr;
    draw_native();
    require(checked_renderer->asset_statistics().normal_draws ==
                qualified.normal_draws,
            "Mismatched texture-entry identity was accepted");
    material_context.texture_entry = &source_texture;
    draw_native();
    require(checked_renderer->asset_statistics().normal_draws >
                qualified.normal_draws,
            "Restored authored native UV binding was not usable");
    struct DeferredBackendScope {
      platform::Render3D *renderer = zvid::render3d();
      zvid::DrawBuffers buffers = zvid::draw_buffers();
      ~DeferredBackendScope() {
        zvid::set_render3d(renderer);
        zvid::draw_buffers() = buffers;
      }
    } deferred_backend;
    zvid::set_render3d(checked_renderer.get());
    platform::TLVertex deferred_vertices[] = {
        {0, 0, .5f, 1, 0xffffffff, 0, 0, 0},
        {64, 0, .5f, 1, 0xffffffff, 0, 1, 0},
        {0, 64, .5f, 1, 0xffffffff, 0, 0, 1}};
    zvid::draw_buffers().tl =
        reinterpret_cast<zvid::TLVertex *>(deferred_vertices);
    zvid::device_state().primitive = 6;
    require(zvid::transparent_queue().count == 0 &&
                zvid::overlay_list().count == 0,
            "Native deferred fixtures require empty queues");
    checked_renderer->clear(true, 0, 0, 0);
    const auto before_deferred = checked_renderer->asset_statistics();
    checked_renderer->begin_model_draw(model_context);
    checked_renderer->begin_material_draw(material_context);
    for (int i = 0; i < 4; ++i)
      zvid::draw_textured_white(3, &device_texture, 0, .5f, i & 1);
    const auto admission = checked_renderer->asset_statistics();
    require(admission.native_fingerprint_evaluations ==
                before_deferred.native_fingerprint_evaluations + 1,
            "Native model fingerprint was recomputed per polygon");
    auto receipt = checked_renderer->capture_deferred_material_binding(
        device_texture.handle);
    checked_renderer->end_material_draw();
    checked_renderer->end_model_draw();
    zvid::flush_transparent();
    require(checked_renderer->read_back(&pixels, &width, &height),
            "Transparent readback failed");
    const auto after_transparent = checked_renderer->asset_statistics();
    require(after_transparent.deferred_material_admissions >
                    before_deferred.deferred_material_admissions &&
                after_transparent.normal_draws == before_deferred.normal_draws &&
                after_transparent.binding_rejected_mismatch ==
                    before_deferred.binding_rejected_mismatch,
            "Transparent queue lost qualified material admission");
    zvid::flush_overlay();
    require(checked_renderer->read_back(&pixels, &width, &height),
            "Overlay readback failed");
    const auto after_deferred = checked_renderer->asset_statistics();
    // Overlay draws are blended too, so (like the transparent queue above) they keep their
    // receipt but are deliberately not sun-lit; admission is what normal_draws cannot show.
    require(after_deferred.deferred_material_admissions >
                    after_transparent.deferred_material_admissions &&
                after_deferred.binding_rejected_mismatch ==
                    before_deferred.binding_rejected_mismatch,
            "Overlay queue lost qualified material admission");
    platform::DrawState receipt_state;
    receipt_state.texture = device_texture.handle;
    checked_renderer->clear(true, 0, 0, 0);
    checked_renderer->begin_deferred_material_draw(receipt);
    checked_renderer->draw(platform::Primitive::kFan, deferred_vertices, 3,
                           receipt_state);
    checked_renderer->end_deferred_material_draw();
    require(checked_renderer->read_back(&pixels, &width, &height),
            "Opaque deferred admission readback failed");
    const auto after_opaque = checked_renderer->asset_statistics();
    require(after_opaque.deferred_material_admissions ==
                after_deferred.deferred_material_admissions + 1,
            "Opaque draw was excluded from deferred material admissions");
    // Same handle after an upload cannot reuse a previously admitted receipt.
    mw34::materials::set_active_surface_key(t1m1_terrain_key);
    checked_renderer->update_texture(device_texture.handle, 128, 128,
                                     green_data.data());
    mw34::materials::clear_active_surface_key();
    checked_renderer->begin_deferred_material_draw(receipt);
    checked_renderer->draw(platform::Primitive::kFan, deferred_vertices, 3,
                           receipt_state);
    checked_renderer->end_deferred_material_draw();
    require(checked_renderer->read_back(&pixels, &width, &height),
            "Stale admission readback failed");
    require(checked_renderer->asset_statistics().normal_draws ==
                    after_opaque.normal_draws &&
                checked_renderer->asset_statistics().binding_rejected_mismatch >
                    after_opaque.binding_rejected_mismatch,
            "Deferred admission survived a same-handle upload");
    // A source mutation inside a model scope explicitly invalidates its hash.
    checked_renderer->begin_model_draw(model_context);
    checked_renderer->begin_material_draw(material_context);
    checked_renderer->capture_deferred_material_binding(device_texture.handle);
    const auto before_mutation = checked_renderer->asset_statistics();
    uvs[2] = .75f;
    checked_renderer->invalidate_material_geometry();
    checked_renderer->capture_deferred_material_binding(device_texture.handle);
    require(
        checked_renderer->asset_statistics().native_fingerprint_evaluations ==
                before_mutation.native_fingerprint_evaluations + 1 &&
            checked_renderer->asset_statistics().binding_rejected_mismatch >
                before_mutation.binding_rejected_mismatch,
        "In-scope source UV mutation did not invalidate authentication");
    uvs[2] = 1;
    checked_renderer->end_material_draw();
    checked_renderer->end_model_draw();
    // The first admission after reset must reload catalogs before its lookup.
    checked_renderer->reset_scene_resources();
    mw34::materials::set_active_surface_key(t1m1_terrain_key);
    checked_renderer->update_texture(device_texture.handle, 128, 128,
                                     green_data.data());
    mw34::materials::clear_active_surface_key();
    checked_renderer->begin_model_draw(model_context);
    checked_renderer->begin_material_draw(material_context);
    auto reloaded_receipt = checked_renderer->capture_deferred_material_binding(
        device_texture.handle);
    require(bool(reloaded_receipt),
            "First deferred material after reset was not admitted");
    checked_renderer->end_material_draw();
    checked_renderer->end_model_draw();
    const auto before_reloaded = checked_renderer->asset_statistics();
    checked_renderer->begin_deferred_material_draw(reloaded_receipt);
    checked_renderer->draw(platform::Primitive::kFan, deferred_vertices, 3,
                           receipt_state);
    checked_renderer->end_deferred_material_draw();
    require(checked_renderer->read_back(&pixels, &width, &height),
            "Reloaded admission readback failed");
    require(
        checked_renderer->asset_statistics().normal_draws >
                before_reloaded.normal_draws &&
            checked_renderer->asset_statistics().binding_rejected_mismatch ==
                before_reloaded.binding_rejected_mismatch,
        "First deferred material after reset lost normal binding");
    const auto before_old_epoch = checked_renderer->asset_statistics();
    checked_renderer->begin_deferred_material_draw(receipt);
    checked_renderer->draw(platform::Primitive::kFan, deferred_vertices, 3,
                           receipt_state);
    checked_renderer->end_deferred_material_draw();
    require(checked_renderer->read_back(&pixels, &width, &height),
            "Old-epoch admission readback failed");
    require(checked_renderer->asset_statistics().normal_draws ==
                    before_old_epoch.normal_draws &&
                checked_renderer->asset_statistics().binding_rejected_mismatch >
                    before_old_epoch.binding_rejected_mismatch,
            "Deferred admission survived scene resource reset");
#include "native_material_only_checks.inc"
  }
}

// Authored TL geometry only: each planar face has an independent diagonal.
// A real current-epoch keyed upload is essential: unkeyed sky never reached
// the defective ordinary-surface branch and would give a false RED control.
void check_native_sky_unlit(SDL_Window *window,
                            sdlfe::RendererBackend backend) {
  using Hook = cc_mw3_re::testing::RigidCaptureTestHook;
  struct Restore {
    zmth::Projection projection = zmth::projection();
    zmth::View view = zmth::view();
    mw34::materials::SurfaceKey key{};
    bool had_key = mw34::materials::get_active_surface_key(&key);
    std::fenv_t fp{};
    SDL_Window *window;
    int width{}, height{};
    explicit Restore(SDL_Window *w) : window(w) {
      std::fegetenv(&fp);
      SDL_GetWindowSize(window, &width, &height);
    }
    ~Restore() {
      zmth::projection() = projection;
      zmth::view() = view;
      if (had_key)
        mw34::materials::set_active_surface_key(key);
      else
        mw34::materials::clear_active_surface_key();
      SDL_SetWindowSize(window, width, height);
      SDL_SyncWindow(window);
      std::fesetenv(&fp);
    }
  } restore(window);
  std::vector<uint32_t> checker(64);
  for (int y = 0; y < 8; ++y)
    for (int x = 0; x < 8; ++x)
      checker[y * 8 + x] = ((x / 2 + y / 2) & 1) ? 0xffe0e0e0 : 0xff303030;
  const mw34::materials::SurfaceKey key{
      8, 8, 1, mw34::materials::normal_hash(checker.data(), checker.size() * 4)};
  require(key.hash != 0, "Sky fixture has no surface identity");
  unsigned cases = 0;
  for (const auto extent : {std::array<int, 2>{64, 48},
                            std::array<int, 2>{86, 36}}) {
    const int width = extent[0], height = extent[1];
    require(SDL_SetWindowSize(window, width, height) && SDL_SyncWindow(window),
            SDL_GetError());
    // Both view axes vary, including yaw/pitch; projection variant 2 differs
    // ONLY in projection, to catch incomplete adjacent-draw compatibility.
    auto set_view = [&](int variant) {
      zmth::projection() = {};
      auto &p = zmth::projection();
      p.near_z = 1;
      p.far_z = 100;
      p.fx_near = float(width) * (variant == 2 ? .24f : .7f);
      p.fy_near = float(height) * (variant == 2 ? 1.1f : .7f);
      p.cx = float(width) * .5f;
      p.cy = float(height) * (variant == 2 ? .2f : .5f);
      zmth::view().camera = {{1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0}};
      if (variant == 1)
        zmth::view().camera = {{.8f, .36f, -.48f, 0, .8f, .6f,
                               .6f, -.48f, .64f, 3, 4, 5}};
    };
    auto poison_view = [&] {
      set_view(1);
      zmth::projection().cx = -1000;
      zmth::view().camera.m[9] = 900;
    };
    auto face = [&](int side, bool white) {
      const float left = float(width) * (side ? .5f : .08f);
      const float right = float(width) * (side ? .92f : .5f);
      const float top = float(height) * .12f, bottom = float(height) * .88f;
      const float a = side ? .25f : .125f, b = side ? .1f : .25f;
      const uint32_t colors[] = {0xff80c060, 0xffc080a0,
                                 0xff6080c0, 0xffc0a080};
      auto color = [&](int vertex) {
        return white ? 0xffffffffu : colors[(vertex + side) % 4];
      };
      return std::array<platform::TLVertex, 4>{{
          {left, top, a, a, color(0), 0xff000000, 0, 0},
          {right, top, b, b, color(1), 0xd0000000, 1, 0},
          {right, bottom, b, b, color(2), 0xb0000000, 1, 1},
          {left, bottom, a, a, color(3), 0xe0000000, 0, 1}}};
    };
    const uint32_t background = 0xff07111b;
    std::vector<uint32_t> first_terrain_sun;
    for (int sun = 0; sun != 2; ++sun) {
      struct Mode {
        std::unique_ptr<cc_mw3_re::VulkanFrameRenderer> renderer;
        int texture;
      } modes[3];
      const char *names[] = {"off", "flat", "normal"};
      for (int m = 0; m != 3; ++m) {
        sdlfe::CoreCriticalAssets assets;
        assets.lighting = names[m];
        assets.sun_azimuth = sun ? "90" : "-90";
        assets.sun_elevation = "35";
        assets.sun_explicit = true;
        modes[m].renderer = make_check_renderer(window, backend, {}, assets);
        auto &r = *modes[m].renderer;
        r.set_viewport(0, 0, width, height);
        mw34::materials::set_active_surface_key(key);
        modes[m].texture = r.create_named_texture(
            "authored-unlit-sky", 8, 8,
            reinterpret_cast<const uint8_t *>(checker.data()), 1);
        mw34::materials::clear_active_surface_key();
        // Actual normal-cache admission; the ordinary companion must use it.
        mw34::materials::WorldNormalCache::TextureRecord normal{};
        normal.name = "authored-sky-companion-normal";
        normal.width = normal.height = 1;
        normal.pixels32 = {0xffd980d9};
        normal.hash = mw34::materials::normal_hash(normal.pixels32.data(), 4);
        Hook::seed_authored_normal(r, key, std::move(normal));
        require(Hook::group_epoch(r) != 0,
                "Sky fixture has no current texture epoch");
      }
      // A negative face index omits that side. Separate submissions are also
      // the independent reference for combined, differently viewed sky draws.
      auto render = [&](int mode, bool sky, bool textured, int diagonal,
                        int left_view, int right_view, bool white = false,
                        bool profile = false, bool poison = true) {
        auto &r = *modes[mode].renderer;
        r.mission_changed(profile ? platform::MissionIdentity{5, 1}
                                  : platform::MissionIdentity{});
        set_view(0);
        r.clear(true, 7, 17, 27);
        r.begin_scene();
        for (int side = 0; side != 2; ++side) {
          const int view = side ? right_view : left_view;
          if (view < 0)
            continue;
          set_view(view);
          auto vertices = face(side, white);
          platform::DrawState state;
          state.texture = textured ? modes[mode].texture : -1;
          state.native_sky = sky;
          state.address_u = state.address_v = 3;
          // Fog factor/alpha are deliberately present in the TL bytes; the
          // identity comparisons cover the same fixed-function operations.
          state.fog = true;
          state.alpha_modulate = sky;
          const int order[2][4] = {{0, 1, 2, 3}, {1, 2, 3, 0}};
          platform::TLVertex ordered[4];
          for (int i = 0; i != 4; ++i)
            ordered[i] = vertices[order[diagonal][i]];
          platform::TLVertex original[4];
          std::memcpy(original, ordered, sizeof ordered);
          r.draw(platform::Primitive::kFan, ordered, 4, state);
          require(!std::memcmp(ordered, original, sizeof ordered),
                  "Sky submission changed authored TL vertices");
          if (poison)
            poison_view();
        }
        if (profile && left_view >= 0 && right_view >= 0 &&
            left_view != right_view) {
          const auto observation = r.scene_binding_statistics();
          require(observation.supported && observation.draws == 2,
                  "Differently viewed adjacent sky draws merged");
        }
        r.end_scene();
        std::vector<uint32_t> pixels;
        int w{}, h{};
        require(r.read_back(&pixels, &w, &h) && w == width && h == height &&
                    pixels.size() == std::size_t(width * height),
                "Native unlit sky readback failed");
        ++cases;
        return pixels;
      };
      for (int camera = 0; camera != 2; ++camera) {
        for (int diagonal = 0; diagonal != 2; ++diagonal) {
          const auto off = render(0, true, true, diagonal, camera, camera);
          const auto flat = render(1, true, true, diagonal, camera, camera);
          const auto normal = render(2, true, true, diagonal, camera, camera);
          require(off == flat && off == normal,
                  "Native unlit sky acquired ordinary surface sun/normal lighting");
          require(modes[2].renderer->asset_statistics().normal_draws == 0,
                  "Native sky bound an ordinary surface normal map");
          const auto white =
              render(0, true, true, diagonal, camera, camera, true);
          require(off != white, "Sky off reference lost nonwhite vertex RGB");
          // Analytic barycentric witnesses use the actual chosen diagonal,
          // perspective rhw and UV, without reproducing a lighting shader.
          unsigned bright_count = 0, dark_count = 0;
          unsigned long bright_sum = 0, dark_sum = 0;
          for (int side = 0; side != 2; ++side) {
            const auto v = face(side, false);
            const int triangles[2][6] = {{0, 1, 2, 0, 2, 3},
                                         {1, 2, 3, 1, 3, 0}};
            for (int y = 2; y < height - 2; ++y)
              for (int x = 2; x < width - 2; ++x)
                for (int t = 0; t != 2; ++t) {
                  const auto &a = v[triangles[diagonal][t * 3]];
                  const auto &b = v[triangles[diagonal][t * 3 + 1]];
                  const auto &c = v[triangles[diagonal][t * 3 + 2]];
                  // The native TL shader applies the D3D half-pixel offset:
                  // framebuffer pixel (x,y) samples original TL (x,y).
                  const float px = float(x), py = float(y);
                  const float area = (b.sy - c.sy) * (a.sx - c.sx) +
                                     (c.sx - b.sx) * (a.sy - c.sy);
                  const float wa = ((b.sy - c.sy) * (px - c.sx) +
                                    (c.sx - b.sx) * (py - c.sy)) / area;
                  const float wb = ((c.sy - a.sy) * (px - c.sx) +
                                    (a.sx - c.sx) * (py - c.sy)) / area;
                  const float wc = 1 - wa - wb;
                  if (std::min({wa, wb, wc}) < .08f)
                    continue;
                  const float q = wa * a.rhw + wb * b.rhw + wc * c.rhw;
                  const float u = (wa * a.rhw * a.tu + wb * b.rhw * b.tu +
                                   wc * c.rhw * c.tu) / q;
                  const float z = (wa * a.rhw * a.tv + wb * b.rhw * b.tv +
                                   wc * c.rhw * c.tv) / q;
                  const float cell_u = u * 4, cell_v = z * 4;
                  const float fu = cell_u - int(cell_u), fv = cell_v - int(cell_v);
                  if (fu < .3f || fu > .7f || fv < .3f || fv > .7f)
                    continue;
                  const uint32_t pixel = off[y * width + x];
                  require(pixel != background,
                          "Sky analytic interior witness is blank");
                  const unsigned sum = (pixel & 255) + ((pixel >> 8) & 255) +
                                       ((pixel >> 16) & 255);
                  if ((int(cell_u) + int(cell_v)) & 1) {
                    ++bright_count;
                    bright_sum += sum;
                  } else {
                    ++dark_count;
                    dark_sum += sum;
                  }
                }
          }
          require(bright_count && dark_count &&
                      bright_sum / bright_count > dark_sum / dark_count + 80,
                  "Native sky checker UV/coverage witness failed");
        }
      }
      const auto normal_draws_before =
          modes[2].renderer->asset_statistics().normal_draws;
      const auto terrain_flat = render(1, false, true, 0, 0, 0, true);
      const auto terrain_normal = render(2, false, true, 0, 0, 0, true);
      require(modes[2].renderer->asset_statistics().normal_draws >
                  normal_draws_before,
              "Ordinary companion lost its normal-map binding");
      if (sun == 0)
        require(terrain_flat != terrain_normal,
                "Ordinary companion lost actual normal-map illumination");
      if (sun == 0)
        first_terrain_sun = terrain_flat;
      else
        require(first_terrain_sun != terrain_flat,
                "Ordinary terrain became insensitive to sun direction");
      if (sun == 0) {
        for (int mode : {1, 2}) {
          for (bool textured : {true, false}) {
            const auto neutral = render(mode, true, textured, 0, 0, 0);
            const auto profile = render(mode, true, textured, 0, 0, 0, false, true);
            require(profile != neutral,
                    "Intentional campaign sky-only profile no longer shades sky");
            for (int second_view : {1, 2}) {
              const auto left = render(mode, true, textured, 0, 0, -1, false, true);
              const auto right =
                  render(mode, true, textured, 0, -1, second_view, false, true);
              const auto right_base =
                  render(mode, true, textured, 0, -1, 0, false, true);
              require(right != right_base,
                      "Profile sky view/projection pixel witness is insensitive");
              const auto combined =
                  render(mode, true, textured, 0, 0, second_view, false, true);
              const auto unpoisoned =
                  render(mode, true, textured, 0, 0, second_view, false, true, false);
              require(combined == unpoisoned,
                      "Sky retained a borrowed producer view after submission");
              for (int y = 0; y < height; ++y)
                for (int x = 0; x < width; ++x)
                  require(combined[y * width + x] ==
                              (x < width / 2 ? left : right)[y * width + x],
                          "Combined sky views differ from isolated profile "
                          "references");
            }
          }
        }
      }
    }
  }
  std::fprintf(stderr, "[NATIVE_SKY_UNLIT] pixel_cases=%u\n", cases);
}

// A briefing loads its mission before the Mech Lab opens. The Lab preview must use
// the configured stock lighting, not the mission's campaign profile: Operation 3's
// red sky tint (c3m3) turned every paint orange and hid the selected skin.
void check_lab_preview_lighting(SDL_Window *window, sdlfe::RendererBackend backend) {
  sdlfe::CoreCriticalAssets assets;
  assets.lighting = "normal";
  auto renderer = make_check_renderer(window, backend, {}, assets);
  require(cc_mw3_re::testing::display_lighting_is_stock(*renderer),
          "Renderer without a mission did not start on stock lighting");
  const platform::MissionIdentity fuel_depot{2, 3};  // c3m3
  renderer->mission_changed(fuel_depot);
  require(!cc_mw3_re::testing::display_lighting_is_stock(*renderer),
          "c3m3 campaign profile was not applied in the mission");
  renderer->set_lab_preview_lighting(true);
  require(cc_mw3_re::testing::display_lighting_is_stock(*renderer),
          "Lab preview kept the mission's campaign lighting");
  // A mission change while the Lab is up (not expected, but possible from a debug
  // start) must not leak its profile into the preview either.
  renderer->mission_changed({0, 1});
  require(cc_mw3_re::testing::display_lighting_is_stock(*renderer),
          "Mission change during the Lab preview restored campaign lighting");
  renderer->mission_changed(fuel_depot);
  renderer->set_lab_preview_lighting(false);
  require(!cc_mw3_re::testing::display_lighting_is_stock(*renderer),
          "Closing the Lab did not restore the mission's campaign lighting");
  std::fprintf(stderr, "[LAB_PREVIEW_LIGHTING] stock in Lab, c3m3 profile restored after\n");
}

void check_sealed_environment(SDL_Window *window,
                              sdlfe::RendererBackend backend) {
  struct RestoreView {
    zmth::Projection projection = zmth::projection();
    zmth::View view = zmth::view();
    ~RestoreView() {
      zmth::projection() = projection;
      zmth::view() = view;
    }
  } restore_view;
  zmth::projection() = {};
  zmth::view().camera = {{1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0}};
  require(SDL_SetWindowSize(window, 32, 32) && SDL_SyncWindow(window),
          SDL_GetError());
  const uint8_t green[4] = {0, 255, 0, 255};
  for (const char *mode : {"flat", "off"}) {
    sdlfe::CoreCriticalAssets assets;
    assets.lighting = mode;
    auto renderer = make_check_renderer(window, backend, {}, assets);
    renderer->set_viewport(0, 0, 32, 32);
    auto read = [&]() {
      std::vector<uint32_t> px;
      int w = 0, h = 0;
      require(renderer->read_back(&px, &w, &h),
              "Sealed environment readback failed");
      require(w == 32 && h == 32 && px.size() == 1024,
              "Sealed environment size mismatch");
      return px;
    };
    auto px_at = [&](const std::vector<uint32_t> &px, int x, int y) {
      return px[y * 32 + x];
    };
    const platform::MissionIdentity sealed_ids[] = {{1, 2}, {1, 4}, {2, 5}};
    for (auto id : sealed_ids) {
      renderer->mission_changed(id);
      renderer->clear(true, 37, 89, 143);
      renderer->begin_scene();
      renderer->end_scene();
      auto px = read();
      uint32_t expected = (mode[0] == 'f') ? 0xFF000000 : 0xFF25598F;
      require(px_at(px, 30, 2) == expected, "sealed clear");
      renderer->begin_scene();
      quad(*renderer, 0.0f, 32.0f, 0.0001f, 0xFFFF0000);
      auto green_handle = renderer->create_texture(1, 1, green, 4);
      platform::DrawState ds;
      ds.texture = green_handle;
      quad(*renderer, 8.0f, 24.0f, 0.00015f, 0xFFFFFFFF, ds);
      platform::DrawState hud;
      hud.sharp = true;
      hud.depth_write = false;
      hud.depth_always = true;
      quad(*renderer, 0.0f, 6.0f, 0.0f, 0xFF0000FF, hud);
      renderer->end_scene();
      px = read();
      uint32_t sky_expected = (mode[0] == 'f') ? 0xFF000000 : 0xFFFF0000;
      require(px_at(px, 30, 2) == sky_expected, "sealed sky");
      require(px_at(px, 16, 16) == 0xFF00FF00, "terrain");
      require(px_at(px, 2, 2) == 0xFF0000FF, "hud");
      renderer->clear(false, 255, 0, 0);
      renderer->begin_scene();
      renderer->end_scene();
      auto px2 = read();
      require(px_at(px2, 16, 16) == 0xFF00FF00, "depth clear preserve");
      renderer->release_texture(green_handle);
    }
    const platform::MissionIdentity outdoor_ids[] = {{5, 1}, {9, 1}, {}};
    for (auto id : outdoor_ids) {
      renderer->mission_changed(id);
      renderer->clear(true, 37, 89, 143);
      renderer->begin_scene();
      renderer->end_scene();
      auto px = read();
      require(px_at(px, 30, 2) == 0xFF25598F, "outdoor clear");
      renderer->begin_scene();
      platform::DrawState sky_state;
      sky_state.native_sky = true;
      quad(*renderer, 0.0f, 32.0f, 0.0001f, 0xFFFF0000, sky_state);
      renderer->end_scene();
      auto px2 = read();
      // The exact profile pixel reflects native sky's captured producer view.
      const uint32_t outdoor_sky_expected =
          (mode[0] == 'f' && id.world_index == 5 && id.number == 1)
              ? 0xFFBD8884
              : 0xFFFF0000;
      require(px_at(px2, 30, 2) == outdoor_sky_expected, "outdoor sky");
    }
    renderer->mission_changed({1, 2});
    renderer->reset_scene_resources();
    renderer->clear(true, 37, 89, 143);
    renderer->begin_scene();
    renderer->end_scene();
    auto px = read();
    require(px_at(px, 30, 2) == 0xFF25598F, "reset clear");
  }
}

void check_prepared(SDL_Window *window, sdlfe::RendererBackend backend,
                    const sdlfe::CoreCriticalQuality &quality,
                    bool materials = false) {
  const auto folder =
      std::filesystem::temp_directory_path() /
      ("cc-prepared-check-" + std::to_string(SDL_GetPerformanceCounter()));
  require(std::filesystem::create_directory(folder),
          "Authored fixture directory already exists");
  struct Files {
    std::filesystem::path folder;
    ~Files() {
      std::error_code error;
      std::filesystem::remove(folder / "mesh.bin", error);
      std::filesystem::remove(folder / "textures.bin", error);
      std::filesystem::remove(folder / "normals.bin", error);
      std::filesystem::remove(folder / "materials.bin", error);
      std::filesystem::remove(folder / "other_textures.bin", error);
      std::filesystem::remove(folder / "other_normals.bin", error);
      std::filesystem::remove(folder / "absent_normals.bin", error);
      std::filesystem::remove(folder / "mixed_mesh.bin", error);
      std::filesystem::remove(folder, error);
    }
  } files{folder};
  // Diagnostic red must not tint the bound green albedo a second time.
  std::ofstream(folder / "mesh.bin", std::ios::binary)
      << prepared_fixture::mesh(2, 0xffff0000);
  std::ofstream(folder / "textures.bin", std::ios::binary)
      << prepared_fixture::textures();
  // Resource-selection checks use normals even when the draw control leaves
  // normal lighting disabled.
  std::ofstream(folder / "normals.bin", std::ios::binary)
      << prepared_fixture::normals(0xffd980d9);
  sdlfe::CoreCriticalAssets options;
  options.textures = (folder / "textures.bin").u8string();
  options.models.push_back(
      {"authored", "0", (folder / "mesh.bin").u8string(), options.textures});
  if (materials) {
    options.normals.push_back(
        {"authored", "0", (folder / "normals.bin").u8string()});
    options.lighting = "normal";
    std::istringstream mesh_input(prepared_fixture::mesh(2, 0xffff0000),
                                  std::ios::binary);
    const auto mesh = ::platform::prepared::read_mesh(mesh_input);
    const auto hash = mw34::materials::compute_mesh_uv_hash(
        mesh.batches, 0, mesh.batches.size());
    const auto metadata = surface_metadata("authored:close", "authored", hash,
                                           .7f, .04f, 0.f, false);
    const auto path = folder / "materials.bin";
    options.materials.push_back({"authored", "0", path.u8string()});
    auto wrong = metadata;
    wrong[24] ^= 1;
    std::ofstream(path, std::ios::binary).write(wrong.data(), wrong.size());
    bool rejected = false;
    try {
      auto invalid = make_check_renderer(window, backend, quality, options);
    } catch (const std::runtime_error &) {
      rejected = true;
    }
    require(rejected,
            "Prepared renderer accepted mismatched authored mesh_uv_hash");
    std::ofstream(path, std::ios::binary)
        .write(metadata.data(), metadata.size());
  }
  {
    std::ofstream(folder / "other_textures.bin", std::ios::binary)
        << prepared_fixture::textures();
    std::ofstream(folder / "other_normals.bin", std::ios::binary)
        << prepared_fixture::normals(0xffd980d9);
    std::ofstream(folder / "absent_normals.bin", std::ios::binary)
        << prepared_fixture::normals(0, true);
    std::ofstream(folder / "mixed_mesh.bin", std::ios::binary)
        << prepared_fixture::build_valid_v4_mesh(
               "ltoe01", "control", "panel", .5, .2, -.1, "", true);
    sdlfe::CoreCriticalAssets selection_options;
    selection_options.lighting = "normal";
    selection_options.models.push_back(
        {"authored", "0", (folder / "mesh.bin").u8string(),
         (folder / "textures.bin").u8string()});
    selection_options.models.push_back(
        {"other", "1", (folder / "mesh.bin").u8string(),
         (folder / "other_textures.bin").u8string()});
    selection_options.models.push_back(
        {"nonormal", "0", (folder / "mesh.bin").u8string(),
         (folder / "textures.bin").u8string()});
    selection_options.normals.push_back(
        {"authored", "0", (folder / "normals.bin").u8string()});
    selection_options.normals.push_back(
        {"other", "1", (folder / "other_normals.bin").u8string()});
    selection_options.normals.push_back(
        {"nonormal", "0", (folder / "absent_normals.bin").u8string()});

    selection_options.models.push_back(
        {"mixed", "0", (folder / "mixed_mesh.bin").u8string(),
         (folder / "textures.bin").u8string()});
    selection_options.normals.push_back(
        {"mixed", "0", (folder / "normals.bin").u8string()});

    const cc_mw3_re::PreparedModels selection_models(selection_options);
    const auto unmatched = selection_models.resources_for_assets(
        {"", "mech_unmatched.flt", "building_tower.flt"});
    require(unmatched.matched_source_assets == 0 &&
                unmatched.textures.empty() && unmatched.normals.empty() &&
                unmatched.rigid_batches.empty(),
            "Unmatched source assets selected prepared texture resources");

    const auto authored_exact =
        selection_models.resources_for_assets({"mech_authored.flt"});
    require(authored_exact.matched_source_assets == 1 &&
                authored_exact.textures.size() == 1 &&
                authored_exact.normals.size() == 1 &&
                authored_exact.textures[0] != nullptr &&
                authored_exact.normals[0] != nullptr &&
                authored_exact.rigid_batches.size() == 1,
            "Exact prepared source asset did not select expected texture and "
            "normal pointers");

    // Repeated source asset names and cross-LOD fallback to the same selected
    // model must deduplicate both model identity and image pointers.
    const auto authored_deduped = selection_models.resources_for_assets(
        {"mech_authored.flt", "mech_authored.flt", "mech_authored_1.flt",
         "mech_unmatched.flt"});
    require(authored_deduped.matched_source_assets == 2 &&
                authored_deduped.textures == authored_exact.textures &&
                authored_deduped.normals == authored_exact.normals &&
                authored_deduped.rigid_batches == authored_exact.rigid_batches,
            "Repeated or cross-LOD fallback source assets duplicated prepared "
            "resource pointers");

    // Mixed-bone geometry stays dynamic while authored images remain selectable.
    const auto mixed_resources =
        selection_models.resources_for_assets({"mech_mixed.flt"});
    require(mixed_resources.matched_source_assets == 1 &&
                mixed_resources.rigid_batches.empty() &&
                mixed_resources.textures.size() == 1 &&
                mixed_resources.normals.size() == 1,
            "Mixed-bone geometry warmup changed authored image selection");

    const auto other_fallback =
        selection_models.resources_for_assets({"mech_other.flt"});
    require(other_fallback.matched_source_assets == 1 &&
                other_fallback.textures.size() == 1 &&
                other_fallback.normals.size() == 1 &&
                other_fallback.textures[0] != authored_exact.textures[0] &&
                other_fallback.normals[0] != authored_exact.normals[0],
            "Distance-to-close LOD fallback did not select the other model's "
            "distinct resource pointers");

    // Explicit no_normal bindings must not select a normal image pointer.
    const auto absent_normal =
        selection_models.resources_for_assets({"mech_nonormal.flt"});
    require(absent_normal.matched_source_assets == 1 &&
                absent_normal.textures.size() == 1 &&
                absent_normal.normals.empty(),
            "Explicit no_normal binding selected a prepared normal resource");
  }
  require(SDL_SetWindowSize(window, 64, 64) && SDL_SyncWindow(window),
          SDL_GetError());
  std::unique_ptr<zcls::Node, int (*)(zcls::Node *)> root(
      zcls::object3d_create(), zcls::tree_destroy);
  auto *control = zcls::object3d_create(), *panel = zcls::object3d_create();
  require(root && control && panel,
          "Authored native nodes could not be created");
  require(zcls::object3d_add_child(root.get(), control) == 0 &&
              zcls::object3d_add_child(control, panel) == 0,
          "Authored native hierarchy could not be linked");
  zcls::node_set_name(root.get(), "actor");
  zcls::node_set_name(control, "control");
  zcls::node_set_name(panel, "panel");
  auto identity = std::make_shared<zcls::SourceAsset>();
  identity->name = "mech_authored.flt";
  identity->nodes = {{"actor", 1}, {"control", 1}, {"panel", 1}};
  root->source_asset = control->source_asset = panel->source_asset = identity;
  root->source_asset_root = true;
  // A valid native source makes accidental warming of the replaced mesh visible.
  float source_positions[]{-1, -1, 2, 1, -1, 2, 0, 1, 2};
  std::uint32_t source_indices[]{2, 1, 0};
  zmod::Material source_material{};
  source_material.alpha = 255;
  zmod::Polygon source_polygon{};
  source_polygon.flags = 3;
  source_polygon.vertex_indices = source_indices;
  source_polygon.material = &source_material;
  zmod::Model source_model{};
  source_model.vertices = source_positions;
  source_model.polygons = &source_polygon;
  const uint32_t source_count = 3, source_polygon_count = 1;
  std::memcpy(source_model.header + 0x14, &source_count, sizeof source_count);
  std::memcpy(source_model.header + 0x10, &source_polygon_count,
              sizeof source_polygon_count);
  panel->model = &source_model;
  panel->source_model_vertices = source_count;
  struct ModelPointer {
    zcls::Node *node;
    ~ModelPointer() { node->model = nullptr; }
  } model_pointer{panel};
  {
    auto warmup_quality = quality;
    warmup_quality.anisotropy = "16";
    auto warmup_renderer =
        make_check_renderer(window, backend, warmup_quality, options);
    const auto mips_before = warmup_renderer->quality_statistics().mip_levels;
    warmup_renderer->mission_changed(platform::MissionIdentity{});
    require(warmup_renderer->quality_statistics().mip_levels > mips_before,
            "Prepared albedo was not preloaded or mip-generated at mission boundary");

    // Verify late native source admission after mission boundary: create a 2x2
    // RGBA native texture while a nonzero unmatched SurfaceKey is active.
    // Must remain CPU-cold until begin_scene triggers scene-boundary warmup.
    const mw34::materials::SurfaceKey late_native_surface_key{2, 2, 1,
                                                              0x11223344ULL};
    mw34::materials::set_active_surface_key(late_native_surface_key);
    const uint8_t late_native_rgba[16] = {
        255, 0, 0, 255,   0, 255, 0, 255,
        0, 0, 255, 255,   255, 255, 0, 255};
    const auto late_native_handle =
        warmup_renderer->create_texture(2, 2, late_native_rgba, 1);
    mw34::materials::clear_active_surface_key();

    const auto mip_levels_after_creation =
        warmup_renderer->quality_statistics().mip_levels;
    warmup_renderer->begin_scene();
    require(warmup_renderer->quality_statistics().mip_levels ==
                mip_levels_after_creation,
            "Unreferenced late native albedo consumed preload VRAM");
    warmup_renderer->end_scene();
    const auto mip_levels_after_warmup =
        warmup_renderer->quality_statistics().mip_levels;
    mw34::materials::set_active_surface_key(late_native_surface_key);
    warmup_renderer->update_texture(late_native_handle, 2, 2, late_native_rgba);
    mw34::materials::clear_active_surface_key();
    warmup_renderer->begin_scene();
    require(warmup_renderer->quality_statistics().mip_levels ==
                mip_levels_after_warmup,
            "Runtime texture update repeated bulk mission preload");
    platform::DrawState late_native_state{};
    late_native_state.texture = late_native_handle;
    quad(*warmup_renderer, 0, 64, .5f, 0xffffffff, late_native_state);
    std::vector<uint32_t> late_native_pixels;
    int late_native_width = 0, late_native_height = 0;
    require(warmup_renderer->read_back(&late_native_pixels, &late_native_width,
                                     &late_native_height) &&
                warmup_renderer->quality_statistics().mip_levels >
                    mip_levels_after_warmup,
            "Runtime texture update did not upload through its normal draw");
    warmup_renderer->end_scene();
    warmup_renderer->release_texture(late_native_handle);
  }
  auto renderer = make_check_renderer(window, backend, quality, options);
  // Preload live-node prepared resources at the mission boundary before the
  // first draw (covering both normal-disabled and normal-enabled runs).
  renderer->mission_changed(platform::MissionIdentity{});
  struct RenderBinding {
    platform::Render3D *previous = zvid::render3d();
    ~RenderBinding() { zvid::set_render3d(previous); }
  } binding;
  zvid::set_render3d(renderer.get());
  renderer->set_viewport(0, 0, 64, 64);
  float matrix[12] = {1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0};
  platform::ModelDrawContext context;
  context.node = panel;
  context.model_to_camera = context.model_to_world = matrix;
  context.near_z = context.clip_near = .1f;
  context.far_z = 100;
  context.fx_near = context.fy_near = 320;
  context.cx = context.cy = 32;
  context.ordinary = true;
  auto frame = [&](cc_mw3_re::VulkanFrameRenderer *target = nullptr,
                   bool read = true, bool early = false) {
    auto *active = target ? target : renderer.get();
    RenderBinding active_binding;
    zvid::set_render3d(active);
    active->clear(true, 0, 0, 0);
    std::fenv_t saved;
    require(std::fegetenv(&saved) == 0,
            "Cannot save authored floating-point environment");
    std::feclearexcept(FE_ALL_EXCEPT);
    std::feraiseexcept(FE_DIVBYZERO);
    const auto rounding = std::fegetround();
    if (early)
      require(active->submit_prepared_geometry(context, {}) ==
                  cc::geometry::Submission::submitted,
              "Material response did not reach early prepared submission");
    else
      active->begin_model_draw(context);
    const auto flags = std::fetestexcept(FE_ALL_EXCEPT);
    const auto next_rounding = std::fegetround();
    std::fesetenv(&saved);
    require(flags == FE_DIVBYZERO && rounding == next_rounding,
            "Visual rendering changed the native floating-point environment");
    if (!early) {
      require(active->replaces_model_geometry(),
              "Prepared model did not admit its authored source");
      const auto queued = zvid::transparent_queue().count;
      require(zvid::queue_transparent(6, 3, nullptr) == nullptr &&
                  zvid::transparent_queue().count == queued,
              "Deferred source geometry escaped its replacement scope");
      quad(*active, 0, 64, .9f, 0xffff00ff);
      active->end_model_draw();
      require(!active->replaces_model_geometry(),
              "Prepared model scope did not end");
    }
    if (!read)
      return std::vector<uint32_t>{};
    std::vector<uint32_t> pixels;
    int width = 0, height = 0;
    require(active->read_back(&pixels, &width, &height) && width == 64 &&
                height == 64,
            "Prepared model did not render at the output extent");
    return pixels;
  };
  {
    // Load-time upload must be reused by the first real prepared draw.
    auto warmed_options = options;
    warmed_options.geometry = "gpu";
    auto warmed_renderer =
        make_check_renderer(window, backend, quality, warmed_options);
    warmed_renderer->set_viewport(0, 0, 64, 64);
    // Leave a frame queued when the mission loads. With --render-thread its
    // present packet is still on the worker, so the load-time upload has to wait
    // for it instead of using the shared Vulkan objects at the same time. The
    // scene stays empty because strict GPU geometry rejects CPU 3D draws.
    warmed_renderer->begin_scene();
    warmed_renderer->end_scene();
    warmed_renderer->mission_changed({});
    require(!source_model.render_geometry,
            "Prepared-owned native geometry was warmed unnecessarily");
    require(warmed_renderer->asset_statistics().geometry_uploads == 1,
            "First warmup should upload geometry");
    warmed_renderer->begin_scene();
    warmed_renderer->end_scene();
    require(warmed_renderer->asset_statistics().geometry_uploads == 1,
            "Late warmup should not upload geometry again");
    const auto warmed_pixels = frame(warmed_renderer.get(), true, true);
    require(!warmed_pixels.empty(), "Warmed frame should produce pixels");
    require(warmed_renderer->asset_statistics().gpu_model_draws > 0,
            "Warmed frame should have GPU model draws");
    require(warmed_renderer->asset_statistics().geometry_uploads == 1,
            "First real draw should reuse warm upload");
    // Tearing the scene down clears the first-world warmup. If it stayed armed,
    // the next scene would upload the old mission's geometry again right after
    // its buffers were retired.
    warmed_renderer->reset_scene_resources();
    warmed_renderer->begin_scene();
    warmed_renderer->end_scene();
    require(warmed_renderer->asset_statistics().geometry_uploads == 1,
            "Scene reset left the first-world preload armed");
  }
  {
    // A selected skin replaces the primary albedos at draw time. Its textures are
    // warmed at mission load as well, so the first skinned draw uploads nothing.
    // Index 0 is the control: it stages only the primary set. The fixture
    // images are too small for mip counts to show a missed upload, so the
    // staged-byte comparison is what detects an unwarmed skin.
    std::uint64_t primary_staged_bytes = 0;
    auto skin_options = options;
    skin_options.geometry = "gpu";
    skin_options.skins.push_back({"authored", "0", options.textures, 1});
    struct SkinIndex {
      zcls::Node *node;
      ~SkinIndex() { node->prepared_skin_index = 0; }
    } skin_index{panel};
    for (const int32_t index : {0, 1}) {
      panel->prepared_skin_index = index;
      auto skinned = make_check_renderer(window, backend, quality, skin_options);
      skinned->set_viewport(0, 0, 64, 64);
      skinned->mission_changed({});
      const auto staged_bytes =
          cc_mw3_re::testing::preload_test_state(*skinned).prepared_staged_bytes;
      if (index == 0)
        primary_staged_bytes = staged_bytes;
      else
        require(staged_bytes > primary_staged_bytes,
                "Selected skin textures were not staged at mission load");
      const auto loaded_mips = skinned->quality_statistics().mip_levels;
      require(!frame(skinned.get(), true, true).empty(), "Skinned frame produced no pixels");
      require(skinned->quality_statistics().mip_levels == loaded_mips,
              index ? "First skinned draw uploaded textures again"
                    : "First primary draw uploaded textures again");
    }
  }
  const auto first = frame();
  {
    using namespace cc_mw3_re::testing;
    using mw34::vkscene::PreloadStopReason;
    constexpr std::uint64_t gib = 1024ULL * 1024ULL * 1024ULL;
    const auto exact = mw34::vkscene::evaluate_preload_budget(8 * gib, 6 * gib - 256, 256);
    require(exact.admitted && exact.headroom_bytes == 2 * gib &&
                !mw34::vkscene::evaluate_preload_budget(8 * gib, 6 * gib - 256, 257).admitted &&
                !mw34::vkscene::evaluate_preload_budget(8 * gib, ~std::uint64_t{}, 1).admitted &&
                !mw34::vkscene::evaluate_preload_budget(gib, 0, 1).admitted,
            "Preload budget boundary, minimum reserve or overflow protection changed");

    // Inspect the backend before and after the fence; completed frontend
    // mission calls alone cannot expose prematurely published cache state.
    {
      using namespace mw34::vkscene;
      ModelGeometry geometry;
      geometry.key = 0x4241544348000001ULL;
      geometry.hash = 1;
      geometry.vertices.resize(3);
      const auto texture = [](std::uint64_t key) {
        return TextureRef{key, 1, 2, 2, TexFormat::rgba8888, {},
                          {0xff0000ff, 0xff00ff00, 0xffff0000, 0xffffffff}};
      };
      Renderer mixed(Renderer::ColorTarget::rgba8, {}, {1, 1, 2, false}, true);
      mixed.set_preload_batch_cap_for_test(256);
      mixed.begin_preload();
      require(mixed.preload_model_geometry(geometry) &&
                  mixed.preload_texture(texture(11)) && mixed.preload_texture(texture(12)) &&
                  mixed.preload_texture(texture(13)) && mixed.preload_texture(texture(11)),
              "Mixed preload batch rejected a small resource");
      require(mixed.preload_pending_count() == 4 && mixed.preload_batch_submissions() == 0 &&
                  mixed.uploads == 0 && mixed.model_uploads == 0 &&
                  mixed.mip_levels_uploaded == 0 && !mixed.model_uploaded(geometry.key) &&
                  !mixed.texture_resident(11) && !mixed.texture_resident(12),
              "Queued preload work published completion before its batch fence");
      mixed.finalize_preload();
      mixed.end_preload();
      const auto mixed_image_memory = mixed.texture_memory_for_test(11);
      const auto mixed_model_memory = mixed.model_memory_for_test(geometry.key);
      require(mixed_image_memory[3] == 64 * 1024 * 1024 &&
                  mixed_model_memory[3] == 64 * 1024 * 1024 &&
                  mixed_model_memory[0] % mixed_model_memory[2] == 0 &&
                  mixed.model_texture_memory_separate_for_test(geometry.key, 11) &&
                  mixed.preload_memory_block_count() == 2 &&
                  mixed.preload_allocation_attempts() == 3,
              "Mixed preload did not share staging and use separate image/linear memory blocks");
      require(mixed.preload_batch_submissions() == 1 && mixed.preload_pending_count() == 0 &&
                  mixed.preload_peak_pending() == 4 && mixed.preload_peak_bytes() == 144 &&
                  mixed.uploads == 3 && mixed.model_uploads == 1 &&
                  mixed.mip_levels_uploaded == 3 && mixed.model_uploaded(geometry.key) &&
                  mixed.texture_resident(11) && mixed.texture_resident(12) &&
                  mixed.texture_resident(13),
              "Many geometry and texture uploads did not complete in one real submission");
      mixed.begin_preload();
      require(mixed.preload_model_geometry(geometry) && mixed.preload_texture(texture(11)),
              "Completed immutable resources were not reusable");
      mixed.finalize_preload();
      mixed.end_preload();
      require(mixed.preload_batch_submissions() == 1 && mixed.uploads == 3 &&
                  mixed.model_uploads == 1,
              "Resident preload resources repeated an upload or empty submission");

      Renderer pooled;
      pooled.set_preload_batch_cap_for_test(256);
      pooled.begin_preload();
      const auto initial_allocations = pooled.live_allocation_count();
      require(pooled.preload_texture(texture(101)) && pooled.preload_texture(texture(102)) &&
                  pooled.preload_texture(texture(103)),
              "Could not queue pooled image fixtures");
      const auto first_memory = pooled.texture_memory_for_test(101);
      const auto second_memory = pooled.texture_memory_for_test(102);
      const auto third_memory = pooled.texture_memory_for_test(103);
      require(first_memory[3] == 64 * 1024 * 1024 &&
                  pooled.texture_memory_shared_for_test(101, 102) &&
                  pooled.texture_memory_shared_for_test(101, 103) &&
                  first_memory[0] % first_memory[2] == 0 &&
                  second_memory[0] % second_memory[2] == 0 &&
                  third_memory[0] % third_memory[2] == 0 &&
                  second_memory[0] >= first_memory[0] + first_memory[1] &&
                  third_memory[0] >= second_memory[0] + second_memory[1] &&
                  third_memory[0] + third_memory[1] <= third_memory[3] &&
                  pooled.preload_allocation_attempts() == 2 &&
                  // Shared staging replaces init's existing 8-byte allocation;
                  // only the new image block increases the live allocation count.
                  pooled.live_allocation_count() == initial_allocations + 1,
              "Pooled images overlapped, lost alignment or repeated native allocations");
      pooled.finalize_preload();
      pooled.end_preload();
      const auto bytes_with_block = pooled.tracked_device_local_bytes();
      const auto allocations_with_block = pooled.live_allocation_count();
      pooled.discard_texture_for_test(101);
      require(pooled.tracked_device_local_bytes() == bytes_with_block &&
                  pooled.live_allocation_count() == allocations_with_block &&
                  pooled.preload_memory_block_count() == 1,
              "Releasing a pooled slice freed memory still owned by other textures");
      pooled.begin_preload();
      require(pooled.preload_texture(texture(104)), "Could not reuse a live image block tail");
      const auto fourth_memory = pooled.texture_memory_for_test(104);
      require(fourth_memory[0] >= third_memory[0] + third_memory[1],
              "A pooled allocation reused a released slice in a still-live block");
      pooled.finalize_preload();
      pooled.end_preload();
      pooled.discard_texture_for_test(102);
      pooled.discard_texture_for_test(103);
      require(pooled.tracked_device_local_bytes() == bytes_with_block,
              "A shared block was freed before its final texture release");
      pooled.discard_texture_for_test(104);
      require(pooled.preload_memory_block_count() == 0 &&
                  pooled.tracked_device_local_bytes() + first_memory[3] == bytes_with_block &&
                  pooled.live_allocation_count() + 1 == allocations_with_block,
              "Final pooled texture release did not free and untrack the complete block");

      // Size the test block from the actual driver requirements, rather than
      // assuming an image has a fixed allocation size or alignment on all GPUs.
      const auto stride = ((first_memory[1] + first_memory[2] - 1) / first_memory[2]) * first_memory[2];
      require(stride && stride * 2 <= 64 * 1024 * 1024,
              "Small image requirements exceed the authored pool fixture bound");
      Renderer crossing;
      crossing.set_preload_batch_cap_for_test(256);
      crossing.set_preload_memory_block_cap_for_test(stride * 2);
      crossing.begin_preload();
      require(crossing.preload_texture(texture(111)) && crossing.preload_texture(texture(112)) &&
                  crossing.preload_texture(texture(113)) &&
                  crossing.texture_memory_shared_for_test(111, 112) &&
                  !crossing.texture_memory_shared_for_test(111, 113) &&
                  crossing.preload_memory_block_count() == 2 &&
                  crossing.preload_allocation_attempts() == 3,
              "Crossing a memory block bound did not allocate a separate bounded block");
      crossing.finalize_preload();
      crossing.end_preload();
      for (const auto key : {111ULL, 112ULL, 113ULL})
        crossing.discard_texture_for_test(key);
      require(crossing.preload_memory_block_count() == 0,
              "Cross-block texture teardown retained pooled device memory");

      Renderer block_budget;
      block_budget.set_preload_memory_block_cap_for_test(stride * 2);
      block_budget.begin_preload();
      const auto initial_block_budget_bytes = block_budget.tracked_device_local_bytes();
      const auto initial_block_budget_allocations = block_budget.live_allocation_count();
      PreloadFaultInjection block_cap{};
      block_cap.override_budget = true;
      block_cap.synthetic_heap_budget_bytes = kMinimumPreloadHeadroomBytes;
      block_budget.set_preload_fault(block_cap);
      const bool block_admitted = block_budget.preload_texture(texture(131));
      // With no queued work, failed preload releases the initialization staging
      // allocation. The denied image block must never enter the live ledger.
      require(!block_admitted && block_budget.preload_stopped() &&
                  block_budget.preload_stop_info().reason == PreloadStopReason::budget_denied &&
                  block_budget.preload_stop_info().requested_bytes == stride * 2 &&
                  block_budget.preload_memory_block_count() == 0 &&
                  block_budget.live_allocation_count() + 1 == initial_block_budget_allocations &&
                  block_budget.preload_allocation_attempts() == 1 &&
                  block_budget.preload_allocation_successes() == 0 &&
                  block_budget.tracked_device_local_bytes() == initial_block_budget_bytes &&
                  !block_budget.partial_texture(131),
              "Pool admission did not account for the complete block before allocating it");
      block_budget.finalize_preload();
      block_budget.end_preload();

      for (const auto result : {VK_ERROR_OUT_OF_DEVICE_MEMORY, VK_ERROR_OUT_OF_HOST_MEMORY}) {
        Renderer pool_oom;
        pool_oom.set_preload_batch_cap_for_test(256);
        pool_oom.set_preload_memory_block_cap_for_test(stride * 2);
        pool_oom.begin_preload();
        PreloadFaultInjection fault{};
        fault.override_budget = true;
        fault.synthetic_heap_budget_bytes = 16 * gib;
        fault.fail_on_allocation_attempt = 3; // New block after two queued image slices.
        fault.injected_result = result;
        pool_oom.set_preload_fault(fault);
        require(pool_oom.preload_texture(texture(121)) && pool_oom.preload_texture(texture(122)) &&
                    !pool_oom.preload_texture(texture(123)) && pool_oom.preload_stopped() &&
                    pool_oom.preload_memory_block_count() == 1 &&
                    pool_oom.preload_pending_count() == 2 &&
                    pool_oom.preload_allocation_attempts() == 3 &&
                    pool_oom.preload_allocation_successes() == 2 &&
                    !pool_oom.partial_texture(123) && !pool_oom.texture_resident(121),
                "Pool-growth OOM damaged queued slices or published success before completion");
        pool_oom.finalize_preload();
        pool_oom.end_preload();
        require(pool_oom.texture_resident(121) && pool_oom.texture_resident(122) &&
                    !pool_oom.texture_resident(123) && pool_oom.uploads == 2 &&
                    pool_oom.preload_batch_submissions() == 1,
                "Pool-growth OOM did not safely complete earlier queued texture slices");
        pool_oom.discard_texture_for_test(121);
        pool_oom.discard_texture_for_test(122);
        require(pool_oom.preload_memory_block_count() == 0,
                "Pool-growth OOM left a shared memory block after final owner release");
      }

      Renderer limited;
      limited.set_preload_batch_cap_for_test(32);
      limited.set_preload_memory_block_cap_for_test(1);
      limited.begin_preload();
      require(limited.preload_texture(texture(21)) && limited.preload_texture(texture(22)) &&
                  limited.preload_texture(texture(23)),
              "Small batch cap rejected resources that fit individually");
      require(limited.preload_batch_submissions() == 1 && limited.uploads == 2 &&
                  limited.preload_pending_count() == 1 && limited.texture_resident(21) &&
                  !limited.texture_resident(23),
              "Crossing the batch byte cap did not flush only the earlier resources");
      limited.finalize_preload();
      limited.end_preload();
      require(limited.preload_batch_submissions() == 2 && limited.uploads == 3 &&
                  limited.preload_peak_bytes() <= 32 && limited.texture_staging_size() == 32 &&
                  limited.preload_pending_count() == 0,
              "Preload staging or queued payload exceeded the hard byte cap");
      limited.begin_preload();
      TextureRef oversized{24, 1, 4, 4, TexFormat::rgba8888, {},
                           std::vector<std::uint32_t>(16, 0xffffffff)};
      require(!limited.preload_texture(oversized) && limited.preload_stopped() &&
                  !limited.partial_texture(24) && !limited.texture_resident(24) &&
                  limited.preload_allocation_attempts() == 4,
              "Oversized optional texture exceeded the cap or left a partial cache entry");
      require(limited.preload_stop_info().reason == PreloadStopReason::oversized_upload &&
                  limited.preload_stop_info().requested_bytes > 32,
              "Oversized optional texture was not reported as an oversized upload");
      limited.finalize_preload();
      limited.end_preload();

      for (const auto result : {VK_ERROR_OUT_OF_DEVICE_MEMORY, VK_ERROR_OUT_OF_HOST_MEMORY}) {
        Renderer interrupted(Renderer::ColorTarget::rgba8, {}, {1, 1, 1, false}, true);
        interrupted.set_preload_batch_cap_for_test(256);
        // Force resource allocations to the dedicated path so this fixture
        // injects native OOM after earlier resources were queued. Pool-growth
        // OOM and shared-block lifetime are checked separately below.
        interrupted.set_preload_memory_block_cap_for_test(1);
        interrupted.begin_preload();
        PreloadFaultInjection fault{};
        fault.override_budget = true;
        fault.synthetic_heap_budget_bytes = 16 * gib;
        // Geometry local memory, shared staging and the first image succeed.
        fault.fail_on_allocation_attempt = 4;
        fault.injected_result = result;
        interrupted.set_preload_fault(fault);
        require(interrupted.preload_model_geometry(geometry) &&
                    interrupted.preload_texture(texture(31)) &&
                    interrupted.preload_pending_count() == 2 &&
                    !interrupted.model_uploaded(geometry.key) && !interrupted.texture_resident(31),
                "OOM fixture did not queue both resource kinds before failure");
        require(!interrupted.preload_texture(texture(32)) && interrupted.preload_stopped() &&
                    interrupted.preload_allocation_attempts() == 4 &&
                    interrupted.preload_allocation_successes() == 3 &&
                    interrupted.preload_pending_count() == 2 &&
                    interrupted.preload_batch_submissions() == 0 &&
                    interrupted.texture_staging_mapped() &&
                    interrupted.texture_staging_size() == 256 &&
                    !interrupted.partial_texture(32) && !interrupted.texture_resident(32) &&
                    !interrupted.model_uploaded(geometry.key) && !interrupted.texture_resident(31),
                "Midbatch OOM freed queued staging or published a failed upload");
        interrupted.finalize_preload();
        interrupted.end_preload();
        require(interrupted.preload_batch_submissions() == 1 &&
                    interrupted.preload_pending_count() == 0 && interrupted.uploads == 1 &&
                    interrupted.model_uploads == 1 && interrupted.model_uploaded(geometry.key) &&
                    interrupted.texture_resident(31) && !interrupted.texture_resident(32),
                "Midbatch OOM did not safely complete earlier queued uploads");
      }

      Renderer abandoned;
      abandoned.set_preload_batch_cap_for_test(32);
      abandoned.begin_preload();
      require(abandoned.preload_texture(texture(41)), "Could not queue abandonment fixture");
      Scene empty_scene;
      bool rejected_render = false;
      try {
        abandoned.render(empty_scene);
      } catch (const std::runtime_error &) {
        rejected_render = true;
      }
      require(rejected_render, "Rendering was allowed to reset an open preload command buffer");
      abandoned.end_preload();
      require(abandoned.preload_batch_submissions() == 0 &&
                  abandoned.preload_pending_count() == 0 && !abandoned.partial_texture(41) &&
                  !abandoned.texture_resident(41) && abandoned.uploads == 0,
              "Noexcept cleanup submitted abandoned commands or leaked a success state");
      abandoned.begin_preload();
      require(abandoned.preload_texture(texture(41)), "Abandoned preload could not be retried");
      abandoned.finalize_preload();
      abandoned.end_preload();
      require(abandoned.preload_batch_submissions() == 1 && abandoned.texture_resident(41),
              "Retry did not reset abandoned preload recording state");
    }

    // Insert farther native resources before nearer ones, plus an unused CPU
    // albedo. Selection must follow live player/proximity, not load/list order.
    zmod::Model far_model = source_model, near_model = source_model;
    zmod::Material far_material = source_material, near_material = source_material;
    zmod::Polygon far_polygon = source_polygon, near_polygon = source_polygon;
    far_polygon.material = &far_material;
    near_polygon.material = &near_material;
    far_model.polygons = &far_polygon;
    near_model.polygons = &near_polygon;
    std::unique_ptr<zcls::Node, int (*)(zcls::Node *)> far_node(
        zcls::object3d_create(), zcls::tree_destroy);
    std::unique_ptr<zcls::Node, int (*)(zcls::Node *)> near_node(
        zcls::object3d_create(), zcls::tree_destroy);
    require(far_node && near_node, "Could not create preload priority nodes");
    struct ClearModels {
      zcls::Node *far_node, *near_node;
      ~ClearModels() { far_node->model = near_node->model = nullptr; }
    } clear_models{far_node.get(), near_node.get()};
    far_node->model = &far_model;
    near_node->model = &near_model;
    auto far_asset = std::make_shared<zcls::SourceAsset>();
    auto near_asset = std::make_shared<zcls::SourceAsset>();
    far_asset->name = "unmatched_far.flt";
    near_asset->name = "unmatched_near.flt";
    far_node->source_asset = far_asset;
    near_node->source_asset = near_asset;
    zcls::object3d_set_translation(far_node.get(), 100, 0, 0);
    zcls::object3d_set_translation(near_node.get(), 10, 0, 0);
    mech3::Mech player{};
    player.target_node = root.get();
    struct PlayerBinding {
      mech3::Mech *previous_player = mech3::world().player;
      mech3::Mech *previous_mission_player = mech3::world().mission_player;
      ~PlayerBinding() {
        mech3::world().player = previous_player;
        mech3::world().mission_player = previous_mission_player;
      }
    } player_binding;
    mech3::world().player = mech3::world().mission_player = &player;
    const uint8_t native_pixels[16] = {0, 255, 0, 255, 0, 255, 0, 255,
                                       0, 255, 0, 255, 0, 255, 0, 255};
    zimg::TextureEntry far_texture{}, near_texture{};
    zvid::D3DTexture far_surface{}, near_surface{};
    far_texture.surface = &far_surface;
    near_texture.surface = &near_surface;
    far_material.flags = near_material.flags = 1;
    far_material.texture = &far_texture;
    near_material.texture = &near_texture;

    // Match the recovery path's GPU submission and lighting. The fixture's
    // earlier reference can use CPU geometry, and native albedos are lit.
    auto recovery_options = options;
    recovery_options.geometry = "partial";
    auto recovery_control = make_check_renderer(window, backend, quality, recovery_options);
    recovery_control->set_viewport(0, 0, 64, 64);
    mw34::materials::set_active_surface_key({2, 2, 1, 0x11223344ULL});
    const auto control_native_handle = recovery_control->create_texture(2, 2, native_pixels, 1);
    mw34::materials::clear_active_surface_key();
    recovery_control->mission_changed({});
    const auto expected_recovered = frame(recovery_control.get(), true, true);
    platform::DrawState control_native_state{};
    control_native_state.texture = control_native_handle;
    quad(*recovery_control, 0, 64, .1f, 0xffffffff, control_native_state);
    std::vector<uint32_t> expected_native;
    int control_width = 0, control_height = 0;
    require(recovery_control->read_back(&expected_native, &control_width, &control_height) &&
                control_width == 64 && control_height == 64 && !expected_native.empty(),
            "Clean lazy draw control did not render at the fixture extent");

    // Geometry local memory and shared staging are allocations 1 and 2.
    // Image allocation 3 is prepared albedo; material runs also allocate its
    // normal before native images. Failing the far native image retains the
    // completed nearby image, regardless of that earlier allocation count.
    for (const auto result : {VK_ERROR_OUT_OF_DEVICE_MEMORY, VK_ERROR_OUT_OF_HOST_MEMORY}) {
      for (std::size_t attempt : {2U, 3U, 4U, 5U}) {
        auto failure_options = options;
        failure_options.geometry = "partial";
        auto failure_renderer = make_check_renderer(window, backend, quality, failure_options);
        set_preload_memory_block_cap(*failure_renderer, 1);
        failure_renderer->set_viewport(0, 0, 64, 64);
        mw34::materials::set_active_surface_key({2, 2, 1, 0x11223344ULL});
        const auto unused = failure_renderer->create_texture(2, 2, native_pixels, 1);
        far_surface.handle = failure_renderer->create_texture(2, 2, native_pixels, 1);
        near_surface.handle = failure_renderer->create_texture(2, 2, native_pixels, 1);
        mw34::materials::clear_active_surface_key();
        mw34::vkscene::PreloadFaultInjection fault{};
        fault.override_budget = true;
        fault.synthetic_heap_budget_bytes = 16 * gib;
        fault.fail_on_allocation_attempt = attempt;
        fault.injected_result = result;
        set_preload_fault_injection(*failure_renderer, fault);
        failure_renderer->mission_changed({});
        const auto stopped = preload_test_state(*failure_renderer);
        const std::size_t nearby_native_attempt = materials ? 5U : 4U;
        const bool nearby_native_completed = attempt > nearby_native_attempt;
        const std::uint64_t expected_native_bytes =
            nearby_native_completed ? sizeof(native_pixels) : 0;
        require(stopped.last_preload_stopped && stopped.stop_log_lines == 1 &&
                    stopped.preload_allocation_attempts == attempt &&
                    stopped.preload_allocation_successes == attempt - 1 &&
                    stopped.stop_info.reason == (result == VK_ERROR_OUT_OF_DEVICE_MEMORY
                        ? PreloadStopReason::out_of_device_memory : PreloadStopReason::out_of_host_memory),
                "Mid-preload allocation failure did not stop optional warming once");
        require(!stopped.ordered_prepared_assets.empty() &&
                    stopped.ordered_prepared_assets.front() == "mech_authored.flt" &&
                    stopped.ordered_native_handles ==
                        std::vector<int32_t>{near_surface.handle, far_surface.handle} &&
                    stopped.native_staged_bytes == expected_native_bytes &&
                    is_texture_gpu_resident(*failure_renderer, near_surface.handle) ==
                        nearby_native_completed &&
                    has_texture_receipt(*failure_renderer, near_surface.handle) ==
                        nearby_native_completed &&
                    !is_texture_gpu_resident(*failure_renderer, far_surface.handle) &&
                    !has_texture_receipt(*failure_renderer, far_surface.handle) &&
                    !is_texture_gpu_resident(*failure_renderer, unused) &&
                    !has_texture_receipt(*failure_renderer, unused),
                "Preload priority or exclusion of unreferenced native albedos changed");
        require(!has_partial_model_buffer_entry(*failure_renderer, 0x4343000000000001ULL),
                "Failed geometry allocation poisoned the immutable buffer cache");
        if (stopped.failed_texture_handle >= 0) {
          require(!has_partial_texture_cache_entry(*failure_renderer, stopped.failed_texture_handle) &&
                      !is_texture_gpu_resident(*failure_renderer, stopped.failed_texture_handle) &&
                      !has_texture_receipt(*failure_renderer, stopped.failed_texture_handle) &&
                      shared_texture_staging_size(*failure_renderer) <= 64 * 1024 * 1024,
                  "Failed texture/staging allocation leaked a cache entry or success receipt");
        }
        require(stopped.pending_count == 0 && stopped.peak_batch_bytes <= 64 * 1024 * 1024,
                "Stopped preload left queued resources or exceeded its byte cap");
        if (attempt >= 4) {
          require(stopped.batch_submissions == 1 && stopped.peak_pending_count >= 2 &&
                      stopped.pending_texture_receipt_observations > 0 &&
                      stopped.premature_texture_receipts == 0 &&
                      stopped.prepared_staged_bytes > 0 &&
                      is_model_geometry_gpu_uploaded(*failure_renderer, 0x4343000000000001ULL),
                  "Frontend OOM did not finalize earlier queued geometry and texture receipts");
          require(!stopped.completed_texture_handles.empty(),
                  "Earlier queued prepared texture lost its completed receipt");
          for (const auto handle : stopped.completed_texture_handles)
            require(has_texture_receipt(*failure_renderer, handle) &&
                        is_texture_gpu_resident(*failure_renderer, handle),
                    "Frontend published a receipt for an incomplete preload image");
        }
        failure_renderer->begin_scene();
        failure_renderer->end_scene();
        require(preload_test_state(*failure_renderer).preload_allocation_attempts == attempt &&
                    preload_test_state(*failure_renderer).stop_log_lines == 1,
                "First-world pass repeated a stopped mission preload");
        const auto recovered = frame(failure_renderer.get(), true, true);
        require(recovered == expected_recovered && failure_renderer->asset_statistics().geometry_uploads == 1,
                "A real lazy draw failed after preload interruption or repeated warm geometry");
        platform::DrawState native_state{};
        native_state.texture = near_surface.handle;
        quad(*failure_renderer, 0, 64, .1f, 0xffffffff, native_state);
        std::vector<uint32_t> lazy_pixels;
        int lazy_width = 0, lazy_height = 0;
        require(failure_renderer->read_back(&lazy_pixels, &lazy_width, &lazy_height) &&
                    is_texture_gpu_resident(*failure_renderer, near_surface.handle) &&
                    lazy_width == control_width && lazy_height == control_height &&
                    lazy_pixels == expected_native,
                "Deferred native albedo did not upload lazily and draw after preload OOM");
      }
    }
    auto capped = make_check_renderer(window, backend, quality, recovery_options);
    capped->set_viewport(0, 0, 64, 64);
    mw34::vkscene::PreloadFaultInjection cap{};
    cap.override_budget = true;
    cap.synthetic_heap_budget_bytes = mw34::vkscene::kMinimumPreloadHeadroomBytes;
    set_preload_fault_injection(*capped, cap);
    capped->mission_changed({});
    const auto capped_state = preload_test_state(*capped);
    require(capped_state.last_preload_stopped &&
                capped_state.stop_info.reason == PreloadStopReason::budget_denied &&
                capped_state.stop_info.heap_budget_bytes == capped_state.stop_info.headroom_bytes &&
                capped_state.prepared_staged_bytes == 0 && capped_state.native_staged_bytes == 0,
            "Actual preload allocations crossed the synthetic budget cap");
    require(frame(capped.get(), true, true) == expected_recovered,
            "Budget-denied resources did not render through the ordinary lazy path");
  }
  require((first[20 * 64 + 23] & 0xff00) != 0 &&
              (first[20 * 64 + 23] & 255) == 0,
          "Prepared geometry/materials were not drawn or source geometry drew "
          "twice");
  const auto initial = renderer->asset_statistics();
  require(initial.gpu_model_draws > 0 && initial.geometry_uploads == 1,
          "Prepared rigid geometry did not use an immutable Vulkan upload");
  if (materials && threaded_checks) {
    // Compare an evolving worker-backed renderer against fresh-renderer GPU
    // baselines. Read the previous pending frame immediately after
    // notification: removing the drain or moving the settings update before it
    // changes that image, even if a later full-frame clear would conceal the
    // ordering bug.
    const platform::MissionIdentity missions[] = {
        {5, 1}, {0, 1}, {1, 2}, {9, 1}};
    std::vector<std::vector<uint32_t>> automatic_profiles;
    for (unsigned variant = 0; variant < 3; ++variant) {
      auto configured = options;
      configured.sun_explicit = variant == 1;
      configured.sun_azimuth = "45";
      configured.sun_elevation = "35";
      if (variant == 2)
        configured.lighting = "off";
      auto evolving = make_check_renderer(window, backend, quality, configured);
      evolving->set_viewport(0, 0, 64, 64);
      auto baseline = [&](platform::MissionIdentity mission) {
        auto fresh = make_check_renderer(window, backend, quality, configured);
        fresh->set_viewport(0, 0, 64, 64);
        fresh->mission_changed(mission);
        return frame(fresh.get());
      };
      const auto configured_pixels = baseline({});
      auto previous_pixels = frame(evolving.get());
      require(previous_pixels == configured_pixels,
              "Initial live lighting differs from fresh configuration");
      bool profile_changed = false, explicit_angle_changed = false;
      std::size_t mission_index = 0;
      for (const auto mission : missions) {
        const auto expected = baseline(mission);
        frame(evolving.get(), false);
        evolving->mission_changed(mission);
        std::vector<uint32_t> pending;
        int pending_width = 0, pending_height = 0;
        require(
            evolving->read_back(&pending, &pending_width, &pending_height) &&
                pending == previous_pixels,
            "Mission transition relit a pending frame or failed to drain the "
            "render worker");
        const auto actual = frame(evolving.get());
        require(actual == expected, "Live backend lighting update differs from "
                                    "a fresh-renderer baseline");
        profile_changed = profile_changed || actual != configured_pixels;
        if (variant == 2)
          require(actual == configured_pixels,
                  "Off-mode live renderer inherited a mission profile");
        if (variant == 0)
          automatic_profiles.push_back(actual);
        if (variant == 1)
          explicit_angle_changed =
              explicit_angle_changed ||
              actual != automatic_profiles.at(mission_index);
        ++mission_index;
        previous_pixels = actual;
      }
      if (variant == 1)
        require(explicit_angle_changed,
                "Explicit sun angles did not affect live profile lighting");
      if (variant != 2)
        require(
            profile_changed,
            "Live mission profile fixture produced no visible lighting change");
      evolving->mission_changed({0, 1});
      const auto known_before_reset = frame(evolving.get());
      if (variant != 2)
        require(
            known_before_reset != configured_pixels,
            "Reset control must start from distinct known-profile lighting");
      frame(evolving.get(), false);
      evolving->reset_scene_resources();
      require(frame(evolving.get()) == configured_pixels,
              "Scene reset retained previous mission lighting");
    }
  }
  matrix[9] = .5f;
  require(zcls::object3d_set_matrix(control, matrix) == 0,
          "Authored control pose could not change");
  const auto moved = frame();
  require(moved != first && (moved[20 * 64 + 23] & 0xffffff) == 0 &&
              renderer->asset_statistics().geometry_uploads == 1,
          "Native control motion did not move the prepared geometry or "
          "reuploaded its vertices");
  matrix[2] = 1;
  matrix[9] = 0;
  matrix[11] = -1.5f;
  require(zcls::object3d_set_matrix(control, matrix) == 0,
          "Authored clipped pose could not change");
  const auto clipped = frame();
  require(
      renderer->asset_statistics().cpu_clipped_triangles > 0 &&
          std::any_of(clipped.begin(), clipped.end(),
                      [](uint32_t value) { return (value & 0xffffff) != 0; }),
      "Prepared near-plane clipping did not produce visible bounded triangles");
  const uint8_t original[] = {64, 64, 64, 128};
  platform::DrawState named{};
  named.texture = renderer->create_named_texture("authored", 1, 1, original, 4);
  renderer->clear(true, 0, 0, 0);
  quad(*renderer, 0, 64, .5f, 0xffffffff, named);
  std::vector<uint32_t> named_pixels;
  int width = 0, height = 0;
  require(renderer->read_back(&named_pixels, &width, &height) &&
              (named_pixels[32 * 64 + 32] >> 24) == 128 &&
              (named_pixels[32 * 64 + 32] & 255) == 0,
          "Prepared named texture did not retain its source alpha mask");
  const uint8_t transparent[] = {64, 64, 64, 0};
  renderer->update_texture(named.texture, 1, 1, transparent);
  renderer->clear(true, 0, 0, 0);
  quad(*renderer, 0, 64, .5f, 0xffffffff, named);
  require(
      renderer->read_back(&named_pixels, &width, &height) &&
          named_pixels[32 * 64 + 32] == 0,
      "Prepared texture reload lost transparent pixels or retained old alpha");
  renderer->release_texture(named.texture);
  require(renderer->asset_statistics().named_textures == 2,
          "Named texture replacement was not recorded");

  constexpr unsigned flare_size = 64;
  std::vector<uint8_t> flare_source(flare_size * flare_size * 4, 255);
  for (unsigned y = 0; y < flare_size; ++y)
    for (unsigned x = 0; x < flare_size; ++x)
      flare_source[(std::size_t(y) * flare_size + x) * 4 + 3] =
          uint8_t((x * 3 + y * 5) % 256);
  const auto named_uploads_before_flare =
      renderer->asset_statistics().named_textures;
  const auto flare = renderer->create_named_texture(
      "lflare2", flare_size, flare_size, flare_source.data(), 1);
  auto flare_state = cc_mw3_re::testing::named_texture_state(*renderer, flare);
  require(flare_state.generated_rgba && flare_state.width == flare_size &&
              flare_state.height == flare_size &&
              flare_state.source_width == flare_size &&
              flare_state.source_height == flare_size,
          "Generated flare did not retain its source dimensions");
  const auto first_generation_pixels = flare_state.pixels;
  renderer->update_texture(flare, flare_size, flare_size, flare_source.data());
  flare_state = cc_mw3_re::testing::named_texture_state(*renderer, flare);
  require(flare_state.generated_rgba && flare_state.width == flare_size &&
              flare_state.height == flare_size &&
              flare_state.source_width == flare_size &&
              flare_state.source_height == flare_size &&
              flare_state.pixels == first_generation_pixels,
          "Generated flare reload changed dimensions or pixels");
  bool rejected_changed_flare_source = false;
  try {
    renderer->update_texture(flare, flare_size + 1, flare_size,
                             flare_source.data());
  } catch (const std::runtime_error &error) {
    rejected_changed_flare_source =
        std::string_view(error.what()) ==
        "Generated flare reload changed its source dimensions";
  }
  require(rejected_changed_flare_source,
          "Generated flare reload did not reject changed source dimensions");
  require(renderer->asset_statistics().named_textures ==
              named_uploads_before_flare,
          "Generated flare was counted as a prepared replacement upload");
  renderer->release_texture(flare);

  auto original_flare_assets = sdlfe::CoreCriticalAssets{};
  original_flare_assets.flare_style = "original";
  auto original_flare_renderer =
      make_check_renderer(window, backend, {}, original_flare_assets);
  const auto original_flare = original_flare_renderer->create_named_texture(
      "lflare2", flare_size, flare_size, flare_source.data(), 1);
  auto original_flare_state = cc_mw3_re::testing::named_texture_state(
      *original_flare_renderer, original_flare);
  std::vector<uint32_t> original_flare_pixels(flare_size * flare_size);
  std::memcpy(original_flare_pixels.data(), flare_source.data(),
              flare_source.size());
  require(!original_flare_state.generated_rgba &&
              original_flare_state.pixels == original_flare_pixels,
          "Original flare style changed uploaded source bytes");
  original_flare_renderer->update_texture(
      original_flare, flare_size, flare_size, flare_source.data());
  original_flare_state = cc_mw3_re::testing::named_texture_state(
      *original_flare_renderer, original_flare);
  require(!original_flare_state.generated_rgba &&
              original_flare_state.pixels == original_flare_pixels,
          "Original flare reload generated or changed source bytes");
  original_flare_renderer->release_texture(original_flare);

  renderer->reset_scene_resources();
  matrix[2] = matrix[9] = matrix[11] = 0;
  require(zcls::object3d_set_matrix(control, matrix) == 0,
          "Authored pose could not reset");
  require(frame() == first &&
              renderer->asset_statistics().geometry_uploads == 2,
          "Prepared scene reload reused stale geometry or changed its pixels");
  if (!materials)
    return;
  require(renderer->asset_statistics().lit_draws > 0 &&
              renderer->asset_statistics().normal_draws > 0,
          "Prepared materials did not reach a per-pixel normal-map draw");

  // Use a white albedo so lighting has a direct numeric oracle independent of
  // UV filtering.
  auto albedo = prepared_fixture::textures();
  albedo.replace(albedo.size() - 4, 4, std::string(4, char(0xff)));
  std::ofstream(folder / "textures.bin", std::ios::binary) << albedo;
  auto render_material = [&](const char *mode, uint32_t normal,
                             bool absent = false, bool mirror = false,
                             bool degenerate = false,
                             std::array<float, 3> source_normal = {0, 0, 1},
                             bool rank_one_uv = false, float roughness = -1.f,
                             float reflectivity = .04f, float metallic = 0.f) {
    zvid::set_render3d(nullptr);
    renderer.reset();
    std::ofstream(folder / "mesh.bin", std::ios::binary)
        << prepared_fixture::mesh(2, 0xffffffff, source_normal, mirror,
                                  degenerate, rank_one_uv);
    // Each deliberate UV/basis variant has its own authored compatibility hash.
    std::ifstream geometry(folder / "mesh.bin", std::ios::binary);
    const auto mesh = ::platform::prepared::read_mesh(geometry);
    const auto hash = mw34::materials::compute_mesh_uv_hash(
        mesh.batches, 0, mesh.batches.size());
    const auto metadata = surface_metadata(
        "authored:close", "authored", hash, roughness >= 0 ? roughness : .7f,
        reflectivity, metallic, roughness >= 0);
    std::ofstream(folder / "materials.bin", std::ios::binary)
        .write(metadata.data(), metadata.size());
    std::ofstream(folder / "normals.bin", std::ios::binary)
        << prepared_fixture::normals(normal, absent);
    options.lighting = mode;
    renderer = make_check_renderer(window, backend, quality, options);
    renderer->set_viewport(0, 0, 64, 64);
    zvid::set_render3d(renderer.get());
    return frame(nullptr, true,
                 options.geometry == "gpu" ||
                     options.geometry == "cpu-reference");
  };
  {
    // Measure the authored BRDF profile without the SDR display curve.
    const auto properties = SDL_GetWindowProperties(window);
    const auto hdr_property = SDL_PROP_WINDOW_HDR_ENABLED_BOOLEAN;
    const bool hdr_enabled = SDL_GetBooleanProperty(properties, hdr_property, false);
    require(SDL_SetBooleanProperty(properties, hdr_property, true),
            "Cannot isolate the BWSFM fixture from the SDR curve");
    const auto azimuth = options.sun_azimuth;
    const auto elevation = options.sun_elevation;
    const auto focal_x = context.fx_near, focal_y = context.fy_near;
    context.fx_near = context.fy_near = 2000;
    options.sun_azimuth = "270";
    options.sun_elevation = "1";
    auto response = [&](const char *mode, float roughness,
                        float reflectivity = .04f, float metallic = 1.f) {
      return render_material(mode, 0xffff8080, false, false, false, {0, 0, -1},
                             false, roughness, reflectivity, metallic);
    };
    const auto smooth = response("normal", .1f);
    const auto medium = response("normal", .7f);
    const auto rough = response("normal", 1.f);
    require(smooth != medium && medium != rough && smooth != rough,
            "BWSFM roughness did not change directional response");
    auto profile = [](const std::vector<uint32_t> &pixels) {
      int peak = 0, width = 0;
      for (int x = 0; x < 64; ++x)
        peak = std::max(peak, int(pixels[32 * 64 + x] & 255));
      const float half = 77.f + float(peak - 77) * .5f;
      for (int x = 0; x < 64; ++x)
        width += float(pixels[32 * 64 + x] & 255) >= half;
      return std::array<int, 2>{peak, width};
    };
    const auto smooth_profile = profile(smooth);
    const auto medium_profile = profile(medium);
    const auto rough_profile = profile(rough);
    std::fprintf(stderr,
                 "[BWSFM_PROFILE] roughness=.1 peak=%d width=%d; "
                 ".7 peak=%d width=%d; 1 peak=%d width=%d\n",
                 smooth_profile[0], smooth_profile[1], medium_profile[0],
                 medium_profile[1], rough_profile[0], rough_profile[1]);
    // The LDR smooth peak can saturate; the finite panel also bounds width.
    require(smooth_profile[0] > medium_profile[0] &&
                medium_profile[0] > rough_profile[0] &&
                smooth_profile[1] < medium_profile[1] &&
                medium_profile[1] <= rough_profile[1],
            "BWSFM highlight peak/width did not track roughness");
    require(response("flat", .1f) == response("flat", 1.f),
            "BWSFM response leaked into flat mode");
    require(response("off", .1f) == response("off", 1.f),
            "BWSFM response leaked into off mode");
    require(response("normal", .7f, 0.f, 0.f) !=
                response("normal", .7f, .5f, 0.f),
            "BWSFM reflectivity did not affect dielectric response");
    require(response("normal", .7f, .04f, 0.f) != medium,
            "BWSFM metallic did not affect response");
    require(response("normal", -1.f) != medium,
            "Missing BWSFM record enabled material response");
    const auto geometry_mode = options.geometry;
    for (const char *mode : {"gpu", "cpu-reference"}) {
      options.geometry = mode;
      const auto actual = response("normal", .7f);
      for (size_t pixel = 0; pixel < actual.size(); ++pixel)
        for (unsigned shift : {0U, 8U, 16U})
          require(std::abs(int((actual[pixel] >> shift) & 255) -
                           int((medium[pixel] >> shift) & 255)) <= 2,
                  "BWSFM GPU/reference response differs from prepared TL");
    }
    options.geometry = geometry_mode;
    options.sun_azimuth = azimuth;
    options.sun_elevation = elevation;
    context.fx_near = focal_x;
    context.fy_near = focal_y;
    require(SDL_SetBooleanProperty(properties, hdr_property, hdr_enabled),
            "Cannot restore display mode after BWSFM check");
  }
  const auto flat = render_material("flat", 0xffd980d9);
  require(render_material("normal", 0xffff8080) == flat,
          "Neutral BWNRM2 map changed flat material lighting");
  require(render_material("normal", 0, true) == flat,
          "Explicit absent normal map changed flat material lighting");
  require(render_material("normal", 0xff808080) == flat,
          "Zero tangent vector produced invalid material lighting");
  const auto normal = render_material("normal", 0xffd980d9);
  const auto mirrored = render_material("normal", 0xffd980d9, false, true);
  const size_t centre = 32 * 64 + 32;
  require(int(normal[centre] & 255) > int(mirrored[centre] & 255) + 30 &&
              normal != flat,
          "Mirrored UV handedness or tangent normal response was lost");
  require(render_material("normal", 0xffd980d9, false, false, true) == flat,
          "Degenerate UVs did not retain the geometric normal");
  require(render_material("normal", 0xff80ff80, false, false, false, {0, 0, 1},
                          true) == flat,
          "Rank-one UVs did not retain finite geometric lighting");
  require(render_material("normal", 0xffd980d9, false, false, false, {0, 0, 1},
                          true) == flat,
          "Rank-one UVs accepted tangent perturbation");
  const auto off = render_material("off", 0xffd980d9);
  render_material("normal", 0xffd980d9);
  require(render_material("off", 0xffd980d9) == off,
          "Material mode leaked across renderer instances");

  matrix[0] = 1.7f;
  matrix[4] = .8f;
  matrix[8] = .5f;
  require(zcls::object3d_set_matrix(control, matrix) == 0,
          "Cannot stage nonuniform source scale");
  options.sun_azimuth = "-45";
  const auto scaled =
      render_material("flat", 0xffff8080, false, false, false, {1, 1, 1});
  const double nx = 1.0 / 1.7, ny = 1.0 / .8, nz = 1.0 / .5;
  const double len = std::hypot(nx, ny, nz);
  const double radians = 3.14159265358979323846 / 180;
  const double direct = std::max(
      0.0, ((nx - nz) * std::cos(35 * radians) * std::cos(45 * radians) +
            ny * std::sin(35 * radians)) /
               len);
  const bool hdr_enabled = SDL_GetBooleanProperty(
      SDL_GetWindowProperties(window), SDL_PROP_WINDOW_HDR_ENABLED_BOOLEAN,
      false);
  const double ambient = hdr_enabled ? .30 : .36;
  const auto display_red = [hdr_enabled](double red) {
    red = std::clamp(red, 0.0, 1.0);
    return int(std::lround(
        red * (hdr_enabled ? 1.0 : 1.0 + .78 * (1.0 - red)) * 255));
  };
  const int expected = display_red(ambient + .85 * direct);
  require(
      std::abs(int((scaled[centre] >> 16) & 255) - expected) <= 1,
      "Nonuniform source scale did not use inverse-transpose material normals");
  options.sun_azimuth = "90";
  const auto scaled_map = render_material("normal", 0xffd980d9);
  // The native XY scale gives the cotangent frame a 0.8/1.7 axis ratio.
  // Transforming positions with the normal matrix would invert that ratio.
  const double ratio = .8 / 1.7;
  const double mapped_z = 1.0 / std::sqrt(1 + ratio * ratio);
  const int mapped_expected =
      display_red(ambient + .85 * std::cos(35 * radians) * mapped_z);
  require(
      std::abs(int((scaled_map[centre] >> 16) & 255) - mapped_expected) <= 1,
      "Tangent basis used normal coordinates instead of true world positions");

  matrix[0] = matrix[4] = matrix[8] = 1;
  matrix[2] = 1;
  matrix[11] = -1.5f;
  require(zcls::object3d_set_matrix(control, matrix) == 0,
          "Cannot stage clipped material source");
  options.sun_azimuth = "45";
  const auto clipped_flat =
      render_material("flat", 0xffff8080, false, false, false, {1, 0, 1});
  const auto clipped_normal =
      render_material("normal", 0xffd980d9, false, false, false, {1, 0, 1});
  const int clipped_expected = display_red(
      ambient + .85 * std::cos(35 * radians) * std::sin(45 * radians));
  require(
      std::abs(int((clipped_flat[centre] >> 16) & 255) - clipped_expected) <= 1,
      "Clipped geometry lost its authored smooth normals");
  require(clipped_normal != clipped_flat &&
              renderer->asset_statistics().normal_draws > 0 &&
              renderer->asset_statistics().cpu_clipped_triangles > 0,
          "Clipped prepared geometry lost per-pixel normal response");

  // Black albedo isolates native fog from the lighting equation. Geometry has
  // varying depth, so this catches interpolation changes and accidental sky
  // dithering.
  const auto saved_fog = zmod::fog();
  auto &fog = zmod::fog();
  fog = {};
  fog.on = 1;
  fog.far_range = 10;
  fog.far_sq = 100;
  fog.inv_range = .1f;
  fog.alt_low = 1;
  fog.alt_high = 100;
  fog.inv_alt = 1.f / 99;
  fog.color[0] = .13f;
  fog.color[1] = .37f;
  fog.color[2] = .61f;
  albedo.replace(albedo.size() - 4, 4, std::string(4, char(0)));
  std::ofstream(folder / "textures.bin", std::ios::binary) << albedo;
  const auto clipped_fog = render_material("off", 0xffff8080);
  require(render_material("normal", 0xffff8080) == clipped_fog,
          "Clipped material lighting changed native fog");
  matrix[11] = 2.5f;
  require(zcls::object3d_set_matrix(control, matrix) == 0,
          "Cannot stage varying-depth fog source");
  const auto gpu_fog = render_material("off", 0xffff8080);
  require(render_material("normal", 0xffff8080) == gpu_fog,
          "Rigid material lighting changed native fog");
  platform::DrawState hud;
  hud.sharp = hud.depth_always = true;
  quad(*renderer, 0, 16, .5f, 0xff112233, hud);
  std::vector<uint32_t> composed;
  require(renderer->read_back(&composed, &width, &height) &&
              composed[8 * 64 + 8] == 0xff112233 &&
              composed[centre] == gpu_fog[centre],
          "Prepared lighting changed sharp HUD composition or existing world "
          "color");
  zmod::fog() = saved_fog;
  if (materials) {
    check_terrain_surface_normals(window, backend);
    check_native_sky_unlit(window, backend);
  }
}
} // namespace

#include "geometry_checks.inc"
#include "scene_binding_checks.inc"
#include "producer_view_checks.inc"
#include "parallax_checks.inc"
#include "platform_checks.inc"
#include "prepared_gpu_checks.inc"
#include "ultrawide_checks.inc"

void check_campaign_lighting_and_policy() {
  using namespace mw34::campaign;
  mw34::sun::Settings base{};
  base.enabled = true;
  const auto sdr = mw34::sun::display_ambient(base, true, false);
  require(sdr.ambient == base.ambient * 1.2f && sdr.color == base.color &&
              sdr.strength == base.strength && sdr.sdr_shadow_lift == .78f,
          "SDR should boost only ambient light");
  require(mw34::sun::display_ambient(base, true, true).ambient == base.ambient &&
              mw34::sun::display_ambient(base, false, false).ambient == base.ambient,
          "HDR and lighting-off should retain authored ambient");
  const auto c1m2_lift =
      mission_sun_settings(base, resolve_mission_lighting("c1m2"), true, false,
                           nullptr, "c1m2");
  const auto c1m1_lift =
      mission_sun_settings(base, resolve_mission_lighting("c1m1"), true, false,
                           nullptr, "c1m1");
  require(c1m2_lift.sdr_extra_shadow_lift > 0.f &&
              c1m1_lift.sdr_extra_shadow_lift == 0.f &&
              base.sdr_extra_shadow_lift == 0.f,
          "C1M2 SDR tuning leaked into other missions");
  const auto training = resolve_mission_lighting("t1m1");
  const auto lit = mission_sun_settings(base, training, true, false);
  require(lit.azimuth == 95.f && lit.elevation == 6.f && lit.strength == 1.05f,
          "Training lighting was not applied");
  const auto manual = mission_sun_settings(base, training, true, true);
  require(manual.azimuth == 45.f && manual.elevation == 35.f,
          "Explicit default sun angles were overwritten");
  const auto off = mission_sun_settings(base, training, false, false);
  require(off.strength == base.strength && off.color == base.color &&
              off.azimuth == base.azimuth,
          "Off-mode inherited campaign lighting");
  const auto restored = mission_sun_settings(
      base, resolve_mission_lighting("unknown"), true, false);
  require(restored.color == base.color && restored.ambient == base.ambient,
          "Unknown mission inherited stale lighting");
  require(
      mission_sun_settings(base, resolve_mission_lighting("c2m2"), true, false)
              .strength == 0.f,
      "Sealed mission retained directional sun");
  {
    const auto campaign_identity =
        platform::make_mission_identity(1, 1, 2, true);
    require(campaign_identity.world_index == 1 && campaign_identity.number == 2,
            "Campaign identity must retain coordinates");
    const auto training_identity =
        platform::make_mission_identity(4, 5, 1, true);
    require(training_identity.world_index == 5 && training_identity.number == 1,
            "Training identity must retain coordinates");
    const auto campaign_sun = mission_sun_settings(
        base,
        resolve_mission_lighting(canonical_mission_id(
            campaign_identity.world_index, campaign_identity.number)),
        true, false);
    require(campaign_sun.strength == 0.f, "Campaign c2m2 must be sealed");
    for (const auto identity :
         {platform::make_mission_identity(2, 1, 2, true),
          platform::make_mission_identity(3, 1, 2, true),
          platform::make_mission_identity(9, 1, 2, true),
          platform::make_mission_identity(1, 1, 2, false)}) {
      require(identity.world_index == -1 && identity.number == 0,
              "Non-campaign or failed load identity must be empty");
      const auto id =
          canonical_mission_id(identity.world_index, identity.number);
      require(id.empty(), "Non-campaign load acquired a campaign profile");
      const auto settings =
          mission_sun_settings(base, resolve_mission_lighting(id), true, false);
      require(settings.strength == base.strength &&
                  settings.color == base.color &&
                  settings.ambient == base.ambient,
              "Non-campaign or failed load must restore configured lighting");
    }
  }
  {
    platform::prepared::EnvironmentSelection selection{};
    selection.mission_ambient.emplace(
        "c1m1", platform::prepared::MissionAmbientOverride{
                    {0.18f, 0.22f, 0.32f}, 0.14f});
    auto resolve_sequence = [&](const platform::MissionIdentity &identity,
                                bool enabled, bool explicit_angles = false) {
      const auto id =
          canonical_mission_id(identity.world_index, identity.number);
      ResolvedMissionLighting resolved{};
      if (!id.empty())
        resolved = resolve_mission_lighting(id);
      return mission_sun_settings(base, resolved, enabled, explicit_angles,
                                  &selection, id);
    };
    const auto c1m1_overridden =
        resolve_sequence(platform::make_mission_identity(1, 0, 1, true), true);
    require(c1m1_overridden.ambient_color ==
                    std::array<float, 3>{0.18f, 0.22f, 0.32f} &&
                c1m1_overridden.ambient == 0.14f &&
                c1m1_overridden.azimuth == 245.0f &&
                c1m1_overridden.elevation == 7.0f &&
                c1m1_overridden.color ==
                    std::array<float, 3>{1.0f, 0.45f, 0.2f} &&
                c1m1_overridden.strength == 1.4f &&
                c1m1_overridden.night_world_gain == 1.0f &&
                !c1m1_overridden.suppress_sky,
            "c1m1 pack ambient override or untouched directional/policy fields "
            "mismatched");
    const auto c1m1_manual = resolve_sequence(
        platform::make_mission_identity(1, 0, 1, true), true, true);
    require(c1m1_manual.azimuth == base.azimuth &&
                c1m1_manual.elevation == base.elevation &&
                c1m1_manual.ambient_color ==
                    std::array<float, 3>{0.18f, 0.22f, 0.32f} &&
                c1m1_manual.ambient == 0.14f && c1m1_manual.strength == 1.4f,
            "Explicit sun angles with pack ambient override failed");
    const auto c1m2_builtin =
        resolve_sequence(platform::make_mission_identity(1, 0, 2, true), true);
    require(c1m2_builtin.ambient_color ==
                    std::array<float, 3>{0.18f, 0.22f, 0.32f} &&
                c1m2_builtin.ambient == 0.14f &&
                c1m2_builtin.azimuth == 210.0f &&
                c1m2_builtin.elevation == 25.0f &&
                c1m2_builtin.color ==
                    std::array<float, 3>{0.35f, 0.45f, 0.65f} &&
                c1m2_builtin.strength == 0.28f &&
                c1m2_builtin.night_world_gain == 0.24f &&
                !c1m2_builtin.suppress_sky,
            "Absent c1m2 pack entry did not restore c1m2 built-in ambient and "
            "directional fields");
    selection.mission_ambient["c1m1"] = {{0.85f, 0.65f, 0.35f}, 0.45f};
    const auto c1m1_distinct =
        resolve_sequence(platform::make_mission_identity(1, 0, 1, true), true);
    require(c1m1_distinct.ambient_color ==
                    std::array<float, 3>{0.85f, 0.65f, 0.35f} &&
                c1m1_distinct.ambient == 0.45f &&
                c1m1_distinct.strength == 1.4f,
            "Adjusted c1m1 pack ambient override was not applied");
    const auto c1m2_after_distinct =
        resolve_sequence(platform::make_mission_identity(1, 0, 2, true), true);
    require(c1m2_after_distinct.ambient_color ==
                    std::array<float, 3>{0.18f, 0.22f, 0.32f} &&
                c1m2_after_distinct.ambient == 0.14f &&
                c1m2_after_distinct.strength == 0.28f,
            "Transition to absent c1m2 leaked previous c1m1 pack ambient");
    for (const auto invalid_identity :
         {platform::MissionIdentity{},
          platform::make_mission_identity(1, 0, 1, false),
          platform::make_mission_identity(2, 0, 1, true)}) {
      const auto reset_settings = resolve_sequence(invalid_identity, true);
      require(reset_settings.ambient_color == base.ambient_color &&
                  reset_settings.ambient == base.ambient &&
                  reset_settings.color == base.color &&
                  reset_settings.strength == base.strength &&
                  reset_settings.azimuth == base.azimuth &&
                  reset_settings.elevation == base.elevation,
              "Invalid or reset mission identity did not return base settings");
    }
    const auto off_settings =
        resolve_sequence(platform::make_mission_identity(1, 0, 1, true), false);
    require(off_settings.ambient_color == base.ambient_color &&
                off_settings.ambient == base.ambient &&
                off_settings.color == base.color &&
                off_settings.strength == base.strength &&
                off_settings.azimuth == base.azimuth &&
                off_settings.elevation == base.elevation,
            "Lighting off did not ignore pack ambient override and return base");
    auto disabled_base = base;
    disabled_base.enabled = false;
    const auto base_off_settings = mission_sun_settings(
        disabled_base, resolve_mission_lighting("c1m1"), true, false,
        &selection, "c1m1");
    require(base_off_settings.ambient_color == disabled_base.ambient_color &&
                base_off_settings.ambient == disabled_base.ambient &&
                base_off_settings.strength == disabled_base.strength,
            "Disabled base lighting did not ignore pack ambient override");
  }
  unsigned identities = 0;
  for (int world = 0; world < 6; ++world)
    for (int number = 0; number <= 7; ++number) {
      const auto id = canonical_mission_id(world, number);
      if (!id.empty()) {
        ++identities;
        require(resolve_mission_lighting(id).has_profile,
                "Native mission identity failed profile lookup");
      }
    }
  require(identities == 24 && canonical_mission_id(4, 4) == "c4m4" &&
              canonical_mission_id(-1, 1).empty(),
          "Native mission mapping has wrong bounds");

  // 1. All 24 real mission IDs distinct and findable
  static constexpr const char *const kAllMissionIds[24] = {
      "t1m1", "t1m2", "t1m3", "t1m4", "c1m1", "c1m2", "c1m3", "c1m4",
      "c2m1", "c2m2", "c2m3", "c2m4", "c3m1", "c3m2", "c3m3", "c3m4",
      "c3m5", "c3m6", "c4m1", "c4m2", "c4m3", "c4m4", "c4m5", "c4m6"};

  const auto *fuel_depot = find_builtin_environment("c3m3");
  require(fuel_depot &&
              fuel_depot->sky_tint == std::array<float, 3>{2.60f, .70f, .35f} &&
              fuel_depot->sky_brightness == 1.15f &&
              fuel_depot->sky_grade == std::array<float, 3>{.78f, .75f, .60f},
          "Fuel Depot must use current authored mission sky values");
  const auto &db = builtin_mission_database();
  require(db.size() == 24,
          "Builtin mission database must contain exactly 24 profiles");

  for (size_t i = 0; i < 24; ++i) {
    const char *id = kAllMissionIds[i];
    const MissionEnvironment *env = find_builtin_environment(id);
    require(env != nullptr,
            "Mission profile must be found in builtin database");
    require(std::string_view(env->id) == id, "Mission environment ID mismatch");

    const auto resolved = resolve_mission_lighting(id);
    require(resolved.has_profile == true,
            "Resolved mission lighting must indicate has_profile == true");
    require(resolved.environment == env,
            "Resolved environment pointer mismatch");

    // Verify distinctness across database entries
    for (size_t j = i + 1; j < 24; ++j) {
      require(std::string_view(kAllMissionIds[i]) != kAllMissionIds[j],
              "Mission IDs must be distinct");
      require(find_builtin_environment(kAllMissionIds[i]) !=
                  find_builtin_environment(kAllMissionIds[j]),
              "Mission environment pointers must be distinct");
    }
  }

  // 2. Unknown case explicit fallback (no profile, stock fallback, no crash/log
  // spam)
  for (const char *unknown_id : {"", "unknown", "c0m0", "c9m9", "t2m1"}) {
    require(find_builtin_environment(unknown_id) == nullptr,
            "Unknown mission ID must return nullptr");
    const auto unk = resolve_mission_lighting(unknown_id);
    require(unk.has_profile == false,
            "Unknown mission must yield has_profile == false");
    require(unk.environment == nullptr,
            "Unknown mission must yield null environment");
    require(unk.policy.inside == false,
            "Unknown mission must default inside == false");
    require(unk.policy.suppress_sun == false,
            "Unknown mission must default suppress_sun == false");
    require(unk.policy.suppress_sky == false,
            "Unknown mission must default suppress_sky == false");
    require(unk.policy.sky_source == SkySource::OriginalClouds,
            "Unknown mission must default to SkySource::OriginalClouds");
  }

  // 3. Sealed policy independent of potentially contradictory profile input
  // Sealed missions: c2m2, c2m4, c3m5
  for (const char *sealed_id : {"c2m2", "c2m4", "c3m5"}) {
    require(sealed_mission(sealed_id) == true,
            "Expected sealed mission identity");
    const auto sealed_res = resolve_mission_lighting(sealed_id);
    require(sealed_res.policy.inside == true,
            "Sealed mission must enforce inside == true");
    require(sealed_res.policy.suppress_sun == true,
            "Sealed mission must suppress sun");
    require(sealed_res.policy.suppress_sky == true,
            "Sealed mission must suppress sky");
    require(sealed_res.policy.sky_source == SkySource::Interior,
            "Sealed mission must resolve to SkySource::Interior");

    // Independent of contradictory profile input: even if profile_interior ==
    // false
    const auto forced_ext = resolve_environment_policy(sealed_id, false);
    require(forced_ext.inside == true,
            "Sealed policy must override contradictory exterior flag");
    require(forced_ext.suppress_sun == true,
            "Sealed policy must override contradictory sun flag");
    require(forced_ext.suppress_sky == true,
            "Sealed policy must override contradictory sky flag");
    require(forced_ext.sky_source == SkySource::Interior,
            "Sealed policy must override contradictory sky source");
  }

  // Unsealed mission with profile_interior == true gets inside policy
  const auto unsealed_interior = resolve_environment_policy("c1m1", true);
  require(unsealed_interior.inside == true,
          "Profile interior flag must set inside == true");
  require(unsealed_interior.suppress_sun == true,
          "Profile interior flag must suppress sun");
  require(unsealed_interior.suppress_sky == true,
          "Profile interior flag must suppress sky");
  require(unsealed_interior.sky_source == SkySource::Interior,
          "Profile interior flag must set Interior sky");

  // Normal unsealed mission (c1m1)
  const auto c1m1_res = resolve_mission_lighting("c1m1");
  require(c1m1_res.policy.inside == false, "c1m1 must not be inside");
  require(c1m1_res.policy.suppress_sun == false, "c1m1 must not suppress sun");
  require(c1m1_res.policy.suppress_sky == false, "c1m1 must not suppress sky");
  require(c1m1_res.policy.sky_source == SkySource::Twilight,
          "c1m1 must have Twilight sky");

  // 4. Expected sky categories
  // ClearDay: t1m2, c2m1, c3m1, c3m2, c4m6
  for (const char *id : {"t1m2", "c2m1", "c3m1", "c3m2", "c4m6"}) {
    require(mission_sky_source(id) == SkySource::ClearDay,
            "Expected ClearDay sky source");
  }
  // Twilight: t1m1, t1m4, c1m1, c3m3, c3m4, c4m3, c4m4, c4m5
  for (const char *id :
       {"t1m1", "t1m4", "c1m1", "c3m3", "c3m4", "c4m3", "c4m4", "c4m5"}) {
    require(mission_sky_source(id) == SkySource::Twilight,
            "Expected Twilight sky source");
  }
  // ClearNight: c3m6
  require(mission_sky_source("c3m6") == SkySource::ClearNight,
          "c3m6 must be ClearNight");
  // DustHaze: c2m3
  require(mission_sky_source("c2m3") == SkySource::DustHaze,
          "c2m3 must be DustHaze");
  // Interior: c2m2, c2m4, c3m5
  for (const char *id : {"c2m2", "c2m4", "c3m5"}) {
    require(mission_sky_source(id) == SkySource::Interior,
            "Expected Interior sky source");
  }
  // OriginalClouds: t1m3, c1m2, c1m3, c1m4, c4m1, c4m2
  for (const char *id : {"t1m3", "c1m2", "c1m3", "c1m4", "c4m1", "c4m2"}) {
    require(mission_sky_source(id) == SkySource::OriginalClouds,
            "Expected OriginalClouds sky source");
  }

  // 5. Representative authored numeric values
  const auto *t1m1 = find_builtin_environment("t1m1");
  require(t1m1 && t1m1->azimuth == 95.0f && t1m1->elevation == 6.0f,
          "t1m1 sun angle mismatch");
  require(t1m1->sun_strength == 1.05f && t1m1->fog_distance == 1100.0f,
          "t1m1 metrics mismatch");

  const auto *t1m2 = find_builtin_environment("t1m2");
  require(t1m2 && t1m2->heat_shimmer == 0.70f && t1m2->azimuth == 115.0f,
          "t1m2 metrics mismatch");

  const auto *t1m3 = find_builtin_environment("t1m3");
  require(t1m3 && t1m3->rain_intensity == 0.70f && !t1m3->shadows,
          "t1m3 metrics mismatch");

  const auto *c1m1 = find_builtin_environment("c1m1");
  require(c1m1 && c1m1->azimuth == 245.0f && c1m1->elevation == 7.0f,
          "c1m1 sun angle mismatch");
  require(c1m1->sun_strength == 1.40f && c1m1->shadow_range == 300.0f,
          "c1m1 metrics mismatch");

  const auto *c1m2 = find_builtin_environment("c1m2");
  require(c1m2 && c1m2->env_lights.size() == 4 && c1m2->rain_intensity == 0.35f,
          "c1m2 light emitters mismatch");

  const auto *c1m3 = find_builtin_environment("c1m3");
  require(c1m3 && c1m3->has_lightning && c1m3->rain_intensity == 0.95f,
          "c1m3 storm metrics mismatch");

  const auto *c2m2 = find_builtin_environment("c2m2");
  require(c2m2 && c2m2->is_interior && c2m2->sun_strength == 0.0f,
          "c2m2 interior metrics mismatch");

  const auto *c3m5 = find_builtin_environment("c3m5");
  require(c3m5 && c3m5->env_lights.size() == 4 && c3m5->is_interior,
          "c3m5 interior light emitters mismatch");

  const auto *c4m1 = find_builtin_environment("c4m1");
  require(c4m1 && c4m1->env_lights.size() == 3 && c4m1->volcanic_ash == 0.75f &&
              c4m1->lava_glow == 0.85f,
          "c4m1 volcanic metrics mismatch");

  const auto *c4m6 = find_builtin_environment("c4m6");
  require(c4m6 && c4m6->azimuth == 110.0f && c4m6->elevation == 28.0f &&
              c4m6->sun_strength == 1.45f,
          "c4m6 metrics mismatch");

  std::fprintf(stderr, "check_campaign_lighting_and_policy: passed (24 mission "
                       "profiles, sealed maps, sky categories)\n");
}

void check_renderer_bridge_config() {
  mw34::materials::SurfaceNormals catalog;
  const mw34::materials::SurfaceKey water_key{64, 64, 1, 0x1234};
  catalog.bindings.emplace(water_key, 0);
  catalog.pack.images.push_back({"water", 1, 1, 0x5678, {}});
  mw34::detail::Bindings detail_bindings;
  mw34::detail::register_catalog(detail_bindings, catalog, 1, 7);
  const mw34::materials::SurfaceKey surf_key{32, 32, 1, 0x2345};
  mw34::materials::SurfaceNormals surf_catalog;
  surf_catalog.bindings.emplace(surf_key, 0);
  surf_catalog.pack.images.push_back({"surf", 1, 1, 0x6789, {}});
  mw34::detail::register_catalog(detail_bindings, surf_catalog, 2, 8);
  const mw34::materials::SurfaceKey cloud_key{128, 64, 1, 0x3456};
  mw34::materials::SurfaceNormals cloud_catalog;
  cloud_catalog.bindings.emplace(cloud_key, 0);
  cloud_catalog.pack.images.push_back({"cloud", 1, 1, 0x789a, {}});
  mw34::detail::register_catalog(detail_bindings, cloud_catalog, 3, 9);
  mw34::detail::Settings detail_settings;
  detail_settings.water = true;
  const auto *water_binding =
      mw34::detail::find_binding(detail_bindings, water_key, detail_settings);
  require(water_binding && water_binding->role == 1 &&
              water_binding->normal_index == 7,
          "exact water surface identity did not bind its detail role/image");
  detail_settings.clouds = true;
  const auto *surf_binding =
      mw34::detail::find_binding(detail_bindings, surf_key, detail_settings);
  const auto *cloud_binding =
      mw34::detail::find_binding(detail_bindings, cloud_key, detail_settings);
  require(surf_binding && surf_binding->role == 2 && cloud_binding &&
              cloud_binding->role == 3,
          "surf/cloud catalog identities did not bind their detail roles");
  detail_settings.water = false;
  require(!mw34::detail::find_binding(detail_bindings, water_key,
                                      detail_settings),
          "disabled water detail retained its role or image");
  require(!mw34::detail::find_binding(
              detail_bindings,
              mw34::materials::SurfaceKey{64, 64, 1, 0x9999}, detail_settings),
          "unmatched texture identity was not inferred as water");
  detail_settings.water = true;
  mw34::sun::Uniform detail_uniform{};
  mw34::detail::uniform(detail_uniform, water_binding->role, detail_settings,
                        2.0);
  require(detail_uniform.detail[0] == 1.0f && detail_uniform.detail[1] > 0,
          "enabled detail role did not reach the shader uniform path");
  detail_settings.water = false;
  mw34::sun::Uniform legacy_uniform{};
  mw34::detail::uniform(legacy_uniform, 1, detail_settings, 2.0);
  require(legacy_uniform.detail == std::array<float, 4>{} &&
              legacy_uniform.detail_motion == std::array<float, 4>{},
          "disabled surface detail changed the legacy shader uniform path");
  // A zero-only check cannot distinguish an untouched block from a cleared one.
  legacy_uniform.detail = {1.f, 2.f, 3.f, 4.f};
  legacy_uniform.detail_motion = {5.f, 6.f, 7.f, 8.f};
  const auto preserved_detail = legacy_uniform.detail;
  const auto preserved_motion = legacy_uniform.detail_motion;
  mw34::detail::uniform(legacy_uniform, 1, detail_settings, 2.0);
  require(legacy_uniform.detail == preserved_detail &&
              legacy_uniform.detail_motion == preserved_motion,
          "disabled surface detail overwrote existing uniform fields");

  // 1. Zero function-static env cache test
  require(mw34::detail::presentation_time(1, 10.5) == 10.5,
          "detail_fixed_time 10.5 mismatch");
  require(mw34::detail::presentation_time(1, 25.0) == 25.0,
          "detail_fixed_time 25.0 mismatch");
  require(mw34::detail::presentation_time(1, std::nullopt) >= 0.0,
          "detail_fixed_time dynamic mismatch");

  cc_mw3_re::RendererBridgeConfig c1;
  c1.world_scale_percent = 75;
  require(c1.world_scale_percent == 75, "world_scale_percent 75 mismatch");
  cc_mw3_re::RendererBridgeConfig c2;
  c2.world_scale_percent = 90;
  require(c2.world_scale_percent == 90, "world_scale_percent 90 mismatch");

  // 2. Config propagation via configure_bridge without env mutation
  sdlfe::CoreCriticalQuality quality{};
  quality.antialiasing = "fxaa";
  quality.anisotropy = "16";
  quality.draw_distance = 1600;

  sdlfe::CoreCriticalAssets assets{};
  assets.lighting = "normal";
  assets.geometry = "gpu";
  assets.sun_azimuth = "60";
  assets.sun_elevation = "40";
  assets.water_detail_explicit = true;
  assets.water_detail = true;
  assets.cloud_detail_explicit = true;
  assets.cloud_detail = true;

  auto cfg_dxgi = cc_mw3_re::configure_bridge(
      sdlfe::RendererBackend::core_critical_dxgi, quality, assets);
  require(cfg_dxgi.dxgi_present == true, "dxgi_present true mismatch");
  require(cfg_dxgi.fxaa == true, "fxaa propagation mismatch");
  require(cfg_dxgi.af_level == 16, "af_level propagation mismatch");
  require(cfg_dxgi.draw_distance == 1600,
          "draw-distance propagation mismatch");
  for (const unsigned draw_distance : {2400u, 3200u}) {
    auto extended_quality = quality;
    extended_quality.draw_distance = draw_distance;
    const auto extended_config = cc_mw3_re::configure_bridge(
        sdlfe::RendererBackend::core_critical_wsi, extended_quality, assets);
    require(extended_config.draw_distance == draw_distance,
            "extended draw-distance propagation mismatch");
  }
  auto invalid_quality = quality;
  invalid_quality.draw_distance = 1000;
  bool invalid_distance_rejected = false;
  try {
    (void)cc_mw3_re::configure_bridge(
        sdlfe::RendererBackend::core_critical_wsi, invalid_quality, assets);
  } catch (const std::runtime_error &) {
    invalid_distance_rejected = true;
  }
  require(invalid_distance_rejected, "unsupported draw distance was accepted");
  require(cfg_dxgi.normal_maps_enabled == true,
          "normal_maps_enabled propagation mismatch");
  require(cfg_dxgi.prepared_cache == true,
          "prepared_cache propagation mismatch");
  require(cfg_dxgi.sun == true, "sun propagation mismatch");
  require(cfg_dxgi.sun_normals == true, "sun_normals propagation mismatch");
  require(std::abs(cfg_dxgi.sun_azimuth - 60.0f) < 0.01f,
          "sun_azimuth propagation mismatch");
  require(std::abs(cfg_dxgi.sun_elevation - 40.0f) < 0.01f,
          "sun_elevation propagation mismatch");
  require(cfg_dxgi.world_scale_percent == 100,
          "world_scale_percent propagation mismatch");
  require(cfg_dxgi.temporal_inputs == false,
          "temporal_inputs propagation mismatch");
  require(cfg_dxgi.fixture_lights == false,
          "fixture_lights propagation mismatch");
  require(cfg_dxgi.water_detail && cfg_dxgi.cloud_detail,
          "surface detail launch options did not reach renderer config");
  sdlfe::CoreCriticalAssets local_light_assets{};
  local_light_assets.lighting = "normal";
  local_light_assets.geometry = "gpu";
  local_light_assets.dynamic_lighting_explicit = true;
  local_light_assets.dynamic_lighting = true;
  local_light_assets.effect_lights = true;
  local_light_assets.effect_light_catalog = "effects.bin";
  local_light_assets.fixture_lights = true;
  local_light_assets.mech_headlights = true;
  local_light_assets.stock_headlights = "stock-headlights.bin";
  local_light_assets.headlight_bindings = "headlights.txt";
  auto local_light_config = cc_mw3_re::configure_bridge(
      sdlfe::RendererBackend::core_critical_wsi, {}, local_light_assets);
  require(local_light_config.sun && local_light_config.effect_lights &&
              local_light_config.fixture_lights &&
              local_light_config.mech_headlights &&
              local_light_config.effect_light_catalog == "effects.bin" &&
              local_light_config.stock_headlights == "stock-headlights.bin" &&
              local_light_config.headlight_bindings == "headlights.txt",
          "explicit local-light launch options did not reach renderer config");
  const auto local_settings =
      mw34::effects::settings(local_light_config, true);
  require(local_settings.enabled && local_settings.fixtures,
          "effect-light settings ignored the renderer launch config");
  struct RestoreLightEnvironment {
    struct Value {
      const char *name;
      std::optional<std::string> previous;
    } values[9];

    explicit RestoreLightEnvironment(const std::array<const char *, 9> &names) {
      for (std::size_t i = 0; i < names.size(); ++i) {
        values[i].name = names[i];
        if (const char *value = std::getenv(names[i]))
          values[i].previous = value;
      }
    }

    ~RestoreLightEnvironment() {
      for (const auto &value : values)
        local_light_test_env(value.name,
                             value.previous ? value.previous->c_str() : nullptr);
    }
  } restore_light_environment({"MW34_EFFECT_LIGHTS", "MW34_FIXTURE_LIGHTS",
                               "MW34_MECH_HEADLIGHTS", "MW34_EFFECT_LIGHT_CATALOG",
                               "MW34_STOCK_HEADLIGHTS", "MW34_HEADLIGHT_BINDINGS",
                               "MW34_SURFACE_NORMALS", "MW34_WORLD_NORMALS",
                               "MW34_SUN_SHADOWS"});
  local_light_test_env("MW34_EFFECT_LIGHTS", "1");
  local_light_test_env("MW34_FIXTURE_LIGHTS", "1");
  local_light_test_env("MW34_MECH_HEADLIGHTS", "1");
  local_light_test_env("MW34_EFFECT_LIGHT_CATALOG", "diagnostic-effects.bin");
  local_light_test_env("MW34_STOCK_HEADLIGHTS", "diagnostic-headlights.bin");
  local_light_test_env("MW34_HEADLIGHT_BINDINGS", "diagnostic-bindings.txt");
  local_light_test_env("MW34_SURFACE_NORMALS", "diagnostic-surface.txt");
  local_light_test_env("MW34_WORLD_NORMALS", "diagnostic-world.txt");
  auto selected_environment_assets = local_light_assets;
  selected_environment_assets.environment_packs_explicit = true;
  const auto selected_environment_config = cc_mw3_re::configure_bridge(
      sdlfe::RendererBackend::core_critical_wsi, {}, selected_environment_assets);
  require(selected_environment_config.environment_packs_explicit &&
              selected_environment_config.surface_normal_catalog.empty() &&
              selected_environment_config.world_normal_manifest.empty(),
          "explicit environment selection retained diagnostic normal catalogs");
  local_light_test_env("MW34_SUN_SHADOWS", "1");
  sdlfe::CoreCriticalAssets shadow_assets{};
  shadow_assets.lighting = "normal";
  shadow_assets.geometry = "gpu";
  auto diagnostic_shadows = cc_mw3_re::configure_bridge(
      sdlfe::RendererBackend::core_critical_wsi, {}, shadow_assets);
  require(diagnostic_shadows.sun_shadows,
          "MW34_SUN_SHADOWS diagnostic setting was not read");
  shadow_assets.sun_shadows_explicit = true;
  shadow_assets.sun_shadows = false;
  const auto launcher_shadows_off = cc_mw3_re::configure_bridge(
      sdlfe::RendererBackend::core_critical_wsi, {}, shadow_assets);
  require(!launcher_shadows_off.sun_shadows,
          "explicit launcher shadows off did not override MW34_SUN_SHADOWS=1");
  local_light_test_env("MW34_SUN_SHADOWS", "0");
  shadow_assets.sun_shadows = true;
  const auto launcher_shadows_on = cc_mw3_re::configure_bridge(
      sdlfe::RendererBackend::core_critical_wsi, {}, shadow_assets);
  require(launcher_shadows_on.sun_shadows,
          "explicit launcher shadows on did not override MW34_SUN_SHADOWS=0");
  local_light_test_env("MW34_SUN_SHADOWS", "invalid");
  shadow_assets.sun_shadows = false;
  const auto explicit_shadows_invalid_env = cc_mw3_re::configure_bridge(
      sdlfe::RendererBackend::core_critical_wsi, {}, shadow_assets);
  require(!explicit_shadows_invalid_env.sun_shadows,
          "explicit launcher shadows choice did not override an invalid diagnostic value");
  shadow_assets.sun_shadows_explicit = false;
  bool invalid_diagnostic_rejected = false;
  try {
    (void)cc_mw3_re::configure_bridge(sdlfe::RendererBackend::core_critical_wsi,
                                      {}, shadow_assets);
  } catch (const std::runtime_error &) {
    invalid_diagnostic_rejected = true;
  }
  require(invalid_diagnostic_rejected,
          "invalid MW34_SUN_SHADOWS diagnostic value was silently accepted");
  local_light_test_env("MW34_SUN_SHADOWS", "1");
  shadow_assets = {};
  const auto shadows_without_sun = cc_mw3_re::configure_bridge(
      sdlfe::RendererBackend::core_critical_wsi, {}, shadow_assets);
  require(!shadows_without_sun.sun && !shadows_without_sun.sun_shadows,
          "diagnostic sun shadows remained enabled without sun lighting");
  local_light_assets.dynamic_lighting = false;
  auto disabled_light_config = cc_mw3_re::configure_bridge(
      sdlfe::RendererBackend::core_critical_wsi, {}, local_light_assets);
  require(disabled_light_config.sun && !disabled_light_config.effect_lights &&
              !disabled_light_config.fixture_lights &&
              !disabled_light_config.mech_headlights &&
              disabled_light_config.effect_light_catalog.empty() &&
              disabled_light_config.stock_headlights.empty() &&
              disabled_light_config.headlight_bindings.empty(),
          "explicit disabled dynamic lighting changed sun or retained local lights");
  sdlfe::CoreCriticalAssets no_sun_light_assets{};
  no_sun_light_assets.dynamic_lighting_explicit = true;
  no_sun_light_assets.dynamic_lighting = true;
  no_sun_light_assets.effect_lights = true;
  no_sun_light_assets.effect_light_catalog = "effects.bin";
  no_sun_light_assets.fixture_lights = true;
  no_sun_light_assets.mech_headlights = true;
  no_sun_light_assets.stock_headlights = "stock-headlights.bin";
  no_sun_light_assets.headlight_bindings = "headlights.txt";
  const auto no_sun_light_config = cc_mw3_re::configure_bridge(
      sdlfe::RendererBackend::core_critical_wsi, {}, no_sun_light_assets);
  require(!no_sun_light_config.sun && !no_sun_light_config.effect_lights &&
              !no_sun_light_config.fixture_lights &&
              !no_sun_light_config.mech_headlights &&
              no_sun_light_config.effect_light_catalog.empty() &&
              no_sun_light_config.stock_headlights.empty() &&
              no_sun_light_config.headlight_bindings.empty(),
          "local lights remained enabled without the sun pipeline");
  const auto no_sun_effect_settings =
      mw34::effects::settings(no_sun_light_config, false);
  require(!no_sun_effect_settings.enabled && !no_sun_effect_settings.fixtures,
          "local-light settings enabled effects without the sun pipeline");
  require(cfg_dxgi.shadow_batch == false, "shadow_batch propagation mismatch");

  auto cfg_wsi = cc_mw3_re::configure_bridge(
      sdlfe::RendererBackend::core_critical_wsi, {}, {});
  require(cfg_wsi.dxgi_present == false, "dxgi_present false mismatch");
  require(cfg_wsi.normal_maps_enabled == false,
          "normal_maps_enabled false mismatch");
  require(cfg_wsi.sun == false, "sun false mismatch");
  require(cfg_wsi.draw_distance == 800, "draw-distance default mismatch");

  // POM is opt-in and must not disappear when it is the only explicit option.
  sdlfe::CoreCriticalAssets pom_assets{};
  require(!pom_assets.pom, "POM must default off");
  require(pom_assets.empty(), "Default Core Critical assets must be empty");
  require(!cfg_dxgi.parallax_materials && !cfg_wsi.parallax_materials,
          "Default bridge configuration must leave POM off");
  pom_assets.pom = true;
  require(!pom_assets.empty(), "Explicit POM must make assets nonempty");
  pom_assets.pom = false;
  require(pom_assets.empty(), "POM off must preserve empty assets");
  pom_assets.environment_packs_explicit = true;
  require(!pom_assets.empty(),
          "Explicit empty environment-pack selection must reach the renderer");
  pom_assets.environment_packs_explicit = false;

  struct PomCase {
    sdlfe::RendererBackend backend;
    const char *lighting;
    bool pom;
    bool accepted;
  };
  const PomCase pom_cases[] = {
      {sdlfe::RendererBackend::core_critical_dxgi, "off", false, true},
      {sdlfe::RendererBackend::core_critical_wsi, "flat", false, true},
      {sdlfe::RendererBackend::sdl, "off", false, true},
      {sdlfe::RendererBackend::core_critical_dxgi, "normal", true, true},
      {sdlfe::RendererBackend::core_critical_wsi, "normal", true, true},
      {sdlfe::RendererBackend::core_critical_dxgi, "off", true, false},
      {sdlfe::RendererBackend::core_critical_wsi, "off", true, false},
      {sdlfe::RendererBackend::core_critical_dxgi, "flat", true, false},
      {sdlfe::RendererBackend::core_critical_wsi, "flat", true, false},
      {sdlfe::RendererBackend::sdl, "normal", true, false},
  };
  for (const auto &test : pom_cases) {
    pom_assets = {};
    pom_assets.lighting = test.lighting;
    pom_assets.pom = test.pom;
    bool rejected = false;
    try {
      const auto config =
          cc_mw3_re::configure_bridge(test.backend, {}, pom_assets);
      require(test.accepted, "Unsupported POM configuration was accepted");
      require(config.parallax_materials == test.pom,
              "Typed POM option did not reach the renderer bridge");
      require(config.normal_maps_enabled == (pom_assets.lighting == "normal"),
              "POM changed normal-map permission");
    } catch (const std::runtime_error &error) {
      require(std::string_view(error.what()).find("--cc-pom 1 requires ") == 0,
              "POM configuration failed for an unrelated reason");
      rejected = true;
    }
    require(rejected != test.accepted,
            "POM configuration acceptance mismatch");
  }

  check_campaign_lighting_and_policy();

  std::fprintf(stderr, "check_renderer_bridge_config: passed\n");
}

int main(int argc, char **argv) {
  bool geometry_check = false, ultrawide_check = false;
  bool native_wsi = false, quality_check = false, prepared_check = false,
       material_check = false, scene_bindings_check = false, pom_check = false,
       producer_view_check = false;
  sdlfe::CoreCriticalQuality quality;
  for (int i = 1; i < argc; ++i) {
    const std::string_view option(argv[i]);
    if (option == "--render-thread")
      threaded_checks = true;
    else if (option == "--wsi")
      native_wsi = true;
    else if (option == "--prepared")
      prepared_check = true;
    else if (option == "--geometry")
      geometry_check = true;
    else if (option == "--scene-bindings")
      scene_bindings_check = true;
    else if (option == "--producer-view")
      producer_view_check = true;
    else if (option == "--pom")
      pom_check = true;
    else if (option == "--ultrawide")
      ultrawide_check = true;
    else if (option == "--materials")
      prepared_check = material_check = true;
    else if (option == "--quality" && i + 1 < argc) {
      quality.antialiasing = argv[++i];
      quality.anisotropy = "16";
      quality_check = true;
    } else {
      std::fprintf(stderr, "usage: mw3ccvulkan_checks [--wsi] "
                           "[--prepared|--materials|--scene-bindings|--producer-view|--pom] "
                           "[--quality MODE]\n");
      return 1;
    }
  }
  if (!SDL_Init(SDL_INIT_VIDEO)) {
    std::fprintf(stderr, "%s\n", SDL_GetError());
    return 1;
  }
  auto *window = SDL_CreateWindow("Core Critical adapter checks", 32, 32,
                                  SDL_WINDOW_HIDDEN |
                                      (native_wsi ? SDL_WINDOW_VULKAN : 0));
  int result = 0;
  try {
    check_local_light_core();
    check_native_fixture_core();
    check_native_fixture_sources_core();
    check_renderer_bridge_config();
    cc_mw3_re::platform::run_platform_checks();
    require(window != nullptr, SDL_GetError());
    if (native_wsi) {
      auto *invalid =
          SDL_CreateWindow("Non-Vulkan window", 32, 32, SDL_WINDOW_HIDDEN);
      require(invalid != nullptr, SDL_GetError());
      bool rejected = false;
      try {
        auto renderer = make_check_renderer(
            invalid, sdlfe::RendererBackend::core_critical_wsi);
      } catch (const std::exception &error) {
        rejected =
            std::string_view(error.what()).find("SDL Vulkan surface:") == 0;
      }
      SDL_DestroyWindow(invalid);
      require(rejected,
              "Native WSI accepted a window without Vulkan surface support");

      auto tracker =
          std::make_shared<cc_mw3_re::platform::SdlWindowStateTracker>(window);
      require(tracker->is_owner_thread(),
              "Adapter check must execute on the SDL owner thread");
      bool foreign_sample_rejected = false;
      std::thread foreign([&] {
        try {
          tracker->sample_owner();
        } catch (const std::runtime_error &) {
          foreign_sample_rejected = true;
        }
      });
      foreign.join();
      require(foreign_sample_rejected,
              "Foreign thread must not query SDL window state");

      // Verify worker resident/resize handle resolution and coherent scope
      const auto native = cc_mw3_re::platform::get_window_native_handle(window);
      const auto hwnd = cc_mw3_re::platform::get_window_hwnd(window);
      bool worker_setup_ok = false;
      std::thread worker([&] {
        try {
          cc_mw3_re::platform::ExclusiveFullscreenHandler handler;
          handler.setup_swapchain_chain(native);
          const auto resolved =
              cc_mw3_re::platform::resolve_window_hwnd(native);
          if (resolved == hwnd) {
            worker_setup_ok = true;
          }
        } catch (...) {
          worker_setup_ok = false;
        }
      });
      worker.join();
      require(worker_setup_ok, "Worker thread must resolve cached native "
                               "window handle during swapchain setup");

      // Verify coherent snapshot and scope across queued job and owner update
      std::atomic<bool> worker_scope_ok{false};
      std::thread worker_job([&] {
        cc_mw3_re::platform::SdlWindowStateScope scope(tracker.get(),
                                                       {true, 1920, 1080});
        if (tracker->worker_drawable_width() == 1920 &&
            tracker->worker_drawable_height() == 1080 &&
            tracker->worker_visible()) {
          worker_scope_ok.store(true);
        }
      });
      tracker->sample_owner();
      worker_job.join();
      require(worker_scope_ok.load(), "Worker job must retain immutable "
                                      "captured state during owner sampling");
    }
    const auto backend = native_wsi
                             ? sdlfe::RendererBackend::core_critical_wsi
                             : sdlfe::RendererBackend::core_critical_dxgi;
    if (producer_view_check)
      check_producer_views(window, backend);
    else if (scene_bindings_check)
      check_scene_bindings(window, backend);
    else if (pom_check) {
      check_owned_rigid_capture(window, backend);
      check_parallax(window, backend);
    }
    else if (ultrawide_check)
      check_ultrawide(window, backend);
    else if (geometry_check) {
      check_radial_world_visibility();
      check_radial_model_views(window, backend);
      check_campaign_fog_color();
      check_distance_fog(window, backend);
      check_owned_rigid_capture(window, backend);
      check_strict_geometry(window, backend);
      const auto gpu = check_native_geometry(window, backend);
      const auto reference = check_native_geometry(window, backend, true);
      require(gpu.size() == reference.size(),
              "Geometry comparison lost a scenario");
      for (std::size_t frame = 0; frame < gpu.size(); ++frame) {
        require(gpu[frame].size() == reference[frame].size(),
                "Geometry comparison lost pixels");
        for (std::size_t pixel = 0; pixel < gpu[frame].size(); ++pixel)
          for (unsigned shift : {0U, 8U, 16U})
            require(std::abs(int((gpu[frame][pixel] >> shift) & 255) -
                             int((reference[frame][pixel] >> shift) & 255)) <=
                        2,
                    "GPU/reference transform, fog, clipping or normal debug "
                    "mismatch");
      }
      check_gpu_prepared(window, backend);
    } else if (prepared_check) {
      if (material_check && threaded_checks) {
        check_sealed_environment(window, backend);
        check_lab_preview_lighting(window, backend);
      }
      check_prepared(window, backend, quality, material_check);
    } else if (quality_check)
      check_quality(window, backend, quality);
    else {
      check_local_light_gpu(window, backend);
      check_native_fixture_gpu(window, backend);
      check_scene(window, backend);
      check_menu_background_gpu(window, backend);
    }
    if (native_wsi || material_check)
      check_fullscreen_resize(window, backend);
    // The staging checks write a temp effect-light catalog and set effect-light environment
    // variables (restored by their guards), so they run only in the --materials variants.
    if (material_check)
      check_local_light_staging(window, backend);
  } catch (const std::exception &error) {
    std::fprintf(stderr, "%s\n", error.what());
    result = 1;
  }
  if (window) {
    SDL_DestroyWindow(window);
  }
  SDL_Quit();
  return result;
}
