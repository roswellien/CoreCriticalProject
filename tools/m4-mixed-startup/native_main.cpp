// Diagnostic selected-root integration; the complete CRT/table is still open.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include "native_protocol.hpp"
#include "admission.hpp"
#include "../m4-initializer-chain/runtime_adapter.hpp"
#include "../m4-integer-startup/runtime_adapter.hpp"
#include "mixed_bindings.hpp"
#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>

namespace mw34::m4_mixed {
thread_local Native *observation{};
void verify_current_fp_code(m4_runtime::Runtime &runtime){
  for(const auto &binding:fp_bindings)if(binding.entry==runtime.cpu().eip){
    std::vector<std::byte> bytes(binding.bytes);runtime.memory().read({binding.entry},bytes);
    require(mw34::m4::sha256(bytes)==binding.code,"Mixed FP original code changed after registration");return;
  }
  throw std::runtime_error("Missing current FP code binding");
}
class Output {
  std::filesystem::path destination,stage;HANDLE handle=INVALID_HANDLE_VALUE;bool owns{};
public:
  explicit Output(const char *path):destination(path),stage(destination.string()+".mixed-stage-"+std::to_string(GetCurrentProcessId())){
    require(!std::filesystem::exists(destination),"Fresh mixed output required");
    handle=CreateFileW(stage.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
    require(handle!=INVALID_HANDLE_VALUE,"Fresh mixed stage required");owns=true;
  }
  void write(const void *data,unsigned size){DWORD actual{};require(WriteFile(handle,data,size,&actual,nullptr)&&actual==size,"Mixed output write failed");}
  void commit(){require(FlushFileBuffers(handle),"Mixed output flush failed");require(CloseHandle(handle),"Mixed output close failed");handle=INVALID_HANDLE_VALUE;
    require(MoveFileExW(stage.c_str(),destination.c_str(),MOVEFILE_WRITE_THROUGH),"Mixed output commit failed");owns=false;}
  ~Output(){if(handle!=INVALID_HANDLE_VALUE)CloseHandle(handle);if(owns)DeleteFileW(stage.c_str());}
};
static void seed(m4_runtime::Runtime &runtime,unsigned repeat,unsigned cw,unsigned top){
  auto &s=*std::launder(reinterpret_cast<State *>(runtime.remill_state().data()));
  auto *raw=reinterpret_cast<std::uint8_t *>(&s);const auto pattern=repeat*3571+cw;
  for(unsigned i=0;i<3504;++i)raw[i]=static_cast<std::uint8_t>(i*29+pattern+(i>>8)*7);
  std::memset(&s.addr,0,sizeof(s.addr));std::memset(&s.x87,0,sizeof(s.x87));
  s.addr.fs_base.dword=runtime.fs_base().value;s.seg.cs.flat=0x23;s.seg.ds.flat=0x2b;s.seg.ss.flat=0x2b;
  runtime.cpu()={0x13579bdf,0x2468ace0,0x81726354,0x10293847,frame+4,0x92837465,0x56473829,0xaabbccdd,0x202,broker};
  overlay_cpu(s,runtime.cpu());s.x87.fxsave.cwd.flat=cw;s.x87.fxsave.swd.flat=top<<11;s.x87.fxsave.mxcsr.flat=0x1f80;
  s.sw.ie=s.sw.de=s.sw.ze=s.sw.oe=s.sw.ue=s.sw.pe=s.sw.sf=s.sw.c0=s.sw.c1=s.sw.c2=s.sw.c3=0;
  for(unsigned i=0;i<8;++i){std::memset(&s.st.elems[i].val,0,10);std::memset(&s.vec[i],0,16);}
  runtime.mark_remill_seeded();sync_fx(runtime,s);
  // Authored reference stack fixture, initialized once per complete sequence.
  std::array<std::byte,4096> stack{};stack.fill(std::byte{0xa5});runtime.memory().write({0x20001000},stack);
  runtime.memory().store<std::uint32_t>({frame},broker);
}
static void register_all(m4_runtime::Runtime &runtime){
  using namespace m4_runtime;
  mw34::m4_initializer_chain::register_component(runtime,chain_object,chain_gate);
  mw34::m4_integer_startup::register_component(runtime,integer_object,integer_gate);
  for(const auto &b:fp_bindings)runtime.register_translation({{b.entry},{Abi::Cdecl,0,true},b.native,"Mixed FP initializer "+std::to_string(b.entry),{Domain::admitted_game,mw34::m4::admitted_image_hash,b.bytes,b.code,b.object,b.gate}});
  runtime.freeze_registry();
}
static void controls_for_shared_fp(std::span<const std::byte> image){
  using namespace m4_runtime;unsigned positives{},denials{},poisoned{};
  for(const auto &binding:fp_bindings)for(unsigned scenario=0;scenario<10;++scenario){
    Policy policy{};policy.stack_low={0x20001000};policy.stack_bytes=4096;
    auto runtime=Runtime::from_admitted_image(image,policy);register_all(runtime);seed(runtime,0,0x37f,7);
    auto &s=*std::launder(reinterpret_cast<State *>(runtime.remill_state().data()));Native record{};observation=&record;
    switch(scenario){
    case 1:s.addr.fs_base.dword+=4;break;
    case 2:s.x87.fxsave.ftw.flat=1;runtime.fx()[4]=std::byte{1};break;
    case 3:s.x87.fxsave.cwd.flat=0x37e;runtime.fx()[0]=std::byte{0x7e};break;
    case 4:s.x87.fxsave.mxcsr.flat=0x1f81;runtime.fx()[24]=std::byte{0x81};break;
    case 5:runtime.fx()[1]=std::byte{2};break;
    case 6:{for(const auto &region:runtime.image_metadata().mapped_regions)if(binding.entry>=region.start.value&&binding.entry<region.start.value+region.size){runtime.memory().protect(region.start,mw34::Permissions::read|mw34::Permissions::write);break;}
      const auto byte=runtime.memory().load<std::uint8_t>({binding.entry});runtime.memory().store<std::uint8_t>({binding.entry},byte^1);break;}
    case 7:{for(const auto &region:runtime.image_metadata().mapped_regions)if(0x5c8000>=region.start.value&&0x5c8000<region.start.value+region.size){runtime.memory().protect(region.start,mw34::Permissions::none);break;}break;}
    case 9:s.x87.fxsave.swd.flat|=0x8000;runtime.fx()[3]|=std::byte{0x80};break;
    }
    bool rejected{};try{runtime.call_direct({binding.entry},{scenario==8?0x10000100U:broker});}catch(const Fault &error){rejected=true;
      require(scenario==8?error.reason()==FaultReason::abi_violation:error.reason()==FaultReason::memory_access,"Unexpected shared context failure route");}
    observation=nullptr;
    if(!scenario){require(!rejected&&record.common.host_restored&&record.state_seeded&&runtime.calls().size()==1&&runtime.calls()[0].completed,"Shared FP positive control failed");++positives;}
    else{require(rejected&&(runtime.calls().empty()||!runtime.calls()[0].completed),"Invalid shared context became a successful callback");++denials;
      if(scenario!=8){bool stopped{};try{runtime.call_direct({binding.entry},{broker});}catch(const Fault &error){stopped=error.reason()==FaultReason::poisoned;}require(stopped,"Failed shared context was reused");++poisoned;}}
  }
  require(positives==10&&denials==90&&poisoned==80,"Shared context control extent differs");
  std::cout<<"{\"passed\":true,\"positive_callbacks\":10,\"invalid_context_denials\":90,\"poisoned_reuse_denials\":80}\n";
}
}
int main(int argc,char **argv){try{
  using namespace mw34::m4_mixed;using namespace mw34::m4_runtime;
  SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
  if(argc==2&&std::string(argv[1])=="--layout"){std::cout<<"{\"record_size\":103468,\"common_size\":92388,\"State_size\":3504,\"pages\":11,\"selected_roots\":26,\"full_ledger_completed\":false}\n";return 0;}
  require(argc==3,"Usage: mixed_native exact-image fresh-output, or --check-context exact-image");
  const bool controls_mode=std::string(argv[1])=="--check-context";
  std::ifstream input(argv[controls_mode?2:1],std::ios::binary);require(bool(input),"Admitted image unavailable");
  const std::vector<char> image((std::istreambuf_iterator<char>(input)),{});
  // Admission occurs before creating output ownership.
  mw34::m4::admit_image(std::as_bytes(std::span{image}));
  if(controls_mode){controls_for_shared_fp(std::as_bytes(std::span{image}));return 0;}
  Output output(argv[2]);const std::uint32_t header[]{1,48,26,1248,11,sizeof(Native)};
  output.write("MW4MXN01",8);output.write(header,sizeof(header));unsigned sequence{},phases{};
  for(unsigned repeat=0;repeat<2;++repeat)for(auto cw:controls)for(unsigned top:{0U,7U}){
    Policy policy{};policy.stack_low={0x20001000};policy.stack_bytes=4096;
    auto runtime=Runtime::from_admitted_image(std::as_bytes(std::span{image}),policy);
    register_all(runtime);seed(runtime,repeat,cw,top);
    auto ledger=runtime.prepare_initializers({0x5e0000},{0x5e0244});require(ledger.items().size()==145,"Full initializer snapshot differs");
    unsigned phase{},slot{};
    for(const auto &item:ledger.items()){
      ++slot;if(std::find(entries.begin(),entries.end(),item.target.value)==entries.end())continue;
      Native record{};record.common.sequence=sequence;record.common.repeat=repeat;record.common.phase=phase;record.common.table_slot=item.slot.value;
      record.common.entry=item.target.value;record.common.cw=cw;record.common.initial_top=top;
      require(runtime.cpu().esp==frame+4,"Persistent caller stack differs");
      observation=&record;
      try{runtime.call_direct(item.target,{broker});}catch(...){observation=nullptr;throw;}
      observation=nullptr;
      require(!record.common.status&&record.common.host_restored&&record.state_seeded&&!record.domain_error,"Mixed callback observation failed");
      require(record.common.before.pc==item.target.value&&record.common.before.gpr[4]==frame&&record.common.after.pc==broker&&record.common.after.gpr[4]==frame+4,"Mixed recorded actual ABI differs");
      output.write(&record,sizeof(record));++phase;++phases;
    }
    require(phase==26&&runtime.calls().size()==26&&runtime.translation_count()==26&&!ledger.completed()&&!ledger.failed(),"Selected root count/order or partial ledger differs");
    for(const auto &call:runtime.calls())require(call.completed&&!call.import&&call.return_pc.value==broker,"Actual selected call route incomplete");
    ++sequence;
  }
  require(phases==1248&&sequence==48,"Mixed sequence extent differs");output.commit();
  std::cout<<"1248 actual selected-root phases, 48 persistent sequences; differential comparison and review required; full ledger incomplete\n";
  return 0;
}catch(const std::exception &error){std::cerr<<error.what()<<'\n';return 1;}}
