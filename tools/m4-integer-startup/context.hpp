#pragma once
#include "protocol.hpp"
#include "memory/guest_memory.hpp"
#include <remill/Arch/X86/Runtime/State.h>
#include <thread>
#include <csetjmp>
#define DECLARE_ENTRY(x) extern "C" void *mw34_integer_entry_##x(State *,std::uint32_t,void *)
DECLARE_ENTRY(43aec0);DECLARE_ENTRY(43aee0);DECLARE_ENTRY(43af00);DECLARE_ENTRY(43af20);DECLARE_ENTRY(43af40);DECLARE_ENTRY(43af60);DECLARE_ENTRY(43af80);DECLARE_ENTRY(43afa0);
DECLARE_ENTRY(467490);DECLARE_ENTRY(4674b0);DECLARE_ENTRY(4674d0);DECLARE_ENTRY(4b5b20);DECLARE_ENTRY(4c7940);DECLARE_ENTRY(4cfef0);
#undef DECLARE_ENTRY
namespace mw34::m4_integer_startup {
inline Cpu observed_cpu(const State &s){return {{s.gpr.rax.dword,s.gpr.rcx.dword,s.gpr.rdx.dword,s.gpr.rbx.dword,s.gpr.rsp.dword,s.gpr.rbp.dword,s.gpr.rsi.dword,s.gpr.rdi.dword},0x202U|(s.aflag.cf<<0)|(s.aflag.pf<<2)|(s.aflag.af<<4)|(s.aflag.zf<<6)|(s.aflag.sf<<7)|(s.aflag.df<<10)|(s.aflag.of<<11),s.gpr.rip.dword};}
inline constexpr std::array<std::uint32_t,8> destinations{0x605928,0x605908,0x605888,0x6058e8,0x605948,0x6058c8,0x6058a8,0x605968};
struct HarnessMemory {
    mw34::GuestMemory memory;
    HarnessMemory(const Request &q,std::span<const std::uint8_t> code){
        validate_request(q);require(code.size()==389&&sha256(code)==code_hash,"Wrong batch harness code");
        for(auto p:{0x43a000U,0x467000U,0x4b5000U,0x4c7000U,0x4cf000U})memory.map({p},page_size,mw34::Permissions::read|mw34::Permissions::write);
        for(const auto &f:fragments)memory.write({f.entry},std::as_bytes(code.subspan(f.bundle,f.size)));
        for(auto p:{0x43a000U,0x467000U,0x4b5000U,0x4c7000U,0x4cf000U})memory.protect({p},mw34::Permissions::read|mw34::Permissions::execute);
        const auto bytes=initial_memory(q);
        for(unsigned i=0;i<3;++i){const auto p=i==0?stack_base:(i==1?global_base:second_global_base);memory.map({p},page_size,mw34::Permissions::read|mw34::Permissions::write);memory.write({p},std::as_bytes(std::span{bytes.data()+i*page_size,page_size}));}
    }
};
class Context {
    using Entry=void *(*)(State *,std::uint32_t,void *);
    static constexpr std::array<Entry,14> compiled{&mw34_integer_entry_43aec0,&mw34_integer_entry_43aee0,&mw34_integer_entry_43af00,&mw34_integer_entry_43af20,&mw34_integer_entry_43af40,&mw34_integer_entry_43af60,&mw34_integer_entry_43af80,&mw34_integer_entry_43afa0,&mw34_integer_entry_467490,&mw34_integer_entry_4674b0,&mw34_integer_entry_4674d0,&mw34_integer_entry_4b5b20,&mw34_integer_entry_4c7940,&mw34_integer_entry_4cfef0};
    unsigned index{};bool selected{},frozen{},active{},consumed{},escape_ready{};std::thread::id owner;std::jmp_buf escape;
    void fault(){failed=true;if(active&&escape_ready&&owner==std::this_thread::get_id())std::longjmp(escape,1);}
    bool admitted(){if(!active||failed||owner!=std::this_thread::get_id()){fault();return false;}return true;}
    unsigned expected_events()const{return index<8?8U:(index<11?1U:(index==11?5U:(index==12?2U:3U)));}
    bool access(std::uint32_t address,unsigned width,unsigned op){
        if(!admitted()||trace_count>=expected_events()){fault();return false;}
        std::uint32_t target{};unsigned w=4,operation=1;
        if(index<8){target=destinations[index]+trace_count*4;if(trace_count==7){target=frame;operation=0;}}
        else if(index<11){target=frame;operation=0;}
        else if(index==11){target=0x60b2b8+trace_count*4;if(trace_count==2){target=0x60b2c0;w=1;}else if(trace_count==3){target=0x60b2c1;w=1;}else if(trace_count==4){target=frame;operation=0;}}
        else if(index==12){target=trace_count?frame:0x60b44c;operation=trace_count?0:1;}
        else{target=trace_count==2?frame:0x60b4a8+trace_count*4;operation=trace_count==2?0:1;}
        if(address!=target||width!=w||op!=operation){fault();return false;}return true;
    }
    void log(std::uint32_t address,std::uint32_t value,unsigned width,unsigned operation){events[trace_count++]={address,value,width,operation};}
 public:
    mw34::GuestMemory &memory;std::uint32_t frame{},return_target{},trace_count{},route_count{};bool failed{},complete{};
    std::array<Event,max_events> events{};std::array<Route,1> routes{};
    Context(mw34::GuestMemory &owned,std::uint32_t sp,std::uint32_t low=stack_base,std::uint32_t top=stack_base+page_size,std::uint32_t ret=sentinel):memory(owned),frame(sp),return_target(ret){
        require(frame>=low&&std::uint64_t{frame}+4<=top,"Unsafe borrowed integer stack");std::array<std::uint8_t,389> actual{};
        for(const auto &f:fragments)memory.read({f.entry},std::as_writable_bytes(std::span{actual.data()+f.bundle,f.size}));require(sha256(actual)==code_hash,"Borrowed integer code differs");
    }
    void select(std::uint32_t pc){require(!selected&&!frozen,"Frozen integer selection");for(unsigned i=0;i<14;++i)if(pc==entries[i]){index=i;selected=true;return;}throw std::runtime_error("Unknown compiled integer root");}
    void freeze(std::string_view image){require(selected&&!frozen&&image==image_hash,"Incomplete/frozen/wrong integer image");frozen=true;}
    void *enter(State &s,std::uint32_t pc){require(frozen&&!active&&!consumed&&!failed&&pc==entries[index]&&s.gpr.rip.dword==pc&&s.gpr.rsp.dword==frame,"Wrong integer context entry");active=consumed=escape_ready=true;owner=std::this_thread::get_id();void *token=this;if(setjmp(escape)==0)token=compiled[index](&s,pc,this);active=escape_ready=false;if(token!=this||!complete||trace_count!=expected_events()||route_count!=(index<8?1U:0U))failed=true;return token;}
    std::uint32_t read32(std::uint32_t address){if(!access(address,4,0))return 0;std::uint32_t value{};bool ok{};try{value=memory.load<std::uint32_t>({address});ok=true;}catch(const std::exception &){}if(!ok){fault();return 0;}log(address,value,4,0);return value;}
    template<class T>void write(std::uint32_t address,T value){if(!access(address,sizeof(T),1))return;bool ok{};try{memory.store<T>({address},value);ok=true;}catch(const std::exception &){}if(!ok){fault();return;}log(address,value,sizeof(T),1);}
    void write32(std::uint32_t address,std::uint32_t value){write(address,value);}void write8(std::uint32_t address,std::uint8_t value){write(address,value);}
    void *tail(State &s,std::uint32_t pc){if(!admitted())return this;if(index>=8||route_count||pc!=0x43ae30||s.gpr.rip.dword!=pc||s.gpr.rsp.dword!=frame||s.gpr.rcx.dword!=destinations[index]||trace_count){fault();return this;}route_count=1;routes[0].before=observed_cpu(s);routes[0].entry_pc=pc;routes[0].return_pc=return_target;return this;}
    void *returned(State &s,std::uint32_t target){if(!admitted())return this;if(complete||target!=return_target||s.gpr.rip.dword!=target||s.gpr.rsp.dword!=frame+4){fault();return this;}if(route_count){routes[0].after=observed_cpu(s);routes[0].complete=1;}complete=true;return this;}
    void capture(std::array<std::uint8_t,memory_size> &bytes)const{for(unsigned i=0;i<3;++i)memory.read({i==0?stack_base:(i==1?global_base:second_global_base)},std::as_writable_bytes(std::span{bytes.data()+i*page_size,page_size}));}
};
} // namespace mw34::m4_integer_startup
