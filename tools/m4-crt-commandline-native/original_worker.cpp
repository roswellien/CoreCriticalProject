// Actual original11-byte writer plus an explicitly authored outer JMP/capture.
#include "common.hpp"
#include "spec.hpp"
#include "original_broker.hpp"
#include <memory>
using namespace mw34;using namespace mw34::m4_cmd_native;
static_assert(sizeof(void*)==4);
extern "C" {
Cpu crt_input{},crt_before{},crt_after{},cmd_service_before{},cmd_service_after{};std::uint32_t crt_host_esp{},cmd_api{};
alignas(16)std::uint8_t crt_guest_fx[512]{},crt_host_fx[512]{},crt_host_after[512]{},crt_fx_before[512]{},crt_fx_after[512]{},cmd_service_fx_before[512]{},cmd_service_fx_after[512]{};
std::uint8_t crt_guest_env[28]{},crt_env_before[28]{},crt_env_after[28]{},crt_host_env[28]{},crt_host_env_after[28]{},cmd_service_env_before[28]{},cmd_service_env_after[28]{};
void crt_enter();void crt_capture();void crt_restore();void cmd_service();
}
static unsigned execute(){__try{crt_enter();return 0;}__except(EXCEPTION_EXECUTE_HANDLER){crt_restore();return 1;}}
struct Region{void*base;explicit Region(unsigned a):base(mw34::original_broker::reserve_or_adopt(a)){}~Region(){VirtualFree(base,0,MEM_RELEASE);}Region(const Region&)=delete;};
static std::uint8_t*page(unsigned a){auto*p=static_cast<std::uint8_t*>(VirtualAlloc(reinterpret_cast<void*>(a),4096,MEM_COMMIT,PAGE_READWRITE));require(p==reinterpret_cast<void*>(a),"Exact owned original page commit failed");return p;}
static void protect(void*p,DWORD desired){DWORD old{};require(VirtualProtect(p,4096,desired,&old)!=0,"Original protection failed");if(desired==PAGE_EXECUTE_READ)require(FlushInstructionCache(GetCurrentProcess(),p,4096)!=0,"Original instruction cache failed");}
static void snapshot(Record&r,bool before,const std::array<std::uint8_t*,5>&pages){auto&v=before?r.memory_before:r.memory_after;for(unsigned i=0;i<5;++i)std::memcpy(v.data()+4096*i,pages[i],4096);}
int main(){try{
 SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);if(auto result=mw34::original_broker::dispatch())return *result;
 auto provider=readfile(environment("MW34_CMN_PROVIDER"),266293),game=readfile(environment("MW34_CMN_GAME"),2384384),pack=readfile(environment("MW34_CMN_PACK"),12324);Provider exact(provider);require(pack.size()==12324&&m4::sha256(pack)==pack_sha,"Exact original private pack required");require(game.size()==2384384&&m4::sha256(game)==m4::admitted_image_hash,"Exact original game identity required");auto parsed=m4::load_pe32(game);unsigned owner{};for(auto&i:parsed.metadata.imports)if(i.iat_rva+0x400000==game_iat.value){require(i.name&&*i.name=="_acmdln"&&library(i.library,"msvcrt.dll"),"Actual game data owner required");++owner;}require(owner==1,"One actual data import owner required");
 Output output(environment("MW34_CMN_OUTPUT"));auto supplied=environment("MW34_CMN_SUPPLIED");std::vector<std::unique_ptr<Region>>regions;for(auto b:mw34::original_broker::bases)regions.push_back(std::make_unique<Region>(b));std::array<std::uint8_t*,5>pages{};for(unsigned i=0;i<5;++i)pages[i]=page(observed_pages[i]);
 for(unsigned i=0;i<3;++i)std::memcpy(pages[i],pack.data()+20+i*4104,4096);parsed.memory.read({0x5bb000},std::as_writable_bytes(std::span{pages[3],4096}));auto*stub=page(0x10000000);std::memset(stub,0xcc,4096);stub[0x100]=0xe9;m4_crt_probe::put32(stub+0x101,static_cast<unsigned>(reinterpret_cast<std::uintptr_t>(&crt_capture)-0x10000105));stub[0x200]=0xe9;m4_crt_probe::put32(stub+0x201,static_cast<unsigned>(reinterpret_cast<std::uintptr_t>(&cmd_service)-0x10000205));protect(stub,PAGE_EXECUTE_READ);
 // Only isolated original transport patches IAT to the authored instrumented
 // broker; the broker calls the actual associated Windows target, no fake result.
 cmd_api=static_cast<unsigned>(reinterpret_cast<std::uintptr_t>(&GetCommandLineA));m4_crt_probe::put32(pages[1]+0x34,service_gate.value);protect(pages[0],PAGE_EXECUTE_READ);protect(pages[1],PAGE_READONLY);protect(pages[3],PAGE_READONLY);
 auto first=own_host_input();prefix(output,false,supplied,first.bytes);unsigned id{};
 for(unsigned repeat=0;repeat<2;++repeat)for(auto cw:m4_crt_probe::controls)for(unsigned top:{0U,7U}){
  Record r{};r.id=id++;r.repeat=repeat;r.cw=cw;r.top=top;std::memset(pages[4],0xa5,4096);m4_crt_probe::put32(pages[4]+0x800,capture_gate.value);std::memcpy(pages[2],pack.data()+20+2*4104,4096);snapshot(r,true,pages);
  m4_crt_probe::seed_fp(crt_guest_fx,crt_guest_env,cw,top);crt_input=m4_crt_probe::seed_cpu(0);crt_input.pc=writer.value;r.status=execute();require(!r.status,"Actual original writer/provider query faulted");r.before=crt_before;r.after=crt_after;r.service_before=cmd_service_before;r.service_after=cmd_service_after;
  std::memcpy(r.fx_before.data(),crt_fx_before,512);std::memcpy(r.fx_after.data(),crt_fx_after,512);std::memcpy(r.host_before.data(),crt_host_fx,512);std::memcpy(r.host_after.data(),crt_host_after,512);std::memcpy(r.service_fx_before.data(),cmd_service_fx_before,512);std::memcpy(r.service_fx_after.data(),cmd_service_fx_after,512);
  std::memcpy(r.env_before.data(),crt_env_before,28);std::memcpy(r.env_after.data(),crt_env_after,28);std::memcpy(r.host_env_before.data(),crt_host_env,28);std::memcpy(r.host_env_after.data(),crt_host_env_after,28);std::memcpy(r.service_env_before.data(),cmd_service_env_before,28);std::memcpy(r.service_env_after.data(),cmd_service_env_after,28);r.host_restored=hostequal(r,false);require(r.host_restored,"Actual original host restoration failed");
  auto current=own_host_input();require(first.bytes==current.bytes&&first.borrowed_pointer==current.borrowed_pointer,"Original actual OS pointer/bytes changed");r.input_bytes=static_cast<unsigned>(current.bytes.size());r.input_regions=static_cast<unsigned>(current.regions.size());r.host_pointer=current.borrowed_pointer;r.api_before=api_record(current.before);r.api_after=api_record(current.after);snapshot(r,false,pages);r.data_address=provider_global.value;std::memcpy(&r.data_value,pages[2]+0x174,4);require(r.data_value==current.borrowed_pointer&&r.after.eax==r.data_value,"Actual original returned pointer/global mismatch");require(r.after.pc==capture_gate.value&&r.after.esp==0x20001800&&r.service_before.esp==0x200017fc&&r.service_after.esp==0x200017fc,"Actual original CALL/RET0 continuation failed");r.route={service_gate.value,return_pc.value,r.service_before.esp,r.after.esp,1};r.capture=1;
  output.write(&r,sizeof(r));output.write(current.regions.data(),static_cast<unsigned>(current.regions.size()*sizeof(HostRegion)));output.write(current.bytes.data(),static_cast<unsigned>(current.bytes.size()));
 }
 require(id==cases,"Original command-line extent failed");output.commit();std::cout<<"48 actual original writer/provider cases captured; authored capture only\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
