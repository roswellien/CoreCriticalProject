"""Seal current native inputs and receipt anchors without historical expansion."""
import hashlib,json,pathlib,sys,time
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-commandline-carry'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def main(name):
 out=BASE/name;assert name.startswith('author-submission-')and not out.exists()and out.parent==BASE
 began=time.perf_counter();files={};anchors={}
 def bind(p,h=None):
  p=str(pathlib.Path(p).resolve());actual=sha(p);assert h is None or actual==h,(p,actual,h)
  assert p not in files or files[p]==actual,p;files[p]=actual;return actual
 paths=dict(preparation=BASE/'preparation-r5/report.json',build=BASE/'build-r6/build.json',author_execution=BASE/'execution-r3/report.json',source_audit=BASE/'source-contract-r2/report.json',root_execution=BASE/'root-execution-r1/report.json',root_observer=BASE/'root-observer-r1/report.json',accepted_filename=ROOT/'reports/m4-crt-filename/root-acceptance-r1/report.json')
 for k,p in paths.items():
  r=read(p);assert r.get('passed',False),(k,p);anchors[k]=dict(path=str(p),sha256=bind(p))
 build=read(paths['build']);assert anchors['build']['sha256']=='10969868ff59f5bd1c37b60065b2329d0649785ab3a5d48763696fe846759ce9'
 for category in ('sources','tools','libraries','entry_objects','compiler_read_headers','artifacts'):
  for p,h in build[category].items():bind(p,h)
 pins=BASE/'preparation-r5/pins.json';bind(pins,'c4520c939b5cd886180720116cbc6c034719d03d1dc5a565890aca97dbc20105')
 for p,h in read(pins)['files'].items():bind(p,h)
 execution=read(paths['author_execution']);assert execution['build_sha256']==anchors['build']['sha256']and execution['positive_sequences']==48 and execution['causal_negative_sequences']==24
 for p,h in execution['input_files'].items():bind(p,h)
 # Executions and complete captures are anchored by their immutable receipts;
 # independent root bundles/source proof seal those observations separately.
 for p in (pathlib.Path(__file__),ROOT/'tools/m4-crt-commandline-carry/README.md'):bind(p)
 out.mkdir();report=dict(passed=True,scope='Author submission of current hash-bound command-line carry native candidate; final independent compiled acceptance remains separate',anchors=anchors,files=files,physical_bindings=len(files),positive_sequences=48,causal_negative_sequences=24,producer_source_bytes=11,producer_accesses=3,consumer_source_instructions=14,consumer_accesses=9,new_routes=7,borrowed_pages=16,owned_buffer=0x33000000,State_bytes=3504,FX_bytes=512,State_reseed_after_writer=False,original_DLL_scheduling_proved=False,fragment_RET_claimed=False,parser_body_executed=False,SDK_file_open_attestation=False,whole_M4_complete=False,historical_receipt_closure_expanded=False,capture_artifacts_rehashed_here=False,seconds=time.perf_counter()-began)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k not in('files','anchors')},indent=2));print('report_sha256='+sha(out/'report.json'))
if __name__=='__main__':main(sys.argv[1])
