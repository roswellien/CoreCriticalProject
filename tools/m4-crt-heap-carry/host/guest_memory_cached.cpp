// Native-host implementation of mw34::GuestMemory (the host fork memory/guest_memory.hpp; runtime/memory/
// guest_memory.cpp stays unchanged, it is pinned by earlier acceptance evidence). The interface and every fault are
// those of the original class; the storage is flat: one host reservation per guest address space, each region's
// bytes at flat_base() + guest address. Pages are committed while any region touches them, with host protection
// from the union of those regions' permissions (read or execute -> read-only, write -> read/write, none -> no
// access), so recompiled code that accesses base + address directly (inline_objects.py --flat-mem) faults exactly
// on unmapped and protected pages. Host transfers keep the exact per-region checks, served first from the small
// per-thread cache of recently hit regions (guest_memory_fast.hpp); every map/unmap/protect advances its generation.
#include "guest_memory_fast.hpp"

#define NOMINMAX
#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#include <algorithm>
#include <cstring>
#include <iterator>
#include <limits>
#include <new>
#include <string>

namespace mw34 {
using fastmem::cached;
using fastmem::generation;
using fastmem::slot;

namespace {
constexpr std::uint64_t page = 4096;
constexpr std::uint64_t reservation = GuestMemory::address_space_size + 0x10000;  // 64 KiB guard past 4 GiB
[[noreturn]] void vm_fail(const char *what, std::uint64_t guest, std::uint64_t size) {
    throw std::runtime_error(std::string("Flat guest memory: ") + what + " failed at guest 0x" + std::to_string(guest) +
                             " size " + std::to_string(size) + " (Windows error " + std::to_string(::GetLastError()) + ")");
}
} // namespace

void GuestMemory::validate_permissions(Permissions permissions) {
    if ((static_cast<std::uint8_t>(permissions) & ~std::uint8_t{7}) != 0) {
        throw std::invalid_argument("Unknown guest memory permission bits");
    }
}

void GuestMemory::reserve() {
    if (base_) return;
    void *p = ::VirtualAlloc(nullptr, static_cast<SIZE_T>(reservation), MEM_RESERVE | MEM_WRITE_WATCH, PAGE_NOACCESS);
    if (!p) p = ::VirtualAlloc(nullptr, static_cast<SIZE_T>(reservation), MEM_RESERVE, PAGE_NOACCESS);
    if (!p) vm_fail("4 GiB reservation", 0, reservation);
    base_ = static_cast<std::byte *>(p);
}

void GuestMemory::release() noexcept {
    if (base_) {
        ::VirtualFree(base_, 0, MEM_RELEASE);
        base_ = nullptr;
    }
}

GuestMemory::~GuestMemory() { release(); }

GuestMemory::GuestMemory(GuestMemory &&other) noexcept : regions_(std::move(other.regions_)), base_(other.base_) {
    other.base_ = nullptr;
    other.regions_.clear();
    ++generation;
}

GuestMemory &GuestMemory::operator=(GuestMemory &&other) noexcept {
    if (this != &other) {
        release();
        regions_ = std::move(other.regions_);
        base_ = other.base_;
        other.base_ = nullptr;
        other.regions_.clear();
        ++generation;
    }
    return *this;
}

GuestMemory::GuestMemory(const GuestMemory &other) { *this = other; }

GuestMemory &GuestMemory::operator=(const GuestMemory &other) {
    if (this == &other) return *this;
    release();
    regions_ = other.regions_;
    if (!regions_.empty()) {
        reserve();
        for (const auto &[start, region] : regions_) {  // commit writable, copy the bytes, then apply protections
            std::byte *dst = base_ + (start & ~(page - 1));
            const std::uint64_t hi = (std::uint64_t{start} + region.size + page - 1) & ~(page - 1);
            if (!::VirtualAlloc(dst, static_cast<SIZE_T>(hi - (start & ~(page - 1))), MEM_COMMIT, PAGE_READWRITE)) vm_fail("copy commit", start, region.size);
            DWORD old{};
            ::VirtualProtect(dst, static_cast<SIZE_T>(hi - (start & ~(page - 1))), PAGE_READWRITE, &old);
        }
        for (const auto &[start, region] : regions_) {
            DWORD old{};
            const std::uint64_t lo = start & ~(page - 1), hi = (std::uint64_t{start} + region.size + page - 1) & ~(page - 1);
            ::VirtualProtect(other.base_ + lo, static_cast<SIZE_T>(hi - lo), PAGE_READONLY, &old);  // readable source view
            std::memcpy(base_ + start, other.base_ + start, static_cast<std::size_t>(region.size));
        }
        for (const auto &[start, region] : regions_) {
            refresh_pages(start, std::uint64_t{start} + region.size);
            const_cast<GuestMemory &>(other).refresh_pages(start, std::uint64_t{start} + region.size);
        }
    }
    ++generation;
    return *this;
}

// Recomputes [lo, hi) page by page: decommit pages no region touches; commit the others with the union of the
// touching regions' permissions.
void GuestMemory::refresh_pages(std::uint64_t lo, std::uint64_t hi) {
    if (!base_) return;
    for (std::uint64_t p = lo & ~(page - 1); p < hi; p += page) {
        std::uint8_t perms = 0;
        bool touched = false;
        auto it = regions_.upper_bound(static_cast<std::uint32_t>(p));
        if (it != regions_.begin()) --it;
        for (; it != regions_.end() && it->first < p + page; ++it) {
            if (std::uint64_t{it->first} + it->second.size <= p) continue;
            touched = true;
            perms |= static_cast<std::uint8_t>(it->second.permissions);
        }
        std::byte *at = base_ + p;
        if (!touched) {
            ::VirtualFree(at, static_cast<SIZE_T>(page), MEM_DECOMMIT);
            continue;
        }
        if (!::VirtualAlloc(at, static_cast<SIZE_T>(page), MEM_COMMIT, PAGE_READWRITE)) vm_fail("page commit", p, page);
        const DWORD protection = (perms & static_cast<std::uint8_t>(Permissions::write)) ? PAGE_READWRITE
                                 : (perms & (static_cast<std::uint8_t>(Permissions::read) | static_cast<std::uint8_t>(Permissions::execute))) ? PAGE_READONLY
                                                                                                                                          : PAGE_NOACCESS;
        DWORD old{};
        if (!::VirtualProtect(at, static_cast<SIZE_T>(page), protection, &old)) throw std::runtime_error("Guest page protection failed");
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
        const auto previous_end = std::uint64_t{previous->first} + previous->second.size;
        if (previous_end > start.value) {
            throw std::invalid_argument("Guest mapping overlaps an existing region");
        }
    }

    reserve();
    // Zero-initialised: commit the pages writable and clear the region's bytes (a page shared with a neighbouring
    // region may hold bytes of an earlier mapping), then apply the final protections.
    const std::uint64_t lo = start.value & ~(page - 1), hi = (end + page - 1) & ~(page - 1);
    if (!::VirtualAlloc(base_ + lo, static_cast<SIZE_T>(hi - lo), MEM_COMMIT, PAGE_READWRITE)) vm_fail("map commit", start.value, size);
    DWORD old{};
    ::VirtualProtect(base_ + lo, static_cast<SIZE_T>(hi - lo), PAGE_READWRITE, &old);
    std::memset(base_ + start.value, 0, static_cast<std::size_t>(size));
    regions_.emplace(start.value, Region{size, permissions});
    refresh_pages(lo, hi);
    ++generation;
}

void GuestMemory::unmap(GuestAddress start) {
    const auto region = regions_.find(start.value);
    if (region == regions_.end()) {
        throw std::invalid_argument("Unmap requires the exact start of an existing region");
    }
    const std::uint64_t end = std::uint64_t{start.value} + region->second.size;
    regions_.erase(region);
    refresh_pages(start.value, end);
    ++generation;
}

void GuestMemory::protect(GuestAddress start, Permissions permissions) {
    validate_permissions(permissions);
    const auto region = regions_.find(start.value);
    if (region == regions_.end()) {
        throw std::invalid_argument("Protect requires the exact start of an existing region");
    }
    region->second.permissions = permissions;
    refresh_pages(start.value, std::uint64_t{start.value} + region->second.size);
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
    if (offset >= region->second.size || size > region->second.size - offset) {
        throw MemoryFault(MemoryFaultReason::unmapped,
                          "Guest access must fit in one mapped region");
    }
    if ((static_cast<std::uint8_t>(region->second.permissions) &
         static_cast<std::uint8_t>(permission)) == 0) {
        throw MemoryFault(MemoryFaultReason::permission_denied, "Guest access permission denied");
    }
    auto &h = slot(address.value);
    h = {this, generation, region->first, region->second.size, base_ + region->first,
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
    (void)find_access(address, destination.size(), Permissions::read);
    std::copy_n(base_ + address.value, destination.size(), destination.data());
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
    (void)find_access(address, source.size(), Permissions::write);
    std::copy_n(source.data(), source.size(), base_ + address.value);
}

} // namespace mw34
