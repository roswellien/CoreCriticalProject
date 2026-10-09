// Authored provider-contract fixture and raw capture format. No vendor code.
#pragma once
#include <array>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <vector>
namespace mw34::m4_crt_probe {
inline constexpr unsigned record_count=1728,original_stride=18668,native_stride=17588,memory_bytes=8204;
inline constexpr std::uint32_t stack_page=0x20001000,table_page=0x20002000,stack_entry=0x20001800;
inline constexpr std::uint32_t table_begin=0x20002100,counter=0x20002800,sentinel=0x10000100;
inline constexpr std::array<std::uint32_t,5> callbacks{0x10001000,0x10001040,0x10001080,0x100010c0,0x10001100};
inline constexpr std::array<std::uint32_t,9> entries{0x780014f8,0x780014f8,0x780014f8,0x780014f8,0x780014f8,0x780014f8,0x78004625,0x7800462f,0x78004635};
inline constexpr std::array<std::uint16_t,12> controls{0x007f,0x047f,0x087f,0x0c7f,0x027f,0x067f,0x0a7f,0x0e7f,0x037f,0x077f,0x0b7f,0x0f7f};
struct Cpu {std::uint32_t eax,ecx,edx,ebx,esp,ebp,esi,edi,flags,pc;};
static_assert(sizeof(Cpu)==40);
inline void need(bool ok,const char *why){if(!ok)throw std::runtime_error(why);}
inline void put32(std::uint8_t *p,std::uint32_t v){std::memcpy(p,&v,4);}
inline void put16(std::uint8_t *p,std::uint16_t v){std::memcpy(p,&v,2);}
inline std::vector<std::uint8_t> callback_bytes(unsigned index){
 need(index<5,"Authored callback index");std::vector<std::uint8_t> b;
 auto emit=[&](std::initializer_list<std::uint8_t> x){b.insert(b.end(),x);};
 auto dword=[&](std::uint32_t value){for(unsigned j=0;j<4;++j)b.push_back(static_cast<std::uint8_t>(value>>(8*j)));};
 if(index==3){emit({0xc7,0x05});dword(table_begin+4);dword(callbacks[2]);}
 if(index==4){emit({0xc7,0x44,0x24,0x10});dword(table_begin+4);}
 const auto digit=index<3?index+1:1;
 emit({0xa1});dword(counter);emit({0x6b,0xc0,0x0a,0x83,0xc0,static_cast<std::uint8_t>(digit),0xa3});dword(counter);
 emit({0xb8});dword(0xaabbcc00+digit);emit({0xb9});dword(0x12345600+digit);emit({0xba});dword(0xfedcba00+digit);emit({0xc3});
 need(b.size()<=64,"Authored callback extent");return b;
}
inline void seed_memory(std::uint8_t *stack,std::uint8_t *table,std::uint8_t *globals,unsigned c){
 need(c<9,"Authored case");std::memset(stack,0xa5,4096);std::memset(table,0xa5,4096);std::memset(globals,0,12);
 put32(stack+0x800,sentinel);put32(table+0x800,0);std::uint32_t begin=table_begin,end=table_begin;
 if(c==0){for(unsigned i=0;i<4;++i)put32(table+0x100+4*i,i==1?callbacks[0]:i==2?callbacks[1]:0);end+=16;}
 else if(c==1||c==4||c==5){put32(table+0x100,callbacks[c==4?3:c==5?4:0]);put32(table+0x104,callbacks[1]);end+=8;}
 else if(c==3){begin=table_begin+8;end=table_begin;}
 put32(stack+0x804,c==6?2:begin);put32(stack+0x808,end);
}
inline void seed_fp(std::uint8_t *fx,std::uint8_t *env,std::uint16_t cw,unsigned top){
 need(top<8,"Authored TOP");std::memset(fx,0,512);put16(fx,cw);put16(fx+2,static_cast<std::uint16_t>(top<<11));put32(fx+24,0x1f80);
 // Empty physical tags and nonzero raw 80-bit storage: MOV-only services must
 // preserve both. Metadata is separately seeded through legacy FLDENV.
 for(unsigned i=0;i<8;++i)for(unsigned j=0;j<10;++j)fx[32+16*i+j]=static_cast<std::uint8_t>(17+i*13+j*7);
 for(unsigned i=0;i<128;++i)fx[160+i]=static_cast<std::uint8_t>(i*19+3);
 std::memset(env,0,28);put16(env,cw);put16(env+2,0xffff);put16(env+4,static_cast<std::uint16_t>(top<<11));put16(env+6,0xffff);put16(env+8,0xffff);put16(env+10,0xffff);
 put32(env+12,0x11223344);put16(env+16,0x23);put16(env+18,0x11d);put32(env+20,0x55667788);put16(env+24,0x2b);put16(env+26,0xffff);
}
inline Cpu seed_cpu(unsigned c){return {0x13579bdf,0x2468ace0,0x81726354,0x10293847,stack_entry,0x92837465,0x56473829,0xaabbccdd,0x202,entries.at(c)};}
} // namespace mw34::m4_crt_probe
