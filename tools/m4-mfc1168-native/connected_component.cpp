// Reusable literal component. No main, isolated CPU/FX pack, or admission factory.
#include "connected_component.hpp"
#include "connected_literals.hpp"
#include "admission.hpp"
#include <Windows.h>
#include <algorithm>
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <type_traits>

namespace mw34::m4_mfc1168_connected {
namespace {
struct Access {unsigned pc,address;std::uint64_t value;unsigned width,writing;};
struct Frame {unsigned target,frame,ret,site;};
struct ApiRecord {std::array<std::uint64_t,16>words{};m4_runtime::Cpu32 before,after;std::array<std::byte,64>frame{};std::array<std::byte,40>CS_before{},CS_after{};};
static_assert(sizeof(Access)==24&&sizeof(Frame)==16&&sizeof(ApiRecord)==352);
struct Emitter {Sink sink{};void*opaque{};};
thread_local Emitter emitter{};
static void dump(const std::string&name,const void*data,std::size_t size){require(emitter.sink,"Current complete component capture sink");emitter.sink(name,std::span(static_cast<const std::byte*>(data),size),emitter.opaque);}
static std::vector<std::byte>read_file(const std::filesystem::path&p){std::ifstream f(p,std::ios::binary|std::ios::ate);require(bool(f),"Actual native provider input open");auto n=f.tellg();require(n>=0&&n<64*1024*1024,"Bounded native provider input");std::vector<std::byte>b(static_cast<std::size_t>(n));f.seekg(0);f.read(reinterpret_cast<char*>(b.data()),b.size());require(bool(f),"Complete native provider input");return b;}
#include "resource_witness.hpp"
constexpr std::array<unsigned,5>role_bases{0x33001000,0x33002000,0x33003000,0x33004000,0x33005000};
constexpr std::array<unsigned,5>role_extents{256,16,12,280,4240};
constexpr std::array<unsigned,3>CRT_cells{0x7803708c,0x780379c0,0x78037ae8};
constexpr std::array<unsigned,7>import_PCs{0x5abed0,0x5ae3c4,0x5f40107d,0x5f401012,0x7800106f,0x78003eab,0x780012ab};
constexpr std::array<unsigned,7>import_cells{0x5bb210,0x5bb674,0x5f49815c,0x5f498330,0x7802e044,0x7802e0c8,0x7802e048};
void validate_input_shape(Runtime&r,const Inputs&i){
 require(r.domain()==m4_runtime::Domain::admitted_game&&r.fs_base().value==0x7ffde000,"Current admitted connected Runtime and minimal TIB");
 require(i.addresses.bases[0]==0&&i.addresses.bases[1]==0x20001800&&i.addresses.bases[2]==r.fs_base().value,"Exact absolute/current-frame/current-FS role bases");
 for(unsigned k=0;k<5;++k)require(i.addresses.bases[3+k]==role_bases[k]&&i.borrowed_before[k].size()==role_extents[k],"Five explicit disjoint whole borrowed role extents");
 require(i.guest_thread&&i.guest_CS==0x33007000,"Explicit typed guest thread/CS24 association");
 require(i.original_prefix_receipt_sha256.size()==64&&i.source_domain_receipt_sha256.size()==64,"Fresh chronological original and source domain receipt identities");
 require(i.new_mappings.size()>=8&&i.new_mappings.size()<=150,"Finite reviewed new source mappings");
 const std::array<unsigned,6>cells{0x5f4cb018,0x5f4cb01c,0x5f4cb040,r.fs_base().value+0xe1c,role_bases[1]+12,role_bases[2]+4};
 const std::array<unsigned,6>targets{role_bases[0],role_bases[1],role_bases[4],role_bases[1],role_bases[2],role_bases[3]};
 for(unsigned k=0;k<6;++k)require(i.pointer_cells[k].address==cells[k]&&i.pointer_cells[k].before&&i.pointer_cells[k].projected==targets[k],"Exactly six consumed/carried typed pointer projections");
 for(unsigned k=0;k<3;++k)require(i.CRT_cells[k].address==CRT_cells[k],"Exactly three source-proved CRT merge cells");
 require(i.CRT_cells[0].projected==i.guest_CS&&i.CRT_cells[1].projected==1252&&i.CRT_cells[2].projected==1,"Finite cached1252 lock25/transient domain");
 for(unsigned k=0;k<7;++k)require(i.imports[k].pc==import_PCs[k]&&i.imports[k].cell==import_cells[k]&&i.imports[k].raw&&i.imports[k].projected,"Seven exact owning import projection identities");
 require(i.imports[0].projected==0x5f401083&&i.imports[1].projected==0x78003ddb&&i.imports[2].projected==0x78001496,"Literal provider ordinal/setmbcp/EH import targets");
}
void whole_bytes(Runtime&r,unsigned address,std::span<const std::byte>expected,const char*reason){std::vector<std::byte>b(expected.size());r.memory().read({address},b);require(std::equal(b.begin(),b.end(),expected.begin()),reason);}
} // anonymous

void materialize_loader_inputs(Runtime&r,const Inputs&i,const ChronologicalAdmission&a){
 require(a.runtime_==&r&&a.inputs_==&i&&a.digest_==i.source_domain_receipt_sha256,"Exact unforgeable chronological loader admission");validate_input_shape(r,i);require(!r.poisoned()&&r.calls().empty(),"Loader additions precede all carried startup calls");
 // All map/protect/write validation runs on the owned copy. No partial mutation.
 auto candidate=r.memory();
 for(const auto&b:i.new_mappings){require(!b.before.empty()&&b.before.size()<=8192&&b.permissions!=0,"Bounded complete new BEFORE mapping including4240B role");candidate.map({b.address},b.before.size(),Permissions::read|Permissions::write);candidate.write({b.address},b.before);candidate.protect({b.address},static_cast<Permissions>(b.permissions));}
 for(const auto&cell:i.pointer_cells){require(candidate.load<unsigned>({cell.address})==cell.before,"Genuine BEFORE typed pointer cell preimage");candidate.store<unsigned>({cell.address},cell.projected);}
 for(const auto&cell:i.CRT_cells){require(candidate.load<unsigned>({cell.address})==cell.before,"Current carried CRT cell and proved prior-domain preimage");candidate.store<unsigned>({cell.address},cell.projected);}
 for(const auto&v:i.imports)require(candidate.load<unsigned>({v.cell})==v.raw,"Parent's owning raw IAT cells retained completely");
 // Whole registry and minimal TIB source bytes survive the only three-cell merge.
 for(unsigned cell:std::array<unsigned,6>{0x78037888,0x7803788c,0x78037890,r.fs_base().value,r.fs_base().value+4,r.fs_base().value+0x18})require(candidate.load<unsigned>({cell})==r.memory().load<unsigned>({cell}),"Existing registry/TIB source identity conserved");
 r.memory()=std::move(candidate);
}

struct Component::Impl {
 Runtime&r;const Inputs&input;State&s;DWORD host_thread=GetCurrentThreadId(),host_TLS=TLS_OUT_OF_INDEXES;bool TLS_live{},CS_live{},entered{},complete{};unsigned access_cursor{},API_cursor{},CS_depth{};CRITICAL_SECTION CS{};
 std::vector<std::byte>host_thread_backing;std::vector<Access>accesses;std::vector<ApiRecord>APIs;std::vector<Frame>frames;std::vector<std::array<unsigned,6>>imports;
 static thread_local Impl*current;
 Impl(Runtime&runtime,const Inputs&i,Sink sink,void*opaque):r(runtime),input(i),s(*reinterpret_cast<State*>(r.remill_state().data())){
  require(!current&&!emitter.sink&&sink,"Unique current component/source/resource sink");validate_input_shape(r,input);
  for(unsigned k=0;k<5;++k)whole_bytes(r,role_bases[k],i.borrowed_before[k],"Whole chronological borrowed BEFORE after declared relocation");whole_bytes(r,i.guest_CS,i.CS_before,"Whole source guestCS24 BEFORE");
  require(r.memory().load<unsigned>({r.fs_base().value+0xe1c})==role_bases[1],"Minimal guest TIB TLS mirror only");
  for(const auto&v:i.imports)require(r.memory().load<unsigned>({v.cell})==v.raw,"Exact current physical raw import preimage");
  for(const auto&v:i.CRT_cells)require(r.memory().load<unsigned>({v.address})==v.projected,"Chronological cached CRT additions retained before root");
  host_thread_backing=i.borrowed_before[1];emitter={sink,opaque};current=this;resource_serial=0;
  try{host_TLS=mf_TlsAlloc();require(host_TLS!=TLS_OUT_OF_INDEXES,"Actual owned component TLS slot");TLS_live=true;require(mf_TlsGetValue(host_TLS)==nullptr,"Actual new TLS slot starts empty");require(mf_TlsSetValue(host_TLS,host_thread_backing.data()),"Actual current-thread native association");resource_CS=&CS;mf_InitializeCriticalSection(&CS);CS_live=true;require(!CS.RecursionCount&&CS.OwningThread==nullptr,"Owned hostCS40 initialized and unheld");}
  catch(...){cleanup_failed();throw;}
 }
 ~Impl(){try{if(TLS_live||CS_live)cleanup_failed();}catch(...){/* Explicit cleanup is separately checked by the caller. */}if(current==this)current=nullptr;resource_CS=nullptr;emitter={};}
 void authority(){require(current==this&&GetCurrentThreadId()==host_thread&&TLS_live&&CS_live,"Exact live connected context/thread/native resource ownership");}
 void access(unsigned address,std::uint64_t value,unsigned width,bool writing){authority();require(matches(access_cursor,s.gpr.rip.dword,address,width,writing,input.addresses),"Exact causal connected source PC/role/offset/width/direction order");accesses.push_back({s.gpr.rip.dword,address,value,width,unsigned(writing)});++access_cursor;}
 std::uint64_t read(unsigned a,unsigned n){authority();require(n<=8,"Bounded source scalar read");std::array<std::byte,8>b{};r.memory().read({a},std::span(b.data(),n));std::uint64_t value{};std::memcpy(&value,b.data(),n);
  for(const auto&v:input.imports)if(v.pc==s.gpr.rip.dword&&v.cell==a){require(n==4&&value==v.raw,"Exact owning raw physical source IAT read");imports.push_back({access_cursor,v.pc,v.cell,v.raw,v.projected,unsigned(frames.size())});value=v.projected;break;}
  access(a,value,n,false);return value;
 }
 void write(unsigned a,std::uint64_t v,unsigned n){authority();access(a,v,n,true);if(a==role_bases[4]+0x14)require(n==1&&v==0&&s.gpr.rip.dword==0x5ae3b7,"Literal connected byte14 store");if(a==role_bases[4]+0x1040)require(n==4&&v==0x421&&s.gpr.rip.dword==0x5ae3ba,"Literal connected DWORD1040 store");std::array<std::byte,8>b{};std::memcpy(b.data(),&v,n);r.memory().write({a},std::span(b.data(),n));if(auto row=literal::instruction(s.gpr.rip.dword);row&&row->call)frames.push_back({0,a,unsigned(v),row->pc});}
 void returned(unsigned target){authority();require(!frames.empty(),"Source RET owns actual current call frame");auto f=frames.back();require(target==f.ret,"Exact current saved source return");if(f.target==0x5f40107d)require(f.site==0x5f4010b0&&target==0x5f4010b5&&s.gpr.rsp.dword==f.frame-12,"Source-defined imported EH prolog special return frame");else{require(!accesses.empty(),"Actual RET source read ledger");const auto&last=accesses.back();auto row=literal::instruction(last.pc);require(row&&row->ret&&last.address==f.frame,"Ordinary literal RET reads its actual current frame");}frames.pop_back();}
 void CS_transport(){require(CS.RecursionCount==CS_depth&&reinterpret_cast<std::uintptr_t>(CS.OwningThread)==(CS_depth?host_thread:0),"Actual owned hostCS40/current-thread source depth relation");const std::array<unsigned,3>sem{CS_depth?0xfffffffeU:0xffffffffU,CS_depth,CS_depth?input.guest_thread:0};for(unsigned k=0;k<3;++k)r.memory().store<unsigned>({input.guest_CS+4+4*k},sem[k]);}
 void API(unsigned index,unsigned target){authority();require(index==API_cursor&&index<4&&!frames.empty(),"Exact four typed source API calls/current frame");const auto&spec=literal::APIs[index];const auto&projection=input.imports[index+3];auto f=frames.back();require(target==projection.projected&&s.gpr.rip.dword==target&&f.site==spec.call_site&&f.frame==s.gpr.rsp.dword,"Named source target/current CALL or resolver tail frame");require(accesses.size()>=(index==2?1U:2U),"Actual source IAT operand exists");const auto&iat=accesses[accesses.size()-(index==2?1:2)];require(iat.pc==spec.site&&!iat.writing&&iat.width==4&&iat.value==target,"Owning projected IAT read provenance");if(index!=2){const auto&push=accesses.back();require(push.pc==spec.site&&push.writing&&push.address==f.frame&&push.width==4&&push.value==spec.ret,"Actual committed source API return push");}require(r.memory().load<unsigned>({f.frame})==spec.ret,"Actual source API saved return bytes");if(spec.argc)require(r.memory().load<unsigned>({f.frame+4})==(index==0?3:input.guest_CS),"Typed guest TLS index3/borrowed CS24 argument");
  ApiRecord rec;rec.before=cpu(s);r.memory().read({f.frame},rec.frame);std::memcpy(rec.CS_before.data(),&CS,40);std::uint64_t raw{};unsigned result{};auto error_before=GetLastError();
  if(index==0){auto p=mf_TlsGetValue(host_TLS);raw=reinterpret_cast<std::uintptr_t>(p);require(p==host_thread_backing.data(),"Actual current owned TLS association");whole_bytes(r,role_bases[1],host_thread_backing,"Whole borrowed current thread/native template mirror");result=role_bases[1];}
  if(index==1){require(!CS_depth,"Finite lock25 enter depth0");mf_EnterCriticalSection(&CS);CS_depth=1;CS_transport();}
  if(index==2){raw=mf_GetACP();require(raw==1252,"Actual finite native ACP1252 only");result=unsigned(raw);}
  if(index==3){require(CS_depth==1,"Finite lock25 leave depth1");mf_LeaveCriticalSection(&CS);CS_depth=0;CS_transport();}
  auto error_after=GetLastError();std::memcpy(rec.CS_after.data(),&CS,40);s.gpr.rax.dword=result;s.gpr.rsp.dword+=4*(spec.argc+1);s.gpr.rip.dword=spec.ret;rec.after=cpu(s);rec.words={1,index,spec.site,target,spec.argc,rec.before.esp,spec.ret,result,raw,host_thread,host_TLS,reinterpret_cast<std::uintptr_t>(host_thread_backing.data()),role_bases[1],CS_depth,error_before,error_after};APIs.push_back(rec);frames.pop_back();++API_cursor;
 }
 void*dispatch(unsigned target,bool tail){authority();if(!tail){require(!frames.empty()&&frames.back().target==0&&frames.back().frame==s.gpr.rsp.dword,"Committed literal CALL frame before routing");frames.back().target=target;}for(unsigned k=0;k<4;++k)if(target==input.imports[k+3].projected){API(k,target);return this;}require(literal::body(target),"Unobserved lazy/callback/foreign provider target denied");return literal::dispatch(target,&s,this);}
 void execute(State&state,unsigned frame,unsigned ret){authority();require(&state==&s&&!entered&&frame==input.addresses.bases[1],"One exact carried component source invocation");entered=true;for(const auto&row:literal::source_spans){std::array<std::byte,16>b{};r.memory().read({row.pc},std::span(b.data(),row.size));require(std::equal(b.begin(),b.begin()+row.size,row.bytes.begin()),"Complete literal physical source span admission");}frames.push_back({root,frame,ret,0});checkpoint("before");literal::dispatch(root,&s,this);require(access_cursor==operands.size()&&API_cursor==4&&frames.empty()&&!CS_depth,"Complete finite literal operand/API/EH closure");complete=true;checkpoint("after");}
 void checkpoint(std::string_view stem){std::string p(stem);auto c=cpu(s);dump(p+"/State.bin",&s,sizeof(s));dump(p+"/CPU.bin",&c,sizeof(c));dump(p+"/FX.bin",r.fx().data(),512);dump(p+"/accesses.bin",accesses.data(),accesses.size()*sizeof(Access));dump(p+"/APIs.bin",APIs.data(),APIs.size()*sizeof(ApiRecord));dump(p+"/frames.bin",frames.data(),frames.size()*sizeof(Frame));dump(p+"/import-projections.bin",imports.data(),imports.size()*sizeof(imports[0]));dump(p+"/nativeCS40.bin",&CS,40);dump(p+"/native-thread-mirror.bin",host_thread_backing.data(),host_thread_backing.size());for(unsigned k=0;k<5;++k){std::vector<std::byte>b(role_extents[k]);r.memory().read({role_bases[k]},b);dump(p+"/borrowed/"+std::to_string(k)+".bin",b.data(),b.size());}std::array<std::byte,24>cs{};r.memory().read({input.guest_CS},cs);dump(p+"/guestCS24.bin",cs.data(),cs.size());const std::array<std::uint64_t,12>w{host_thread,host_TLS,unsigned(TLS_live),unsigned(CS_live),CS_depth,std::uint64_t(CS.RecursionCount),reinterpret_cast<std::uintptr_t>(CS.OwningThread),access_cursor,API_cursor,unsigned(entered),unsigned(complete),resource_serial};dump(p+"/resource-context.bin",w.data(),sizeof(w));}
 void cleanup_failed(){require(GetCurrentThreadId()==host_thread,"Actual cleanup current-thread resource owner");if(CS_live){require(CS.RecursionCount<=1,"Finite actual owned CS cleanup depth");if(CS.RecursionCount)mf_LeaveCriticalSection(&CS);CS_depth=0;mf_DeleteCriticalSection(&CS);CS_live=false;}if(TLS_live){require(mf_TlsSetValue(host_TLS,nullptr)&&mf_TlsGetValue(host_TLS)==nullptr,"Actual cleanup TLS clear");require(mf_TlsFree(host_TLS),"Actual cleanup TLS free");TLS_live=false;}resource_CS=nullptr;}
 void finish(){authority();require(complete&&access_cursor==113&&API_cursor==4&&frames.empty()&&!CS_depth,"Completed source closure before actual resource release");require(mf_TlsGetValue(host_TLS)==host_thread_backing.data(),"Actual native TLS held until complete source return");cleanup_failed();const std::array<std::uint64_t,8>w{1,host_thread,host_TLS,4,0,1,1,1};dump("lifecycle.bin",w.data(),sizeof(w));}
};
thread_local Component::Impl*Component::Impl::current{};
Component::Component(Runtime&r,const Inputs&i,const ChronologicalAdmission&a,Sink sink,void*opaque){require(a.runtime_==&r&&a.inputs_==&i&&a.digest_==i.source_domain_receipt_sha256,"Exact admitted chronological component inputs");impl_=std::make_unique<Impl>(r,i,sink,opaque);}
Component::~Component()=default;
Runtime&Component::runtime()noexcept{return impl_->r;}
void Component::authority(){impl_->authority();}
void Component::execute_literal(State&s,unsigned frame,unsigned ret){impl_->execute(s,frame,ret);}
void Component::finish(){impl_->finish();}
void Component::cleanup_failed(){impl_->cleanup_failed();}
void Component::checkpoint(std::string_view stem){impl_->checkpoint(stem);}

// Literal COFF bridge authority is separate from the registry Session and its
// registration callback list. All source effects use the actual current State.
static auto&owner(void*p){auto*c=Component::Impl::current;require(c&&p==c,"Exact current connected literal bridge context");c->authority();return*c;}
} // namespace mw34::m4_mfc1168_connected
using namespace mw34::m4_mfc1168_connected;
extern "C" std::uint8_t mw34_mfc1168_read8(void*p,unsigned a){return static_cast<std::uint8_t>(owner(p).read(a,1));}
extern "C" std::uint16_t mw34_mfc1168_read16(void*p,unsigned a){return static_cast<std::uint16_t>(owner(p).read(a,2));}
extern "C" unsigned mw34_mfc1168_read32(void*p,unsigned a){return unsigned(owner(p).read(a,4));}
extern "C" std::uint64_t mw34_mfc1168_read64(void*p,unsigned a){return owner(p).read(a,8);}
extern "C" void*mw34_mfc1168_write8(void*p,unsigned a,std::uint8_t v){owner(p).write(a,v,1);return p;}
extern "C" void*mw34_mfc1168_write16(void*p,unsigned a,std::uint16_t v){owner(p).write(a,v,2);return p;}
extern "C" void*mw34_mfc1168_write32(void*p,unsigned a,unsigned v){owner(p).write(a,v,4);return p;}
extern "C" void*mw34_mfc1168_write64(void*p,unsigned a,std::uint64_t v){owner(p).write(a,v,8);return p;}
extern "C" void*mw34_mfc1168_call(State*s,unsigned a,void*p){auto&c=owner(p);require(&c.s==s,"Current bridge State identity");return c.dispatch(a,false);}
extern "C" void*mw34_mfc1168_jump(State*s,unsigned a,void*p){auto&c=owner(p);require(&c.s==s,"Current bridge State identity");return c.dispatch(a,true);}
extern "C" void*mw34_mfc1168_missing(State*s,unsigned a,void*p){return mw34_mfc1168_jump(s,a,p);}
extern "C" void*mw34_mfc1168_return(State*s,unsigned a,void*p){auto&c=owner(p);require(&c.s==s,"Current bridge State identity");c.returned(a);return p;}
extern "C" void*mw34_mfc1168_async_hyper_call(State*,unsigned,void*){throw std::runtime_error("Unentered cold/padded source instruction denied");}
#include "connected_bridges.inc"
