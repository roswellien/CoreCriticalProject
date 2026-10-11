#pragma once
// Admission interface only. The chronological input/owner implementation is
// supplied by a separately reviewed connected domain, never an isolated State.
#include "runtime.hpp"
#include <remill/Arch/X86/Runtime/State.h>
#include <algorithm>
#include <array>
#include <cstddef>
#include <stdexcept>
#include <thread>

namespace mw34::m4_mfc1168_connected {
using m4_runtime::Runtime;
inline constexpr unsigned root=0x5ae3e4,slot=0x5e0040;
inline void require(bool value,const char *reason){if(!value)throw std::runtime_error(reason);}

// The resource implementation must validate its full BEFORE graph, exact IAT
// projections, current TLS association and source operand order independently.
// This interface deliberately contains no original/native AFTER data and no
// whole-State input setter. A concrete implementation is not admitted yet.
class Invocation {
 public:
  virtual ~Invocation()=default;
  virtual Runtime &runtime()noexcept=0;
  virtual void authority()=0;
  virtual void execute_literal(State &,unsigned frame,unsigned return_pc)=0;
};
inline thread_local Invocation *active{};
class Borrow {
 Invocation &invocation_;std::thread::id thread_=std::this_thread::get_id();
 public:
  explicit Borrow(Invocation &invocation):invocation_(invocation){
   require(!active,"Serial connected MFC invocation authority required");
   invocation_.authority();active=&invocation_;
  }
  Borrow(const Borrow&)=delete;Borrow&operator=(const Borrow&)=delete;
  ~Borrow()noexcept{if(active==&invocation_)active=nullptr;}
  void check(){require(thread_==std::this_thread::get_id()&&active==&invocation_,"Current connected MFC borrowed authority");invocation_.authority();}
};
inline m4_runtime::Cpu32 cpu(const State&s){
 return {s.gpr.rax.dword,s.gpr.rcx.dword,s.gpr.rdx.dword,s.gpr.rbx.dword,
  s.gpr.rsp.dword,s.gpr.rbp.dword,s.gpr.rsi.dword,s.gpr.rdi.dword,
  static_cast<unsigned>((s.rflag.flat&~0xcd5ULL)|(s.aflag.cf<<0)|(s.aflag.pf<<2)|
   (s.aflag.af<<4)|(s.aflag.zf<<6)|(s.aflag.sf<<7)|(s.aflag.df<<10)|(s.aflag.of<<11)),s.gpr.rip.dword};
}
inline void project(State&s,const m4_runtime::Cpu32&c){
 s.gpr.rax.dword=c.eax;s.gpr.rcx.dword=c.ecx;s.gpr.rdx.dword=c.edx;s.gpr.rbx.dword=c.ebx;
 s.gpr.rsp.dword=c.esp;s.gpr.rbp.dword=c.ebp;s.gpr.rsi.dword=c.esi;s.gpr.rdi.dword=c.edi;
 s.gpr.rip.dword=c.eip;s.rflag.flat=c.eflags;
 s.aflag.cf=(c.eflags>>0)&1;s.aflag.pf=(c.eflags>>2)&1;s.aflag.af=(c.eflags>>4)&1;
 s.aflag.zf=(c.eflags>>6)&1;s.aflag.sf=(c.eflags>>7)&1;s.aflag.df=(c.eflags>>10)&1;s.aflag.of=(c.eflags>>11)&1;
}
// Explicit NativeEntry: this initializer registers no callback and therefore
// cannot be routed through the accepted registry Session::enter path.
inline void entry(Runtime&r){
 require(active&&&active->runtime()==&r&&r.domain()==m4_runtime::Domain::admitted_game&&r.remill_seeded(),"Admitted persistent MFC NativeEntry owner");
 active->authority();auto &s=*reinterpret_cast<State*>(r.remill_state().data());
 require(r.cpu().eip==root&&s.addr.ds_base.dword==0&&s.addr.ss_base.dword==0&&s.addr.fs_base.dword==r.fs_base().value,"Carried connected MFC source segment/entry identity");
 project(s,r.cpu());const auto frame=s.gpr.rsp.dword;
 require(frame==0x20001800,"Chronological connected root frame required");
 const auto ret=r.memory().load<unsigned>({frame});std::array<std::byte,512>fx{};
 std::copy(r.fx().begin(),r.fx().end(),fx.begin());
 active->execute_literal(s,frame,ret);active->authority();
 require(s.gpr.rsp.dword==frame+4&&s.gpr.rip.dword==ret,"Literal MFC root consumes its committed current Runtime return frame");
 require(std::equal(fx.begin(),fx.end(),r.fx().begin()),"Integer MFC source retains entire carried Runtime FX512");
 r.cpu()=cpu(s);
}
static_assert(sizeof(State)==3504&&sizeof(m4_runtime::Cpu32)==40);
} // namespace mw34::m4_mfc1168_connected
