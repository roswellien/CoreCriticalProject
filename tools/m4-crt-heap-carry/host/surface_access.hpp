#pragma once

namespace mw34::surface {
class LockAccess {
    bool writable_{};
    bool cpu_accessible_{};

  public:
    bool writable() const noexcept { return writable_; }
    void acquire(bool read_only, bool gpu_handled) noexcept {
        writable_ |= !read_only;
        cpu_accessible_ |= !gpu_handled;
    }
    void expose_cpu_access() noexcept { cpu_accessible_ = true; }
    bool release(bool final_lock) noexcept {
        const bool changed = writable_ && cpu_accessible_;
        if (final_lock) {
            writable_ = false;
            cpu_accessible_ = false;
        }
        return changed;
    }
};

template <typename InvalidateHistory, typename FlushHud, typename EnableCpuAccess>
void run_cpu_fallback(InvalidateHistory invalidate_history, FlushHud flush_hud,
                      EnableCpuAccess enable_cpu_access) {
    invalidate_history();
    flush_hud();
    enable_cpu_access();
}
} // namespace mw34::surface
