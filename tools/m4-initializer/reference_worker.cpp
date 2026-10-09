#include "protocol.hpp"
#include "original_broker.hpp"
#include "staging.hpp"
#include <iostream>
using namespace mw34::m4_initializer;
static_assert(sizeof(void *)==4);
extern "C" {
Cpu m4_input{},m4_before{},m4_after{};
std::uint32_t m4_host_esp{};
alignas(16) std::uint8_t m4_guest_fx[512]{},m4_host_fx[512]{},m4_host_after[512]{};
alignas(16) std::uint8_t m4_fx_before[512]{},m4_fx_after[512]{};
std::uint8_t m4_env_before[28]{},m4_env_after[28]{};
std::uint8_t m4_host_env[28]{},m4_host_env_after[28]{};
void m4_enter();void m4_capture();void m4_restore_fp();
}
static std::uint32_t execute() {
    __try { m4_enter();return 0; }
    __except(EXCEPTION_EXECUTE_HANDLER) {m4_restore_fp();return 1;}
}
struct Map {
    void *reservation{},*mapping{};
    Map(std::uint32_t address) {
        const auto base=address&~0xffffU;
        reservation=mw34::original_broker::reserve_or_adopt(address);
        if(reservation!=reinterpret_cast<void *>(base)){
            const auto error=GetLastError();if(reservation)VirtualFree(reservation,0,MEM_RELEASE);reservation=nullptr;
            throw std::runtime_error("Original guarded address reservation failed: base="+std::to_string(base)+" page="+std::to_string(address)+" Win32="+std::to_string(error));
        }
        mapping=VirtualAlloc(reinterpret_cast<void *>(address),page_size,MEM_COMMIT,PAGE_READWRITE);
        if(mapping!=reinterpret_cast<void *>(address)){VirtualFree(reservation,0,MEM_RELEASE);reservation=nullptr;throw std::runtime_error("Original page commit failed");}
    }
    ~Map(){if(reservation)VirtualFree(reservation,0,MEM_RELEASE);}
    Map(const Map &)=delete;
    void rx() {
        DWORD previous{};
        require(VirtualProtect(mapping,page_size,PAGE_EXECUTE_READ,&previous)&&FlushInstructionCache(GetCurrentProcess(),mapping,page_size),"Original RX mapping failed");
    }
};
static void print_protocol_controls() {
    std::cout<<"Protocol controls: "<<protocol_controls()<<"\n";
}
int main(int argc,char **argv) {
    try {
        SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
        if(auto broker=mw34::original_broker::dispatch(argc,argv,5))return *broker;
        if(argc==2&&std::string(argv[1])=="--check-protocol"){print_protocol_controls();return 0;}
        if(argc==4&&std::string(argv[1])=="--stage-collision-control"){stage_collision_control(argv[2],argv[3]);return 0;}
        require(argc==5,"M4 reference: input output code image");
        // Reserve reviewed fixed guest ranges before large image/corpus heap
        // allocations can claim them. Admission still precedes RX/body/output.
        Map executable(code_page),stack(stack_base),globals(global_base),capture(0x10000000);
        admit_output(argv[2]);
        const auto code=admit_code(argv[3],argv[4]);std::ifstream input(argv[1],std::ios::binary);
        const auto matrix=read_requests(input); // Every record admitted before entry/output.
        std::memcpy(static_cast<std::uint8_t *>(executable.mapping)+(entry-code_page),code.data(),code.size());
        auto *stub=static_cast<std::uint8_t *>(capture.mapping)+(sentinel-0x10000000);stub[0]=0xe9;
        const auto delta=static_cast<std::uint32_t>(reinterpret_cast<std::uintptr_t>(&m4_capture)-(sentinel+5));std::memcpy(stub+1,&delta,4);
        executable.rx();capture.rx();
        const std::filesystem::path destination(argv[2]),staged=destination.string()+".m4-stage-"+std::to_string(GetCurrentProcessId());
        auto staging=own_new_stage(staged);
        std::ofstream out(staged,std::ios::binary|std::ios::trunc);write_record(out,output_header(static_cast<std::uint32_t>(matrix.size()),32));
        for(const auto &q:matrix) {
            Result r{};r.memory_before=initial_memory(q);
            std::memcpy(stack.mapping,r.memory_before.data(),page_size);std::memcpy(globals.mapping,r.memory_before.data()+page_size,page_size);
            std::memcpy(r.memory_before.data(),stack.mapping,page_size);std::memcpy(r.memory_before.data()+page_size,globals.mapping,page_size);
            m4_input=q.state;m4_before={};m4_after={};std::memcpy(m4_guest_fx,q.fx.data(),512);
            r.status=execute();r.observation_mode=0;
            r.host_restored=std::memcmp(m4_host_fx,m4_host_after,5)==0&&std::memcmp(m4_host_fx+24,m4_host_after+24,4)==0&&
                std::memcmp(m4_host_env,m4_host_env_after,28)==0;
            for(unsigned i=0;i<8;++i)r.host_restored&=std::memcmp(m4_host_fx+32+i*16,m4_host_after+32+i*16,10)==0;
            r.host_restored&=std::memcmp(m4_host_fx+160,m4_host_after+160,128)==0;
            require(!r.status&&r.host_restored,"Original hardware execution or FP restoration failed");
            r.cpu_before=m4_before;r.cpu_after=m4_after;
            std::memcpy(r.fx_before.data(),m4_fx_before,512);std::memcpy(r.fx_after.data(),m4_fx_after,512);
            std::memcpy(r.env_before.data(),m4_env_before,28);std::memcpy(r.env_after.data(),m4_env_after,28);
            std::memcpy(r.memory_after.data(),stack.mapping,page_size);std::memcpy(r.memory_after.data()+page_size,globals.mapping,page_size);
            // Remill blobs stay zero: original hardware cannot observe that opaque storage.
            write_record(out,r);
        }
        out.close();require(bool(out),"M4 staged output failed");
        require(MoveFileExW(staged.c_str(),destination.c_str(),MOVEFILE_WRITE_THROUGH),"M4 output commit failed");
        std::cout<<"Executed "<<matrix.size()<<" actual original M4 records; hardware FX/env provenance\n";return 0;
    }catch(const std::exception &error){std::cerr<<error.what()<<'\n';return 1;}
}
