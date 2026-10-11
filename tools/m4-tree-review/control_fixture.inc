// One literal tree root after the authentic connected bootstrap. This fixture
// preserves the caller boundary through catches and separately measured cleanup.
#include "current_pages.hpp"
using namespace mw34;
using namespace mw34::m4_mixed;
namespace {
constexpr unsigned tree_root=0x4b7f70;
struct alignas(16) Hardware {std::array<std::byte,512>fx{};std::array<std::byte,28>env{};};
void hardware(Hardware&h){__asm__ volatile("fxsave64 %0\n\tfnstenv %1\n\tfldenv %1":"=m"(h.fx),"=m"(h.env)::"memory");}
bool hardware_equal(const Hardware&a,const Hardware&b){
 bool same=!std::memcmp(a.fx.data(),b.fx.data(),5)&&!std::memcmp(a.fx.data()+24,b.fx.data()+24,4)&&a.env==b.env;
 for(unsigned k=0;k<8;++k)same=same&&!std::memcmp(a.fx.data()+32+k*16,b.fx.data()+32+k*16,10);
 return same&&!std::memcmp(a.fx.data()+256,b.fx.data()+256,160);
}
void rich_seed(Hardware&h){
 Hardware old{};hardware(old);unsigned mxcsr=0x5fa5;unsigned short cw=0xa7f;
 __asm__ volatile("fninit\n\tfld1\n\tfldpi\n\tfldz\n\tfld1\n\tfdivp\n\tfldcw %0\n\tldmxcsr %1"::"m"(cw),"m"(mxcsr):"memory","st","st(1)","st(2)","st(3)");hardware(h);
 __asm__ volatile("fxrstor64 %0\n\tfldenv %1"::"m"(old.fx),"m"(old.env):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)","xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");
 for(unsigned n=256;n<416;++n)h.fx[n]=std::byte((n*73+19)&255);
}
struct NativeBackingSink {
 capture_direct::Writer*w;std::string prefix;std::vector<unsigned>*aliases;
 static void sink(std::string_view name,std::span<const std::byte>bytes,void*context){
  if(name!="locale-allocations.bin")return;auto&x=*static_cast<NativeBackingSink*>(context);
  need(bytes.size()%128==0,"Complete actual private owner rows");
  for(std::size_t n=0;n<bytes.size();n+=128){std::array<std::uint64_t,16>row{};std::memcpy(row.data(),bytes.data()+n,128);
   if(row[1]&&std::find(x.aliases->begin(),x.aliases->end(),row[1])==x.aliases->end())x.aliases->push_back(unsigned(row[1]));
   if(row[8]){need(row[3]&&row[3]<=1024*1024,"Finite actual native capacity");x.w->append(x.prefix+"native-full-"+std::to_string(row[5])+".bin",reinterpret_cast<const void*>(row[8]),row[3]);}
  }
 }
};
void dump(Context&c,capture_direct::Writer&w,const std::string&prefix,std::vector<unsigned>&aliases){
 DirectPhaseWriter sink{&w,prefix};c.registry().dump(&DirectPhaseWriter::sink,&sink);
 NativeBackingSink native{&w,prefix,&aliases};c.registry().dump(&NativeBackingSink::sink,&native);
 w.append(prefix+"current-page-addresses.bin",mw34_tree_fixture::current_pages.data(),sizeof(mw34_tree_fixture::current_pages));
 std::array<std::byte,4096>b{};for(auto address:mw34_tree_fixture::current_pages){c.runtime().memory().read({address},b);w.append(prefix+"current-page-"+std::to_string(address)+".bin",b.data(),b.size());}
}
struct Task {Context*c;capture_direct::Writer*w;unsigned retry{},okay{},cleanup{},completed{};std::string prefix;std::vector<unsigned>aliases;std::vector<Native>records;};
thread_local Task*active_tree_task{};
}
#include "control_hooks.hpp"
namespace {
[[clang::noinline]] unsigned invoke(Task&t)noexcept{
 m4_spi_connected::ErrorBoundary errors;ni::NumericHostBoundary boundary(0x37f);
 try{if(t.retry)t.c->registry().replay(tree_root);else{t.okay=t.c->invoke_selected_table(0,0,0,t.records);t.completed=t.c->completed;}}
 catch(...){t.okay=0;}return t.okay;
}
#pragma pack(push,1)
struct Sample {
 std::array<std::uint64_t,32>tags{},owner_before{},owner_after{};
 std::array<std::byte,3504>state_before{},state_after{};
 std::array<std::byte,512>fx_before{},fx_after{};
 std::array<std::byte,40>cpu_before{},cpu_after{};
 Hardware host_before{},host_after{};
};
#pragma pack(pop)
}
extern "C" unsigned data_boundary_call(void*,void*,void*,void*);
extern "C" unsigned data_boundary_initialize(void*p)noexcept{
 auto&t=*static_cast<Task*>(p);auto&c=*t.c;active_tree_task=&t;
 c.before_phase=+[](Context&c,unsigned phase){need(active_tree_task&&phase==0,"One actual tree before phase");dump(c,*active_tree_task->w,active_tree_task->prefix+"actual-before-root/",active_tree_task->aliases);};
 c.after_phase=+[](Context&c,unsigned phase){need(active_tree_task&&phase==1,"One actual tree after phase");dump(c,*active_tree_task->w,active_tree_task->prefix+"actual-after-root/",active_tree_task->aliases);};
 (void)invoke(t);mw34_tree_controls::restore_actual();
 try{
  ni::NumericHostBoundary observer(0x37f);m4_spi_connected::ErrorBoundary errors;
  t.w->append(t.prefix+"actual-causal-State.bin",&c.state(),3504);t.w->append(t.prefix+"actual-causal-CPU.bin",&c.runtime().cpu(),40);t.w->append(t.prefix+"actual-causal-FX.bin",c.runtime().fx().data(),512);
  t.w->append(t.prefix+"actual-root-records.bin",t.records.data(),t.records.size()*sizeof(Native));
  t.w->append(t.prefix+"actual-context-failure.bin",c.failure_reason(),std::strlen(c.failure_reason()));
  const auto view=ni::view(c.state());t.w->append(t.prefix+"actual-causal-guest-ENV.bin",view.env.data(),view.env.size());
  dump(c,*t.w,t.prefix+"actual-live/",t.aliases);
  Hardware before{},after{};hardware(before);c.registry().finish();hardware(after);
  t.w->append(t.prefix+"actual-cleanup-hardware-before.bin",&before,sizeof(before));t.w->append(t.prefix+"actual-cleanup-hardware-after.bin",&after,sizeof(after));
  need(hardware_equal(before,after),"Actual normal/fault cleanup preserves caller FP environment");
  t.cleanup=!c.registry().live_handle();
  for(auto alias:t.aliases){bool gone{};try{(void)c.runtime().memory().load<unsigned char>({alias});}catch(const MemoryFault&e){gone=e.reason()==MemoryFaultReason::unmapped;}need(gone,"Every actual owner guest alias unmapped by cleanup");}
 }catch(...){t.cleanup=0;}
 active_tree_task=nullptr;return t.okay;
}

namespace {
void attempt(Context&c,capture_direct::Writer&w,unsigned retry){
 const unsigned selected=mw34_tree_controls::selected;const auto prefix="case-"+std::to_string(selected)+(retry?"/retry/":"/first/");
 Sample sample{};sample.owner_before=c.registry().summary();std::memcpy(sample.state_before.data(),&c.state(),3504);std::copy(c.runtime().fx().begin(),c.runtime().fx().end(),sample.fx_before.begin());std::memcpy(sample.cpu_before.data(),&c.runtime().cpu(),40);
 Hardware rich{},before{},after{};rich_seed(rich);Host restore(0x37f);Task t{&c,&w,retry,0,0,0,prefix};SetLastError(0x4d573354);std::uint64_t flags_before{},flags_after{};
 __asm__ volatile("pushfq\n\tpopq %0":"=r"(flags_before)::"memory");const auto result=data_boundary_call(&t,&before,&after,&rich);__asm__ volatile("pushfq\n\tpopq %0":"=r"(flags_after)::"memory");
 const auto error=GetLastError();const auto equal=hardware_equal(before,after);restore.restore();
 sample.owner_after=c.registry().summary();sample.host_before=before;sample.host_after=after;std::memcpy(sample.state_after.data(),&c.state(),3504);std::copy(c.runtime().fx().begin(),c.runtime().fx().end(),sample.fx_after.begin());std::memcpy(sample.cpu_after.data(),&c.runtime().cpu(),40);
 sample.tags={1,selected,retry,result,t.completed,t.cleanup,error,flags_before,flags_after,unsigned(equal),c.registry().fs_witnesses().size(),c.registry().mfc_witnesses().size(),unsigned(c.runtime().poisoned()),sample.owner_after[3],mw34_tree_controls::hits,mw34_tree_controls::mutations,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0};
 w.append(prefix+"sample.bin",&sample,sizeof(sample));dump(c,w,prefix+"actual-cleaned/",t.aliases);
 if(!retry){using namespace mw34_tree_controls;for(const auto&[n,b]:trigger)w.append(prefix+"trigger/"+n,b.data(),b.size());w.append(prefix+"trigger/private-before.bin",private_before.data(),private_before.size());w.append(prefix+"trigger/private-after.bin",private_after.data(),private_after.size());w.append(prefix+"trigger/private-name.bin",private_name.data(),private_name.size());w.append(prefix+"trigger/intervention.bin",intervention.data(),sizeof(intervention));w.append(prefix+"trigger/native40-before.bin",resource_before.data(),40);w.append(prefix+"trigger/native40-after.bin",resource_after.data(),40);const unsigned id[]{point_id,pc_id,hits,mutations};w.append(prefix+"trigger/identity.bin",id,sizeof(id));}
 need(equal,"Immediate outside-return strict hardware and ENV");need(error==0x4d573354&&!((flags_before^flags_after)&0x400),"Actual caller LastError and DF conservation");
 need(t.cleanup&&!sample.owner_after[10]&&!sample.owner_after[11]&&!sample.owner_after[15]&&!m4_onexit::active(),"All actual native allocations/CS/heap cleaned");
 if(retry){need(!result&&sample.owner_before==sample.owner_after,"Same cleaned Session refuses subsequent replay without work");need(sample.state_before==sample.state_after&&sample.fx_before==sample.fx_after&&sample.cpu_before==sample.cpu_after,"Refused retry conserves full machine");}
 else if(!selected)need(result&&t.completed==1&&sample.tags[10]==7&&sample.tags[11]==7,"Actual registered positive tree extent");
 else need(!result&&mw34_tree_controls::hits==1&&mw34_tree_controls::mutations==1&&sample.owner_after[3],"Exactly one actual tree causal intervention is refused");
}
}
int main(int argc,char**argv){try{
 need(argc==6,"Exact provider/fresh output arguments");auto game=old::read(argv[1],2384384),numeric=old::read(argv[2],565760),crt=old::read(argv[3],266293),mfc=old::read(argv[4],954128);
 need(old::sha256(numeric)==ni::provider_sha&&old::sha256(crt)=="2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7"&&old::sha256(mfc)=="5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8","Exact providers");
 capture_direct::Options options;options.reports_root=std::filesystem::current_path()/"reports";capture_direct::Writer w(argv[5],options);const unsigned header[]{1,18,36,sizeof(Sample),tree_root,3504,40,512,65};w.append("header.bin",header,sizeof(header));
 try{for(unsigned n=0;n<18;++n){std::cout<<"Tree scenario "<<n<<'\n'<<std::flush;mw34_tree_controls::reset(n);Context c(std::as_bytes(std::span{game}),std::as_bytes(std::span{numeric}),std::as_bytes(std::span{crt}),std::as_bytes(std::span{mfc}),0,0x37f,0);c.registry().test_hook=&mw34_tree_controls::observe<m4_onexit::Session>;attempt(c,w,0);c.registry().test_hook=nullptr;attempt(c,w,1);}
 const char done[]="Bounded actual Runtime tree controls passed; full125 acceptance is separate\n";w.append("COMPLETE.txt",done,sizeof(done)-1);w.finish();return 0;
 }catch(const std::exception&e){w.append("FAILURE.txt",e.what(),std::strlen(e.what()));w.finish();throw;}
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
