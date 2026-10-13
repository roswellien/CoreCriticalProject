// Native-host implementation of mw34::GuestMemory (runtime/memory/guest_memory.hpp) with a small
// per-thread cache of recently hit regions. The interface, layout and every fault are those of
// runtime/memory/guest_memory.cpp (left unchanged; it is pinned by earlier acceptance evidence): an access
// is served from the cache only when it lies entirely inside a cached region whose permission allows it,
// and any map/unmap/protect advances a generation that invalidates the cache. Misses take the original
// ordered-map lookup. The native host links this object ahead of the library member.
#include "memory/guest_memory.hpp"

#include <algorithm>
#include <iterator>
#include <limits>

namespace mw34 {
namespace {
struct Hit {
    const GuestMemory *owner;
    std::uint64_t generation;
    std::uint32_t start;
    std::uint64_t size;
    std::byte *bytes;
    std::uint8_t permissions;
};
std::uint64_t generation = 1;
// Direct-mapped by guest page: each slot remembers the region that covered the last access to a page
// mapping onto it.
thread_local std::array<Hit, 1024> hits{};
Hit &slot(std::uint32_t address) { return hits[(address >> 12) & 1023]; }
const Hit *cached(const GuestMemory *owner, std::uint32_t address, std::uint64_t size, Permissions permission) {
    const auto &h = slot(address);
    if (h.owner == owner && h.generation == generation && address >= h.start &&
        std::uint64_t{address} - h.start + size <= h.size &&
        (h.permissions & static_cast<std::uint8_t>(permission)) != 0)
        return &h;
    return nullptr;
}
} // namespace

// Native-host fast path: the host pointer for [address, address+size) when a cached region holds it with
// the permission; null otherwise (the caller then takes the ordinary load/store path, which fills the slot).
std::byte *guest_fast_pointer(const GuestMemory *owner, std::uint32_t address, std::uint64_t size, Permissions permission) {
    const auto *h = cached(owner, address, size, permission);
    return h ? h->bytes + (address - h->start) : nullptr;
}

void GuestMemory::validate_permissions(Permissions permissions) {
    if ((static_cast<std::uint8_t>(permissions) & ~std::uint8_t{7}) != 0) {
        throw std::invalid_argument("Unknown guest memory permission bits");
    }
}

void GuestMemory::map(GuestAddress start, std::uint64_t size, Permissions permissions) {
    validate_permissions(permissions);
    if (size == 0 || size > address_space_size - start.value) {
        throw std::invalid_argument("Guest mapping must be nonempty and fit in 32-bit space");
    }
    if (size > std::numeric_limits<std::size_t>::max()) {
        throw std::length_error("Guest mapping is too large for host storage");
    }

    const auto next = regions_.lower_bound(start.value);
    const auto end = std::uint64_t{start.value} + size;
    if (next != regions_.end() && end > next->first) {
        throw std::invalid_argument("Guest mapping overlaps an existing region");
    }
    if (next != regions_.begin()) {
        const auto previous = std::prev(next);
        const auto previous_end = std::uint64_t{previous->first} + previous->second.bytes.size();
        if (previous_end > start.value) {
            throw std::invalid_argument("Guest mapping overlaps an existing region");
        }
    }

    regions_.emplace(start.value,
                     Region{std::vector<std::byte>(static_cast<std::size_t>(size)), permissions});
    ++generation;
}

void GuestMemory::unmap(GuestAddress start) {
    if (regions_.erase(start.value) == 0) {
        throw std::invalid_argument("Unmap requires the exact start of an existing region");
    }
    ++generation;
}

void GuestMemory::protect(GuestAddress start, Permissions permissions) {
    validate_permissions(permissions);
    const auto region = regions_.find(start.value);
    if (region == regions_.end()) {
        throw std::invalid_argument("Protect requires the exact start of an existing region");
    }
    region->second.permissions = permissions;
    ++generation;
}

GuestMemory::Regions::const_iterator
GuestMemory::find_access(GuestAddress address, std::uint64_t size, Permissions permission) const {
    if (size > address_space_size - address.value) {
        throw MemoryFault(MemoryFaultReason::address_overflow, "Guest memory access wraps 32 bits");
    }
    auto region = regions_.upper_bound(address.value);
    if (region == regions_.begin()) {
        throw MemoryFault(MemoryFaultReason::unmapped, "Guest address is not mapped");
    }
    --region;
    const auto offset = std::uint64_t{address.value} - region->first;
    if (offset >= region->second.bytes.size() || size > region->second.bytes.size() - offset) {
        throw MemoryFault(MemoryFaultReason::unmapped,
                          "Guest access must fit in one mapped region");
    }
    if ((static_cast<std::uint8_t>(region->second.permissions) &
         static_cast<std::uint8_t>(permission)) == 0) {
        throw MemoryFault(MemoryFaultReason::permission_denied, "Guest access permission denied");
    }
    auto &h = slot(address.value);
    h = {this, generation, region->first, region->second.bytes.size(),
         const_cast<std::byte *>(region->second.bytes.data()),
         static_cast<std::uint8_t>(region->second.permissions)};
    return region;
}

void GuestMemory::read(GuestAddress address, std::span<std::byte> destination) const {
    if (destination.empty()) {
        return;
    }
    if (const auto *h = cached(this, address.value, destination.size(), Permissions::read)) {
        std::copy_n(h->bytes + (address.value - h->start), destination.size(), destination.data());
        return;
    }
    const auto region = find_access(address, destination.size(), Permissions::read);
    const auto offset = static_cast<std::size_t>(address.value - region->first);
    std::copy_n(region->second.bytes.data() + offset, destination.size(), destination.data());
}

void GuestMemory::write(GuestAddress address, std::span<const std::byte> source) {
    if (source.empty()) {
        return;
    }
    if (const auto *h = cached(this, address.value, source.size(), Permissions::write)) {
        std::copy_n(source.data(), source.size(), h->bytes + (address.value - h->start));
        return;
    }
    // Check the entire transfer before touching storage, so failed writes change no bytes.
    const auto checked = find_access(address, source.size(), Permissions::write);
    auto &region = regions_.at(checked->first);
    const auto offset = static_cast<std::size_t>(address.value - checked->first);
    std::copy_n(source.data(), source.size(), region.bytes.data() + offset);
}

} // namespace mw34
