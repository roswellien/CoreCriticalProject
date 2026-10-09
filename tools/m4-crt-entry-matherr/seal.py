"""Seal additive submission, frozen dependencies and actual worker observations."""
import hashlib,json,pathlib,sys
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-entry-matherr'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def main(name):
 out=BASE/name;assert not out.exists();out.mkdir();files={}
 def bind(p,h=None):
  p=pathlib.Path(p).resolve();v=sha(p);assert h is None or v==h,p;assert str(p)not in files or files[str(p)]==v;files[str(p)]=v
 for p,h in read(BASE/'preparation-r1/pins.json')['files'].items():bind(p,h)
 bind(BASE/'preparation-r1/pins.json')
 build=BASE/'build-r1/build.json';b=read(build);assert b['passed']
 for group in('sources','tools','libraries','entry_objects','compiler_read_headers','artifacts'):
  for p,h in b[group].items():bind(p,h)
 bind(build)
 for category in('execution-r1','author-observer-r1'):
  r=read(BASE/category/'report.json');assert r['passed']
  for p in(BASE/category).rglob('*'):
   if p.is_file():bind(p)
 for p in(BASE/'run-r1-O0').rglob('*'):
  if p.is_file():bind(p)
 for p in(ROOT/'tools/m4-crt-entry-matherr').rglob('*'):
  if p.is_file()and '__pycache__'not in p.parts:bind(p)
 ancestor=(BASE/'preparation-r1/matherr_context.hpp.ancestor').read_text();derived=(BASE/'preparation-r1/matherr_context.hpp').read_text()
 original=ancestor.split('extern "C" unsigned __remill_read_memory_32(void *p,unsigned a) {')[0]
 inverse=derived.replace('\n    void (*test_before_execute)(Context &){};','').replace('try { if(test_before_execute)test_before_execute(*this); token=sub_7800b38f(&state,entry,this); }','try { token=sub_7800b38f(&state,entry,this); }')
 assert inverse==original,'Exact Context inverse derivative required'
 report=dict(passed=True,scope='Author submitted exact matherr registration connected after FDIV in same persistent CRT entry; awaiting independent source/compiled closure',build_path=str(build),build_sha256=sha(build),execution_report=str(BASE/'execution-r1/report.json'),execution_report_sha256=sha(BASE/'execution-r1/report.json'),author_observer=str(BASE/'author-observer-r1/report.json'),author_observer_sha256=sha(BASE/'author-observer-r1/report.json'),actual_positive_sequences=48,actual_causal_denials=48,complete_State_bytes=3504,complete_pages=14,writer_events_per_positive=97,game_events_per_positive=35,matherr_events_per_positive=5,completed_CRT_services=4,translated_RET_leaf=0x5ac5c0,matherr_provider_leaf=0x7800b38f,matherr_callback_argument=0x51e7b0,matherr_zero_global=0x780392b8,matherr_callback_global=0x7803b0c4,next_required_source_PC=0x5ac431,next_required_direct_target=0x5ac5a0,callback_invoked=False,State_reseed_after_writer=False,provider_data_reseed_after_writer=False,shared_r9_changed=False,raw_IAT_mutation_in_positive=False,Context_inverse_derivative_verified=True,original_game_entry_executed=False,full_CRT=False,whole_M4_complete=False,retained_initial_manual_O0_run=str(BASE/'run-r1-O0'),earlier_non_execution_diagnostics=['Initial manual invocation used nonexistent pack/before-input paths and returned Input file unavailable before any Runtime was constructed.','Observer code generation assertion refused creation; no native work or evidence modified.','Author observer syntax check rejected reserved import keyword in a dictionary constructor before execution; corrected before first created observer report.'])
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');bind(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),bindings=len(files))))
if __name__=='__main__':main(sys.argv[1])
