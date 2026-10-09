#pragma once
#include "runtime.hpp"
#include <remill/Arch/X86/Runtime/State.h>
#include <cstring>
namespace mw34::m4_crt_fdiv {
// Architectural defined output: clear IE..ES (bits0..7) and B(bit15).
// C0-C3 are undefined. This native representative preserves their input bits;
// no original measured condition-code policy is claimed by this primitive.
inline bool clear_guest_exceptions(State &state,std::span<std::byte,512>fx){
    std::uint16_t separate{};std::memcpy(&separate,fx.data()+2,2);
    const auto raw=state.x87.fxsave.swd.flat;const auto&s=state.sw;
    if(separate!=raw||s.ie!=((raw>>0)&1)||s.de!=((raw>>1)&1)||s.ze!=((raw>>2)&1)||
       s.oe!=((raw>>3)&1)||s.ue!=((raw>>4)&1)||s.pe!=((raw>>5)&1)||s.sf!=((raw>>6)&1)||
       s.c0!=((raw>>8)&1)||s.c1!=((raw>>9)&1)||s.c2!=((raw>>10)&1)||s.c3!=((raw>>14)&1))return false;
    const auto sw=static_cast<std::uint16_t>(state.x87.fxsave.swd.flat&~0x80ffU);
    state.x87.fxsave.swd.flat=sw;
    std::memcpy(fx.data()+2,&sw,2);
    state.sw.ie=state.sw.de=state.sw.ze=state.sw.oe=state.sw.ue=state.sw.pe=state.sw.sf=0;
    return true;
}
}
