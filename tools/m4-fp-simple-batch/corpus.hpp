#pragma once
#include <array>
#include <cstdint>
namespace mw34::m4_fp_simple_corpus {
// Authored IEEE-754 input words. These deliberately change one reviewed
// constant at its original address; they are not retail asset/code bytes.
inline constexpr auto inputs=std::to_array<std::uint32_t>({
    0x00000000,0x80000000,0x00000001,0x80000001,0x007fffff,0x00800000,
    0x00800001,0x3f000000,0xbf000000,0x3f800000,0xbf800000,0x3f800001,
    0xbf800001,0x3fffffff,0x40000000,0x41a00000,0xc1a00000,0x3eaaaaab,
    0x3f3504f3,0x1a000000,0x1a000001,0x1fffffff,0x20000000,0x20000001,
    0x5effffff,0x5f000000,0x5f000001,0x5f7fffff,0x5f800000,0x7f7fffff,
    0xff7fffff,0x7f800000,0xff800000,0x7fc00000,0xffc00000,0x7fc00001,
    0xffc12345,0x7f800001,0xff800001,0x7fa12345,0xffa12345,0x3f123456
});
inline constexpr std::array<std::uint16_t,12> controls{0x007f,0x047f,0x087f,0x0c7f,0x027f,0x067f,0x0a7f,0x0e7f,0x037f,0x077f,0x0b7f,0x0f7f};
inline constexpr auto integers=std::to_array<std::uint32_t>({
 0,1,0xffffffff,2,0xfffffffe,127,128,0xffffff80,32767,32768,0xffff8000,
 0x007fffff,0x00800000,0x00ffffff,0x01000000,0x01000001,0xfeffffff,
 0x7fffffff,0x80000000,0x80000001});
inline constexpr std::uint32_t directed_records=(inputs.size()+integers.size())*12*2*2*2;
static_assert(inputs.size()==42&&integers.size()==20&&directed_records==5952);
}
