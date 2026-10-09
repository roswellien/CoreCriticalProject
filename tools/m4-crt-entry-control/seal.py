"""Seal final literal control candidate and retain unsuccessful revisions."""
import hashlib,json,pathlib,re,sys
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/m4-crt-entry-control'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def main(name):
 out=BASE/name;assert not out.exists();out.mkdir();files={}
 def bind(p,h=None):
  p=pathlib.Path(p).resolve();v=sha(p);assert h is None or h==v,p;assert str(p)not in files or files[str(p)]==v;files[str(p)]=v
 prep=BASE/'preparation-r5';receipt=read(prep/'report.json');assert receipt['passed'] and receipt['control_IR_reverse_equal']
 for p,h in read(prep/'pins.json')['files'].items():bind(p,h)
 ir=(prep/'control.ll').read_text()
 for a,b in receipt['control_IR_symbol_mapping'].items():ir=ir.replace(b,a)
 assert ir==(prep/'control.ll.ancestor').read_text()
 build=BASE/'build-r6/build.json';b=read(build);assert b['passed']
 for group in('sources','tools','libraries','entry_objects','compiler_read_headers','artifacts'):
  for p,h in b[group].items():bind(p,h)
 bind(build);bind(prep/'pins.json')
 for category in('execution-r3','author-observer-r1'):
  report=read(BASE/category/'report.json');assert report['passed']
  for p in(BASE/category).rglob('*'):
   if p.is_file():bind(p)
 # llc is a recorded invocation but absent from the inherited generic tool map.
 # This binding is a physical post-build tool association, not process tracing.
 bind(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llc.exe')
 for old in('preparation-r1','preparation-r2','preparation-r3','preparation-r4','build-r2','build-r3','build-r4','build-r5','execution-r1'):
  for p in(BASE/old).rglob('*'):
   if p.is_file():bind(p)
 for p in(ROOT/'tools/m4-crt-entry-control').rglob('*'):
  if p.is_file()and '__pycache__'not in p.parts:bind(p)
 report=dict(passed=True,scope='Author complete staged control wrapper/provider connected into actual CRT entry, submitted for independent acceptance',preparation_path=str(prep/'report.json'),preparation_sha256=sha(prep/'report.json'),build_path=str(build),build_sha256=sha(build),execution_report=str(BASE/'execution-r3/report.json'),execution_sha256=sha(BASE/'execution-r3/report.json'),author_observer=str(BASE/'author-observer-r1/report.json'),author_observer_sha256=sha(BASE/'author-observer-r1/report.json'),positive_sequences=48,causal_denials=72,host_direct_pairs=234,complete_State_bytes=3504,complete_pages=14,game_events_per_positive=38,control_events_per_positive=13,compiled_control_accesses_per_positive=52,completed_Runtime_call_records=7,incomplete_root=1,next_required_PC=0x5ac440,next_required_target=0x5ac598,control_IR_reverse_equal=True,IR_symbol_mapping=receipt['control_IR_symbol_mapping'],provider_pages_remapped=False,expected_CW_reseed=False,State_reseed=False,shared_r9_changed=False,ordinary_game_launched=False,full_CRT=False,whole_M4_complete=False,post_build_tool_identity_only=True,retained_diagnostics=['Initial source materializer refused a checkpoint definition anchor; incomplete preparation-r1 retained.','Build-r2 link rejected duplicate wrapper/thunk and seven pure Remill helpers; reversible symbol derivative resolves ownership without linker ambiguity.','Build-r3 rejected a nonexistent accidentally changed frozen entry-object path before any compilation.','Execution-r1 retained positive24/oldcontrols O0 prefix before invalid negative game-region protection; fixed to actual region401000.','Execution-r2 was rejected before directory creation and worker execution because an associated source had changed to fix observer cleanup.','Author observer parser initially rejected a reserved dictionary keyword before execution; corrected before first created report.'])
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');bind(out/'report.json')
 (out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(dict(passed=True,bindings=len(files),report_sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
