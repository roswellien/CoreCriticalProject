// Authored local x64 x87 unit probe. No original process, DLL or game code runs.
#include "protocol.hpp"
#include "corpus.hpp"
#include <array>
namespace old=mw34::m4_numeric_max;
struct alignas(16) Fx{std::array<std::uint8_t,512>b{};};
#pragma pack(push,1)
struct Row{
 std::uint32_t repeat,input,cw,top,depth,sticky,c1,result,host_restored;
 std::array<std::uint8_t,512>before,loaded,stored,host_before,host_after;
 std::array<std::uint8_t,28>env_before,env_loaded,env_stored,host_env_before,host_env_after;
};
#pragma pack(pop)
static_assert(sizeof(Row)==2736);
static Row probe(unsigned rep,unsigned inp,unsigned cw,unsigned top,unsigned depth,unsigned sticky,unsigned c1){
 Row r{};r.repeat=rep;r.input=inp;r.cw=cw;r.top=top;r.depth=depth;r.sticky=sticky;r.c1=c1;
 Fx seed{},before{},loaded{},stored{},host_before{},host_after{};std::array<std::uint8_t,28>seed_env{},eb{},el{},es{},host_env{},host_env_after{};
 old::seed(cw,top,depth,0,seed.b.data(),seed_env.data());const std::uint16_t sw=static_cast<std::uint16_t>((top<<11)|sticky|(c1<<9));std::memcpy(seed.b.data()+2,&sw,2);const unsigned env_sw=0xffff0000U|sw;std::memcpy(seed_env.data()+4,&env_sw,4);
 const unsigned input=old::inputs[inp];unsigned output=0;
 // Every numeric operation and checkpoint remains in this single compiler
 // barrier. Checkpoints do not insert a numeric stack operation.
 __asm__ volatile(
  "fxsave64 %[hb]\n\tfnstenv %[he]\n\t"
  "fxrstor64 %[seed]\n\tfldenv %[se]\n\t"
  "fxsave64 %[before]\n\tfnstenv %[eb]\n\tfldenv %[eb]\n\t"
  "flds %[input]\n\t"
  "fxsave64 %[loaded]\n\tfnstenv %[el]\n\tfldenv %[el]\n\t"
  "fstps %[output]\n\t"
  "fxsave64 %[stored]\n\tfnstenv %[es]\n\t"
  "fxrstor64 %[hb]\n\tfldenv %[he]\n\t"
  "fxsave64 %[ha]\n\tfnstenv %[hea]\n\tfldenv %[he]"
  :[hb]"=m"(host_before),[he]"=m"(host_env),[before]"=m"(before),[eb]"=m"(eb),[loaded]"=m"(loaded),[el]"=m"(el),[output]"=m"(output),[stored]"=m"(stored),[es]"=m"(es),[ha]"=m"(host_after),[hea]"=m"(host_env_after)
  :[seed]"m"(seed),[se]"m"(seed_env),[input]"m"(input)
  :"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)","xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");
 r.before=before.b;r.loaded=loaded.b;r.stored=stored.b;r.env_before=eb;r.env_loaded=el;r.env_stored=es;r.host_before=host_before.b;r.host_after=host_after.b;r.host_env_before=host_env;r.host_env_after=host_env_after;r.result=output;r.host_restored=host_before.b==host_after.b&&host_env==host_env_after;
 old::require(r.host_restored,"Actual complete host hardware FX512/ENV28 restoration");return r;
}
int main(int argc,char**argv){try{old::require(argc==2,"Fresh local hardware unit output required");old::Output out(argv[1]);old::Header h{};std::memcpy(h.magic,"MW4NMC01",8);h.version=1;h.count=18432;h.stride=sizeof(Row);h.pages=0;out.write(h);unsigned count=0;
 for(unsigned rep=0;rep<2;++rep)for(unsigned inp=0;inp<16;++inp)for(unsigned depth:{0U,1U,7U})for(unsigned sticky:{0U,2U,32U,34U})for(auto cw:old::control_words)for(unsigned top:{0U,7U})for(unsigned c1:{0U,1U}){const auto row=probe(rep,inp,cw,top,depth,sticky,c1);out.write(row);++count;}
 old::require(count==h.count,"Exact local hardware carry schedule");out.commit();std::cout<<count<<" authored hardware FLD/FSTP unit captures; no original process executed\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
