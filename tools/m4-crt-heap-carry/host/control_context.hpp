#pragma once
#include "../../m4-crt-control-integration/common.hpp"
#include "runtime.hpp"
#include "guest_cw.hpp"
#include "admission.hpp"
#include <thread>
#include <cctype>
namespace mw34::m4_crt_control_integration {
struct Event{unsigned kind,pc,esp,return_pc;};
struct Frame{unsigned pc,esp,return_pc;std::array<unsigned,4>nonvol;};
struct Context;
inline thread_local Context*owner{};
extern "C" void*mw34_entry_control_sub_5ac5a0(State*,unsigned,void*) noexcept(false);
extern "C" void*sub_780042e1(State*,unsigned,void*) noexcept(false);
inline m4_runtime::Cpu32 cpu_view(const State&s){return {s.gpr.rax.dword,s.gpr.rcx.dword,s.gpr.rdx.dword,s.gpr.rbx.dword,s.gpr.rsp.dword,s.gpr.rbp.dword,s.gpr.rsi.dword,s.gpr.rdi.dword,static_cast<unsigned>((s.rflag.flat&~0xcd5ULL)|(s.aflag.cf<<0)|(s.aflag.pf<<2)|(s.aflag.af<<4)|(s.aflag.zf<<6)|(s.aflag.sf<<7)|(s.aflag.df<<10)|(s.aflag.of<<11)),s.gpr.rip.dword};}
inline void project_cpu(State&s,const m4_runtime::Cpu32&c){s.gpr.rax.dword=c.eax;s.gpr.rcx.dword=c.ecx;s.gpr.rdx.dword=c.edx;s.gpr.rbx.dword=c.ebx;s.gpr.rsp.dword=c.esp;s.gpr.rbp.dword=c.ebp;s.gpr.rsi.dword=c.esi;s.gpr.rdi.dword=c.edi;s.gpr.rip.dword=c.eip;s.rflag.flat=c.eflags;s.aflag.cf=(c.eflags>>0)&1;s.aflag.pf=(c.eflags>>2)&1;s.aflag.af=(c.eflags>>4)&1;s.aflag.zf=(c.eflags>>6)&1;s.aflag.sf=(c.eflags>>7)&1;s.aflag.df=(c.eflags>>10)&1;s.aflag.of=(c.eflags>>11)&1;}
struct BridgeAbort {};
struct Access{unsigned pc,address,value,width,write;};
struct Context{
 m4_runtime::Runtime&runtime;GuestMemory&memory;State&state;m4_guest_cw::Context cw;
 unsigned boundary_depth{};bool active{},failed{},complete{};const char*reason{};unsigned fault_pc{},fault_address{};std::thread::id thread=std::this_thread::get_id();
 std::array<Access,256>accesses{};unsigned access_count{};
 void(*test_before_execute)(Context&,unsigned){};void(*test_after_access)(Context&,unsigned){};void(*test_after_event)(Context&,unsigned){};
 std::array<Frame,8>frames{};unsigned depth{};std::array<Event,16>events{};unsigned count{};unsigned raw_iat{};
 Context(m4_runtime::Runtime&r,State&s):runtime(r),memory(r.memory()),state(s),cw(memory,s,r.fx(),GuestAddress{0x20001000},4096){
  if(r.domain()!=m4_runtime::Domain::admitted_game||reinterpret_cast<std::byte*>(&s)!=r.remill_state().data()||!r.remill_seeded())throw std::invalid_argument("Exact seeded persistent admitted Runtime State required");
  unsigned matches{};for(const auto&i:r.image_metadata().imports)if(r.image_metadata().image_base+i.iat_rva==slot){auto library=i.library;std::transform(library.begin(),library.end(),library.begin(),[](unsigned char c){return static_cast<char>(std::tolower(c));});if(library!="msvcrt.dll"||!i.name||*i.name!="_controlfp")throw std::invalid_argument("Exact unique named control import owner required");raw_iat=i.original_iat_value;++matches;}if(matches!=1||memory.load<unsigned>(GuestAddress{slot})!=raw_iat)throw std::invalid_argument("Original named control IAT identity required");
 }
 [[noreturn]]void deny(const char*w,unsigned address=0){if(!failed){failed=true;reason=w;fault_pc=state.gpr.rip.dword;fault_address=address;}throw BridgeAbort{};}
 void guard(){if(owner!=this||!active||failed||thread!=std::this_thread::get_id())deny("Exact active serial control owner required");}
 void access(unsigned address,unsigned value,unsigned width,unsigned write){guard();if(access_count==accesses.size())deny("Control access bound",address);accesses[access_count++]={state.gpr.rip.dword,address,value,width,write};if(test_after_access)test_after_access(*this,access_count);}
 bool stack(unsigned a,unsigned bytes)const{return a>=0x20001000&&std::uint64_t{a}+bytes<=0x20002000;}
 unsigned read32(unsigned a,bool observed=false){guard();if(a!=slot&&!stack(a,4))deny("Required checked read outside owned stack/named IAT");unsigned v{};bool bad{};try{v=memory.load<unsigned>(GuestAddress{a});}catch(...){bad=true;}if(bad)deny("Required checked32-bit read fault",a);if(observed)access(a,v,4,0);return v;}
 void write32(unsigned a,unsigned v){guard();if(!stack(a,4))deny("Required checked write outside owned stack");bool bad{};try{memory.store<unsigned>(GuestAddress{a},v);}catch(...){bad=true;}if(bad)deny("Required checked32-bit write fault",a);access(a,v,4,1);}
 std::array<unsigned,4>nonvol()const{return {state.gpr.rbx.dword,state.gpr.rbp.dword,state.gpr.rsi.dword,state.gpr.rdi.dword};}
 void event(unsigned kind,unsigned pc,unsigned esp,unsigned ret){if(count==events.size())deny("Connected actual route ledger overflow");events[count++]={kind,pc,esp,ret};if(test_after_event)test_after_event(*this,count);}
 void state_identity(State*s,unsigned pc){guard();if(s!=&state||pc!=state.gpr.rip.dword||state.addr.ds_base.dword||state.addr.ss_base.dword||state.addr.fs_base.dword!=runtime.fs_base().value)deny("Connected persistent State/flat segments/guest FS identity rejected");}
 void provider_identity(){bool bad{};try{std::vector<std::byte>hot(303),cold(125);memory.read(GuestAddress{0x780042e1},hot);memory.read(GuestAddress{0x7801129b},cold);bad=m4::sha256(hot)!="adf05ce99957b1a9d6c33dce1dda80a595cda795085d2794935bb4d78a46f47b"||m4::sha256(cold)!="b48e01a7f8be0f6c5f477cb30911f7dc92adcca417894943587560507db19b88";}catch(...){bad=true;}if(bad)deny("Exact connected provider source identity changed");}
 void game_enter(State*s,unsigned pc){state_identity(s,pc);const auto esp=state.gpr.rsp.dword;const auto ret=read32(esp);if(pc==wrapper){if(depth||ret!=outer_return||runtime.cpu().eip!=wrapper||runtime.cpu().esp!=esp)deny("Unadmitted real outer wrapper frame");frames[depth++]={pc,esp,ret,nonvol()};event(1,pc,esp,ret);}else if(pc==thunk){if(depth!=1||esp!=frames[0].esp-12||ret!=provider_return||read32(esp+4)!=0x10000||read32(esp+8)!=0x30000)deny("Actual wrapper CALL/arguments/thunk frame rejected");event(3,pc,esp,ret);}else deny("Unknown game entry");}
 void enter(State*s,unsigned pc){state_identity(s,pc);provider_identity();if(depth==frames.size())deny("Connected provider frame bound");auto esp=state.gpr.rsp.dword,ret=read32(esp);unsigned callsite{};
  if(pc==provider_entry&&depth==1){if(frames[0].pc!=wrapper||ret!=provider_return||esp!=frames[0].esp-12)deny("Actual typed provider frame rejected");callsite=0x5ac5aa;}
  else{if(!depth)deny("Provider execution lacks game owner");if(pc==0x780042f7&&frames[depth-1].pc==provider_entry)callsite=0x780042ef;if(pc==0x7800432c&&frames[depth-1].pc==0x780042f7)callsite=0x78004303;if(pc==0x7800439f&&frames[depth-1].pc==0x780042f7)callsite=0x7800431a;if(!callsite||ret!=callsite+5)deny("Unadmitted connected provider CALL/return");}
  std::array<std::byte,5>code{};bool bad{};try{memory.read(GuestAddress{callsite},code);}catch(...){bad=true;}if(bad||code[0]!=std::byte{0xe8})deny("Actual connected CALL source fault");int delta{};std::memcpy(&delta,code.data()+1,4);if(callsite+5+static_cast<unsigned>(delta)!=(pc==provider_entry?thunk:pc))deny("Actual connected CALL target changed");frames[depth++]={pc,esp,ret,nonvol()};event(1,pc,esp,ret);
 }
 void returned(State*s,unsigned pc){state_identity(s,pc);provider_identity();if(!depth)deny("Connected return has no frame");const auto f=frames[depth-1];if(pc!=f.return_pc||state.gpr.rsp.dword!=f.esp+4||nonvol()!=f.nonvol)deny("Actual connected RET/nonvolatile/cleanup rejected");--depth;event(2,pc,state.gpr.rsp.dword,f.return_pc);}
 void wait(State*s,unsigned pc){guard();const auto&f=state.x87.fxsave;const auto&sw=state.sw;if(s!=&state||pc!=0x780042fc||f.swd.flat||f.ftw.flat||sw.ie||sw.de||sw.ze||sw.oe||sw.ue||sw.pe||sw.sf||sw.c0||sw.c1||sw.c2||sw.c3)deny("Unsupported connected FWAIT pending/nonempty state");}
 void execute(unsigned entry){
  const bool outer=boundary_depth==0;if((entry!=wrapper&&entry!=provider_entry)||failed||boundary_depth==4||thread!=std::this_thread::get_id()||owner!=this||(outer?active:!active))throw std::runtime_error(reason?reason:"Connected boundary admission rejected");
  ++boundary_depth;if(outer)active=true;
  try{if(test_before_execute)test_before_execute(*this,entry);void*result=(entry==wrapper?mw34_entry_control_sub_5ac5a0:sub_780042e1)(&state,entry,this);if(result!=this)deny("Connected compiled entry result identity rejected");}
  catch(BridgeAbort const&){--boundary_depth;if(outer)active=false;throw std::runtime_error(reason);}
  catch(...){--boundary_depth;if(outer)active=false;throw;}
  --boundary_depth;if(outer){active=false;complete=!failed&&depth==0;}if(failed)throw std::runtime_error(reason);
 }

 void tail(State*s,unsigned pc){state_identity(s,pc);if(depth!=1||pc!=raw_iat||read32(slot)!=raw_iat||read32(state.gpr.rsp.dword)!=provider_return||state.gpr.rsp.dword!=frames[0].esp-12)deny("Actual import tail/raw-IAT/return-frame identity rejected");
  bool bad{};try{std::vector<std::byte>code(19),jump(6),outer(5);memory.read(GuestAddress{wrapper},code);memory.read(GuestAddress{thunk},jump);memory.read(GuestAddress{0x5ac431},outer);if(m4::sha256(code)!="ae1fa42ecf74ee2fb8a6076d57a6d7cb51e91890df3a0b0e839f8a4f4063f4ac"||m4::sha256(jump)!="cd4225ce0b49983d72e298fad14f78fed9e8bfdc3042de603871ce08a29e3646"||m4::sha256(outer)!="f8b21f68d2277b61d744273c7c041f160b18ea4ada0625df395fc2053d33b3de")bad=true;}catch(...){bad=true;}if(bad)deny("Exact game wrapper/thunk/outer CALL source changed");
  const auto frame_sp=state.gpr.rsp.dword;event(4,pc,frame_sp,provider_return);
  // The actual compiled CALL already wrote this word. r9's caller-ESP
  // convention rewrites the SAME word at the SAME address; State remains at
  // the real pushed frame. This is orchestration, not a second guest CALL.
  runtime.cpu()=cpu_view(state);runtime.cpu().esp=frame_sp+4;runtime.cpu().eip=0x5ac5aa;
  bool routing_failed{};try{runtime.call_import(GuestAddress{slot},GuestAddress{provider_return});}catch(...){routing_failed=true;}if(routing_failed)deny("Required typed control import route fault");
  if(depth!=1||runtime.cpu().eip!=provider_return||runtime.cpu().esp!=frame_sp+4||state.gpr.rip.dword!=provider_return||state.gpr.rsp.dword!=frame_sp+4||read32(frame_sp)!=provider_return)deny("Typed import actual return/frame closure rejected");event(5,provider_return,state.gpr.rsp.dword,provider_return);
 }
};
inline void wrapper_adapter(m4_runtime::Runtime&r){if(!owner||&owner->runtime!=&r)throw std::runtime_error("Stable serial connected Context owner required");project_cpu(owner->state,r.cpu());owner->execute(wrapper);if(owner->depth)throw std::runtime_error("Actual outer wrapper frame incomplete");r.cpu()=cpu_view(owner->state);}
inline void provider_adapter(m4_runtime::Runtime&r){if(!owner||&owner->runtime!=&r||owner->depth!=1)throw std::runtime_error("Actual import provider lacks stable wrapper owner");owner->state.gpr.rip.dword=provider_entry;owner->execute(provider_entry);if(owner->depth!=1)throw std::runtime_error("Actual typed provider frame incomplete");r.cpu()=cpu_view(owner->state);}
}
