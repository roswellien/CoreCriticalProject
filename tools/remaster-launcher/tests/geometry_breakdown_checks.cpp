#include "geometry_breakdown.hpp"
#include <cstring>

int main(int argc, char** argv) {
    if (argc != 2) return 1;
    if (::_putenv_s("MW34_GEOMETRY_BREAKDOWN", argv[1])) return 1;
    // Seed non-default rounding and exception flags. The diagnostic's lazy
    // setup, nested scopes, exception unwinding and output must preserve them.
    unsigned mxcsr = 0x5fa1;
    unsigned short control = 0x0b7f;
    __asm__ volatile("ldmxcsr %0; fldcw %1" :: "m"(mxcsr), "m"(control) : "memory");
    alignas(16) unsigned char before[512]{}, after[512]{};
    __asm__ volatile("fxsave64 %0" : "=m"(before) :: "memory");
    ::SetLastError(0x12345678);
    auto& profile = mw34::geometry_breakdown::profile();
    {
        mw34::geometry_breakdown::Scope outer(mw34::geometry_breakdown::MeshOther);
        try {
            mw34::geometry_breakdown::Scope inner(mw34::geometry_breakdown::Material);
            throw 7;
        } catch (int) {}
        if (profile.current != mw34::geometry_breakdown::MeshOther) return 2;
    }
    if (profile.current != mw34::geometry_breakdown::Other ||
        profile.calls[mw34::geometry_breakdown::MeshOther] != 1 ||
        profile.calls[mw34::geometry_breakdown::Material] != 1) return 3;
    mw34::geometry_breakdown::present(1200);
    if (::GetLastError() != 0x12345678) return 4;
    __asm__ volatile("fxsave64 %0" : "=m"(after) :: "memory");
    if (std::memcmp(before, after, 4) || std::memcmp(before+24, after+24, 4)) return 5;
    for (unsigned i = 0; i < mw34::geometry_breakdown::Count; ++i)
        if (profile.calls[i] || profile.ticks[i] || profile.inclusive[i]) return 6;
    std::puts("Geometry profiling: nested exception, FP and Win32 error checks passed");
}
