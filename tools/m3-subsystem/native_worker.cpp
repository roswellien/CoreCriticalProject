#include "context.hpp"
#include <algorithm>
#include <iostream>
using namespace mw34::m3_subsystem;
static_assert(sizeof(void*)==8&&sizeof(State)==3504);
extern "C" std::uint32_t __remill_read_memory_32(void*t,std::uint32_t a){return static_cast<Context*>(t)->read<4>(a);}
extern "C" std::uint16_t __remill_read_memory_16(void*t,std::uint32_t a){return static_cast<std::uint16_t>(static_cast<Context*>(t)->read<2>(a));}
extern "C" void*__remill_write_memory_32(void*t,std::uint32_t a,std::uint32_t v){static_cast<Context*>(t)->write<4>(a,v);return t;}
extern "C" void*__remill_write_memory_16(void*t,std::uint32_t a,std::uint16_t v){static_cast<Context*>(t)->write<2>(a,v);return t;}
extern "C" void*__remill_function_return(State*s,std::uint32_t pc,void*t){return static_cast<Context*>(t)->returned(*s,pc);}
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
    s.gpr.rax.dword=q.steps[0].state.registers[0];s.gpr.rcx.dword=q.steps[0].state.registers[1];s.gpr.rdx.dword=q.steps[0].state.registers[2];s.gpr.rbx.dword=q.steps[0].state.registers[3];
    s.gpr.rsp.dword=q.steps[0].state.registers[4];s.gpr.rbp.dword=q.steps[0].state.registers[5];s.gpr.rsi.dword=q.steps[0].state.registers[6];s.gpr.rdi.dword=q.steps[0].state.registers[7];s.gpr.rip.dword=q.steps[0].state.eip;
    s.rflag.flat=q.steps[0].state.flags;s.aflag.cf=(q.steps[0].state.flags>>0)&1;s.aflag.pf=(q.steps[0].state.flags>>2)&1;s.aflag.af=(q.steps[0].state.flags>>4)&1;
    s.aflag.zf=(q.steps[0].state.flags>>6)&1;s.aflag.sf=(q.steps[0].state.flags>>7)&1;s.aflag.df=(q.steps[0].state.flags>>10)&1;s.aflag.of=(q.steps[0].state.flags>>11)&1;
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
static void overlay(State&s,const Step&q){
 s.gpr.rax.dword=q.state.registers[0];s.gpr.rcx.dword=q.state.registers[1];s.gpr.rdx.dword=q.state.registers[2];s.gpr.rbx.dword=q.state.registers[3];s.gpr.rsp.dword=q.state.registers[4];s.gpr.rbp.dword=q.state.registers[5];s.gpr.rsi.dword=q.state.registers[6];s.gpr.rdi.dword=q.state.registers[7];s.gpr.rip.dword=q.state.eip;
 s.rflag.flat=q.state.flags;s.aflag.cf=(q.state.flags>>0)&1;s.aflag.pf=(q.state.flags>>2)&1;s.aflag.af=(q.state.flags>>4)&1;s.aflag.zf=(q.state.flags>>6)&1;s.aflag.sf=(q.state.flags>>7)&1;s.aflag.df=(q.state.flags>>10)&1;s.aflag.of=(q.state.flags>>11)&1;
}
static void execute(State&s,Context&ctx,const Step&q,Result&r){
 overlay(s,q);ctx.prepare(q);r.observation_mode=1;ctx.capture(r.memory_before);capture(s,r,true);
 {FpuScope host;ctx.enter(s,q.state.eip);r.status=ctx.failed?1:0;capture(s,r,false);ctx.capture(r.memory_after);r.trace_count=ctx.trace_count;std::copy_n(ctx.events.begin(),r.trace_count,r.events.begin());r.host_restored=host.captured_restoration();}
}
static bool preserved(const Result&r,std::uint32_t pc){
 for(unsigned i=0;i<state_size;++i){const bool allowed=(i>=2216&&i<2220)||(i>=2312&&i<2316)||(i>=2472&&i<2476)||(i>=2264&&i<(pc==setter?2268:2266))||(pc==consumer&&i>=2248&&i<2252)||i==2065||i==2067||i==2069||i==2071||i==2073||i==2077;if(!allowed&&r.state_before[i]!=r.state_after[i])return false;}return true;
}
static void storage_controls(const std::array<std::vector<std::uint8_t>,2>&codes){
 unsigned checks{};for(unsigned pc:{0U,2U,3U})for(unsigned rc=0;rc<4;++rc)for(unsigned top=0;top<8;++top)for(unsigned ftw:{0U,2U,255U}){
  auto q=probe_request();const auto fx=mw34::m3_slice::probe_request(pc,rc,top,ftw);q.fx=fx.fx;q.full_tags=fx.full_tags;q.seed=checks*3571;Context c(q,codes);c.select(&mw34_setter_entry,&mw34_consumer_entry);c.freeze(image_hash);State s;initialize(s,q);
  for(unsigned n=0;n<2;++n){Result r{};execute(s,c,q.steps[n],r);require(!r.status&&r.host_restored&&preserved(r,q.steps[n].state.eip)&&r.fx_before==r.fx_after&&r.env_before==r.env_after,"Persisted full State storage failed");++checks;}
 }std::cout<<"Sequence storage controls: "<<checks<<"\n";
}
static void context_controls(const std::array<std::vector<std::uint8_t>,2>&codes){
 unsigned checks{};auto q=probe_request();auto reject=[&](auto fn){try{fn();}catch(const std::exception&){++checks;return;}throw std::runtime_error("Invalid context control admitted");};
 {Context c(q,codes);State s;initialize(s,q);reject([&]{c.enter(s,setter);});reject([&]{c.freeze(image_hash);});c.select(&mw34_setter_entry,&mw34_consumer_entry);reject([&]{c.select(&mw34_setter_entry,&mw34_consumer_entry);});reject([&]{c.freeze("wrong");});c.freeze(image_hash);reject([&]{c.freeze(image_hash);});reject([&]{c.select(&mw34_setter_entry,&mw34_consumer_entry);});reject([&]{c.enter(s,consumer+1);});}
 for(auto a:std::array<std::uint32_t,4>{buffer_base-1,buffer_base+8191,0xfffffffe,0x55a000}){Context c(q,codes);std::array<std::uint8_t,memory_size>before,after;c.capture(before);c.write<2>(a,1);c.capture(after);require(c.failed&&before==after,"Unadmitted atomic bridge write failed");++checks;}
 {Context c(q,codes);c.select(&mw34_setter_entry,&mw34_consumer_entry);c.freeze(image_hash);State s;initialize(s,q);Result r{};execute(s,c,q.steps[0],r);require(!r.status&&r.trace_count==8&&c.selected_setter==1,"Selected setter path failed");++checks;Result next{};execute(s,c,q.steps[1],next);require(!next.status&&next.trace_count>8&&c.selected_consumer==1,"Selected consumer/logged access path failed");++checks;}
 {Context c(q,codes);c.select(&mw34_setter_entry,&mw34_consumer_entry);c.freeze(image_hash);c.memory.protect({global_base},mw34::Permissions::read);State s;initialize(s,q);Result r{};execute(s,c,q.steps[0],r);require(r.status==1&&r.host_restored&&r.memory_before==r.memory_after,"Contained setter permission fault failed");++checks;reject([&]{c.prepare(q.steps[1]);});}
 {Context c(q,codes);c.select(&mw34_setter_entry,&mw34_consumer_entry);c.freeze(image_hash);State s;initialize(s,q);Result first{};execute(s,c,q.steps[0],first);c.memory.protect({buffer_base},mw34::Permissions::read);Result next{};execute(s,c,q.steps[1],next);require(next.status==1&&next.host_restored&&std::equal(next.memory_before.begin()+8192,next.memory_before.end(),next.memory_after.begin()+8192),"Contained consumer atomic buffer fault failed");++checks;}
 {Context c(q,codes);c.memory.protect({buffer_base},mw34::Permissions::none);reject([&]{c.memory.store<std::uint16_t>({buffer_base},1);});}
 std::cout<<"Sequence context controls: "<<checks<<"\n";
}
static void environment_controls(const std::array<std::vector<std::uint8_t>,2>&codes){
 unsigned checks{};for(unsigned kind=0;kind<2;++kind)for(unsigned pc:{0U,2U,3U})for(unsigned rc=0;rc<4;++rc)for(bool error:{false,true}){
  auto q=probe_request();const auto fx=mw34::m3_slice::probe_request(pc,rc);q.fx=fx.fx;q.full_tags=fx.full_tags;Context c(q,codes);c.select(&mw34_setter_entry,&mw34_consumer_entry);c.freeze(image_hash);State s;initialize(s,q);if(kind){Result setup{};execute(s,c,q.steps[0],setup);require(!setup.status,"Environment consumer setup failed");}if(error)c.memory.protect({kind?buffer_base:global_base},mw34::Permissions::read);
  Result r{};FpuScope outside;auto seed=outside.saved;const std::uint16_t cw=word<std::uint16_t>(q.fx.data()),sw=0x3820,fop=0x123,exp=0x3fff;const std::uint64_t ip=0x123456789abcdef0ULL,dp=0x7fedcba987654321ULL,sig=0xc000000000000001ULL;
  std::memcpy(seed.bytes,&cw,2);std::memcpy(seed.bytes+2,&sw,2);seed.bytes[4]=0x80;std::memcpy(seed.bytes+6,&fop,2);std::memcpy(seed.bytes+8,&ip,8);std::memcpy(seed.bytes+16,&dp,8);std::memcpy(seed.bytes+32,&sig,8);std::memcpy(seed.bytes+40,&exp,2);
  std::uint8_t before[28],after[28];FpuScope::restore(seed);__asm__ volatile("fnstenv %0":"=m"(before)::"memory");require(word<std::uint32_t>(before+12)==static_cast<std::uint32_t>(ip)&&word<std::uint32_t>(before+20)==static_cast<std::uint32_t>(dp)&&word<std::uint16_t>(before+18)==fop,"Actual host metadata seed unobserved");
  execute(s,c,q.steps[kind],r);__asm__ volatile("fnstenv %0":"=m"(after)::"memory");require(r.host_restored&&r.status==unsigned(error)&&!std::memcmp(before,after,28),"Selected normal/error host environment failed");++checks;
 }std::cout<<"Sequence FP environment controls: "<<checks<<"\n";
}
int main(int argc,char**argv){try{
 SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
 if(argc==2&&std::string(argv[1])=="--check-protocol"){std::cout<<"Sequence protocol controls: "<<protocol_controls()<<"\n";return 0;}
 if(argc==2&&std::string(argv[1])=="--layout"){std::cout<<"{\"state_size\":3504,\"request_size\":1296,\"result_size\":73728,\"vec_offset\":16,\"vec_size\":2048,\"mmx_offset\":2608,\"st_offset\":2486,\"st_stride\":16,\"x87_offset\":2768,\"trace_event_size\":16,\"trace_capacity\":2048,\"host_metadata\":\"actual legacy FNSTENV; high64 pointers unobserved\"}\n";return 0;}
 if(argc==5){const auto codes=admit_codes(argv[2],argv[3],argv[4]);const std::string mode(argv[1]);if(mode=="--check-context")context_controls(codes);else if(mode=="--check-state-storage")storage_controls(codes);else if(mode=="--check-fp-environment")environment_controls(codes);else throw std::runtime_error("Unknown subsystem native control");return 0;}
 require(argc==6,"Subsystem native: input output settercode consumercode image");admit_output(argv[2]);const auto codes=admit_codes(argv[3],argv[4],argv[5]);std::ifstream input(argv[1],std::ios::binary);const auto rows=read_requests(input);
 const std::filesystem::path dest(argv[2]),stage=dest.string()+".s3-stage-"+std::to_string(GetCurrentProcessId());require(!std::filesystem::exists(stage),"Staging output exists");struct Cleanup{std::filesystem::path p;~Cleanup(){std::error_code e;std::filesystem::remove(p,e);}}cleanup{stage};std::ofstream out(stage,std::ios::binary|std::ios::trunc);write_record(out,output_header(output_count(rows),64));
 for(unsigned sequence=0;sequence<rows.size();++sequence){const auto&q=rows[sequence];Context c(q,codes);c.select(&mw34_setter_entry,&mw34_consumer_entry);c.freeze(image_hash);State s;initialize(s,q);
  for(unsigned n=0;n<q.step_count;++n){Result r{};r.sequence_index=sequence;r.step_index=n;execute(s,c,q.steps[n],r);require(!r.status&&r.host_restored,"Selected subsystem body/context/host restoration failed");write_record(out,r);}
 }
 out.close();require(bool(out),"Native subsystem staged output failed");require(MoveFileExW(stage.c_str(),dest.c_str(),MOVEFILE_WRITE_THROUGH),"Native subsystem commit failed");std::cout<<"Executed "<<output_count(rows)<<" selected static subsystem entries with actual ordered memory bridges\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
