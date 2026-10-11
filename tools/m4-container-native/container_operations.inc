// Additive checked container imports, borrowed CString seed and genuine free(NULL).
void Binding::container_guard(){
 if(!registry_root_)return;
 for(const auto&r:mfc_records_)if(r.words[2]==registry_root_){
  for(const auto&spec:container_vector_stores)if(spec.root==registry_root_&&spec.call==r.words[4]){
   unsigned expected{};for(const auto&w:container_stores_)if(w[2]==registry_root_&&w[4]==spec.address&&w[8]==r.words[1])expected=unsigned(w[6]);
   if(runtime.memory().load<unsigned>({spec.address})!=expected)deny("Normal empty-container fields carry only literal zero input and committed owned endpoint stores",spec.address);
  }
 }
}
void Binding::container_hook(unsigned point){
 const auto nulls=container_nulls_,borrowed=container_borrowed_;const auto imports=container_imports_;const auto stores=container_stores_;const auto probe=container_probe_;
 const auto null_active=container_null_active_,borrowed_active=container_borrowed_active_;
 stable_hook(point);
 if(nulls!=container_nulls_||borrowed!=container_borrowed_||imports!=container_imports_||stores!=container_stores_||probe!=container_probe_||null_active!=container_null_active_||borrowed_active!=container_borrowed_active_)
  deny("Container observer changed private import/borrowed/null-free/store witnesses",state.gpr.rip.dword);
}
void Binding::mfc_called(unsigned target,unsigned site,unsigned frame){
 if(target==mfc_free_entry&&runtime.memory().load<unsigned>({frame+4})==0){
  if(container_null_active_||mfc_free_active_||container_nulls_.size()>=512)deny("One finite genuine null MFC825 CALL at a time",frame,site);
  const auto*spec=container_free_input(registry_root_,site);
  if(registry_root_&&!spec)deny("Exact normal container null-free CALL site",frame,site);
  ContainerRecord r;r.words={1,container_nulls_.size(),registry_root_,site,target,frame,runtime.memory().load<unsigned>({frame}),0,
   site?0x80000339ULL:0,site?0x5abd1aULL:0,generation_,0,0,0,0,0,0,0,0,fs_expected_,0,0,0,native_apis_.size(),0,live_allocations(),0,source_accesses_.size(),0,0,0,0};
  container_nulls_.push_back(r);container_null_active_=unsigned(r.words[1])+1;container_hook(90);return;
 }
 if(target==free_entry&&container_null_active_){
  auto&w=container_nulls_[container_null_active_-1].words;
  if(site!=0x5f401786||frame!=w[5]-8||runtime.memory().load<unsigned>({frame})!=0x5f40178c||runtime.memory().load<unsigned>({frame+4})||w[16]!=free_entry)
   deny("Exact literal MFC825 CALL to CRTfree with genuine zero argument",frame,site);
  w[11]=target;w[12]=frame;w[13]=runtime.memory().load<unsigned>({frame});w[20]=fs_expected_;container_hook(91);return;
 }
 if(target==container_borrowed_entry){
  if(container_borrowed_active_||container_borrowed_.size()>=512)deny("One finite genuine MFC540 constructor at a time",frame,site);
  const auto*spec=container_borrowed_input(registry_root_,site);
  if(!spec||state.gpr.rcx.dword!=spec->object)deny("Exact root/site/ECX for original borrowed MFC540 constructor",frame,site);
  ContainerRecord r;r.words={1,container_borrowed_.size(),registry_root_,target,site,frame,runtime.memory().load<unsigned>({frame}),state.gpr.rcx.dword,
   0x8000021c,0x5abdb0,0,0,0,container_borrowed_data,0,0,0,0,0,0,0,0,0,source_accesses_.size(),0,fs_expected_,0,native_apis_.size(),0,live_allocations(),0,0};
  container_borrowed_.push_back(r);container_borrowed_active_=unsigned(r.words[1])+1;container_hook(94);return;
 }
 if(target==container_accessor_entry&&container_borrowed_active_){
  auto&w=container_borrowed_[container_borrowed_active_-1].words;
  if(site!=0x5f4020b7||frame!=w[5]-8||runtime.memory().load<unsigned>({frame})!=0x5f4020bc)deny("Exact MFC540 CALL frame for borrowed data accessor",frame,site);
  w[10]=frame;w[11]=runtime.memory().load<unsigned>({frame});return;
 }
 accepted109_mfc_called(target,site,frame);
}
void Binding::container_read_before(unsigned address,unsigned bytes){
 if(address!=container_borrowed_data)return;
 if(bytes!=4||state.gpr.rip.dword!=0x5f4020bc||!container_borrowed_active_)deny("Only exact MFC540 source borrowed DWORD read",address);
 auto&w=container_borrowed_[container_borrowed_active_-1].words;
 if(w[12]!=address||state.gpr.rax.dword!=address)deny("Borrowed DWORD read follows genuine source accessor RET",address);
 container_hook(95);
}
std::uint64_t Binding::mfc_read(unsigned address,std::uint64_t value,unsigned bytes){
 const auto pc=state.gpr.rip.dword;
 if(bytes==4&&(address==0x5bb4c8||address==0x5bb454)){
  const bool free=address==0x5bb4c8;const auto raw=free?0x80000339U:0x8000021cU,target=free?mfc_free_entry:container_borrowed_entry;
  if(pc!=(free?0x5abd1aU:0x5abdb0U)||value!=raw)deny("Exact container game owning ordinal source import relocation",address,pc);
  container_imports_.push_back({1,container_imports_.size(),registry_root_,pc,address,value,target,free?825ULL:540ULL});
  research_projections_.push_back({5,pc,address,unsigned(value),target,0,0,0});return target;
 }
 if(address==0x5f498148&&container_null_active_){
  if(bytes!=4||pc!=0x5f401786||value!=mfc_raw_free)deny("Exact genuine null-free MFC source import relocation",address,pc);
  auto&w=container_nulls_[container_null_active_-1].words;w[14]=value;w[15]=pc;w[16]=free_entry;
  container_imports_.push_back({1,container_imports_.size(),registry_root_,pc,address,value,free_entry,0});
  research_projections_.push_back({5,pc,address,unsigned(value),free_entry,0,0,0});return free_entry;
 }
 if(address==container_borrowed_data){
  if(bytes!=4||pc!=0x5f4020bc||!container_borrowed_active_||value!=container_borrowed_loaded)deny("Exact measured post-DllMain borrowed MFC DWORD",address,pc);
  auto&w=container_borrowed_[container_borrowed_active_-1].words;w[14]=pc;w[15]=value;container_hook(96);return value;
 }
 return accepted109_mfc_read(address,value,bytes);
}
void Binding::mfc_returned(unsigned entry,unsigned result,unsigned frame){
 if(container_null_active_&&(entry==free_entry||entry==mfc_free_entry)){
  auto&w=container_nulls_[container_null_active_-1].words;
  if(native_apis_.size()!=w[23]||live_allocations()!=w[25]||generation_!=w[10]||fs_expected_!=w[19])deny("Normal free(NULL) restores exact chain and has zero API/owner/generation effects",frame);
  if(entry==free_entry){if(frame!=w[12]||!w[11])deny("Genuine CRTfree(NULL) RET consumes its exact source frame",frame);w[17]=1;w[21]=fs_expected_;w[29]=result;container_hook(92);return;}
  if(frame!=w[5]||!w[17])deny("Genuine MFC825 null RET follows complete literal CRTfree(NULL)",frame);
  w[18]=1;w[22]=fs_expected_;w[24]=native_apis_.size();w[26]=live_allocations();w[28]=source_accesses_.size();w[30]=result;w[31]=generation_;container_hook(93);container_null_active_=0;return;
 }
 if(container_borrowed_active_&&(entry==container_accessor_entry||entry==container_borrowed_entry)){
  auto&w=container_borrowed_[container_borrowed_active_-1].words;
  if(entry==container_accessor_entry){if(frame!=w[10]||result!=container_borrowed_data)deny("Literal borrowed accessor RET gives its exact owned module DWORD address",frame);w[12]=result;return;}
  if(frame!=w[5]||!w[19]||result!=w[7]||native_apis_.size()!=w[27]||live_allocations()!=w[29]||fs_expected_!=w[25])deny("Complete MFC540 RET preserves borrowed identity and creates no owner/API",frame);
  w[20]=source_accesses_.back().pc;w[21]=result;w[22]=1;w[24]=source_accesses_.size();w[26]=fs_expected_;w[28]=native_apis_.size();w[30]=live_allocations();container_hook(99);container_borrowed_active_=0;return;
 }
 accepted109_mfc_returned(entry,result,frame);
}
void Binding::container_write_before(unsigned address,std::uint64_t value,unsigned bytes){
 const auto pc=state.gpr.rip.dword;
 if(pc==0x5f4020be){
  if(!container_borrowed_active_)deny("Literal borrowed publication has its genuine constructor",address);
  auto&w=container_borrowed_[container_borrowed_active_-1].words;
  if(bytes!=4||address!=w[7]||value!=w[15]||w[14]!=0x5f4020bc||w[19])deny("Only exact unchanged borrowed MFC DWORD is copied to source ECX object",address);
  w[16]=address;w[17]=pc;w[18]=value;container_hook(97);return;
 }
 const auto*spec=container_vector_store(registry_root_,pc);if(!spec)return;
 MfcRecord*record{};for(auto&r:mfc_records_)if(r.words[2]==registry_root_&&r.words[4]==spec->call&&r.words[21])record=&r;
 if(!record)deny("Vector endpoint publication retains its genuine positive MFC owner",address,pc);
 auto*a=allocation_for(unsigned(record->words[16]));const auto wanted=record->words[16]+(spec->kind==3?record->words[7]:0);
 if(bytes!=4||address!=spec->address||!a||a->kind!=4||a->generation!=record->words[18]||value!=wanted)deny("Exact normal empty-container endpoint/capacity and live whole owned allocation",address,pc);
 if(container_stores_.size()>=4096)deny("Finite container endpoint source-store ledger",address);
 container_probe_={1,container_stores_.size(),registry_root_,pc,address,bytes,value,spec->kind,record->words[1],record->words[16],record->words[18],record->words[7],record->words[17],record->words[19],source_accesses_.size(),0};container_hook(100);
}
void Binding::container_write_after(unsigned address,std::uint64_t value,unsigned bytes){
 const auto pc=state.gpr.rip.dword;
 if(pc==0x5f4020be&&container_borrowed_active_){auto&w=container_borrowed_[container_borrowed_active_-1].words;if(w[16]!=address||w[18]!=value||bytes!=4)deny("Committed literal borrowed object store equals checked input",address);w[19]=1;container_hook(98);}
 if(container_probe_[3]==pc&&container_probe_[4]==address&&container_probe_[5]==bytes&&container_probe_[6]==value){container_probe_[15]=source_accesses_.size();container_stores_.push_back(container_probe_);container_hook(101);container_probe_={};}
}
void Binding::dump_container(CaptureSink sink,void*context)const{
 static_assert(sizeof(ContainerRecord)==256&&std::is_standard_layout_v<ContainerRecord>&&std::is_trivially_copyable_v<ContainerRecord>);
 sink("container-nullfree-witnesses.bin",std::as_bytes(std::span(container_nulls_)),context);sink("container-borrowed-witnesses.bin",std::as_bytes(std::span(container_borrowed_)),context);
 sink("container-import-ledger.bin",std::as_bytes(std::span(container_imports_)),context);sink("container-vector-stores.bin",std::as_bytes(std::span(container_stores_)),context);sink("container-vector-probe.bin",std::as_bytes(std::span(container_probe_)),context);
 const std::array<unsigned,2>active{container_null_active_,container_borrowed_active_};sink("container-active.bin",std::as_bytes(std::span(active)),context);
 sink("container-null-active.bin",std::as_bytes(std::span(&container_null_active_,1)),context);sink("container-borrowed-active.bin",std::as_bytes(std::span(&container_borrowed_active_,1)),context);
}
