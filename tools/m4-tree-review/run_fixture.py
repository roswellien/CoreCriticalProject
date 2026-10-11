"""Run only the two compiled isolated tree workers; seal diagnostics on failure."""
from pathlib import Path
import hashlib,json,subprocess,sys,time,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]

def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main(buildpath,digest,name):
 out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir(parents=True)
 pins,workers={},{};passed=False
 def pin(p,h=None):
  p=Path(p).resolve();a=sha(p);assert h is None or a==h,(str(p),h,a);assert str(p)not in pins or pins[str(p)]==a;pins[str(p)]=a;return p
 try:
  b=json.loads(pin(buildpath,digest).read_bytes());assert b['passed']
  for p,h in b['sources'].items():pin(p,h)
  pin(__file__)
  game=pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
  cp=pin(R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a')
  crt=pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
  mfc=pin(R/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8')
  for level in('O0','O2'):
   worker=pin(b['workers'][level]['path'],b['workers'][level]['sha256']);dest=out/level
   start=time.perf_counter();r=subprocess.run(list(map(str,(worker,game,cp,crt,mfc,dest))),cwd=R,capture_output=True,timeout=90,creationflags=0x08000000)
   elapsed=time.perf_counter()-start;(out/f'{level}.stdout').write_bytes(r.stdout);(out/f'{level}.stderr').write_bytes(r.stderr)
   transport=dest/'transport.json'
   if transport.is_file():
    t=json.loads(pin(transport).read_bytes())
    for part in t['parts']:pin(dest/part['bundle'],part['sha256'])
   workers[level]=dict(exit_code=r.returncode,seconds=elapsed,transport=str(transport)if transport.is_file()else None,transport_sha256=sha(transport)if transport.is_file()else None)
   print(json.dumps(dict(level=level,exit_code=r.returncode,seconds=elapsed,stderr=r.stderr.decode(errors='replace')[:500])),flush=True)
  for p,h in pins.items():assert sha(p)==h,(p,h)
  passed=all(x['exit_code']==0 for x in workers.values())
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
 finally:
  report=dict(passed=passed,scope='Actual Runtime-selected isolated O0/O2 tree smoke; preparatory owner predicate and full source/control acceptance remain separate',build_path=str(buildpath),build_sha256=digest,
              native_preparation=b['native_preparation']if'b'in locals()else None,native_preparation_sha256=b['native_preparation_sha256']if'b'in locals()else None,
              workers=workers,native_executed=True,selected_roots=1,initializer_credit=0,full_M4_complete=False,files=pins)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
  print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'))))

if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
