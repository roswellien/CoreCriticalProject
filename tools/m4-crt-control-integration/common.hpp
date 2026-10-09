#pragma once
#include "probe_common.hpp"
namespace mw34::m4_crt_control_integration {
using mw34::m4_crt_probe::Cpu;
inline constexpr unsigned records=192,original_stride=10444,native_stride=17764;
inline constexpr unsigned wrapper=0x5ac5a0,thunk=0x5ac5d6,slot=0x5bb578,provider_entry=0x780042e1,outer_return=0x5ac436,provider_return=0x5ac5af;
inline constexpr std::array<unsigned,8>stack_offsets{0x100,0x1fc,0x200,0x7f0,0x7fc,0x800,0x808,0xff0};
inline constexpr std::array<unsigned,8>flag_patterns{0x202,0x203,0x212,0x246,0x282,0xa02,0x242,0x802};
inline Cpu cpu(unsigned scenario){
 mw34::m4_crt_probe::need(scenario<8,"Connected authored CPU/stack scenario");
 const unsigned q=0x1020304*scenario;
 return {0x13579bdf^q,0x2468ace0^q,0x81726354^q,0x10293847^q,0x20001000+stack_offsets[scenario],0x92837465^q,0x56473829^q,0xaabbccdd^q,flag_patterns[scenario],wrapper};
}
}
