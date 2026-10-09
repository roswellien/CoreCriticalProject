#pragma once
#include "guest_cw.hpp"
#include "common.hpp"
#include <array>
#include <csetjmp>
#include <cstring>
namespace mw34::m4_crt_control {
struct Event{std::uint32_t kind,pc,esp,return_pc;};
struct Frame{std::uint32_t pc,esp,return_pc;std::array<std::uint32_t,4>nonvol;};
struct Context{
 GuestMemory&memory;State&state;std::array<std::byte,512>&fx;m4_guest_cw::Context cw;
 std::jmp_buf boundary{};bool failed{};const char*reason{};std::array<Frame,4>frames{};unsigned depth{};std::array<Event,8>events{};unsigned count{};
 Context(GuestMemory&m,State&s,std::array<std::byte,512>&f):memory(m),state(s),fx(f),cw(m,s,f,GuestAddress{0x20001000},4096){}
 [[noreturn]]void deny(const char*why){failed=true;reason=why;std::longjmp(boundary,1);}
 std::uint32_t read32(std::uint32_t a){std::uint32_t v{};bool bad{};try{v=memory.load<std::uint32_t>(GuestAddress{a});}catch(...){bad=true;}if(bad)deny("Required checked32-bit read fault");return v;}
 void write32(std::uint32_t a,std::uint32_t v){bool bad{};try{memory.store<std::uint32_t>(GuestAddress{a},v);}catch(...){bad=true;}if(bad)deny("Required checked32-bit write fault");}
 std::array<std::uint32_t,4> nonvol()const{return {state.gpr.rbx.dword,state.gpr.rbp.dword,state.gpr.rsi.dword,state.gpr.rdi.dword};}
 void event(unsigned kind,unsigned pc,unsigned esp,unsigned ret){if(count==events.size())deny("Actual route ledger overflow");events[count++]={kind,pc,esp,ret};}
 void enter(State*s,unsigned pc){
  if(s!=&state||pc!=state.gpr.rip.dword||depth==frames.size())deny("Wrong persistent State or actual entry route");auto esp=state.gpr.rsp.dword;auto ret=read32(esp);
  if(!depth){if((pc!=entries[0]&&pc!=entries[1])||esp!=0x20001800||ret!=0x10000100)deny("Unadmitted actual outer provider route");}
  else{
   unsigned callsite{};if(pc==0x780042f7&&frames[depth-1].pc==0x780042e1)callsite=0x780042ef;
   if(pc==0x7800432c&&frames[depth-1].pc==0x780042f7)callsite=0x78004303;
   if(pc==0x7800439f&&frames[depth-1].pc==0x780042f7)callsite=0x7800431a;
   if(!callsite||ret!=callsite+5)deny("Unadmitted original CALL/return pair");std::array<std::byte,5>code{};bool bad{};try{memory.read(GuestAddress{callsite},code);}catch(...){bad=true;}if(bad||code[0]!=std::byte{0xe8})deny("Actual CALL source admission failed");std::int32_t delta{};std::memcpy(&delta,code.data()+1,4);if((callsite+5+static_cast<unsigned>(delta))!=pc)deny("Actual direct CALL target rejected");
  }
  frames[depth++]={pc,esp,ret,nonvol()};event(1,pc,esp,ret);
 }
 void returned(State*s,unsigned pc){if(s!=&state||!depth)deny("Required return State/frame missing");auto f=frames[depth-1];if(pc!=f.return_pc||state.gpr.rip.dword!=f.return_pc||state.gpr.rsp.dword!=f.esp+4||nonvol()!=f.nonvol)deny("Actual RET/nonvolatile/cleanup contract rejected");--depth;event(2,pc,state.gpr.rsp.dword,f.return_pc);}
 void wait(State*s,unsigned pc){const auto&f=state.x87.fxsave;const auto&sw=state.sw;if(s!=&state||pc!=0x780042fc||f.swd.flat||f.ftw.flat||sw.ie||sw.de||sw.ze||sw.oe||sw.ue||sw.pe||sw.sf||sw.c0||sw.c1||sw.c2||sw.c3)deny("Unsupported guest FWAIT pending/nonempty state");}
};
}
extern "C" std::uint32_t __remill_read_memory_32(void*p,std::uint32_t a){return static_cast<mw34::m4_crt_control::Context*>(p)->read32(a);}
extern "C" void*__remill_write_memory_32(void*p,std::uint32_t a,std::uint32_t v){static_cast<mw34::m4_crt_control::Context*>(p)->write32(a,v);return p;}
extern "C" void*__remill_function_return(State*s,std::uint32_t pc,void*p){static_cast<mw34::m4_crt_control::Context*>(p)->returned(s,pc);return p;}
extern "C" void*mw34_cf_enter(State*s,std::uint32_t pc,void*p){static_cast<mw34::m4_crt_control::Context*>(p)->enter(s,pc);return p;}
extern "C" void*mw34_cf_wait(State*s,std::uint32_t pc,void*p){static_cast<mw34::m4_crt_control::Context*>(p)->wait(s,pc);return p;}
extern "C" void*mw34_cf_store_cw(State*s,std::uint32_t a,void*p){auto*c=static_cast<mw34::m4_crt_control::Context*>(p);if(!c->cw.store(s,mw34::GuestAddress{a}))c->deny("Required typed FNSTCW fault");return p;}
extern "C" void*mw34_cf_load_cw(State*s,std::uint32_t a,void*p){auto*c=static_cast<mw34::m4_crt_control::Context*>(p);if(!c->cw.load(s,mw34::GuestAddress{a}))c->deny("Required typed FLDCW fault");return p;}
