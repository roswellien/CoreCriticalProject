// Asset-free integration fixture for the actual authored stage include.
// Original lifted bodies and guest memory are mocked; this is not game proof.
#define NOMINMAX
#include <Windows.h>
#include <xmmintrin.h>
#include <array>
#include <bit>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>
#include "native-overrides/turret_aim_math.hpp"
namespace mw34::vkscene {
struct HostFpEnvironment {
 unsigned short cw;unsigned mx;
 HostFpEnvironment(){__asm__ volatile("fnstcw %0\n\tstmxcsr %1":"=m"(cw),"=m"(mx));const unsigned short c=0x27f;const unsigned m=0x1f80;__asm__ volatile("fnclex\n\tfldcw %0\n\tldmxcsr %1"::"m"(c),"m"(m));}
 ~HostFpEnvironment(){__asm__ volatile("fnclex\n\tfldcw %0\n\tldmxcsr %1"::"m"(cw),"m"(mx));}
};
}
struct State {
 struct {struct R{unsigned dword{};}rcx,rdx,rsp,rax,rbx;}gpr;
 struct {struct E{struct V{unsigned char data[10];}val;unsigned char padding[6];}elems[8];}st;
 unsigned sw{},sentinel{};
};
static void check(bool yes,const char*why){if(!yes)throw std::runtime_error(why);}
static unsigned bits(float x){return std::bit_cast<unsigned>(x);}
struct Fx {
 alignas(16) unsigned char data[512];
 void save(){__asm__ volatile("fxsave64 %0":"=m"(data)::"memory");}
 void restore(){__asm__ volatile("fxrstor64 %0"::"m"(data):"memory");}
};
static void same_environment(const Fx&a,const Fx&b){
 check(std::memcmp(a.data,b.data,24)==0,"host x87 control/status/environment changed");
 check(std::memcmp(a.data+24,b.data+24,4)==0,"host MXCSR changed");
}
struct MockStage {
 State state{};struct {unsigned frames=1;}host;
 std::vector<unsigned char>memory=std::vector<unsigned char>(0x800000);
 static constexpr unsigned actor=0x10000,node=0x20000,data=0x30000,matrix=data+0x30,sp=0x70000;
 std::vector<std::pair<unsigned,unsigned>>regions{{actor,0x300},{node,0xd4},{data,0x100},{sp,0x100},{0x72c52c,4},{0x63d340,8}};
 bool readable(unsigned a,unsigned n){for(auto [p,z]:regions)if(a>=p&&std::uint64_t(a)+n<=std::uint64_t(p)+z)return true;return false;}
 unsigned load(unsigned a){check(readable(a,4),"mock read outside mapped region");unsigned v;std::memcpy(&v,memory.data()+a,4);return v;}
 void store(unsigned a,unsigned v){check(readable(a,4),"mock write outside mapped region");std::memcpy(memory.data()+a,&v,4);}
 float wide_float(unsigned a){return std::bit_cast<float>(load(a));}
 #include "native-overrides/turret_aim_stage.inc"
 MockStage(){
  std::memset(&state,0xa5,sizeof state);state.gpr.rcx.dword=actor;state.gpr.rsp.dword=sp;
  store(actor,0x5c8770);store(actor+0xfc,node);store(actor+0x100,matrix);store(node+0x34,5);store(node+0x38,data);
  for(unsigned i=0;i<12;++i)store(matrix+4*i,bits(i==0||i==4||i==8?1.f:0.f));
  store(0x72c52c,bits(.005f));store(sp,0x4a729b);store(sp+4,bits(.015f));
 }
 template<class F>void scope(F&& f){state.gpr.rcx.dword=actor;turret_aim_body(&state,0x4a71c0,this,[&]()->void*{f();return this;});}
};
static auto top(float f){return mw34::turret_aim::encode_f32(f);}
static void lookup(MockStage&s,bool repaired,unsigned caller,float input,float returned,bool scoped=true){
 s.store(MockStage::sp,caller);s.store(MockStage::sp+4,bits(input));
 State expected{};bool ran=false;Fx afterOriginal{},afterHook{};DWORD originalError=0;
 auto invoke=[&]{s.state.gpr.rsp.dword=MockStage::sp;
  void* result=s.turret_aim_body(&s.state,0x523f70,&s,[&]()->void*{
   ran=true;s.store(0x63d340,bits(1.f));s.store(0x63d344,bits(float(std::exp(-1./51.))));
   auto v=top(returned);std::memcpy(s.state.st.elems[0].val.data,v.data(),10);
   s.state.gpr.rax.dword=0xdeadbeef;s.state.gpr.rbx.dword=0x12345678;s.state.gpr.rsp.dword+=8;s.state.sw=0xa732;s.state.sentinel=0xb00b;
   expected=s.state;const unsigned short c=0xb7f;const unsigned m=0x5fa5;__asm__ volatile("fnclex\n\tfldcw %0\n\tldmxcsr %1\n\tfldz\n\tfldz\n\tfdivp\n\tfstp %%st(0)"::"m"(c),"m"(m));
   ::SetLastError(0x123456);originalError=::GetLastError();afterOriginal.save();return &s;
  });afterHook.save();check(result==&s,"lookup changed body return pointer");check(::GetLastError()==originalError,"lookup changed LastError");
  check(std::memcmp(afterOriginal.data,afterHook.data,24)==0,"lookup changed x87 control/status/environment");
  check(std::memcmp(afterOriginal.data+24,afterHook.data+24,4)==0,"lookup changed MXCSR");
  if(repaired){auto r=mw34::turret_aim::first_interval(input,returned,1.f,s.wide_float(0x63d344));check(r.changed,"fixture expected repair");auto v=top(r.value);std::memcpy(expected.st.elems[0].val.data,v.data(),10);}
  check(ran&&std::memcmp(&expected,&s.state,sizeof expected)==0,"stage changed original callback outputs beyond ST0");
 };
 if(scoped)s.scope(invoke);else invoke();
}
static void publication(bool enabled){
 constexpr unsigned offsets[]{0,8,0x18,0x20};
 for(unsigned mode=0;mode<7;++mode){MockStage s;s.store(0x72c52c,bits(mode==1?.001f:0.f));
  const auto before=s.turret_aim_yaw(MockStage::matrix);bool called=false;
  s.scope([&]{
   for(unsigned i=0;i<4;++i)s.store(MockStage::matrix+offsets[i],i%2?0x80000000U:0);
   s.state.gpr.rcx.dword=mode==2?MockStage::node+4:MockStage::node;
   s.state.gpr.rdx.dword=mode==3?MockStage::matrix+4:MockStage::matrix;
   s.store(MockStage::sp,mode==4?0x4a7427:0x4a7426);
   if(mode==5)s.store(MockStage::actor+0xfc,MockStage::node+4);
   if(mode==6)s.store(MockStage::actor+0x100,MockStage::matrix+4);
   const auto baseline=s.memory;
   Fx beforePublish{},atCommit{};::SetLastError(0x6767);beforePublish.save();
   s.turret_aim_body(&s.state,0x4fc300,&s,[&]()->void*{
    atCommit.save();same_environment(beforePublish,atCommit);check(::GetLastError()==0x6767,"publish changed LastError before original commit");
    called=true;auto expected=baseline;
    if(enabled&&mode==0)for(unsigned i=0;i<4;++i)std::memcpy(expected.data()+MockStage::matrix+offsets[i],&before[i],4);
    check(expected==s.memory,"publication must restore only four words before original commit");
    s.store(MockStage::data,0x31);s.state.sw=0x1919;return &s;
   });check(s.load(MockStage::data)==0x31&&s.state.sw==0x1919,"original commit did not run");
  });check(called,"publication callback missing");check(!s.turret_aim_scope.actor,"scope leaked after publication");
 }
}
int main(int argc,char**argv){Fx initial;initial.save();const DWORD initialError=::GetLastError();try{
 check(argc==2,"expected on/off argument");const bool on=std::string(argv[1])=="on";
 MockStage s;check(s.turret_aim_on()==on,"fresh process repair environment mismatch");
 lookup(s,on,0x4a729b,.015f,1.f);
 lookup(s,false,0x4a729c,.015f,1.f);lookup(s,false,0x4a729b,.1f,.9f);
 lookup(s,false,0x4a729b,.1f,1.f);lookup(s,false,0x4a729b,.015f,.5f);
 lookup(s,false,0x4a729b,.015f,1.f,false);lookup(s,false,0x4a729b,0.f,1.f);
 MockStage invalid;invalid.store(MockStage::actor,0x1234);lookup(invalid,false,0x4a729b,.015f,1.f);
 MockStage wrongKind;wrongKind.store(MockStage::node+0x34,6);lookup(wrongKind,false,0x4a729b,.015f,1.f);
 MockStage wrongMatrix;wrongMatrix.store(MockStage::actor+0x100,MockStage::matrix+4);lookup(wrongMatrix,false,0x4a729b,.015f,1.f);
 publication(on);
 MockStage captured;Fx beforeCapture{},inOriginal{};::SetLastError(0x1818);beforeCapture.save();
 captured.scope([&]{inOriginal.save();same_environment(beforeCapture,inOriginal);check(::GetLastError()==0x1818,"scope capture changed LastError");});
 MockStage nested; nested.scope([&]{const auto outer=nested.turret_aim_scope;
  nested.state.gpr.rcx.dword=0;nested.turret_aim_body(&nested.state,0x4a71c0,&nested,[&]()->void*{check(!nested.turret_aim_scope.actor,"nested invalid scope inherited actor");return &nested;});
  check(nested.turret_aim_scope.actor==outer.actor,"nested scope not restored");
  try{nested.turret_aim_body(&nested.state,0x4a71c0,&nested,[&]()->void*{throw std::runtime_error("expected");});}catch(const std::runtime_error&){}
  check(nested.turret_aim_scope.actor==outer.actor,"throw did not restore outer scope");
 });check(!nested.turret_aim_scope.actor,"outer scope leaked");
 initial.restore();::SetLastError(initialError);std::cout<<"turret aim authored stage fixture "<<(on?"on":"off")<<" passed; original bodies mocked\n";return 0;
 }catch(const std::exception&e){initial.restore();::SetLastError(initialError);std::cerr<<e.what()<<'\n';return 1;}}
