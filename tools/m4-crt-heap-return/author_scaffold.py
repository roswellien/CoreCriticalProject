"""Author only the new heap-return namespace from its frozen predecessor."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OLD=ROOT/'tools/m4-crt-heap-version'
HERE=Path(__file__).resolve().parent
def replace(s,a,b):
 assert s.count(a)==1,(a[:100],s.count(a))
 return s.replace(a,b)
def main():
 HERE.mkdir(exist_ok=True)
 h=(OLD/'heap_version.hpp').read_text().replace('namespace mw34::m4_crt_heap_version','namespace mw34::m4_crt_heap_return')
 h=replace(h,'#include "heap_mode.hpp"','#include "heap_mode.hpp"\n#include "heap_version.hpp"')
 h=replace(h,' unsigned query_frame{},query_pointer{},query_result{},output_count{};',' unsigned query_frame{},query_pointer{},query_result{},output_count{};\n bool selector_unwound{},mode_store_before{},mode_published{},initializer_return_before{},initializer_returned{};unsigned mode_value{};\n std::array<unsigned,8>progress()const noexcept;')
 h=replace(h,' bool query_bound_{},',' bool selector_unwound_private_{},mode_store_before_private_{},mode_published_private_{},initializer_return_before_private_{},initializer_returned_private_{};unsigned mode_value_private_{};\n bool query_bound_{},')
 (HERE/'heap_return.hpp').write_text(h)
 s=(OLD/'heap_version_binding.inc').read_text().replace('namespace mw34::m4_crt_heap_version','namespace mw34::m4_crt_heap_return').replace('mw34::m4_crt_heap_version::query_iat','mw34::m4_crt_heap_return::query_iat')
 s=replace(s,'bool has_authority()noexcept{return authority!=nullptr;}','bool has_authority()noexcept{return authority!=nullptr;}\nstd::array<unsigned,8>Binding::progress()const noexcept{return {1,unsigned(selector_unwound_private_),unsigned(mode_store_before_private_),unsigned(mode_published_private_),mode_value_private_,unsigned(initializer_return_before_private_),unsigned(initializer_returned_private_),unsigned(token_valid(token))};}')
 s=s.replace('m4_crt_heap_mode::has_authority()||','m4_crt_heap_version::has_authority()||m4_crt_heap_mode::has_authority()||')
 s=replace(s,' if(state.addr.ds_base.dword',' if(selector_unwound!=selector_unwound_private_||mode_store_before!=mode_store_before_private_||mode_published!=mode_published_private_||mode_value!=mode_value_private_||initializer_return_before!=initializer_return_before_private_||initializer_returned!=initializer_returned_private_)deny("Private genuine initializer progress mirrors required",mode_ret);\n if(state.addr.ds_base.dword')
 s=replace(s,'auto expected=source_[2];if(published)std::memcpy(expected.data(),&guest_result_,4);','auto expected=source_[2];if(published)std::memcpy(expected.data(),&guest_result_,4);if(mode_published_private_)std::memcpy(expected.data()+4,&mode_value_private_,4);')
 s=s.replace('Only genuine source token publication may change heap-global page','Only genuine source token and mode publications may change heap-global page')
 controls=''' if(point==21&&control==157)m.protect({global},Permissions::read);
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
'''
 s=replace(s,' if(extra)extra(*this,point);',controls+' if(extra)extra(*this,point);')
 s=replace(s,'const auto old_progress=progress();','const auto old_initializer=std::array<unsigned,6>{unsigned(selector_unwound),unsigned(mode_store_before),unsigned(mode_published),mode_value,unsigned(initializer_return_before),unsigned(initializer_returned)};const auto old_progress=progress();')
 s=replace(s,' if(old_query_witness!=query_witness',' if(old_initializer!=std::array<unsigned,6>{unsigned(selector_unwound),unsigned(mode_store_before),unsigned(mode_published),mode_value,unsigned(initializer_return_before),unsigned(initializer_returned)})deny("Observer changed genuine initializer progress",mode_ret);\n if(old_query_witness!=query_witness')
 s=replace(s,'  else if(pc==env_site){address=env_iat;expected=env_raw;}','  else if(pc==0x78003a0a&&access_count==33&&depth==2&&selector_unwound_private_&&mode_published_private_){address=admitted_frame_-4;expected=1;if(state.gpr.rsp.dword!=admitted_frame_)deny("Generated POP publishes ESP before checked read",a);}\n  else if(pc==0x78003a0b&&access_count==34&&depth==2&&selector_unwound_private_&&mode_published_private_){address=admitted_frame_;expected=ret;if(state.gpr.rsp.dword!=admitted_frame_||state.gpr.rax.dword!=1)deny("Genuine initializer RET input frame required",a);initializer_return_before_private_=initializer_return_before=true;checkpoint(runtime,"heap-return-initializer-return-before");stable_hook(23);guard();source_identity();}\n  else if(pc==env_site){address=env_iat;expected=env_raw;}')
 s=replace(s,'  else if(pc==0x78003a51){','  else if(pc==0x780039eb&&access_count==31&&depth==2&&selector_unwound_private_&&!mode_published_private_){address=global+4;expected=1;if(state.gpr.rax.dword!=1||state.gpr.rsp.dword!=admitted_frame_)deny("Actual selector result required for genuine mode publication",a);mode_store_before_private_=mode_store_before=true;checkpoint(runtime,"heap-return-mode-store-before");stable_hook(21);guard();source_identity();}\n  else if(pc==0x78003a08&&access_count==32&&depth==2&&mode_published_private_){address=admitted_frame_-4;expected=1;if(state.gpr.rax.dword!=1||state.gpr.rsp.dword!=admitted_frame_)deny("Genuine mode1 PUSH input required",a);}\n  else if(pc==0x78003a51){')
 s=replace(s,'if(access_count==8)published=true;record(a,v,1);','if(access_count==8)published=true;if(access_count==31&&pc==0x780039eb){mode_published_private_=mode_published=true;mode_value_private_=mode_value=v;event(12,pc,a,v);}record(a,v,1);if(access_count==32&&pc==0x780039eb){checkpoint(runtime,"heap-return-mode-store-after");stable_hook(22);guard();source_identity();}')
 s=replace(s,'depth=3;(void)m4_crt_heap_mode::mw34_heap_mode_selector_body(s,target,this);deny("Unexpected completed selector past required OS-query frontier",target,mode_site);','depth=3;auto result=m4_crt_heap_mode::mw34_heap_mode_selector_body(s,target,this);guard();source_identity();if(result!=this||!selector_unwound_private_||depth!=2||state.gpr.rip.dword!=mode_ret||state.gpr.rsp.dword!=admitted_frame_||state.gpr.rax.dword!=1||access_count!=31||event_count!=11)deny("Genuine selector must unwind into its original translated provider CALL",mode_ret,mode_site);return this;')
 s=replace(s,'first("Genuine selector returned; heap mode publication remains unadmitted",mode_ret,0x78003a7f);admitted_parent_->first(reason,fault_address,fault_pc);throw m4_runtime::Fault(m4_runtime::FaultReason::unresolved_translation,{0x78003a7f},{mode_ret},reason);','selector_unwound_private_=selector_unwound=true;depth=2;return this;')
 s=replace(s,'void*Binding::returned(State*s,unsigned target,void*p){guard();source_identity();','''void*Binding::returned(State*s,unsigned target,void*p){guard();source_identity();
 if(target==ret){const auto&w=accesses[34];if(s!=&state||p!=this||state.gpr.rip.dword!=ret||depth!=2||!selector_unwound_private_||!mode_published_private_||mode_value_private_!=1||!initializer_return_before_private_||initializer_returned_private_||!owned_handle_||!registered_||access_count!=35||api_access_count!=2||event_count!=12||undefined_count!=5||state.gpr.rax.dword!=1||state.gpr.rsp.dword!=admitted_frame_+4||state.gpr.rbp.dword!=mode_ebp_||state.gpr.rbx.dword!=mode_ebx_||w.pc!=0x78003a0b||w.address!=admitted_frame_||w.value!=ret||w.write)deny("Genuine initializer RET must preserve original frame and private live heap",ret,0x78003a0b);
  initializer_returned_private_=initializer_returned=true;event(13,0x78003a0b,ret,w.address);checkpoint(runtime,"heap-return-initializer-return-after");stable_hook(24);guard();source_identity();first("Genuine heap initializer returned; fragment caller continuation remains unadmitted",ret,0x78003a0b);admitted_parent_->first(reason,fault_address,fault_pc);throw m4_runtime::Fault(m4_runtime::FaultReason::unresolved_translation,{0x78003a0b},{ret},reason);}
''')
 (HERE/'heap_return_binding.inc').write_text(s)
 for name in ('build.ps1','run.py','capture.s'):
  s=(OLD/name).read_text()
  if name!='capture.s':s=s.replace('m4-crt-heap-version','m4-crt-heap-return').replace('entry_heap_version','entry_heap_return')
  if name=='build.ps1':
   s=s.replace("'preparation-r2'","'preparation-r1'")
   s=replace(s,'$cpObject=Join-Path $cpPrep "$cpKind-$cpLevel.obj";','$cpObject=Join-Path $cpRoot "reports/m4-crt-heap-version/preparation-r2/$cpKind-$cpLevel.obj";')
   s=s.replace('old_guest_objects=30','old_guest_objects=38').replace('Source/build-only real version API bridge and four exact translated postquery blocks','Source/build-only genuine initializer mode publication and RET using38 unchanged source COFFs')
  if name=='run.py':
   s=s.replace("'fccb8400f1c4a5b8ee3824684d763d1a6391d9322ad28c0a5b173ef8bf483154'","'cedd67126afce1ec3392e8e0f8fec71f54823e58bc353055aee723203eef18d1'")
   s=s.replace('reports/m4-crt-heap-mode-root/root-acceptance-r1/report.json','reports/m4-crt-heap-version-root/root-acceptance-r1/report.json')
   s=s.replace('index + 121','index + 133').replace('heap-version-witness.bin','heap-return-witness.bin').replace('heap-version-registry.bin','heap-return-registry.bin').replace('heap-version-query-witness.bin','heap-return-query-witness.bin')
   s=s.replace('ordinary_source_PCs_if_qualifying=51','ordinary_source_PCs_if_qualifying=59').replace('ordinary_source_accesses_if_qualifying=31','ordinary_source_accesses_if_qualifying=35').replace('source_RET_count_if_qualifying=2','source_RET_count_if_qualifying=3').replace('new_guest_objects=8, reused_guest_objects=30','new_guest_objects=0, reused_guest_objects=38')
   s=s.replace('heap_mode_global_published=False, initializer_RET_executed=False,heap_initialized=False','heap_mode_global_published=qualifying_returns>0, initializer_RET_executed=qualifying_returns>0,heap_initialized=False')
   s=s.replace('"""Root-owned x64 execution, timed stages and externally bound capture bundles."""','"""Author-executed x64 source returns, timed stages and strict capture bundles."""')
  (HERE/name).write_text(s)
 (HERE/'native').mkdir(exist_ok=True)
 (HERE/'native/CMakeLists.txt').write_text((OLD/'native/CMakeLists.txt').read_text().replace('HeapVersion','HeapReturn').replace('entry_heap_version','entry_heap_return'))
if __name__=='__main__':main()
