#include "memory/guest_memory.hpp"
#include "heap_partitions.hpp"
#include <iostream>
#include <limits>

int main() {
    using namespace mw34;
    using heap_partitions::GuestHeap;
    unsigned checks = 0;
    auto check = [&](bool value) {
        ++checks;
        if (!value) throw std::runtime_error("Guest heap address-space regression");
    };
    GuestMemory memory;
    constexpr unsigned module = 0x5f400000, module_end = 0x5f4ed000;
    memory.map({module}, module_end - module, Permissions::read | Permissions::write);
    memory.store<unsigned>({module}, 0x12345678);
    memory.protect({module}, Permissions::read);
    // The old allocation from the actual crash must fail on the real mapper.
    bool rejected = false;
    try { memory.map({0x5f3d0000}, 0x100000, Permissions::read | Permissions::write); }
    catch (const std::invalid_argument&) { rejected = true; }
    check(rejected);
    GuestHeap heap;
    heap.top = heap.mapped = heap.region_end = 0x5f3d0000;
    heap.fast_mapped = 0x5f3d0000;
    auto commit = [&](unsigned at, unsigned size) { memory.map({at}, size, Permissions::read | Permissions::write); };
    auto clear = [&](unsigned at, unsigned size) { std::vector<std::byte> bytes(size); memory.write({at}, bytes); };
    auto find = [&](unsigned at, unsigned size, unsigned limit) { return memory.find_unmapped_range(at, size, limit); };
    const auto allocated = heap.allocate(0x80000, true, 7, commit, clear, find);
    check(allocated == 0x5f4f0000 && heap.owner_of(allocated) == 7);
    check(heap.fast_mapped == 0x5f3d0000); // Old translated ABI never treats the skipped DLL as heap.
    check(heap.contains(allocated, 0x80000) && !heap.contains(module, 1));
    check(!heap.contains(allocated + 0xffff0, 32));
    check(memory.load<unsigned>({module}) == 0x12345678 && memory.load<unsigned>({allocated}) == 0);
    rejected = false;
    try { memory.store<unsigned>({module}, 0); } catch (const MemoryFault&) { rejected = true; }
    check(rejected); // Skipping must not weaken the module's read-only protection.
    heap.release(allocated);
    check(heap.allocate(0x80000, false, 7, commit, clear, find) == allocated);
    // Several adjacent/unaligned mappings and exact-fit holes.
    memory.map({0x60000001}, 0x10001, Permissions::none);
    memory.map({0x60020000}, 0x80000, Permissions::read);
    check(find(0x60000000, 0x100000, 0x70000000) == 0x600a0000);
    check(find(0x5f300000, 0x100000, module) == 0x5f300000);
    check(find(0x6ff00000, 0x100000, GuestHeap::hi) == 0x6ff00000);
    check(find(0x6ff00001, 0x100000, GuestHeap::hi) == 0);
    check(find(0xffff0001, 0x10000, 0xffffffff) == 0);
    check(find(GuestHeap::lo, 0, GuestHeap::hi) == 0);
    memory.map({0x6ff00000}, 0x100000, Permissions::none);
    GuestHeap exhausted;
    exhausted.top = exhausted.mapped = exhausted.region_end = 0x6ff00000;
    bool touched = false;
    check(exhausted.allocate(1, false, 9, [&](unsigned, unsigned) { touched = true; }, clear, find) == 0);
    check(!touched && exhausted.live.empty() && exhausted.regions().empty() && exhausted.mapped == 0x6ff00000);
    GuestHeap failed;
    bool threw = false;
    try { failed.allocate(1, false, 1, [](unsigned, unsigned) { throw std::runtime_error("commit failure"); }, clear, find); }
    catch (const std::runtime_error&) { threw = true; }
    check(threw && failed.live.empty() && failed.regions().empty() && failed.mapped == GuestHeap::lo);
    std::cout << "Real guest mapper and heap collision checks=" << checks << " failures=0\n";
}
