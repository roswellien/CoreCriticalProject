#pragma once
#include "protocol.hpp"
#include "memory/guest_memory.hpp"
#include <remill/Arch/X86/Runtime/State.h>
#include <thread>
#include <csetjmp>
extern "C" void *mw34_lifted_entry(State *,std::uint32_t,void *);
namespace mw34::m4_initializer {
class Context {
    using Entry=void *(*)(State *,std::uint32_t,void *);
    Entry selected{};
    bool frozen{},active{},consumed{},escape_ready{};
    std::thread::id owner;
    std::jmp_buf escape;
    void fault() {
        failed=true;
        if(active&&escape_ready&&owner==std::this_thread::get_id())std::longjmp(escape,1);
    }
    bool admitted() {
        if(!active||failed||owner!=std::this_thread::get_id()){fault();return false;}
        return true;
    }
    void log(std::uint32_t a,std::uint32_t value,unsigned width,unsigned operation) {
        if(trace_count==max_events){fault();return;}
        events[trace_count++]={a,value,width,operation};
    }
 public:
    mw34::GuestMemory memory;
    std::uint32_t frame{},reads{},writes{},returns{},trace_count{};
    bool failed{},complete{};
    std::array<Event,max_events> events{};
    Context(const Request &q,std::span<const std::uint8_t> code):frame(q.state.registers[4]) {
        validate_request(q);require(code.size()==36&&sha256(code)==code_hash,"Context code identity mismatch");
        memory.map({code_page},page_size,mw34::Permissions::read|mw34::Permissions::write);
        memory.write({entry},std::as_bytes(code));
        memory.protect({code_page},mw34::Permissions::read|mw34::Permissions::execute);
        memory.map({stack_base},page_size,mw34::Permissions::read|mw34::Permissions::write);
        memory.map({global_base},page_size,mw34::Permissions::read|mw34::Permissions::write);
        const auto bytes=initial_memory(q);
        memory.write({stack_base},std::as_bytes(std::span{bytes.data(),page_size}));
        memory.write({global_base},std::as_bytes(std::span{bytes.data()+page_size,page_size}));
    }
    void select(Entry fn) {
        require(!frozen&&!selected&&fn==&mw34_lifted_entry,"Frozen/conflicting/unadmitted static selection");selected=fn;
    }
    void freeze(std::string_view identity) {
        require(!frozen&&selected&&identity==image_hash,"Incomplete/frozen/wrong-image context");frozen=true;
    }
    void *enter(State &s,std::uint32_t pc) {
        require(frozen&&!active&&!consumed&&!failed&&pc==entry&&s.gpr.rip.dword==entry&&s.gpr.rsp.dword==frame,
                "Unfrozen/reentrant/faulted/consumed/wrong entry context");
        active=true;consumed=true;escape_ready=true;owner=std::this_thread::get_id();
        // A failure-only escape leaves no live bridge exception/destructor and
        // crosses only the pure LLVM body. The caller's FpuScope remains live.
        void *token=this;
        if(setjmp(escape)==0)token=selected(&s,pc,this);
        escape_ready=false;active=false;
        if(token!=this||failed||!complete||reads!=1||writes!=167||returns!=1||trace_count!=168)failed=true;
        return token;
    }
    std::uint32_t read32(std::uint32_t a) {
        if(!admitted())return 0;
        if(a!=frame||reads||writes!=167){fault();return 0;}
        std::uint32_t value{};bool ok{};
        try{value=memory.load<std::uint32_t>({a});ok=true;}catch(const std::exception &){}
        if(!ok){fault();return 0;}
        ++reads;log(a,value,4,0);return value;
    }
    void write8(std::uint32_t a,std::uint8_t value) {
        if(!admitted())return;
        if(writes>=167||a!=global_first+writes*20||reads){fault();return;}
        bool ok{};
        try{memory.store<std::uint8_t>({a},value);ok=true;}catch(const std::exception &){}
        if(!ok){fault();return;}
        ++writes;log(a,value,1,1);
    }
    void *returned(State &s,std::uint32_t target) {
        if(!admitted())return this;
        if(returns||target!=sentinel||s.gpr.rip.dword!=sentinel||std::uint64_t{frame}+4!=s.gpr.rsp.dword){fault();return this;}
        ++returns;complete=true;return this;
    }
    void capture(std::array<std::uint8_t,memory_size> &bytes) const {
        memory.read({stack_base},std::as_writable_bytes(std::span{bytes.data(),page_size}));
        memory.read({global_base},std::as_writable_bytes(std::span{bytes.data()+page_size,page_size}));
    }
};
}
