#pragma once
#include "native_context.hpp"
namespace mw34::m4_crt_control_integration {
template<class T>T get(const std::uint8_t*p){T v{};std::memcpy(&v,p,sizeof(v));return v;}
inline Cpu captured_cpu(const State&s){auto c=cpu_view(s);return {c.eax,c.ecx,c.edx,c.ebx,c.esp,c.ebp,c.esi,c.edi,c.eflags,c.eip};}
inline void initialize(State&s,const Cpu&c,const std::uint8_t*fx,const std::uint8_t*env,unsigned seed){
 auto*b=reinterpret_cast<std::uint8_t*>(&s);for(unsigned i=0;i<3504;++i)b[i]=static_cast<std::uint8_t>(i*13+seed+7);s.addr.ds_base.dword=s.addr.ss_base.dword=0;s.addr.fs_base.dword=0x7ffde000;
 project_cpu(s,{c.eax,c.ecx,c.edx,c.ebx,c.esp,c.ebp,c.esi,c.edi,c.flags,c.pc});std::memset(&s.sw,0,sizeof(s.sw));std::memcpy(&s.x87,fx,512);auto&f=s.x87.fxsave;f.ip=get<unsigned>(env+12);f.cs.flat=get<std::uint16_t>(env+16);f.fop=get<std::uint16_t>(env+18);f.dp=get<unsigned>(env+20);f.ds.flat=get<std::uint16_t>(env+24);
 for(unsigned i=0;i<8;++i){std::memcpy(&s.st.elems[i].val,fx+32+16*i,10);std::memcpy(&s.vec[i],fx+160+16*i,16);}
}
inline std::array<std::uint8_t,28>legacy(const State&s,const std::uint8_t*reserved){std::array<std::uint8_t,28>r{};std::memcpy(r.data(),reserved,28);const auto&f=s.x87.fxsave;mw34::m4_crt_probe::put16(r.data(),f.cwd.flat);mw34::m4_crt_probe::put16(r.data()+4,f.swd.flat);mw34::m4_crt_probe::need(f.ftw.flat==0,"Connected native empty physical tags required");mw34::m4_crt_probe::put16(r.data()+8,0xffff);mw34::m4_crt_probe::put32(r.data()+12,f.ip);mw34::m4_crt_probe::put16(r.data()+16,f.cs.flat);mw34::m4_crt_probe::put16(r.data()+18,f.fop);mw34::m4_crt_probe::put32(r.data()+20,f.dp);mw34::m4_crt_probe::put16(r.data()+24,f.ds.flat);return r;}
struct HostScope{
 struct alignas(16) Image{std::uint8_t bytes[512];};Image before{},after{};std::uint8_t env[28]{},env_after[28]{};
 HostScope(){__asm__ volatile("fxsave64 %0\n\tfnstenv %1":"=m"(before),"=m"(env)::"memory");}
 void restore(){__asm__ volatile("fxrstor64 %0\n\tfldenv %1"::"m"(before),"m"(env):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)","xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");}
 void capture(){restore();__asm__ volatile("fxsave64 %0\n\tfnstenv %1":"=m"(after),"=m"(env_after)::"memory");}
 ~HostScope(){restore();}
};
struct SerialOwner{explicit SerialOwner(Context&c){if(owner)throw std::runtime_error("Connected Context already active");owner=&c;}~SerialOwner(){owner=nullptr;}};
}
