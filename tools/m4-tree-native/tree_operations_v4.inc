// Additive normal tree admission. Literal bodies perform every source effect.
// No host map, reconstructed AFTER image, or synthetic allocator is used.
void Binding::tree_enter(){
 if(registry_root_!=tree_root)return;
 if(tree_started_||tree_completed_||runtime.memory().load<unsigned>({0x60b314})||
    runtime.memory().load<unsigned>({0x60b318}))
  deny("Only a fresh empty movement tree source input is admitted",0x60b314);
 tree_started_=true;
}
unsigned Binding::tree_role(unsigned generation){
 unsigned role{};
 for(const auto&r:mfc_records_)if(r.words[2]==tree_root){
  if(r.words[18]==generation){
   if(role>=std::size(tree_owner_sites)||r.words[4]!=tree_owner_sites[role])
    deny("Tree role follows its actual allocation occurrence and exact source CALL",unsigned(r.words[16]));
   return role;
  }
  ++role;
 }
 deny("Tree owner role requires an actual current allocation generation",generation);return UINT32_MAX;
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
 const auto role=tree_role(a->generation);
 if(tree_owner_cursor_>=std::size(tree_access_order))deny("Finite exact normal tree owner access order",address);
 const auto&expected=tree_access_order[tree_owner_cursor_];
 if(expected.pc!=ins->pc||expected.role!=role||expected.offset!=offset||expected.width!=bytes||expected.writing!=writing)
  deny("Tree access retains its exact source PC, role occurrence, offset and causal order",address,ins->pc);
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
  const auto&expected=tree_access_order[tree_owner_cursor_];
  if(expected.value_role!=UINT32_MAX){
   auto*value_owner=allocation_for(unsigned(value),24);
   if(!value_owner||value_owner->guest!=value||value_owner->kind!=4||tree_role(value_owner->generation)!=expected.value_role)
    deny("Tree pointer access resolves its exact current live owner role",address);
  }
  fs_owner_accesses_.push_back(fs_owner_probe_);
  ++tree_owner_cursor_;
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
 if(tree_publication_cursor_>=std::size(tree_publication_order))deny("Finite exact normal tree primary publication order",address,pc);
 const auto&expected=tree_publication_order[tree_publication_cursor_];
 if(expected.pc!=pc||expected.role!=tree_role(a->generation)||
    (parent?(expected.parent!=tree_role(parent->generation)||expected.offset!=offset):expected.global!=address))
  deny("Tree publication retains its exact source and actual child/parent role generations",address,pc);
 ++r->words[23];
 ++tree_publication_cursor_;
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
 if(tree_lockit_contexts_.size()>=std::size(tree_lockit_order)||
    tree_lockit_order[tree_lockit_contexts_.size()]!=site)
  deny("Tree Lockit CALL retains its exact normal causal occurrence",frame,site);
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
  const auto fs_begin=fs==fs_records_.rend()?fs_events_.rend():std::find_if(fs_events_.rbegin(),fs_events_.rend(),[&](const auto&e){return e[3]==fs->words[1]&&e[4]==80;});
  if(fs==fs_records_.rend()||fs_begin==fs_events_.rend()||imported==lockit_imports_.rend()||
     imported->at(6)<=fs_begin->at(13)||imported->at(6)>=source_accesses_.size())
   deny("Tree register CALL has its current source/FS definition lifetime",frame,site);
  const auto&read=source_accesses_[imported->at(6)-1];
  if(read.pc!=definition->pc||read.address!=definition->slot||read.value!=definition->raw||read.bytes!=4||read.write)
   deny("Tree register definition retains its exact committed import read",frame,site);
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
 if(calls_.empty()||fs_active_.empty())deny("Tree Lockit CALL retains its current caller and active FS invocation",frame,site);
 const auto&caller=calls_.back();
 const auto invocation=fs_active_.back()+1;
 const bool ctor=target==0x7810a290;
 unsigned paired=UINT32_MAX;
 if(!ctor){
  const auto expected_ctor=site==0x4ba364?0x4ba2efU:site==0x4ba3ca?0x4ba395U:
                           site==0x4bae05?0x4bab28U:site==0x4badd0?0x4bad8fU:0U;
  if(tree_lockit_held_.empty())deny("Tree destructor has its live source scratch constructor",frame,site);
  const auto&held=tree_lockit_held_.back();
  if(!expected_ctor||held[2]!=state.gpr.rcx.dword||held[3]!=caller.entry||held[4]!=caller.frame||
     held[5]!=invocation||held[6]!=expected_ctor||held[7]!=section_for(0x78145640)->depth)
   deny("Tree destructor consumes the same live scratch, caller and FS invocation in LIFO order",frame,site);
  paired=unsigned(held[1]);
 }
 tree_lockit_contexts_.push_back({1,lockit_calls_.size(),site,unsigned(ctor),state.gpr.rcx.dword,
  caller.entry,caller.frame,invocation,tree_lockit_held_.size(),paired,source_accesses_.size(),0,0,0,0,0});
 lockit_calls_.push_back({1,lockit_calls_.size(),tree_root,target,site,frame,
  runtime.memory().load<unsigned>({frame}),state.gpr.rcx.dword,
  section_for(0x78145640)->depth,source_accesses_.size(),native_apis_.size(),0,0,0,0,0});
}
void Binding::tree_lockit_returned(unsigned entry,unsigned frame){
 if(registry_root_!=tree_root||(entry!=0x7810a290&&entry!=0x7810a350))return;
 if(lockit_calls_.empty()||tree_lockit_contexts_.empty())deny("Tree Lockit RET retains its source context",frame);
 auto&context=tree_lockit_contexts_.back();const auto&call=lockit_calls_.back();
 if(context[1]!=call[1]||context[11]||call[5]!=frame||!call[11])
  deny("Tree Lockit RET completes its exact pending context",frame);
 if(entry==0x7810a290){
  if(tree_lockit_held_.size()>=8)deny("Finite live tree scratch nesting",frame);
  tree_lockit_held_.push_back({1,call[1],context[4],context[5],context[6],context[7],context[2],call[13]});
 }else{
  if(tree_lockit_held_.empty()||tree_lockit_held_.back()[1]!=context[9])
   deny("Tree Lockit destructor RET consumes its actual paired scratch",frame);
  tree_lockit_held_.pop_back();
 }
 context[11]=1;context[12]=call[13];context[13]=source_accesses_.size();
}
void Binding::tree_returned(unsigned entry){
 if(entry!=tree_root)return;
 if(!tree_started_||tree_completed_||!tree_lockit_held_.empty()||!fs_active_.empty()||
    section_for(0x78145640)->depth||runtime.memory().load<unsigned>({0x60b318})!=1||
    runtime.memory().load<unsigned>({0x60b304})!=5)
  deny("Normal tree root RET restores all owned FS and scratch lifetimes",entry);
 unsigned owners{};
 for(const auto&r:mfc_records_)if(r.words[2]==tree_root){
  if(!r.words[21]||r.words[23]!=1||r.words[7]!=24)deny("Tree root RET retains all positive source publications",entry);
  ++owners;
 }
 if(owners!=7||tree_owner_cursor_!=std::size(tree_access_order)||tree_publication_cursor_!=7||tree_lockit_contexts_.size()!=26)
  deny("Tree root RET retains all measured source access, allocation and Lockit occurrences",entry);
 tree_completed_=true;
}
