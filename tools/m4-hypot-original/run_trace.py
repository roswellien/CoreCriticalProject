"""Run the independently admitted separate genuine source tracer once."""
from pathlib import Path
import hashlib,json,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-hypot-original'
sys.path.insert(0,str(R/'tools/m4-pipeline'));from stages import run_stage,verify_stage
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(build,digest,name,preflight,preflight_digest):
 out=B/name;assert not out.exists();out.mkdir();pins={};passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h;assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 try:
  b=json.loads(pin(build,digest).read_text(encoding='utf-8-sig'));assert b['passed'];p=Path(b['preparation'])/'report.json';prep=json.loads(pin(p,b['preparation_sha256']).read_bytes());assert prep['trace_descriptors']==3538 and prep['SetThreadContext_written_sections']=='CONTEXT_CONTROL only'and not prep['debugger_FP_or_integer_sections_written']and prep['trace_source_hook_overlaps']==0 and not prep['normal_return_replay_used']and not prep['source_after_seed']
  pre=json.loads(pin(preflight,preflight_digest).read_bytes());assert pre['passed'];assert pre['files'][str(build.resolve())]==digest and pre['files'][str(p.resolve())]==b['preparation_sha256'],'Current physical preflight binds exact build and preparation'
  for path,h in json.loads(pin(build.parent/'pins.json').read_text(encoding='utf-8-sig'))['files'].items():pin(path,h)
  args=[pin(b['worker'],b['worker_sha256']),pin(b['pack']),pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'),pin(R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a'),out/'original'];pin(__file__);pin(sys.executable);stage=out/'run';result=run_stage([str(a)for a in args],stage,timeout_seconds=190,required_outputs=[out/'original/transport.json'],inputs=list(pins));verify_stage(stage,sha(pin(stage/'stage.json')));assert result['passed'],'Actual separate original trace worker failed';passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Fresh independently admitted six-case actual game/hypot/CRT instruction trace execution stage; source/control/operand validation follows',build_path=str(build),build_sha256=digest,prelaunch_review_path=str(preflight),prelaunch_review_sha256=preflight_digest,original_capture=str(out/'original/transport.json'),original_executed=True,source_trace_executed=True,normal_return_replay_used=False,native_executed=False,provider_preinvoked=False,per_phase_reseed=False,numerical_expected_seed=False,validation_pending=True,files=pins);q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(q))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3],Path(sys.argv[4]).resolve(),sys.argv[5])
