// Exact complete staged-provider CW bodies only; no expected results or imports.
#include "common.hpp"
#include "probe_io.hpp"
#include "probe_spec.hpp"
#include "original_broker.hpp"
#include <iostream>
#include <memory>
using namespace mw34::m4_crt_probe;
namespace cf=mw34::m4_crt_control;
static_assert(sizeof(void*)==4);
extern "C" {
Cpu crt_input{},crt_before{},crt_after{};std::uint32_t crt_host_esp{};
alignas(16) std::uint8_t crt_guest_fx[512]{},crt_host_fx[512]{},crt_host_after[512]{},crt_fx_before[512]{},crt_fx_after[512]{};
std::uint8_t crt_guest_env[28]{},crt_env_before[28]{},crt_env_after[28]{},crt_host_env[28]{},crt_host_env_after[28]{};
void crt_enter();void crt_capture();void crt_restore();
}
static std::uint32_t execute(){__try{crt_enter();return 0;}__except(EXCEPTION_EXECUTE_HANDLER){crt_restore();return 1;}}
struct Region{void*base;explicit Region(std::uint32_t a):base(mw34::original_broker::reserve_or_adopt(a)){}~Region(){VirtualFree(base,0,MEM_RELEASE);}Region(const Region&)=delete;};
static std::uint8_t*page(std::uint32_t a){auto*p=static_cast<std::uint8_t*>(VirtualAlloc(reinterpret_cast<void*>(a),4096,MEM_COMMIT,PAGE_READWRITE));need(p==reinterpret_cast<void*>(a),"Exact page commit failed");return p;}
static void rx(void*p){DWORD old{};need(VirtualProtect(p,4096,PAGE_EXECUTE_READ,&old)&&FlushInstructionCache(GetCurrentProcess(),p,4096),"Exact RX page protection failed");MEMORY_BASIC_INFORMATION m{};need(VirtualQuery(p,&m,sizeof(m))==sizeof(m)&&m.Protect==PAGE_EXECUTE_READ,"Actual RX protection rejected");}
int main(int argc,char**argv){try{
 SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
 if(argc==2&&std::string(argv[1])=="--check-hash"){hash_controls();std::cout<<"2 SHA controls passed\n";return 0;}
 if(auto result=mw34::original_broker::dispatch(argc,argv,4))return *result;
 need(argc==4,"CRT control reference: exact-pack exact-provider fresh-output");std::vector<std::unique_ptr<Region>>regions;for(auto b:mw34::original_broker::bases)regions.push_back(std::make_unique<Region>(b));
 const auto provider=read(argv[2],266293);need(provider.size()==266293&&digest(provider)=="2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7","Provider identity rejected");const auto pack=read(argv[1],8220);need(pack.size()==8220&&digest(pack)==cf::pack_sha,"Pack identity rejected");need(std::memcmp(pack.data(),"MW4CFPK1",8)==0,"Pack version rejected");std::uint32_t count{};std::memcpy(&count,pack.data()+8,4);need(count==2,"Pack count rejected");
 std::array<std::uint8_t*,2>code{};for(unsigned i=0;i<2;++i){const auto offset=12+i*4104;std::uint32_t base{},perms{};std::memcpy(&base,pack.data()+offset,4);std::memcpy(&perms,pack.data()+offset+4,4);need(base==(i?0x78011000U:0x78004000U)&&perms==1,"Exact control provider page layout");code[i]=page(base);std::memcpy(code[i],pack.data()+offset+8,4096);rx(code[i]);}
 auto*stack=page(stack_page);auto*capture=page(0x10000000);std::memset(capture,0xcc,4096);capture[0x100]=0xe9;const auto delta=static_cast<std::uint32_t>(reinterpret_cast<std::uintptr_t>(&crt_capture)-0x10000105);put32(capture+0x101,delta);rx(capture);
 Output out(argv[3]);out.write("MW4CFC01",8);const std::uint32_t header[]{1,cf::records,cf::original_stride,4096};out.write(header,16);std::array<std::uint8_t,4096>before{},after{};
 for(unsigned repeat=0;repeat<2;++repeat)for(unsigned entry=0;entry<2;++entry)for(unsigned c=0;c<cf::cases;++c)for(auto cw:controls){
  const auto q=cf::input(c);std::memset(stack,0xa5,4096);put32(stack+0x800,sentinel);put32(stack+0x804,q.value);put32(stack+0x808,q.mask);std::memcpy(before.data(),stack,4096);seed_fp(crt_guest_fx,crt_guest_env,cw,0);crt_input=cf::cpu(entry);crt_before={};crt_after={};const auto status=execute();need(status==0,"Actual control provider body faulted");need(crt_after.pc==sentinel&&crt_after.esp==stack_entry+4,"Actual provider cdecl return failed");need(std::memcmp(crt_host_fx,crt_host_after,512)==0&&std::memcmp(crt_host_env,crt_host_env_after,28)==0,"Complete actual host FP restoration failed");std::memcpy(after.data(),stack,4096);
  const std::uint32_t tag[]{repeat,entry,c,cw,q.value,q.mask};out.write(tag,24);out.write(&crt_before,40);out.write(&crt_after,40);for(auto s:{crt_fx_before,crt_fx_after,crt_host_fx,crt_host_after})out.write(s,512);for(auto s:{crt_env_before,crt_env_after,crt_host_env,crt_host_env_after})out.write(s,28);out.write(before.data(),4096);out.write(after.data(),4096);
 }
 for(unsigned i=0;i<2;++i)need(std::memcmp(code[i],pack.data()+12+i*4104+8,4096)==0,"Actual provider RX bytes changed");out.commit();std::cout<<"3264 actual original complete CRT control records captured; native equivalence pending\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
