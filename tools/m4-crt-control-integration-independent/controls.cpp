// Independent causal harness. No author fixture, observer, or executor imports.
#include "native_context.hpp"
#include <fstream>
#include <iostream>
#include <memory>
using namespace mw34;
namespace ci=mw34::m4_crt_control_integration;
namespace rt=mw34::m4_runtime;
namespace {
unsigned checks{},scenarios{};
std::vector<std::byte>game,pack;
void check(bool b,const char*w){if(!b)throw std::runtime_error(std::string(w)+" [independent scenario "+std::to_string(scenarios)+"]");++checks;}
std::vector<std::byte>read(const char*p){std::ifstream f(p,std::ios::binary);if(!f)throw std::runtime_error("Input open");std::vector<char>c{std::istreambuf_iterator<char>(f),{}};std::vector<std::byte>b(c.size());std::memcpy(b.data(),c.data(),c.size());return b;}
template<class T>T get(const std::byte*p){T v{};std::memcpy(&v,p,sizeof(v));return v;}
template<class T>void put(std::byte*p,T v){std::memcpy(p,&v,sizeof(v));}
rt::Policy policy(unsigned depth){rt::Policy p;p.stack_low=GuestAddress{0x20001000};p.stack_bytes=4096;p.heap_bytes=8192;p.max_call_depth=depth;return p;}
struct Host {
 struct alignas(16) FX{std::byte v[512];};FX before{},after{};std::array<std::byte,28>env{},env_after{};
 Host(){__asm__ volatile("fxsave64 %0\n\tfnstenv %1":"=m"(before),"=m"(env)::"memory");restore();}
 void restore(){__asm__ volatile("fxrstor64 %0\n\tfldenv %1"::"m"(before),"m"(env):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)","xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");}
 void restored_check(){restore();__asm__ volatile("fxsave64 %0\n\tfnstenv %1":"=m"(after),"=m"(env_after)::"memory");check(std::memcmp(&before,&after,512)==0&&env==env_after,"Explicit host restoration on success/fault");}
 ~Host(){restore();}
};
struct Fixture {
 rt::Runtime runtime;State&state;std::unique_ptr<ci::Context>context;
 explicit Fixture(unsigned esp=0x20001140,unsigned cw=0x37f,bool service=true,unsigned depth=64):runtime(rt::Runtime::from_admitted_image(game,policy(depth))),state(*std::construct_at(reinterpret_cast<State*>(runtime.remill_state().data()))){
  ++scenarios;auto raw=runtime.remill_state();for(unsigned i=0;i<raw.size();++i)raw[i]=std::byte((i*17+0x29)&255);
  state.addr.ds_base.dword=state.addr.ss_base.dword=0;state.addr.fs_base.dword=runtime.fs_base().value;
  ci::project_cpu(state,{0x12345678,0x89abcdef,0x8badf00d,0xcafebabe,esp,0x31a2b3c4,0xa1b2c3d4,0x7eadbeef,0xa17,ci::wrapper});
  std::memset(&state.sw,0,sizeof(state.sw));std::fill(runtime.fx().begin(),runtime.fx().end(),std::byte{});
  put<std::uint16_t>(runtime.fx().data(),static_cast<std::uint16_t>(cw));put<unsigned>(runtime.fx().data()+24,0x1f80);put<unsigned>(runtime.fx().data()+28,0xffff);
  for(unsigned i=0;i<8;++i){for(unsigned k=0;k<10;++k)runtime.fx()[32+16*i+k]=std::byte((i*13+k+7)&255);for(unsigned k=0;k<16;++k)runtime.fx()[160+16*i+k]=std::byte((i*19+k+23)&255);}
  std::memcpy(&state.x87,runtime.fx().data(),512);state.x87.fxsave.ip=0x5ace01;state.x87.fxsave.dp=0x608fd0;state.x87.fxsave.fop=0x123;state.x87.fxsave.cs.flat=0x23;state.x87.fxsave.ds.flat=0x2b;
  for(unsigned i=0;i<8;++i){std::memcpy(&state.st.elems[i].val,runtime.fx().data()+32+16*i,10);std::memcpy(&state.vec[i],runtime.fx().data()+160+16*i,16);}
  runtime.mark_remill_seeded();context=std::make_unique<ci::Context>(runtime,state);
  for(unsigned i=2;i<4;++i){unsigned offset=12+i*4104,base=get<unsigned>(pack.data()+offset);check(base==(i==2?0x78004000U:0x78011000U)&&get<unsigned>(pack.data()+offset+4)==1,"Actual declared provider page");runtime.memory().map(GuestAddress{base},4096,Permissions::read|Permissions::write);runtime.memory().write(GuestAddress{base},std::span(pack.data()+offset+8,4096));runtime.memory().protect(GuestAddress{base},Permissions::read|Permissions::execute);}
  std::array<std::byte,4096>stack;stack.fill(std::byte{0x6c});runtime.memory().write(GuestAddress{0x20001000},stack);
  if(esp>=0x20001000&&esp<=0x20001ffc)runtime.memory().store<unsigned>(GuestAddress{esp},ci::outer_return);
  runtime.register_translation({GuestAddress{ci::wrapper},{rt::Abi::Cdecl,0,true},ci::wrapper_adapter,"independent actual compiled wrapper",{rt::Domain::admitted_game,m4::admitted_image_hash,19,"ae1fa42ecf74ee2fb8a6076d57a6d7cb51e91890df3a0b0e839f8a4f4063f4ac",MW34_CONNECTED_ARTIFACT_SHA,"2ff6fb125e0abae0b125f0e00e430cf5e8e4a0ab3a22b1c1eb9fefcb65c8175a"}});
  if(service)runtime.register_service({GuestAddress{ci::slot},{rt::Abi::Cdecl,8,true},ci::provider_adapter,"MSVCRT.dll!_controlfp",rt::Domain::admitted_game,"2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7","b75abde48029efcdb8cb123c163c6bfb27a9b76dc62da014e620fca7c95bac56"});
  runtime.freeze_registry();runtime.cpu()=ci::cpu_view(state);runtime.cpu().esp+=4;runtime.cpu().eip=0x5ac431;
 }
 void protection(unsigned address,Permissions p){for(const auto&r:runtime.image_metadata().mapped_regions)if(address>=r.start.value&&std::uint64_t{address}<std::uint64_t{r.start.value}+r.size){runtime.memory().protect(r.start,p);return;}throw std::runtime_error("Mapping not found");}
 bool call(bool owned=true){Host host;auto*prior=ci::owner;check(prior==nullptr,"Independent serial boundary starts unowned");ci::owner=owned?context.get():nullptr;bool denied{};try{runtime.call_direct(GuestAddress{ci::wrapper},GuestAddress{ci::outer_return});}catch(const std::exception&){denied=true;}ci::owner=prior;host.restored_check();return denied;}
 void failure(const char*reason=nullptr,bool owned=true){const auto denied=call(owned);if(!denied||!runtime.poisoned()||runtime.calls().empty()||runtime.calls()[0].completed)std::cerr<<"Fault diagnostic: denied="<<denied<<" poisoned="<<runtime.poisoned()<<" calls="<<runtime.calls().size()<<" context_failed="<<context->failed<<" count="<<context->count<<" reason="<<(context->reason?context->reason:"none")<<'\n';check(denied&&runtime.poisoned()&&!runtime.calls().empty()&&!runtime.calls()[0].completed,"Actual compiled fault leaves incomplete poisoned outer route");check(context->boundary_depth==0||context->boundary_depth==4,"All entered setjmp boundaries unwound");if(reason)check(context->failed&&context->reason&&std::strcmp(context->reason,reason)==0,"Exact first fault retained");}
 template<class Repair>void repair_retry(Repair repair){auto count=context->count;auto depth=context->depth;auto why=context->reason;auto pc=context->fault_pc;repair();std::array<std::byte,3504>before;std::memcpy(before.data(),&state,3504);std::array<std::byte,512>fx;std::memcpy(fx.data(),runtime.fx().data(),512);check(call()&&context->count==count&&context->depth==depth&&context->reason==why&&context->fault_pc==pc,"Repairing trigger cannot revive poisoned Context/Runtime or overwrite first fault");check(std::memcmp(before.data(),&state,3504)==0&&std::memcmp(fx.data(),runtime.fx().data(),512)==0,"Poisoned retry leaves whole State/FX unchanged");}
};
void positives(){
 constexpr unsigned words[]{0x37f,0x27f,0x77f,0xa7f,0xf7f,0x67f};
 for(unsigned i=0;i<6;++i){Fixture f(i==0?0x20001080:i==1?0x20001ffc:0x20001141+4*i,words[i]);std::array<std::byte,3504>before;std::memcpy(before.data(),&f.state,3504);std::array<std::byte,512>fx;std::memcpy(fx.data(),f.runtime.fx().data(),512);const auto esp=f.state.gpr.rsp.dword;check(!f.call()&&!f.runtime.poisoned()&&!f.context->failed&&f.context->count==13&&f.context->depth==0,"Independent boundary/unaligned/CW positive actual route");check(f.runtime.calls().size()==2&&f.runtime.calls()[0].completed&&f.runtime.calls()[1].completed&&f.runtime.calls()[1].import,"Two real completed wrapper/import routes");check(f.state.gpr.rsp.dword==esp+4&&f.state.gpr.rip.dword==ci::outer_return&&f.runtime.memory().load<unsigned>(GuestAddress{esp-12})==ci::provider_return,"Actual CALL residue and CDECL cleanup");const auto new_cw=static_cast<std::uint16_t>((words[i]&~0x300U)|0x200U);check(f.state.x87.fxsave.cwd.flat==new_cw&&get<std::uint16_t>(f.runtime.fx().data())==new_cw,"Measured wrapper PC53 mask retains other incoming CW bits");put<std::uint16_t>(fx.data(),new_cw);check(std::memcmp(fx.data(),f.runtime.fx().data(),512)==0,"Whole software FX changes only CW");check(f.state.x87.fxsave.ip==0x5ace01&&f.state.x87.fxsave.dp==0x608fd0&&f.state.x87.fxsave.fop==0x123&&f.state.x87.fxsave.cs.flat==0x23&&f.state.x87.fxsave.ds.flat==0x2b,"Distinct nonzero legacy metadata persists despite zero FX metadata");check(before[3503]==reinterpret_cast<std::byte*>(&f.state)[3503]&&std::memcmp(before.data()+2480,reinterpret_cast<std::byte*>(&f.state)+2480,256)==0&&std::memcmp(before.data()+16,reinterpret_cast<std::byte*>(&f.state)+16,2048)==0,"Protected trailing State/logical raw80/SIMD regions persist");}
 // Native-only boundary observation: the frozen empty-state CW bridge does
 // not enforce all exception mask bits. This is outside the actual-original
 // twelve masked-CW corpus, so it grants no enlarged differential domain.
 {Fixture f(0x20001140,0x37e);check(!f.call()&&!f.runtime.poisoned()&&f.state.x87.fxsave.cwd.flat==0x27e,"Unmasked empty native-only positive retained without original equivalence credit");}
}
void negatives(){
 for(unsigned k=0;k<3;++k){Fixture f;auto&base=k==0?f.state.addr.fs_base:k==1?f.state.addr.ss_base:f.state.addr.ds_base;auto good=base.dword;base.dword^=4;f.failure("Connected persistent State/flat segments/guest FS identity rejected");f.repair_retry([&]{base.dword=good;});}
 for(unsigned k=0;k<9;++k){Fixture f;if(k==0)f.state.sw.de=1;if(k==1)f.state.x87.fxsave.swd.flat=1;if(k==2)f.state.x87.fxsave.ftw.flat=1;if(k==3)put<std::uint16_t>(f.runtime.fx().data()+2,1);if(k==4)f.runtime.fx()[4]=std::byte{1};if(k==5)put<unsigned>(f.runtime.fx().data()+24,0x1f00);if(k==6)f.state.x87.fxsave.mxcsr.flat=0x1f00;if(k==7)f.state.x87.fxsave.cwd.flat=0x27f;if(k==8){f.state.x87.fxsave.cwd.flat=0x3ff;put<std::uint16_t>(f.runtime.fx().data(),0x3ff);}f.failure();f.repair_retry([&]{std::memset(&f.state.sw,0,sizeof(f.state.sw));f.state.x87.fxsave.swd.flat=0;f.state.x87.fxsave.ftw.flat=0;f.state.x87.fxsave.cwd.flat=0x37f;f.state.x87.fxsave.mxcsr.flat=0x1f80;put<std::uint16_t>(f.runtime.fx().data(),0x37f);put<std::uint16_t>(f.runtime.fx().data()+2,0);f.runtime.fx()[4]=std::byte{};put<unsigned>(f.runtime.fx().data()+24,0x1f80);});}
 for(unsigned k=0;k<5;++k){Fixture f;const unsigned a=k==0?ci::wrapper:k==1?ci::thunk:k==2?0x5ac431:k==3?0x780042e1:0x7801129b;const unsigned b=k>=3?(a&~4095U):0;auto old=f.runtime.memory().load<std::uint8_t>(GuestAddress{a});if(k>=3)f.runtime.memory().protect(GuestAddress{b},Permissions::read|Permissions::write);else f.protection(a,Permissions::read|Permissions::write);f.runtime.memory().store<std::uint8_t>(GuestAddress{a},old^1);if(k>=3)f.runtime.memory().protect(GuestAddress{b},Permissions::read|Permissions::execute);else f.protection(a,Permissions::read|Permissions::execute);f.failure(k>=3?"Exact connected provider source identity changed":"Exact game wrapper/thunk/outer CALL source changed");f.repair_retry([&]{if(k>=3)f.runtime.memory().protect(GuestAddress{b},Permissions::read|Permissions::write);else f.protection(a,Permissions::read|Permissions::write);f.runtime.memory().store<std::uint8_t>(GuestAddress{a},old);if(k>=3)f.runtime.memory().protect(GuestAddress{b},Permissions::read|Permissions::execute);else f.protection(a,Permissions::read|Permissions::execute);});}
 {Fixture f;f.protection(ci::slot,Permissions::read|Permissions::write);f.runtime.memory().store<unsigned>(GuestAddress{ci::slot},0);f.protection(ci::slot,Permissions::read);f.failure("Actual import tail/raw-IAT/return-frame identity rejected");f.repair_retry([&]{f.protection(ci::slot,Permissions::read|Permissions::write);f.runtime.memory().store<unsigned>(GuestAddress{ci::slot},f.context->raw_iat);f.protection(ci::slot,Permissions::read);});}
 {Fixture f(0x20001140,0x37f,false);f.failure("Required typed control import route fault");f.repair_retry([]{});}
 {Fixture f(0x20001140,0x37f,true,1);f.failure("Required typed control import route fault");f.repair_retry([]{});}
 {Fixture f;f.failure(nullptr,false);f.repair_retry([]{});}
 {Fixture f;f.runtime.memory().protect(GuestAddress{0x20001000},Permissions::read);f.failure();f.repair_retry([&]{f.runtime.memory().protect(GuestAddress{0x20001000},Permissions::read|Permissions::write);});}
 {Fixture f(0x20001004);f.failure();f.repair_retry([&]{f.runtime.cpu().esp=0x20001144;});}
 {Fixture f;f.runtime.memory().protect(GuestAddress{0x78011000},Permissions::none);f.failure("Exact connected provider source identity changed");f.repair_retry([&]{f.runtime.memory().protect(GuestAddress{0x78011000},Permissions::read|Permissions::execute);});}
 {Fixture f;f.context->count=16;f.failure("Connected actual route ledger overflow");f.repair_retry([&]{f.context->count=16;});}
 {Fixture f;f.context->boundary_depth=4;f.failure();f.repair_retry([&]{f.context->boundary_depth=0;});}
}
}
int main(int argc,char**argv){try{check(argc==3,"Inputs: exact-game exact-pack");game=read(argv[1]);pack=read(argv[2]);check(game.size()==2384384&&m4::sha256(game)==m4::admitted_image_hash,"Exact game identity");check(pack.size()==16428&&m4::sha256(pack)=="135d7d7f8c41ba9a232f2cdc76fb673f9eb52e1939cf70111b3b59cbd6fd91d9","Exact source pack identity");positives();negatives();std::cout<<checks<<" independent compiled controls across "<<scenarios<<" scenarios passed\n";return 0;}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
