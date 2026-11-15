// Ours, not original code: Dear ImGui over the game while the game editor is
// up (docs/editor.md, Dear ImGui for the editor's dialogs). The editor's
// dialogs draw here; the editor's own menus stay zTwoD's. Made at the editor's
// first frame, so nothing of ImGui exists in play.
#pragma once

#include <functional>
#include <stdexcept>
#include <string>

#include <SDL3/SDL.h>

#include "frontend/sdl/editor_forms_imgui.h"
#include "frontend/sdl/editor_context.h"

namespace mech3 {
struct EditorForm;
}

namespace sdlfe {

class EditorUi : private EditorFrameBackend {
 public:
  // `up`: whether the editor is up (mech3::editor_state().active).
  EditorUi(SDL_Window* window, SDL_GPUDevice* device, std::function<bool()> up, EditorOwnedPaths paths);
  ~EditorUi();
  EditorUi(const EditorUi&) = delete;
  EditorUi& operator=(const EditorUi&) = delete;

  // SdlPump's overlay_event: true when the event is ImGui's and not the game's.
  bool event(const SDL_Event& e);
  // SdlRender3D's overlay: ImGui's frame drawn on the swapchain after the game's.
  void overlay(SDL_GPUCommandBuffer* cmd, SDL_GPUTexture* target, Uint32 width, Uint32 height);
  // ImGui's frame without the draw: what the dialogs want of the input is
  // decided here (the overlay runs it; the tests, on a hidden window, alone).
  bool step();
  bool active() const { return context_.active(); }
  // Consume the borrowed draw data synchronously while its CPU context is current.
  // Neither the backend nor the consumer may retain a context or draw-data borrow.
  bool frame(EditorFrameBackend& backend, const std::function<void(ImDrawData*)>& consume);
  // Select an existing CPU context even while inactive so its GPU owner can detach.
  // The operation runs synchronously and must not retain the current-context scope.
  bool with_current(const std::function<void()>& operation);
  // What the editor's dialogs draw, once a frame between ImGui's NewFrame and Render.
  std::function<void()> draw;
  bool started() const { return context_.started(); }
  // CPU startup from input must leave the concrete renderer untouched.
  bool renderer_started() const { context_.started(); return backend_started_; }

 private:
  void new_frame() override;
  EditorContext context_;
  SDL_Window* window_;
  SDL_GPUDevice* device_;
  bool backend_started_ = false;
  bool drawn_ = false;
};

// Borrowed by a renderer, owned on the SDL producer beside its lazy EditorUi.
// Acquisition may create the CPU owner only while active. Existing never creates
// it. Neither entry point, nor the returned borrow, belongs in a worker job.
class EditorUiSource {
 public:
  EditorUiSource() : owner_thread_(SDL_GetCurrentThreadID()) {}
  virtual ~EditorUiSource() = default;
  EditorUiSource(const EditorUiSource&) = delete;
  EditorUiSource& operator=(const EditorUiSource&) = delete;
  EditorUi* acquire_if_active() {
    require_owner();
    return acquire_active();
  }
  EditorUi* existing() const {
    require_owner();
    return existing_ui();
  }

 protected:
  virtual EditorUi* acquire_active() = 0;
  virtual EditorUi* existing_ui() const = 0;

 private:
  void require_owner() const {
    if (SDL_GetCurrentThreadID() != owner_thread_)
      throw std::logic_error("editor: source requires its producer thread");
  }
  const SDL_ThreadID owner_thread_;
};

}  // namespace sdlfe
