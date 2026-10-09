#include "execution.hpp"
#include "staging.hpp"
#include <iostream>
#include <memory>
using namespace mw34::m4_integer_startup;
static_assert(sizeof(void *)==8&&sizeof(State)==3504);
static void storage_controls(std::span<const std::uint8_t> code){unsigned count{};for(unsigned root=0;root<14;++root)for(unsigned pc:{0U,2U,3U})for(unsigned rc=0;rc<4;++rc)for(unsigned top=0;top<8;++top)for(unsigned ftw:{0U,2U,255U}){auto q=probe_request(pc,rc,top,ftw);q.arg_a=root;q.state.eip=entries[root];q.seed=count*3571;HarnessMemory h(q,code);Context c(h.memory,q.state.registers[4]);c.select(q.state.eip);c.freeze(image_hash);Result r{};execute(q,c,r);require(!r.status&&r.host_restored&&r.fx_before==r.fx_after&&r.env_before==r.env_after,"Batch integer FP storage changed");++count;}std::cout<<"State storage controls: "<<count<<'\n';}
static void context_controls(std::span<const std::uint8_t> code){unsigned count{};
    for(unsigned root=0;root<14;++root){auto q=probe_request();q.arg_a=root;q.state.eip=entries[root];HarnessMemory h(q,code);Context c(h.memory,q.state.registers[4]);c.select(q.state.eip);c.freeze(image_hash);Result r{};execute(q,c,r);require(!r.status&&r.host_restored&&r.route_count==(root<8?1U:0U),"Actual compiled tail/RET failed");++count;
        HarnessMemory f(q,code);Context bad(f.memory,q.state.registers[4],stack_base,stack_base+4096,sentinel+4);bad.select(q.state.eip);bad.freeze(image_hash);Result rejected{};execute(q,bad,rejected);require(rejected.status==1&&rejected.host_restored&&!bad.complete,"Actual compiled RET ignored declared target");++count;
    }
    {auto q=probe_request();HarnessMemory h(q,code);Context c(h.memory,q.state.registers[4]);State s;initialize(s,q);const auto before=initial_memory(q);c.tail(s,0x43ae30);std::array<std::uint8_t,memory_size> after;c.capture(after);require(c.failed&&before==after,"Inactive tail observer changed memory");++count;}
    {auto q=probe_request();HarnessMemory h(q,code);Context c(h.memory,q.state.registers[4]);c.select(entry);c.freeze(image_hash);h.memory.protect({global_base},mw34::Permissions::read);Result r{};execute(q,c,r);require(r.status==1&&r.host_restored&&r.memory_before==r.memory_after,"Denied actual first store mutated memory or host FP");++count;}
    std::cout<<"Context controls: "<<count<<'\n';
}
static void environment_controls(std::span<const std::uint8_t> code) {
    unsigned checks{};for(unsigned pc:{0U,2U,3U})for(unsigned rc=0;rc<4;++rc)for(bool error:{false,true}){
        auto q=probe_request(pc,rc);HarnessMemory h(q,code);Context c(h.memory,q.state.registers[4]);c.select(entry);c.freeze(image_hash);if(error)c.memory.protect({global_base},mw34::Permissions::read);Result r{};
        FpuScope outside;auto seed=outside.saved;const std::uint16_t cw=static_cast<std::uint16_t>(0x7f|(pc<<8)|(rc<<10)),sw=0x3820;std::memcpy(seed.bytes,&cw,2);std::memcpy(seed.bytes+2,&sw,2);seed.bytes[4]=0x80;
        const std::uint64_t sig=0xc000000000000001ULL,ip=0x123456789abcdef0ULL,dp=0x7fedcba987654321ULL;const std::uint16_t exp=0x3fff;
        std::memcpy(seed.bytes+32,&sig,8);std::memcpy(seed.bytes+40,&exp,2);std::memcpy(seed.bytes+8,&ip,8);std::memcpy(seed.bytes+16,&dp,8);
        const std::uint16_t fop=0x123;std::memcpy(seed.bytes+6,&fop,2);
        std::uint8_t env_before[28],env_after[28];
        FpuScope::restore(seed);__asm__ volatile("fnstenv %0":"=m"(env_before)::"memory");
        require(word<std::uint32_t>(env_before+12)==static_cast<std::uint32_t>(ip)&&word<std::uint32_t>(env_before+20)==static_cast<std::uint32_t>(dp)&&word<std::uint16_t>(env_before+18)==fop,"Seeded host legacy pointer/opcode metadata was not observed");
        execute(q,c,r);__asm__ volatile("fnstenv %0":"=m"(env_after)::"memory");
        require(r.host_restored&&r.status==unsigned(error)&&std::memcmp(env_before,env_after,28)==0,"Normal/error selected body FP environment restoration failed");++checks;
    }std::cout<<"FP environment controls: "<<checks<<"\n";
}
int main(int argc,char **argv){try{
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    if(argc==2&&std::string(argv[1])=="--layout"){std::cout<<"{\"state_size\":3504,\"result_size\":"<<sizeof(Result)<<",\"memory_before\":"<<offsetof(Result,memory_before)<<",\"memory_after\":"<<offsetof(Result,memory_after)<<",\"State_before\":"<<offsetof(Result,state_before)<<",\"State_after\":"<<offsetof(Result,state_after)<<"}\n";return 0;}
    if(argc==2&&std::string(argv[1])=="--check-protocol"){std::cout<<"Protocol controls: "<<protocol_controls()<<'\n';return 0;}
    if(argc==4&&std::string(argv[1])=="--stage-collision-control"){stage_collision_control(argv[2],argv[3]);return 0;}
    if(argc==4){const auto code=admit_code(argv[2],argv[3]);const std::string mode(argv[1]);if(mode=="--check-context")context_controls(code);else if(mode=="--check-state-storage")storage_controls(code);else if(mode=="--check-fp-environment")environment_controls(code);else throw std::runtime_error("Unknown integer native control");return 0;}
    require(argc==5,"Integer native: input output code image");admit_output(argv[2]);const auto code=admit_code(argv[3],argv[4]);std::ifstream input(argv[1],std::ios::binary);const auto rows=read_requests(input);
    const std::filesystem::path destination(argv[2]),staged=destination.string()+".m4-stage-"+std::to_string(GetCurrentProcessId());auto cleanup=own_new_stage(staged);std::ofstream out(staged,std::ios::binary|std::ios::trunc);write_record(out,output_header(static_cast<std::uint32_t>(rows.size()),64));
    std::unique_ptr<HarnessMemory> harness;State s;
    for(const auto &q:rows){if(!q.arg_b||!q.arg_a){harness=std::make_unique<HarnessMemory>(q,code);initialize(s,q);}else{s.gpr.rsp.dword=q.state.registers[4];s.gpr.rip.dword=q.state.eip;}
        Context c(harness->memory,q.state.registers[4]);c.select(q.state.eip);c.freeze(image_hash);Result r{};execute_state(s,c,r);require(!r.status&&r.host_restored,"Static integer body/context/host restoration failed");write_record(out,r);
    }
    out.close();require(bool(out),"Integer staged output failed");require(MoveFileExW(staged.c_str(),destination.c_str(),MOVEFILE_WRITE_THROUGH),"Integer output commit failed");std::cout<<"Executed "<<rows.size()<<" actual statically compiled integer initializer records\n";return 0;
}catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}}
