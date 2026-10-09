// Native-only compiled leaf testing. Frozen original records are optional data.
#include "paired_context.hpp"
#include "protocol.hpp"
#include "probe_io.hpp"
#include <fstream>
#include <iostream>
#include <memory>
#include <sstream>
namespace mp=mw34::m4_crt_matherr_paired;
namespace mn=mw34::m4_crt_matherr_paired_native;
namespace pr=mw34::m4_crt_probe;
using namespace mw34;
static void need(bool v,const char *m){pr::need(v,m);}
static auto bytes(const auto &v){return std::as_bytes(std::span{v});}
static unsigned u32(const void *p){unsigned v;std::memcpy(&v,p,4);return v;}
static unsigned u16(const void *p){std::uint16_t v;std::memcpy(&v,p,2);return v;}
static void put(auto &v,unsigned o,unsigned x){std::memcpy(v.data()+o,&x,4);}
static m4_runtime::Cpu32 cpu(const mp::Cpu &c){return {c.eax,c.ecx,c.edx,c.ebx,c.esp,c.ebp,c.esi,c.edi,c.flags,c.pc};}
static mp::Cpu cpu(const m4_runtime::Cpu32 &c){return {c.eax,c.ecx,c.edx,c.ebx,c.esp,c.ebp,c.esi,c.edi,c.eflags,c.eip};}
struct HostScope {
 struct alignas(16) Image{std::array<std::uint8_t,512> b{};};Image before{},after{};
 std::array<std::uint8_t,28> env{},env_after{};
 HostScope(){__asm__ volatile("fxsave64 %0\n\tfnstenv %1":"=m"(before),"=m"(env)::"memory");restore();}
 void restore(){__asm__ volatile("fxrstor64 %0\n\tfldenv %1"::"m"(before),"m"(env):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)","xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");}
 void capture(){restore();__asm__ volatile("fxsave64 %0\n\tfnstenv %1":"=m"(after),"=m"(env_after)::"memory");}
 void check(){need(before.b==after.b&&env==env_after,"Full host FX512/ENV28 restoration");}
 ~HostScope(){restore();}
};
static m4_runtime::Policy policy(){m4_runtime::Policy p;p.stack_low={0x20001000};p.stack_bytes=4096;p.heap_bytes=8192;return p;}
struct Input {
 std::array<unsigned,5>tag{};mp::Cpu before{};
 std::array<std::uint8_t,512>fx{};std::array<std::uint8_t,28>env{};
 std::array<std::uint8_t,12288>memory{};
};
static Input authored(unsigned index){
 Input i;i.tag={index/768,index,mp::arguments[index%8],pr::controls[(index/64)%12],(index/8)%8};i.before=mp::input_cpu(index);
 mp::seed_pages(i.memory,index,i.tag[2]);mp::seed_fp(i.fx.data(),i.env.data(),i.tag[3],i.tag[4],index%8);return i;
}
// This accessor deliberately reads ONLY original BEFORE fields as native input.
static Input offline_input(const mp::OriginalRecord &r){return {r.tag,r.before,r.fx[0],r.env[0],r.memory[0]};}
struct Fixture {
 m4_runtime::Runtime r;State &s;std::unique_ptr<mn::Context> c;Input input;
 Fixture(std::span<const std::byte>game,std::span<const std::byte>code,const Input &i,bool service=true):r(m4_runtime::Runtime::from_admitted_image(game,policy())),s(*std::construct_at(reinterpret_cast<State*>(r.remill_state().data()))),input(i){
  auto raw=reinterpret_cast<std::uint8_t*>(&s);for(unsigned j=0;j<3504;++j)raw[j]=static_cast<std::uint8_t>(j*13+i.tag[1]+7);
  std::memcpy(raw+2768,i.fx.data(),512); // Hardware FX and legacy ENV have separate provenance.
  std::memcpy(raw+2774,i.env.data()+18,2);std::memcpy(raw+2776,i.env.data()+12,4);std::memcpy(raw+2780,i.env.data()+16,2);
  std::memcpy(raw+2784,i.env.data()+20,4);std::memcpy(raw+2788,i.env.data()+24,2);
  const unsigned sw=u16(i.fx.data()+2);for(auto [o,b]:std::array<std::pair<unsigned,unsigned>,11>{{{2737,8},{2739,9},{2741,10},{2743,14},{2745,5},{2747,4},{2749,3},{2751,2},{2753,1},{2755,0},{2757,6}}})raw[o]=static_cast<std::uint8_t>((sw>>b)&1);
  for(unsigned j=0;j<8;++j){std::memcpy(raw+2486+16*j,i.fx.data()+32+16*j,10);std::memcpy(raw+16+64*j,i.fx.data()+160+16*j,16);}
  s.addr.ds_base.dword=s.addr.ss_base.dword=0;s.addr.fs_base.dword=r.fs_base().value;
  mn::project(s,cpu(i.before));std::memcpy(r.fx().data(),i.fx.data(),512);r.mark_remill_seeded();
  r.memory().map({0x7800b000},4096,Permissions::read|Permissions::write);r.memory().write({mp::entry},code);r.memory().protect({0x7800b000},Permissions::read|Permissions::execute);
  for(unsigned j=1;j<3;++j)r.memory().map({mp::pages[j]},4096,Permissions::read|Permissions::write);
  for(unsigned j=0;j<3;++j)r.memory().write({mp::pages[j]},bytes(i.memory).subspan(4096*j,4096));
  r.cpu()=cpu(i.before);r.cpu().esp+=4;r.cpu().eip=0x5ac428;
  c=std::make_unique<mn::Context>(r);
  if(service)r.register_service({{c->slot},{m4_runtime::Abi::Cdecl,4,true},&mn::adapter,"Compiled exact matherr native unit variant",m4_runtime::Domain::admitted_game,"2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7","72dabe5c1616590b1fe624844914b6d21fab26cf8eb8ddc3d430de98f50adce4"});
  r.freeze_registry();
 }
 auto state(){std::array<std::uint8_t,3504>v{};std::memcpy(v.data(),&s,3504);return v;}
 auto memory(){std::array<std::uint8_t,12288>v{};for(unsigned j=0;j<3;++j)r.memory().read({mp::pages[j]},std::as_writable_bytes(std::span{v}).subspan(4096*j,4096));return v;}
 void repair_pages(){for(auto p:mp::pages){try{r.memory().unmap({p});}catch(...){}r.memory().map({p},4096,Permissions::read|Permissions::write);}}
 void game_write(unsigned a,unsigned v){for(const auto &g:r.image_metadata().mapped_regions)if(a>=g.start.value&&std::uint64_t{a}+4<=std::uint64_t{g.start.value}+g.size){r.memory().protect(g.start,Permissions::read|Permissions::write);r.memory().store<unsigned>({a},v);r.memory().protect(g.start,g.permissions);return;}throw std::runtime_error("Owned game mapping absent");}
 void invoke(unsigned ret=mp::return_pc,bool own=true){need(!mn::owner,"Serial owner already occupied");mn::owner=own?c.get():nullptr;try{r.call_import({c->slot},{ret});}catch(...){mn::owner=nullptr;throw;}mn::owner=nullptr;}
};
struct NativeRecord {
 mp::OriginalRecord common;
 std::array<std::uint8_t,3504>before,after;
 std::array<mn::Event,5>events;
 std::array<unsigned,6>route;
 std::array<unsigned,4>counters;
};
static_assert(sizeof(NativeRecord)==mp::native_stride);
static NativeRecord positive(Fixture &f){
 NativeRecord n{};n.common.tag=f.input.tag;n.common.before=f.input.before;n.before=f.state();n.common.fx[0]=f.input.fx;n.common.env[0]=f.input.env;n.common.memory[0]=f.memory();
 HostScope h;f.invoke();h.capture();h.check();n.after=f.state();n.common.after=cpu(f.r.cpu());n.common.memory[1]=f.memory();
 std::memcpy(n.common.fx[1].data(),f.r.fx().data(),512);n.common.fx[2]=h.before.b;n.common.fx[3]=h.after.b;n.common.env[1]=f.input.env;n.common.env[2]=h.env;n.common.env[3]=h.env_after;
 n.events=f.c->events;const auto &route=f.r.calls().back();n.route={route.site.value,route.target.value,route.return_pc.value,unsigned(route.import),unsigned(route.completed),0};n.counters={f.c->step,unsigned(f.c->used),unsigned(f.c->complete),unsigned(f.c->failed)};
 auto expected=n.before;put(expected,2216,f.input.tag[2]);put(expected,2312,mp::frame+4);put(expected,2472,mp::return_pc);
 for(auto [o,v]:std::array<std::pair<unsigned,unsigned>,6>{{{2065,0},{2067,1},{2069,0},{2071,1},{2073,0},{2077,0}}})expected[o]=static_cast<std::uint8_t>(v);
 need(n.after==expected,"Full State3504 mutation model");auto mem=n.common.memory[0];put(mem,4096+0x2b8,0);put(mem,8192+0xc4,f.input.tag[2]);need(n.common.memory[1]==mem,"All three pages mutation model");
 auto ec=cpu(f.input.before);ec.eax=f.input.tag[2];ec.esp=mp::frame+4;ec.eip=mp::return_pc;ec.eflags=(ec.eflags&~0x8d5U)|0x44U;need(f.r.cpu()==ec,"CPU/defined flags/RET/Cdecl model");
 const std::array<mn::Event,5>ev{{{mp::argument_address,f.input.tag[2],4,0},{mp::zero_global,u32(mem.data()+4096+0x2b8),4,0},{mp::zero_global,0,4,1},{mp::callback_global,f.input.tag[2],4,1},{mp::frame,mp::return_pc,4,0}}};auto e=ev;e[1].value=u32(n.common.memory[0].data()+4096+0x2b8);
 need(!std::memcmp(e.data(),n.events.data(),sizeof(e)),"Five exact compiled ordered events");need(n.route==std::array<unsigned,6>{0x5ac428,0x5bb50c,mp::return_pc,1,1,0}&&n.counters==std::array<unsigned,4>{5,1,1,0},"Actual complete named import route");
 need(n.common.fx[0]==n.common.fx[1]&&n.common.env[0]==n.common.env[1]&&!f.r.poisoned(),"All coherent FP/legacy metadata preserved");return n;
}
static unsigned hook_mode{};
static void hook(mn::Context &c,unsigned step){
 if(hook_mode==1&&step==4)c.runtime.memory().protect({mp::pages[0]},Permissions::none);
 if(hook_mode==2&&step==4)c.runtime.memory().store<unsigned>({mp::frame},0x12345678);
 if(hook_mode==3&&step==4)c.state.gpr.rbx.dword^=1;
 if(hook_mode==4&&step==1)c.step=4;
 if(hook_mode==5&&step==4)c.state.gpr.rax.dword^=1;
}
static void unit(std::span<const std::byte>game,std::span<const std::byte>code,const char*out){
 unsigned checks{},positives{},faults{},reuse{};std::ostringstream rows;
 auto check=[&](bool v,const char*m){++checks;need(v,m);};
 for(unsigned j=0;j<1536;++j){Fixture f(game,code,authored(j));(void)positive(f);++positives;check(f.r.calls().size()==1,"One positive route");}
 for(unsigned scenario=0;scenario<21;++scenario){
  Fixture f(game,code,authored(767),scenario!=18);auto &c=*f.c;hook_mode=0;bool own=true;unsigned ret=mp::return_pc;
  switch(scenario){
   case 0:f.r.memory().protect({mp::pages[0]},Permissions::read);break;
   case 1:f.r.memory().protect({mp::pages[1]},Permissions::read);break;
   case 2:f.r.memory().protect({mp::pages[2]},Permissions::read);break;
   case 3:f.r.memory().unmap({mp::pages[1]});break;
   case 4:f.r.memory().unmap({mp::pages[2]});break;
   case 5:f.r.memory().unmap({mp::pages[0]});f.r.memory().map({mp::pages[0]},2048,Permissions::read|Permissions::write);f.r.memory().store<unsigned>({mp::frame},mp::return_pc);break;
   case 6:hook_mode=1;break;case 7:hook_mode=2;break;case 8:hook_mode=3;break;case 9:hook_mode=4;break;case 10:hook_mode=5;break;
   case 11:f.r.memory().protect({0x7800b000},Permissions::read|Permissions::write);f.r.memory().store<std::uint8_t>({mp::entry},0x90);break;
   case 12:f.r.memory().protect({0x7800b000},Permissions::none);break;
   case 13:f.game_write(c.slot,0x12345678);break;
   case 14:f.s.addr.ds_base.dword=1;break;case 15:f.s.addr.fs_base.dword^=1;break;
   case 16:own=false;break;case 17:ret=0x12345678;break;case 18:break;
   case 19:f.r.cpu().esp=f.r.stack_low().value;break;
   case 20:(void)positive(f);break;
  }
  if(hook_mode)c.test_after_event=&hook;
  HostScope h;bool denied{};std::string error;try{f.invoke(ret,own);}catch(const std::exception &e){denied=true;error=e.what();}h.capture();h.check();std::cout<<"scenario "<<scenario<<" denied="<<denied<<" active="<<c.active<<" step="<<c.step<<" error="<<error<<std::endl;check(denied,"Actual native fault denied");++faults;
  check(!c.active,"Active scope unwound");check(mn::owner==nullptr,"Owner released");
  if(scenario>=1&&scenario<=9){check(c.failed&&c.used&&!c.complete,"Compiled first error retained");check(scenario==8?c.step==5:c.step<5,"Access faults stop early; nonvolatile RET guard checks completed accesses");}
  if(scenario==1)check(c.fault_pc==0x7800b393&&c.fault_address==mp::zero_global&&c.step==2,"First zero write fault PC/address/order");
  if(scenario==2||scenario==4)check(c.fault_pc==0x7800b39a&&c.fault_address==mp::callback_global&&c.step==3,"First callback write fault PC/address/order");
  if(scenario==3)check(c.fault_pc==0x7800b393&&c.fault_address==mp::zero_global&&c.step==1,"First zero read fault PC/address/order");
  if(scenario==5)check(c.fault_pc==mp::entry&&c.fault_address==mp::argument_address&&c.step==0,"Compiled argument read fault PC/address/order");
  if(scenario==6||scenario==7)check(c.fault_pc==0x7800b39f&&c.fault_address==mp::frame&&c.step==4,"Compiled RET read fault PC/address/order");
  rows<<"{\"scenario\":"<<scenario<<",\"step\":"<<c.step<<",\"used\":"<<c.used<<",\"complete\":"<<c.complete<<",\"failed\":"<<c.failed<<",\"fault_pc\":"<<c.fault_pc<<",\"fault_address\":"<<c.fault_address<<",\"poisoned\":"<<f.r.poisoned()<<",\"call_count\":"<<f.r.calls().size()<<"}";
  if(scenario!=20)rows<<",";
  if(f.r.poisoned()){
   const auto snapshot=f.state();std::array<std::byte,512>fx{};std::memcpy(fx.data(),f.r.fx().data(),512);const auto oldstep=c.step,oldpc=c.fault_pc,oldaddr=c.fault_address;const auto oldreason=c.reason;const auto count=f.r.calls().size();
   f.repair_pages();f.s.addr.ds_base.dword=0;f.s.addr.fs_base.dword=f.r.fs_base().value;c.test_after_event=nullptr;hook_mode=0;f.r.cpu().esp=mp::frame+4;f.r.cpu().eip=0x5ac428;
   // Preserve State byte identity even when fixing authored entry fields.
   std::memcpy(&f.s,snapshot.data(),3504);
   bool stopped{};HostScope retry;try{f.invoke();}catch(const std::exception &){stopped=true;}retry.capture();retry.check();
   check(stopped&&f.r.poisoned(),"Poisoned corrected retry denied");check(f.r.calls().size()==count&&c.step==oldstep,"Retry has no guest progression");check(c.fault_pc==oldpc&&c.fault_address==oldaddr&&c.reason==oldreason,"First POD error stable on retry");check(f.state()==snapshot&&!std::memcmp(fx.data(),f.r.fx().data(),512),"Whole State/FX preserved on poisoned reuse");++reuse;
  }
 }
 const auto text=std::string("{\"passed\":true,\"positive_cases\":")+std::to_string(positives)+",\"fault_scenarios\":"+std::to_string(faults)+",\"poisoned_retries\":"+std::to_string(reuse)+",\"checks\":"+std::to_string(checks)+",\"rows\":["+rows.str()+"],\"original_executed\":false,\"callback_invoked\":false}\n";
 pr::Output o(out);o.write(text.data(),text.size());o.commit();std::cout<<positives<<" coherent positives / "<<faults<<" actual denial scenarios / "<<checks<<" assertions passed\n";
}
int main(int argc,char**argv){try{
 need(argc==6||argc==7,"Native paired unit/replay arguments required");const std::string mode=argv[1];need((mode=="--unit"&&argc==6)||(mode=="--replay"&&argc==7),"Exact native paired mode/argc required");
 pr::hash_controls();auto game=pr::read(argv[2],2384384),provider=pr::read(argv[3],266293),code=pr::read(argv[4],17);
 need(game.size()==2384384&&pr::digest(game)=="95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf","Exact game identity");need(provider.size()==266293&&pr::digest(provider)=="2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7","Exact provider identity");need(code.size()==17&&pr::digest(code)=="db28fc73ef336b9925b6cd56a37615599cc224d6a38cdd3b3cf5851c72e77bc9","Exact compiled leaf source identity");
 if(mode=="--unit"){unit(bytes(game),bytes(code),argv[5]);return 0;}
 auto raw=pr::read(argv[5],41220120);need(raw.size()==41220120&&pr::digest(raw)=="50adc9316afe26f0deb78cac3aeb737bc5c0810324897031c3bd548fec30c472","Exact frozen offline original input identity");need(!std::memcmp(raw.data(),"MW4MOR01",8)&&u32(raw.data()+8)==1&&u32(raw.data()+12)==1536&&u32(raw.data()+16)==26836&&u32(raw.data()+20)==12288,"Offline original framing");
 pr::Output out(argv[6]);out.write("MW4MPN01",8);const std::array<unsigned,4>header{1,1536,33964,3504};out.write(header.data(),sizeof(header));
 for(unsigned j=0;j<1536;++j){mp::OriginalRecord observed;std::memcpy(&observed,raw.data()+24+j*26836,26836);const auto in=offline_input(observed);need(in.tag==authored(j).tag&&in.before.esp==mp::frame&&in.before.pc==mp::entry,"Offline BEFORE schedule/frame");Fixture f(bytes(game),bytes(code),in);const auto n=positive(f);out.write(&n,sizeof(n));}
 out.commit();std::cout<<"1536 BEFORE-only native replays passed; no original execution and no callback invocation\n";return 0;
}catch(const std::exception&e){mn::owner=nullptr;std::cerr<<e.what()<<'\n';return 1;}}
