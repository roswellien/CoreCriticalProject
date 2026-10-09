"""Adapt only fresh mutable author copies to the whole locale unit."""
from pathlib import Path
H=Path(__file__).resolve().parent
p=H/'locale_batch_binding.inc';s=p.read_text()
def rep(a,b):
 global s
 assert s.count(a)==1,(a[:100],s.count(a))
 s=s.replace(a,b)
rep('Binding::~Binding()noexcept{if(owned_allocation_)',
    'Binding::~Binding()noexcept{(void)cleanup_sections_noexcept();(void)cleanup_allocations_noexcept();if(owned_allocation_)')
rep('void Binding::guard(){admit_current();', 'void Binding::guard(){admit_current();')
rep(' if(allocation_phase_private_)allocator_guard();', ' if(batch_phase_)batch_guard();else if(allocation_phase_private_)allocator_guard();')
rep('void Binding::source_identity(){admit_current();', 'void Binding::source_identity(){admit_current();if(batch_phase_){batch_source_identity();return;}')
rep('unsigned Binding::read32(unsigned a){guard();source_identity();', 'unsigned Binding::read32(unsigned a){if(batch_phase_)return static_cast<unsigned>(read(a,4));guard();source_identity();')
rep('void Binding::write32(unsigned a,unsigned v){guard();source_identity();', 'void Binding::write32(unsigned a,unsigned v){if(batch_phase_){write(a,v,4);return;}guard();source_identity();')
rep('unsigned char Binding::undefined(){guard();source_identity();', 'unsigned char Binding::undefined(){if(batch_phase_)return batch_undefined();guard();source_identity();')
rep('void*Binding::called(State*s,unsigned target,void*p){guard();source_identity();', 'void*Binding::called(State*s,unsigned target,void*p){if(batch_phase_)return batch_called(s,target,p);guard();source_identity();')
rep('void*Binding::returned(State*s,unsigned target,void*p){guard();source_identity();', 'void*Binding::returned(State*s,unsigned target,void*p){if(batch_phase_)return batch_returned(s,target,p);guard();source_identity();')
rep('void*Binding::missing(State*s,unsigned target,void*p){guard();source_identity();', 'void*Binding::missing(State*s,unsigned target,void*p){if(batch_phase_)return batch_missing(s,target,p);guard();source_identity();')
rep('void Binding::cleanup(){std::exception_ptr observer;', 'void Binding::cleanup(){if(!cleanup_sections_noexcept()||!cleanup_allocations_noexcept())throw std::runtime_error("Live locale ownership retained after unsuccessful cleanup");std::exception_ptr observer;')
rep('bool Binding::release_noexcept(bool skip)noexcept{', 'bool Binding::release_noexcept(bool skip)noexcept{if(live_allocations()||live_critical_sections())return false;')
rep('[[noreturn]]void Binding::start(mg::Context&c)', 'void Binding::start(mg::Context&c)')
rep('~Cleanup()noexcept{if(b.owned_allocation_)', '~Cleanup()noexcept{if(b.active&&!b.failed)return;(void)b.cleanup_sections_noexcept();(void)b.cleanup_allocations_noexcept();if(b.owned_allocation_)')
rep('catch(const CallerComplete&){allocator_batch();}\n first("Functional source allocation/free research caller completed; original attach remains unadmitted",free_marker,0x78001424);admitted_parent_->first(reason,fault_address,fault_pc);throw m4_runtime::Fault(m4_runtime::FaultReason::unresolved_translation,{0x78001424},{free_marker},reason);',
    'catch(const CallerComplete&){locale_batch();}\n if(!locale_complete_)deny("Complete genuine default locale required",0x78003dda);return;')
rep('#include "locale_batch_allocator.inc"', '#include "locale_batch_allocator.inc"\n#include "locale_batch_operations.inc"')
p.write_text(s)
