#pragma once
#include <SDL3/SDL.h>

#include <array>
#include <chrono>
#include <cstdint>
#include <functional>
#include <map>
#include <memory>
#include <string>
#include <vector>

#include "frontend/sdl/sdl_fit.h"
#include "frontend/sdl/sdl_render3d.h"
#include "frontend/sdl/gpu_hud.h"
#include "platform/platform.h"
#include "platform/prepared_menu_background.h"

namespace zgame { class App; }

// The SDL3 program's Windows stand-ins (docs/program.md). FIX (A) each: the
// window and its GPU device, the message pump zGameApp::Run drives, the clock,
// the message boxes, and the 16-bit menu frame shown through the GPU.
namespace sdlfe {

class SdlInput;
class SdlMusicOutput;

// Shared by presentation and the asset-free GPU readback checks. Texture order
// is gain, added light, keyed native artwork; all handles remain caller-owned.
void draw_menu_background_gpu(FrameRenderer& renderer, int32_t background_texture,
                              const std::array<int32_t, 3>& textures,
                              const platform::MenuBackgroundGpuLayers& layers,
                              const platform::MenuBackgroundLayerRect& rectangle,
                              const platform::MenuBackgroundLayerRect* background_rectangle = nullptr);

// The main window ("Mech3Class", CWnd::CreateEx in 0x00482d10) with the GPU
// device behind Render3D. Made hidden at start so Render3D exists before the
// game creates its window; create() sizes, titles and keeps it hidden until
// UpdateWindow shows it.
class SdlWindow : public platform::Window {
 public:
  // The window and GPU device; false with SDL's error printed. `adopt`: the
  // launcher's window, taken instead of a new one (ours, docs/launcher.md).
  bool init(bool hidden_for_good, SDL_Window* adopt = nullptr,
            RendererBackend backend = RendererBackend::sdl, const CoreCriticalQuality& quality = {},
            const CoreCriticalAssets& assets = {});
  ~SdlWindow() override;
  uint32_t create(const std::string& title, int width, int height) override;
  void set_title(const std::string& title) override;
  void show() override;
  void client_size(int* width, int* height) override;
  void frame_size(int width, int height, int canvas_w = 0, int canvas_h = 0) override;
  // --window not given: the window takes the frame's shape (sdl_fit.h).
  void set_auto_size(bool on) { auto_size_ = on; }
  void set_fullscreen(bool on) { fullscreen_ = on; }  // ours: borderless, the desktop's size
  // Ours (Alt+Enter): fullscreen or a window now, for this run only; the
  // window takes the frame's shape at the size it would open with, kept
  // inside the display's usable area.
  void switch_fullscreen(bool on);
  bool fullscreen() const { return fullscreen_; }
  const FrameShape& shape() const { return shape_; }
  // A play run (not a check or a shot): a first start takes the desktop's size.
  void set_first_start_desktop(bool on) { first_start_desktop_ = on; }
  bool first_start_size(int* width, int* height) override;

  SDL_Window* sdl() const { return window_; }
  SDL_GPUDevice* device() const { return device_; }
  FrameRenderer* render() const { return render_.get(); }
  static constexpr uint32_t kHwnd = 0x00020000;  // the HWND handle the game keeps

 private:
  SDL_Window* window_ = nullptr;
  SDL_GPUDevice* device_ = nullptr;
  std::unique_ptr<FrameRenderer> render_;
  bool hidden_ = false;
  bool auto_size_ = false;
  bool fullscreen_ = false;
  bool first_start_desktop_ = false;
  void inside_usable(int* w, int* h) const;  // shrunk into the display's usable area
  int windowed_w_ = 1280, windowed_h_ = 960;  // the size create() asked for
  FrameShape shape_;
};

// The DirectDraw flip of the 16-bit back buffer (0x00576ea0): the pixels as a
// texture drawn over the whole window by Render3D.
class SdlScreen2D : public platform::Screen2D {
 public:
  explicit SdlScreen2D(FrameRenderer* render, const HudOptions& hud = {}, SDL_Window* window = nullptr,
                       const FrameShape* shape = nullptr);
  ~SdlScreen2D() override;
  void begin_overlay_16(const uint16_t*, int width, int height, int pitch) override;
  void cancel_overlay_16() override;
  void begin_menu_observation(const uint16_t*, int width, int height, int pitch) override;
  void cancel_menu_observation() noexcept override;
  void finish_menu_observation() noexcept override;
  void present_16(const uint16_t* pixels, int width, int height, int pitch, bool rgb565) override;
  // A 16-bit pixel (565, else 555) as the layer's RGBA8, opaque.
  static uint32_t rgba(uint16_t pixel, bool rgb565);
  // Every pixel of the layer still `key` (pitch in bytes): nothing to overlay.
  static bool layer_empty(const uint16_t* pixels, int width, int height, int pitch, uint16_t key);
  void overlay_16(const uint16_t* pixels, int width, int height, int pitch, bool rgb565, uint16_t key,
                  const uint8_t* alpha, const uint16_t* colour) override;
  int frames = 0;  // frames shown

 private:
  void upload(const uint16_t* pixels, int width, int height, int pitch, bool rgb565, bool keyed, uint16_t key,
              const uint8_t* alpha = nullptr, const uint16_t* colour = nullptr);
  void draw_layer(int width, int height, bool blend, bool sharp = true,
                  const platform::MenuBackgroundLayerRect* rectangle = nullptr);
  bool prepare_menu_gpu(const uint16_t* pixels, int width, int height, int pitch,
                        bool rgb565, bool* cache_hit);
  FrameRenderer* render_;
  std::unique_ptr<GpuHud> hud_;
  std::unique_ptr<platform::MenuBackgroundImage> menu_background_;
  SDL_Window* hud_window_{};
  const FrameShape* hud_shape_{};
  int32_t texture_ = -1;
  int tw_ = 0, th_ = 0;
  std::vector<uint8_t> rgba_;
  // The compositor shares texture_; only a native upload can validate these cached bytes.
  bool native_texture_current_ = false;
  std::vector<uint32_t> menu_composed_;
  platform::PreparedMenuBackgroundComposer menu_composer_;
  platform::PreparedMenuBackgroundComposer menu_gpu_composer_;
  platform::MenuBackgroundGpuLayers menu_gpu_layers_;
  std::array<int32_t, 3> menu_gpu_textures_{-1, -1, -1};
  int32_t menu_hd_texture_ = -1;
  int menu_gpu_width_ = 0, menu_gpu_height_ = 0;
  uint64_t menu_gpu_uploaded_revision_ = 0;
  bool menu_use_gpu_ = true;
  bool menu_gpu_available_ = true;
  bool hud_overlay_enabled_ = false;
  unsigned menu_hd_bound_width_ = 0;
  unsigned menu_hd_bound_height_ = 0;
  std::chrono::steady_clock::time_point menu_background_report_start_ = std::chrono::steady_clock::now();
  unsigned menu_background_report_frames_ = 0, menu_background_report_hits_ = 0, menu_background_report_gpu_frames_ = 0;
  double menu_background_report_milliseconds_ = 0;
  double menu_background_report_gpu_milliseconds_ = 0;
  bool menu_observation_active_{};
  bool menu_observation_enabled_{};
  bool menu_layout_active_{};
  bool menu_gpu_recording_{};
  bool menu_gpu_sealed_{};
  const uint16_t* menu_gpu_target_{};
  int menu_gpu_recorded_width_{};
  int menu_gpu_recorded_height_{};
  int menu_gpu_recorded_pitch_{};
  std::chrono::steady_clock::time_point menu_report_start_{};
  uint64_t menu_report_frames_{}, menu_report_images_{}, menu_report_text_hits_{},
      menu_report_fallbacks_{};
  std::map<std::string, uint64_t> menu_report_shadow_reasons_;
  bool live_menu_gpu_enabled() const;
  void set_menu_layout_active(bool active) noexcept;
};

// GetTickCount from the game's start, and Sleep. With `frame_ms` (ours,
// --frame-ms): each pass of the app's loop is that long and a sleep only
// adds its time, so a run's timing is the same however fast it draws.
class SdlClock : public platform::Clock {
 public:
  SdlClock() : start_(SDL_GetTicks()) {}
  uint32_t ticks_ms() override {
    if (frame_ms) return static_cast<uint32_t>(frames_ * frame_ms + slept_);
    return static_cast<uint32_t>(SDL_GetTicks() - start_);
  }
  void sleep(uint32_t ms) override {
    if (frame_ms) slept_ += ms;
    else SDL_Delay(ms);
  }
  // A pass of the app's loop. `paced` (a network run): the pass also waits
  // until the wall clock has caught up, as the other players run in real time.
  void frame() {
    ++frames_;
    if (!paced) return;
    const Uint64 due = start_ + frames_ * frame_ms + slept_, now = SDL_GetTicks();
    if (due > now) SDL_Delay(static_cast<Uint32>(due - now));
  }

  uint32_t frame_ms = 0;
  bool paced = false;

 private:
  Uint64 start_;
  uint64_t frames_ = 0, slept_ = 0;
};

// MessageBoxA: SDL's message box on the window.
class SdlAlert : public platform::Alert {
 public:
  explicit SdlAlert(SDL_Window* parent, bool headless) : parent_(parent), headless_(headless) {}
  void abort_message(const std::string& message) override;
  int32_t message_box(const std::string& text, const std::string& caption, uint32_t style) override;

 private:
  SDL_Window* parent_;
  bool headless_;  // log only (screenshots, scripted runs)
};

// The Windows message queue (zGameApp::Run, docs/game-loop.md): SDL's event
// queue. Input events go to the input layer, focus changes to the frame's
// OnActivate (0x00590c00), a finished music file becomes MM_MCINOTIFY
// (0x00590740), the window's close WM_CLOSE -> PostQuitMessage.
class SdlPump : public platform::MessagePump {
 public:
  SdlPump(SdlInput* input, zgame::App* app) : input_(input), app_(app) {}
  bool peek() override;
  bool pump() override;
  void wait(uint32_t ms) override;
  void post_quit() override;
  void raise_priority() override;

  // Asked before each look at the queue: true posts the quit (mw3 --frames).
  std::function<bool()> should_quit;
  // Ours: run at each look at the queue that finds no message, once a pass
  // of the app's loop that runs the game (--frame-ms steps its clock there).
  std::function<void()> each_pass;
  static Uint32 music_event();  // the user event SdlMusicOutput posts at a file's end
  // Ours: the window gained (true) or lost the focus (the sound mutes).
  std::function<void(bool)> focus_changed;
  // Ours: a run that ends by itself (--frames, --shot, a chain) stays active
  // when its window loses focus; the original's pause on deactivation
  // (0x00590c00) is for play. A check started behind another app, or on a
  // window the launcher handed over unfocused, idled for good otherwise.
  bool stays_active = false;
  // Ours: Alt+Enter, swallowed before the game sees the Enter.
  std::function<void()> toggle_fullscreen;
  // Ours: the game editor's ImGui sees each event first while it is up; true
  // keeps the event from zInput (editor_imgui.h). Window events go on as ever.
  std::function<bool(const SDL_Event&)> overlay_event;

  void handle(const SDL_Event& e);  // public for the tests

 private:
  SdlInput* input_;
  zgame::App* app_;
  bool quit_ = false;
  bool enter_swallowed_ = false;  // Alt+Enter's Enter is down: its release goes too
};

}  // namespace sdlfe
