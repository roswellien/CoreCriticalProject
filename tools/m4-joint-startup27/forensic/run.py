"""No acceptance: retain repeated frozen-large-frame diagnostic outcomes."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'reports/m4-joint-startup27'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
out=Path(sys.argv[1]).resolve();assert out.parent==BASE and not out.exists();out.mkdir(parents=True)
build=BASE/'forensic-build-r1';b=json.loads((build/'build.json').read_text());assert b['passed'] and not b['guest_executed']
pins=json.loads((build/'pins.json').read_text())['files'];pins[str(build/'build.json')]=sha(build/'build.json');pins[str(build/'pins.json')]=sha(build/'pins.json')
for p,h in pins.items():assert sha(p)==h,(p,h)
worker=Path(b['workers']['O2']['path']);assert sha(worker)==b['workers']['O2']['sha256']
results=[]
for i in range(6):
 args=list(map(str,(worker,ROOT/'MW3/Mech3.exe',ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL',out/f'attempt-{i}')));r=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=90)
 (out/f'attempt-{i}.stdout').write_bytes(r.stdout);(out/f'attempt-{i}.stderr').write_bytes(r.stderr)
 labels=[{'kind':int(k),'cw':int(cw),'retry':int(retry)}for k,cw,retry in re.findall(r'CONTROL_FAIL kind=(\d+) cw=(\d+) retry=(\d+)',r.stderr.decode(errors='replace'))]
 results.append({'arguments':args,'exit_code':r.returncode,'failure_labels':labels});print(json.dumps({'attempt':i,'exit_code':r.returncode,'labels':labels}),flush=True)
 if labels:break
report={'passed':False,'scope':'Diagnostic frozen large-frame Context with volatile kind/CW/retry marks; no pre-Host function call; observed outcomes only, no acceptance','outcomes':results,'localized_failure':any(x['failure_labels']for x in results),'whole_M4_complete':False}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
pins[str(Path(__file__).resolve())]=sha(__file__)
for p in out.rglob('*'):
 if p.is_file():pins[str(p)]=sha(p)
(out/'pins.json').write_text(json.dumps({'files':pins},indent=2)+'\n')
