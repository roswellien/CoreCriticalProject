namespace {
const FormattingRoot*formatting_root(unsigned root){for(const auto&r:formatting_roots)if(r.root==root)return &r;return nullptr;}
void Binding::formatting_enter(){
 const auto*r=formatting_root(registry_root_);if(!r)return;
 if(formatting_active_||runtime.memory().load<unsigned>({r->publication})||state.addr.es_base.dword)
  deny("Fresh exact normal formatter object and flat ES input required",r->publication);
 formatting_active_=true;formatting_base_=formatting_owner_=formatting_generation_=formatting_owned_cursor_=formatting_dispatch_cursor_=formatting_publications_=0;
}
std::uint64_t Binding::formatting_read(unsigned address,std::uint64_t value,unsigned bytes){
 if(!formatting_active_)return value;const auto pc=state.gpr.rip.dword;
 for(const auto&r:formatting_imports)if(pc==r.pc){
  if(bytes!=4||address!=r.slot||value!=r.raw)deny("Exact formatter source import cell and owning read PC",address,pc);
  research_projections_.push_back({5,pc,address,unsigned(value),r.target,0,0,0});return r.target;
 }
 if(pc==0x7800fcef){
  constexpr unsigned order[]{1,7,1,7};const auto index=state.gpr.rax.dword;
  if(formatting_dispatch_cursor_>=4||index!=order[formatting_dispatch_cursor_]||bytes!=4||address!=0x780103fa+4*index||value!=(index==1?0x7800fd04U:0x7800fe69U))
   deny("Formatter exact narrow table branch and current source index",address,pc);
  formatting_dispatches_.push_back({1,registry_root_,formatting_dispatch_cursor_,pc,index,address,value,source_accesses_.size()});++formatting_dispatch_cursor_;
 }
 return value;
}
void Binding::formatting_owner_before(unsigned address,std::uint64_t value,unsigned bytes,bool writing){
 if(!formatting_active_)return;const auto pc=state.gpr.rip.dword;
 const bool required=pc==0x7801042a||pc==0x78022bd5;
 auto*a=allocation_for(address,bytes);if(!a){if(required)deny("Formatter source output requires its current live owner",address,pc);return;}
 if(!required){if(a->guest==formatting_owner_&&pc>=0x78000000)deny("No unproved formatter private backing operand",address,pc);return;}
 const auto*r=formatting_root(registry_root_);
 if(!r||a->guest!=formatting_owner_||a->generation!=formatting_generation_||a->kind!=1||a->requested!=r->request||a->extent!=16||std::uint64_t(address)+bytes>std::uint64_t(a->guest)+a->requested||formatting_owned_cursor_>=r->owned_count)
  deny("Formatter exact malloc generation, requested bounds and finite operand order",address,pc);
 const auto&e=formatting_owned_order[r->owned_begin+formatting_owned_cursor_];
 if(e.pc!=pc||e.offset!=address-a->guest||e.bytes!=bytes||e.writing!=writing||(writing&&e.value!=value))
  deny("Formatter exact literal byteflow and ordered source owner offset",address,pc);
}
void Binding::formatting_owner_after(unsigned address,std::uint64_t value,unsigned bytes,bool writing){
 if(!formatting_active_)return;const auto pc=state.gpr.rip.dword;
 if(pc==0x7801042a||pc==0x78022bd5){
  const auto*r=formatting_root(registry_root_);const auto&e=formatting_owned_order[r->owned_begin+formatting_owned_cursor_];
  if(writing&&e.value!=value)deny("Formatter write value is literal source-derived",address,pc);
  if(!writing){auto*a=allocation_for(address,bytes);if(!a||a->initial[address-a->guest]!=std::byte(value))deny("Formatter NUL RMW reads its genuine untouched allocation input byte",address,pc);}
  formatting_owned_.push_back({1,registry_root_,formatting_owned_cursor_,pc,address,bytes,unsigned(writing),value,formatting_owner_,formatting_generation_,address-formatting_owner_,source_accesses_.size()});++formatting_owned_cursor_;
 }
 if(writing&&pc==0x4deabc){
  const auto*r=formatting_root(registry_root_);auto*a=allocation_for(unsigned(value),1);
  if(!r||bytes!=4||address!=r->publication||!a||value!=formatting_owner_||a->generation!=formatting_generation_||formatting_publications_++)
   deny("Formatter primary publication binds exact source field and actual malloc occurrence",address,pc);
  formatting_publication_records_.push_back({1,registry_root_,pc,address,value,a->generation,a->requested,a->extent,source_accesses_.size(),0,0,0});
 }
}
void Binding::formatting_called(unsigned target,unsigned site,unsigned frame){
 if(!formatting_active_)return;const auto*r=formatting_root(registry_root_);
 if(target==0x4de9c0){if(formatting_base_)deny("One shared formatter constructor per root",target,site);formatting_base_=frame;return;}
 const FormattingImport*spec{};for(const auto&i:formatting_imports)if(i.pc==site)spec=&i;
 if(!spec)return;
 if(!formatting_base_||target!=spec->target||frame!=formatting_base_+spec->frame_offset||runtime.memory().load<unsigned>({frame})!=site+6)
  deny("Exact formatter cdecl entry frame and source constructor lifetime",frame,site);
 const auto first=runtime.memory().load<unsigned>({frame+4});
 if(target==0x780264a9){if(first!=r->filename||runtime.memory().load<unsigned>({frame+8})!=0x2e)deny("Exact original filename/dot search arguments",frame,site);}
 if(target==malloc_entry){if(first!=r->request||formatting_owner_)deny("One exact source-computed formatter malloc request",frame,site);}
 if(target==0x78022b9a){if(first!=formatting_owner_||runtime.memory().load<unsigned>({frame+8})!=0x5e37f0||runtime.memory().load<unsigned>({frame+12})!=r->filename||runtime.memory().load<unsigned>({frame+16})!=formatting_base_-8||runtime.memory().load<unsigned>({formatting_base_-8})!=0x64727a2e||runtime.memory().load<unsigned char>({formatting_base_-4}))deny("Exact source output owner/format/filename/suffix cdecl arguments",frame,site);}
 std::array<std::uint64_t,16>row{1,registry_root_,site,target,frame,formatting_base_,spec->argc,0,0,0,0,0,formatting_owner_,formatting_generation_,0,0};for(unsigned k=0;k<spec->argc;++k)row[7+k]=runtime.memory().load<unsigned>({frame+4+4*k});formatting_calls_.push_back(row);
}
void Binding::formatting_returned(unsigned entry,unsigned result,unsigned frame){
 if(!formatting_active_)return;const auto*r=formatting_root(registry_root_);
 if(entry==malloc_entry){auto*a=allocation_for(result,1);if(!a||a->guest!=result||a->requested!=r->request||a->extent!=16||a->kind!=1||!a->native||formatting_owner_)deny("Genuine formatter malloc RET owns one actual round16 backing",result);formatting_owner_=result;formatting_generation_=a->generation;}
 if(entry==0x780264a9||entry==malloc_entry||entry==0x78022b9a){
  auto it=std::find_if(formatting_calls_.rbegin(),formatting_calls_.rend(),[&](const auto&w){return w[1]==registry_root_&&w[3]==entry&&!w[14];});
  if(it==formatting_calls_.rend()||(*it)[4]!=frame||state.gpr.rsp.dword!=frame+4)deny("Formatter exact genuine cdecl RET and outstanding invocation",frame);
  (*it)[12]=formatting_owner_;(*it)[13]=formatting_generation_;(*it)[14]=1;(*it)[15]=result;
  if(entry==0x780264a9&&result)deny("Only measured no-dot filename path admitted",result);
  if(entry==0x78022b9a&&(result!=r->request-1||formatting_owned_cursor_!=r->owned_count||formatting_dispatch_cursor_!=4||formatting_publications_!=1))deny("Complete literal formatter count, byte operands, table branches and publication",result);
 }
 if(entry==registry_root_){if(formatting_owned_cursor_!=r->owned_count||formatting_dispatch_cursor_!=4||formatting_publications_!=1)deny("Complete exact normal formatter root lifetime",entry);formatting_active_=false;++formatting_completed_;}
}
}
