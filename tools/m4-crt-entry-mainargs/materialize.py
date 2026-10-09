"""One-time additive composition derivative of the accepted literal initterm gate."""
import pathlib,shutil,sys
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2];HERE=pathlib.Path(__file__).resolve().parent;OLD=ROOT/'reports/m4-crt-entry-initterm/preparation-r3'
def replace(s,a,b):
 assert s.count(a)==1,(a[:90],s.count(a));return s.replace(a,b)
def main():
 for n in ('composition.cpp','main_v2.inc','observations.hpp','control_binding.inc','initterm_binding.inc','initterm_context.hpp','seed.hpp','matherr_context.hpp','control_context.hpp'):
  assert not (HERE/n).exists();shutil.copyfile(OLD/n,HERE/n)
 shutil.copyfile(ROOT/'tools/m4-crt-entry-initterm/capture.s',HERE/'capture.s')
 (HERE/'native').mkdir();shutil.copyfile(ROOT/'tools/m4-crt-entry-initterm/native/CMakeLists.txt',HERE/'native/CMakeLists.txt')
 for n in ('build.ps1','run.py'):shutil.copyfile(ROOT/'tools/m4-crt-entry-initterm'/n,HERE/n)
 p=HERE/'composition.cpp';s=p.read_text();s=replace(s,'#include "initterm_context.hpp"','#include "initterm_context.hpp"\n#include "mainargs_context.hpp"');s=replace(s,'namespace nt=mw34::m4_crt_entry_initerm;','namespace nt=mw34::m4_crt_entry_initerm;\nnamespace mg=mw34::m4_crt_entry_mainargs;');s=replace(s,'#include "initterm_binding.inc"','#include "initterm_binding.inc"\n#include "mainargs_binding.inc"')
 # Strict highest-priority current-owner dispatch, before any other typed token.
 a='extern "C" unsigned __remill_read_memory_32(void*p,unsigned a) noexcept(false) {';s=replace(s,a,a+'if(mg::owner){if(p!=mg::owner||nt::owner||ci::owner||mn::owner)mg::owner->deny("Exact current mainargs read token",a);return mg::owner->read(a);}')
 a='extern "C" void*__remill_write_memory_32(void*p,unsigned a,unsigned v) noexcept(false) {';s=replace(s,a,a+'if(mg::owner){if(p!=mg::owner||nt::owner||ci::owner||mn::owner)mg::owner->deny("Exact current mainargs write token",a);mg::owner->write(a,v);return p;}')
 a='extern "C" void*__remill_function_call(State*s,unsigned a,void*p) noexcept(false) {';s=replace(s,a,a+'if(mg::owner){if(p!=mg::owner||nt::owner||ci::owner||mn::owner)mg::owner->deny("Exact current mainargs import token",a,mg::import_call);mg::owner->called(s,a);}')
 a='extern "C" void*__remill_function_return(State*s,unsigned a,void*p) noexcept(false) {';s=replace(s,a,a+'if(mg::owner){if(p!=mg::owner||nt::owner||ci::owner||mn::owner)mg::owner->deny("Exact current mainargs return token",a);mg::owner->deny("Required mainargs RET outside bounded prefix",a);}')
 s=replace(s,'extern "C" unsigned char __remill_read_memory_8(void*,unsigned) noexcept(false) {throw std::runtime_error("Unreached required byte-read bridge");}','extern "C" unsigned char __remill_read_memory_8(void*p,unsigned a) noexcept(false) {if(mg::owner){if(p!=mg::owner||nt::owner||ci::owner||mn::owner)mg::owner->deny("Exact current mainargs byte-read token",a);mg::owner->deny("Required mainargs byte read outside bounded prefix",a);}throw std::runtime_error("Unreached required byte-read bridge");}')
 # Non-mainargs bridges cannot fall through while the mainargs owner is current.
 lines=s.splitlines()
 for i,line in enumerate(lines):
  if line.startswith('extern "C"') and 'noexcept(false) {'in line and not any(x in line for x in ['__remill_read_memory_32','__remill_write_memory_32','__remill_function_call','__remill_function_return','__remill_read_memory_8']):
   lines[i]=line.replace('noexcept(false) {','noexcept(false) {require(!mg::owner,"Other bridge cannot use active mainargs owner");',1)
 s='\n'.join(lines)+'\n';a='#include "main_v2.inc"'
 bridges='''extern "C" void*sub_7800bbbc(State*s,unsigned a,void*p) noexcept(false){if(!mg::owner)throw std::runtime_error("Mainargs nested builder owner absent");if(p!=mg::owner||nt::owner||ci::owner||mn::owner)mg::owner->deny("Exact current mainargs nested builder token",a,mg::internal_call);mg::owner->nested(s,a,p);return p;}
extern "C" void*sub_7800b3b4(State*s,unsigned a,void*p) noexcept(false){if(!mg::owner)throw std::runtime_error("Mainargs wildcard owner absent");mg::owner->unsupported(s,a,p,0x7800ba71);}
extern "C" void*sub_7800bc48(State*s,unsigned a,void*p) noexcept(false){if(!mg::owner)throw std::runtime_error("Mainargs parser owner absent");mg::owner->unsupported(s,a,p,0x7800bbf7);}
extern "C" void*sub_780012b3(State*s,unsigned a,void*p) noexcept(false){if(!mg::owner)throw std::runtime_error("Mainargs allocator owner absent");mg::owner->unsupported(s,a,p,0x7800bc06);}
extern "C" void*sub_7800badb(State*s,unsigned a,void*p) noexcept(false){if(!mg::owner)throw std::runtime_error("Mainargs exit owner absent");mg::owner->unsupported(s,a,p,0x7800bc16);}
extern "C" unsigned char mw34_mainargs_normal_argv_undefined_8() noexcept(false){if(!mg::owner)throw std::runtime_error("Mainargs undefined owner absent");mg::owner->deny("Required argv TEST AF outside bounded prefix");}
'''
 s=replace(s,a,bridges+a);p.write_text(s)
 p=HERE/'observations.hpp';s=p.read_text();a='fresh_output(phase/"state.bin",r.remill_state());';s=replace(s,a,'{std::array<std::byte,66>a{};std::array<std::byte,140>b{};r.memory().read({mg::entry},a);r.memory().read({mg::builder},b);fresh_output(phase/"mainargs-provider.bin",a);fresh_output(phase/"mainargs-builder.bin",b);}\n '+a);p.write_text(s)
 p=HERE/'main_v2.inc';s=p.read_text().replace('MW34_ENTRY_INITTERM_NO_MAIN','MW34_ENTRY_MAINARGS_NO_MAIN');s=replace(s,'void initterm_checkpoint(Runtime&r,const char*name){snapshot(r,checkpoint_directory,name);}','void initterm_checkpoint(Runtime&r,const char*name){snapshot(r,checkpoint_directory,name);}void mainargs_checkpoint(Runtime&r,const char*name){snapshot(r,checkpoint_directory,name);}')
 s=replace(s,'scenario<72','scenario<84');s=replace(s,'InitermBinding initterm(r,image,provider,mode);','InitermBinding initterm(r,image,provider,mode);MainargsBinding mainargs(r,provider,mode);')
 a='r.cpu().esp=frame+4;r.cpu().eip=Runtime::external_return;r.freeze_registry();';s=replace(s,a,'r.register_service({{mg::slot},{Abi::Cdecl,20,true},&mainargs_adapter,"Actual compiled __getmainargs bounded provider prefix",Domain::admitted_game,fd::provider_sha,MW34_MAINARGS_RECOVERY_SHA});\n  '+a)
 a='initterm_binding=&initterm;boundary';s=replace(s,a,'initterm_binding=&initterm;mainargs_binding=&mainargs;boundary');a='initterm_binding=nullptr;\n  snapshot';s=replace(s,a,'initterm_binding=nullptr;mainargs_binding=nullptr;\n  snapshot')
 a='require(entry_job.denied&&r.poisoned(),"Required unresolved or causal dependency terminal");';addition='''raw_output(row/"mainargs-events.bin",mainargs.context.events);raw_output(row/"mainargs-accesses.bin",mainargs.context.accesses);auto&mc=mainargs.context;std::array<unsigned,20>mainargs_job{mg::slot,mc.raw,mc.frame,mc.ret,mc.argc_ptr,mc.argv_ptr,mc.env_ptr,mc.wildcard,mc.startup_ptr,mc.startup_value,mc.access_count,mc.event_count,mc.boundary_depth,unsigned(mc.used),unsigned(mc.active),unsigned(mc.failed),unsigned(mc.reached_import),mc.stage,mc.fault_pc,mc.fault_address};raw_output(row/"mainargs-job.bin",mainargs_job);std::ofstream mainargs_reason(row/"mainargs-reason.txt");mainargs_reason<<(mc.reason?mc.reason:"")<<'\\n';require(bool(mainargs_reason),"Mainargs first reason retained");
  ''';s=replace(s,a,addition+a)
 s=replace(s,'entry_job.fault_pc==0x5ac468&&entry_job.fault_target==0x5bb514','entry_job.fault_pc==mg::import_call&&entry_job.fault_target==mg::import_slot')
 s=replace(s,'r.calls().size()==10&&!r.calls()[0].completed','r.calls().size()==11&&!r.calls()[0].completed&&!r.calls()[10].completed');s=replace(s,'} else require(entry_job.fault_pc!=0x5ac468||entry_job.fault_target!=0x5bb514','} else require(entry_job.fault_pc!=mg::import_call||entry_job.fault_target!=mg::import_slot')
 s=replace(s,'!initterm.context.active&&!initterm.context.boundary_depth,"Matherr ownership cleanup','!initterm.context.active&&!initterm.context.boundary_depth&&!mg::owner&&!mainargs_binding&&!mainargs.context.active&&!mainargs.context.boundary_depth,"Matherr ownership cleanup')
 a='const auto chain=r.seh_chain();';s=replace(s,a,'require(mainargs.context.reached_import&&mainargs.context.failed&&mainargs.context.access_count==16&&mainargs.context.event_count==4,"Literal mainargs/helper source reaches named OS import before parser");\n   '+a)
 p.write_text(s)
 p=HERE/'native/CMakeLists.txt';s=p.read_text().replace('MW34EntryInitterm','MW34EntryMainargs').replace('entry_initterm','entry_mainargs').replace('"${MW34_INITTERM_OBJECT}"','"${MW34_INITTERM_OBJECT}" "${MW34_MAINARGS_OBJECT}" "${MW34_ARGV_OBJECT}"').replace('MW34_REPLAY_INPUT_SHA="${MW34_REPLAY_INPUT_SHA}"','MW34_REPLAY_INPUT_SHA="${MW34_REPLAY_INPUT_SHA}" MW34_MAINARGS_RECOVERY_SHA="${MW34_MAINARGS_RECOVERY_SHA}"');p.write_text(s)
 p=HERE/'build.ps1';s=p.read_text().replace('reports/m4-crt-entry-initterm','reports/m4-crt-mainargs').replace("'preparation-r3'","'preparation-r1'").replace("'entry_initterm.exe'","'entry_mainargs.exe'")
 s=replace(s,'$cpIniterm=Join-Path $cpRoot "reports/m4-crt-mainargs/provider-preparation-r3/provider-$cpLevel.obj";','$cpIniterm=Join-Path $cpRoot "reports/m4-crt-entry-initterm/provider-preparation-r3/provider-$cpLevel.obj";')
 a='$cpObjects[$cpIniterm]=Hash $cpIniterm';s=replace(s,a,a+'\n  $cpMainargs=Join-Path $cpRoot "reports/m4-crt-mainargs/recovery-r3/mainargs-$cpLevel.obj";$cpObjects[$cpMainargs]=Hash $cpMainargs\n  $cpArgv=Join-Path $cpRoot "reports/m4-crt-mainargs/recovery-r3/normal_argv-$cpLevel.obj";$cpObjects[$cpArgv]=Hash $cpArgv')
 a='"-DMW34_INITTERM_OBJECT=$cpIniterm"';s=replace(s,a,a+' ,"-DMW34_MAINARGS_OBJECT=$cpMainargs","-DMW34_ARGV_OBJECT=$cpArgv","-DMW34_MAINARGS_RECOVERY_SHA=ea623fb2d4bbad3e7636e8155eaafbc6ce6915e293fdd851e4f9eadbc2e0c038"')
 s=s.replace('full bounded CRT entry plus actual first _initterm provider','full bounded CRT entry plus actual mainargs/helper provider prefix');p.write_text(s)
 p=HERE/'run.py';s=p.read_text().replace('m4-crt-entry-initterm','m4-crt-mainargs').replace('range(72)','range(84)').replace('native_phases=144','native_phases=168').replace('causal_negative_sequences=96','causal_negative_sequences=120').replace('with actual control and compiled first initterm provider to unresolved __getmainargs','with actual mainargs/helper prefix to required named GetModuleFileNameA');p.write_text(s)
 print('New mainargs source derivative materialized; frozen sources unchanged')
if __name__=='__main__':main()
