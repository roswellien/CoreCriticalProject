#pragma once
#include <array>
#include <cstdint>
namespace mw34::m4_fp_sqrt_corpus {
// Authored binary64 fixtures, never expected results. Multipliers are the
// exact image constants except in the explicitly named multiplier cases.
inline constexpr auto inputs=std::to_array<std::uint64_t>({
 0ULL,0x8000000000000000ULL,1ULL,0x8000000000000001ULL,
 0x000fffffffffffffULL,0x800fffffffffffffULL,0x0010000000000000ULL,0x8010000000000000ULL,
 0x0010000000000001ULL,0x8010000000000001ULL,0x3cb0000000000000ULL,0xbcb0000000000000ULL,
 0x3fd0000000000000ULL,0xbfd0000000000000ULL,0x3fe0000000000000ULL,0xbfe0000000000000ULL,
 0x3fefffffffffffffULL,0x3ff0000000000000ULL,0xbff0000000000000ULL,0x3ff0000000000001ULL,
 0x4000000000000000ULL,0xc000000000000000ULL,0x4008000000000000ULL,0x4010000000000000ULL,
 0x4022000000000000ULL,0x4030000000000000ULL,0x400921fb54442d18ULL,0xc00921fb54442d18ULL,
 0x4130000000000000ULL,0xc130000000000000ULL,0x43dfffffffffffffULL,0xc3dfffffffffffffULL,
 0x47d333332cccccc0ULL,0x47d333332cccccc1ULL,0x47d333332cccccbfULL,
 0x7fefffffffffffffULL,0xffefffffffffffffULL,0x7ff0000000000000ULL,0xfff0000000000000ULL,
 0x7ff8000000000123ULL,0xfff8000000000123ULL,0x7ff0000000000123ULL,0xfff0000000000123ULL,
 0x3fd5555555555555ULL,0x3ff6a09e667f3bcdULL,0x0100000000000000ULL,0x7f00000000000000ULL,
 0x3ff123456789abcdULL});
struct Fixture {std::uint64_t input,left,right;};
inline constexpr auto multipliers=std::to_array<Fixture>({
 {0x4010000000000000ULL,0ULL,0x8000000000000000ULL},
 {0x4010000000000000ULL,0x3ff0000000000000ULL,0xbff0000000000000ULL},
 {0x4010000000000000ULL,1ULL,0x8000000000000001ULL},
 {0x4010000000000000ULL,0x000fffffffffffffULL,0x0010000000000000ULL},
 {0x4010000000000000ULL,0x7fefffffffffffffULL,0xffefffffffffffffULL},
 {0x4010000000000000ULL,0x7ff0000000000000ULL,0xfff0000000000000ULL},
 {0x4010000000000000ULL,0x7ff8000000000123ULL,0xfff8000000000123ULL},
 {0x4010000000000000ULL,0x7ff0000000000123ULL,0xfff0000000000123ULL},
 {0ULL,0x7ff0000000000000ULL,0x3ff0000000000000ULL},
 {0x4000000000000000ULL,0x3ff0000000000001ULL,0xbfefffffffffffffULL},
 {0x7fefffffffffffffULL,0x7fefffffffffffffULL,1ULL},
 {1ULL,0x7fefffffffffffffULL,1ULL}});
inline constexpr std::array<std::uint16_t,12> controls{0x007f,0x047f,0x087f,0x0c7f,0x027f,0x067f,0x0a7f,0x0e7f,0x037f,0x077f,0x0b7f,0x0f7f};
inline constexpr unsigned fixture_count=inputs.size()+multipliers.size();
inline constexpr unsigned directed_records=fixture_count*12*2*2*2;
inline constexpr Fixture fixture(unsigned i){return i<inputs.size()?Fixture{inputs[i],0x3fe0000000000000ULL,0xbfe0000000000000ULL}:multipliers[i-inputs.size()];}
static_assert(inputs.size()==48&&multipliers.size()==12&&directed_records==5760);
}
