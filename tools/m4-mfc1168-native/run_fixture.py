"""Fresh bounded actual writer only; source verification is separate."""
from pathlib import Path
import hashlib,json,subprocess,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(build,digest,name):
 out=R/'reports/m4-mfc1168-native'/name;assert not out.exists();out.mkdir();pins={};runs={};passed=False
 def pin(p,h=None):
  p=Path(p).resolve();a=sha(p);assert h is None or a==h,(p,h,a);assert str(p)not in pins or pins[str(p)]==a;pins[str(p)]=a;return p
 try:
  b=json.loads(pin(build,digest).read_bytes());assert b['passed'];prep=json.loads(pin(b['preparation'],b['preparation_sha256']).read_bytes());assert prep['passed']
  for q,h in b['files'].items():pin(q,h)
  pin(__file__);pin(sys.executable);image=pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');pack=pin(prep['input_pack'])
  for level in('O0','O2'):
   worker=pin(b['workers'][level]['path'],b['workers'][level]['sha256']);target=out/level;args=[str(worker),str(image),str(pack),str(target)];r=subprocess.run(args,cwd=R,capture_output=True,timeout=45,creationflags=0x08000000)
   (out/f'{level}.stdout').write_bytes(r.stdout);(out/f'{level}.stderr').write_bytes(r.stderr);runs[level]=dict(arguments=args,exit_code=r.returncode);print(json.dumps(dict(level=level,exit_code=r.returncode)),flush=True);assert r.returncode==0,(level,r.stderr.decode(errors='replace'))
   assert pin(target/'COMPLETE.txt').read_bytes()==b'complete';runs[level]['outputs']={str(q):sha(q)for q in target.rglob('*')if q.is_file()}
  for q,h in pins.items():assert sha(q)==h
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Actual isolated native O0/O2 one registered MFC1168 cached root; source equality pending',build=str(build),build_sha256=digest,runs=runs,files=pins,native_executed=passed,initializer_credit=0,capture_archive_reader_opened=False,all_workers_terminal=True)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
