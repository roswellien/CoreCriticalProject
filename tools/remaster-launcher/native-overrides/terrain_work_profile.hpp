#pragma once
#include <windows.h>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <map>
#include <stdexcept>
#include <string>

namespace mw34 {
// Inclusive CPU scopes for the existing mesh body, material lighting and fog.
// Integer QPC records avoid altering the guest FP environment to format times.
struct TerrainWorkProfile {
    struct Count { std::uint64_t calls{}, ticks{}; };
    std::array<std::array<Count, 3>, 3> counts{};
    std::map<std::string, Count> mesh_names;
    FILE* file{};
    std::uint64_t frequency{};
    unsigned from{400}, group{};
    TerrainWorkProfile() {
        const char* path = std::getenv("MW34_TERRAIN_WORK_PROFILE");
        if (!path || !*path) return;
        if (const char* value = std::getenv("MW34_TERRAIN_WORK_FROM")) {
            char* end{};
            const unsigned long parsed = std::strtoul(value, &end, 10);
            if (end == value || *end || parsed > 1000000)
                throw std::runtime_error("Invalid terrain profile start frame");
            from = unsigned(parsed);
        }
        LARGE_INTEGER q{};
        if (!::QueryPerformanceFrequency(&q) || q.QuadPart <= 0)
            throw std::runtime_error("Terrain profiling QPC unavailable");
        frequency = std::uint64_t(q.QuadPart);
        file = std::fopen(path, "w");
        if (!file) throw std::runtime_error("Terrain profile file unavailable");
    }
    TerrainWorkProfile(const TerrainWorkProfile&) = delete;
    TerrainWorkProfile& operator=(const TerrainWorkProfile&) = delete;
    ~TerrainWorkProfile() {
        if (!file) return;
        std::fprintf(file, "group,function,qpc_hz,calls,inclusive_ticks\n");
        constexpr const char* groups[]{"other", "ter", "bwg"};
        constexpr const char* functions[]{"53f2e0", "545720", "555a70"};
        for (unsigned g = 0; g < 3; ++g)
            for (unsigned k = 0; k < 3; ++k)
                std::fprintf(file, "%s,%s,%llu,%llu,%llu\n", groups[g], functions[k],
                    (unsigned long long)frequency,
                    (unsigned long long)counts[g][k].calls,
                    (unsigned long long)counts[g][k].ticks);
        for (const auto& [name, count] : mesh_names)
            std::fprintf(file, "node:%s,53f2e0,%llu,%llu,%llu\n", name.c_str(),
                (unsigned long long)frequency, (unsigned long long)count.calls,
                (unsigned long long)count.ticks);
        std::fclose(file);
    }
    static std::uint64_t now() {
        const DWORD error = ::GetLastError();
        LARGE_INTEGER q{};
        ::QueryPerformanceCounter(&q);
        ::SetLastError(error);
        return std::uint64_t(q.QuadPart);
    }
    struct Scope {
        TerrainWorkProfile& profile;
        unsigned kind{}, group{}, previous{};
        std::uint64_t start{};
        Count* named{};
        bool active{}, mesh{};
        Scope(TerrainWorkProfile& p, unsigned k, unsigned frame, unsigned category = 0,
              const std::string& name = {})
            : profile(p), kind(k), previous(p.group), mesh(k == 0) {
            active = p.file && frame >= p.from;
            if (!active) return;
            if (mesh) { p.group = category; named = &p.mesh_names[name]; }
            group = p.group;
            start = now();
        }
        ~Scope() {
            if (!active) return;
            auto& count = profile.counts[group][kind];
            const auto ticks = now() - start;
            count.ticks += ticks;
            ++count.calls;
            if (named) { named->ticks += ticks; ++named->calls; }
            if (mesh) profile.group = previous;
        }
    };
};
}
