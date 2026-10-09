#pragma once
#include "protocol.hpp"
namespace mw34::m4_numeric_max {
inline constexpr std::array<std::uint32_t,16> inputs{0x7f7fffff,0,0x80000000,1,0x80000001,0x007fffff,0x00800000,0x3f800000,0xbf800000,0x3eaaaaab,0xff7fffff,0x7f800000,0xff800000,0x7fc12345,0x7f812345,0xff812345};
inline unsigned records(bool directed){return 2*2*(directed?inputs.size():1)*3*3*12*2;}
inline void seed(unsigned cw,unsigned top,unsigned depth,unsigned sticky,std::uint8_t*fx,std::uint8_t*env){
 require(depth<8 && (top==0||top==7) && sticky<=2,"Bounded live-stack domain rejected");
 bool allowed{};for(auto c:control_words)allowed|=cw==c;require(allowed,"Masked CW domain rejected");
 std::memset(fx,0,512);std::memset(env,0,28);
 auto put16=[](std::uint8_t*p,std::uint16_t v){std::memcpy(p,&v,2);};auto put32=[](std::uint8_t*p,std::uint32_t v){std::memcpy(p,&v,4);};
 const std::uint16_t sw=(top<<11)|(sticky==0?0:sticky==1?2:34);put16(fx,cw);put16(fx+2,sw);put32(fx+24,0x1f80);
 unsigned ftw{},tags=0xffff;
 for(unsigned i=0;i<8;++i){const std::uint64_t m=0x8000000000000000ULL+(std::uint64_t{i}<<56);std::memcpy(fx+32+16*i,&m,8);put16(fx+40+16*i,0x4000|(i%2?0x8000:0));
  if(i<depth){auto phys=(top+i)&7;ftw|=1<<phys;tags&=~(3<<(phys*2));}}
 fx[4]=ftw;put32(env,0xffff0000U|cw);put32(env+4,0xffff0000U|sw);put32(env+8,0xffff0000U|tags);
 put32(env+12,0x11223344);put32(env+16,0x011d0023);put32(env+20,0x55667788);put32(env+24,0xffff002b);
}
}
