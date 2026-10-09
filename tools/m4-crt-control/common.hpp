#pragma once
#include "probe_common.hpp"
namespace mw34::m4_crt_control {
using mw34::m4_crt_probe::Cpu;
inline constexpr unsigned cases=68,records=3264,original_stride=10456;
inline constexpr std::uint32_t entries[]{0x780042e1,0x780042f7};
struct Input{std::uint32_t value,mask;};
inline Input input(unsigned i){
 mw34::m4_crt_probe::need(i<cases,"Directed CW case");
 if(i==0)return {0,0};if(i==1)return {0,0xffffffff};if(i==2)return {0xffffffff,0xffffffff};if(i==3)return {0x35ab96d2,0x8c75ea31};
 const auto bit=std::uint32_t{1}<<((i-4)/2);return {(i&1)?0:bit,bit};
}
inline Cpu cpu(unsigned entry){return {0x13579bdf,0x2468ace0,0x81726354,0x10293847,0x20001800,0x92837465,0x56473829,0xaabbccdd,0x202,entries[entry]};}
}
