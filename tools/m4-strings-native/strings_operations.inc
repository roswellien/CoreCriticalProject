// Additional private witness and source bounds; literal LLVM supplies all values.
bool string_copy_pc(unsigned pc)noexcept{switch(pc){case 0x78002fde:case 0x7800366b:case 0x7800368c:case 0x78003693:case 0x780036a5:case 0x780036ad:case 0x780036b6:return true;default:return false;}}
Binding::StringRecord*Binding::current_string()noexcept{if(string_records_.empty()||string_records_.back().words[17])return nullptr;return &string_records_.back();}
void Binding::string_hook(unsigned point){
 const auto records=string_records_;const auto probe=string_copy_probe_;
 stable_hook(point);
 if(records!=string_records_||probe!=string_copy_probe_)deny("String observer changed private exact input/ownership/copy witnesses",state.gpr.rip.dword);
}
void Binding::string_called(unsigned target,unsigned site,unsigned frame){
 if(target==0x78010a6d){
  if(current_string()||string_records_.size()>=1024)deny("One finite genuine strdup invocation at a time",target,site);
  const auto source=runtime.memory().load<unsigned>({frame+4});StringRecord record;
  record.words={1,string_records_.size(),registry_root_,target,source,frame,runtime.memory().load<unsigned>({frame}),0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,source_accesses_.size(),0,0,0,0,0,0,0};
  if(registry_root_){const auto*spec=string_input(registry_root_);if(!spec||spec->source!=source||spec->call!=site)deny("Exact fixed string pointer and actual original CALL site required",source,site);
   record.input=guest_bytes(source,spec->size);const auto physical=guest_bytes(source,spec->physical_size);if(m4::sha256(physical)!=spec->physical_sha)deny("Exact original NUL input and aligned DWORD trailing bytes required",source,site);
  }else if(source){for(unsigned n=0;n<1024*1024;++n){auto byte=guest_bytes(source+n,1)[0];record.input.push_back(byte);if(byte==std::byte{})break;}if(record.input.empty()||record.input.back()!=std::byte{})deny("Finite probe input with genuine mapped NUL required",source,site);}
  record.words[7]=record.input.size();string_records_.push_back(std::move(record));string_hook(50);return;
 }
 auto*record=current_string();if(!record)return;
 if(target==0x78002f32){if(site!=0x78010a77||runtime.memory().load<unsigned>({frame+4})!=record->words[4])deny("Genuine strdup strlen source argument required",frame,site);record->words[20]=frame;}
 if(target==malloc_entry){if(site!=0x78010a7e||runtime.memory().load<unsigned>({frame+4})!=record->words[7])deny("Genuine strlen-plus-one source malloc request required",frame,site);record->words[9]=runtime.memory().load<unsigned>({frame+4});record->words[21]=frame;}
 if(target==0x78002fab){const auto destination=runtime.memory().load<unsigned>({frame+4}),source=runtime.memory().load<unsigned>({frame+8});auto*a=allocation_for(destination,static_cast<unsigned>(record->words[7]));
  if(site!=0x78010a8b||source!=record->words[4]||destination!=record->words[10]||!a||a->kind!=3||a->requested!=record->words[7]||a->generation!=record->words[12])deny("Actual source strdup copy requires exact still-live private malloc association",frame,site);
  if(guest_bytes(source,static_cast<unsigned>(record->words[7]))!=record->input)deny("Immutable NUL-inclusive source string before literal copy",source,site);
  record->words[14]=destination;record->words[22]=frame;string_hook(52);
 }
}
void Binding::string_returned(unsigned entry,unsigned result,unsigned frame){
 auto*record=current_string();if(!record)return;
 if(entry==0x78002f32){if(frame!=record->words[20]||!record->words[7]||result+1!=record->words[7])deny("Literal strlen result must match immutable NUL-inclusive input",frame);record->words[8]=result;string_hook(51);}
 if(entry==malloc_entry){if(frame!=record->words[21])deny("Actual source malloc frame tied to strdup",frame);record->words[10]=result;if(result){auto*a=allocation_for(result);if(!a||a->guest!=result||a->kind!=3||a->requested!=record->words[9])deny("Literal returned malloc requires exact owned duplicate storage",result);record->words[11]=a->acquired;record->words[12]=a->generation;record->words[13]=a->extent;}}
 if(entry==0x78002fab){if(frame!=record->words[22]||result!=record->words[10]||record->words[16]!=record->words[7]||guest_bytes(result,static_cast<unsigned>(record->words[7]))!=record->input)deny("Genuine strcpy RET and complete committed NUL-inclusive bytes required",result);record->words[15]=result;}
 if(entry==0x78010a6d){if(frame!=record->words[5]||result!=record->words[10]||(result&&record->words[15]!=result))deny("Genuine strdup RET requires actual null or completely copied owned pointer",result);record->words[17]=1;record->words[23]=result;record->words[25]=source_accesses_.size();string_hook(55);}
}
void Binding::string_write_before(unsigned address,std::uint64_t value,unsigned bytes){
 auto*record=current_string();if(!record||!string_copy_pc(state.gpr.rip.dword))return;
 const auto base=static_cast<unsigned>(record->words[10]);if(!base||address!=base+record->words[16]||bytes>record->words[7]-record->words[16]||!allocation_for(address,bytes))deny("Literal strcpy writes only sequential requested owned string bytes",address);
 string_copy_probe_={state.gpr.rip.dword,address,bytes,value,record->words[16]};string_hook(53);
}
void Binding::string_write_after(unsigned address,unsigned bytes){
 auto*record=current_string();if(!record||!string_copy_pc(state.gpr.rip.dword))return;
 record->words[16]+=bytes;record->words[26]=state.gpr.rip.dword;record->words[27]=address;string_hook(54);
}
void Binding::dump_strings(CaptureSink sink,void*context)const{
 std::vector<std::array<std::uint64_t,32>>words;for(const auto&r:string_records_){auto w=r.words;for(const auto&a:owned_allocations_)if(a->generation==w[12]){w[18]=a->source_freed;w[19]=a->cleanup_freed;w[28]=a->native!=nullptr;w[29]=a->mapped;}words.push_back(w);const auto name="string-"+std::to_string(w[1]);sink(name+"-input.bin",r.input,context);}
 sink("strings-witnesses.bin",std::as_bytes(std::span(words)),context);sink("strings-copy-probe.bin",std::as_bytes(std::span(string_copy_probe_)),context);
}
