#pragma once
#include <windows.h>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <stdexcept>

namespace mw34 {
// Development-only CPU scopes. Values are QPC ticks, converted offline; never
// change the guest FP environment to format floating-point profiling values.
struct GeometryProfile {
    FILE* file{};
    std::uint64_t frequency{}, source_calls{}, source_ticks{}, emit_calls{}, emit_ticks{};
    std::uint64_t cpu_vertices{}, gpu_vertices{}, tl_bytes{}, gpu_batches{}, near_batches{};
    GeometryProfile() {
        const char* path = std::getenv("MW34_GEOMETRY_PROFILE");
        if (!path || !*path) return;
        LARGE_INTEGER f{};
        if (!::QueryPerformanceFrequency(&f) || f.QuadPart <= 0)
            throw std::runtime_error("Geometry profiling QPC unavailable");
        frequency = std::uint64_t(f.QuadPart);
        file = std::fopen(path, "w");
        if (!file) throw std::runtime_error("Geometry profile file unavailable");
        std::fprintf(file, "frame,qpc_hz,source_calls,source_ticks,emit_calls,emit_ticks,cpu_vertices,gpu_vertices,tl_bytes,gpu_batches,near_batches\n");
    }
    GeometryProfile(const GeometryProfile&) = delete;
    GeometryProfile& operator=(const GeometryProfile&) = delete;
    ~GeometryProfile() { if (file) std::fclose(file); }
    static std::uint64_t now() {
        LARGE_INTEGER q{}; ::QueryPerformanceCounter(&q);
        return std::uint64_t(q.QuadPart);
    }
    struct Scope {
        GeometryProfile& profile;
        bool source;
        std::uint64_t start{};
        Scope(GeometryProfile& p, bool s) : profile(p), source(s) {
            if (p.file) start = now();
        }
        ~Scope() {
            if (!profile.file) return;
            const auto ticks = now() - start;
            if (source) { ++profile.source_calls; profile.source_ticks += ticks; }
            else { ++profile.emit_calls; profile.emit_ticks += ticks; }
        }
    };
    void present(unsigned frame) {
        if (!file) return;
        std::fprintf(file, "%u,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu\n",
            frame, (unsigned long long)frequency,
            (unsigned long long)source_calls, (unsigned long long)source_ticks,
            (unsigned long long)emit_calls, (unsigned long long)emit_ticks,
            (unsigned long long)cpu_vertices, (unsigned long long)gpu_vertices,
            (unsigned long long)tl_bytes, (unsigned long long)gpu_batches,
            (unsigned long long)near_batches);
        source_calls=source_ticks=emit_calls=emit_ticks=0;
        cpu_vertices=gpu_vertices=tl_bytes=gpu_batches=near_batches=0;
        std::fflush(file);
    }
};
}
