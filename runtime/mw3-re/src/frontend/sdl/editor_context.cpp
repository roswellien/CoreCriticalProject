#include "frontend/sdl/editor_context.h"

#include <exception>
#include <filesystem>
#include <stdexcept>
#include <utility>

#if defined(_M_IX86) || defined(_M_X64) || defined(__SSE__)
#include <xmmintrin.h>
#endif

#include "imgui.h"
#include "backends/imgui_impl_sdl3.h"
#include "frontend/sdl/editor_forms_imgui.h"

namespace sdlfe {
namespace {
void save_fp(std::fenv_t& fp, uint32_t& mxcsr) {
  if (std::fegetenv(&fp) != 0) throw std::runtime_error("editor: cannot preserve FP environment");
#if defined(_M_IX86) || defined(_M_X64) || defined(__SSE__)
  mxcsr = _mm_getcsr();
#else
  mxcsr = 0;
#endif
}
void restore_fp(const std::fenv_t& fp, uint32_t mxcsr) noexcept {
  if (std::fesetenv(&fp) != 0) std::terminate();
#if defined(_M_IX86) || defined(_M_X64) || defined(__SSE__)
  _mm_setcsr(mxcsr);
#else
  (void)mxcsr;
#endif
}
struct FpScope {
  std::fenv_t fp{};
  uint32_t mxcsr = 0;
  FpScope() { save_fp(fp, mxcsr); }
  ~FpScope() { restore_fp(fp, mxcsr); }
};
bool valid_destination(const std::string& name) {
  if (name.empty() || name.find('\0') != std::string::npos) return false;
  const std::filesystem::path path(name);
  return path.is_absolute() && path.has_filename() && path.filename() != "." && path.filename() != "..";
}
// Recover a callback's incomplete Begin/Push stacks as supported by the pinned
// ImGui version, without changing the caller's normal error reporting policy.
void cancel_frame() {
  ImGuiIO& io = ImGui::GetIO();
  struct Restore {
    ImGuiIO& io;
    bool recovery, assertion, log, tooltip;
    ~Restore() {
      io.ConfigErrorRecovery = recovery;
      io.ConfigErrorRecoveryEnableAssert = assertion;
      io.ConfigErrorRecoveryEnableDebugLog = log;
      io.ConfigErrorRecoveryEnableTooltip = tooltip;
    }
  } restore{io, io.ConfigErrorRecovery, io.ConfigErrorRecoveryEnableAssert,
            io.ConfigErrorRecoveryEnableDebugLog, io.ConfigErrorRecoveryEnableTooltip};
  io.ConfigErrorRecovery = true;
  io.ConfigErrorRecoveryEnableAssert = false;
  io.ConfigErrorRecoveryEnableDebugLog = false;
  io.ConfigErrorRecoveryEnableTooltip = false;
  ImGui::EndFrame();
}
}  // namespace

EditorContext::EditorContext(SDL_Window* window, std::function<bool()> active, EditorOwnedPaths paths)
    : window_(window), active_(std::move(active)), paths_(std::move(paths)), owner_thread_(SDL_GetCurrentThreadID()) {
  if (!valid_destination(paths_.ini_filename) || !valid_destination(paths_.log_filename) ||
      paths_.ini_filename == paths_.log_filename)
    throw std::invalid_argument("editor: distinct absolute ini/log destinations required");
}

void EditorContext::require_owner_thread() const {
  if (SDL_GetCurrentThreadID() != owner_thread_) throw std::logic_error("editor: wrong owner thread");
}
void EditorContext::require_current() const {
  require_owner_thread();
  if (!context_ || ImGui::GetCurrentContext() != context_ || current_scopes_ == 0)
    throw std::logic_error("editor: owned current context scope required");
}

EditorContext::~EditorContext() {
  // Never tear a platform/backend down from a foreign thread or through a live
  // borrow. These ownership contract violations cannot safely be recovered here.
  if (SDL_GetCurrentThreadID() != owner_thread_ || current_scopes_ != 0) std::terminate();
  FpScope fp;
  if (!context_) return;
  ImGuiContext* previous = ImGui::GetCurrentContext();
  const bool previous_was_owned = previous == context_;
  ImGui::SetCurrentContext(context_);
  if (ImGui::GetIO().BackendRendererUserData) std::terminate();  // Concrete owner must detach first.
  ImGui_ImplSDL3_Shutdown();
  ImGui::DestroyContext(context_);
  context_ = nullptr;
  ImGui::SetCurrentContext(previous_was_owned ? nullptr : previous);
}

bool EditorContext::started() const {
  require_owner_thread();
  return context_ != nullptr;
}

bool EditorContext::active() const {
  require_owner_thread();
  FpScope fp;
  return active_ && active_();
}

bool EditorContext::start_if_active() {
  require_owner_thread();
  FpScope fp;
  if (!active_ || !active_()) return false;
  if (context_) return true;
  if (!window_) throw std::runtime_error("editor: window required");
  ImGuiContext* previous = ImGui::GetCurrentContext();
  try {
    IMGUI_CHECKVERSION();
    context_ = ImGui::CreateContext();
    if (!context_) throw std::runtime_error("editor: context creation failed");
    ImGui::SetCurrentContext(context_);
    ImGuiIO& io = ImGui::GetIO();
    io.IniFilename = paths_.ini_filename.c_str();
    io.LogFilename = paths_.log_filename.c_str();
    io.ConfigFlags |= ImGuiConfigFlags_NavEnableKeyboard;
    ImGui::StyleColorsDark();
    const float scale = SDL_GetWindowDisplayScale(window_);
    if (scale > 0) ImGui::GetStyle().ScaleAllSizes(scale), ImGui::GetStyle().FontScaleDpi = scale;
    if (!ImGui_ImplSDL3_InitForOther(window_)) throw std::runtime_error("editor: platform initialization failed");
    ImGui::SetCurrentContext(previous);
    return true;
  } catch (...) {
    if (context_) {
      ImGui::SetCurrentContext(context_);
      if (ImGui::GetIO().BackendPlatformUserData) ImGui_ImplSDL3_Shutdown();
      ImGui::DestroyContext(context_);
      context_ = nullptr;
    }
    ImGui::SetCurrentContext(previous);
    throw;
  }
}

EditorContext::Current::Current(EditorContext& owner) : owner_(owner) {
  owner_.require_owner_thread();
  if (!owner_.context_) throw std::logic_error("editor: context has not started");
  save_fp(fp_, mxcsr_);
  previous_ = ImGui::GetCurrentContext();
  ImGui::SetCurrentContext(owner_.context_);
  ++owner_.current_scopes_;
}
EditorContext::Current::~Current() {
  if (SDL_GetCurrentThreadID() != owner_.owner_thread_) std::terminate();
  ImGui::SetCurrentContext(previous_);
  --owner_.current_scopes_;
  restore_fp(fp_, mxcsr_);
}
EditorContext::Current EditorContext::current_existing() { return Current(*this); }

bool EditorContext::event(const SDL_Event& event) {
  require_owner_thread();
  FpScope fp;
  if (!start_if_active()) return false;
  auto current = current_existing();
  require_current();
  ImGui_ImplSDL3_ProcessEvent(&event);
  const ImGuiIO& io = ImGui::GetIO();
  return !editor_event_to_game(event, io.WantCaptureMouse, io.WantCaptureKeyboard, io.WantTextInput);
}

bool EditorContext::frame(EditorFrameBackend& backend, const std::function<void()>& draw) {
  require_owner_thread();
  FpScope fp;
  frame_complete_ = false;
  if (!active_ || !active_()) return false;
  require_current();
  bool opened = false;
  try {
    backend.new_frame();
    require_current();
    ImGui_ImplSDL3_NewFrame();
    ImGui::NewFrame();
    opened = true;
    if (draw) draw();
    require_current();
    ImGui::Render();
    frame_complete_ = true;
    return true;
  } catch (...) {
    ImGui::SetCurrentContext(context_);
    if (opened) cancel_frame();
    throw;
  }
}

ImDrawData* EditorContext::draw_data() {
  require_current();
  if (!frame_complete_) throw std::logic_error("editor: no completed current frame");
  return ImGui::GetDrawData();
}
}  // namespace sdlfe
