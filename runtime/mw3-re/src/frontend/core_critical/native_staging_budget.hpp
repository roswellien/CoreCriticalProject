#pragma once

#include <cstddef>

namespace cc_mw3_re::staging {

// Native views can retain replacement textures until their final local lights
// are known. This is a staging allowance, not a total process or GPU limit.
inline constexpr std::size_t native_budget_bytes = std::size_t{1024} * 1024 * 1024;

inline constexpr bool fits(std::size_t current_bytes, std::size_t pending_bytes,
                           std::size_t maximum_bytes = native_budget_bytes) noexcept {
    return pending_bytes <= maximum_bytes && current_bytes <= maximum_bytes - pending_bytes;
}

} // namespace cc_mw3_re::staging
