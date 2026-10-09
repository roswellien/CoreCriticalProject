// Isolated actual x86 game/provider code. No DLL initialization or service result.
#include "protocol.hpp"
#include "spec.hpp"
#include "corpus.hpp"
#include "original_broker.hpp"
#include <memory>
using namespace mw34::m4_numeric_max;
static_assert(sizeof(void*)==4 && sizeof(CONTEXT)==716);
extern "C" {
Cpu numeric_input{},numeric_before{},numeric_after{};
std::uint32_t numeric_host_esp{},numeric_env_ready{};
alignas(16) std::uint8_t numeric_guest_fx[512]{},numeric_host_fx[512]{},numeric_host_after[512]{};
alignas(16) std::uint8_t numeric_fx_before[512]{},numeric_fx_after[512]{};
std::uint8_t numeric_guest_env[28]{},numeric_env_before[28]{},numeric_env_after[28]{},numeric_host_env[28]{},numeric_host_env_after[28]{};
void numeric_enter();void numeric_capture();void numeric_restore();
}
static std::uint32_t execute(){__try{numeric_enter();return 0;}__except(EXCEPTION_EXECUTE_HANDLER){const auto code=GetExceptionCode();numeric_restore();return code;}}
static CONTEXT checkpoint{};static unsigned checkpoint_seen{},checkpoint_pending{},checkpoint_error{};static DWORD owner{};
bool mw34::original_broker::handle_debug_checkpoint(HANDLE child,const DEBUG_EVENT&event){
 const auto&exception=event.u.Exception.ExceptionRecord;auto code=exception.ExceptionCode;
 if((code!=EXCEPTION_BREAKPOINT&&code!=0x4000001fU)||exception.ExceptionAddress!=reinterpret_cast<void*>(0x4c1a09))return false;
 auto get=[&](const void*address,void*data,SIZE_T size){SIZE_T copied{};require(ReadProcessMemory(child,address,data,size,&copied)&&copied==size,"Checkpoint child read failed");};
 auto put=[&](void*address,const void*data,SIZE_T size){SIZE_T copied{};require(WriteProcessMemory(child,address,data,size,&copied)&&copied==size,"Checkpoint child write failed");};
 unsigned pending{},seen{};DWORD child_owner{};get(&checkpoint_pending,&pending,4);get(&checkpoint_seen,&seen,4);get(&owner,&child_owner,4);
 require(pending==1&&!seen&&child_owner==event.dwThreadId,"Checkpoint owner/pending rejected");
 Handle thread(OpenThread(THREAD_GET_CONTEXT|THREAD_SET_CONTEXT|THREAD_QUERY_INFORMATION,FALSE,event.dwThreadId));require(thread.value!=nullptr,"Checkpoint thread open failed");
 CONTEXT actual{};actual.ContextFlags=CONTEXT_FULL|CONTEXT_FLOATING_POINT|CONTEXT_EXTENDED_REGISTERS;require(GetThreadContext(thread.value,&actual),"Actual stopped x86 CONTEXT unavailable");
 require(actual.Eip==0x4c1a0a&&actual.Esp==frame-12&&actual.Ebp==frame-12,"Actual provider return frame/PC rejected");
 std::uint8_t byte{};get(reinterpret_cast<void*>(0x4c1a09),&byte,1);require(byte==0xcc,"Checkpoint trap byte differs");
 // Retain the debugger's literal CONTEXT before the authored EIP rewind.
 put(&checkpoint,&actual,sizeof(actual));DWORD old{};require(VirtualProtectEx(child,reinterpret_cast<void*>(0x4c1000),4096,PAGE_EXECUTE_READWRITE,&old),"Checkpoint source writable transition failed");
 byte=0xd9;put(reinterpret_cast<void*>(0x4c1a09),&byte,1);DWORD ignored{};require(FlushInstructionCache(child,reinterpret_cast<void*>(0x4c1a09),1)&&VirtualProtectEx(child,reinterpret_cast<void*>(0x4c1000),4096,PAGE_EXECUTE_READ,&ignored),"Checkpoint source restore failed");
 seen=1;pending=0;put(&checkpoint_seen,&seen,4);put(&checkpoint_pending,&pending,4);
 // GetThreadContext's FX/FloatSave legacy metadata was measured zero. Never
 // write that observer projection back over the live guest FP environment.
 actual.Eip=0x4c1a09;actual.ContextFlags=CONTEXT_CONTROL;
 require(SetThreadContext(thread.value,&actual),"Original FSTP continuation restore failed");return true;
}
struct Region {void*base{};explicit Region(std::uint32_t a):base(mw34::original_broker::reserve_or_adopt(a)){}~Region(){if(base)VirtualFree(base,0,MEM_RELEASE);}};
static void protect(void*page,DWORD flags){DWORD prior{};require(VirtualProtect(page,4096,flags,&prior),"Page protection failed");}
static void capture_memory(std::array<std::uint8_t,memory_size>&b){for(unsigned i=0;i<4;++i)std::memcpy(b.data()+4096*i,reinterpret_cast<void*>(observed_pages[i]),4096);}
static void captures(Record&r){
 r.before=numeric_before;r.after=numeric_after;
 for(auto pair:{std::pair{r.guest_fx_before.data(),numeric_fx_before},std::pair{r.guest_fx_after.data(),numeric_fx_after},std::pair{r.host_fx_before.data(),numeric_host_fx},std::pair{r.host_fx_after.data(),numeric_host_after}})std::memcpy(pair.first,pair.second,512);
 for(auto pair:{std::pair{r.guest_env_before.data(),numeric_env_before},std::pair{r.guest_env_after.data(),numeric_env_after},std::pair{r.host_env_before.data(),numeric_host_env},std::pair{r.host_env_after.data(),numeric_host_env_after}})std::memcpy(pair.first,pair.second,28);
 std::memcpy(r.checkpoint_context.data(),&checkpoint,sizeof(checkpoint));r.tag.checkpoint_seen=checkpoint_seen;
}
int main(int argc,char**argv){try{
 SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
 if(argc==2&&std::string(argv[1])=="--check-protocol"){
  auto checks=protocol_controls();std::uint8_t fx[512]{},env[28]{};bool rejected{};try{seed(0x37f,0,8,0,fx,env);}catch(const std::exception&){rejected=true;}
  require(rejected,"Full stack admitted before execution");++checks;rejected=false;try{seed(0x340,0,0,0,fx,env);}catch(const std::exception&){rejected=true;}require(rejected,"Unmasked CW admitted");
  std::cout<<checks+1<<" protocol/domain checks passed before guest execution\n";return 0;
 }
 if(argc==3&&std::string(argv[1])=="--check-publication"){publication_controls(argv[2]);return 0;}
 bool directed=argc>1&&std::string(argv[argc-1])=="--directed";if(auto result=mw34::original_broker::dispatch(argc,argv,directed?6:5))return *result;
 require(argc==(directed?6:5),"Original numeric-max: exact-pack exact-game exact-provider fresh-output [--directed]");
 std::vector<std::unique_ptr<Region>> regions;for(auto base:mw34::original_broker::bases)regions.push_back(std::make_unique<Region>(base));
 const auto game=read(argv[2],2384384),provider=read(argv[3],565760),pack=read(argv[1],pack_size);
 require(game.size()==2384384&&sha256(game)==image_sha,"Exact game identity rejected");
 require(provider.size()==565760&&sha256(provider)=="91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a","Exact provider identity rejected");
 require(pack.size()==pack_size&&sha256(pack)==pack_sha,"Exact pack identity rejected");
 std::array<void*,7> pages{};
 for(unsigned i=0;i<7;++i){const auto off=12+i*4104;require(word<std::uint32_t>(pack.data()+off)==page_bases[i]&&word<std::uint32_t>(pack.data()+off+4)==page_permissions[i],"Exact page metadata rejected");pages[i]=VirtualAlloc(reinterpret_cast<void*>(page_bases[i]),4096,MEM_COMMIT,PAGE_READWRITE);require(pages[i]==reinterpret_cast<void*>(page_bases[i]),"Exact page commit failed");std::memcpy(pages[i],pack.data()+off+8,4096);}
 for(auto c:code_bindings){const auto&im=c.origin?provider:game;require(c.image_offset+c.size<=im.size()&&std::memcmp(reinterpret_cast<void*>(c.pc),im.data()+c.image_offset,c.size)==0,"Instruction/image binding rejected");}
 auto*stub=reinterpret_cast<std::uint8_t*>(capture_pc);require(std::memcmp(stub,"\xcc\xcc\xcc\xcc\xcc",5)==0,"Capture slot differs");stub[0]=0xe9;const auto delta=static_cast<std::uint32_t>(reinterpret_cast<std::uintptr_t>(&numeric_capture)-(capture_pc+5));std::memcpy(stub+1,&delta,4);
 for(unsigned i=0;i<7;++i){protect(pages[i],page_permissions[i]==1?PAGE_EXECUTE_READ:page_permissions[i]==0?PAGE_READONLY:PAGE_READWRITE);if(page_permissions[i]==1)require(FlushInstructionCache(GetCurrentProcess(),pages[i],4096),"Code cache flush failed");}
 owner=GetCurrentThreadId();
 Output out(argv[4]);Header h{};std::memcpy(h.magic,"MW4NMO01",8);h.version=1;h.count=records(directed);h.stride=sizeof(Record);h.pages=4;out.write(h);
 unsigned captured{};
 for(unsigned repeat=0;repeat<2;++repeat)for(unsigned input=0;input<(directed?inputs.size():1);++input)for(unsigned depth:{0U,1U,7U})for(unsigned sticky:{0U,1U,2U})for(auto cw:control_words)for(unsigned top:{0U,7U})for(unsigned entry:{0x780c10f0U,0x4c19f0U}){
  std::memcpy(pages[5],pack.data()+12+5*4104+8,4096);std::memcpy(pages[6],pack.data()+12+6*4104+8,4096);std::memset(reinterpret_cast<void*>(0x60b368),0xa5,44);std::memcpy(reinterpret_cast<void*>(frame),&capture_pc,4);
  if(directed){protect(pages[4],PAGE_READWRITE);std::memcpy(reinterpret_cast<void*>(0x78115004),&inputs[input],4);protect(pages[4],PAGE_READONLY);}
  seed(cw,top,depth,sticky,numeric_guest_fx,numeric_guest_env);numeric_env_ready=1;
  numeric_input={0x13579bdf,0x2468ace0,0x81726354,0x10293847,frame,0x92837465,0x56473829,0xaabbccdd,0x202,entry};
  checkpoint={};checkpoint_seen=0;checkpoint_pending=entry==0x4c19f0;checkpoint_error=0;
  if(checkpoint_pending){protect(pages[0],PAGE_EXECUTE_READWRITE);require(*reinterpret_cast<std::uint8_t*>(0x4c1a09)==0xd9,"Checkpoint instruction identity differs");*reinterpret_cast<std::uint8_t*>(0x4c1a09)=0xcc;require(FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(0x4c1a09),1),"Checkpoint flush failed");protect(pages[0],PAGE_EXECUTE_READ);}
  auto r=std::make_unique<Record>();r->tag={repeat,input,entry,cw,top,depth,sticky,0,0,0};capture_memory(r->memory_before);numeric_before={};numeric_after={};r->tag.status=execute();captures(*r);capture_memory(r->memory_after);r->tag.host_restored=host_restored(*r);out.write(*r);++captured;
  if(r->tag.status||!r->tag.host_restored||r->after.pc!=capture_pc||r->after.esp!=returned_esp||checkpoint_error||checkpoint_seen!=(entry==0x4c19f0)){
   out.commit();std::cerr<<"Actual original failed record="<<captured<<" status="<<r->tag.status<<" checkpoint="<<checkpoint_seen<<" observer_error="<<checkpoint_error<<'\n';return 1;
  }
  for(auto c:code_bindings){const auto&im=c.origin?provider:game;require(std::memcmp(reinterpret_cast<void*>(c.pc),im.data()+c.image_offset,c.size)==0,"Original selected instruction changed after checkpoint");}
 }
 require(captured==h.count,"Domain count differs");out.commit();std::cout<<captured<<" actual original provider/wrapper records; live-stack checkpoint has distinct Windows CONTEXT provenance\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
