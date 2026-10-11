// Additive normal tree admission. Literal bodies perform every source effect.
// No host map, reconstructed AFTER image, or synthetic allocator is used.
void Binding::tree_enter(){
 if(registry_root_!=tree_root)return;
 if(tree_started_||tree_completed_||runtime.memory().load<unsigned>({0x60b314})||
    runtime.memory().load<unsigned>({0x60b318}))
  deny("Only a fresh empty movement tree source input is admitted",0x60b314);
 tree_started_=true;
}
void Binding::tree_owner_before(unsigned address,std::uint64_t value,unsigned bytes,bool writing){
 fs_owner_probe_={};
 if(registry_root_!=tree_root||state.gpr.rip.dword>=0x78000000)return;
 auto*a=allocation_for(address,bytes);if(!a||a->kind!=4)return;
 auto*r=mfc_for_generation(a->generation);
 const auto*ins=instruction(state.gpr.rip.dword);
 const auto offset=address-a->guest;
 if(!tree_started_||!r||r->words[2]!=tree_root||a->requested!=24||
    (r->words[4]!=0x4ba306&&r->words[4]!=0x4ba33c&&r->words[4]!=0x4bab32)||
    !ins||!tree_instruction(ins->pc)||bytes!=4||(offset&3)||offset>20||
    std::uint64_t(address)+bytes>std::uint64_t(a->guest)+a->requested)
  deny("Tree access requires exact source operand and current requested owner generation",address);
 // check_source_access has already bound this address/value to the actual
 // literal effective operand. The unique generation resolves repeated CALLpc.
 fs_owner_probe_={1,fs_owner_accesses_.size(),tree_root,ins->pc,address,bytes,value,unsigned(writing),
  r->words[2],r->words[4],a->guest,a->generation,a->acquired,offset,r->words[1],0};
 if(writing)fs_hook(86);
}
void Binding::tree_owner_after(unsigned address,std::uint64_t value,unsigned bytes,bool writing){
 if(fs_owner_probe_[0]){
  if(fs_owner_probe_[3]!=state.gpr.rip.dword||fs_owner_probe_[4]!=address||
     fs_owner_probe_[5]!=bytes||fs_owner_probe_[7]!=writing||fs_owner_accesses_.size()>=8192)
   deny("Tree owned access commits its exact generation-bound source observation",address);
  fs_owner_probe_[6]=value;fs_owner_probe_[15]=source_accesses_.size();
  fs_owner_accesses_.push_back(fs_owner_probe_);
  if(writing)fs_hook(87);fs_owner_probe_={};
 }
 if(!writing||bytes!=4)return;
 const auto pc=state.gpr.rip.dword;
 if(pc!=0x4ba315&&pc!=0x4ba347&&pc!=0x4bab9c&&pc!=0x4babac)return;
 auto*a=allocation_for(unsigned(value),24);auto*r=a?mfc_for_generation(a->generation):nullptr;
 const auto call=pc==0x4ba315?0x4ba306U:pc==0x4ba347?0x4ba33cU:0x4bab32U;
 if(!a||a->guest!=value||a->kind!=4||!r||r->words[2]!=tree_root||r->words[4]!=call||
    !r->words[21]||r->words[23]||a->requested!=24)
  deny("Tree primary publication resolves its exact positive allocation occurrence",address,pc);
 Allocation*parent{};unsigned offset{};
 if(pc==0x4ba315||pc==0x4ba347){
  if(address!=(pc==0x4ba315?0x60b314U:0x60b2fcU))
   deny("Tree static primary publication has its literal global",address,pc);
 }else{
  parent=allocation_for(address,4);auto*pr=parent?mfc_for_generation(parent->generation):nullptr;
  offset=parent?address-parent->guest:UINT32_MAX;
  if(!parent||!pr||parent->guest==value||parent->kind!=4||pr->words[2]!=tree_root||
     parent->requested!=24||offset!=(pc==0x4bab9c?8U:0U)||!pr->words[21])
   deny("Tree node publication has the actual live parent generation and branch edge",address,pc);
 }
 ++r->words[23];
 fs_publications_.push_back({1,fs_publications_.size(),tree_root,pc,address,value,r->words[18],
  r->words[17],r->words[4],parent?parent->generation:0,parent?parent->guest:0,offset,
  source_accesses_.size(),0x60b2f8,r->words[1],0});
}
std::uint64_t Binding::tree_lockit_read(unsigned address,std::uint64_t value,unsigned width){
 if(width!=4||(address!=0x5bb4f8&&address!=0x5bb4f4))return value;
 const auto pc=state.gpr.rip.dword;const auto*spec=tree_import(pc);
 if(!tree_started_||!spec||spec->slot!=address||spec->raw!=value||!lockit_admitted_||
    !section_for(0x78145640))deny("Exact tree source import definition and live Lockit resource required",address,pc);
 lockit_guard();
 research_projections_.push_back({5,pc,address,unsigned(value),spec->target,0,0,0});
 lockit_imports_.push_back({1,tree_root,pc,address,value,spec->target,source_accesses_.size(),spec->reg});
 return spec->target;
}
void Binding::tree_lockit_called(unsigned target,unsigned site,unsigned frame){
 const auto*spec=tree_scratch(site);
 if(!spec||!spec->normal||target!=spec->target||state.gpr.rcx.dword!=frame+spec->offset)
  deny("Only the recovered fixed-normal tree scratch/CALL branch is admitted",frame,site);
 const auto*ins=instruction(site);
 if(!ins||source_accesses_.empty())deny("Tree Lockit CALL retains exact literal source",frame,site);
 if(ins->operands[0].kind==1){
  const auto reg=ins->operands[0].reg;const TreeImport*definition{};
  if(reg==6&&target==0x7810a290)definition=tree_import(0x4bab1a);
  if(!definition||register_value(state,reg)!=target)
   deny("Tree register CALL retains its named literal import definition",frame,site);
  const auto owner=std::find_if(calls_.rbegin(),calls_.rend(),[](const auto&c){return c.entry==0x4bab00;});
  if(owner==calls_.rend())deny("Tree register import belongs to its actual insertion invocation",frame,site);
  // Its current source read must follow this invocation's FS predecessor read.
  const auto fs=std::find_if(fs_records_.rbegin(),fs_records_.rend(),[&](const auto&r){
   return r.words[3]==owner->entry&&r.words[5]==owner->frame&&!r.words[21];});
  const auto imported=std::find_if(lockit_imports_.rbegin(),lockit_imports_.rend(),[&](const auto&r){
   return r[1]==tree_root&&r[2]==definition->pc&&r[3]==definition->slot&&r[5]==target;});
  if(fs==fs_records_.rend()||imported==lockit_imports_.rend()||imported->at(6)>=source_accesses_.size())
   deny("Tree register CALL has its current source/FS definition lifetime",frame,site);
 }else{
  if(source_accesses_.size()<2)deny("Direct tree Lockit CALL has its actual IAT read",frame,site);
  const auto&r=source_accesses_[source_accesses_.size()-2];const auto*definition=tree_import(site);
  if(!definition||r.pc!=site||r.write||r.bytes!=4||r.address!=definition->slot||r.value!=definition->raw)
   deny("Direct tree Lockit CALL retains actual raw IAT read before return store",frame,site);
 }
 if(site==0x4badd0){
  // The two immediately preceding committed writes bind the normal left
  // rotation to LEA4BADCC. The +60 alternate branch is not admitted here.
  if(source_accesses_.size()<4)deny("Rotation scratch retains its causal owned-write prefix",frame,site);
  const auto&a=source_accesses_[source_accesses_.size()-4];
  const auto&b=source_accesses_[source_accesses_.size()-3];
  if(a.pc!=0x4badc7||b.pc!=0x4badc9||!a.write||!b.write||a.bytes!=4||b.bytes!=4||
     a.address!=state.gpr.rax.dword||a.value!=state.gpr.rdi.dword||
     b.address!=state.gpr.rdi.dword+4||b.value!=state.gpr.rax.dword)
   deny("Shared rotation destructor scratch follows only its exact committed left branch",frame,site);
 }
 lockit_calls_.push_back({1,lockit_calls_.size(),tree_root,target,site,frame,
  runtime.memory().load<unsigned>({frame}),state.gpr.rcx.dword,
  section_for(0x78145640)->depth,source_accesses_.size(),native_apis_.size(),0,0,0,0,0});
}
