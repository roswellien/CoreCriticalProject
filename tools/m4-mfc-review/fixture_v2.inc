// Independent main over the exact frozen connected103 implementation and objects.
#include "fixture_hooks_v2.hpp"
using namespace mw34;
using namespace mw34::m4_mixed;
namespace {
using mw34_onexit_review::check;
struct alignas(16) ReviewHardware{std::array<std::byte,512>fx{};std::array<std::byte,28>env{};};
void review_rich_seed(ReviewHardware&h){
 ReviewHardware old{};__asm__ volatile("fxsave64 %0\n\tfnstenv %1\n\tfldenv %1":"=m"(old.fx),"=m"(old.env)::"memory");
 unsigned mxcsr=0x5fa5;unsigned short cw=0xa7f;
 __asm__ volatile("fninit\n\tfld1\n\tfldpi\n\tfldz\n\tfld1\n\tfdivp\n\tfldcw %0\n\tldmxcsr %1"::"m"(cw),"m"(mxcsr):"memory","st","st(1)","st(2)","st(3)");
 __asm__ volatile("fxsave64 %0\n\tfnstenv %1\n\tfldenv %1":"=m"(h.fx),"=m"(h.env)::"memory");
 __asm__ volatile("fxrstor64 %0\n\tfldenv %1"::"m"(old.fx),"m"(old.env):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)","xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");
 for(unsigned i=256;i<416;++i)h.fx[i]=std::byte((i*73+19)&255);
}
bool review_hardware_equal(const ReviewHardware&a,const ReviewHardware&b){
 bool okay=!std::memcmp(a.fx.data(),b.fx.data(),5)&&!std::memcmp(a.fx.data()+24,b.fx.data()+24,4)&&a.env==b.env;
 for(unsigned i=0;i<8;++i)okay=okay&&!std::memcmp(a.fx.data()+32+i*16,b.fx.data()+32+i*16,10);
 return okay&&!std::memcmp(a.fx.data()+256,b.fx.data()+256,160);
}
struct ReviewTask{Context*c;std::vector<Native>*records;capture_direct::Writer*writer;unsigned attempt;bool cleanup_ok{};};
thread_local ReviewTask*review_task{};
void review_dump(Context&c,capture_direct::Writer&w,const std::string&prefix){c.registry().dump(&mw34_onexit_review::receive,nullptr);DirectPhaseWriter direct{&w,prefix};c.registry().dump(&DirectPhaseWriter::sink,&direct);}
void review_before_phase(Context&c,unsigned phase){
 if(mw34_mfc_review::selected!=1||mw34_mfc_review::hits||phase!=0)return;
 c.runtime().memory().protect({0x5bb000},Permissions::read|Permissions::write);c.runtime().memory().store<unsigned>({0x5bb4bc},0x5f401ea0);c.runtime().memory().protect({0x5bb000},Permissions::read);++mw34_mfc_review::hits;
}
void review_probe(Context&c,unsigned argument){
 const auto oldsp=c.state().gpr.rsp.dword;const auto sp=oldsp-4;c.runtime().memory().store<unsigned>({sp},argument);c.state().gpr.rsp.dword=sp;c.runtime().cpu().esp=sp;++mw34_mfc_review::probe_calls;
 const std::array<std::uint64_t,7>probe_input{1,mw34_mfc_review::selected==19?0x5f401ea0u:0x5f401782u,c.state().gpr.rsp.dword,c.runtime().cpu().esp,c.runtime().memory().load<unsigned>({sp}),0xffffff40u,sp-4};mw34_mfc_review::probe_inputs.push_back(probe_input);
 c.registry().probe_mfc(mw34_mfc_review::selected==19?0x5f401ea0:0x5f401782);c.state().gpr.rsp.dword=oldsp;c.runtime().cpu().esp=oldsp;
}
void review_after_phase(Context&c,unsigned completed){
 const auto selected=mw34_mfc_review::selected;if(completed!=1||selected<14||selected>19)return;
 const auto rows=c.registry().mfc_witnesses();check(rows.size()==1&&rows[0][16]&&rows[0][21],"First genuine object is live after completed constructor");const auto guest=unsigned(rows[0][16]);
 if(selected>=16){++mw34_mfc_review::hits;mw34_mfc_review::trigger_mfc=rows[0];}
 if(selected==18)review_probe(c,guest);
 review_probe(c,selected==16?guest+4:selected==17?0x603fd8:selected==19?1048577:guest);
 check(false,"Intended original MFC research refusal was not reached");
}
void review_after_selected(Context&c){
 check(mw34_mfc_review::selected==0,"Only ordinary MFC control completes selected103");
 const auto rows=c.registry().mfc_witnesses();check(rows.size()==35,"35 actual MFC calls across32 initializers");
 for(const auto&w:rows){check(w[21]&&w[16]&&w[17]&&!w[30]&&w[23]==1,"Each source object remains privately owned and published once");mw34_onexit_review::add_alias(unsigned(w[16]));}
 const auto strings=c.registry().string_witnesses();check(strings.size()==16,"All16 accepted strings carried");for(const auto&w:strings)mw34_onexit_review::add_alias(unsigned(w[10]));
 const auto before=c.registry().summary();bool refused{};
 std::thread worker([&]{try{c.registry().finish();}catch(const std::exception&){refused=true;}});worker.join();
 check(refused&&before==c.registry().summary(),"Foreign thread refuses cleanup of all live private objects");++mw34_mfc_review::thread_checks;
 check(!c.registry().growth_witnesses().empty(),"Actual75 registry entries caused genuine growth");
 for(const auto&g:c.registry().growth_witnesses()){mw34_onexit_review::add_alias(unsigned(g[3]));mw34_onexit_review::add_alias(unsigned(g[13]));}
}
#pragma pack(push,1)
struct ReviewSample{
 std::array<std::uint64_t,32>tags{},owner_before{},owner_after{};
 std::array<std::byte,3504>state_before{},state_after{};
 std::array<std::byte,512>fx_before{},fx_after{};
 std::array<std::byte,40>cpu_before{},cpu_after{};
 ReviewHardware host_before{},host_after{};
};
#pragma pack(pop)
}
extern "C" unsigned data_boundary_call(void*,void*,void*,void*);
extern "C" unsigned data_boundary_initialize(void*p)noexcept{
 auto&t=*static_cast<ReviewTask*>(p);review_task=&t;
 const unsigned okay=t.c->invoke_selected_table(0,0,0,*t.records);
 try{
  // Begin only after the candidate returned. Preserve that exact return
  // hardware through subsequent observer/dump/cleanup work; this cannot repair
  // any mismatch already returned by invoke_selected_table.
  ni::NumericHostBoundary observer_boundary(0x37f);m4_spi_connected::ErrorBoundary observer_error;
  if(!t.attempt){const auto stem="case-"+std::to_string(mw34_mfc_review::selected)+"/first-causal-";t.writer->append(stem+"state.bin",&t.c->state(),3504);std::array<std::byte,4096>stack{};t.c->runtime().memory().read({0x20001000},stack);t.writer->append(stem+"stack.bin",stack.data(),stack.size());const std::array<unsigned,3>inputs{t.c->runtime().memory().load<unsigned>({0x603fdc}),t.c->runtime().memory().load<unsigned>({0x5bb4bc}),t.c->runtime().memory().load<unsigned>({0x5f498970})};t.writer->append(stem+"inputs.bin",inputs.data(),sizeof(inputs));t.writer->append(stem+"probe-inputs.bin",mw34_mfc_review::probe_inputs.data(),mw34_mfc_review::probe_inputs.size()*sizeof(mw34_mfc_review::probe_inputs[0]));}
  review_dump(*t.c,*t.writer,"case-"+std::to_string(mw34_mfc_review::selected)+(t.attempt?"/retry-live/":"/first-live/"));
  t.c->registry().finish();mw34_onexit_review::cleanup_api_after=mw34_onexit_review::pressure_identity("HeapDestroy",reinterpret_cast<std::uintptr_t>(&::HeapDestroy));t.cleanup_ok=!t.c->registry().live_handle();
  for(const auto alias:mw34_onexit_review::owned_guest_aliases){
   bool unmapped{};try{(void)t.c->runtime().memory().load<unsigned char>({alias});}
   catch(const MemoryFault&e){unmapped=e.reason()==MemoryFaultReason::unmapped;}
   check(unmapped,"Independent actual old/new owned guest aliases are unmapped after cleanup");
  }
 }catch(...){t.cleanup_ok=false;}
 review_task=nullptr;return okay;
}
namespace {
void review_attempt(Context&c,capture_direct::Writer&w,std::vector<Native>&records,bool retry){
 ReviewSample sample{};sample.owner_before=c.registry().summary();std::memcpy(sample.state_before.data(),&c.state(),3504);
 std::copy(c.runtime().fx().begin(),c.runtime().fx().end(),sample.fx_before.begin());std::memcpy(sample.cpu_before.data(),&c.runtime().cpu(),40);
 const auto previous=c.fault();const auto oldcalls=c.runtime().calls().size();const auto oldcompleted=c.completed;
 ReviewHardware rich{},before{},after{};review_rich_seed(rich);Host restore(0x37f);
 ReviewTask task{&c,&records,&w,unsigned(retry)};SetLastError(0x4D573354);
 std::uint64_t flags_before{},flags_after{};__asm__ volatile("pushfq\n\tpopq %0":"=r"(flags_before)::"memory");
 const auto result=data_boundary_call(&task,&before,&after,&rich);
 __asm__ volatile("pushfq\n\tpopq %0":"=r"(flags_after)::"memory");const auto error=GetLastError();restore.restore();
 sample.host_before=before;sample.host_after=after;sample.owner_after=c.registry().summary();
 std::memcpy(sample.state_after.data(),&c.state(),3504);std::copy(c.runtime().fx().begin(),c.runtime().fx().end(),sample.fx_after.begin());std::memcpy(sample.cpu_after.data(),&c.runtime().cpu(),40);
 const auto fault=c.fault();const auto selected=mw34_mfc_review::selected;
 sample.tags={1,selected,unsigned(retry),result,c.completed,unsigned(c.failed()),unsigned(c.runtime().poisoned()),mw34_mfc_review::hits,mw34_mfc_review::thread_checks,
  oldcalls,c.runtime().calls().size(),oldcompleted,records.size(),error,unsigned(task.cleanup_ok),fault.phase,fault.pc,fault.address,fault.step,fault.kind,
  flags_before,flags_after,mw34_mfc_review::probe_calls,0,0,0,0,0,0,0,0,0};
 const auto prefix="case-"+std::to_string(selected)+(retry?"/retry":"/first");w.append(prefix+".bin",&sample,sizeof(sample));
 review_dump(c,w,prefix+"-cleaned/");
 if(!retry){
  const auto&a=mw34_onexit_review::cleanup_api_after;const auto id=prefix+"-cleanup-api-after";
  const std::array<std::uint64_t,11>v{a.target,a.named_target,a.owner,a.owner_named_target,a.region.base,a.region.bytes,a.region.allocation,a.region.state,a.region.type,a.region.protect,a.region.allocation_protect};
  w.append(id+".bin",v.data(),sizeof(v));w.append(id+"-module-path.bin",a.module_path.data(),a.module_path.size()*sizeof(wchar_t));w.append(id+"-module-sha.bin",a.module_sha.data(),a.module_sha.size());
 }
 if(!retry){w.append(prefix+"-trigger-mfc.bin",mw34_mfc_review::trigger_mfc.data(),sizeof(mw34_mfc_review::trigger_mfc));w.append(prefix+"-trigger-store.bin",mw34_mfc_review::trigger_store.data(),sizeof(mw34_mfc_review::trigger_store));w.append(prefix+"-trigger-native-before.bin",mw34_mfc_review::trigger_native_before.data(),mw34_mfc_review::trigger_native_before.size());w.append(prefix+"-trigger-native-after.bin",mw34_mfc_review::trigger_native_after.data(),mw34_mfc_review::trigger_native_after.size());}
 check(review_hardware_equal(before,after),"Independent strict outside-return hardware preservation");
 check(error==0x4D573354&&!((flags_before^flags_after)&0x400),"Independent LastError and ABI DF preserved");
 // Fresh native preparation-r6 and later summary15 is the live handle. Earlier sealed
 // summaries retain the acquired historical pointer under their own schema.
 check(task.cleanup_ok&&!sample.owner_after[10]&&!sample.owner_after[11]&&!sample.owner_after[15],"Actual source owner cleanup complete");
 check(observation==nullptr&&ni::owner==nullptr&&m4_spi_connected::owner==nullptr&&!m4_onexit::active(),"Independent lexical source owner cleanup");
 if(!retry&&!selected){check(result&&c.completed==103&&records.size()==103,"Actual complete connected103 ordinary sequence");check(mw34_mfc_review::thread_checks==1,"One actual foreign-thread refusal observed");check(sample.owner_after[14]>=1,"Ordinary actual reallocation growth observed");}
 else if(retry){
  check(!result&&c.failed()&&fault.kind,"Consumed/poisoned connected entry refuses retry");
  check(oldcalls==c.runtime().calls().size()&&oldcompleted==c.completed,"Retry performs no further root routes");
  check(sample.owner_before==sample.owner_after,"Retry performs no additional native/source owner work");
  check(sample.state_before==sample.state_after&&sample.fx_before==sample.fx_after&&sample.cpu_before==sample.cpu_after,"Refused retry preserves complete carried machine");
  if(previous.kind)check(!std::memcmp(&previous,&fault,sizeof(fault)),"Original first fault retained on retry");
 }else{check(!result&&c.failed()&&fault.kind&&mw34_mfc_review::hits==1,"Exactly one actual independent causal refusal");check(records.size()==c.completed,"Fault retains completed source prefix");}
 if(!retry)for(unsigned n=0;n<records.size();++n)w.append("case-"+std::to_string(selected)+"/prefix-"+std::to_string(n)+".bin",&records[n],sizeof(Native));
}
}
int main(int argc,char**argv){try{
 check(argc==6,"Independent exact game/numeric/CRT/MFC/fresh direct output");
 auto game=old::read(argv[1],2384384),numeric=old::read(argv[2],565760),crt=old::read(argv[3],266293),mfc=old::read(argv[4],954128);
 check(old::sha256(numeric)==ni::provider_sha&&old::sha256(crt)=="2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7","Exact immutable providers");
 capture_direct::Options options;options.reports_root=std::filesystem::current_path()/"reports";check(old::sha256(mfc)=="5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8","Exact immutable MFC source");capture_direct::Writer writer(argv[5],options);
 const unsigned header[]{1,21,42,sizeof(ReviewSample),sizeof(Native),35};writer.append("header.bin",header,sizeof(header));
 try{
 for(unsigned selected=0;selected<21;++selected){
  std::cout<<"Independent scenario "<<selected<<'\n'<<std::flush;
  mw34_mfc_review::selected=selected;mw34_mfc_review::hits=0;mw34_mfc_review::thread_checks=0;mw34_mfc_review::trigger_mfc={};mw34_mfc_review::trigger_store={};mw34_mfc_review::probe_calls=0;mw34_mfc_review::probe_inputs.clear();mw34_mfc_review::trigger_native_before.clear();mw34_mfc_review::trigger_native_after.clear();
  mw34_onexit_review::owned_guest_aliases.clear();
  Context context(std::as_bytes(std::span{game}),std::as_bytes(std::span{numeric}),std::as_bytes(std::span{crt}),std::as_bytes(std::span{mfc}),0,0x37f,0);
  context.registry().test_hook=&mw34_mfc_review::observe<m4_onexit::Session>;context.after_selected=&review_after_selected;context.before_phase=&review_before_phase;context.after_phase=&review_after_phase;
  std::vector<Native>records;records.reserve(103);review_attempt(context,writer,records,false);
  context.registry().test_hook=nullptr;context.after_selected=nullptr;context.before_phase=nullptr;context.after_phase=nullptr;review_attempt(context,writer,records,true);
 }
 const unsigned counts[]{mw34_onexit_review::checks,21,42};writer.append("counts.bin",counts,sizeof(counts));const char done[]="Independent connected103 MFC controls passed\n";writer.append("COMPLETE.txt",done,sizeof(done)-1);writer.finish();std::cout<<mw34_onexit_review::checks<<" checks;21 independent scenarios;42 actual attempts\n";return 0;
 }catch(const std::exception&e){writer.append("FAILURE.txt",e.what(),std::strlen(e.what()));writer.finish();throw;}
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
