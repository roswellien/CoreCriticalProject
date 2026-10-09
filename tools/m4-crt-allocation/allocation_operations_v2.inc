// This is included inside the fresh allocation namespace. Every source effect
// below is performed by literal lifted objects; the plans only check operands.
void Binding::configure_request(unsigned n){
 if(started_||active||used||authority||binding==this||n>4096)throw std::invalid_argument("Fresh bounded allocator request input required");
 request_private_=requested_size=n;allocator_snapshot();
}
bool Binding::allocation_token_valid(unsigned p)const noexcept{
 return authority_is_current()&&owned_handle_&&owned_allocation_&&allocation_mapped_&&p==allocation_address&&allocation_guest_private_==p;
}
std::array<unsigned,16>Binding::allocation_progress()const noexcept{return {1,unsigned(caller_cleaned_private_),unsigned(malloc_returned_private_),
 unsigned(client_verified_private_),unsigned(free_returned_private_),unsigned(null_free_returned_private_),unsigned(batch_complete_private_),
 request_private_,allocation_extent_private_,allocation_phase_private_,allocator_plan_index_,unsigned(allocator_plan_.size()),allocator_start_access_,
 unsigned(owned_allocation_!=nullptr),unsigned(allocation_mapped_),fs_expected_};}
void Binding::allocator_snapshot()noexcept{
 requested_size=request_private_;allocation_phase=allocation_phase_private_;allocation_guest=allocation_guest_private_;
 allocation_extent=allocation_extent_private_;allocation_output_count=allocation_output_private_;external_count=external_count_private_;
 caller_cleaned=caller_cleaned_private_;malloc_returned=malloc_returned_private_;client_verified=client_verified_private_;
 free_returned=free_returned_private_;null_free_returned=null_free_returned_private_;batch_complete=batch_complete_private_;
 allocation_witness=allocation_witness_private_;
 allocation_registry={1,reinterpret_cast<std::uintptr_t>(this),1,allocation_guest_private_,acquired_allocation_,
  request_private_,allocation_extent_private_,allocation_mapped_?4096U:0U,alloc_calls_,unsigned(owned_allocation_!=nullptr),
  free_calls_,free_successes_,unsigned(allocation_mapped_),unsigned(!allocation_pattern_private_.empty()),unsigned(client_verified_private_),
  unsigned(malloc_returned_private_),unsigned(free_returned_private_),cleanup_free_calls_,cleanup_free_successes_,allocation_denials_,
  acquired_handle_,acquired_allocation_,malloc_marker,free_marker};
}
void Binding::allocator_guard(){
 if(requested_size!=request_private_||allocation_phase!=allocation_phase_private_||allocation_guest!=allocation_guest_private_||
  allocation_extent!=allocation_extent_private_||allocation_output_count!=allocation_output_private_||external_count!=external_count_private_||
  caller_cleaned!=caller_cleaned_private_||malloc_returned!=malloc_returned_private_||client_verified!=client_verified_private_||
  free_returned!=free_returned_private_||null_free_returned!=null_free_returned_private_||batch_complete!=batch_complete_private_)
  deny("Immutable private allocation progress and requested input required",malloc_entry);
 for(auto [slot,raw]:std::array<std::pair<unsigned,unsigned>,2>{{{alloc_iat,alloc_raw},{free_iat,free_raw}}}){unsigned value{};try{value=runtime.memory().load<unsigned>({slot});}catch(...){deny("Checked original allocator IAT identity",slot);}if(value!=raw)deny("Exact raw named original allocator import required",slot);}
 auto old=allocation_registry;const auto old_witness=allocation_witness;allocator_snapshot();if(old!=allocation_registry||old_witness!=allocation_witness_private_||
  allocation_initial!=allocation_initial_private_||allocation_pattern!=allocation_pattern_private_)
  deny("Private full allocation ownership, API witness and byte mirrors required",allocation_address);
 if(state.addr.fs_base.dword!=runtime.fs_base().value||runtime.memory().load<unsigned>(runtime.fs_base())!=fs_expected_)
  deny("Only genuine source SEH registration/restoration may change carried FS chain",runtime.fs_base().value);
 std::array<std::byte,4096>upper{};runtime.memory().read({0x20001000},upper);
 if(upper!=upper_expected_)deny("Only committed source/API/external caller writes may change upper research stack",0x20001000);
 for(const auto&[a,expected]:allocator_sources_){std::vector<std::byte>actual(expected.size());runtime.memory().read({a},actual);
  if(actual!=expected)deny("Exact full source allocator/caller identity required",a);}
 if(allocation_mapped_){std::vector<std::byte>actual(4096);runtime.memory().read({allocation_address},actual);
  if(actual!=allocation_expected_)deny("Only declared native output/client synchronization may change allocation backing",allocation_address);
  if(owned_allocation_&&std::memcmp(owned_allocation_,allocation_expected_.data(),allocation_extent_private_))
   deny("Privately owned full native allocation and guest backing must agree",allocation_address);}
}
void Binding::committed_stack_write(unsigned a,unsigned v){
 if(a>=0x20001000&&std::uint64_t(a)+4<=0x20002000)std::memcpy(upper_expected_.data()+a-0x20001000,&v,4);
 if(a>=lower_stack&&std::uint64_t(a)+4<=std::uint64_t(lower_stack)+4096)std::memcpy(lower_expected_.data()+a-lower_stack,&v,4);
 if(query_bound_&&a>=query_pointer_private_&&std::uint64_t(a)+4<=std::uint64_t(query_pointer_private_)+148)
  std::memcpy(query_expected_.data()+a-query_pointer_private_,&v,4);
 if(a==runtime.fs_base().value)fs_expected_=v;
}
void Binding::external_call(unsigned pc,unsigned arg,unsigned marker){
 guard();source_identity();if(state.gpr.rsp.dword!=admitted_parent_frame_||!caller_cleaned_private_||!owned_handle_)
  deny("External cdecl caller requires authentic cleaned source frame and live heap",pc);
 allocator_frame_=admitted_parent_frame_-8;allocator_start_access_=access_count;allocator_plan_index_=0;allocator_depth_=0;operation_returned_=false;
 allocator_saved_ebp_=state.gpr.rbp.dword;allocator_saved_ebx_=state.gpr.rbx.dword;allocator_saved_esi_=state.gpr.rsi.dword;allocator_saved_edi_=state.gpr.rdi.dword;
 fs_previous_=fs_expected_;allocator_newmode_=runtime.memory().load<unsigned>({mg::newmode});
 for(auto [a,v]:std::array<std::pair<unsigned,unsigned>,2>{{{allocator_frame_+4,arg},{allocator_frame_,marker}}}){
  if(external_count_private_==external_accesses.size())deny("Bounded external caller store ledger",a);
  runtime.memory().store<unsigned>({a},v);committed_stack_write(a,v);
  external_accesses[external_count_private_++]={pc,a,v,4,1};external_count=external_count_private_;
 }
 if(external_projection_count_==external_projections.size())deny("Bounded external caller projection ledger",pc);
 external_projections[external_projection_count_++]={1,state.gpr.rip.dword,state.gpr.rsp.dword,pc,allocator_frame_,arg,allocator_frame_,marker};
 state.gpr.rsp.dword=allocator_frame_;state.gpr.rip.dword=pc;allocator_snapshot();
 if(pc==malloc_entry)make_malloc_plan();else make_free_plan(arg);
}
void Binding::make_malloc_plan(){
 const auto M=allocator_frame_;allocator_plan_.clear();
 auto A=[&](unsigned pc,unsigned a,unsigned v,unsigned w){allocator_plan_.push_back({pc,a,v,4,w});};
 A(0x780012b3,mg::newmode,allocator_newmode_,0);A(0x780012b3,M-4,allocator_newmode_,1);
 A(0x780012b9,M+4,request_private_,0);A(0x780012b9,M-8,request_private_,1);A(0x780012bd,M-12,0x780012c2,1);
 A(0x780012c5,M-8,request_private_,0);A(0x780012d0,M-8,request_private_,0);A(0x780012d0,M-16,request_private_,1);A(0x780012d4,M-20,0x780012d9,1);
 A(0x780012e3,M-24,allocator_saved_ebp_,1);A(0x780012e6,M-28,0xffffffffU,1);A(0x780012e8,M-32,0x7802e248,1);A(0x780012ed,M-36,0x7800ef03,1);
 A(0x780012f2,runtime.fs_base().value,fs_previous_,0);A(0x780012f8,M-40,fs_previous_,1);A(0x780012f9,runtime.fs_base().value,M-40,1);
 A(0x78001303,M-56,allocator_saved_ebx_,1);A(0x78001304,M-60,allocator_saved_esi_,1);A(0x78001305,M-64,allocator_saved_edi_,1);A(0x78001306,global+4,1,0);
 A(0x7800cc97,M-16,request_private_,0);if(!request_private_){A(0x7800cc9e,M-68,1,1);A(0x7800cca0,M-68,1,0);}
 allocation_extent_private_=((request_private_?request_private_:1)+15)&~15U;
 A(0x7800cca6,M-68,allocation_extent_private_,1);A(0x78001377,M-72,0,1);A(0x78001379,global,token,0);A(0x78001379,M-76,token,1);
 A(alloc_site,alloc_iat,alloc_raw,0);A(alloc_site,M-80,alloc_return,1);
 A(0x78001367,M-40,fs_previous_,0);A(0x7800136a,runtime.fs_base().value,fs_previous_,1);
 A(0x78001371,M-64,allocator_saved_edi_,0);A(0x78001372,M-60,allocator_saved_esi_,0);A(0x78001373,M-56,allocator_saved_ebx_,0);A(0x78001374,M-24,allocator_saved_ebp_,0);
 A(0x78001375,M-20,0x780012d9,0);A(0x780012db,M-16,request_private_,0);
 A(0x780012e2,M-12,0x780012c2,0);A(0x780012c2,M-8,request_private_,0);A(0x780012c3,M-4,allocator_newmode_,0);A(0x780012c4,M,malloc_marker,0);
 allocator_snapshot();
}
void Binding::make_free_plan(unsigned pointer){
 const auto F=allocator_frame_;allocator_plan_.clear();
 auto A=[&](unsigned pc,unsigned a,unsigned v,unsigned w){allocator_plan_.push_back({pc,a,v,4,w});};
 A(0x78001390,F-4,allocator_saved_ebp_,1);A(0x78001393,F-8,0xffffffffU,1);A(0x78001395,F-12,0x7802e260,1);A(0x7800139a,F-16,0x7800ef03,1);
 A(0x7800139f,runtime.fs_base().value,fs_previous_,0);A(0x780013a5,F-20,fs_previous_,1);A(0x780013a6,runtime.fs_base().value,F-20,1);
 A(0x780013b0,F-48,allocator_saved_ebx_,1);A(0x780013b1,F-52,allocator_saved_esi_,1);A(0x780013b2,F-56,allocator_saved_edi_,1);A(0x780013b3,F+4,pointer,0);
 if(pointer){A(0x780013ba,global+4,1,0);A(0x7800cc39,F-60,pointer,1);A(0x78001428,F-64,0,1);A(0x7800142a,global,token,0);A(0x7800142a,F-68,token,1);A(free_site,free_iat,free_raw,0);A(free_site,F-72,free_return,1);}
 A(0x78001416,F-20,fs_previous_,0);A(0x78001419,runtime.fs_base().value,fs_previous_,1);A(0x78001420,F-56,allocator_saved_edi_,0);A(0x78001421,F-52,allocator_saved_esi_,0);A(0x78001422,F-48,allocator_saved_ebx_,0);A(0x78001423,F-4,allocator_saved_ebp_,0);A(0x78001424,F,free_marker,0);
 allocator_snapshot();
}
unsigned Binding::allocator_read32(unsigned a){
 if(allocator_plan_index_>=allocator_plan_.size())deny("Source allocation access exceeds exact path plan",a);
 const auto&expected=allocator_plan_[allocator_plan_index_];
 if(expected.write||expected.pc!=state.gpr.rip.dword||expected.address!=a)deny("Exact literal allocator read PC/operand required",a);
 unsigned value{};try{value=runtime.memory().load<unsigned>({a});}catch(...){deny("Checked authentic allocator source read fault",a);}
 if(value!=expected.value)deny("Exact source-carried allocator read value required",a);
 ++allocator_plan_index_;record(a,value,0);return value;
}
void Binding::allocator_write32(unsigned a,unsigned v){
 if(allocator_plan_index_>=allocator_plan_.size())deny("Source allocation access exceeds exact path plan",a);
 const auto&expected=allocator_plan_[allocator_plan_index_];
 if(!expected.write||expected.pc!=state.gpr.rip.dword||expected.address!=a||expected.value!=v)deny("Exact literal allocator store PC/operand/value required",a);
 try{runtime.memory().store<unsigned>({a},v);}catch(...){deny("Checked authentic allocator source store fault",a);}
 committed_stack_write(a,v);++allocator_plan_index_;record(a,v,1);
 if(a==runtime.fs_base().value){const bool install=v!=fs_previous_;const char*name=allocation_phase_private_==2?
  (install?"allocation-malloc-seh-installed":"allocation-malloc-seh-restored"):
  allocation_phase_private_==4?(install?"allocation-free-seh-installed":"allocation-free-seh-restored"):
  (install?"allocation-null-free-seh-installed":"allocation-null-free-seh-restored");checkpoint(runtime,name);}
}
unsigned char Binding::allocator_undefined(){
 const auto pc=state.gpr.rip.dword;
 if(!((allocation_phase_private_==2&&(pc==0x7800cc9a||pc==0x7800cca4||pc==0x780012d9))||
      ((allocation_phase_private_==4||allocation_phase_private_==5)&&pc==0x780013b6)))
  deny("Only exact generated allocator TEST/AND AF sites are admitted",pc);
 unsigned required_count{},next_pc{};
 if(allocation_phase_private_==2){if(pc==0x7800cc9a){required_count=6;next_pc=request_private_?0x7800cca6:0x7800cc9e;}
  else if(pc==0x7800cca4){required_count=7;next_pc=0x7800cca6;}else{required_count=8;next_pc=0x780012db;}}
 else{required_count=allocation_phase_private_==4?9:10;next_pc=allocation_phase_private_==4?0x780013ba:0x78001416;}
 if(undefined_count!=required_count||allocator_plan_index_>=allocator_plan_.size()||allocator_plan_[allocator_plan_index_].pc!=next_pc)
  deny("Only once at the exact literal allocator access position is generated AF admitted",pc);
 if(undefined_count==undefined_sites.size())deny("Bounded allocator generated AF ledger",pc);
 undefined_sites[undefined_count++]=pc;return 0;
}
void*Binding::allocator_called(State*s,unsigned target,void*p){
 if(s!=&state||p!=this||state.gpr.rip.dword!=target||!allocator_plan_index_)deny("Exact allocator CALL State and private token required",target);
 const auto&w=accesses[access_count-1];if(!w.write||w.address!=state.gpr.rsp.dword)deny("Genuine allocator CALL committed return word required",target);
 if(allocation_phase_private_==2&&target==size_entry&&w.pc==0x780012bd&&w.value==0x780012c2&&allocator_depth_==0){
  allocator_depth_=1;event(20,w.pc,target,w.value);return mw34_allocation_size_body(s,target,this);}
 if(allocation_phase_private_==2&&target==worker_entry&&w.pc==0x780012d4&&w.value==0x780012d9&&allocator_depth_==1){
  allocator_depth_=2;event(21,w.pc,target,w.value);return mw34_allocation_worker_body(s,target,this);}
 if(allocation_phase_private_==2&&target==alloc_raw&&w.pc==alloc_site&&w.value==alloc_return&&allocator_depth_==2){
  allocator_api_frame_=allocator_frame_-80;event(22,alloc_site,alloc_iat,alloc_raw);allocation_api();return this;}
 if(allocation_phase_private_==4&&target==free_raw&&w.pc==free_site&&w.value==free_return&&allocator_depth_==0){
  allocator_api_frame_=allocator_frame_-72;event(23,free_site,free_iat,free_raw);free_api();return this;}
 deny("Unadmitted allocator helper/API CALL remains unresolved",target,w.pc);
}
void*Binding::allocator_returned(State*s,unsigned target,void*p){
 if(s!=&state||p!=this||state.gpr.rip.dword!=target||!allocator_plan_index_)deny("Exact allocator RET State/private token required",target);
 const auto&r=accesses[access_count-1];if(r.write||r.value!=target)deny("Genuine allocator source RET read required",target);
 if(allocation_phase_private_==2&&target==0x780012d9&&r.pc==0x78001375&&allocator_depth_==2){allocator_depth_=1;event(24,r.pc,target,r.address);return this;}
 if(allocation_phase_private_==2&&target==0x780012c2&&r.pc==0x780012e2&&allocator_depth_==1){allocator_depth_=0;event(25,r.pc,target,r.address);return this;}
 if(allocator_depth_||allocator_plan_index_!=allocator_plan_.size()||state.gpr.rsp.dword!=allocator_frame_+4||
  state.gpr.rbp.dword!=allocator_saved_ebp_||state.gpr.rbx.dword!=allocator_saved_ebx_||state.gpr.rsi.dword!=allocator_saved_esi_||state.gpr.rdi.dword!=allocator_saved_edi_||fs_expected_!=fs_previous_)
  deny("Complete source allocator RET must restore original cdecl/nonvolatile/FS frame",target);
 if(allocation_phase_private_==2&&target==malloc_marker&&r.pc==0x780012c4&&state.gpr.rax.dword==allocation_guest_private_){
  malloc_returned_private_=true;operation_returned_=true;allocator_snapshot();event(26,r.pc,target,r.address);checkpoint(runtime,"allocation-malloc-returned");stable_hook(31);return this;}
 if((allocation_phase_private_==4||allocation_phase_private_==5)&&target==free_marker&&r.pc==0x78001424){
  if(allocation_phase_private_==4)free_returned_private_=true;else null_free_returned_private_=true;
  operation_returned_=true;allocator_snapshot();event(27,r.pc,target,r.address);checkpoint(runtime,allocation_phase_private_==4?"allocation-free-returned":"allocation-null-free-returned");stable_hook(36);return this;}
 deny("Unadmitted source allocator return target",target);
}
void*Binding::allocator_missing(State*s,unsigned target,void*p){
 if(s!=&state||p!=this||state.gpr.rip.dword!=target)deny("Exact source allocator continuation State/private token required",target);
 if(allocation_phase_private_==2&&allocator_depth_==2&&target==0x7800cc97)return mw34_allocation_round_body(s,target,this);
 if(allocation_phase_private_==2&&allocator_depth_==2&&target==0x78001377){
  // Full worker object begins at12E3 and cannot be restarted here. Preparation
  // provides a separate literal tail object for this discontiguous cold return.
  return mw34_allocation_alloc_tail_body(s,target,this);}
 if(allocation_phase_private_==4&&target==0x7800cc39)return mw34_allocation_freecold_body(s,target,this);
 if(allocation_phase_private_==4&&target==0x78001428)return mw34_allocation_free_tail_body(s,target,this);
 if((allocation_phase_private_==4||allocation_phase_private_==5)&&target==0x78001416)return mw34_allocation_free_epilogue_body(s,target,this);
 if(allocation_phase_private_==2&&target==0x78001367)return mw34_allocation_worker_epilogue_body(s,target,this);
 if(allocation_phase_private_==2&&allocator_depth_==1&&target==0x7800cc3f&&!allocation_guest_private_&&allocator_newmode_==0)return mw34_allocation_null_body(s,target,this);
 if(allocation_phase_private_==2&&allocator_depth_==1&&target==0x780012e2&&!allocation_guest_private_&&allocator_newmode_==0)return mw34_allocation_size_ret_body(s,target,this);
 deny("Unadmitted allocator branch/exception/small-block path remains unresolved",target);
}
void Binding::allocation_api(){
 const auto M=allocator_frame_;if(!owned_handle_||owned_allocation_||alloc_calls_||state.gpr.rsp.dword!=M-80||
  runtime.memory().load<unsigned>({M-80})!=alloc_return||runtime.memory().load<unsigned>({M-76})!=token||
  runtime.memory().load<unsigned>({M-72})||runtime.memory().load<unsigned>({M-68})!=allocation_extent_private_)
  deny("Genuine HeapAlloc source handle/flags/rounded size/return closure required",alloc_iat,alloc_site);
 (void)owns_token(token);auto preflight=runtime.memory();preflight.map({allocation_address},4096,Permissions::read|Permissions::write);
 alloc_before=measured_api("HeapAlloc",reinterpret_cast<std::uintptr_t>(&::HeapAlloc));free_before=measured_api("HeapFree",reinterpret_cast<std::uintptr_t>(&::HeapFree));
 checkpoint(runtime,"allocation-native-before");stable_hook(26);guard();source_identity();
 {auto final_preflight=runtime.memory();final_preflight.map({allocation_address},4096,Permissions::read|Permissions::write);}
 {InvocationHostBoundary fp;fn::LastErrorBoundary errors;SetLastError(caller_error);alloc_error_before_=GetLastError();
  owned_allocation_=::HeapAlloc(owned_handle_,0,allocation_extent_private_);++alloc_calls_;acquired_allocation_=reinterpret_cast<std::uintptr_t>(owned_allocation_);
  alloc_error_after_=GetLastError();SetLastError(caller_error);alloc_error_restored_=GetLastError();}
 allocation_witness_private_={1,0,allocation_extent_private_,acquired_allocation_,alloc_error_before_,alloc_error_after_,alloc_error_restored_,0,0,acquired_handle_,0,0,0,0,0,0};
 if(owned_allocation_){allocation_initial_private_.resize(allocation_extent_private_);std::memcpy(allocation_initial_private_.data(),owned_allocation_,allocation_extent_private_);
  allocation_initial=allocation_initial_private_;allocation_expected_.assign(4096,std::byte{});std::copy(allocation_initial_private_.begin(),allocation_initial_private_.end(),allocation_expected_.begin());}
 alloc_after=measured_api("HeapAlloc",reinterpret_cast<std::uintptr_t>(&::HeapAlloc));if(alloc_before!=alloc_after)deny("Actual HeapAlloc identity changed",alloc_iat,alloc_site);
 allocator_snapshot();checkpoint(runtime,"allocation-native-after");stable_hook(27);guard();source_identity();
 if(owned_allocation_){runtime.memory().map({allocation_address},4096,Permissions::read|Permissions::write);allocation_mapped_=true;
  runtime.memory().write({allocation_address},allocation_expected_);allocation_guest_private_=allocation_address;allocation_output_private_=allocation_extent_private_;allocator_snapshot();}
 else{auto i=std::find_if(allocator_plan_.begin(),allocator_plan_.end(),[](const mg::Access&a){return a.pc==0x780012e2;});
  allocator_plan_.insert(i,{0x7800cc3f,allocator_frame_-4,allocator_newmode_,4,0});}
 checkpoint(runtime,"allocation-backing-published");stable_hook(28);guard();source_identity();allocation_api_return();
}
void Binding::allocation_api_return(){
 checkpoint(runtime,"allocation-api-return-before");guard();source_identity();unsigned value=runtime.memory().load<unsigned>({allocator_api_frame_});
 if(value!=alloc_return||state.gpr.rsp.dword!=allocator_api_frame_||state.gpr.rip.dword!=alloc_raw)deny("Genuine HeapAlloc return-word and actual API frontier required",allocator_api_frame_,alloc_site);
 api_accesses[api_access_count++]={alloc_site,allocator_api_frame_,value,4,0};stable_hook(29);guard();source_identity();
 state.gpr.rax.dword=allocation_guest_private_;state.gpr.rsp.dword=allocator_api_frame_+16;state.gpr.rip.dword=alloc_return;
 checkpoint(runtime,"allocation-api-returned");stable_hook(30);guard();source_identity();
}
void Binding::client_pattern(){
 if(!allocation_token_valid(allocation_address)||!malloc_returned_private_)deny("Client protocol requires actual returned live allocation token",allocation_address);
 allocation_phase=allocation_phase_private_=3;allocator_snapshot();checkpoint(runtime,"allocation-client-before");stable_hook(32);guard();source_identity();
 auto pattern=std::vector<std::byte>(allocation_extent_private_);for(unsigned n=0;n<pattern.size();++n)pattern[n]=std::byte((n*37+request_private_*11+0x5a)&255);
 // Checked guest write commits first. The private full native pointer is then
 // synchronized under the same finite research client protocol, before hooks.
 runtime.memory().write({allocation_address},pattern);std::memcpy(owned_allocation_,pattern.data(),pattern.size());
 std::copy(pattern.begin(),pattern.end(),allocation_expected_.begin());allocation_pattern_private_=pattern;allocation_pattern=pattern;
 std::vector<std::byte>actual(pattern.size());runtime.memory().read({allocation_address},actual);
 if(actual!=pattern||std::memcmp(owned_allocation_,pattern.data(),pattern.size()))deny("Complete client pattern read/write/native synchronization required",allocation_address);
 client_verified_private_=true;allocator_snapshot();checkpoint(runtime,"allocation-client-after");stable_hook(33);guard();source_identity();
}
void Binding::free_api(){
 const auto F=allocator_frame_;if(!allocation_token_valid(allocation_address)||state.gpr.rsp.dword!=F-72||
  runtime.memory().load<unsigned>({F-72})!=free_return||runtime.memory().load<unsigned>({F-68})!=token||
  runtime.memory().load<unsigned>({F-64})||runtime.memory().load<unsigned>({F-60})!=allocation_address)
  {++allocation_denials_;allocator_snapshot();deny("Genuine HeapFree source frame and private full pointer association required",free_iat,free_site);}
 (void)owns_token(token);if(!client_verified_private_)deny("Original free requires completed declared client synchronization",allocation_address);
 free_before=measured_api("HeapFree",reinterpret_cast<std::uintptr_t>(&::HeapFree));checkpoint(runtime,"allocation-free-native-before");stable_hook(34);guard();source_identity();
 {InvocationHostBoundary fp;fn::LastErrorBoundary errors;SetLastError(caller_error);free_error_before_=GetLastError();const auto actual=owned_allocation_;
  const BOOL result=::HeapFree(owned_handle_,0,actual);++free_calls_;std::memcpy(&free_result_,&result,4);free_error_after_=GetLastError();
  if(result){++free_successes_;owned_allocation_=nullptr;}SetLastError(caller_error);free_error_restored_=GetLastError();}
 allocation_witness_private_[7]=free_calls_;allocation_witness_private_[8]=free_result_;allocation_witness_private_[10]=acquired_allocation_;
 allocation_witness_private_[11]=free_error_before_;allocation_witness_private_[12]=free_error_after_;allocation_witness_private_[13]=free_error_restored_;
 if(!owned_allocation_&&allocation_mapped_){runtime.memory().unmap({allocation_address});allocation_mapped_=false;}
 free_after=measured_api("HeapFree",reinterpret_cast<std::uintptr_t>(&::HeapFree));if(free_before!=free_after)deny("Actual HeapFree identity changed",free_iat,free_site);
 allocator_snapshot();checkpoint(runtime,"allocation-free-native-after");stable_hook(35);guard();source_identity();free_api_return();
}
void Binding::free_api_return(){
 unsigned value=runtime.memory().load<unsigned>({allocator_api_frame_});if(value!=free_return||state.gpr.rsp.dword!=allocator_api_frame_||state.gpr.rip.dword!=free_raw)
  deny("Genuine HeapFree source return word required",allocator_api_frame_,free_site);
 api_accesses[api_access_count++]={free_site,allocator_api_frame_,value,4,0};
 state.gpr.rax.dword=free_result_;state.gpr.rsp.dword=allocator_api_frame_+16;state.gpr.rip.dword=free_return;
 checkpoint(runtime,"allocation-free-api-returned");guard();source_identity();
}
bool Binding::release_allocation_noexcept()noexcept{
 if(!owned_allocation_)return true;InvocationHostBoundary fp;const auto saved=GetLastError();++cleanup_free_calls_;
 const auto ok=::HeapFree(owned_handle_,0,owned_allocation_);SetLastError(saved);
 if(ok){++cleanup_free_successes_;owned_allocation_=nullptr;if(allocation_mapped_){try{runtime.memory().unmap({allocation_address});allocation_mapped_=false;}catch(...){}}}
 allocator_snapshot();return ok!=FALSE;
}
void Binding::allocator_batch(){
 guard();source_identity();allocation_phase=allocation_phase_private_=2;allocator_snapshot();external_call(malloc_entry,request_private_,malloc_marker);
 checkpoint(runtime,"allocation-malloc-before");auto result=mw34_allocation_malloc_body(&state,malloc_entry,this);guard();source_identity();
 if(result!=this||!operation_returned_||!malloc_returned_private_)deny("Authentic complete malloc export return required",malloc_marker);
 if(!allocation_guest_private_)deny("Actual HeapAlloc returned NULL; functional live-allocation roundtrip unavailable",alloc_iat,alloc_site);
 client_pattern();
 auto cleanup_argument=[&](){guard();source_identity();if(state.gpr.rsp.dword!=allocator_frame_+4)deny("External cdecl argument cleanup frame required",state.gpr.rsp.dword);
  external_projections[external_projection_count_++]={2,state.gpr.rip.dword,state.gpr.rsp.dword,state.gpr.rip.dword,state.gpr.rsp.dword+4,0,allocator_frame_,0};state.gpr.rsp.dword+=4;};
 cleanup_argument();allocation_phase=allocation_phase_private_=4;allocator_snapshot();external_call(free_entry,allocation_guest_private_,free_marker);
 checkpoint(runtime,"allocation-free-before");result=mw34_allocation_free_body(&state,free_entry,this);guard();source_identity();
 if(result!=this||!operation_returned_||!free_returned_private_||owned_allocation_||free_successes_!=1)deny("Authentic free export and actual successful HeapFree required",free_marker);
 cleanup_argument();allocation_phase=allocation_phase_private_=5;allocator_snapshot();external_call(free_entry,0,free_marker);
 checkpoint(runtime,"allocation-null-free-before");result=mw34_allocation_free_body(&state,free_entry,this);guard();source_identity();
 if(result!=this||!operation_returned_||!null_free_returned_private_||free_calls_!=1||owned_allocation_)deny("Authentic free(NULL) must return without another native HeapFree",free_marker);
 batch_complete_private_=true;allocator_snapshot();checkpoint(runtime,"allocation-batch-complete");
}
