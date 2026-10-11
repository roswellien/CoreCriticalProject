// Isolated exact four-root finite-vtable research controls after genuine source bootstrap.
#include "current_pages.hpp"
#include "hooks.hpp"
using namespace mw34;
using namespace mw34::m4_mixed;
namespace {
using mw34_onexit_review::check;
constexpr unsigned vtable_roots[]{0x40f0e0,0x4795f0,0x47f5f0,0x4b5220};
struct alignas(16) Hardware{std::array<std::byte,512>fx{};std::array<std::byte,28>env{};};
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
struct Task{Context*c;capture_direct::Writer*w;unsigned retry{},completed{},okay{},cleanup{},pointee_unmapped{};};
thread_local Task*task{};
// Same lexical caller boundary as the connected root harness, enclosing the
// authored source invocation AND its C++ catch. Naked throwing Session replay
// is outside this claim; the accepted109 control receipt preserves that failure.
[[clang::noinline]] unsigned invoke(Task&t)noexcept{
 m4_spi_connected::ErrorBoundary errors;ni::NumericHostBoundary boundary(0x37f);
 try{if(t.retry)t.c->registry().replay(vtable_roots[0]);else{t.c->registry().bootstrap();for(auto root:vtable_roots){t.c->registry().replay(root);++t.completed;}t.okay=1;}}
 catch(...){t.okay=0;}return t.okay;
}
struct NativeBackingSink{capture_direct::Writer*w;std::string prefix;static void sink(std::string_view name,std::span<const std::byte>bytes,void*ctx){if(name!="locale-allocations.bin")return;auto&x=*static_cast<NativeBackingSink*>(ctx);check(bytes.size()%128==0,"Whole actual private owner rows");for(std::size_t n=0;n<bytes.size();n+=128){std::array<std::uint64_t,16>row{};std::memcpy(row.data(),bytes.data()+n,128);if(row[8]){check(row[3]&&row[3]<=1024*1024,"Finite full actual native extent");x.w->append(x.prefix+"native-full-"+std::to_string(row[5])+".bin",reinterpret_cast<const void*>(row[8]),row[3]);}}}};
void dump(Context&c,capture_direct::Writer&w,const std::string&prefix){c.registry().dump(&mw34_onexit_review::receive,nullptr);DirectPhaseWriter sink{&w,prefix};c.registry().dump(&DirectPhaseWriter::sink,&sink);NativeBackingSink native{&w,prefix};c.registry().dump(&NativeBackingSink::sink,&native);w.append(prefix+"current-page-addresses.bin",mw34_vtable_controls::current_pages.data(),sizeof(mw34_vtable_controls::current_pages));std::array<std::byte,4096>b{};for(auto address:mw34_vtable_controls::current_pages){c.runtime().memory().read({address},b);w.append(prefix+"current-page-"+std::to_string(address)+".bin",b.data(),b.size());}}
void append_trigger(capture_direct::Writer&w,const std::string&p){
 using namespace mw34_vtable_controls;
 w.append(p+"calls.bin",trigger.calls.data(),trigger.calls.size()*256);w.append(p+"stores.bin",trigger.stores.data(),trigger.stores.size()*128);
 w.append(p+"read.bin",trigger.read.data(),sizeof(trigger.read));w.append(p+"vptr.bin",trigger.vptr.data(),sizeof(trigger.vptr));w.append(p+"store.bin",trigger.store.data(),sizeof(trigger.store));w.append(p+"active.bin",&trigger.active,4);
 w.append(p+"State.bin",trigger_state.data(),trigger_state.size());w.append(p+"FX.bin",trigger_fx.data(),trigger_fx.size());w.append(p+"CPU.bin",trigger_cpu.data(),trigger_cpu.size());w.append(p+"stack.bin",trigger_stack.data(),trigger_stack.size());w.append(p+"guest-ENV.bin",trigger_env.data(),trigger_env.size());
 w.append(p+"TIB.bin",trigger_tib.data(),sizeof(trigger_tib));w.append(p+"record.bin",trigger_record.data(),sizeof(trigger_record));w.append(p+"frame.bin",trigger_frame.data(),sizeof(trigger_frame));
 w.append(p+"private-before.bin",private_before.data(),private_before.size());w.append(p+"private-after.bin",private_after.data(),private_after.size());w.append(p+"private-name.bin",private_name.data(),private_name.size());w.append(p+"actual-intervention.bin",actual_intervention.data(),sizeof(actual_intervention));const unsigned id[]{trigger_point,trigger_PC,mutation_hits};w.append(p+"identity.bin",id,sizeof(id));
}
#pragma pack(push,1)
struct Sample{std::array<std::uint64_t,32>tags{},owner_before{},owner_after{};std::array<std::byte,3504>state_before{},state_after{};std::array<std::byte,512>fx_before{},fx_after{};std::array<std::byte,40>cpu_before{},cpu_after{};Hardware host_before{},host_after{};};
#pragma pack(pop)
}
extern "C" unsigned data_boundary_call(void*,void*,void*,void*);
extern "C" unsigned data_boundary_initialize(void*p)noexcept{
 auto&t=*static_cast<Task*>(p);task=&t;auto&c=*t.c;const auto stem="case-"+std::to_string(mw34_vtable_controls::selected)+(t.retry?"/retry":"/first");
 (void)invoke(t);
 try{
  // Begin after actual candidate calls have returned; preserve their precise
  // outside hardware through subsequent diagnostics and cleanup work.
  ni::NumericHostBoundary observer(0x37f);m4_spi_connected::ErrorBoundary errors;
  t.w->append(stem+"-causal-State.bin",&c.state(),3504);t.w->append(stem+"-causal-CPU.bin",&c.runtime().cpu(),40);t.w->append(stem+"-causal-FX.bin",c.runtime().fx().data(),512);
  const auto causal_view=ni::view(c.state());t.w->append(stem+"-causal-guest-ENV.bin",causal_view.env.data(),causal_view.env.size());
  std::array<std::byte,4096>stack{};c.runtime().memory().read({0x20001000},stack);t.w->append(stem+"-causal-stack.bin",stack.data(),stack.size());
  dump(c,*t.w,stem+"-live/");
  Hardware cleanup_before{},cleanup_after{};hardware(cleanup_before);c.registry().finish();hardware(cleanup_after);
  t.w->append(stem+"-cleanup-hardware-before.bin",&cleanup_before,sizeof(cleanup_before));t.w->append(stem+"-cleanup-hardware-after.bin",&cleanup_after,sizeof(cleanup_after));check(hardware_equal(cleanup_before,cleanup_after),"Exact normal/fault source-owner cleanup hardware");
  mw34_onexit_review::cleanup_api_after=mw34_onexit_review::pressure_identity("HeapDestroy",reinterpret_cast<std::uintptr_t>(&::HeapDestroy));
  t.cleanup=!c.registry().live_handle();
  for(auto alias:mw34_onexit_review::owned_guest_aliases){bool gone{};try{(void)c.runtime().memory().load<unsigned char>({alias});}catch(const MemoryFault&e){gone=e.reason()==MemoryFaultReason::unmapped;}check(gone,"Actual private guest alias is unmapped after cleanup");}
 }catch(...){t.cleanup=0;}
 task=nullptr;return t.okay;
}
namespace {
void attempt(Context&c,capture_direct::Writer&w,unsigned retry,unsigned completed){
 Sample sample{};sample.owner_before=c.registry().summary();std::memcpy(sample.state_before.data(),&c.state(),3504);std::copy(c.runtime().fx().begin(),c.runtime().fx().end(),sample.fx_before.begin());std::memcpy(sample.cpu_before.data(),&c.runtime().cpu(),40);
 Hardware rich{},before{},after{};rich_seed(rich);Host restore(0x37f);Task t{&c,&w,retry,completed};SetLastError(0x4d573354);std::uint64_t flags_before{},flags_after{};
 __asm__ volatile("pushfq\n\tpopq %0":"=r"(flags_before)::"memory");const auto result=data_boundary_call(&t,&before,&after,&rich);__asm__ volatile("pushfq\n\tpopq %0":"=r"(flags_after)::"memory");const auto error=GetLastError();const bool boundary_equal=hardware_equal(before,after);restore.restore();
 sample.owner_after=c.registry().summary();sample.host_before=before;sample.host_after=after;std::memcpy(sample.state_after.data(),&c.state(),3504);std::copy(c.runtime().fx().begin(),c.runtime().fx().end(),sample.fx_after.begin());std::memcpy(sample.cpu_after.data(),&c.runtime().cpu(),40);
 const auto selected=mw34_vtable_controls::selected;sample.tags={1,selected,retry,result,t.completed,mw34_vtable_controls::hits,t.cleanup,error,flags_before,flags_after,c.registry().fs_witnesses().size(),c.registry().mfc_witnesses().size(),c.registry().summary()[16],c.registry().summary()[17],c.registry().summary()[3],unsigned(c.runtime().poisoned()),unsigned(boundary_equal),t.pointee_unmapped,0,0,0,0,0,0,0,0,0,0,0,0,0,0};
 const auto prefix="case-"+std::to_string(selected)+(retry?"/retry":"/first");w.append(prefix+".bin",&sample,sizeof(sample));dump(c,w,prefix+"-cleaned/");
 if(!retry){append_trigger(w,prefix+"-trigger/");const auto&a=mw34_onexit_review::cleanup_api_after;const std::array<std::uint64_t,11>id{a.target,a.named_target,a.owner,a.owner_named_target,a.region.base,a.region.bytes,a.region.allocation,a.region.state,a.region.type,a.region.protect,a.region.allocation_protect};w.append(prefix+"-cleanup-api-after.bin",id.data(),sizeof(id));w.append(prefix+"-cleanup-api-path.bin",a.module_path.data(),a.module_path.size()*sizeof(wchar_t));w.append(prefix+"-cleanup-api-sha.bin",a.module_sha.data(),a.module_sha.size());}
 check(boundary_equal,"Immediate strict actual outside-return FX/ENV/nonvolatileSIMD");check(hardware_equal(sample.host_before,sample.host_after),"Retained raw outside-return hardware matches immediate predicate");check(error==0x4d573354&&!((flags_before^flags_after)&0x400),"Caller LastError/DF are conserved");check(t.cleanup&&!sample.owner_after[10]&&!sample.owner_after[11]&&!sample.owner_after[15],"All actual native owners and heap cleaned");check(!m4_onexit::active(),"Lexical source authority released");
 if(retry){check(!result&&sample.owner_before==sample.owner_after,"Same finished/poisoned Session refuses additional source/native work");check(sample.state_before==sample.state_after&&sample.fx_before==sample.fx_after&&sample.cpu_before==sample.cpu_after,"Refused same-spec retry conserves complete machine");}
 else if(!selected){check(result&&t.completed==4&&sample.tags[10]==1&&!sample.tags[11]&&mw34_vtable_controls::snapshot(c.registry()).calls.size()==6&&!c.registry().string_witnesses().size(),"Actual isolated four-root six-indirect-call extent");}
 else check(!result&&mw34_vtable_controls::hits==1&&sample.owner_after[3],"Exactly one genuine targeted finite vtable source refusal");
}
}
int main(int argc,char**argv){try{
 check(argc==6,"Exact game/numeric/CRT/MFC/fresh capture output");auto game=old::read(argv[1],2384384),numeric=old::read(argv[2],565760),crt=old::read(argv[3],266293),mfc=old::read(argv[4],954128);
 check(old::sha256(numeric)==ni::provider_sha&&old::sha256(crt)=="2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7"&&old::sha256(mfc)=="5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8","Exact immutable providers");
 capture_direct::Options options;options.reports_root=std::filesystem::current_path()/"reports";capture_direct::Writer w(argv[5],options);const unsigned header[]{1,27,54,sizeof(Sample),4,6};w.append("header.bin",header,sizeof(header));
 try{for(unsigned selected=0;selected<27;++selected){std::cout<<"Vtable scenario "<<selected<<'\n'<<std::flush;mw34_vtable_controls::selected=selected;mw34_vtable_controls::hits=0;mw34_vtable_controls::mutation_hits=0;mw34_vtable_controls::trigger={};mw34_vtable_controls::trigger_frame={};mw34_vtable_controls::trigger_record={};mw34_vtable_controls::private_before.clear();mw34_vtable_controls::private_after.clear();mw34_vtable_controls::private_name.clear();mw34_vtable_controls::actual_intervention={};mw34_vtable_controls::trigger_point=mw34_vtable_controls::trigger_PC=0;mw34_onexit_review::owned_guest_aliases.clear();
  Context c(std::as_bytes(std::span{game}),std::as_bytes(std::span{numeric}),std::as_bytes(std::span{crt}),std::as_bytes(std::span{mfc}),0,0x37f,0);c.registry().test_hook=&mw34_vtable_controls::observe<m4_onexit::Session>;attempt(c,w,0,0);c.registry().test_hook=nullptr;attempt(c,w,1,0);
 }const unsigned counts[]{mw34_onexit_review::checks,27,54};w.append("counts.bin",counts,sizeof(counts));const char done[]="Bounded four-root finite-vtable research controls passed; canonical120 is separate\n";w.append("COMPLETE.txt",done,sizeof(done)-1);w.finish();return 0;}catch(const std::exception&e){w.append("FAILURE.txt",e.what(),std::strlen(e.what()));w.finish();throw;}
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
