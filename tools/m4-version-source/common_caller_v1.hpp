#pragma once
#include <array>
#include <cstdint>
// One external caller recipe, independently authored; no provider/candidate output.
namespace mw34::m4_version_common {
inline constexpr std::array<std::uint32_t,10> cpu{
 0x13579bdf,0x2468ace0,0x81726354,0x10293847,0x20001800,
 0x92837465,0x56473829,0xaabbccdd,0x202,0x4af240};
inline constexpr std::uint32_t original_return=0x410a80,native_return=0xfffffff0;
inline constexpr std::uint32_t stack_low=0x20001000,stack_bytes=4096;
inline std::array<unsigned char,512> fx(){std::array<unsigned char,512> a{};a[0]=0x7f;a[24]=0x80;a[25]=0x1f;return a;}
inline constexpr std::array<unsigned char,28> env{
 0x7f,0,0xff,0xff,0,0,0xff,0xff,0xff,0xff,0xff,0xff,
 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0xff,0xff};
inline constexpr std::array<unsigned char,4096> stack{};
// Root ESP/PC, GPR/flags, FX/ENV and stack are assigned once after bootstrap.
// Runtime::invoke contributes its native return token; original capture uses its
// distinct independently authored token. Providers, heap/registry and own TIB
// remain owned by each actual branch and are never seeded from captured outputs.
}
