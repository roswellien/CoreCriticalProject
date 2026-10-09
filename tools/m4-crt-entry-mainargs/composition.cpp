// Bounded native research: literal translated CRT entry to its first missing
// service. This is not startup admission or a native game launcher.
#include "runtime.hpp"
#include "admission.hpp"
#include "crt_services.hpp"
#include "seed.hpp"
#include <remill/Arch/X86/Runtime/State.h>
#include "matherr_context.hpp"
#include "control_context.hpp"
#include "initterm_context.hpp"
#include "mainargs_context.hpp"
#include <algorithm>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <thread>
using namespace mw34;
namespace mn=mw34::m4_crt_matherr_paired_native;
namespace ci=mw34::m4_crt_control_integration;
namespace nt=mw34::m4_crt_entry_initerm;
namespace mg=mw34::m4_crt_entry_mainargs;
namespace {
using namespace m4_runtime;
constexpr unsigned entry=0x5ac3a0,frame=0x20001900;
extern "C" void *sub_5ac3a0(State*,unsigned,void*) noexcept(false);
extern "C" void *sub_5ac5c0(State*,unsigned,void*) noexcept(false);
void require(bool b,const char *reason){if(!b)throw std::runtime_error(reason);}
std::vector<std::byte> read_file(const char *name){std::ifstream f(name,std::ios::binary|std::ios::ate);require(bool(f),"Input open failed");auto size=f.tellg();require(size>0&&size<64*1024*1024,"Bounded input size");std::vector<std::byte>b(static_cast<std::size_t>(size));f.seekg(0);f.read(reinterpret_cast<char*>(b.data()),static_cast<std::streamsize>(b.size()));require(bool(f),"Complete input read");return b;}
void output(const std::string&path,std::span<const std::byte>b){std::ofstream f(path,std::ios::binary);require(bool(f),"Fresh output open failed");f.write(reinterpret_cast<const char*>(b.data()),static_cast<std::streamsize>(b.size()));require(bool(f),"Complete output write");}
Cpu32 cpu(const State&s){return {s.gpr.rax.dword,s.gpr.rcx.dword,s.gpr.rdx.dword,s.gpr.rbx.dword,s.gpr.rsp.dword,s.gpr.rbp.dword,s.gpr.rsi.dword,s.gpr.rdi.dword,static_cast<unsigned>((s.rflag.flat&~0xcd5ULL)|(s.aflag.cf<<0)|(s.aflag.pf<<2)|(s.aflag.af<<4)|(s.aflag.zf<<6)|(s.aflag.sf<<7)|(s.aflag.df<<10)|(s.aflag.of<<11)),s.gpr.rip.dword};}
void project(State&s,const Cpu32&c){s.gpr.rax.dword=c.eax;s.gpr.rcx.dword=c.ecx;s.gpr.rdx.dword=c.edx;s.gpr.rbx.dword=c.ebx;s.gpr.rsp.dword=c.esp;s.gpr.rbp.dword=c.ebp;s.gpr.rsi.dword=c.esi;s.gpr.rdi.dword=c.edi;s.gpr.rip.dword=c.eip;s.rflag.flat=c.eflags;s.aflag.cf=(c.eflags>>0)&1;s.aflag.pf=(c.eflags>>2)&1;s.aflag.af=(c.eflags>>4)&1;s.aflag.zf=(c.eflags>>6)&1;s.aflag.sf=(c.eflags>>7)&1;s.aflag.df=(c.eflags>>10)&1;s.aflag.of=(c.eflags>>11)&1;}
struct Event{unsigned pc,address,value,width,write;};
void entry_checkpoint(Runtime&);
void matherr_checkpoint(Runtime&,const char*);
// Caller-owned FP state spans the actual guest call and C++ fault handling.
// The outer nonthrowing boundary below restores again after its final catch.
struct InvocationHostBoundary {
 alignas(16)std::array<std::byte,512>fx;std::array<std::byte,28>env;
 InvocationHostBoundary()noexcept{__asm__ volatile("fxsave64 %0\n\tfnstenv %1":"=m"(fx),"=m"(env)::"memory");restore();}
 void restore()noexcept{__asm__ volatile("fxrstor64 %0\n\tfldenv %1"::"m"(fx),"m"(env):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)","xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");}
 ~InvocationHostBoundary()noexcept{restore();}
};
constexpr std::array<unsigned,3>matherr_pages{0x7800b000,0x78039000,0x7803b000};
std::array<std::byte,4096> provider_raw_page(std::span<const std::byte>file,unsigned address){
 auto word=[&](unsigned p){require(std::uint64_t(p)+2<=file.size(),"PE word bounds");unsigned short x{};std::memcpy(&x,file.data()+p,2);return x;};
 auto dword=[&](unsigned p){require(std::uint64_t(p)+4<=file.size(),"PE DWORD bounds");unsigned x{};std::memcpy(&x,file.data()+p,4);return x;};
 require(m4::sha256(file)==fd::provider_sha,"Exact provider page source");const auto pe=dword(0x3c),opt=pe+24;require(dword(opt+28)==0x78000000,"Provider preferred guest base");
 const auto sections=word(pe+6),size=word(pe+20);unsigned matches{};std::array<std::byte,4096>page{};
 for(unsigned i=0;i<sections;++i){const auto p=opt+size+i*40,virtual_size=dword(p+8),rva=dword(p+12),raw_size=dword(p+16),offset=dword(p+20),flags=dword(p+36);const auto requested=address-0x78000000;
  if(requested>=rva&&std::uint64_t(requested)+4096<=std::uint64_t(rva)+raw_size){require((flags&0xe0000000)==((address==matherr_pages[0]||address==0x78001000)?0x60000000U:0xc0000000U),"Exact provider page source permissions");require(std::uint64_t(offset)+requested-rva+4096<=file.size()&&virtual_size&&requested<rva+virtual_size,"Literal raw source page inside aligned mapped section");std::memcpy(page.data(),file.data()+offset+requested-rva,4096);++matches;}}
 require(matches==1,"One literal source-backed provider page");return page;
}
struct MatherrBinding {
 mn::Context context;std::array<std::array<std::byte,4096>,3>initial_pages;unsigned control{};
 MatherrBinding(Runtime&r,std::span<const std::byte>provider,unsigned mode):context(r),control(mode){for(unsigned i=0;i<3;++i)initial_pages[i]=provider_raw_page(provider,matherr_pages[i]);}
};
thread_local MatherrBinding*matherr_binding{};
void matherr_before(mn::Context&c){matherr_checkpoint(c.runtime,"matherr-projected");if(matherr_binding&&matherr_binding->control==24)throw std::runtime_error("Authored observer exception control");}
void matherr_event(mn::Context&c,unsigned step){
 require(matherr_binding&& &matherr_binding->context==&c,"Exact observer owner");const auto mode=matherr_binding->control;
 if(step==4&&mode==18)c.runtime.memory().store<unsigned>({c.frame},c.return_pc^1);
 if(step==4&&mode==19)c.state.gpr.rbx.dword^=1;
 if(step==4&&mode==20)c.state.gpr.rax.dword^=1;
 if(step==1&&mode==21)c.step=4;
}
void matherr_adapter(Runtime&r){
 require(matherr_binding&& &matherr_binding->context.runtime==&r&&!mn::owner,"Exact serial matherr owner");auto&b=*matherr_binding;auto&c=b.context;
 matherr_checkpoint(r,"matherr-before");
 try{
  for(unsigned i=0;i<3;++i){std::array<std::byte,4096>page{};r.memory().read({matherr_pages[i]},page);require(page==b.initial_pages[i],"Matherr owned literal source pages intact before first service");}
  require(r.cpu().eip==0x5bb50c&&r.memory().load<unsigned>({r.cpu().esp})==0x5ac42e&&r.memory().load<unsigned>({r.cpu().esp+4})==0x51e7b0,"Actual game matherr callback/return frame");
  c.test_before_execute=&matherr_before;c.test_after_event=&matherr_event;mn::owner=&c;c.execute();mn::owner=nullptr;
  require(c.complete&&c.argument==0x51e7b0&&c.step==5&&r.memory().load<unsigned>({mn::zero_global})==0&&r.memory().load<unsigned>({mn::callback_global})==0x51e7b0,"Actual callback registration source writes completed");
  for(unsigned i=0;i<3;++i){auto expected=b.initial_pages[i];if(i==1){const unsigned zero=0;std::memcpy(expected.data()+(mn::zero_global&4095),&zero,4);}if(i==2){const unsigned callback=0x51e7b0;std::memcpy(expected.data()+(mn::callback_global&4095),&callback,4);}std::array<std::byte,4096>actual{};r.memory().read({matherr_pages[i]},actual);require(actual==expected,"Only two source-owned matherr DWORD stores modify complete pages");}
  matherr_checkpoint(r,"matherr-after");
 }catch(...){mn::owner=nullptr;matherr_checkpoint(r,"matherr-after");throw;}
}
#include "control_binding.inc"
#include "initterm_binding.inc"
#include "mainargs_binding.inc"
class Context;
thread_local Context*owner{};
class Context {
 Runtime&r_;State&s_;std::thread::id thread_=std::this_thread::get_id();
 std::vector<Event>events_;bool running_{};unsigned data_iat_{};fd::Registry&fdiv_;
public:struct DataRoute{unsigned pc,slot,raw,guest_address,value;};
private:std::vector<DataRoute>data_routes_;std::vector<unsigned>undefined_sites_;
public:
 Context(Runtime&r,fd::Registry&fdiv,const std::string&native_sha):r_(r),s_(*reinterpret_cast<State*>(r.remill_state().data())),fdiv_(fdiv){
  unsigned owners=0;for(const auto&i:r.image_metadata().imports)if(r.image_metadata().image_base+i.iat_rva==0x5bb508){require(i.name&&*i.name=="_adjust_fdiv"&&i.library=="MSVCRT.dll","Actual FDIV data import owner");data_iat_=i.original_iat_value;++owners;}require(owners==1&&r.memory().load<unsigned>({0x5bb508})==data_iat_,"Exact source FDIV raw IAT identity");
  require(r.remill_seeded()&&fdiv_.ready(),"Existing completed writer and persistent State required; no entry reseed");
  require(s_.addr.ds_base.dword==0&&s_.addr.ss_base.dword==0&&s_.addr.fs_base.dword==r.fs_base().value,"Carried flat DS/SS and owned guest FS required");
  r.register_translation({{entry},{Abi::Cdecl,0,true},&adapter,"Unaccepted complete CRT entry first-fault probe",{Domain::admitted_game,m4::admitted_image_hash,430,"30da37cdf0ae957fc87f6e0caf250b4a60e0e63767dea24935381791e60ad856",native_sha,"0c67cae86dad6468e082607ebe9d2b2504094829adb28e37b0c082d6e158d724"}});
  r.register_translation({{0x5ac5c0},{Abi::Cdecl,0,true},&leaf_adapter,"Literal translated CRT RET leaf",{Domain::admitted_game,m4::admitted_image_hash,1,"ae3f4619b0413d70d3004b9131c3752153074e45725be13b9a148978895e359e",native_sha,"0c67cae86dad6468e082607ebe9d2b2504094829adb28e37b0c082d6e158d724"}});
 }
 static void leaf_adapter(Runtime&r){require(owner&& &owner->r_==&r,"Leaf owner absent");owner->guard();project(owner->s_,r.cpu());auto*p=sub_5ac5c0(&owner->s_,0x5ac5c0,owner);require(p==owner,"Literal leaf memory token returned");r.cpu()=cpu(owner->s_);}
 static void adapter(Runtime&r){require(owner && &owner->r_==&r,"Entry owner absent");owner->run();}
 void guard(){require(owner==this&&running_&&thread_==std::this_thread::get_id(),"Stable serial entry ownership required");}
 void run(){require(!running_&&thread_==std::this_thread::get_id()&&r_.remill_seeded(),"Fresh serial entry required");std::vector<std::byte>source(430);r_.memory().read({entry},source);require(m4::sha256(source)=="30da37cdf0ae957fc87f6e0caf250b4a60e0e63767dea24935381791e60ad856","Current original entry identity");auto pending=r_.cpu();auto carried=cpu(s_);carried.esp=pending.esp;carried.eip=pending.eip;require(std::memcmp(&carried,&pending,sizeof(Cpu32))==0,"Only declared outer ESP/EIP transition permitted");s_.gpr.rsp.dword=pending.esp;s_.gpr.rip.dword=pending.eip;running_=true;try{entry_checkpoint(r_);(void)sub_5ac3a0(&s_,entry,this);throw std::runtime_error("Unexpected complete entry return");}catch(...){running_=false;throw;}}
 unsigned read(unsigned a,unsigned width){guard();require(width==4,"Only reached DWORD reads admitted");auto v=r_.memory().load<unsigned>({a});events_.push_back({s_.gpr.rip.dword,a,v,width,0});if(a==0x5bb508){require(s_.gpr.rip.dword==0x5ac408&&v==data_iat_,"Exact raw FDIV data import read");auto resolved=fdiv_.resolve_data({a});require(resolved&&resolved->value==fd::global&&fdiv_.ready(),"Only actual initialized owned FDIV data may resolve");auto value=r_.memory().load<unsigned>(*resolved);require(fdiv_.lookups().size()==3&&value==fdiv_.lookups()[2].raw_result,"Source-written data bound to actual query receipt");data_routes_.push_back({s_.gpr.rip.dword,a,v,resolved->value,value});return resolved->value;}if(a==fd::global){require(s_.gpr.rip.dword==0x5ac40d&&data_routes_.size()==1&&v==data_routes_[0].value&&fdiv_.ready(),"Actual dependent load of initialized FDIV data");}return v;}
 void write(unsigned a,unsigned v){guard();r_.memory().store<unsigned>({a},v);events_.push_back({s_.gpr.rip.dword,a,v,4,1});if(matherr_binding&&matherr_binding->control==17&&s_.gpr.rip.dword==0x5ac423)r_.memory().store<unsigned>({a},v^1);if(initterm_binding&&initterm_binding->control==47&&s_.gpr.rip.dword==0x5ac43b)r_.memory().store<unsigned>({a},v^1);}
 void*call(State*s,unsigned target){guard();require(s==&s_&&events_.size()>=2,"Actual source CALL memory events");const auto&read=events_[events_.size()-2];const auto&write=events_.back();
  constexpr std::array<std::array<unsigned,3>,5>calls{{{0x5ac3cf,0x5bb5a4,0x5ac3d5},{0x5ac3ec,0x5bb57c,0x5ac3f2},{0x5ac3fa,0x5bb504,0x5ac400},{0x5ac428,0x5bb50c,0x5ac42e},{0x5ac468,0x5bb514,0x5ac46e}}};
  const auto found=std::find_if(calls.begin(),calls.end(),[&](const auto&row){return row[0]==read.pc&&row[1]==read.address;});require(found!=calls.end()&&read.write==0&&read.value==target&&write.pc==read.pc&&write.write==1&&write.address==s_.gpr.rsp.dword&&write.value==(*found)[2],"Exact source-owned CRT import CALL/frame");
  r_.cpu()=cpu(s_);r_.cpu().esp+=4;r_.cpu().eip=read.pc;r_.call_import({read.address},{write.value});project(s_,r_.cpu());return this;
 }

 void invoke(){InvocationHostBoundary host;require(!owner,"No nested entry owner");owner=this;try{r_.invoke({entry});}catch(...){owner=nullptr;throw;}owner=nullptr;}
 void*direct(State*s,unsigned target){guard();require(s==&s_&&(target==0x5ac5c0||target==0x5ac5a0||target==0x5ac598)&&!events_.empty(),"Exact next required source helper");const auto&w=events_.back();const auto site=target==0x5ac5c0?0x5ac415U:target==0x5ac5a0?0x5ac431U:0x5ac440U,ret=target==0x5ac5c0?0x5ac41aU:target==0x5ac5a0?0x5ac436U:0x5ac445U;require(w.pc==site&&w.write==1&&w.width==4&&w.address==s_.gpr.rsp.dword&&w.value==ret&&r_.memory().load<unsigned>({w.address})==w.value,"True source direct CALL frame/return word");if(target==0x5ac5a0&&control_binding){if(control_binding->control==30)s_.x87.fxsave.cwd.flat^=0x100;if(control_binding->control==31){s_.x87.fxsave.swd.flat=1;r_.fx()[2]=std::byte{1};}if(control_binding->control==32){s_.x87.fxsave.ftw.flat=1;r_.fx()[4]=std::byte{1};}}r_.cpu()=cpu(s_);r_.cpu().esp+=4;r_.cpu().eip=w.pc;r_.call_direct({target},{w.value});project(s_,r_.cpu());return this;}
 void*returned(State*s,unsigned pc){guard();require(s==&s_&&pc==0x5ac41a&&s_.gpr.rip.dword==pc,"Only actual translated RET leaf return admitted");return this;}
 unsigned char undefined_flag(){guard();require(s_.gpr.rip.dword==0x5ac41f,"Only source TEST undefined AF site");undefined_sites_.push_back(s_.gpr.rip.dword);return 0;}
 const auto&undefined_sites()const{return undefined_sites_;}
 const auto&events()const{return events_;}const auto&data_routes()const{return data_routes_;}State&state(){return s_;}
};
}
extern "C" unsigned __remill_read_memory_32(void*p,unsigned a) noexcept(false) {if(mg::owner){if(p!=mg::owner||nt::owner||ci::owner||mn::owner)mg::owner->deny("Exact current mainargs read token",a);return mg::owner->read(a);}if(nt::owner){require(p==nt::owner&&!ci::owner&&!mn::owner,"Exact current initterm read token");return nt::owner->read(a);}if(ci::owner){require(p==ci::owner&&!mn::owner&&!nt::owner,"Exact current control memory token");return ci::owner->read32(a,true);}if(mn::owner){require(p==mn::owner,"Exact current matherr memory token");return mn::owner->read(a);}require(owner&&p==owner,"Exact active entry memory token");return owner->read(a,4);}
extern "C" unsigned char __remill_read_memory_8(void*p,unsigned a) noexcept(false) {if(mg::owner){if(p!=mg::owner||nt::owner||ci::owner||mn::owner)mg::owner->deny("Exact current mainargs byte-read token",a);mg::owner->deny("Required mainargs byte read outside bounded prefix",a);}throw std::runtime_error("Unreached required byte-read bridge");}
extern "C" void*__remill_write_memory_32(void*p,unsigned a,unsigned v) noexcept(false) {if(mg::owner){if(p!=mg::owner||nt::owner||ci::owner||mn::owner)mg::owner->deny("Exact current mainargs write token",a);mg::owner->write(a,v);return p;}if(nt::owner){require(p==nt::owner&&!ci::owner&&!mn::owner,"Exact current initterm write token");nt::owner->write(a,v);return p;}if(ci::owner){require(p==ci::owner&&!mn::owner&&!nt::owner,"Exact current control write token");ci::owner->write32(a,v);return p;}if(mn::owner){require(p==mn::owner,"Exact current matherr memory token");mn::owner->write(a,v);return p;}require(owner&&p==owner,"Exact active entry memory token");owner->write(a,v);return p;}
extern "C" void*__remill_function_call(State*s,unsigned a,void*p) noexcept(false) {if(mg::owner){if(p!=mg::owner||nt::owner||ci::owner||mn::owner)mg::owner->deny("Exact current mainargs import token",a,mg::import_call);mg::owner->called(s,a);}if(nt::owner){require(p==nt::owner&&!ci::owner&&!mn::owner,"Exact current initterm callback token");nt::owner->called(s,a);return p;}require(owner&&p==owner&&!ci::owner&&!mn::owner&&!nt::owner,"Exact active entry call token");return owner->call(s,a);}
extern "C" void*__remill_function_return(State*s,unsigned a,void*p) noexcept(false) {if(mg::owner){if(p!=mg::owner||nt::owner||ci::owner||mn::owner)mg::owner->deny("Exact current mainargs return token",a);mg::owner->deny("Required mainargs RET outside bounded prefix",a);}if(nt::owner){require(p==nt::owner&&!ci::owner&&!mn::owner,"Exact current initterm return token");nt::owner->returned(s,a);return p;}if(ci::owner){require(p==ci::owner&&!mn::owner&&!nt::owner,"Exact current control return token");ci::owner->returned(s,a);return p;}if(mn::owner){require(p==mn::owner,"Exact current matherr return token");mn::owner->returned(s,a);return p;}require(owner&&p==owner,"Exact active entry return token");return owner->returned(s,a);}
extern "C" void*__remill_jump(State*s,unsigned a,void*p) noexcept(false) {require(!mg::owner,"Other bridge cannot use active mainargs owner");if(nt::owner){require(p==nt::owner&&!ci::owner&&!mn::owner,"Exact current initterm jump token");nt::owner->tail(s,a);return p;}require(ci::owner&&p==ci::owner&&!mn::owner&&!nt::owner,"Exact current control jump token");ci::owner->tail(s,a);return p;}
extern "C" void*mw34_ci_enter(State*s,unsigned a,void*p) noexcept(false) {require(!mg::owner,"Other bridge cannot use active mainargs owner");require(ci::owner&&p==ci::owner&&!mn::owner&&!nt::owner,"Exact current control game-enter token");ci::owner->game_enter(s,a);return p;}
extern "C" void*mw34_cf_enter(State*s,unsigned a,void*p) noexcept(false) {require(!mg::owner,"Other bridge cannot use active mainargs owner");require(ci::owner&&p==ci::owner&&!mn::owner&&!nt::owner,"Exact current control provider-enter token");ci::owner->enter(s,a);return p;}
extern "C" void*mw34_cf_wait(State*s,unsigned a,void*p) noexcept(false) {require(!mg::owner,"Other bridge cannot use active mainargs owner");require(ci::owner&&p==ci::owner&&!mn::owner&&!nt::owner,"Exact current control wait token");ci::owner->wait(s,a);return p;}
extern "C" void*mw34_cf_store_cw(State*s,unsigned a,void*p) noexcept(false) {require(!mg::owner,"Other bridge cannot use active mainargs owner");require(ci::owner&&p==ci::owner&&!mn::owner&&!nt::owner,"Exact current control CW-store token");auto&c=*ci::owner;c.guard();if(!c.cw.store(s,{a}))c.deny("Required connected typed FNSTCW fault",a);c.access(a,c.memory.load<unsigned short>({a}),2,1);return p;}
extern "C" void*mw34_cf_load_cw(State*s,unsigned a,void*p) noexcept(false) {require(!mg::owner,"Other bridge cannot use active mainargs owner");require(ci::owner&&p==ci::owner&&!mn::owner&&!nt::owner,"Exact current control CW-load token");auto&c=*ci::owner;c.guard();const auto v=c.memory.load<unsigned short>({a});if(!c.cw.load(s,{a}))c.deny("Required connected typed FLDCW fault",a);c.access(a,v,2,0);return p;}
extern "C" void*mw34_crte_direct(State*s,unsigned a,void*p) noexcept(false) {require(!mg::owner,"Other bridge cannot use active mainargs owner");require(owner&&p==owner&&!ci::owner&&!mn::owner&&!nt::owner,"Exact active entry direct token");return owner->direct(s,a);}
extern "C" void*mw34_crte_enter(State*s,unsigned a,void*p) noexcept(false) {require(!mg::owner,"Other bridge cannot use active mainargs owner");if(nt::owner){require(p==nt::owner&&!ci::owner&&!mn::owner,"Exact current initterm thunk-enter token");nt::owner->enter(s,a);return p;}require(owner&&p==owner&&!ci::owner&&!mn::owner&&!nt::owner,"Exact active entry enter token");owner->guard();require(s==&owner->state()&&(a==entry||a==0x5ac5c0),"Only actual ordinary entry or literal RET leaf reached");return p;}
extern "C" unsigned char mw34_fdiv_entry_undefined_8() noexcept(false) {require(!mg::owner,"Other bridge cannot use active mainargs owner");require(owner,"Undefined representative needs active owner");return owner->undefined_flag();}

extern "C" unsigned char mw34_entry_initerm_undefined_8() noexcept(false){require(!mg::owner&&nt::owner&&!ci::owner&&!mn::owner,"Exact current initterm undefined owner");return nt::owner->undefined();}
namespace mw34::m4_crt {void compiled_initterm(m4_runtime::Runtime&r){::initterm_provider_adapter(r);}}
extern "C" void*sub_7800bbbc(State*s,unsigned a,void*p) noexcept(false){if(!mg::owner)throw std::runtime_error("Mainargs nested builder owner absent");if(p!=mg::owner||nt::owner||ci::owner||mn::owner)mg::owner->deny("Exact current mainargs nested builder token",a,mg::internal_call);mg::owner->nested(s,a,p);return p;}
extern "C" void*sub_7800b3b4(State*s,unsigned a,void*p) noexcept(false){if(!mg::owner)throw std::runtime_error("Mainargs wildcard owner absent");if(nt::owner||ci::owner||mn::owner)mg::owner->deny("Exact exclusive mainargs wildcard token",a,0x7800ba71);mg::owner->unsupported(s,a,p,0x7800ba71);}
extern "C" void*sub_7800bc48(State*s,unsigned a,void*p) noexcept(false){if(!mg::owner)throw std::runtime_error("Mainargs parser owner absent");if(nt::owner||ci::owner||mn::owner)mg::owner->deny("Exact exclusive mainargs parser token",a,0x7800bbf7);mg::owner->unsupported(s,a,p,0x7800bbf7);}
extern "C" void*sub_780012b3(State*s,unsigned a,void*p) noexcept(false){if(!mg::owner)throw std::runtime_error("Mainargs allocator owner absent");if(nt::owner||ci::owner||mn::owner)mg::owner->deny("Exact exclusive mainargs allocator token",a,0x7800bc06);mg::owner->unsupported(s,a,p,0x7800bc06);}
extern "C" void*sub_7800badb(State*s,unsigned a,void*p) noexcept(false){if(!mg::owner)throw std::runtime_error("Mainargs exit owner absent");if(nt::owner||ci::owner||mn::owner)mg::owner->deny("Exact exclusive mainargs exit token",a,0x7800bc16);mg::owner->unsupported(s,a,p,0x7800bc16);}
extern "C" unsigned char mw34_mainargs_normal_argv_undefined_8() noexcept(false){if(!mg::owner)throw std::runtime_error("Mainargs undefined owner absent");if(nt::owner||ci::owner||mn::owner)mg::owner->deny("Exact exclusive mainargs undefined owner");mg::owner->deny("Required argv TEST AF outside bounded prefix");}
#include "main_v2.inc"
