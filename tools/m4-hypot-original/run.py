"""Run once into a fresh strict original-hypot1 archive; validation is separate."""
from pathlib import Path
import hashlib,json,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-hypot-original'
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'));from stages import run_stage,verify_stage
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(build,digest,name):
 out=BASE/name;assert not out.exists();out.mkdir(parents=True);pins={};passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 try:
  b=json.loads(pin(build,digest).read_text(encoding='utf-8-sig'));assert b['passed']
  for p,h in json.loads(pin(Path(build).parent/'pins.json').read_text(encoding='utf-8-sig'))['files'].items():pin(p,h)
  args=[pin(b['worker'],b['worker_sha256']),pin(b['pack']),pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'),pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a'),out/'original']
  pin(__file__);pin(sys.executable);stage=out/'run';result=run_stage([str(a)for a in args],stage,timeout_seconds=190,required_outputs=[out/'original/transport.json'],inputs=list(pins));verify_stage(stage,sha(pin(stage/'stage.json')));assert result['passed'],'Actual original-hypot1 execution stage failed';passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Fresh bounded original-hypot1 execution stage only; full typed/FS/source validation follows',build_path=str(build),build_sha256=digest,original_capture=str(out/'original/transport.json'),original_executed=True,native_executed=False,per_phase_reseed=False,validation_pending=True,files=pins)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])

