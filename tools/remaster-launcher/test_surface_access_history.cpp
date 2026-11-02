#include "../m4-crt-heap-carry/host/camera_history.hpp"
#include "../m4-crt-heap-carry/host/surface_access.hpp"
#include <bit>
#include <iostream>
#include <memory>
#include <stdexcept>

namespace {
using mw34::surface::LockAccess;
using mw34::surface::run_cpu_fallback;
using mw34::temporal::History;
using mw34::temporal::Reset;
using mw34::temporal::Snapshot;

void require(bool condition, const char *message) {
    if (!condition)
        throw std::runtime_error(message);
}

Snapshot snapshot(unsigned frame) {
    Snapshot value{};
    value.view = {1, 2, 3, 0};
    value.frame = frame;
    value.target = 7;
    value.attachment = 8;
    value.viewport = 9;
    value.camera[0] = value.camera[4] = value.camera[8] = std::bit_cast<unsigned>(1.f);
    value.inverse = value.camera;
    value.projection = {1, 20, 20, 32, 32, .1f};
    value.far_clip = 100;
    value.viewport_rect = {0, 0, 64, 64};
    value.sizes.fill(64);
    return value;
}

void complete_frame(History &history, Snapshot &value, unsigned frame) {
    value.frame = frame;
    history.observe(std::make_shared<const Snapshot>(value));
    history.complete(frame, 7);
}

History with_history(Snapshot &value) {
    History history;
    complete_frame(history, value, 1);
    complete_frame(history, value, 2);
    require(history.pairs().at(value.view).valid(), "Fixture did not establish camera history");
    return history;
}

void read_only_readback_preserves_history() {
    auto value = snapshot(1);
    auto history = with_history(value);
    LockAccess access;
    unsigned surface_version = 12;

    access.acquire(true, false);
    if (access.release(true))
        ++surface_version;
    require(surface_version == 12, "Read-only z-buffer Unlock advanced its version");

    complete_frame(history, value, 3);
    require(history.pairs().at(value.view).valid(),
            "Read-only readback between world submissions discarded camera history");
}

void read_only_hud_fallback_preserves_history() {
    auto value = snapshot(1);
    auto history = with_history(value);
    LockAccess access;
    unsigned surface_version = 12;

    access.acquire(true, true);
    run_cpu_fallback(
        [&] {
            if (access.writable())
                history.invalidate(Reset::external_write);
        },
        [] {}, [&] { access.expose_cpu_access(); });
    if (access.release(true))
        ++surface_version;
    require(surface_version == 12, "Read-only HUD fallback advanced its surface version");

    complete_frame(history, value, 3);
    require(history.pairs().at(value.view).valid(),
            "Read-only HUD fallback discarded camera history");
}

void hud_fallback_invalidates_before_cpu_write_and_flip() {
    auto value = snapshot(1);
    auto history = with_history(value);
    LockAccess access;
    unsigned surface_version = 12;
    bool cpu_access_allowed = false;
    unsigned fallback_step = 0;

    access.acquire(false, true);
    run_cpu_fallback(
        [&] {
            history.invalidate(Reset::external_write);
            require(fallback_step++ == 0, "HUD fallback did not invalidate first");
        },
        [&] { require(fallback_step++ == 1, "HUD draws did not flush second"); },
        [&] {
            access.expose_cpu_access();
            cpu_access_allowed = true;
            require(fallback_step++ == 2, "CPU surface access was enabled too early");
        });
    require(cpu_access_allowed, "HUD fallback did not expose CPU surface access");
    if (access.release(true))
        ++surface_version;
    require(surface_version == 13, "Writable fallback Unlock did not advance its version");

    complete_frame(history, value, 3);
    require(history.pairs().empty() && history.last_reset() == Reset::external_write,
            "CPU write followed by Flip committed camera history");
}

void gpu_handled_hud_preserves_history() {
    auto value = snapshot(1);
    auto history = with_history(value);
    LockAccess access;
    unsigned surface_version = 12;

    access.acquire(false, true);
    if (access.release(true))
        ++surface_version;
    require(surface_version == 12, "GPU-handled HUD Unlock advanced the surface version");

    complete_frame(history, value, 3);
    require(history.pairs().at(value.view).valid(), "GPU-handled HUD invalidated camera history");
}
} // namespace

int main() {
    try {
        read_only_readback_preserves_history();
        read_only_hud_fallback_preserves_history();
        hud_fallback_invalidates_before_cpu_write_and_flip();
        gpu_handled_hud_preserves_history();
        std::cout << "Surface lock and camera-history regressions passed\n";
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "FAIL: " << error.what() << '\n';
        return 1;
    }
}
