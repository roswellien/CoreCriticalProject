// Retain the actual frozen source adapters required by the 427 linked COFFs.
// This renamed inherited main is never called by the six-root fixture.
#define main mw34_widget_unused_inherited_main
#define need mw34_widget_unused_inherited_need
#include "inherited_main.cpp"
#undef need
#undef main
// Concrete caller-owned accepted registry route. No original observation pack.
#include "component.hpp"
#include "session.hpp"
#include "widget_bindings.hpp"
#include "admission.hpp"
#include "provider_pages.hpp"
#include <Windows.h>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <vector>
using namespace mw34;
namespace W=m4_widget_native;
namespace {
void need(bool v,const char*m){if(!v)throw std::runtime_error(m);}
std::vector<std::byte>read_file(const char*p){std::ifstream f(p,std::ios::binary|std::ios::ate);need(bool(f),"Whole physical input open");auto n=f.tellg();need(n>0&&n<64*1024*1024,"Bounded whole physical provider input");std::vector<std::byte>b(static_cast<std::size_t>(n));f.seekg(0);f.read(reinterpret_cast<char*>(b.data()),b.size());need(bool(f),"Complete physical input read");return b;}
struct Writer {std::filesystem::path out;std::string prefix;static void sink(std::string_view p,std::span<const std::byte>b,void*opaque){auto&w=*static_cast<Writer*>(opaque);auto f=w.out/(w.prefix+std::string(p));std::filesystem::create_directories(f.parent_path());std::ofstream stream(f,std::ios::binary);need(bool(stream),"Fresh bounded output path");stream.write(reinterpret_cast<const char*>(b.data()),b.size());need(bool(stream),"Complete bounded output");}void bytes(std::string_view p,const void*b,std::size_t n){sink(p,std::span(static_cast<const std::byte*>(b),n),this);}};
struct AcceptedServices final:W::Services {
 m4_runtime::Runtime&r;m4_onexit::Session&session;
 AcceptedServices(m4_runtime::Runtime&runtime,m4_onexit::Session&s):r(runtime),session(s){}
 m4_runtime::Runtime&runtime()noexcept override{return r;}
 void authority()override{const auto v=session.summary();need(&session.runtime()==&r&&v[1]&&!v[3]&&!v[4]&&session.live_handle(),"Actual live persistent accepted registry service context");}
 unsigned resolve_import(const W::Import&i)override{authority();need(i.pc==0x5ac11e&&i.slot==0x5bb52c&&i.raw==0x1decb0&&i.projected==0x78004a36,"Exact actual source onexit projection");return i.projected;}
 void invoke(State&s,const W::SourceCall&call)override{authority();need(call.site==0x5ac11e&&call.target==0x78004a36&&call.return_pc==0x5ac124&&!call.tail,"One admitted actual source onexit service");session.borrow_widget_onexit(s,call.root,call.frame,call.return_pc);authority();}
};
void initialize_current_caller(m4_runtime::Runtime&r){
 auto&s=*std::construct_at(reinterpret_cast<State*>(r.remill_state().data()));
 // Authored current external caller, shared for this entire seven-root sequence.
 // There is no original CPU/FX/State or per-root memory/FP projection input.
 s.addr.ds_base.dword=s.addr.es_base.dword=s.addr.ss_base.dword=0;s.addr.fs_base.dword=r.fs_base().value;s.seg.cs.flat=0x23;s.seg.ds.flat=s.seg.es.flat=s.seg.ss.flat=0x2b;
 r.cpu()={0,0,0,0,0x20001804,0,0,0,0x202,0x5ac3a0};s.gpr.rsp.dword=r.cpu().esp;s.gpr.rip.dword=r.cpu().eip;s.rflag.flat=0x202;
 s.x87.fxsave.cwd.flat=0x007f;s.x87.fxsave.swd.flat=0;s.x87.fxsave.mxcsr.flat=0x1f80;
 std::memcpy(r.fx().data(),&s.x87.fxsave,512);r.mark_remill_seeded();
}
void whole_current_game(m4_runtime::Runtime&r,Writer&w,std::string_view stem,bool require_provider=true){for(const auto&region:r.image_metadata().mapped_regions){std::vector<std::byte>b(static_cast<std::size_t>(region.size));r.memory().read(region.start,b);w.bytes(std::string(stem)+"/game-region-"+std::to_string(region.start.value)+".bin",b.data(),b.size());}std::array<std::byte,4096>stack{};r.memory().read({0x20001000},stack);w.bytes(std::string(stem)+"/stack.bin",stack.data(),stack.size());std::array<unsigned,5>tib{r.fs_base().value,r.fs_load32(0),r.fs_load32(4),r.fs_load32(8),r.fs_load32(0x18)};w.bytes(std::string(stem)+"/TIB.bin",tib.data(),sizeof(tib));w.bytes(std::string(stem)+"/State.bin",r.remill_state().data(),3504);w.bytes(std::string(stem)+"/CPU.bin",&r.cpu(),40);w.bytes(std::string(stem)+"/FX.bin",r.fx().data(),512);
 for(const auto&p:fps_provider_pages){std::array<std::byte,4096>page{};try{r.memory().read({p.address},page);}catch(const MemoryFault&e){if(e.reason()!=MemoryFaultReason::unmapped||require_provider)throw;continue;}w.bytes(std::string(stem)+"/provider-source-page-"+std::to_string(p.address)+".bin",page.data(),page.size());}
}
void map_current_formatter_sources(m4_runtime::Runtime&r,std::span<const std::byte>crt,Writer&w){
 need(m4::sha256(crt)==fps_crt_sha,"Exact whole owned physical CRT input");
 for(const auto&p:fps_provider_pages){need(p.file_offset+4096<=crt.size(),"Whole current physical provider source page");auto physical=crt.subspan(p.file_offset,4096);need(m4::sha256(physical)==p.sha256,"Exact current own provider page payload");std::array<std::byte,4096>before{};bool absent{};
  try{r.memory().read({p.address},before);}catch(const MemoryFault&e){if(e.reason()!=MemoryFaultReason::unmapped)throw;absent=true;}
  if(absent){r.memory().map({p.address},4096,Permissions::read|Permissions::write);r.memory().write({p.address},physical);r.memory().protect({p.address},static_cast<Permissions>(p.permissions));}
  else {std::array<std::byte,4096>after{};r.memory().read({p.address},after);need(before==after,"Existing whole provider state preserved during source admission");}
  std::array<std::byte,4096>current{};r.memory().read({p.address},current);if(absent)need(std::equal(current.begin(),current.end(),physical.begin()),"Complete physical source page map");
  const std::array<unsigned,6>row{1,p.address,p.file_offset,p.permissions,unsigned(absent),unsigned(!absent)};w.bytes("provider-mapping/page-"+std::to_string(p.address)+"-row.bin",row.data(),sizeof(row));w.bytes("provider-mapping/page-"+std::to_string(p.address)+"-physical.bin",physical.data(),physical.size());if(!absent)w.bytes("provider-mapping/page-"+std::to_string(p.address)+"-before.bin",before.data(),before.size());w.bytes("provider-mapping/page-"+std::to_string(p.address)+"-after.bin",current.data(),current.size());
 }
}
} // namespace
int main(int argc,char**argv){try{
 need(argc==7,"worker game CRT MFC MSVCP fresh-output independent-review-sha");const auto game=read_file(argv[1]),crt=read_file(argv[2]),mfc=read_file(argv[3]),msvcp=read_file(argv[4]);
 Writer writer{std::filesystem::path(argv[5]),{}};need(!std::filesystem::exists(writer.out),"Fresh widget output");std::filesystem::create_directories(writer.out);const std::string review=argv[6];need(review.size()==64,"Exact current independent prelaunch identity");
 auto r=m4_runtime::Runtime::from_admitted_image(game,[](){m4_runtime::Policy p;p.stack_low={0x20001000};p.stack_bytes=4096;return p;}());initialize_current_caller(r);
 for(const auto&b:widget_bindings){m4_runtime::Evidence evidence{m4_runtime::Domain::admitted_game,m4::admitted_image_hash,b.source_size,b.source_sha256,WIDGET_COMPONENT_LIBRARY_SHA,review};r.register_translation({{b.root},{m4_runtime::Abi::Cdecl,0,true},b.callback,"Literal widget constructor",std::move(evidence)});}r.freeze_registry();
 whole_current_game(r,writer,"initial-own-input",false);m4_onexit::Session registry(r,crt,mfc,msvcp);registry.bootstrap();map_current_formatter_sources(r,crt,writer);registry.dump(&Writer::sink,&writer);AcceptedServices services(r,registry);
 W::Inputs input;input.before_domain_gate_sha256=review;const std::array<unsigned,7>pcs{0x5a013c,0x5a063f,0x5a074b,0x517287,0x5ac11e,0x5ac580,0x5a2f68},slots{0x5bb070,0x5bb074,0x5bb068,0x5bb064,0x5bb52c,0x5bb530,0x5bb53c},targets{0x71f00010,0x71f00020,0x71f00030,0,0x78004a36,0,0x780230dd};for(unsigned k=0;k<7;++k){auto raw=r.memory().load<unsigned>({slots[k]});input.imports[k]={pcs[k],slots[k],raw,targets[k]?targets[k]:raw};}
 W::Component component(r,services,input,&Writer::sink,&writer);bool failed{};
 for(unsigned phase=0;phase<widget_bindings.size();++phase){writer.prefix="phase-"+std::to_string(phase)+"/";whole_current_game(r,writer,"before");W::HostBoundary hardware{};try{component.execute(widget_bindings[phase].root,hardware);}catch(const std::exception&e){writer.bytes("failure.bin",e.what(),std::strlen(e.what()));component.checkpoint("fault");failed=true;}writer.bytes("caller-hardware.bin",&hardware,sizeof(hardware));whole_current_game(r,writer,"after");if(failed)break;}
 writer.prefix="cleanup/";W::HostBoundary hardware{};component.cleanup_fonts(hardware);writer.bytes("font-caller-hardware.bin",&hardware,sizeof(hardware));registry.finish();registry.dump(&Writer::sink,&writer);whole_current_game(r,writer,"after");
 const std::array<unsigned,8>status{1,unsigned(!failed),7,58,unsigned(r.poisoned()),0,0,0};writer.bytes("status.bin",status.data(),sizeof(status));return failed?1:0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
