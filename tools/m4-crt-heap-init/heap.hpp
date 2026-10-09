#pragma once
#include "mainargs_context.hpp"
namespace mw34::m4_crt_heap_init {
namespace mg=m4_crt_entry_mainargs;
inline constexpr unsigned fragment=0x7800183c,entry=0x780039bf,site=0x7800183e,ret=0x78001843,api_site=0x780039d0,iat=0x7802e0a8,api_ret=0x780039d6,raw_import=0x3461e;
extern "C" void*mw34_heap_init_fragment_body(State*,unsigned,void*)noexcept(false);
extern "C" void*mw34_heap_init_provider_body(State*,unsigned,void*)noexcept(false);
struct Binding;
inline thread_local Binding*binding{};
inline thread_local Binding*admitted_binding{};
inline thread_local Binding*owner{};
Binding*current(void*,unsigned=0);bool has_authority()noexcept;
void checkpoint(m4_runtime::Runtime&,const char*);
struct Binding {
 m4_runtime::Runtime&runtime;State&state;mg::Context*parent{};
 unsigned control{},frame{},parent_frame{},access_count{},event_count{},undefined_count{},stage{},depth{},fault_pc{},fault_address{},caller_error{},restored_error{};
 bool used{},active{},failed{},api_reached{};const char*reason{};
 std::array<mg::Access,32>accesses{};std::array<mg::Event,8>events{};std::array<unsigned,8>undefined_sites{};std::array<unsigned,8>scheduler{};
 void(*extra)(Binding&,unsigned){}; // 1 projected,2 completed access,3 API frontier,4 terminal.
 Binding(mg::Context&,std::span<const std::byte>,unsigned=0);
 Binding(const Binding&)=delete;Binding&operator=(const Binding&)=delete;
 void first(const char*,unsigned=0,unsigned=0);[[noreturn]]void deny(const char*,unsigned=0,unsigned=0);
 void guard();void source_identity();[[noreturn]]void start(mg::Context&);
 unsigned read32(unsigned);void write32(unsigned,unsigned);unsigned char undefined();void*called(State*,unsigned,void*);
 [[noreturn]]void unsupported(unsigned,const char*);
 private:
 mg::Context*const admitted_parent_;
 unsigned admitted_control_{},admitted_frame_{},admitted_parent_frame_{};bool started_{};std::thread::id thread_=std::this_thread::get_id();
 std::array<std::byte,512>entry_fx_{};std::array<std::vector<std::byte>,2>source_;
 void admit_current();void hook(unsigned);void stable_hook(unsigned,bool=false);void record(unsigned,unsigned,unsigned);void event(unsigned,unsigned,unsigned,unsigned);
};
}
