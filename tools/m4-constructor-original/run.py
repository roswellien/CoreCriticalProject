"""One direct-bound chronological constructor37 writer; current prelaunch and semantic validation are separate."""
from pathlib import Path
import hashlib,json,shutil,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];BASE=R/'reports/m4-constructor-original'
sys.path.insert(0,str(R/'tools/m4-pipeline'));from stages import run_stage,verify_stage
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(build,digest,preflight,preflight_digest,name):
 out=BASE/name
 if out.exists():raise ValueError('Fresh single execution required; never resume/relaunch an existing writer')
 pins={};passed=False;started=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p)
  if h is not None and v!=h:raise ValueError('Exact current physical input '+str(p))
  if str(p)in pins and pins[str(p)]!=v:raise ValueError('No conflicting current identity')
  pins[str(p)]=v;return p
 b=json.loads(pin(build,digest).read_text(encoding='utf-8-sig'));q=json.loads(pin(preflight,preflight_digest).read_text(encoding='utf-8-sig'))
 if not b['passed']or not q['passed']or(b['roots'],b['phases'],b['record_bytes'])!=(37,222,356992):raise ValueError('Exact chronological constructor37 current build and independent prelaunch required')
 if q['files'].get(str(build.resolve()))!=digest or q['files'].get(str(Path(b['worker']).resolve()))!=b['worker_sha256']:raise ValueError('Current independent prelaunch must physically bind build and final linked worker')
 for p,h in q['files'].items():pin(p,h)
 for p,h in json.loads(pin(build.parent/'pins.json').read_text(encoding='utf-8-sig'))['files'].items():pin(p,h)
 required=3*1024**3;free=shutil.disk_usage(BASE).free
 if free<=required:raise ValueError('Current chronological constructor37 destination requires conservative3GiB free headroom')
 out.mkdir(parents=True)
 try:
  args=[pin(b['worker'],b['worker_sha256']),pin(b['pack']),pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'),pin(R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a'),out/'original']
  pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7');pin(R/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8')
  pin(__file__);pin(Path(__file__).with_name('derive_runner.py'));pin(R/'tools/m4-startup131-original/run.py');pin(R/'tools/m4-pipeline/stages.py');pin(sys.executable);stage=out/'run';started=True
  result=run_stage([str(a)for a in args],stage,timeout_seconds=300,required_outputs=[out/'original/transport.json'],inputs=list(pins));verify_stage(stage,sha(pin(stage/'stage.json')))
  if not result['passed']:raise ValueError('Actual chronological constructor37 writer stage failed')
  passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Genuine37-root selected original chronology through three new constructors; semantic source/resource validation follows',build_path=str(build),build_sha256=digest,preflight_path=str(preflight),preflight_sha256=preflight_digest,original_capture=str(out/'original/transport.json'),original_executed=started,native_executed=False,per_phase_reseed=False,validation_pending=True,source_after_seed=False,initializer_credit=0,destination_free_before_bytes=free,conservative_required_free_bytes=required,files=pins)
  p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(p))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4],sys.argv[5])
