#pragma once

#include <cstdint>
#include <type_traits>

namespace mw34 {

// A guest pointer is an address in the 32-bit guest address space, never a host pointer.
struct GuestAddress {
    std::uint32_t value{};

    // x86 integer pointer arithmetic wraps modulo 2^32. Memory access is checked separately.
    [[nodiscard]] constexpr GuestAddress wrapping_add(std::uint32_t offset) const noexcept {
        return GuestAddress{static_cast<std::uint32_t>(value + offset)};
    }

    friend constexpr bool operator==(GuestAddress, GuestAddress) = default;
};

static_assert(sizeof(GuestAddress) == 4);
static_assert(std::is_trivially_copyable_v<GuestAddress>);

} // namespace mw34
