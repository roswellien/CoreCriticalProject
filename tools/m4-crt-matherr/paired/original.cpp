// Actual isolated provider leaf; static game CALL is not executed here.
#include "protocol.hpp"
#include "pack_spec.hpp"
#include "probe_io.hpp"
#include "original_broker.hpp"
#include <iostream>
#include <memory>
using namespace mw34::m4_crt_probe;
namespace mp=mw34::m4_crt_matherr_paired;
static_assert(sizeof(void*)==4);
extern "C" {
Cpu crt_input{},crt_before{},crt_after{};std::uint32_t crt_host_esp{};
alignas(16) std::uint8_t crt_guest_fx[512]{},crt_host_fx[512]{},crt_host_after[512]{},crt_fx_before[512]{},crt_fx_after[512]{};
std::uint8_t crt_guest_env[28]{},crt_env_before[28]{},crt_env_after[28]{},crt_host_env[28]{},crt_host_env_after[28]{};
void crt_enter();void crt_capture();void crt_restore();
}
static std::uint32_t execute(){__try{crt_enter();return 0;}__except(EXCEPTION_EXECUTE_HANDLER){crt_restore();return 1;}}
struct Region{void*base;explicit Region(std::uint32_t a):base(mw34::original_broker::reserve_or_adopt(a)){}~Region(){VirtualFree(base,0,MEM_RELEASE);}Region(const Region&)=delete;};
static std::uint8_t*page(unsigned a){auto*p=static_cast<std::uint8_t*>(VirtualAlloc(reinterpret_cast<void*>(a),4096,MEM_COMMIT,PAGE_READWRITE));need(p==reinterpret_cast<void*>(a),"Exact paired page commit failed");return p;}
static void protect(void*p,DWORD desired){DWORD old{};need(VirtualProtect(p,4096,desired,&old)!=0,"Exact paired page protection failed");if(desired==PAGE_EXECUTE_READ)need(FlushInstructionCache(GetCurrentProcess(),p,4096)!=0,"Paired code cache flush failed");MEMORY_BASIC_INFORMATION m{};need(VirtualQuery(p,&m,sizeof(m))==sizeof(m)&&m.Protect==desired,"Actual paired protection rejected");}
int main(int argc,char**argv){try{
 SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);need(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))==0x60000000,"Fixed disjoint paired probe host image base rejected");
 if(argc==2&&std::string(argv[1])=="--check-hash"){hash_controls();std::cout<<"2 SHA controls passed\n";return 0;}
 if(auto result=mw34::original_broker::dispatch(argc,argv,5))return *result;
 need(argc==5,"Matherr original: exact-pack exact-provider exact-game fresh-output");
 std::vector<std::unique_ptr<Region>>regions;for(auto b:mw34::original_broker::bases)regions.push_back(std::make_unique<Region>(b));
 auto provider=read(argv[2],266293);need(provider.size()==266293&&digest(provider)=="2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7","Provider identity rejected");auto game=read(argv[3],2384384);need(game.size()==2384384&&digest(game)=="95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf","Game identity rejected");auto pack=read(argv[1],8220);need(pack.size()==8220&&digest(pack)==mp::pack_sha,"Pack identity rejected");need(std::memcmp(pack.data(),"MW4MTK01",8)==0,"Pack version rejected");unsigned n{};std::memcpy(&n,pack.data()+8,4);need(n==2,"Pack count rejected");
 std::array<std::uint8_t*,2>code{};for(unsigned i=0;i<2;++i){const auto offset=12+i*4104;unsigned base{},role{};std::memcpy(&base,pack.data()+offset,4);std::memcpy(&role,pack.data()+offset+4,4);need(base==(i?0x7800b000U:0x5ac000U)&&role==1,"Exact paired code page layout");code[i]=page(base);std::memcpy(code[i],pack.data()+offset+8,4096);protect(code[i],PAGE_EXECUTE_READ);}
 std::array<std::uint8_t*,3>memory{};for(unsigned k=0;k<3;++k)memory[k]=page(mp::pages[k]);auto*capture=page(0x10000000);std::memset(capture,0xcc,4096);capture[0x100]=0xe9;put32(capture+0x101,static_cast<unsigned>(reinterpret_cast<std::uintptr_t>(&crt_capture)-0x10000105));protect(capture,PAGE_EXECUTE_READ);
 Output out(argv[4]);out.write("MW4MOR01",8);const unsigned header[]{1,mp::record_count,mp::original_stride,12288};out.write(header,16);
 auto rec=std::make_unique<mp::OriginalRecord>();unsigned index{};
 for(unsigned repeat=0;repeat<2;++repeat)for(auto cw:controls)for(unsigned top=0;top<8;++top)for(unsigned arg=0;arg<8;++arg){
  *rec={};rec->tag={repeat,index,mp::arguments[arg],cw,top};mp::seed_pages(rec->memory[0],index,mp::arguments[arg]);for(unsigned k=0;k<3;++k)std::memcpy(memory[k],rec->memory[0].data()+k*4096,4096);
  mp::seed_fp(crt_guest_fx,crt_guest_env,cw,top,arg);crt_input=mp::input_cpu(index);crt_before={};crt_after={};need(execute()==0,"Actual matherr original leaf faulted");need(crt_before.pc==mp::entry&&crt_after.pc==mp::capture_pc&&crt_after.esp==mp::frame+4,"Actual matherr original entry/return capture rejected");
  need(std::memcmp(crt_host_fx,crt_host_after,512)==0&&std::memcmp(crt_host_env,crt_host_env_after,28)==0,"Complete matherr original host restoration rejected");rec->before=crt_before;rec->after=crt_after;
  const std::array<const std::uint8_t*,4>fx{crt_fx_before,crt_fx_after,crt_host_fx,crt_host_after},env{crt_env_before,crt_env_after,crt_host_env,crt_host_env_after};for(unsigned k=0;k<4;++k){std::memcpy(rec->fx[k].data(),fx[k],512);std::memcpy(rec->env[k].data(),env[k],28);}for(unsigned k=0;k<3;++k)std::memcpy(rec->memory[1].data()+k*4096,memory[k],4096);
  out.write(rec.get(),sizeof(*rec));++index;
 }
 need(index==mp::record_count,"Exact original matherr schedule");for(unsigned k=0;k<2;++k)need(std::memcmp(code[k],pack.data()+20+k*4104,4096)==0,"Actual paired RX code changed");out.commit();std::cout<<"1536 actual original matherr records captured; callback never executed\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
