#pragma once

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iterator>
#include <map>
#include <stdexcept>
#include <vector>

namespace mw34::heap_partitions {

// Packed guest allocations keep each heap's regions and free blocks private.
// A codec HeapFree must never make its decoded pixels available to the CRT heap.
struct GuestHeap {
    // Public accounting describes guest addresses, not host pointers. Callers
    // serialize access; callbacks implement actual guest mapping and zero fill.
    // The region map and its slot table are written and read on the game thread only.
    static constexpr unsigned lo = 0x50000000, hi = 0x70000000, chunk = 0x100000;
    // Regions start and end on 64 KiB boundaries, so each 64 KiB slot of the
    // window lies inside at most one region and can record that region's end.
    static constexpr unsigned slot_shift = 16, slot_bytes = 1U << slot_shift;
    static constexpr unsigned slot_count = (hi - lo) >> slot_shift;
    unsigned top = lo, mapped = lo, region_end = lo;
    // The translated fast bridge may use only the uninterrupted heap prefix.
    // Allocations beyond a foreign mapping use the Stage's exact region checks.
    unsigned fast_mapped = lo;
    std::map<unsigned, unsigned> free_blocks, live, region_owners;
    std::uint64_t allocs{}, frees{};

    // Region start -> end. Read-only here; add_region keeps the slot table in step.
    const std::map<unsigned, unsigned> &regions() const { return regions_; }

    void add_region(unsigned start, unsigned end) {
        const bool aligned = (start & (slot_bytes - 1)) == 0 && (end & (slot_bytes - 1)) == 0;
        const bool inside_window = lo <= start && start < end && end <= hi;
        if (!aligned || !inside_window || overlaps_region(start, end))
            throw std::runtime_error("Invalid guest heap region");
        regions_.emplace(start, end);
        fill_slots(start, end, end);
    }
    // Only tests remove regions; the host keeps every reservation until shutdown.
    void erase_region(unsigned start) {
        auto region = regions_.find(start);
        if (region == regions_.end())
            return;
        fill_slots(region->first, region->second, 0);
        regions_.erase(region);
    }
    void clear_regions() {
        regions_.clear();
        std::fill(region_end_by_slot_.begin(), region_end_by_slot_.end(), 0U);
    }

    unsigned region_of(unsigned address) const {
        auto it = regions_.upper_bound(address);
        if (it == regions_.begin())
            return 0;
        --it;
        return address < it->second ? it->first : 0;
    }
    // Called for every guest pointer the host checks, so it reads one table slot
    // instead of searching the region map.
    bool contains(unsigned address, unsigned bytes) const {
        const bool inside = contains_by_slot(address, bytes);
        if (region_table_check_enabled() && inside != contains_by_map(address, bytes))
            throw std::runtime_error("Guest heap table disagrees with the region map");
        return inside;
    }
    unsigned owner_of(unsigned address) const {
        auto it = region_owners.find(region_of(address));
        if (it == region_owners.end())
            throw std::runtime_error("Guest heap region has no owner");
        return it->second;
    }

    struct Unoccupied {
        unsigned operator()(unsigned at, unsigned, unsigned) const { return at; }
    };
    template <class Commit, class Clear, class FindSpace = Unoccupied>
    unsigned allocate(unsigned bytes, bool zero, unsigned owner, Commit commit, Clear clear,
                      FindSpace find_space = {}) {
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
                const unsigned next = find_space(mapped, size, hi);
                if (!next) return 0;
                if (next < mapped || (next & 0xffffU) || std::uint64_t(next) + size > hi)
                    throw std::runtime_error("Invalid free guest heap range");
                commit(next, size);
                if (owner_changed)
                    free_blocks.emplace(top, region_end - top);
                add_region(next, next + size);
                region_owners.emplace(next, owner);
                top = next;
                mapped = next + size;
                if (next == fast_mapped) fast_mapped = mapped;
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

  private:
    std::map<unsigned, unsigned> regions_;
    // The end of the region covering each 64 KiB slot of [lo, hi), or 0 for none.
    std::vector<unsigned> region_end_by_slot_ = std::vector<unsigned>(slot_count, 0U);

    // MW34_HEAP_TABLE_CHECK=1 compares every lookup with the region map search.
    // It doubles the cost of each check, so it is for test runs only.
    static bool region_table_check_enabled() {
        static const bool value = [] {
            const char *setting = std::getenv("MW34_HEAP_TABLE_CHECK");
            if (!setting || !*setting || !std::strcmp(setting, "0"))
                return false;
            if (!std::strcmp(setting, "1"))
                return true;
            throw std::runtime_error("MW34_HEAP_TABLE_CHECK must be 0 or 1");
        }();
        return value;
    }
    // A new region may not share any byte with an existing one, including the same start.
    bool overlaps_region(unsigned start, unsigned end) const {
        auto next_region = regions_.lower_bound(start);
        if (next_region != regions_.end() && next_region->first < end)
            return true;
        if (next_region == regions_.begin())
            return false;
        auto previous_region = std::prev(next_region);
        return previous_region->second > start;
    }
    void fill_slots(unsigned start, unsigned end, unsigned value) {
        const unsigned first_slot = (start - lo) >> slot_shift;
        const unsigned end_slot = (end - lo) >> slot_shift;
        std::fill(region_end_by_slot_.begin() + first_slot, region_end_by_slot_.begin() + end_slot,
                  value);
    }
    bool contains_by_slot(unsigned address, unsigned bytes) const {
        // Every region lies inside the window, so an address outside it is in none.
        if (address < lo || address >= hi)
            return false;
        // Regions are aligned to slots and never overlap, so the slot holds the end
        // of the only region that can contain this address. Start 0, the old map
        // search's sentinel, can't occur: add_region rejects anything below lo.
        const unsigned end = region_end_by_slot_[(address - lo) >> slot_shift];
        return end != 0 && address < end && std::uint64_t(address) + bytes <= end;
    }
    // The previous lookup, kept as the reference for the check mode and the tests.
    bool contains_by_map(unsigned address, unsigned bytes) const {
        auto region = regions_.upper_bound(address);
        if (region == regions_.begin())
            return false;
        --region;
        // Preserve the zero-key sentinel and reject an empty range at a region's end.
        return region->first != 0 && address < region->second &&
               std::uint64_t(address) + bytes <= region->second;
    }
};

} // namespace mw34::heap_partitions
