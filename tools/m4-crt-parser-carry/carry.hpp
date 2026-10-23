#pragma once
#include "filename.hpp"
#include "host_input.hpp"
namespace mw34::m4_crt_commandline_carry {
namespace mg=m4_crt_entry_mainargs;
namespace old=m4_cmd_native;
inline constexpr unsigned writer=0x7800188c,iat=0x7802e034,global=0x78037174,ret=0x78001892,end=0x78001897,buffer=0x33000000,pgmptr=0x7803b3e0,parser_site=0x7800bbf7,parser=0x7800bc48,parser_ret=0x7800bbfc;
extern "C" void*mw34_carry_cmd_writer_body(State*,unsigned,void*) noexcept(false);
struct Binding;
inline thread_local Binding*binding{};
inline thread_local Binding*admitted_binding{};
inline thread_local Binding*producer_owner{};
Binding*current_producer(void*,unsigned);
void outer_owner_guard(mg::Context&);
void checkpoint(m4_runtime::Runtime&,const char*);
struct Binding {
 mg::Context&context;unsigned control{};
 unsigned frame{},saved_pc{},saved_runtime_eax{},raw{},size{},access_count{},event_count{},consumer_access_count{},stage{},depth{},fault_pc{},fault_address{},caller_error{},restored_error{};
 bool used{},active{},api_called{},mapped{},published{},captured{},carried{},consumed{},parser_reached{},failed{};const char*reason{};
 std::array<mg::Access,16>accesses{};std::array<mg::Access,16>consumer_accesses{};std::array<mg::Event,16>events{};
 old::HostInput host{};
 void(*extra)(Binding&,unsigned){}; // 1 projected,2 API before,3 API after,4 owned-copy,5 writer end,6 consumer before,7 access,8 parser.
 explicit Binding(mg::Context&c,std::span<const std::byte>provider,unsigned mode=0):context(c),control(mode){old::Provider p(provider);raw=p.dword({iat});if(raw!=0x3442e)throw std::invalid_argument("Exact command-line raw provider IAT");unsigned count{};for(const auto&i:c.runtime.image_metadata().imports)if(c.runtime.image_metadata().image_base+i.iat_rva==old::game_iat.value){if(!i.name||*i.name!="_acmdln"||i.library!="MSVCRT.dll")throw std::invalid_argument("Exact game command-line data owner");game_raw_=i.original_iat_value;++count;}if(count!=1)throw std::invalid_argument("Unique command-line game data owner");}
 ~Binding()noexcept{if(owned_mapping_){try{context.runtime.memory().unmap({buffer});}catch(...){}}}
 Binding(const Binding&)=delete;Binding&operator=(const Binding&)=delete;
 void first(const char*,unsigned=0,unsigned=0);[[noreturn]]void deny(const char*,unsigned=0,unsigned=0);
 void guard(bool);void source_identity();void hook(unsigned);void event(unsigned,unsigned,unsigned,unsigned);
 void initialize();unsigned read(unsigned);void write(unsigned,unsigned);void invoke(State*,unsigned,void*);void finish(State*,unsigned,void*);
 unsigned consume(unsigned,void*);unsigned char read8(unsigned,void*);void consumer_write(unsigned,unsigned,void*);[[noreturn]]void parser_stop(State*,unsigned,void*);void*parser_call(State*,unsigned,void*);unsigned post_parser_read(unsigned,void*);void post_parser_write(unsigned,unsigned,void*);[[noreturn]]void malloc_stop(State*,unsigned,void*);
 bool parser_returned{};unsigned parser_numargs{},parser_numchars{},parser_undefined{},post_reads{},post_writes{},malloc_size{};
 bool ready()const;const std::vector<std::byte>&actual_bytes()const noexcept{return actual_bytes_;}
 private:
 unsigned game_raw_{},admitted_frame_{},admitted_pc_{},admitted_eax_{};std::thread::id thread_=std::this_thread::get_id();std::vector<std::byte>actual_bytes_;old::HostInput actual_host_{};
 std::array<std::byte,3504>entry_state_{};std::array<std::byte,512>entry_fx_{};m4_runtime::Cpu32 entry_cpu_{};
 unsigned admitted_size_{};bool owned_mapping_{};
 void memory_access(unsigned,unsigned,unsigned,unsigned,bool=false);void call_closure(State*,unsigned,void*);void consumer_guard(void*);void lifecycle(unsigned);void stable_hook(unsigned);void admit_current();
};
inline Binding*current(mg::Context&c){if(!binding||binding!=admitted_binding)c.deny("Exact admitted current command-line side binding required",global,0x7800bbd6);if(&binding->context!=&c)c.deny("Command-line side binding cannot use stale mainargs Context",global,0x7800bbd6);return binding;}
}
