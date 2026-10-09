"""Seal the exact author candidate and observations without changing ancestors."""
import hashlib,json,pathlib,sys
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-entry-initterm'
def sha(p):
 with pathlib.Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def main(name):
 out=BASE/name;assert not out.exists();out.mkdir();files={}
 def bind(p,h=None):
  p=pathlib.Path(p).resolve();v=sha(p);assert h is None or h==v,p;assert str(p)not in files or files[str(p)]==v;files[str(p)]=v
 prep=BASE/'preparation-r3';r=read(prep/'report.json');assert r['passed']and not r['old_callback_continuation_admitted']
 for p,h in read(prep/'pins.json')['files'].items():bind(p,h)
 original=(prep/'crt_services.cpp.ancestor').read_text();derived=(prep/'crt_services.cpp').read_text()
 inverse=derived.replace('\nvoid compiled_initterm(m4_runtime::Runtime&);','').replace('slots.initterm,"_initterm",compiled_initterm,8','slots.initterm,"_initterm",initterm,8').replace('// First-null gate admits no callback continuation; complete provider source is owned by its literal full page.','r.register_service_continuation(provider,std::move(c));')
 assert inverse==original
 build=BASE/'build-r3/build.json';b=read(build);assert b['passed']
 for group in('sources','tools','libraries','entry_objects','compiler_read_headers','artifacts'):
  for p,h in b[group].items():bind(p,h)
 bind(build);bind(prep/'pins.json')
 for folder in('execution-r2','author-observer-r1'):
  assert read(BASE/folder/'report.json')['passed']
  for p in(BASE/folder).rglob('*'):
   if p.is_file():bind(p)
 for folder in('provider-preparation-r1','provider-preparation-r2','provider-preparation-r3','preparation-r1','preparation-r2','build-r1','build-r2','execution-r1'):
  for p in(BASE/folder).rglob('*'):
   if p.is_file():bind(p)
 for p in(ROOT/'tools/m4-crt-entry-initterm').rglob('*'):
  if p.is_file()and '__pycache__'not in p.parts:bind(p)
 report=dict(passed=True,scope='Author compiled literal first-null CRT initterm composition submitted for independent root acceptance',preparation_path=str(prep/'report.json'),preparation_sha256=sha(prep/'report.json'),build_path=str(build),build_sha256=sha(build),execution_report=str(BASE/'execution-r2/report.json'),execution_sha256=sha(BASE/'execution-r2/report.json'),author_observer_path=str(BASE/'author-observer-r1/report.json'),author_observer_sha256=sha(BASE/'author-observer-r1/report.json'),positive_compositions=48,causal_controls=96,direct_host_pairs=282,whole_State_bytes=3504,separate_FX_bytes=512,owned_pages=16,source_identity_bytes=934,positive_writer_events=4656,positive_game_events=2304,positive_control_routes=624,positive_control_accesses=2496,positive_initterm_routes=288,positive_initterm_accesses=384,Session_derivative_exact_reverse=True,old_callback_continuation_admitted=False,provider_page_literal=True,table_page_borrowed=True,callback_success_admitted=False,compiled_callback_CALL_denial=True,State_reseed=False,FX_reseed=False,next_required_import=dict(source_PC=0x5ac468,iat_slot=0x5bb514,name='MSVCRT.dll!__getmainargs',return_PC=0x5ac46e),connected_initializer_roots=27,total_nonzero_roots=144,remaining_nonzero_roots=117,ordinary_game_launched=False,original_executed=False,full_CRT=False,whole_M4_complete=False,causal_ESP_mutation_limit='Mode43 mutates StateESP after the MOV source read. O0 computes20002008; O2 preserves earlier compiled operand20001874; both current-operand guards deny at78001502. This injected observer case grants no original architectural partial-fault equivalence.',retained_diagnostics=['Provider preparation-r1 refused unexpected LLVM ctpop intrinsic before adaptation output; r2 refused unavailable Python wrapper for LLVMSetValueName2; r3 uses the exact DLL API and compiles complete objects.','First composition candidate retained unused continuation publication and its overlapping provider slice; this unexecuted source candidate was superseded by the explicit first-null withholding seam.','Author execution-r1 completed positives and controls1..42, then refused control43 because after-access hooks had not been attached; corrected hook wiring in finalprep3.','Author observer materializer refused a duplicated replacement anchor before file creation; the unchanged historical observer refused an existing old directory; corrected new observer passed all144records.'])
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');bind(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(dict(passed=True,bindings=len(files),report_sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
