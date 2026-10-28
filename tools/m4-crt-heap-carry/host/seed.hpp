// Replay inputs are direct ORIGINAL BEFORE projections. This worker invokes
// the unchanged accepted Registry and its own actual Windows services.
#include "registry.hpp"
#include <iostream>
using namespace mw34;namespace fd=mw34::m4_crt_fdiv;
namespace {
void check(bool ok,const char*m){if(!ok)throw std::runtime_error(m);}
constexpr std::array<unsigned,9>bases{0x78004000,0x78011000,0x7802c000,0x7802e000,0x7802f000,0x78030000,0x78037000,0x20001000,0x5bb000};
#pragma pack(push,1)
struct Input {unsigned id,repeat,cw,original_w,original_stack_lo,original_stack_hi;m4_runtime::Cpu32 cpu;std::array<std::byte,512>fx;std::array<std::byte,28>env;std::array<std::byte,4096>stack,observed;};
struct Api{std::uint64_t address,named,owner,owner_named;fd::HostRegion region;char sha[64];wchar_t path[1024];};
struct Module{std::uint64_t handle;fd::HostRegion region;char sha[64];wchar_t path[1024];};
struct Lookup{unsigned kind,token,argument,result,last_error;std::uint64_t host_result;Api before,after;Module module;};
struct Record{unsigned id,repeat,cw,status,event_count,route_count,lookup_count;std::array<std::byte,3504>state_before,state_after;std::array<std::byte,512>fx_before,fx_after,host_before,host_after;std::array<std::byte,28>env_before,env_after;std::array<std::byte,9*4096>pages_before,pages_after;std::array<fd::Event,256>events;std::array<unsigned,21>routes;std::array<Lookup,3>lookups;};
struct Header{char magic[8];unsigned version,count,stride,pages;};
#pragma pack(pop)
static_assert(sizeof(Input)==8796&&sizeof(Record)==107740&&sizeof(State)==3504);
unsigned word(std::span<const std::byte>b,unsigned p){check(std::uint64_t(p)+4<=b.size(),"Bounded input word");unsigned v{};std::memcpy(&v,b.data()+p,4);return v;}
unsigned short half(const std::byte*p){unsigned short v{};std::memcpy(&v,p,2);return v;}
void seed(m4_runtime::Runtime&r,const Input&in){
    State s;auto*p=reinterpret_cast<unsigned char*>(&s);for(unsigned i=0;i<3504;++i)p[i]=static_cast<unsigned char>(i*31+in.id*17+3);
    std::memset(&s.addr,0,sizeof(s.addr));s.addr.fs_base.dword=r.fs_base().value;
    s.gpr.rax.dword=in.cpu.eax;s.gpr.rcx.dword=in.cpu.ecx;s.gpr.rdx.dword=in.cpu.edx;s.gpr.rbx.dword=in.cpu.ebx;s.gpr.rsp.dword=in.cpu.esp;s.gpr.rbp.dword=in.cpu.ebp;s.gpr.rsi.dword=in.cpu.esi;s.gpr.rdi.dword=in.cpu.edi;s.gpr.rip.dword=in.cpu.eip;s.rflag.flat=in.cpu.eflags;
    s.aflag.cf=(in.cpu.eflags>>0)&1;s.aflag.pf=(in.cpu.eflags>>2)&1;s.aflag.af=(in.cpu.eflags>>4)&1;s.aflag.zf=(in.cpu.eflags>>6)&1;s.aflag.sf=(in.cpu.eflags>>7)&1;s.aflag.df=(in.cpu.eflags>>10)&1;s.aflag.of=(in.cpu.eflags>>11)&1;
    std::memcpy(&s.x87,in.fx.data(),512);
    check(half(in.fx.data())==in.cw&&!half(in.fx.data()+2)&&in.fx[4]==std::byte{}&&half(in.env.data())==in.cw&&!half(in.env.data()+4)&&half(in.env.data()+8)==0xffff,"Coherent actual empty BEFORE FP domain");
    // Separate legacy metadata is observed by FNSTENV, not invented from the
    // zero FXSAVE metadata returned on this Windows hardware.
    std::memcpy(&s.x87.fxsave.ip,in.env.data()+12,4);s.x87.fxsave.cs.flat=half(in.env.data()+16);s.x87.fxsave.fop=half(in.env.data()+18);std::memcpy(&s.x87.fxsave.dp,in.env.data()+20,4);s.x87.fxsave.ds.flat=half(in.env.data()+24);
    s.sw.ie=s.sw.de=s.sw.ze=s.sw.oe=s.sw.ue=s.sw.pe=s.sw.sf=s.sw.c0=s.sw.c1=s.sw.c2=s.sw.c3=0;
    for(unsigned i=0;i<8;++i){std::memcpy(&s.vec[i].xmm,in.fx.data()+160+16*i,16);std::memcpy(&s.mmx.elems[i].val,in.fx.data()+32+16*i,8);}
    // Empty logical ST doubles and unobserved segment/cache/vector upper fields
    // retain the declared authored pattern; no nonempty FP value is fabricated.
    std::memcpy(r.remill_state().data(),&s,3504);std::memcpy(r.fx().data(),in.fx.data(),512);r.cpu()=in.cpu;r.mark_remill_seeded();r.memory().write({fd::stack_begin},in.stack);
    check(r.memory().load<unsigned>({fd::entry_esp})==fd::outer_return,"Explicit normalized original outer frame");
}
Api api(const fd::HostIdentity&h){Api a{};check(h.sha.size()==64&&h.path.size()<1024,"Actual replay API serialization");a.address=h.address;a.named=h.named;a.owner=h.owner;a.owner_named=h.owner_named;a.region=h.region;std::memcpy(a.sha,h.sha.data(),64);std::copy(h.path.begin(),h.path.end(),a.path);return a;}
Module module(const fd::ModuleIdentity&h){Module m{};check(h.handle&&h.sha.size()==64&&h.path.size()<1024,"Actual replay module serialization");m.handle=h.handle;m.region=h.region;std::memcpy(m.sha,h.sha.data(),64);std::copy(h.path.begin(),h.path.end(),m.path);return m;}
class Output {HANDLE f_{INVALID_HANDLE_VALUE};public:explicit Output(const char*p){f_=CreateFileA(p,GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);check(f_!=INVALID_HANDLE_VALUE,"Fresh replay output required");Header h{};std::memcpy(h.magic,"MW4FDRN1",8);h.version=1;h.count=24;h.stride=sizeof(Record);h.pages=9;write(&h,sizeof(h));}~Output(){if(f_!=INVALID_HANDLE_VALUE)CloseHandle(f_);}void write(const void*p,unsigned n){DWORD v{};check(WriteFile(f_,p,n,&v,nullptr)&&v==n,"Observed native replay write");}void finish(){write("COMPLETE",8);check(FlushFileBuffers(f_)!=0,"Replay flush");}};
void pages(m4_runtime::Runtime&r,std::span<std::byte,9*4096>b){for(unsigned i=0;i<9;++i)r.memory().read({bases[i]},b.subspan(i*4096,4096));}
}
