#pragma once
#include "carry.hpp"
namespace mw34::m4_crt_parser_prefix {
namespace mg=m4_crt_entry_mainargs;
namespace cm=m4_crt_commandline_carry;
inline constexpr unsigned entry=0x7800bc48,site=0x7800bbf7,ret=0x7800bbfc,stop=0x7800bce6,table=0x780379e1;
inline constexpr char source_sha[]="b372b4c114b8ecb170208ad508f2541c73262c3b44cfa2e7626e06a5be61fd8b";
extern "C" void*mw34_mainargs_normal_parser_body(State*,unsigned,void*) noexcept(false);
struct Binding;
inline thread_local Binding*binding{};
inline thread_local Binding*admitted_binding{};
inline thread_local Binding*owner{};
Binding*current(void*,unsigned=0);
void checkpoint(m4_runtime::Runtime&,const char*);
struct Binding {
 mg::Context&context;cm::Binding&commandline;unsigned control{},frame{},parent_frame{},access_count{},event_count{},undefined_count{},stage{},depth{},fault_pc{},fault_address{};
 bool used{},active{},failed{},locale_reached{};const char*reason{};
 std::array<mg::Access,32>accesses{};std::array<mg::Event,8>events{};std::array<unsigned,8>undefined_sites{};
 void(*extra)(Binding&,unsigned){}; // 1 projected,2 successful access,3 locale frontier,4 terminal after.
 Binding(mg::Context&,cm::Binding&,std::span<const std::byte>,unsigned=0);
 Binding(const Binding&)=delete;Binding&operator=(const Binding&)=delete;
 void first(const char*,unsigned=0,unsigned=0);[[noreturn]]void deny(const char*,unsigned=0,unsigned=0);
 void guard();void source_identity();[[noreturn]]void enter(State*,unsigned,void*);unsigned read32(unsigned);void write32(unsigned,unsigned);unsigned char read8(unsigned);unsigned char undefined();
 [[noreturn]]void unsupported(unsigned,const char*);
 private:
 unsigned admitted_frame_{},admitted_parent_{},admitted_control_{};bool started_{};std::thread::id thread_=std::this_thread::get_id();std::array<unsigned,4>saved_{};
 std::vector<std::byte>source_;std::array<std::byte,512>entry_fx_{};unsigned last_value_{};
 void admit_current();void call_closure(State*,unsigned,void*);void record(unsigned,unsigned,unsigned,unsigned);void hook(unsigned);void stable_hook(unsigned,bool=false);void event(unsigned,unsigned,unsigned,unsigned);
};
}
