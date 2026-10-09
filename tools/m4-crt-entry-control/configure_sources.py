"""Materialize explicit new composition edits; no prior source is modified."""
import pathlib,shutil
HERE=pathlib.Path(__file__).resolve().parent
def once(s,a,b):
 assert s.count(a)==1,a
 return s.replace(a,b)
def main():
 for name in ('composition.cpp','main_v2.inc','observations.hpp'):
  shutil.copyfile(HERE.parents[1]/'reports/m4-crt-entry-matherr/preparation-r3'/name,HERE/name)
 for dest,source in [('native/CMakeLists.txt','native/CMakeLists.txt'),('build.ps1','build_v3.ps1'),('run.py','run.py')]:
  shutil.copyfile(HERE.parent/'m4-crt-entry-matherr'/source,HERE/dest)
 p=HERE/'composition.cpp';s=p.read_text()
 s=once(s,'#include "matherr_context.hpp"','#include "matherr_context.hpp"\n#include "control_context.hpp"')
 s=once(s,'namespace mn=mw34::m4_crt_matherr_paired_native;','namespace mn=mw34::m4_crt_matherr_paired_native;\nnamespace ci=mw34::m4_crt_control_integration;')
 s=once(s,'class Context;','#include "control_binding.inc"\nclass Context;')
 s=once(s,'(target==0x5ac5c0||target==0x5ac5a0)','(target==0x5ac5c0||target==0x5ac5a0||target==0x5ac598)')
 s=once(s,'const auto site=target==0x5ac5c0?0x5ac415U:0x5ac431U,ret=target==0x5ac5c0?0x5ac41aU:0x5ac436U;','const auto site=target==0x5ac5c0?0x5ac415U:target==0x5ac5a0?0x5ac431U:0x5ac440U,ret=target==0x5ac5c0?0x5ac41aU:target==0x5ac5a0?0x5ac436U:0x5ac445U;')
 s=once(s,'r_.cpu()=cpu(s_);r_.cpu().esp+=4;r_.cpu().eip=w.pc;r_.call_direct',
  'if(target==0x5ac5a0&&control_binding){if(control_binding->control==30)s_.x87.fxsave.cwd.flat^=0x100;if(control_binding->control==31){s_.x87.fxsave.swd.flat=1;r_.fx()[2]=std::byte{1};}if(control_binding->control==32){s_.x87.fxsave.ftw.flat=1;r_.fx()[4]=std::byte{1};}}r_.cpu()=cpu(s_);r_.cpu().esp+=4;r_.cpu().eip=w.pc;r_.call_direct')
 s=once(s,'{if(mn::owner){require(p==mn::owner,"Exact current matherr memory token");return mn::owner->read(a);}', '{if(ci::owner){require(p==ci::owner&&!mn::owner,"Exact current control memory token");return ci::owner->read32(a,true);}if(mn::owner){require(p==mn::owner,"Exact current matherr memory token");return mn::owner->read(a);}')
 s=once(s,'{if(mn::owner){require(p==mn::owner,"Exact current matherr memory token");mn::owner->write(a,v);return p;}', '{if(ci::owner){require(p==ci::owner&&!mn::owner,"Exact current control write token");ci::owner->write32(a,v);return p;}if(mn::owner){require(p==mn::owner,"Exact current matherr memory token");mn::owner->write(a,v);return p;}')
 s=once(s,'{if(mn::owner){require(p==mn::owner,"Exact current matherr return token");mn::owner->returned(s,a);return p;}', '{if(ci::owner){require(p==ci::owner&&!mn::owner,"Exact current control return token");ci::owner->returned(s,a);return p;}if(mn::owner){require(p==mn::owner,"Exact current matherr return token");mn::owner->returned(s,a);return p;}')
 s=once(s,'extern "C" void*__remill_jump(State*,unsigned,void*) noexcept(false) {throw std::runtime_error("Unreached required jump bridge");}',
  'extern "C" void*__remill_jump(State*s,unsigned a,void*p) noexcept(false) {require(ci::owner&&p==ci::owner&&!mn::owner,"Exact current control jump token");ci::owner->tail(s,a);return p;}\n'
  'extern "C" void*mw34_ci_enter(State*s,unsigned a,void*p) noexcept(false) {require(ci::owner&&p==ci::owner&&!mn::owner,"Exact current control game-enter token");ci::owner->game_enter(s,a);return p;}\n'
  'extern "C" void*mw34_cf_enter(State*s,unsigned a,void*p) noexcept(false) {require(ci::owner&&p==ci::owner&&!mn::owner,"Exact current control provider-enter token");ci::owner->enter(s,a);return p;}\n'
  'extern "C" void*mw34_cf_wait(State*s,unsigned a,void*p) noexcept(false) {require(ci::owner&&p==ci::owner&&!mn::owner,"Exact current control wait token");ci::owner->wait(s,a);return p;}\n'
  'extern "C" void*mw34_cf_store_cw(State*s,unsigned a,void*p) noexcept(false) {require(ci::owner&&p==ci::owner&&!mn::owner,"Exact current control CW-store token");auto&c=*ci::owner;c.guard();if(!c.cw.store(s,{a}))c.deny("Required connected typed FNSTCW fault",a);c.access(a,c.memory.load<unsigned short>({a}),2,1);return p;}\n'
  'extern "C" void*mw34_cf_load_cw(State*s,unsigned a,void*p) noexcept(false) {require(ci::owner&&p==ci::owner&&!mn::owner,"Exact current control CW-load token");auto&c=*ci::owner;c.guard();const auto v=c.memory.load<unsigned short>({a});if(!c.cw.load(s,{a}))c.deny("Required connected typed FLDCW fault",a);c.access(a,v,2,0);return p;}')
 # Other outer entry-only bridge tokens cannot become usable while nested owner active.
 for text in ('Exact active entry call token','Exact active entry direct token','Exact active entry enter token'):
  s=once(s,'require(owner&&p==owner,"'+text+'")','require(owner&&p==owner&&!ci::owner&&!mn::owner,"'+text+'")')
 p.write_text(s)
 p=HERE/'main_v2.inc';s=p.read_text();s=once(s,'#ifndef MW34_ENTRY_MATHERR_NO_MAIN','#ifndef MW34_ENTRY_CONTROL_NO_MAIN');s=once(s,'scenario<48','scenario<60')
 s=once(s,'MatherrBinding matherr(r,provider,mode);Context context','MatherrBinding matherr(r,provider,mode);ControlBinding control(r,mode);Context context')
 anchor='  r.cpu().esp=frame+4;r.cpu().eip=Runtime::external_return;r.freeze_registry();'
 s=once(s,anchor,'  r.register_translation({{ci::wrapper},{Abi::Cdecl,0,true},&control_wrapper_adapter,"Actual compiled game control wrapper inside entry",{Domain::admitted_game,m4::admitted_image_hash,19,"ae1fa42ecf74ee2fb8a6076d57a6d7cb51e91890df3a0b0e839f8a4f4063f4ac",MW34_CONTROL_OBJECT_SHA,"2ff6fb125e0abae0b125f0e00e430cf5e8e4a0ab3a22b1c1eb9fefcb65c8175a"}});\n  r.register_service({{ci::slot},{Abi::Cdecl,8,true},&control_provider_adapter,"Actual staged MSVCRT control provider",Domain::admitted_game,fd::provider_sha,"b75abde48029efcdb8cb123c163c6bfb27a9b76dc62da014e620fca7c95bac56"});\n'+anchor)
 anchor='  snapshot(r,row,"entry-before-invoke");'
 s=once(s,anchor,'  if(mode==25)mutation(r,ci::wrapper,0);\n  if(mode==26)mutation(r,ci::thunk,0);\n  if(mode==27)mutation(r,ci::slot,control.context.raw_iat^1);\n  if(mode==28)mutation(r,ci::provider_entry,0);\n  if(mode==29)mutation(r,0x7801129b,0);\n'+anchor)
 s=once(s,'matherr_binding=&matherr;boundary(entry_job,row,"entry",scenario);matherr_binding=nullptr;','matherr_binding=&matherr;control_binding=&control;boundary(entry_job,row,"entry",scenario);matherr_binding=nullptr;control_binding=nullptr;')
 anchor='  require(entry_job.denied&&r.poisoned(),"Required unresolved or causal dependency terminal");'
 s=once(s,anchor,'  raw_output(row/"control-events.bin",control.context.events);raw_output(row/"control-accesses.bin",control.context.accesses);std::array<unsigned,12>control_job{control.context.raw_iat,control.context.count,control.context.access_count,control.context.depth,control.context.boundary_depth,unsigned(control.context.active),unsigned(control.context.failed),unsigned(control.context.complete),control.context.fault_pc,control.context.fault_address,static_cast<unsigned>(control.context.cw.fault()),control.context.cw.fault_address().value};raw_output(row/"control-job.bin",control_job);std::ofstream control_reason(row/"control-reason.txt");control_reason<<(control.context.reason?control.context.reason:"")<<\'\\n\';require(bool(control_reason),"Control reason retained");\n'+anchor)
 s=s.replace('entry_job.fault_pc==0x5ac431&&entry_job.fault_target==0x5ac5a0','entry_job.fault_pc==0x5ac440&&entry_job.fault_target==0x5ac598').replace('entry_job.fault_pc!=0x5ac431||entry_job.fault_target!=0x5ac5a0','entry_job.fault_pc!=0x5ac440||entry_job.fault_target!=0x5ac598')
 s=once(s,'require(r.calls().size()==6&&!r.calls()[0].completed','require(r.calls().size()==8&&!r.calls()[0].completed');s=once(s,'for(unsigned i=1;i<6;++i)','for(unsigned i=1;i<8;++i)')
 s=once(s,'   const auto chain=r.seh_chain();','   require(control.context.complete&&!control.context.failed&&!control.context.depth&&!control.context.boundary_depth&&!control.context.active,"Actual complete control returned into real entry continuation");\n   const auto chain=r.seh_chain();')
 s=once(s,'require(!matherr.context.active&&!mn::owner&&!matherr_binding,','require(!matherr.context.active&&!mn::owner&&!matherr_binding&&!control.context.active&&!control.context.boundary_depth&&!ci::owner&&!control_binding,')
 s=s.replace('Next actual direct control-wrapper dependency','Next actual initializer-range dependency')
 p.write_text(s)
 p=HERE/'observations.hpp';s=p.read_text();s=once(s,'fresh_output(phase/"matherr-source.bin",matherr_source);',
  'fresh_output(phase/"matherr-source.bin",matherr_source);for(auto [address,size,name]:std::array<std::tuple<unsigned,unsigned,const char*>,4>{{{ci::wrapper,19,"control-wrapper.bin"},{ci::thunk,6,"control-thunk.bin"},{ci::provider_entry,303,"control-hot.bin"},{0x7801129b,125,"control-cold.bin"}}}){std::vector<std::byte>bytes(size);r.memory().read({address},bytes);fresh_output(phase/name,bytes);}')
 p.write_text(s)
 p=HERE/'main_v2.inc';s=p.read_text();s=once(s,'void matherr_checkpoint(Runtime&r,const char*name){snapshot(r,checkpoint_directory,name);}','void matherr_checkpoint(Runtime&r,const char*name){snapshot(r,checkpoint_directory,name);}void control_checkpoint(Runtime&r,const char*name){snapshot(r,checkpoint_directory,name);}')
 p.write_text(s)
 p=HERE/'native/CMakeLists.txt';s=p.read_text().replace('entry_matherr','entry_control').replace('MW34EntryMatherr','MW34EntryControl');s=once(s,'"${MW34_MATHERR_OBJECT}")','"${MW34_MATHERR_OBJECT}" "${MW34_CONTROL_OBJECT}" "${MW34_ROOT}/tools/m4-guest-cw/guest_cw.cpp")');s=once(s,'MW34_ENTRY_OBJECT_SHA="${MW34_ENTRY_OBJECT_SHA}"','MW34_ENTRY_OBJECT_SHA="${MW34_ENTRY_OBJECT_SHA}" MW34_CONTROL_OBJECT_SHA="${MW34_CONTROL_OBJECT_SHA}"');p.write_text(s)
 p=HERE/'build.ps1';s=p.read_text().replace('m4-crt-entry-matherr','m4-crt-entry-control').replace('preparation-r3','preparation-r2').replace('entry_matherr.exe','entry_control.exe')
 s=once(s,'  $cpLibrary=Join-Path', '  $cpControl=Join-Path $cpRoot "reports/m4-crt-control-integration/native-build-r1/native-$cpLevel.obj";$cpObjects[$cpControl]=Hash $cpControl\n  $cpLibrary=Join-Path')
 s=once(s,'"-DMW34_MATHERR_OBJECT=$cpMatherr"','"-DMW34_MATHERR_OBJECT=$cpMatherr","-DMW34_CONTROL_OBJECT=$cpControl","-DMW34_CONTROL_OBJECT_SHA=$($cpObjects[$cpControl])"')
 p.write_text(s)
 p=HERE/'run.py';s=p.read_text().replace('m4-crt-entry-matherr','m4-crt-entry-control').replace('range(48)','range(60)').replace('native_phases=96','native_phases=120').replace('causal_negative_sequences=48','causal_negative_sequences=72');p.write_text(s)
if __name__=='__main__':main()
