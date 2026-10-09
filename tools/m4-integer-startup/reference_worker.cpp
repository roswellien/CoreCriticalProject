#include "protocol.hpp"
#include "original_broker.hpp"
#include "staging.hpp"
#include <iostream>
#include <memory>
using namespace mw34::m4_integer_startup;
static_assert(sizeof(void *)==4);
extern "C" {Cpu m4_input{},m4_before{},m4_after{};std::uint32_t m4_host_esp{};
alignas(16)std::uint8_t m4_guest_fx[512]{},m4_host_fx[512]{},m4_host_after[512]{},m4_fx_before[512]{},m4_fx_after[512]{};
std::uint8_t m4_env_before[28]{},m4_env_after[28]{},m4_host_env[28]{},m4_host_env_after[28]{};void m4_enter();void m4_capture();void m4_restore_fp();}
static std::uint32_t execute(){__try{m4_enter();return 0;}__except(EXCEPTION_EXECUTE_HANDLER){m4_restore_fp();return 1;}}
struct Region{void *reservation{};Region(std::uint32_t base){reservation=mw34::original_broker::reserve_or_adopt(base);require(reservation==reinterpret_cast<void *>(base),"Original batch region reservation differs");}~Region(){if(reservation)VirtualFree(reservation,0,MEM_RELEASE);}Region(const Region&)=delete;};
static void commit(std::uint32_t address){require(VirtualAlloc(reinterpret_cast<void *>(address),4096,MEM_COMMIT,PAGE_READWRITE)==reinterpret_cast<void *>(address),"Original batch page commit failed");}
static void rx(std::uint32_t address){DWORD old{};require(VirtualProtect(reinterpret_cast<void *>(address),4096,PAGE_EXECUTE_READ,&old)&&FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void *>(address),4096),"Original batch RX failed");}
static void copy_memory(std::array<std::uint8_t,memory_size> &bytes){for(unsigned i=0;i<3;++i)std::memcpy(bytes.data()+i*page_size,reinterpret_cast<void *>(i==0?stack_base:(i==1?global_base:second_global_base)),page_size);}
int main(int argc,char **argv){try{
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);if(auto broker=mw34::original_broker::dispatch(argc,argv,5))return *broker;
    if(argc==2&&std::string(argv[1])=="--check-protocol"){std::cout<<"Protocol controls: "<<protocol_controls()<<'\n';return 0;}
    if(argc==4&&std::string(argv[1])=="--stage-collision-control"){stage_collision_control(argv[2],argv[3]);return 0;}
    require(argc==5,"Integer reference: input output code image");std::vector<std::unique_ptr<Region>> regions;for(auto base:mw34::original_broker::bases)regions.push_back(std::make_unique<Region>(base));
    admit_output(argv[2]);const auto code=admit_code(argv[3],argv[4]);std::ifstream input(argv[1],std::ios::binary);const auto rows=read_requests(input);
    for(auto page:{0x43a000U,0x467000U,0x4b5000U,0x4c7000U,0x4cf000U,stack_base,global_base,second_global_base,0x10000000U})commit(page);
    for(const auto &f:fragments)std::memcpy(reinterpret_cast<void *>(f.entry),code.data()+f.bundle,f.size);
    auto *stub=reinterpret_cast<std::uint8_t *>(sentinel);stub[0]=0xe9;const auto delta=static_cast<std::uint32_t>(reinterpret_cast<std::uintptr_t>(&m4_capture)-(sentinel+5));std::memcpy(stub+1,&delta,4);
    for(auto page:{0x43a000U,0x467000U,0x4b5000U,0x4c7000U,0x4cf000U,0x10000000U})rx(page);
    const std::filesystem::path destination(argv[2]),staged=destination.string()+".m4-stage-"+std::to_string(GetCurrentProcessId());auto cleanup=own_new_stage(staged);std::ofstream out(staged,std::ios::binary|std::ios::trunc);write_record(out,output_header(static_cast<std::uint32_t>(rows.size()),32));
    for(const auto &q:rows){if(!q.arg_b||!q.arg_a){auto seeded=initial_memory(q);for(unsigned i=0;i<3;++i)std::memcpy(reinterpret_cast<void *>(i==0?stack_base:(i==1?global_base:second_global_base)),seeded.data()+i*page_size,page_size);m4_input=q.state;std::memcpy(m4_guest_fx,q.fx.data(),512);}else{m4_input=m4_after;m4_input.registers[4]=q.state.registers[4];m4_input.eip=q.state.eip;std::memcpy(m4_guest_fx,m4_fx_after,512);}
        Result r{};copy_memory(r.memory_before);m4_before={};m4_after={};r.status=execute();r.host_restored=std::memcmp(m4_host_fx,m4_host_after,5)==0&&std::memcmp(m4_host_fx+24,m4_host_after+24,4)==0&&std::memcmp(m4_host_env,m4_host_env_after,28)==0;
        for(unsigned i=0;i<8;++i)r.host_restored&=std::memcmp(m4_host_fx+32+i*16,m4_host_after+32+i*16,10)==0;r.host_restored&=std::memcmp(m4_host_fx+160,m4_host_after+160,128)==0;require(!r.status&&r.host_restored,"Actual original integer execution/FP restoration failed");
        r.cpu_before=m4_before;r.cpu_after=m4_after;std::memcpy(r.fx_before.data(),m4_fx_before,512);std::memcpy(r.fx_after.data(),m4_fx_after,512);std::memcpy(r.env_before.data(),m4_env_before,28);std::memcpy(r.env_after.data(),m4_env_after,28);copy_memory(r.memory_after);write_record(out,r);
    }
    out.close();require(bool(out),"Original integer staged output failed");require(MoveFileExW(staged.c_str(),destination.c_str(),MOVEFILE_WRITE_THROUGH),"Original integer output commit failed");std::cout<<"Executed "<<rows.size()<<" actual original integer initializer records\n";return 0;
}catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}}
