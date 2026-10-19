#include "native-overrides/surface_page_pool.hpp"
#include <cassert>
#include <cstdio>

int main() {
    using mw34::surface_pages::FreeList;
    FreeList pool;
    assert(pool.take(4096) == 0);
    pool.put(0x80002000, 8192);
    pool.put(0x80000000, 4096);
    pool.put(0x80001000, 4096);
    assert(pool.take(12288) == 0x80000000); // merge both neighbors, split remainder
    assert(pool.take(4096) == 0x80003000);
    assert(pool.take(4096) == 0);
    pool.put(0x80000000, 16384);
    pool.put(0x90000000, 4096);
    assert(pool.take(4096) == 0x90000000); // preserve larger allocations
    bool rejected = false;
    try { pool.put(0x80001000, 4096); } catch (...) { rejected = true; }
    assert(rejected);
    assert(pool.take(16384) == 0x80000000); // rejected overlap did not change ownership
    for (unsigned i=0; i<100000; ++i) {
        pool.put(0xeff00000, 0x100000);
        assert(pool.take(0x100000) == 0xeff00000); // repeated scene-sized reuse
    }
    rejected = false;
    try { pool.put(0xfffff000, 8192); } catch (...) { rejected = true; }
    assert(rejected);
    std::puts("Surface page pool checks passed");
}
