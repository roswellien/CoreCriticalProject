// Actual complete original wrapper, import tail jump and measured provider.
#include "common.hpp"
#include "probe_io.hpp"
#include "probe_spec.hpp"
#include "original_broker.hpp"
#include <iostream>
#include <memory>
using namespace mw34::m4_crt_probe;namespace ci=mw34::m4_crt_control_integration;
static_assert(sizeof(void*)==4);
extern "C" {
Cpu crt_input{},crt_before{},crt_after{};std::uint32_t crt_host_esp{};
alignas(16) std::uint8_t crt_guest_fx[512]{},crt_host_fx[512]{},crt_host_after[512]{},crt_fx_before[512]{},crt_fx_after[512]{};
std::uint8_t crt_guest_env[28]{},crt_env_before[28]{},crt_env_after[28]{},crt_host_env[28]{},crt_host_env_after[28]{};
void crt_enter();void crt_capture();void crt_restore();
}
static std::uint32_t execute(){__try{crt_enter();return 0;}__except(EXCEPTION_EXECUTE_HANDLER){crt_restore();return 1;}}
struct Region{void*base;explicit Region(std::uint32_t a):base(mw34::original_broker::reserve_or_adopt(a)){}~Region(){VirtualFree(base,0,MEM_RELEASE);}Region(const Region&)=delete;};
static std::uint8_t*page(unsigned a){auto*p=static_cast<std::uint8_t*>(VirtualAlloc(reinterpret_cast<void*>(a),4096,MEM_COMMIT,PAGE_READWRITE));need(p==reinterpret_cast<void*>(a),"Exact connected page commit failed");return p;}
static void protect(void*p,DWORD desired){DWORD old{};need(VirtualProtect(p,4096,desired,&old)!=0,"Exact connected page protection failed");if(desired==PAGE_EXECUTE_READ)need(FlushInstructionCache(GetCurrentProcess(),p,4096)!=0,"Connected code cache flush failed");MEMORY_BASIC_INFORMATION m{};need(VirtualQuery(p,&m,sizeof(m))==sizeof(m)&&m.Protect==desired,"Actual connected protection rejected");}
int main(int argc,char**argv){try{
 SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
 need(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))==0x60000000,"Fixed disjoint connected probe host image base rejected");
 if(argc==2&&std::string(argv[1])=="--check-hash"){hash_controls();std::cout<<"2 SHA controls passed\n";return 0;}
 if(auto result=mw34::original_broker::dispatch(argc,argv,5))return *result;
 need(argc==5,"Connected control reference: exact-pack exact-provider exact-game fresh-output");std::vector<std::unique_ptr<Region>>regions;for(auto b:mw34::original_broker::bases)regions.push_back(std::make_unique<Region>(b));
 const auto provider=read(argv[2],266293);need(provider.size()==266293&&digest(provider)=="2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7","Provider identity rejected");const auto game=read(argv[3],2384384);need(game.size()==2384384&&digest(game)=="95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf","Game identity rejected");const auto pack=read(argv[1],16428);need(pack.size()==16428&&digest(pack)==ci::pack_sha,"Pack identity rejected");need(std::memcmp(pack.data(),"MW4CIPK1",8)==0,"Pack version rejected");unsigned count{};std::memcpy(&count,pack.data()+8,4);need(count==4,"Pack count rejected");
 std::array<std::uint8_t*,4>pages{};const unsigned addresses[]{0x5ac000,0x5bb000,0x78004000,0x78011000};
 for(unsigned i=0;i<4;++i){const auto offset=12+i*4104;unsigned base{},role{};std::memcpy(&base,pack.data()+offset,4);std::memcpy(&role,pack.data()+offset+4,4);need(base==addresses[i]&&role==(i==1?2U:1U),"Exact connected page layout");pages[i]=page(base);std::memcpy(pages[i],pack.data()+offset+8,4096);protect(pages[i],i==1?PAGE_READONLY:PAGE_EXECUTE_READ);}
 auto*stack=page(stack_page);auto*capture=page(0x10000000);std::memset(capture,0xcc,4096);capture[0x100]=0xe9;put32(capture+0x101,static_cast<unsigned>(reinterpret_cast<std::uintptr_t>(&crt_capture)-0x10000105));protect(capture,PAGE_EXECUTE_READ);
 Output out(argv[4]);out.write("MW4CIC01",8);const unsigned header[]{1,ci::records,ci::original_stride,4096};out.write(header,16);std::array<std::uint8_t,4096>before{},after{};
 for(unsigned repeat=0;repeat<2;++repeat)for(auto cw:controls)for(unsigned scenario=0;scenario<8;++scenario){
  crt_input=ci::cpu(scenario);std::memset(stack,0xa5,4096);put32(stack+ci::stack_offsets[scenario],ci::outer_return);std::memcpy(before.data(),stack,4096);seed_fp(crt_guest_fx,crt_guest_env,cw,0);crt_before={};crt_after={};need(execute()==0,"Actual connected original body faulted");need(crt_after.pc==sentinel&&crt_after.esp==crt_input.esp+4,"Actual connected game return/capture failed");need(std::memcmp(crt_host_fx,crt_host_after,512)==0&&std::memcmp(crt_host_env,crt_host_env_after,28)==0,"Complete connected host restoration failed");std::memcpy(after.data(),stack,4096);
  const unsigned tags[]{repeat,cw,scenario};out.write(tags,12);out.write(&crt_before,40);out.write(&crt_after,40);for(auto p:{crt_fx_before,crt_fx_after,crt_host_fx,crt_host_after})out.write(p,512);for(auto p:{crt_env_before,crt_env_after,crt_host_env,crt_host_env_after})out.write(p,28);out.write(before.data(),4096);out.write(after.data(),4096);
 }
 for(unsigned i=0;i<4;++i)need(std::memcmp(pages[i],pack.data()+20+i*4104,4096)==0,"Actual connected RX/RO source changed");out.commit();std::cout<<"192 actual original connected game control records captured; native comparison pending\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
