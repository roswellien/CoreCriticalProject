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

// Bootstrap memory backing for translated code. It does not execute x86 instructions.
class GuestMemory {
  public:
    static constexpr std::uint64_t address_space_size = std::uint64_t{1} << 32;

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

  private:
    struct Region {
        std::vector<std::byte> bytes;
        Permissions permissions;
    };

    using Regions = std::map<std::uint32_t, Region>;
    [[nodiscard]] Regions::const_iterator find_access(GuestAddress address, std::uint64_t size,
                                                      Permissions permission) const;
    static void validate_permissions(Permissions permissions);
    Regions regions_;
};

} // namespace mw34
