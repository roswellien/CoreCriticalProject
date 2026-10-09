"""Read-only final literal source/derivative/build/COFF association review."""
import difflib, importlib.util, json, re, sys, traceback
from pathlib import Path
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('independent_mainargs_source',Path(__file__).with_name('review.py'))
R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
ROOT,BASE=R.ROOT,R.BASE
OLD=ROOT/'reports/m4-crt-entry-initterm/preparation-r3'
CHECKS=[]
def text(p):return R.pin(p).read_text(encoding='utf-8-sig')
def read(p):return json.loads(text(p))
def check(name,**facts):CHECKS.append(dict(name=name,passed=True,**facts))
def once(s,a,b):R.need(s.count(a)==1,'Exact derivative anchor '+a[:100]);return s.replace(a,b)
def frozen(prep,build):
 old=read(ROOT/'reports/m4-crt-entry-initterm/build-r3/build.json')
 names=['seed.hpp','matherr_context.hpp','control_context.hpp','control_binding.inc','initterm_context.hpp','initterm_binding.inc','crt_services.cpp','crt_services.hpp']
 for n in names:R.need(text(prep/n)==text(OLD/n),'Whole predecessor retained '+n)
 R.need(text(ROOT/'tools/m4-crt-entry-mainargs/capture.s')==text(ROOT/'tools/m4-crt-entry-initterm/capture.s'),'Encompassing raw FX/full legacy host capture unchanged')
 objects=[]
 for p,h in old['entry_objects'].items():R.need(build['entry_objects'].get(p)==h,'Frozen compiled object exact reuse');R.pin(p,h);objects.append(dict(path=p,sha256=h))
 for p,h in old['libraries'].items():R.need(build['libraries'].get(p)==h,'Frozen registry library exact reuse');R.pin(p,h)
 check('Whole frozen components and Session mapping/publication seam unchanged',sources=names,objects=objects,old_Runtime_modified=False,old_callback_bodies_modified=False,old_global_mapping_bytes=12)
def composition(prep,out):
 new=text(prep/'composition.cpp');old=text(OLD/'composition.cpp');s=new
 s=once(s,'#include "initterm_context.hpp"\n#include "mainargs_context.hpp"','#include "initterm_context.hpp"')
 s=once(s,'namespace nt=mw34::m4_crt_entry_initerm;\nnamespace mg=mw34::m4_crt_entry_mainargs;','namespace nt=mw34::m4_crt_entry_initerm;')
 s=once(s,'#include "initterm_binding.inc"\n#include "mainargs_binding.inc"','#include "initterm_binding.inc"')
 prefixes={
 '__remill_read_memory_32':'if(mg::owner){if(p!=mg::owner||nt::owner||ci::owner||mn::owner)mg::owner->deny("Exact current mainargs read token",a);return mg::owner->read(a);}',
 '__remill_write_memory_32':'if(mg::owner){if(p!=mg::owner||nt::owner||ci::owner||mn::owner)mg::owner->deny("Exact current mainargs write token",a);mg::owner->write(a,v);return p;}',
 '__remill_function_call':'if(mg::owner){if(p!=mg::owner||nt::owner||ci::owner||mn::owner)mg::owner->deny("Exact current mainargs import token",a,mg::import_call);mg::owner->called(s,a);}',
 '__remill_function_return':'if(mg::owner){if(p!=mg::owner||nt::owner||ci::owner||mn::owner)mg::owner->deny("Exact current mainargs return token",a);mg::owner->deny("Required mainargs RET outside bounded prefix",a);}',
 }
 for sym,prefix in prefixes.items():
  line=[l for l in s.splitlines()if l.startswith('extern "C"')and sym+'('in l];R.need(len(line)==1,'Unique current token dispatcher '+sym);R.need(prefix in line[0],'Exact current exclusive typed prefix '+sym);s=once(s,prefix,'')
  R.need('p!=mg::owner||nt::owner||ci::owner||mn::owner'in prefix,'No cast or route before exact exclusive token')
 newbyte='extern "C" unsigned char __remill_read_memory_8(void*p,unsigned a) noexcept(false) {if(mg::owner){if(p!=mg::owner||nt::owner||ci::owner||mn::owner)mg::owner->deny("Exact current mainargs byte-read token",a);mg::owner->deny("Required mainargs byte read outside bounded prefix",a);}throw std::runtime_error("Unreached required byte-read bridge");}'
 oldbyte='extern "C" unsigned char __remill_read_memory_8(void*,unsigned) noexcept(false) {throw std::runtime_error("Unreached required byte-read bridge");}'
 s=once(s,newbyte,oldbyte)
 added={'sub_7800bbbc','sub_7800b3b4','sub_7800bc48','sub_780012b3','sub_7800badb','mw34_mainargs_normal_argv_undefined_8'}
 oldextern=[l for l in old.splitlines()if l.startswith('extern "C"')]
 lines=s.splitlines();kept=[];guards=0
 for l in lines:
  m=re.match(r'^extern "C".*?\b([A-Za-z0-9_]+)\(',l)
  if m and m[1]in added:
   R.need('!mg::owner'in l and 'nt::owner'in l and 'ci::owner'in l and 'mn::owner'in l,'Exclusive new helper wrapper '+m[1]);continue
  if l.startswith('extern "C"')and 'require(!mg::owner,"Other bridge cannot use active mainargs owner");'in l:l=l.replace('require(!mg::owner,"Other bridge cannot use active mainargs owner");','',1);guards+=1
  kept.append(l)
 reversed='\n'.join(kept)+'\n'
 reversed=once(reversed,'require(!mg::owner&&nt::owner&&!ci::owner&&!mn::owner,"Exact current initterm undefined owner");','require(nt::owner&&!ci::owner&&!mn::owner,"Exact current initterm undefined owner");')
 R.need(reversed==old,'Complete composition is exact old source plus audited additive new dispatch/wrappers')
 af=[l for l in new.splitlines()if l.startswith('extern "C"')and 'mw34_entry_initerm_undefined_8('in l];R.need(len(af)==1 and 'require(!mg::owner'in af[0],'Compact predecessor AF bridge cannot escape new owner priority')
 R.need('construct_at'not in new and 'std::memcpy(r.fx()'not in new,'No State/FX reset in new borrower')
 p=out/'complete-composition-diff.txt';p.write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(OLD/'composition.cpp'),tofile=str(prep/'composition.cpp'))));R.pin(p)
 check('Complete reversible additive production derivative and all current-owner dispatches',new_global_memory_dispatchers=5,new_helper_wrappers=len(added),guarded_old_extern_bridges=guards,original_entry_and_host_preservation_logic_retained=True)
def context(prep,out):
 c=text(prep/'mainargs_context.hpp');b=text(prep/'mainargs_binding.inc');main=text(prep/'main_v2.inc');obs=text(prep/'observations.hpp')
 for fragment in ['state(*reinterpret_cast<State*>(r.remill_state().data()))','owner!=this||!active||failed||thread!=std::this_thread::get_id()','0x7802e018','"GetModuleFileNameA"','"KERNEL32.dll"','word(offset(value,2))!=292','provider_raw!=0x343b0']:
  R.need(fragment in c,'New persistent State/current owner/provider metadata source authority '+fragment)
 original=read(BASE/'independent-contract-r1/report.json')
 for span in original['source_spans']:
  if span['label']in('mainargs','normal-builder'):R.need(span['sha256']in c,'Complete provider source identity '+span['label'])
 for fragment in ['pc==0x7800ba61&&a==frame+20','pc==0x7800ba64&&a==frame+16','pc==0x7800ba68&&a==startup_ptr','pc==import_call&&a==import_slot','pc==0x7800ba6a&&a==newmode&&value==loaded_startup','pc==internal_call?internal_return:0x7800ba76','pc==import_call&&a==f-36&&value==import_return']:
  R.need(fragment in c,'Actual source operand and partial order guard '+fragment)
 R.need(c.index('runtime.memory().store<unsigned>({a},value)')<c.index('if(pc==0x7800ba6a&&value!=0)'),'Nonzero source newmode store precedes admitted-domain failure')
 R.need('throw m4_runtime::Fault(m4_runtime::FaultReason::unresolved_import,{import_call},{import_slot},reason)'in c,'Public exact source provider-import fault; not remapped game metadata')
 R.need('runtime.call_import'not in c+b and 'runtime.call_direct'not in c+b and 'register_translation'not in c+b,'Provider internal/native OS routes not game Runtime routes')
 R.need('mw34_mainargs_normal_argv_body(&state,builder,this)'in b and 'mw34_mainargs_mainargs_body(&c.state,mg::entry,&c)'in b,'Full actual native source bodies invoked')
 R.need('access_count!=6'in b and 'accesses[5].pc!=internal_call'in b and 'runtime.memory().load<unsigned>({frame-8})!=internal_return'in b,'Actual direct CALL write/current frame checked before native builder')
 R.need('c.active=false;c.boundary_depth=0;mg::owner=nullptr;'in b and b.count('c.active=false;c.boundary_depth=0;mg::owner=nullptr;')==2,'Every outer C++ catch clears current owner/active/depth before observers')
 R.need('catch(...){--boundary_depth;mainargs_checkpoint(runtime,"mainargs-builder-after");throw;}'in b,'Nested failure decrements depth before checkpoint and unwinds through outer cleanup')
 R.need('source_identity();event(3,builder' in b and 'c.source_identity();c.event(1,mg::entry' in b,'Actual source identity after injected before-observer, not only constructor')
 for s in ('setjmp','longjmp','construct_at','memset('):R.need(s not in c+b,'No standalone reset/longjmp '+s)
 R.need('.map('not in b+c and '.unmap('not in b+c,'Current16-page owners borrowed without remap')
 R.need('r.register_service({{mg::slot},{Abi::Cdecl,20,true},&mainargs_adapter'in main,'Actual game import has exact Cdecl20 contract')
 R.need(main.count('seed(r,in)')==1,'Single original BEFORE seed only')
 for n in('argc_ptr','argv_ptr','env_ptr'):R.need('store<unsigned>({c.'+n+'}'not in b+c,'No fabricated mainargs output '+n)
 pages=lambda s:[int(x,16)for x in re.findall(r'0x[0-9a-f]+',re.search(r'composition_pages\{([^}]+)\}',s)[1])]
 R.need(pages(obs)==pages(text(OLD/'observations.hpp'))and len(set(pages(obs)))==16,'Identical complete16-page checkpoint union')
 R.need('mainargs-provider.bin'in obs and 'mainargs-builder.bin'in obs,'Exact new206-byte source identities captured')
 delta=out/'main-boundary-diff.txt';delta.write_text(''.join(difflib.unified_diff(text(OLD/'main_v2.inc').splitlines(True),main.splitlines(True))));R.pin(delta)
 check('New native provider typed source/frame/permission and exception contract',State_bytes=3504,separate_FX_bytes=512,checkpoint_pages=pages(obs),new_source_bytes=206,only_game_mainargs_generic_service=True,internal_provider_generic_Runtime_ledger=False,filename_import_success=False,outputs_initialized=False,actual_partial_CALL_frame_before_import_fault=True,source_PC_fault_distinct_from_stale_Runtime_CPU=True)
def association(prep,bp,build,out):
 source=BASE/'recovery-r3';report=read(source/'report.json');R.need(report['passed'],'Literal source recovery passed');parts=[]
 for name,entry,size in [('mainargs',0x7800ba5e,66),('normal_argv',0x7800bbbc,140)]:
  body=read(BASE/'independent-contract-r1/report.json')['source_spans'][1 if name=='mainargs'else 2]['sha256'];R.pin(source/(name+'-source.bin'),body)
  n=report['native'][name];host=text(source/(name+'-host.ll'));guest=text(source/(name+'-guest.ll'));R.need(R.sha(source/(name+'-host.ll'))==n['host_sha256']and n['layouts']['struct.State']['size']==3504 and len(n['layouts'])==34,'Provider exact full State layout/source association')
  symbol='mw34_mainargs_'+name+'_body'
  h=re.search(r'^define ptr @'+symbol+r'\(.*?\n\}',host,re.M|re.S).group(0)
  g=re.search(r'^define ptr @sub_'+format(entry,'x')+r'\(.*?\n\}',guest,re.M|re.S).group(0)
  expected=g.replace('@sub_'+format(entry,'x')+'(', '@'+symbol+'(')
  if name=='normal_argv':expected=expected.replace('@__remill_undefined_8()','@mw34_mainargs_normal_argv_undefined_8()')
  R.need(h==expected,'Complete source body preserved except isolated symbol derivative '+name)
  R.need(not re.search(r'\b(nounwind|willreturn)\b',host),'Provider permits checked C++ bridge unwind')
  lifts=[x for x in report['commands']if '--ir_out='+str(source/(name+'-guest.ll'))in x['arguments']];R.need(len(lifts)==1 and lifts[0]['exit_code']==0 and '--entry_address='+str(entry)in lifts[0]['arguments']and '--bytes='+(source/(name+'-source.bin')).read_bytes().hex()in lifts[0]['arguments'],'Original bytes to complete lifted CFG command association')
  for level in('O0','O2'):
   obj=source/(name+'-'+level+'.obj');R.pin(obj,build['entry_objects'][str(obj)])
   commands=[x for x in report['commands']if str(obj)in x['arguments']and '-c'in x['arguments']];R.need(len(commands)==1 and commands[0]['exit_code']==0 and '-'+level in commands[0]['arguments']and str(source/(name+'-host.ll'))in commands[0]['arguments'],'Actual source LLVM compile O0/O2 '+name)
   info=R.run(out,[R.LLVM/'llvm-readobj.exe','--file-headers','--symbols','--relocations','--unwind',obj],level+'-'+name+'-coff')
   dis=R.run(out,[R.LLVM/'llvm-objdump.exe','-d','-r','--x86-asm-syntax=intel',obj],level+'-'+name+'-body')
   R.need('IMAGE_FILE_MACHINE_AMD64'in info and 'RuntimeFunction'in info,'Actual AMD64 COFF source with unwind')
   for sym in(symbol,'__remill_read_memory_32','__remill_write_memory_32'):
    R.need(sym in info and sym in dis,'Actual provider and required checked bridge '+sym)
   if name=='mainargs':R.need('sub_7800bbbc'in info and re.search(r'IMAGE_REL_AMD64_REL32 sub_7800bbbc',info),'Actual direct source nested helper relocation')
   if name=='normal_argv':R.need('__remill_function_call'in info and '__remill_function_call'in dis,'Actual IAT CALL native bridge relocation')
   parts.append(dict(level=level,source_function=symbol,object=str(obj),sha256=R.sha(obj)))
 for level in('O0','O2'):
  cc=read(bp.parent/level/'compile_commands.json')
  for name in('composition.cpp','crt_services.cpp'):
   cs=[x for x in cc if Path(x['file']).name==name];R.need(len(cs)==1 and Path(cs[0]['file']).resolve()==prep/name and '/EHs 'in cs[0]['command']and '/EHsc'not in cs[0]['command'],'Actual source compiled with external C++ bridge unwind '+name)
  objs=list((bp.parent/level/'CMakeFiles').rglob('composition.cpp.obj'));R.need(len(objs)==1,'Exactly one native production COFF');obj=R.pin(objs[0]);info=R.run(out,[R.LLVM/'llvm-readobj.exe','--file-headers','--symbols','--relocations','--unwind',obj],level+'-composition-coff')
  R.need('IMAGE_FILE_MACHINE_AMD64'in info and '__CxxFrameHandler'in info,'Actual production AMD64 C++ exception/unwind closure')
  for sym in('mainargs_adapter','sub_7800bbbc','mw34_mainargs_mainargs_body','mw34_mainargs_normal_argv_body','__remill_function_call'):
   R.need(sym in info,'Actual typed production adapter and native source association '+sym)
  includes=set(p.strip()for p in re.findall(r'Note: including file:\s*(.+?)\s*$',text(bp.parent/('build-'+level+'.log')),re.M));R.need(includes,'Actual compiler include associations')
  for name in('mainargs_context.hpp','mainargs_binding.inc','initterm_context.hpp','main_v2.inc'):
   R.need(any(Path(p).resolve()==prep/name for p in includes),'Compiler consumed exact new/old header '+name)
  R.need(any(p.replace('\\','/').endswith('/remill/Arch/X86/Runtime/State.h')for p in includes),'Actual full State.h consumed')
  ninja=text(bp.parent/level/'build.ninja');R.need('mainargs-'+level+'.obj'in ninja and 'normal_argv-'+level+'.obj'in ninja,'Actual provider objects linked to worker')
  R.need('/force:multiple'not in ninja.lower(),'No duplicate-symbol resolution substitution')
  parts.append(dict(level=level,object=str(obj),sha256=R.sha(obj),kind='Production source body/bridges'))
 check('Complete new source derivative and actual AMD64 compiler/header/COFF/unwind linkage',components=parts,full_source_functions_preserved=True,process_file_open_attested=False)
def main(prep_name,build_name,out_name):
 prep=BASE/prep_name;bp=BASE/build_name/'build.json';out=BASE/out_name;R.need(out.parent==BASE and out_name.startswith('independent-contract-')and not out.exists(),'New review output only');out.mkdir(parents=True)
 try:
  for p,h in R.FROZEN.items():R.pin(ROOT/p,h)
  build=read(bp);pr=read(prep/'report.json');R.need(build['passed']and pr['passed']and build['preparation_sha256']==R.sha(prep/'report.json'),'Stable candidate source/build association')
  count=0
  for key in('sources','tools','libraries','entry_objects','compiler_read_headers','artifacts'):
   for p,h in build.get(key,{}).items():R.pin(p,h);count+=1
  for p,h in read(prep/'pins.json')['files'].items():R.pin(p,h)
  frozen(prep,build);composition(prep,out);context(prep,out);association(prep,bp,build,out);R.pin(Path(__file__))
  report=dict(passed=True,scope='Independent read-only complete-source derivative, typed provider stop, compiler/header/AMD64 COFF/unwind association audit; no native execution',build_path=str(bp),build_sha256=R.sha(bp),preparation_sha256=R.sha(prep/'report.json'),physical_build_bindings_checked=count,checks=CHECKS,commands=R.COMMANDS,files=R.PINS,actual_new_source_bytes=206,unchanged_16page_carry=True,argc_argv_environment_initialized=False,filename_service_success=False,ordinary_game_launched=False,native_executed=False,whole_M4_complete=False)
 except Exception as e:report=dict(passed=False,error=str(e),traceback=traceback.format_exc(),checks=CHECKS,commands=R.COMMANDS,files=R.PINS)
 rp=out/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');R.pin(rp);(out/'pins.json').write_text(json.dumps(dict(files=R.PINS),indent=2)+'\n');print(json.dumps(dict(passed=report['passed'],report=str(rp),report_sha256=R.sha(rp),bindings=len(R.PINS),error=report.get('error'))));return 0 if report['passed']else 1
if __name__=='__main__':raise SystemExit(main(*sys.argv[1:]))
