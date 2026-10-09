"""Fresh native27 whole sequences, preserved hardware state before cleanup."""
from pathlib import Path
import hashlib,json,subprocess,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'reports/m4-joint-startup27';PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);assert h is None or v==h,(str(p),v,h);PINS[str(p)]=v;return p
def main(build,out):
 build=Path(build).resolve();out=Path(out).resolve();assert build.parent==out.parent==BASE and not out.exists();out.mkdir(parents=True);commands=[];failure=None
 try:
  b=json.loads(pin(build/'build.json').read_text());assert b['passed'] and not b['guest_executed']
  for p,h in json.loads(pin(build/'pins.json').read_text())['files'].items():pin(p,h)
  game=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');provider=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a')
  for level,w in b['workers'].items():
   worker=pin(w['path'],w['sha256']);args=list(map(str,(worker,game,provider,out/level)));(out/f'{level}-sealed-recipe.json').write_text(json.dumps({'arguments':args,'worker_sha256':sha(worker),'source_binding_map':b['sources'],'objects':w['objects']},indent=2)+'\n')
   r=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=120);(out/f'{level}.stdout').write_bytes(r.stdout);(out/f'{level}.stderr').write_bytes(r.stderr);commands.append({'arguments':args,'exit_code':r.returncode});assert r.returncode==0,(level,r.stderr.decode(errors='replace'))
   assert pin(out/level/'native.bin').stat().st_size==32+1296*132636 and pin(out/level/'sequences.bin').stat().st_size==24+48*122824
   print(json.dumps({'level':level,'passed':True,'phases':1296,'sequences':48}),flush=True)
 except Exception:failure=traceback.format_exc();(out/'failure.txt').write_text(failure)
 report={'passed':failure is None,'failure':failure,'commands':commands,'actual_native_phases':2592 if failure is None else None,'actual_native_sequences':96 if failure is None else None,'scope':'Actual new native outer-boundary candidate27 complete persistent selected-table sequences; independent original/raw/failure review pending','per_phase_reseed':False,'ordinary_game_launched':False,'whole_M4_complete':False}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(__file__);pin(sys.executable)
 for p in out.rglob('*'):
  if p.is_file():pin(p)
 (out/'pins.json').write_text(json.dumps({'files':PINS},indent=2)+'\n')
 if failure:raise RuntimeError(failure)
if __name__=='__main__':main(sys.argv[1],sys.argv[2])
