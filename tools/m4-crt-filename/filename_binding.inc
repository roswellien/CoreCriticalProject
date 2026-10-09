} // composition anonymous namespace
namespace mw34::m4_crt_filename {
void checkpoint(m4_runtime::Runtime&,const char*);
void Binding::first(const char*w,unsigned address,unsigned pc){if(!failed){failed=true;reason=w;fault_pc=pc;fault_address=address;}}
[[noreturn]]void Binding::deny(const char*w,unsigned address,unsigned pc){first(w,address,pc);context.deny(w,address,pc);}
void Binding::guard(){if(m4_crt_entry_mainargs::owner&&m4_crt_entry_mainargs::owner!=&context)m4_crt_entry_mainargs::owner->deny("Filename side binding cannot use stale mainargs Context",mg::import_slot,mg::import_call);context.guard();if(current(context)!=this||m4_crt_entry_initerm::owner||m4_crt_control_integration::owner||m4_crt_matherr_paired_native::owner)deny("Exact exclusive filename/current mainargs owner required");}
void Binding::witness_closure(unsigned point){
 const bool lifecycle=(point==2&&active&&!stored&&!returned&&!stopped)||(point==3&&active&&stored&&!returned&&!stopped)||(point==4&&active&&stored&&returned&&!stopped)||(point==5&&!active&&stored&&returned&&!stopped);
 if(frame!=admitted_frame_||context.frame!=admitted_frame_+44||!used||!api_called||failed||!lifecycle||stage!=point||hook_count!=point||std::memcmp(&witness,&actual_witness_,sizeof(Witness))||result!=actual_witness_.result||last_error!=actual_witness_.last_error)deny("Immutable actual filename API witness/frame/progress changed",buffer,point>=4?stop_pc:mg::import_call);
}
void Binding::closure(State*s,unsigned target){
 guard();if(frame!=admitted_frame_||context.frame!=admitted_frame_+44)deny("Exact immutable filename admitted frame required",admitted_frame_);context.source_identity();auto&r=context.runtime;auto&c=context;
 if(c.stage!=2||s!=&c.state||target!=c.provider_raw||c.state.gpr.rip.dword!=target||c.state.gpr.rsp.dword!=c.frame-44||c.access_count!=16)deny("Actual filename CALL source/frame rejected",target);
 const auto&rd=c.accesses[14];const auto&wr=c.accesses[15];
 if(rd.pc!=mg::import_call||rd.address!=mg::import_slot||rd.value!=target||rd.write||wr.pc!=mg::import_call||wr.address!=c.frame-44||wr.value!=mg::import_return||!wr.write)deny("Actual filename source IAT/return access rejected",mg::import_slot);
 if(r.memory().load<unsigned>({mg::import_slot})!=c.provider_raw||r.memory().load<unsigned>({c.frame-44})!=mg::import_return||r.memory().load<unsigned>({c.frame-40})!=0||r.memory().load<unsigned>({c.frame-36})!=buffer||r.memory().load<unsigned>({c.frame-32})!=capacity)deny("Actual filename NULL/module/buffer/capacity/return closure rejected",c.frame-44);
 if(r.cpu().eip!=mg::slot||r.cpu().esp!=c.frame)deny("Filename internal route must retain outer Runtime CPU",mg::slot);
}
void Binding::hook(unsigned point){stage=point;++hook_count;
 if(point==1){
  if(control==61)context.runtime.memory().store<unsigned>({frame},mg::import_return^1);
  if(control==63)mainargs_change(context,mg::import_slot,context.provider_raw^1);
  if(control==64)mainargs_change(context,mg::builder,0);
  if(control==65)context.runtime.memory().store<unsigned>({frame+4},1);
  if(control==66)context.runtime.memory().store<unsigned>({frame+12},259);
  if(control==67)throw std::runtime_error("Authored filename admission observer exception");
 }
 if(point==2){if(control==62)context.runtime.memory().protect({buffer&~4095U},Permissions::read);if(control==68)throw std::runtime_error("Authored filename API observer exception");if(control==71)context.runtime.memory().store<unsigned>({frame},mg::import_return^1);if(control==72)context.state.gpr.rsi.dword^=1;}
 if(point==3&&control==69)throw std::runtime_error("Authored filename buffer observer exception");
 if(point==4&&control==70)throw std::runtime_error("Authored filename RET observer exception");
 if(extra)extra(*this,point);
}
void Binding::invoke(State*s,unsigned target,void*p){
 LastErrorBoundary errors;InvocationHostBoundary fp;
 guard();if(p!=&context)deny("Exact filename opaque token required",target);if(used||active||failed)deny("Filename service is single use",target);
 caller_error=errors.saved;errors.restored=&restored_error;
 used=true;active=true;admitted_frame_=context.frame-44;frame=admitted_frame_;
 try{
  closure(s,target);checkpoint(context.runtime,"filename-before");hook(1);
  if(!used||!active||api_called||stored||returned||stopped||failed||stage!=1||hook_count!=1)deny("Exact filename admission lifecycle before actual API required",admitted_frame_);
  closure(s,target);
  try{context.runtime.memory().read({buffer},witness.before);}catch(...){deny("Checked full filename guest buffer read rejected",buffer);}
  const auto saved_state=context.state;std::array<std::byte,512>saved_fx{};std::copy(context.runtime.fx().begin(),context.runtime.fx().end(),saved_fx.begin());
  const auto named=GetModuleHandleW(L"kernel32.dll");const auto procedure=GetProcAddress(named,"GetModuleFileNameA");
  api_before=fd::host_identity(procedure,named,"GetModuleFileNameA");module_before=fd::module_identity(GetModuleHandleW(nullptr));
  context.event(4,mg::import_call,mg::import_slot,target);context.reached_import=true;
  witness=native_filename(capacity,incoming_error,witness.before,procedure);result=witness.result;last_error=witness.last_error;api_called=true;
  actual_witness_=witness;
  api_after=fd::host_identity(procedure,named,"GetModuleFileNameA");module_after=fd::module_identity(GetModuleHandleW(nullptr));
  if(!(api_before==api_after)||!(module_before==module_after))deny("Actual filename native API/module identity changed",mg::import_slot);
  checkpoint(context.runtime,"filename-api-after");hook(2);witness_closure(2);closure(s,target);
  if(std::memcmp(&saved_state,&context.state,sizeof(State))||!std::equal(saved_fx.begin(),saved_fx.end(),context.runtime.fx().begin()))deny("Filename service carried State/FX changed before publication",buffer);
  try{context.runtime.memory().write({buffer},actual_witness_.after);}catch(...){deny("Checked atomic full filename guest buffer write rejected",buffer);}
  stored=true;checkpoint(context.runtime,"filename-buffer-after");hook(3);witness_closure(3);if(!stored||returned)deny("Filename stored progress changed before RET",buffer);closure(s,target);
  if(std::memcmp(&saved_state,&context.state,sizeof(State))||!std::equal(saved_fx.begin(),saved_fx.end(),context.runtime.fx().begin()))deny("Filename service carried State/FX changed after guest buffer store",buffer);
  std::array<std::byte,260>actual{};context.runtime.memory().read({buffer},actual);if(actual!=actual_witness_.after)deny("Filename API buffer changed after checked transfer",buffer);
  context.state.gpr.rax.dword=actual_witness_.result;context.state.gpr.rsp.dword=admitted_frame_+16;context.state.gpr.rip.dword=mg::import_return;returned=true;
  std::memcpy(return_state_.data(),&context.state,sizeof(State));std::copy(context.runtime.fx().begin(),context.runtime.fx().end(),return_fx_.begin());
  context.event(5,mg::import_return,admitted_frame_+16,result);checkpoint(context.runtime,"filename-return-after");hook(4);witness_closure(4);active=false;
 }catch(...){first(context.failed?context.reason:"Filename observer or host exception",context.failed?context.fault_address:buffer,context.failed?context.fault_pc:context.state.gpr.rip.dword);active=false;throw;}
}
[[noreturn]]void Binding::stop(unsigned address,void*p){
 LastErrorBoundary errors;InvocationHostBoundary fp;guard();
 try{
 if(frame!=admitted_frame_||context.frame!=admitted_frame_+44||p!=&context||!returned||active||failed||address!=commandline||context.state.gpr.rip.dword!=stop_pc||context.state.gpr.rsp.dword!=admitted_frame_+16)deny("Exact filename return/next command-line read token rejected",address,stop_pc);
 context.source_identity();checkpoint(context.runtime,"filename-commandline-before");hook(5);guard();context.source_identity();witness_closure(5);if(!stored||!returned||active||stopped)deny("Filename returned progress changed before command-line read",address,stop_pc);
 if(std::memcmp(return_state_.data(),&context.state,sizeof(State))||!std::equal(return_fx_.begin(),return_fx_.end(),context.runtime.fx().begin()))deny("Filename next command-line read State/FX changed",address,stop_pc);
 stopped=true;context.event(6,stop_pc,commandline,0);context.first("Required initialized CRT command-line producer remains unresolved",commandline,stop_pc);
 throw m4_runtime::Fault(m4_runtime::FaultReason::unresolved_translation,{stop_pc},{commandline},context.reason);
 }catch(const m4_runtime::Fault&){throw;}catch(...){first(context.failed?context.reason:"Filename stop observer or host exception",context.failed?context.fault_address:commandline,context.failed?context.fault_pc:stop_pc);throw;}
}
}
namespace {
