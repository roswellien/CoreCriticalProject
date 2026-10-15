#pragma once

#include "core/guest_address.hpp"

#include <array>
#include <concepts>
#include <cstddef>
#include <cstdint>
#include <map>
#include <span>
#include <stdexcept>
#include <vector>

namespace mw34 {

enum class Permissions : std::uint8_t { none = 0, read = 1, write = 2, execute = 4 };

[[nodiscard]] constexpr Permissions operator|(Permissions lhs, Permissions rhs) noexcept {
    return static_cast<Permissions>(static_cast<std::uint8_t>(lhs) |
                                    static_cast<std::uint8_t>(rhs));
}

enum class MemoryFaultReason { address_overflow, unmapped, permission_denied };

class MemoryFault : public std::runtime_error {
  public:
    MemoryFault(MemoryFaultReason reason, const char *message)
        : std::runtime_error(message), reason_(reason) {}

    [[nodiscard]] MemoryFaultReason reason() const noexcept { return reason_; }

  private:
    MemoryFaultReason reason_;
};

template <typename T>
concept GuestScalar = std::unsigned_integral<T> && !std::same_as<T, bool> && sizeof(T) <= 8;

// Native-host fork of runtime/memory/guest_memory.hpp (the runtime file and its implementation stay unchanged; they
// are pinned by acceptance evidence). Every host translation unit includes "memory/guest_memory.hpp", and this
// directory precedes runtime/ on the host include path, so the native host uses this definition throughout.
//
// Flat guest address space: one host reservation of 4 GiB (+64 KiB guard) per GuestMemory, and every region's bytes
// live at flat_base() + guest address. Recompiled code built with inline_objects.py --flat-mem accesses guest memory
// as base + address directly; host page protection (the union of the regions touching a page) makes unmapped and
// protected pages fault. map/unmap/protect/read/write keep the exact semantics of the original class: regions are
// exact byte ranges, zero-initialised, non-overlapping; host transfers are checked against them and fault as before.
class GuestMemory {
  public:
    static constexpr std::uint64_t address_space_size = std::uint64_t{1} << 32;

    GuestMemory() = default;
    GuestMemory(const GuestMemory &other);
    GuestMemory(GuestMemory &&other) noexcept;
    GuestMemory &operator=(const GuestMemory &other);
    GuestMemory &operator=(GuestMemory &&other) noexcept;
    ~GuestMemory();

    // Mapping is exact, zero-initialized, and rejects overlap and wrapping extents.
    void map(GuestAddress start, std::uint64_t size, Permissions permissions);
    void unmap(GuestAddress start);
    void protect(GuestAddress start, Permissions permissions);

    // Nonempty transfers must fit in one mapping. Empty transfers are no-ops.
    void read(GuestAddress address, std::span<std::byte> destination) const;
    void write(GuestAddress address, std::span<const std::byte> source);

    // Explicit little-endian serialization permits unaligned x86 accesses on any host.
    template <GuestScalar T> [[nodiscard]] T load(GuestAddress address) const {
        std::array<std::byte, sizeof(T)> bytes{};
        read(address, bytes);
        std::uint64_t value = 0;
        for (std::size_t index = 0; index < bytes.size(); ++index) {
            value |= std::uint64_t{std::to_integer<std::uint8_t>(bytes[index])} << (index * 8);
        }
        return static_cast<T>(value);
    }

    template <GuestScalar T> void store(GuestAddress address, T value) {
        std::array<std::byte, sizeof(T)> bytes{};
        for (std::size_t index = 0; index < bytes.size(); ++index) {
            bytes[index] = static_cast<std::byte>((std::uint64_t{value} >> (index * 8)) & 0xffU);
        }
        write(address, bytes);
    }

    // Host address of guest address 0 (reserved on first map; null before).
    [[nodiscard]] std::byte *flat_base() const noexcept { return base_; }
    // True when the host address lies inside this space's reservation (fault attribution).
    [[nodiscard]] bool owns_host(const void *p) const noexcept {
        return base_ && p >= base_ && p < base_ + address_space_size + 0x10000;
    }

  private:
    struct Region {
        std::uint64_t size;
        Permissions permissions;
    };

    using Regions = std::map<std::uint32_t, Region>;
    [[nodiscard]] Regions::const_iterator find_access(GuestAddress address, std::uint64_t size,
                                                      Permissions permission) const;
    static void validate_permissions(Permissions permissions);
    void reserve();
    void release() noexcept;
    void refresh_pages(std::uint64_t lo, std::uint64_t hi);  // commit/decommit/protect pages of [lo, hi)
    Regions regions_;
    std::byte *base_{};
};

} // namespace mw34
