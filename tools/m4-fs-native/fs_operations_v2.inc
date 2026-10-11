// Checked virtual guest exception-chain records. Source bodies perform all effects.
void Binding::fs_admit(){
 if(fs_admitted_)deny("Guest FS provenance is single-use",runtime.fs_base().value);
 const auto base=runtime.fs_base().value;
 fs_native_input_={1,base,state.addr.fs_base.dword,runtime.memory().load<unsigned>({base}),
  runtime.memory().load<unsigned>({base+4}),runtime.memory().load<unsigned>({base+8}),
  runtime.memory().load<unsigned>({base+0x18}),m4_runtime::Runtime::seh_end,0,0,0,0,0,0,0,0};
 if(base!=0x7ffde000||state.addr.fs_base.dword!=base||fs_native_input_[3]!=m4_runtime::Runtime::seh_end||
    fs_native_input_[4]!=runtime.stack_top().value||fs_native_input_[5]!=runtime.stack_low().value||fs_native_input_[6]!=base)
  deny("Runtime-owned native guest TIB and explicit end sentinel provenance",base);
 fs_admitted_=true;
}
void Binding::fs_guard(){
 if(!fs_admitted_||!batch_phase_)return;
 const auto base=runtime.fs_base().value;
 if(base!=fs_native_input_[1]||state.addr.fs_base.dword!=base||
    runtime.memory().load<unsigned>({base+4})!=fs_native_input_[4]||
    runtime.memory().load<unsigned>({base+8})!=fs_native_input_[5]||
    runtime.memory().load<unsigned>({base+0x18})!=fs_native_input_[6])
  deny("Stable native guest TIB identity and carried source stack domain",base);
 if(fs_active_.size()>8||fs_records_.size()>128||fs_events_.size()>4096)
  deny("Finite normal guest FS record/chain observations",base);
 for(auto index:fs_active_){
  const auto&w=fs_records_[index].words;
  if(!w[15]||w[19]||runtime.memory().load<unsigned>({unsigned(w[9])})!=w[8]||
     runtime.memory().load<unsigned>({unsigned(w[9]+4)})!=w[10])
   deny("Installed source FS predecessor/handler and active private frame identity",unsigned(w[9]));
 }
 // Accepted CRT allocator/free bodies may temporarily nest their own original
 // records around an active game record. Authenticate their exact committed
 // FS install and raw predecessor; do not import host-chain bytes.
 auto head=runtime.memory().load<unsigned>({base});
 const unsigned expected=fs_active_.empty()?m4_runtime::Runtime::seh_end:unsigned(fs_records_[fs_active_.back()].words[9]);
 unsigned depth{};
 while(head!=expected){
  if(head==m4_runtime::Runtime::seh_end||++depth>8||(head&3)||head<lower_stack||std::uint64_t(head)+12>0x20002000)
   deny("Normal FS chain retains the owned game predecessor or native sentinel",head);
  const auto install=std::find_if(source_accesses_.rbegin(),source_accesses_.rend(),[&](const auto&a){return a.address==base&&a.bytes==4&&a.write&&a.value==head;});
  if(install==source_accesses_.rend()||install->pc<0x78000000||!instruction(install->pc)||
     runtime.memory().load<unsigned>({head+4})!=0x7800ef03)
   deny("Only an accepted original CRT normal frame may nest the owned guest FS chain",head);
  const auto previous=runtime.memory().load<unsigned>({head});
  if(previous!=m4_runtime::Runtime::seh_end&&previous<=head)deny("Bounded original CRT FS predecessor ordering",head);
  head=previous;
 }
}
void Binding::fs_hook(unsigned point){
 const auto records=fs_records_;const auto active=fs_active_;const auto events=fs_events_;const auto probe=fs_probe_;
 const auto accesses=fs_owner_accesses_;const auto owner_probe=fs_owner_probe_;const auto publications=fs_publications_;const auto graphs=fs_graphs_;const auto raw_records=fs_record_bytes_;
 const auto native_input=fs_native_input_;const auto admitted=fs_admitted_;
 stable_hook(point);
 if(records!=fs_records_||active!=fs_active_||events!=fs_events_||probe!=fs_probe_||accesses!=fs_owner_accesses_||owner_probe!=fs_owner_probe_||publications!=fs_publications_||graphs!=fs_graphs_||raw_records!=fs_record_bytes_||native_input!=fs_native_input_||admitted!=fs_admitted_)
  deny("FS observer changed private source-frame/chain witnesses",state.gpr.rip.dword);
}
void Binding::fs_event(unsigned index,unsigned point,unsigned before,unsigned after){
 if(index>=fs_records_.size()||fs_events_.size()>=4096)deny("Finite current FS observation index",index);
 const auto&w=fs_records_[index].words;
 const auto scope=runtime.memory().load<unsigned>({unsigned(w[9]+8)});
 fs_probe_={1,fs_events_.size(),registry_root_,index,point,state.gpr.rip.dword,runtime.fs_base().value,
  before,after,w[8],w[10],scope,w[5],source_accesses_.size(),fs_active_.size(),0};
 fs_events_.push_back(fs_probe_);
}
void Binding::fs_read_before(unsigned address,unsigned bytes){
 if(address!=runtime.fs_base().value)return;
 const auto*spec=fs_frame_read(state.gpr.rip.dword);
 if(!spec)return; // Exact inherited CRT reads retain their accepted contracts.
 if(bytes!=4||!fs_admitted_||calls_.empty())deny("Exact original normal FS0 source read",address);
 fs_guard();
 const auto&call=calls_.back();const auto frame=state.gpr.rsp.dword+8;
 if(frame!=call.frame||runtime.memory().load<unsigned>({frame})!=call.return_pc||
    runtime.memory().load<unsigned>({frame-8})!=spec->handler||runtime.memory().load<unsigned>({frame-4})!=UINT32_MAX)
  deny("Original source CALL frame and literal handler/scope pushes before FS read",frame);
 FsRecord record;
 record.words={1,fs_records_.size(),registry_root_,spec->entry,call.site,frame,call.return_pc,spec->read,
  fs_expected_,frame-12,spec->handler,UINT32_MAX,fs_active_.size(),fs_active_.empty()?0:fs_active_.back()+1,
  spec->install,0,0,0,spec->restore,0,spec->ret,0,0,call.entry,runtime.fs_base().value,m4_runtime::Runtime::seh_end,0,0,0,0,0,0};
 fs_records_.push_back(record);fs_event(unsigned(record.words[1]),80,fs_expected_,fs_expected_);fs_hook(80);
}
void Binding::fs_read_after(unsigned address,std::uint64_t value,unsigned bytes){
 const auto pc=state.gpr.rip.dword;
 if(address==runtime.fs_base().value&&fs_frame_read(pc)){
  if(bytes!=4||fs_records_.empty()||fs_records_.back().words[7]!=pc||value!=fs_records_.back().words[8])
   deny("Actual source FS0 read equals the checked current owned predecessor",address);
 }
 for(auto&record:fs_records_){auto&w=record.words;const auto*spec=fs_frame_entry(unsigned(w[3]));
  if(w[15]&&!w[19]&&w[2]==registry_root_&&spec&&pc==spec->saved){
   if(bytes!=4||address!=w[9]||value!=w[8]||fs_active_.empty()||fs_active_.back()!=w[1])
    deny("Actual epilogue source read recovers exact saved predecessor of current FS frame",address);
   w[16]=pc;w[17]=value;
  }
 }
}
void Binding::fs_write_before(unsigned address,std::uint64_t value,unsigned bytes){
 if(address!=runtime.fs_base().value)return;
 const auto pc=state.gpr.rip.dword;
 const auto*install=fs_frame_install(pc);const auto*restore=fs_frame_restore(pc);
 if(!install&&!restore)return;
 if(bytes!=4||!fs_admitted_)deny("Only exact original DWORD normal FS0 installation/restoration",address);
 fs_guard();
 if(install){
  if(fs_records_.empty())deny("FS installation requires its genuine earlier predecessor read",address);
  auto&w=fs_records_.back().words;
  if(w[3]!=install->entry||w[15]||w[2]!=registry_root_||value!=w[9]||state.gpr.rsp.dword!=w[9]||
     fs_expected_!=w[8]||runtime.memory().load<unsigned>({unsigned(w[9])})!=w[8]||
     runtime.memory().load<unsigned>({unsigned(w[9]+4)})!=w[10]||runtime.memory().load<unsigned>({unsigned(w[9]+8)})!=UINT32_MAX)
   deny("Literal FS installation commits the original complete twelve-byte source record",unsigned(value));
  const auto raw=guest_bytes(unsigned(w[9]),12);std::array<unsigned,3>actual{};std::memcpy(actual.data(),raw.data(),12);
  w[27]=actual[0];w[28]=actual[1];w[29]=actual[2];
  fs_record_bytes_.push_back({1,fs_record_bytes_.size(),w[1],registry_root_,81,pc,w[9],12,actual[0],actual[1],actual[2],source_accesses_.size(),fs_expected_,fs_active_.size(),m4_runtime::Runtime::seh_end,0});
  fs_event(unsigned(w[1]),81,fs_expected_,unsigned(value));fs_hook(81);
 }else{
  if(fs_active_.empty())deny("Source FS restore has its installed active frame",address);
  auto&w=fs_records_[fs_active_.back()].words;
  if(w[3]!=restore->entry||w[19]||!w[16]||w[17]!=value||value!=w[8]||fs_expected_!=w[9])
   deny("Literal FS restore uses exactly the saved predecessor and current owned record",unsigned(value));
  fs_event(unsigned(w[1]),83,fs_expected_,unsigned(value));fs_hook(83);
 }
}
void Binding::fs_write_after(unsigned address,std::uint64_t value,unsigned bytes){
 if(address!=runtime.fs_base().value||bytes!=4)return;
 const auto pc=state.gpr.rip.dword;
 if(fs_frame_install(pc)){
  auto&w=fs_records_.back().words;w[15]=1;fs_active_.push_back(unsigned(w[1]));
  fs_event(unsigned(w[1]),82,unsigned(w[8]),unsigned(value));fs_hook(82);
 }else if(fs_frame_restore(pc)){
  auto&w=fs_records_[fs_active_.back()].words;w[19]=1;w[22]=value;
  const auto raw=guest_bytes(unsigned(w[9]),12);std::array<unsigned,3>actual{};std::memcpy(actual.data(),raw.data(),12);
  w[26]=actual[2];w[30]=actual[0];w[31]=actual[1];
  fs_record_bytes_.push_back({1,fs_record_bytes_.size(),w[1],registry_root_,84,pc,w[9],12,actual[0],actual[1],actual[2],source_accesses_.size(),fs_expected_,fs_active_.size(),m4_runtime::Runtime::seh_end,0});
  fs_active_.pop_back();
  fs_event(unsigned(w[1]),84,unsigned(w[9]),unsigned(value));fs_hook(84);
 }
}
void Binding::fs_returned(unsigned entry,unsigned frame,unsigned return_pc){
 for(auto&record:fs_records_){auto&w=record.words;
  if(w[5]!=frame||w[21]||w[2]!=registry_root_)continue;
  if(!w[19]||w[23]!=entry||w[6]!=return_pc||fs_expected_!=w[8]||source_accesses_.empty()||
     source_accesses_.back().pc!=w[20])deny("Genuine normal frame RET follows exact FS/stack predecessor restoration",frame);
  fs_guard();if(w[3]==0x4e78d0)fs_graph_complete();w[21]=1;fs_event(unsigned(w[1]),85,unsigned(w[9]),fs_expected_);fs_hook(85);
 }
}
void Binding::dump_fs(CaptureSink sink,void*context)const{
 std::vector<std::array<std::uint64_t,32>>records;for(const auto&r:fs_records_)records.push_back(r.words);
 sink("fs-native-input.bin",std::as_bytes(std::span(fs_native_input_)),context);
 sink("fs-frame-witnesses.bin",std::as_bytes(std::span(records)),context);
 sink("fs-chain-events.bin",std::as_bytes(std::span(fs_events_)),context);
 sink("fs-chain-probe.bin",std::as_bytes(std::span(fs_probe_)),context);
 sink("fs-active-records.bin",std::as_bytes(std::span(fs_active_)),context);
 const std::array<unsigned,5>tib{runtime.fs_base().value,runtime.memory().load<unsigned>(runtime.fs_base()),
  runtime.memory().load<unsigned>({runtime.fs_base().value+4}),runtime.memory().load<unsigned>({runtime.fs_base().value+8}),runtime.memory().load<unsigned>({runtime.fs_base().value+0x18})};
 sink("fs-current-tib.bin",std::as_bytes(std::span(tib)),context);
 sink("fs-owned-accesses.bin",std::as_bytes(std::span(fs_owner_accesses_)),context);
 sink("fs-owned-access-probe.bin",std::as_bytes(std::span(fs_owner_probe_)),context);
 sink("fs-owned-publications.bin",std::as_bytes(std::span(fs_publications_)),context);
 sink("fs-shared-graph-witnesses.bin",std::as_bytes(std::span(fs_graphs_)),context);
 sink("fs-record-bytes.bin",std::as_bytes(std::span(fs_record_bytes_)),context);
}

Binding::MfcRecord*Binding::fs_mfc_owner(unsigned root,unsigned site){
 for(auto&r:mfc_records_)if(r.words[2]==root&&r.words[4]==site&&r.words[21])return &r;
 return nullptr;
}
void Binding::fs_owner_before(unsigned address,std::uint64_t value,unsigned bytes,bool writing){
 fs_owner_probe_={};
 if(!fs_root(registry_root_)||state.gpr.rip.dword>=0x78000000)return;
 auto*a=allocation_for(address,bytes);if(!a||a->kind!=4)return;
 auto*owner=mfc_for_generation(a->generation);if(!owner)deny("FS source-owned access retains actual MFC allocation provenance",address);
 const FsOwnedAccess*spec{};
 for(const auto&i:fs_owned_accesses)if(i.root==registry_root_&&i.pc==state.gpr.rip.dword&&i.bytes==bytes&&i.write==writing&&
   i.owner_root==owner->words[2]&&i.owner_call==owner->words[4]&&address==a->guest+i.offset){spec=&i;break;}
 if(!spec||std::uint64_t(address)+bytes>std::uint64_t(a->guest)+a->requested)
  deny("Exact FS root/PC/live owner generation/requested offset access",address);
 fs_owner_probe_={1,fs_owner_accesses_.size(),registry_root_,state.gpr.rip.dword,address,bytes,value,unsigned(writing),
  owner->words[2],owner->words[4],a->guest,a->generation,a->acquired,spec->offset,owner->words[1],0};
 if(writing)fs_hook(86);
}
bool Binding::fs_allowed_cross(unsigned address,unsigned bytes)const noexcept{
 return fs_owner_probe_[0]&&fs_owner_probe_[2]==registry_root_&&fs_owner_probe_[3]==state.gpr.rip.dword&&
  fs_owner_probe_[4]==address&&fs_owner_probe_[5]==bytes&&fs_owner_probe_[7]==1;
}
void Binding::fs_owner_after(unsigned address,std::uint64_t value,unsigned bytes,bool writing){
 if(fs_owner_probe_[0]){
  if(fs_owner_probe_[3]!=state.gpr.rip.dword||fs_owner_probe_[4]!=address||fs_owner_probe_[5]!=bytes||fs_owner_probe_[7]!=writing)
   deny("Genuine checked FS owned access commits its exact observation",address);
  if(fs_owner_accesses_.size()>=8192)deny("Finite FS shared-owner access ledger",address);
  fs_owner_probe_[6]=value;fs_owner_probe_[15]=source_accesses_.size();fs_owner_accesses_.push_back(fs_owner_probe_);
  if(writing)fs_hook(87);fs_owner_probe_={};
 }
 if(!writing||bytes!=4||!fs_root(registry_root_))return;
 for(const auto&spec:fs_inputs){
  if(spec.root!=registry_root_||spec.publication_pc!=state.gpr.rip.dword)continue;
  auto*r=fs_mfc_owner(spec.root,spec.call);if(!r||r->words[16]!=value)continue;
  unsigned expected=spec.publication;MfcRecord*parent{};
  if(spec.owner_root){parent=fs_mfc_owner(spec.owner_root,spec.owner_call);if(!parent)deny("Dynamic FS publication has its genuine prior allocated owner",address);expected=unsigned(parent->words[16])+spec.offset;}
  if(address!=expected||r->words[23])deny("Exact one-time source publication PC and current owned alias",address);
  ++r->words[23];fs_publications_.push_back({1,fs_publications_.size(),registry_root_,state.gpr.rip.dword,address,value,
   r->words[18],r->words[17],r->words[4],parent?parent->words[18]:0,parent?parent->words[16]:0,spec.offset,source_accesses_.size(),spec.object,0,0});
 }
}
void Binding::fs_graph_complete(){
 auto*registry=fs_mfc_owner(0x46ab30,0x4e7902);auto*sentinel=fs_mfc_owner(0x46ab30,0x4e7924);
 if(!registry||!sentinel)deny("Shared FS registry and sentinel came from genuine first-root allocation calls",0x60b888);
 const auto container=unsigned(registry->words[16]),stop=unsigned(sentinel->words[16]);
 if(!allocation_for(container,12)||!allocation_for(stop,12)||runtime.memory().load<unsigned>({0x60b888})!=container||
   runtime.memory().load<unsigned>({container+4})!=stop)deny("Shared registry retains exact acquired container/sentinel identities",container);
 const auto count=runtime.memory().load<unsigned>({container+8});unsigned expected_count{};
 for(const auto&r:mfc_records_)if(r.words[4]==0x4e795c&&r.words[21]&&r.words[23])++expected_count;
 if(!count||count>5||count!=expected_count)deny("Shared list count equals genuine committed append publications",container+8);
 auto node=runtime.memory().load<unsigned>({stop+4});unsigned previous=stop;
 std::array<std::uint64_t,16>w{1,fs_graphs_.size(),registry_root_,container,registry->words[18],stop,sentinel->words[18],count,0,0,0,0,0,0,0,source_accesses_.size()};
 for(unsigned k=0;k<count;++k){
  auto*a=allocation_for(node,12);auto*r=a?mfc_for_generation(a->generation):nullptr;
  const auto*input=r?fs_input(unsigned(r->words[2]),unsigned(r->words[4])):nullptr;
  if(!a||a->kind!=4||a->guest!=node||!r||!input||r->words[4]!=0x4e795c||!r->words[23]||
    runtime.memory().load<unsigned>({node})!=previous||runtime.memory().load<unsigned>({node+8})!=input->object)
   deny("Circular FS list node has exact live generation/link/static-object identity",node);
  w[8+k]=node;previous=node;node=runtime.memory().load<unsigned>({node+4});
 }
 if(node!=stop||runtime.memory().load<unsigned>({stop})!=previous)deny("Actual FS append links close at owned sentinel",node);
 fs_graphs_.push_back(w);
}
