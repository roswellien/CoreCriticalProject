#pragma once
#include "protocol.hpp"
#include "memory/guest_memory.hpp"
#include <remill/Arch/X86/Runtime/State.h>
#include <thread>

extern "C" void *mw34_lifted_entry(State *,std::uint32_t,void *);
namespace mw34::m3_slice {
// A single admitted static route. Guest addresses never carry host pointers.
class Context {
    using Entry = void *(*)(State *,std::uint32_t,void *);
    Entry selected{};
    bool frozen{},active{},consumed{};
    std::thread::id owner;
  public:
    mw34::GuestMemory memory;
    std::uint32_t frame{},reads{},writes{},returns{};
    bool failed{},complete{};
    Context(const Request &q,std::span<const std::uint8_t> code):frame(q.state.registers[4]) {
        validate_request(q);require(code.size()==43&&sha256(code)==code_hash,"Context code identity mismatch");
        memory.map({code_page},page_size,mw34::Permissions::read|mw34::Permissions::write);
        memory.write({entry},std::as_bytes(code));
        memory.protect({code_page},mw34::Permissions::read|mw34::Permissions::execute);
        memory.map({stack_base},page_size,mw34::Permissions::read|mw34::Permissions::write);
        memory.map({global_base},page_size,mw34::Permissions::read|mw34::Permissions::write);
        const auto initial=initial_memory(q);
        memory.write({stack_base},std::as_bytes(std::span{initial.data(),page_size}));
        memory.write({global_base},std::as_bytes(std::span{initial.data()+page_size,page_size}));
    }
    void select(Entry fn) {
        require(!frozen&&!selected&&fn==&mw34_lifted_entry,"Frozen/conflicting/unadmitted static selection");selected=fn;
    }
    void freeze(std::string_view image) {
        require(!frozen&&selected&&image==image_hash,"Incomplete/frozen/wrong-image context");frozen=true;
    }
    void *enter(State &s,std::uint32_t pc) {
        require(frozen&&!active&&!consumed&&pc==entry&&s.gpr.rip.dword==entry&&s.gpr.rsp.dword==frame,"Unfrozen/reentrant/consumed/wrong entry context");
        active=true;consumed=true;owner=std::this_thread::get_id();
        auto *token=selected(&s,pc,this);
        active=false;
        if(token!=this||failed||!complete||reads!=3||writes!=5||returns!=1)failed=true;
        return token;
    }
    bool bridge_admitted() {if(!active||owner!=std::this_thread::get_id()||failed){failed=true;return false;}return true;}
    std::uint32_t read32(std::uint32_t address) noexcept {
        if(!bridge_admitted())return 0;
        if(address!=frame&&address!=frame+4&&address!=frame+8){failed=true;return 0;}
        try {auto v=memory.load<std::uint32_t>({address});++reads;return v;}catch(const std::exception &){failed=true;return 0;}
    }
    void write32(std::uint32_t address,std::uint32_t value) noexcept {
        if(!bridge_admitted())return;
        if(address<global_first||address>=global_first+20||(address-global_first)%4){failed=true;return;}
        try {memory.store<std::uint32_t>({address},value);++writes;}catch(const std::exception &){failed=true;}
    }
    void *returned(State &s,std::uint32_t pc) noexcept {
        if(!bridge_admitted())return this;
        if(returns||pc!=sentinel||s.gpr.rip.dword!=sentinel||std::uint64_t{frame}+12!=s.gpr.rsp.dword){failed=true;return this;}
        ++returns;complete=true;return this;
    }
    void capture(std::array<std::uint8_t,memory_size> &out) const {
        memory.read({stack_base},std::as_writable_bytes(std::span{out.data(),page_size}));
        memory.read({global_base},std::as_writable_bytes(std::span{out.data()+page_size,page_size}));
    }
};
} // namespace mw34::m3_slice
