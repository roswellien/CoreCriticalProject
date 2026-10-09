// Fresh whole-unit implementation. Literal x86 bodies supply source effects;
// this binding checks effective operands and owns finite native API objects.
namespace {
std::uint64_t register_value(const State&s,unsigned r){
 switch(r){case 1:return s.gpr.rax.dword;case 2:return s.gpr.rcx.dword;case 3:return s.gpr.rdx.dword;case 4:return s.gpr.rbx.dword;case 5:return s.gpr.rsp.dword;case 6:return s.gpr.rbp.dword;case 7:return s.gpr.rsi.dword;case 8:return s.gpr.rdi.dword;
 case 9:return s.gpr.rax.dword&255;case 10:return s.gpr.rcx.dword&255;case 11:return s.gpr.rdx.dword&255;case 12:return s.gpr.rbx.dword&255;
 case 13:return (s.gpr.rax.dword>>8)&255;case 14:return (s.gpr.rcx.dword>>8)&255;case 15:return (s.gpr.rdx.dword>>8)&255;case 16:return (s.gpr.rbx.dword>>8)&255;
 case 17:return s.gpr.rax.dword&65535;case 18:return s.gpr.rcx.dword&65535;case 19:return s.gpr.rdx.dword&65535;case 20:return s.gpr.rbx.dword&65535;case 21:return s.gpr.rsp.dword&65535;case 22:return s.gpr.rbp.dword&65535;case 23:return s.gpr.rsi.dword&65535;case 24:return s.gpr.rdi.dword&65535;default:return 0;}
}
unsigned operand_address(const State&s,const OperandSpec&o){return static_cast<unsigned>(register_value(s,o.base)+register_value(s,o.index)*o.scale+o.disp+(o.segment==1?s.addr.fs_base.dword:0));}
std::uint64_t width_mask(unsigned n){return n==8?~0ULL:(1ULL<<(8*n))-1;}
std::string bare_mnemonic(const SourceInstruction&i){std::string m=i.mnemonic;auto p=m.rfind(' ');return p==std::string::npos?m:m.substr(p+1);}
void emit_identity(CaptureSink sink,void*context,const std::string&name,const m4_cmd_native::ApiIdentity&a){
 std::array<std::uint64_t,11>v{a.target,a.named_target,a.owner,a.owner_named_target,a.region.base,a.region.bytes,a.region.allocation,a.region.state,a.region.type,a.region.protect,a.region.allocation_protect};
 sink(name+".bin",std::as_bytes(std::span(v)),context);
 sink(name+"-module-path.bin",std::as_bytes(std::span(a.module_path)),context);sink(name+"-module-sha.bin",std::as_bytes(std::span(a.module_sha)),context);
}
}
unsigned Binding::live_allocations()const noexcept{unsigned n{};for(const auto&p:owned_allocations_)n+=p->native!=nullptr;return n;}
unsigned Binding::live_critical_sections()const noexcept{unsigned n{};for(const auto&p:owned_sections_)n+=p->initialized&&!p->deleted;return n;}
std::array<unsigned,32>Binding::summary()const noexcept{return {1,control,batch_phase_,unsigned(static_complete_),unsigned(locale_complete_),parser_passes_,unsigned(builder_complete_),argc_,argv_,allocations_created_,allocations_freed_,allocations_cleanup_freed_,sections_initialized_,sections_deleted_,live_allocations(),live_critical_sections(),static_cast<unsigned>(source_accesses_.size()),static_cast<unsigned>(api_transports_.size()),static_cast<unsigned>(native_apis_.size()),static_cast<unsigned>(calls_.size()),static_cast<unsigned>(research_accesses_.size()),static_cast<unsigned>(research_projections_.size()),unsigned(suspended_),unsigned(finished_),program_input_,program_extent_,sizing_chars_,sizing_slots_,allocation_cursor_,fs_expected_,unsigned(owned_handle_!=nullptr),unsigned(failed)};}
void Binding::dump(CaptureSink sink,void*context)const{
 auto s=summary();sink("locale-summary.bin",std::as_bytes(std::span(s)),context);
 const std::array<unsigned,4>fault{unsigned(failed),fault_pc,fault_address,stage};sink("locale-fault.bin",std::as_bytes(std::span(fault)),context);if(reason)sink("locale-fault-reason.bin",std::as_bytes(std::span(reason,std::strlen(reason))),context);
 sink("locale-source-accesses.bin",std::as_bytes(std::span(source_accesses_)),context);sink("locale-api-transports.bin",std::as_bytes(std::span(api_transports_)),context);
 sink("locale-research-accesses.bin",std::as_bytes(std::span(research_accesses_)),context);sink("locale-research-projections.bin",std::as_bytes(std::span(research_projections_)),context);
 sink("locale-call-frames.bin",std::as_bytes(std::span(calls_)),context);
 std::vector<std::array<std::uint64_t,16>>allocs,sections;
 for(const auto&p:owned_allocations_){allocs.push_back({1,p->guest,p->requested,p->extent,p->mapped_bytes,p->generation,p->kind,p->acquired,reinterpret_cast<std::uintptr_t>(p->native),unsigned(p->mapped),unsigned(p->source_freed),unsigned(p->cleanup_freed),acquired_handle_,0,0,0});
  const auto name="locale-allocation-"+std::to_string(p->generation);sink(name+"-initial.bin",p->initial,context);sink(name+"-expected.bin",p->expected,context);
  if(p->mapped){std::vector<std::byte>b(p->mapped_bytes);runtime.memory().read({p->guest},b);sink(name+"-owned-page.bin",b,context);}}
 for(const auto&p:owned_sections_)sections.push_back({1,p->guest,p->generation,p->enters,p->leaves,p->depth,p->initializes,p->deletes,unsigned(p->initialized),unsigned(p->deleted),reinterpret_cast<std::uintptr_t>(&p->native),sizeof(CRITICAL_SECTION),0,0,0,0});
 sink("locale-allocations.bin",std::as_bytes(std::span(allocs)),context);sink("locale-critical-sections.bin",std::as_bytes(std::span(sections)),context);
 for(std::size_t n=0;n<native_apis_.size();++n){const auto&a=native_apis_[n];const auto name="locale-api-"+std::to_string(n);sink(name+"-witness.bin",std::as_bytes(std::span(a.words)),context);
  sink(name+"-export-before.bin",a.export_before,context);sink(name+"-export-after.bin",a.export_after,context);sink(name+"-buffers.bin",std::as_bytes(std::span(a.buffers)),context);emit_identity(sink,context,name+"-identity-before",a.before);emit_identity(sink,context,name+"-identity-after",a.after);
  for(std::size_t k=0;k<a.inputs.size();++k)sink(name+"-input-"+std::to_string(k)+".bin",a.inputs[k],context);for(std::size_t k=0;k<a.outputs.size();++k)sink(name+"-output-"+std::to_string(k)+".bin",a.outputs[k],context);}
 sink("locale-diagnostic.bin",std::as_bytes(std::span(diagnostic_)),context);
}
void Binding::expected_store(unsigned a,const void*data,unsigned n){
 for(auto&[page,b]:expected_pages_){const auto begin=std::max<std::uint64_t>(a,page),end=std::min<std::uint64_t>(std::uint64_t(a)+n,std::uint64_t(page)+4096);if(begin<end)std::memcpy(b.data()+begin-page,static_cast<const std::byte*>(data)+begin-a,end-begin);}
 if(a>=lower_stack&&std::uint64_t(a)+n<=std::uint64_t(lower_stack)+4096)std::memcpy(lower_expected_.data()+a-lower_stack,data,n);
 if(a>=0x20001000&&std::uint64_t(a)+n<=0x20002000)std::memcpy(upper_expected_.data()+a-0x20001000,data,n);
 if(query_bound_){auto begin=std::max<std::uint64_t>(a,query_pointer_private_),end=std::min<std::uint64_t>(std::uint64_t(a)+n,std::uint64_t(query_pointer_private_)+148);if(begin<end)std::memcpy(query_expected_.data()+begin-query_pointer_private_,static_cast<const std::byte*>(data)+begin-a,end-begin);}
 for(auto&p:owned_allocations_)if(p->mapped){auto begin=std::max<std::uint64_t>(a,p->guest),end=std::min<std::uint64_t>(std::uint64_t(a)+n,std::uint64_t(p->guest)+p->mapped_bytes);if(begin<end){std::memcpy(p->expected.data()+begin-p->guest,static_cast<const std::byte*>(data)+begin-a,end-begin);auto native_end=std::min<std::uint64_t>(end,std::uint64_t(p->guest)+p->extent);if(p->native&&begin<native_end)std::memcpy(static_cast<std::byte*>(p->native)+begin-p->guest,static_cast<const std::byte*>(data)+begin-a,native_end-begin);}}
 if(a==runtime.fs_base().value&&n==4){std::memcpy(&fs_expected_,data,4);tib_expected_[1]=fs_expected_;}
}
void Binding::batch_guard(){
 if(suspended_||finished_||state.addr.fs_base.dword!=runtime.fs_base().value||state.addr.ds_base.dword||state.addr.ss_base.dword)deny("Exact current flat guest and normal FS ownership required",state.addr.fs_base.dword);
 if(calls_.size()>32||source_accesses_.size()>source_budget_||native_apis_.size()>128||live_allocations()>16)deny("Finite whole locale/parser resource bounds",state.gpr.rip.dword);
 if(runtime.memory().load<unsigned>(runtime.fs_base())!=fs_expected_)deny("Only source normal FS lifecycle may change chain",runtime.fs_base().value);
 if(std::array<unsigned,5>{runtime.fs_base().value,runtime.memory().load<unsigned>(runtime.fs_base()),runtime.memory().load<unsigned>({runtime.fs_base().value+4}),runtime.memory().load<unsigned>({runtime.fs_base().value+8}),runtime.memory().load<unsigned>({runtime.fs_base().value+0x18})}!=tib_expected_)deny("Carried minimal mapped TIB fields must remain source-derived",runtime.fs_base().value);
 for(const auto&[page,expected]:expected_pages_){std::array<std::byte,4096>actual{};runtime.memory().read({page},actual);if(actual!=expected)deny("Only committed source/API/research effects may change owned locale pages",page);}
 for(const auto&p:owned_allocations_)if(p->mapped){std::vector<std::byte>b(p->mapped_bytes);runtime.memory().read({p->guest},b);if(b!=p->expected||!p->native||std::memcmp(p->native,p->expected.data(),p->extent))deny("Checked complete current guest/native allocation backing and private generation required",p->guest);}
 if(program_input_&&(!cm::binding||&cm::binding->context!=admitted_parent_||!cm::binding->ready()||guest_bytes(program_input_,program_extent_)!=cm::binding->actual_bytes()))deny("Immutable actual owned NUL-inclusive command line required",program_input_);
}
void Binding::batch_source_identity(){
 admitted_parent_->source_identity();for(const auto&[address,original]:locale_sources_){auto b=guest_bytes(address,static_cast<unsigned>(original.size()));if(b!=original)deny("Exact current literal locale source identity",address);}
 for(const auto&a:source_api_contracts())if(runtime.memory().load<unsigned>({a.slot})!=a.raw)deny("Exact original named locale/allocator import identity",a.slot,a.site);
}
void Binding::source_access(unsigned a,std::uint64_t v,unsigned n,bool write){if(source_accesses_.size()>=source_budget_)deny("Bounded actual source memory ledger",a);source_accesses_.push_back({state.gpr.rip.dword,a,v,n,unsigned(write)});last_source_pc_=state.gpr.rip.dword;}
void Binding::check_source_access(unsigned a,std::uint64_t v,unsigned n,bool writing){
 const auto*ins=instruction(state.gpr.rip.dword);if(!ins||!n||n>8||std::uint64_t(a)+n>0x100000000ULL)deny("Exact admitted source PC and access width required",a);
 const auto m=bare_mnemonic(*ins);const auto mask=width_mask(n);v&=mask;bool allowed{};std::uint64_t expected{};bool value_checked{};
 if((m=="push"||m=="call")&&writing){allowed=n==4&&a==state.gpr.rsp.dword-4;value_checked=true;
  if(m=="call")expected=ins->pc+ins->length;else if(ins->operands[0].kind==1)expected=register_value(state,ins->operands[0].reg);
  else if(ins->operands[0].kind==2)expected=ins->operands[0].imm;else{if(source_accesses_.empty())deny("Source PUSH memory requires its actual read",a);const auto&r=source_accesses_.back();if(r.pc!=ins->pc||r.write||r.address!=operand_address(state,ins->operands[0])||r.bytes!=4)deny("Source PUSH memory ordered operand read",a);expected=r.value;}}
 else if((m=="pop"||m=="ret")&&!writing){allowed=n==4&&a==(m=="pop"?state.gpr.rsp.dword-4:state.gpr.rsp.dword);}
 else if(m=="leave"&&!writing){allowed=n==4&&a==state.gpr.rbp.dword;}
 else if(m=="stosb"||m=="stosw"||m=="stosd"){const auto bytes=m=="stosb"?1U:m=="stosw"?2U:4U;allowed=writing&&n==bytes&&a==state.gpr.rdi.dword;value_checked=true;expected=register_value(state,1);}
 else if(m=="movsb"||m=="movsw"||m=="movsd"){const auto bytes=m=="movsb"?1U:m=="movsw"?2U:4U;allowed=n==bytes&&a==(writing?state.gpr.rdi.dword:state.gpr.rsi.dword);if(writing){value_checked=true;if(source_accesses_.empty()||source_accesses_.back().pc!=ins->pc||source_accesses_.back().write)deny("Source MOVS requires actual ordered input read",a);expected=source_accesses_.back().value;}}
 else{
  for(unsigned k=0;k<ins->count;++k){const auto&o=ins->operands[k];if(o.kind!=3||o.width!=n||operand_address(state,o)!=a||!(o.access&(writing?2U:1U)))continue;allowed=true;
   if(writing&&m=="mov"&&k==0&&ins->count==2){const auto&src=ins->operands[1];expected=src.kind==1?register_value(state,src.reg):src.imm;value_checked=src.kind==1||src.kind==2;}
   if(writing&&(m=="or"||m=="and"||m=="add"||m=="sub"||m=="inc"||m=="dec")){if(source_accesses_.empty())deny("Source memory arithmetic requires prior read",a);const auto&r=source_accesses_.back();if(r.pc!=ins->pc||r.address!=a||r.write||r.bytes!=n)deny("Exact source read-modify-write chronology",a);auto rhs=ins->count==2?(ins->operands[1].kind==1?register_value(state,ins->operands[1].reg):ins->operands[1].imm):1;expected=m=="or"?(r.value|rhs):m=="and"?(r.value&rhs):m=="sub"||m=="dec"?r.value-rhs:r.value+rhs;value_checked=true;}
  }
 }
 if(!allowed||(value_checked&&(expected&mask)!=v))deny("Exact decoded source memory operand/store value required",a,ins->pc);
 if(a>=0x31000000&&a<0x32000000&&!allocation_for(a,n))deny("Current source allocation token/extent/generation required",a,ins->pc);
 if(writing&&ins->pc>=0x7800bc48&&ins->pc<0x7800bdfc&&a>=0x31000000&&a<0x32000000){const bool vector=n==4&&a>=parser_vector_&&std::uint64_t(a)+n<=parser_vector_end_,chars=n==1&&a>=parser_chars_&&std::uint64_t(a)+n<=parser_chars_end_;if(!vector&&!chars)deny("Exact requested parser vector/character output subrange required",a,ins->pc);}
 if(a>=cm::buffer&&a<std::uint64_t(cm::buffer)+131072&&(writing||a<program_input_||std::uint64_t(a)+n>std::uint64_t(program_input_)+program_extent_))deny("Immutable NUL-inclusive command-line extent required",a,ins->pc);
}
std::uint64_t Binding::read(unsigned a,unsigned n){guard();source_identity();check_source_access(a,0,n,false);std::uint64_t v{};std::span<std::byte>b(reinterpret_cast<std::byte*>(&v),n);try{runtime.memory().read({a},b);}catch(...){deny("Checked actual source locale/parser read fault",a);}source_access(a,v,n,false);return v;}
void Binding::write(unsigned a,std::uint64_t v,unsigned n){guard();source_identity();check_source_access(a,v,n,true);if(control==210&&!control_used_&&n==1&&a>=parser_chars_&&a<parser_chars_end_){control_used_=true;runtime.memory().protect({a&~4095U},Permissions::read);}try{runtime.memory().write({a},std::span<const std::byte>(reinterpret_cast<const std::byte*>(&v),n));}catch(...){deny("Checked actual source locale/parser store fault",a);}expected_store(a,&v,n);source_access(a,v,n,true);
 if(a==runtime.fs_base().value)checkpoint(runtime,("locale-source-seh-"+std::to_string(source_accesses_.size())+"-after").c_str());}
unsigned char Binding::batch_undefined(){guard();source_identity();const auto pc=state.gpr.rip.dword;const auto sites=generated_undefined_sites();if(std::find(sites.begin(),sites.end(),pc)==sites.end())deny("Exact new generated undefined AF callback site required",pc);
 const auto key=std::pair<unsigned,std::size_t>{pc,source_accesses_.size()};if(std::count(undefined_occurrences_.begin(),undefined_occurrences_.end(),key)>=std::count(sites.begin(),sites.end(),pc))deny("Generated undefined-byte callbacks exceed exact artifact multiplicity",pc);undefined_occurrences_.push_back(key);if(undefined_count==undefined_sites.size())deny("Bounded actual generated undefined-byte callback ledger",pc);undefined_sites[undefined_count++]=pc;return 0;}
std::vector<std::byte>Binding::guest_bytes(unsigned a,unsigned n){if(n>1024*1024||std::uint64_t(a)+n>0x100000000ULL)deny("Finite actual API input/output extent required",a);std::vector<std::byte>b(n);for(unsigned offset=0;offset<n;){const auto chunk=std::min(n-offset,4096-((a+offset)&4095U));runtime.memory().read({a+offset},std::span(b).subspan(offset,chunk));offset+=chunk;}return b;}
void Binding::preflight_write(unsigned a,unsigned n){if(!n)return;auto clone=runtime.memory();auto bytes=guest_bytes(a,n);for(unsigned offset=0;offset<n;){const auto chunk=std::min(n-offset,4096-((a+offset)&4095U));clone.write({a+offset},std::span(bytes).subspan(offset,chunk));offset+=chunk;}}
void Binding::api_transfer(unsigned a,std::span<const std::byte>b){for(unsigned n=0;n<b.size();){const auto width=std::min<unsigned>({4,static_cast<unsigned>(b.size()-n),4096-((a+n)&4095U)});std::uint64_t v{};std::memcpy(&v,b.data()+n,width);guard();source_identity();runtime.memory().write({a+n},b.subspan(n,width));expected_store(a+n,b.data()+n,width);api_transports_.push_back({static_cast<unsigned>(native_apis_.back().words[2]),a+n,v,width,1});n+=width;if(control==207&&!control_used_&&n<b.size()){control_used_=true;runtime.memory().protect({(a+n)&~4095U},Permissions::read);}}}
Binding::Allocation*Binding::allocation_for(unsigned a,unsigned n)noexcept{for(auto&p:owned_allocations_)if(p->native&&p->mapped&&a>=p->guest&&std::uint64_t(a)+n<=std::uint64_t(p->guest)+p->extent)return p.get();return nullptr;}
Binding::CriticalSection*Binding::section_for(unsigned a)noexcept{for(auto&p:owned_sections_)if(p->guest==a&&p->initialized&&!p->deleted)return p.get();return nullptr;}

void Binding::locale_batch(){
 guard();source_identity();batch_phase_=1;caller_pc_=state.gpr.rip.dword;caller_sp_=state.gpr.rsp.dword;
 if(caller_sp_!=0x20001860||!owned_handle_||!mode_published_private_||mode_value_private_!=1)deny("Fresh authentic persistent heap and completed caller cleanup required",caller_sp_);
 for(const auto&s:source_spans()){auto b=guest_bytes(s.address,s.bytes);if(m4::sha256(b)!=s.sha)deny("Recovered exact literal locale source span required",s.address);locale_sources_.push_back({s.address,std::move(b)});}
 for(const auto&p:source_pages()){std::array<std::byte,4096>b{};runtime.memory().read({p.address},b);expected_pages_.push_back({p.address,b});}
 for(const auto page:std::array<unsigned,2>{lower_stack,0x20001000})if(std::none_of(expected_pages_.begin(),expected_pages_.end(),[&](const auto&p){return p.first==page;})){std::array<std::byte,4096>b{};runtime.memory().read({page},b);expected_pages_.push_back({page,b});}
 tib_expected_={runtime.fs_base().value,runtime.memory().load<unsigned>(runtime.fs_base()),runtime.memory().load<unsigned>({runtime.fs_base().value+4}),runtime.memory().load<unsigned>({runtime.fs_base().value+8}),runtime.memory().load<unsigned>({runtime.fs_base().value+0x18})};
 for(unsigned n=0;n<access_count;++n){const auto&a=accesses[n];source_accesses_.push_back({a.pc,a.address,a.value,a.width,a.write});}
 checkpoint(runtime,"locale-batch-before");external_source_call(0x78003bf4,0xffffffc0);
 if(!static_complete_||sections_initialized_!=4||live_critical_sections()!=4)deny("Complete static CRT critical-section helper required",0x78003c1c);
 checkpoint(runtime,"locale-static-locks-returned");batch_phase_=2;external_source_call(0x78003dd2,0xffffffb0);
 if(!locale_complete_||live_allocations()!=1||!section_for(runtime.memory().load<unsigned>({0x7803708c}))||section_for(runtime.memory().load<unsigned>({0x7803708c}))->depth)deny("Complete default locale and released owned lock25 required",0x7803708c);
 checkpoint(runtime,"locale-default-returned");
}
void Binding::external_source_call(unsigned target,unsigned marker){
 guard();source_identity();if(!has_body(target)||!calls_.empty())deny("Fresh whole-helper external source invocation required",target);
 const auto oldpc=state.gpr.rip.dword,oldsp=state.gpr.rsp.dword,frame=oldsp-4;
 runtime.memory().store<unsigned>({frame},marker);expected_store(frame,&marker,4);research_accesses_.push_back({oldpc,frame,marker,4,1});
 research_projections_.push_back({1,oldpc,oldsp,target,frame,marker,0,0});state.gpr.rip.dword=target;state.gpr.rsp.dword=frame;
 calls_.push_back({target,frame,marker,0,state.gpr.rbp.dword,state.gpr.rbx.dword,state.gpr.rsi.dword,state.gpr.rdi.dword,0});
 auto result=dispatch_body(target,&state,this);guard();source_identity();if(result!=this||!calls_.empty()||state.gpr.rsp.dword!=oldsp||state.gpr.rip.dword!=marker)deny("Complete genuine source helper RET to external return marker required",target);
 research_projections_.push_back({2,marker,oldsp,oldpc,oldsp,0,0,0});state.gpr.rip.dword=oldpc;
}
void Binding::suspend_for_commandline(){
 guard();source_identity();if(!locale_complete_||suspended_||!calls_.empty()||state.gpr.rsp.dword!=0x20001860||runtime.cpu().esp!=0x20001860||runtime.cpu().eip!=mg::slot)deny("Exact completed locale and actual mainargs frame before producer required",cm::writer);
 const auto original_pc=0x5ac468U;research_projections_.push_back({3,state.gpr.rip.dword,state.gpr.rsp.dword,original_pc,state.gpr.rsp.dword,0,0,0});state.gpr.rip.dword=original_pc;
 checkpoint(runtime,"locale-commandline-suspended");suspended_=true;owner=nullptr;authority=nullptr;
}
void Binding::admit_commandline(){
 if(!suspended_||authority||owner||binding!=this||admitted_binding!=this||!cm::binding||cm::binding!=cm::admitted_binding||&cm::binding->context!=admitted_parent_||!cm::binding->ready())deny("Exact actual command-line producer and immutable parent required",cm::global);
 auto&c=*cm::binding;if(c.access_count!=3||c.consumer_access_count||c.actual_bytes().empty()||c.actual_bytes().size()>131072||c.actual_bytes().back()!=std::byte{})deny("Completed actual command-line source/witness required",cm::global);
 const std::array<std::array<unsigned,4>,3>expected{{{cm::writer,cm::iat,c.raw,0},{cm::writer,0x2000185c,cm::ret,1},{cm::ret,cm::global,cm::buffer,1}}};
 for(unsigned n=0;n<3;++n){const auto&a=c.accesses[n];if(a.pc!=expected[n][0]||a.address!=expected[n][1]||a.value!=expected[n][2]||a.write!=expected[n][3]||a.width!=4)deny("Actual command-line three-access source contract required",a.address);if(a.write)expected_store(a.address,&a.value,4);source_accesses_.push_back({a.pc,a.address,a.value,a.width,a.write});}
 program_input_=cm::buffer;program_extent_=c.actual_bytes().size();if(guest_bytes(program_input_,program_extent_)!=c.actual_bytes())deny("Actual owned command-line bytes required",program_input_);
 if(state.gpr.rsp.dword!=0x20001860||state.gpr.rip.dword!=0x5ac468||state.gpr.rax.dword!=program_input_||runtime.cpu().eax!=program_input_)deny("Only admitted actual command-line carry effects required",cm::global);
 suspended_=false;owner=this;authority=this;guard();source_identity();
}
void Binding::resume_mainargs(mg::Context&c){
 try{
 if(&c!=admitted_parent_)deny("Exact same original mainargs context required",mg::entry);admit_commandline();batch_phase_=3;
 const auto frame=runtime.cpu().esp;if(frame!=0x20001860||runtime.cpu().eip!=mg::slot||runtime.memory().load<unsigned>({frame})!=mg::return_pc)deny("Actual original zero-wildcard mainargs source frame required",frame);
 startup_value_=runtime.memory().load<unsigned>({runtime.memory().load<unsigned>({frame+20})});if(startup_value_||runtime.memory().load<unsigned>({frame+16}))deny("Original captured zero wildcard/startup mode domain required",frame);
 research_projections_.push_back({4,state.gpr.rip.dword,state.gpr.rsp.dword,mg::entry,frame,0,0,0});state.gpr.rip.dword=mg::entry;
 calls_.push_back({mg::entry,frame,mg::return_pc,0,state.gpr.rbp.dword,state.gpr.rbx.dword,state.gpr.rsi.dword,state.gpr.rdi.dword,0});
 checkpoint(runtime,"locale-mainargs-before");(void)dispatch_body(mg::entry,&state,this);deny("Mainargs must stop at genuine completed builder return",0x7800ba9e);
 }catch(const Completion&){throw;}catch(const std::exception&e){if(!failed){host_fault_reason_private_=e.what();first(host_fault_reason_private_.c_str());}admitted_parent_->first(reason,fault_address,fault_pc);throw;}catch(...){if(!failed)first("Required whole-unit source observer or host fault");admitted_parent_->first(reason,fault_address,fault_pc);throw;}
}
void*Binding::batch_called(State*s,unsigned target,void*p){
 guard();source_identity();if(s!=&state||p!=this||state.gpr.rip.dword!=target||source_accesses_.empty())deny("Exact active whole-unit CALL State/private token required",target);
 const auto&w=source_accesses_.back();const auto*ins=instruction(w.pc);if(!ins||bare_mnemonic(*ins)!="call"||!w.write||w.bytes!=4||w.address!=state.gpr.rsp.dword||w.value!=w.pc+ins->length||runtime.memory().load<unsigned>({w.address})!=w.value)deny("Actual source CALL committed return frame required",target,w.pc);
 for(const auto&a:source_api_contracts())if(a.site==w.pc&&a.raw==target&&!a.tail){actual_api(a.site,a.raw,a.argc);return this;}
 if(!has_body(target))deny("Required source CALL dependency remains unrecovered",target,w.pc);
 if(ins->operands[0].kind==2&&static_cast<unsigned>(ins->operands[0].imm)!=target)deny("Original direct source CALL target required",target,w.pc);
 if(target==malloc_entry){const auto request=runtime.memory().load<unsigned>({w.address+4});if(request>1024*1024)deny("Bounded genuine source malloc request required",request,w.pc);
  if(w.pc==0x7800bc06){const std::uint64_t required=std::uint64_t(sizing_chars_)+4ULL*sizing_slots_;if(!parser_passes_||required>UINT32_MAX||request!=required)deny("Checked sizing-pass argv allocation arithmetic required",request,w.pc);}}
 if(target==mg::builder)builder_frame_=w.address;
 if(target==0x7800bc48){if(!locale_complete_||parser_passes_>=2||runtime.memory().load<unsigned>({w.address+4})!=program_input_||runtime.memory().load<unsigned>({w.address+16})!=builder_frame_-8||runtime.memory().load<unsigned>({w.address+20})!=builder_frame_-12)deny("Parser needs completed locale, actual input and exact source counter pointers",target,w.pc);
  parser_vector_=runtime.memory().load<unsigned>({w.address+8});parser_chars_=runtime.memory().load<unsigned>({w.address+12});if(!parser_passes_){if(parser_vector_||parser_chars_)deny("Sizing pass requires genuine null output arguments",target,w.pc);parser_vector_end_=parser_chars_end_=0;}
  else{auto*a=allocation_for(parser_vector_);if(!a||a->guest!=parser_vector_||a->kind!=2||a->requested!=sizing_chars_+4*sizing_slots_||parser_chars_!=parser_vector_+4*sizing_slots_)deny("Output pass requires exact source-owned vector/character partition",target,w.pc);parser_vector_end_=parser_chars_;parser_chars_end_=a->guest+a->requested;}
  checkpoint(runtime,parser_passes_?"locale-parser-output-before":"locale-parser-sizing-before");}
 const auto kind=target==probe?1U:0U;CallFrame f{target,w.address,static_cast<unsigned>(w.value),w.pc,state.gpr.rbp.dword,state.gpr.rbx.dword,state.gpr.rsi.dword,state.gpr.rdi.dword,kind};calls_.push_back(f);if(kind)calls_.back().kind=state.gpr.rax.dword|0x80000000U;
 auto result=dispatch_body(target,s,this);guard();source_identity();if(result!=this)deny("Exact literal source body memory token must return",target,w.pc);return this;
}
void*Binding::batch_returned(State*s,unsigned target,void*p){
 guard();source_identity();if(s!=&state||p!=this||state.gpr.rip.dword!=target||calls_.empty()||source_accesses_.empty())deny("Exact whole-unit genuine RET State/token required",target);
 const auto&r=source_accesses_.back();const auto*ins=instruction(r.pc);auto f=calls_.back();if(!ins||bare_mnemonic(*ins)!="ret"||r.write||r.bytes!=4||r.value!=target||target!=f.return_pc)deny("Actual source RET read and current caller target required",target,r.pc);
 if(f.kind&0x80000000U){const auto size=f.kind&0x7fffffffU;if(state.gpr.rsp.dword!=f.frame+4-size||r.address!=state.gpr.rsp.dword-4)deny("Genuine relocated custom stack-probe RET required",target,r.pc);}
 else{unsigned cleanup=ins->count&&ins->operands[0].kind==2?static_cast<unsigned>(ins->operands[0].imm):0;if(r.address!=f.frame||state.gpr.rsp.dword!=f.frame+4+cleanup||state.gpr.rbp.dword!=f.ebp||state.gpr.rbx.dword!=f.ebx||state.gpr.rsi.dword!=f.esi||state.gpr.rdi.dword!=f.edi)deny("Genuine source RET restores cdecl/nonvolatile frame",target,r.pc);}
 calls_.pop_back();event(50,r.pc,target,r.address);
 if(f.entry==0x78003bf4){if(target!=0xffffffc0||sections_initialized_!=4)deny("Whole static initializer RET after four real initializations required",target,r.pc);static_complete_=true;}
 if(f.entry==0x78003dd2){if(target!=0xffffffb0||state.gpr.rax.dword!=0||!section_for(runtime.memory().load<unsigned>({0x7803708c})))deny("Genuine default stub success RET and owned lock25 required",target,r.pc);locale_complete_=true;}
 if(f.entry==0x7800bc48){++parser_passes_;if(parser_passes_==1){sizing_chars_=runtime.memory().load<unsigned>({builder_frame_-12});sizing_slots_=runtime.memory().load<unsigned>({builder_frame_-8});if(!sizing_slots_||sizing_chars_>program_extent_+1||sizing_slots_>program_extent_+1)deny("Finite complete parser sizing counts required",target,r.pc);}checkpoint(runtime,parser_passes_==1?"locale-parser-sizing-returned":"locale-parser-output-returned");}
 if(f.entry==mg::builder){
  if(target!=0x7800ba9e||parser_passes_!=2)deny("Genuine original builder RET and two complete parser passes required",target,r.pc);
  argv_=runtime.memory().load<unsigned>({0x7803b3d8});argc_=runtime.memory().load<unsigned>({0x78038ef4});auto*a=allocation_for(argv_,4);if(!a||argc_+1!=sizing_slots_||a->requested!=sizing_chars_+4*sizing_slots_||runtime.memory().load<unsigned>({argv_+4*argc_}))deny("Source-published owned argv/count and null sentinel required",argv_,r.pc);
  for(unsigned n=0;n<argc_;++n){auto address=runtime.memory().load<unsigned>({argv_+4*n});if(address<argv_+4*sizing_slots_||address>=argv_+a->requested)deny("Every argv pointer must name exact requested character storage",address,r.pc);bool end{};for(unsigned k=0;std::uint64_t(address)+k<std::uint64_t(argv_)+a->requested;++k)if(!runtime.memory().load<unsigned char>({address+k})){end=true;break;}if(!end)deny("Every source argv string must terminate inside requested character area",address,r.pc);}
  stable_hook(60);builder_complete_=true;batch_phase_=4;checkpoint(runtime,"locale-builder-returned");throw Completion{};
 }
 return this;
}
void*Binding::batch_missing(State*s,unsigned target,void*p){
 guard();source_identity();if(s!=&state||p!=this||state.gpr.rip.dword!=target||calls_.empty())deny("Exact source branch continuation State/private token required",target);
 for(const auto&a:source_api_contracts())if(a.raw==target&&a.tail){actual_api(a.site,a.raw,a.argc);return this;}
 if(!has_body(target))deny("Required source continuation remains outside recovered whole unit",target);return dispatch_body(target,s,this);
}
void Binding::api_return(unsigned frame,unsigned argc,unsigned result){
 guard();source_identity();auto&api=native_apis_.back();const auto target=runtime.memory().load<unsigned>({frame});if(state.gpr.rsp.dword!=frame||target!=api.words[6])deny("Genuine checked native API stdcall return word required",frame,api.words[2]);
 if(api_access_count==api_accesses.size())deny("Bounded separate native API return ledger",frame);api_accesses[api_access_count++]={static_cast<unsigned>(api.words[2]),frame,target,4,0};
 state.gpr.rax.dword=result;state.gpr.rsp.dword=frame+4*(argc+1);state.gpr.rip.dword=target;api.words[15]=1;
 if(api.words[19]){if(calls_.empty()||calls_.back().frame!=frame||calls_.back().return_pc!=target)deny("Tail API retains actual source caller return frame",frame,api.words[2]);calls_.pop_back();}
}
void Binding::finish(){
 if(std::this_thread::get_id()!=thread_)throw std::runtime_error("Locale finish requires the actual admitted owner thread");admit_current();if(finished_)return;if(!started_||api_active_||(active&&!failed&&!builder_complete_))deny("Locale finish requires completed or faulted source work outside a native API callback",state.gpr.rip.dword);InvocationHostBoundary fp;fn::LastErrorBoundary error;
 if(!cleanup_sections_noexcept()||!cleanup_allocations_noexcept())throw std::runtime_error("Locale cleanup failed; full private native ownership retained");
 if(owned_handle_&&!release_noexcept())throw std::runtime_error("Actual heap release failed; private ownership retained");finished_=true;active=false;depth=0;owner=nullptr;authority=nullptr;checkpoint(runtime,"locale-batch-cleaned");
}

void Binding::actual_api(unsigned site,unsigned raw,unsigned argc){
 guard();source_identity();if(api_active_||argc>8||native_apis_.size()>=128)deny("One finite actual source API invocation at a time required",raw,site);
 const auto specs=source_api_contracts();auto spec=std::find_if(specs.begin(),specs.end(),[&](const auto&a){return a.site==site&&a.raw==raw&&a.argc==argc;});if(spec==specs.end()||runtime.memory().load<unsigned>({spec->slot})!=raw)deny("Exact source named API metadata/raw target required",raw,site);
 const auto frame=state.gpr.rsp.dword,return_pc=runtime.memory().load<unsigned>({frame});if(spec->tail){const auto&r=source_accesses_.back();if(calls_.empty()||calls_.back().frame!=frame||calls_.back().return_pc!=return_pc||r.pc!=site||r.write||r.address!=spec->slot||r.value!=raw)deny("Source tail API must use genuine resolver frame and actual IAT read",frame,site);}
 else{const auto*ins=instruction(site);if(!ins||bare_mnemonic(*ins)!="call"||return_pc!=site+ins->length||source_accesses_.back().pc!=site||!source_accesses_.back().write||source_accesses_.back().address!=frame)deny("Actual original source API CALL/return closure required",frame,site);}
 ApiCapture record;record.words={1,native_apis_.size(),site,spec->slot,raw,frame,return_pc,argc,0,caller_error,0,0,0,0,0,0,0,0,0,spec->tail,0,0,0,0,0,0,0,0,0,0,0,0};
 for(unsigned n=0;n<argc;++n)record.words[20+n]=runtime.memory().load<unsigned>({frame+4+4*n});native_apis_.push_back(std::move(record));api_active_=true;
 struct Active{Binding&b;~Active()noexcept{b.api_active_=false;}}active{*this};
 if(std::string(spec->name)=="HeapAlloc")native_allocate(site,frame,argc);
 else if(std::string(spec->name)=="HeapFree")native_free(site,frame,argc);
 else if(std::string(spec->name).find("CriticalSection")!=std::string::npos)native_section(site,frame,argc);
 else native_nls(site,frame,argc);
}
void Binding::native_allocate(unsigned site,unsigned frame,unsigned argc){
 auto&api=native_apis_.back();const auto request=static_cast<unsigned>(api.words[22]);if(argc!=3||api.words[20]!=token||api.words[21]||!request||request>1024*1024||!owned_handle_||runtime.memory().load<unsigned>({global+4})!=1)deny("Authentic bounded mode1 HeapAlloc handle/flags/rounded extent required",alloc_iat,site);
 const auto mapped=(request+4095)&~4095U,guest=allocation_cursor_;if(std::uint64_t(guest)+mapped>0x32000000ULL)deny("Finite disjoint research allocation address space",guest,site);
 auto object=std::make_unique<Allocation>();object->guest=guest;object->extent=request;object->mapped_bytes=mapped;object->generation=++generation_;object->kind=batch_phase_==3?2:1;
 for(auto i=calls_.rbegin();i!=calls_.rend();++i)if(i->entry==malloc_entry){object->requested=runtime.memory().load<unsigned>({i->frame+4});break;}
 if(!object->requested&&request!=16)deny("Source zero malloc rounding must be genuine",request,site);
 auto preflight=runtime.memory();preflight.map({guest},mapped,Permissions::read|Permissions::write);
 NativeExportProof before;api.before=measured_api("HeapAlloc",reinterpret_cast<std::uintptr_t>(&::HeapAlloc),&before);std::memcpy(api.export_before.data(),&before,sizeof(before));
 checkpoint(runtime,("locale-api-"+std::to_string(native_apis_.size()-1)+"-before").c_str());stable_hook(40);guard();source_identity();{auto final=runtime.memory();final.map({guest},mapped,Permissions::read|Permissions::write);}
 auto*owned=object.get();owned_allocations_.push_back(std::move(object));
 {InvocationHostBoundary hardware;fn::LastErrorBoundary error;SetLastError(caller_error);api.words[9]=GetLastError();owned->native=::HeapAlloc(owned_handle_,0,request);owned->acquired=reinterpret_cast<std::uintptr_t>(owned->native);++allocations_created_;api.words[10]=GetLastError();SetLastError(caller_error);api.words[11]=GetLastError();}
 api.words[8]=owned->acquired;api.words[14]=1;
 if(owned->native){owned->initial.resize(request);std::memcpy(owned->initial.data(),owned->native,request);owned->expected.assign(mapped,std::byte{});std::copy(owned->initial.begin(),owned->initial.end(),owned->expected.begin());api.outputs.push_back(owned->initial);}
 NativeExportProof after;api.after=measured_api("HeapAlloc",reinterpret_cast<std::uintptr_t>(&::HeapAlloc),&after);std::memcpy(api.export_after.data(),&after,sizeof(after));if(api.before!=api.after||api.export_before!=api.export_after)deny("Actual measured allocation export identity remained stable",alloc_iat,site);
 checkpoint(runtime,("locale-api-"+std::to_string(native_apis_.size()-1)+"-after").c_str());stable_hook(41);guard();source_identity();
 if(owned->native){runtime.memory().map({guest},mapped,Permissions::read|Permissions::write);owned->mapped=true;runtime.memory().write({guest},owned->expected);allocation_cursor_+=mapped;}
 api.words[12]=owned->native?guest:0;api.words[13]=owned->native?request:0;api_return(frame,argc,owned->native?guest:0);
 checkpoint(runtime,("locale-api-"+std::to_string(native_apis_.size()-1)+"-returned").c_str());stable_hook(43);
}
void Binding::native_free(unsigned site,unsigned frame,unsigned argc){
 auto&api=native_apis_.back();const auto guest=static_cast<unsigned>(api.words[22]);auto*a=allocation_for(guest);if(argc!=3||api.words[20]!=token||api.words[21]||!a||a->guest!=guest||!owned_handle_)deny("Exact source HeapFree token/full allocation ownership required",free_iat,site);
 if(section_for(guest))deny("Native critical section must be deleted before backing is freed",guest,site);
 NativeExportProof before;api.before=measured_api("HeapFree",reinterpret_cast<std::uintptr_t>(&::HeapFree),&before);std::memcpy(api.export_before.data(),&before,sizeof(before));api.inputs.push_back(guest_bytes(a->guest,a->extent));
 checkpoint(runtime,("locale-api-"+std::to_string(native_apis_.size()-1)+"-before").c_str());stable_hook(40);guard();source_identity();std::memcpy(a->native,a->expected.data(),a->extent);
 unsigned result{};{InvocationHostBoundary hardware;fn::LastErrorBoundary error;SetLastError(caller_error);api.words[9]=GetLastError();const BOOL outcome=::HeapFree(owned_handle_,0,a->native);std::memcpy(&result,&outcome,4);api.words[10]=GetLastError();SetLastError(caller_error);api.words[11]=GetLastError();if(outcome){a->native=nullptr;a->source_freed=true;++allocations_freed_;}}
 api.words[8]=result;api.words[12]=result;api.words[14]=1;api.words[16]=a->acquired;if(!a->native&&a->mapped){runtime.memory().unmap({a->guest});a->mapped=false;}
 NativeExportProof after;api.after=measured_api("HeapFree",reinterpret_cast<std::uintptr_t>(&::HeapFree),&after);std::memcpy(api.export_after.data(),&after,sizeof(after));if(api.before!=api.after||api.export_before!=api.export_after)deny("Actual measured free export identity remained stable",free_iat,site);
 checkpoint(runtime,("locale-api-"+std::to_string(native_apis_.size()-1)+"-after").c_str());stable_hook(41);guard();source_identity();api_return(frame,argc,result);
}
void Binding::native_section(unsigned site,unsigned frame,unsigned argc){
 static_assert(sizeof(CRITICAL_SECTION)==40&&alignof(CRITICAL_SECTION)==8);
 auto&api=native_apis_.back();const auto guest=static_cast<unsigned>(api.words[20]);const auto specs=source_api_contracts();auto spec=std::find_if(specs.begin(),specs.end(),[&](const auto&a){return a.site==site&&a.raw==api.words[4];});if(spec==specs.end()||argc!=1)deny("One checked opaque original critical-section object required",guest,site);
 const auto name=std::string(spec->name);CriticalSection*section=section_for(guest);const auto preserve_eax=state.gpr.rax.dword;
 if(name=="InitializeCriticalSection"){
  if(section||std::any_of(owned_sections_.begin(),owned_sections_.end(),[&](const auto&p){return p->guest==guest;}))deny("Critical section cannot be initialized twice",guest,site);
  const std::array<unsigned,4>statics{0x78037100,0x78037130,0x78037118,0x780370e8};if(std::find(statics.begin(),statics.end(),guest)==statics.end()&&!allocation_for(guest,24))deny("Source static object or live malloc24 backing required",guest,site);
  auto object=std::make_unique<CriticalSection>();object->guest=guest;object->generation=++generation_;section=object.get();owned_sections_.push_back(std::move(object));
 }else if(!section)deny("Initialized private native critical-section association required",guest,site);
 api.inputs.push_back(guest_bytes(guest,24));api.words[16]=reinterpret_cast<std::uintptr_t>(&section->native);api.words[17]=sizeof(CRITICAL_SECTION);
 const auto address=name=="InitializeCriticalSection"?reinterpret_cast<std::uintptr_t>(&::InitializeCriticalSection):name=="EnterCriticalSection"?reinterpret_cast<std::uintptr_t>(&::EnterCriticalSection):name=="LeaveCriticalSection"?reinterpret_cast<std::uintptr_t>(&::LeaveCriticalSection):reinterpret_cast<std::uintptr_t>(&::DeleteCriticalSection);
 NativeExportProof before;api.before=measured_api(name.c_str(),address,&before);std::memcpy(api.export_before.data(),&before,sizeof(before));
 if(name=="LeaveCriticalSection"&&(!section->depth||section->owner_thread!=thread_))deny("Leave requires this thread's live recursive acquisition",guest,site);
 checkpoint(runtime,("locale-api-"+std::to_string(native_apis_.size()-1)+"-before").c_str());stable_hook(40);guard();source_identity();if(runtime.memory().load<unsigned>({frame+4})!=guest)deny("Actual checked critical-section argument immediately before native call",frame+4,site);
 {InvocationHostBoundary hardware;fn::LastErrorBoundary error;SetLastError(caller_error);api.words[9]=GetLastError();
  if(name=="InitializeCriticalSection"){::InitializeCriticalSection(&section->native);section->initialized=true;++section->initializes;++sections_initialized_;}
  else if(name=="EnterCriticalSection"){if(section->depth&&section->owner_thread!=thread_)deny("Owned serial fixture critical-section owner required",guest,site);::EnterCriticalSection(&section->native);section->owner_thread=thread_;++section->depth;++section->enters;}
  else if(name=="LeaveCriticalSection"){::LeaveCriticalSection(&section->native);--section->depth;++section->leaves;}
  else{if(section->depth)deny("Cannot delete a held critical section",guest,site);::DeleteCriticalSection(&section->native);section->deleted=true;++section->deletes;++sections_deleted_;}
  api.words[10]=GetLastError();SetLastError(caller_error);api.words[11]=GetLastError();}
 api.words[14]=1;api.words[18]=section->depth;NativeExportProof after;api.after=measured_api(name.c_str(),address,&after);std::memcpy(api.export_after.data(),&after,sizeof(after));if(api.before!=api.after||api.export_before!=api.export_after)deny("Actual measured critical-section export identity remained stable",guest,site);
 checkpoint(runtime,("locale-api-"+std::to_string(native_apis_.size()-1)+"-after").c_str());stable_hook(41);guard();source_identity();api_return(frame,argc,preserve_eax);
}
bool Binding::cleanup_sections_noexcept()noexcept{
 if(std::this_thread::get_id()!=thread_)return false;InvocationHostBoundary hardware;const auto saved=GetLastError();bool okay=true;
 for(auto i=owned_sections_.rbegin();i!=owned_sections_.rend();++i){auto&p=**i;if(!p.initialized||p.deleted)continue;if(p.depth&&p.owner_thread!=thread_){okay=false;continue;}while(p.depth){if(!lifecycle_api("LeaveCriticalSection",0x7802e048,0x3449a,reinterpret_cast<std::uintptr_t>(&p.native),[&](){::LeaveCriticalSection(&p.native);--p.depth;++p.leaves;return true;})){okay=false;break;}}if(p.depth)continue;if(!lifecycle_api("DeleteCriticalSection",0x7802e040,0x3446a,reinterpret_cast<std::uintptr_t>(&p.native),[&](){::DeleteCriticalSection(&p.native);p.deleted=true;++p.deletes;++sections_deleted_;return true;}))okay=false;}
 SetLastError(saved);return okay;
}
bool Binding::cleanup_allocations_noexcept()noexcept{
 if(std::this_thread::get_id()!=thread_)return false;InvocationHostBoundary hardware;const auto saved=GetLastError();bool okay=true;if(live_critical_sections()){SetLastError(saved);return false;}
 for(auto i=owned_allocations_.rbegin();i!=owned_allocations_.rend();++i){auto&p=**i;if(!p.native)continue;if(!owned_handle_){okay=false;continue;}if(!lifecycle_api("HeapFree",free_iat,free_raw,p.acquired,[&](){const auto result=::HeapFree(owned_handle_,0,p.native);if(result){p.native=nullptr;p.cleanup_freed=true;++allocations_cleanup_freed_;}return result!=FALSE;}))okay=false;if(!p.native&&p.mapped){try{runtime.memory().unmap({p.guest});p.mapped=false;}catch(...){okay=false;}}}
 SetLastError(saved);return okay;
}

template<class F>bool Binding::lifecycle_api(const char*name,unsigned slot,unsigned raw,std::uint64_t subject,F&&action)noexcept{
 if(std::this_thread::get_id()!=thread_)return false;try{
  const std::string n=name;const auto address=n=="HeapFree"?reinterpret_cast<std::uintptr_t>(&::HeapFree):n=="LeaveCriticalSection"?reinterpret_cast<std::uintptr_t>(&::LeaveCriticalSection):reinterpret_cast<std::uintptr_t>(&::DeleteCriticalSection);
  ApiCapture record;record.words={1,native_apis_.size(),0,slot,raw,0,0,0,0,caller_error,0,0,0,0,0,0,subject,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1};NativeExportProof before;record.before=measured_api(name,address,&before);std::memcpy(record.export_before.data(),&before,sizeof(before));native_apis_.push_back(std::move(record));auto&api=native_apis_.back();bool okay{};
  {InvocationHostBoundary hardware;fn::LastErrorBoundary errors;SetLastError(caller_error);api.words[9]=GetLastError();okay=action();api.words[10]=GetLastError();SetLastError(caller_error);api.words[11]=GetLastError();}
  api.words[8]=okay;api.words[14]=1;api.words[15]=1;NativeExportProof after;api.after=measured_api(name,address,&after);std::memcpy(api.export_after.data(),&after,sizeof(after));return okay&&api.before==api.after&&api.export_before==api.export_after;
 }catch(...){return false;}
}
void Binding::batch_control(unsigned point){
 if(control_used_)return;
 if(control==211&&point==60){control_used_=true;throw std::runtime_error("Authored observer exception after genuine builder RET before completion publication");}
 if(native_apis_.empty())return;const auto&api=native_apis_.back();const auto slot=api.words[3],site=api.words[2];
 if(control==201&&point==40&&site==0x78003c01){control_used_=true;throw std::runtime_error("Authored observer exception before first actual static critical-section initialization");}
 if(control==202&&point==41&&site==0x78003c01){control_used_=true;throw std::runtime_error("Authored observer exception after first actual static critical-section initialization");}
 if(control==203&&point==40&&slot==alloc_iat){control_used_=true;runtime.memory().map({allocation_cursor_},4096,Permissions::read|Permissions::write);}
 if(control==204&&point==40&&slot==0x7802e044){control_used_=true;runtime.memory().store<unsigned>({static_cast<unsigned>(api.words[5])+4},0x13579bdf);}
 if(control==205&&point==40&&slot==0x7802e0c4){control_used_=true;runtime.memory().protect({static_cast<unsigned>(api.words[21])&~4095U},Permissions::read);}
 if(control==206&&point==41&&slot==0x7802e0c4){control_used_=true;throw std::runtime_error("Authored observer exception after actual code-page API response");}
 if(control==208&&point==40&&slot==0x7802e0c4){control_used_=true;auto address=static_cast<unsigned>(slot);runtime.memory().protect({address&~4095U},Permissions::read|Permissions::write);runtime.memory().store<unsigned>({address},static_cast<unsigned>(api.words[4])^1);}
 if(control==209&&point==43&&slot==0x7802e018){control_used_=true;runtime.memory().protect({program_input_},Permissions::read|Permissions::write);auto b=runtime.memory().load<unsigned char>({program_input_});runtime.memory().store<unsigned char>({program_input_},b^1);runtime.memory().protect({program_input_},Permissions::read);}
 if(control==212&&point==40){control_used_=true;runtime.cpu().eax^=1;}
}

void Binding::native_nls(unsigned site,unsigned frame,unsigned argc){
 static_assert(sizeof(wchar_t)==2&&sizeof(WORD)==2&&sizeof(CPINFO)==20);
 auto&api=native_apis_.back();auto spec=std::find_if(source_api_contracts().begin(),source_api_contracts().end(),[&](const auto&a){return a.site==site&&a.raw==api.words[4];});if(spec==source_api_contracts().end())deny("Exact recovered native NLS API name required",site);const auto name=std::string(spec->name);
 std::array<unsigned,8>a{};for(unsigned n=0;n<argc;++n)a[n]=api.words[20+n];
 auto input_bytes=[&](unsigned pointer,int count,unsigned unit){if(count<-1||count>65536)deny("Finite exact native text input count required",pointer,site);unsigned bytes{};std::uint64_t limit=0x100000000ULL;
  if(pointer>=0x31000000&&pointer<0x32000000){auto*p=allocation_for(pointer);if(!p||pointer>=std::uint64_t(p->guest)+p->requested)deny("Native input must begin inside current requested allocation extent",pointer,site);limit=std::uint64_t(p->guest)+p->requested;}
  if(program_input_&&pointer>=program_input_&&pointer<std::uint64_t(program_input_)+131072){if(pointer>=std::uint64_t(program_input_)+program_extent_)deny("Native input must begin inside actual owned command line",pointer,site);limit=std::uint64_t(program_input_)+program_extent_;}
  if(count==-1){bool end{};for(unsigned n=0;n<65536;++n){if(std::uint64_t(pointer)+(n+1)*unit>limit)deny("Native negative-length scan cannot cross requested/owned input extent",pointer+n*unit,site);auto b=guest_bytes(pointer+n*unit,unit);if(std::all_of(b.begin(),b.end(),[](auto v){return v==std::byte{};})){bytes=(n+1)*unit;end=true;break;}}if(!end)deny("Actual native text input needs bounded guest NUL",pointer,site);}
  else{bytes=static_cast<unsigned>(count)*unit;if(std::uint64_t(pointer)+bytes>limit)deny("Native input count cannot cross requested/owned input extent",pointer,site);}auto b=guest_bytes(pointer,bytes);const unsigned index=api.inputs.size();api.inputs.push_back(b);api.buffers.push_back({pointer,bytes,1,index});return b;};
 std::vector<char>input_a,output_a;std::vector<wchar_t>input_w,output_w;std::vector<WORD>output_types;
 CPINFO info{};BOOL used_default{};std::array<char,2>default_character{};
 struct Output {unsigned address,bytes;const void*data;};std::vector<Output>outputs;
 auto output_before=[&](unsigned address,unsigned bytes){if(bytes>1024*1024)deny("Finite exact native output extent required",address,site);auto b=guest_bytes(address,bytes);preflight_write(address,bytes);const unsigned index=static_cast<unsigned>(api.inputs.size());api.inputs.push_back(b);api.buffers.push_back({address,bytes,2,index});return b;};
 auto chars=[&](auto&vector,const std::vector<std::byte>&bytes,unsigned units){vector.resize(std::max(1U,units));if(!bytes.empty())std::memcpy(vector.data(),bytes.data(),bytes.size());};
 std::function<unsigned()>call;std::uintptr_t target{};
 if(name=="GetACP"||name=="GetOEMCP"){if(argc)deny("Exact no-argument code-page resolver API required",site);target=name=="GetACP"?reinterpret_cast<std::uintptr_t>(&::GetACP):reinterpret_cast<std::uintptr_t>(&::GetOEMCP);call=[&](){return name=="GetACP" ? ::GetACP() : ::GetOEMCP();};}
 else if(name=="GetCPInfo"){if(argc!=2||!a[1])deny("Exact genuine CPINFO output pointer required",site);auto b=output_before(a[1],sizeof(info));std::memcpy(&info,b.data(),sizeof(info));outputs.push_back({a[1],sizeof(info),&info});target=reinterpret_cast<std::uintptr_t>(&::GetCPInfo);call=[&](){return static_cast<unsigned>(::GetCPInfo(a[0],&info));};}
 else if(name=="GetModuleFileNameA"){if(argc!=3||a[0]||!a[1]||!a[2]||a[2]>32768)deny("Actual process filename NULL/module bounded output contract required",site);auto b=output_before(a[1],a[2]);chars(output_a,b,a[2]);outputs.push_back({a[1],a[2],output_a.data()});target=reinterpret_cast<std::uintptr_t>(&::GetModuleFileNameA);call=[&](){return ::GetModuleFileNameA(nullptr,output_a.data(),a[2]);};}
 else if(name=="MultiByteToWideChar"){
  if(argc!=6||static_cast<int>(a[5])<0||a[5]>65536)deny("Bounded genuine MultiByteToWideChar arguments required",site);auto in=input_bytes(a[2],static_cast<int>(a[3]),1);chars(input_a,in,in.size());
  if(a[4]){auto out=output_before(a[4],2*a[5]);chars(output_w,out,a[5]);outputs.push_back({a[4],2*a[5],output_w.data()});}else if(a[5])deny("Null native conversion output requires zero capacity",site);
  target=reinterpret_cast<std::uintptr_t>(&::MultiByteToWideChar);call=[&](){return static_cast<unsigned>(::MultiByteToWideChar(a[0],a[1],a[2]?input_a.data():nullptr,static_cast<int>(a[3]),a[4]?output_w.data():nullptr,a[5]));};
 }
 else if(name=="WideCharToMultiByte"){
  if(argc!=8||static_cast<int>(a[5])<0||a[5]>65536)deny("Bounded genuine WideCharToMultiByte arguments required",site);auto in=input_bytes(a[2],static_cast<int>(a[3]),2);chars(input_w,in,in.size()/2);
  if(a[4]){auto out=output_before(a[4],a[5]);chars(output_a,out,a[5]);outputs.push_back({a[4],a[5],output_a.data()});}else if(a[5])deny("Null native byte conversion output requires zero capacity",site);
  if(a[6]){auto d=input_bytes(a[6],2,1);std::memcpy(default_character.data(),d.data(),2);}if(a[7]){auto b=output_before(a[7],4);std::memcpy(&used_default,b.data(),4);outputs.push_back({a[7],4,&used_default});}
  target=reinterpret_cast<std::uintptr_t>(&::WideCharToMultiByte);call=[&](){return static_cast<unsigned>(::WideCharToMultiByte(a[0],a[1],a[2]?input_w.data():nullptr,static_cast<int>(a[3]),a[4]?output_a.data():nullptr,a[5],a[6]?default_character.data():nullptr,a[7]?&used_default:nullptr));};
 }
 else if(name=="GetStringTypeW"||name=="GetStringTypeA"){
  const bool wide=name=="GetStringTypeW";if(argc!=(wide?4U:5U))deny("Exact string-type original argument count required",site);const unsigned input_index=wide?1:2,count_index=wide?2:3,out_index=wide?3:4;auto in=input_bytes(a[input_index],static_cast<int>(a[count_index]),wide?2:1);const unsigned units=static_cast<unsigned>(in.size()/(wide?2:1));
  if(wide)chars(input_w,in,units);else chars(input_a,in,units);if(!a[out_index]||!units)deny("Actual string-type output must cover bounded input",site);auto out=output_before(a[out_index],2*units);chars(output_types,out,units);outputs.push_back({a[out_index],2*units,output_types.data()});
  target=wide?reinterpret_cast<std::uintptr_t>(&::GetStringTypeW):reinterpret_cast<std::uintptr_t>(&::GetStringTypeA);call=[&,wide](){return static_cast<unsigned>(wide ? ::GetStringTypeW(a[0],a[1]?input_w.data():nullptr,static_cast<int>(a[2]),output_types.data()) : ::GetStringTypeA(a[0],a[1],a[2]?input_a.data():nullptr,static_cast<int>(a[3]),output_types.data()));};
 }
 else if(name=="LCMapStringW"||name=="LCMapStringA"){
  const bool wide=name=="LCMapStringW";if(argc!=6||static_cast<int>(a[5])<0||a[5]>65536)deny("Bounded exact locale-map argument contract required",site);auto in=input_bytes(a[2],static_cast<int>(a[3]),wide?2:1);if(wide)chars(input_w,in,in.size()/2);else chars(input_a,in,in.size());
  const bool byte_output=!wide||(a[1]&LCMAP_SORTKEY);const auto output_bytes=a[5]*(byte_output?1:2);if(a[4]){auto out=output_before(a[4],output_bytes);if(!wide){chars(output_a,out,output_bytes);outputs.push_back({a[4],output_bytes,output_a.data()});}else{chars(output_w,out,(output_bytes+1)/2);outputs.push_back({a[4],output_bytes,output_w.data()});}}else if(a[5])deny("Null locale-map destination requires zero capacity",site);
  target=wide?reinterpret_cast<std::uintptr_t>(&::LCMapStringW):reinterpret_cast<std::uintptr_t>(&::LCMapStringA);call=[&,wide](){if(wide)return static_cast<unsigned>(::LCMapStringW(a[0],a[1],a[2]?input_w.data():nullptr,static_cast<int>(a[3]),a[4]?output_w.data():nullptr,a[5]));return static_cast<unsigned>(::LCMapStringA(a[0],a[1],a[2]?input_a.data():nullptr,static_cast<int>(a[3]),a[4]?output_a.data():nullptr,a[5]));};
 }
 else deny("Required measured native API is not implemented in locale batch",api.words[3],site);
 api.words[29]=api.inputs.size();api.words[30]=outputs.size();NativeExportProof before;api.before=measured_api(name.c_str(),target,&before);std::memcpy(api.export_before.data(),&before,sizeof(before));
 checkpoint(runtime,("locale-api-"+std::to_string(native_apis_.size()-1)+"-before").c_str());stable_hook(40);guard();source_identity();
 for(const auto&out:outputs)preflight_write(out.address,out.bytes);for(const auto&buffer:api.buffers)if(guest_bytes(buffer[0],buffer[1])!=api.inputs[buffer[3]])deny("Actual admitted API input/output BEFORE bytes changed before native call",buffer[0],site);
 unsigned result{};{InvocationHostBoundary hardware;fn::LastErrorBoundary error;SetLastError(caller_error);api.words[9]=GetLastError();result=call();api.words[10]=GetLastError();SetLastError(caller_error);api.words[11]=GetLastError();}
 api.words[8]=result;api.words[12]=result;api.words[14]=1;for(const auto&out:outputs){std::vector<std::byte>b(out.bytes);if(out.bytes)std::memcpy(b.data(),out.data,out.bytes);api.outputs.push_back(std::move(b));}
 NativeExportProof after;api.after=measured_api(name.c_str(),target,&after);std::memcpy(api.export_after.data(),&after,sizeof(after));if(api.before!=api.after||api.export_before!=api.export_after)deny("Actual measured native NLS API identity changed",api.words[3],site);
 checkpoint(runtime,("locale-api-"+std::to_string(native_apis_.size()-1)+"-after").c_str());stable_hook(41);guard();source_identity();
 for(unsigned n=0;n<outputs.size();++n){api_transfer(outputs[n].address,api.outputs[n]);api.words[13]+=outputs[n].bytes;}
 checkpoint(runtime,("locale-api-"+std::to_string(native_apis_.size()-1)+"-output-after").c_str());stable_hook(42);guard();source_identity();api_return(frame,argc,result);
 checkpoint(runtime,("locale-api-"+std::to_string(native_apis_.size()-1)+"-returned").c_str());stable_hook(43);guard();source_identity();
}
