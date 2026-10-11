// Exact finite indirect source calls. Literal COFF bodies provide all effects.
void Binding::vtable_hook(unsigned point){stable_hook(point);}
void Binding::vtable_read_before(unsigned address,unsigned bytes){
 const auto pc=state.gpr.rip.dword;const auto*spec=vtable_input(registry_root_,pc);
 if(pc==0x59ff64&&vtable_root(registry_root_)){
  const auto*next=vtable_input(registry_root_,0x59ff6e);
  if(!next||bytes!=4||address!=next->object||state.gpr.rcx.dword!=next->ecx)deny("Exact live instance source vptr read geometry",address,pc);
  vtable_read_probe_={1,registry_root_,pc,address,bytes,next->vtable,source_accesses_.size(),1};vtable_hook(110);return;
 }
 if(!spec)return;
 if(bytes!=4||address!=spec->slot||state.gpr.rcx.dword!=spec->ecx)deny("Exact finite indirect source cell/ECX read geometry",address,pc);
 if(spec->vtable&&(state.gpr.rdx.dword!=spec->vtable||vtable_vptr_[1]!=registry_root_||vtable_vptr_[3]!=spec->object||vtable_vptr_[4]!=spec->vtable))deny("Virtual source cell retains actual instance vptr and loaded EDX",address,pc);
 vtable_read_probe_={1,registry_root_,pc,address,bytes,spec->target,source_accesses_.size(),0};vtable_hook(110);
}
void Binding::vtable_read_after(unsigned address,std::uint64_t value,unsigned bytes){
 const auto pc=state.gpr.rip.dword;
 if(pc==0x59ff64&&vtable_root(registry_root_)){
  const auto*spec=vtable_input(registry_root_,0x59ff6e);const SourceAccess*publication{};
  for(auto i=source_accesses_.rbegin();i!=source_accesses_.rend();++i)if(i->write&&i->address==spec->object&&i->bytes==4){publication=&*i;break;}
  if(bytes!=4||address!=spec->object||value!=spec->vtable||!publication||publication->pc!=spec->publication_pc||publication->value!=value)deny("Actual live instance vptr follows its exact committed source publication",address,pc);
  vtable_vptr_={1,registry_root_,pc,address,value,source_accesses_.size()-1,static_cast<std::uint64_t>(publication-source_accesses_.data()),spec->publication_pc};vtable_hook(111);return;
 }
 const auto*spec=vtable_input(registry_root_,pc);if(!spec)return;
 if(bytes!=4||address!=spec->slot||value!=spec->target||vtable_active_||vtable_records_.size()>=128)deny("Exact physical finite indirect cell target and one active call",address,pc);
 std::array<std::uint64_t,32>w{1,vtable_records_.size(),registry_root_,pc,address,value,value,pc,source_accesses_.size()-1,state.gpr.rcx.dword,
  spec->vtable?vtable_vptr_[4]:0,spec->vtable,spec->vtable?vtable_vptr_[6]:0,spec->vtable?vtable_vptr_[5]:0,0,0,0,spec->cleanup,0,0,0,0,source_accesses_.size()-1,0,fs_expected_,0,native_apis_.size(),0,live_allocations(),0,0,0};
 vtable_records_.push_back(w);vtable_active_=unsigned(w[1])+1;vtable_hook(111);
}
void Binding::vtable_called(unsigned target,unsigned site,unsigned frame){
 const auto*spec=vtable_input(registry_root_,site);
 if(!spec){if(target==0x59ff80&&vtable_root(registry_root_))deny("Unadmitted virtual pointer source CALL site",frame,site);return;}
 if(!vtable_active_)deny("Finite indirect CALL retains actual owning source cell read",frame,site);
 auto&w=vtable_records_[vtable_active_-1];const auto*ins=instruction(site);
 if(w[2]!=registry_root_||w[3]!=site||w[6]!=target||target!=spec->target||state.gpr.rcx.dword!=spec->ecx||!ins||runtime.memory().load<unsigned>({frame})!=site+ins->length)deny("Exact genuine finite indirect CALL frame/target/ECX",frame,site);
 const auto argument=spec->argument==UINT_MAX?0ULL:runtime.memory().load<unsigned>({frame+4});
 if(spec->argument!=UINT_MAX&&argument!=spec->argument)deny("Normal finite indirect constructor pointer argument must be zero before pointee dereference",frame+4,site);
 w[14]=frame;w[15]=runtime.memory().load<unsigned>({frame});w[16]=argument;vtable_hook(112);
}
void Binding::vtable_returned(unsigned entry,unsigned result,unsigned frame){
 if(!vtable_active_)return;auto&w=vtable_records_[vtable_active_-1];if(w[6]!=entry)return;
 if(frame!=w[14]||state.gpr.rsp.dword!=frame+4+w[17]||state.gpr.rip.dword!=w[15]||native_apis_.size()!=w[26]||live_allocations()!=w[28]||fs_expected_!=w[24])deny("Finite indirect literal RET preserves genuine cleanup/source owner/API/chain",frame);
 w[18]=state.gpr.rsp.dword;w[19]=result;w[20]=source_accesses_.back().pc;w[21]=1;w[23]=source_accesses_.size();w[25]=fs_expected_;w[27]=native_apis_.size();w[29]=live_allocations();vtable_hook(113);vtable_active_=0;
}
void Binding::vtable_write_before(unsigned address,std::uint64_t value,unsigned bytes){
 if(!vtable_root(registry_root_)||address>=0x20000000)return;
 const auto*ins=instruction(state.gpr.rip.dword);if(!ins||(bare_mnemonic(*ins)!="mov"&&bare_mnemonic(*ins)!="or"))return;
 bool explicit_store{};for(unsigned k=0;k<ins->count;++k)if(ins->operands[k].kind==3&&(ins->operands[k].access&2))explicit_store=true;if(!explicit_store)return;
 if(vtable_stores_.size()>=256)deny("Finite exact game object store ledger",address);
 vtable_store_probe_={1,vtable_stores_.size(),registry_root_,state.gpr.rip.dword,address,bytes,value,source_accesses_.size(),0,fs_expected_,vtable_active_,0,0,0,0,0};vtable_hook(114);
}
void Binding::vtable_write_after(unsigned address,std::uint64_t value,unsigned bytes){
 if(vtable_store_probe_[0]!=1||vtable_store_probe_[3]!=state.gpr.rip.dword||vtable_store_probe_[4]!=address||vtable_store_probe_[5]!=bytes||vtable_store_probe_[6]!=value)return;
 vtable_store_probe_[8]=source_accesses_.size();vtable_stores_.push_back(vtable_store_probe_);vtable_hook(115);vtable_store_probe_={};
}
void Binding::dump_vtable(CaptureSink sink,void*context)const{
 sink("vtable-call-witnesses.bin",std::as_bytes(std::span(vtable_records_)),context);sink("vtable-source-stores.bin",std::as_bytes(std::span(vtable_stores_)),context);
 sink("vtable-read-probe.bin",std::as_bytes(std::span(vtable_read_probe_)),context);sink("vtable-instance-vptr.bin",std::as_bytes(std::span(vtable_vptr_)),context);sink("vtable-store-probe.bin",std::as_bytes(std::span(vtable_store_probe_)),context);sink("vtable-active.bin",std::as_bytes(std::span(&vtable_active_,1)),context);
}
