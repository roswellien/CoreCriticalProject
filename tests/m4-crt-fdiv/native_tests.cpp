// Native-only authored controls. No original game/provider instructions execute.
#include "registry.hpp"
#include <iostream>
#include <memory>
using namespace mw34;
namespace fd=mw34::m4_crt_fdiv;
namespace mw34::m4_crt_fdiv {
// Only authored negative fixtures can access private active routing. These are
// not original observations and never bind a game translation or successful API.
struct RegistryControlProbe {
 static void query(Registry&r){auto&s=r.state_;r.entered_=r.active_=true;r.frames_.push_back({0x780042a3,entry_esp,0x7800425e,r.nonvolatile()});s.gpr.rsp.dword=entry_esp-24;}
 static void phase(Registry&r,unsigned index){auto&s=r.state_;constexpr unsigned ret[]{0x780042ae,0x780042c2,0x780042ce};constexpr unsigned target[]{module_route,proc_route,feature_route};s.gpr.rip.dword=target[index];s.gpr.rsp.dword=entry_esp-24;r.runtime_.memory().store<unsigned>({s.gpr.rsp.dword},ret[index]);r.runtime_.memory().store<unsigned>({s.gpr.rsp.dword+4},index==0?0x7802e404:index==1?module_token:0);if(index==1)r.runtime_.memory().store<unsigned>({s.gpr.rsp.dword+8},0x7802e3e8);}
 static void fnclex(Registry&r){auto&s=r.state_;r.entered_=r.active_=r.flag_written_=true;r.cleared_=false;r.frames_.clear();r.frames_.push_back({writer,entry_esp,outer_return,r.nonvolatile()});s.gpr.rip.dword=0x78004268;}
 static void wrong_issue(Registry&r){r.lookups_[1].guest_token^=1;}
};
}
namespace {
unsigned checks{},scenarios{};
void check(bool ok,const char*detail){++checks;if(!ok)throw std::runtime_error(detail);}
constexpr std::array<unsigned short,12>controls{0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f};
constexpr std::array<unsigned,9>bases{0x78004000,0x78011000,0x7802c000,0x7802e000,0x7802f000,0x78030000,0x78037000,0x20001000,0x5bb000};
void status(State&s,unsigned word){s.x87.fxsave.swd.flat=static_cast<unsigned short>(word);s.sw.ie=(word>>0)&1;s.sw.de=(word>>1)&1;s.sw.ze=(word>>2)&1;s.sw.oe=(word>>3)&1;s.sw.ue=(word>>4)&1;s.sw.pe=(word>>5)&1;s.sw.sf=(word>>6)&1;s.sw.c0=(word>>8)&1;s.sw.c1=(word>>9)&1;s.sw.c2=(word>>10)&1;s.sw.c3=(word>>14)&1;}
State seed(unsigned short cw,unsigned repeat){State s;auto*p=reinterpret_cast<unsigned char*>(&s);for(unsigned i=0;i<3504;++i)p[i]=static_cast<unsigned char>(i*31+repeat*17+3);std::memset(&s.addr,0,sizeof(s.addr));s.addr.fs_base.dword=0x7ffde000;s.gpr.rax.dword=0x13579bdf;s.gpr.rcx.dword=0x2468ace0;s.gpr.rdx.dword=0x81726354;s.gpr.rbx.dword=0x10293847;s.gpr.rsp.dword=fd::entry_esp;s.gpr.rbp.dword=0x92837465;s.gpr.rsi.dword=0x56473829;s.gpr.rdi.dword=0xaabbccdd;s.gpr.rip.dword=fd::writer;s.rflag.flat=0x202;s.aflag.cf=s.aflag.pf=s.aflag.af=s.aflag.zf=s.aflag.sf=s.aflag.df=s.aflag.of=0;s.x87.fxsave.cwd.flat=cw;status(s,0);s.x87.fxsave.ftw.flat=0;s.x87.fxsave.mxcsr.flat=0x1f80;s.x87.fxsave.mxcsr_mask.flat=0x2ffff;
    // Full raw storage and nonzero legacy metadata remain live across callbacks.
    s.x87.fxsave.ip=0x11223344;s.x87.fxsave.cs.flat=0x23;s.x87.fxsave.fop=0x11d;s.x87.fxsave.dp=0x55667788;s.x87.fxsave.ds.flat=0x2b;return s;
}
void seed_runtime(m4_runtime::Runtime&r,unsigned short cw,unsigned repeat){auto s=seed(cw,repeat);std::memcpy(r.remill_state().data(),&s,3504);std::memcpy(r.fx().data(),&s.x87,512);std::memset(r.fx().data()+6,0,18);r.mark_remill_seeded();std::array<std::byte,4096>stack{};for(unsigned i=0;i<4096;++i)stack[i]=std::byte(static_cast<unsigned char>(i*7+repeat*19+0xa5));r.memory().write({fd::stack_begin},stack);r.memory().store<unsigned>({fd::entry_esp},fd::outer_return);}
State&state(m4_runtime::Runtime&r){return *reinterpret_cast<State*>(r.remill_state().data());}
#pragma pack(push,1)
struct Api{std::uint64_t address,named,owner,owner_named;fd::HostRegion region;char sha[64];wchar_t path[1024];};
struct Module{std::uint64_t handle;fd::HostRegion region;char sha[64];wchar_t path[1024];};
struct Lookup{unsigned kind,token,argument,result,last_error;std::uint64_t host_result;Api before,after;Module module;};
struct Record{
    unsigned id,repeat,cw,status,event_count,route_count,lookup_count;
    std::array<std::byte,3504>state_before,state_after;
    std::array<std::byte,512>fx_before,fx_after,host_before,host_after;
    std::array<std::byte,28>env_before,env_after;
    std::array<std::byte,9*4096>pages_before,pages_after;
    std::array<fd::Event,256>events;
    std::array<unsigned,21>routes;
    std::array<Lookup,3>lookups;
};
struct Header{char magic[8];unsigned version,count,record_bytes,pages;};
#pragma pack(pop)
Api api(const fd::HostIdentity&h){Api a{};a.address=h.address;a.named=h.named;a.owner=h.owner;a.owner_named=h.owner_named;a.region=h.region;check(h.sha.size()==64&&h.path.size()<1024,"Actual API serialization bounds");std::memcpy(a.sha,h.sha.data(),64);std::copy(h.path.begin(),h.path.end(),a.path);return a;}
Module module(const fd::ModuleIdentity&h){Module m{};m.handle=h.handle;m.region=h.region;check(h.handle&&h.sha.size()==64&&h.path.size()<1024,"Actual returned borrowed module serialization bounds");std::memcpy(m.sha,h.sha.data(),64);std::copy(h.path.begin(),h.path.end(),m.path);return m;}
class Output{HANDLE file_{INVALID_HANDLE_VALUE};public:explicit Output(const char*p){file_=CreateFileA(p,GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);check(file_!=INVALID_HANDLE_VALUE,"Fresh native-only raw output");Header h{};std::memcpy(h.magic,"MW4FDIN2",8);h.version=2;h.count=24;h.record_bytes=sizeof(Record);h.pages=9;write(&h,sizeof(h));}~Output(){if(file_!=INVALID_HANDLE_VALUE)CloseHandle(file_);}void write(const void*p,unsigned n){DWORD done{};check(WriteFile(file_,p,n,&done,nullptr)&&done==n,"Native raw write");}};
void pages(m4_runtime::Runtime&r,std::span<std::byte,9*4096>out){for(unsigned i=0;i<9;++i)r.memory().read({bases[i]},out.subspan(i*4096,4096));}
void primitive(){
    for(unsigned sw=0;sw<65536;++sw){auto s=seed(controls[sw%12],sw);status(s,sw);s.x87.fxsave.ftw.flat=static_cast<unsigned char>(sw*73);s.x87.fxsave.mxcsr.flat=0x1f80^(sw<<8);std::array<std::byte,512>fx{};std::memcpy(fx.data(),&s.x87,512);std::memset(fx.data()+6,0x5a,18);auto want=s;auto wanted_fx=fx;status(want,sw&~0x80ffU);auto output=static_cast<unsigned short>(sw&~0x80ffU);std::memcpy(wanted_fx.data()+2,&output,2);check(fd::clear_guest_exceptions(s,fx),"Coherent exhaustive typed FNCLEX admission");check(!std::memcmp(&s,&want,3504)&&fx==wanted_fx,"All defined clears and complete opaque State/FX preservation; native undefined CC representative");}
    for(unsigned mode=0;mode<12;++mode){auto s=seed(0x37f,mode);std::array<std::byte,512>fx{};std::memcpy(fx.data(),&s.x87,512);if(!mode)fx[2]=std::byte{1};else{auto*flags=reinterpret_cast<unsigned char*>(&s.sw);constexpr std::array<unsigned,11>offsets{1,3,5,7,9,11,13,15,17,19,21};flags[offsets[mode-1]]=1;}auto before=s;auto oldfx=fx;check(!fd::clear_guest_exceptions(s,fx)&&!std::memcmp(&s,&before,3504)&&fx==oldfx,"Incoherent FNCLEX views reject without mutation");}
}
bool absent(GuestMemory&m,unsigned address){try{(void)m.load<unsigned>({address});return false;}catch(const MemoryFault&e){return e.reason()==MemoryFaultReason::unmapped;}}
}
int main(int argc,char**argv){try{
    check(argc==5,"Native controls: actual-game actual-provider exact-pack fresh-raw");auto game=fd::readfile(argv[1],2384384),provider=fd::readfile(argv[2],266293),pack=fd::readfile(argv[3],28740);primitive();Output output(argv[4]);unsigned id{};
    for(auto cw:controls)for(unsigned repeat=0;repeat<2;++repeat){++scenarios;auto runtime=m4_runtime::Runtime::from_admitted_image(game);seed_runtime(runtime,cw,repeat);fd::Registry registry(runtime);check(registry.admit(provider,pack)&&!registry.ready(),"Exact admission does not manufacture initialized data");Record record{};record.id=id++;record.repeat=repeat;record.cw=cw;std::memcpy(record.state_before.data(),runtime.remill_state().data(),3504);std::memcpy(record.fx_before.data(),runtime.fx().data(),512);pages(runtime,record.pages_before);auto before=state(runtime);auto last_error=0xaabb0000U+record.id;SetLastError(last_error);bool success=registry.initialize();if(!success&&registry.first_fault())std::cerr<<"fault "<<std::hex<<registry.first_fault()->pc<<' '<<registry.first_fault()->address<<' '<<registry.first_fault()->detail<<std::dec<<'\n';check(success&&registry.ready(),"Actual compiled writer successful Windows query path");check(GetLastError()==last_error,"Outer native host last error restored");check(registry.host_before()==registry.host_after()&&registry.host_env_before()==registry.host_env_after(),"Whole host FX512 and ENV28 restored after actual services and typed control");
        const auto&lookups=registry.lookups();check(lookups.size()==3&&lookups[0].host_result&&lookups[1].host_result&&lookups[0].guest_token==fd::module_token&&lookups[1].guest_token==fd::feature_route,"Actual nonnull OS lookup owns typed module/export tokens");auto address=registry.resolve_data({fd::game_iat});check(address&&address->value==fd::global&&runtime.memory().load<unsigned>(*address)==lookups[2].raw_result,"Actual compiled returned BOOL global data writer");check(runtime.memory().load<unsigned>({fd::game_iat})==registry.original_game_word()&&runtime.memory().load<unsigned>({fd::module_iat})==0x345d2&&runtime.memory().load<unsigned>({fd::proc_iat})==0x346ac,"Raw game/provider IAT words remain unchanged");
        State want=before;want.gpr.rax.dword=0x9001f|((cw>>10&3)<<8);want.gpr.rcx.dword=0x30000;want.gpr.rdx.dword=0x300;want.gpr.rsp.dword=fd::entry_esp+4;want.gpr.rip.dword=fd::outer_return;want.aflag.cf=want.aflag.af=want.aflag.sf=want.aflag.of=0;want.aflag.pf=want.aflag.zf=1;want.x87.fxsave.cwd.flat=(cw&~0x300U)|0x200;
        check(!std::memcmp(&state(runtime),&want,3504),"All3504 actual State bytes match complete source-policy output");auto fx=record.fx_before;std::memcpy(fx.data(),&want.x87.fxsave.cwd.flat,2);check(!std::memcmp(fx.data(),runtime.fx().data(),512),"Separate whole guestFX changes only actual canonical control word");
        check(registry.routes().size()==3&&registry.events().size()<256,"Actual bounded route/access records");for(unsigned i=0;i<3;++i){auto&r=registry.routes()[i];check(r.complete&&r.exit_esp==r.entry_esp+4+r.argument_bytes,"Actual Windows stdcall frame cleanup");record.routes[i*7+0]=r.site;record.routes[i*7+1]=r.target;record.routes[i*7+2]=r.return_pc;record.routes[i*7+3]=r.entry_esp;record.routes[i*7+4]=r.exit_esp;record.routes[i*7+5]=r.argument_bytes;record.routes[i*7+6]=r.complete;auto&l=lookups[i];record.lookups[i]={l.kind,l.guest_token,l.argument,l.raw_result,l.last_error,l.host_result,api(l.before),api(l.after),module(l.module)};}
        record.status=1;record.event_count=static_cast<unsigned>(registry.events().size());record.route_count=3;record.lookup_count=3;std::copy(registry.events().begin(),registry.events().end(),record.events.begin());std::memcpy(record.state_after.data(),runtime.remill_state().data(),3504);std::memcpy(record.fx_after.data(),runtime.fx().data(),512);record.host_before=registry.host_before();record.host_after=registry.host_after();record.env_before=registry.host_env_before();record.env_after=registry.host_env_after();pages(runtime,record.pages_after);
        // Replay only actual checked stores to verify whole pages. This is an
        // observed access-semantic check, not an expected instruction oracle.
        auto replay=record.pages_before;for(const auto&e:registry.events())if(e.kind==1){unsigned p=9;for(unsigned i=0;i<9;++i)if(e.address>=bases[i]&&std::uint64_t(e.address)+e.width<=std::uint64_t(bases[i])+4096)p=i;check(p<9&&(e.width==2||e.width==4),"Actual store belongs to one owned page");for(unsigned i=0;i<e.width;++i)replay[p*4096+e.address-bases[p]+i]=std::byte((e.value>>(i*8))&255);}check(replay==record.pages_after,"Whole source/global/stack/IAT pages match actual ordered checked stores");output.write(&record,sizeof(record));
    }
    for(unsigned mode=0;mode<23;++mode){++scenarios;auto runtime=m4_runtime::Runtime::from_admitted_image(game);seed_runtime(runtime,0x37f,mode);auto registry=std::make_unique<fd::Registry>(runtime);bool foreign=mode<3;unsigned sentinel=mode==0?0x78004000:mode==1?0x7802e000:0x78037000;if(foreign){runtime.memory().map({sentinel},16,Permissions::read|Permissions::write);runtime.memory().store<unsigned>({sentinel},0xabcdef12);}auto changed=pack;if(mode==3)changed[100]^=std::byte{1};bool admitted=registry->admit(provider,changed);if(mode<4)check(!admitted&&registry->first_fault(),"Actual mapping/pack admission fails causally");else{check(admitted,"Control exact admission");auto&s=state(runtime);if(mode==4)s.gpr.rip.dword++;if(mode==5)s.gpr.rsp.dword+=4;if(mode==6)runtime.memory().store<unsigned>({fd::entry_esp},fd::outer_return+1);if(mode==7)s.addr.ds_base.dword=4;if(mode==8)s.addr.ss_base.dword=4;if(mode==9)s.addr.fs_base.dword+=4;if(mode==10)s.aflag.df=1;if(mode==11)status(s,1);if(mode==12)status(s,7<<11);if(mode==13)runtime.fx()[2]=std::byte{1};if(mode==14)s.x87.fxsave.mxcsr.flat=0x1f81;if(mode==15)runtime.fx()[24]=std::byte{0};if(mode==16)s.x87.fxsave.cwd.flat=0x37e;if(mode==17){unsigned short cw=0x17f;s.x87.fxsave.cwd.flat=cw;std::memcpy(runtime.fx().data(),&cw,2);}if(mode==18)runtime.memory().protect({0x20000000},Permissions::read);if(mode==19)runtime.memory().protect({0x78037000},Permissions::read);if(mode==20){runtime.memory().protect({0x78004000},Permissions::read|Permissions::write);runtime.memory().store<unsigned>({fd::writer},0);}if(mode==21){runtime.memory().protect({0x7802e000},Permissions::read|Permissions::write);runtime.memory().store<unsigned>({fd::module_iat},0);}if(mode==22){unsigned short cw=0x137f;s.x87.fxsave.cwd.flat=cw;std::memcpy(runtime.fx().data(),&cw,2);}SetLastError(0x1234abce);check(!registry->initialize()&&!registry->ready()&&registry->first_fault(),"Required source/state/memory fault cannot become writer success");check(GetLastError()==0x1234abce&&registry->host_before()==registry->host_after()&&registry->host_env_before()==registry->host_env_after(),"Host thread error and whole FP environment restored on actual fault");check(registry->lookups().empty(),"All directed early faults stop before actual dynamic APIs");}
        auto f=*registry->first_fault();auto old=state(runtime);auto oldfx=std::array<std::byte,512>{};std::memcpy(oldfx.data(),runtime.fx().data(),512);check(!registry->initialize()&&!registry->admit(provider,pack)&&!registry->resolve_data({fd::game_iat}),"Required fault remains terminal on repaired retry");check(f.reason==registry->first_fault()->reason&&f.pc==registry->first_fault()->pc&&f.address==registry->first_fault()->address&&!std::memcmp(&old,&state(runtime),3504)&&!std::memcmp(oldfx.data(),runtime.fx().data(),512),"First fault/fullState/FX prefix preserved across retry");std::cout<<"control "<<mode<<" fault_pc "<<f.pc<<" address "<<f.address<<" reason "<<static_cast<unsigned>(f.reason)<<" events "<<registry->events().size()<<'\n';registry.reset();for(auto p:{0x78004000U,0x7802e000U,0x78037000U})if(foreign&&p==sentinel)check(runtime.memory().load<unsigned>({p})==0xabcdef12,"Partial cleanup preserves foreign sentinel");else check(absent(runtime.memory(),p),"Owned provider mappings cleaned without foreign deletion");
    }
    // Private active-query fixtures exercise causal route checks at their exact
    // call phase. Any successful preparation invokes the real module/export API;
    // the fixture does not stand in for a completed compiled writer.
    for(unsigned mode=0;mode<12;++mode){++scenarios;auto runtime=m4_runtime::Runtime::from_admitted_image(game);seed_runtime(runtime,0x37f,mode);fd::Registry registry(runtime);check(registry.admit(provider,pack),"Route fixture exact admission");auto&s=state(runtime);
      fd::RegistryControlProbe::query(registry);unsigned phase=mode<3?0:mode<6?1:2;
      if(mode>=9){s.gpr.rip.dword=0x7802c070;phase=0;}
      if(mode<9){for(unsigned i=0;i<phase;++i){fd::RegistryControlProbe::phase(registry,i);registry.service(&s,i?fd::proc_route:fd::module_route);}fd::RegistryControlProbe::phase(registry,phase);}
      auto prefix=registry.lookups().size();fd::FaultReason expected=fd::FaultReason::call_frame;
      if(mode==0){s.gpr.rip.dword=fd::module_route+1;expected=fd::FaultReason::call_frame;}
      if(mode==1)runtime.memory().store<unsigned>({s.gpr.rsp.dword},0x780042af);
      if(mode==2){runtime.memory().store<unsigned>({s.gpr.rsp.dword+4},0x7802e405);expected=fd::FaultReason::import_owner;}
      if(mode==3){runtime.memory().store<unsigned>({s.gpr.rsp.dword+4},fd::module_token+1);expected=fd::FaultReason::dynamic_route;}
      if(mode==4){runtime.memory().store<unsigned>({s.gpr.rsp.dword+8},0x7802e3e9);expected=fd::FaultReason::dynamic_route;}
      if(mode==5)runtime.memory().store<unsigned>({s.gpr.rsp.dword},0x780042c3);
      if(mode==6){runtime.memory().store<unsigned>({s.gpr.rsp.dword+4},1);expected=fd::FaultReason::dynamic_route;}
      if(mode==7){fd::RegistryControlProbe::wrong_issue(registry);expected=fd::FaultReason::dynamic_route;}
      if(mode==8){s.gpr.rip.dword=fd::feature_route+1;expected=fd::FaultReason::call_frame;}
      if(mode==9)expected=fd::FaultReason::unsupported_fallback;
      if(mode==10)s.gpr.rip.dword=0x78004268;
      if(mode==11){fd::RegistryControlProbe::fnclex(registry);status(s,1);}
      bool threw{};try{if(mode==9)registry.unsupported(&s,s.gpr.rip.dword);else if(mode>=10){registry.fnclex(&s,s.gpr.rip.dword);}else registry.service(&s,s.gpr.rip.dword);}catch(...){threw=true;}
      if(mode>=10)expected=fd::FaultReason::state_domain;
      check(threw&&registry.first_fault()&&registry.first_fault()->reason==expected&&!registry.ready(),"Exact typed route/fallback/FNCLEX denial is causal");check(registry.lookups().size()==prefix,"Denied service never manufactures a lookup/result");auto old=s;auto oldfx=std::array<std::byte,512>{};std::memcpy(oldfx.data(),runtime.fx().data(),512);auto f=*registry.first_fault();check(!registry.initialize()&&!registry.resolve_data({fd::game_iat})&&!std::memcmp(&old,&s,3504)&&!std::memcmp(oldfx.data(),runtime.fx().data(),512)&&registry.first_fault()->pc==f.pc,"Late route first fault and opaque prefix retained on retry");std::cout<<"route-unit "<<mode<<" actual_preparation_lookups "<<prefix<<" fault_pc "<<f.pc<<" address "<<f.address<<" reason "<<static_cast<unsigned>(f.reason)<<'\n';
    }
    std::cout<<"{\"passed\":true,\"native_only\":true,\"checks\":"<<checks<<",\"scenarios\":"<<scenarios<<",\"actual_writer_records\":24,\"FNCLEX_words\":65536,\"FNCLEX_incoherent_controls\":12,\"authored_route_units\":12,\"original_execution\":false}\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
