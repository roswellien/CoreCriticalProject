"""Run exactly the physically admitted eight-mode widget control workers."""
from pathlib import Path
import hashlib,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/m4-pipeline'))
from stages import run_stage,verify_stage
PH='47af86a27b82f00b38b5da26eeb1017058f997d32bb89cac5d4ac81fa7a45663'
BH='63f6d56ce07bba98a5ec1decdbaf3e061751393807c15b3aa625292d38d34017'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(review,review_sha,source_review,source_sha,name):
 out=R/'reports/m4-widget-native'/name;need(not out.exists(),'Fresh actual admitted controls');out.mkdir();pins={};runs=[];passed=False;launched=0
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No archive or canonical capture reader');v=sha(p);need(h is None or v==h,'Exact current input '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Stable current input');pins[str(p)]=v;return p
 try:
  p=json.loads(pin(R/'reports/m4-widget-native/controls-preparation-r1/report.json',PH).read_bytes());b=json.loads(pin(R/'reports/m4-widget-native/controls-build-r2/build.json',BH).read_bytes());ad=json.loads(pin(review,review_sha).read_bytes());sr=json.loads(pin(source_review,source_sha).read_bytes());need(p['passed']and b['passed']and b['preparation_sha256']==PH and p['control_modes']==8,'Exact current eight-mode build');need(ad['passed']and ad['preparation_sha256']==PH and ad['build_sha256']==BH,'Root physical COFF admission for exact current code');need(sr['passed']and sr['preparation_sha256']==PH and sr['build_sha256']==BH and sr['control_modes_reviewed']==8,'Independent finite recipe and source review')
  for d in(p,b,ad,sr):
   for q,h in d['files'].items():pin(q,h)
  inputs=[pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'),pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'),pin(R/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8'),pin(R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a')];pin(__file__);pin(sys.executable);pin(R/'tools/m4-pipeline/stages.py')
  for level in('O0','O2'):
   worker=pin(b['workers'][level]['path'],b['workers'][level]['sha256'])
   for mode in range(1,9):
    capture=out/level/f'mode-{mode}';stage=out/level/f'mode-{mode}-stage';args=[str(worker),*[str(q)for q in inputs],str(capture),review_sha,str(mode)];launched+=1;st=run_stage(args,stage,timeout_seconds=180,required_outputs=[capture/'cleanup/status.bin'],inputs=list(pins));stage_path=pin(stage/'stage.json');verify_stage(stage,sha(stage_path));runs.append(dict(level=level,mode=mode,worker=str(worker),worker_sha256=sha(worker),arguments=args,capture=str(capture),stage=str(stage_path),stage_sha256=sha(stage_path),passed=st['passed'],elapsed_seconds=st['elapsed_seconds']));print(json.dumps(dict(level=level,mode=mode,worker_passed=st['passed'])),flush=True);need(st['passed'],'Actual worker terminal success; caught first refusal alone is insufficient')
    status=struct.unpack('<8I',pin(capture/'cleanup/status.bin').read_bytes());need(status[:5]==(1,mode,1,1,1)and status[5]==status[6]and status[7]==1,'Actual first refusal, poisoned retry and cleanup complete')
    manifest={str(q.relative_to(capture)).replace('\\','/'):dict(bytes=q.stat().st_size,sha256=sha(q))for q in capture.rglob('*')if q.is_file()};f=out/level/f'mode-{mode}-manifest.json';f.write_text(json.dumps(manifest,indent=2)+'\n');pin(f);runs[-1].update(output_manifest=str(f),output_manifest_sha256=sha(f),observed_files=len(manifest))
  for q,h in list(pins.items()):need(sha(q)==h,'Inputs and receipts unchanged after all worker terminals')
  need(launched==16 and all(v['passed']for v in runs),'Exactly two levels by eight actual fault workers');passed=True
 except BaseException:
  passed=False;(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  q=out/'report.json';q.write_text(json.dumps(dict(passed=passed,scope='Actual eight authored refusal workers at both levels; worker structure only, detailed semantic refusals/byte retries require separate checker',preparation_sha256=PH,build_sha256=BH,admission_review=str(review),admission_review_sha256=review_sha,source_review=str(source_review),source_review_sha256=source_sha,runs=runs,actual_workers_launched=launched,all_workers_terminal=True,archive_reader_opened=False,initializer_credit=0,files=pins),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),passed=passed)))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4],sys.argv[5])
