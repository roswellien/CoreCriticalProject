// Compile against the private candidate's authored body_dispatch.hpp. Exhaust
// the full table domain, including unaligned addresses and unsigned edges.
#include "body_dispatch.hpp"
#include <algorithm>
#include <cstdio>
#include <limits>

int main() {
    // These original adapters must reach Stage even with fast dispatch enabled.
    for (unsigned target : {0x584a70U,0x581230U,0x581400U,0x584b40U,0x5814b0U,0x40adf0U, 0x40ae70U, 0x40af30U, 0x418f30U, 0x418e90U,
                            0x421760U, 0x421900U, 0x421c00U, 0x421d40U, 0x421d50U,
                            0x421e40U, 0x493040U, 0x4931e0U, 0x4f32e0U, 0x4f3390U,
                            0x4eb050U, 0x4eaf90U, 0x4f3560U, 0x4f3620U, 0x4f3870U,
                            0x4f36b0U, 0x4f3920U})
        if (!mw34::body_dispatch::handled(target)) {
            std::fprintf(stderr, "Camera adapter %08x bypassed by fast dispatch\n", target);
            return 3;
        }
    unsigned checks{};
    const auto check = [&](unsigned target) {
        const bool expected = std::find(std::begin(mw34::body_dispatch::targets),
            std::end(mw34::body_dispatch::targets), target) != std::end(mw34::body_dispatch::targets);
        ++checks;
        return mw34::body_dispatch::handled(target) == expected;
    };
    for (unsigned target = 0x3fff00; target < 0x600100; ++target)
        if (!check(target)) return 1;
    for (unsigned target : {0U, 1U, 15U, 16U, 0x78002551U, 0xffffffefU, 0xfffffff0U,
                            std::numeric_limits<unsigned>::max()})
        if (!check(target)) return 2;
    std::printf("Body dispatch membership: %u checks, %zu handled targets\n", checks,
                std::size(mw34::body_dispatch::targets));
}
