// Finite native source execution. Numeric values come only from the literal
// linked bodies, genuine BEFORE memory, and typed raw80 hardware primitives.
#include "fixture_spec.hpp"
#include "literal_dispatch.hpp"
#include "runtime.hpp"
#include "admission.hpp"
#include <Windows.h>
#include <remill/Arch/X86/Runtime/State.h>
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <span>
#include <vector>
using namespace mw34;
using namespace mw34::m4_runtime;
namespace hf = mw34_hypot_fixture;
static_assert(sizeof(State) == 3504 && sizeof(Cpu32) == 40);
static void need(bool v, const char *s) { if (!v) throw std::runtime_error(s); }
static std::filesystem::path output;
static std::vector<std::byte> file(const std::filesystem::path &p) {
    std::ifstream f(p, std::ios::binary | std::ios::ate);
    need(bool(f), "Native bounded input open");
    auto n = f.tellg(); need(n >= 0 && n < 64 * 1024 * 1024, "Native bounded input size");
    std::vector<std::byte> b(static_cast<std::size_t>(n)); f.seekg(0);
    f.read(reinterpret_cast<char *>(b.data()), b.size()); need(bool(f), "Whole native input read"); return b;
}
static void dump(const std::string &name, const void *p, std::size_t n) {
    const auto path = output / name; std::filesystem::create_directories(path.parent_path());
    need(!std::filesystem::exists(path), "Fresh native output file");
    std::ofstream f(path, std::ios::binary); f.write(static_cast<const char *>(p), n);
    need(bool(f), "Whole native output write");
}
struct Page { unsigned address, permissions; std::array<std::byte,4096> initial; };
struct Access { unsigned pc, address, width, writing; std::array<std::byte,28> bytes{}; };
struct Frame { unsigned target, address, ret; };
struct Api {
    unsigned ordinal{}, frame{}, ret{};
    State before{}, after{};
    Cpu32 CPU_before{}, CPU_after{};
    std::array<std::byte,32> frame_before{}, frame_after{};
    std::array<std::byte,4096> stack_before{}, stack_after{};
};
struct alignas(16) Hardware { std::array<std::byte,512> fx{}; std::array<std::byte,28> env{}; };
static void hardware(Hardware &x) {
    __asm__ volatile("fxsave64 %0\n\tfnstenv %1\n\tfxrstor64 %0\n\tfldenv %1"
        : "=m"(x.fx), "=m"(x.env) :: "memory");
}
static void restore(const Hardware &x) {
    __asm__ volatile("fxrstor64 %0\n\tfldenv %1" :: "m"(x.fx), "m"(x.env)
        : "memory", "st", "st(1)", "st(2)", "st(3)", "st(4)", "st(5)", "st(6)", "st(7)",
          "xmm0", "xmm1", "xmm2", "xmm3", "xmm4", "xmm5", "xmm6", "xmm7", "xmm8",
          "xmm9", "xmm10", "xmm11", "xmm12", "xmm13", "xmm14", "xmm15");
}
struct Isolation {
    Hardware before{}, after{}; bool closed{};
    explicit Isolation(std::uint16_t cw) {
        hardware(before);
        __asm__ volatile("fninit\n\tfldcw %0" :: "m"(cw) : "memory", "st", "st(1)",
            "st(2)", "st(3)", "st(4)", "st(5)", "st(6)", "st(7)");
    }
    void close() { restore(before); hardware(after); closed = true; }
    ~Isolation() { if (!closed) restore(before); }
};
struct Context;
static thread_local Context *active{};
struct Context {
    Runtime &r; State &s; const std::vector<Page> &pages;
    unsigned sequence, cursor{}, tests{}, clears{}, primitives{}, returns{};
    DWORD thread = GetCurrentThreadId(); bool entered{}, complete{};
    std::vector<Access> accesses; std::vector<Frame> frames; std::array<Api,2> APIs{}; unsigned API_count{};
    Context(Runtime &runtime, const std::vector<Page> &p, unsigned n)
        : r(runtime), s(*reinterpret_cast<State *>(r.remill_state().data())), pages(p), sequence(n) {
        need(!active && n < 6 && r.domain() == Domain::admitted_game, "Unique admitted numeric context");
        accesses.reserve(hf::accesses.size()); frames.reserve(64); active = this;
    }
    ~Context() { if (active == this) active = nullptr; }
    void authority() {
        need(active == this && GetCurrentThreadId() == thread, "Exact active numeric context and host thread");
        if (entered && !complete) {
            const bool final_return = s.gpr.rip.dword == Runtime::external_return && frames.size() == 1 && frames.back().ret == Runtime::external_return;
            need(final_return || hf::reached_PC(s.gpr.rip.dword), "Unobserved numeric source PC at a native bridge denied");
        }
    }
    Cpu32 cpu() const {
        Cpu32 c{s.gpr.rax.dword,s.gpr.rcx.dword,s.gpr.rdx.dword,s.gpr.rbx.dword,
            s.gpr.rsp.dword,s.gpr.rbp.dword,s.gpr.rsi.dword,s.gpr.rdi.dword,hf::initial_flags,s.gpr.rip.dword};
        const unsigned f[]{s.aflag.cf,s.aflag.pf,s.aflag.af,s.aflag.zf,s.aflag.sf,s.aflag.df,s.aflag.of};
        constexpr unsigned bits[]{0,2,4,6,7,10,11};
        for (unsigned i = 0; i < 7; ++i) c.eflags = (c.eflags & ~(1U<<bits[i])) | (unsigned(bool(f[i]))<<bits[i]);
        return c;
    }
    void checkpoint(const char *stem) {
        auto c = cpu(); dump(std::string(stem)+"/State.bin", &s, sizeof(s));
        dump(std::string(stem)+"/CPU.bin", &c, sizeof(c));
        for (const auto &p : pages) { std::array<std::byte,4096> b; r.memory().read({p.address},b);
            dump(std::string(stem)+"/pages/"+std::to_string(p.address)+".bin",b.data(),b.size()); }
    }
    void access(unsigned a, unsigned n, bool writing, std::span<const std::byte> value) {
        authority(); need(cursor < hf::accesses.size(), "Finite source operand count");
        const auto &e = hf::accesses[cursor];
        if (!(e.pc == s.gpr.rip.dword && e.address == a && e.width == n && e.writing == unsigned(writing))) {
            std::cerr << "operand=" << cursor << " actual_PC=" << std::hex << s.gpr.rip.dword
                      << " expected_PC=" << e.pc << " address=" << a << " expected=" << e.address
                      << " width=" << std::dec << n << " writing=" << writing << '\n';
            throw std::runtime_error("Exact causal source PC/address/width/direction");
        }
        need(n <= 28 && value.size() == n, "Complete bounded source operand payload");
        Access v{e.pc,a,n,unsigned(writing)}; std::memcpy(v.bytes.data(),value.data(),n);
        accesses.push_back(v); ++cursor;
    }
    void read(unsigned a, std::span<std::byte> value) {
        authority(); r.memory().read({a},value); access(a,unsigned(value.size()),false,value);
    }
    void write(unsigned a, std::span<const std::byte> value) {
        access(a,unsigned(value.size()),true,value); r.memory().write({a},value);
        if (value.size() == 4 && hf::is_call(s.gpr.rip.dword)) {
            unsigned ret; std::memcpy(&ret,value.data(),4); frames.push_back({0,a,ret});
        }
    }
    void *dispatch(unsigned pc, bool call) {
        authority(); need(s.gpr.rip.dword == pc, "Exact actual source dispatch PC");
        if (call) { need(!frames.empty() && frames.back().target == 0 && frames.back().address == s.gpr.rsp.dword,
            "Actual committed source CALL frame"); frames.back().target = pc; }
        const mw34_hypot_literal::Body *body{};
        for (const auto &b : mw34_hypot_literal::bodies) if (b.entry == pc) body = &b;
        need(body, "Unobserved source callback or fragment denied");
        if (pc != 0x7802a122) return body->call(&s,pc,this);
        need(call && API_count < 2, "Two genuine literal cdecl hypot intervals");
        auto &a = APIs[API_count]; a.ordinal = API_count++; a.frame = s.gpr.rsp.dword; a.ret = frames.back().ret;
        a.before = s; a.CPU_before = cpu(); r.memory().read({a.frame},a.frame_before);
        r.memory().read({0x20001000},a.stack_before);
        void *result = body->call(&s,pc,this);
        a.after = s; a.CPU_after = cpu(); r.memory().read({a.frame},a.frame_after);
        r.memory().read({0x20001000},a.stack_after);
        need(result == this && s.gpr.rip.dword == a.ret && s.gpr.rsp.dword == a.frame+4,
            "Exact cdecl RET4 leaves caller argument cleanup to literal source"); return result;
    }
    void returned(unsigned pc) {
        authority(); need(!frames.empty() && frames.back().ret == pc, "Exact current source return frame identity");
        frames.pop_back(); ++returns;
    }
};
static Context &owner(void *p) { need(active && active == p, "Exact numeric memory token"); active->authority(); return *active; }
extern "C" void mw34_hypot_control_admit(State *s, void *p) { need(&owner(p).s == s, "Exact control State identity"); }
template <typename T> static T load(void *p, unsigned a) { T v{}; owner(p).read(a,{reinterpret_cast<std::byte*>(&v),sizeof(v)}); return v; }
template <typename T> static void *store(void *p, unsigned a, T v) { owner(p).write(a,{reinterpret_cast<const std::byte*>(&v),sizeof(v)}); return p; }
extern "C" std::uint8_t mw34_hypot_read_memory_8(void*p,unsigned a){return load<std::uint8_t>(p,a);}
extern "C" std::uint16_t mw34_hypot_read_memory_16(void*p,unsigned a){return load<std::uint16_t>(p,a);}
extern "C" unsigned mw34_hypot_read_memory_32(void*p,unsigned a){return load<unsigned>(p,a);}
extern "C" std::uint64_t mw34_hypot_read_memory_64(void*p,unsigned a){return load<std::uint64_t>(p,a);}
extern "C" float mw34_hypot_read_memory_f32(void*p,unsigned a){return load<float>(p,a);}
extern "C" double mw34_hypot_read_memory_f64(void*p,unsigned a){return load<double>(p,a);}
extern "C" void *mw34_hypot_read_memory_f80(void*p,unsigned a,void *v){owner(p).read(a,{static_cast<std::byte*>(v),10});return p;}
extern "C" void *mw34_hypot_write_memory_8(void*p,unsigned a,std::uint8_t v){return store(p,a,v);}
extern "C" void *mw34_hypot_write_memory_16(void*p,unsigned a,std::uint16_t v){return store(p,a,v);}
extern "C" void *mw34_hypot_write_memory_32(void*p,unsigned a,unsigned v){return store(p,a,v);}
extern "C" void *mw34_hypot_write_memory_64(void*p,unsigned a,std::uint64_t v){return store(p,a,v);}
extern "C" void *mw34_hypot_write_memory_f32(void*p,unsigned a,float v){return store(p,a,v);}
extern "C" void *mw34_hypot_write_memory_f64(void*p,unsigned a,double v){return store(p,a,v);}
extern "C" void *mw34_hypot_write_memory_f80(void*p,unsigned a,const void*v){owner(p).write(a,{static_cast<const std::byte*>(v),10});return p;}
extern "C" void *mw34_hypot_function_call(State*s,unsigned pc,void*p){auto&c=owner(p);need(s==&c.s,"Exact call State");return c.dispatch(pc,true);}
extern "C" void *mw34_hypot_jump(State*s,unsigned pc,void*p){auto&c=owner(p);need(s==&c.s,"Exact jump State");return c.dispatch(pc,false);}
extern "C" void *mw34_hypot_missing_block(State*s,unsigned pc,void*p){return mw34_hypot_jump(s,pc,p);}
extern "C" void *mw34_hypot_function_return(State*s,unsigned pc,void*p){auto&c=owner(p);need(s==&c.s,"Exact return State");c.returned(pc);return p;}
extern "C" void *mw34_hypot_async_hyper_call(State*,unsigned,void*){throw std::runtime_error("Unobserved padded source instruction denied");}
extern "C" void *mw34_hypot_sync_hyper_call(State*,unsigned,void*){throw std::runtime_error("Unobserved source hypercall denied");}
extern "C" void mw34_hypot_fpu_exception_clear(unsigned mask){need(active&&mask==127,"Exact admitted FP exception mask");active->authority();++active->clears;__asm__ volatile("fnclex":::"memory");}
extern "C" unsigned mw34_hypot_fpu_exception_test(unsigned mask){need(active&&mask==127,"Exact admitted FP exception mask");active->authority();++active->tests;std::uint16_t sw;__asm__ volatile("fnstsw %0":"=m"(sw)::"memory");return sw&mask;}
struct Raw80 { std::array<std::byte,10> bytes; };
extern "C" void mw34_hypot_fsqrt_raw80(const Raw80 *input, Raw80 *out){need(active,"Active raw80 sqrt context");active->authority();++active->primitives;__asm__ volatile("fldt %1\n\tfsqrt\n\tfstpt %0":"=m"(*out):"m"(*input):"memory","st");}
#include "generated_bridges.inc"
static void native_root(Runtime &r) {
    auto &c = owner(active); need(&r == &c.r && !c.entered, "One registered native numeric root"); c.entered = true;
    auto cpu = r.cpu(); std::memset(&c.s,0,sizeof(c.s));
    const unsigned offsets[]{2216,2248,2264,2232,2312,2328,2280,2296,2472};
    const unsigned values[]{cpu.eax,cpu.ecx,cpu.edx,cpu.ebx,cpu.esp,cpu.ebp,cpu.esi,cpu.edi,cpu.eip};
    for(unsigned i=0;i<9;++i)std::memcpy(reinterpret_cast<std::byte*>(&c.s)+offsets[i],values+i,4);
    c.s.rflag.flat=cpu.eflags;
    const unsigned offsets_f[]{2065,2067,2069,2071,2073,2075,2077},bits[]{0,2,4,6,7,10,11};
    for(unsigned i=0;i<7;++i)reinterpret_cast<std::byte*>(&c.s)[offsets_f[i]]=std::byte{static_cast<unsigned char>((cpu.eflags>>bits[i])&1)};
    std::memcpy(&c.s.x87,r.fx().data(),512);c.s.seg.cs.flat=0x23;c.s.seg.ds.flat=0x2b;c.s.seg.ss.flat=0x2b;
    need(c.s.x87.fxsave.ftw.flat==0,"Measured normal empty source stack only");
    // The source occupies its virtual x87 stack through literal loads. The
    // compiler's independent hardware stack starts empty under the source CW.
    r.mark_remill_seeded();c.frames.push_back({0x4b5910,cpu.esp,Runtime::external_return});c.checkpoint("before");
    Isolation hw(c.s.x87.fxsave.cwd.flat);void *result=c.dispatch(0x4b5910,false);hw.close();
    dump("host-before-FX.bin",hw.before.fx.data(),512);dump("host-after-FX.bin",hw.after.fx.data(),512);
    dump("host-before-ENV.bin",hw.before.env.data(),28);dump("host-after-ENV.bin",hw.after.env.data(),28);
    need(result==&c&&c.frames.empty()&&c.cursor==hf::accesses.size()&&c.API_count==2,"Complete finite native numeric closure");
    c.complete=true;r.cpu()=c.cpu();c.checkpoint("after");
}
int main(int argc,char **argv) {
    try {
        need(argc==6,"image BEFORE-pack CPU/FX/ENV six-input file sequence fresh-output");
        auto seq=unsigned(std::stoul(argv[4]));need(seq<6,"Finite numeric input sequence");output=argv[5];
        need(!std::filesystem::exists(output)&&std::filesystem::create_directory(output),"Fresh native fixture output");
        auto image=file(argv[1]);need(m4::sha256(image)==m4::admitted_image_hash,"Exact admitted game image");
        Policy policy;policy.stack_bytes=65536;auto r=Runtime::from_admitted_image(image,policy);
        auto pack=file(argv[2]);need(pack.size()>=12&&!std::memcmp(pack.data(),"MW4J124P",8),"Whole genuine BEFORE pack");
        unsigned count;std::memcpy(&count,pack.data()+8,4);need(count==190&&pack.size()==12+std::size_t(count)*4104,"Exact190 pages");
        std::vector<Page> pages;pages.reserve(count);
        for(unsigned i=0;i<count;++i){Page p{};auto at=pack.data()+12+i*4104;std::memcpy(&p.address,at,4);std::memcpy(&p.permissions,at+4,4);std::memcpy(p.initial.data(),at+8,4096);need(p.permissions<=2,"Typed source page rights");bool mapped=false;
            if(p.address>=policy.stack_low.value&&std::uint64_t(p.address)+4096<=std::uint64_t(policy.stack_low.value)+policy.stack_bytes){r.memory().write({p.address},p.initial);mapped=true;}
            for(const auto &region:r.image_metadata().mapped_regions)if(region.start.value<=p.address&&std::uint64_t(p.address)+4096<=std::uint64_t(region.start.value)+region.size){r.memory().protect(region.start,Permissions::read|Permissions::write);r.memory().write({p.address},p.initial);r.memory().protect(region.start,region.permissions);mapped=true;break;}
            if(!mapped){r.memory().map({p.address},4096,Permissions::read|Permissions::write);r.memory().write({p.address},p.initial);r.memory().protect({p.address},p.permissions==0?Permissions::read|Permissions::execute:p.permissions==1?Permissions::read:Permissions::read|Permissions::write);}pages.push_back(p);
        }
        auto inputs=file(argv[3]);need(inputs.size()==3480,"Six exact genuine CPU40/FX512/ENV28 BEFORE inputs");
        Cpu32 cpu;std::memcpy(&cpu,inputs.data()+seq*580,40);need(cpu.eip==0x4b5910&&cpu.esp==0x20001800,"Actual finite source entry/frame");
        cpu.esp+=4;r.cpu()=cpu;std::memcpy(r.fx().data(),inputs.data()+seq*580+40,512);
        r.register_translation({{0x4b5910},{Abi::Cdecl,0,true},&native_root,"Finite literal hypot game root",{Domain::admitted_game,m4::admitted_image_hash,hf::root_bytes,hf::root_sha,hf::native_object_sha,hf::lift_report_sha}});r.freeze_registry();
        Context c(r,pages,seq);r.invoke({0x4b5910});need(c.complete&&r.calls().size()==1&&r.calls()[0].completed&&!r.poisoned(),"Actual registered native Runtime completed");
        dump("accesses.bin",c.accesses.data(),c.accesses.size()*sizeof(Access));dump("APIs.bin",c.APIs.data(),sizeof(c.APIs));
        const std::array<unsigned,10> schema{sizeof(Access),sizeof(Api),c.cursor,c.API_count,sizeof(State),sizeof(Cpu32),unsigned(pages.size()),c.primitives,c.tests,c.clears};dump("schema.bin",schema.data(),sizeof(schema));
        dump("COMPLETE.txt","complete",8);std::cout<<"one registered native numeric root completed\n";return 0;
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
