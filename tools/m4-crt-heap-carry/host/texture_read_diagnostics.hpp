#pragma once
#include <array>
#include <cstdint>
#include <span>
#include <cstdio>
#include <cstring>
#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <intrin.h>
#endif

namespace mw34::texture_diagnostics {
#ifdef _WIN32
inline void hardware_summary() {
    char brand[49]{};
    int cpu[4]{};
    __cpuid(cpu, int(0x80000000U));
    if (unsigned(cpu[0]) >= 0x80000004U) {
        for (unsigned leaf=0;leaf<3;++leaf) {
            __cpuid(cpu,int(0x80000002U+leaf));
            std::memcpy(brand+leaf*16,cpu,16);
        }
    }
    std::fprintf(stderr,"Playtest hardware: CPU=%s logical_processors=%lu\n",brand[0]?brand:"unavailable",::GetActiveProcessorCount(ALL_PROCESSOR_GROUPS));
    MEMORYSTATUSEX memory{};memory.dwLength=sizeof(memory);
    if (::GlobalMemoryStatusEx(&memory))
        std::fprintf(stderr,"Playtest memory: total_physical_MiB=%llu available_physical_MiB=%llu memory_load_percent=%lu\n",memory.ullTotalPhys/1048576ULL,memory.ullAvailPhys/1048576ULL,memory.dwMemoryLoad);
    else std::fprintf(stderr,"Playtest memory: unavailable error=%lu\n",::GetLastError());
}
#endif
struct ReadFrame {
    unsigned site{}, destination{}, size{}, count{}, stream{}, object{};
    bool found{};
};

// Admitted MSVCRT fread at 78022459 saves EBP and ESI before locking.
// These three MW3 call sites preserve ESI as the live texture descriptor.
// Read metadata only when the exact return chain and saved frame are readable.
template<class Valid, class Read>
ReadFrame read_frame(std::span<const unsigned> returns, std::span<const unsigned> slots,
                     Valid valid, Read read) {
    for (unsigned i = 0; i < returns.size() && i < slots.size(); ++i) {
        const unsigned site = returns[i], slot = slots[i];
        if (site != 0x00517e2d && site != 0x00517e5d && site != 0x00517ea7) continue;
        if (slot < 8 || slot > 0xffffffe7U || !valid(slot - 8, 28)) return {};
        return {site, read(slot + 4), read(slot + 8), read(slot + 12),
                read(slot + 16), read(slot - 8), true};
    }
    return {};
}

struct Seek {
    unsigned handle{}, offset{}, high_pointer{}, origin{}, result{}, error{};
    bool replacement{}, texture_caller{}, widened{};
};

// TextureBank::load's call at 518e11 enters 517f80, whose first push saves
// ESI: the matched 40-byte table record (32-byte name, offset, palette index).
template<class Valid, class Read>
unsigned lookup_entry(std::span<const unsigned> returns, std::span<const unsigned> slots,
                      Valid valid, Read read) {
    for (unsigned i=0;i<returns.size() && i<slots.size();++i) {
        if (returns[i] != 0x00518e16 || slots[i] < 4 || !valid(slots[i]-4,4)) continue;
        const unsigned entry=read(slots[i]-4);
        return entry && entry <= 0xffffffd7U && valid(entry,40) ? entry : 0;
    }
    return 0;
}
struct RecentSeeks {
    std::array<Seek, 8> entries{};
    unsigned count{};
    void push(Seek seek) { entries[count++ % entries.size()] = seek; }
};
} // namespace mw34::texture_diagnostics
