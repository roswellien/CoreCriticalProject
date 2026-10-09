#include "protocol.hpp"
#include "../m3-slice/original_broker.hpp"
#include <iostream>
using namespace mw34::m3_subsystem;
static_assert(sizeof(void*)==4);
extern "C"{
Cpu s3_input{},s3_before{},s3_after{};std::uint32_t s3_host_esp{};
alignas(16)std::uint8_t s3_guest_fx[512]{},s3_host_fx[512]{},s3_host_after[512]{},s3_fx_before[512]{},s3_fx_after[512]{};
std::uint8_t s3_guest_env[28]{},s3_env_before[28]{},s3_env_after[28]{},s3_host_env[28]{},s3_host_env_after[28]{};
void s3_enter();void s3_capture();void s3_restore_fp();
}
static std::uint32_t execute(){__try{s3_enter();return 0;}__except(EXCEPTION_EXECUTE_HANDLER){s3_restore_fp();return 1;}}
struct Reservation{
 void*base{};Reservation(std::uint32_t address){base=mw34::original_broker::reserve_or_adopt(address);}
 ~Reservation(){if(base)VirtualFree(base,0,MEM_RELEASE);}Reservation(const Reservation&)=delete;
 void*commit(std::uint32_t address,std::size_t size=page_size){auto*p=VirtualAlloc(reinterpret_cast<void*>(address),size,MEM_COMMIT,PAGE_READWRITE);require(p==reinterpret_cast<void*>(address),"Original subsystem page commit failed");return p;}
 static void rx(void*p){DWORD old{};require(VirtualProtect(p,page_size,PAGE_EXECUTE_READ,&old)&&FlushInstructionCache(GetCurrentProcess(),p,page_size),"Original subsystem RX mapping failed");}
};
static bool host_restored(){
 if(std::memcmp(s3_host_fx,s3_host_after,5)||std::memcmp(s3_host_fx+24,s3_host_after+24,4)||std::memcmp(s3_host_env,s3_host_env_after,28))return false;
 for(unsigned i=0;i<8;++i)if(std::memcmp(s3_host_fx+32+i*16,s3_host_after+32+i*16,10))return false;
 return !std::memcmp(s3_host_fx+160,s3_host_after+160,128);
}
int main(int argc,char**argv){try{
 SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
 if(auto broker=mw34::original_broker::dispatch(argc,argv,6))return *broker;
 if(argc==2&&std::string(argv[1])=="--check-protocol"){std::cout<<"Sequence protocol controls: "<<protocol_controls()<<"\n";return 0;}
 require(argc==6,"Subsystem original: input output settercode consumercode image");
 // One reservation for both code pages; one for stack plus two buffer pages.
 // Uncommitted surrounding pages, including20002000, remain NOACCESS.
 Reservation code_region(0x550000),data_region(0x20000000),global_region(0x720000),capture_region(0x10000000);
 auto*setcode=code_region.commit(0x558000);auto*concode=code_region.commit(0x55a000);auto*stack=data_region.commit(stack_base);auto*buffer=data_region.commit(buffer_base,8192);auto*globals=global_region.commit(global_base);auto*stubpage=capture_region.commit(0x10000000);
 admit_output(argv[2]);const auto codes=admit_codes(argv[3],argv[4],argv[5]);std::ifstream in(argv[1],std::ios::binary);const auto matrix=read_requests(in);
 std::memcpy(static_cast<std::uint8_t*>(setcode)+(setter-0x558000),codes[0].data(),codes[0].size());std::memcpy(static_cast<std::uint8_t*>(concode)+(consumer-0x55a000),codes[1].data(),codes[1].size());
 auto*stub=static_cast<std::uint8_t*>(stubpage)+256;stub[0]=0xe9;const auto delta=static_cast<std::uint32_t>(reinterpret_cast<std::uintptr_t>(&s3_capture)-(sentinel+5));std::memcpy(stub+1,&delta,4);
 Reservation::rx(setcode);Reservation::rx(concode);Reservation::rx(stubpage);
 const std::filesystem::path dest(argv[2]),stage=dest.string()+".s3-stage-"+std::to_string(GetCurrentProcessId());require(!std::filesystem::exists(stage),"Output staging exists");struct Cleanup{std::filesystem::path p;~Cleanup(){std::error_code e;std::filesystem::remove(p,e);}}cleanup{stage};
 std::ofstream out(stage,std::ios::binary|std::ios::trunc);write_record(out,output_header(output_count(matrix),32));
 auto capture_pages=[&](auto&b){std::memcpy(b.data(),stack,4096);std::memcpy(b.data()+4096,globals,4096);std::memcpy(b.data()+8192,buffer,8192);};
 for(unsigned sequence=0;sequence<matrix.size();++sequence){const auto&q=matrix[sequence];const auto b=initial_memory(q);std::memcpy(stack,b.data(),4096);std::memcpy(globals,b.data()+4096,4096);std::memcpy(buffer,b.data()+8192,8192);
  std::memcpy(s3_guest_fx,q.fx.data(),512);const auto env=seed_env(q);std::memcpy(s3_guest_env,env.data(),28);
  for(unsigned index=0;index<q.step_count;++index){const auto&s=q.steps[index];Result r{};r.sequence_index=sequence;r.step_index=index;r.observation_mode=0;
   const std::uint32_t frame[]{sentinel,s.arg_a,s.arg_b};std::memcpy(static_cast<std::uint8_t*>(stack)+(s.state.registers[4]-stack_base),frame,s.state.eip==setter?12:4);
   capture_pages(r.memory_before);s3_input=s.state;s3_before={};s3_after={};r.status=execute();r.host_restored=host_restored();require(!r.status&&r.host_restored,"Original subsystem execution/host restoration failed");
   r.cpu_before=s3_before;r.cpu_after=s3_after;std::memcpy(r.fx_before.data(),s3_fx_before,512);std::memcpy(r.fx_after.data(),s3_fx_after,512);std::memcpy(r.env_before.data(),s3_env_before,28);std::memcpy(r.env_after.data(),s3_env_after,28);capture_pages(r.memory_after);
   // Actual prior guest captures restore persistent FP state at the next entry.
   std::memcpy(s3_guest_fx,s3_fx_after,512);std::memcpy(s3_guest_env,s3_env_after,28);
   // No original per-access tracing is performed; mode0 State/events stay zero.
   write_record(out,r);
  }
 }
 out.close();require(bool(out),"Original staged subsystem output failed");require(MoveFileExW(stage.c_str(),dest.c_str(),MOVEFILE_WRITE_THROUGH),"Original subsystem output commit failed");std::cout<<"Executed "<<output_count(matrix)<<" original subsystem entries; actual pages/CPU/FX/ENV, access trace unobserved\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
