// Native-host region cache for mw34::GuestMemory (guest_memory_cached.cpp), shared inline so the stage's
// per-access fast path needs no out-of-line call. A slot is served only when the access lies entirely inside
// the cached region and its permission allows it; every map/unmap/protect advances `generation`, which
// invalidates all slots. Misses take GuestMemory's ordinary lookup, which refills the slot.
#pragma once
#include "memory/guest_memory.hpp"

#include <array>
#include <cstdint>

namespace mw34::fastmem {
struct Hit {
    const GuestMemory *owner;
    std::uint64_t generation;
    std::uint32_t start;
    std::uint64_t size;
    std::byte *bytes;
    std::uint8_t permissions;
};
inline std::uint64_t generation = 1;
// Direct-mapped by guest page: each slot remembers the region that covered the last access to a page
// mapping onto it.
inline thread_local std::array<Hit, 1024> hits{};
inline Hit &slot(std::uint32_t address) { return hits[(address >> 12) & 1023]; }
inline const Hit *cached(const GuestMemory *owner, std::uint32_t address, std::uint64_t size, Permissions permission) {
    const auto &h = slot(address);
    if (h.owner == owner && h.generation == generation && address >= h.start &&
        std::uint64_t{address} - h.start + size <= h.size &&
        (h.permissions & static_cast<std::uint8_t>(permission)) != 0)
        return &h;
    return nullptr;
}
} // namespace mw34::fastmem

namespace mw34 {
// The host pointer for [address, address+size) when a cached region holds it with the permission; null
// otherwise (the caller then takes the ordinary load/store path, which fills the slot).
inline std::byte *guest_fast_pointer(const GuestMemory *owner, std::uint32_t address, std::uint64_t size, Permissions permission) {
    const auto *h = fastmem::cached(owner, address, size, permission);
    return h ? h->bytes + (address - h->start) : nullptr;
}
} // namespace mw34
