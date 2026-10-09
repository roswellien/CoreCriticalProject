"""Independent exact derivative and compiled association audit.

The source contract, root scalar composition observer and independent actual
compiled causal/hardware fixture each supply distinct, bounded evidence.
"""
import importlib.util, json, re, sys, traceback
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('own_frozen_control_source_review',HERE/'review.py')
R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
ROOT,BASE=R.ROOT,R.BASE

def once(s,a,b):
 R.need(s.count(a)==1,'Independent exact derivative anchor: '+a)
 return s.replace(a,b)

def context_derivative(prep):
 original=ROOT/'tools/m4-crt-control-integration/native_context.hpp'
 old=R.text(original);target=R.text(prep/'control_context.hpp')
 tail='extern "C" unsigned __remill_read_memory_32(void*p,unsigned a){'
 R.need(old.count(tail)==1,'Historical standalone global bridge tail')
 expected=old.split(tail)[0]
 replacements=[
  ('#include "common.hpp"','#include "'+(ROOT/'tools/m4-crt-control-integration/common.hpp').as_posix()+'"'),
  ('#include <csetjmp>','#include <thread>'),
  ('extern "C" void*sub_5ac5a0(State*,unsigned,void*);','extern "C" void*sub_5ac5a0(State*,unsigned,void*) noexcept(false);'),
  ('extern "C" void*sub_780042e1(State*,unsigned,void*);','extern "C" void*sub_780042e1(State*,unsigned,void*) noexcept(false);'),
  ('struct Context{','struct BridgeAbort {};\nstruct Access{unsigned pc,address,value,width,write;};\nstruct Context{'),
  ('std::array<std::jmp_buf,4>boundaries{};unsigned boundary_depth{};bool failed{};const char*reason{};unsigned fault_pc{};',
   'unsigned boundary_depth{};bool active{},failed{},complete{};const char*reason{};unsigned fault_pc{},fault_address{};std::thread::id thread=std::this_thread::get_id();\n std::array<Access,256>accesses{};unsigned access_count{};\n void(*test_before_execute)(Context&,unsigned){};void(*test_after_access)(Context&,unsigned){};void(*test_after_event)(Context&,unsigned){};'),
  ('[[noreturn]]void deny(const char*w){if(!failed){failed=true;reason=w;fault_pc=state.gpr.rip.dword;}if(!boundary_depth)throw std::runtime_error(reason);std::longjmp(boundaries[boundary_depth-1],1);}',
   '[[noreturn]]void deny(const char*w,unsigned address=0){if(!failed){failed=true;reason=w;fault_pc=state.gpr.rip.dword;fault_address=address;}throw BridgeAbort{};}\n void guard(){if(owner!=this||!active||failed||thread!=std::this_thread::get_id())deny("Exact active serial control owner required");}\n void access(unsigned address,unsigned value,unsigned width,unsigned write){guard();if(access_count==accesses.size())deny("Control access bound",address);accesses[access_count++]={state.gpr.rip.dword,address,value,width,write};if(test_after_access)test_after_access(*this,access_count);'),
  ('unsigned read32(unsigned a){if(a!=slot','unsigned read32(unsigned a,bool observed=false){guard();if(a!=slot'),
  ('if(bad)deny("Required checked32-bit read fault");return v;','if(bad)deny("Required checked32-bit read fault",a);if(observed)access(a,v,4,0);return v;'),
  ('void write32(unsigned a,unsigned v){if(!stack','void write32(unsigned a,unsigned v){guard();if(!stack'),
  ('if(bad)deny("Required checked32-bit write fault");}','if(bad)deny("Required checked32-bit write fault",a);access(a,v,4,1);}'),
  ('events[count++]={kind,pc,esp,ret};}','events[count++]={kind,pc,esp,ret};if(test_after_event)test_after_event(*this,count);}'),
  ('void state_identity(State*s,unsigned pc){if(','void state_identity(State*s,unsigned pc){guard();if('),
  ('void wait(State*s,unsigned pc){const auto&f=','void wait(State*s,unsigned pc){guard();const auto&f='),
 ]
 # The access callback addition remains a single method body after reversal.
 replacements[6]=(replacements[6][0],replacements[6][1]+'}')
 for old_text,new_text in replacements:expected=once(expected,old_text,new_text)
 begin=expected.index(' void execute(unsigned entry){');end=expected.index('\n void tail(',begin)
 execute=''' void execute(unsigned entry){
  const bool outer=boundary_depth==0;if((entry!=wrapper&&entry!=provider_entry)||failed||boundary_depth==4||thread!=std::this_thread::get_id()||owner!=this||(outer?active:!active))throw std::runtime_error(reason?reason:"Connected boundary admission rejected");
  ++boundary_depth;if(outer)active=true;
  try{if(test_before_execute)test_before_execute(*this,entry);void*result=(entry==wrapper?sub_5ac5a0:sub_780042e1)(&state,entry,this);if(result!=this)deny("Connected compiled entry result identity rejected");}
  catch(BridgeAbort const&){--boundary_depth;if(outer)active=false;throw std::runtime_error(reason);}
  catch(...){--boundary_depth;if(outer)active=false;throw;}
  --boundary_depth;if(outer){active=false;complete=!failed&&depth==0;}if(failed)throw std::runtime_error(reason);
 }
'''
 expected=expected[:begin]+execute+expected[end:]
 expected=re.sub(r'\bsub_5ac5a0\b','mw34_entry_control_sub_5ac5a0',expected)
 R.need(target==expected,'Entire control Context derivative differs only by audited typed guards, logs and C++ exception closure')
 R.need('longjmp'not in target and 'setjmp'not in target and 'construct_at'not in target and 'memset'not in target,'No longjmp or State reseed')
 R.check('Whole derivative reverses to historical control Context outside declared exception/token/observation repairs and wrapper symbol namespace',derivative_changes=len(replacements)+3,State_reseed=False,guest_FX_reset=False,CW_transfer_unchanged=True,source_callframe_supervisor_unchanged=True,CXX_BridgeAbort=True)

def IR_derivative(prep):
 old=R.text(ROOT/'reports/m4-crt-control-integration/research-r1/host.ll')
 target=R.text(prep/'control.ll')
 symbols=('sub_5ac5a0','sub_5ac5d6','__remill_flag_computation_zero','__remill_flag_computation_sign','__remill_undefined_8','__remill_compare_eq','__remill_compare_neq','__remill_flag_computation_carry','__remill_flag_computation_overflow')
 expected=old
 for symbol in symbols:expected=re.sub(r'(?<![A-Za-z0-9_.])'+re.escape(symbol)+r'(?![A-Za-z0-9_.])','mw34_entry_control_'+symbol,expected)
 R.need(target==expected,'Entire candidate control IR differs only by exact nine symbol namespace changes')
 reverse=target
 for symbol in symbols:reverse=re.sub(r'(?<![A-Za-z0-9_.])mw34_entry_control_'+re.escape(symbol)+r'(?![A-Za-z0-9_.])',symbol,reverse)
 R.need(reverse==old,'Exact full reverse IR equals accepted compiled source')
 definitions=set(re.findall(r'^define\s+[^@]*@([^ (]+)',target,re.M))
 for root in ('sub_780042e1','sub_780042f7','sub_7800432c','sub_7800439f'):R.need(root in definitions,'All actual provider bodies unchanged '+root)
 R.check('Control IR complete reversal preserves all guest source semantics and external bridge ABIs',exact_symbol_mapping={s:'mw34_entry_control_'+s for s in symbols},provider_bodies_unchanged=True,bridges_unchanged=True,complete_old_IR_sha256=R.sha(ROOT/'reports/m4-crt-control-integration/research-r1/host.ll'),candidate_IR_sha256=R.sha(prep/'control.ll'),old_control_COFF_reused=False)

def receipt_maps(build):
 count=0
 for key in ('sources','source_files','tools','tool_files','libraries','entry_objects','matherr_objects','control_objects','compiler_read_headers','artifacts'):
  for p,h in build.get(key,{}).items():R.pin(p,h);count+=1
 return count

def inspect_objects(out,build,bp,prep):
 objects=[];headers=0
 for level in ('O0','O2'):
  p=bp.parent/f'control-{level}.obj'
  R.pin(p,build['entry_objects'][str(p)])
  llc=[c for c in build['commands']if Path(c['program']).name=='llc.exe'and str(p)in c['arguments']]
  R.need(len(llc)==1 and llc[0]['exit_code']==0 and '-'+level in llc[0]['arguments'] and str(prep/'control.ll')in llc[0]['arguments'],'Exact candidate control IR/compiler/object command association')
  decoded=R.run(out,[R.LLVM/'llvm-objdump.exe','-d','-r','--x86-asm-syntax=intel','--print-imm-hex',p],level+'-control.txt')
  info=R.run(out,[R.LLVM/'llvm-readobj.exe','--file-headers','--symbols','--relocations','--unwind',p],level+'-control-coff.txt')
  for symbol in ('mw34_entry_control_sub_5ac5a0','mw34_entry_control_sub_5ac5d6','sub_780042e1','sub_780042f7','sub_7800432c','sub_7800439f','mw34_cf_store_cw','mw34_cf_load_cw','__remill_jump'):
   R.need(symbol in info and symbol in decoded,'Actual candidate control body/bridge: '+symbol)
  R.need('IMAGE_FILE_MACHINE_AMD64' in info and 'RuntimeFunction' in info,'Actual AMD64 control object/unwind')
  objects.append(dict(level=level,path=str(p),sha256=R.sha(p),kind='exact source-semantic symbol-namespace derivative control guest body'))
  commands=R.read(bp.parent/level/'compile_commands.json')
  matches=[x for x in commands if x['file'].replace('\\','/').endswith('/composition.cpp')]
  R.need(len(matches)==1,'Exactly one production composition compiler command')
  command=matches[0]['command'];R.need('/EHs 'in command and '/EHsc'not in command,'Production extern C throwing bridge flags')
  candidates=list((bp.parent/level/'CMakeFiles').rglob('composition.cpp.obj'))
  R.need(len(candidates)==1,'Exactly one production composition object')
  obj=candidates[0];R.pin(obj)
  production=R.run(out,[R.LLVM/'llvm-readobj.exe','--file-headers','--symbols','--relocations','--unwind',obj],level+'-production-coff.txt')
  R.need('IMAGE_FILE_MACHINE_AMD64'in production and '__CxxFrameHandler'in production,'Actual production throwing boundary unwind handler')
  for symbol in ('mw34_cf_enter','mw34_cf_wait','mw34_cf_store_cw','mw34_cf_load_cw','mw34_ci_enter'):
   R.need(symbol in production,'Actual production owner bridge definition '+symbol)
  objects.append(dict(level=level,path=str(obj),sha256=R.sha(obj),kind='production typed boundaries'))
  log=R.text(bp.parent/f'build-{level}.log')
  consumed=set(re.findall(r'Note: including file:\s*(.+?)\s*$',log,re.M))
  R.need(consumed,'Actual compiler-read header associations')
  for p in consumed:R.pin(p.strip());headers+=1
 R.check('Fresh namespace derivative control objects and actual production exception/token bridge associations',objects=objects,actual_compiler_header_read_associations=headers)

def composition_contract(prep):
 new=R.text(prep/'composition.cpp')
 old=R.text(ROOT/'reports/m4-crt-entry-matherr/preparation-r3/composition.cpp')
 guard_begin='struct InvocationHostBoundary {'
 def host_scope(t):
  i=t.index(guard_begin);return t[i:t.index('\n};',i)+3]
 R.need(host_scope(new)==host_scope(old),'Accepted encompassing caller FP/ENV guard unchanged')
 main=R.text(prep/'main_v2.inc')
 R.need('extern "C" bool data_boundary_initialize(Job*j) noexcept {\n InvocationHostBoundary host;\n try {'in main,'Full outer host preservation includes final C++ catches')
 R.need('construct_at'not in new and 'std::memcpy(r.fx()'not in new,'Control borrowers have no State or FX reset')
 R.need('ci::owner' in new and 'p==ci::owner' in new,'Control typed token checks before dispatch')
 R.need('static_cast<ci::Context*>(p)'not in new,'No unguarded arbitrary control token cast')
 R.need('0x5ac440' in new and '0x5ac598' in new and '0x5ac445' in new,'Actual next CALL/frame source admitted to unresolved boundary')
 dispatch={
 '__remill_read_memory_32':'if(ci::owner){require(p==ci::owner&&!mn::owner,"Exact current control memory token");return ci::owner->read32(a,true);}if(mn::owner){require(p==mn::owner,"Exact current matherr memory token");return mn::owner->read(a);}require(owner&&p==owner,"Exact active entry memory token");return owner->read(a,4);',
 '__remill_write_memory_32':'if(ci::owner){require(p==ci::owner&&!mn::owner,"Exact current control write token");ci::owner->write32(a,v);return p;}if(mn::owner){require(p==mn::owner,"Exact current matherr memory token");mn::owner->write(a,v);return p;}require(owner&&p==owner,"Exact active entry memory token");owner->write(a,v);return p;',
 '__remill_function_return':'if(ci::owner){require(p==ci::owner&&!mn::owner,"Exact current control return token");ci::owner->returned(s,a);return p;}if(mn::owner){require(p==mn::owner,"Exact current matherr return token");mn::owner->returned(s,a);return p;}require(owner&&p==owner,"Exact active entry return token");return owner->returned(s,a);',
 '__remill_function_call':'require(owner&&p==owner&&!ci::owner&&!mn::owner,"Exact active entry call token");return owner->call(s,a);',
 '__remill_jump':'require(ci::owner&&p==ci::owner&&!mn::owner,"Exact current control jump token");ci::owner->tail(s,a);return p;',
 'mw34_ci_enter':'require(ci::owner&&p==ci::owner&&!mn::owner,"Exact current control game-enter token");ci::owner->game_enter(s,a);return p;',
 'mw34_cf_enter':'require(ci::owner&&p==ci::owner&&!mn::owner,"Exact current control provider-enter token");ci::owner->enter(s,a);return p;',
 'mw34_cf_wait':'require(ci::owner&&p==ci::owner&&!mn::owner,"Exact current control wait token");ci::owner->wait(s,a);return p;',
 'mw34_cf_store_cw':'require(ci::owner&&p==ci::owner&&!mn::owner,"Exact current control CW-store token");auto&c=*ci::owner;c.guard();if(!c.cw.store(s,{a}))c.deny("Required connected typed FNSTCW fault",a);c.access(a,c.memory.load<unsigned short>({a}),2,1);return p;',
 'mw34_cf_load_cw':'require(ci::owner&&p==ci::owner&&!mn::owner,"Exact current control CW-load token");auto&c=*ci::owner;c.guard();const auto v=c.memory.load<unsigned short>({a});if(!c.cw.load(s,{a}))c.deny("Required connected typed FLDCW fault",a);c.access(a,v,2,0);return p;',
 'mw34_crte_direct':'require(owner&&p==owner&&!ci::owner&&!mn::owner,"Exact active entry direct token");return owner->direct(s,a);',
 'mw34_crte_enter':'require(owner&&p==owner&&!ci::owner&&!mn::owner,"Exact active entry enter token");owner->guard();require(s==&owner->state()&&(a==entry||a==0x5ac5c0),"Only actual ordinary entry or literal RET leaf reached");return p;',
 }
 for symbol,expected in dispatch.items():
  matches=[line for line in new.splitlines()if '"C"' in line and symbol+'(' in line]
  R.need(len(matches)==1,'One exact production token bridge '+symbol)
  line=matches[0]
  R.need('noexcept(false)'in line and line.split('{',1)[1].rsplit('}',1)[0]==expected,'Entire guarded typed bridge body '+symbol)
 binding=R.text(ROOT/'tools/m4-crt-entry-control/control_binding.inc')
 R.need('catch(...){ci::owner=nullptr;control_checkpoint(r,"control-after");throw;}'in binding,'Owner cleared before failure observer may throw')
 R.need('context(r,*reinterpret_cast<State*>(r.remill_state().data()))'in binding and '.map('not in binding and 'initialize('not in binding and 'memcpy'not in binding,'Control Context borrows existing State and FX without map/reset')
 # The precise complete token closure also has independently executed null,
 # arbitrary, cross-owner and stale-token cases; source presence alone grants
 # no such execution credit.
 R.check('Persistent borrowed State/FX, whole typed token bridge bodies, source continuation and encompassing host guard',State_bytes=3504,FX_bytes=512,exact_guarded_dispatchers=len(dispatch),host_guard_unchanged=True,provider_remap=False,source_next_callsite=0x5ac440,source_next_target=0x5ac598,observer_exception_owner_cleanup=True,complete_token_execution_requires_separate_compiled_review=True)

def main():
 R.need(len(sys.argv)==4,'final.py fresh-report-dir preparation-dir build-json')
 out,prep,bp=map(lambda p:Path(p).resolve(),sys.argv[1:])
 R.need(out.parent==BASE and out.name.startswith('independent-source-')and not out.exists(),'Fresh independent source closure');out.mkdir(parents=True)
 (out/'final.py').write_bytes(Path(__file__).read_bytes());R.pin(out/'final.py')
 try:
  for relative,want in R.FROZEN.items():R.pin(ROOT/relative,want)
  build=R.read(bp);R.need(build['passed'],'Completed candidate build')
  count=receipt_maps(build);context_derivative(prep);IR_derivative(prep);composition_contract(prep);inspect_objects(out,build,bp,prep)
  report=dict(passed=True,scope='Independent candidate source/build/object association closure; root scalar observations and independent compiled causal/hardware evidence required separately',checks=R.CHECKS,commands=R.COMMANDS,physical_bindings_rehashed=count,source_contract_report=str(BASE/'independent-source-r1/report.json'),findings=[],full_CRT=False,native_menu=False,selected_initializer_count_unchanged=27,whole_M4_complete=False)
  R.pin(BASE/'independent-source-r1/report.json','fd8881fc5ceb5dc1bb304bbd75a5dacc8fa63334e35ea5c3245e8a277a7e4f57')
  R.pin(BASE/'independent-source-r1/pins.json','28fd4768c0993f73430743252606f6439131cd947f56f807fc4a1131728ea926')
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');R.pin(out/'report.json');R.pin(Path(__file__));R.pin(HERE/'review.py')
  (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(R.PINS.items()))),indent=2)+'\n')
  print(json.dumps(dict(passed=True,files=len(R.PINS),checks=len(R.CHECKS),report=str(out/'report.json'),report_sha256=R.sha(out/'report.json'),pins_sha256=R.sha(out/'pins.json'))))
 except Exception:
  (out/'failure.txt').write_text(traceback.format_exc());raise

if __name__=='__main__':main()
