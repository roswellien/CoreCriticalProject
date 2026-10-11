"""One admitted O0/O2 by eight batch of ordinary current Context faults.

This controller authenticates exact workers, terminals and complete ordinary
outputs. Fault effects, same-context bytes and resource identities are verified
by the separate semantic checker; no canonical archive reader is used.
"""
from pathlib import Path
import hashlib,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/m4-pipeline'))
from stages_capture_storage import run_stage,verify_stage
from paths_capture_storage import STORAGE_ROOT
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(build,build_sha,review,review_sha,name):
 out=R/'reports/m4-joint-startup138'/name;need(not out.exists(),'Fresh actual Context fault batch');out.mkdir();pins={};runs=[];passed=False;launched=0
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'Ordinary inputs only; no canonical reader');v=sha(p);need(h is None or v==h,'Exact physical input '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Stable exact input');pins[str(p)]=v;return p
 try:
  storage_review=json.loads(pin(R/'reports/m4-tree-review/capture-storage-r1/report.json','74920256d02e000da908748ac96857a69cce60d20dad9ff9cd8e9ea87a3538b7').read_bytes());need(storage_review['passed']and storage_review['hash_index_payload_limits_and_stable_close_unchanged'],'Strict admitted fixed local storage root')
  for q,h in storage_review['files'].items():pin(q,h)
  b=json.loads(pin(build,build_sha).read_bytes());p=json.loads(pin(b['preparation'],b['preparation_sha256']).read_bytes());ad=json.loads(pin(review,review_sha).read_bytes());need(b['passed']and p['passed']and p['control_modes']==8 and p['control_phase']==135 and p['completed_prefix_roots']==135 and p['source_owned_font_create_calls']==15,'Exact current eight-mode Context recipe/build');need(ad['passed']and ad['build_sha256']==build_sha and ad['preparation_sha256']==b['preparation_sha256'],'Independent physical current worker admission');need(p['borrowed_service_preparation_sha256']=='cb0e8aaffe9ed7320113b1c1b18d2d3615e38d84eb16a51fcec3bdc4018385f9','Actual current positive growth provider used in fault workers')
  for d in(b,p,ad):
   for q,h in d['files'].items():pin(q,h)
  sources=[pin(R/f,h)for f,h in [('MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'),('local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a'),('local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'),('local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8')]];pin(__file__);pin(sys.executable);pin(R/'tools/m4-pipeline/stages.py')
  cases=[(0,127,0),(0,895,7),(0,3967,0),(1,1151,7),(1,2687,0),(1,3711,7)]
  for level in('O0','O2'):
   worker=pin(b['workers'][level]['path'],b['workers'][level]['sha256'])
   for mode in range(1,9):
    capture=STORAGE_ROOT/'reports/m4-joint-startup138'/name/level/f'mode-{mode}';stage=out/level/f'mode-{mode}-stage';args=[str(worker),*[str(q)for q in sources],str(capture),review_sha,str(mode)];launched+=1;st=run_stage(args,stage,timeout_seconds=420,required_outputs=[capture/'COMPLETE.txt',capture/'status.bin'],inputs=list(pins),cwd=STORAGE_ROOT);sp=pin(stage/'stage.json');verify_stage(stage,sha(sp));runs.append(dict(level=level,mode=mode,worker=str(worker),worker_sha256=sha(worker),arguments=args,capture=str(capture),stage=str(sp),stage_sha256=sha(sp),passed=st['passed'],elapsed_seconds=st['elapsed_seconds']));print(json.dumps(dict(level=level,mode=mode,worker_passed=st['passed'])),flush=True);need(st['passed'],'Actual complete current Context worker terminal '+level+'/'+str(mode))
    w=struct.unpack('<16I',pin(capture/'status.bin').read_bytes());need(w[:5]==(1,mode,*cases[(mode-1)%6])and w[5:10]==(1,1,1,1,135)and w[10]==w[11]and w[12]==135 and w[15]==1,'Actual refusal, poison, same Context retry and cleanup structure');need(pin(capture/'admission.txt').read_text()==review_sha,'Actual worker admission marker');need(pin(capture/'COMPLETE.txt').read_bytes()==b'Complete current Context refusal/retry and owned cleanup','Current complete worker statement');need(pin(capture/'refusal.txt').stat().st_size>0,'Actual first refusal retained');need(pin(capture/'prefix-records.bin').stat().st_size==135*159716,'135 complete selected prefix ABI records');need(all(pin(capture/(x+'-hardware.bin')).stat().st_size==1632 for x in('invoke','retry','cleanup')),'Three complete actual hardware boundaries')
    manifest={str(q.relative_to(capture)).replace('\\','/'):dict(bytes=q.stat().st_size,sha256=sha(q))for q in capture.rglob('*')if q.is_file()};mp=out/level/f'mode-{mode}-manifest.json';mp.write_text(json.dumps(manifest,indent=2)+'\n');pin(mp);runs[-1].update(output_manifest=str(mp),output_manifest_sha256=sha(mp),observed_files=len(manifest))
  for q,h in list(pins.items()):need(sha(q)==h,'All current worker/source inputs unchanged after terminals')
  need(launched==16 and len(runs)==16 and all(x['passed']for x in runs),'Exactly two current levels by eight actual faults');passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  d=dict(passed=passed,scope='Actual current carried138 Context fault workers only; independent whole-byteflow/private/resource/source proofs remain separate',build_path=str(build),build_sha256=build_sha,preparation_path=b['preparation']if'b'in locals()else None,preparation_sha256=b['preparation_sha256']if'b'in locals()else None,admission_review=str(review),admission_review_sha256=review_sha,runs=runs,actual_workers_launched=launched,all_workers_terminal=True,ordinary_outputs_only=True,archive_reader_opened=False,initializer_credit=0,files=pins);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(q),sha256=sha(q))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4],sys.argv[5])
