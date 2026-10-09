"""Fresh namespace derivation; never mutates the accepted heap-mode ancestor."""
import pathlib,json
ROOT=pathlib.Path(__file__).resolve().parents[2]
HERE=pathlib.Path(__file__).resolve().parent
OLD=ROOT/'tools/m4-crt-heap-mode'
REC=ROOT/'reports/m4-crt-heap-version-recovery/recovery-r1'
def replace(s,a,b):
 assert s.count(a)==1,(a[:100],s.count(a))
 return s.replace(a,b)
def write(name,s):(HERE/name).write_text(s)
def derive(name):return (OLD/name).read_text().replace('m4_crt_heap_mode','m4_crt_heap_version').replace('heap_mode','heap_version').replace('heap-mode','heap-version')

h=derive('heap_mode.hpp')
h=replace(h,'#include "heap_create.hpp"','#include "heap_create.hpp"\n#include "heap_mode.hpp"')
h=replace(h,'extern "C" void*mw34_heap_version_selector_body(State*,unsigned,void*);\nextern "C" void*mw34_heap_version_probe_body(State*,unsigned,void*);','inline constexpr unsigned branch=0x78003a31,environment=0x78003a4b,cold=0x7800ccc5,epilogue=0x78003a7d,env_site=0x78003a5c,env_iat=0x7802e09c,env_raw=0x345e6,env_ret=0x78003a62,env_name=0x7802e3b8;\nextern "C" void*mw34_heap_version_branch_body(State*,unsigned,void*);\nextern "C" void*mw34_heap_version_environment_body(State*,unsigned,void*);\nextern "C" void*mw34_heap_version_mode1_body(State*,unsigned,void*);\nextern "C" void*mw34_heap_version_epilogue_body(State*,unsigned,void*);')
h=replace(h,'std::array<unsigned,8>undefined_sites{},scheduler{};','std::array<unsigned,8>undefined_sites{},scheduler{};\n unsigned query_frame{},query_pointer{},query_result{},output_count{};\n bool query_called{},query_preflight{},query_output_complete{},query_returned{},selector_returned{},environment_reached{};\n std::array<std::uint64_t,20>query_witness{};std::array<std::byte,148>query_input{},query_output{};\n std::array<mg::Access,64>output_accesses{};\n m4_cmd_native::ApiIdentity query_before,query_after;')
h=replace(h,'[[noreturn]]void missing(State*,unsigned,void*);','void*missing(State*,unsigned,void*);void*jumped(State*,unsigned,void*);')
h=replace(h,'std::array<std::vector<std::byte>,6>source_;','std::array<std::vector<std::byte>,11>source_;')
h=replace(h,'unsigned lower_word(unsigned)const;','unsigned lower_word(unsigned)const;unsigned query_word(unsigned)const;\n std::array<std::byte,148>query_input_private_{},query_output_private_{},query_expected_{};\n unsigned query_frame_private_{},query_pointer_private_{},query_result_private_{},output_count_private_{},query_api_error_{},query_restored_error_{};\n bool query_bound_{},query_called_private_{},query_preflight_private_{},query_complete_private_{},query_returned_private_{},selector_returned_private_{},environment_private_{};\n void query();void query_return();void query_snapshot()noexcept;')
write('heap_version.hpp',h)
b=derive('heap_mode_binding.inc')
b=b.replace('m4_crt_heap_version::has_authority()||','m4_crt_heap_mode::has_authority()||')
b=b.replace('mw34_heap_version_probe_body','m4_crt_heap_mode::mw34_heap_mode_probe_body').replace('mw34_heap_version_selector_body','m4_crt_heap_mode::mw34_heap_mode_selector_body')
sp=json.loads((REC/'report.json').read_text())['spans']
additional=''
for i,label in enumerate(('selector-conditions','selector-environment-frontier','selector-mode1-cold','selector-epilogue'),6):
 x=sp[label];additional+=f' source_[{i}]=p.slice({{{x["start"]}}},{x["bytes"]},0x60000000);if(m4::sha256(source_[{i}])!="{x["sha256"]}")throw std::invalid_argument("Exact fresh version continuation source required");\n'
additional+=' source_[10]=p.slice({0x7800c000},4096,0x60000000);if(m4::sha256(source_[10])!="25bd92364d0f450dda6dde287dbeb44ac27d890e3d03c10d73b504d071defb32")throw std::invalid_argument("Exact raw cold selector RX page required");\n'
b=replace(b,' runtime.memory().read({lower_stack},lower_initial_);',additional+' runtime.memory().read({lower_stack},lower_initial_);')
b=replace(b,'void Binding::guard(){','void Binding::query_snapshot()noexcept{query_witness={1,unsigned(query_reached),unsigned(query_called_private_),query_result_private_,148,query_pointer_private_,query_frame_private_,query_ret,caller_error,query_api_error_,query_restored_error_,output_count_private_,unsigned(query_preflight_private_),unsigned(query_complete_private_),unsigned(api_access_count==2),unsigned(query_returned_private_),unsigned(selector_returned_private_),unsigned(environment_private_),query_called_private_?query_word(4):0,query_called_private_?query_word(16):0};}\nunsigned Binding::query_word(unsigned offset)const{unsigned v{};std::memcpy(&v,query_output_private_.data()+offset,4);return v;}\nvoid Binding::guard(){')
b=replace(b,' const auto old=registry;',' if(query_bound_){const auto old_query=query_witness;query_snapshot();if(old_query!=query_witness||query_input!=query_input_private_||query_output!=query_output_private_||query_frame!=query_frame_private_||query_pointer!=query_pointer_private_||query_result!=query_result_private_||output_count!=output_count_private_||query_called!=query_called_private_||query_preflight!=query_preflight_private_||query_output_complete!=query_complete_private_||query_returned!=query_returned_private_||selector_returned!=selector_returned_private_||environment_reached!=environment_private_)deny("Immutable measured query witness and private output transport required",query_site);}\n const auto old=registry;')
b=replace(b,' unsigned query{};try{query=runtime.memory().load<unsigned>({query_iat});}', ' for(unsigned i=6;i<11;++i){const unsigned a=i==6?branch:i==7?environment:i==8?cold:i==9?epilogue:0x7800c000;std::vector<std::byte>b(source_[i].size());try{runtime.memory().read({a},b);}catch(...){deny("Checked exact fresh version source page",a);}if(b!=source_[i])deny("Fresh compiled version continuation identity required",a);}\n if(query_bound_){std::array<std::byte,148>actual{};try{runtime.memory().read({query_pointer_private_},actual);}catch(...){deny("Checked complete version API transport buffer",query_pointer_private_);}if(actual!=query_expected_)deny("Only committed actual API output transport may change version buffer",query_pointer_private_);}\n unsigned query{};try{query=runtime.memory().load<unsigned>({query_iat});}')
controls=''' if(point==13&&control==145)m.protect({0x20001000},Permissions::read);
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
'''
b=replace(b,' if(extra)extra(*this,point);',controls+' if(extra)extra(*this,point);')
b=replace(b,'const auto old_create_before=create_before;', 'const auto old_query_witness=query_witness;const auto old_query_input=query_input;const auto old_query_output=query_output;const auto old_output_accesses=output_accesses;const auto old_query_before=query_before;const auto old_query_after=query_after;const auto old_query_public=std::array<unsigned,10>{query_frame,query_pointer,query_result,output_count,unsigned(query_called),unsigned(query_preflight),unsigned(query_output_complete),unsigned(query_returned),unsigned(selector_returned),unsigned(environment_reached)};const auto old_create_before=create_before;')
b=replace(b,' if(old_create_before!=create_before', ' if(old_query_witness!=query_witness||old_query_input!=query_input||old_query_output!=query_output||std::memcmp(old_output_accesses.data(),output_accesses.data(),sizeof(output_accesses))||old_query_before!=query_before||old_query_after!=query_after||old_query_public!=std::array<unsigned,10>{query_frame,query_pointer,query_result,output_count,unsigned(query_called),unsigned(query_preflight),unsigned(query_output_complete),unsigned(query_returned),unsigned(selector_returned),unsigned(environment_reached)})deny("Query observer changed actual witness, API identity or transport ledger",query_site);\n if(old_create_before!=create_before')
# source-owned continuation accesses use literal PC plus private actual API output.
b=replace(b,' default:deny("Heap mode DWORD read outside admitted source prefix",a);',' default:if(!query_returned_private_)deny("Version source read before actual checked API return",a);\n  pc=state.gpr.rip.dword;if(pc==0x78003a35&&access_count==24&&query_result_private_){address=query_pointer_private_+16;expected=query_word(16);}\n  else if(pc==0x78003a3e&&access_count==25&&query_result_private_&&query_word(16)==2){address=query_pointer_private_+4;expected=query_word(4);}\n  else if(pc==0x7800ccc7&&access_count==27){address=admitted_frame_-8-0x122c-8;expected=1;}\n  else if(pc==0x78003a7d&&access_count==28){address=admitted_frame_-8-0x122c-4;expected=mode_ebx_;}\n  else if(pc==0x78003a7e&&access_count==29){address=admitted_frame_-8;expected=mode_ebp_;}\n  else if(pc==0x78003a7f&&access_count==30){address=admitted_frame_-4;expected=mode_ret;}\n  else if(pc==env_site){address=env_iat;expected=env_raw;}\n  else deny("Version source read outside admitted literal continuation",a);\n  break;')
b=replace(b,' default:deny("Heap mode store outside admitted source prefix",a);',' default:if(!query_returned_private_)deny("Version source store before checked actual API return",a);pc=state.gpr.rip.dword;\n  if(pc==cold&&access_count==26&&query_result_private_&&query_word(16)==2&&query_word(4)>=5){address=admitted_frame_-8-0x122c-8;expected=1;}\n  else if(pc==0x78003a4b){address=admitted_frame_-8-0x122c-8;expected=0x104;}\n  else if(pc==0x78003a57){address=admitted_frame_-8-0x122c-12;expected=admitted_frame_-8-0x118c;}\n  else if(pc==0x78003a58){address=admitted_frame_-8-0x122c-16;expected=env_name;}\n  else if(pc==env_site){address=admitted_frame_-8-0x122c-20;expected=env_ret;}\n  else deny("Version store outside admitted source continuation",a);break;')
b=replace(b,'if(!(old||added))deny("Only four exact XOR/TEST generated AF representatives are admitted",pc);','const bool version=depth==3&&query_returned_private_&&pc==branch&&access_count==24&&api_access_count==2&&undefined_count==4;\n if(!(old||added||version))deny("Only five exact XOR/TEST generated AF representatives are admitted",pc);')
# The query call binds original input before any observer can change it.
needle='  (void)owns_token(token);query_reached=true;event(9,query_site,query_iat,query_raw);checkpoint(runtime,"heap-version-query-before");stable_hook(13);guard();source_identity();first("Required genuine CRT GetVersionExA remains unresolved",query_iat,query_site);admitted_parent_->first(reason,fault_address,fault_pc);throw m4_runtime::Fault(m4_runtime::FaultReason::unresolved_import,{query_site},{query_iat},reason);}'
replacement='''  (void)owns_token(token);query_reached=true;event(9,query_site,query_iat,query_raw);query_frame=query_frame_private_=state.gpr.rsp.dword;query_pointer=query_pointer_private_=admitted_frame_-8-0x98;
  try{runtime.memory().read({query_pointer_private_},query_input_private_);}catch(...){deny("Checked actual full original query input",query_pointer_private_,query_site);}query_input=query_input_private_;query_expected_=query_input_private_;query_bound_=true;query_snapshot();checkpoint(runtime,"heap-mode-query-before");stable_hook(13);guard();source_identity();query();return this;}'''
b=replace(b,needle,replacement)
b=replace(b,' if(target!=mode||depth!=2', ''' if(target==env_raw){if(depth!=3||!query_returned_private_||undefined_count!=5||w.pc!=env_site||w.address!=admitted_frame_-8-0x122c-20||w.value!=env_ret||!w.write||state.gpr.rsp.dword!=w.address||event_count!=10||!owned_handle_||!registered_)deny("Genuine unresolved environment source CALL required",env_iat,env_site);environment_private_=environment_reached=true;query_snapshot();event(11,env_site,env_iat,env_raw);checkpoint(runtime,"heap-version-environment-before");stable_hook(20);guard();source_identity();first("Required genuine CRT GetEnvironmentVariableA remains unresolved",env_iat,env_site);admitted_parent_->first(reason,fault_address,fault_pc);throw m4_runtime::Fault(m4_runtime::FaultReason::unresolved_import,{env_site},{env_iat},reason);}
 if(target!=mode||depth!=2''')
# retain old phase tags for every prior checkpoint
b=b.replace('"heap-version-probe-before"','"heap-mode-probe-before"').replace('"heap-version-probe-after"','"heap-mode-probe-after"')
# New selector RET must stop before old provider continuation executes.
b=replace(b,'void*Binding::returned(State*s,unsigned target,void*p){guard();source_identity();','''void*Binding::returned(State*s,unsigned target,void*p){guard();source_identity();
 if(target==mode_ret){const auto&w=accesses[30];if(s!=&state||p!=this||state.gpr.rip.dword!=mode_ret||depth!=3||!query_returned_private_||!query_result_private_||query_word(16)!=2||query_word(4)<5||access_count!=31||api_access_count!=2||event_count!=10||undefined_count!=5||state.gpr.rax.dword!=1||state.gpr.rsp.dword!=admitted_frame_||state.gpr.rbp.dword!=mode_ebp_||state.gpr.rbx.dword!=mode_ebx_||w.pc!=0x78003a7f||w.address!=admitted_frame_-4||w.value!=mode_ret||w.write)deny("Genuine selector RET and original restored frame required",mode_ret,0x78003a7f);
  selector_returned_private_=selector_returned=true;query_snapshot();event(11,0x78003a7f,mode_ret,w.address);checkpoint(runtime,"heap-version-selector-return-after");stable_hook(20);guard();source_identity();first("Genuine selector returned; heap mode publication remains unadmitted",mode_ret,0x78003a7f);admitted_parent_->first(reason,fault_address,fault_pc);throw m4_runtime::Fault(m4_runtime::FaultReason::unresolved_translation,{0x78003a7f},{mode_ret},reason);}
''')
b=replace(b,'[[noreturn]]void Binding::missing(State*s,unsigned target,void*p){guard();source_identity();','''void*Binding::jumped(State*s,unsigned target,void*p){return missing(s,target,p);}
void*Binding::missing(State*s,unsigned target,void*p){guard();source_identity();
 if(query_returned_private_){if(s!=&state||p!=this||state.gpr.rip.dword!=target||depth!=3||api_access_count!=2||!owned_handle_||!registered_)deny("Exact live query continuation State required",target);
  if(target==branch&&access_count==24&&undefined_count==4&&state.gpr.rsp.dword==admitted_frame_-8-0x122c-4&&state.gpr.rax.dword==query_result_private_)return mw34_heap_version_branch_body(s,target,this);
  if(target==cold&&access_count==26&&undefined_count==5&&query_result_private_&&query_word(16)==2&&query_word(4)>=5)return mw34_heap_version_mode1_body(s,target,this);
  if(target==epilogue&&access_count==28&&state.gpr.rax.dword==1&&query_result_private_&&query_word(16)==2&&query_word(4)>=5)return mw34_heap_version_epilogue_body(s,target,this);
  if(target==environment&&undefined_count==5&&((!query_result_private_&&access_count==24)||(query_result_private_&&query_word(16)!=2&&access_count==25)||(query_result_private_&&query_word(16)==2&&query_word(4)<5&&access_count==26)))return mw34_heap_version_environment_body(s,target,this);
  deny("Unadmitted postquery source block",target);
 }
''')
q='''void Binding::query(){
 guard();source_identity();if(query_called_private_||query_preflight_private_||query_word(0)||query_input_private_[0]!=std::byte{0x94})deny("One genuine size-qualified query required",query_pointer_private_,query_site);
 // Only this private copied memory is written by permission preflight.
 // It invokes the frozen exact extent/permissions implementation without any
 // resident guest write, source store, State reset or output declaration.
 try{auto private_permission_snapshot=runtime.memory();private_permission_snapshot.write({query_pointer_private_},query_input_private_);}catch(...){deny("Full actual query destination permission preflight failed",query_pointer_private_,query_site);}
 query_preflight=query_preflight_private_=true;query_before=measured_api("GetVersionExA",reinterpret_cast<std::uintptr_t>(&::GetVersionExA));query_snapshot();checkpoint(runtime,"heap-version-query-native-before");stable_hook(14);guard();source_identity();
 OSVERSIONINFOA scratch;static_assert(sizeof(scratch)==148);std::memcpy(&scratch,query_input_private_.data(),148);
 {InvocationHostBoundary fp;fn::LastErrorBoundary errors;SetLastError(caller_error);const BOOL actual=::GetVersionExA(&scratch);query_called_private_=query_called=true;std::memcpy(&query_result_private_,&actual,4);query_result=query_result_private_;query_api_error_=GetLastError();SetLastError(caller_error);query_restored_error_=GetLastError();}
 std::memcpy(query_output_private_.data(),&scratch,148);query_output=query_output_private_;query_after=measured_api("GetVersionExA",reinterpret_cast<std::uintptr_t>(&::GetVersionExA));if(query_before!=query_after)deny("Actual GetVersionExA identity changed across native query",query_iat,query_site);query_snapshot();checkpoint(runtime,"heap-version-query-native-after");stable_hook(15);guard();source_identity();
 for(unsigned n=0;n<37;++n){const unsigned a=query_pointer_private_+4*n,v=query_word(4*n);guard();source_identity();try{runtime.memory().store<unsigned>({a},v);}catch(...){deny("Checked actual API output transport store fault",a,query_site);}std::memcpy(query_expected_.data()+4*n,&v,4);output_accesses[output_count_private_++]={query_site,a,v,4,1};output_count=output_count_private_;query_snapshot();stable_hook(16);}
 query_complete_private_=query_output_complete=true;query_snapshot();checkpoint(runtime,"heap-version-query-output-after");stable_hook(17);guard();source_identity();query_return();
}
void Binding::query_return(){checkpoint(runtime,"heap-version-query-return-before");guard();source_identity();if(!query_complete_private_||output_count_private_!=37||api_access_count!=1||access_count!=24||state.gpr.rip.dword!=query_raw||state.gpr.rsp.dword!=query_frame_private_)deny("Exact real query stdcall return frame required",query_frame_private_,query_site);
 unsigned value{};try{value=runtime.memory().load<unsigned>({query_frame_private_});}catch(...){deny("Checked real query return-word read fault",query_frame_private_,query_site);}if(value!=query_ret)deny("Genuine query CALL return word required",query_frame_private_,query_site);api_accesses[api_access_count++]={query_site,query_frame_private_,value,4,0};query_snapshot();stable_hook(18);guard();source_identity();
 state.gpr.rax.dword=query_result_private_;state.gpr.rsp.dword=query_frame_private_+8;state.gpr.rip.dword=query_ret;query_returned_private_=query_returned=true;query_snapshot();event(10,query_site,query_frame_private_,query_ret);checkpoint(runtime,"heap-version-query-returned");stable_hook(19);guard();source_identity();
}
'''
b=replace(b,'void*Binding::called(State*s,unsigned target,void*p){',q+'void*Binding::called(State*s,unsigned target,void*p){')
write('heap_version_binding.inc',b)
for name in ('build.ps1','run.py','capture.s','native/CMakeLists.txt'):
 s=(OLD/name).read_text()
 if name!='capture.s':s=s.replace('heap-mode','heap-version').replace('heap_mode','heap_version').replace('HeapMode','HeapVersion')
 write(name,s)
