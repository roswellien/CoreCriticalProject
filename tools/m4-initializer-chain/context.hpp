#pragma once
#include "protocol.hpp"
#include "access_schedule.hpp"
#include "memory/guest_memory.hpp"
#include <remill/Arch/X86/Runtime/State.h>
#include <thread>
#include <csetjmp>
extern "C" void *mw34_chain_entry_410910(State *,std::uint32_t,void *);
extern "C" void *mw34_chain_entry_410940(State *,std::uint32_t,void *);
namespace mw34::m4_initializer_chain {
inline Cpu observed_cpu(const State &s) {
    return {{s.gpr.rax.dword,s.gpr.rcx.dword,s.gpr.rdx.dword,s.gpr.rbx.dword,s.gpr.rsp.dword,s.gpr.rbp.dword,s.gpr.rsi.dword,s.gpr.rdi.dword},
        0x202U|(s.aflag.cf<<0)|(s.aflag.pf<<2)|(s.aflag.af<<4)|(s.aflag.zf<<6)|(s.aflag.sf<<7)|(s.aflag.df<<10)|(s.aflag.of<<11),s.gpr.rip.dword};
}
// Test-only construction is separate from the borrowed-memory executor.
struct HarnessMemory {
    mw34::GuestMemory memory;
    HarnessMemory(const Request &q,std::span<const std::uint8_t> code) {
        validate_request(q);require(code.size()==305&&sha256(code)==code_hash,"Harness code identity mismatch");
        memory.map({code_page},page_size,mw34::Permissions::read|mw34::Permissions::write);
        memory.map({helper_page},page_size,mw34::Permissions::read|mw34::Permissions::write);
        memory.write({preceding_entry},std::as_bytes(code.first(36)));memory.write({entry},std::as_bytes(code.subspan(36,203)));
        memory.write({0x40daf0},std::as_bytes(code.subspan(239,23)));memory.write({0x40db30},std::as_bytes(code.subspan(262,43)));
        memory.protect({code_page},mw34::Permissions::read|mw34::Permissions::execute);
        memory.protect({helper_page},mw34::Permissions::read|mw34::Permissions::execute);
        memory.map({stack_base},page_size,mw34::Permissions::read|mw34::Permissions::write);
        memory.map({global_base},page_size,mw34::Permissions::read|mw34::Permissions::write);
        const auto bytes=initial_memory(q);
        memory.write({stack_base},std::as_bytes(std::span{bytes.data(),page_size}));memory.write({global_base},std::as_bytes(std::span{bytes.data()+page_size,page_size}));
    }
};
class Context {
    using Entry=void *(*)(State *,std::uint32_t,void *);
    Entry selected{};
    std::uint32_t selected_pc{};
    bool frozen{},active{},consumed{},escape_ready{},callee_active{};
    std::thread::id owner;
    std::jmp_buf escape;
    void fault(){failed=true;if(active&&escape_ready&&owner==std::this_thread::get_id())std::longjmp(escape,1);}
    bool admitted(){if(!active||failed||owner!=std::this_thread::get_id()){fault();return false;}return true;}
    bool access(std::uint32_t address,unsigned width,unsigned operation) {
        if(!admitted())return false;
        if(selected_pc==preceding_entry){
            if(trace_count<167){if(width!=1||operation!=1||address!=global_first+trace_count*20){fault();return false;}}
            else if(trace_count!=167||width!=4||operation||address!=frame){fault();return false;}
        }else{
            if(trace_count>=initializer_accesses.size()){fault();return false;}
            const auto &expect=initializer_accesses[trace_count];
            const auto wanted=expect.stack?static_cast<std::uint32_t>(std::int64_t{frame}+expect.location):static_cast<std::uint32_t>(expect.location);
            if(address!=wanted||width!=expect.width||operation!=expect.operation){fault();return false;}
        }
        return true;
    }
    void log(std::uint32_t address,std::uint32_t value,unsigned width,unsigned operation){if(trace_count==max_events){fault();return;}events[trace_count++]={address,value,width,operation};}
 public:
    mw34::GuestMemory &memory;
    std::uint32_t frame{},return_target{},reads{},writes{},returns{},trace_count{},route_count{};
    bool failed{},complete{};
    std::array<Event,max_events> events{};
    std::array<Route,2> routes{};
    Context(mw34::GuestMemory &persistent,std::uint32_t stack_frame,std::uint32_t stack_low=stack_base,
            std::uint32_t stack_top=stack_base+page_size,std::uint32_t expected_return=sentinel):memory(persistent),frame(stack_frame),return_target(expected_return) {
        require(std::uint64_t{frame}>=std::uint64_t{stack_low}+28&&std::uint64_t{frame}+4<=stack_top,"Unsafe borrowed stack frame");
        std::array<std::uint8_t,305> actual{};
        memory.read({preceding_entry},std::as_writable_bytes(std::span{actual.data(),36}));memory.read({entry},std::as_writable_bytes(std::span{actual.data()+36,203}));
        memory.read({0x40daf0},std::as_writable_bytes(std::span{actual.data()+239,23}));memory.read({0x40db30},std::as_writable_bytes(std::span{actual.data()+262,43}));
        require(sha256(actual)==code_hash,"Borrowed image code identity mismatch");
    }
    void select(std::uint32_t pc){require(!frozen&&!selected&&(pc==entry||pc==preceding_entry),"Frozen/conflicting/unknown static selection");selected_pc=pc;selected=pc==entry?&mw34_chain_entry_410940:&mw34_chain_entry_410910;}
    void freeze(std::string_view identity){require(!frozen&&selected&&identity==image_hash,"Incomplete/frozen/wrong-image context");frozen=true;}
    void *enter(State &s,std::uint32_t pc) {
        require(frozen&&!active&&!consumed&&!failed&&pc==selected_pc&&s.gpr.rip.dword==pc&&s.gpr.rsp.dword==frame,"Unfrozen/reentrant/faulted/consumed/wrong entry context");
        active=true;consumed=true;escape_ready=true;owner=std::this_thread::get_id();void *token=this;
        if(setjmp(escape)==0)token=selected(&s,pc,this);
        escape_ready=false;active=false;
        const bool prior=selected_pc==preceding_entry;
        if(token!=this||failed||!complete||callee_active||trace_count!=(prior?168U:60U)||route_count!=(prior?0U:2U)||returns!=(prior?1U:3U)||reads!=(prior?1U:12U)||writes!=(prior?167U:48U))failed=true;
        return token;
    }
    std::uint32_t read32(std::uint32_t address) {
        if(!access(address,4,0))return 0;
        std::uint32_t value{};bool ok{};try{value=memory.load<std::uint32_t>({address});ok=true;}catch(const std::exception &){}
        if(!ok){fault();return 0;}++reads;log(address,value,4,0);return value;
    }
    void write32(std::uint32_t address,std::uint32_t value) {
        if(!access(address,4,1))return;
        bool ok{};try{memory.store<std::uint32_t>({address},value);ok=true;}catch(const std::exception &){}
        if(!ok){fault();return;}++writes;log(address,value,4,1);
    }
    void write8(std::uint32_t address,std::uint8_t value) {
        if(!access(address,1,1))return;
        bool ok{};try{memory.store<std::uint8_t>({address},value);ok=true;}catch(const std::exception &){}
        if(!ok){fault();return;}++writes;log(address,value,1,1);
    }
    void *callee(State &s,std::uint32_t pc) {
        if(!admitted())return this;
        if(selected_pc!=entry||callee_active||route_count>=2){fault();return this;}
        const bool first=route_count==0;const auto target=first?0x40daf0U:0x40db30U;const auto span=first?20U:28U;
        if(pc!=target||s.gpr.rip.dword!=target||s.gpr.rsp.dword!=frame-span||s.gpr.rcx.dword!=(first?0x6040f0U:0x6040d0U)){fault();return this;}
        auto &route=routes[route_count++];route.before=observed_cpu(s);route.entry_pc=target;route.return_pc=first?0x4109d7:0x4109fc;route.pop_bytes=first?12:20;callee_active=true;return this;
    }
    void *returned(State &s,std::uint32_t target) {
        if(!admitted())return this;
        if(callee_active){auto &route=routes[route_count-1];if(target!=route.return_pc||s.gpr.rip.dword!=target||s.gpr.rsp.dword!=frame-4){fault();return this;}route.after=observed_cpu(s);route.complete=1;callee_active=false;}
        else{if(complete||target!=return_target||s.gpr.rip.dword!=return_target||s.gpr.rsp.dword!=frame+4){fault();return this;}complete=true;}
        ++returns;return this;
    }
    void capture(std::array<std::uint8_t,memory_size> &bytes) const {memory.read({stack_base},std::as_writable_bytes(std::span{bytes.data(),page_size}));memory.read({global_base},std::as_writable_bytes(std::span{bytes.data()+page_size,page_size}));}
};
} // namespace mw34::m4_initializer_chain
