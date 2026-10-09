"""Rehash and run the preserved whole-loop controls in new owned output."""
from pathlib import Path
import hashlib,json,subprocess,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-joint-startup27'
PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();actual=sha(p);assert h is None or h==actual,(str(p),actual,h);PINS[str(p)]=actual;return p
def main(out):
 out=Path(out).resolve();assert out.parent==BASE and not out.exists();out.mkdir(parents=True)
 commands=[];failure=None
 try:
  ancestor=ROOT/'reports/m4-joint27-startup/controls-build-r1'
  receipt=json.loads(pin(ancestor/'report.json').read_text(encoding='utf-8-sig'));assert receipt['passed'] and not receipt['worker_executed']
  for p,h in json.loads(pin(ancestor/'pins.json').read_text(encoding='utf-8-sig'))['files'].items():pin(p,h)
  for level in ('O0','O2'):
   recipe=json.loads(pin(ancestor/f'{level}-sealed-recipe.json').read_text(encoding='utf-8-sig'))
   for p,h in recipe['source_bindings'].items()|recipe['objects'].items():pin(p,h)
   worker=pin(recipe['worker'],recipe['worker_sha256']);game=pin(ROOT/'MW3/Mech3.exe',recipe['game_sha256']);provider=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL',recipe['provider_sha256'])
   # Only the output path changes. No guest input, component or behavior changes.
   args=list(map(str,(worker,game,provider,out/level)))
   result=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=120)
   (out/f'{level}.stdout').write_bytes(result.stdout);(out/f'{level}.stderr').write_bytes(result.stderr)
   commands.append({'arguments':args,'exit_code':result.returncode,'worker_sha256':sha(worker)})
   assert result.returncode==0,(level,result.stderr.decode(errors='replace'))
   counts=json.loads(pin(out/level/'counts.json').read_text());assert counts['scenarios']==51 and counts['records']==102 and counts['stride']==124604
   raw=pin(out/level/'controls.bin');assert raw.stat().st_size==24+102*124604
   print(json.dumps({'level':level,'passed':True,'counts':counts}),flush=True)
 except Exception:failure=traceback.format_exc();(out/'failure.txt').write_text(failure)
 report={'passed':failure is None,'failure':failure,'scope':'Actual native frozen whole-loop control execution; independent raw review required','commands':commands,'source_fixture_unchanged':True,'scenarios':102 if failure is None else None,'actual_records':204 if failure is None else None,'original_executed':False,'whole_M4_complete':False}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(__file__);pin(sys.executable)
 for p in out.rglob('*'):
  if p.is_file():pin(p)
 (out/'pins.json').write_text(json.dumps({'files':PINS},indent=2)+'\n')
 if failure:raise RuntimeError(failure)
if __name__=='__main__':main(sys.argv[1])
