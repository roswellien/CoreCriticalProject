// Bounded hand translation of the recovered caller, with a real host query.
// Guest volatility is explicitly unspecified; original volatile observations
// are never loaded into this implementation or synthesized to match an oracle.
#include "common.hpp"
#include "image_loader.hpp"
#include <remill/Arch/X86/Runtime/State.h>
#include <memory>
namespace mw34::spi {
static_assert(sizeof(State)==3504);
static Cpu cpu(const State&s){return {{s.gpr.rax.dword,s.gpr.rcx.dword,s.gpr.rdx.dword,s.gpr.rbx.dword,s.gpr.rsp.dword,s.gpr.rbp.dword,s.gpr.rsi.dword,s.gpr.rdi.dword},0x202U|s.aflag.cf|(s.aflag.pf<<2)|(s.aflag.af<<4)|(s.aflag.zf<<6)|(s.aflag.sf<<7)|(s.aflag.df<<10)|(s.aflag.of<<11),s.gpr.rip.dword};}
static void seed(State&s,unsigned cw,unsigned top,unsigned variant,unsigned repeat){auto*b=reinterpret_cast<std::uint8_t*>(&s);for(unsigned i=0;i<3504;++i)b[i]=static_cast<std::uint8_t>(i*29+cw+variant*91+repeat*3571+(i>>8)*7);std::memset(&s.addr,0,sizeof(s.addr));s.addr.fs_base.dword=0x7ffde000;s.seg.cs.flat=0x23;s.seg.ds.flat=s.seg.es.flat=s.seg.ss.flat=0x2b;std::memset(&s.x87,0,sizeof(s.x87));auto fx=initialfx(cw,top,variant);std::memcpy(&s.x87,fx.data(),512);for(unsigned i=0;i<8;++i){std::memset(&s.st.elems[i].val,0,10);std::memcpy(&s.vec[i],fx.data()+160+i*16,16);}s.sw.ie=s.sw.de=s.sw.ze=s.sw.oe=s.sw.ue=s.sw.pe=s.sw.sf=s.sw.c0=s.sw.c1=s.sw.c2=s.sw.c3=0;auto c=initial(variant);s.gpr.rax.dword=c.gpr[0];s.gpr.rcx.dword=c.gpr[1];s.gpr.rdx.dword=c.gpr[2];s.gpr.rbx.dword=c.gpr[3];s.gpr.rsp.dword=c.gpr[4];s.gpr.rbp.dword=c.gpr[5];s.gpr.rsi.dword=c.gpr[6];s.gpr.rdi.dword=c.gpr[7];s.gpr.rip.dword=c.pc;s.rflag.flat=c.flags;s.aflag.cf=c.flags&1;s.aflag.pf=(c.flags>>2)&1;s.aflag.af=(c.flags>>4)&1;s.aflag.zf=(c.flags>>6)&1;s.aflag.sf=(c.flags>>7)&1;s.aflag.df=(c.flags>>10)&1;s.aflag.of=(c.flags>>11)&1;}
static void project(const State&s,std::array<std::uint8_t,512>&fx,std::array<std::uint8_t,28>&env){std::memcpy(fx.data(),&s.x87,512);for(unsigned i=0;i<8;++i){std::memcpy(fx.data()+32+i*16,&s.st.elems[i].val,10);std::memcpy(fx.data()+160+i*16,&s.vec[i],16);}const std::uint32_t e[]{0xffff0000|s.x87.fxsave.cwd.flat,0xffff0000|s.x87.fxsave.swd.flat,0xffffffff,s.x87.fxsave.ip,s.x87.fxsave.cs.flat|(std::uint32_t(s.x87.fxsave.fop)<<16),s.x87.fxsave.dp,0xffff0000|s.x87.fxsave.ds.flat};std::memcpy(env.data(),e,28);}
struct Isolation {struct alignas(16)F{std::uint8_t b[512];}saved;std::uint8_t env[28];Isolation(){__asm__ volatile("fxsave64 %0\n\tfnstenv %1":"=m"(saved),"=m"(env)::"memory");}void restore(){__asm__ volatile("fxrstor64 %0\n\tfldenv %1"::"m"(saved),"m"(env):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)","xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");}void finish(Record&r){F after;std::uint8_t ae[28];__asm__ volatile("fxrstor64 %2\n\tfldenv %3\n\tfxsave64 %0\n\tfnstenv %1":"=m"(after),"=m"(ae):"m"(saved),"m"(env):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)","xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");std::memcpy(r.host_before.data(),saved.b,512);std::memcpy(r.host_after.data(),after.b,512);std::memcpy(r.host_env_before.data(),env,28);std::memcpy(r.host_env_after.data(),ae,28);r.host_restored=hostequal(r,true);}~Isolation(){restore();}};
class Context {
    bool active{},used{};std::uint32_t sentinel{broker};
public:
    GuestMemory memory;Record &record;State state;unsigned queries{};bool failed{},completed{};
    explicit Context(std::span<const std::uint8_t>pack,Record&r):record(r){for(unsigned i=0;i<5;++i){auto p=pack.data()+12+i*4104;auto a=word<std::uint32_t>(p),perm=word<std::uint32_t>(p+4);memory.map({a},4096,Permissions::read|Permissions::write);memory.write({a},std::as_bytes(std::span{p+8,4096}));memory.protect({a},perm==1?Permissions::read|Permissions::execute:perm==0?Permissions::read:Permissions::read|Permissions::write);}memory.store<std::uint32_t>({iat},0x1df20c);memory.protect({0x5bb000},Permissions::read);}
    void fixture(unsigned v){for(unsigned p=1;p<3;++p){auto b=pagefixture(p,v);memory.write({observed_pages[p]},std::as_bytes(std::span{b}));}memory.store<std::uint32_t>({frame},sentinel);}
    void capture(bool before){auto&bytes=before?record.memory_before:record.memory_after;for(unsigned i=0;i<3;++i)memory.read({observed_pages[i]},std::as_writable_bytes(std::span{bytes.data()+i*4096,4096}));(before?record.before:record.after)=cpu(state);std::memcpy((before?record.state_before:record.state_after).data(),&state,3504);project(state,before?record.fx_before:record.fx_after,before?record.env_before:record.env_after);}
    void log(unsigned pc,unsigned a,unsigned v,unsigned op){require(record.event_count<64,"Event capacity rejected");record.events[record.event_count++]={pc,a,v,4,op};}
    std::uint32_t load(unsigned pc,unsigned a){auto v=memory.load<std::uint32_t>({a});log(pc,a,v,0);return v;}
    void store(unsigned pc,unsigned a,unsigned v){memory.store<std::uint32_t>({a},v);log(pc,a,v,1);}
    void push(unsigned pc,unsigned v){state.gpr.rsp.dword-=4;store(pc,state.gpr.rsp.dword,v);}
    std::uint32_t pop(unsigned pc){auto v=load(pc,state.gpr.rsp.dword);state.gpr.rsp.dword+=4;return v;}
    void query(unsigned pc,unsigned owner){require(active&&!failed&&queries==0&&pc==call&&state.gpr.rip.dword==call&&owner==iat&&state.gpr.rsp.dword==frame-32,"Service route/lifetime rejected");
        require(load(pc,owner)==0x1df20c,"Owning IAT changed");auto sp=state.gpr.rsp.dword;
        require(load(pc,sp)==resume&&load(pc,sp+4)==SPI_GETWORKAREA&&load(pc,sp+8)==0&&load(pc,sp+12)==output&&load(pc,sp+16)==0,"Only exact read-only query arguments admitted");
        require(!state.aflag.df&&state.addr.ds_base.dword==0&&state.addr.es_base.dword==0&&state.addr.ss_base.dword==0,"Flat forward REP/query domain required");
        RECT rect{};memory.read({output},std::as_writable_bytes(std::span{&rect,1}));
        // The fixed40-byte object lies in one owned writable mapping. Six real
        // prefix stores already exercised its write permission before this API.
        auto &sv=record.service;sv.before=cpu(state);sv.before.pc=call;sv.rect_before=std::bit_cast<std::array<std::uint8_t,16>>(rect);
        struct alignas(16) F{std::uint8_t b[512];};F qb,qa;std::uint8_t eb[28],ea[28];
        __asm__ volatile("fxsave64 %0\n\tfnstenv %1":"=m"(qb),"=m"(eb)::"memory");
        const auto result=SystemParametersInfoA(SPI_GETWORKAREA,0,&rect,0);
        __asm__ volatile("fxsave64 %0\n\tfnstenv %1":"=m"(qa),"=m"(ea)::"memory");
        ++queries;sv.called=1;sv.BOOL_value=static_cast<std::uint32_t>(result);sv.guest_cleanup=16;
        std::memcpy(sv.fx_before.data(),qb.b,512);std::memcpy(sv.fx_after.data(),qa.b,512);std::memcpy(sv.env_before.data(),eb,28);std::memcpy(sv.env_after.data(),ea,28);
        sv.rect_after=std::bit_cast<std::array<std::uint8_t,16>>(rect);
        for(unsigned i=0;i<4;++i)store(pc,output+i*4,word<std::uint32_t>(sv.rect_after.data()+i*4));
        // These guest volatile fields have no service-defined output values.
        // Preserve their incoming representative; do not copy an original oracle.
        state.gpr.rax.dword=static_cast<std::uint32_t>(result);state.gpr.rsp.dword+=20;state.gpr.rip.dword=resume;sv.after=cpu(state);
    }
    void enter(){require(!active&&!used&&!failed&&state.gpr.rip.dword==entry&&state.gpr.rsp.dword==frame&&!state.aflag.df&&state.addr.ds_base.dword==0&&state.addr.es_base.dword==0&&state.addr.ss_base.dword==0,"Fresh exact caller/flat forward domain required");used=true;active=true;
        try{state.gpr.rip.dword=0x482d00;state.gpr.rcx.dword=object;state.gpr.rip.dword=0x482cc0;
            push(0x482cc0,state.gpr.rbx.dword);state.gpr.rbx.dword=state.gpr.rcx.dword;push(0x482cc3,state.gpr.rsi.dword);push(0x482cc4,state.gpr.rdi.dword);state.gpr.rax.dword=state.gpr.rbx.dword+24;
            push(0x482cc8,0);state.gpr.rcx.dword=6;state.gpr.rsi.dword=0x5e6000;state.gpr.rdi.dword=state.gpr.rbx.dword;push(0x482cd6,state.gpr.rax.dword);push(0x482cd7,0);push(0x482cd9,0x30);
            while(state.gpr.rcx.dword){store(0x482cdb,state.gpr.rdi.dword,load(0x482cdb,state.gpr.rsi.dword));state.gpr.rsi.dword+=4;state.gpr.rdi.dword+=4;--state.gpr.rcx.dword;}
            state.gpr.rip.dword=call;push(call,resume);query(call,iat);state.gpr.rdi.dword=pop(resume);state.gpr.rax.dword=state.gpr.rbx.dword;state.gpr.rsi.dword=pop(0x482ce6);state.gpr.rbx.dword=pop(0x482ce7);state.gpr.rip.dword=pop(0x482ce8);
            require(state.gpr.rip.dword==sentinel&&state.gpr.rsp.dword==frame+4&&queries==1,"Exact caller return rejected");completed=true;record.completed=1;
        }catch(...){failed=true;active=false;throw;}active=false;
    }
};
static void check_import(std::span<const std::uint8_t>image){auto parsed=m4::load_pe32(std::as_bytes(image));unsigned found{};for(auto&x:parsed.metadata.imports)if(x.iat_rva+0x400000==iat){require(x.name&&*x.name=="SystemParametersInfoA"&&_stricmp(x.library.c_str(),"USER32.dll")==0&&x.original_iat_value==0x1df20c,"Exact owning import identity required");++found;}require(found==1,"One owning import required");}
static void controls_run(std::span<const std::uint8_t>pack){unsigned denied{},positive{},poison{};for(unsigned mode=0;mode<12;++mode){Record r{};Context c(pack,r);c.fixture(0);seed(c.state,0x37f,0,0,0);switch(mode){case 1:c.state.aflag.df=1;break;case 2:c.state.addr.ds_base.dword=4;break;case 3:c.state.addr.es_base.dword=4;break;case 4:c.memory.protect({0x608000},Permissions::read);break;case 5:c.memory.protect({0x5e6000},Permissions::none);break;case 6:c.memory.unmap({0x20001000});break;case 7:c.memory.protect({0x5bb000},Permissions::read|Permissions::write);c.memory.store<std::uint32_t>({iat},1);break;case 8:c.memory.store<std::uint32_t>({frame},broker+1);break;case 9:c.state.gpr.rip.dword=entry+1;break;case 10:c.state.gpr.rsp.dword=frame+4;break;case 11:c.state.addr.ss_base.dword=4;break;}
        bool rejected{};{Isolation isolate;try{c.enter();}catch(const std::exception&){rejected=true;}isolate.finish(r);}require(r.host_restored,"Fault path host restoration failed");if(!mode){require(!rejected&&c.completed&&c.queries==1,"Positive real query failed");++positive;}else{require(rejected&&!c.completed,"Bad context became complete");if(mode!=8)require(c.queries==0,"Guard allowed query before invalid context denial");++denied;}
        bool reused{};try{c.enter();}catch(const std::exception&){reused=true;}require(reused,"Used/faulted context reused");++poison;
    }std::cout<<"{\"passed\":true,\"positive\":"<<positive<<",\"denials\":"<<denied<<",\"reuse_denials\":"<<poison<<"}\n";}
}
int main(int argc,char**argv){try{using namespace mw34::spi;SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);require(argc==4,"Usage: spi_native pack image fresh-output or --controls");const auto pack=admit(argv[1],argv[2]);check_import(read(argv[2],2384384));provider(true);if(std::string(argv[3])=="--controls"){controls_run(pack);return 0;}Output out(argv[3]);Header h{};std::memcpy(h.magic,"MW4SPIN1",8);h.version=1;h.count=cases;h.record_bytes=sizeof(Record);h.observed_pages=3;out.write(&h,sizeof(h));unsigned id{};for(unsigned repeat=0;repeat<2;++repeat)for(auto cw:controls)for(unsigned top:{0U,7U})for(unsigned v=0;v<3;++v){Record r{};r.id=id++;r.repeat=repeat;r.cw=cw;r.top=top;r.variant=v;r.native=1;r.service_defined_cpu=0x2f9;Context c(pack,r);c.fixture(v);seed(c.state,cw,top,v,repeat);c.capture(true);{Isolation isolate;c.enter();isolate.finish(r);}c.capture(false);require(r.completed&&r.host_restored,"Incomplete query caller");out.write(&r,sizeof(r));}require(id==cases,"Case extent differs");out.commit();return 0;}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
