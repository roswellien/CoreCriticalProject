// Hardware execution of four exact staged-provider bodies, authored callbacks.
// No expected output, game entry, DLL loader, imports or DllMain execution.
#include "probe_common.hpp"
#include "probe_io.hpp"
#include "probe_spec.hpp"
#include "original_broker.hpp"
#include <iostream>
#include <memory>
using namespace mw34::m4_crt_probe;
static_assert(sizeof(void*)==4);
extern "C" {
Cpu crt_input{},crt_before{},crt_after{};std::uint32_t crt_host_esp{};
alignas(16) std::uint8_t crt_guest_fx[512]{},crt_host_fx[512]{},crt_host_after[512]{},crt_fx_before[512]{},crt_fx_after[512]{};
std::uint8_t crt_guest_env[28]{},crt_env_before[28]{},crt_env_after[28]{},crt_host_env[28]{},crt_host_env_after[28]{};
void crt_enter();void crt_capture();void crt_restore();
}
static std::uint32_t execute(){__try{crt_enter();return 0;}__except(EXCEPTION_EXECUTE_HANDLER){crt_restore();return 1;}}
struct Region {void*base;explicit Region(std::uint32_t address):base(mw34::original_broker::reserve_or_adopt(address)){}~Region(){VirtualFree(base,0,MEM_RELEASE);}Region(const Region&)=delete;};
static void protect(void*p,DWORD flags){DWORD old{};need(VirtualProtect(p,4096,flags,&old),"Page protect failed");if(flags==PAGE_EXECUTE_READ)need(FlushInstructionCache(GetCurrentProcess(),p,4096),"Code cache flush failed");}
static std::uint8_t*page(std::uint32_t address){auto*p=static_cast<std::uint8_t*>(VirtualAlloc(reinterpret_cast<void*>(address),4096,MEM_COMMIT,PAGE_READWRITE));need(p==reinterpret_cast<void*>(address),"Exact page commit failed");return p;}
static void capture_memory(std::uint8_t*out){std::memcpy(out,reinterpret_cast<void*>(stack_page),4096);std::memcpy(out+4096,reinterpret_cast<void*>(table_page),4096);std::memcpy(out+8192,reinterpret_cast<void*>(0x78038ee8),12);}
int main(int argc,char**argv){try{
 SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
 if(argc==2&&std::string(argv[1])=="--check-hash"){hash_controls();std::cout<<"2 SHA controls passed\n";return 0;}
 if(auto result=mw34::original_broker::dispatch(argc,argv,4))return *result;
 need(argc==4,"CRT reference: exact-pack exact-provider fresh-output");std::vector<std::unique_ptr<Region>>regions;for(auto b:mw34::original_broker::bases)regions.push_back(std::make_unique<Region>(b));
 const auto provider=read(argv[2],266293);need(provider.size()==266293&&digest(provider)=="2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7","Provider identity rejected");
 const auto pack=read(argv[1],8220);need(pack.size()==8220&&digest(pack)==pack_sha,"Pack identity rejected");need(std::memcmp(pack.data(),"MW4CRPK1",8)==0,"Pack version rejected");std::uint32_t count{};std::memcpy(&count,pack.data()+8,4);need(count==2,"Pack count rejected");
 std::array<std::uint8_t*,2>code{};for(unsigned i=0;i<2;++i){const auto offset=12+i*4104;std::uint32_t base{},perms{};std::memcpy(&base,pack.data()+offset,4);std::memcpy(&perms,pack.data()+offset+4,4);need(base==(i?0x78004000U:0x78001000U)&&perms==1,"Exact provider code page layout");code[i]=page(base);std::memcpy(code[i],pack.data()+offset+8,4096);protect(code[i],PAGE_EXECUTE_READ);}
 auto*stack=page(stack_page);auto*table=page(table_page);auto*globals=page(0x78038000)+0xee8;
 auto*capture=page(0x10000000);std::memset(capture,0xcc,4096);capture[0x100]=0xe9;const auto delta=static_cast<std::uint32_t>(reinterpret_cast<std::uintptr_t>(&crt_capture)-0x10000105);put32(capture+0x101,delta);protect(capture,PAGE_EXECUTE_READ);
 auto*cb=page(0x10001000);std::memset(cb,0xcc,4096);for(unsigned i=0;i<5;++i){const auto b=callback_bytes(i);std::memcpy(cb+callbacks[i]-0x10001000,b.data(),b.size());}const auto callback_page=std::vector<std::uint8_t>(cb,cb+4096);protect(cb,PAGE_EXECUTE_READ);
 Output out(argv[3]);out.write("MW4CRO01",8);const std::uint32_t header[]{1,record_count,original_stride,memory_bytes};out.write(header,sizeof(header));std::array<std::uint8_t,memory_bytes>before{},after{};
 for(unsigned repeat=0;repeat<2;++repeat)for(unsigned c=0;c<9;++c)for(auto cw:controls)for(unsigned top=0;top<8;++top){
  seed_memory(stack,table,globals,c);capture_memory(before.data());seed_fp(crt_guest_fx,crt_guest_env,cw,top);crt_input=seed_cpu(c);crt_before={};crt_after={};const auto status=execute();need(status==0,"Original CRT body faulted");need(crt_after.pc==sentinel&&crt_after.esp==stack_entry+4,"Original CRT return contract failed");
  need(std::memcmp(crt_host_fx,crt_host_after,5)==0&&std::memcmp(crt_host_fx+24,crt_host_after+24,4)==0&&std::memcmp(crt_host_env,crt_host_env_after,28)==0,"Host FP environment restoration failed");
  for(unsigned j=0;j<8;++j)need(std::memcmp(crt_host_fx+32+16*j,crt_host_after+32+16*j,10)==0,"Host raw x87 storage restoration failed");need(std::memcmp(crt_host_fx+160,crt_host_after+160,128)==0,"Host XMM restoration failed");capture_memory(after.data());
  const std::uint32_t tag[]{repeat,c,cw,top,status};out.write(tag,sizeof(tag));out.write(&crt_before,sizeof(Cpu));out.write(&crt_after,sizeof(Cpu));for(auto s:{crt_fx_before,crt_fx_after,crt_host_fx,crt_host_after})out.write(s,512);for(auto s:{crt_env_before,crt_env_after,crt_host_env,crt_host_env_after})out.write(s,28);out.write(before.data(),before.size());out.write(after.data(),after.size());
 }
 for(unsigned i=0;i<2;++i)need(std::memcmp(code[i],pack.data()+12+i*4104+8,4096)==0,"Provider RX bytes changed");need(std::memcmp(cb,callback_page.data(),4096)==0,"Authored callback RX bytes changed");out.commit();std::cout<<"1728 actual original CRT provider records captured; native equivalence pending\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
