#include "context.hpp"
#include "staging.hpp"
#include <iostream>
#include <algorithm>
using namespace mw34::m4_initializer_chain;
static_assert(sizeof(void *)==8&&sizeof(State)==state_size);
static_assert(__builtin_offsetof(State,st)+6==2486&&__builtin_offsetof(State,x87)==2768);

#include "execution.hpp"
static void layout() {
    std::cout<<"{\"state_size\":3504,\"request_size\":568,\"result_size\":54908,\"phase_size\":27452,\"vec_offset\":"<<__builtin_offsetof(State,vec)<<",\"vec_size\":"<<sizeof(State::vec)<<",\"vec_stride\":64,\"mmx_offset\":"<<__builtin_offsetof(State,mmx)<<",\"mmx_size\":128,\"st_offset\":2486,\"st_stride\":16,\"x87_offset\":2768,\"x87_size\":512,\"sw_offset\":"<<__builtin_offsetof(State,sw)<<",\"aflag_offset\":"<<__builtin_offsetof(State,aflag)<<",\"rflag_offset\":"<<__builtin_offsetof(State,rflag)<<",\"addr_offset\":"<<__builtin_offsetof(State,addr)<<",\"addr_size\":"<<sizeof(State::addr)<<",\"gpr_offsets\":[2216,2248,2264,2232,2312,2328,2280,2296],\"eip_offset\":2472,\"sw_flag_offsets\":[2755,2753,2751,2749,2747,2745,2757,2737,2739,2741,2743],\"mode0\":\"actual-x86-hardware-fx-env; opaque-State-unobserved\",\"mode1\":\"actual-State-bytes; FX-env-serialized-projection\"}\n";
}
static void storage_controls(std::span<const std::uint8_t> code) {
    unsigned checks{};for(unsigned pc:{0U,2U,3U})for(unsigned rc=0;rc<4;++rc)for(unsigned top=0;top<8;++top)for(unsigned ftw:{0U,2U,255U}){
        auto q=probe_request(pc,rc,top,ftw);q.seed=checks*3571;q.state.flags|=(checks&1)?0x400:0;HarnessMemory h(q,code);Context c(h.memory,q.state.registers[4]);c.select(entry);c.freeze(image_hash);Result r{};execute(q,c,r);
        require(!r.status&&r.host_restored&&preserved(r)&&r.fx_before==r.fx_after&&r.env_before==r.env_after,"Native full noninteger State storage preservation failed");++checks;
    }std::cout<<"State storage controls: "<<checks<<"\n";
}
static void context_controls(std::span<const std::uint8_t> code) {
    unsigned checks{};auto q=probe_request();
    auto reject=[&](auto f){try{f();}catch(const std::exception &){++checks;return;}throw std::runtime_error("Context rejected-control admitted");};
    {HarnessMemory h(q,code);Context c(h.memory,q.state.registers[4]);State s;initialize(s,q);reject([&]{c.enter(s,entry);});reject([&]{c.freeze(image_hash);});reject([&]{c.select(0x40daf0);});c.select(entry);reject([&]{c.select(entry);});reject([&]{c.freeze("wrong");});c.freeze(image_hash);reject([&]{c.freeze(image_hash);});reject([&]{c.select(preceding_entry);});reject([&]{c.enter(s,entry+1);});}
    for(auto address:std::array<std::uint32_t,4>{global_first-1,global_first+20,0xfffffffe,code_page}){HarnessMemory h(q,code);Context c(h.memory,q.state.registers[4]);const auto before=initial_memory(q);c.write8(address,1);std::array<std::uint8_t,memory_size> after;c.capture(after);require(c.failed&&before==after,"Inactive/wrapping write was not atomic");++checks;}
    {HarnessMemory h(q,code);Context c(h.memory,q.state.registers[4]);c.select(entry);c.freeze(image_hash);c.memory.protect({stack_base},mw34::Permissions::read);Result r{};execute(q,c,r);require(r.status==1&&r.host_restored&&r.memory_before==r.memory_after,"Denied first push changed memory or host FP");++checks;}
    {HarnessMemory h(q,code);Context c(h.memory,q.state.registers[4]);c.select(entry);c.freeze(image_hash);Result r{};execute(q,c,r);require(!r.status&&r.host_restored&&r.route_count==2&&r.routes[0].complete&&r.routes[1].complete,"Actual compiled callees/return routing failed");++checks;State s;initialize(s,q);reject([&]{c.enter(s,entry);});}
    {HarnessMemory h(q,code);Context c(h.memory,q.state.registers[4]);State s;initialize(s,q);const auto before=initial_memory(q);c.callee(s,0x40daf0);std::array<std::uint8_t,memory_size> after;c.capture(after);require(c.failed&&before==after,"Inactive direct-call hook admitted");++checks;}
    {HarnessMemory h(q,code);h.memory.protect({code_page},mw34::Permissions::read|mw34::Permissions::write);h.memory.store<std::uint8_t>({entry},0);reject([&]{Context c(h.memory,q.state.registers[4]);});}
    {HarnessMemory h(q,code);reject([&]{Context c(h.memory,stack_base+27);});}
    {HarnessMemory h(q,code);Context c(h.memory,q.state.registers[4],stack_base,stack_base+4096,sentinel+4);c.select(entry);c.freeze(image_hash);Result r{};execute(q,c,r);require(r.status==1&&r.host_restored&&r.route_count==2&&r.routes[0].complete&&r.routes[1].complete,"Actual final RET ignored declared return target");++checks;}
    std::cout<<"Context controls: "<<checks<<"\n";
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
int main(int argc,char **argv){
  try{
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    if(argc==2&&std::string(argv[1])=="--layout"){layout();return 0;}
    if(argc==2&&std::string(argv[1])=="--check-protocol"){std::cout<<"Protocol controls: "<<protocol_controls()<<"\n";return 0;}
    if(argc==4&&std::string(argv[1])=="--stage-collision-control"){stage_collision_control(argv[2],argv[3]);return 0;}
    if(argc==4){const auto code=admit_code(argv[2],argv[3]);const std::string mode(argv[1]);if(mode=="--check-context")context_controls(code);else if(mode=="--check-state-storage")storage_controls(code);else if(mode=="--check-fp-environment")environment_controls(code);else throw std::runtime_error("Unknown M4 native control");return 0;}
    require(argc==5,"M4 native: input output code image");admit_output(argv[2]);const auto code=admit_code(argv[3],argv[4]);std::ifstream input(argv[1],std::ios::binary);const auto rows=read_requests(input);
    const std::filesystem::path destination(argv[2]),staged=destination.string()+".m4-stage-"+std::to_string(GetCurrentProcessId());
    auto cleanup=own_new_stage(staged);
    std::ofstream out(staged,std::ios::binary|std::ios::trunc);write_record(out,output_header(static_cast<std::uint32_t>(rows.size()),64));
    for(const auto &q:rows){
        HarnessMemory harness(q,code);State s;initialize(s,q);ChainResult chain{};chain.phase_count=q.arg_a?2U:1U;
        for(unsigned phase=0;phase<chain.phase_count;++phase){
            if(phase){s.gpr.rsp.dword=q.state.registers[4];s.gpr.rip.dword=entry;}
            Context c(harness.memory,q.state.registers[4]);c.select(s.gpr.rip.dword);c.freeze(image_hash);auto &r=chain.phases[phase];execute_state(s,c,r);
            require(!r.status&&r.host_restored,"Native execution/context/host restoration failed");
        }
        write_record(out,chain);
    }
    out.close();require(bool(out),"Native staged output failed");require(MoveFileExW(staged.c_str(),destination.c_str(),MOVEFILE_WRITE_THROUGH),"Native output commit failed");
    std::cout<<"Executed "<<rows.size()<<" selected static native M4 records; actual State provenance\n";return 0;
  }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
