// Finite mixed initializer admission. Literal bodies supply every tree/list effect.
void Binding::mixed_format_enter(){
 if(registry_root_!=mixed_format_root)return;
 if(runtime.memory().load<unsigned>({0x60b7d0})||runtime.memory().load<unsigned>({0x60b7d4})||
    std::any_of(mfc_records_.begin(),mfc_records_.end(),[](const auto&r){return r.words[2]==mixed_format_root;}))
  deny("Fresh shared header/counter and first mixed initializer invocation",0x60b7d4);
}
void Binding::mixed_format_owner_before(unsigned address,std::uint64_t value,unsigned bytes,bool writing){
 if(registry_root_!=mixed_format_root)return;const auto pc=state.gpr.rip.dword;
 const bool required=std::any_of(std::begin(mixed_format_owned),std::end(mixed_format_owned),[&](const auto&r){return r.pc==pc;});
 if(!required)return;
 const auto cursor=std::count_if(fs_owner_accesses_.begin(),fs_owner_accesses_.end(),[](const auto&r){return r[2]==mixed_format_root;});
 if(cursor>=std::size(mixed_format_owned))deny("Finite exact ordered mixed MFC source operands",address,pc);
 const auto&e=mixed_format_owned[cursor];const auto&spec=mixed_format_mfc_inputs[e.owner];auto*owner=fs_mfc_owner(mixed_format_root,spec.call);auto*a=allocation_for(address,bytes);
 if(!writing||e.pc!=pc||e.bytes!=bytes||!owner||!a||a->kind!=4||a->guest!=owner->words[16]||a->generation!=owner->words[18]||a->requested!=spec.request||address!=a->guest+e.offset||std::uint64_t(address)+bytes>std::uint64_t(a->guest)+a->requested)
  deny("Mixed exact live MFC role/generation/PC/offset/width/order",address,pc);
 unsigned expected=e.literal;
 if(e.value_owner>=0){auto*other=fs_mfc_owner(mixed_format_root,mixed_format_mfc_inputs[e.value_owner].call);if(!other)deny("Mixed pointer operand derives from its actual prior MFC owner",address,pc);expected=unsigned(other->words[16]);}
 if(value!=expected)deny("Mixed source scalar/pointer value derives from its exact role",address,pc);
}
void Binding::mixed_format_called(unsigned target,unsigned site,unsigned frame){
 if(registry_root_!=mixed_format_root)return;
 if(target==0x4e22e0&&(runtime.memory().load<unsigned>({frame+4})||site<0x4e2190||site>=0x4e22d9))
  deny("Only the literal five NULL mixed string-helper invocations are admitted",frame,site);
 if(target==0x78010a6d)deny("Unobserved mixed non-NULL strdup branch is outside this finite domain",target,site);
}
void Binding::mixed_format_returned(unsigned entry){
 if(registry_root_!=mixed_format_root||entry!=mixed_format_root)return;
 const auto accesses=std::count_if(fs_owner_accesses_.begin(),fs_owner_accesses_.end(),[](const auto&r){return r[2]==mixed_format_root;});
 const auto pubs=std::count_if(fs_publications_.begin(),fs_publications_.end(),[](const auto&r){return r[2]==mixed_format_root;});
 if(accesses!=10||pubs!=3||runtime.memory().load<unsigned>({0x60b7d0})!=1)
  deny("Complete mixed ten literal owned writes and three actual owner publications",entry);
 for(const auto&spec:mixed_format_mfc_inputs){auto*owner=fs_mfc_owner(mixed_format_root,spec.call);if(!owner||!owner->words[21]||owner->words[23]!=1)deny("Mixed source owner retains one completed allocation/publication",spec.call);}
}
