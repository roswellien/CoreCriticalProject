#pragma once
#include "mainargs_context.hpp"
#include "heap.hpp"
#include "heap_create.hpp"
#include "heap_mode.hpp"
#include "heap_version.hpp"
#include "heap_return.hpp"
#include <functional>
namespace mw34::m4_crt_locale_batch {
namespace mg=m4_crt_entry_mainargs;
struct Completion final {};
struct SourceAccess {unsigned pc,address;std::uint64_t value;unsigned bytes,write;};
struct OperandSpec {unsigned kind,width,reg,segment,base,index,scale;int disp;std::uint64_t imm;unsigned access;};
struct SourceInstruction {unsigned pc,length;const char*mnemonic;std::array<OperandSpec,3>operands;unsigned count,repeat;};
struct SourceSpan {unsigned address,bytes,permissions;const char*sha;};
struct SourcePage {unsigned address,permissions;};
struct SourceApi {unsigned site,slot,raw,argc;const char*name;unsigned tail;};
const SourceInstruction*instruction(unsigned)noexcept;
std::span<const SourceSpan>source_spans()noexcept;
std::span<const SourcePage>source_pages()noexcept;
std::span<const unsigned>generated_undefined_sites()noexcept;
std::span<const SourceApi>source_api_contracts()noexcept;
bool has_body(unsigned)noexcept;
struct ApiCapture {
 std::array<std::uint64_t,32>words{};
 m4_cmd_native::ApiIdentity before,after;
 std::array<std::byte,4624>export_before{},export_after{};
 std::vector<std::vector<std::byte>>inputs,outputs;
 std::vector<std::array<unsigned,4>>buffers;
};
using CaptureSink=void(*)(std::string_view,std::span<const std::byte>,void*);
// Root preparation supplies only exact literal entry routing, without source
// State projection or an invented CALL/RET.
void*dispatch_body(unsigned,State*,void*);
inline constexpr unsigned fragment=0x7800183c,entry=0x780039bf,site=0x7800183e,ret=0x78001843,api_site=0x780039d0,iat=0x7802e0a8,api_ret=0x780039d6,raw_import=0x3461e;
inline constexpr unsigned global=0x78035000,mode_site=0x780039e3,mode=0x78003a0c,mode_ret=0x780039e8,zero=0x7800cddc,token=0x48450001;
inline constexpr unsigned probe=0x780058b5,probe_site=0x78003a14,probe_ret=0x78003a19,query_site=0x78003a2b,query_iat=0x7802e0a0,query_raw=0x34600,query_ret=0x78003a31,lower_stack=0x20000000;
inline constexpr unsigned branch=0x78003a31,environment=0x78003a4b,cold=0x7800ccc5,epilogue=0x78003a7d,env_site=0x78003a5c,env_iat=0x7802e09c,env_raw=0x345e6,env_ret=0x78003a62,env_name=0x7802e3b8;
inline constexpr unsigned caller_cleanup=0x78001843,caller_stop=0x7800184c;
inline constexpr unsigned malloc_entry=0x780012b3,size_entry=0x780012c5,worker_entry=0x780012e3,free_entry=0x78001390;
inline constexpr unsigned malloc_marker=0xffffffe0,free_marker=0xffffffd0,allocation_address=0x31000000;
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
struct NativeExportProof {
 std::array<std::uint64_t,6>scalar{}; // v,named module,target,named resolved,owner,owner resolved
 std::array<char,32>requested{};std::array<char,256>forwarder{};std::array<char,64>owner_export{};
 std::array<char,64>named_sha{},owner_sha{};std::array<wchar_t,1024>named_path{},owner_path{};
 bool operator==(const NativeExportProof&)const=default;
};
static_assert(sizeof(NativeExportProof)==4624);
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
 std::array<mg::Access,128>accesses{};std::array<mg::Access,1024>api_accesses{};std::array<mg::Event,1024>events{};
 std::array<unsigned,8192>undefined_sites{};std::array<unsigned,8>scheduler{};
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
 m4_cmd_native::ApiIdentity alloc_before,alloc_after,free_before,free_after;NativeExportProof alloc_export_before,alloc_export_after,free_export_before,free_export_after;
 void(*extra)(Binding&,unsigned){};
 Binding(mg::Context&,std::span<const std::byte>,unsigned=0);
 ~Binding()noexcept;
 Binding(const Binding&)=delete;Binding&operator=(const Binding&)=delete;
 void first(const char*,unsigned=0,unsigned=0);[[noreturn]]void deny(const char*,unsigned=0,unsigned=0);
 void guard();void source_identity();void start(mg::Context&);
 void suspend_for_commandline();void resume_mainargs(mg::Context&);void finish();
 std::uint64_t read(unsigned,unsigned);void write(unsigned,std::uint64_t,unsigned);
 void dump(CaptureSink,void*)const;
 std::array<unsigned,32>summary()const noexcept;
 bool completed()const noexcept{return builder_complete_;}
 bool default_locale_ready()const noexcept{return locale_complete_;}
 bool static_locks_ready()const noexcept{return static_complete_;}
 unsigned live_allocations()const noexcept;unsigned live_critical_sections()const noexcept;
 std::span<const SourceAccess>source_ledger()const noexcept{return source_accesses_;}
 std::span<const SourceAccess>transport_ledger()const noexcept{return api_transports_;}
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
 bool query_return_read_private_{};bool query_bound_{},query_called_private_{},query_preflight_private_{},query_complete_private_{},query_returned_private_{},selector_returned_private_{},environment_private_{};
 void query();void query_return();void query_snapshot()noexcept;void admit_current();void hook(unsigned);void stable_hook(unsigned,bool=false,bool=false);
 void record(unsigned,unsigned,unsigned);void event(unsigned,unsigned,unsigned,unsigned);
 bool authority_is_current()const noexcept;
 void api();void api_return();void cleanup();bool release_noexcept(bool=false)noexcept;void registry_snapshot()noexcept;
 unsigned request_private_{24},allocation_phase_private_{},allocation_extent_private_{},allocation_output_private_{},external_count_private_{},allocator_frame_{},fs_previous_{},alloc_calls_{},free_calls_{},free_successes_{},cleanup_free_calls_{},cleanup_free_successes_{},allocation_denials_{};
 unsigned fs_expected_{},allocator_start_access_{},allocator_depth_{},allocator_api_frame_{},allocator_saved_ebp_{},allocator_saved_ebx_{},allocator_saved_esi_{},allocator_saved_edi_{},allocator_newmode_{},alloc_error_before_{},alloc_error_after_{},alloc_error_restored_{},free_error_before_{},free_error_after_{},free_error_restored_{},free_result_{};
 unsigned allocator_plan_index_{},external_projection_count_{},allocation_guest_private_{};
 std::string host_fault_reason_private_;NativeExportProof alloc_export_before_private_,alloc_export_after_private_,free_export_before_private_,free_export_after_private_;
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
 struct Allocation {
  unsigned guest{},requested{},extent{},mapped_bytes{},generation{},kind{};
  void*native{};std::uint64_t acquired{};bool mapped{},source_freed{},cleanup_freed{};
  std::vector<std::byte>initial,expected;
 };
 struct CriticalSection {
  unsigned guest{},generation{},enters{},leaves{},depth{},initializes{},deletes{};
  std::thread::id owner_thread{};bool initialized{},deleted{};
  CRITICAL_SECTION native{};
 };
 struct CallFrame {unsigned entry{},frame{},return_pc{},site{},ebp{},ebx{},esi{},edi{},kind{};};
 std::vector<std::unique_ptr<Allocation>>owned_allocations_;
 std::vector<std::unique_ptr<CriticalSection>>owned_sections_;
 std::vector<CallFrame>calls_;
 std::vector<SourceAccess>source_accesses_,api_transports_,research_accesses_;
 std::vector<std::array<unsigned,8>>research_projections_;
 std::vector<ApiCapture>native_apis_;
 std::vector<std::pair<unsigned,std::vector<std::byte>>>locale_sources_;
 std::vector<std::pair<unsigned,std::array<std::byte,4096>>>expected_pages_;
 std::vector<unsigned>initial_pages_;
 std::vector<std::pair<unsigned,std::size_t>>undefined_occurrences_;
 unsigned batch_phase_{},generation_{},allocation_cursor_{0x31000000},allocations_created_{},allocations_freed_{},allocations_cleanup_freed_{},sections_initialized_{},sections_deleted_{},parser_passes_{},argc_{},argv_{},caller_pc_{},caller_sp_{},last_source_pc_{},body_depth_{},query_output_committed_{},source_budget_{200000};
 unsigned program_input_{},program_extent_{},startup_value_{},builder_frame_{},sizing_chars_{},sizing_slots_{};
 unsigned parser_vector_{},parser_vector_end_{},parser_chars_{},parser_chars_end_{};
 bool static_complete_{},locale_complete_{},builder_complete_{},suspended_{},finished_{},api_active_{},control_used_{};
 std::string diagnostic_;
 std::array<std::byte,4096>table_before_{},table_after_{};
 std::array<unsigned,5>tib_expected_{};
 void locale_batch();void external_source_call(unsigned,unsigned);void admit_commandline();
 void batch_guard();void batch_source_identity();void expected_store(unsigned,const void*,unsigned);
 void source_access(unsigned,std::uint64_t,unsigned,bool);void check_source_access(unsigned,std::uint64_t,unsigned,bool);
 void*batch_called(State*,unsigned,void*);void*batch_returned(State*,unsigned,void*);void*batch_missing(State*,unsigned,void*);
 unsigned char batch_undefined();void actual_api(unsigned,unsigned,unsigned);
 void api_return(unsigned,unsigned,unsigned);void api_transfer(unsigned,std::span<const std::byte>);
 std::vector<std::byte>guest_bytes(unsigned,unsigned);void preflight_write(unsigned,unsigned);
 Allocation*allocation_for(unsigned,unsigned=1)noexcept;CriticalSection*section_for(unsigned)noexcept;
 bool cleanup_sections_noexcept()noexcept;bool cleanup_allocations_noexcept()noexcept;
 template<class F>bool lifecycle_api(const char*,unsigned,unsigned,std::uint64_t,F&&)noexcept;
 void batch_control(unsigned);
 void native_allocate(unsigned,unsigned,unsigned);void native_free(unsigned,unsigned,unsigned);
 void native_section(unsigned,unsigned,unsigned);void native_nls(unsigned,unsigned,unsigned);
};
static_assert(sizeof(HANDLE)==8&&sizeof(std::uintptr_t)==8);
}
