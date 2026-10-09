"""Seal unchanged author objects and complete bounded startup observations."""
import hashlib,json,pathlib,sys
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-mainargs'
def sha(p):
 with pathlib.Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def main(name):
 out=BASE/name;assert not out.exists();out.mkdir();files={}
 def bind(p,h=None):
  p=pathlib.Path(p).resolve();key=str(p)
  if key in files:assert h is None or files[key]==h;return
  value=sha(p);assert h is None or value==h,p;files[key]=value
 prep=BASE/'preparation-r2';receipt=read(prep/'report.json');assert receipt['passed'] and not receipt['State_reseed_inside_mainargs'] and receipt['new_pages']==[]
 for p,h in read(prep/'pins.json')['files'].items():bind(p,h)
 assert (prep/'crt_services.cpp').read_bytes()==(ROOT/'reports/m4-crt-entry-initterm/preparation-r3/crt_services.cpp').read_bytes()
 for n in ('crt_services.hpp','seed.hpp','matherr_context.hpp','control_context.hpp','initterm_context.hpp','control_binding.inc','initterm_binding.inc'):
  assert (prep/n).read_bytes()==(ROOT/'reports/m4-crt-entry-initterm/preparation-r3'/n).read_bytes()
 build=BASE/'build-r2/build.json';b=read(build);assert b['passed']
 for group in ('sources','tools','libraries','entry_objects','compiler_read_headers','artifacts'):
  for p,h in b[group].items():bind(p,h)
 bind(build);bind(prep/'pins.json')
 for folder in ('execution-r1','author-observer-r1'):
  assert read(BASE/folder/'report.json')['passed']
  for p in(BASE/folder).rglob('*'):
   if p.is_file():bind(p)
 for folder in ('recovery-r1','recovery-r2','recovery-r3','preparation-r1','build-r1','author-observer-failed-syntax-r1'):
  for p in(BASE/folder).rglob('*'):
   if p.is_file():bind(p)
 for namespace in ('m4-crt-mainargs-recovery','m4-crt-entry-mainargs'):
  for p in(ROOT/'tools'/namespace).rglob('*'):
   if p.is_file()and '__pycache__'not in p.parts:bind(p)
 prior=ROOT/'reports/m4-crt-entry-initterm/root-acceptance-r2'
 prior_receipt=read(prior/'report.json');assert prior_receipt['passed'];bind(prior/'report.json');bind(prior/'pins.json')
 report=dict(passed=True,scope='Author literal compiled mainargs/ordinary-builder prefix submitted for independent root acceptance',preparation_path=str(prep/'report.json'),preparation_sha256=sha(prep/'report.json'),build_path=str(build),build_sha256=sha(build),execution_report=str(BASE/'execution-r1/report.json'),execution_sha256=sha(BASE/'execution-r1/report.json'),author_observer_path=str(BASE/'author-observer-r1/report.json'),author_observer_sha256=sha(BASE/'author-observer-r1/report.json'),provider_recovery=str(BASE/'recovery-r3/report.json'),provider_recovery_sha256=sha(BASE/'recovery-r3/report.json'),prior_first_initterm_acceptance=str(prior/'report.json'),prior_first_initterm_acceptance_sha256=sha(prior/'report.json'),prior_first_initterm_pins_sha256=sha(prior/'pins.json'),positive_compositions=48,causal_controls=120,new_causal_controls=24,direct_host_pairs=330,whole_State_bytes=3504,separate_FX_bytes=512,owned_pages=16,source_identity_bytes=1140,positive_mainargs_accesses=48*16,positive_mainargs_routes=48*4,source_bodies=[dict(entry=0x7800ba5e,size=66),dict(entry=0x7800bbbc,size=140)],Runtime_provider_translation_registered=False,Runtime_provider_import_registered=False,Session_changed=False,new_pages=0,State_reseed=False,FX_reseed=False,argc_argv_environment_outputs_admitted=False,next_required_import=dict(source_PC=0x7800bbd0,iat_slot=0x7802e018,name='KERNEL32.dll!GetModuleFileNameA',raw_IAT=0x343b0,return_PC=0x7800bbd6,arguments=[0,0x7803b3f0,260]),connected_initializer_roots=27,total_nonzero_roots=144,remaining_nonzero_roots=117,ordinary_game_launched=False,original_executed=False,full_CRT=False,whole_M4_complete=False,retained_diagnostics=['Recovery-r1 refused an incorrect asserted decoded export instruction count before source output; sourcegraph is21 instructions/66bytes.','Recovery-r2 refused exact direct source helper declarations as unreviewed bridges; final lowering keeps them as typed stops and reversibly names each compiled root.','Composition prep/build-r1 failed before execution at a mixed const-auto declaration; final prep2 also closes all cross-owner helper exclusions.','Author observer reserved-keyword syntax refusal occurred before execution and is retained separately.'])
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');bind(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(dict(passed=True,bindings=len(files),report_sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
