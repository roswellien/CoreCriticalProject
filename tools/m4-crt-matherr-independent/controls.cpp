// Root causal harness: exact production Context/guest objects, own fixtures.
#include "paired_context.hpp"
#include <fstream>
#include <iostream>
#include <memory>
using namespace mw34;
namespace mn=mw34::m4_crt_matherr_paired_native;
namespace rt=mw34::m4_runtime;
namespace {
constexpr unsigned frame=0x200017fc,ret=0x5ac42e;
unsigned checks{},scenarios{},mode{};
std::vector<std::byte>game,code;
void check(bool b,const char*w){++checks;if(!b)throw std::runtime_error(std::string(w)+" [root scenario "+std::to_string(scenarios)+"]");}
std::vector<std::byte>read(const char*p){std::ifstream f(p,std::ios::binary);if(!f)throw std::runtime_error("Input absent");std::vector<char>v{std::istreambuf_iterator<char>(f),{}};std::vector<std::byte>b(v.size());std::memcpy(b.data(),v.data(),v.size());return b;}
template<class T>void put(std::byte*p,T v){std::memcpy(p,&v,sizeof(v));}
struct Host {
 struct alignas(16) FX{std::byte v[512];};FX before{},after{};std::array<std::byte,28>env{},afterenv{};
 Host(){__asm__ volatile("fxsave64 %0\n\tfnstenv %1":"=m"(before),"=m"(env)::"memory");restore();}
 void restore(){__asm__ volatile("fxrstor64 %0\n\tfldenv %1"::"m"(before),"m"(env):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)","xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");}
 void verify(){restore();__asm__ volatile("fxsave64 %0\n\tfnstenv %1":"=m"(after),"=m"(afterenv)::"memory");check(!std::memcmp(&before,&after,512)&&env==afterenv,"Full outer host FX/ENV restoration on success/fault");}
 ~Host(){restore();}
};
rt::Policy policy(){rt::Policy p;p.stack_low={0x20001000};p.stack_bytes=4096;p.heap_bytes=8192;return p;}
void hook(mn::Context&c,unsigned step){
 if(step!=4)return;
 if(mode==1)c.runtime.memory().protect({0x20001000},Permissions::none);
 if(mode==2)c.runtime.memory().store<unsigned>({frame},0x12345678);
 if(mode==3)c.state.gpr.rbx.dword^=1;
 if(mode==4)c.state.gpr.rax.dword^=1;
}
struct Fixture {
 rt::Runtime r;State&s;std::unique_ptr<mn::Context>c;unsigned arg;
 explicit Fixture(unsigned value=0xdeadbeef):r(rt::Runtime::from_admitted_image(game,policy())),s(*std::construct_at(reinterpret_cast<State*>(r.remill_state().data()))),arg(value){
  ++scenarios;auto raw=r.remill_state();for(unsigned i=0;i<3504;++i)raw[i]=std::byte((i*17+scenarios*3+41)&255);
  s.addr.ds_base.dword=s.addr.ss_base.dword=0;s.addr.fs_base.dword=r.fs_base().value;
  s.gpr.rax.dword=0x12345678;s.gpr.rcx.dword=0x89abcdef;s.gpr.rdx.dword=0x8badf00d;s.gpr.rbx.dword=0xcafebabe;s.gpr.rsp.dword=frame;s.gpr.rbp.dword=0x31a2b3c4;s.gpr.rsi.dword=0xa1b2c3d4;s.gpr.rdi.dword=0x7eadbeef;s.gpr.rip.dword=mn::entry;
  s.rflag.flat=0xad7;s.aflag.cf=1;s.aflag.pf=1;s.aflag.af=1;s.aflag.zf=1;s.aflag.sf=1;s.aflag.df=0;s.aflag.of=1;
  std::fill(r.fx().begin(),r.fx().end(),std::byte{});put<std::uint16_t>(r.fx().data(),0xa7f);put<std::uint16_t>(r.fx().data()+2,0x2825);r.fx()[4]=std::byte{0xff};put<unsigned>(r.fx().data()+24,0x1f80);put<unsigned>(r.fx().data()+28,0x2ffff);
  for(unsigned i=0;i<8;++i){put<std::uint64_t>(r.fx().data()+32+i*16,0x8000000000000000ULL+i*0x0101010101010101ULL);put<std::uint16_t>(r.fx().data()+40+i*16,static_cast<std::uint16_t>(0x3fff+i));}
  for(unsigned i=0;i<128;++i)r.fx()[160+i]=std::byte((i*19+3)&255);
  std::memcpy(&s.x87,r.fx().data(),512);s.x87.fxsave.fop=0x11d;s.x87.fxsave.ip=0x11223344;s.x87.fxsave.dp=0x55667788;s.x87.fxsave.cs.flat=0x23;s.x87.fxsave.ds.flat=0x2b;
  const std::pair<unsigned,unsigned>status[]={{2737,8},{2739,9},{2741,10},{2743,14},{2745,5},{2747,4},{2749,3},{2751,2},{2753,1},{2755,0},{2757,6}};
  for(auto[o,b]:status)raw[o]=std::byte((0x2825>>b)&1);
  for(unsigned i=0;i<8;++i){std::memcpy(&s.st.elems[i].val,r.fx().data()+32+i*16,10);std::memcpy(&s.vec[i],r.fx().data()+160+i*16,16);}
  r.mark_remill_seeded();r.memory().map({0x7800b000},4096,Permissions::read|Permissions::write);r.memory().write({mn::entry},code);r.memory().protect({0x7800b000},Permissions::read|Permissions::execute);
  for(unsigned a:{0x78039000U,0x7803b000U})r.memory().map({a},4096,Permissions::read|Permissions::write);
  for(unsigned a:{0x20001000U,0x78039000U,0x7803b000U}){std::array<std::byte,4096>page;page.fill(std::byte{0x5b});r.memory().write({a},page);}
  r.memory().store<unsigned>({frame},ret);r.memory().store<unsigned>({frame+4},arg);
  r.cpu()={0x12345678,0x89abcdef,0x8badf00d,0xcafebabe,frame+4,0x31a2b3c4,0xa1b2c3d4,0x7eadbeef,0xad7,0x5ac428};
  c=std::make_unique<mn::Context>(r);r.register_service({{c->slot},{rt::Abi::Cdecl,4,true},mn::adapter,"Root exact compiled matherr",rt::Domain::admitted_game,"2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7","72dabe5c1616590b1fe624844914b6d21fab26cf8eb8ddc3d430de98f50adce4"});r.freeze_registry();
 }
 auto state(){std::array<std::byte,3504>b;std::memcpy(b.data(),&s,3504);return b;}
 auto fx(){std::array<std::byte,512>b;std::memcpy(b.data(),r.fx().data(),512);return b;}
 auto memory(){std::array<std::byte,12288>b;unsigned i{};for(unsigned a:{0x20001000U,0x78039000U,0x7803b000U}){r.memory().read({a},std::span(b).subspan(i++*4096,4096));}return b;}
 bool call(unsigned return_pc=ret,bool owner=true){Host h;check(mn::owner==nullptr,"Root serial owner empty");mn::owner=owner?c.get():nullptr;bool denied{};try{r.call_import({c->slot},{return_pc});}catch(const std::exception&){denied=true;}mn::owner=nullptr;h.verify();return denied;}
 void resetframe(){r.cpu().esp=frame+4;r.cpu().eip=0x5ac428;}
 void imagewrite(unsigned addr,unsigned val){for(const auto&region:r.image_metadata().mapped_regions)if(addr>=region.start.value&&std::uint64_t{addr}+4<=std::uint64_t{region.start.value}+region.size){r.memory().protect(region.start,Permissions::read|Permissions::write);r.memory().store<unsigned>({addr},val);r.memory().protect(region.start,region.permissions);return;}throw std::runtime_error("Root image region absent");}
 void positive(){auto sb=state();auto fxb=fx();auto mem=memory();check(!call()&&!r.poisoned()&&c->used&&c->complete&&!c->failed&&!c->active,"Actual one complete compiled positive");
  auto sa=sb;put<unsigned>(sa.data()+2216,arg);put<unsigned>(sa.data()+2312,frame+4);put<unsigned>(sa.data()+2472,ret);for(auto[o,v]:std::initializer_list<std::pair<unsigned,unsigned>>{{2065,0},{2067,1},{2069,0},{2071,1},{2073,0},{2077,0}})sa[o]=std::byte(v);
  check(state()==sa,"Independent whole3504-byte source mutation model");put<unsigned>(mem.data()+4096+0x2b8,0);put<unsigned>(mem.data()+8192+0xc4,arg);check(memory()==mem,"Only two source DWORD writes across whole3pages");check(fx()==fxb,"Entire RuntimeFX/capability/live raw80 preserved");
  check(r.cpu().eax==arg&&r.cpu().esp==frame+4&&r.cpu().eip==ret&&r.cpu().eflags==((0xad7&~0x8d5U)|0x44U),"All source-defined/nativeAF0 CPU result");check(c->step==5&&r.calls().size()==1&&r.calls()[0].completed&&r.calls()[0].import,"Exactly one complete route/five actual accesses");
  const mn::Event ev[]={{frame+4,arg,4,0},{mn::zero_global,0x5b5b5b5b,4,0},{mn::zero_global,0,4,1},{mn::callback_global,arg,4,1},{frame,ret,4,0}};check(!std::memcmp(c->events.data(),ev,sizeof(ev)),"Actual ordered source events/values");
 }
 template<class Repair>void poisoned_retry(Repair repair){auto why=c->reason;auto pc=c->fault_pc;auto addr=c->fault_address;auto step=c->step;auto count=r.calls().size();repair();resetframe();auto sb=state();auto fxb=fx();check(call()&&r.poisoned(),"Repaired trigger cannot revive poisoned Runtime");check(state()==sb&&fx()==fxb&&r.calls().size()==count&&c->reason==why&&c->fault_pc==pc&&c->fault_address==addr&&c->step==step&&!c->active,"First error/progression/fullStateFX stable on retry");}
};
void run(){
 for(unsigned a:{0U,0x51e7b0U,0xffffffffU,0x10000001U,0x30000000U,0x7800b38fU,0x80000000U,0x12345678U}){Fixture f(a);f.positive();}
 for(unsigned scenario=0;scenario<13;++scenario){Fixture f;mode=0;
  if(scenario==0)f.r.memory().protect({0x20001000},Permissions::read);
  if(scenario==1)f.r.memory().protect({0x78039000},Permissions::read);
  if(scenario==2)f.r.memory().protect({0x7803b000},Permissions::read);
  if(scenario==3)f.r.memory().unmap({0x78039000});
  if(scenario==4)f.r.memory().unmap({0x7803b000});
  if(scenario==5){f.r.memory().unmap({0x20001000});f.r.memory().map({0x20001000},2048,Permissions::read|Permissions::write);f.r.memory().store<unsigned>({frame},ret);}
  if(scenario>=6&&scenario<=9){mode=scenario-5;f.c->test_after_event=&hook;}
  if(scenario==10){f.r.memory().protect({0x7800b000},Permissions::read|Permissions::write);f.r.memory().store<std::uint8_t>({mn::entry},0x90);}
  if(scenario==11)f.s.addr.fs_base.dword^=4;
  check(f.call(ret,scenario!=12)&&f.r.poisoned()&&!f.c->active&&mn::owner==nullptr,"Actual entered failure unwinds/poisons/releases owner");
  if(scenario>=1&&scenario<=9){check(f.c->used&&f.c->failed&&!f.c->complete,"Actual compiled first failure retained");unsigned expected=scenario==1?2:scenario==2||scenario==4?3:scenario==3?1:scenario==5?0:scenario<=7?4:5;check(f.c->step==expected,"Exact stopped access prefix");}
  if(scenario==1||scenario==3)check(f.c->fault_pc==0x7800b393&&f.c->fault_address==mn::zero_global,"Exact first AND read/write fault");
  if(scenario==2||scenario==4)check(f.c->fault_pc==0x7800b39a&&f.c->fault_address==mn::callback_global,"Exact callback store fault");
  if(scenario==5)check(f.c->fault_pc==mn::entry&&f.c->fault_address==frame+4,"Exact argument-read fault");
  if(scenario==6||scenario==7)check(f.c->fault_pc==0x7800b39f&&f.c->fault_address==frame,"Exact RET-read/frame fault");
  f.poisoned_retry([&]{for(unsigned a:{0x20001000U,0x78039000U,0x7803b000U}){try{f.r.memory().unmap({a});}catch(...){}f.r.memory().map({a},4096,Permissions::read|Permissions::write);}f.r.memory().protect({0x7800b000},Permissions::read|Permissions::write);f.r.memory().write({mn::entry},code);f.r.memory().protect({0x7800b000},Permissions::read|Permissions::execute);f.s.addr.fs_base.dword=f.r.fs_base().value;f.c->test_after_event=nullptr;mode=0;});
 }
 {Fixture f;f.imagewrite(f.c->slot,0);check(f.call()&&!f.r.poisoned()&&!f.c->used&&f.r.calls().empty(),"Pre-routing rawIAT denial does not enter/consume Context");f.imagewrite(f.c->slot,f.c->raw_iat);f.positive();}
 {Fixture f;check(f.call(0x12345678)&&!f.r.poisoned()&&!f.c->used&&f.r.calls().empty(),"Unadmitted return destination pre-routing denial");f.positive();}
 {Fixture f;f.positive();f.resetframe();check(f.call()&&f.r.poisoned()&&f.c->complete&&f.c->step==5,"Completed one-call owner cannot execute again");f.poisoned_retry([]{});}
}
}
int main(int argc,char**argv){try{check(argc==3,"Exact game/source inputs");game=read(argv[1]);code=read(argv[2]);check(game.size()==2384384&&m4::sha256(game)==m4::admitted_image_hash,"Exact game identity");check(code.size()==17&&m4::sha256(code)=="db28fc73ef336b9925b6cd56a37615599cc224d6a38cdd3b3cf5851c72e77bc9","Exact leaf source identity");run();std::cout<<checks<<" root compiled checks / "<<scenarios<<" scenarios passed\n";return 0;}catch(const std::exception&e){mn::owner=nullptr;std::cerr<<e.what()<<'\n';return 1;}}
