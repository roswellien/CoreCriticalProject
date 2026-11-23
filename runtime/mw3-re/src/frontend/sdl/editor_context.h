// CPU/platform lifetime for editor forms; concrete renderers own their backends.
#pragma once

#include <cfenv>
#include <cstdint>
#include <functional>
#include <string>

#include <SDL3/SDL.h>

struct ImGuiContext;
struct ImDrawData;

namespace sdlfe {

// Stable destinations supplied by the host, not filesystem admission or a lease.
struct EditorOwnedPaths {
  std::string ini_filename;
  std::string log_filename;
};

struct EditorFrameBackend {
  virtual ~EditorFrameBackend() = default;
  virtual void new_frame() = 0;
};

class EditorContext {
 public:
  EditorContext(SDL_Window* window, std::function<bool()> active, EditorOwnedPaths paths);
  ~EditorContext();
  EditorContext(const EditorContext&) = delete;
  EditorContext& operator=(const EditorContext&) = delete;

  // No renderer operation is reachable from event or start_if_active.
  bool event(const SDL_Event& event);
  bool start_if_active();
  bool started() const;
  bool active() const;

  // Owner-thread only. Scope, borrowed draw data and previous foreign context
  // must remain alive in that order; no scope may outlive this CPU owner.
  class Current {
   public:
    ~Current();
    Current(const Current&) = delete;
    Current& operator=(const Current&) = delete;
    Current(Current&&) = delete;
    Current& operator=(Current&&) = delete;

   private:
    friend class EditorContext;
    explicit Current(EditorContext& owner);
    EditorContext& owner_;
    ImGuiContext* previous_ = nullptr;
    std::fenv_t fp_{};
    uint32_t mxcsr_ = 0;
  };

  Current current_existing();  // Also usable while inactive for backend shutdown.
  bool frame(EditorFrameBackend& backend, const std::function<void()>& draw);
  // Current completed frame only. Borrow expires at the next frame/destruction.
  ImDrawData* draw_data();

 private:
  void require_owner_thread() const;
  void require_current() const;
  SDL_Window* window_;
  std::function<bool()> active_;
  EditorOwnedPaths paths_;
  SDL_ThreadID owner_thread_;
  ImGuiContext* context_ = nullptr;
  unsigned current_scopes_ = 0;
  bool frame_complete_ = false;
};

}  // namespace sdlfe
