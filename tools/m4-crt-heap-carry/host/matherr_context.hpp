#pragma once
#include "runtime.hpp"
#include "admission.hpp"
#include <remill/Arch/X86/Runtime/State.h>
#include <algorithm>
#include <array>
#include <cctype>
#include <cstring>
#include <thread>

namespace mw34::m4_crt_matherr_paired_native {
static_assert(sizeof(State)==3504);
inline constexpr unsigned entry = 0x7800b38f;
inline constexpr unsigned zero_global = 0x780392b8, callback_global = 0x7803b0c4;
struct Event { unsigned address, value, width, write; };
extern "C" void *sub_7800b38f(State *, unsigned, void *);

inline m4_runtime::Cpu32 cpu(const State &s) {
    return {s.gpr.rax.dword,s.gpr.rcx.dword,s.gpr.rdx.dword,s.gpr.rbx.dword,
            s.gpr.rsp.dword,s.gpr.rbp.dword,s.gpr.rsi.dword,s.gpr.rdi.dword,
            static_cast<unsigned>((s.rflag.flat & ~0xcd5ULL) | (s.aflag.cf << 0) |
                (s.aflag.pf << 2) | (s.aflag.af << 4) | (s.aflag.zf << 6) |
                (s.aflag.sf << 7) | (s.aflag.df << 10) | (s.aflag.of << 11)),
            s.gpr.rip.dword};
}
inline void project(State &s, const m4_runtime::Cpu32 &c) {
    s.gpr.rax.dword=c.eax;s.gpr.rcx.dword=c.ecx;s.gpr.rdx.dword=c.edx;
    s.gpr.rbx.dword=c.ebx;s.gpr.rsp.dword=c.esp;s.gpr.rbp.dword=c.ebp;
    s.gpr.rsi.dword=c.esi;s.gpr.rdi.dword=c.edi;s.gpr.rip.dword=c.eip;
    s.rflag.flat=c.eflags;s.aflag.cf=(c.eflags>>0)&1;s.aflag.pf=(c.eflags>>2)&1;
    s.aflag.af=(c.eflags>>4)&1;s.aflag.zf=(c.eflags>>6)&1;
    s.aflag.sf=(c.eflags>>7)&1;s.aflag.df=(c.eflags>>10)&1;s.aflag.of=(c.eflags>>11)&1;
}

// The admitted Runtime and provider mappings must outlive this one-call owner.
// Callback DWORDs are data here; callback execution is deliberately unresolved.
// Tiny C++ exception crosses only non-noexcept bridges and unwind-capable IR.
struct BridgeAbort {};
struct Context {
    m4_runtime::Runtime &runtime;
    State &state;
    unsigned slot{}, raw_iat{}, frame{}, return_pc{}, argument{}, step{};
    bool used{}, active{}, failed{}, complete{};
    const char *reason{};
    unsigned fault_pc{}, fault_address{};
    std::array<Event,5> events{};
    std::array<unsigned,4> nonvolatile{};
    std::thread::id thread;
    // Authored unit fault observer only; null in every paired replay.
    void (*test_after_event)(Context &, unsigned){};
    void (*test_before_execute)(Context &){};

    explicit Context(m4_runtime::Runtime &r)
        : runtime(r), state(*reinterpret_cast<State *>(r.remill_state().data())) {
        if(r.domain()!=m4_runtime::Domain::admitted_game || !r.remill_seeded())
            throw std::invalid_argument("Matherr requires seeded admitted persistent Runtime State");
        unsigned count{};
        for(const auto &i:r.image_metadata().imports) {
            auto library=i.library;
            std::transform(library.begin(),library.end(),library.begin(),
                [](unsigned char c){return static_cast<char>(std::tolower(c));});
            if(library=="msvcrt.dll" && i.name && *i.name=="__setusermatherr") {
                ++count;slot=r.image_metadata().image_base+i.iat_rva;raw_iat=i.original_iat_value;
            }
        }
        if(count!=1 || r.memory().load<unsigned>({slot})!=raw_iat)
            throw std::invalid_argument("Exact unique original matherr import-slot ownership required");
    }
    [[noreturn]] void deny(const char *why, unsigned address=0) {
        if(!failed){failed=true;reason=why;fault_pc=state.gpr.rip.dword;fault_address=address;}
        throw BridgeAbort{};
    }
    void guard() {
        if(!active || failed || thread!=std::this_thread::get_id()) deny("Matherr inactive/wrong-thread/faulted bridge");
    }
    unsigned read(unsigned address) {
        guard();
        const unsigned expected = step==0 ? frame+4 : step==1 ? zero_global : step==4 ? frame : 0;
        if(!expected || address!=expected) deny("Matherr unexpected required read",address);
        unsigned value{};bool bad{};
        try{value=runtime.memory().load<unsigned>({address});}catch(...){bad=true;}
        if(bad) deny("Matherr checked read fault",address);
        if(step==0)argument=value;
        if(step==4 && value!=return_pc) deny("Matherr return word changed",address);
        events[step++]={address,value,4,0};
        if(test_after_event)test_after_event(*this,step);
        return value;
    }
    void write(unsigned address,unsigned value) {
        guard();
        if(!((step==2 && address==zero_global && value==0) ||
             (step==3 && address==callback_global && value==argument)))
            deny("Matherr unexpected required store",address);
        bool bad{};try{runtime.memory().store<unsigned>({address},value);}catch(...){bad=true;}
        if(bad) deny("Matherr checked write fault",address);
        events[step++]={address,value,4,1};
        if(test_after_event)test_after_event(*this,step);
    }
    void returned(State *s,unsigned pc) {
        guard();
        const auto actual=cpu(state);
        if(s!=&state || pc!=return_pc || actual.eip!=return_pc || actual.esp!=frame+4 ||
           step!=5 || actual.eax!=argument || (actual.eflags&0x8c5)!=0x44 ||
           std::array<unsigned,4>{actual.ebx,actual.ebp,actual.esi,actual.edi}!=nonvolatile)
            deny("Matherr actual RET/CPU/frame closure rejected");
        complete=true;
    }
    void execute() {
        if(used || failed || active || runtime.poisoned() || runtime.cpu().eip!=slot)
            throw std::runtime_error("Matherr one-call typed service admission rejected");
        project(state,runtime.cpu());state.gpr.rip.dword=entry;
        frame=state.gpr.rsp.dword;
        if(state.addr.ds_base.dword || state.addr.ss_base.dword ||
           state.addr.fs_base.dword!=runtime.fs_base().value ||
           frame<runtime.stack_low().value || std::uint64_t{frame}+8>runtime.stack_top().value)
            throw std::runtime_error("Matherr flat segments/owned guest frame rejected");
        std::array<std::byte,17> code{};runtime.memory().read({entry},code);
        if(m4::sha256(code)!="db28fc73ef336b9925b6cd56a37615599cc224d6a38cdd3b3cf5851c72e77bc9" ||
           runtime.memory().load<unsigned>({slot})!=raw_iat)
            throw std::runtime_error("Matherr exact source/raw IAT changed");
        return_pc=runtime.memory().load<unsigned>({frame});
        nonvolatile={state.gpr.rbx.dword,state.gpr.rbp.dword,state.gpr.rsi.dword,state.gpr.rdi.dword};
        used=true;active=true;thread=std::this_thread::get_id();
        void *token=this;
        try { if(test_before_execute)test_before_execute(*this); token=sub_7800b38f(&state,entry,this); }
        catch(const BridgeAbort &) { /* First POD error was retained by deny. */ }
        catch(...) { active=false; throw; }
        active=false;
        if(token!=this || failed || !complete) {
            if(!failed){failed=true;reason="Matherr complete compiled leaf did not return";fault_pc=state.gpr.rip.dword;}
            throw std::runtime_error(reason);
        }
        runtime.cpu()=cpu(state);
    }
};
inline thread_local Context *owner{};
inline void adapter(m4_runtime::Runtime &r) {
    if(!owner || &owner->runtime!=&r) throw std::runtime_error("Matherr stable serial owner required");
    owner->execute();
}
}
