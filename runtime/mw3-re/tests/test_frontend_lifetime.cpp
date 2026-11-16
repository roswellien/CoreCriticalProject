// Asset-free lifetime checks: the engine owns the real UI; this service records its releases.
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <memory>
#include <stdexcept>
#include <vector>

#include "frontend/sdl/frontend_lifetime.h"
#include "frontend/sdl/sdl_input.h"
#include "frontend/sdl/sdl_twod_host.h"
#include "gamez/zerror/zerr.h"
#include "gamez/zimage/zimg_library.h"
#include "gamez/zutil/zutl_path.h"
#include "mech3/app.h"
#include "mech3/app_engine.h"
#include "mech3/menu_widgets.h"

namespace {
int assertions = 0;
void require(bool condition, const char* message) {
  ++assertions;
  if (!condition) throw std::runtime_error(message);
}

// Real app construction must load an actual message resource, not a success stub.
struct AuthoredMessages {
  zutl::Mounts previous = zutl::mounts();
  std::filesystem::path directory;
  AuthoredMessages() {
    const auto nonce = std::chrono::steady_clock::now().time_since_epoch().count();
    directory = std::filesystem::path(MW3_LIFETIME_TEST_ROOT) /
                ("frontend-lifetime-fixture-" + std::to_string(nonce));
    require(std::filesystem::create_directory(directory), "cannot create authored fixture directory");
    std::vector<uint8_t> bytes(0x400);
    auto u16 = [&](size_t offset, uint16_t value) {
      bytes[offset] = static_cast<uint8_t>(value);
      bytes[offset + 1] = static_cast<uint8_t>(value >> 8);
    };
    auto u32 = [&](size_t offset, uint32_t value) {
      u16(offset, static_cast<uint16_t>(value));
      u16(offset + 2, static_cast<uint16_t>(value >> 16));
    };
    bytes[0] = 'M'; bytes[1] = 'Z'; u32(0x3c, 0x80);
    std::memcpy(bytes.data() + 0x80, "PE\0\0", 4);
    u16(0x84, 0x14c); u16(0x86, 1); u16(0x94, 0xe0); u16(0x96, 0x2102);
    constexpr size_t optional = 0x98, section = optional + 0xe0, resource = 0x200;
    u16(optional, 0x10b); u32(optional + 28, 0x400000);
    u32(optional + 32, 0x1000); u32(optional + 36, 0x200);
    u32(optional + 56, 0x2000); u32(optional + 60, 0x200);
    u32(optional + 92, 16); u32(optional + 112, 0x1000); u32(optional + 116, 0x200);
    std::memcpy(bytes.data() + section, ".rsrc", 5);
    u32(section + 8, 0x200); u32(section + 12, 0x1000);
    u32(section + 16, 0x200); u32(section + 20, resource); u32(section + 36, 0x40000040);
    // RT_MESSAGETABLE type -> name -> language -> one authored message block.
    u16(resource + 14, 1); u32(resource + 16, 11); u32(resource + 20, 0x80000018);
    u16(resource + 0x18 + 14, 1); u32(resource + 0x18 + 16, 1);
    u32(resource + 0x18 + 20, 0x80000030);
    u16(resource + 0x30 + 14, 1); u32(resource + 0x30 + 16, 0x409);
    u32(resource + 0x30 + 20, 0x48); u32(resource + 0x48, 0x1060);
    constexpr char text[] = "Authored lifetime fixture";
    u32(resource + 0x4c, 20 + sizeof(text));
    u32(resource + 0x60, 1); u32(resource + 0x64, 7);
    u32(resource + 0x68, 7); u32(resource + 0x6c, 16);
    u16(resource + 0x70, 4 + sizeof(text));
    std::memcpy(bytes.data() + resource + 0x74, text, sizeof(text));
    const auto path = directory / "Mech3Msg.dll";
    std::ofstream output(path, std::ios::binary);
    output.write(reinterpret_cast<const char*>(bytes.data()), bytes.size());
    output.close();
    require(!output.fail(), "cannot write authored message resource");
    zutl::MessageDll messages;
    require(zutl::read_message_dll(path.string(), messages) && messages.text[7] == text,
            "authored message DLL did not pass the real resource parser");
    zutl::mounts() = zutl::Mounts{};
    zutl::mount(directory.string());
    zutl::mounts().write = directory.string();
  }
  ~AuthoredMessages() {
    zutl::mounts() = std::move(previous);
    std::error_code ignored;
    std::filesystem::remove_all(directory, ignored);
  }
};

struct LifetimeLedger {
  bool backend_alive = false;
  bool observe_app = false, app_alive = false;
  mech3::Mech3App* expected_app = nullptr;
  int font_acquires = 0, font_releases = 0, font_refs = 0;
  int image_acquires = 0, image_releases = 0, cached_frees = 0, violations = 0;
  zimg::Texture* cached_image = nullptr;  // Observation only; FontText owns this allocation.
  std::vector<zimg::Texture*> owned_images;

  ~LifetimeLedger() {
    // Failed legacy-order assertions must not leak the images its no-op host abandoned.
    // The default host DOES free FontText's cached image, so never free that observation.
    for (auto* image : owned_images) zimg::free_texture(image);
  }
};

struct RecordingHost : ztwod::Host {
  LifetimeLedger& ledger;
  sdlfe::SdlTwodHost factory{nullptr, nullptr, nullptr};
  std::unique_ptr<int> font_token = std::make_unique<int>(17);

  explicit RecordingHost(LifetimeLedger& value) : ledger(value) { ledger.backend_alive = true; }
  ~RecordingHost() override {
    if (ledger.font_refs != 0) ++ledger.violations;
    ledger.backend_alive = false;
  }
  zgame::Handle GetStockObject(int32_t) override { return 0; }
  void font_addref(zgame::Handle font) override {
    if (!ledger.backend_alive || font != 17 || !font_token || ledger.font_refs != 0)
      ++ledger.violations;
    ++ledger.font_acquires;
    ++ledger.font_refs;
  }
  ztwod::NamedFont font_fields(zgame::Handle font) override {
    if (font != 17 || !font_token || ledger.font_refs != 1) ++ledger.violations;
    return {17, 0xffffff, 0xffffff, 0, 0};
  }
  void font_release(zgame::Handle font) override {
    if (!ledger.backend_alive || font != 17 || !font_token || ledger.font_refs != 1)
      ++ledger.violations;
    if (ledger.observe_app && (!ledger.app_alive || mech3::app_if_any() != ledger.expected_app))
      ++ledger.violations;
    ++ledger.font_releases;
    --ledger.font_refs;
  }
  zimg::Texture* allocate_owned_image() {
    auto* image = factory.image_new(2, 2);
    if (!image) throw std::bad_alloc();
    ledger.owned_images.push_back(image);
    return image;
  }
  zimg::Texture* image_get(const char* name) override {
    if (!name || std::strcmp(name, "fixture-owned") != 0) return nullptr;
    ++ledger.image_acquires;
    return allocate_owned_image();
  }
  zimg::Texture* image_release(zimg::Texture* image) override {
    auto found = std::find(ledger.owned_images.begin(), ledger.owned_images.end(), image);
    if (!ledger.backend_alive || found == ledger.owned_images.end()) {
      ++ledger.violations;
      return nullptr;
    }
    ledger.owned_images.erase(found);
    ++ledger.image_releases;
    return factory.image_release(image);
  }
  zimg::Texture* allocate_cached_image() {
    ledger.cached_image = factory.image_new(2, 2);
    if (!ledger.cached_image) throw std::bad_alloc();
    return ledger.cached_image;
  }
  void texture_free(zimg::Texture* image) override {
    if (!ledger.backend_alive || image != ledger.cached_image) {
      ++ledger.violations;
      return;
    }
    ++ledger.cached_frees;
    ledger.cached_image = nullptr;
    factory.texture_free(image);
  }
};

void acquire_ui(mech3::GameEngine& engine, RecordingHost& host) {
  // Unlike adopt_screen(), this factory registers engine-deleted ownership.
  const auto handle = engine.construct(0x4289a0, {});
  auto* screen = engine.screen_of(handle);
  require(screen != nullptr, "engine did not construct its owned Credits screen");
  require(screen->texts[0].set_named_font(17, true), "named font was not acquired");
  screen->texts[0].image = host.allocate_cached_image();
  screen->images[0].set_image("fixture-owned");
  screen->set_static_bg(host.allocate_owned_image());
  require(screen->images[0].image != nullptr, "owned named image was not acquired");
  require(screen->images[0].owned != 0, "raw borrowed image cannot prove UI release");
  require(host.ledger.font_acquires == 1 && host.ledger.font_refs == 1,
          "fixture did not acquire a real named-font lease");
  require(host.ledger.image_acquires == 1 && host.ledger.owned_images.size() == 2,
          "fixture did not allocate both owned dialog images");
}

void require_released(const LifetimeLedger& ledger) {
  require(ledger.font_releases == 1, "named font was not released through the live host");
  require(ledger.font_refs == 0, "named-font lease survived backend shutdown");
  require(ledger.cached_frees == 1, "cached FontText image bypassed the live host");
  require(ledger.image_releases == 2, "Dialog did not release both owned images");
  require(ledger.owned_images.empty(), "UI-owned image allocations survived engine teardown");
  require(ledger.violations == 0, "resource release used an expired or mismatched service");
  require(!ledger.backend_alive, "fixture did not exercise backend shutdown");
}

void normal_shutdown() {
  LifetimeLedger ledger;
  auto* previous_host = &ztwod::host();
  {
    mech3::GameEngine engine(mech3::Platform{}, "mech3.exe -nofmv");
    {
      RecordingHost host(ledger);
      sdlfe::FrontendUiLifetime ui_lifetime(engine, host);
      acquire_ui(engine, host);
    }
  }
  require(&ztwod::host() == previous_host, "previous 2D registration was not restored");
  require_released(ledger);
}

struct InitiatingFailure : std::runtime_error {
  const void* identity;
  explicit InitiatingFailure(const void* value) : std::runtime_error("initiating failure"), identity(value) {}
};

struct FailingCallback {
  const void* identity;
  explicit FailingCallback(const void* value) : identity(value) {}
  FailingCallback(const FailingCallback& other) { throw InitiatingFailure(other.identity); }
  bool operator()() const { return false; }
};

// Observation only: this does not release UI or unregister anything.
struct ObserveAppLifetime {
  LifetimeLedger& ledger;
  ObserveAppLifetime(LifetimeLedger& value, mech3::Mech3App& app) : ledger(value) {
    ledger.observe_app = ledger.app_alive = true;
    ledger.expected_app = &app;
  }
  ~ObserveAppLifetime() { ledger.app_alive = false; }
};

void callback_assignment_failure() {
  LifetimeLedger ledger;
  std::function<bool()> in_mission;
  auto* previous_app = mech3::app_if_any();
  int failure_identity = 0;
  bool caught_original = false;
  try {
    mech3::GameEngine engine(mech3::Platform{}, "mech3.exe -nofmv");
    RecordingHost host(ledger);
    sdlfe::FrontendUiLifetime ui_lifetime(engine, host);
    acquire_ui(engine, host);
    mech3::Mech3App app(&engine);
    ObserveAppLifetime observed{ledger, app};
    sdlfe::FrontendAppLifetime app_lifetime(ui_lifetime, app, in_mission);
    in_mission = [&app] { return app.current() != nullptr; };
    require(!in_mission(), "fresh app unexpectedly has a current state");
    const FailingCallback failing(&failure_identity);
    in_mission = failing;  // Deterministic failure in the real std::function assignment.
  } catch (const InitiatingFailure& error) {
    caught_original = error.identity == &failure_identity;
  }
  const bool app_restored = mech3::app_if_any() == previous_app;
  const bool callback_cleared = !in_mission;
  // Keep a failing adverse control from poisoning subsequent cases; inspect before cleanup.
  mech3::set_app(previous_app);
  in_mission = nullptr;
  require(caught_original, "cleanup replaced or swallowed the initiating callback exception");
  require(app_restored, "app registration survived failed callback assignment");
  require(callback_cleared, "callback retained an expired app after failed assignment");
  require_released(ledger);
}
// The app's first constructor hook fails; the failure token remains live through unwind.
class ThrowingAppEngine : public mech3::GameEngine {
 public:
  explicit ThrowingAppEngine(const void* value)
      : GameEngine(mech3::Platform{}, "mech3.exe -nofmv"), identity(value) {}
  void run_dir() override { throw InitiatingFailure(identity); }
  const void* identity;
};

void partial_app_construction_failure() {
  LifetimeLedger ledger;
  auto* previous_app = mech3::app_if_any();
  auto* previous_host = &ztwod::host();
  int failure_identity = 0;
  bool caught_original = false;
  try {
    ThrowingAppEngine engine(&failure_identity);
    RecordingHost host(ledger);
    sdlfe::FrontendUiLifetime ui_lifetime(engine, host);
    acquire_ui(engine, host);
    mech3::Mech3App app(&engine);
  } catch (const InitiatingFailure& error) {
    caught_original = error.identity == &failure_identity;
  }
  require(caught_original, "cleanup replaced or swallowed the app-constructor exception");
  require(mech3::app_if_any() == previous_app, "app registration survived failed construction");
  require(&ztwod::host() == previous_host, "2D registration survived failed app construction");
  require_released(ledger);
}

enum class UiExit { NormalApp, EarlyReturn, OriginalException, BeforeAppReturn, RepeatedRelease };

void ui_exit_path(UiExit mode) {
  LifetimeLedger ledger;
  std::function<bool()> in_mission;
  auto* previous_host = &ztwod::host();
  auto* previous_app = mech3::app_if_any();
  int failure_identity = 0;
  bool caught_original = false;
  int result = -1;
  auto run = [&]() -> int {
    mech3::GameEngine engine(mech3::Platform{}, "mech3.exe -nofmv");
    RecordingHost host(ledger);
    sdlfe::FrontendUiLifetime ui_lifetime(engine, host);
    acquire_ui(engine, host);
    if (mode == UiExit::BeforeAppReturn) return 23;
    mech3::Mech3App app(&engine);
    ObserveAppLifetime observed{ledger, app};
    sdlfe::FrontendAppLifetime app_lifetime(ui_lifetime, app, in_mission);
    in_mission = [&app] { return app.current() != nullptr; };
    require(mech3::app_if_any() == &app && !in_mission(), "live app registration/callback missing");
    if (mode == UiExit::OriginalException) throw InitiatingFailure(&failure_identity);
    if (mode == UiExit::EarlyReturn) return 23;
    if (mode == UiExit::RepeatedRelease) {
      ui_lifetime.release_ui();
      ui_lifetime.release_ui();
      require(ledger.backend_alive && ledger.app_alive, "explicit release outlived its services");
      require(ledger.font_releases == 1 && ledger.cached_frees == 1 && ledger.image_releases == 2,
              "explicit/repeated release missed or duplicated actual resource releases");
    }
    return 0;
  };
  try {
    result = run();
  } catch (const InitiatingFailure& error) {
    caught_original = error.identity == &failure_identity;
  }
  if (mode == UiExit::OriginalException)
    require(caught_original && result == -1, "original exception became successful completion");
  else
    require(!caught_original && result == ((mode == UiExit::EarlyReturn || mode == UiExit::BeforeAppReturn) ? 23 : 0),
            "cleanup changed the initiating return status");
  require(&ztwod::host() == previous_host, "2D registration was not restored on scope exit");
  require(mech3::app_if_any() == previous_app, "app registration was not restored on scope exit");
  require(!in_mission, "callback retained an expired app on scope exit");
  require_released(ledger);
}

void restore_live_registrations() {
  LifetimeLedger ledger, previous_ledger;
  auto* saved_host = &ztwod::host();
  auto* saved_app = mech3::app_if_any();
  {
    mech3::GameEngine engine(mech3::Platform{}, "mech3.exe -nofmv");
    RecordingHost previous_host(previous_ledger);
    sdlfe::FrontendUiLifetime previous_ui(engine, previous_host);
    mech3::Mech3App previous_app(&engine);
    std::function<bool()> previous_callback;
    sdlfe::FrontendAppLifetime previous_registration(previous_ui, previous_app, previous_callback);
    {
      RecordingHost host(ledger);
      sdlfe::FrontendUiLifetime ui_lifetime(engine, host);
      acquire_ui(engine, host);
      mech3::Mech3App app(&engine);
      ObserveAppLifetime observed{ledger, app};
      std::function<bool()> callback;
      sdlfe::FrontendAppLifetime app_lifetime(ui_lifetime, app, callback);
      callback = [&app] { return app.current() != nullptr; };
    }
    require(&ztwod::host() == &previous_host, "previous live nondefault host was not restored");
    require(mech3::app_if_any() == &previous_app, "previous live app was not restored");
  }
  require(&ztwod::host() == saved_host && mech3::app_if_any() == saved_app,
          "outer registrations were not restored");
  require_released(ledger);
}

int input_error_reports = 0;
void observe_input_error(int, const char* file, int line, const char*) {
  if (line == 0x96 && std::strstr(file, "zin_init.cpp")) ++input_error_reports;
}

void input_registration_shutdown() {
  zin::stop();
  zin::set_input(nullptr);
  zin::set_host(nullptr);
  {
    sdlfe::SdlInput input;
    bool host_cleared = false;
    {
      sdlfe::SdlZinHost host(&input);
      {
        sdlfe::FrontendInputLifetime input_lifetime(host);
        zin::set_input(&input);
        require(zin::start(1, 0) == 0 && zin::state().di == &input,
                "fixture did not start the real input devices");
        require(input.acquire(platform::Input::kKeyboard) == 0,
                "fixture keyboard was not actually opened");
        zin::mouse_size_from_window();
        require(zin::state().width == 640, "fixture input host did not receive dispatch");
      }
      // Observe failed-unregistration controls before the former host actually expires.
      zin::mouse_size_from_window();
      host_cleared = zin::state().width == 0;
      if (!host_cleared) zin::set_host(nullptr);
    }
    const bool stopped = zin::state().di == nullptr && zin::state().started == 0;
    const bool closed = input.acquire(platform::Input::kKeyboard) == platform::Input::kNotAcquired;
    // Probe the separate hidden g_di registration while its former input is still alive.
    // This catches an omitted set_input(nullptr) without dereferencing an expired object.
    if (zin::state().window) zin::stop();
    const int before = input_error_reports;
    zerr::set_sink(observe_input_error);
    const int restarted = zin::start(1, 0);
    zerr::set_sink(nullptr);
    if (restarted != -1) {
      zin::stop();
      zin::set_input(nullptr);  // Failed adverse-control hygiene, after capturing the result.
    }
    require(stopped, "input registration survived its lifetime boundary");
    require(closed, "real SDL keyboard remained open after lifetime shutdown");
    require(host_cleared, "input dispatch still reached the expired host");
    require(restarted == -1 && input_error_reports == before + 1,
            "hidden platform input registration survived lifetime shutdown");
  }
  const int before = input_error_reports;
  zerr::set_sink(observe_input_error);
  const int after_expiry = zin::start(1, 0);
  zerr::set_sink(nullptr);
  require(after_expiry == -1 && input_error_reports == before + 1,
          "start after actual platform input destruction did not fail visibly");
}
void input_only_exception() {
  sdlfe::SdlInput input;
  sdlfe::SdlZinHost host(&input);
  int failure_identity = 0;
  bool caught_original = false;
  try {
    sdlfe::FrontendInputLifetime input_lifetime(host);
    zin::set_input(&input);
    throw InitiatingFailure(&failure_identity);  // No engine or 2D host was constructed.
  } catch (const InitiatingFailure& error) {
    caught_original = error.identity == &failure_identity;
  }
  const int before = input_error_reports;
  zerr::set_sink(observe_input_error);
  const int restarted = zin::start(1, 0);
  zerr::set_sink(nullptr);
  if (restarted != -1) { zin::stop(); zin::set_input(nullptr); }
  zin::mouse_size_from_window();
  const bool host_cleared = zin::state().width == 0;
  if (!host_cleared) zin::set_host(nullptr);
  require(caught_original, "input-only unwind replaced the original exception");
  require(restarted == -1 && input_error_reports == before + 1,
          "input-only unwind retained direct platform input registration");
  require(host_cleared, "input-only unwind retained its expired host");
}
}  // namespace

int run_checks() {
  struct Case { const char* name; void (*run)(); };
  const Case cases[] = {{"normal_shutdown", normal_shutdown},
                        {"callback_assignment_failure", callback_assignment_failure},
                        {"input_registration_shutdown", input_registration_shutdown},
                        {"partial_app_construction_failure", partial_app_construction_failure},
                        {"normal_app_shutdown", +[] { ui_exit_path(UiExit::NormalApp); }},
                        {"early_return", +[] { ui_exit_path(UiExit::EarlyReturn); }},
                        {"original_exception", +[] { ui_exit_path(UiExit::OriginalException); }},
                        {"before_app_return", +[] { ui_exit_path(UiExit::BeforeAppReturn); }},
                        {"repeated_release", +[] { ui_exit_path(UiExit::RepeatedRelease); }},
                        {"restore_live_registrations", restore_live_registrations},
                        {"input_only_exception", input_only_exception}};
  constexpr int expected_cases = 11;
  int executed = 0, failed = 0;
  for (const auto& test : cases) {
    ++executed;
    const int before = assertions;
    auto* previous_app = mech3::app_if_any();
    auto* previous_host = &ztwod::host();
    try {
      test.run();
      require(assertions > before, "case executed no assertions");
      std::printf("PASS %s\n", test.name);
    } catch (const std::exception& error) {
      ++failed;
      std::fprintf(stderr, "FAIL %s: %s\n", test.name, error.what());
      // Restore globals only after a failed case, never to manufacture a passing assertion.
      mech3::set_app(previous_app);
      ztwod::set_host(previous_host);
    }
  }
  std::printf("lifetime: executed=%d expected=%d failed=%d assertions=%d\n",
              executed, expected_cases, failed, assertions);
  return failed != 0 || executed != expected_cases || assertions == 0 ? 1 : 0;
}

int main() {
  try {
    AuthoredMessages fixtures;
    return run_checks();
  } catch (const std::exception& error) {
    std::fprintf(stderr, "FAIL fixture setup: %s\n", error.what());
    return 2;
  }
}
