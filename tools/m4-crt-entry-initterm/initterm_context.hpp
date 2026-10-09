#pragma once
#include "runtime.hpp"
#include "admission.hpp"
#include <remill/Arch/X86/Runtime/State.h>
#include <array>
#include <thread>
namespace mw34::m4_crt_entry_initerm {
inline constexpr unsigned thunk=0x5ac598,slot=0x5bb510,entry=0x780014f8,return_pc=0x5ac445,begin=0x5e0248,end=0x5e024c;
extern "C" void*sub_5ac598(State*,unsigned,void*) noexcept(false);
extern "C" void*sub_780014f8(State*,unsigned,void*) noexcept(false);
struct Access{unsigned pc,address,value,width,write;};
struct Event{unsigned kind,pc,address,value;};
struct BridgeAbort{};struct Context;inline thread_local Context*owner{};
struct Context{
 m4_runtime::Runtime&runtime;State&state;unsigned raw{},frame{},ret{},first{},last{},access_count{},provider_step{},event_count{},boundary_depth{},fault_pc{},fault_address{};
 bool used{},active{},failed{},complete{},provider_complete{};const char*reason{};std::thread::id thread=std::this_thread::get_id();std::array<unsigned,4>nonvolatile{};
 std::array<Access,32>accesses{};std::array<Event,16>events{};std::vector<unsigned>undefined_sites;
 void(*test_before_execute)(Context&,unsigned){};void(*test_after_access)(Context&,unsigned){};void(*test_after_event)(Context&,unsigned){};
 explicit Context(m4_runtime::Runtime&r):runtime(r),state(*reinterpret_cast<State*>(r.remill_state().data())){
  if(r.domain()!=m4_runtime::Domain::admitted_game||!r.remill_seeded())throw std::invalid_argument("Exact admitted persistent initterm State required");
  unsigned matches{};for(const auto&i:r.image_metadata().imports)if(r.image_metadata().image_base+i.iat_rva==slot){if(i.library!="MSVCRT.dll"||!i.name||*i.name!="_initterm")throw std::invalid_argument("Actual unique initterm named owner");raw=i.original_iat_value;++matches;}
  if(matches!=1||r.memory().load<unsigned>({slot})!=raw)throw std::invalid_argument("Original unique initterm raw IAT required");
 }
 [[noreturn]]void deny(const char*w,unsigned address=0,unsigned pc=0){if(!failed){failed=true;reason=w;fault_pc=pc?pc:state.gpr.rip.dword;fault_address=address;}throw BridgeAbort{};}
 void guard(){if(owner!=this||!active||failed||thread!=std::this_thread::get_id())deny("Exact current active serial initterm owner required");}
 bool stack(unsigned a)const{return a>=0x20001000&&std::uint64_t(a)+4<=0x20002000;}
 std::array<unsigned,4>nonvol()const{return {state.gpr.rbx.dword,state.gpr.rbp.dword,state.gpr.rsi.dword,state.gpr.rdi.dword};}
 void source_identity(){std::array<std::byte,6>jump{};std::array<std::byte,28>code{};bool bad{};try{runtime.memory().read({thunk},jump);runtime.memory().read({entry},code);bad=m4::sha256(jump)!="86127a1a5240eff849fe402fc8517ae3ead7498476c8f17188afd36be6060947"||m4::sha256(code)!="960ed0d00b0200736930590a16fbb3caa9c3bc24af9851a3728258fd9b340678";}catch(...){bad=true;}if(bad)deny("Exact initterm thunk/provider source identity");}
 void event(unsigned kind,unsigned pc,unsigned address,unsigned value){if(event_count==events.size())deny("Initterm route bound");events[event_count++]={kind,pc,address,value};if(test_after_event)test_after_event(*this,event_count);}
 void access(unsigned a,unsigned value,unsigned write){if(access_count==accesses.size())deny("Initterm access bound",a);auto pc=state.gpr.rip.dword;if(pc!=thunk)++provider_step;accesses[access_count++]={pc,a,value,4,write};if(test_after_access)test_after_access(*this,access_count);}
 unsigned read(unsigned a){guard();const auto pc=state.gpr.rip.dword;
  if(!((pc==thunk&&a==slot)||(pc==0x780014f9&&a==state.gpr.rsp.dword+8&&stack(a))||(pc==0x78001502&&a==state.gpr.rsp.dword+12&&stack(a))||(pc==0x78001508&&a==begin)||(pc==0x78001512&&a==frame-4)||(pc==0x78001513&&a==frame)))deny("Required initterm read outside exact current source operand",a);
  unsigned v{};bool bad{};try{v=runtime.memory().load<unsigned>({a});}catch(...){bad=true;}if(bad)deny("Required checked initterm read fault",a);
  if(pc==0x78001513&&v!=ret)deny("Initterm actual return word changed",a);
  access(a,v,0);if(pc==0x78001508)event(v?7:4,pc,a,v);return v;
 }
 void write(unsigned a,unsigned v){guard();const auto pc=state.gpr.rip.dword;if(!((pc==entry&&a==frame-4&&v==nonvolatile[2])||(pc==0x7800150e&&a==state.gpr.rsp.dword-4&&v==0x78001510)))deny("Required initterm write outside actual PUSH/CALL",a);
  bool bad{};try{runtime.memory().store<unsigned>({a},v);}catch(...){bad=true;}if(bad)deny("Required checked initterm write fault",a);access(a,v,1);
 }
 void enter(State*s,unsigned pc){guard();if(s!=&state||pc!=thunk||state.gpr.rip.dword!=pc||state.addr.ds_base.dword||state.addr.ss_base.dword||state.addr.fs_base.dword!=runtime.fs_base().value)deny("Initterm thunk State/segment identity");source_identity();event(1,pc,frame,ret);}
 void tail(State*s,unsigned target);
 void returned(State*s,unsigned pc){guard();source_identity();if(s!=&state||pc!=ret||state.gpr.rip.dword!=ret||state.gpr.rsp.dword!=frame+4||nonvol()!=nonvolatile)deny("Actual initterm RET/nonvolatile/stack closure");provider_complete=true;event(5,pc,state.gpr.rsp.dword,ret);}
 void called(State*s,unsigned target){guard();if(s!=&state||state.gpr.rip.dword!=target||state.gpr.rsp.dword!=frame-8||runtime.memory().load<unsigned>({state.gpr.rsp.dword})!=0x78001510)deny("Actual initterm callback CALL frame changed",target,0x7800150e);deny("Required initterm callback remains unreviewed",target,0x7800150e);}
 unsigned char undefined(){guard();if(state.gpr.rip.dword!=0x7800150a)deny("Only initterm TEST AF representative admitted");undefined_sites.push_back(state.gpr.rip.dword);return 0;}
};
}
