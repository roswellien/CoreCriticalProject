"""Independent exact derivative, source/compiler/header and COFF association audit."""
import importlib.util, json, re, sys, traceback
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('own_initterm_source_contract',HERE/'review.py')
R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
ROOT,BASE=R.ROOT,R.BASE
OLD=ROOT/'reports/m4-crt-entry-control/preparation-r5'

def once(s,a,b):
 R.need(s.count(a)==1,'Exact derivative anchor '+a);return s.replace(a,b)

def frozen_components(prep,build):
 oldbuild=R.read(ROOT/'reports/m4-crt-entry-control/build-r6/build.json')
 for name in('seed.hpp','matherr_context.hpp','control_context.hpp'):
  ancestor=R.text(OLD/name);candidate=R.text(prep/name)
  R.need(candidate==ancestor,'Frozen complete source retained '+name)
 R.need(R.text(prep/'control_binding.inc')==R.text(ROOT/'tools/m4-crt-entry-control/control_binding.inc'),'Whole accepted control binding retained unchanged')
 R.need(R.text(ROOT/'tools/m4-crt-entry-initterm/capture.s')==R.text(ROOT/'tools/m4-crt-entry-control/capture.s'),'Exact encompassing host capture assembly retained')
 reused=[]
 for level in('O0','O2'):
  for path in(ROOT/f'reports/m4-crt-fdiv-entry-prefix/preparation-r2/candidate-{level}.obj',ROOT/f'reports/m4-crt-matherr/paired-native-build-r7/native-{level}.obj',ROOT/f'reports/m4-crt-entry-control/build-r6/control-{level}.obj'):
   wanted=oldbuild['entry_objects'][str(path)]
   R.need(build['entry_objects'].get(str(path))==wanted,'Exact old compiled object association');R.pin(path,wanted);reused.append(dict(path=str(path),sha256=wanted))
  lib=ROOT/f'build/m4-fdiv-native-build-r3-{level}/fdiv_registry.lib'
  wanted=oldbuild['libraries'][str(lib)];R.need(build['libraries'].get(str(lib))==wanted,'Exact old FDIV compiled registry');R.pin(lib,wanted)
 R.check('Whole frozen producer, matherr and control source/object components preserved',objects=reused,control_object_recompiled=False,old_provider_FP_transfer_changed=False,old_full_components_modified=False)

def session_derivative(prep):
 old=R.text(ROOT/'tools/m4-crt/crt_services.cpp');new=R.text(prep/'crt_services.cpp')
 expected=once(old,'namespace mw34::m4_crt {','namespace mw34::m4_crt {\nvoid compiled_initterm(m4_runtime::Runtime&);')
 expected=once(expected,'slots.initterm,"_initterm",initterm,8','slots.initterm,"_initterm",compiled_initterm,8')
 expected=once(expected,'r.register_service_continuation(provider,std::move(c));','// First-null gate admits no callback continuation; complete provider source is owned by its literal full page.')
 R.need(new==expected,'Complete Session derivative consists only of the three declared narrow edits')
 R.need(R.text(prep/'crt_services.cpp.ancestor')==old and R.text(prep/'crt_services.hpp')==R.text(ROOT/'tools/m4-crt/crt_services.hpp'),'Frozen original Session/header association')
 R.need(new[new.index('void Session::initterm'):]==old[old.index('void Session::initterm'):],'Historical handwritten _initterm body untouched and inactive')
 R.check('Exact minimal CRT Session publication seam',changes=['One compiled_initterm forward declaration','Only _initterm callback registration pointer replaced','Unused callback continuation publication withheld'],all_other_constructor_services_globals_and_bodies_unchanged=True,callback_continuation_registered=False,handwritten_Session_initerm_execution_credit=False,old_exact_slice_mapping_withheld=True,new_full_literal_RX_page_owner=0x78001000)

def composition_derivative(prep):
 old=R.text(OLD/'composition.cpp');new=R.text(prep/'composition.cpp')
 expected=old
 replacements=[
  ('#include "control_context.hpp"','#include "control_context.hpp"\n#include "initterm_context.hpp"'),
  ('namespace ci=mw34::m4_crt_control_integration;','namespace ci=mw34::m4_crt_control_integration;\nnamespace nt=mw34::m4_crt_entry_initerm;'),
  ('#include "control_binding.inc"','#include "control_binding.inc"\n#include "initterm_binding.inc"'),
  ('address==matherr_pages[0]?0x60000000U','(address==matherr_pages[0]||address==0x78001000)?0x60000000U'),
  ('if(matherr_binding&&matherr_binding->control==17&&s_.gpr.rip.dword==0x5ac423)r_.memory().store<unsigned>({a},v^1);','if(matherr_binding&&matherr_binding->control==17&&s_.gpr.rip.dword==0x5ac423)r_.memory().store<unsigned>({a},v^1);if(initterm_binding&&initterm_binding->control==47&&s_.gpr.rip.dword==0x5ac43b)r_.memory().store<unsigned>({a},v^1);'),
  ('std::array<std::array<unsigned,3>,4>calls','std::array<std::array<unsigned,3>,5>calls'),
  ('{0x5ac428,0x5bb50c,0x5ac42e}}}','{0x5ac428,0x5bb50c,0x5ac42e},{0x5ac468,0x5bb514,0x5ac46e}}}'),
 ]
 for a,b in replacements:expected=once(expected,a,b)
 # Inspect complete dispatcher lines rather than trusting a selective string diff.
 nt_bodies={
 '__remill_read_memory_32':'if(nt::owner){require(p==nt::owner&&!ci::owner&&!mn::owner,"Exact current initterm read token");return nt::owner->read(a);}',
 '__remill_write_memory_32':'if(nt::owner){require(p==nt::owner&&!ci::owner&&!mn::owner,"Exact current initterm write token");nt::owner->write(a,v);return p;}',
 '__remill_function_call':'if(nt::owner){require(p==nt::owner&&!ci::owner&&!mn::owner,"Exact current initterm callback token");nt::owner->called(s,a);return p;}',
 '__remill_function_return':'if(nt::owner){require(p==nt::owner&&!ci::owner&&!mn::owner,"Exact current initterm return token");nt::owner->returned(s,a);return p;}',
 '__remill_jump':'if(nt::owner){require(p==nt::owner&&!ci::owner&&!mn::owner,"Exact current initterm jump token");nt::owner->tail(s,a);return p;}',
 'mw34_crte_enter':'if(nt::owner){require(p==nt::owner&&!ci::owner&&!mn::owner,"Exact current initterm thunk-enter token");nt::owner->enter(s,a);return p;}',
 }
 for symbol,prefix in nt_bodies.items():
  lines=[l for l in expected.splitlines()if 'extern "C"'in l and symbol+'('in l];R.need(len(lines)==1,'One ancestor bridge '+symbol)
  line=lines[0];expected=once(expected,line,line.replace('{','{'+prefix,1))
 expected=expected.replace('&&!mn::owner,"Exact current control','&&!mn::owner&&!nt::owner,"Exact current control').replace('&&!ci::owner&&!mn::owner,"Exact active entry','&&!ci::owner&&!mn::owner&&!nt::owner,"Exact active entry')
 suffix='extern "C" unsigned char mw34_entry_initerm_undefined_8() noexcept(false){require(nt::owner&&!ci::owner&&!mn::owner,"Exact current initterm undefined owner");return nt::owner->undefined();}\nnamespace mw34::m4_crt {void compiled_initterm(m4_runtime::Runtime&r){::initterm_provider_adapter(r);}}\n'
 expected=once(expected,'#include "main_v2.inc"',suffix+'#include "main_v2.inc"')
 R.need(new==expected,'Entire composition equals unchanged ancestor plus explicitly audited additive integration')
 R.need('construct_at'not in new and 'std::memcpy(r.fx()'not in new,'No persistent State/FX reset in new borrower')
 for symbol in nt_bodies:
  line=[l for l in new.splitlines()if 'extern "C"'in l and symbol+'('in l][0]
  R.need('noexcept(false)'in line and 'p==nt::owner'in line and 'static_cast'not in line,'Exact typed token before cast '+symbol)
 R.check('Whole production composition derivative and typed global bridge dispatch',old_composition_sha256=R.sha(OLD/'composition.cpp'),candidate_composition_sha256=R.sha(prep/'composition.cpp'),complete_ancestor_control_matherr_entry_helpers_unchanged=True,additive_current_initterm_dispatchers=len(nt_bodies),encompassing_host_FX_legacy_ENV_guard_unchanged=True,actual_next_source_CALL=0x5ac468,source_next_raw_target=0x1ded02)

def context_contract(prep):
 context=R.text(prep/'initterm_context.hpp');binding=R.text(prep/'initterm_binding.inc');main=R.text(prep/'main_v2.inc');obs=R.text(prep/'observations.hpp')
 R.need('state(*reinterpret_cast<State*>(r.remill_state().data()))'in context,'Persistent State borrowed directly')
 R.need('owner!=this||!active||failed||thread!=std::this_thread::get_id()'in context,'Exact current active serial owner guard')
 R.need('pc==0x7800150e&&a==state.gpr.rsp.dword-4&&v==0x78001510'in context,'Callback checked store uses pre-publication current ESP-4')
 R.need('pc==0x78001508&&a==begin'in context and 'pc==0x78001512&&a==frame-4'in context and 'pc==0x78001513&&a==frame'in context,'Exact reached table/POP/RET operand addresses')
 R.need('pc==0x780014f9&&a==state.gpr.rsp.dword+8&&stack(a)'in context and 'pc==0x78001502&&a==state.gpr.rsp.dword+12&&stack(a)'in context,'Actual dynamic source argument addresses')
 R.need('deny("Required initterm callback remains unreviewed",target,0x7800150e)'in context and 'runtime.call_direct'not in context,'Reached callback is terminal without successful callback/continuation credit')
 R.need('jump' in context and '86127a1a5240eff849fe402fc8517ae3ead7498476c8f17188afd36be6060947'in context and '960ed0d00b0200736930590a16fbb3caa9c3bc24af9851a3728258fd9b340678'in context,'Whole actual thunk/provider source identity checks')
 R.need('r.memory().read({0x5e0000},table)'in binding and 'table==b.table&&page==b.provider_page'in binding,'Whole literal table/provider integrity before provider entry')
 R.need('runtime.cpu()=m4_crt_control_integration::cpu_view(state);runtime.cpu().esp=frame+4;runtime.cpu().eip=thunk;'in binding and 'runtime.call_import({slot},{ret})'in binding,'Actual existing CALL word supervised with caller ESP convention')
 view=R.text(prep/'control_context.hpp')
 actual=re.search(r'inline m4_runtime::Cpu32 cpu_view\(const State&s\)\{(.*?)\}',view).group(1)
 projection=re.search(r'Cpu32 cpu\(const State&s\)\{(.*?)\}',R.text(prep/'composition.cpp')).group(1)
 R.need(actual==projection,'Declared borrowed CPU view is identical to outer State projection')
 R.need('c.test_before_execute=&initterm_before;c.test_after_access=&initterm_access;c.test_after_event=&initterm_event;'in binding,'Actual provider hooks connected before native source execution')
 R.need('if(c.boundary_depth)--c.boundary_depth;c.active=false;nt::owner=nullptr;initterm_checkpoint(r,"initterm-thunk-after")'in binding,'All outer failure ownership cleared before observer checkpoint')
 R.need('catch(const nt::BridgeAbort&){--c.boundary_depth;throw std::runtime_error'in binding,'Nested BridgeAbort converted only after boundary-depth cleanup')
 R.need('catch(const nt::BridgeAbort&){if(c.boundary_depth)--c.boundary_depth;c.active=false;nt::owner=nullptr;'in binding,'Thunk BridgeAbort closure clears exact ownership')
 R.need('if(initterm_binding->extra_after)initterm_binding->extra_after(c)'in binding,'Independent after-completion observer exception seam available')
 R.need('c.first==nt::begin&&c.last==nt::end'in binding,'Only actual null-only first interval admitted')
 R.need('extern "C" bool data_boundary_initialize(Job*j) noexcept {\n InvocationHostBoundary host;\n try {'in main,'Full host preservation includes outer C++ final catches')
 R.need(main.count('seed(r,in)')==1 and 'State and distinct FX without reseed'in main,'Only input BEFORE seed; borrowers preserve full State/FX')
 R.need('r.memory().map({0x78001000},4096,Permissions::read|Permissions::write)'in main and 'r.memory().protect({0x78001000},Permissions::read|Permissions::execute)'in main,'New literal raw provider page protected RX')
 R.need('Already admitted complete literal game table page; no remap'in binding and '.map('not in binding,'Existing game table checked without remap')
 pages=re.search(r'composition_pages\{([^}]+)\}',obs);R.need(pages,'Complete checkpoint page union')
 page_values=[int(v,16)for v in re.findall(r'0x[0-9a-f]+',pages[1])]
 ancestor=R.text(OLD/'observations.hpp');oldpages=[int(v,16)for v in re.findall(r'0x[0-9a-f]+',re.search(r'composition_pages\{([^}]+)\}',ancestor)[1])]
 R.need(page_values==oldpages+[0x5e0000,0x78001000] and len(set(page_values))==16,'Exactly old fourteen pages plus borrowed table and literal provider page')
 R.need('initterm-thunk.bin'in obs and 'initterm-provider.bin'in obs,'Additional actual source bytes captured')
 R.need(all(word not in context+binding for word in('setjmp','longjmp','construct_at','memset(')),'No standalone longjmp or borrower reset')
 R.check('Exact new provider operands, no-reseed ownership and full exception closure',pages=page_values,State_bytes=3504,separate_FX_bytes=512,all_integer_FP_State_FX_metadata_carry=True,typed_callbacks_terminal=True,callback_continuation_admitted=False,checked_store_before_ESP_in_PUSH_and_CALL=True,POP_ESP_before_checked_read=True,RET_partial_State_publication_before_return_validation=True,owner_cleared_before_failure_observer=True)

def maps(build):
 n=0
 for key in('sources','tools','libraries','entry_objects','compiler_read_headers','artifacts'):
  for p,h in build.get(key,{}).items():R.pin(p,h);n+=1
 return n

def compiled_association(out,prep,bp,build):
 provider=ROOT/'reports/m4-crt-entry-initterm/provider-preparation-r3';report=R.read(provider/'report.json');R.pin(provider/'host.ll',report['host_sha256'])
 R.need(report['passed']and len(report['layouts'])==34 and report['layouts']['struct.State']['size']==3504,'Actual whole provider source layout preparation')
 host=R.text(provider/'host.ll');guest=R.text(provider/'guest.ll');R.need('nounwind'not in host and 'willreturn'not in host,'Provider bridged C++ unwind allowed')
 guestbody=re.search(r'^define.*@sub_780014f8.*?\n\}',guest,re.M|re.S).group(0)
 hostbody=re.search(r'^define.*@sub_780014f8.*?\n\}',host,re.M|re.S).group(0)
 R.need(hostbody==guestbody.replace('@__remill_undefined_8()','@mw34_entry_initerm_undefined_8()'),'Entire new provider source function body preserved except isolated undefined-AF bridge name')
 lift=[c for c in report['commands']if c['program'].endswith('remill-lift-control-21.exe')]
 R.need(len(lift)==1 and '--bytes='+ (provider/'source.bin').read_bytes().hex()in lift[0]['arguments']and '--entry_address='+str(0x780014f8)in lift[0]['arguments']and lift[0]['exit_code']==0,'Actual complete source-byte to lifted CFG command association')
 R.pin(lift[0]['program'])
 binaries=[];headers=0
 for level in('O0','O2'):
  obj=provider/f'provider-{level}.obj';R.pin(obj,build['entry_objects'][str(obj)])
  commands=[c for c in report['commands']if str(obj)in c['arguments']]
  R.need(len(commands)==1 and commands[0]['exit_code']==0 and '-'+level in commands[0]['arguments']and str(provider/'host.ll')in commands[0]['arguments'],'Provider source/compiler/COFF command association')
  R.pin(commands[0]['program'])
  info=R.run(out,[R.LLVM/'llvm-readobj.exe','--file-headers','--symbols','--relocations','--unwind',obj],level+'-provider-coff.txt')
  decoded=R.run(out,[R.LLVM/'llvm-objdump.exe','-d','-r','--x86-asm-syntax=intel',obj],level+'-provider-body.txt')
  R.need('IMAGE_FILE_MACHINE_AMD64'in info and 'RuntimeFunction'in info,'Provider is actual AMD64 native COFF with unwind')
  for sym in('sub_780014f8','__remill_read_memory_32','__remill_write_memory_32','__remill_function_call','__remill_function_return','mw34_entry_initerm_undefined_8'):
   R.need(sym in info and sym in decoded,'Actual source provider body and checked bridge '+sym)
  cc=R.read(bp.parent/level/'compile_commands.json')
  for name in('composition.cpp','crt_services.cpp'):
   c=[v for v in cc if Path(v['file']).name==name];R.need(len(c)==1 and Path(c[0]['file']).resolve()==prep/name,'Production source compilation '+name)
   command=c[0]['command'];R.need('/EHs 'in command and '/EHsc'not in command,'External C throwing bridges compiled without nounwind assumption')
  candidates=list((bp.parent/level/'CMakeFiles').rglob('composition.cpp.obj'));R.need(len(candidates)==1,'Exactly one production composition COFF')
  production=candidates[0];R.pin(production)
  pi=R.run(out,[R.LLVM/'llvm-readobj.exe','--file-headers','--symbols','--relocations','--unwind',production],level+'-production-coff.txt')
  R.need('IMAGE_FILE_MACHINE_AMD64'in pi and '__CxxFrameHandler'in pi,'Actual compiled production C++ exception unwind handler')
  for symbol in('compiled_initterm','initterm_thunk_adapter','sub_780014f8','mw34_entry_initerm_undefined_8','__remill_function_call','__remill_function_return'):
   R.need(symbol in pi,'Actual production defined service and guarded bridges '+symbol)
  if level=='O0':R.need('initterm_provider_adapter'in pi,'O0 retains provider adapter definition')
  if level=='O2':R.need('$cppxdata$?compiled_initterm'in pi and re.search(r'IMAGE_REL_AMD64_REL32 sub_780014f8',pi),'O2 inlines provider adapter into typed compiled service with actual provider relocation and C++ unwind')
  consumed=set(re.findall(r'Note: including file:\s*(.+?)\s*$',R.text(bp.parent/f'build-{level}.log'),re.M))
  R.need(consumed,'Actual consumed header associations')
  for p in consumed:R.pin(p.strip());headers+=1
  R.need(any(p.replace('\\','/').endswith('/remill/Arch/X86/Runtime/State.h')for p in consumed),'Actual State.h consumed by composition')
  for name in('initterm_context.hpp','initterm_binding.inc','main_v2.inc','crt_services.hpp'):
   R.need(any(Path(p.strip()).resolve()==prep/name for p in consumed),'Actual additive source header consumed '+name)
  binaries.extend([dict(level=level,path=str(obj),sha256=R.sha(obj),kind='Full actual new source provider'),dict(level=level,path=str(production),sha256=R.sha(production),kind='Production typed bridges and C++ exception closure')])
 R.check('Actual new provider and production AMD64 compiler/header/unwind associations',objects=binaries,compiler_read_header_associations=headers,complete_provider_body_preserved=True,old_game_thunk_object_reused=True,State_header_compiled=True,process_file_open_attested=False)

def main():
 R.need(len(sys.argv)==4,'final.py fresh-report-directory preparation-directory build-json')
 out,prep,bp=map(lambda s:Path(s).resolve(),sys.argv[1:]);R.need(out.parent==BASE and out.name.startswith('independent-source-')and not out.exists(),'Fresh isolated source closure');out.mkdir(parents=True)
 (out/'final.py').write_bytes(Path(__file__).read_bytes());R.pin(out/'final.py')
 try:
  for rel,want in R.FROZEN.items():R.pin(ROOT/rel,want)
  build=R.read(bp);R.need(build['passed'],'Completed candidate build');count=maps(build)
  frozen_components(prep,build);session_derivative(prep);composition_derivative(prep);context_contract(prep);compiled_association(out,prep,bp,build)
  R.pin(BASE/'independent-source-r1/report.json','793113c1cd1c90e569aac9e32433c2c2ce17a96d1b426d05c47a9ddabcc7680e');R.pin(BASE/'independent-source-r1/pins.json','1505b4e2bee4179cf60f1b6d75d3f8e3239f462f0ad58c6a4b0852ef012b61dd')
  report=dict(passed=True,scope='Independent exact candidate source/build/header/COFF association closure; root BEFORE-only scalar proof and independent actual compiled causal/hardware evidence remain separate',build_path=str(bp),build_sha256=R.sha(bp),preparation_path=str(prep/'report.json'),checks=R.CHECKS,commands=R.COMMANDS,physical_bindings_rehashed=count,findings=[],ordinary_game_launched=False,full_CRT=False,native_menu=False,successful_initializer_callbacks=0,selected_initializer_count_unchanged=27,total_selected_initializers=144,whole_M4_complete=False)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');R.pin(out/'report.json');R.pin(Path(__file__));R.pin(HERE/'review.py')
  (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(R.PINS.items()))),indent=2)+'\n')
  print(json.dumps(dict(passed=True,files=len(R.PINS),checks=len(R.CHECKS),report=str(out/'report.json'),report_sha256=R.sha(out/'report.json'),pins_sha256=R.sha(out/'pins.json'))))
 except Exception:
  (out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main()
