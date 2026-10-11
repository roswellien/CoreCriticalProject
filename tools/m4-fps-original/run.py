"""One direct-bound normal widget capture; independent validation is separate."""
from pathlib import Path
import hashlib,json,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];BASE=R/'reports/m4-fps-original'
sys.path.insert(0,str(R/'tools/m4-pipeline'));from stages import run_stage,verify_stage
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(build,digest,preflight,preflight_digest,name):
 out=BASE/name
 if out.exists():raise ValueError('Fresh single execution required')
 pins={};passed=False;started=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p)
  if h is not None and v!=h:raise ValueError('Exact physical input '+str(p))
  pins[str(p)]=v;return p
 b=json.loads(pin(build,digest).read_text(encoding='utf-8-sig'));q=json.loads(pin(preflight,preflight_digest).read_text(encoding='utf-8-sig'))
 if not b['passed']or not q['passed']:raise ValueError('Current build and independent prelaunch required')
 if q['files'].get(str(build.resolve()))!=digest or q['files'].get(str(Path(b['worker']).resolve()))!=b['worker_sha256']:raise ValueError('Independent prelaunch physically binds exact build and linked worker')
 for p,h in q['files'].items():pin(p,h)
 for p,h in json.loads(pin(build.parent/'pins.json').read_text(encoding='utf-8-sig'))['files'].items():pin(p,h)
 out.mkdir(parents=True)
 try:
  args=[pin(b['worker'],b['worker_sha256']),pin(b['pack']),pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'),pin(R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a'),out/'original']
  pin(__file__);pin(sys.executable);stage=out/'run';started=True
  result=run_stage([str(a)for a in args],stage,timeout_seconds=240,required_outputs=[out/'original/transport.json'],inputs=list(pins));verify_stage(stage,sha(pin(stage/'stage.json')))
  if not result['passed']:raise ValueError('Actual widget execution stage failed')
  passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Genuine carried five-widget plus479590 plus40F000 fps original normal execution only; source/semantic/resource validation follows',build_path=str(build),build_sha256=digest,preflight_path=str(preflight),preflight_sha256=preflight_digest,original_capture=str(out/'original/transport.json'),original_executed=started,native_executed=False,per_phase_reseed=False,validation_pending=True,source_after_seed=False,initializer_credit=0,files=pins)
  p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(p))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4],sys.argv[5])
