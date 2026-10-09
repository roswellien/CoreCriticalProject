"""Bind immutable author submission, complete runs, and every retained failure."""
import hashlib,json,pathlib,sys
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-entry-data'
def sha(p):
 with pathlib.Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(out):
 out=pathlib.Path(out).resolve();assert out.parent==BASE and not out.exists();out.mkdir();files={}
 def bind(p,h=None):
  p=pathlib.Path(p).resolve();value=sha(p);assert h is None or value==h,str(p);assert str(p)not in files or files[str(p)]==value
  files[str(p)]=value
 for name in('preparation-r1','preparation-r2','preparation-r3','preparation-r4','author-observer-r1'):
  pins=BASE/name/'pins.json'
  for p,h in json.loads(pins.read_text())['files'].items():bind(p,h)
  bind(pins)
 for name in('build-r1','build-r3','build-r4','build-r5','build-r6'):
  p=BASE/name/'build.json';receipt=json.loads(p.read_text(encoding='utf-8-sig'))
  for group in('sources','tools','libraries','entry_objects','compiler_read_headers','artifacts'):
   for path,h in receipt[group].items():bind(path,h)
  bind(p)
 for name in('build-r2','probe-r1-O0','run-r1-O0','run-r2-O0','run-r2-O2','run-r3-O0','run-r3-O2'):
  for p in(BASE/name).rglob('*'):
   if p.is_file():bind(p)
 for p in(ROOT/'tools/m4-crt-entry-data').rglob('*'):
  if p.is_file()and '__pycache__'not in p.parts:bind(p)
 for name in('root-model-r2/report.json','root-model-r2/pins.json'):
  bind(ROOT/'reports/m4-crt-fdiv-replay'/name)
 build=BASE/'build-r6/build.json';observer=BASE/'author-observer-r1/report.json'
 assert json.loads(build.read_text(encoding='utf-8-sig'))['passed']and json.loads(observer.read_text())['passed']
 report=dict(passed=True,scope='Author-submitted bounded FDIV writer → actual CRT consumer + translated RET leaf; awaiting independent root closure',
  final_build=str(build),final_build_sha256=sha(build),author_observer=str(observer),author_observer_sha256=sha(observer),
  runs=[str(BASE/'run-r3-O0'),str(BASE/'run-r3-O2')],actual_positive_records=48,actual_causal_denials=24,
  supported_control_words=12,complete_State_bytes=3504,complete_pages=11,guest_NT_TIB_fields_only=[4,8,4],
  writer_events_per_success=97,game_events_per_success=34,actual_game_source_PCs=35,real_CRT_services=3,literal_translated_RET_leaf=0x5ac5c0,
  actual_consumer_load=0x5ac40d,actual_consumer_store=0x5ac40f,source_data_IAT=0x5bb508,source_initialized_global=0x78037c2c,
  next_required_source_PC=0x5ac428,next_required_owning_IAT=0x5bb50c,next_required_service='MSVCRT!__setusermatherr',
  undefined_flag_policy='Only exact TEST5AC41F emits AF=0 as undefined native representative; raw site separately captured; no original AF equality credit',
  State_reseed_after_writer=False,provider_data_reseed_after_writer=False,raw_game_and_provider_IAT_preserved=True,
  direct_caller_boundary='Whole legacy ENV28, CW/SW/FTW, physical raw80, MXCSR, seeded ABI XMM6..15; XMM0..5 observed without equality requirement',
  permissions='Exact harness mapping-base protection changes and real denied accesses; no public current-permission query exists in shared GuestMemory',
  retained_failures=['build-r1 mixed ASM tool flags; no execution','build-r2 both objects linked but finally publisher failed; no execution','probe-r1-O0 inherited undefined TEST AF bridge rejected','run-r1-O0 first24 positives retained but wrong authored mutation mapping-base blocked remaining controls'],
  compilation_direct_tool_provenance='Build receipt fixed direct-tool hashes plus prior frozen preparation pins checked before build, including actual clang.exe assembly provider; source/header/library associations remain explicit',
  original_game_entry_executed=False,shared_r9_changed=False,joint_initializer_accepted_count=26,full_CRT=False,whole_M4_complete=False,
  required_context='Completed FDIV Registry borrowed same live r9 Runtime/3504 State/pages; flat DS/SS, owned FS, coherent empty twelve-CW BEFORE; explicit outer ESP/EIP only transition; no guest SEH dispatch')
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');bind(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n')
 print(json.dumps(dict(passed=True,report=str(out/'report.json'),bindings=len(files),report_sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
