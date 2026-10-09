// Independent main over the exact frozen connected71 implementation and objects.
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
 if(mw34_onexit_review::selected!=12||mw34_onexit_review::hits||phase!=0)return;
 ++mw34_onexit_review::hits;c.runtime().memory().store<unsigned>({0x5bb670},0x78010a6d);
}
void review_after_selected(Context&c){
 check(mw34_onexit_review::selected==0,"Only ordinary string control completes selected71");
 const auto rows=c.registry().string_witnesses();check(rows.size()==16,"16 actual duplicates; null descriptor root bypasses strdup");
 for(const auto&w:rows){check(w[17]&&w[7]==w[16]&&w[10]==w[15]&&w[10]==w[23]&&w[28]&&w[29],"Each completed duplicate remains privately owned and mapped");mw34_onexit_review::add_alias(unsigned(w[10]));}
 const auto before=c.registry().summary();bool refused{};
 std::thread worker([&]{try{c.registry().finish();}catch(const std::exception&){refused=true;}});worker.join();
 check(refused&&before==c.registry().summary(),"Foreign thread refuses cleanup of16 live duplicate owners");++mw34_onexit_review::thread_checks;
 check(!c.registry().growth_witnesses().empty(),"Actual selected43 registry caused genuine growth");
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
  review_dump(*t.c,*t.writer,"case-"+std::to_string(mw34_onexit_review::selected)+(t.attempt?"/retry-live/":"/first-live/"));
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
 const auto fault=c.fault();const auto selected=mw34_onexit_review::selected;
 sample.tags={1,selected,unsigned(retry),result,c.completed,unsigned(c.failed()),unsigned(c.runtime().poisoned()),mw34_onexit_review::hits,mw34_onexit_review::thread_checks,
  oldcalls,c.runtime().calls().size(),oldcompleted,records.size(),error,unsigned(task.cleanup_ok),fault.phase,fault.pc,fault.address,fault.step,fault.kind,
  flags_before,flags_after,0,0,0,0,0,0,0,0,0,0};
 const auto prefix="case-"+std::to_string(selected)+(retry?"/retry":"/first");w.append(prefix+".bin",&sample,sizeof(sample));
 review_dump(c,w,prefix+"-cleaned/");
 if(!retry){
  const auto&a=mw34_onexit_review::cleanup_api_after;const auto id=prefix+"-cleanup-api-after";
  const std::array<std::uint64_t,11>v{a.target,a.named_target,a.owner,a.owner_named_target,a.region.base,a.region.bytes,a.region.allocation,a.region.state,a.region.type,a.region.protect,a.region.allocation_protect};
  w.append(id+".bin",v.data(),sizeof(v));w.append(id+"-module-path.bin",a.module_path.data(),a.module_path.size()*sizeof(wchar_t));w.append(id+"-module-sha.bin",a.module_sha.data(),a.module_sha.size());
 }
 if(!retry){w.append(prefix+"-trigger-string.bin",mw34_onexit_review::trigger_string.data(),sizeof(mw34_onexit_review::trigger_string));w.append(prefix+"-trigger-copy.bin",mw34_onexit_review::trigger_copy.data(),sizeof(mw34_onexit_review::trigger_copy));w.append(prefix+"-trigger-native-before.bin",mw34_onexit_review::trigger_native_before.data(),mw34_onexit_review::trigger_native_before.size());}
 check(review_hardware_equal(before,after),"Independent strict outside-return hardware preservation");
 check(error==0x4D573354&&!((flags_before^flags_after)&0x400),"Independent LastError and ABI DF preserved");
 // Fresh native preparation-r6 and later summary15 is the live handle. Earlier sealed
 // summaries retain the acquired historical pointer under their own schema.
 check(task.cleanup_ok&&!sample.owner_after[10]&&!sample.owner_after[11]&&!sample.owner_after[15],"Actual source owner cleanup complete");
 check(observation==nullptr&&ni::owner==nullptr&&m4_spi_connected::owner==nullptr&&!m4_onexit::active(),"Independent lexical source owner cleanup");
 if(!retry&&!selected){check(result&&c.completed==71&&records.size()==71,"Actual complete connected71 ordinary sequence");check(mw34_onexit_review::thread_checks==1,"One actual foreign-thread refusal observed");check(sample.owner_after[14]>=1,"Ordinary actual reallocation growth observed");}
 else if(retry){
  check(!result&&c.failed()&&fault.kind,"Consumed/poisoned connected entry refuses retry");
  check(oldcalls==c.runtime().calls().size()&&oldcompleted==c.completed,"Retry performs no further root routes");
  check(sample.owner_before==sample.owner_after,"Retry performs no additional native/source owner work");
  check(sample.state_before==sample.state_after&&sample.fx_before==sample.fx_after&&sample.cpu_before==sample.cpu_after,"Refused retry preserves complete carried machine");
  if(previous.kind)check(!std::memcmp(&previous,&fault,sizeof(fault)),"Original first fault retained on retry");
 }else{check(!result&&c.failed()&&fault.kind&&mw34_onexit_review::hits==1,"Exactly one actual independent causal refusal");check(records.size()==c.completed,"Fault retains completed source prefix");}
 if(!retry)for(unsigned n=0;n<records.size();++n)w.append("case-"+std::to_string(selected)+"/prefix-"+std::to_string(n)+".bin",&records[n],sizeof(Native));
}
}
int main(int argc,char**argv){try{
 check(argc==5,"Independent exact game/numeric/CRT/fresh direct output");
 auto game=old::read(argv[1],2384384),numeric=old::read(argv[2],565760),crt=old::read(argv[3],266293);
 check(old::sha256(numeric)==ni::provider_sha&&old::sha256(crt)=="2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7","Exact immutable providers");
 capture_direct::Options options;options.reports_root=std::filesystem::current_path()/"reports";capture_direct::Writer writer(argv[4],options);
 const unsigned header[]{1,14,28,sizeof(ReviewSample),sizeof(Native),32};writer.append("header.bin",header,sizeof(header));
 try{
 for(unsigned selected=0;selected<14;++selected){
  std::cout<<"Independent scenario "<<selected<<'\n'<<std::flush;
  mw34_onexit_review::selected=selected;mw34_onexit_review::hits=0;mw34_onexit_review::thread_checks=0;mw34_onexit_review::trigger_string={};mw34_onexit_review::trigger_copy={};mw34_onexit_review::trigger_native_before.clear();
  mw34_onexit_review::owned_guest_aliases.clear();
  Context context(std::as_bytes(std::span{game}),std::as_bytes(std::span{numeric}),std::as_bytes(std::span{crt}),0,0x37f,0);
  context.registry().test_hook=&mw34_onexit_review::observe<m4_onexit::Session>;context.after_selected=&review_after_selected;context.before_phase=&review_before_phase;
  std::vector<Native>records;records.reserve(71);review_attempt(context,writer,records,false);
  context.registry().test_hook=nullptr;context.after_selected=nullptr;context.before_phase=nullptr;review_attempt(context,writer,records,true);
 }
 const unsigned counts[]{mw34_onexit_review::checks,14,28};writer.append("counts.bin",counts,sizeof(counts));const char done[]="Independent connected71 onexit controls passed\n";writer.append("COMPLETE.txt",done,sizeof(done)-1);writer.finish();std::cout<<mw34_onexit_review::checks<<" checks;14 independent scenarios;28 actual attempts\n";return 0;
 }catch(const std::exception&e){writer.append("FAILURE.txt",e.what(),std::strlen(e.what()));writer.finish();throw;}
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
