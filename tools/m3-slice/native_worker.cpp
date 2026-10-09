#include "context.hpp"
#include <iostream>
#include <algorithm>
using namespace mw34::m3_slice;
static_assert(sizeof(void *)==8&&sizeof(State)==state_size);
static_assert(__builtin_offsetof(State,st)+6==2486&&__builtin_offsetof(State,x87)==2768);

extern "C" std::uint32_t __remill_read_memory_32(void *token,std::uint32_t address){return static_cast<Context *>(token)->read32(address);}
extern "C" void *__remill_write_memory_32(void *token,std::uint32_t address,std::uint32_t value){static_cast<Context *>(token)->write32(address,value);return token;}
extern "C" void *__remill_function_return(State *s,std::uint32_t pc,void *token){return static_cast<Context *>(token)->returned(*s,pc);}

struct FpuScope {
    struct alignas(16) Image {std::uint8_t bytes[512];} saved;
    std::uint8_t legacy_env[28];
    FpuScope() {
        __asm__ volatile("fxsave64 %0\n\tfnstenv %1\n\tfninit" : "=m"(saved),"=m"(legacy_env) : : "memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)");
        const std::uint32_t mxcsr=0x1f80;
        __asm__ volatile("ldmxcsr %0" : : "m"(mxcsr) : "memory");
    }
    static void restore(const Image &image) {
        __asm__ volatile("fxrstor64 %0" : : "m"(image) : "memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)",
          "xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");
    }
    void restore_all() {
        __asm__ volatile("fxrstor64 %0\n\tfldenv %1" : : "m"(saved),"m"(legacy_env) : "memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)",
          "xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");
    }
    bool captured_restoration() {
        Image after;std::uint8_t env_after[28];
        __asm__ volatile("fxrstor64 %2\n\tfldenv %3\n\tfxsave64 %0\n\tfnstenv %1" : "=m"(after),"=m"(env_after) : "m"(saved),"m"(legacy_env) : "memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)",
          "xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");
        // Reserved FX bytes and capability mask are not architectural restoration observations.
        if(std::memcmp(saved.bytes,after.bytes,5)||std::memcmp(saved.bytes+24,after.bytes+24,4)||std::memcmp(legacy_env,env_after,28))return false;
        for(unsigned i=0;i<8;++i)if(std::memcmp(saved.bytes+32+i*16,after.bytes+32+i*16,10))return false;
        return std::memcmp(saved.bytes+160,after.bytes+160,256)==0;
    }
    ~FpuScope(){restore_all();}
};
static Cpu cpu(const State &s) {
    Cpu c{{s.gpr.rax.dword,s.gpr.rcx.dword,s.gpr.rdx.dword,s.gpr.rbx.dword,s.gpr.rsp.dword,s.gpr.rbp.dword,s.gpr.rsi.dword,s.gpr.rdi.dword},
      0x202U|(s.aflag.cf<<0)|(s.aflag.pf<<2)|(s.aflag.af<<4)|(s.aflag.zf<<6)|(s.aflag.sf<<7)|(s.aflag.df<<10)|(s.aflag.of<<11),s.gpr.rip.dword};return c;
}
static std::uint16_t status(const State &s){return (s.x87.fxsave.swd.flat&0xb880)|(s.sw.ie<<0)|(s.sw.de<<1)|(s.sw.ze<<2)|(s.sw.oe<<3)|(s.sw.ue<<4)|(s.sw.pe<<5)|(s.sw.sf<<6)|(s.sw.c0<<8)|(s.sw.c1<<9)|(s.sw.c2<<10)|(s.sw.c3<<14);}
static void initialize(State &s,const Request &q) {
    auto *raw=reinterpret_cast<std::uint8_t *>(&s);for(unsigned i=0;i<sizeof(s);++i)raw[i]=static_cast<std::uint8_t>(i*29+q.seed+(i>>8)*7);
    // Segment bases are an explicit flat guest-context dependency.
    std::memset(&s.addr,0,sizeof(s.addr));
    s.gpr.rax.dword=q.state.registers[0];s.gpr.rcx.dword=q.state.registers[1];s.gpr.rdx.dword=q.state.registers[2];s.gpr.rbx.dword=q.state.registers[3];
    s.gpr.rsp.dword=q.state.registers[4];s.gpr.rbp.dword=q.state.registers[5];s.gpr.rsi.dword=q.state.registers[6];s.gpr.rdi.dword=q.state.registers[7];s.gpr.rip.dword=q.state.eip;
    s.rflag.flat=q.state.flags;s.aflag.cf=(q.state.flags>>0)&1;s.aflag.pf=(q.state.flags>>2)&1;s.aflag.af=(q.state.flags>>4)&1;
    s.aflag.zf=(q.state.flags>>6)&1;s.aflag.sf=(q.state.flags>>7)&1;s.aflag.df=(q.state.flags>>10)&1;s.aflag.of=(q.state.flags>>11)&1;
    std::memcpy(&s.x87,q.fx.data(),512);const auto sw=word<std::uint16_t>(q.fx.data()+2);
    s.sw.ie=(sw>>0)&1;s.sw.de=(sw>>1)&1;s.sw.ze=(sw>>2)&1;s.sw.oe=(sw>>3)&1;s.sw.ue=(sw>>4)&1;s.sw.pe=(sw>>5)&1;
    s.sw.sf=(sw>>6)&1;s.sw.c0=(sw>>8)&1;s.sw.c1=(sw>>9)&1;s.sw.c2=(sw>>10)&1;s.sw.c3=(sw>>14)&1;
    for(unsigned i=0;i<8;++i){std::memcpy(&s.st.elems[i].val,q.fx.data()+32+i*16,10);std::memcpy(&s.vec[i],q.fx.data()+160+i*16,16);}
}
static void capture(const State &s,Result &r,bool before) {
    auto &fx=before?r.fx_before:r.fx_after;auto &env=before?r.env_before:r.env_after;auto &raw=before?r.state_before:r.state_after;
    (before?r.cpu_before:r.cpu_after)=cpu(s);std::memcpy(raw.data(),&s,sizeof(s));std::memcpy(fx.data(),&s.x87,512);
    const auto sw=status(s),cw=s.x87.fxsave.cwd.flat;std::memcpy(fx.data()+2,&sw,2);
    unsigned tags{},top=(sw>>11)&7,ftw=s.x87.fxsave.ftw.flat;
    for(unsigned i=0;i<8;++i){
        std::memcpy(fx.data()+32+i*16,&s.st.elems[i].val,10);std::memcpy(fx.data()+160+i*16,&s.vec[i],16);
        const auto physical=(top+i)&7;tags|=((ftw&(1U<<physical))?occupied_tag(fx.data()+32+i*16):3U)<<(physical*2);
    }
    const auto put=[&](unsigned offset,std::uint32_t v){std::memcpy(env.data()+offset,&v,4);};
    put(0,0xffff0000U|cw);put(4,0xffff0000U|sw);put(8,0xffff0000U|tags);
    put(12,s.x87.fxsave.ip);put(16,s.x87.fxsave.cs.flat|(std::uint32_t{s.x87.fxsave.fop}<<16));put(20,s.x87.fxsave.dp);put(24,0xffff0000U|s.x87.fxsave.ds.flat);
}
static void execute(const Request &q,Context &ctx,Result &r) {
    State s;initialize(s,q);r.observation_mode=1;ctx.capture(r.memory_before);capture(s,r,true);
    // Context allocation and every potentially throwing observer run before final restore.
    // The translated body only reports bridge faults; no C++ exception crosses LLVM frames.
    {
        FpuScope host;
        ctx.enter(s,entry);
        r.status=ctx.failed?1U:0U;
        capture(s,r,false);ctx.capture(r.memory_after);
        r.host_restored=host.captured_restoration();
    } // Last operation is FXSAVE64 host restoration; no escaping EH is credited.
}
static bool preserved(const Result &r) {
    for(unsigned i=0;i<state_size;++i){
        const bool changed=(i>=2216&&i<2220)||(i>=2264&&i<2268)||(i>=2312&&i<2316)||(i>=2472&&i<2476)||
            i==2065||i==2067||i==2069||i==2071||i==2073||i==2077;
        if(!changed&&r.state_before[i]!=r.state_after[i])return false;
    }return true;
}
static void layout() {
    std::cout<<"{\"state_size\":3504,\"request_size\":568,\"result_size\":24564,\"vec_offset\":"<<__builtin_offsetof(State,vec)<<",\"vec_size\":"<<sizeof(State::vec)<<",\"vec_stride\":64,\"mmx_offset\":"<<__builtin_offsetof(State,mmx)<<",\"mmx_size\":128,\"st_offset\":2486,\"st_stride\":16,\"x87_offset\":2768,\"x87_size\":512,\"sw_offset\":"<<__builtin_offsetof(State,sw)<<",\"aflag_offset\":"<<__builtin_offsetof(State,aflag)<<",\"rflag_offset\":"<<__builtin_offsetof(State,rflag)<<",\"addr_offset\":"<<__builtin_offsetof(State,addr)<<",\"addr_size\":"<<sizeof(State::addr)<<",\"gpr_offsets\":[2216,2248,2264,2232,2312,2328,2280,2296],\"eip_offset\":2472,\"sw_flag_offsets\":[2755,2753,2751,2749,2747,2745,2757,2737,2739,2741,2743],\"mode0\":\"actual-x86-hardware-fx-env; opaque-State-unobserved\",\"mode1\":\"actual-State-bytes; FX-env-serialized-projection\"}\n";
}
static void storage_controls(std::span<const std::uint8_t> code) {
    unsigned checks{};for(unsigned pc:{0U,2U,3U})for(unsigned rc=0;rc<4;++rc)for(unsigned top=0;top<8;++top)for(unsigned ftw:{0U,2U,255U}){
        auto q=probe_request(pc,rc,top,ftw);q.seed=checks*3571;q.state.flags|=(checks&1)?0x400:0;Context c(q,code);c.select(&mw34_lifted_entry);c.freeze(image_hash);Result r{};execute(q,c,r);
        require(!r.status&&r.host_restored&&preserved(r)&&r.fx_before==r.fx_after&&r.env_before==r.env_after,"Native full noninteger State storage preservation failed");++checks;
    }std::cout<<"State storage controls: "<<checks<<"\n";
}
static void context_controls(std::span<const std::uint8_t> code) {
    unsigned checks{};auto q=probe_request();auto reject=[&](auto f){try{f();}catch(const std::exception &){++checks;return;}throw std::runtime_error("Context rejected-control admitted");};
    {Context c(q,code);State s;initialize(s,q);reject([&]{c.enter(s,entry);});}
    {Context c(q,code);reject([&]{c.freeze(image_hash);});c.select(&mw34_lifted_entry);reject([&]{c.select(&mw34_lifted_entry);});reject([&]{c.freeze("wrong");});c.freeze(image_hash);reject([&]{c.freeze(image_hash);});reject([&]{c.select(&mw34_lifted_entry);});State s;initialize(s,q);reject([&]{c.enter(s,entry+1);});}
    for(auto address:std::array<std::uint32_t,4>{global_first-1,global_first+20,0xfffffffe,code_page}){Context c(q,code);const auto before=initial_memory(q);c.write32(address,1);std::array<std::uint8_t,memory_size> after;c.capture(after);require(c.failed&&before==after,"Inactive/wrapping write was not atomic");++checks;}
    {Context c(q,code);c.select(&mw34_lifted_entry);c.freeze(image_hash);c.memory.protect({global_base},mw34::Permissions::read);Result r{};execute(q,c,r);require(r.status==1&&r.host_restored&&r.memory_before==r.memory_after,"Error-status path/atomic writes/host restore failed");++checks;}
    {Context c(q,code);c.select(&mw34_lifted_entry);c.freeze(image_hash);Result r{};execute(q,c,r);require(!r.status&&r.host_restored,"Selected compiled body failed");++checks;State s;initialize(s,q);reject([&]{c.enter(s,entry);});}
    {Context c(q,code);c.memory.protect({global_base},mw34::Permissions::read|mw34::Permissions::execute);c.select(&mw34_lifted_entry);c.freeze(image_hash);Result r{};execute(q,c,r);require(r.status==1&&r.host_restored,"RX permission fault not mandatory");++checks;}
    {Context c(q,code);c.memory.protect({global_base},mw34::Permissions::none);reject([&]{c.memory.store<std::uint32_t>({global_first},1);});}
    std::cout<<"Context controls: "<<checks<<"\n";
}
static void environment_controls(std::span<const std::uint8_t> code) {
    unsigned checks{};for(unsigned pc:{0U,2U,3U})for(unsigned rc=0;rc<4;++rc)for(bool error:{false,true}){
        auto q=probe_request(pc,rc);Context c(q,code);c.select(&mw34_lifted_entry);c.freeze(image_hash);if(error)c.memory.protect({global_base},mw34::Permissions::read);Result r{};
        FpuScope outside;auto seed=outside.saved;const std::uint16_t cw=0x37f,sw=0x3820;std::memcpy(seed.bytes,&cw,2);std::memcpy(seed.bytes+2,&sw,2);seed.bytes[4]=0x80;
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
    if(argc==4){const auto code=admit_code(argv[2],argv[3]);const std::string mode(argv[1]);if(mode=="--check-context")context_controls(code);else if(mode=="--check-state-storage")storage_controls(code);else if(mode=="--check-fp-environment")environment_controls(code);else throw std::runtime_error("Unknown M3 native control");return 0;}
    require(argc==5,"M3 native: input output code image");admit_output(argv[2]);const auto code=admit_code(argv[3],argv[4]);std::ifstream input(argv[1],std::ios::binary);const auto rows=read_requests(input);
    const std::filesystem::path destination(argv[2]),staged=destination.string()+".m3-stage-"+std::to_string(GetCurrentProcessId());
    require(!std::filesystem::exists(staged),"Output staging file already exists");struct Cleanup{std::filesystem::path p;~Cleanup(){std::error_code e;std::filesystem::remove(p,e);}}cleanup{staged};
    std::ofstream out(staged,std::ios::binary|std::ios::trunc);write_record(out,output_header(static_cast<std::uint32_t>(rows.size()),64));
    for(const auto &q:rows){Context c(q,code);c.select(&mw34_lifted_entry);c.freeze(image_hash);Result r{};execute(q,c,r);require(!r.status&&r.host_restored,"Native execution/context/host restoration failed");write_record(out,r);}
    out.close();require(bool(out),"Native staged output failed");require(MoveFileExW(staged.c_str(),destination.c_str(),MOVEFILE_WRITE_THROUGH),"Native output commit failed");
    std::cout<<"Executed "<<rows.size()<<" selected static native M3 records; actual State provenance\n";return 0;
  }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
