#pragma once
#include "context.hpp"
#include <algorithm>
namespace mw34::m4_integer_startup {
struct FpuScope {
    struct alignas(16) Image {std::uint8_t bytes[512];} saved;
    std::uint8_t legacy_env[28];
    FpuScope() {
        __asm__ volatile("fxsave64 %0\n\tfnstenv %1\n\tfninit" : "=m"(saved),"=m"(legacy_env) : : "memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)");
        const std::uint32_t mxcsr=0x1f80;
        __asm__ volatile("ldmxcsr %0" : : "m"(mxcsr) : "memory");
    }
    static void restore(const Image &image) {
        __asm__ volatile("fxrstor64 %0" : : "m"(image) : "memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)",
          "xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");
    }
    void restore_all() {
        __asm__ volatile("fxrstor64 %0\n\tfldenv %1" : : "m"(saved),"m"(legacy_env) : "memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)",
          "xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");
    }
    bool captured_restoration() {
        Image after;std::uint8_t env_after[28];
        __asm__ volatile("fxrstor64 %2\n\tfldenv %3\n\tfxsave64 %0\n\tfnstenv %1" : "=m"(after),"=m"(env_after) : "m"(saved),"m"(legacy_env) : "memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)",
          "xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");
        // Reserved FX bytes and capability mask are not architectural restoration observations.
        if(std::memcmp(saved.bytes,after.bytes,5)||std::memcmp(saved.bytes+24,after.bytes+24,4)||std::memcmp(legacy_env,env_after,28))return false;
        for(unsigned i=0;i<8;++i)if(std::memcmp(saved.bytes+32+i*16,after.bytes+32+i*16,10))return false;
        return std::memcmp(saved.bytes+160,after.bytes+160,256)==0;
    }
    ~FpuScope(){restore_all();}
};
static Cpu cpu(const State &s) {
    Cpu c{{s.gpr.rax.dword,s.gpr.rcx.dword,s.gpr.rdx.dword,s.gpr.rbx.dword,s.gpr.rsp.dword,s.gpr.rbp.dword,s.gpr.rsi.dword,s.gpr.rdi.dword},
      0x202U|(s.aflag.cf<<0)|(s.aflag.pf<<2)|(s.aflag.af<<4)|(s.aflag.zf<<6)|(s.aflag.sf<<7)|(s.aflag.df<<10)|(s.aflag.of<<11),s.gpr.rip.dword};return c;
}
static std::uint16_t status(const State &s){return (s.x87.fxsave.swd.flat&0xb880)|(s.sw.ie<<0)|(s.sw.de<<1)|(s.sw.ze<<2)|(s.sw.oe<<3)|(s.sw.ue<<4)|(s.sw.pe<<5)|(s.sw.sf<<6)|(s.sw.c0<<8)|(s.sw.c1<<9)|(s.sw.c2<<10)|(s.sw.c3<<14);}
static void initialize(State &s,const Request &q) {
    auto *raw=reinterpret_cast<std::uint8_t *>(&s);for(unsigned i=0;i<sizeof(s);++i)raw[i]=static_cast<std::uint8_t>(i*29+q.seed+(i>>8)*7);
    // Segment bases are an explicit flat guest-context dependency.
    std::memset(&s.addr,0,sizeof(s.addr));
    s.gpr.rax.dword=q.state.registers[0];s.gpr.rcx.dword=q.state.registers[1];s.gpr.rdx.dword=q.state.registers[2];s.gpr.rbx.dword=q.state.registers[3];
    s.gpr.rsp.dword=q.state.registers[4];s.gpr.rbp.dword=q.state.registers[5];s.gpr.rsi.dword=q.state.registers[6];s.gpr.rdi.dword=q.state.registers[7];s.gpr.rip.dword=q.state.eip;
    s.rflag.flat=q.state.flags;s.aflag.cf=(q.state.flags>>0)&1;s.aflag.pf=(q.state.flags>>2)&1;s.aflag.af=(q.state.flags>>4)&1;
    s.aflag.zf=(q.state.flags>>6)&1;s.aflag.sf=(q.state.flags>>7)&1;s.aflag.df=(q.state.flags>>10)&1;s.aflag.of=(q.state.flags>>11)&1;
    std::memcpy(&s.x87,q.fx.data(),512);const auto sw=word<std::uint16_t>(q.fx.data()+2);
    s.sw.ie=(sw>>0)&1;s.sw.de=(sw>>1)&1;s.sw.ze=(sw>>2)&1;s.sw.oe=(sw>>3)&1;s.sw.ue=(sw>>4)&1;s.sw.pe=(sw>>5)&1;
    s.sw.sf=(sw>>6)&1;s.sw.c0=(sw>>8)&1;s.sw.c1=(sw>>9)&1;s.sw.c2=(sw>>10)&1;s.sw.c3=(sw>>14)&1;
    for(unsigned i=0;i<8;++i){std::memcpy(&s.st.elems[i].val,q.fx.data()+32+i*16,10);std::memcpy(&s.vec[i],q.fx.data()+160+i*16,16);}
}
static void capture(const State &s,Result &r,bool before) {
    auto &fx=before?r.fx_before:r.fx_after;auto &env=before?r.env_before:r.env_after;auto &raw=before?r.state_before:r.state_after;
    (before?r.cpu_before:r.cpu_after)=cpu(s);std::memcpy(raw.data(),&s,sizeof(s));std::memcpy(fx.data(),&s.x87,512);
    const auto sw=status(s),cw=s.x87.fxsave.cwd.flat;std::memcpy(fx.data()+2,&sw,2);
    unsigned tags{},top=(sw>>11)&7,ftw=s.x87.fxsave.ftw.flat;
    for(unsigned i=0;i<8;++i){
        std::memcpy(fx.data()+32+i*16,&s.st.elems[i].val,10);std::memcpy(fx.data()+160+i*16,&s.vec[i],16);
        const auto physical=(top+i)&7;tags|=((ftw&(1U<<physical))?occupied_tag(fx.data()+32+i*16):3U)<<(physical*2);
    }
    const auto put=[&](unsigned offset,std::uint32_t v){std::memcpy(env.data()+offset,&v,4);};
    put(0,0xffff0000U|cw);put(4,0xffff0000U|sw);put(8,0xffff0000U|tags);
    put(12,s.x87.fxsave.ip);put(16,s.x87.fxsave.cs.flat|(std::uint32_t{s.x87.fxsave.fop}<<16));put(20,s.x87.fxsave.dp);put(24,0xffff0000U|s.x87.fxsave.ds.flat);
}
static void execute_state(State &s,Context &ctx,Result &r) {
    r.observation_mode=1;ctx.capture(r.memory_before);capture(s,r,true);
    // Context allocation and every potentially throwing observer run before final restore.
    // The translated body only reports bridge faults; no C++ exception crosses LLVM frames.
    {
        FpuScope host;
        ctx.enter(s,s.gpr.rip.dword);
        r.status=ctx.failed?1U:0U;
        capture(s,r,false);ctx.capture(r.memory_after);r.trace_count=ctx.trace_count;r.events=ctx.events;r.route_count=ctx.route_count;r.routes=ctx.routes;
        r.host_restored=host.captured_restoration();
    } // Last operation is FXSAVE64 host restoration; no escaping EH is credited.
}
static void execute(const Request &q,Context &ctx,Result &r) {State s;initialize(s,q);execute_state(s,ctx,r);}

} // namespace mw34::m4_integer_startup
