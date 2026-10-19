#pragma once
#include <cstdint>
#include <map>
#include <iterator>
#include <stdexcept>

namespace mw34::surface_pages {
// Only unmapped, unreferenced surface pages enter this pool. COM identities
// are never recycled along with the pixel addresses.
class FreeList {
    std::map<unsigned, unsigned> blocks;
public:
    void put(unsigned address, unsigned bytes) {
        if (!address || !bytes || (address & 4095) || (bytes & 4095) ||
            std::uint64_t(address) + bytes > 0x100000000ULL)
            throw std::runtime_error("Invalid retired surface pages");
        auto next = blocks.lower_bound(address);
        if (next != blocks.end() && std::uint64_t(address) + bytes > next->first)
            throw std::runtime_error("Overlapping retired surface pages");
        if (next != blocks.begin()) {
            auto prev = std::prev(next);
            const auto end = std::uint64_t(prev->first) + prev->second;
            if (end > address) throw std::runtime_error("Overlapping retired surface pages");
            if (end == address) { address = prev->first; bytes += prev->second; blocks.erase(prev); }
        }
        if (next != blocks.end() && std::uint64_t(address) + bytes == next->first) {
            bytes += next->second; blocks.erase(next);
        }
        blocks.emplace(address, bytes);
    }
    unsigned take(unsigned bytes) {
        if (!bytes || (bytes & 4095)) throw std::runtime_error("Invalid surface page request");
        auto best = blocks.end();
        for (auto it = blocks.begin(); it != blocks.end(); ++it)
            if (it->second >= bytes && (best == blocks.end() || it->second < best->second)) best = it;
        if (best == blocks.end()) return 0;
        const unsigned address = best->first, left = best->second - bytes;
        blocks.erase(best);
        if (left) blocks.emplace(address + bytes, left);
        return address;
    }
};
}
