// Additive MFC source-frame and private-owner witnesses. Literal bodies provide effects.
Binding::MfcRecord*Binding::current_mfc()noexcept{if(mfc_records_.empty()||mfc_records_.back().words[21])return nullptr;return &mfc_records_.back();}
Binding::MfcRecord*Binding::mfc_for_generation(unsigned generation)noexcept{for(auto&r:mfc_records_)if(r.words[18]==generation)return &r;return nullptr;}
void Binding::mfc_hook(unsigned point){
 const auto records=mfc_records_;const auto imports=mfc_imports_;const auto stores=mfc_stores_;const auto probe=mfc_store_probe_;const auto free=mfc_free_active_;
 stable_hook(point);
 if(records!=mfc_records_||imports!=mfc_imports_||stores!=mfc_stores_||probe!=mfc_store_probe_||free!=mfc_free_active_)deny("MFC observer changed private source-frame/import/owner/store witnesses",state.gpr.rip.dword);
}
void Binding::mfc_called(unsigned target,unsigned site,unsigned frame){
 if(target==mfc_allocate_entry){
  if(current_mfc()||mfc_records_.size()>=512)deny("One finite genuine MFC allocation at a time",target,site);
  const auto request=runtime.memory().load<unsigned>({frame+4});const auto*spec=mfc_root_input(registry_root_,site);
  if(request>1024*1024||(registry_root_&&(!spec||spec->call!=site||spec->request!=request)))deny("Exact root/site/request for original MFC allocator CALL",frame,site);
  MfcRecord record;record.words={1,mfc_records_.size(),registry_root_,target,site,frame,runtime.memory().load<unsigned>({frame}),request,0,0,0,0,0,0,0,0,0,0,0,0,0,0,state.gpr.rcx.dword,0,0,0,0,0,0,0,0,0};
  mfc_records_.push_back(record);mfc_hook(70);return;
 }
 auto*record=current_mfc();
 if(target==malloc_entry&&record){
  if(site!=0x5f401eb5||frame!=record->words[5]-24||runtime.memory().load<unsigned>({frame})!=0x5f401eb7||runtime.memory().load<unsigned>({frame+4})!=record->words[7]||state.gpr.rbx.dword!=malloc_entry||record->words[9]!=malloc_entry)deny("Genuine MFC CALL EBX and exact original cdecl malloc frame",frame,site);
  record->words[11]=site;record->words[12]=frame;record->words[13]=runtime.memory().load<unsigned>({frame+4});
 }
 if(target==mfc_free_entry){
  const auto guest=runtime.memory().load<unsigned>({frame+4});auto*a=allocation_for(guest);auto*r=a?mfc_for_generation(a->generation):nullptr;
  if(mfc_free_active_||!a||a->guest!=guest||a->kind!=4||!r||!r->words[21]||r->words[25])deny("MFC free entry requires exact live whole private object and generation",guest,site);
  r->words[25]=target;r->words[26]=frame;mfc_free_active_=static_cast<unsigned>(r->words[1])+1;
 }
 if(target==free_entry&&mfc_free_active_){
  auto&r=mfc_records_[mfc_free_active_-1];auto*a=allocation_for(static_cast<unsigned>(r.words[16]));
  if(site!=0x5f401786||frame!=r.words[26]-8||runtime.memory().load<unsigned>({frame})!=0x5f40178c||runtime.memory().load<unsigned>({frame+4})!=r.words[16]||!a||a->kind!=4||a->generation!=r.words[18]||r.words[29]!=free_entry)deny("Exact literal MFC825 CALL and owned CRTfree argument",frame,site);
  r.words[27]=frame;mfc_hook(76);
 }
}
std::uint64_t Binding::mfc_read(unsigned address,std::uint64_t value,unsigned bytes){
 if(bytes!=4)return value;auto*record=current_mfc();
 if(address==0x5f49814c){
  if(state.gpr.rip.dword!=0x5f401ea1||value!=mfc_raw_malloc||!record)deny("Exact MFC source malloc import relocation",address);
  record->words[8]=value;record->words[9]=malloc_entry;record->words[10]=state.gpr.rip.dword;
  mfc_imports_.push_back({1,record->words[1],record->words[2],state.gpr.rip.dword,address,value,malloc_entry,1});
  research_projections_.push_back({5,state.gpr.rip.dword,address,static_cast<unsigned>(value),malloc_entry,0,0,0});return malloc_entry;
 }
 if(address==0x5f498970){
  if(state.gpr.rip.dword!=0x5f401ead||value!=mfc_handler||!record)deny("Exact post-loader MFC allocation handler input",address);
  record->words[14]=state.gpr.rip.dword;record->words[15]=value;
  mfc_imports_.push_back({1,record->words[1],record->words[2],state.gpr.rip.dword,address,value,value,3});return value;
 }
 if(address==0x5f498148){
  if(state.gpr.rip.dword!=0x5f401786||value!=mfc_raw_free||!mfc_free_active_)deny("Exact MFC source free import relocation",address);
  auto&r=mfc_records_[mfc_free_active_-1];r.words[28]=value;r.words[29]=free_entry;
  mfc_imports_.push_back({1,r.words[1],r.words[2],state.gpr.rip.dword,address,value,free_entry,2});
  research_projections_.push_back({5,state.gpr.rip.dword,address,static_cast<unsigned>(value),free_entry,0,0,0});return free_entry;
 }
 if(address==mfc_game_iat){
  if(value!=mfc_game_raw||!mfc_callsite(state.gpr.rip.dword))deny("Exact game MFC ordinal823 source import relocation",address);
  mfc_imports_.push_back({1,mfc_records_.size(),registry_root_,state.gpr.rip.dword,address,value,mfc_allocate_entry,0});
  research_projections_.push_back({5,state.gpr.rip.dword,address,static_cast<unsigned>(value),mfc_allocate_entry,0,0,0});return mfc_allocate_entry;
 }
 return value;
}
void Binding::mfc_returned(unsigned entry,unsigned result,unsigned frame){
 auto*record=current_mfc();
 if(entry==malloc_entry&&record){
  if(frame!=record->words[12])deny("Actual CRTmalloc RET is tied to the exact MFC CALL frame",frame);
  record->words[20]=result;
  if(result){auto*a=allocation_for(result);if(!a||a->guest!=result||a->kind!=4||a->requested!=record->words[7])deny("MFC returned malloc requires exact private owned requested storage",result);
   record->words[16]=result;record->words[17]=a->acquired;record->words[18]=a->generation;record->words[19]=a->extent;}
  mfc_hook(72);
 }
 if(entry==mfc_allocate_entry&&record){
  if(frame!=record->words[5]||result!=record->words[20]||!result||result!=record->words[16])deny("Literal positive MFC allocator RET requires actual owned malloc result",result);
  record->words[21]=1;mfc_hook(75);
 }
 if(entry==mfc_free_entry){
  if(!mfc_free_active_)deny("Genuine MFC825 RET has its active private cleanup owner",frame);
  auto&r=mfc_records_[mfc_free_active_-1];Allocation*a{};for(auto&p:owned_allocations_)if(p->generation==r.words[18])a=p.get();
  if(frame!=r.words[26]||!a||a->native||a->mapped||!a->source_freed)deny("Genuine MFC825 RET follows actual source free and unmapping",frame);
  r.words[30]=1;mfc_hook(77);mfc_free_active_=0;
 }
}
void Binding::mfc_write_before(unsigned address,std::uint64_t value,unsigned bytes){
 auto*active=current_mfc();
 if(active&&state.gpr.rip.dword==0x5f401eb5){
  if(bytes!=4||address!=active->words[5]-24||value!=0x5f401eb7||state.gpr.rbx.dword!=malloc_entry||runtime.memory().load<unsigned>({address+4})!=active->words[7])deny("Before literal MFC CALL EBX exact target/size/return frame",address);
  mfc_hook(71);
 }
 Binding::MfcRecord*record{};unsigned kind{};
 if(auto*a=allocation_for(address,bytes);a&&a->kind==4){record=mfc_for_generation(a->generation);kind=1;
  if(!record||record->words[2]!=registry_root_||std::uint64_t(address)+bytes>std::uint64_t(a->guest)+a->requested)deny("Literal MFC object store stays inside exact root-owned requested bytes",address);
 }else if(bytes==4){for(auto&r:mfc_records_)if(r.words[2]==registry_root_&&r.words[21]&&r.words[16]==value){const auto*spec=mfc_root_input(registry_root_,static_cast<unsigned>(r.words[4]));if(spec&&address==spec->publication){record=&r;kind=2;break;}}}
 if(!record)return;
 if(mfc_stores_.size()>=8192)deny("Finite MFC object/publication store ledger",address);
 mfc_store_probe_={1,record->words[1],record->words[2],state.gpr.rip.dword,address,bytes,value,kind};mfc_hook(73);
}
void Binding::mfc_write_after(unsigned address,std::uint64_t value,unsigned bytes){
 if(mfc_store_probe_[3]!=state.gpr.rip.dword||mfc_store_probe_[4]!=address||mfc_store_probe_[5]!=bytes||mfc_store_probe_[6]!=value)return;
 auto&r=mfc_records_[mfc_store_probe_[1]];if(mfc_store_probe_[7]==1)r.words[24]+=bytes;else ++r.words[23];
 mfc_stores_.push_back(mfc_store_probe_);mfc_hook(74);mfc_store_probe_={};
}
void Binding::dump_mfc(CaptureSink sink,void*context)const{
 std::vector<std::array<std::uint64_t,32>>rows;for(const auto&r:mfc_records_){auto w=r.words;for(const auto&a:owned_allocations_)if(a->generation==w[18]){w[30]=a->source_freed;w[31]=a->cleanup_freed;}rows.push_back(w);}
 sink("mfc-allocation-witnesses.bin",std::as_bytes(std::span(rows)),context);
 sink("mfc-import-ledger.bin",std::as_bytes(std::span(mfc_imports_)),context);sink("mfc-store-ledger.bin",std::as_bytes(std::span(mfc_stores_)),context);
 sink("mfc-store-probe.bin",std::as_bytes(std::span(mfc_store_probe_)),context);
}
