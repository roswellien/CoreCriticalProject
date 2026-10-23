"""Portable numeric adapter with physically unadmitted carried-input frontier."""
from pathlib import Path
import hashlib,json,shutil,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-startup142-runway/component-preparation-r1';assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h,str(p);pins[str(p)]=v;return p
 fixture=R/'reports/m4-hypot-native/fixture-preparation-r6';f=json.loads(pin(fixture/'report.json','7219937e27edf2960129466f6416bfe109bee5b03f4e702c103fa296d80db03a').read_bytes());source=pin(fixture/'fixture.cpp',f['files'][str((fixture/'fixture.cpp').resolve())]).read_text();start=source.index('static void native_root(Runtime &r) {');prefix=source[:start];code=prefix;deltas=[]
 def replace(old,new):
  nonlocal code
  assert code.count(old)==1,old[:100];code=code.replace(old,new);deltas.append(dict(old=old,new=new))
 replace('#include "fixture_spec.hpp"','#include "fixture_spec.hpp"\n#include "component.hpp"\n#include <exception>\n#include <memory>')
 i=code.index('static std::filesystem::path output;');j=code.index('struct Page {')
 replace(code[i:j],'''using NumericSink=mw34::m4_hypot_borrow::Sink;
static thread_local NumericSink current_sink{};
static thread_local void *current_sink_token{};
static void dump(const std::string &name,const void*p,std::size_t n){
 need(current_sink,"Actual borrowing numeric sink");
 current_sink(name,{static_cast<const std::byte*>(p),n},current_sink_token);
}
''')
 replace('DWORD thread = GetCurrentThreadId(); bool entered{}, complete{};','DWORD thread = GetCurrentThreadId(); bool entered{}, complete{}; unsigned outer_return{};')
 replace('s.gpr.rip.dword == Runtime::external_return && frames.size() == 1 && frames.back().ret == Runtime::external_return','s.gpr.rip.dword == outer_return && frames.size() == 1 && frames.back().ret == outer_return')
 replace('s.gpr.rsp.dword,s.gpr.rbp.dword,s.gpr.rsi.dword,s.gpr.rdi.dword,hf::initial_flags,s.gpr.rip.dword};','s.gpr.rsp.dword,s.gpr.rbp.dword,s.gpr.rsi.dword,s.gpr.rdi.dword,unsigned(s.rflag.flat),s.gpr.rip.dword};\n        need((c.eflags & ~0xcd5U)==(hf::initial_flags & ~0xcd5U),"Unproven carried non-arithmetic EFLAGS domain denied");')
 # DF remains part of finite admitted assumption, not a variable source flag.
 # Mask cd5 is CF/PF/AF/ZF/SF/OF only; DF10 must match source initial202.
 tail=r'''
namespace mw34::m4_hypot_borrow {
struct Component::Impl {
 Runtime&r;State&s;std::vector<Page>pages;Sink sink;void*token;unsigned sequence;bool attempted{};
 Impl(Runtime&runtime,std::span<const unsigned>addresses,unsigned seq,Sink out,void*p):r(runtime),s(*reinterpret_cast<State*>(runtime.remill_state().data())),sink(out),token(p),sequence(seq){
  need(sink&&seq<6&&r.domain()==Domain::admitted_game,"Exact finite numeric adapter binding");
  for(unsigned a:addresses){need((a&4095)==0,"Whole observation page address");Page q{};q.address=a;pages.push_back(q);}
 }
 void admit(){
  need(!attempted&&!active&&!r.poisoned(),"Unique live borrowed numeric root");
  // Closed by source, not a caller-supplied boolean or digest. A future immutable
  // derivative must bind independently proven actual carried-before input domain.
  need(Component::carried_domain_admitted(),"Carried142 numerical input/source/frame domain remains unproved");
  const auto&calls=r.calls();need(!calls.empty()&&!calls.back().completed&&calls.back().target.value==0x4b5910&&calls.back().return_pc.value==0x410a80,"Actual pending carried initializer CALL");
  need(r.remill_seeded()&&r.cpu().eip==0x4b5910&&r.cpu().esp==0x20001800&&s.gpr.rip.dword==0x4b5910&&s.gpr.rsp.dword==0x20001800,"Existing carried State and exact source entry frame");
  need(r.memory().load<unsigned>({r.cpu().esp})==calls.back().return_pc.value,"Whole committed current source return word");
  need(s.x87.fxsave.ftw.flat==0,"Measured normal empty source stack only");
  need(s.seg.cs.flat==0x23&&s.seg.ds.flat==0x2b&&s.seg.ss.flat==0x2b,"Finite original segment domain");
  need((unsigned(s.rflag.flat)&~0xcd5U)==(hf::initial_flags&~0xcd5U),"Exact original non-arithmetic EFLAGS domain");
  need(!std::memcmp(&s.x87,r.fx().data(),512),"Whole carried Runtime FX agrees with actual source State");
  const auto cw=s.x87.fxsave.cwd.flat;need(cw==((cw&0x1f3fU)|0x40U)&&(cw&63U)==63U,"Finite source-owned normalized masked CW");
 }
 void invoke(){
  Context c(r,pages,sequence);c.entered=true;c.outer_return=r.calls().back().return_pc.value;
  current_sink=sink;current_sink_token=token;
  struct Clear{~Clear(){current_sink=nullptr;current_sink_token=nullptr;}}clear;
  const auto cpu=c.cpu();need(!std::memcmp(&cpu,&r.cpu(),40),"Whole actual CPU40 projection agreement");
  c.frames.push_back({0x4b5910,cpu.esp,c.outer_return});c.checkpoint("before");
  Isolation hw(c.s.x87.fxsave.cwd.flat);void*result=c.dispatch(0x4b5910,false);hw.close();
  dump("host-before-FX.bin",hw.before.fx.data(),512);dump("host-after-FX.bin",hw.after.fx.data(),512);
  dump("host-before-ENV.bin",hw.before.env.data(),28);dump("host-after-ENV.bin",hw.after.env.data(),28);
  need(result==&c&&c.frames.empty()&&c.cursor==hf::accesses.size()&&c.API_count==2,"Complete finite native numeric closure");
  c.complete=true;r.cpu()=c.cpu();c.checkpoint("after");
  dump("accesses.bin",c.accesses.data(),c.accesses.size()*sizeof(Access));dump("APIs.bin",c.APIs.data(),sizeof(c.APIs));
 }
};
struct Task{Component::Impl*owner;std::exception_ptr error;};
extern "C" void mw34_hypot_borrow_hardware_call(void*,void*);
Component::Component(Runtime&r,std::span<const unsigned>pages,unsigned sequence,Sink sink,void*p):impl_(std::make_unique<Impl>(r,pages,sequence,sink,p)){}
Component::~Component()=default;
bool Component::carried_domain_admitted()noexcept{return false;}
void Component::borrow_entry(HostBoundary&boundary){impl_->admit();impl_->attempted=true;Task t{impl_.get(),{}};mw34_hypot_borrow_hardware_call(&t,boundary.bytes.data());if(t.error)std::rethrow_exception(t.error);}
}
extern "C" void mw34_hypot_borrow_invoke_guarded(void*p)noexcept{
 auto&t=*static_cast<mw34::m4_hypot_borrow::Task*>(p);try{t.owner->invoke();}catch(...){t.error=std::current_exception();}
}
'''
 header='''#pragma once
#include "runtime.hpp"
#include <array>
#include <memory>
#include <span>
#include <string_view>
namespace mw34::m4_hypot_borrow {
using Sink=void(*)(std::string_view,std::span<const std::byte>,void*);
struct alignas(16) HostBoundary{std::array<std::byte,1632>bytes{};};
class Component final{
public:struct Impl;
private:std::unique_ptr<Impl>impl_;
public:
Component(m4_runtime::Runtime&,std::span<const unsigned>observation_pages,unsigned source_domain_sequence,Sink,void*);
~Component();Component(const Component&)=delete;Component&operator=(const Component&)=delete;
static bool carried_domain_admitted()noexcept;
void borrow_entry(HostBoundary&);
};
}
'''
 restored=code
 for d in reversed(deltas):assert restored.count(d['new'])==1;restored=restored.replace(d['new'],d['old'])
 assert restored==prefix
 asm=pin(R/'tools/m4-hypot-native/hardware_boundary.s').read_text();newasm=asm.replace('hypot_hardware_call','mw34_hypot_borrow_hardware_call').replace('hypot_invoke_guarded','mw34_hypot_borrow_invoke_guarded');assert newasm.replace('mw34_hypot_borrow_hardware_call','hypot_hardware_call').replace('mw34_hypot_borrow_invoke_guarded','hypot_invoke_guarded')==asm
 # Standalone8 injection guards and entire typed numerical/cdecl/finalC1 body remain.
 assert all(('fire('+str(i)+')')in code for i in range(1,9))
 assert 'memset'not in tail and 'r.fx().data()'in tail and 'r.memory().write'not in tail
 out.mkdir(parents=True)
 for n in ['fixture_spec_O0.hpp','fixture_spec_O2.hpp','generated_bridges.inc','literal_dispatch.hpp','control_runtime.cpp']:
  q=pin(fixture/n,f['files'][str((fixture/n).resolve())]);shutil.copyfile(q,out/n)
 (out/'component.cpp').write_text(code+tail);(out/'component.hpp').write_text(header);(out/'hardware_boundary.s').write_text(newasm)
 (out/'source-inverse.json').write_text(json.dumps(dict(parent_source=str(fixture/'fixture.cpp'),parent_sha256=sha(fixture/'fixture.cpp'),prefix_sha256=hashlib.sha256(prefix.encode()).hexdigest(),exact_inverse_prefix=True,changes=deltas,removed_standalone_tail=source[start:],added_component_tail=tail,closed_frontier=True,hardware_changes='Two symbol substitutions only'),indent=2)+'\n')
 cmake='''cmake_minimum_required(VERSION 3.24)
project(HypotBorrow LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
configure_file("${CMAKE_CURRENT_SOURCE_DIR}/fixture_spec_${MW34_LEVEL}.hpp" "${CMAKE_CURRENT_BINARY_DIR}/fixture_spec.hpp" COPYONLY)
add_library(hypot-borrow STATIC component.cpp control_runtime.cpp ${MW34_OBJECTS} ${MW34_HARDWARE})
target_include_directories(hypot-borrow PRIVATE "${CMAKE_CURRENT_BINARY_DIR}" "${MW34_ROOT}/tools/m4-runtime" "${MW34_ROOT}/tools/m4-startup" "${MW34_ROOT}/runtime")
target_include_directories(hypot-borrow SYSTEM PRIVATE "${MW34_REMILL}")
'''
 (out/'CMakeLists.txt').write_text(cmake)
 objects={k:[x for x in v if Path(x).name!='hardware_boundary.obj']for k,v in f['objects'].items()};assert all(len(v)==21 for v in objects.values())
 for level,v in objects.items():
  for q in v:pin(q,f['files'][str(Path(q).resolve())])
 for q in out.iterdir():pin(q)
 pin(__file__);pin(sys.executable)
 report=dict(passed=True,scope='Compile-only portable borrowing numeric adapter; closed carried142 source-input admission frontier, no runnable registration or acceptance',source_parent=str(fixture/'report.json'),source_parent_sha256=sha(fixture/'report.json'),objects=objects,remill_include=f['remill_include'],exact_inverse_prefix=True,source_changes=len(deltas),all8_causal_injection_guards_retained=True,standalone_retry_controller_reused=False,carried_domain_admitted=False,caller_can_open_frontier=False,memory_or_State_or_FX_seed_present=False,native_executed=False,archive_reader_opened=False,initializer_credit=0,files=pins,remaining=['Independently prove actual141 carried-before source input/FP/EFLAGS/operand domain before fresh immutable frontier derivative','Whole-linked current adapter dependency/typed/ASM/TLS review and rootContext registration/current refusal retry integration','New142 carried original/source/whole-State/API/hardware and causal retry validation'])
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),passed=True)))
if __name__=='__main__':main()
