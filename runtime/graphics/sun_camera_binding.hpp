#pragma once
#include <array>
#include <bit>
#include <cmath>
#include <cstdint>
#include <stdexcept>
#include <string>

namespace mw34::sun {
// Read-only provenance for the original renderer's 12-word camera activation.
// Original effects also activate temporary matrices; those are not world views.
// Both source ownership and the exact active inverse authenticate world lighting.
// Storage is column-major: original code flips columns Y and Z by sign-bit XOR.
struct CameraBinding {
    using Words = std::array<std::uint32_t, 12>;
    std::uint32_t source{};
    Words renderer{}, inverse{};
    bool valid{};

    void capture(std::uint32_t address, Words original, const Words &actual, const Words &view) {
        valid = false;
        for (unsigned i = 3; i < 9; ++i)
            original[i] ^= 0x80000000U;
        if (!address || original != actual)
            throw std::runtime_error("Sun camera producer copy disagrees with renderer basis");
        source = address;
        renderer = actual;
        inverse = view;
        valid = true;
    }
    bool owns(std::uint32_t address) const { return valid && source == address; }
    void validate(const Words &view) const {
        if (!valid)
            throw std::runtime_error("Sun camera activation is missing");
        if(inverse!=view)
            throw std::runtime_error("Sun camera activated inverse view changed");
    }
    std::array<double, 16> matrix() const {
        if (!valid)
            throw std::runtime_error("Sun camera has no authenticated activation");
        std::array<double, 16> result{0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1};
        for (unsigned row = 0; row < 3; ++row)
            for (unsigned col = 0; col < 4; ++col) {
                const auto value = std::bit_cast<float>(renderer[col * 3 + row]);
                if (!std::isfinite(value))
                    throw std::runtime_error("Nonfinite sun camera activation");
                result[row * 4 + col] = value;
            }
        return result;
    }
};
} // namespace mw34::sun
