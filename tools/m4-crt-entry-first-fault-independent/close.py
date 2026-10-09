"""Final independent complete-entry static and bounded first-fault compiled closure."""
from pathlib import Path
import hashlib,json,re,subprocess,sys,traceback
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-entry';OUT=BASE/'independent-first-fault-closure-r1'
LLVM=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';PINS={};COMMANDS=[]
def need(ok,w):
 if not ok:raise ValueError(w)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();got=sha(p);need(h is None or got==h,'Physically stable exact entry identity '+str(p));PINS[str(p)]=got;return p
def js(p,h=None):return json.loads(pin(p,h).read_text())
def flat(p,h=None):
 d=js(p,h)['files']
 for p,h in d.items():pin(p,h)
 return len(d)
def run(args,name,cwd=ROOT):
 args=list(map(str,args));r=subprocess.run(args,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60);p=OUT/name;p.write_bytes(r.stdout);pin(p);need(r.returncode==0,'Fresh own entry artifact inspection '+name);COMMANDS.append(dict(command=args,cwd=str(cwd),exit_code=r.returncode,log=str(p),sha256=sha(p)));return r.stdout.decode(errors='replace')
def main():
 need(not OUT.exists(),'Fresh first-fault final private report');OUT.mkdir(parents=True)
 try:
  src=Path(__file__).resolve();(OUT/'review-source.py').write_bytes(src.read_bytes());pin(src);pin(OUT/'review-source.py');pin(sys.executable)
  static=js(BASE/'independent-first-fault-static-r2/report.json','f4a508cda2534aa961b37b9b2f63c6dacc9f768bf031b40652c8901502af4489');static_count=flat(BASE/'independent-first-fault-static-r2/pins.json','477798097aacfcf80d0de49d50c26b26d540befff2bca53273d8599097b53fae')
  compiled=js(BASE/'independent-first-fault-compiled-r1/report.json','173e570704406cf97bf8fc452531386f07eb2af93f9fa158cf47dd2374833e2b');compiled_count=flat(BASE/'independent-first-fault-compiled-r1/pins.json','2cb2f1603b6187a39773fd2d04090d176d65a4c45c4fa36fa99c57e188c121fa')
  observer=js(BASE/'first-fault-observation-r2/report.json','880f25fffaea5f527d8935aa6f420f5d7f914e1084f5d163eac6b0fd987acba5');flat(BASE/'first-fault-observation-r2/pins.json','09bd235d445aa61568cae03ba578037e6d174f7a96ea73cde59e183494f56c8e')
  need(static['passed']and compiled['passed']and observer['passed'],'All separately frozen scoped stages pass')
  root=(ROOT/'tools/m4-crt-entry/observe_first_fault.py').read_text();need('for _ in range(16):'in root and 'assert len(program)==16'in root and "data['after-state.bin']==state"in root and "data['events.bin']==b''.join"in root,'Root raw model source prefix and complete State/event comparison read independently')
  need(root.count("(('before',m.before),('after',m.mem))")==1 and 'no original execution'in root,'Raw original startup and declared before-memory limitations retained')
  own=pin(ROOT/'tools/m4-crt-entry-first-fault-independent/compiled/controls.cpp').read_text();need(own.count('noexcept(false)')==10 and 'r_.call_import({slot},{0x5ac3d5})'in own and 'std::memcpy(&t,&s,3504)'in own,'Own throwing ABI and whole opaque State source model')
  need('constexpr unsigned entry=0x5ac3a0,slot=0x5bb5a4,frame=0x20001880'in own and 'frame=0x20001900'in (ROOT/'tools/m4-crt-entry/first_fault.cpp').read_text(),'Own independently chosen frame is distinct from root raw fixture')
  need('mode_==5&&n==14'in own and 'Own actual guest CALL return storage'in own and 'Poison retry leaves whole State/softwareFX/pages/TIB/CPU/events/ledger/owner unchanged'in own,'Actual source CALL write and checked bridge faults plus immutable terminal retry controls')
  need(static['IR']['instruction_calculation_changes']==0 and static['IR']['named_types']==34 and static['IR']['direct_seams']==8 and len(static['IR']['roots'])==11,'Exact full prepared State/body/seam scope preserved from own inverse analysis')
  readobj=pin(LLVM/'llvm-readobj.exe');dump=pin(LLVM/'llvm-objdump.exe');decodes=[];deps=set()
  for result in compiled['results']:
   lv=result['level'];r=result['result'];need(result['exit_code']==0 and r==dict(passed=True,checks=224,scenarios=19,predicted_source_rows=4,actual_denial_calls=37,poisoned_retries=19,unentered_corrected_reuses=2,original_execution=False,full_CRT=False),'Exact actual independent source/causal counts')
   obj=next((BASE/'independent-first-fault-compiled-r1'/lv).rglob('controls.cpp.obj'));pin(obj);meta=run([readobj,'--symbols','--relocations','--unwind',obj],lv+'-own-adapter-coff.txt');code=run([dump,'-d','--print-imm-hex',obj],lv+'-own-adapter-code.txt');need('sub_5ac3a0'in meta and'__CxxFrameHandler3'in meta and 'Handler: __CxxFrameHandler3'in meta,'Actual C++ caller/checked-memory bridge exception unwind Handler')
   decodes.append(str(obj));obj=pin(result['object'],result['object_sha256']);meta=run([readobj,'--symbols','--relocations','--unwind',obj],lv+'-exact-guest-coff.txt');code=run([dump,'-d','--print-imm-hex',obj],lv+'-exact-guest-code.txt');need(all(x in meta for x in('sub_5ac3a0','mw34_crte_enter','__remill_read_memory_32','__remill_write_memory_32','__remill_function_call')) and meta.count('RuntimeFunction {')>=11,'Actual complete eleven-root object unwind and real throwing source memory/CALL routes');decodes.append(str(obj))
   folder=BASE/'independent-first-fault-compiled-r1'/lv;ninja=pin(Path('C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'));text=run([ninja,'-t','deps'],lv+'-own-compiler-read-dependencies.txt',folder)
   for line in text.splitlines():
    name=line.strip()
    if re.match(r'^[A-Za-z]:[\\/]',name)and Path(name).is_file():deps.add(str(Path(name).resolve()));pin(name)
  need(len(deps)>300,'Actual own compiler dependency paths separately rehashed post-build')
  report=dict(passed=True,scope='Independent physical/source/full-entry inverse-IR/ABI/object closure and actual compiled first deliberately unresolved CRT service research only',prepared_unique_PCs=148,ordinary_entry_PCs=118,prepared_complete_roots=11,native_reached_source_PCs=16,root_actual_raw_rows=2,root_raw_source_corruption_rejects=len(observer['own_corruption_rejects']),own_actual_compiled_checks=448,own_actual_compiled_scenarios=38,own_predictive_source_rows=8,own_actual_denial_calls=74,own_terminal_poisoned_retries=38,own_corrected_unentered_reuses=4,own_compiled_fresh_object_decodes=4,prior_static_fresh_decodes=4,decodes=decodes,own_compiler_dependency_paths=len(deps),static_input_bindings=static_count,compiled_input_bindings=compiled_count,first_required_service=dict(call_pc=0x5ac3cf,iat_slot=0x5bb5a4,symbol='MSVCRT.dll!__set_app_type',return_pc=0x5ac3d5,completed=False),causal_scope=['Five real checked-memory faults at second stack push/FS read/FS write/IAT read/actual CALL return push, caught through guest LLVM unwind','Actual source CALL return-frame corruption and changed raw owning IAT denial','Whole430-byte current source mutation beyond reached prefix, absent seed, sequential wrong-thread entered adapter refusal and wrong FS region','Outer frame RO failure occurs before guest adapter while Runtime outer ledger entered and poisoned','Pre-routing bad return and nested lexical owner refusal remain unentered and reusable; missing adapter owner is entered terminal fault','After permission/source/IAT/FS/seed correction, failed Runtime remains poisoned with complete State/softwareFX/pages/TIB/CPU/events/call ledger and own first-origin diagnostic unchanged'],diagnostic_limit='Own first bridge-origin diagnostic is added fixture instrumentation; frozen production Runtime exposes its existing coarse typed Fault. Neither implies real guest SEH dispatch.',state_limit='Independent dirty seed and owned stack/NT_TIB policy, distinct root raw fixture frame; no original process startup State or measured floating-point coherence proof.',artifact_limit='Exact disk source/tool/object identities and current actual compiler dependency paths rehashed after build; no execution-time memory attestation or full process trace.',prefix_review_included=False,author_fixture_model_executor_imported=False,original_executed=False,actual_host_FP_boundary_proved=False,complete_SEH_dispatch=False,first_service_completed=False,full_CRT=False,full_startup=False,whole_M4_complete=False,commands=COMMANDS)
  (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(OUT/'report.json')
  for p,h in PINS.items():need(sha(p)==h,'Final immutable first-fault sources/evidence')
  (OUT/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n');print(json.dumps(dict(passed=True,bindings=len(PINS),report_sha256=sha(OUT/'report.json'),pins_sha256=sha(OUT/'pins.json'))))
 except Exception:(OUT/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main()
