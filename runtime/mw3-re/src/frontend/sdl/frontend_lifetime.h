#pragma once

#include <functional>

#include "gamez/zinput/zinput.h"
#include "gamez/ztwod/twod_host.h"
#include "mech3/app.h"
#include "mech3/app_engine.h"

namespace sdlfe {

// Outermost frontend registration: input and host outlive engine/force-feedback teardown.
class FrontendInputLifetime {
 public:
  explicit FrontendInputLifetime(zin::Host& host) { zin::set_host(&host); }
  FrontendInputLifetime(const FrontendInputLifetime&) = delete;
  FrontendInputLifetime& operator=(const FrontendInputLifetime&) = delete;
  FrontendInputLifetime(FrontendInputLifetime&&) = delete;
  FrontendInputLifetime& operator=(FrontendInputLifetime&&) = delete;

  ~FrontendInputLifetime() {
    zin::stop();
    zin::set_input(nullptr);
    zin::set_host(nullptr);
  }
};

// Engine-owned screens must release through the actual host before its font cache closes.
// The engine outlives this scope, but its later destructor finds no remaining owned UI.
class FrontendUiLifetime {
 public:
  FrontendUiLifetime(mech3::GameEngine& engine, ztwod::Host& host)
      : engine_(engine), previous_host_(&ztwod::host()) {
    ztwod::set_host(&host);
  }
  FrontendUiLifetime(const FrontendUiLifetime&) = delete;
  FrontendUiLifetime& operator=(const FrontendUiLifetime&) = delete;
  FrontendUiLifetime(FrontendUiLifetime&&) = delete;
  FrontendUiLifetime& operator=(FrontendUiLifetime&&) = delete;

  ~FrontendUiLifetime() {
    release_ui();
    ztwod::set_host(previous_host_);
  }

  void release_ui() {
    if (released_) return;
    // Preserve the engine's actual release behavior, including its existing allocation risk.
    engine_.delete_screens();
    released_ = true;
  }

 private:
  mech3::GameEngine& engine_;
  ztwod::Host* previous_host_;
  bool released_ = false;
};

// Declared after the app: UI releases and captured callbacks must finish before it dies.
class FrontendAppLifetime {
 public:
  FrontendAppLifetime(FrontendUiLifetime& ui, mech3::Mech3App& app,
                      std::function<bool()>& in_mission)
      : ui_(ui), in_mission_(in_mission), previous_app_(mech3::app_if_any()) {
    mech3::set_app(&app);
  }
  FrontendAppLifetime(const FrontendAppLifetime&) = delete;
  FrontendAppLifetime& operator=(const FrontendAppLifetime&) = delete;
  FrontendAppLifetime(FrontendAppLifetime&&) = delete;
  FrontendAppLifetime& operator=(FrontendAppLifetime&&) = delete;

  ~FrontendAppLifetime() {
    ui_.release_ui();
    in_mission_ = nullptr;
    mech3::set_app(previous_app_);
  }

 private:
  FrontendUiLifetime& ui_;
  std::function<bool()>& in_mission_;
  mech3::Mech3App* previous_app_;
};

}  // namespace sdlfe
