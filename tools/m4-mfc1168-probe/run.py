"""Write two bounded one-root original probes; never open a capture archive."""
from pathlib import Path
import hashlib,json,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-mfc1168-probe'
sys.path.insert(0,str(R/'tools/m4-pipeline'));from stages import run_stage,verify_stage
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(build,h,name):
 out=B/name;assert not out.exists();out.mkdir();pins={};passed=False;results=[]
 def pin(p,expected=None):
  p=Path(p).resolve();v=sha(p);assert expected is None or v==expected;pins[str(p)]=v;return p
 try:
  b=json.loads(pin(build,h).read_text(encoding='utf-8-sig'));assert b['passed']
  for p,d in json.loads(pin(Path(build).parent/'pins.json').read_text(encoding='utf-8-sig'))['files'].items():pin(p,d)
  pin(__file__);pin(sys.executable)
  for mode in('normal','trace'):
   args=[pin(b['worker'],b['worker_sha256']),pin(b['pack']),out/mode,mode];stage=out/(mode+'-stage');result=run_stage([str(a)for a in args],stage,timeout_seconds=190,required_outputs=[out/mode/'COMPLETE.txt'],inputs=list(pins));verify_stage(stage,sha(pin(stage/'stage.json')));results.append(dict(mode=mode,stage=str(stage/'stage.json'),stage_sha256=sha(stage/'stage.json'),passed=result['passed']));assert result['passed'],'Genuine focused '+mode+' probe failed'
  passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Actual authentic-loader normal and debugger one-root writers only; detailed bounded source/API validation follows',build=str(build),build_sha256=h,results=results,root=0x5ae3e4,capture_archive_reader_opened=False,normal=str(out/'normal'),trace=str(out/'trace'),initializer_credit=0,files=pins)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
