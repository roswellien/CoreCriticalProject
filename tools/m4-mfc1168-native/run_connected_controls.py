"""Admitted exact two control writers, then bounded strict canonical checks."""
from pathlib import Path
import hashlib,importlib.util,json,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/m4-pipeline'))
from stages import run_stage,verify_stage
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(build,digest,review,review_sha,name):
 out=R/'reports/m4-mfc1168-native'/name;need(not out.exists(),'Fresh current controls');out.mkdir();pins={};levels=[];runs={};passed=False;closed=True;launched=0
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact current '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Stable input');pins[str(p)]=v;return p
 try:
  admission=json.loads(pin(review,review_sha).read_bytes());b=json.loads(pin(build,digest).read_bytes());p=json.loads(pin(b['preparation'],b['preparation_sha256']).read_bytes());need(admission['passed']and b['passed']and p['passed']and p['control_cases']==12,'Current exact passed build/preparation/review');need(admission['build_sha256']==digest and admission['preparation_sha256']==b['preparation_sha256'],'Current exact admission')
  for q,h in b['files'].items():pin(q,h)
  sources=[pin(R/f,h)for f,h in [('MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'),('local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a'),('local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'),('local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8')]];pin(__file__);pin(sys.executable)
  for level in ('O0','O2'):
   worker=pin(b['workers'][level]['path'],b['workers'][level]['sha256']);capture=out/level;stage=out/(level+'-stage');args=list(map(str,[worker,*sources,capture]));launched+=1;st=run_stage(args,stage,timeout_seconds=120,required_outputs=[capture/'transport.json'],inputs=list(pins));pin(stage/'stage.json');verify_stage(stage,sha(stage/'stage.json'));runs[level]=dict(worker=str(worker),stage=str(stage/'stage.json'),capture=str(capture/'transport.json'),elapsed_seconds=st['elapsed_seconds']);print(json.dumps(dict(level=level,stage_passed=st['passed'])),flush=True);need(st['passed'],'Actual control worker terminal '+level)
  path=pin(R/'tools/m4-crt-allocation-root/run_v2.py');spec=importlib.util.spec_from_file_location('connected_control_transport',path);ds=importlib.util.module_from_spec(spec);spec.loader.exec_module(ds)
  for level in ('O0','O2'):
   records=ds.DirectSet(Path(runs[level]['capture']),pin);closed=False
   try:
    need(records.words('control-header.bin',5)==(1,12,14,17,159716),'Current control ABI')
    for mode in range(1,13):
     stem=f'control-{mode}/';facts=records.words(stem+'facts.bin',8);need(facts[:7]==(1,mode,13,1,1,1,1),'Actual refusal/retry/cleanup extent');need(records.data(stem+'refusal.txt'),'Precise actual refusal retained')
     for phase in range(13):need(len(records.data(stem+f'phase-{phase}.bin'))==159716,'Every whole completed prior root retained')
     for part in ('caller-hardware.bin','retry-hardware.bin'):
      hw=records.data(stem+part);need(len(hw)==1632 and hw[:512]==hw[1088:1600]and hw[512:540]==hw[1600:1628],'Whole actual caller512/28 restoration')
     for part in ('State.bin','CPU.bin','FX.bin','Context-status.bin','Context-reason.txt','Runtime-calls.bin','registry-summary.bin','memory-index.bin'):
      need(records.data(stem+'retry-before/'+part)==records.data(stem+'retry-after/'+part),'Whole unchanged retry '+part)
     if facts[7]:need(records.words(stem+'MFC/cleaned/resource-context.bin',12,'Q')[2:7]==(0,0,0,0,0),'Actual owned TLS/CS cleanup')
    need(records.data('COMPLETE.txt')==b'12 actual connected MFC denials, unchanged poisoned retries and owned cleanup; no initializer credit\n','Exact complete control writer');levels.append(dict(**runs[level],level=level,logical_files=len(records.entries),payload_bytes=records.value['payload_bytes']));print(json.dumps(dict(level=level,structural_passed=True)),flush=True)
   finally:records.close();del records;closed=True
  for q,h in pins.items():need(sha(q)==h,'Stable current inputs after closure')
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Current12 connected public mutations O0/O2 structural observed refusal/retry/caller/cleanup; complete causal/private/provider checker separate',build=str(build),build_sha256=digest,admission_review=str(review),admission_review_sha256=review_sha,levels=levels,runs=runs,files=pins,actual_workers_launched=launched,all_workers_terminal=True,all_bounded_readers_closed=closed,initializer_credit=0)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4],sys.argv[5])
