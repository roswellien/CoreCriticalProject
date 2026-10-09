#include "protocol.hpp"
#include "spec.hpp"
#include "corpus.hpp"
#include "code_identity.hpp"
#include "host_scope.hpp"
#include "memory/guest_memory.hpp"
#include <remill/Arch/X86/Runtime/State.h>
#include <bit>
#include <algorithm>
#include <csetjmp>
#include <memory>
#include <thread>
extern "C" void *mw34_numeric_entry_4c19f0(State*,std::uint32_t,void*);
extern "C" void *mw34_numeric_entry_780c10f0(State*,std::uint32_t,void*);
namespace mw34::m4_numeric_max {
#pragma pack(push,1)
struct Checkpoint {Cpu cpu;std::array<std::uint8_t,512> fx;std::array<std::uint8_t,28> env;std::array<std::uint8_t,3504> state;};
struct Event {std::uint32_t address,value,width,operation;};
struct Route {std::uint32_t entry,returned,pop,complete;Cpu before,after;};
struct NativeRecord {Record common;std::array<std::uint8_t,3504> state_before,state_after;Checkpoint checkpoint;
 std::uint32_t events,reads,writes,clears,tests,returns,routes,failed;std::array<Event,22> trace;std::array<Route,2> route;};
#pragma pack(pop)
static_assert(sizeof(State)==3504&&sizeof(NativeRecord)==47432&&sizeof(void*)==8);
static Cpu cpu(const State&s){return {s.gpr.rax.dword,s.gpr.rcx.dword,s.gpr.rdx.dword,s.gpr.rbx.dword,s.gpr.rsp.dword,s.gpr.rbp.dword,s.gpr.rsi.dword,s.gpr.rdi.dword,
 0x202U|(s.aflag.cf<<0)|(s.aflag.pf<<2)|(s.aflag.af<<4)|(s.aflag.zf<<6)|(s.aflag.sf<<7)|(s.aflag.df<<10)|(s.aflag.of<<11),s.gpr.rip.dword};}
static std::uint16_t status(const State&s){return (s.x87.fxsave.swd.flat&0xb880)|(s.sw.ie<<0)|(s.sw.de<<1)|(s.sw.ze<<2)|(s.sw.oe<<3)|(s.sw.ue<<4)|(s.sw.pe<<5)|(s.sw.sf<<6)|(s.sw.c0<<8)|(s.sw.c1<<9)|(s.sw.c2<<10)|(s.sw.c3<<14);}
static unsigned full_tag(const std::uint8_t*b){auto m=word<std::uint64_t>(b);auto e=word<std::uint16_t>(b+8)&0x7fff;return !e&&!m?1:e==0x7fff||!e||!(m>>63)?2:0;}
static void capture(const State&s,Cpu&c,std::array<std::uint8_t,512>&fx,std::array<std::uint8_t,28>&env,std::array<std::uint8_t,3504>&raw){
 c=cpu(s);std::memcpy(raw.data(),&s,3504);std::memcpy(fx.data(),&s.x87,512);auto sw=status(s);std::memcpy(fx.data()+2,&sw,2);
 // Software legacy metadata has its own State fields. Hardware FX metadata
 // is a separate projection with the measured zero provenance on this host.
 std::memset(fx.data()+6,0,18);unsigned tags=0xffff,top=(sw>>11)&7;
 for(unsigned i=0;i<8;++i){std::memcpy(fx.data()+32+i*16,&s.st.elems[i].val,10);std::memcpy(fx.data()+160+i*16,&s.vec[i],16);auto phys=(top+i)&7;
  if(s.x87.fxsave.ftw.flat&(1<<phys))tags=(tags&~(3<<(2*phys)))|(full_tag(fx.data()+32+i*16)<<(2*phys));}
 auto put=[&](unsigned offset,std::uint32_t value){std::memcpy(env.data()+offset,&value,4);};
 put(0,0xffff0000U|s.x87.fxsave.cwd.flat);put(4,0xffff0000U|sw);put(8,0xffff0000U|tags);put(12,s.x87.fxsave.ip);put(16,s.x87.fxsave.cs.flat|(std::uint32_t{s.x87.fxsave.fop}<<16));put(20,s.x87.fxsave.dp);put(24,0xffff0000U|s.x87.fxsave.ds.flat);
}
static void initialize(State&s,const Tag&t){
 auto*b=reinterpret_cast<std::uint8_t*>(&s);for(unsigned i=0;i<3504;++i)b[i]=static_cast<std::uint8_t>(i*29+t.repeat*71+t.input*11+(i>>8)*7);
 std::memset(&s.addr,0,sizeof(s.addr));s.seg.cs.flat=0x23;s.seg.ds.flat=0x2b;s.seg.ss.flat=0x2b;
 s.gpr.rax.dword=0x13579bdf;s.gpr.rcx.dword=0x2468ace0;s.gpr.rdx.dword=0x81726354;s.gpr.rbx.dword=0x10293847;s.gpr.rsp.dword=frame;s.gpr.rbp.dword=0x92837465;s.gpr.rsi.dword=0x56473829;s.gpr.rdi.dword=0xaabbccdd;s.gpr.rip.dword=t.entry;
 s.rflag.flat=0x202;s.aflag.cf=0;s.aflag.pf=0;s.aflag.af=0;s.aflag.zf=0;s.aflag.sf=0;s.aflag.df=0;s.aflag.of=0;
 alignas(16)std::uint8_t fx[512];std::uint8_t env[28];seed(t.cw,t.top,t.depth,t.sticky,fx,env);std::memcpy(&s.x87,fx,512);
 auto sw=word<std::uint16_t>(fx+2);s.sw.ie=0;s.sw.de=(sw>>1)&1;s.sw.ze=0;s.sw.oe=0;s.sw.ue=0;s.sw.pe=(sw>>5)&1;s.sw.sf=0;s.sw.c0=0;s.sw.c1=0;s.sw.c2=0;s.sw.c3=0;
 s.x87.fxsave.ip=0x11223344;s.x87.fxsave.dp=0x55667788;s.x87.fxsave.cs.flat=0x23;s.x87.fxsave.ds.flat=0x2b;s.x87.fxsave.fop=0x11d;
 for(unsigned i=0;i<8;++i){std::memcpy(&s.st.elems[i].val,fx+32+i*16,10);std::memset(&s.vec[i],0,16);}
}
struct Harness {
 mw34::GuestMemory memory;
 explicit Harness(const std::vector<std::uint8_t>&pack,unsigned input,bool directed){
  for(unsigned i=0;i<7;++i){memory.map({page_bases[i]},4096,mw34::Permissions::read|mw34::Permissions::write);memory.write({page_bases[i]},std::as_bytes(std::span{pack.data()+12+i*4104+8,4096}));memory.protect({page_bases[i]},page_permissions[i]==1?mw34::Permissions::read|mw34::Permissions::execute:page_permissions[i]==0?mw34::Permissions::read:mw34::Permissions::read|mw34::Permissions::write);}
  if(directed){memory.protect({0x78115000},mw34::Permissions::read|mw34::Permissions::write);memory.store<std::uint32_t>({0x78115004},inputs[input]);memory.protect({0x78115000},mw34::Permissions::read);}
  std::array<std::byte,44> dirty;dirty.fill(std::byte{0xa5});memory.write({0x60b368},dirty);memory.store<std::uint32_t>({frame},capture_pc);
 }
 void capture_memory(std::array<std::uint8_t,memory_size>&bytes){for(unsigned i=0;i<4;++i)memory.read({observed_pages[i]},std::as_writable_bytes(std::span{bytes.data()+i*4096,4096}));}
};
class Context;static thread_local Context*active{};
class Context {
 bool running{},used{},escape_ready{};std::thread::id owner=std::this_thread::get_id();std::jmp_buf escape;unsigned level{},commits{};
 void fault(){r.failed=1;if(running&&escape_ready&&owner==std::this_thread::get_id())std::longjmp(escape,1);}
 bool code_matches(){bool ok{};try{std::vector<std::uint8_t> bytes;for(auto c:code_bindings){std::vector<std::byte> b(c.size);memory.read({c.pc},b);for(auto x:b)bytes.push_back(std::to_integer<std::uint8_t>(x));}ok=sha256(bytes)==selected_code_sha;}catch(const std::exception&){}return ok;}
 bool admitted(){if(!running||r.failed||owner!=std::this_thread::get_id()){fault();return false;}return true;}
 Event wanted(unsigned index){
  if(r.common.tag.entry==0x780c10f0)return index==0?Event{0x78115004,0,4,0}:Event{frame,0,4,0};
  const std::array<Event,22> schedule{{{frame-4,0,4,1},{frame-8,0,4,1},{frame-12,0,4,1},{0x5bb4fc,0,4,0},{frame-16,0,4,1},{0x78115004,0,4,0},{frame-16,0,4,0},
  {0x60b368,0,4,1},{0x60b36c,0,4,1},{0x60b370,0,4,1},{0x60b374,0,4,1},{0x60b378,0,4,1},{0x60b37c,0,4,1},{0x60b380,0,4,1},{0x60b384,0,4,1},{0x60b388,0,4,1},{0x60b38c,0,4,1},{0x60b390,0,4,1},
  {frame-12,0,4,0},{frame-8,0,4,0},{frame-4,0,4,0},{frame,0,4,0}}};return schedule[index];
 }
 bool access(unsigned address,unsigned operation){if(!admitted())return false;auto extent=r.common.tag.entry==0x780c10f0?2:22;if(r.events>=extent){fault();return false;}auto e=wanted(r.events);if(e.address!=address||e.operation!=operation){fault();return false;}return true;}
 void log(unsigned address,unsigned value,unsigned operation){r.trace[r.events++]={address,value,4,operation};}
public:
 mw34::GuestMemory&memory;NativeRecord&r;bool complete{};
 Context(mw34::GuestMemory&m,NativeRecord&record):memory(m),r(record){}
 void enter(State&s){
  require(!active&&!running&&!used&&!r.failed,"Context lifetime rejected");used=true;require(owner==std::this_thread::get_id(),"Context owner rejected");
  require(r.common.tag.entry==0x780c10f0||r.common.tag.entry==0x4c19f0,"Unknown static entry rejected");
  require(s.gpr.rip.dword==r.common.tag.entry&&s.gpr.rsp.dword==frame,"Context entry rejected");
  require(memory.load<std::uint32_t>({frame})==capture_pc&&memory.load<std::uint32_t>({0x5bb4fc})==0x780c10f0,"Resolved owning IAT/return rejected");
  require(r.common.tag.depth<8,"Full stack denied before body");
  std::uint8_t seed_fx[512],seed_env[28];seed(r.common.tag.cw,r.common.tag.top,r.common.tag.depth,r.common.tag.sticky,seed_fx,seed_env);
  require(s.x87.fxsave.cwd.flat==word<std::uint16_t>(seed_fx)&&status(s)==word<std::uint16_t>(seed_fx+2)&&s.x87.fxsave.ftw.flat==seed_fx[4]&&s.x87.fxsave.mxcsr.flat==0x1f80,"Bounded CW/status/TOP/tags rejected");
  require(r.common.tag.input<inputs.size()&&memory.load<std::uint32_t>({0x78115004})==inputs[r.common.tag.input],"Declared provider data fixture rejected");
  require(s.seg.cs.flat==0x23&&s.seg.ds.flat==0x2b&&s.seg.ss.flat==0x2b&&std::memcmp(&s.addr,std::array<std::uint8_t,sizeof(s.addr)>{}.data(),sizeof(s.addr))==0,"Flat guest segment domain rejected");
  for(unsigned i=0;i<8;++i)require(std::memcmp(&s.st.elems[i].val,seed_fx+32+16*i,10)==0,"Declared live/dead raw80 input rejected");
  require(code_matches(),"Current game/provider code identity rejected");
  running=true;escape_ready=true;active=this;void*token=this;
  if(setjmp(escape)==0)token=r.common.tag.entry==0x780c10f0?mw34_numeric_entry_780c10f0(&s,s.gpr.rip.dword,this):mw34_numeric_entry_4c19f0(&s,s.gpr.rip.dword,this);
  active=nullptr;escape_ready=false;running=false;
  if(token!=this||!complete||level||r.events!=(r.common.tag.entry==0x780c10f0?2U:22U)||r.returns!=(r.common.tag.entry==0x780c10f0?1U:3U)||r.routes!=(r.common.tag.entry==0x780c10f0?0U:2U)||commits!=(MW34_NUMERIC_REPAIRED?(r.common.tag.entry==0x780c10f0?1U:2U):0U))r.failed=1;
 }
 unsigned read32(unsigned address){if(!access(address,0))return 0;unsigned value{};bool ok{};try{value=memory.load<std::uint32_t>({address});ok=true;}catch(const std::exception&){}if(!ok){fault();return 0;}++r.reads;log(address,value,0);return value;}
 void write32(unsigned address,unsigned value){if(!access(address,1))return;bool ok{};try{memory.store<std::uint32_t>({address},value);ok=true;}catch(const std::exception&){}if(!ok){fault();return;}++r.writes;log(address,value,1);}
 void*body(State&s,unsigned pc){if(!admitted())return this;if(level||pc!=0x4c1a00||s.gpr.rsp.dword!=frame-8||s.gpr.rbp.dword!=frame-4||r.events!=2){fault();return this;}level=1;r.routes=1;r.route[0]={pc,0x4c19f8,0,0,cpu(s),{}};return this;}
 void*call(State&s,unsigned pc){if(!admitted())return this;if(level!=1||pc!=0x780c10f0||s.gpr.rsp.dword!=frame-16||s.gpr.rbp.dword!=frame-12||r.events!=5){fault();return this;}
  level=2;r.routes=2;r.route[1]={pc,0x4c1a09,0,0,cpu(s),{}};return mw34_numeric_entry_780c10f0(&s,pc,this);}
 void*returned(State&s,unsigned pc){if(!admitted())return this;
  if(level==2){if(pc!=0x4c1a09||s.gpr.rsp.dword!=frame-12||r.events!=7){fault();return this;}r.route[1].after=cpu(s);r.route[1].complete=1;level=1;capture(s,r.checkpoint.cpu,r.checkpoint.fx,r.checkpoint.env,r.checkpoint.state);r.common.tag.checkpoint_seen=1;}
  else if(level==1){if(pc!=0x4c19f8||s.gpr.rsp.dword!=frame-4||r.events!=20){fault();return this;}r.route[0].after=cpu(s);r.route[0].complete=1;level=0;}
  else{if(!code_matches()){fault();return this;}if(complete||pc!=capture_pc||s.gpr.rsp.dword!=frame+4){fault();return this;}complete=true;}
  if(s.gpr.rip.dword!=pc){fault();return this;}++r.returns;return this;}
 void clear(unsigned mask){if(!admitted())return;if(mask!=127||r.clears||r.tests){fault();return;}++r.clears;__asm__ volatile("fnclex":::"memory");}
 unsigned test(unsigned mask){if(!admitted())return 0;if(mask!=127||r.clears!=1||r.tests){fault();return 0;}++r.tests;std::uint16_t sw;__asm__ volatile("fnstsw %0":"=m"(sw)::"memory");return sw&mask;}
 void tag_commit(State&s,bool push){if(!admitted())return;
  const auto top=(s.x87.fxsave.swd.flat>>11)&7;
  if(push){if(commits||s.gpr.rip.dword!=0x780c10f0||r.events!=(r.common.tag.entry==0x780c10f0?1U:6U)||level!=(r.common.tag.entry==0x780c10f0?0U:2U)||(s.x87.fxsave.ftw.flat&(1<<top))){fault();return;}s.x87.fxsave.ftw.flat|=1<<top;}
  else{auto old=(top+7)&7;if(commits!=1||level!=1||s.gpr.rip.dword!=0x4c1a09||r.events!=8||!(s.x87.fxsave.ftw.flat&(1<<old))){fault();return;}s.x87.fxsave.ftw.flat&=~(1<<old);}
  ++commits;
 }
};
static std::vector<std::uint8_t> admit(const char*packpath,const char*gamepath,const char*providerpath){auto game=read(gamepath,2384384),provider=read(providerpath,565760),pack=read(packpath,pack_size);
 require(game.size()==2384384&&sha256(game)==image_sha,"Exact game identity rejected");require(provider.size()==565760&&sha256(provider)=="91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a","Exact provider identity rejected");require(pack.size()==pack_size&&sha256(pack)==pack_sha,"Exact pack identity rejected");
 for(auto c:code_bindings){auto i=std::find(page_bases.begin(),page_bases.end(),c.pc&~4095)-page_bases.begin();auto off=12+i*4104+8+(c.pc&4095);auto&im=c.origin?provider:game;require(c.image_offset+c.size<=im.size()&&std::memcmp(pack.data()+off,im.data()+c.image_offset,c.size)==0,"Exact instruction/image binding rejected");}return pack;}
static void execute(Harness&h,State&s,NativeRecord&r){Context context(h.memory,r);h.capture_memory(r.common.memory_before);capture(s,r.common.before,r.common.guest_fx_before,r.common.guest_env_before,r.state_before);
 {FpuScope host(r.common.tag.cw);context.enter(s);r.common.tag.status=r.failed;capture(s,r.common.after,r.common.guest_fx_after,r.common.guest_env_after,r.state_after);h.capture_memory(r.common.memory_after);r.common.tag.host_restored=host.restored(r.common);}}
static void controls(const std::vector<std::uint8_t>&pack){
 unsigned positives{},denials{},reuse{},bridge_faults{};
 for(unsigned entry:{0x780c10f0U,0x4c19f0U}){
  for(unsigned depth:{0U,1U,7U})for(unsigned top:{0U,7U}){
   Harness h(pack,0,false);NativeRecord r{};r.common.tag={0,0,entry,0x37f,top,depth,2,0,0,0};State s;initialize(s,r.common.tag);execute(h,s,r);require(!r.failed&&r.common.tag.host_restored,"Positive compiled live-stack route failed");++positives;
  }
  for(unsigned mode=0;mode<14;++mode){
   Harness h(pack,0,false);NativeRecord r{};r.common.tag={0,0,entry,0x37f,0,1,0,0,0,0};State s;initialize(s,r.common.tag);Context c(h.memory,r);
   switch(mode){
    case 0:s.gpr.rip.dword++;break;case 1:s.gpr.rsp.dword++;break;
    case 2:h.memory.protect({0x5bb000},mw34::Permissions::read|mw34::Permissions::write);h.memory.store<std::uint32_t>({0x5bb4fc},0x780c10f1);break;
    case 3:h.memory.store<std::uint32_t>({frame},capture_pc+1);break;
    case 4:h.memory.protect({0x780c1000},mw34::Permissions::read|mw34::Permissions::write);h.memory.store<std::uint8_t>({0x780c10f0},0xcc);break;
    case 5:s.x87.fxsave.cwd.flat&=~1U;break;case 6:s.x87.fxsave.ftw.flat^=2;break;case 7:s.x87.fxsave.swd.flat^=0x800;break;
    case 8:s.sw.ie=1;break;case 9:s.seg.ds.flat=0;break;case 10:s.addr.ds_base.dword=4;break;
    case 11:h.memory.protect({0x78115000},mw34::Permissions::read|mw34::Permissions::write);h.memory.store<std::uint32_t>({0x78115004},0x3f000000);break;
    case 12:break;case 13:reinterpret_cast<std::uint8_t*>(&s.st.elems[0].val)[0]^=1;break;
   }
   bool rejected{};
   if(mode==12){std::thread wrong([&]{try{c.enter(s);}catch(const std::exception&){rejected=true;}});wrong.join();}
   else try{c.enter(s);}catch(const std::exception&){rejected=true;}
   require(rejected&&r.events==0&&!r.routes,"Invalid context ran guest computation");++denials;
   rejected=false;try{c.enter(s);}catch(const std::exception&){rejected=true;}require(rejected&&r.events==0,"Rejected context was reusable");++reuse;
  }
  {Harness h(pack,0,false);NativeRecord r{};Context c(h.memory,r);c.write32(0x60b368,0);require(r.failed&&!r.events,"Inactive bridge admitted");++bridge_faults;}
 }
 {Harness h(pack,0,false);NativeRecord r{};r.common.tag={0,0,0x4c19f0,0x37f,0,0,0,0,0,0};State s;initialize(s,r.common.tag);h.memory.protect({0x60b000},mw34::Permissions::read);Context c(h.memory,r);
  FpuScope host(0x37f);c.enter(s);require(r.failed&&!c.complete&&r.events==7&&host.restored(r.common),"Actual typed output fault was admitted or lost host FP");++bridge_faults;}
 std::uint8_t fx[512]{},env[28]{};bool full{};try{seed(0x37f,0,8,0,fx,env);}catch(const std::exception&){full=true;}require(full,"Depth8 admitted before execution");++denials;
 std::cout<<"Compiled controls positives="<<positives<<" pre-entry denials="<<denials<<" poisoned reuse="<<reuse<<" typed bridge faults="<<bridge_faults<<" total="<<positives+denials+reuse+bridge_faults<<"\n";
}
}
extern "C" std::uint32_t __remill_read_memory_32(void*c,std::uint32_t a){return static_cast<mw34::m4_numeric_max::Context*>(c)->read32(a);}
extern "C" float __remill_read_memory_f32(void*c,std::uint32_t a){return std::bit_cast<float>(static_cast<mw34::m4_numeric_max::Context*>(c)->read32(a));}
extern "C" void*__remill_write_memory_32(void*c,std::uint32_t a,std::uint32_t v){static_cast<mw34::m4_numeric_max::Context*>(c)->write32(a,v);return c;}
extern "C" void*__remill_write_memory_f32(void*c,std::uint32_t a,float v){static_cast<mw34::m4_numeric_max::Context*>(c)->write32(a,std::bit_cast<std::uint32_t>(v));return c;}
extern "C" void*__remill_function_call(State*s,std::uint32_t pc,void*c){return static_cast<mw34::m4_numeric_max::Context*>(c)->call(*s,pc);}
extern "C" void*__remill_function_return(State*s,std::uint32_t pc,void*c){return static_cast<mw34::m4_numeric_max::Context*>(c)->returned(*s,pc);}
extern "C" void*mw34_numeric_body_entry(State*s,std::uint32_t pc,void*c){return static_cast<mw34::m4_numeric_max::Context*>(c)->body(*s,pc);}
extern "C" void __remill_fpu_exception_clear(unsigned mask){auto*c=mw34::m4_numeric_max::active;if(!c)std::abort();c->clear(mask);}
extern "C" unsigned __remill_fpu_exception_test(unsigned mask){auto*c=mw34::m4_numeric_max::active;if(!c)std::abort();return c->test(mask);}
extern "C" void mw34_numeric_fld_commit(State*s,void*c){static_cast<mw34::m4_numeric_max::Context*>(c)->tag_commit(*s,true);}
extern "C" void mw34_numeric_fstp_commit(State*s,void*c){static_cast<mw34::m4_numeric_max::Context*>(c)->tag_commit(*s,false);}
int main(int argc,char**argv){using namespace mw34::m4_numeric_max;try{
 SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
 if(argc==3&&std::string(argv[1])=="--check-publication"){publication_controls(argv[2]);return 0;}
 if(argc==5&&std::string(argv[1])=="--check-context"){auto p=admit(argv[2],argv[3],argv[4]);controls(p);return 0;}
 require(argc==5||argc==6,"Native numeric-max: exact-pack exact-game exact-provider fresh-output [--directed]");const bool directed=argc==6;require(!directed||std::string(argv[5])=="--directed","Unknown mode");auto pack=admit(argv[1],argv[2],argv[3]);Output out(argv[4]);Header header{};std::memcpy(header.magic,"MW4NMN01",8);header.version=1;header.count=records(directed);header.stride=sizeof(NativeRecord);header.pages=4;out.write(header);
 for(unsigned repeat=0;repeat<2;++repeat)for(unsigned input=0;input<(directed?inputs.size():1);++input)for(unsigned depth:{0U,1U,7U})for(unsigned sticky:{0U,1U,2U})for(auto cw:control_words)for(unsigned top:{0U,7U})for(unsigned entry:{0x780c10f0U,0x4c19f0U}){
  auto r=std::make_unique<NativeRecord>();r->common.tag={repeat,input,entry,cw,top,depth,sticky,0,0,0};Harness h(pack,input,directed);State state;initialize(state,r->common.tag);execute(h,state,*r);out.write(*r);if(r->failed||!r->common.tag.host_restored){out.commit();std::cerr<<"Native route/restore failed\n";return 1;}
 }
 out.commit();std::cout<<header.count<<" compiled native provider/wrapper observation records; baseline equivalence unproven\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
