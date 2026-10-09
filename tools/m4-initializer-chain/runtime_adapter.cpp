#include "runtime_adapter.hpp"
#include "execution.hpp"
#include <memory>
namespace mw34::m4_initializer_chain {
namespace {
void overlay_cpu(State &s,const mw34::m4_runtime::Cpu32 &c) {
    s.gpr.rax.dword=c.eax;s.gpr.rcx.dword=c.ecx;s.gpr.rdx.dword=c.edx;s.gpr.rbx.dword=c.ebx;
    s.gpr.rsp.dword=c.esp;s.gpr.rbp.dword=c.ebp;s.gpr.rsi.dword=c.esi;s.gpr.rdi.dword=c.edi;s.gpr.rip.dword=c.eip;
    s.rflag.flat=c.eflags;s.aflag.cf=(c.eflags>>0)&1;s.aflag.pf=(c.eflags>>2)&1;s.aflag.af=(c.eflags>>4)&1;
    s.aflag.zf=(c.eflags>>6)&1;s.aflag.sf=(c.eflags>>7)&1;s.aflag.df=(c.eflags>>10)&1;s.aflag.of=(c.eflags>>11)&1;
}
void callback(mw34::m4_runtime::Runtime &runtime) {
    require(runtime.domain()==mw34::m4_runtime::Domain::admitted_game&&runtime.image_metadata().image_base==0x400000,"Component requires owned admitted image");
    auto storage=runtime.remill_state();
    const bool seeded=runtime.remill_seeded();
    if(!runtime.remill_seeded()) {
        State seed{};std::memcpy(storage.data(),&seed,sizeof(seed));runtime.mark_remill_seeded();
        auto &s=*std::launder(reinterpret_cast<State *>(storage.data()));s.addr.fs_base.dword=runtime.fs_base().value;
    }
    auto &s=*std::launder(reinterpret_cast<State *>(storage.data()));
    require(s.addr.ds_base.dword==0&&s.addr.ss_base.dword==0&&s.addr.fs_base.dword==runtime.fs_base().value,"Unsupported shared segment-base state");
    overlay_cpu(s,runtime.cpu());
    const auto fx=runtime.fx();Request domain{};domain.state=observed_cpu(s);domain.arg_a=s.gpr.rip.dword==preceding_entry?1:0;
    std::memcpy(domain.fx.data(),fx.data(),512);
    // Shared host stack bounds replace the offline frame bounds; all remaining
    // CPU/FP admission remains the same reviewed domain.
    const auto actual_frame=domain.state.registers[4];domain.state.registers[4]=stack_base+1024;domain.full_tags=0;
    const auto sw=word<std::uint16_t>(domain.fx.data()+2);const unsigned top=(sw>>11)&7,ftw=domain.fx[4];
    for(unsigned i=0;i<8;++i){const auto physical=(top+i)&7;domain.full_tags|=((ftw&(1U<<physical))?occupied_tag(domain.fx.data()+32+i*16):3U)<<(physical*2);}
    validate_request(domain);
    std::array<std::byte,18> legacy_metadata{};
    if(seeded)std::memcpy(legacy_metadata.data(),reinterpret_cast<std::byte *>(&s.x87)+6,legacy_metadata.size());
    std::memcpy(&s.x87,fx.data(),512);
    // Non-FP callbacks preserve persistent legacy ENV metadata. It cannot be
    // inferred from Windows FX pointer/opcode bytes, which may remain zero.
    if(seeded)std::memcpy(reinterpret_cast<std::byte *>(&s.x87)+6,legacy_metadata.data(),legacy_metadata.size());
    s.sw.ie=(sw>>0)&1;s.sw.de=(sw>>1)&1;s.sw.ze=(sw>>2)&1;s.sw.oe=(sw>>3)&1;s.sw.ue=(sw>>4)&1;s.sw.pe=(sw>>5)&1;
    s.sw.sf=(sw>>6)&1;s.sw.c0=(sw>>8)&1;s.sw.c1=(sw>>9)&1;s.sw.c2=(sw>>10)&1;s.sw.c3=(sw>>14)&1;
    for(unsigned i=0;i<8;++i){std::memcpy(&s.st.elems[i].val,domain.fx.data()+32+i*16,10);std::memcpy(&s.vec[i],domain.fx.data()+160+i*16,16);}
    const auto expected_return=runtime.memory().load<std::uint32_t>({actual_frame});
    Context context(runtime.memory(),actual_frame,runtime.stack_low().value,runtime.stack_top().value,expected_return);
    context.select(s.gpr.rip.dword);context.freeze(image_hash);
    {
        FpuScope host;context.enter(s,s.gpr.rip.dword);require(!context.failed&&host.captured_restoration(),"Shared static initializer execution/host restoration failed");
    }
    const auto c=observed_cpu(s);runtime.cpu()={c.registers[0],c.registers[1],c.registers[2],c.registers[3],c.registers[4],c.registers[5],c.registers[6],c.registers[7],c.flags,c.eip};
    Result projection{};capture(s,projection,false);
    std::array<std::byte,18> fx_metadata{};std::memcpy(fx_metadata.data(),fx.data()+6,fx_metadata.size());
    std::memcpy(runtime.fx().data(),projection.fx_after.data(),512);
    std::memcpy(runtime.fx().data()+6,fx_metadata.data(),fx_metadata.size());
}
} // namespace
void register_component(mw34::m4_runtime::Runtime &runtime,std::string_view object_hash,std::string_view gate_hash) {
    using namespace mw34::m4_runtime;
    const auto evidence=[&](std::uint32_t bytes,const char *code){return Evidence{Domain::admitted_game,image_hash,bytes,code,std::string(object_hash),std::string(gate_hash)};};
    runtime.register_translation({{preceding_entry},{Abi::Cdecl,0,true},&callback,"CRT initializer 410910",evidence(36,"f5a91456f4eb0ecab7e5cd689b1d1465dc4e2610bc879397e500b02d00946af7")});
    runtime.register_translation({{entry},{Abi::Cdecl,0,true},&callback,"CRT initializer 410940 connected callees",evidence(203,"483e3a9fd5dccbe4ce508f1cfa05f483ffa055bef943a5d065e1ecd3f8d3c165")});
}
} // namespace mw34::m4_initializer_chain
