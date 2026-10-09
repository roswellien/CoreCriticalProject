"""Extend only the fresh allocation binding's inherited initializer path."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
 p=HERE/'allocation_binding.inc';s=p.read_text()
 def rep(a,b):
  nonlocal s
  assert s.count(a)==1,(a[:100],s.count(a));s=s.replace(a,b)
 rep('namespace {thread_local Binding*authority{};thread_local Binding*capture_binding{};}',
     'namespace {thread_local Binding*authority{};thread_local Binding*capture_binding{};struct CallerComplete{};}')
 rep('runtime.memory().read({lower_stack},lower_initial_);lower_expected_=lower_initial_;registry_snapshot();',
 '''runtime.memory().read({lower_stack},lower_initial_);lower_expected_=lower_initial_;
 runtime.memory().read({0x20001000},upper_initial_);upper_expected_=upper_initial_;
 if(state.addr.fs_base.dword!=runtime.fs_base().value)throw std::invalid_argument("Exact carried guest FS base required");
 fs_previous_=fs_expected_=runtime.memory().load<unsigned>(runtime.fs_base());
 for(auto [a,n]:std::array<std::pair<unsigned,unsigned>,8>{{{caller_cleanup,9},{malloc_entry,18},{size_entry,30},{worker_entry,173},{0x7800cc97,21},{0x7800cc3f,35},{free_entry,177},{0x7800cc39,6}}})allocator_sources_.push_back({a,p.slice({a},n,0x60000000)});
 if(p.dword({alloc_iat})!=alloc_raw||p.dword({free_iat})!=free_raw)throw std::invalid_argument("Exact original HeapAlloc/HeapFree IATs required");
 registry_snapshot();allocator_snapshot();''')
 rep('Binding::~Binding()noexcept{if(owned_handle_)', 'Binding::~Binding()noexcept{if(owned_allocation_)(void)release_allocation_noexcept();if(owned_handle_)')
 # The accepted heap-return owner is now unused, just like the older owners.
 s=s.replace('m4_crt_heap_version::has_authority()||','m4_crt_heap_return::has_authority()||m4_crt_heap_version::has_authority()||')
 rep('void Binding::guard(){admit_current();','void Binding::guard(){admit_current();')
 rep(' const auto old=registry;registry_snapshot();', ' if(allocation_phase_private_)allocator_guard();\n const auto old=registry;registry_snapshot();')
 rep('void Binding::record(unsigned a,unsigned v,unsigned write){', 'void Binding::record(unsigned a,unsigned v,unsigned write){')
 rep('unsigned Binding::read32(unsigned a){guard();source_identity();unsigned pc{},address{},expected{};',
     'unsigned Binding::read32(unsigned a){guard();source_identity();if(allocation_phase_private_>=2)return allocator_read32(a);unsigned pc{},address{},expected{};')
 rep('  else if(pc==env_site){address=env_iat;expected=env_raw;}',
     '  else if(pc==0x78001845&&access_count==35&&allocation_phase_private_==1&&depth==1){address=admitted_frame_+4;expected=1;if(state.gpr.rsp.dword!=admitted_parent_frame_)deny("Genuine caller POP advances ESP before its read",a);}\n  else if(pc==env_site){address=env_iat;expected=env_raw;}')
 rep('void Binding::write32(unsigned a,unsigned v){guard();source_identity();unsigned pc{},address{},expected{};',
     'void Binding::write32(unsigned a,unsigned v){guard();source_identity();if(allocation_phase_private_>=2){allocator_write32(a,v);return;}unsigned pc{},address{},expected{};')
 rep('if(a>=lower_stack&&std::uint64_t(a)+4<=std::uint64_t(lower_stack)+4096)std::memcpy(lower_expected_.data()+a-lower_stack,&v,4);',
     'if(a>=lower_stack&&std::uint64_t(a)+4<=std::uint64_t(lower_stack)+4096)std::memcpy(lower_expected_.data()+a-lower_stack,&v,4);if(a>=0x20001000&&std::uint64_t(a)+4<=0x20002000)std::memcpy(upper_expected_.data()+a-0x20001000,&v,4);')
 rep('unsigned char Binding::undefined(){guard();source_identity();const auto pc=state.gpr.rip.dword;',
     'unsigned char Binding::undefined(){guard();source_identity();if(allocation_phase_private_>=2)return allocator_undefined();const auto pc=state.gpr.rip.dword;\n if(allocation_phase_private_==1&&pc==caller_cleanup&&access_count==35&&undefined_count==5){undefined_sites[undefined_count++]=pc;return 0;}')
 rep('std::memcpy(query_expected_.data()+4*n,&v,4);', 'std::memcpy(query_expected_.data()+4*n,&v,4);std::memcpy(upper_expected_.data()+a-0x20001000,&v,4);')
 rep('void*Binding::called(State*s,unsigned target,void*p){guard();source_identity();',
     'void*Binding::called(State*s,unsigned target,void*p){guard();source_identity();if(allocation_phase_private_>=2)return allocator_called(s,target,p);')
 rep('(void)m4_crt_heap_init::mw34_heap_init_provider_body(s,target,this);deny("Unexpected successful heap initializer return",target);',
     '''auto result=m4_crt_heap_init::mw34_heap_init_provider_body(s,target,this);guard();source_identity();
 if(result!=this||!initializer_returned_private_||depth!=1||state.gpr.rip.dword!=ret||state.gpr.rsp.dword!=admitted_frame_+4)deny("Genuine initializer must unwind to fragment caller",ret);
 allocation_phase=allocation_phase_private_=1;allocator_snapshot();checkpoint(runtime,"allocation-caller-before");
 return mw34_allocation_caller_body(s,ret,this);''')
 rep('void*Binding::returned(State*s,unsigned target,void*p){guard();source_identity();',
     'void*Binding::returned(State*s,unsigned target,void*p){guard();source_identity();if(allocation_phase_private_>=2)return allocator_returned(s,target,p);')
 rep('first("Genuine heap initializer returned; fragment caller continuation remains unadmitted",ret,0x78003a0b);admitted_parent_->first(reason,fault_address,fault_pc);throw m4_runtime::Fault(m4_runtime::FaultReason::unresolved_translation,{0x78003a0b},{ret},reason);',
     'depth=1;return this;')
 rep('void*Binding::missing(State*s,unsigned target,void*p){guard();source_identity();',
     '''void*Binding::missing(State*s,unsigned target,void*p){guard();source_identity();
 if(allocation_phase_private_>=2)return allocator_missing(s,target,p);
 if(allocation_phase_private_==1&&s==&state&&p==this&&target==caller_stop&&state.gpr.rip.dword==caller_stop&&state.gpr.rsp.dword==admitted_parent_frame_&&state.gpr.rax.dword==1&&state.gpr.rcx.dword==1&&access_count==36&&undefined_count==6&&initializer_returned_private_&&mode_published_private_){caller_cleaned=caller_cleaned_private_=true;allocator_snapshot();checkpoint(runtime,"allocation-caller-after");stable_hook(25);guard();source_identity();throw CallerComplete{};}''')
 rep('void Binding::cleanup(){std::exception_ptr observer;', 'void Binding::cleanup(){std::exception_ptr observer;')
 rep(' if(owned_handle_){if(control==132', ' if(owned_allocation_&&!release_allocation_noexcept())throw std::runtime_error("Actual HeapFree cleanup failed; allocation ownership retained");\n if(owned_handle_){if(control==132')
 rep('~Cleanup()noexcept{if(b.owned_handle_)', '~Cleanup()noexcept{if(b.owned_allocation_)(void)b.release_allocation_noexcept();if(b.owned_handle_)')
 rep('(void)m4_crt_heap_init::mw34_heap_init_fragment_body(&state,fragment,this);deny("Unexpected completion past declared heap mode boundary",fragment);',
     '''try{(void)m4_crt_heap_init::mw34_heap_init_fragment_body(&state,fragment,this);deny("Unexpected completion past declared heap mode boundary",fragment);}catch(const CallerComplete&){allocator_batch();}
 first("Functional source allocation/free research caller completed; original attach remains unadmitted",free_marker,0x78001424);admitted_parent_->first(reason,fault_address,fault_pc);throw m4_runtime::Fault(m4_runtime::FaultReason::unresolved_translation,{0x78001424},{free_marker},reason);''')
 rep('}\n}\nnamespace {\n', '}\n#include "allocation_operations.inc"\n}\nnamespace {\n')
 p.write_text(s)
if __name__=='__main__':main()
