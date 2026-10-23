#pragma once
#include "mainargs_context.hpp"
#include "host_services.hpp"
namespace mw34::m4_crt_filename {
inline constexpr unsigned buffer=0x7803b3f0,capacity=260,commandline=0x78037174,stop_pc=0x7800bbd6;
struct LastErrorBoundary {
 unsigned saved=GetLastError();unsigned*restored{};
 explicit LastErrorBoundary(unsigned*p=nullptr)noexcept:restored(p){}
 ~LastErrorBoundary()noexcept{SetLastError(saved);if(restored)*restored=GetLastError();}
};
struct Witness {
 unsigned capacity{},incoming_error{},result{},last_error{};
 std::array<std::byte,260>before{},after{};
};
inline Witness native_filename(unsigned size,unsigned incoming,std::span<const std::byte,260>seed,FARPROC procedure){
 Witness w{};w.capacity=size;w.incoming_error=incoming;std::copy(seed.begin(),seed.end(),w.before.begin());w.after=w.before;
 if(size>260||!procedure)throw std::invalid_argument("Bounded actual filename API witness");
 using Function=DWORD(WINAPI*)(HMODULE,LPSTR,DWORD);SetLastError(incoming);
 w.result=reinterpret_cast<Function>(procedure)(nullptr,reinterpret_cast<char*>(w.after.data()),size);
 w.last_error=GetLastError(); // Capture immediately; metadata queries occur afterwards.
 if(w.result>size)throw std::runtime_error("Actual filename result exceeds supplied capacity");
 return w;
}
struct Binding {
 m4_crt_entry_mainargs::Context&context;unsigned control{},incoming_error{};
 unsigned frame{},result{},last_error{},caller_error{},restored_error{},stage{},hook_count{},fault_pc{},fault_address{};
 bool used{},active{},api_called{},stored{},returned{},stopped{},failed{};const char*reason{};
 Witness witness{};m4_crt_fdiv::HostIdentity api_before{},api_after{};m4_crt_fdiv::ModuleIdentity module_before{},module_after{};
 void(*extra)(Binding&,unsigned){}; // 1 before API,2 API witnessed,3 buffer stored,4 RET published,5 before unresolved read.
 explicit Binding(m4_crt_entry_mainargs::Context&c,unsigned mode=0,unsigned error=0):context(c),control(mode),incoming_error(error){}
 void first(const char*,unsigned,unsigned);
 [[noreturn]]void deny(const char*,unsigned=0,unsigned=m4_crt_entry_mainargs::import_call);
 void guard();void closure(State*,unsigned);void hook(unsigned);void invoke(State*,unsigned,void*);
 unsigned consume(unsigned,void*);
 const Witness&actual_witness()const noexcept{return actual_witness_;}
 private:
 Witness actual_witness_{};unsigned admitted_frame_{};std::array<std::byte,3504>return_state_{};std::array<std::byte,512>return_fx_{};
 void witness_closure(unsigned);
};
inline thread_local Binding*binding{};
inline thread_local Binding*admitted_binding{};
inline Binding*current(m4_crt_entry_mainargs::Context&c){
 if(!binding||binding!=admitted_binding)c.deny("Exact admitted current filename side binding required",m4_crt_entry_mainargs::import_slot,m4_crt_entry_mainargs::import_call);
 if(&binding->context!=&c)c.deny("Filename side binding cannot use stale mainargs Context",m4_crt_entry_mainargs::import_slot,m4_crt_entry_mainargs::import_call);
 return binding;
}
inline thread_local unsigned outer_error_before{},outer_error_after{};
}
