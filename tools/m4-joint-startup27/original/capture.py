"""Bounded original hardware sequence runner, direct primary/debug secondary."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'reports/m4-joint-startup27';PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();actual=sha(p);assert h is None or h==actual,(str(p),h,actual);PINS[str(p)]=actual;return p
def main(out,debugger):
 out=Path(out).resolve();assert out.parent==BASE and not out.exists();out.mkdir(parents=True)
 commands=[];failure=None
 try:
  build=BASE/'original-build-r2';b=json.loads(pin(build/'build.json').read_text(encoding='utf-8-sig'));assert b['passed'] and not b['guest_executed']
  for p,h in json.loads(pin(build/'pins.json').read_text(encoding='utf-8-sig'))['files'].items():pin(p,h)
  for p,h in json.loads(pin(BASE/'original-extraction-r1/pins.json').read_text())['files'].items():pin(p,h)
  worker=pin(b['worker'],b['worker_sha256']);pack=pin(b['pack']);game=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');provider=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a')
  recipe={'arguments':list(map(str,(worker,pack,game,provider,out/'raw.bin')))+(['--checkpoint']if debugger else []),'direct_primary':not debugger,'debugger_secondary':debugger,'worker_sha256':sha(worker),'pack_sha256':sha(pack),'original_execution_only':True}
  (out/'sealed-recipe.json').write_text(json.dumps(recipe,indent=2)+'\n')
  result=subprocess.run(recipe['arguments'],cwd=ROOT,capture_output=True,timeout=190)
  (out/'stdout.txt').write_bytes(result.stdout);(out/'stderr.txt').write_bytes(result.stderr);commands.append({'arguments':recipe['arguments'],'exit_code':result.returncode})
  assert result.returncode==0,result.stderr.decode(errors='replace')
  raw=pin(out/'raw.bin');assert raw.stat().st_size==32+1296*117684
 except Exception:failure=traceback.format_exc();(out/'failure.txt').write_text(failure)
 report={'passed':failure is None,'failure':failure,'commands':commands,'scope':'Actual sparse original27 hardware sequence; direct CPU/FX512/ENV28 and14wholepages with one declared owning IAT relocation; debugger checkpoint secondary only'if debugger else 'Actual direct sparse original27 CPU/FX512/ENV28 and14wholepages; no debugger or perphase reseed','direct_primary':not debugger,'debugger_secondary':debugger,'sequences':48 if failure is None else None,'phases':1296 if failure is None else None,'original_record_size':117684,'native_Common_size':116964,'provider_checkpoint_CONTEXT_size':716,'provider_checkpoint_count':48 if debugger and failure is None else 0,'original_State_observed':False,'original_access_events_observed':False,'native_executed':False,'whole_M4_complete':False}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(__file__);pin(sys.executable)
 for p in out.iterdir():
  if p.is_file():pin(p)
 (out/'pins.json').write_text(json.dumps({'files':PINS},indent=2)+'\n')
 print(json.dumps({'passed':failure is None,'out':str(out),'direct_primary':not debugger}),flush=True)
 if failure:raise RuntimeError(failure)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--checkpoint',action='store_true');a=p.parse_args();main(a.output,a.checkpoint)
