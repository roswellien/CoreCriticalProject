#pragma once
// Private diagnostic only. Nested scopes charge exclusive CPU wall time; no
// original routine is skipped. Integer output preserves the guest FP state.
#include <windows.h>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <stdexcept>

namespace mw34::geometry_breakdown {
enum Category { Other, Adapter, MeshResident, MeshOther, Material, Subdivide, Fog, Matrix,
                Callback57ea20, Callback57d690,
                Body51dfa0, Api, Draw, WorldBinding, SunCapture, EffectCapture,
                Scene, Renderer, ShadowPrepare, ShadowRecord, Count };
inline constexpr const char* names[]{"other", "geometry_adapter", "mesh_body_with_world_scope",
    "mesh_body_other", "material_545720", "light_subdivision_547740", "fog_555a70", "matrix_51fb30",
    "callback_57ea20", "callback_57d690",
    "body_51dfa0", "host_api", "draw_capture", "world_binding", "sun_capture",
    "effect_capture", "scene_build", "renderer", "shadow_prepare", "shadow_record"};
struct PreserveEnvironment {
    alignas(16) unsigned char fx[512];
    DWORD error{};
    PreserveEnvironment() {
        __asm__ volatile("fxsave64 %0" : "=m"(fx) :: "memory");
        error = ::GetLastError();
    }
    ~PreserveEnvironment() {
        ::SetLastError(error);
        __asm__ volatile("fxrstor64 %0" :: "m"(fx) : "memory",
            "xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7",
            "xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");
    }
};
inline std::uint64_t now() {
    const DWORD error = ::GetLastError();
    LARGE_INTEGER value{};
    ::QueryPerformanceCounter(&value);
    ::SetLastError(error);
    return std::uint64_t(value.QuadPart);
}
struct Profile {
    FILE* file{};
    std::uint64_t hz{}, last{};
    Category current{Other};
    std::array<std::uint64_t, Count> ticks{}, inclusive{}, calls{};
    Profile() {
        PreserveEnvironment preserve;
        const char* path = std::getenv("MW34_GEOMETRY_BREAKDOWN");
        if (!path || !*path) return;
        LARGE_INTEGER value{};
        if (!::QueryPerformanceFrequency(&value) || value.QuadPart <= 0)
            throw std::runtime_error("Geometry breakdown QPC unavailable");
        hz = std::uint64_t(value.QuadPart);
        file = std::fopen(path, "w");
        if (!file) throw std::runtime_error("Geometry breakdown output unavailable");
        std::fputs("frame,hz,category,exclusive_ticks,inclusive_ticks,calls\n", file);
        last = now();
    }
    ~Profile() { if (file) std::fclose(file); }
    void charge() { const auto end = now(); ticks[current] += end - last; last = end; }
};
inline Profile& profile() { static Profile value; return value; }
struct Scope {
    Category previous{}, category{};
    std::uint64_t start{};
    bool active{};
    explicit Scope(Category selected, bool enabled = true) : category(selected) {
        if (!enabled) return;
        auto& value = profile();
        active = value.file != nullptr;
        if (active) {
            value.charge(); previous = value.current; value.current = category;
            start = value.last;
            ++value.calls[category];
        }
    }
    Scope(const Scope&) = delete;
    Scope& operator=(const Scope&) = delete;
    ~Scope() {
        if (active) {
            auto& value = profile(); value.charge();
            value.inclusive[category] += value.last - start;
            value.current = previous;
        }
    }
};
inline bool selected(unsigned target) {
    return target == 0x53f2e0 || target == 0x545720 || target == 0x547740 || target == 0x555a70 ||
           target == 0x51fb30 || target == 0x51dfa0 || target == 0x57ea20 || target == 0x57d690;
}
inline Category body(unsigned target, bool resident) {
    switch (target) {
    case 0x53f2e0: return resident ? MeshResident : MeshOther;
    case 0x545720: return Material;
    case 0x547740: return Subdivide;
    case 0x57ea20: return Callback57ea20;
    case 0x57d690: return Callback57d690;
    case 0x555a70: return Fog;
    case 0x51fb30: return Matrix;
    case 0x51dfa0: return Body51dfa0;
    default: return Other;
    }
}
inline void present(unsigned frame) {
    PreserveEnvironment preserve;
    auto& value = profile();
    if (!value.file) return;
    value.charge();
    if (frame >= 1200 && frame < 2700)
        for (unsigned i = 0; i < Count; ++i)
            std::fprintf(value.file, "%u,%llu,%s,%llu,%llu,%llu\n", frame,
                (unsigned long long)value.hz, names[i],
                (unsigned long long)value.ticks[i], (unsigned long long)value.inclusive[i],
                (unsigned long long)value.calls[i]);
    value.ticks = {}; value.inclusive = {}; value.calls = {};
}
}
