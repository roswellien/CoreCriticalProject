#pragma once
#include "probe_common.hpp"
namespace mw34::m4_crt_matherr_paired {
using mw34::m4_crt_probe::Cpu;
inline constexpr unsigned record_count=1536,original_stride=26836,native_stride=33964;
inline constexpr unsigned entry=0x7800b38f,return_pc=0x5ac42e,capture_pc=0x10000100;
inline constexpr unsigned frame=0x200017fc,argument_address=frame+4;
inline constexpr unsigned zero_global=0x780392b8,callback_global=0x7803b0c4;
inline constexpr std::array<unsigned,3>pages{0x20001000,0x78039000,0x7803b000};
inline constexpr std::array<unsigned,8>arguments{0,0x51e7b0,0xffffffff,0x10000001,0x30000000,0x7800b38f,0x80000000,0x12345678};
inline constexpr std::array<unsigned,8>depths{0,1,7,8,0,1,7,8};
struct OriginalRecord {
 std::array<unsigned,5>tag;Cpu before,after;
 std::array<std::array<std::uint8_t,512>,4>fx;
 std::array<std::array<std::uint8_t,28>,4>env;
 std::array<std::array<std::uint8_t,12288>,2>memory;
};
static_assert(sizeof(OriginalRecord)==original_stride);
inline Cpu input_cpu(unsigned index){return {0x13579bdf^index,0x2468ace0,0x81726354,0x10293847,frame,0x92837465,0x56473829,0xaabbccdd,0x202U|((index&1)?0xcd5U:0),entry};}
inline void seed_pages(std::array<std::uint8_t,12288>&out,unsigned index,unsigned argument){
 for(unsigned k=0;k<pages.size();++k)for(unsigned j=0;j<4096;++j)out[k*4096+j]=static_cast<std::uint8_t>(index+j*7+k*19);
 mw34::m4_crt_probe::put32(out.data()+0x7fc,return_pc);mw34::m4_crt_probe::put32(out.data()+0x800,argument);
}
inline void seed_fp(std::uint8_t*fx,std::uint8_t*env,unsigned cw,unsigned top,unsigned arg_index){
 using namespace mw34::m4_crt_probe;
 need(top<8&&arg_index<8,"Declared coherent FP profile");std::memset(fx,0,512);std::memset(env,0,28);
 const auto sw=static_cast<std::uint16_t>((top<<11)|(arg_index>=4?0x25:0));unsigned ftw{},tag=0xffff;
 for(unsigned i=0;i<depths[arg_index];++i){const unsigned p=(top+i)&7;ftw|=1U<<p;tag&=~(3U<<(2*p));}
 put16(fx,static_cast<std::uint16_t>(cw));put16(fx+2,sw);fx[4]=static_cast<std::uint8_t>(ftw);put32(fx+24,0x1f80);
 for(unsigned i=0;i<8;++i){const std::uint64_t mantissa=0x8000000000000000ULL+0x0101010101010101ULL*i;std::memcpy(fx+32+16*i,&mantissa,8);put16(fx+40+16*i,static_cast<std::uint16_t>(0x3fff+i));}
 for(unsigned i=0;i<128;++i)fx[160+i]=static_cast<std::uint8_t>(i*19+3+arg_index);
 put16(env,static_cast<std::uint16_t>(cw));put16(env+2,0xffff);put16(env+4,sw);put16(env+6,0xffff);put16(env+8,static_cast<std::uint16_t>(tag));put16(env+10,0xffff);
 put32(env+12,0x11223344);put16(env+16,0x23);put16(env+18,0x11d);put32(env+20,0x55667788);put16(env+24,0x2b);put16(env+26,0xffff);
}
}
