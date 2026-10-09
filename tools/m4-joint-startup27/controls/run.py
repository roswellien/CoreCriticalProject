"""Preserve additive native whole-loop control captures and measured failures."""
from pathlib import Path
import argparse,hashlib,json,re,subprocess,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'reports/m4-joint-startup27';PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();actual=sha(p);assert h is None or actual==h,(str(p),h,actual);PINS[str(p)]=actual;return p
def main(build,out):
 build=Path(build).resolve();out=Path(out).resolve();assert build.parent==out.parent==BASE and not out.exists();out.mkdir(parents=True)
 failure=None;commands=[];labels=[];diagnostic=False
 try:
  b=json.loads(pin(build/'build.json').read_text());assert b['passed'] and not b['guest_executed'];diagnostic=b['diagnostic']
  for p,h in json.loads(pin(build/'pins.json').read_text())['files'].items():pin(p,h)
  # Retain literal current derivative alongside receipts even if a future
  # additive path supersedes it. Original frozen ancestors remain untouched.
  for p,h in b['sources'].items():
   if Path(p).is_relative_to(ROOT/'tools/m4-joint-startup27'):
    q=out/'sources'/Path(p).relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(Path(p).read_bytes());assert sha(q)==h
  game=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');provider=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a')
  for level,w in b['workers'].items():
   worker=pin(w['path'],w['sha256']);args=list(map(str,(worker,game,provider,out/level)));r=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=120)
   (out/f'{level}.stdout').write_bytes(r.stdout);(out/f'{level}.stderr').write_bytes(r.stderr);commands.append({'arguments':args,'exit_code':r.returncode,'worker_sha256':sha(worker)})
   labels.extend({'level':level,'kind':int(k),'cw':int(cw),'retry':int(retry)}for k,cw,retry in re.findall(r'CONTROL_START kind=(\d+) cw=(\d+) retry=(\d+)',r.stderr.decode(errors='replace')))
   if diagnostic:
    assert r.returncode==1 and labels,'Diagnostic must reproduce retained failure with path label'
   else:
    assert r.returncode==0,(level,r.stderr.decode(errors='replace'))
    counts=json.loads(pin(out/level/'counts.json').read_text());assert counts['scenarios']==51 and counts['records']==102 and counts['stride']==124604
    assert pin(out/level/'controls.bin').stat().st_size==24+102*124604
   print(json.dumps({'level':level,'exit_code':r.returncode,'diagnostic':diagnostic,'last_label':labels[-1]if labels else None}),flush=True)
 except Exception:failure=traceback.format_exc();(out/'failure.txt').write_text(failure)
 report={'passed':failure is None,'failure':failure,'diagnostic_only':diagnostic,'scope':'Observed retained O2 caller-state failure with last active path label; no acceptance'if diagnostic else'Actual additive outer-boundary whole-loop controls; independent raw review required','commands':commands,'path_labels':labels,'actual_records':204 if not diagnostic and failure is None else None,'scenarios':102 if not diagnostic and failure is None else None,'guest_objects_changed':False,'ordinary_game_launched':False,'whole_M4_complete':False}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(__file__);pin(sys.executable)
 for p in out.rglob('*'):
  if p.is_file():pin(p)
 (out/'pins.json').write_text(json.dumps({'files':PINS},indent=2)+'\n')
 if failure:raise RuntimeError(failure)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('build');p.add_argument('output');a=p.parse_args();main(a.build,a.output)
