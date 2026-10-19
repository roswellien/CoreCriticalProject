#pragma once

#include <algorithm>
#include <cstdint>
#include <map>
#include <stdexcept>
#include <vector>

namespace mw34::heap_partitions {

// Packed guest allocations keep each heap's regions and free blocks private.
// A codec HeapFree must never make its decoded pixels available to the CRT heap.
struct GuestHeap {
    static constexpr unsigned lo = 0x50000000, hi = 0x70000000, chunk = 0x100000;
    unsigned top = lo, mapped = lo, region_end = lo;
    std::map<unsigned, unsigned> free_blocks, live, regions, region_owners;
    std::uint64_t allocs{}, frees{};

    unsigned region_of(unsigned address) const {
        auto it = regions.upper_bound(address);
        if (it == regions.begin())
            return 0;
        --it;
        return address < it->second ? it->first : 0;
    }
    bool contains(unsigned address, unsigned bytes) const {
        return address >= lo && std::uint64_t(address) + bytes <= mapped;
    }
    unsigned owner_of(unsigned address) const {
        auto it = region_owners.find(region_of(address));
        if (it == region_owners.end())
            throw std::runtime_error("Guest heap region has no owner");
        return it->second;
    }

    template <class Commit, class Clear>
    unsigned allocate(unsigned bytes, bool zero, unsigned owner, Commit commit, Clear clear) {
        const auto wide_need = (std::uint64_t(std::max(bytes, 1U)) + 15U) & ~std::uint64_t(15);
        if (wide_need > hi - lo)
            return 0;
        const unsigned need = unsigned(wide_need);
        unsigned at = 0;
        for (auto it = free_blocks.begin(); it != free_blocks.end(); ++it) {
            if (it->second < need || owner_of(it->first) != owner)
                continue;
            at = it->first;
            const unsigned rest = it->second - need;
            free_blocks.erase(it);
            if (rest)
                free_blocks[at + need] = rest;
            break;
        }
        if (!at) {
            const bool other_heap = top < region_end && owner_of(top) != owner;
            if (other_heap || std::uint64_t(top) + need > region_end) {
                const unsigned size = unsigned(
                    std::max<std::uint64_t>(chunk, (wide_need + 0xffffU) & ~std::uint64_t(0xffff)));
                if (std::uint64_t(mapped) + size > hi)
                    return 0;
                commit(mapped, size);
                if (other_heap)
                    free_blocks.emplace(top, region_end - top);
                regions.emplace(mapped, mapped + size);
                region_owners.emplace(mapped, owner);
                top = mapped;
                mapped += size;
                region_end = mapped;
            }
            at = top;
            top += need;
        }
        if (zero)
            clear(at, need);
        live.emplace(at, bytes);
        ++allocs;
        return at;
    }

    void release(unsigned at) {
        auto it = live.find(at);
        if (it == live.end())
            throw std::runtime_error("HeapFree of a pointer that is not a live guest heap block");
        unsigned size =
            unsigned((std::uint64_t(std::max(it->second, 1U)) + 15U) & ~std::uint64_t(15));
        live.erase(it);
        ++frees;
        const unsigned region = region_of(at);
        auto next = free_blocks.lower_bound(at);
        if (next != free_blocks.end() && at + size == next->first &&
            region_of(next->first) == region) {
            size += next->second;
            next = free_blocks.erase(next);
        }
        if (next != free_blocks.begin()) {
            auto previous = std::prev(next);
            if (previous->first + previous->second == at && region_of(previous->first) == region) {
                previous->second += size;
                return;
            }
        }
        free_blocks[at] = size;
    }

    // Retain mapped reservations until host shutdown, as before; end only this
    // heap's live blocks. Other heaps and environment snapshots remain valid.
    std::size_t destroy(unsigned owner) {
        std::vector<unsigned> blocks;
        for (const auto &[at, size] : live) {
            (void)size;
            if (owner_of(at) == owner)
                blocks.push_back(at);
        }
        for (unsigned at : blocks)
            release(at);
        return blocks.size();
    }
};

} // namespace mw34::heap_partitions
