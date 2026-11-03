#pragma once

#include <cfenv>
#include <stdexcept>

#if defined(__SSE__) || defined(_M_X64)
#include <xmmintrin.h>
#endif

#if defined(_WIN32)
#pragma push_macro("NOMINMAX")
#pragma push_macro("WIN32_LEAN_AND_MEAN")
#ifndef NOMINMAX
#define NOMINMAX
#endif
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#pragma pop_macro("WIN32_LEAN_AND_MEAN")
#pragma pop_macro("NOMINMAX")
#endif

namespace mw34::adaptive_ground {

// Dedicated workers still preserve their actual environment per request. Sticky
// exception flags and LastError from one request must not leak into the next.
class WorkerEnvironment {
    std::fenv_t environment_{};
#if defined(__SSE__) || defined(_M_X64)
    unsigned mxcsr_{};
#endif
#if defined(_WIN32)
    DWORD last_error_{::GetLastError()};
#endif

  public:
    WorkerEnvironment() {
#if defined(__SSE__) || defined(_M_X64)
        mxcsr_ = _mm_getcsr();
#endif
        if (std::fegetenv(&environment_) != 0)
            throw std::runtime_error("Cannot capture adaptive worker FP environment");
        if (std::fesetenv(FE_DFL_ENV) != 0 || std::fesetround(FE_TONEAREST) != 0) {
            restore();
            throw std::runtime_error("Cannot establish adaptive worker FP environment");
        }
#if defined(__SSE__) || defined(_M_X64)
        _mm_setcsr(0x1f80);
#endif
    }
    WorkerEnvironment(const WorkerEnvironment &) = delete;
    WorkerEnvironment &operator=(const WorkerEnvironment &) = delete;
    ~WorkerEnvironment() { restore(); }

  private:
    void restore() noexcept {
        std::fesetenv(&environment_);
#if defined(__SSE__) || defined(_M_X64)
        _mm_setcsr(mxcsr_);
#endif
#if defined(_WIN32)
        ::SetLastError(last_error_);
#endif
    }
};

} // namespace mw34::adaptive_ground
