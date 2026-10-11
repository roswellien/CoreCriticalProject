"""Run exactly the current independently admitted constructor37 workers."""
from pathlib import Path
import hashlib,json,sys,traceback
R=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True;sys.path.insert(0,str(R/'tools/m4-pipeline'))
from stages import run_stage,verify_stage
BUILD='0f5761af58092ef55ccd265ed0acf5a0bbdead40fab96cdb87eccb79f99f1d18'
PREP='f0dfc1427c9cca0c1b920be6fc030c6b9bb7e53ef631946abcbf4ddf215001a0'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(review,digest,name):
 out=R/'reports/m4-constructor-native'/name;need(not out.exists(),'One fresh admitted execution');out.mkdir();files={};runs={};launched=0;passed=False;terminal=True
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'Writer controller never opens captures');v=sha(p);need(h is None or h==v,'Exact controller input '+str(p));need(str(p)not in files or files[str(p)]==v,'One input identity');files[str(p)]=v;return p
 try:
  a=json.loads(pin(review,digest).read_bytes());b=json.loads(pin(R/'reports/m4-constructor-native/fixture-build-r10/build.json',BUILD).read_bytes());p=json.loads(pin(R/'reports/m4-constructor-native/fixture-preparation-r6/report.json',PREP).read_bytes());need(a['passed']and a['build_sha256']==BUILD and a['preparation_sha256']==PREP and b['passed']and p['passed']and b['preparation_sha256']==PREP,'Current independent whole-linked admission')
  need(a['files'].get(str((R/'reports/m4-constructor-native/fixture-build-r10/build.json').resolve()))==BUILD and a['files'].get(str((R/'reports/m4-constructor-native/fixture-preparation-r6/report.json').resolve()))==PREP,'Current preflight physically binds fixture8')
  for level in('O0','O2'):need(a['files'].get(str(Path(b['workers'][level]['path']).resolve()))==b['workers'][level]['sha256'],'Current preflight physically binds each worker')
  for q,h in a['files'].items():pin(q,h)
  for q,h in b['files'].items():pin(q,h)
  for q,h in p['files'].items():pin(q,h)
  inputs=[pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'),pin(R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a'),pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'),pin(R/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8')];pin(__file__);pin(sys.executable);pin(R/'tools/m4-pipeline/stages.py')
  for level in('O0','O2'):
   worker=pin(b['workers'][level]['path'],b['workers'][level]['sha256']);capture=out/level;stage=out/(level+'-stage');argv=list(map(str,[worker,*inputs,capture]));launched+=1;terminal=False
   result=run_stage(argv,stage,timeout_seconds=300,required_outputs=[capture/'transport.json'],inputs=list(files));terminal=True;receipt=pin(stage/'stage.json');verify_stage(stage,sha(receipt));runs[level]=dict(worker=str(worker),arguments=argv,stage=str(receipt),stage_sha256=sha(receipt),capture=str(capture/'transport.json'),stage_passed=result['passed'],elapsed_seconds=result['elapsed_seconds']);print(json.dumps(dict(level=level,terminal=True,passed=result['passed'])),flush=True);need(result['passed'],'Actual constructor37 '+level+' terminal worker success');pin(capture/'transport.json')
  for q,h in files.items():need(sha(q)==h,'Current physical controller conservation')
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  d=dict(passed=passed,scope='Actual current two-level bounded37 writers only; strict source/provider validation and full144 chronology separate',build_sha256=BUILD,preparation_sha256=PREP,admission_review=str(review),admission_review_sha256=digest,runs=runs,actual_workers_launched=launched,all_workers_terminal=terminal,archive_reader_opened=False,initializer_credit=0,files=files);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(q))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
