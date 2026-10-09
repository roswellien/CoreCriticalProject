#pragma once
#include "mainargs_context.hpp"
#include "heap.hpp"
#include "heap_create.hpp"
#include "heap_mode.hpp"
namespace mw34::m4_crt_heap_version {
namespace mg=m4_crt_entry_mainargs;
inline constexpr unsigned fragment=0x7800183c,entry=0x780039bf,site=0x7800183e,ret=0x78001843,api_site=0x780039d0,iat=0x7802e0a8,api_ret=0x780039d6,raw_import=0x3461e;
inline constexpr unsigned global=0x78035000,mode_site=0x780039e3,mode=0x78003a0c,mode_ret=0x780039e8,zero=0x7800cddc,token=0x48450001;
inline constexpr unsigned probe=0x780058b5,probe_site=0x78003a14,probe_ret=0x78003a19,query_site=0x78003a2b,query_iat=0x7802e0a0,query_raw=0x34600,query_ret=0x78003a31,lower_stack=0x20000000;
inline constexpr unsigned branch=0x78003a31,environment=0x78003a4b,cold=0x7800ccc5,epilogue=0x78003a7d,env_site=0x78003a5c,env_iat=0x7802e09c,env_raw=0x345e6,env_ret=0x78003a62,env_name=0x7802e3b8;
extern "C" void*mw34_heap_version_branch_body(State*,unsigned,void*);
extern "C" void*mw34_heap_version_environment_body(State*,unsigned,void*);
extern "C" void*mw34_heap_version_mode1_body(State*,unsigned,void*);
extern "C" void*mw34_heap_version_epilogue_body(State*,unsigned,void*);
struct Binding;
inline thread_local Binding*binding{};
inline thread_local Binding*admitted_binding{};
inline thread_local Binding*owner{};
Binding*current(void*,unsigned=0);bool has_authority()noexcept;
const Binding*capture_for(m4_runtime::Runtime&)noexcept;
void checkpoint(m4_runtime::Runtime&,const char*);
struct Binding {
 m4_runtime::Runtime&runtime;State&state;mg::Context*parent{};
 unsigned control{},probe_frame{},frame{},parent_frame{},access_count{},api_access_count{},event_count{},undefined_count{},stage{},depth{},fault_pc{},fault_address{},caller_error{},restored_error{};
 bool used{},active{},failed{},api_reached{},api_called{},registered{},api_returned{},published{},mode_reached{},zero_reached{},probe_reached{},probe_returned{},query_reached{},cleanup_succeeded{};const char*reason{};
 std::array<mg::Access,64>accesses{};std::array<mg::Access,8>api_accesses{};std::array<mg::Event,16>events{};
 std::array<unsigned,8>undefined_sites{},scheduler{};
 unsigned query_frame{},query_pointer{},query_result{},output_count{};
 bool query_called{},query_preflight{},query_output_complete{},query_returned{},selector_returned{},environment_reached{};
 std::array<std::uint64_t,20>query_witness{};std::array<std::byte,148>query_input{},query_output{};
 std::array<mg::Access,64>output_accesses{};
 m4_cmd_native::ApiIdentity query_before,query_after;
 // Fixed uint64 witness: v,injected_zero,called,flags,initial,max,handle,token,
 // incoming_error,API_error,restored_error,registry_handle,frame,return,ESP,EIP.
 std::array<std::uint64_t,16>witness{};
 // v,owner,generation,token,handle,acquired,registered,live,create_calls,
 // destroy_calls,destroy_ok,destroy_error,cleanup_attempts,cleanup_skips,
 // rollback,finalized,destroy_input_handle,lookup_denials.
 std::array<std::uint64_t,18>registry{};
 m4_cmd_native::ApiIdentity create_before,create_after,destroy_before,destroy_after;
 void(*extra)(Binding&,unsigned){};
 Binding(mg::Context&,std::span<const std::byte>,unsigned=0);
 ~Binding()noexcept;
 Binding(const Binding&)=delete;Binding&operator=(const Binding&)=delete;
 void first(const char*,unsigned=0,unsigned=0);[[noreturn]]void deny(const char*,unsigned=0,unsigned=0);
 void guard();void source_identity();[[noreturn]]void start(mg::Context&);
 unsigned read32(unsigned);void write32(unsigned,unsigned);unsigned char undefined();void*called(State*,unsigned,void*);void*returned(State*,unsigned,void*);
 std::span<const std::byte>initial_lower_stack()const noexcept{return lower_initial_;}
 void*missing(State*,unsigned,void*);void*jumped(State*,unsigned,void*);[[noreturn]]void unsupported(unsigned,const char*);
 bool owns_token(unsigned);bool live_handle()const noexcept{return owned_handle_!=nullptr;}
 std::uint64_t known_handle()const noexcept{return acquired_handle_;}
 unsigned actual_create_calls()const noexcept{return create_called_;}
 unsigned actual_destroy_calls()const noexcept{return destroy_calls_;}
 unsigned successful_destroy_calls()const noexcept{return destroy_successes_;}
 bool token_valid(unsigned value)const noexcept{return authority_is_current()&&owned_handle_&&registered_&&value==token&&guest_result_==token;}
 void test_cleanup();
 private:
 mg::Context*const admitted_parent_;
 const unsigned admitted_control_;
 unsigned admitted_probe_frame_{},mode_ebp_{},mode_ebx_{},probe_ecx_{};
 unsigned admitted_frame_{},admitted_parent_frame_{},guest_result_{};bool started_{},registered_{},create_called_{},cleanup_skip_used_{};
 std::thread::id thread_=std::this_thread::get_id();
 HANDLE owned_handle_{};std::uint64_t acquired_handle_{},destroy_input_handle_{};unsigned destroy_calls_{},destroy_successes_{},destroy_error_{},cleanup_attempts_{},cleanup_skips_{},lookup_denials_{};bool rollback_{},finalized_{};
 std::array<std::byte,512>entry_fx_{};std::array<std::vector<std::byte>,11>source_;std::array<std::byte,4096>lower_initial_{},lower_expected_{};
 unsigned lower_word(unsigned)const;unsigned query_word(unsigned)const;
 std::array<std::byte,148>query_input_private_{},query_output_private_{},query_expected_{};
 unsigned query_frame_private_{},query_pointer_private_{},query_result_private_{},output_count_private_{},query_api_error_{},query_restored_error_{};
 bool query_bound_{},query_called_private_{},query_preflight_private_{},query_complete_private_{},query_returned_private_{},selector_returned_private_{},environment_private_{};
 void query();void query_return();void query_snapshot()noexcept;void admit_current();void hook(unsigned);void stable_hook(unsigned,bool=false,bool=false);
 void record(unsigned,unsigned,unsigned);void event(unsigned,unsigned,unsigned,unsigned);
 bool authority_is_current()const noexcept;
 void api();void api_return();void cleanup();bool release_noexcept(bool=false)noexcept;void registry_snapshot()noexcept;
};
static_assert(sizeof(HANDLE)==8&&sizeof(std::uintptr_t)==8);
}
