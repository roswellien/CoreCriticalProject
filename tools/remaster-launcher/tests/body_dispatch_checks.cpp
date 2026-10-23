// Compile against the private candidate's authored body_dispatch.hpp. Exhaust
// the full table domain, including unaligned addresses and unsigned edges.
#include "body_dispatch.hpp"
#include <algorithm>
#include <cstdio>
#include <limits>

int main() {
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
