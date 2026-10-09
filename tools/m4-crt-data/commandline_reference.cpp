// Exact initialization writer fragment; actual Windows GetCommandLineA import.
#include "probe_common.hpp"
#include "probe_io.hpp"
#include "commandline_spec.hpp"
#include "original_broker.hpp"
#include <iostream>
#include <memory>
using namespace mw34::m4_crt_probe;
namespace cd=mw34::m4_crt_data;
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
static void protect(void*p,DWORD desired){DWORD old{};need(VirtualProtect(p,4096,desired,&old)!=0,"Original page protection failed");if(desired==PAGE_EXECUTE_READ)need(FlushInstructionCache(GetCurrentProcess(),p,4096)!=0,"Original instruction cache failed");MEMORY_BASIC_INFORMATION m{};need(VirtualQuery(p,&m,sizeof(m))==sizeof(m)&&m.Protect==desired,"Actual original page protection rejected");}
struct ObservedRegion{std::uint32_t base,bytes,allocation,state,type,protect,allocation_protect;};
static ObservedRegion query(const void*p){MEMORY_BASIC_INFORMATION m{};need(VirtualQuery(p,&m,sizeof(m))==sizeof(m),"Observed memory query failed");return {static_cast<std::uint32_t>(reinterpret_cast<std::uintptr_t>(m.BaseAddress)),static_cast<std::uint32_t>(m.RegionSize),static_cast<std::uint32_t>(reinterpret_cast<std::uintptr_t>(m.AllocationBase)),m.State,m.Type,m.Protect,m.AllocationProtect};}
static std::vector<std::uint8_t> commandline(const char*p,std::vector<ObservedRegion>&regions){
 need(p!=nullptr,"Actual OS command-line pointer null");std::vector<std::uint8_t>out;std::uintptr_t boundary{};
 for(unsigned i=0;i<131072;++i){const auto at=reinterpret_cast<std::uintptr_t>(p)+i;need(at<=0xffffffffULL,"Actual command-line pointer wrap");if(at>=boundary){auto m=query(reinterpret_cast<const void*>(at));need(m.state==MEM_COMMIT&&!(m.protect&(PAGE_GUARD|PAGE_NOACCESS))&&(m.protect&(PAGE_READONLY|PAGE_READWRITE|PAGE_WRITECOPY|PAGE_EXECUTE_READ|PAGE_EXECUTE_READWRITE|PAGE_EXECUTE_WRITECOPY)),"Actual command-line buffer not readable");boundary=static_cast<std::uintptr_t>(m.base)+m.bytes;need(boundary>at,"Actual command-line query extent");regions.push_back(m);}const auto b=static_cast<std::uint8_t>(p[i]);out.push_back(b);if(!b)return out;}
 throw std::runtime_error("Actual command-line NUL exceeds admitted bound");
}
int main(int argc,char**argv){try{
 SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
 if(argc==2&&std::string(argv[1])=="--check-hash"){hash_controls();std::cout<<"2 SHA controls passed\n";return 0;}
 if(auto result=mw34::original_broker::dispatch(argc,argv,4))return *result;
 need(argc==4,"CRT command-line reference: exact-pack exact-provider fresh-output");std::vector<std::unique_ptr<Region>>regions;for(auto b:mw34::original_broker::bases)regions.push_back(std::make_unique<Region>(b));
 const auto provider=read(argv[2],266293);need(provider.size()==266293&&digest(provider)=="2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7","Provider identity rejected");const auto pack=read(argv[1],4112);need(pack.size()==4112&&digest(pack)==cd::pack_sha,"Pack identity rejected");need(std::memcmp(pack.data(),"MW4CMPK1",8)==0,"Pack version rejected");std::uint32_t base{},bytes{};std::memcpy(&base,pack.data()+8,4);std::memcpy(&bytes,pack.data()+12,4);need(base==0x78001000&&bytes==4096,"Original fragment layout rejected");
 auto*code=page(0x78001000);std::memcpy(code,pack.data()+16,4096);protect(code,PAGE_EXECUTE_READ);auto*imports=page(0x7802e000);std::memset(imports,0xa5,4096);const auto api=static_cast<std::uint32_t>(reinterpret_cast<std::uintptr_t>(&GetCommandLineA));put32(imports+0x34,api);protect(imports,PAGE_READONLY);auto*globals=page(0x78037000);auto*stack=page(stack_page);auto*capture=page(0x10000000);std::memset(capture,0xcc,4096);capture[0x100]=0xe9;put32(capture+0x101,static_cast<std::uint32_t>(reinterpret_cast<std::uintptr_t>(&crt_capture)-0x10000105));protect(capture,PAGE_EXECUTE_READ);
 const auto*system=GetCommandLineA();const auto system_address=static_cast<std::uint32_t>(reinterpret_cast<std::uintptr_t>(system));std::vector<ObservedRegion>buffer_regions;const auto buffer=commandline(system,buffer_regions);const auto api_region=query(reinterpret_cast<const void*>(api));need(api_region.state==MEM_COMMIT&&api_region.type==MEM_IMAGE&&(api_region.protect&(PAGE_EXECUTE|PAGE_EXECUTE_READ|PAGE_EXECUTE_READWRITE|PAGE_EXECUTE_WRITECOPY)),"Actual imported OS target not executable image");
 std::array<char,32768>module_path{};const auto path_bytes=GetModuleFileNameA(reinterpret_cast<HMODULE>(api_region.allocation),module_path.data(),static_cast<DWORD>(module_path.size()));need(path_bytes>0&&path_bytes<module_path.size(),"Actual OS target module path unavailable");const auto module=read(module_path.data(),16*1024*1024);const auto module_sha=digest(module);
 need(buffer_regions.size()<65536,"Actual buffer region count bound");const auto stride=18636+static_cast<std::uint32_t>(buffer_regions.size())*sizeof(ObservedRegion);
 Output out(argv[3]);out.write("MW4CMD01",8);const std::uint32_t header[]{1,192,stride,static_cast<std::uint32_t>(buffer.size()),api,api_region.allocation,system_address,path_bytes,static_cast<std::uint32_t>(buffer_regions.size())};out.write(header,sizeof(header));out.write(module_path.data(),path_bytes);out.write(module_sha.data(),64);out.write(&api_region,sizeof(api_region));out.write(buffer_regions.data(),buffer_regions.size()*sizeof(ObservedRegion));out.write(buffer.data(),buffer.size());
 std::array<std::uint8_t,4096>sb{},sa{},gb{},ga{};
 for(unsigned repeat=0;repeat<2;++repeat)for(auto cw:controls)for(unsigned top=0;top<8;++top){
  std::memset(stack,0xa5,4096);put32(stack+0x800,sentinel);std::memset(globals,0xa5,4096);std::memcpy(sb.data(),stack,4096);std::memcpy(gb.data(),globals,4096);seed_fp(crt_guest_fx,crt_guest_env,cw,top);crt_input=seed_cpu(0);crt_input.pc=0x7800188c;crt_before={};crt_after={};const auto status=execute();need(status==0,"Actual command-line writer fragment faulted");need(crt_after.pc==sentinel&&crt_after.esp==stack_entry,"Actual indirect stdcall/fragment continuation failed");std::uint32_t initialized{};std::memcpy(&initialized,globals+0x174,4);need(initialized==system_address&&crt_after.eax==initialized,"Actual initialized _acmdln differs from OS pointer");need(std::memcmp(crt_host_fx,crt_host_after,512)==0&&std::memcmp(crt_host_env,crt_host_env_after,28)==0,"Complete actual host restoration failed");std::memcpy(sa.data(),stack,4096);std::memcpy(ga.data(),globals,4096);std::vector<ObservedRegion>after_regions;const auto same_pointer=GetCommandLineA()==system;const auto same_bytes=commandline(system,after_regions)==buffer;const auto same_count=after_regions.size()==buffer_regions.size();const auto same_regions=same_count&&std::memcmp(after_regions.data(),buffer_regions.data(),buffer_regions.size()*sizeof(ObservedRegion))==0;
  (void)same_regions;bool same_owner=same_count;for(unsigned j=0;same_owner&&j<buffer_regions.size();++j){const auto&a=buffer_regions[j];const auto&b=after_regions[j];same_owner=a.base==b.base&&a.allocation==b.allocation&&a.state==b.state&&a.type==b.type&&a.protect==b.protect&&a.allocation_protect==b.allocation_protect;}
  need(same_pointer&&same_bytes&&same_owner,"OS buffer bytes/pointer/readable allocation identity changed during measurement");
  const std::uint32_t tags[]{repeat,cw,top};out.write(tags,sizeof(tags));out.write(&crt_before,40);out.write(&crt_after,40);for(auto p:{crt_fx_before,crt_fx_after,crt_host_fx,crt_host_after})out.write(p,512);for(auto p:{crt_env_before,crt_env_after,crt_host_env,crt_host_env_after})out.write(p,28);for(const auto*p:{sb.data(),sa.data(),gb.data(),ga.data()})out.write(p,4096);out.write(after_regions.data(),after_regions.size()*sizeof(ObservedRegion));
 }
 need(std::memcmp(code,pack.data()+16,4096)==0,"Actual RX fragment bytes changed");need(*reinterpret_cast<const std::uint32_t*>(imports+0x34)==api,"Actual imported target cell changed");out.commit();std::cout<<"192 actual original command-line writer observations captured; full DllMain and native admission pending\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
