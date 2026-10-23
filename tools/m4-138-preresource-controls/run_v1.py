"""ROOT-admitted single ordinary worker case only; not invoked by preparation."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,traceback,time
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(a):
 out=R/'reports/m4-138-preresource-controls'/a.name;assert not out.exists();pins={};passed=False;closed=True;worker_executed=False;facts={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip');v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 bp=pin(R/'reports/m4-138-preresource-controls/build-r2/build.json','ba6a26b3af64a351057380507397999bb42ceb34d87c33627f8acc80235c6b6b');b=json.loads(bp.read_bytes());assert b['passed'] and b['worker_executed']is False
 pp=pin(b['preparation'],b['preparation_sha256']);pr=json.loads(pp.read_bytes());assert pr['passed'] and pr['cases']['modes']==list(range(1,13))
 admission=pin(a.admission,a.admission_sha);review=json.loads(admission.read_bytes());assert review['passed']is True
 assert review['scope_identity']=='current138_preresource_legacy12' and review['ordinary_outputs_only']is True
 assert review['modes']==list(range(1,13)) and review['levels']==['O0','O2']
 for p in (bp,pp,Path(__file__).resolve()):assert review['files'][str(p)]==sha(p);pin(p)
 required=('complete_source_inverse','whole_linked_current_context_and_provider_inputs','typed_COFf_CALL_TLS_ownership','whole85byte_boundary_target_and_unwind','exact_real64byte_MFC_entry_frame','current_MFC_and_widget_fault_cleanup','bounded14prefix_no_reseed','complete_private_and_public_retry_inventory')
 assert set(review['prelaunch_checks'])==set(required) and all(review['prelaunch_checks'][x]is True for x in required)
 assert a.level in('O0','O2') and 1<=a.mode<=12
 for p,h in b['files'].items():pin(p,h)
 source=(Path(pp).parent/'controls_main.cpp').read_text();assert 'phase>=14' in source
 images=[]
 for v in pr['source_images']:
  p=Path(v['path']).resolve();assert p.stat().st_size==v['bytes'];pin(p,review['files'][str(p)]);images.append(p)
 w=b['workers'][a.level];worker=pin(w['path'],w['sha256']);assert review['files'][str(worker)]==w['sha256'];out.mkdir();closed=False
 try:
  command=list(map(str,[worker,*images,out/'payload',a.admission_sha,a.mode]));worker_executed=True;t=time.monotonic();r=subprocess.run(command,cwd=R,capture_output=True,timeout=120,creationflags=0x08000000);closed=True
  (out/'stdout.bin').write_bytes(r.stdout);(out/'stderr.bin').write_bytes(r.stderr);facts=dict(arguments=command,exit_code=r.returncode,elapsed_seconds=time.monotonic()-t)
  assert r.returncode==0,'Failed case preserved without acceptance or refusal credit'
  payload=out/'payload';assert (payload/'COMPLETE.txt').is_file() and not(payload/'FAILED.txt').exists()
  leaves=[p for p in payload.rglob('*')if p.is_file()];assert len(leaves)<=4096 and sum(p.stat().st_size for p in leaves)<=128*1024*1024
  for p in leaves:assert p.stat().st_size<=32*1024*1024;pin(p)
  assert (payload/'admission.txt').read_text()==a.admission_sha
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  for p in out.iterdir():
   if p.is_file():pin(p)
  report=dict(passed=passed,scope='Single actual current138 pre-resource mode raw output production only; strict independent refusal/TLS/API/resource/retry equivalence remains required',level=a.level,mode=a.mode,worker_executed=worker_executed,worker_closed=closed,reader_opened=False,accepted_function_credit=0,initializer_credit=0,facts=facts,files=pins);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('admission');p.add_argument('admission_sha');p.add_argument('level',choices=['O0','O2']);p.add_argument('mode',type=int);main(p.parse_args())
