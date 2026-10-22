#pragma once
#include <cstdint>
#include <map>
#include <iterator>
#include <stdexcept>

namespace mw34::surface_pages {
// Only unmapped, unreferenced surface pages enter this pool. COM identities
// are never recycled along with the pixel addresses.
// The owning surface service serializes access; the pool owns no locks.
class FreeList {
    std::map<unsigned, unsigned> free_blocks_;

  public:
    // Record a retired guest-address range in 4096-byte units. The caller has
    // already removed mappings and references; this pool performs no unmapping.
    // Reject overlaps, then merge adjacent ranges on either side of this block.
    void put(unsigned address, unsigned bytes) {
        if (!address || !bytes || (address & 4095) || (bytes & 4095) ||
            std::uint64_t(address) + bytes > 0x100000000ULL)
            throw std::runtime_error("Invalid retired surface pages");
        auto next_block = free_blocks_.lower_bound(address);
        if (next_block != free_blocks_.end() && std::uint64_t(address) + bytes > next_block->first)
            throw std::runtime_error("Overlapping retired surface pages");
        if (next_block != free_blocks_.begin()) {
            auto prev = std::prev(next_block);
            const auto end = std::uint64_t(prev->first) + prev->second;
            if (end > address)
                throw std::runtime_error("Overlapping retired surface pages");
            if (end == address) {
                address = prev->first;
                bytes += prev->second;
                free_blocks_.erase(prev);
            }
        }
        if (next_block != free_blocks_.end() &&
            std::uint64_t(address) + bytes == next_block->first) {
            bytes += next_block->second;
            free_blocks_.erase(next_block);
        }
        free_blocks_.emplace(address, bytes);
    }
    unsigned take(unsigned bytes) {
        // Best fit minimizes the leftover range. Address-ordered iteration also
        // makes equal-size ties choose the lower address. Return zero if no
        // range fits; allocation/mapping and surface identity belong to callers.
        if (!bytes || (bytes & 4095))
            throw std::runtime_error("Invalid surface page request");
        auto best_fit = free_blocks_.end();
        for (auto it = free_blocks_.begin(); it != free_blocks_.end(); ++it)
            if (it->second >= bytes &&
                (best_fit == free_blocks_.end() || it->second < best_fit->second))
                best_fit = it;
        if (best_fit == free_blocks_.end())
            return 0;
        const unsigned address = best_fit->first, remaining_bytes = best_fit->second - bytes;
        free_blocks_.erase(best_fit);
        if (remaining_bytes)
            free_blocks_.emplace(address + bytes, remaining_bytes);
        return address;
    }
};
} // namespace mw34::surface_pages
