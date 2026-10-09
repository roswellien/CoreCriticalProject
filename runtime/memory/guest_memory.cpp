#include "memory/guest_memory.hpp"

#include <algorithm>
#include <iterator>
#include <limits>

namespace mw34 {

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
}

void GuestMemory::unmap(GuestAddress start) {
    if (regions_.erase(start.value) == 0) {
        throw std::invalid_argument("Unmap requires the exact start of an existing region");
    }
}

void GuestMemory::protect(GuestAddress start, Permissions permissions) {
    validate_permissions(permissions);
    const auto region = regions_.find(start.value);
    if (region == regions_.end()) {
        throw std::invalid_argument("Protect requires the exact start of an existing region");
    }
    region->second.permissions = permissions;
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
    return region;
}

void GuestMemory::read(GuestAddress address, std::span<std::byte> destination) const {
    if (destination.empty()) {
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
    // Check the entire transfer before touching storage, so failed writes change no bytes.
    const auto checked = find_access(address, source.size(), Permissions::write);
    auto &region = regions_.at(checked->first);
    const auto offset = static_cast<std::size_t>(address.value - checked->first);
    std::copy_n(source.data(), source.size(), region.bytes.data() + offset);
}

} // namespace mw34
