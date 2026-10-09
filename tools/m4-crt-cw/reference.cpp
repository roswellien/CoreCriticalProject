// Authored FLDCW/FNSTCW hardware micro-contract. No vendor or game execution.
#include "probe_io.hpp"
#include <iostream>
using namespace mw34::m4_crt_probe;
static_assert(sizeof(void*)==4);
namespace {
alignas(16) std::uint8_t guest_fx[512]{},host_fx[512]{},host_after[512]{},fx_before[512]{},fx_after[512]{};
std::uint8_t guest_env[28]{},env_before[28]{},env_after[28]{},host_env[28]{},host_env_after[28]{};
std::uint16_t requested{},observed{};
__declspec(noinline) void enter(){
 __asm {
  fxsave host_fx
  fnstenv host_env
  fxrstor guest_fx
  fldenv guest_env
  fxsave fx_before
  fnstenv env_before
  fldcw requested
  fnstcw observed
  fxsave fx_after
  fnstenv env_after
  fxrstor host_fx
  fldenv host_env
  fxsave host_after
  fnstenv host_env_after
  fldenv host_env
 }
}
__declspec(noinline) void restore(){
 __asm {
  fxrstor host_fx
  fldenv host_env
  fxsave host_after
  fnstenv host_env_after
  fldenv host_env
 }
}
std::uint32_t execute(){__try{enter();return 0;}__except(EXCEPTION_EXECUTE_HANDLER){const auto error=GetExceptionCode();restore();return error;}}
}
int main(int argc,char**argv){try{
 SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
 if(argc==2&&std::string(argv[1])=="--check-hash"){hash_controls();std::cout<<"2 SHA controls passed\n";return 0;}
 need(argc==2,"CW reference: fresh-output");Output out(argv[1]);out.write("MW4CW001",8);const std::uint32_t header[]{1,131072,2176,65536};out.write(header,sizeof(header));unsigned hardware_faults{};
 for(unsigned repeat=0;repeat<2;++repeat)for(unsigned input=0;input<65536;++input){
  seed_fp(guest_fx,guest_env,0x037f,0);requested=static_cast<std::uint16_t>(input);observed=0;std::memset(fx_before,0,512);std::memset(fx_after,0,512);std::memset(env_before,0,28);std::memset(env_after,0,28);
  const auto status=execute();hardware_faults+=status!=0;
  // A hardware rejection remains a recorded rejection; the input is never
  // replaced with a convenient masked/reserved-bit value and rerun.
  need(std::memcmp(host_fx,host_after,512)==0&&std::memcmp(host_env,host_env_after,28)==0,"Exact actual host FX/ENV restoration failed");
  const std::uint32_t tag[]{repeat,input,observed,status};out.write(tag,sizeof(tag));for(auto p:{fx_before,fx_after,host_fx,host_after})out.write(p,512);for(auto p:{env_before,env_after,host_env,host_env_after})out.write(p,28);
 }
 out.commit();std::cout<<"131072 authored hardware CW observations captured; hardware_faults="<<hardware_faults<<"; no provider/native bridge admission\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
