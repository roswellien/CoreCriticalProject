// Ours, not original code (docs/editor.md, Dear ImGui for the editor's dialogs).
#include "frontend/sdl/editor_imgui.h"

#include <cstdio>
#include <stdexcept>
#include <utility>

#include "imgui.h"
#include "backends/imgui_impl_sdlgpu3.h"

namespace sdlfe {

EditorUi::EditorUi(SDL_Window* window, SDL_GPUDevice* device, std::function<bool()> up, EditorOwnedPaths paths)
    : context_(window, std::move(up), std::move(paths)), window_(window), device_(device) {
  draw = draw_editor_forms;
}

EditorUi::~EditorUi() {
  if (!backend_started_) return;
  // The CPU owner remains alive, including when the editor is closed. Select
  // the actual backend context and restore the caller's context and FP state.
  auto current = context_.current_existing();
  ImGui_ImplSDLGPU3_Shutdown();
  backend_started_ = false;
}

void EditorUi::new_frame() {
  if (!backend_started_) {
    if (!device_) throw std::runtime_error("editor: SDL GPU device required");
    ImGui_ImplSDLGPU3_InitInfo info{};
    info.Device = device_;
    info.ColorTargetFormat = SDL_GetGPUSwapchainTextureFormat(device_, window_);
    info.MSAASamples = SDL_GPU_SAMPLECOUNT_1;
    if (info.ColorTargetFormat == SDL_GPU_TEXTUREFORMAT_INVALID)
      throw std::runtime_error("editor: SDL GPU swapchain format unavailable");
    try {
      if (!ImGui_ImplSDLGPU3_Init(&info)) throw std::runtime_error("editor: SDL GPU initialization failed");
      backend_started_ = true;
    } catch (...) {
      if (ImGui::GetIO().BackendRendererUserData) ImGui_ImplSDLGPU3_Shutdown();
      throw;
    }
  }
  ImGui_ImplSDLGPU3_NewFrame();
}

bool EditorUi::event(const SDL_Event& e) { return context_.event(e); }

bool EditorUi::frame(EditorFrameBackend& backend,
                     const std::function<void(ImDrawData*)>& consume) {
  if (!context_.start_if_active()) return false;
  if (!consume) throw std::invalid_argument("editor: frame consumer required");
  auto current = context_.current_existing();
  if (!context_.frame(backend, draw)) return false;
  consume(context_.draw_data());
  return true;
}

bool EditorUi::with_current(const std::function<void()>& operation) {
  if (!context_.started()) return false;
  if (!operation) throw std::invalid_argument("editor: current-context operation required");
  auto current = context_.current_existing();
  operation();
  return true;
}

bool EditorUi::step() {
  if (!context_.start_if_active()) return false;
  auto current = context_.current_existing();
  return context_.frame(*this, draw);
}

void EditorUi::overlay(SDL_GPUCommandBuffer* cmd, SDL_GPUTexture* target, Uint32, Uint32) {
  if (!context_.start_if_active()) return;
  auto current = context_.current_existing();
  if (!cmd || !target) throw std::invalid_argument("editor: overlay command and target required");
  if (!context_.frame(*this, draw)) return;
  ImDrawData* d = context_.draw_data();
  if (!d || d->DisplaySize.x <= 0 || d->DisplaySize.y <= 0) return;
  ImGui_ImplSDLGPU3_PrepareDrawData(d, cmd);
  SDL_GPUColorTargetInfo t{};
  t.texture = target;
  t.load_op = SDL_GPU_LOADOP_LOAD;  // over the game's frame
  t.store_op = SDL_GPU_STOREOP_STORE;
  SDL_GPURenderPass* pass = SDL_BeginGPURenderPass(cmd, &t, 1, nullptr);
  if (!pass) throw std::runtime_error("editor: overlay render pass failed");
  ImGui_ImplSDLGPU3_RenderDrawData(d, cmd, pass);
  SDL_EndGPURenderPass(pass);
  if (!drawn_) std::printf("mw3: the editor's dialogs drawn over the game (%d lists)\n", d->CmdListsCount), drawn_ = true;
}

}  // namespace sdlfe
