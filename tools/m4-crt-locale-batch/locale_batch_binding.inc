} // composition anonymous namespace
namespace mw34::m4_crt_locale_batch {
namespace {thread_local Binding*authority{};thread_local Binding*capture_binding{};struct CallerComplete{};}
bool has_authority()noexcept{return authority!=nullptr;}
std::array<unsigned,8>Binding::progress()const noexcept{return {1,unsigned(selector_unwound_private_),unsigned(mode_store_before_private_),unsigned(mode_published_private_),mode_value_private_,unsigned(initializer_return_before_private_),unsigned(initializer_returned_private_),unsigned(token_valid(token))};}
const Binding*capture_for(m4_runtime::Runtime&r)noexcept{return capture_binding&& &capture_binding->runtime==&r?capture_binding:nullptr;}
bool Binding::authority_is_current()const noexcept{return authority==this&&owner==this&&binding==this&&admitted_binding==this&&parent==admitted_parent_&&active&&thread_==std::this_thread::get_id();}
#include "forward_identity.inc"
m4_cmd_native::ApiIdentity measured_api(const char*name,std::uintptr_t actual,NativeExportProof*proof=nullptr){
 fn::LastErrorBoundary errors;InvocationHostBoundary fp;m4_cmd_native::ApiIdentity a;a.target=actual;
 auto kernel=GetModuleHandleW(L"kernel32.dll");if(!kernel)throw std::runtime_error("Loaded heap API module required");
 a.named_target=reinterpret_cast<std::uintptr_t>(GetProcAddress(kernel,name));if(a.named_target!=actual)throw std::runtime_error("Actual imported heap API differs from named export");
 a.region=m4_cmd_native::region(reinterpret_cast<const void*>(actual));if(a.region.state!=MEM_COMMIT||a.region.type!=MEM_IMAGE||(a.region.protect&(PAGE_GUARD|PAGE_NOACCESS))||!(a.region.protect&(PAGE_EXECUTE|PAGE_EXECUTE_READ|PAGE_EXECUTE_READWRITE|PAGE_EXECUTE_WRITECOPY)))throw std::runtime_error("Loaded executable heap API identity required");
 a.owner=a.region.allocation;if(proof){*proof=prove_native_export(name,actual,a);a.owner_named_target=proof->scalar[5];}else a.owner_named_target=reinterpret_cast<std::uintptr_t>(GetProcAddress(reinterpret_cast<HMODULE>(a.owner),name));if(a.owner_named_target!=actual)throw std::runtime_error("Actual heap API owner named export required");
 std::array<wchar_t,32768>path{};auto n=GetModuleFileNameW(reinterpret_cast<HMODULE>(a.owner),path.data(),static_cast<DWORD>(path.size()));if(!n||n>=path.size())throw std::runtime_error("Actual heap API module path bounds");a.module_path.assign(path.data(),n);a.module_sha=m4::sha256(m4_cmd_native::readfile(std::filesystem::path(a.module_path),16*1024*1024));return a;
}
 unsigned original_query_import(std::span<const std::byte>b){
  if(m4::sha256(b)!="2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7")throw std::invalid_argument("Exact provider import source required");
  auto word=[&](unsigned p){if(std::uint64_t(p)+2>b.size())throw std::invalid_argument("Provider PE word bounds");unsigned short v{};std::memcpy(&v,b.data()+p,2);return v;};
  auto dword=[&](unsigned p){if(std::uint64_t(p)+4>b.size())throw std::invalid_argument("Provider PE DWORD bounds");unsigned v{};std::memcpy(&v,b.data()+p,4);return v;};
  const auto pe=dword(0x3c),opt=pe+24;if(dword(pe)!=0x4550||word(pe+4)!=0x14c||word(opt)!=0x10b||dword(opt+28)!=0x78000000)throw std::invalid_argument("Exact PE32 provider import authority");
  auto offset=[&](unsigned rva,unsigned size){unsigned matches{},result{};for(unsigned n=0;n<word(pe+6);++n){const auto p=opt+word(pe+20)+n*40,va=dword(p+12),rs=dword(p+16),rp=dword(p+20);if(rva>=va&&std::uint64_t(rva)+size<=std::uint64_t(va)+rs){result=rp+rva-va;++matches;}}if(matches!=1||std::uint64_t(result)+size>b.size())throw std::invalid_argument("Provider import raw RVA bounds");return result;};
  auto text=[&](unsigned rva){const auto p=offset(rva,1);std::string result;for(unsigned n=0;n<4096;++n){if(p+n>=b.size())throw std::invalid_argument("Provider name bounds");auto v=std::to_integer<unsigned char>(b[p+n]);if(!v)return result;result.push_back(static_cast<char>(v));}throw std::invalid_argument("Terminated provider import name required");};
  const auto directory=dword(opt+104),size=dword(opt+108);unsigned matches{},result{};bool terminal{};
  for(unsigned d=0;d<size/20;++d){const auto p=offset(directory+d*20,20),original=dword(p),name=dword(p+12),iat=dword(p+16);if(!(original||dword(p+4)||dword(p+8)||name||iat)){terminal=true;break;}const auto library=text(name);const auto lookup=original?original:iat;bool end{};
   for(unsigned n=0;n<8192;++n){const auto value=dword(offset(lookup+4*n,4));if(!value){end=true;break;}if(!(value&0x80000000U)&&text(value+2)=="GetVersionExA"){if(library!="KERNEL32.dll"||0x78000000+iat+4*n!=mw34::m4_crt_locale_batch::query_iat||word(offset(value,2))!=373)throw std::invalid_argument("Exact unique provider GetVersionExA name/hint/slot");result=dword(offset(iat+4*n,4));++matches;}}
   if(!end)throw std::invalid_argument("Provider import thunk termination");
  }if(!terminal||matches!=1)throw std::invalid_argument("Exactly one named GetVersionExA provider import");return result;
 }
 unsigned original_allocation_import(std::span<const std::byte>b,const char*requested,unsigned slot,unsigned hint){
  if(m4::sha256(b)!="2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7")throw std::invalid_argument("Exact provider import source required");
  auto word=[&](unsigned p){if(std::uint64_t(p)+2>b.size())throw std::invalid_argument("Provider PE word bounds");unsigned short v{};std::memcpy(&v,b.data()+p,2);return v;};
  auto dword=[&](unsigned p){if(std::uint64_t(p)+4>b.size())throw std::invalid_argument("Provider PE DWORD bounds");unsigned v{};std::memcpy(&v,b.data()+p,4);return v;};
  const auto pe=dword(0x3c),opt=pe+24;if(dword(pe)!=0x4550||word(pe+4)!=0x14c||word(opt)!=0x10b||dword(opt+28)!=0x78000000)throw std::invalid_argument("Exact PE32 provider import authority");
  auto offset=[&](unsigned rva,unsigned size){unsigned matches{},result{};for(unsigned n=0;n<word(pe+6);++n){const auto p=opt+word(pe+20)+n*40,va=dword(p+12),rs=dword(p+16),rp=dword(p+20);if(rva>=va&&std::uint64_t(rva)+size<=std::uint64_t(va)+rs){result=rp+rva-va;++matches;}}if(matches!=1||std::uint64_t(result)+size>b.size())throw std::invalid_argument("Provider import raw RVA bounds");return result;};
  auto text=[&](unsigned rva){const auto p=offset(rva,1);std::string result;for(unsigned n=0;n<4096;++n){if(p+n>=b.size())throw std::invalid_argument("Provider name bounds");auto v=std::to_integer<unsigned char>(b[p+n]);if(!v)return result;result.push_back(static_cast<char>(v));}throw std::invalid_argument("Terminated provider import name required");};
  const auto directory=dword(opt+104),size=dword(opt+108);unsigned matches{},result{};bool terminal{};
  for(unsigned d=0;d<size/20;++d){const auto p=offset(directory+d*20,20),original=dword(p),name=dword(p+12),iat=dword(p+16);if(!(original||dword(p+4)||dword(p+8)||name||iat)){terminal=true;break;}const auto library=text(name);const auto lookup=original?original:iat;bool end{};
   for(unsigned n=0;n<8192;++n){const auto value=dword(offset(lookup+4*n,4));if(!value){end=true;break;}if(!(value&0x80000000U)&&text(value+2)==requested){if(library!="KERNEL32.dll"||0x78000000+iat+4*n!=slot||word(offset(value,2))!=hint)throw std::invalid_argument("Exact unique provider GetVersionExA name/hint/slot");result=dword(offset(iat+4*n,4));++matches;}}
   if(!end)throw std::invalid_argument("Provider import thunk termination");
  }if(!terminal||matches!=1)throw std::invalid_argument("Exactly one named GetVersionExA provider import");return result;
 }

Binding::Binding(mg::Context&c,std::span<const std::byte>provider,unsigned ctl):runtime(c.runtime),state(c.state),parent(&c),control(ctl),admitted_parent_(&c),admitted_control_(ctl){
 m4_cmd_native::Provider p(provider);source_[0]=p.slice({fragment},7,0x60000000);source_[1]=p.slice({entry},77,0x60000000);source_[2]=p.slice({global},4096,0xc0000000);
 if(m4::sha256(source_[0])!="67c33f8cdb056ef8c51db43178b7fec29b78f7da00d0d4b0c34fde166a0fc6f1"||m4::sha256(source_[1])!="72922b45de858dc84ab5a08a8626acf0fca8487bd1e1cba955a3c0afba30e6ba"||m4::sha256(source_[2])!="e26f5dc868bcd5e27e775540dc063331d45d91dc5f6863560f04b0a252e68c50"||m4_crt_heap_init::original_import(provider)!=raw_import||p.dword({iat})!=raw_import)throw std::invalid_argument("Exact heap source, raw RW page and unique named HeapCreate import required");
 source_[3]=p.slice({mode},37,0x60000000);source_[4]=p.slice({probe},49,0x60000000);source_[5]=p.slice({0x78005000},4096,0x60000000);
 if(m4::sha256(source_[3])!="40dd412d93fff04b1e6bb4fd70fd4ecca4cf95cc9d4c152906a537f0ebbc2135"||m4::sha256(source_[4])!="6c3968aa37f1e1ba00793f924b85c69c73dedc74491d3770c477e82b6107dd77"||m4::sha256(source_[5])!="fe49ff60694b0a98e256fe973938e06a77c7c1a71dd6963f46c7d75e6bd32c9e"||original_query_import(provider)!=query_raw||p.dword({query_iat})!=query_raw)throw std::invalid_argument("Exact bounded selector, complete probe, raw RX page and unique OS-query import required");
 source_[6]=p.slice({2013280817},26,0x60000000);if(m4::sha256(source_[6])!="01a55efb16ac7d967cd8751767e9a5d4f777789dddc2721da7cbd09094e0a1e6")throw std::invalid_argument("Exact fresh version continuation source required");
 source_[7]=p.slice({2013280843},23,0x60000000);if(m4::sha256(source_[7])!="dc83bfaa45738e3c6b43b1f52f85c3fac14df0a3d0ac8e659bec4207c260a39b")throw std::invalid_argument("Exact fresh version continuation source required");
 source_[8]=p.slice({2013318341},8,0x60000000);if(m4::sha256(source_[8])!="4d90edd4b00e939a6870c8aef54d9893f207146959ae0a499825a51ac1f6b237")throw std::invalid_argument("Exact fresh version continuation source required");
 source_[9]=p.slice({2013280893},3,0x60000000);if(m4::sha256(source_[9])!="c6828dbffb37926291e846b3b503a42921c7e0bb1b6e2026b416c1218d33680d")throw std::invalid_argument("Exact fresh version continuation source required");
 source_[10]=p.slice({0x7800c000},4096,0x60000000);if(m4::sha256(source_[10])!="25bd92364d0f450dda6dde287dbeb44ac27d890e3d03c10d73b504d071defb32")throw std::invalid_argument("Exact raw cold selector RX page required");
 runtime.memory().read({lower_stack},lower_initial_);lower_expected_=lower_initial_;
 runtime.memory().read({0x20001000},upper_initial_);upper_expected_=upper_initial_;
 if(state.addr.fs_base.dword!=runtime.fs_base().value)throw std::invalid_argument("Exact carried guest FS base required");
 fs_previous_=fs_expected_=runtime.memory().load<unsigned>(runtime.fs_base());
 for(auto [a,n]:std::array<std::pair<unsigned,unsigned>,8>{{{caller_cleanup,9},{malloc_entry,18},{size_entry,30},{worker_entry,173},{0x7800cc97,21},{0x7800cc3f,35},{free_entry,177},{0x7800cc39,6}}})allocator_sources_.push_back({a,p.slice({a},n,0x60000000)});
 if(original_allocation_import(provider,"HeapAlloc",alloc_iat,409)!=alloc_raw||original_allocation_import(provider,"HeapFree",free_iat,415)!=free_raw||p.dword({alloc_iat})!=alloc_raw||p.dword({free_iat})!=free_raw)throw std::invalid_argument("Exact original HeapAlloc/HeapFree IATs required");
 registry_snapshot();allocator_snapshot();
}
Binding::~Binding()noexcept{(void)cleanup_sections_noexcept();(void)cleanup_allocations_noexcept();if(owned_allocation_)(void)release_allocation_noexcept();if(owned_handle_)(void)release_noexcept();if(capture_binding==this)capture_binding=nullptr;}
Binding*current(void*p,unsigned a){auto*known=authority;if(!known)throw std::invalid_argument("Heap creation active private authority absent");if(p!=known||owner!=known||binding!=known||admitted_binding!=known)known->deny("Exact current exclusive heap creation token required",a);return known;}
void Binding::first(const char*w,unsigned a,unsigned pc){if(!failed){failed=true;reason=w;fault_pc=pc?pc:state.gpr.rip.dword;fault_address=a;}}
[[noreturn]]void Binding::deny(const char*w,unsigned a,unsigned pc){first(w,a,pc);admitted_parent_->first(reason,fault_address,fault_pc);throw mg::BridgeAbort{};}
void Binding::admit_current(){if(authority&&authority!=this)authority->deny("Stale heap creation binding cannot use current authority",entry);if(binding!=this||admitted_binding!=this)deny("Exact admitted heap creation side binding required",entry);if(parent!=admitted_parent_||&admitted_parent_->runtime!=&runtime||&admitted_parent_->state!=&state)deny("Immutable heap creation parent association required",entry);}
void Binding::registry_snapshot()noexcept{registry={1,reinterpret_cast<std::uintptr_t>(this),1,registered_?token:0,acquired_handle_,unsigned(acquired_handle_!=0),unsigned(registered_),unsigned(owned_handle_!=nullptr),unsigned(create_called_),destroy_calls_,destroy_successes_,destroy_error_,cleanup_attempts_,cleanup_skips_,unsigned(rollback_),unsigned(finalized_),destroy_input_handle_,lookup_denials_};}
void Binding::query_snapshot()noexcept{query_witness={1,unsigned(query_reached),unsigned(query_called_private_),query_result_private_,148,query_pointer_private_,query_frame_private_,query_ret,caller_error,query_api_error_,query_restored_error_,output_count_private_,unsigned(query_preflight_private_),unsigned(query_complete_private_),unsigned(query_return_read_private_),unsigned(query_returned_private_),unsigned(selector_returned_private_),unsigned(environment_private_),query_called_private_?query_word(4):0,query_called_private_?query_word(16):0};}
unsigned Binding::query_word(unsigned offset)const{unsigned v{};std::memcpy(&v,query_output_private_.data()+offset,4);return v;}
void Binding::guard(){admit_current();if(authority!=this||owner!=this||!active||failed||!started_||control!=admitted_control_||thread_!=std::this_thread::get_id()||depth<1||depth>4||frame!=admitted_frame_||parent_frame!=admitted_parent_frame_||mg::owner||pp::owner||m4_crt_heap_return::has_authority()||m4_crt_heap_version::has_authority()||m4_crt_heap_mode::has_authority()||m4_crt_heap_create::has_authority()||m4_crt_heap_init::has_authority()||ld::has_authority()||cm::producer_owner||nt::owner||ci::owner||mn::owner||admitted_parent_->used||admitted_parent_->active)deny("Exact active serial heap creation authority/frame required",frame);
 if(selector_unwound!=selector_unwound_private_||mode_store_before!=mode_store_before_private_||mode_published!=mode_published_private_||mode_value!=mode_value_private_||initializer_return_before!=initializer_return_before_private_||initializer_returned!=initializer_returned_private_)deny("Private genuine initializer progress mirrors required",mode_ret);
 if(state.addr.ds_base.dword||state.addr.ss_base.dword||(probe_reached&&probe_frame!=admitted_probe_frame_))deny("Flat carried segments and immutable genuine probe frame required",probe_frame);
 if(!std::equal(entry_fx_.begin(),entry_fx_.end(),runtime.fx().begin()))deny("Heap bridge changed carried Runtime FX",entry);cm::outer_owner_guard(*admitted_parent_);
 if(query_bound_){const auto old_query=query_witness;query_snapshot();if(old_query!=query_witness||query_input!=query_input_private_||query_output!=query_output_private_||query_frame!=query_frame_private_||query_pointer!=query_pointer_private_||query_result!=query_result_private_||output_count!=output_count_private_||query_called!=query_called_private_||query_preflight!=query_preflight_private_||query_output_complete!=query_complete_private_||query_returned!=query_returned_private_||selector_returned!=selector_returned_private_||environment_reached!=environment_private_)deny("Immutable measured query witness and private output transport required",query_site);}
 if(batch_phase_)batch_guard();else if(allocation_phase_private_)allocator_guard();
 const auto old=registry;registry_snapshot();if(old!=registry||registered!=registered_||api_called!=create_called_||(registered_&&(!owned_handle_||guest_result_!=token||witness[6]!=acquired_handle_||witness[7]!=token||witness[11]!=acquired_handle_)))deny("Immutable private full HANDLE registry and token lifecycle required",global);
}
void Binding::source_identity(){admit_current();if(batch_phase_){batch_source_identity();return;}if(access_count>accesses.size()||api_access_count>api_accesses.size()||event_count>events.size()||undefined_count>undefined_sites.size())deny("Bounded heap mode source/lifecycle ledger counts required",entry);admitted_parent_->source_identity();for(unsigned i=0;i<2;++i){auto address=i?entry:fragment;std::vector<std::byte>b(source_[i].size());try{runtime.memory().read({address},b);}catch(...){deny("Checked exact heap executable source read",address);}if(b!=source_[i])deny("Exact current compiled heap source identity required",address);}
 for(unsigned i=3;i<6;++i){const unsigned a=i==3?mode:i==4?probe:0x78005000;std::vector<std::byte>b(source_[i].size());try{runtime.memory().read({a},b);}catch(...){deny("Checked new selector/probe executable source read",a);}if(b!=source_[i])deny("Exact current compiled selector/probe source identity required",a);}
 for(unsigned i=6;i<11;++i){const unsigned a=i==6?branch:i==7?environment:i==8?cold:i==9?epilogue:0x7800c000;std::vector<std::byte>b(source_[i].size());try{runtime.memory().read({a},b);}catch(...){deny("Checked exact fresh version source page",a);}if(b!=source_[i])deny("Fresh compiled version continuation identity required",a);}
 if(query_bound_){std::array<std::byte,148>actual{};try{runtime.memory().read({query_pointer_private_},actual);}catch(...){deny("Checked complete version API transport buffer",query_pointer_private_);}if(actual!=query_expected_)deny("Only committed actual API output transport may change version buffer",query_pointer_private_);}
 unsigned query{};try{query=runtime.memory().load<unsigned>({query_iat});}catch(...){deny("Checked original OS-query IAT identity",query_iat);}if(query!=query_raw)deny("Exact unique original GetVersionExA raw import required",query_iat);
 unsigned loaded{};try{loaded=runtime.memory().load<unsigned>({iat});}catch(...){deny("Checked original HeapCreate IAT identity",iat);}if(loaded!=raw_import)deny("Exact unique original HeapCreate raw import required",iat);
 // Full declared lower-page carry is checked against the immutable initial input
 // and only already committed literal source stores. The single authored read-
 // permission control exposes its real TEST fault without a prior identity read.
 if(!(control==135&&depth==4&&access_count>=12&&access_count<=13&&!failed)){
  std::array<std::byte,4096>actual_lower{};try{runtime.memory().read({lower_stack},actual_lower);}catch(...){deny("Checked complete declared owned lower-stack page",lower_stack);}if(actual_lower!=lower_expected_)deny("Only committed source writes may change complete declared lower-stack input",lower_stack);
 }
 auto expected=source_[2];if(published)std::memcpy(expected.data(),&guest_result_,4);if(mode_published_private_)std::memcpy(expected.data()+4,&mode_value_private_,4);std::array<std::byte,4096>b{};try{runtime.memory().read({global},b);}catch(...){deny("Checked source-backed raw heap-global page",global);}if(!std::equal(b.begin(),b.end(),expected.begin()))deny("Only genuine source token and mode publications may change heap-global page",global);
}
void Binding::event(unsigned k,unsigned pc,unsigned a,unsigned v){if(event_count==events.size())deny("Heap creation event bound",a,pc);events[event_count++]={k,pc,a,v};}
void Binding::hook(unsigned point){stage=point;auto&m=runtime.memory();if(batch_phase_)batch_control(point);
 if(point==4&&control==122)throw std::runtime_error("Injected observer exception after private actual HeapCreate ownership");
 if(point==4&&control==123){rollback_=true;registry_snapshot();deny("Injected registration rollback after private actual HeapCreate ownership",global,api_site);}
 if(point==5&&control==124)witness[7]^=1;
 if(point==6&&control==125)throw std::runtime_error("Injected observer exception after checked stdcall return read before projection");
 if(point==7&&control==126)state.gpr.rax.dword^=1;
 if(point==2&&control==127&&access_count==9)throw std::runtime_error("Injected observer exception after genuine heap token publication");
 if(point==7&&control==128)m.protect({global},Permissions::read);
 if(point==2&&control==129&&access_count==9)m.protect({0x20001000},Permissions::read);
 if(point==8&&control==130){m.protect({0x78003000},Permissions::read|Permissions::write);m.store<unsigned>({mode_site},0);m.protect({0x78003000},Permissions::read|Permissions::execute);}
 if(point==10&&control==131)throw std::runtime_error("Injected terminal observer exception after actual HeapDestroy cleanup");
 if(point==8&&control==133){m.protect({0x78003000},Permissions::read|Permissions::write);m.store<unsigned>({mode},0);m.protect({0x78003000},Permissions::read|Permissions::execute);}
 if(point==8&&control==134){m.protect({0x78005000},Permissions::read|Permissions::write);m.store<unsigned>({probe},0);m.protect({0x78005000},Permissions::read|Permissions::execute);}
 if(point==11&&control==135)m.protect({lower_stack},Permissions::none);
 if(point==11&&control==136)m.protect({lower_stack},Permissions::read);
 if(point==2&&control==137&&access_count==13)m.store<unsigned>({admitted_probe_frame_},probe_ret^1);
 if(point==2&&control==138&&access_count==14)throw std::runtime_error("Injected observer exception after first genuine probe TEST read");
 if(point==2&&control==139&&access_count==15)throw std::runtime_error("Injected observer exception after second genuine probe TEST read");
 if(point==2&&control==140&&access_count==18)m.store<unsigned>({admitted_frame_-8-0x122c-4},probe_ret^1);
 if(point==12&&control==141){m.protect({0x7802e000},Permissions::read|Permissions::write);m.store<unsigned>({query_iat},query_raw^1);}
 if(point==12&&control==142)m.protect({lower_stack},Permissions::read);
 if(point==2&&control==143&&access_count==24)throw std::runtime_error("Injected observer exception after query CALL store before ESP/EIP publication");
 if(point==10&&control==144)throw std::runtime_error("Injected terminal observer exception after real private heap cleanup");
 if(point==13&&control==145)m.protect({0x20001000},Permissions::read);
 if(point==15&&control==146)throw std::runtime_error("Injected observer exception after actual GetVersionExA");
 if(point==15&&control==147)query_witness[3]^=1;
 if(point==15&&control==148)m.protect({0x20001000},Permissions::read);
 if(point==16&&control==149&&output_count==1)throw std::runtime_error("Injected observer exception after actual output transport commit one");
 if(point==16&&control==150&&output_count==37)throw std::runtime_error("Injected observer exception after all actual output transport commits");
 if(point==17&&control==151)m.store<unsigned>({query_frame_private_},query_ret^1);
 if(point==18&&control==152)throw std::runtime_error("Injected observer exception after genuine query return read before projection");
 if(point==19&&control==153)state.gpr.rax.dword^=1;
 if(point==19&&control==154){m.protect({0x78003000},Permissions::read|Permissions::write);m.store<unsigned>({branch},0);m.protect({0x78003000},Permissions::read|Permissions::execute);}
 if(point==2&&control==155&&access_count==30)m.store<unsigned>({admitted_frame_-4},mode_ret^1);
 if(point==10&&control==156)throw std::runtime_error("Injected terminal observer exception after actual heap cleanup");
 if(point==21&&control==157)m.protect({global},Permissions::read);
 if(point==21&&control==158)mode_published=true;
 if(point==22&&control==159)m.store<unsigned>({global+4},0);
 if(point==22&&control==160)throw std::runtime_error("Injected observer exception after genuine mode publication");
 if(point==22&&control==161)m.protect({0x20001000},Permissions::read);
 if(point==2&&control==162&&access_count==33)throw std::runtime_error("Injected observer exception after PUSH commit before ESP publication");
 if(point==2&&control==163&&access_count==33)m.store<unsigned>({admitted_frame_-4},2);
 if(point==2&&control==164&&access_count==34)throw std::runtime_error("Injected observer exception after POP read with ESP already advanced");
 if(point==23&&control==165)m.store<unsigned>({admitted_frame_},ret^1);
 if(point==2&&control==166&&access_count==35)throw std::runtime_error("Injected observer exception after genuine initializer return read before EIP/ESP publication");
 if(point==24&&control==167)state.gpr.rax.dword^=1;
 if(point==10&&control==168)throw std::runtime_error("Injected terminal observer exception after real heap cleanup");

 if(point==27&&control==169)throw std::runtime_error("Injected observer fault after provisional full HeapAlloc ownership");
 if(point==27&&control==170)allocation_registry[4]^=1;
 if(point==32&&control==171)m.protect({allocation_address},Permissions::read);
 if(point==34&&control==172)m.store<unsigned>({allocator_frame_-60},allocation_address+4);
 if(point==25&&control==173)m.protect(runtime.fs_base(),Permissions::read);
 if(point==2&&control==174&&state.gpr.rip.dword==0x780012f9)throw std::runtime_error("Injected fault after genuine FS chain registration store");
 if(point==30&&control==175)m.store<unsigned>(runtime.fs_base(),fs_expected_^1);
 if(point==35&&control==176)throw std::runtime_error("Injected fault after actual successful HeapFree");
 if(point==31&&control==177)throw std::runtime_error("Injected fault after genuine malloc export RET with live pointer");
 if(point==36&&control==178&&allocation_phase_private_==4)free_api();
 if(point==34&&control==179)owner=nullptr;
 if(point==10&&control==180)throw std::runtime_error("Injected terminal fault after allocation and heap cleanup");
 if(extra)extra(*this,point);
}
void Binding::stable_hook(unsigned point,bool terminal,bool cleaning){const auto old_state=state;const auto old_cpu=runtime.cpu();std::array<std::byte,512>fx{};std::copy(runtime.fx().begin(),runtime.fx().end(),fx.begin());
 auto progress=[&](){return std::array<unsigned,27>{probe_frame,unsigned(probe_reached),unsigned(probe_returned),unsigned(query_reached),frame,parent_frame,access_count,api_access_count,event_count,undefined_count,depth,fault_pc,fault_address,unsigned(used),unsigned(active),unsigned(failed),unsigned(api_reached),unsigned(api_called),unsigned(registered),unsigned(api_returned),unsigned(published),unsigned(mode_reached),unsigned(zero_reached),unsigned(cleanup_succeeded),caller_error,restored_error,unsigned(admitted_parent_->failed)};};
 const auto old_initializer=std::array<unsigned,6>{unsigned(selector_unwound),unsigned(mode_store_before),unsigned(mode_published),mode_value,unsigned(initializer_return_before),unsigned(initializer_returned)};const auto old_progress=progress();const auto old_scheduler=scheduler;const auto old_undefined=undefined_sites;const auto old_accesses=accesses;const auto old_api_accesses=api_accesses;const auto old_events=events;const auto old_witness=witness;const auto old_registry=registry;const auto old_reason=reason;const auto old_handle=owned_handle_;const auto old_result=guest_result_;const auto old_query_witness=query_witness;const auto old_query_input=query_input;const auto old_query_output=query_output;const auto old_output_accesses=output_accesses;const auto old_query_before=query_before;const auto old_query_after=query_after;const auto old_query_public=std::array<unsigned,10>{query_frame,query_pointer,query_result,output_count,unsigned(query_called),unsigned(query_preflight),unsigned(query_output_complete),unsigned(query_returned),unsigned(selector_returned),unsigned(environment_reached)};const auto old_alloc_export_before=alloc_export_before,old_alloc_export_after=alloc_export_after,old_free_export_before=free_export_before,old_free_export_after=free_export_after;const auto old_alloc_registry=allocation_registry;const auto old_alloc_witness=allocation_witness;const auto old_external_accesses=external_accesses;const auto old_external_projections=external_projections;
 const auto old_alloc_initial=allocation_initial;const auto old_alloc_pattern=allocation_pattern;const auto old_alloc_before=alloc_before;const auto old_alloc_after=alloc_after;const auto old_free_before=free_before;const auto old_free_after=free_after;
 const auto old_alloc_public=std::array<unsigned,12>{requested_size,allocation_phase,allocation_guest,allocation_extent,allocation_output_count,external_count,unsigned(caller_cleaned),unsigned(malloc_returned),unsigned(client_verified),unsigned(free_returned),unsigned(null_free_returned),unsigned(batch_complete)};
 const auto old_create_before=create_before;const auto old_create_after=create_after;const auto old_destroy_before=destroy_before;const auto old_destroy_after=destroy_after;hook(point);admit_current();
 if(authority!=(terminal?nullptr:this)||owner!=(terminal?nullptr:this)||control!=admitted_control_||stage!=point||old_progress!=progress()||old_scheduler!=scheduler||old_undefined!=undefined_sites||old_reason!=reason||old_handle!=owned_handle_||old_result!=guest_result_||std::memcmp(&old_state,&state,sizeof(State))||std::memcmp(&old_cpu,&runtime.cpu(),sizeof(old_cpu))||!std::equal(fx.begin(),fx.end(),runtime.fx().begin())||std::memcmp(old_accesses.data(),accesses.data(),sizeof(accesses))||std::memcmp(old_api_accesses.data(),api_accesses.data(),sizeof(api_accesses))||std::memcmp(old_events.data(),events.data(),sizeof(events))||old_witness!=witness||old_registry!=registry)deny("Heap creation observer changed State/FX or ownership/lifecycle ledgers",entry);
 if(old_initializer!=std::array<unsigned,6>{unsigned(selector_unwound),unsigned(mode_store_before),unsigned(mode_published),mode_value,unsigned(initializer_return_before),unsigned(initializer_returned)})deny("Observer changed genuine initializer progress",mode_ret);
 if(old_query_witness!=query_witness||old_query_input!=query_input||old_query_output!=query_output||std::memcmp(old_output_accesses.data(),output_accesses.data(),sizeof(output_accesses))||old_query_before!=query_before||old_query_after!=query_after||old_query_public!=std::array<unsigned,10>{query_frame,query_pointer,query_result,output_count,unsigned(query_called),unsigned(query_preflight),unsigned(query_output_complete),unsigned(query_returned),unsigned(selector_returned),unsigned(environment_reached)})deny("Query observer changed actual witness, API identity or transport ledger",query_site);
 if(old_create_before!=create_before||old_create_after!=create_after||old_destroy_before!=destroy_before||old_destroy_after!=destroy_after)deny("Heap API identity witness changed by observer",iat);

 if(old_alloc_export_before!=alloc_export_before||old_alloc_export_after!=alloc_export_after||old_free_export_before!=free_export_before||old_free_export_after!=free_export_after)deny("Observer changed actual native named export/forwarder proof",alloc_iat);
 if(old_alloc_registry!=allocation_registry||old_alloc_witness!=allocation_witness||old_alloc_initial!=allocation_initial||old_alloc_pattern!=allocation_pattern||
  std::memcmp(old_external_accesses.data(),external_accesses.data(),sizeof(external_accesses))||old_external_projections!=external_projections||
  old_alloc_before!=alloc_before||old_alloc_after!=alloc_after||old_free_before!=free_before||old_free_after!=free_after||
  old_alloc_public!=std::array<unsigned,12>{requested_size,allocation_phase,allocation_guest,allocation_extent,allocation_output_count,external_count,unsigned(caller_cleaned),unsigned(malloc_returned),unsigned(client_verified),unsigned(free_returned),unsigned(null_free_returned),unsigned(batch_complete)})
  deny("Allocation observer changed actual API identity, private ownership mirrors, external frame ledger or progress",allocation_address);
 if(!terminal&&!cleaning){guard();source_identity();}
}
void Binding::record(unsigned a,unsigned v,unsigned write){if(access_count==accesses.size())deny("Heap creation source access bound",a);accesses[access_count++]={state.gpr.rip.dword,a,v,4,write};if(published&&access_count==9)checkpoint(runtime,"heap-create-published");stable_hook(2);}
unsigned Binding::lower_word(unsigned a)const{if(a<lower_stack||std::uint64_t(a)+4>std::uint64_t(lower_stack)+4096)throw std::invalid_argument("Declared owned lower-stack input bounds");unsigned v{};std::memcpy(&v,lower_initial_.data()+a-lower_stack,4);return v;}
unsigned Binding::read32(unsigned a){if(batch_phase_)return static_cast<unsigned>(read(a,4));guard();source_identity();if(allocation_phase_private_>=2)return allocator_read32(a);unsigned pc{},address{},expected{};switch(access_count){
 case 3:pc=0x780039c3;address=admitted_frame_+4;expected=1;break;
 case 6:pc=api_site;address=iat;expected=raw_import;break;
 case 13:pc=0x780058db;address=admitted_frame_-8-0x1000;expected=lower_word(address);break;
 case 14:pc=0x780058c5;address=admitted_frame_-8-0x122c;expected=lower_word(address);break;
 case 15:pc=0x780058c9;address=admitted_probe_frame_-4;expected=probe_ecx_;break;
 case 16:pc=0x780058cb;address=admitted_probe_frame_;expected=probe_ret;break;
 case 18:pc=0x780058cf;address=admitted_frame_-8-0x122c-4;expected=probe_ret;break;
 case 22:pc=query_site;address=query_iat;expected=query_raw;break;
 default:if(!query_returned_private_)deny("Version source read before actual checked API return",a);
  pc=state.gpr.rip.dword;if(pc==0x78003a35&&access_count==24&&query_result_private_){address=query_pointer_private_+16;expected=query_word(16);}
  else if(pc==0x78003a3e&&access_count==25&&query_result_private_&&query_word(16)==2){address=query_pointer_private_+4;expected=query_word(4);}
  else if(pc==0x7800ccc7&&access_count==27){address=admitted_frame_-8-0x122c-8;expected=1;}
  else if(pc==0x78003a7d&&access_count==28){address=admitted_frame_-8-0x122c-4;expected=mode_ebx_;}
  else if(pc==0x78003a7e&&access_count==29){address=admitted_frame_-8;expected=mode_ebp_;}
  else if(pc==0x78003a7f&&access_count==30){address=admitted_frame_-4;expected=mode_ret;}
  else if(pc==0x78003a0a&&access_count==33&&depth==2&&selector_unwound_private_&&mode_published_private_){address=admitted_frame_-4;expected=1;if(state.gpr.rsp.dword!=admitted_frame_)deny("Generated POP publishes ESP before checked read",a);}
  else if(pc==0x78003a0b&&access_count==34&&depth==2&&selector_unwound_private_&&mode_published_private_){address=admitted_frame_;expected=ret;if(a!=address||state.gpr.rsp.dword!=admitted_frame_||state.gpr.rax.dword!=1)deny("Genuine initializer RET input frame required",a);initializer_return_before_private_=initializer_return_before=true;checkpoint(runtime,"heap-return-initializer-return-before");stable_hook(23);guard();source_identity();}
  else if(pc==0x78001845&&access_count==35&&allocation_phase_private_==1&&depth==1){address=admitted_frame_+4;expected=1;if(state.gpr.rsp.dword!=admitted_parent_frame_)deny("Genuine caller POP advances ESP before its read",a);}
  else if(pc==env_site){address=env_iat;expected=env_raw;}
  else deny("Version source read outside admitted literal continuation",a);
  break;
 }if(state.gpr.rip.dword!=pc||a!=address)deny("Exact generated heap mode/probe read operand required",a);unsigned value{};try{value=runtime.memory().load<unsigned>({a});}catch(...){if(control==135&&access_count==13)runtime.memory().protect({lower_stack},Permissions::read|Permissions::write);deny("Checked heap mode/probe source DWORD read fault",a);}if(value!=expected)deny("Exact source-owned or declared initial lower-stack read value required",a);record(a,value,0);return value;}
void Binding::write32(unsigned a,unsigned v){if(batch_phase_){write(a,v,4);return;}guard();source_identity();if(allocation_phase_private_>=2){allocator_write32(a,v);return;}unsigned pc{},address{},expected{};switch(access_count){
 case 0:pc=fragment;address=admitted_parent_frame_-4;expected=1;break;case 1:pc=site;address=admitted_frame_;expected=ret;break;
 case 2:pc=0x780039c1;address=admitted_frame_-4;break;case 4:pc=0x780039c7;address=admitted_frame_-8;expected=4096;break;case 5:pc=0x780039cf;address=admitted_frame_-12;break;case 7:pc=api_site;address=admitted_frame_-16;expected=api_ret;break;
 case 8:pc=0x780039d8;address=global;expected=guest_result_;if(!api_returned||undefined_count!=2)deny("Source heap publication requires exact real API return and TEST",a);break;
 case 9:pc=mode_site;address=admitted_frame_-4;expected=mode_ret;if(!published||!registered_||!owned_handle_||guest_result_!=token)deny("Real mode CALL requires privately owned source-published token",a);break;
 case 10:pc=mode;address=admitted_frame_-8;expected=mode_ebp_;break;
 case 11:pc=probe_site;address=admitted_probe_frame_;expected=probe_ret;break;
 case 12:pc=probe;address=admitted_probe_frame_-4;expected=probe_ecx_;break;
 case 17:pc=0x780058ce;address=admitted_frame_-8-0x122c-4;expected=probe_ret;break;
 case 19:pc=0x78003a1f;address=admitted_frame_-8-0x122c-4;expected=mode_ebx_;break;
 case 20:pc=0x78003a20;address=admitted_frame_-8-0x122c-8;expected=admitted_frame_-8-0x98;break;
 case 21:pc=0x78003a21;address=admitted_frame_-8-0x98;expected=0x94;break;
 case 23:pc=query_site;address=admitted_frame_-8-0x122c-12;expected=query_ret;break;
 default:if(!query_returned_private_)deny("Version source store before checked actual API return",a);pc=state.gpr.rip.dword;
  if(pc==cold&&access_count==26&&query_result_private_&&query_word(16)==2&&query_word(4)>=5){address=admitted_frame_-8-0x122c-8;expected=1;}
  else if(pc==0x780039eb&&access_count==31&&depth==2&&selector_unwound_private_&&!mode_published_private_){address=global+4;expected=1;if(a!=address||v!=expected||state.gpr.rax.dword!=1||state.gpr.rsp.dword!=admitted_frame_)deny("Actual selector result required for genuine mode publication",a);mode_store_before_private_=mode_store_before=true;checkpoint(runtime,"heap-return-mode-store-before");stable_hook(21);guard();source_identity();}
  else if(pc==0x78003a08&&access_count==32&&depth==2&&mode_published_private_){address=admitted_frame_-4;expected=1;if(state.gpr.rax.dword!=1||state.gpr.rsp.dword!=admitted_frame_)deny("Genuine mode1 PUSH input required",a);}
  else if(pc==0x78003a51){address=admitted_frame_-8-0x122c-8;expected=0x1090;}
  else if(pc==0x78003a56){address=admitted_frame_-8-0x122c-12;expected=admitted_frame_-8-0x122c;}
  else if(pc==0x78003a57){address=admitted_frame_-8-0x122c-16;expected=env_name;}
  else if(pc==env_site){address=admitted_frame_-8-0x122c-20;expected=env_ret;}
  else deny("Version store outside admitted source continuation",a);break;
 }if(state.gpr.rip.dword!=pc||a!=address||v!=expected)deny("Exact generated heap PUSH/CALL/global store required",a);try{runtime.memory().store<unsigned>({a},v);}catch(...){deny("Checked generated heap source store fault",a);}if(a>=lower_stack&&std::uint64_t(a)+4<=std::uint64_t(lower_stack)+4096)std::memcpy(lower_expected_.data()+a-lower_stack,&v,4);if(a>=0x20001000&&std::uint64_t(a)+4<=0x20002000)std::memcpy(upper_expected_.data()+a-0x20001000,&v,4);if(access_count==8)published=true;if(access_count==31&&pc==0x780039eb){mode_published_private_=mode_published=true;mode_value_private_=mode_value=v;event(12,pc,a,v);}record(a,v,1);if(access_count==32&&pc==0x780039eb){checkpoint(runtime,"heap-return-mode-store-after");stable_hook(22);guard();source_identity();}
}
unsigned char Binding::undefined(){if(batch_phase_)return batch_undefined();guard();source_identity();if(allocation_phase_private_>=2)return allocator_undefined();const auto pc=state.gpr.rip.dword;
 if(allocation_phase_private_==1&&pc==caller_cleanup&&access_count==35&&undefined_count==5){undefined_sites[undefined_count++]=pc;return 0;}
 const bool old=depth==2&&((pc==entry&&access_count==2&&undefined_count==0)||(pc==api_ret&&access_count==8&&undefined_count==1&&api_returned));
 const bool added=depth==4&&probe_reached&&!probe_returned&&((pc==0x780058db&&access_count==14&&undefined_count==2)||(pc==0x780058c5&&access_count==15&&undefined_count==3));
 const bool version=depth==3&&query_returned_private_&&pc==branch&&access_count==24&&api_access_count==2&&undefined_count==4;
 if(!(old||added||version))deny("Only five exact XOR/TEST generated AF representatives are admitted",pc);undefined_sites[undefined_count++]=pc;return 0;}
bool Binding::owns_token(unsigned value){admit_current();if(!owned_handle_||!registered_||value!=token||guest_result_!=token||thread_!=std::this_thread::get_id()){++lookup_denials_;registry_snapshot();deny("Unknown/stale/closed opaque heap token rejected",value);}return true;}
void Binding::test_cleanup(){admit_current();if(!started_)deny("Unused heap registry cannot request cleanup",global);if(!active&&!owned_handle_&&cleanup_succeeded&&!authority&&!owner)return;if(authority!=this||owner!=this||thread_!=std::this_thread::get_id())deny("Only exact current heap registry may request cleanup",global);cleanup();}
void Binding::api(){checkpoint(runtime,"heap-create-api-before");stable_hook(3);guard();source_identity();
 create_before=measured_api("HeapCreate",reinterpret_cast<std::uintptr_t>(&::HeapCreate));destroy_before=measured_api("HeapDestroy",reinterpret_cast<std::uintptr_t>(&::HeapDestroy));
 witness={1,unsigned(control==121),0,0,4096,0,0,0,caller_error,0,caller_error,0,admitted_frame_-16,api_ret,admitted_frame_,api_ret};
 if(control!=121){InvocationHostBoundary fp;fn::LastErrorBoundary errors;SetLastError(caller_error);witness[8]=GetLastError();
  // The private fixed slot takes provisional ownership in this expression.
  // Nothing that can throw or allocate runs between API return and ownership.
  owned_handle_=::HeapCreate(0,4096,0);create_called_=true;acquired_handle_=reinterpret_cast<std::uintptr_t>(owned_handle_);const auto observed_error=GetLastError();SetLastError(caller_error);api_called=true;witness[2]=1;witness[6]=acquired_handle_;witness[9]=observed_error;witness[10]=GetLastError();registry_snapshot();
 }
 create_after=measured_api("HeapCreate",reinterpret_cast<std::uintptr_t>(&::HeapCreate));if(create_before!=create_after)deny("Actual HeapCreate target identity changed across call",iat,api_site);
 stable_hook(4);guard();source_identity();if(owned_handle_){registered_=true;registered=true;guest_result_=token;witness[7]=token;witness[11]=acquired_handle_;registry_snapshot();}
 stable_hook(5);guard();source_identity();api_return();
}
void Binding::api_return(){checkpoint(runtime,"heap-create-api-return-before");guard();source_identity();if(api_access_count||access_count!=8||state.gpr.rip.dword!=raw_import||state.gpr.rsp.dword!=admitted_frame_-16)deny("Exact declared heap API stdcall frame required",admitted_frame_-16,api_site);
 unsigned value{};try{value=runtime.memory().load<unsigned>({admitted_frame_-16});}catch(...){deny("Checked heap API stdcall return-word read fault",admitted_frame_-16,api_site);}if(value!=api_ret)deny("Genuine heap API source return word required",admitted_frame_-16,api_site);api_accesses[api_access_count++]={api_site,admitted_frame_-16,value,4,0};stable_hook(6);guard();source_identity();
 // Finite guest API model: preserve every other carried State byte, FX and CPU.
 state.gpr.rax.dword=guest_result_;state.gpr.rsp.dword=admitted_frame_;state.gpr.rip.dword=api_ret;api_returned=true;event(4,api_site,admitted_frame_-16,api_ret);checkpoint(runtime,"heap-create-api-returned");stable_hook(7);guard();source_identity();
}
void Binding::query(){
 guard();source_identity();if(query_called_private_||query_preflight_private_||query_word(0)||query_input_private_[0]!=std::byte{0x94})deny("One genuine size-qualified query required",query_pointer_private_,query_site);
 // Only this private copied memory is written by permission preflight.
 // It invokes the frozen exact extent/permissions implementation without any
 // resident guest write, source store, State reset or output declaration.
 try{auto private_permission_snapshot=runtime.memory();private_permission_snapshot.write({query_pointer_private_},query_input_private_);}catch(...){deny("Full actual query destination permission preflight failed",query_pointer_private_,query_site);}
 query_preflight=query_preflight_private_=true;query_before=measured_api("GetVersionExA",reinterpret_cast<std::uintptr_t>(&::GetVersionExA));query_snapshot();checkpoint(runtime,"heap-version-query-native-before");stable_hook(14);guard();source_identity();
 try{auto final_permission_snapshot=runtime.memory();final_permission_snapshot.write({query_pointer_private_},query_input_private_);}catch(...){deny("Immediate native query destination permission preflight failed",query_pointer_private_,query_site);}
 OSVERSIONINFOA scratch;static_assert(sizeof(scratch)==148);std::memcpy(&scratch,query_input_private_.data(),148);
 {InvocationHostBoundary fp;fn::LastErrorBoundary errors;SetLastError(caller_error);const BOOL actual=::GetVersionExA(&scratch);query_called_private_=query_called=true;std::memcpy(&query_result_private_,&actual,4);query_result=query_result_private_;query_api_error_=GetLastError();SetLastError(caller_error);query_restored_error_=GetLastError();}
 std::memcpy(query_output_private_.data(),&scratch,148);query_output=query_output_private_;query_after=measured_api("GetVersionExA",reinterpret_cast<std::uintptr_t>(&::GetVersionExA));if(query_before!=query_after)deny("Actual GetVersionExA identity changed across native query",query_iat,query_site);query_snapshot();checkpoint(runtime,"heap-version-query-native-after");stable_hook(15);guard();source_identity();
 for(unsigned n=0;n<37;++n){const unsigned a=query_pointer_private_+4*n,v=query_word(4*n);guard();source_identity();try{runtime.memory().store<unsigned>({a},v);}catch(...){deny("Checked actual API output transport store fault",a,query_site);}std::memcpy(query_expected_.data()+4*n,&v,4);std::memcpy(upper_expected_.data()+a-0x20001000,&v,4);output_accesses[output_count_private_++]={query_site,a,v,4,1};output_count=output_count_private_;query_snapshot();stable_hook(16);}
 query_complete_private_=query_output_complete=true;query_snapshot();checkpoint(runtime,"heap-version-query-output-after");stable_hook(17);guard();source_identity();query_return();
}
void Binding::query_return(){checkpoint(runtime,"heap-version-query-return-before");guard();source_identity();if(!query_complete_private_||output_count_private_!=37||api_access_count!=1||access_count!=24||state.gpr.rip.dword!=query_raw||state.gpr.rsp.dword!=query_frame_private_)deny("Exact real query stdcall return frame required",query_frame_private_,query_site);
 unsigned value{};try{value=runtime.memory().load<unsigned>({query_frame_private_});}catch(...){deny("Checked real query return-word read fault",query_frame_private_,query_site);}if(value!=query_ret)deny("Genuine query CALL return word required",query_frame_private_,query_site);api_accesses[api_access_count++]={query_site,query_frame_private_,value,4,0};query_return_read_private_=true;query_snapshot();stable_hook(18);guard();source_identity();
 state.gpr.rax.dword=query_result_private_;state.gpr.rsp.dword=query_frame_private_+8;state.gpr.rip.dword=query_ret;query_returned_private_=query_returned=true;query_snapshot();event(10,query_site,query_frame_private_,query_ret);checkpoint(runtime,"heap-version-query-returned");stable_hook(19);guard();source_identity();
}
void*Binding::called(State*s,unsigned target,void*p){if(batch_phase_)return batch_called(s,target,p);guard();source_identity();if(allocation_phase_private_>=2)return allocator_called(s,target,p);if(s!=&state||p!=this||state.gpr.rip.dword!=target||!access_count)deny("Exact real heap CALL State/token required",target);const auto&w=accesses[access_count-1];
 if(target==entry){if(depth!=1||event_count!=1||access_count!=2||w.pc!=site||w.address!=admitted_frame_||w.value!=ret||!w.write||state.gpr.rsp.dword!=admitted_frame_||runtime.memory().load<unsigned>({admitted_frame_})!=ret||runtime.memory().load<unsigned>({admitted_frame_+4})!=1)deny("Actual original heap caller frame closure required",admitted_frame_,site);event(2,site,target,ret);depth=2;checkpoint(runtime,"heap-create-provider-before");auto result=m4_crt_heap_init::mw34_heap_init_provider_body(s,target,this);guard();source_identity();
 if(result!=this||!initializer_returned_private_||depth!=1||state.gpr.rip.dword!=ret||state.gpr.rsp.dword!=admitted_frame_+4)deny("Genuine initializer must unwind to fragment caller",ret);
 allocation_phase=allocation_phase_private_=1;allocator_snapshot();checkpoint(runtime,"allocation-caller-before");
 return mw34_allocation_caller_body(s,ret,this);}
 if(target==raw_import){const auto&r=accesses[6];if(depth!=2||event_count!=2||access_count!=8||undefined_count!=1||api_reached||r.pc!=api_site||r.address!=iat||r.value!=raw_import||r.write||w.pc!=api_site||w.address!=admitted_frame_-16||w.value!=api_ret||!w.write||state.gpr.rsp.dword!=admitted_frame_-16||state.gpr.rax.dword||runtime.memory().load<unsigned>({admitted_frame_-16})!=api_ret||runtime.memory().load<unsigned>({admitted_frame_-12})||runtime.memory().load<unsigned>({admitted_frame_-8})!=4096||runtime.memory().load<unsigned>({admitted_frame_-4}))deny("Actual HeapCreate IAT/arguments/source CALL closure required",iat,api_site);api_reached=true;event(3,api_site,iat,raw_import);api();return this;}
 if(target==probe){if(depth!=3||event_count!=6||access_count!=12||undefined_count!=2||probe_reached||state.gpr.rsp.dword!=admitted_probe_frame_||state.gpr.rbp.dword!=admitted_frame_-8||state.gpr.rax.dword!=0x122c||w.pc!=probe_site||w.address!=admitted_probe_frame_||w.value!=probe_ret||!w.write||runtime.memory().load<unsigned>({admitted_probe_frame_})!=probe_ret)deny("Genuine source stack-probe CALL and custom allocation input required",target,probe_site);
  probe_reached=true;event(7,probe_site,probe,probe_ret);depth=4;checkpoint(runtime,"heap-mode-probe-before");stable_hook(11);guard();source_identity();auto result=m4_crt_heap_mode::mw34_heap_mode_probe_body(s,target,this);guard();source_identity();if(result!=this||!probe_returned||depth!=3||state.gpr.rip.dword!=probe_ret||state.gpr.rsp.dword!=admitted_frame_-8-0x122c||state.gpr.rax.dword!=probe_ret||state.gpr.rcx.dword!=probe_ecx_)deny("Real compiled probe must return after its genuine relocated RET",probe_ret,probe_site);return this;}
 if(target==query_raw){if(depth!=3||event_count!=8||access_count!=24||api_access_count!=1||undefined_count!=4||!probe_returned||query_reached||!registered_||!owned_handle_||state.gpr.rsp.dword!=admitted_frame_-8-0x122c-12||state.gpr.rbp.dword!=admitted_frame_-8||state.gpr.rax.dword!=admitted_frame_-8-0x98||w.pc!=query_site||w.address!=state.gpr.rsp.dword||w.value!=query_ret||!w.write||accesses[22].pc!=query_site||accesses[22].address!=query_iat||accesses[22].value!=query_raw||accesses[22].write||runtime.memory().load<unsigned>({state.gpr.rsp.dword})!=query_ret||runtime.memory().load<unsigned>({state.gpr.rsp.dword+4})!=admitted_frame_-8-0x98||runtime.memory().load<unsigned>({admitted_frame_-8-0x98})!=0x94)deny("Exact genuine first OS-query CALL/header/argument closure required",query_iat,query_site);
  (void)owns_token(token);query_reached=true;event(9,query_site,query_iat,query_raw);query_frame=query_frame_private_=state.gpr.rsp.dword;query_pointer=query_pointer_private_=admitted_frame_-8-0x98;
  try{runtime.memory().read({query_pointer_private_},query_input_private_);}catch(...){deny("Checked actual full original query input",query_pointer_private_,query_site);}query_input=query_input_private_;query_expected_=query_input_private_;query_bound_=true;query_snapshot();checkpoint(runtime,"heap-mode-query-before");stable_hook(13);guard();source_identity();query();return this;}
 if(target==env_raw){if(depth!=3||!query_returned_private_||undefined_count!=5||w.pc!=env_site||w.address!=admitted_frame_-8-0x122c-20||w.value!=env_ret||!w.write||state.gpr.rsp.dword!=w.address||event_count!=10||!owned_handle_||!registered_)deny("Genuine unresolved environment source CALL required",env_iat,env_site);environment_private_=environment_reached=true;query_snapshot();event(11,env_site,env_iat,env_raw);checkpoint(runtime,"heap-version-environment-before");stable_hook(20);guard();source_identity();first("Required genuine CRT GetEnvironmentVariableA remains unresolved",env_iat,env_site);admitted_parent_->first(reason,fault_address,fault_pc);throw m4_runtime::Fault(m4_runtime::FaultReason::unresolved_import,{env_site},{env_iat},reason);}
 if(target!=mode||depth!=2||event_count!=4||access_count!=10||api_access_count!=1||undefined_count!=2||!api_returned||!published||!registered_||!owned_handle_||state.gpr.rsp.dword!=admitted_frame_-4||state.gpr.rax.dword!=token||w.pc!=mode_site||w.address!=admitted_frame_-4||w.value!=mode_ret||!w.write||runtime.memory().load<unsigned>({admitted_frame_-4})!=mode_ret||runtime.memory().load<unsigned>({global})!=token)deny("Exact genuine source-published mode-selector CALL required",target,mode_site);
 (void)owns_token(token);event(5,0x780039d8,global,token);mode_reached=true;event(6,mode_site,mode,mode_ret);checkpoint(runtime,"heap-create-mode-before");stable_hook(8);guard();source_identity();mode_ebp_=state.gpr.rbp.dword;mode_ebx_=state.gpr.rbx.dword;probe_ecx_=state.gpr.rcx.dword;probe_frame=admitted_frame_-12;admitted_probe_frame_=probe_frame;depth=3;auto result=m4_crt_heap_mode::mw34_heap_mode_selector_body(s,target,this);guard();source_identity();if(result!=this||!selector_unwound_private_||depth!=2||state.gpr.rip.dword!=mode_ret||state.gpr.rsp.dword!=admitted_frame_||state.gpr.rax.dword!=1||access_count!=31||event_count!=11)deny("Genuine selector must unwind into its original translated provider CALL",mode_ret,mode_site);return this;
}
void*Binding::returned(State*s,unsigned target,void*p){if(batch_phase_)return batch_returned(s,target,p);guard();source_identity();if(allocation_phase_private_>=2)return allocator_returned(s,target,p);
 if(target==ret){const auto&w=accesses[34];if(s!=&state||p!=this||state.gpr.rip.dword!=ret||depth!=2||!selector_unwound_private_||!mode_published_private_||mode_value_private_!=1||!initializer_return_before_private_||initializer_returned_private_||!owned_handle_||!registered_||access_count!=35||api_access_count!=2||event_count!=12||undefined_count!=5||state.gpr.rax.dword!=1||state.gpr.rsp.dword!=admitted_frame_+4||state.gpr.rbp.dword!=mode_ebp_||state.gpr.rbx.dword!=mode_ebx_||w.pc!=0x78003a0b||w.address!=admitted_frame_||w.value!=ret||w.write)deny("Genuine initializer RET must preserve original frame and private live heap",ret,0x78003a0b);
  initializer_returned_private_=initializer_returned=true;event(13,0x78003a0b,ret,w.address);checkpoint(runtime,"heap-return-initializer-return-after");stable_hook(24);guard();source_identity();depth=1;return this;}

 if(target==mode_ret){const auto&w=accesses[30];if(s!=&state||p!=this||state.gpr.rip.dword!=mode_ret||depth!=3||!query_returned_private_||!query_result_private_||query_word(16)!=2||query_word(4)<5||access_count!=31||api_access_count!=2||event_count!=10||undefined_count!=5||state.gpr.rax.dword!=1||state.gpr.rsp.dword!=admitted_frame_||state.gpr.rbp.dword!=mode_ebp_||state.gpr.rbx.dword!=mode_ebx_||w.pc!=0x78003a7f||w.address!=admitted_frame_-4||w.value!=mode_ret||w.write)deny("Genuine selector RET and original restored frame required",mode_ret,0x78003a7f);
  selector_returned_private_=selector_returned=true;query_snapshot();event(11,0x78003a7f,mode_ret,w.address);checkpoint(runtime,"heap-version-selector-return-after");stable_hook(20);guard();source_identity();selector_unwound_private_=selector_unwound=true;depth=2;return this;}
const auto&w=accesses[18];if(s!=&state||p!=this||target!=probe_ret||state.gpr.rip.dword!=probe_ret||depth!=4||event_count!=7||access_count!=19||undefined_count!=4||!probe_reached||probe_returned||state.gpr.rsp.dword!=admitted_frame_-8-0x122c||state.gpr.rax.dword!=probe_ret||state.gpr.rcx.dword!=probe_ecx_||w.pc!=0x780058cf||w.address!=admitted_frame_-8-0x122c-4||w.value!=probe_ret||w.write||runtime.memory().load<unsigned>({w.address})!=probe_ret)deny("Only genuine source probe relocated RET/frame is admitted",target,0x780058cf);probe_returned=true;depth=3;event(8,0x780058cf,probe_ret,w.address);checkpoint(runtime,"heap-mode-probe-after");stable_hook(12);guard();source_identity();return this;}
void*Binding::jumped(State*s,unsigned target,void*p){return missing(s,target,p);}
void*Binding::missing(State*s,unsigned target,void*p){if(batch_phase_)return batch_missing(s,target,p);guard();source_identity();
 if(allocation_phase_private_>=2)return allocator_missing(s,target,p);
 if(allocation_phase_private_==1&&s==&state&&p==this&&target==caller_stop&&state.gpr.rip.dword==caller_stop&&state.gpr.rsp.dword==admitted_parent_frame_&&state.gpr.rax.dword==1&&state.gpr.rcx.dword==1&&access_count==36&&undefined_count==6&&initializer_returned_private_&&mode_published_private_){caller_cleaned=caller_cleaned_private_=true;allocator_snapshot();checkpoint(runtime,"allocation-caller-after");stable_hook(25);guard();source_identity();throw CallerComplete{};}
 if(query_returned_private_){if(s!=&state||p!=this||state.gpr.rip.dword!=target||depth!=3||api_access_count!=2||!owned_handle_||!registered_)deny("Exact live query continuation State required",target);
  if(target==branch&&access_count==24&&undefined_count==4&&state.gpr.rsp.dword==admitted_frame_-8-0x122c-4&&state.gpr.rax.dword==query_result_private_)return mw34_heap_version_branch_body(s,target,this);
  if(target==cold&&access_count==26&&undefined_count==5&&query_result_private_&&query_word(16)==2&&query_word(4)>=5)return mw34_heap_version_mode1_body(s,target,this);
  if(target==epilogue&&access_count==28&&state.gpr.rax.dword==1&&query_result_private_&&query_word(16)==2&&query_word(4)>=5)return mw34_heap_version_epilogue_body(s,target,this);
  if(target==environment&&undefined_count==5&&((!query_result_private_&&access_count==24)||(query_result_private_&&query_word(16)!=2&&access_count==25)||(query_result_private_&&query_word(16)==2&&query_word(4)<5&&access_count==26)))return mw34_heap_version_environment_body(s,target,this);
  deny("Unadmitted postquery source block",target);
 }
if(s!=&state||p!=this||target!=zero||state.gpr.rip.dword!=zero||state.gpr.rsp.dword!=admitted_frame_||state.gpr.rax.dword||access_count!=9||api_access_count!=1||undefined_count!=2||!api_returned||!published||registered_||owned_handle_)deny("Only bounded genuine zero-result cold frontier is admitted",target);
 zero_reached=true;event(5,0x780039d8,global,0);event(7,0x780039dd,zero,0);checkpoint(runtime,"heap-create-zero-before");stable_hook(8);guard();source_identity();first("HeapCreate zero-result cold source body remains unadmitted",zero,0x780039dd);admitted_parent_->first(reason,fault_address,fault_pc);throw m4_runtime::Fault(m4_runtime::FaultReason::unresolved_translation,{0x780039dd},{zero},reason);
}
bool Binding::release_noexcept(bool skip)noexcept{if(std::this_thread::get_id()!=thread_||live_allocations()||live_critical_sections())return false;++cleanup_attempts_;if(owned_allocation_){registry_snapshot();return false;}if(!owned_handle_){registry_snapshot();return true;}if(skip){++cleanup_skips_;registry_snapshot();return false;}InvocationHostBoundary fp;const auto saved=GetLastError();const auto actual=owned_handle_;++destroy_calls_;destroy_input_handle_=reinterpret_cast<std::uintptr_t>(actual);const auto ok=::HeapDestroy(actual);const auto error=GetLastError();SetLastError(saved);destroy_error_=error;
 if(ok){++destroy_successes_;owned_handle_=nullptr;finalized_=true;}registry_snapshot();return ok!=FALSE;
}
void Binding::cleanup(){if(!cleanup_sections_noexcept()||!cleanup_allocations_noexcept())throw std::runtime_error("Live locale ownership retained after unsuccessful cleanup");std::exception_ptr observer;try{stable_hook(9,false,true);}catch(...){observer=std::current_exception();}
 if(owned_allocation_&&!release_allocation_noexcept())throw std::runtime_error("Actual HeapFree cleanup failed; allocation ownership retained");
 if(owned_handle_){if(control==132&&!cleanup_skip_used_){cleanup_skip_used_=true;(void)release_noexcept(true);}
  if(!release_noexcept()){first("Actual HeapDestroy failed; ownership retained",global,mode_site);if(!release_noexcept())throw std::runtime_error("Actual HeapDestroy retry failed; owned handle retained for final safeguard");}
  destroy_after=measured_api("HeapDestroy",reinterpret_cast<std::uintptr_t>(&::HeapDestroy));if(destroy_before!=destroy_after)throw std::runtime_error("Actual HeapDestroy API identity changed across cleanup");
 }
 cleanup_succeeded=owned_handle_==nullptr;finalized_=cleanup_succeeded;registry_snapshot();if(observer)std::rethrow_exception(observer);
}
[[noreturn]]void Binding::unsupported(unsigned a,const char*w){guard();deny(w,a);}
void Binding::start(mg::Context&c){fn::LastErrorBoundary errors;InvocationHostBoundary fp;if(authority&&authority!=this)authority->deny("Stale heap creation binding cannot enter current authority",entry);if(&c!=admitted_parent_)deny("Heap scheduler exact immutable parent required",entry);admit_current();cm::outer_owner_guard(c);
 if(authority||owner||used||active||failed||started_||depth||access_count||api_access_count||event_count||undefined_count||control!=admitted_control_||mg::owner||pp::owner||m4_crt_heap_return::has_authority()||m4_crt_heap_version::has_authority()||m4_crt_heap_mode::has_authority()||m4_crt_heap_create::has_authority()||m4_crt_heap_init::has_authority()||ld::has_authority()||cm::producer_owner||nt::owner||ci::owner||mn::owner||c.used||c.active||runtime.cpu().eip!=mg::slot||runtime.cpu().esp!=0x20001860||state.gpr.rsp.dword!=runtime.cpu().esp||owned_handle_||registered_)deny("Fresh bounded original fragment heap creation scheduler required",fragment);
 source_identity();{std::array<std::byte,4096>b{};runtime.memory().read({lower_stack},b);if(b!=lower_initial_)deny("Declared initial owned lower stack changed before source execution",lower_stack);}
 // Private guard admission is the authenticated original mainargs BEFORE seam.
 // Original CRT source has already registered FS0 and written its caller frames;
 // no guest memory or State bytes are changed by this guard snapshot.
 if(state.addr.fs_base.dword!=runtime.fs_base().value)deny("Exact carried FS base at authenticated mainargs admission",runtime.fs_base().value);
 fs_previous_=fs_expected_=runtime.memory().load<unsigned>(runtime.fs_base());
 runtime.memory().read({0x20001000},upper_initial_);upper_expected_=upper_initial_;
 parent_frame=runtime.cpu().esp;admitted_parent_frame_=parent_frame;frame=parent_frame-8;admitted_frame_=frame;caller_error=errors.saved;errors.restored=&restored_error;std::copy(runtime.fx().begin(),runtime.fx().end(),entry_fx_.begin());capture_binding=this;checkpoint(runtime,"heap-create-before");scheduler={1,state.gpr.rip.dword,state.gpr.rsp.dword,fragment,state.gpr.rsp.dword,0,runtime.cpu().eip,runtime.cpu().esp};state.gpr.rip.dword=fragment;used=true;started_=true;active=true;depth=1;authority=this;owner=this;
 struct Cleanup{Binding&b;~Cleanup()noexcept{if(b.active&&!b.failed)return;(void)b.cleanup_sections_noexcept();(void)b.cleanup_allocations_noexcept();if(b.owned_allocation_)(void)b.release_allocation_noexcept();if(b.owned_handle_)(void)b.release_noexcept();b.active=false;b.depth=0;owner=nullptr;authority=nullptr;}}safety{*this};event(1,fragment,parent_frame,0);
 try{checkpoint(runtime,"heap-create-projected");stable_hook(1);guard();source_identity();try{(void)m4_crt_heap_init::mw34_heap_init_fragment_body(&state,fragment,this);deny("Unexpected completion past declared heap mode boundary",fragment);}catch(const CallerComplete&){locale_batch();}
 if(!locale_complete_)deny("Complete genuine default locale required",0x78003dda);return;}
 catch(...){auto original=std::current_exception();if(!failed){try{std::rethrow_exception(original);}catch(const std::exception&e){host_fault_reason_private_=e.what();first(host_fault_reason_private_.c_str());}catch(...){first("Required heap creation observer or host fault");}}admitted_parent_->first(reason,fault_address,fault_pc);try{cleanup();}catch(...){first("Heap cleanup observer or host fault; private safeguard remains");if(owned_handle_)(void)release_noexcept();cleanup_succeeded=owned_handle_==nullptr;finalized_=cleanup_succeeded;registry_snapshot();}
  active=false;depth=0;owner=nullptr;authority=nullptr;checkpoint(runtime,"heap-create-after");stable_hook(10,true);std::rethrow_exception(original);
 }
}
#include "locale_batch_allocator.inc"
#include "locale_batch_operations.inc"
}
namespace {
