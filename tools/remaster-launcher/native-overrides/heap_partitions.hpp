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
    // Public accounting describes guest addresses, not host pointers. Callers
    // serialize access; callbacks implement actual guest mapping and zero fill.
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
        // Arena/high-water containment only. This does not prove that a pointer
        // is a live allocation or that its region belongs to a particular heap.
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
        // Reserve at least one byte, rounded to 16-byte alignment, while live[]
        // retains the requested size (including zero) for guest heap semantics.
        const auto aligned_bytes_wide =
            (std::uint64_t(std::max(bytes, 1U)) + 15U) & ~std::uint64_t(15);
        if (aligned_bytes_wide > hi - lo)
            return 0;
        const unsigned aligned_bytes = unsigned(aligned_bytes_wide);
        unsigned allocation_address = 0;
        for (auto it = free_blocks.begin(); it != free_blocks.end(); ++it) {
            if (it->second < aligned_bytes || owner_of(it->first) != owner)
                continue;
            allocation_address = it->first;
            const unsigned remaining_bytes = it->second - aligned_bytes;
            free_blocks.erase(it);
            if (remaining_bytes)
                free_blocks[allocation_address + aligned_bytes] = remaining_bytes;
            break;
        }
        if (!allocation_address) {
            // A different owner cannot consume this region's unused tail. Park
            // that tail for its original owner and commit a separate region.
            const bool owner_changed = top < region_end && owner_of(top) != owner;
            if (owner_changed || std::uint64_t(top) + aligned_bytes > region_end) {
                const unsigned size = unsigned(std::max<std::uint64_t>(
                    chunk, (aligned_bytes_wide + 0xffffU) & ~std::uint64_t(0xffff)));
                if (std::uint64_t(mapped) + size > hi)
                    return 0;
                commit(mapped, size);
                if (owner_changed)
                    free_blocks.emplace(top, region_end - top);
                regions.emplace(mapped, mapped + size);
                region_owners.emplace(mapped, owner);
                top = mapped;
                mapped += size;
                region_end = mapped;
            }
            allocation_address = top;
            top += aligned_bytes;
        }
        if (zero)
            clear(allocation_address, aligned_bytes);
        // Callback exceptions propagate. This allocator does not provide a
        // rollback transaction for guest mappings or a failed zero-fill callback.
        live.emplace(allocation_address, bytes);
        ++allocs;
        return allocation_address;
    }

    void release(unsigned allocation_address) {
        // Accept allocation starts only. Coalesce adjacent free blocks within
        // one committed region; even equal-owner regions retain their boundary.
        auto it = live.find(allocation_address);
        if (it == live.end())
            throw std::runtime_error("HeapFree of a pointer that is not a live guest heap block");
        unsigned size =
            unsigned((std::uint64_t(std::max(it->second, 1U)) + 15U) & ~std::uint64_t(15));
        live.erase(it);
        ++frees;
        const unsigned region = region_of(allocation_address);
        auto next_free_block = free_blocks.lower_bound(allocation_address);
        if (next_free_block != free_blocks.end() &&
            allocation_address + size == next_free_block->first &&
            region_of(next_free_block->first) == region) {
            size += next_free_block->second;
            next_free_block = free_blocks.erase(next_free_block);
        }
        if (next_free_block != free_blocks.begin()) {
            auto previous_free_block = std::prev(next_free_block);
            if (previous_free_block->first + previous_free_block->second == allocation_address &&
                region_of(previous_free_block->first) == region) {
                previous_free_block->second += size;
                return;
            }
        }
        free_blocks[allocation_address] = size;
    }

    // Retain mapped reservations until host shutdown, as before; end only this
    // heap's live blocks. Other heaps and environment snapshots remain valid.
    std::size_t destroy(unsigned owner) {
        std::vector<unsigned> blocks;
        for (const auto &[allocation_address, size] : live) {
            (void)size;
            if (owner_of(allocation_address) == owner)
                blocks.push_back(allocation_address);
        }
        for (unsigned allocation_address : blocks)
            release(allocation_address);
        return blocks.size();
    }
};

} // namespace mw34::heap_partitions
