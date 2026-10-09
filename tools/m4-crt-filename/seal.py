"""Author submission receipt; independent filename review and root acceptance remain separate."""
import hashlib,json,pathlib,sys,time
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2];HERE=pathlib.Path(__file__).resolve().parent;BASE=ROOT/'reports/m4-crt-filename'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def main(build_name,execution_name,observer_name,out_name):
 out=BASE/out_name;assert out.parent==BASE and not out.exists();files={};start=time.perf_counter()
 def add(path,value):
  p=str(pathlib.Path(path).resolve());assert p not in files or files[p]==value,p;files[p]=value
 receipts={}
 for label,path in [('build',BASE/build_name/'build.json'),('execution',BASE/execution_name/'report.json'),('observer',BASE/observer_name/'report.json'),('accepted_predecessor',ROOT/'reports/m4-crt-mainargs/root-acceptance-r1/report.json')]:
  receipt=read(path);assert receipt['passed'];receipts[label]=dict(path=str(path),sha256=sha(path));add(path,sha(path))
  for key in ['sources','tools','libraries','entry_objects','compiler_read_headers','artifacts','input_files','files']:
   for p,h in receipt.get(key,{}).items():add(p,h)
  if label=='build':prep=pathlib.Path(receipt['preparation_path']);assert sha(prep)==receipt['preparation_sha256'];add(prep,sha(prep));pins=read(prep.parent/'pins.json');add(prep.parent/'pins.json',sha(prep.parent/'pins.json'));[add(p,h)for p,h in pins['files'].items()]
 e=read(BASE/execution_name/'report.json');o=read(BASE/observer_name/'report.json')
 assert e['build_sha256']==receipts['build']['sha256'] and o['build_sha256']==receipts['build']['sha256'] and o['execution_sha256']==receipts['execution']['sha256']
 assert e['positive_sequences']==o['positive_sequences']==48 and e['causal_negative_sequences']==o['causal_sequences']==24
 assert o['actual_API_unit_cases']==8 and o['ordinary_host_pairs']==146 and o['selected_capture_corruption_denials']==616
 for p in HERE.rglob('*'):
  if p.is_file()and'__pycache__'not in p.parts:add(p,sha(p))
 for p,h in files.items():assert sha(p)==h,p
 out.mkdir();report=dict(passed=True,scope='Author native filename service submission; root seal and independent compiled/host reviews required separately',receipts=receipts,files=files,bindings=len(files),seconds=time.perf_counter()-start,positive_sequences=48,causal_sequences=24,actual_API_unit_cases=8,ordinary_host_pairs=146,selected_capture_corruption_denials=616,next_required_source_PC=0x7800bbd6,next_required_address=0x78037174,actual_native_NULL_module_identity=True,guest_TEB_LastError_written=False,State_reseed=False,new_guest_mappings=[],native_x86_API_volatile_register_equivalence=False,argc_argv_environment_outputs=False,provider_RET=False,main_initializers_count_27_unchanged=True,whole_M4_complete=False)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='files'}))
if __name__=='__main__':main(*sys.argv[1:])
