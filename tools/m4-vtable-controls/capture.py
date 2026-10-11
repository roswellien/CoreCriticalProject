from pathlib import Path
import hashlib,json,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-vtable-controls'
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from stages import run_stage,verify_stage
from manifests import verify_manifest
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(build,digest,name):
 out=BASE/name;assert not out.exists();out.mkdir(parents=True);pins={};rows=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h,(p,h,v);pins[str(p)]=v;return p
 try:
  b=json.loads(pin(build,digest).read_bytes());assert b['passed']
  for p,h in json.loads(pin(Path(build).parent/'pins.json').read_bytes())['files'].items():pin(p,h)
  game=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');numeric=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a');crt=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7');mfc=pin(ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8');pin(__file__)
  for level in ('O0','O2'):
   worker=pin(b['workers'][level]['path'],b['workers'][level]['sha256']);capture=out/level;stage=out/(level+'-stage')
   st=run_stage(list(map(str,(worker,game,numeric,crt,mfc,capture))),stage,timeout_seconds=240,required_outputs=[capture/'transport.json'],inputs=list(pins));pin(stage/'stage.json');verify_stage(stage,sha(stage/'stage.json'))
   rows.append(dict(level=level,passed=st['passed'],stage=str(stage/'stage.json'),stage_sha256=sha(stage/'stage.json'),capture=str(capture/'transport.json'),capture_sha256=sha(capture/'transport.json'),elapsed_seconds=st['elapsed_seconds']));print(json.dumps(rows[-1]),flush=True)
  assert all(r['passed']for r in rows),'Functional fixture failed; preserved captures'
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,build=str(build),build_sha256=digest,levels=rows,files=pins,physical_closure=verify_manifest(pins),native_executed=True,source_bodies_modified=False,API_response_injection=False,initializer_credit=False)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pins[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
