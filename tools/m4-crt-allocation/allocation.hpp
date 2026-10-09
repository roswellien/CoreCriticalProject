#pragma once
#include "mainargs_context.hpp"
#include "heap.hpp"
#include "heap_create.hpp"
#include "heap_mode.hpp"
#include "heap_version.hpp"
#include "heap_return.hpp"
namespace mw34::m4_crt_allocation {
namespace mg=m4_crt_entry_mainargs;
inline constexpr unsigned fragment=0x7800183c,entry=0x780039bf,site=0x7800183e,ret=0x78001843,api_site=0x780039d0,iat=0x7802e0a8,api_ret=0x780039d6,raw_import=0x3461e;
inline constexpr unsigned global=0x78035000,mode_site=0x780039e3,mode=0x78003a0c,mode_ret=0x780039e8,zero=0x7800cddc,token=0x48450001;
inline constexpr unsigned probe=0x780058b5,probe_site=0x78003a14,probe_ret=0x78003a19,query_site=0x78003a2b,query_iat=0x7802e0a0,query_raw=0x34600,query_ret=0x78003a31,lower_stack=0x20000000;
inline constexpr unsigned branch=0x78003a31,environment=0x78003a4b,cold=0x7800ccc5,epilogue=0x78003a7d,env_site=0x78003a5c,env_iat=0x7802e09c,env_raw=0x345e6,env_ret=0x78003a62,env_name=0x7802e3b8;
inline constexpr unsigned caller_cleanup=0x78001843,caller_stop=0x7800184c;
inline constexpr unsigned malloc_entry=0x780012b3,size_entry=0x780012c5,worker_entry=0x780012e3,free_entry=0x78001390;
inline constexpr unsigned malloc_marker=0xffffffe0,free_marker=0xffffffd0,allocation_address=0x30000000;
inline constexpr unsigned alloc_site=0x7800137f,alloc_iat=0x7802e094,alloc_raw=0x345c6,alloc_return=0x78001385;
inline constexpr unsigned free_site=0x78001430,free_iat=0x7802e090,free_raw=0x345ba,free_return=0x78001436;
extern "C" void*mw34_heap_version_branch_body(State*,unsigned,void*);
extern "C" void*mw34_heap_version_environment_body(State*,unsigned,void*);
extern "C" void*mw34_heap_version_mode1_body(State*,unsigned,void*);
extern "C" void*mw34_heap_version_epilogue_body(State*,unsigned,void*);
extern "C" void*mw34_allocation_caller_body(State*,unsigned,void*);
extern "C" void*mw34_allocation_malloc_body(State*,unsigned,void*);
extern "C" void*mw34_allocation_size_body(State*,unsigned,void*);
extern "C" void*mw34_allocation_worker_body(State*,unsigned,void*);
extern "C" void*mw34_allocation_round_body(State*,unsigned,void*);
extern "C" void*mw34_allocation_null_body(State*,unsigned,void*);
extern "C" void*mw34_allocation_free_body(State*,unsigned,void*);
extern "C" void*mw34_allocation_freecold_body(State*,unsigned,void*);
extern "C" void*mw34_allocation_alloc_tail_body(State*,unsigned,void*);
extern "C" void*mw34_allocation_worker_epilogue_body(State*,unsigned,void*);
extern "C" void*mw34_allocation_free_tail_body(State*,unsigned,void*);
extern "C" void*mw34_allocation_free_epilogue_body(State*,unsigned,void*);
extern "C" void*mw34_allocation_size_ret_body(State*,unsigned,void*);
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
 std::array<mg::Access,128>accesses{};std::array<mg::Access,8>api_accesses{};std::array<mg::Event,48>events{};
 std::array<unsigned,32>undefined_sites{};std::array<unsigned,8>scheduler{};
 unsigned query_frame{},query_pointer{},query_result{},output_count{};
 bool selector_unwound{},mode_store_before{},mode_published{},initializer_return_before{},initializer_returned{};unsigned mode_value{};
 std::array<unsigned,8>progress()const noexcept;
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
 unsigned requested_size{24},allocation_phase{},allocation_guest{},allocation_extent{},allocation_output_count{},external_count{};
 bool caller_cleaned{},malloc_returned{},client_verified{},free_returned{},null_free_returned{},batch_complete{};
 std::array<std::uint64_t,24>allocation_registry{};
 std::array<std::uint64_t,16>allocation_witness{};
 std::array<mg::Access,16>external_accesses{};
 std::array<std::array<unsigned,8>,8>external_projections{};
 std::vector<std::byte>allocation_initial,allocation_pattern;
 m4_cmd_native::ApiIdentity alloc_before,alloc_after,free_before,free_after;
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
 void configure_request(unsigned);
 bool allocation_token_valid(unsigned)const noexcept;
 std::uint64_t known_allocation()const noexcept{return acquired_allocation_;}
 unsigned actual_alloc_calls()const noexcept{return alloc_calls_;}
 unsigned actual_free_calls()const noexcept{return free_calls_;}
 unsigned successful_free_calls()const noexcept{return free_successes_;}
 std::array<unsigned,16>allocation_progress()const noexcept;
 std::span<const std::byte>allocation_backing()const noexcept{return allocation_expected_;}
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
 bool selector_unwound_private_{},mode_store_before_private_{},mode_published_private_{},initializer_return_before_private_{},initializer_returned_private_{};unsigned mode_value_private_{};
 bool query_bound_{},query_called_private_{},query_preflight_private_{},query_complete_private_{},query_returned_private_{},selector_returned_private_{},environment_private_{};
 void query();void query_return();void query_snapshot()noexcept;void admit_current();void hook(unsigned);void stable_hook(unsigned,bool=false,bool=false);
 void record(unsigned,unsigned,unsigned);void event(unsigned,unsigned,unsigned,unsigned);
 bool authority_is_current()const noexcept;
 void api();void api_return();void cleanup();bool release_noexcept(bool=false)noexcept;void registry_snapshot()noexcept;
 unsigned request_private_{24},allocation_phase_private_{},allocation_extent_private_{},allocation_output_private_{},external_count_private_{},allocator_frame_{},fs_previous_{},alloc_calls_{},free_calls_{},free_successes_{},cleanup_free_calls_{},cleanup_free_successes_{},allocation_denials_{};
 unsigned fs_expected_{},allocator_start_access_{},allocator_depth_{},allocator_api_frame_{},allocator_saved_ebp_{},allocator_saved_ebx_{},allocator_saved_esi_{},allocator_saved_edi_{},allocator_newmode_{},alloc_error_before_{},alloc_error_after_{},alloc_error_restored_{},free_error_before_{},free_error_after_{},free_error_restored_{},free_result_{};
 unsigned allocator_plan_index_{},external_projection_count_{},allocation_guest_private_{};
 std::vector<mg::Access>allocator_plan_;
 std::array<std::uint64_t,16>allocation_witness_private_{};
 bool caller_cleaned_private_{},malloc_returned_private_{},client_verified_private_{},free_returned_private_{},null_free_returned_private_{},batch_complete_private_{},allocation_mapped_{},operation_returned_{};
 void*owned_allocation_{};std::uint64_t acquired_allocation_{};
 std::vector<std::byte>allocation_initial_private_,allocation_pattern_private_,allocation_expected_;
 std::array<std::byte,4096>upper_initial_{},upper_expected_{};
 std::vector<std::pair<unsigned,std::vector<std::byte>>>allocator_sources_;
 void allocator_snapshot()noexcept;void allocator_guard();void allocator_batch();void external_call(unsigned,unsigned,unsigned);
 void make_malloc_plan();void make_free_plan(unsigned);void committed_stack_write(unsigned,unsigned);
 void client_pattern();void allocation_api();void allocation_api_return();void free_api();void free_api_return();
 bool release_allocation_noexcept()noexcept;
 unsigned allocator_read32(unsigned);void allocator_write32(unsigned,unsigned);unsigned char allocator_undefined();
 void*allocator_called(State*,unsigned,void*);void*allocator_returned(State*,unsigned,void*);void*allocator_missing(State*,unsigned,void*);
};
static_assert(sizeof(HANDLE)==8&&sizeof(std::uintptr_t)==8);
}
