#pragma once
#include "mainargs_context.hpp"
namespace mw34::m4_crt_locale_default {
namespace mg=m4_crt_entry_mainargs;
inline constexpr unsigned entry=0x78003dd2,setmbcp=0x78003ddb,lock=0x78001055,malloc_entry=0x780012b3;
inline constexpr unsigned stub_call=0x78003dd4,stub_ret=0x78003dd9,lock_call=0x78003de6,lock_ret=0x78003deb,malloc_call=0x7800107b,malloc_ret=0x78001080,lock_slot=0x7803708c;
extern "C" void*mw34_locale_default_mbinit_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_locale_default_setmbcp_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_locale_default_lock_body(State*,unsigned,void*) noexcept(false);
struct Binding;
inline thread_local Binding*binding{};
inline thread_local Binding*admitted_binding{};
inline thread_local Binding*owner{};
Binding*current(void*,unsigned=0);
bool has_authority()noexcept;
void checkpoint(m4_runtime::Runtime&,const char*);
struct Binding {
 m4_runtime::Runtime&runtime;State&state;mg::Context*parent{};
 unsigned control{},frame{},parent_frame{},access_count{},event_count{},stage{},depth{},fault_pc{},fault_address{},caller_error{},restored_error{};
 bool used{},active{},failed{},malloc_reached{};const char*reason{};
 std::array<mg::Access,32>accesses{};std::array<mg::Event,8>events{};
 std::array<unsigned,10>scheduler{}; // separate authored State projection and host store.
 void(*extra)(Binding&,unsigned){}; // 1 projected,2 successful source access,3 malloc frontier,4 terminal.
 Binding(mg::Context&,std::span<const std::byte>,unsigned=0);
 Binding(const Binding&)=delete;Binding&operator=(const Binding&)=delete;
 void first(const char*,unsigned=0,unsigned=0);[[noreturn]]void deny(const char*,unsigned=0,unsigned=0);
 void guard();void source_identity();[[noreturn]]void start(mg::Context&);
 unsigned read32(unsigned);void write32(unsigned,unsigned);void*called(State*,unsigned,void*);
 [[noreturn]]void unsupported(unsigned,const char*);
 private:
 mg::Context*const admitted_parent_;
 unsigned admitted_control_{},admitted_frame_{},admitted_parent_frame_{};bool started_{};std::thread::id thread_=std::this_thread::get_id();
 std::array<unsigned,4>saved_{};std::array<std::byte,512>entry_fx_{};
 std::array<std::vector<std::byte>,3>source_;
 void admit_current();void hook(unsigned);void stable_hook(unsigned,bool=false);void record(unsigned,unsigned,unsigned);void event(unsigned,unsigned,unsigned,unsigned);
};
}
