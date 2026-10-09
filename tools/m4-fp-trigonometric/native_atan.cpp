// Actual statically compiled 4133C0 experiment. Guest bytes are data only here.
// State serialization is a software projection, separately labelled from the
// original worker's actual hardware FXSAVE and legacy FNSTENV observations.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <bcrypt.h>
#include "probe_spec.hpp"
#include "memory/guest_memory.hpp"
#include <remill/Arch/X86/Runtime/State.h>
#include <array>
#include <bit>
#include <csetjmp>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <thread>
extern "C" void *mw34_fp_entry_4b7020(State *,std::uint32_t,void *);
#include "atan_corpus.hpp"
#include "atan_publication.hpp"
namespace mw34::m4_fp_atan {
constexpr std::uint32_t entry=0x4b7020,frame=0x20001800,sentinel=0x10000100;
static unsigned input_address(){return 0x5c9398;}
static unsigned output_address(){return 0x60b2b0;}
static unsigned event_extent(){return 7;}
static unsigned exception_tests(){return 5;}
constexpr char image_sha[]="95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf";
constexpr unsigned memory_size=9*4096;
static void require(bool ok,const char *why){if(!ok)throw std::runtime_error(why);}
template<class T> static T word(const void *p){T value;std::memcpy(&value,p,sizeof(value));return value;}
static std::vector<std::uint8_t> read(const char *path,std::size_t maximum){
    std::ifstream f(path,std::ios::binary|std::ios::ate);require(bool(f),"Input unavailable");
    const auto size=f.tellg();require(size>=0&&static_cast<std::uint64_t>(size)<=maximum,"Input extent rejected");
    std::vector<std::uint8_t> bytes(static_cast<std::size_t>(size));f.seekg(0);f.read(reinterpret_cast<char *>(bytes.data()),bytes.size());
    require(bool(f),"Input read failed");return bytes;
}
static std::string sha256(std::span<const std::uint8_t> bytes){
    BCRYPT_ALG_HANDLE algorithm{};BCRYPT_HASH_HANDLE hash{};
    require(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)==0,"SHA provider failed");
    struct Close {BCRYPT_ALG_HANDLE a;BCRYPT_HASH_HANDLE &h;~Close(){if(h)BCryptDestroyHash(h);BCryptCloseAlgorithmProvider(a,0);}} close{algorithm,hash};
    require(BCryptCreateHash(algorithm,&hash,nullptr,0,nullptr,0,0)==0,"SHA object failed");
    require(bytes.size()<=0xffffffffULL&&BCryptHashData(hash,const_cast<PUCHAR>(bytes.data()),static_cast<ULONG>(bytes.size()),0)==0,"SHA update failed");
    std::array<std::uint8_t,32> digest{};require(BCryptFinishHash(hash,digest.data(),digest.size(),0)==0,"SHA final failed");
    std::ostringstream out;out<<std::hex<<std::setfill('0');for(auto byte:digest)out<<std::setw(2)<<unsigned(byte);return out.str();
}
static std::vector<std::uint8_t> admit(const char *pack_path,const char *image_path){
    const auto image=read(image_path,2384384);require(image.size()==2384384&&sha256(image)==image_sha,"Exact image identity required");
    auto pack=read(pack_path,61572);require(pack.size()==61572&&sha256(pack)==m4_fp::pack_sha,"Exact reviewed pack required");
    require(std::memcmp(pack.data(),"MW4FPK01",8)==0&&word<std::uint32_t>(pack.data()+8)==15,"Pack header rejected");
    for(unsigned i=0;i<15;++i){const auto p=pack.data()+12+i*4104;
        require(word<std::uint32_t>(p)==m4_fp::page_bases[i]&&word<std::uint32_t>(p+4)==m4_fp::page_permissions[i],"Pack page metadata rejected");}
    return pack;
}
struct Harness {
    GuestMemory memory;
    explicit Harness(std::span<const std::uint8_t> pack){
        for(unsigned i=0;i<15;++i){const auto base=m4_fp::page_bases[i];memory.map({base},4096,Permissions::read|Permissions::write);
            memory.write({base},std::as_bytes(pack.subspan(12+i*4104+8,4096)));
            memory.protect({base},m4_fp::page_permissions[i]==1?Permissions::read|Permissions::execute:
                m4_fp::page_permissions[i]==0?Permissions::read:Permissions::read|Permissions::write);}
        memory.store<std::uint32_t>({frame},sentinel);
    }
    void capture(std::array<std::uint8_t,memory_size> &bytes)const{
        for(unsigned i=6;i<15;++i)memory.read({m4_fp::page_bases[i]},std::as_writable_bytes(std::span{bytes.data()+(i-6)*4096,4096}));
    }
};
#pragma pack(push,1)
struct Cpu {std::array<std::uint32_t,8> gpr;std::uint32_t flags,pc;};
struct Event {std::uint32_t address;std::uint64_t value;std::uint32_t width,operation;};
struct Result {
    std::uint32_t repeat,pc,cw,top,status;
    Cpu before,after;
    std::array<std::uint8_t,3504> state_before,state_after;
    std::array<std::uint8_t,512> fx_before,fx_after;
    std::array<std::uint8_t,28> env_before,env_after;
    std::array<std::uint8_t,512> host_before,host_after;
    std::array<std::uint8_t,28> host_env_before,host_env_after;
    std::array<std::uint8_t,memory_size> memory_before,memory_after;
    std::uint32_t event_count,reads,writes,clears,tests,returns,host_restored,primitives;
    std::array<Event,7> events;
};
#pragma pack(pop)
static_assert(sizeof(void *)==8&&sizeof(State)==3504&&sizeof(Cpu)==40&&sizeof(Result)==83168);
class Context;
static thread_local Context *active_context{};
class Context {
    bool active{},used{},escape_ready{};std::thread::id owner;std::jmp_buf escape;
    void fault(){failed=true;if(active&&escape_ready&&owner==std::this_thread::get_id())std::longjmp(escape,1);}
    bool admitted(){if(!active||failed||owner!=std::this_thread::get_id()){fault();return false;}return true;}
    bool access(std::uint32_t address,unsigned width,unsigned operation){
        if(!admitted())return false;
        const std::array<Event,7> sequence{{{0x5c9398,0,8,0},{0x5c93a0,0,8,0},{0x60b2b0,0,4,1},
          {0x5c9398,0,8,0},{0x5c93a0,0,8,0},{0x60b2ec,0,4,1},{frame,0,4,0}}};
        if(event_count>=event_extent()){fault();return false;}const auto &e=sequence[event_count];
        if(address!=e.address||width!=e.width||operation!=e.operation){fault();return false;}return true;
    }
    void log(std::uint32_t address,std::uint64_t value,unsigned width,unsigned operation){events[event_count++]={address,value,width,operation};}
public:
    GuestMemory &memory;bool failed{},complete{};
    std::uint32_t event_count{},reads{},writes{},clears{},tests{},returns{},primitives{};std::array<Event,7> events{};
    explicit Context(GuestMemory &m):memory(m){}
    void enter(State &s){
        require(!active&&!used&&!failed&&!active_context&&s.gpr.rip.dword==entry&&s.gpr.rsp.dword==frame,"Context entry rejected");
        used=true;active=true;escape_ready=true;owner=std::this_thread::get_id();active_context=this;void *token=this;
        if(setjmp(escape)==0)token=mw34_fp_entry_4b7020(&s,entry,this);
        active_context=nullptr;escape_ready=false;active=false;
        if(token!=this||failed||!complete||event_count!=event_extent()||reads!=5||writes!=2||clears!=5||tests!=5||returns!=1||primitives!=2)failed=true;
    }
    std::uint32_t read32(std::uint32_t address){
        if(!access(address,4,0))return 0;std::uint32_t value{};bool ok{};
        try{value=memory.load<std::uint32_t>({address});ok=true;}catch(const std::exception &){}
        // The catch is complete before the bounded escape; no exception or
        // nontrivial automatic object crosses a statically lifted frame.
        if(!ok){fault();return 0;}++reads;log(address,value,4,0);return value;
    }
    std::uint64_t read64(std::uint32_t address){
        if(!access(address,8,0))return 0;std::uint64_t value{};bool ok{};
        try{value=memory.load<std::uint64_t>({address});ok=true;}catch(const std::exception &){}
        if(!ok){fault();return 0;}++reads;log(address,value,8,0);return value;
    }
    void primitive(unsigned operation){if(!admitted())return;if(operation!=primitives||primitives>=2||clears!=1+primitives||tests!=(operation==0?0:1)||event_count!=2){fault();return;}++primitives;}
    void write32(std::uint32_t address,std::uint32_t value){
        if(!access(address,4,1))return;bool ok{};try{memory.store<std::uint32_t>({address},value);ok=true;}catch(const std::exception &){}
        if(!ok){fault();return;}++writes;log(address,value,4,1);
    }
    void clear(unsigned mask){if(!admitted())return;if(mask!=127||clears!=tests||clears>=exception_tests()){fault();return;}++clears;__asm__ volatile("fnclex":::"memory");}
    unsigned test(unsigned mask){if(!admitted())return 0;if(mask!=127||clears!=tests+1||tests>=exception_tests()){fault();return 0;}++tests;
        std::uint16_t sw;__asm__ volatile("fnstsw %0":"=m"(sw)::"memory");return sw&mask;
    }
    void *returned(State &s,std::uint32_t pc){
        if(!admitted())return this;if(complete||event_count!=event_extent()||pc!=sentinel||s.gpr.rip.dword!=pc||s.gpr.rsp.dword!=frame+4){fault();return this;}
        complete=true;++returns;return this;
    }
};
static Cpu cpu(const State &s){return {{s.gpr.rax.dword,s.gpr.rcx.dword,s.gpr.rdx.dword,s.gpr.rbx.dword,s.gpr.rsp.dword,s.gpr.rbp.dword,s.gpr.rsi.dword,s.gpr.rdi.dword},
    0x202U|(s.aflag.cf<<0)|(s.aflag.pf<<2)|(s.aflag.af<<4)|(s.aflag.zf<<6)|(s.aflag.sf<<7)|(s.aflag.df<<10)|(s.aflag.of<<11),s.gpr.rip.dword};}
static std::uint16_t status(const State &s){return (s.x87.fxsave.swd.flat&0xb880)|(s.sw.ie<<0)|(s.sw.de<<1)|(s.sw.ze<<2)|(s.sw.oe<<3)|(s.sw.ue<<4)|(s.sw.pe<<5)|(s.sw.sf<<6)|(s.sw.c0<<8)|(s.sw.c1<<9)|(s.sw.c2<<10)|(s.sw.c3<<14);}
static void initialize(State &s,unsigned cw,unsigned top,unsigned seed){
    auto *raw=reinterpret_cast<std::uint8_t *>(&s);for(unsigned i=0;i<sizeof(s);++i)raw[i]=static_cast<std::uint8_t>(i*29+seed+(i>>8)*7);
    std::memset(&s.addr,0,sizeof(s.addr));std::memset(&s.x87,0,sizeof(s.x87));
    s.seg.cs.flat=0x23;s.seg.ds.flat=0x2b;s.seg.ss.flat=0x2b;
    s.gpr.rax.dword=0x13579bdf;s.gpr.rcx.dword=0x2468ace0;s.gpr.rdx.dword=0x81726354;s.gpr.rbx.dword=0x10293847;
    s.gpr.rsp.dword=frame;s.gpr.rbp.dword=0x92837465;s.gpr.rsi.dword=0x56473829;s.gpr.rdi.dword=0xaabbccdd;s.gpr.rip.dword=entry;
    s.rflag.flat=0x202;s.aflag.cf=0;s.aflag.pf=0;s.aflag.af=0;s.aflag.zf=0;s.aflag.sf=0;s.aflag.df=0;s.aflag.of=0;
    s.x87.fxsave.cwd.flat=cw;s.x87.fxsave.swd.flat=top<<11;s.x87.fxsave.mxcsr.flat=0x1f80;
    s.sw.ie=0;s.sw.de=0;s.sw.ze=0;s.sw.oe=0;s.sw.ue=0;s.sw.pe=0;s.sw.sf=0;s.sw.c0=0;s.sw.c1=0;s.sw.c2=0;s.sw.c3=0;
    for(unsigned i=0;i<8;++i){std::memset(&s.st.elems[i].val,0,10);std::memset(&s.vec[i],0,16);}
}
static void capture(const State &s,Result &r,bool before){
    auto &raw=before?r.state_before:r.state_after;auto &fx=before?r.fx_before:r.fx_after;auto &env=before?r.env_before:r.env_after;
    (before?r.before:r.after)=cpu(s);std::memcpy(raw.data(),&s,3504);std::memcpy(fx.data(),&s.x87,512);
    const auto sw=status(s);std::memcpy(fx.data()+2,&sw,2);
    for(unsigned i=0;i<8;++i){std::memcpy(fx.data()+32+i*16,&s.st.elems[i].val,10);std::memcpy(fx.data()+160+i*16,&s.vec[i],16);}
    const auto put=[&](unsigned offset,std::uint32_t value){std::memcpy(env.data()+offset,&value,4);};
    require(s.x87.fxsave.ftw.flat==0,"First empty-stack experiment unexpectedly changed FTW");
    put(0,0xffff0000U|s.x87.fxsave.cwd.flat);put(4,0xffff0000U|sw);put(8,0xffffffffU);
    put(12,s.x87.fxsave.ip);put(16,s.x87.fxsave.cs.flat|(std::uint32_t{s.x87.fxsave.fop}<<16));
    put(20,s.x87.fxsave.dp);put(24,0xffff0000U|s.x87.fxsave.ds.flat);
}
// Derived from the previously reviewed integer worker's dual-format isolation,
// compiled afresh here. Host hardware bytes remain independent of State.
struct FpuScope {
    struct alignas(16) Image {std::uint8_t bytes[512];} saved;
    std::uint8_t env[28];
    explicit FpuScope(std::uint16_t cw){
        __asm__ volatile("fxsave64 %0\n\tfnstenv %1\n\tfninit\n\tfldcw %2":"=m"(saved),"=m"(env):"m"(cw):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)");
        const std::uint32_t mxcsr=0x1f80;__asm__ volatile("ldmxcsr %0"::"m"(mxcsr):"memory");
    }
    void restore(){__asm__ volatile("fxrstor64 %0\n\tfldenv %1"::"m"(saved),"m"(env):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)","xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");}
    bool restored(Result &r){
        Image after;std::uint8_t after_env[28];
        __asm__ volatile("fxrstor64 %2\n\tfldenv %3\n\tfxsave64 %0\n\tfnstenv %1":"=m"(after),"=m"(after_env):"m"(saved),"m"(env):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)","xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");
        std::memcpy(r.host_before.data(),saved.bytes,512);std::memcpy(r.host_after.data(),after.bytes,512);
        std::memcpy(r.host_env_before.data(),env,28);std::memcpy(r.host_env_after.data(),after_env,28);
        if(std::memcmp(saved.bytes,after.bytes,5)||std::memcmp(saved.bytes+24,after.bytes+24,4)||std::memcmp(env,after_env,28))return false;
        for(unsigned i=0;i<8;++i)if(std::memcmp(saved.bytes+32+i*16,after.bytes+32+i*16,10))return false;
        return std::memcmp(saved.bytes+160,after.bytes+160,256)==0;
    }
    ~FpuScope(){restore();}
};
static void execute(Harness &h,State &s,Context &c,Result &r){
    h.capture(r.memory_before);capture(s,r,true);
    {FpuScope host(r.cw);c.enter(s);r.status=c.failed;capture(s,r,false);h.capture(r.memory_after);
        r.event_count=c.event_count;r.events=c.events;r.reads=c.reads;r.writes=c.writes;r.clears=c.clears;r.tests=c.tests;r.returns=c.returns;
        r.host_restored=host.restored(r);r.primitives=c.primitives;}
}
static void controls(std::span<const std::uint8_t> pack){
    unsigned checks{};auto reject=[&](auto f){try{f();}catch(const std::exception &){++checks;return;}throw std::runtime_error("Rejected context control admitted");};
    {Harness h(pack);Context c(h.memory);State s;initialize(s,0x7f,0,1);s.gpr.rip.dword=entry+1;reject([&]{c.enter(s);});}
    {Harness h(pack);Context c(h.memory);c.write32(output_address(),0);require(c.failed&&c.event_count==0,"Inactive memory bridge admitted");++checks;}
    for(unsigned fault_index=0;fault_index<3;++fault_index){
        const unsigned address=fault_index==0?(input_address()&~4095U):fault_index==1?(output_address()&~4095U):0x20001000U;
        Harness h(pack);Context c(h.memory);State s;initialize(s,0x7f,0,1);Result r{};r.cw=0x7f;
        if(fault_index==1)h.memory.protect({address},Permissions::read);else h.memory.protect({address},Permissions::none);
        // Faulted pages cannot be captured; do not convert an observer failure
        // to fake successful execution. Capture the typed execution only.
        {FpuScope host(r.cw);c.enter(s);require(c.failed&&!c.complete,"Guest permission fault became success");require(host.restored(r),"Fault path lost host FP");}
        ++checks;
    }
    {Harness h(pack);Context c(h.memory);State s;initialize(s,0x7f,0,1);Result r{};r.cw=0x7f;execute(h,s,c,r);require(!r.status&&r.host_restored,"Positive actual compiled route failed");++checks;reject([&]{c.enter(s);});}
    {Harness h(pack);h.memory.store<std::uint32_t>({frame},sentinel+4);Context c(h.memory);State s;initialize(s,0x7f,0,1);Result r{};r.cw=0x7f;execute(h,s,c,r);require(r.status&&!c.complete&&r.host_restored,"Wrong return admitted");++checks;}
    std::cout<<"First FP compiled context controls: "<<checks<<"\n";
}
class Output {
    std::filesystem::path destination,staged;HANDLE handle=INVALID_HANDLE_VALUE;bool owns{};
public:
    explicit Output(const char *path):destination(path),staged(destination.string()+".fp-stage-"+std::to_string(GetCurrentProcessId())){
        require(!std::filesystem::exists(destination),"Fresh output required");
        handle=CreateFileW(staged.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
        require(handle!=INVALID_HANDLE_VALUE,"Fresh stage required");owns=true;
    }
    void write(const void *data,unsigned size){DWORD written{};require(WriteFile(handle,data,size,&written,nullptr)&&written==size,"Output write failed");}
    void commit(){require(FlushFileBuffers(handle),"Output flush failed");require(CloseHandle(handle),"Output close failed");handle=INVALID_HANDLE_VALUE;
        require(MoveFileExW(staged.c_str(),destination.c_str(),MOVEFILE_WRITE_THROUGH),"Output commit failed");owns=false;}
    ~Output(){if(handle!=INVALID_HANDLE_VALUE)CloseHandle(handle);if(owns)DeleteFileW(staged.c_str());}
};
} // namespace mw34::m4_fp_atan
extern "C" double __remill_read_memory_f64(void *c,std::uint32_t address){return std::bit_cast<double>(static_cast<mw34::m4_fp_atan::Context *>(c)->read64(address));}
extern "C" std::uint32_t __remill_read_memory_32(void *c,std::uint32_t address){return static_cast<mw34::m4_fp_atan::Context *>(c)->read32(address);}
extern "C" void *__remill_write_memory_f32(void *c,std::uint32_t address,float value){static_cast<mw34::m4_fp_atan::Context *>(c)->write32(address,std::bit_cast<std::uint32_t>(value));return c;}
extern "C" void *__remill_function_return(State *s,std::uint32_t pc,void *c){return static_cast<mw34::m4_fp_atan::Context *>(c)->returned(*s,pc);}
extern "C" void __remill_fpu_exception_clear(unsigned mask){auto *c=mw34::m4_fp_atan::active_context;if(!c)std::abort();c->clear(mask);}
extern "C" unsigned __remill_fpu_exception_test(unsigned mask){auto *c=mw34::m4_fp_atan::active_context;if(!c)std::abort();return c->test(mask);}
extern "C" float __remill_read_memory_f32(void *c,std::uint32_t address){return std::bit_cast<float>(static_cast<mw34::m4_fp_atan::Context *>(c)->read32(address));}
extern "C" void *__remill_write_memory_32(void *c,std::uint32_t address,std::uint32_t value){static_cast<mw34::m4_fp_atan::Context *>(c)->write32(address,value);return c;}
extern "C" void mw34_atan_primitive_admit(unsigned op){auto *c=mw34::m4_fp_atan::active_context;if(!c)std::abort();c->primitive(op);}
int main(int argc,char **argv){using namespace mw34::m4_fp_atan;try{
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    if(argc==3&&std::string(argv[1])=="--check-publication"){mw34::m4_fp_atan_publication::controls<Output>(argv[2]);return 0;}
    if(argc==2&&std::string(argv[1])=="--layout"){std::cout<<"State3504 Result83168 Header32 roots1\n";return 0;}
    if(argc==4&&std::string(argv[1])=="--check-context"){const auto pack=admit(argv[2],argv[3]);controls(pack);return 0;}
    require(argc==4||argc==5,"Sqrt native: pack image fresh-output [--directed]");
    const bool directed=argc==5;require(!directed||std::string(argv[4])=="--directed","Unknown mode");
    const auto pack=admit(argv[1],argv[2]);Output out(argv[3]);const std::uint32_t header[]{1,directed?mw34::m4_fp_atan_corpus::directed_records:48,sizeof(Result),3504,9,4096};
    out.write("MW4ATN01",8);out.write(header,sizeof(header));
    for(unsigned repeat=0;repeat<2;++repeat)for(unsigned input=0;input<(directed?mw34::m4_fp_atan_corpus::fixture_count:1);++input)
      for(unsigned sticky=0;sticky<(directed?2:1);++sticky)for(auto cw:mw34::m4_fp_atan_corpus::controls)for(unsigned top:{0U,7U}){
        Harness h(pack);if(directed){const auto v=mw34::m4_fp_atan_corpus::fixture(input);h.memory.protect({0x5c9000},mw34::Permissions::read|mw34::Permissions::write);
          h.memory.store<std::uint64_t>({0x5c9398},v.y);h.memory.store<std::uint64_t>({0x5c93a0},v.x);h.memory.protect({0x5c9000},mw34::Permissions::read);}
        Context c(h.memory);State s;initialize(s,cw,top,input*7919+repeat*3571+cw+sticky*449);s.sw.de=sticky;
        Result r{};r.repeat=directed?(repeat<<16)|(sticky<<15)|input:repeat;r.pc=entry;r.cw=cw;r.top=top;execute(h,s,c,r);
        if(r.status||!r.host_restored){std::cerr<<"case input="<<input<<" sticky="<<sticky<<" cw="<<cw<<" top="<<top<<" status="<<r.status<<" host="<<r.host_restored<<" events="<<r.event_count<<" reads="<<r.reads<<" writes="<<r.writes<<" clears="<<r.clears<<" tests="<<r.tests<<" returns="<<r.returns<<" primitive="<<r.primitives<<'\n';}
        require(!r.status&&r.host_restored,"Actual sqrt native route/host isolation failed");out.write(&r,sizeof(r));
    }
    out.commit();std::cout<<header[1]<<" actual compiled FSIN/FCOS records\n";return 0;
}catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}}
