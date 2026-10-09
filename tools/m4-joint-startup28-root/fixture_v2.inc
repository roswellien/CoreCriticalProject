// Independent source mutation and outside-return controls. The candidate body
// and all literal COFFs remain unchanged; main is replaced in a fresh build.
#include <functional>
using namespace mw34;
using namespace mw34::m4_mixed;
namespace {
unsigned checks{},kind{},hook_hits{};
void check(bool b,const char*m){++checks;need(b,m);}
GuestAddress region(Context&c,unsigned a){for(const auto&r:c.runtime().image_metadata().mapped_regions)if(a>=r.start.value&&std::uint64_t(a)<std::uint64_t(r.start.value)+r.size)return r.start;throw std::runtime_error("Control image region absent");}
void permit(Context&c,unsigned a,Permissions p){c.runtime().memory().protect(region(c,a),p);}
void event_hook(m4_spi_connected::Session&s,unsigned step){
 if(kind==6&&step==1){++hook_hits;s.runtime().memory().protect({0x20001000},Permissions::read);}
 if(kind==10&&step==24){++hook_hits;s.runtime().memory().store<unsigned>({frame},0x12345678);}
 if(kind==11&&step==25){++hook_hits;SetLastError(0xbad11);throw std::runtime_error("Independent throw after real source RET read");}
 if(kind==14&&step==1){++hook_hits;SetLastError(0xbad14);throw std::runtime_error("Independent source prefix observer exception");}
 if(kind==13&&step==7){++hook_hits;s.runtime().memory().unmap({0x5e6000});}
}
void before_api(m4_spi_connected::Session&s){
 if(kind==7){++hook_hits;s.runtime().memory().store<unsigned>({frame-20},0x12345678);}
 if(kind==8){++hook_hits;for(const auto&r:s.runtime().image_metadata().mapped_regions)if(m4_spi_connected::output>=r.start.value&&std::uint64_t(m4_spi_connected::output)<std::uint64_t(r.start.value)+r.size)s.runtime().memory().protect(r.start,Permissions::read);}
}
void after_api(m4_spi_connected::Session&s){if(kind==15){++hook_hits;SetLastError(0xbad15);throw std::runtime_error("Independent observer exception after actual API");}if(kind==9){++hook_hits;for(const auto&r:s.runtime().image_metadata().mapped_regions)if(m4_spi_connected::output>=r.start.value&&std::uint64_t(m4_spi_connected::output)<std::uint64_t(r.start.value)+r.size)s.runtime().memory().protect(r.start,Permissions::read);}}
void phase_hook(Context&c,unsigned completed){
 if(kind==12&&completed==15){++hook_hits;throw std::runtime_error("Independent observer throw after actual SPI root RET");}
 if(completed!=14)return;
 if(kind==1){++hook_hits;permit(c,0x482cf0,Permissions::read|Permissions::write|Permissions::execute);auto v=c.runtime().memory().load<unsigned char>({0x482cf0});c.runtime().memory().store<unsigned char>({0x482cf0},v^1);}
 if(kind==2){++hook_hits;permit(c,m4_spi_connected::slot,Permissions::read|Permissions::write);c.runtime().memory().store<unsigned>({m4_spi_connected::slot},m4_spi_connected::raw_iat^1);}
 if(kind==3){++hook_hits;c.state().aflag.df=1;c.runtime().cpu().eflags|=0x400;}
 if(kind==4){++hook_hits;c.state().addr.ds_base.dword=1;}
 if(kind==5){++hook_hits;permit(c,m4_spi_connected::object,Permissions::read);}
}
struct alignas(16) Hardware{std::array<std::byte,512>fx{};std::array<std::byte,28>env{};};
void rich_seed(Hardware&h){
 Hardware old{};__asm__ volatile("fxsave64 %0\n\tfnstenv %1\n\tfldenv %1":"=m"(old.fx),"=m"(old.env)::"memory");
 unsigned mxcsr=0x5fa5;unsigned short cw=0xa7f;
 __asm__ volatile("fninit\n\tfld1\n\tfldpi\n\tfldz\n\tfld1\n\tfdivp\n\tfldcw %0\n\tldmxcsr %1"::"m"(cw),"m"(mxcsr):"memory","st","st(1)","st(2)","st(3)");
 __asm__ volatile("fxsave64 %0\n\tfnstenv %1\n\tfldenv %1":"=m"(h.fx),"=m"(h.env)::"memory");
 __asm__ volatile("fxrstor64 %0\n\tfldenv %1"::"m"(old.fx),"m"(old.env):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)","xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");
 for(unsigned i=256;i<416;++i)h.fx[i]=std::byte((i*73+19)&255);
}
bool hardware_equal(const Hardware&a,const Hardware&b){bool ok=!std::memcmp(a.fx.data(),b.fx.data(),5)&&!std::memcmp(a.fx.data()+24,b.fx.data()+24,4)&&a.env==b.env;for(unsigned i=0;i<8;++i)ok=ok&&!std::memcmp(a.fx.data()+32+i*16,b.fx.data()+32+i*16,10);return ok&&!std::memcmp(a.fx.data()+256,b.fx.data()+256,160);}
struct Task{Context*c;std::vector<Native>*records;};
#pragma pack(push,1)
struct Sample{
 std::array<unsigned,24>tags{};
 m4_spi_connected::View before{},after{};
 std::array<std::byte,512>host_before{},host_after{};
 std::array<std::byte,28>env_before{},env_after{};
 std::array<std::byte,69632>memory_before{},memory_after{};
 std::array<unsigned,155>routes{};
};
#pragma pack(pop)
unsigned pages_read(Context&c,std::array<std::byte,69632>&b){unsigned mask{};for(unsigned i=0;i<pages.size();++i)try{c.runtime().memory().read({pages[i]},std::span{b}.subspan(i*4096,4096));mask|=1U<<i;}catch(const MemoryFault&){}return mask;}
}
extern "C" unsigned data_boundary_call(void*,void*,void*,void*);
extern "C" unsigned data_boundary_initialize(void*p)noexcept{auto&t=*static_cast<Task*>(p);return t.c->invoke_selected_table(0,0,0,*t.records);}
namespace {
void emit(Context&c,capture_direct::Writer&w,std::vector<Native>&records,bool retry){
 Sample s{};s.before=m4_spi_connected::view(c.state());auto present_before=pages_read(c,s.memory_before);auto previous=c.fault();auto oldcalls=c.runtime().calls().size();auto oldcompleted=c.completed;auto oldstep=c.spi().step();
 Hardware rich{},before{},after{};rich_seed(rich);Host cleanup(0x37f);Task task{&c,&records};SetLastError(0x4d573328);auto result=data_boundary_call(&task,&before,&after,&rich);auto error=GetLastError();cleanup.restore();
 s.host_before=before.fx;s.host_after=after.fx;s.env_before=before.env;s.env_after=after.env;
 check(hardware_equal(before,after),"Rich outside-return host restoration failed");check(error==0x4d573328,"Whole connected boundary LastError changed");
 s.after=m4_spi_connected::view(c.state());auto present_after=pages_read(c,s.memory_after);auto f=c.fault();
 s.tags={kind,unsigned(retry),result,c.completed,unsigned(c.failed()),unsigned(c.runtime().poisoned()),unsigned(c.spi().failed()),c.spi().step(),unsigned(c.runtime().calls().size()),f.phase,f.pc,f.address,f.step,f.kind,unsigned(c.spi().api_called()),unsigned(c.spi().complete()),hook_hits,present_before,present_after,unsigned(oldcalls),oldcompleted,oldstep,error,unsigned(records.size())};
 check(observation==nullptr&&ni::owner==nullptr&&m4_spi_connected::owner==nullptr,"Lexical observer/owner cleanup failed");
 unsigned i{};for(const auto&r:c.runtime().calls()){check(i<31,"Route record overflow");s.routes[i*5]=r.site.value;s.routes[i*5+1]=r.target.value;s.routes[i*5+2]=r.return_pc.value;s.routes[i*5+3]=r.import;s.routes[i*5+4]=r.completed;++i;}
 if(!retry&&kind==0){check(result&&c.completed==28&&records.size()==28&&i==31&&!c.failed()&&!c.runtime().poisoned(),"Actual success sequence incomplete");}
 else{check(!result&&c.failed()&&f.kind,"Fault not retained");if(retry){check(oldcalls==i&&oldcompleted==c.completed&&oldstep==c.spi().step(),"Refused retry executed more work");if(previous.kind)check(!std::memcmp(&previous,&f,sizeof(f)),"First fault overwritten");check(!std::memcmp(&s.before,&s.after,sizeof(s.before))&&s.memory_before==s.memory_after&&present_before==present_after,"Refused retry mutated persistent guest state");}else{check(c.completed==(kind==12?15:14)&&records.size()==c.completed,"Fault did not retain completed prefix");check(hook_hits==1,"Independent control did not fire once");check(c.spi().api_called()==(kind>=9&&kind<=12||kind==15),"Actual API call boundary differs");check(kind==12?c.spi().complete():!c.spi().complete(),"Literal root RET completion differs");check(kind==12?!c.runtime().poisoned():c.runtime().poisoned(),"Runtime first-fault poison differs");}}
 const auto name="case-"+std::to_string(kind)+(retry?"/retry.bin":"/first.bin");w.append(name,&s,sizeof(s));
 if(!retry){for(unsigned n=0;n<records.size();++n)w.append("case-"+std::to_string(kind)+"/prefix-"+std::to_string(n)+".bin",&records[n],sizeof(Native));auto&sp=c.spi();w.append("case-"+std::to_string(kind)+"/events.bin",sp.events().data(),sp.step()*sizeof(SpiEvent));w.append("case-"+std::to_string(kind)+"/transports.bin",sp.transports().data(),sp.transport_count()*sizeof(SpiEvent));w.append("case-"+std::to_string(kind)+"/witness.bin",sp.witness().data(),sizeof(sp.witness()));}
}
}
int main(int argc,char**argv){try{
 check(argc==4,"Exact game/provider/fresh archive required");auto game=old::read(argv[1],2384384),provider=old::read(argv[2],565760);m4::admit_image(std::as_bytes(std::span{game}));check(old::sha256(provider)==ni::provider_sha,"Exact provider identity");capture_direct::Options options;options.reports_root=std::filesystem::current_path()/"reports";capture_direct::Writer writer(argv[3],options);
 const unsigned header[]{1,16,32,sizeof(Sample),17,sizeof(Native)};writer.append("header.bin",header,sizeof(header));
 for(kind=0;kind<16;++kind){hook_hits=0;Context c(std::as_bytes(std::span{game}),std::as_bytes(std::span{provider}),0,0x37f,0);c.after_phase=&phase_hook;c.spi().after_source_event=&event_hook;c.spi().before_api=&before_api;c.spi().after_api=&after_api;std::vector<Native>records;records.reserve(28);emit(c,writer,records,false);c.after_phase=nullptr;c.spi().after_source_event=nullptr;c.spi().before_api=nullptr;c.spi().after_api=nullptr;emit(c,writer,records,true);}
 const unsigned counts[]{checks,16,32};writer.append("counts.bin",counts,sizeof(counts));const char done[]="Independent connected28 controls passed\n";writer.append("COMPLETE.txt",done,sizeof(done)-1);writer.finish();std::cout<<checks<<" checks;16 independent scenarios;32 actual attempts\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
