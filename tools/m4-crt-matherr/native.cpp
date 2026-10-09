// Isolated typed r9 service experiment. Full CRT entry is not executed.
#include "context.hpp"
#include <fstream>
#include <filesystem>
#include <iostream>
#include <vector>

using namespace mw34;
using namespace mw34::m4_crt_matherr;
static void need(bool ok,const char *why){if(!ok)throw std::runtime_error(why);}
static std::vector<std::byte> read_file(const char *name,std::size_t maximum){
    std::ifstream in(name,std::ios::binary|std::ios::ate);need(bool(in),"Input file unavailable");
    const auto end=in.tellg();need(end>=0 && static_cast<std::uint64_t>(end)<=maximum,"Input bound");
    std::vector<std::byte>b(static_cast<std::size_t>(end));in.seekg(0);
    in.read(reinterpret_cast<char*>(b.data()),static_cast<std::streamsize>(b.size()));
    need(bool(in),"Complete input read");return b;
}
struct HostScope {
    struct alignas(16) Image{std::uint8_t bytes[512];};Image before{},after{};
    std::uint8_t env[28]{},env_after[28]{};
    HostScope(){__asm__ volatile("fxsave64 %0\n\tfnstenv %1":"=m"(before),"=m"(env)::"memory");}
    void restore(){__asm__ volatile("fxrstor64 %0\n\tfldenv %1"::"m"(before),"m"(env):
        "memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)",
        "xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7",
        "xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");}
    void capture(){restore();__asm__ volatile("fxsave64 %0\n\tfnstenv %1":"=m"(after),"=m"(env_after)::"memory");}
    ~HostScope(){restore();}
};
static void host_check(const HostScope &s){
    need(!std::memcmp(s.before.bytes,s.after.bytes,5) &&
         !std::memcmp(s.before.bytes+24,s.after.bytes+24,4) &&
         !std::memcmp(s.env,s.env_after,28),"Host architectural control/ENV restoration");
    for(unsigned i=0;i<8;++i)need(!std::memcmp(s.before.bytes+32+16*i,s.after.bytes+32+16*i,10),"Host raw80 restoration");
    need(!std::memcmp(s.before.bytes+160,s.after.bytes+160,256),"All host XMM restoration");
}
template<class T>static void output(std::ofstream &out,const T &value){out.write(reinterpret_cast<const char*>(&value),sizeof(value));need(bool(out),"Complete observation write");}
int main(int argc,char **argv){try{
    need(argc==5,"Matherr native: admitted-game exact-provider exact-leaf fresh-raw-output");
    auto game=read_file(argv[1],2384384),provider=read_file(argv[2],266293),code=read_file(argv[3],17);
    need(provider.size()==266293 && m4::sha256(provider)=="2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7","Exact provider identity");
    need(code.size()==17 && m4::sha256(code)=="db28fc73ef336b9925b6cd56a37615599cc224d6a38cdd3b3cf5851c72e77bc9","Exact leaf identity");
    need(!std::filesystem::exists(argv[4]),"Fresh raw output required");
    auto r=m4_runtime::Runtime::from_admitted_image(game);
    auto &s=*reinterpret_cast<State*>(r.remill_state().data());
    r.memory().map({0x7800b000},4096,Permissions::read|Permissions::write);
    r.memory().write({entry},code);r.memory().protect({0x7800b000},Permissions::read|Permissions::execute);
    for(auto a:{0x78039000U,0x7803b000U})r.memory().map({a},4096,Permissions::read|Permissions::write);
    r.mark_remill_seeded();Context seed(r);
    r.register_service({GuestAddress{seed.slot},{m4_runtime::Abi::Cdecl,4,true},&adapter,
        "Exact __setusermatherr leaf experiment",m4_runtime::Domain::admitted_game,
        "2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7",
        "72dabe5c1616590b1fe624844914b6d21fab26cf8eb8ddc3d430de98f50adce4"});r.freeze_registry();
    std::ofstream out(argv[4],std::ios::binary);need(bool(out),"Create fresh observation");
    out.write("MW4MTH01",8);const std::array<unsigned,4>header{1,1536,3504,12288};output(out,header);
    constexpr std::array<unsigned,8> args{0,0x51e7b0,0xffffffff,0x10000001,0x30000000,0x7800b38f,0x80000000,0x12345678};
    constexpr std::array<unsigned,12> cws{0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f};
    constexpr std::array<unsigned,3> pages{0x20001000,0x78039000,0x7803b000};
    unsigned count{};
    for(unsigned repeat=0;repeat<2;++repeat)for(auto cw:cws)for(unsigned top=0;top<8;++top)for(auto arg:args){
        const auto index=count++;const unsigned caller_sp=0x20001800;
        for(unsigned j=0;j<3504;++j)reinterpret_cast<unsigned char*>(&s)[j]=static_cast<unsigned char>(j*13+index+7);
        s.addr.ds_base.dword=s.addr.ss_base.dword=0;s.addr.fs_base.dword=r.fs_base().value;
        s.x87.fxsave.cwd.flat=static_cast<std::uint16_t>(cw);s.x87.fxsave.swd.flat=static_cast<std::uint16_t>(top<<11);
        // This is declared raw State storage, not a hardware FLDENV admission.
        r.cpu()={0x13579bdf^index,0x2468ace0,0x81726354,0x10293847,caller_sp,
            0x92837465,0x56473829,0xaabbccdd,0x202U|((index&1)?0xcd5U:0),0x5ac428};
        project(s,r.cpu());
        std::array<std::byte,4096>page{};
        for(unsigned k=0;k<pages.size();++k){for(unsigned j=0;j<page.size();++j)page[j]=std::byte((index+j*7+k*19)&255);r.memory().write({pages[k]},page);}
        r.memory().store<unsigned>({caller_sp},arg);
        const auto initial_zero=r.memory().load<unsigned>({zero_global});
        std::array<std::byte,3504>state_before{},state_after{},expected{};
        std::memcpy(state_before.data(),&s,3504);expected=state_before;
        std::array<std::byte,12288>mem_before{},mem_after{},expected_memory{};
        for(unsigned k=0;k<pages.size();++k)r.memory().read({pages[k]},std::span{mem_before}.subspan(4096*k,4096));
        expected_memory=mem_before;
        auto put=[&](auto &bytes,unsigned offset,unsigned value){std::memcpy(bytes.data()+offset,&value,4);};
        put(expected,2216,arg);put(expected,2472,0x5ac42e);
        for(auto [offset,value]:std::array<std::pair<unsigned,unsigned>,6>{{{2065,0},{2067,1},{2069,0},{2071,1},{2073,0},{2077,0}}})expected[offset]=std::byte(value);
        put(expected_memory,0x7fc,0x5ac42e);put(expected_memory,4096+0x2b8,0);put(expected_memory,8192+0xc4,arg);
        const auto before_cpu=r.cpu();Context c(r);need(!owner,"Serial owner already occupied");owner=&c;
        HostScope host;
        try{r.call_import({c.slot},{0x5ac42e});}catch(...){owner=nullptr;throw;}
        owner=nullptr;host.capture();host_check(host);
        std::memcpy(state_after.data(),&s,3504);
        for(unsigned k=0;k<pages.size();++k)r.memory().read({pages[k]},std::span{mem_after}.subspan(4096*k,4096));
        need(state_after==expected,"Whole State differs from source-defined mutation model");
        need(mem_after==expected_memory,"Whole stack/global pages differ from source mutation model");
        const std::array<Event,5>events{{{caller_sp,arg,4,0},{zero_global,initial_zero,4,0},
            {zero_global,0,4,1},{callback_global,arg,4,1},{caller_sp-4,0x5ac42e,4,0}}};
        need(!std::memcmp(c.events.data(),events.data(),sizeof(events)) && c.complete && !c.failed,"All actual source-ordered memory events");
        auto expected_cpu=before_cpu;expected_cpu.eax=arg;expected_cpu.eip=0x5ac42e;
        expected_cpu.eflags=(before_cpu.eflags&~0x8d5U)|0x44U;
        need(r.cpu()==expected_cpu,"Actual typed CPU/Cdecl closure");
        const std::array<unsigned,5>tag{repeat,index,arg,cw,top};output(out,tag);output(out,before_cpu);output(out,r.cpu());
        output(out,state_before);output(out,state_after);output(out,mem_before);output(out,mem_after);
        output(out,c.events);output(out,host.before);output(out,host.after);output(out,host.env);output(out,host.env_after);
    }
    need(count==1536 && r.calls().size()==1536 && !r.poisoned(),"Actual complete typed call count");
    out.flush();need(bool(out),"Flush all actual observations");
    std::cout<<"1536 native whole-State/page/event/host checks passed; original comparison and independent acceptance pending\n";
    return 0;
}catch(const std::exception &e){owner=nullptr;std::cerr<<e.what()<<'\n';return 1;}}
