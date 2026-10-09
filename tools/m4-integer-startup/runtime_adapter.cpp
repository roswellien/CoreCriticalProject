#include "runtime_adapter.hpp"
#include "execution.hpp"
#include <memory>
namespace mw34::m4_integer_startup {
namespace {
constexpr std::array<const char *,14> code_hashes{"8062a220c79eac07bf80be183e512caef7c40b3a07444c6d86f76a66103103b0","a422e41a1c6f38639a6834539368dd5189fc0ef68939efeb181ce2e7709fb8d4","b998a2850b6615005b64a4d020e236a9069db99c7107b371f20390b3eb77f777","5e77ab61d661f61f8b2dbc39a4365e062920a945d8958b1bf5600ff5ae87eb6b","1d99429b6d724e695f5ffcb506e650e0dc4b595d172290956327832abdc24253","473211a528c28c21522297fc96338db2f54ea4b73f852e877c0c3f514cb5427c","5d629e16962e93d3761fa51b2ede25e3f41acb8e12a5b0bde27f75bba2db88c9","36dfd9e458b885e3a5a7081422c24b084cb5df223173ab1285da6ff8de0520ed","dd28a8dc5f1f41e91a91b97a262230070c515521144f1da4c6a065ed0d58acce","dd28a8dc5f1f41e91a91b97a262230070c515521144f1da4c6a065ed0d58acce","dd28a8dc5f1f41e91a91b97a262230070c515521144f1da4c6a065ed0d58acce","b2b78673f5a163c4891b8f15e49d5568a3de4d97ad7e15d2ddd033a9503b33c3","67384db78c6e53a195600613639cbbe4f09c9f9c20bc15d36bc88723a8966c92","d566c9497ecd4cb9acb9a460a55d517a8e17701a6ee91088159b8c1c38b6f6f2"};
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
    const auto fx=runtime.fx();Request domain{};domain.state=observed_cpu(s);domain.arg_a=14;for(unsigned i=0;i<14;++i)if(s.gpr.rip.dword==entries[i])domain.arg_a=i;
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
    for(unsigned i=0;i<14;++i){const auto &f=fragments[i];
        runtime.register_translation({{f.entry},{Abi::Cdecl,0,true},&callback,"CRT integer initializer "+std::to_string(f.entry),evidence(f.size,code_hashes[i])});
    }
}
} // namespace mw34::m4_integer_startup
