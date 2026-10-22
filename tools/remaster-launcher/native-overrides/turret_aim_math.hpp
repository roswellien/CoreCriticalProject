// Authored first-interval interpolation and degenerate-yaw guards.
// Callers own authentication, guest-memory access and the FP environment.
#pragma once
#include <array>
#include <bit>
#include <cmath>
#include <cstdint>
#include <stdexcept>

namespace mw34::turret_aim {
struct IntervalResult {
    float value;
    bool changed;
};
// Repair only the first table interval when the original helper returned its
// unchanged first value. Keep the double intermediates and single final float
// conversion: changing their precision changes the guest-visible result bits.
inline IntervalResult first_interval(float input, float original_value, float table_first,
                                     float table_next) {
    if (original_value != 1.f || table_first != 1.f || !(table_next > 0.f && table_next < 1.f) ||
        !std::isfinite(input) || !(input > 0.f))
        return {original_value, false};
    const double table_position = double(input) * 51.0;
    if (!(table_position < 1.0))
        return {original_value, false};
    const float value =
        float(double(table_first) + table_position * (double(table_next) - double(table_first)));
    return {value, value != original_value};
}
using YawBits = std::array<std::uint32_t, 4>; // m00,m02,m20,m22
// This is a finite, nondegenerate determinant guard, not an orthonormality test.
// The absolute determinant admits either handedness within the observed bounds.
inline bool valid_yaw(const YawBits &raw_bits) {
    std::array<float, 4> components{};
    for (unsigned i = 0; i < 4; ++i) {
        components[i] = std::bit_cast<float>(raw_bits[i]);
        if (!std::isfinite(components[i]))
            return false;
    }
    const double determinant = double(components[0]) * double(components[3]) -
                               double(components[1]) * double(components[2]);
    const double magnitude = std::abs(determinant);
    return magnitude > .5 && magnitude < 2.0;
}
inline bool collapsed_yaw(const YawBits &raw_bits) {
    // Both signs of zero count as collapsed. Even the smallest subnormal component
    // is nonzero here; no epsilon or host rounding mode changes this bit predicate.
    for (auto component_bits : raw_bits)
        if (component_bits & 0x7fffffffU)
            return false;
    return true;
}
inline bool should_keep_yaw(float delta_time, const YawBits &before, const YawBits &after) {
    // Preserve a valid prior yaw only for signed-zero dt and a fully collapsed
    // result. This helper does not write the matrix or authenticate its source.
    return (std::bit_cast<std::uint32_t>(delta_time) & 0x7fffffffU) == 0 && valid_yaw(before) &&
           collapsed_yaw(after);
}
// Exact little-endian x87 80-bit payload; no host long-double layout dependency.
inline std::array<std::uint8_t, 10> encode_f32(float value) {
    // Normalize binary32 subnormals explicitly, then serialize the integer
    // significand and biased exponent. No host x87 load or arithmetic is needed.
    const std::uint32_t raw_bits = std::bit_cast<std::uint32_t>(value);
    const unsigned exponent = (raw_bits >> 23) & 255U, fraction = raw_bits & 0x7fffffU;
    if ((raw_bits >> 31) || exponent == 255U || (!exponent && !fraction))
        throw std::invalid_argument("Expected a positive finite nonzero float");
    std::uint64_t significand{};
    unsigned extended_exponent{};
    if (exponent) {
        significand = std::uint64_t(0x800000U | fraction) << 40;
        extended_exponent = exponent + 16383U - 127U;
    } else {
        const unsigned highest_fraction_bit = 31U - unsigned(std::countl_zero(fraction));
        significand = std::uint64_t(fraction) << (63U - highest_fraction_bit);
        extended_exponent = highest_fraction_bit + 16383U - 149U;
    }
    std::array<std::uint8_t, 10> payload{};
    for (unsigned i = 0; i < 8; ++i)
        payload[i] = std::uint8_t(significand >> (8 * i));
    payload[8] = std::uint8_t(extended_exponent);
    payload[9] = std::uint8_t(extended_exponent >> 8);
    return payload;
}
} // namespace mw34::turret_aim
