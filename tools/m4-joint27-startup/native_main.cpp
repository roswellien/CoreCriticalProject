// New build-only candidate until separate source/COFF review authorizes captures.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include "joint_protocol.hpp"
#include "session.hpp"
#include "mixed_bindings.hpp"
#include "admission.hpp"
#include "../m4-initializer-chain/runtime_adapter.hpp"
#include "../m4-integer-startup/runtime_adapter.hpp"
#include "protocol.hpp"
#include "corpus.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <vector>
namespace ni=mw34::m4_nmx_integration;
namespace old=mw34::m4_numeric_max;
static void need(bool b,const char*m){old::require(b,m);}
#include "caller_observer.inc"
namespace mw34::m4_mixed {
thread_local Native*observation{};
void verify_current_fp_code(m4_runtime::Runtime&r){for(const auto&b:fp_bindings)if(b.entry==r.cpu().eip){std::vector<std::byte>bytes(b.bytes);r.memory().read({b.entry},bytes);require(m4::sha256(bytes)==b.code,"Joint current FP code identity changed");return;}throw std::runtime_error("Joint FP code binding absent");}
#include "seed.inc"
#pragma pack(push,1)
struct SequenceRecord {
 std::array<std::uint32_t,12>tags;
 std::array<std::byte,512>host_before,host_after;
 std::array<std::byte,28>host_env_before,host_env_after;
 std::array<std::byte,3504>state_before,state_after;
 std::array<std::byte,57344>memory_before,memory_after;
};
#pragma pack(pop)
static_assert(sizeof(SequenceRecord)==122824);
static void memory(m4_runtime::Runtime&r,std::span<std::byte,57344>b){for(unsigned i=0;i<pages.size();++i)r.memory().read({pages[i]},b.subspan(i*4096,4096));}
static void root_entry(ni::Session&s){snapshot(s.runtime(),s.state(),true);}
struct FirstFault{unsigned phase{},pc{},address{},step{},kind{};};
struct PhaseFp{struct alignas(16)Image{std::array<std::uint8_t,512>b;};Image fx{};std::array<std::uint8_t,28>env{};void capture(){__asm__ volatile("fxsave64 %0\n\tfnstenv %1\n\tfldenv %1":"=m"(fx),"=m"(env)::"memory");}};
class Context {
 m4_runtime::Runtime r_;State&s_;std::unique_ptr<ni::Session>session_;std::uint16_t admitted_cw_;bool attempted_{},failed_{};FirstFault first_{};
 void canonical(){for(auto x:std::array<std::uint8_t,11>{s_.sw.ie,s_.sw.de,s_.sw.ze,s_.sw.oe,s_.sw.ue,s_.sw.pe,s_.sw.sf,s_.sw.c0,s_.sw.c1,s_.sw.c2,s_.sw.c3})require(x<=1,"Joint noncanonical FP shadow byte");}
public:
 unsigned completed{};
 Context(std::span<const std::byte>game,std::span<const std::byte>provider,unsigned repeat,unsigned cw,unsigned top):r_(m4_runtime::Runtime::from_admitted_image(game,[](){m4_runtime::Policy p;p.stack_low={0x20001000};p.stack_bytes=4096;return p;}())),s_(*std::construct_at(reinterpret_cast<State*>(r_.remill_state().data()))),admitted_cw_(static_cast<std::uint16_t>(cw)){
  require(std::find(controls.begin(),controls.end(),cw)!=controls.end()&&(top==0||top==7),"Joint authored initial CW/TOP domain");
  mw34::m4_initializer_chain::register_component(r_,chain_object,chain_gate);mw34::m4_integer_startup::register_component(r_,integer_object,integer_gate);
  for(const auto&b:fp_bindings)r_.register_translation({{b.entry},{m4_runtime::Abi::Cdecl,0,true},b.native,"Joint inherited FP root",{m4_runtime::Domain::admitted_game,m4::admitted_image_hash,b.bytes,b.code,b.object,b.gate}});
  session_=std::make_unique<ni::Session>(r_,provider,ni::Proof{numeric_object,numeric_gate});session_->observe_root_entry=&root_entry;r_.freeze_registry();seed(r_,repeat,cw,top);
 }
 // Own one stable numerical boundary around all27calls, Borrow, observations,
 // internal catches and owner cleanup. Return cannot unwind after restoration.
 bool invoke_selected_table(unsigned sequence,unsigned repeat,unsigned top,std::vector<Native>&records)noexcept{
  ni::NumericHostBoundary boundary(admitted_cw_);bool ok=false;unsigned phase=0;
  try{
   require(!attempted_&&!failed_,"Joint stable context already attempted");attempted_=true;ni::Session::Borrow borrow(*session_);
   auto ledger=r_.prepare_initializers({0x5e0000},{0x5e0244});require(ledger.items().size()==145,"Joint full ledger snapshot differs");
   for(const auto&item:ledger.items()){
    if(std::find(entries.begin(),entries.end(),item.target.value)==entries.end())continue;
    canonical();require(r_.cpu().esp==frame+4,"Joint persistent caller ESP differs");Native record{};record.common.sequence=sequence;record.common.repeat=repeat;record.common.phase=phase;record.common.table_slot=item.slot.value;record.common.entry=item.target.value;record.common.cw=admitted_cw_;record.common.initial_top=top;record.host_observation_kind=item.target.value==ni::root?2:1;
    const auto start=r_.calls().size();PhaseFp raw_before{},raw_after{};if(item.target.value==ni::root)raw_before.capture();observation=&record;
    try{r_.call_direct(item.target,{broker});}catch(...){observation=nullptr;throw;}observation=nullptr;
    if(item.target.value==ni::root){
     raw_after.capture();snapshot_numeric(record);record.numeric_phase=1;record.host_observation_kind=2;observation=&record;host(raw_before.fx.b.data(),raw_after.fx.b.data(),raw_before.env.data(),raw_after.env.data());observation=nullptr;
    }
    require(!record.common.status&&record.state_seeded&&!record.domain_error,"Joint actual callback incomplete");
    const auto count=r_.calls().size()-start;require(count==(record.numeric_phase?3U:1U),"Joint real dispatcher route extent differs");
    for(unsigned i=0;i<count;++i){const auto&call=r_.calls()[start+i];record.runtime_routes[i*5]=call.site.value;record.runtime_routes[i*5+1]=call.target.value;record.runtime_routes[i*5+2]=call.return_pc.value;record.runtime_routes[i*5+3]=call.import;record.runtime_routes[i*5+4]=call.completed;require(call.completed,"Joint actual route did not complete");}
    require(record.common.before.pc==item.target.value&&record.common.before.gpr[4]==frame&&record.common.after.pc==broker&&record.common.after.gpr[4]==frame+4,"Joint actual CALL/RET frame differs");records.push_back(record);++phase;completed=phase;
   }
   require(phase==27&&r_.calls().size()==29&&r_.translation_count()==28&&!ledger.completed()&&!ledger.failed(),"Joint selected27 registration/route/partial ledger extent differs");ok=true;
  }catch(...){observation=nullptr;failed_=true;if(!first_.kind){first_={phase,r_.cpu().eip,0,session_->step(),1};if(session_->failed()){auto f=session_->fault();first_.pc=f.pc;first_.address=f.address;first_.step=f.step;first_.kind=2;}}}
  return ok;
 }
 void snapshot_numeric(Native&record){observation=&record;snapshot(r_,s_,false);observation=nullptr;auto cp=session_->checkpoint();std::memcpy(record.numeric_checkpoint.data(),&cp,4084);const auto&e=session_->events();record.event_count=session_->step();require(record.event_count==22&&session_->complete()&&!session_->failed(),"Joint real numeric closure differs");for(unsigned i=0;i<22;++i){record.events[i]={e[i].address,e[i].value,e[i].width,e[i].write};record.numeric_PC_events[i*5]=e[i].pc;record.numeric_PC_events[i*5+1]=e[i].address;record.numeric_PC_events[i*5+2]=e[i].value;record.numeric_PC_events[i*5+3]=e[i].width;record.numeric_PC_events[i*5+4]=e[i].write;if(e[i].write)++record.writes;else++record.reads;}record.clears=record.tests=1;record.returns=3;record.state_seeded=r_.remill_seeded();}
 m4_runtime::Runtime&runtime(){return r_;}State&state(){return s_;}ni::Session&session(){return *session_;}bool failed()const{return failed_;}FirstFault fault()const{return first_;}
};
}
int main(int argc,char**argv){try{
 using namespace mw34;using namespace m4_mixed;need(argc==4,"Joint27 exact game/provider fresh-directory");auto game=old::read(argv[1],2384384),provider=old::read(argv[2],565760);m4::admit_image(std::as_bytes(std::span{game}));need(old::sha256(provider)==ni::provider_sha,"Exact joint provider identity");auto out=std::filesystem::path(argv[3]);need(!std::filesystem::exists(out)&&std::filesystem::create_directory(out),"Fresh joint27 output required");
 old::Output phases((out/"native.bin").string().c_str()),sequences((out/"sequences.bin").string().c_str());const unsigned header[]{1,48,27,1296,14,sizeof(Native)};phases.write("MW4J27N1",8);phases.write(header,sizeof(header));const unsigned sequence_header[]{1,48,sizeof(SequenceRecord),14};sequences.write("MW4J27S1",8);sequences.write(sequence_header,sizeof(sequence_header));unsigned seq=0,total=0;
 for(unsigned repeat=0;repeat<2;++repeat)for(auto cw:controls)for(unsigned top:{0U,7U}){
  Context context(std::as_bytes(std::span{game}),std::as_bytes(std::span{provider}),repeat,cw,top);SequenceRecord summary{};std::memcpy(summary.state_before.data(),&context.state(),3504);memory(context.runtime(),summary.memory_before);std::vector<Native>records;records.reserve(27);
  Host caller(static_cast<std::uint16_t>(cw));const bool ok=context.invoke_selected_table(seq,repeat,top,records);caller.capture();summary.host_before=caller.before.b;summary.host_after=caller.after.b;summary.host_env_before=caller.env;summary.host_env_after=caller.env_after;std::memcpy(summary.state_after.data(),&context.state(),3504);memory(context.runtime(),summary.memory_after);auto fault=context.fault();summary.tags={seq,repeat,cw,top,unsigned(ok),context.completed,unsigned(context.failed()),unsigned(context.runtime().poisoned()),fault.phase,fault.pc,fault.address,fault.step};
  if(!ok){old::Output failure((out/("failed-sequence-"+std::to_string(seq)+".bin")).string().c_str());const unsigned failed_header[]{1,1,sizeof(SequenceRecord),14};failure.write("MW4J27F1",8);failure.write(failed_header,sizeof(failed_header));failure.write(summary);failure.commit();throw std::runtime_error("Joint27 invocation refused; complete sequence diagnostic preserved");}
  sequences.write(summary);need(records.size()==27,"Joint27 successful phase extent differs");for(const auto&r:records){phases.write(r);++total;}++seq;
 }
 need(seq==48&&total==1296,"Exact joint27 schedule");phases.commit();sequences.commit();std::cout<<"1296 native phases in48 persistent27-root sequences; fullM4 incomplete\n";return 0;
}catch(const std::exception&e){mw34::m4_mixed::observation=nullptr;ni::owner=nullptr;std::cerr<<e.what()<<'\n';return 1;}}
