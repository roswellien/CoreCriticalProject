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
int main(int argc,char**argv){try{
    check(argc==6,"Native replay: actual-game actual-provider exact-pack before-inputs fresh-output");auto game=fd::readfile(argv[1],2384384),provider=fd::readfile(argv[2],266293),pack=fd::readfile(argv[3],28740),inputs=fd::readfile(argv[4],211128);
    check(inputs.size()==211128&&m4::sha256(inputs)==MW34_REPLAY_INPUT_SHA&&std::memcmp(inputs.data(),"MW4FRIN1",8)==0&&word(inputs,8)==1&&word(inputs,12)==24&&word(inputs,16)==sizeof(Input)&&word(inputs,20)==4096,"Exact before-only input identity/schema required");Output output(argv[5]);
    for(unsigned id=0;id<24;++id){Input in{};std::memcpy(&in,inputs.data()+24+id*sizeof(Input),sizeof(Input));check(in.id==id&&in.cpu.eip==fd::writer&&in.cpu.esp==fd::entry_esp,"Actual input association/frame");auto runtime=m4_runtime::Runtime::from_admitted_image(game);seed(runtime,in);fd::Registry registry(runtime);check(registry.admit(provider,pack),"Frozen Registry admission");Record record{};record.id=id;record.repeat=in.repeat;record.cw=in.cw;std::memcpy(record.state_before.data(),runtime.remill_state().data(),3504);std::memcpy(record.fx_before.data(),runtime.fx().data(),512);pages(runtime,record.pages_before);
        SetLastError(0xaabb0000U+id);const bool complete=registry.initialize();record.status=complete;record.event_count=static_cast<unsigned>(registry.events().size());record.route_count=static_cast<unsigned>(registry.routes().size());record.lookup_count=static_cast<unsigned>(registry.lookups().size());check(record.event_count<=256&&record.route_count<=3&&record.lookup_count<=3,"Bounded actual replay records");std::copy(registry.events().begin(),registry.events().end(),record.events.begin());
        for(unsigned i=0;i<record.route_count;++i){const auto&r=registry.routes()[i];record.routes[i*7+0]=r.site;record.routes[i*7+1]=r.target;record.routes[i*7+2]=r.return_pc;record.routes[i*7+3]=r.entry_esp;record.routes[i*7+4]=r.exit_esp;record.routes[i*7+5]=r.argument_bytes;record.routes[i*7+6]=r.complete;}
        for(unsigned i=0;i<record.lookup_count;++i){const auto&l=registry.lookups()[i];record.lookups[i]={l.kind,l.guest_token,l.argument,l.raw_result,l.last_error,l.host_result,api(l.before),api(l.after),module(l.module)};}
        std::memcpy(record.state_after.data(),runtime.remill_state().data(),3504);std::memcpy(record.fx_after.data(),runtime.fx().data(),512);record.host_before=registry.host_before();record.host_after=registry.host_after();record.env_before=registry.host_env_before();record.env_after=registry.host_env_after();pages(runtime,record.pages_after);output.write(&record,sizeof(record));
        if(!complete&&registry.first_fault())std::cerr<<"actual fault pc="<<registry.first_fault()->pc<<" address="<<registry.first_fault()->address<<" reason="<<registry.first_fault()->detail<<'\n';check(complete&&registry.ready(),"Actual compiled before-only replay failed");check(GetLastError()==0xaabb0000U+id&&registry.host_before()==registry.host_after()&&registry.host_env_before()==registry.host_env_after(),"Actual internal host FP/error restoration checkpoint");
        std::cout<<"actual replay "<<id<<" CW="<<in.cw<<" events="<<record.event_count<<" routes="<<record.route_count<<" BOOL="<<registry.lookups()[2].raw_result<<'\n';
    }
    output.finish();std::cout<<"24 actual native before-only replays; source-model/original comparison pending\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
