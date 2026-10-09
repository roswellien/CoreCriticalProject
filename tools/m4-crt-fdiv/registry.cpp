#include "registry.hpp"
#include "spec.hpp"
namespace mw34::m4_crt_fdiv {
namespace {
constexpr std::array<unsigned,7>bases{0x78004000,0x78011000,0x7802c000,0x7802e000,0x7802f000,0x78030000,0x78037000};
constexpr std::array<unsigned,7>permissions{5,5,5,1,1,1,3};
constexpr std::array<unsigned,6>pointer_pcs{0x78004270,0x7800427a,0x7800427f,0x78004289,0x78004293,0x7800429d};
constexpr std::array<unsigned,6>pointer_slots{0x78037c34,0x78037c30,0x78037c38,0x78037c3c,0x78037c40,0x78037c44};
constexpr std::array<unsigned,6>pointer_values{0x7802838c,0x780286e2,0x780283f2,0x78028332,0x780283da,0x780286e2};
struct Abort{};
unsigned word(std::span<const std::byte>bytes,unsigned offset){require(std::uint64_t(offset)+4<=bytes.size(),"Private pack word bound");unsigned value{};std::memcpy(&value,bytes.data()+offset,4);return value;}
extern "C" void*mw34_fdiv_sub_78004254(State*,unsigned,void*);
void restore_host(const std::array<std::byte,512>&fx,const std::array<std::byte,28>&env){
    __asm__ volatile("fxrstor64 %0\n\tfldenv %1"::"m"(fx),"m"(env):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)","xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");
}
}
Registry::Registry(m4_runtime::Runtime&r):runtime_(r),state_(*reinterpret_cast<State*>(r.remill_state().data())),cw_(r.memory(),state_,r.fx(),GuestAddress{stack_begin},stack_bytes),thread_(GetCurrentThreadId()){
    require(r.domain()==m4_runtime::Domain::admitted_game&&r.remill_seeded()&&!r.poisoned(),"Exact seeded admitted persistent Runtime required");
}
Registry::~Registry(){cleanup();}
void Registry::cleanup()noexcept{for(unsigned i=7;i-->0;)if(owned_[i]){try{runtime_.memory().unmap({bases[i]});}catch(...){}owned_[i]=false;}}
[[noreturn]]void Registry::deny(FaultReason reason,unsigned address,const char*detail){if(!fault_)fault_=Fault{reason,state_.gpr.rip.dword,address,detail};ready_=false;throw Abort{};}
bool Registry::stack(unsigned address,unsigned size)const{return address>=stack_begin&&std::uint64_t(address)+size<=std::uint64_t(stack_begin)+stack_bytes;}
std::array<unsigned,4>Registry::nonvolatile()const{return {state_.gpr.rbx.dword,state_.gpr.rbp.dword,state_.gpr.rsi.dword,state_.gpr.rdi.dword};}
const m4::ImportSymbol&Registry::game_owner()const{const m4::ImportSymbol*found{};for(const auto&i:runtime_.image_metadata().imports)if(std::uint64_t(runtime_.image_metadata().image_base)+i.iat_rva==game_iat){require(!found&&i.name&&*i.name=="_adjust_fdiv"&&library(i.library,"msvcrt.dll"),"Unique actual named game data IAT owner");found=&i;}require(found,"Actual data IAT owner missing");return *found;}
void Registry::event(unsigned kind,unsigned pc,unsigned address,unsigned value,unsigned width){if(events_.size()>=1024)deny(FaultReason::call_frame,address,"Bounded actual event capacity");events_.push_back({kind,pc,address,value,width});}
bool Registry::admit(std::span<const std::byte>provider,std::span<const std::byte>pack)noexcept{
    if(fault_)return false;
    try{require(GetCurrentThreadId()==thread_&&!admitted_&&!entered_,"Fresh serial provider admission");Provider pe(provider);const auto&owner=game_owner();game_word_=owner.original_iat_value;require(runtime_.memory().load<unsigned>({game_iat})==game_word_,"Original raw game data IAT changed");require(pack.size()==pack_bytes&&m4::sha256(pack)==pack_sha&&std::memcmp(pack.data(),"MW4FDIP1",8)==0&&word(pack,8)==7,"Exact private source pack required");
        for(unsigned i=0;i<7;++i){auto offset=12+i*4104;require(word(pack,offset)==bases[i]&&word(pack,offset+4)==permissions[i],"Exact provider page ownership/permissions");pages_[i]={pack.begin()+offset+8,pack.begin()+offset+4104};}
        for(const auto&range:source_ranges){auto original=pe.slice(range.address,range.bytes,0x60000000);require(m4::sha256(original)==range.sha,"Original source range identity");auto index=std::find(bases.begin(),bases.end(),range.address&~4095)-bases.begin();require(index<7&&range.bytes<=4096-(range.address&4095)&&std::equal(original.begin(),original.end(),pages_[index].begin()+(range.address&4095)),"Literal native provider source ranges");}
        require(pages_[3]==pe.slice(0x7802e000,4096,0x40000000)&&pages_[6]==pe.slice(0x78037000,4096,0xc0000000),"Literal provider import/data pages");
        for(unsigned i=0;i<7;++i){runtime_.memory().map({bases[i]},4096,Permissions::read|Permissions::write);owned_[i]=true;runtime_.memory().write({bases[i]},pages_[i]);runtime_.memory().protect({bases[i]},static_cast<Permissions>(permissions[i]));}
        admitted_=true;integrity();return true;
    }catch(const MemoryFault&){if(!fault_)fault_=Fault{FaultReason::memory,state_.gpr.rip.dword,writer,"Required provider admission mapping fault"};}catch(...){if(!fault_)fault_=Fault{FaultReason::invalid_admission,state_.gpr.rip.dword,writer,"Exact provider/pack/game data owner admission rejected"};}cleanup();return false;
}
void Registry::integrity(){
    if(GetCurrentThreadId()!=thread_||!admitted_||runtime_.poisoned())deny(FaultReason::state_domain,writer,"Stable serial admitted Runtime owner required");
    if(game_owner().original_iat_value!=game_word_||runtime_.memory().load<unsigned>({game_iat})!=game_word_)deny(FaultReason::import_owner,game_iat,"Original game data IAT changed");
    for(unsigned i=0;i<7;++i){if(!owned_[i])deny(FaultReason::source_changed,bases[i],"Owned provider page missing");std::array<std::byte,4096>actual{};runtime_.memory().read({bases[i]},actual);if(!std::equal(actual.begin(),actual.end(),pages_[i].begin()))deny(FaultReason::source_changed,bases[i],"Live provider source/IAT/data bytes changed");}
}
void Registry::identity(State*s,unsigned pc){if(fault_)throw Abort{};if(!active_||s!=&state_||pc!=state_.gpr.rip.dword||state_.addr.ds_base.dword||state_.addr.ss_base.dword||state_.addr.fs_base.dword!=runtime_.fs_base().value||state_.aflag.df)deny(FaultReason::state_domain,pc,"Persistent actual State/flat segments/guest FS/DF identity");integrity();}
void Registry::domain(){
    const auto&f=state_.x87.fxsave;const auto&sw=state_.sw;unsigned mx{};std::uint16_t cw{},status{};std::memcpy(&cw,runtime_.fx().data(),2);std::memcpy(&status,runtime_.fx().data()+2,2);std::memcpy(&mx,runtime_.fx().data()+24,4);
    if(f.cwd.flat!=cw||m4_guest_cw::Context::normalized(cw)!=cw||(cw&0x3f)!=0x3f||(cw&0x1000)||((cw>>8)&3)==1||f.swd.flat||status||f.ftw.flat||runtime_.fx()[4]!=std::byte{}||f.mxcsr.flat!=0x1f80||mx!=0x1f80||sw.ie||sw.de||sw.ze||sw.oe||sw.ue||sw.pe||sw.sf||sw.c0||sw.c1||sw.c2||sw.c3)deny(FaultReason::state_domain,writer,"Only twelve masked normalized IC0 CW/empty TOP0/SW0 supported");
}
bool Registry::initialize()noexcept{
    if(fault_)return false;const auto host_error=GetLastError();bool success{};
    __asm__ volatile("fxsave64 %0\n\tfnstenv %1":"=m"(host_before_),"=m"(env_before_)::"memory");
    try{require(admitted_&&!entered_&&!active_&&!ready_,"Fresh provider writer invocation");entered_=true;active_=true;identity(&state_,writer);domain();if(state_.gpr.rsp.dword!=entry_esp||runtime_.memory().load<unsigned>({entry_esp})!=outer_return)deny(FaultReason::call_frame,entry_esp,"Exact source callback return frame required");
        auto result=mw34_fdiv_sub_78004254(&state_,writer,this);if(result!=this||!frames_.empty()||!flag_written_||pointer_writes_!=6||!cleared_||routes_.size()!=3||lookups_.size()!=3||state_.gpr.rip.dword!=outer_return||state_.gpr.rsp.dword!=entry_esp+4)deny(FaultReason::call_frame,writer,"Incomplete real writer/typed services/control/FNCLEX return");integrity();ready_=true;success=true;
        runtime_.cpu()={state_.gpr.rax.dword,state_.gpr.rcx.dword,state_.gpr.rdx.dword,state_.gpr.rbx.dword,state_.gpr.rsp.dword,state_.gpr.rbp.dword,state_.gpr.rsi.dword,state_.gpr.rdi.dword,static_cast<unsigned>((state_.rflag.flat&~0xcd5ULL)|(state_.aflag.cf<<0)|(state_.aflag.pf<<2)|(state_.aflag.af<<4)|(state_.aflag.zf<<6)|(state_.aflag.sf<<7)|(state_.aflag.df<<10)|(state_.aflag.of<<11)),state_.gpr.rip.dword};
    }catch(const MemoryFault&){if(!fault_)fault_=Fault{FaultReason::memory,state_.gpr.rip.dword,state_.gpr.rsp.dword,"Required writer checked memory fault"};}catch(...){if(!fault_)fault_=Fault{FaultReason::call_frame,state_.gpr.rip.dword,writer,"Actual native writer did not complete"};}
    active_=false;if(!success)ready_=false;
    restore_host(host_before_,env_before_);
    __asm__ volatile("fxsave64 %0\n\tfnstenv %1":"=m"(host_after_),"=m"(env_after_)::"memory");
    restore_host(host_before_,env_before_);SetLastError(host_error);return success;
}
unsigned Registry::read32(unsigned address){identity(&state_,state_.gpr.rip.dword);if(!stack(address,4)&&address!=module_iat&&address!=proc_iat)deny(FaultReason::memory,address,"Required32-bit read outside owned stack/provider imports");unsigned raw{};try{raw=runtime_.memory().load<unsigned>({address});}catch(...){deny(FaultReason::memory,address,"Required checked32-bit read fault");}event(0,state_.gpr.rip.dword,address,raw,4);
    if(address==module_iat){if(state_.gpr.rip.dword!=0x780042a8||raw!=0x345d2||!lookups_.empty())deny(FaultReason::import_owner,address,"Exact GetModuleHandleA source import read");event(6,state_.gpr.rip.dword,address,module_route,4);return module_route;}
    if(address==proc_iat){if(state_.gpr.rip.dword!=0x780042bc||raw!=0x346ac||lookups_.size()!=1||!lookups_[0].host_result)deny(FaultReason::import_owner,address,"Exact GetProcAddress source import read");event(6,state_.gpr.rip.dword,address,proc_route,4);return proc_route;}return raw;
}
void Registry::write32(unsigned address,unsigned value){identity(&state_,state_.gpr.rip.dword);auto pc=state_.gpr.rip.dword;bool provider=false;
    if(!stack(address,4)){if(pointer_writes_<6&&pc==pointer_pcs[pointer_writes_]&&address==pointer_slots[pointer_writes_]&&value==pointer_values[pointer_writes_])provider=true;else if(pc==0x7800425e&&address==global&&pointer_writes_==6&&!flag_written_&&lookups_.size()==3&&value==lookups_[2].raw_result)provider=true;else deny(FaultReason::memory,address,"Unadmitted provider data writer");}
    try{runtime_.memory().store<unsigned>({address},value);}catch(...){deny(FaultReason::memory,address,"Required checked32-bit write fault");}event(1,pc,address,value,4);
    if(provider){std::memcpy(pages_[6].data()+(address&4095),&value,4);if(address==global)flag_written_=true;else++pointer_writes_;}
}
void Registry::enter(State*s,unsigned pc){identity(s,pc);if(frames_.size()>=8||!stack(state_.gpr.rsp.dword,4))deny(FaultReason::call_frame,state_.gpr.rsp.dword,"Bounded source function frame");auto esp=state_.gpr.rsp.dword,ret=runtime_.memory().load<unsigned>({esp});unsigned site{};
    if(frames_.empty()){if(pc!=writer||esp!=entry_esp||ret!=outer_return||runtime_.memory().load<unsigned>({callback_global})!=writer)deny(FaultReason::call_frame,pc,"Actual callback pointer/frame identity");site=outer_call;}
    else{auto parent=frames_.back().entry;if(parent==writer){if(pc==0x7800426b)site=0x78004254;if(pc==0x780042a3)site=0x78004259;if(pc==0x780042cf)site=0x78004263;}if(parent==0x780042cf&&pc==0x780042e1)site=0x780042d9;if(parent==0x780042e1&&pc==0x780042f7)site=0x780042ef;if(parent==0x780042f7&&pc==0x7800432c)site=0x78004303;if(parent==0x780042f7&&pc==0x7800439f)site=0x7800431a;
        if(!site||ret!=site+5)deny(FaultReason::call_frame,pc,"Required exact source CALL/return pair");std::array<std::byte,5>code{};runtime_.memory().read({site},code);int delta{};std::memcpy(&delta,code.data()+1,4);if(code[0]!=std::byte{0xe8}||site+5+static_cast<unsigned>(delta)!=pc)deny(FaultReason::source_changed,site,"Original direct CALL target changed");}
    frames_.push_back({pc,esp,ret,nonvolatile()});event(2,pc,esp,ret,4);
}
void Registry::returned(State*s,unsigned pc){identity(s,pc);if(frames_.empty())deny(FaultReason::call_frame,pc,"No source frame for actual RET");const auto f=frames_.back();if(pc!=f.return_pc||state_.gpr.rsp.dword!=f.esp+4||nonvolatile()!=f.nonvolatile||runtime_.memory().load<unsigned>({f.esp})!=f.return_pc)deny(FaultReason::call_frame,pc,"Actual RET/stack cleanup/nonvolatile identity");frames_.pop_back();event(3,pc,state_.gpr.rsp.dword,f.return_pc,4);}
void Registry::service(State*s,unsigned target){identity(s,target);if(frames_.empty()||frames_.back().entry!=0x780042a3||routes_.size()>=3)deny(FaultReason::dynamic_route,target,"Dynamic Windows service lacks actual query caller");auto index=static_cast<unsigned>(routes_.size()),esp=state_.gpr.rsp.dword;const std::array<unsigned,3>targets{module_route,proc_route,feature_route},sites{0x780042a8,0x780042bc,0x780042cc},returns{0x780042ae,0x780042c2,0x780042ce},arguments{4,8,4};if(target!=targets[index]||!stack(esp,4+arguments[index])||runtime_.memory().load<unsigned>({esp})!=returns[index])deny(FaultReason::call_frame,esp,"Exact compiled Windows CALL return/arguments");
    ServiceRoute route{sites[index],target,returns[index],esp,0,arguments[index],false};routes_.push_back(route);LookupRecord lookup;
    try{if(index==0){if(runtime_.memory().load<unsigned>({esp+4})!=0x7802e404)deny(FaultReason::import_owner,esp+4,"Literal original module name pointer");std::array<std::byte,9>name{};runtime_.memory().read({0x7802e404},name);if(std::memcmp(name.data(),"KERNEL32",9))deny(FaultReason::import_owner,0x7802e404,"Owned original module name bytes");lookup=host_.module();state_.gpr.rax.dword=lookup.guest_token;}
        else if(index==1){if(lookups_.size()!=1||runtime_.memory().load<unsigned>({esp+4})!=lookups_[0].guest_token||runtime_.memory().load<unsigned>({esp+8})!=0x7802e3e8)deny(FaultReason::dynamic_route,esp,"Issued module token/named export arguments");std::array<std::byte,26>name{};runtime_.memory().read({0x7802e3e8},name);if(std::memcmp(name.data(),"IsProcessorFeaturePresent",26))deny(FaultReason::import_owner,0x7802e3e8,"Owned original case-sensitive export bytes");lookup=host_.procedure(runtime_.memory().load<unsigned>({esp+4}));state_.gpr.rax.dword=lookup.guest_token;}
        else{if(lookups_.size()!=2||lookups_[1].guest_token!=feature_route||runtime_.memory().load<unsigned>({esp+4})!=0)deny(FaultReason::dynamic_route,esp,"Only actually issued export token/feature0");lookup=host_.feature(target,0);state_.gpr.rax.dword=lookup.raw_result;}
    }catch(const Abort&){throw;}catch(...){deny(FaultReason::host_service,target,"Required actual Windows lookup/query identity failed");}
    // ECX/EDX/flags are ABI volatile. This native representative preserves them;
    // original measurements must retain any differing residual stack halfwords.
    lookups_.push_back(std::move(lookup));state_.gpr.rsp.dword=esp+4+arguments[index];state_.gpr.rip.dword=returns[index];routes_.back().exit_esp=state_.gpr.rsp.dword;routes_.back().complete=true;event(4,sites[index],target,state_.gpr.rax.dword,arguments[index]);integrity();
}
void Registry::fnclex(State*s,unsigned pc){identity(s,pc);if(pc!=0x78004268||!flag_written_||cleared_||frames_.size()!=1)deny(FaultReason::state_domain,pc,"Exact completed source FNCLEX phase");if(!clear_guest_exceptions(state_,runtime_.fx()))deny(FaultReason::state_domain,pc,"Coherent typed FNCLEX State/FX status required");cleared_=true;event(5,pc,0,state_.x87.fxsave.swd.flat,2);}
void Registry::wait(State*s,unsigned pc){identity(s,pc);if(pc!=0x780042fc)deny(FaultReason::state_domain,pc,"Exact control FWAIT site");domain();}
void Registry::store_cw(State*s,unsigned address){identity(s,state_.gpr.rip.dword);if(state_.gpr.rip.dword!=0x780042fd||!cw_.store(s,{address}))deny(FaultReason::memory,address,"Required typed FNSTCW transfer");event(1,state_.gpr.rip.dword,address,state_.x87.fxsave.cwd.flat,2);}
void Registry::load_cw(State*s,unsigned address){identity(s,state_.gpr.rip.dword);if(state_.gpr.rip.dword!=0x78004324||!cw_.load(s,{address}))deny(FaultReason::memory,address,"Required typed FLDCW transfer");event(0,state_.gpr.rip.dword,address,runtime_.memory().load<std::uint16_t>({address}),2);}
[[noreturn]]void Registry::unsupported(State*s,unsigned pc){identity(s,pc);deny(FaultReason::unsupported_fallback,pc,"Actual NULL lookup selected unaccepted FDIV arithmetic fallback");}
std::optional<GuestAddress>Registry::resolve_data(GuestAddress slot)noexcept{if(fault_)return std::nullopt;try{if(!ready_||slot.value!=game_iat||!flag_written_||lookups_.size()!=3)deny(FaultReason::import_owner,slot.value,"Only completed actual initialized _adjust_fdiv data route");integrity();if(runtime_.memory().load<unsigned>({global})!=lookups_[2].raw_result)deny(FaultReason::source_changed,global,"Actual initialized query global changed");return GuestAddress{global};}catch(const MemoryFault&){if(!fault_)fault_=Fault{FaultReason::memory,state_.gpr.rip.dword,slot.value,"Ready data route checked memory fault"};}catch(...){if(!fault_)fault_=Fault{FaultReason::import_owner,state_.gpr.rip.dword,slot.value,"Ready data route rejected"};}ready_=false;return std::nullopt;}
}
extern "C" unsigned mw34_fdiv___remill_read_memory_32(void*p,unsigned a){return static_cast<mw34::m4_crt_fdiv::Registry*>(p)->read32(a);}
extern "C" void*mw34_fdiv___remill_write_memory_32(void*p,unsigned a,unsigned v){static_cast<mw34::m4_crt_fdiv::Registry*>(p)->write32(a,v);return p;}
extern "C" void*mw34_fdiv___remill_function_return(State*s,unsigned pc,void*p){static_cast<mw34::m4_crt_fdiv::Registry*>(p)->returned(s,pc);return p;}
extern "C" void*mw34_fdiv___remill_function_call(State*s,unsigned pc,void*p){static_cast<mw34::m4_crt_fdiv::Registry*>(p)->service(s,pc);return p;}
extern "C" void*mw34_fdiv_enter(State*s,unsigned pc,void*p){static_cast<mw34::m4_crt_fdiv::Registry*>(p)->enter(s,pc);return p;}
extern "C" void*mw34_fdiv_fnclex(State*s,unsigned pc,void*p){static_cast<mw34::m4_crt_fdiv::Registry*>(p)->fnclex(s,pc);return p;}
extern "C" void*mw34_fdiv_unsupported(State*s,unsigned pc,void*p){static_cast<mw34::m4_crt_fdiv::Registry*>(p)->unsupported(s,pc);}
extern "C" void*mw34_fdiv_mw34_cf_wait(State*s,unsigned pc,void*p){static_cast<mw34::m4_crt_fdiv::Registry*>(p)->wait(s,pc);return p;}
extern "C" void*mw34_fdiv_mw34_cf_store_cw(State*s,unsigned a,void*p){static_cast<mw34::m4_crt_fdiv::Registry*>(p)->store_cw(s,a);return p;}
extern "C" void*mw34_fdiv_mw34_cf_load_cw(State*s,unsigned a,void*p){static_cast<mw34::m4_crt_fdiv::Registry*>(p)->load_cw(s,a);return p;}
