#pragma once
#include "joint_protocol.hpp"
#include "spi_bindings.hpp"
#include <thread>
#include <optional>
#include <bit>
namespace mw34::m4_spi_connected {
namespace rt=m4_runtime;
inline constexpr unsigned root=0x482cf0,call_pc=0x482cdd,return_pc=0x482ce3,slot=0x5bb6dc,raw_iat=0x1df20c,object=0x608f88,output=0x608fa0;
extern "C" void*mw34_spi_initializer_body(State*,unsigned,void*);
struct Abort{};
struct ErrorBoundary {DWORD incoming=GetLastError();~ErrorBoundary(){SetLastError(incoming);}};
struct Fault {unsigned pc{},address{},step{};const char*reason{};};
struct View {std::array<std::byte,3504>state{};std::array<std::byte,512>fx{};rt::Cpu32 cpu{};};
struct ExportProof {
 std::array<std::uint64_t,8>scalar{}; // version,named base,actual,named resolved,owner,owner resolved,named RVA,owner RVA
 std::array<char,32>requested{};std::array<char,256>forwarder{};std::array<char,64>owner_export{};
 std::array<char,64>named_sha{},owner_sha{};std::array<wchar_t,1024>named_path{},owner_path{};
 bool operator==(const ExportProof&)const=default;
};
static_assert(sizeof(ExportProof)==4640&&sizeof(RECT)==16&&sizeof(LONG)==4&&sizeof(BOOL)==4);
using Query=BOOL(WINAPI*)(UINT,UINT,PVOID,UINT);
ExportProof prove_export(Query);
inline rt::Cpu32 cpu(const State&s){const auto c=m4_mixed::cpu(s);return {c.gpr[0],c.gpr[1],c.gpr[2],c.gpr[3],c.gpr[4],c.gpr[5],c.gpr[6],c.gpr[7],c.flags,c.pc};}
inline View view(const State&s){View v;std::memcpy(v.state.data(),&s,3504);std::array<unsigned char,512>f{};std::array<unsigned char,28>e{};m4_mixed::projection(s,f,e);std::memcpy(v.fx.data(),f.data(),512);v.cpu=cpu(s);return v;}
struct HostGuard {
 struct alignas(16)Image{std::array<unsigned char,512>b{};};Image before{},after{};std::array<unsigned char,28>env_before{},env_after{};DWORD error{};bool restored{};
 HostGuard():error(GetLastError()){__asm__ volatile("fxsave64 %0\n\tfnstenv %1\n\tfldenv %1":"=m"(before),"=m"(env_before)::"memory");}
 void restore()noexcept{__asm__ volatile("fxrstor64 %0\n\tfldenv %1"::"m"(before),"m"(env_before):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)","xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");SetLastError(error);restored=true;}
 void capture(){restore();__asm__ volatile("fxsave64 %0\n\tfnstenv %1\n\tfldenv %1":"=m"(after),"=m"(env_after)::"memory");}
 ~HostGuard(){if(!restored)restore();}
};
class Session;
inline thread_local Session*owner{};
class Session {
 rt::Runtime&r_;State&s_;std::thread::id thread_=std::this_thread::get_id();Query query_=&SystemParametersInfoA;
 bool running_{},failed_{},used_{},complete_{},api_called_{},api_returned_{};unsigned frame_{},ret_{},step_{};Fault fault_{};
 std::array<m4_mixed::SpiEvent,64>events_{};std::array<m4_mixed::SpiEvent,32>transport_{};unsigned transport_count_{};
 std::array<std::byte,4096>code_page_{},constant_page_{};ExportProof identity_{};View api_before_{},api_after_{};
 std::array<std::uint64_t,16>witness_{};
 void guard(){if(!running_||failed_||owner!=this||thread_!=std::this_thread::get_id())deny("Inactive/wrong-thread/failed SPI owner");}
 void source_check(){std::array<std::byte,4096>c{},d{};r_.memory().read({0x482000},c);r_.memory().read({0x5e6000},d);if(c!=code_page_||d!=constant_page_||r_.memory().load<unsigned>({slot})!=raw_iat)deny("SPI source page, constant page or owning raw IAT changed",slot);}
 void sync(){r_.cpu()=cpu(s_);m4_mixed::sync_fx(r_,s_);}
 void event(unsigned a,unsigned v,unsigned op){if(step_>=events_.size())deny("SPI access overflow",a);events_[step_++]={s_.gpr.rip.dword,a,v,4,op};if(after_source_event)after_source_event(*this,step_);}
 void transport(unsigned a,unsigned v,unsigned op){if(transport_count_>=transport_.size())deny("SPI transport overflow",a);transport_[transport_count_++]={call_pc,a,v,4,op};}
 unsigned transport_load(unsigned a){unsigned v{};try{v=r_.memory().load<unsigned>({a});}catch(...){deny("SPI checked transport read failure",a);}transport(a,v,0);return v;}
 void transport_store(unsigned a,unsigned v){try{r_.memory().store<unsigned>({a},v);}catch(...){deny("SPI checked transport write failure",a);}transport(a,v,1);}
 void expected(unsigned a,unsigned op){guard();unsigned wanted{},operation{},pc{};
  if(step_<3){wanted=frame_-4-4*step_;operation=1;pc=step_==0?0x482cc0:step_==1?0x482cc3:0x482cc4;}
  else if(step_==3){wanted=frame_-16;operation=1;pc=0x482cc8;}
  else if(step_<7){wanted=frame_-4*(step_+1);operation=1;pc=step_==4?0x482cd6:step_==5?0x482cd7:0x482cd9;}
  else if(step_<19){const auto n=(step_-7)/2;wanted=(step_%2)?0x5e6000+4*n:object+4*n;operation=(step_%2)?0:1;pc=0x482cdb;}
  else if(step_==19){wanted=slot;operation=0;pc=call_pc;}
  else if(step_==20){wanted=frame_-32;operation=1;pc=call_pc;}
  else if(step_<25){wanted=step_==24?frame_:frame_-12+4*(step_-21);operation=0;pc=step_==21?return_pc:step_==22?0x482ce6:step_==23?0x482ce7:0x482ce8;}
  else deny("SPI completed access sequence exceeded",a);
  if(a!=wanted||op!=operation||s_.gpr.rip.dword!=pc)deny("Unexpected literal SPI PC/access",a);
 }
 static void root_adapter(rt::Runtime&r){if(!owner||&owner->r_!=&r)throw std::runtime_error("SPI stable owner absent");owner->enter();}
 static void api_adapter(rt::Runtime&r){if(!owner||&owner->r_!=&r)throw std::runtime_error("SPI stable API owner absent");owner->api();}
 void api(){guard();if(api_called_||step_!=21||r_.cpu().esp!=frame_-32||r_.cpu().eip!=slot||s_.gpr.rsp.dword!=frame_-32)deny("SPI actual API dispatcher frame differs");
  HostGuard host;auto&receipt=m4_mixed::observation->spi_service;receipt.before=m4_mixed::cpu(s_);receipt.before.pc=call_pc;api_before_=view(s_);
  try{
   if(before_api)before_api(*this);source_check();const unsigned arguments[]{return_pc,SPI_GETWORKAREA,0,output,0};
   for(unsigned i=0;i<5;++i){const auto a=frame_-32+4*i,v=transport_load(a);if(v!=arguments[i])deny("SPI exact stdcall query arguments differ",a);}
   RECT rect{};for(unsigned i=0;i<4;++i){const auto v=transport_load(output+4*i);std::memcpy(reinterpret_cast<unsigned char*>(&rect)+4*i,&v,4);}receipt.rect_before=std::bit_cast<std::array<unsigned char,16>>(rect);
   // Declared idempotent checked transport probes establish writable output before the actual API.
   for(unsigned i=0;i<4;++i){unsigned v{};std::memcpy(&v,receipt.rect_before.data()+4*i,4);transport_store(output+4*i,v);}
   if(prove_export(query_)!=identity_)deny("Actual requested native export identity changed");
   struct alignas(16)Raw{std::array<unsigned char,512>b{};};Raw before{},after{};
   __asm__ volatile("fxsave64 %0\n\tfnstenv %1\n\tfldenv %1":"=m"(before),"=m"(receipt.env_before)::"memory");
   const auto result=query_(SPI_GETWORKAREA,0,&rect,0);
   __asm__ volatile("fxsave64 %0\n\tfnstenv %1\n\tfldenv %1":"=m"(after),"=m"(receipt.env_after)::"memory");
   const auto api_error=GetLastError();api_called_=true;receipt.called=1;receipt.BOOL_value=static_cast<unsigned>(result);receipt.guest_cleanup=16;receipt.fx_before=before.b;receipt.fx_after=after.b;receipt.rect_after=std::bit_cast<std::array<unsigned char,16>>(rect);
   witness_={1,reinterpret_cast<std::uintptr_t>(query_),reinterpret_cast<std::uintptr_t>(&rect),SPI_GETWORKAREA,0,output,0,static_cast<unsigned>(result),host.error,api_error,host.error,frame_-32,return_pc,16,0,0};
   if(after_api)after_api(*this);
   for(unsigned i=0;i<4;++i){unsigned v{};std::memcpy(&v,receipt.rect_after.data()+4*i,4);transport_store(output+4*i,v);}
   // Native representatives retain the incoming volatile fields and software SIMD; actual BOOL is carried in EAX.
   s_.gpr.rax.dword=static_cast<unsigned>(result);s_.gpr.rsp.dword+=20;s_.gpr.rip.dword=return_pc;receipt.after=m4_mixed::cpu(s_);api_after_=view(s_);sync();api_returned_=true;
   witness_[14]=witness_[15]=1;
   host.capture();m4_mixed::host(host.before.b.data(),host.after.b.data(),host.env_before.data(),host.env_after.data());if(!m4_mixed::observation->common.host_restored||GetLastError()!=host.error)deny("SPI native host/LastError restoration differs");
  }catch(const Abort&){throw;}catch(const std::exception&e){deny("SPI measured API/checked copy failure");}
 }
 void enter(){if(running_||used_||failed_||r_.poisoned()||thread_!=std::this_thread::get_id()||owner!=this||!r_.remill_seeded())throw std::runtime_error("Fresh SPI serial root owner required");
  m4_mixed::overlay_cpu(s_,r_.cpu());frame_=s_.gpr.rsp.dword;ret_=r_.memory().load<unsigned>({frame_});
  if(s_.gpr.rip.dword!=root||frame_<r_.stack_low().value+32||std::uint64_t(frame_)+4>r_.stack_top().value||s_.aflag.df||s_.addr.ds_base.dword||s_.addr.es_base.dword||s_.addr.ss_base.dword)throw std::runtime_error("SPI entry frame/flat forward domain required");
  used_=running_=true;
  try{source_check();m4_mixed::snapshot(r_,s_,true);auto token=mw34_spi_initializer_body(&s_,root,this);if(token!=this||!complete_||step_!=25||!api_called_||!api_returned_)deny("Complete literal SPI closure differs");sync();m4_mixed::snapshot(r_,s_,false);auto&rec=*m4_mixed::observation;rec.spi_phase=1;rec.spi_event_count=step_;rec.spi_transport_count=transport_count_;rec.spi_events=events_;rec.event_count=step_;rec.returns=1;rec.state_seeded=r_.remill_seeded();for(unsigned i=0;i<step_;++i){rec.events[i]={events_[i].address,events_[i].value,4,events_[i].operation};if(events_[i].operation)++rec.writes;else++rec.reads;}}
  catch(const Abort&){running_=false;throw std::runtime_error(fault_.reason);}catch(...){if(!failed_){failed_=true;fault_={s_.gpr.rip.dword,0,step_,"SPI observer/host exception retained"};}running_=false;throw;}running_=false;
 }
public:
 void(*after_source_event)(Session&,unsigned){};void(*before_api)(Session&){};void(*after_api)(Session&){};
 explicit Session(rt::Runtime&r):r_(r),s_(*reinterpret_cast<State*>(r.remill_state().data())){
  unsigned found{};for(const auto&i:r.image_metadata().imports)if(r.image_metadata().image_base+i.iat_rva==slot){auto library=i.library;std::transform(library.begin(),library.end(),library.begin(),[](unsigned char c){return static_cast<char>(std::tolower(c));});if(library!="user32.dll"||!i.name||*i.name!="SystemParametersInfoA"||i.original_iat_value!=raw_iat)throw std::invalid_argument("Exact SPI source import owner required");++found;}if(found!=1||r.memory().load<unsigned>({slot})!=raw_iat)throw std::invalid_argument("Exact SPI raw IAT required");
  r.memory().read({0x482000},code_page_);r.memory().read({0x5e6000},constant_page_);identity_=prove_export(query_);
  r.register_translation({{root},{rt::Abi::Cdecl,0,true},&root_adapter,"Literal connected SPI work-area initializer",{rt::Domain::admitted_game,m4::admitted_image_hash,5,spi_source_sha,spi_native_sha,spi_gate_sha}});
  r.register_service({{slot},{rt::Abi::Stdcall,16,true},&api_adapter,"Measured USER32 SystemParametersInfoA SPI_GETWORKAREA",rt::Domain::admitted_game,std::string(identity_.named_sha.data(),64),spi_gate_sha});
 }
 Session(const Session&)=delete;Session&operator=(const Session&)=delete;
 struct Borrow{Session&s;explicit Borrow(Session&v):s(v){if(owner||v.failed_||v.thread_!=std::this_thread::get_id())throw std::runtime_error("SPI serial borrow rejected");owner=&v;}~Borrow(){owner=nullptr;}};
 [[noreturn]]void deny(const char*why,unsigned at=0){if(!failed_){failed_=true;fault_={s_.gpr.rip.dword,at,step_,why};}throw Abort{};}
 unsigned read(unsigned a){expected(a,0);unsigned v{};try{v=r_.memory().load<unsigned>({a});}catch(...){deny("SPI checked source read failure",a);}if(a==slot&&v!=raw_iat)deny("SPI owning IAT changed",a);event(a,v,0);return a==slot?slot:v;}
 void write(unsigned a,unsigned v){expected(a,1);try{r_.memory().store<unsigned>({a},v);}catch(...){deny("SPI checked source write failure",a);}event(a,v,1);}
 void*call(State*s,unsigned pc){guard();if(s!=&s_||pc!=slot||step_!=21||s_.gpr.rsp.dword!=frame_-32||r_.memory().load<unsigned>({frame_-32})!=return_pc)deny("Actual literal SPI CALL frame differs");sync();r_.cpu().esp+=4;r_.cpu().eip=call_pc;r_.call_import({slot},{return_pc});return this;}
 void*returned(State*s,unsigned pc){guard();source_check();if(s!=&s_||complete_||pc!=ret_||s_.gpr.rip.dword!=pc||s_.gpr.rsp.dword!=frame_+4||step_!=25||!api_returned_)deny("Actual literal SPI RET frame differs");complete_=true;return this;}
 void*jump(State*s,unsigned pc);
 rt::Runtime&runtime(){return r_;}State&state(){return s_;}const auto&events()const{return events_;}const auto&transports()const{return transport_;}const auto&identity()const{return identity_;}const auto&api_before()const{return api_before_;}const auto&api_after()const{return api_after_;}const auto&witness()const{return witness_;}Fault fault()const{return fault_;}bool failed()const{return failed_;}bool complete()const{return complete_;}bool api_called()const{return api_called_;}unsigned step()const{return step_;}unsigned transport_count()const{return transport_count_;}
};
}
extern "C" unsigned mw34_spi_read32(void*p,unsigned a){return static_cast<mw34::m4_spi_connected::Session*>(p)->read(a);}
extern "C" void*mw34_spi_write32(void*p,unsigned a,unsigned v){static_cast<mw34::m4_spi_connected::Session*>(p)->write(a,v);return p;}
extern "C" void*mw34_spi_call(State*s,unsigned pc,void*p){return static_cast<mw34::m4_spi_connected::Session*>(p)->call(s,pc);}
extern "C" void*mw34_spi_return(State*s,unsigned pc,void*p){return static_cast<mw34::m4_spi_connected::Session*>(p)->returned(s,pc);}
extern "C" void*mw34_spi_jump(State*s,unsigned pc,void*p){return static_cast<mw34::m4_spi_connected::Session*>(p)->jump(s,pc);}
