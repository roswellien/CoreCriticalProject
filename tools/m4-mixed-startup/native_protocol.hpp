#pragma once
#include "runtime.hpp"
#include <remill/Arch/X86/Runtime/State.h>
#include <array>
#include <algorithm>
#include <cstring>

namespace mw34::m4_mixed {
constexpr std::uint32_t frame=0x20001800, broker=0x410a80;
constexpr std::array<std::uint32_t,11> pages{0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000};
constexpr std::array<std::uint32_t,26> entries{0x410910,0x410940,0x4133c0,0x43aec0,0x43aee0,0x43af00,0x43af20,0x43af40,0x43af60,0x43af80,0x43afa0,0x467490,0x4674b0,0x4674d0,0x4adb50,0x4b5af0,0x4b5b20,0x4b7020,0x4c78f0,0x4c7940,0x4c79d0,0x4ce5a0,0x4ce5c0,0x4ce5e0,0x4ce600,0x4cfef0};
constexpr std::array<std::uint32_t,12> controls{0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f};
#pragma pack(push,1)
struct Cpu {std::array<std::uint32_t,8> gpr;std::uint32_t flags,pc;};
struct Common {
  std::uint32_t sequence,repeat,phase,table_slot,entry,cw,initial_top,status,host_restored;
  Cpu before,after;
  std::array<std::uint8_t,512> fx_before,fx_after,host_before,host_after;
  std::array<std::uint8_t,28> env_before,env_after,host_env_before,host_env_after;
  std::array<std::uint8_t,11*4096> memory_before,memory_after;
};
struct Event {std::uint32_t address;std::uint64_t value;std::uint32_t width,operation;};
struct Route {std::uint32_t entry,ret,pop,complete;Cpu before,after;};
struct Native {
  Common common;
  std::array<std::uint8_t,3504> state_before,state_after;
  std::uint32_t event_count,reads,writes,clears,tests,returns,primitives,route_count,state_seeded,domain_error;
  std::array<Event,192> events;
  std::array<Route,2> routes;
};
#pragma pack(pop)
static_assert(sizeof(Common)==92388&&sizeof(Native)==103468&&sizeof(State)==3504);
extern thread_local Native *observation;
inline void require(bool condition,const char *why){if(!condition)throw std::runtime_error(why);}
inline Cpu cpu(const State &s){return {{s.gpr.rax.dword,s.gpr.rcx.dword,s.gpr.rdx.dword,s.gpr.rbx.dword,s.gpr.rsp.dword,s.gpr.rbp.dword,s.gpr.rsi.dword,s.gpr.rdi.dword},
  0x202U|(s.aflag.cf<<0)|(s.aflag.pf<<2)|(s.aflag.af<<4)|(s.aflag.zf<<6)|(s.aflag.sf<<7)|(s.aflag.df<<10)|(s.aflag.of<<11),s.gpr.rip.dword};}
inline void overlay_cpu(State &s,const m4_runtime::Cpu32 &c){
  s.gpr.rax.dword=c.eax;s.gpr.rcx.dword=c.ecx;s.gpr.rdx.dword=c.edx;s.gpr.rbx.dword=c.ebx;
  s.gpr.rsp.dword=c.esp;s.gpr.rbp.dword=c.ebp;s.gpr.rsi.dword=c.esi;s.gpr.rdi.dword=c.edi;s.gpr.rip.dword=c.eip;
  s.rflag.flat=c.eflags;s.aflag.cf=(c.eflags>>0)&1;s.aflag.pf=(c.eflags>>2)&1;s.aflag.af=(c.eflags>>4)&1;
  s.aflag.zf=(c.eflags>>6)&1;s.aflag.sf=(c.eflags>>7)&1;s.aflag.df=(c.eflags>>10)&1;s.aflag.of=(c.eflags>>11)&1;
}
inline std::uint16_t status(const State &s){return (s.x87.fxsave.swd.flat&0xb880)|(s.sw.ie<<0)|(s.sw.de<<1)|(s.sw.ze<<2)|(s.sw.oe<<3)|(s.sw.ue<<4)|(s.sw.pe<<5)|(s.sw.sf<<6)|(s.sw.c0<<8)|(s.sw.c1<<9)|(s.sw.c2<<10)|(s.sw.c3<<14);}
inline void projection(const State &s,std::array<std::uint8_t,512> &fx,std::array<std::uint8_t,28> &env){
  require(s.x87.fxsave.ftw.flat==0,"Mixed FP requires an empty guest stack");
  std::memcpy(fx.data(),&s.x87,512);const auto sw=status(s);std::memcpy(fx.data()+2,&sw,2);
  for(unsigned i=0;i<8;++i){std::memcpy(fx.data()+32+i*16,&s.st.elems[i].val,10);std::memcpy(fx.data()+160+i*16,&s.vec[i],16);}
  const auto put=[&](unsigned offset,std::uint32_t value){std::memcpy(env.data()+offset,&value,4);};
  put(0,0xffff0000U|s.x87.fxsave.cwd.flat);put(4,0xffff0000U|sw);put(8,0xffffffffU);
  put(12,s.x87.fxsave.ip);put(16,s.x87.fxsave.cs.flat|(std::uint32_t{s.x87.fxsave.fop}<<16));put(20,s.x87.fxsave.dp);put(24,0xffff0000U|s.x87.fxsave.ds.flat);
}
inline void snapshot(m4_runtime::Runtime &runtime,const State &s,bool before){
  require(observation,"Missing active mixed observation");auto &r=*observation;auto &c=r.common;
  (before?c.before:c.after)=cpu(s);projection(s,before?c.fx_before:c.fx_after,before?c.env_before:c.env_after);
  std::memcpy((before?r.state_before:r.state_after).data(),&s,3504);
  auto &memory=before?c.memory_before:c.memory_after;
  for(unsigned i=0;i<pages.size();++i)runtime.memory().read({pages[i]},std::as_writable_bytes(std::span{memory.data()+i*4096,4096}));
}
inline void host(const std::uint8_t *before,const std::uint8_t *after,const std::uint8_t *env_before,const std::uint8_t *env_after){
  require(observation,"Missing mixed host observer");auto &r=observation->common;
  std::memcpy(r.host_before.data(),before,512);std::memcpy(r.host_after.data(),after,512);
  std::memcpy(r.host_env_before.data(),env_before,28);std::memcpy(r.host_env_after.data(),env_after,28);
  bool equal=!std::memcmp(before,after,5)&&!std::memcmp(before+24,after+24,4)&&!std::memcmp(env_before,env_after,28);
  for(unsigned i=0;i<8;++i)equal=equal&&!std::memcmp(before+32+i*16,after+32+i*16,10);
  equal=equal&&!std::memcmp(before+160,after+160,256);r.host_restored=equal;
}
template<class E> inline void events(const E &source,unsigned count){
  require(observation&&count<=observation->events.size(),"Mixed event extent rejected");observation->event_count=count;
  for(unsigned i=0;i<count;++i){const auto &e=source[i];observation->events[i]={e.address,e.value,e.width,e.operation};}
}
inline void sync_fx(m4_runtime::Runtime &runtime,const State &s){
  std::array<std::uint8_t,512> fx{};std::array<std::uint8_t,28> env{};projection(s,fx,env);
  std::array<std::byte,18> metadata{};std::memcpy(metadata.data(),runtime.fx().data()+6,18);
  std::memcpy(runtime.fx().data(),fx.data(),512);std::memcpy(runtime.fx().data()+6,metadata.data(),18);
}
void first(m4_runtime::Runtime &);void simple(m4_runtime::Runtime &);void sqrt(m4_runtime::Runtime &);
void cosine(m4_runtime::Runtime &);void sincos(m4_runtime::Runtime &);void atan(m4_runtime::Runtime &);
void verify_current_fp_code(m4_runtime::Runtime &);
inline void validate_fp(m4_runtime::Runtime &runtime,const State &s){
  require(s.x87.fxsave.ftw.flat==0&&std::find(controls.begin(),controls.end(),s.x87.fxsave.cwd.flat)!=controls.end(),"Unsupported mixed FP CW/stack domain");
  require(s.x87.fxsave.mxcsr.flat==0x1f80&&!(status(s)&~0x7f7fU),"Unsupported mixed MXCSR/status domain");
  std::array<std::uint8_t,512> fx{};std::array<std::uint8_t,28> env{};projection(s,fx,env);
  // Legacy pointer/opcode metadata lives in State; the independently carried
  // FX projection retains the observed hardware metadata representation.
  for(unsigned i=0;i<512;++i)if(i<6||i>=24)require(fx[i]==std::to_integer<std::uint8_t>(runtime.fx()[i]),"Persistent State and FX projection disagree");
  verify_current_fp_code(runtime);
}
}
