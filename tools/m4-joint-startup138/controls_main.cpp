// Current Context and source providers, renamed positive main never invoked.
#define main mw34_context_controls_unused_positive_main
#include "native_main.cpp"
#undef main

namespace context_control {
using namespace mw34;using m4_mixed::Context;using m4_mixed::Native;
struct Writer {
 std::filesystem::path out;std::string prefix;
 static void sink(std::string_view name,std::span<const std::byte>bytes,void*p){auto&w=*static_cast<Writer*>(p);const auto file=w.out/(w.prefix+std::string(name));need(!std::filesystem::exists(file),"Unique immutable ordinary Context output");std::filesystem::create_directories(file.parent_path());std::ofstream stream(file,std::ios::binary);need(bool(stream),"Current Context ordinary output open");stream.write(reinterpret_cast<const char*>(bytes.data()),bytes.size());need(bool(stream),"Complete current Context ordinary output");}
 void data(std::string_view name,const void*p,std::size_t n){sink(name,std::span(static_cast<const std::byte*>(p),n),this);}
};
struct Injection {Writer*writer;unsigned mode;bool injected{};};
static thread_local Injection*injection{};
static void before_phase(Context&c,unsigned phase){
 if(phase!=16)return;need(injection&&!injection->injected&&c.completed==16,"One actual table-ordered second-widget control after complete owned-font prefix");injection->injected=true;auto&w=*injection->writer;c.control_snapshot("input-before");auto&r=c.runtime();auto&s=c.state();
 auto protect_image=[&](unsigned a,Permissions p){for(const auto&region:r.image_metadata().mapped_regions)if(region.start.value<=a&&std::uint64_t(a)<std::uint64_t(region.start.value)+region.size){r.memory().protect(region.start,p);return region.start.value;}throw std::runtime_error("Control belongs to current admitted image region");};
 unsigned address{},prior{},after{},width{},region{};const auto mode=injection->mode;
 if(mode==1){address=unsigned(reinterpret_cast<const std::byte*>(&s.addr.ds_base.dword)-r.remill_state().data());prior=s.addr.ds_base.dword;after=4;width=4;s.addr.ds_base.dword=after;}
 if(mode==2){prior=r.cpu().eflags;after=prior|0x400;address=0;width=4;s.aflag.df=1;s.rflag.flat|=0x400;r.cpu().eflags=after;}
 if(mode==3){address=0x5bb070;width=4;prior=r.memory().load<unsigned>({address});region=protect_image(address,Permissions::read|Permissions::write);r.memory().store<unsigned>({address},0);after=0;protect_image(address,Permissions::read);}
 if(mode==4){address=0x40ef50;width=1;prior=r.memory().load<std::uint8_t>({address});region=protect_image(address,Permissions::read|Permissions::write);after=prior^1;r.memory().store<std::uint8_t>({address},static_cast<std::uint8_t>(after));protect_image(address,Permissions::read|Permissions::execute);}
 if(mode==5){address=0x5fc838;region=protect_image(address,Permissions::read);}
 if(mode==6){address=region=0x20001000;r.memory().protect({address},Permissions::read);}
 if(mode==7){address=region=r.fs_base().value;r.memory().protect(r.fs_base(),Permissions::read);}
 if(mode==8){c.control_route_override=1;prior=0;after=1;width=4;}
 const std::array<unsigned,9>cause{1,mode,phase,0x40ef50,address,width,prior,after,region};w.data("cause.bin",cause.data(),sizeof(cause));c.control_snapshot("input-after");
}
struct Task {Context*context;unsigned operation,repeat,top;std::vector<Native>*records;bool completed{};std::string error;};
}
extern "C" void context_controls_guarded(context_control::Task*p)noexcept{
 try{if(p->operation==0)p->completed=p->context->invoke_selected_table(0,p->repeat,p->top,*p->records);else{p->context->cleanup_widgets();p->context->registry().finish();p->completed=true;}}catch(const std::exception&e){p->error=e.what();}catch(...){p->error="Unknown current Context hardware-boundary exception";}
}
extern "C" void context_controls_hardware_call(context_control::Task*,void*);
int main(int argc,char**argv){try{
 using namespace mw34;using namespace context_control;need(argc==8,"Current Context control game/MSVCP/CRT/MFC fresh-output admission-hash mode");const auto game=old::read(argv[1],2384384),provider=old::read(argv[2],565760),crt=old::read(argv[3],266293),mfc=old::read(argv[4],954128);m4::admit_image(std::as_bytes(std::span{game}));need(old::sha256(provider)==ni::provider_sha&&old::sha256(crt)=="2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7"&&old::sha256(mfc)=="5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8","Exact current physical providers");const unsigned mode=unsigned(std::stoul(argv[7]));need(mode>=1&&mode<=8&&std::strlen(argv[6])==64,"Finite current Context control and independent admission");Writer writer{argv[5],{}};need(!std::filesystem::exists(writer.out),"Fresh current Context control directory");std::filesystem::create_directories(writer.out);mfc_output.clear();widget_output.clear();
 const std::array<std::array<unsigned,3>,6>cases{{{0,0x7f,0},{0,0x37f,7},{0,0xf7f,0},{1,0x47f,7},{1,0xa7f,0},{1,0xe7f,7}}};const auto input=cases[(mode-1)%6];Context context(std::as_bytes(std::span{game}),std::as_bytes(std::span{provider}),std::as_bytes(std::span{crt}),std::as_bytes(std::span{mfc}),input[0],input[1],input[2]);Injection cause{&writer,mode};injection=&cause;context.before_phase=&before_phase;std::vector<Native>records;records.reserve(17);
 alignas(16)std::array<std::byte,1632>hardware{},retry_hardware{},cleanup_hardware{};Task task{&context,0,input[0],input[2],&records};context_controls_hardware_call(&task,hardware.data());need(cause.injected&&!task.completed&&task.error.empty()&&context.failed()&&context.runtime().poisoned()&&context.completed==16&&records.size()==16,"Actual current Context refusal after full sixteen-root prefix");injection=nullptr;const std::string first=context.failure_reason();need(!first.empty(),"Exact current first refusal reason retained");writer.data("refusal.txt",first.data(),first.size());writer.data("invoke-hardware.bin",hardware.data(),hardware.size());writer.data("prefix-records.bin",records.data(),records.size()*sizeof(Native));
 context.control_snapshot("same-context-before");writer.prefix="retry-before/Registry/";context.registry().dump(&Writer::sink,&writer);writer.prefix="";const auto count=context.runtime().calls().size();const auto priorFault=context.fault();Task retry{&context,0,input[0],input[2],&records};context_controls_hardware_call(&retry,retry_hardware.data());need(!retry.completed&&retry.error.empty()&&context.failed()&&context.runtime().poisoned()&&context.runtime().calls().size()==count&&context.completed==16&&records.size()==16&&first==context.failure_reason(),"Same actual failed Context retains first reason and cannot advance");context.control_snapshot("same-context-after");writer.prefix="retry-after/Registry/";context.registry().dump(&Writer::sink,&writer);writer.prefix="";writer.data("retry-hardware.bin",retry_hardware.data(),retry_hardware.size());
 Task cleanup{&context,1,input[0],input[2],&records};context_controls_hardware_call(&cleanup,cleanup_hardware.data());need(cleanup.completed&&cleanup.error.empty()&&!context.registry().live_handle(),"Actual carried Context fault mark permits real font cleanup before poisoned registry release");writer.data("cleanup-hardware.bin",cleanup_hardware.data(),cleanup_hardware.size());writer.prefix="cleaned/Registry/";context.registry().dump(&Writer::sink,&writer);writer.prefix="";for(const auto&x:widget_output)writer.data("Widget/"+x.name,x.bytes.data(),x.bytes.size());for(const auto&x:mfc_output)writer.data("MFC/"+x.name,x.bytes.data(),x.bytes.size());
 const auto f=context.fault();const std::array<unsigned,16>status{1,mode,input[0],input[1],input[2],1,1,unsigned(context.failed()),unsigned(context.runtime().poisoned()),context.completed,unsigned(count),unsigned(context.runtime().calls().size()),f.phase,f.pc,f.kind,unsigned(!context.registry().live_handle())};writer.data("status.bin",status.data(),sizeof(status));writer.data("admission.txt",argv[6],64);const char complete[]="Complete current Context refusal/retry and owned cleanup";writer.data("COMPLETE.txt",complete,sizeof(complete)-1);std::cout<<"Current Context mode "<<mode<<" refused, retried unchanged and resources cleaned\n";return 0;
 }catch(const std::exception&e){context_control::injection=nullptr;mw34::m4_mixed::observation=nullptr;ni::owner=nullptr;mw34::m4_spi_connected::owner=nullptr;std::cerr<<e.what()<<'\n';return 1;}}
