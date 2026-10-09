// Additive tests of the frozen whole-table Context. No original process.
#define main frozen_joint27_worker_main
#include "native_main.cpp"
#undef main
#include <functional>
#include <sstream>
using namespace mw34;
using namespace mw34::m4_mixed;
namespace {
unsigned checks{},scenarios{},hook_kind{};
void check(bool v,const char*m){++checks;need(v,m);}
GuestAddress region(Context&c,unsigned a){for(const auto&r:c.runtime().image_metadata().mapped_regions)if(a>=r.start.value&&std::uint64_t(a)<std::uint64_t(r.start.value)+r.size)return r.start;throw std::runtime_error("Test image region absent");}
void permit(Context&c,unsigned a,Permissions p){c.runtime().memory().protect(region(c,a),p);}
void late(ni::Session&s,unsigned step){
 auto&r=s.runtime();
 if(hook_kind==1&&step==7){for(const auto&p:r.image_metadata().mapped_regions)if(ni::output>=p.start.value&&std::uint64_t(ni::output)<std::uint64_t(p.start.value)+p.size)r.memory().protect(p.start,Permissions::read);}
 if(hook_kind==2&&step==5)r.memory().unmap({0x78115000});
 if(hook_kind==3&&step==21)r.memory().store<unsigned>({frame},0x12345678);
 if(hook_kind==4&&step==1)r.memory().protect({0x20001000},Permissions::read);
 if(hook_kind==5&&step==19)r.memory().store<unsigned>({frame-8},0x12345678);
 if(hook_kind==6&&step==21)r.memory().unmap({0x780c1000});
}
void numeric_entry(ni::Session&s){root_entry(s);if(hook_kind==7)s.runtime().memory().protect({0x20001000},Permissions::read);}
#pragma pack(push,1)
struct Sample {
 std::array<unsigned,20>tags{};
 ni::View before{},after{};
 std::array<std::byte,512>host_before{},host_after{};
 std::array<std::byte,28>env_before{},env_after{};
 std::array<std::byte,57344>memory_before{},memory_after{};
 unsigned present_before{},present_after{};
 std::array<unsigned,145>route_data{};
};
#pragma pack(pop)
static_assert(sizeof(Sample)==124604);
unsigned pages_read(Context&c,std::array<std::byte,57344>&b){unsigned mask=0;for(unsigned i=0;i<pages.size();++i)try{c.runtime().memory().read({pages[i]},std::span{b}.subspan(i*4096,4096));mask|=1U<<i;}catch(const MemoryFault&){}return mask;}
void emit(Context&c,old::Output&out,unsigned kind,unsigned cw,bool expected,std::vector<Native>&records,bool retry=false,bool previous_owner=false){
 Sample s{};s.before=ni::view(c.state());s.present_before=pages_read(c,s.memory_before);const auto oldcalls=c.runtime().calls().size();const auto oldstep=c.session().step();const auto oldcompleted=c.completed;const auto oldfirst=c.fault();
 marked_kind=kind;marked_cw=cw;marked_retry=retry;
 Host caller(static_cast<std::uint16_t>(cw));bool result=c.invoke_selected_table(0,0,0,records);caller.capture();s.host_before=caller.before.b;s.host_after=caller.after.b;s.env_before=caller.env;s.env_after=caller.env_after;
 s.after=ni::view(c.state());s.present_after=pages_read(c,s.memory_after);auto f=c.fault();s.tags={kind,cw,unsigned(result),unsigned(expected),c.completed,unsigned(c.failed()),unsigned(c.runtime().poisoned()),unsigned(c.session().failed()),c.session().step(),unsigned(c.runtime().calls().size()),f.phase,f.pc,f.address,f.step,f.kind,unsigned(retry),oldcompleted,unsigned(oldcalls),oldstep,unsigned(ni::owner!=nullptr)};
 check(result==expected,"Actual whole-loop result differs");check(ni::owner==(previous_owner?&c.session():nullptr),"Lexical owner cleanup/preserved owner failed");check(observation==nullptr,"Mixed observer cleanup failed");check(c.runtime().calls().size()<=29,"Actual route capacity");
 unsigned k=0;for(const auto&r:c.runtime().calls()){check(k<29,"Route storage capacity");s.route_data[k*5]=r.site.value;s.route_data[k*5+1]=r.target.value;s.route_data[k*5+2]=r.return_pc.value;s.route_data[k*5+3]=r.import;s.route_data[k*5+4]=r.completed;++k;}
 if(expected){check(c.completed==27&&records.size()==27,"Successful actual complete schedule");check(!c.failed()&&!c.runtime().poisoned()&&!c.session().failed(),"Successful context remains valid");check(c.runtime().calls().size()==29,"Actual connected routes");}
 else{check(c.failed()&&f.kind!=0,"First failure retained");if(retry){check(c.completed==oldcompleted&&c.runtime().calls().size()==oldcalls&&c.session().step()==oldstep,"One-use refuses without new work");if(oldfirst.kind)check(std::memcmp(&oldfirst,&f,sizeof(f))==0,"First POD fault overwritten");check(std::memcmp(&s.before,&s.after,sizeof(s.before))==0,"Refused retry mutated CPU/State/FX/ENV");check(s.present_before==s.present_after&&s.memory_before==s.memory_after,"Refused retry mutated owned pages");}}
 out.write(s);
}
}
int main(int argc,char**argv){try{
 check(argc==4,"Fixture exact game/provider/fresh output");auto game=old::read(argv[1],2384384),provider=old::read(argv[2],565760);m4::admit_image(std::as_bytes(std::span{game}));check(old::sha256(provider)==ni::provider_sha,"Fixture provider identity");auto path=std::filesystem::path(argv[3]);check(!std::filesystem::exists(path)&&std::filesystem::create_directory(path),"Fixture fresh directory");old::Output out((path/"controls.bin").string().c_str());const unsigned header[]{1,0,sizeof(Sample),14};out.write("MW4J27C1",8);out.write(header,sizeof(header));unsigned count=0;
 for(unsigned cw:{0x7fU,0x37fU,0xb7fU})for(unsigned kind=0;kind<17;++kind){
  ++scenarios;hook_kind=0;Context c(std::as_bytes(std::span{game}),std::as_bytes(std::span{provider}),0,cw,0);std::vector<Native>records;records.reserve(27);
  auto whole=c.runtime().memory().load<unsigned>({ni::slot});std::byte code{};c.runtime().memory().read({0x410910},std::span{&code,1});
  if(kind==1)c.runtime().memory().protect({0x20001000},Permissions::read);
  if(kind==2)c.runtime().memory().unmap({0x20001000});
  if(kind==3){permit(c,0x410910,Permissions::read|Permissions::write|Permissions::execute);std::byte x=code^std::byte{1};c.runtime().memory().write({0x410910},std::span{&x,1});}
  if(kind==4)c.state().sw.ie=2;
  if(kind==5){c.state().x87.fxsave.cwd.flat=0;sync_fx(c.runtime(),c.state());}
  if(kind>=6&&kind<=12){hook_kind=kind-5;c.session().test_after_event=&late;if(kind==12)c.session().observe_root_entry=&numeric_entry;}
  if(kind==13){auto p=region(c,ni::slot);c.runtime().memory().protect(p,Permissions::read|Permissions::write);c.runtime().memory().store<unsigned>({ni::slot},whole^1);c.runtime().memory().protect(p,Permissions::read);}
  if(kind==14){c.runtime().memory().protect({0x78115000},Permissions::read|Permissions::write);c.runtime().memory().store<unsigned>({ni::data},0x3f800000);c.runtime().memory().protect({0x78115000},Permissions::read);}
  if(kind==15){std::exception_ptr error;std::thread t([&]{try{emit(c,out,kind,cw,false,records);}catch(...){error=std::current_exception();}});t.join();if(error)std::rethrow_exception(error);}
  else if(kind==16){ni::owner=&c.session();emit(c,out,kind,cw,false,records,false,true);check(c.completed==0&&c.runtime().calls().empty(),"Owner refusal happens before guest work");ni::owner=nullptr;}
  else emit(c,out,kind,cw,kind==0,records);
  ++count;
  // Correction is an authored host action, not automatic retry/reset. The
  // same stable Context must still refuse and preserve its first fault.
  hook_kind=0;c.session().test_after_event=nullptr;c.session().observe_root_entry=&root_entry;
  if(kind==1||kind==6||kind==9||kind==12)c.runtime().memory().protect({0x20001000},Permissions::read|Permissions::write);
  if(kind==2){c.runtime().memory().map({0x20001000},4096,Permissions::read|Permissions::write);c.runtime().memory().store<unsigned>({frame},broker);}
  if(kind==3){c.runtime().memory().write({0x410910},std::span{&code,1});permit(c,0x410910,Permissions::read|Permissions::execute);}
  if(kind==4)c.state().sw.ie=0;
  if(kind==5){c.state().x87.fxsave.cwd.flat=cw;sync_fx(c.runtime(),c.state());}
  if(kind==6)permit(c,ni::output,Permissions::read|Permissions::write);
  if(kind==7||kind==11){const unsigned a=kind==7?0x78115000:0x780c1000;const unsigned off=kind==7?0x54c00:0x1000;c.runtime().memory().map({a},4096,Permissions::read|Permissions::write);c.runtime().memory().write({a},std::as_bytes(std::span{provider}).subspan(off,4096));c.runtime().memory().protect({a},kind==7?Permissions::read:Permissions::read|Permissions::execute);}
  if(kind==8)c.runtime().memory().store<unsigned>({frame},broker);
  if(kind==10)c.runtime().memory().store<unsigned>({frame-8},0x4c19f8);
  if(kind==13){permit(c,ni::slot,Permissions::read|Permissions::write);c.runtime().memory().store<unsigned>({ni::slot},whole);permit(c,ni::slot,Permissions::read);}
  if(kind==14){c.runtime().memory().protect({0x78115000},Permissions::read|Permissions::write);c.runtime().memory().store<unsigned>({ni::data},0x7f7fffff);c.runtime().memory().protect({0x78115000},Permissions::read);}
  emit(c,out,kind,cw,false,records,true);++count;
 }
 out.commit();std::ofstream report(path/"counts.json");report<<"{\"checks\":"<<checks<<",\"scenarios\":"<<scenarios<<",\"records\":"<<count<<",\"stride\":"<<sizeof(Sample)<<"}\n";std::cout<<checks<<" checks in "<<scenarios<<" scenarios / "<<count<<" direct outside-return snapshots\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
