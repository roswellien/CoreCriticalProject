"""Compile independently admitted source; no worker execution."""
from pathlib import Path
import hashlib,json,subprocess,sys,time,shutil,traceback
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
ad=R/'reports/m4-original141/root-build-admission-r3/report.json';expected='f39994820f8b7650c65cc93d9c71ce93a0ef682f4c0d34b7c517e574c20a36a3'
assert sha(ad)==expected;d=json.loads(ad.read_bytes());assert d['passed']and d['compile_admitted']and not d['worker_launch_admitted']
for p,h in d['files'].items():assert sha(p)==h
out=R/'reports/m4-original141/root-build-execution-r1';assert not out.exists();out.mkdir()
shell=Path(shutil.which('pwsh')).resolve();script=R/'tools/m4-141-consumer-review/build_original141.ps1';prep=R/'reports/m4-original141/source-preparation-r2'
cmd=[str(shell),'-NoProfile','-File',str(script),'-Preparation',str(prep),'-PreparationSha256','7c1acf0bb08043cf8a371a6b31d7fc3f4071771dae936a748abad66969c8cbd8','-Output',str(R/'reports/m4-original141/build-r1')]
t=time.monotonic();code=None;failure=None
try:
 with(out/'stdout.txt').open('wb')as stdout,(out/'stderr.txt').open('wb')as stderr:
  child=subprocess.Popen(cmd,cwd=R,stdout=stdout,stderr=stderr)
  (out/'running.json').write_text(json.dumps(dict(pid=child.pid,command=cmd),indent=2)+'\n');print(json.dumps(dict(pid=child.pid,command=cmd)),flush=True);code=child.wait(timeout=3600)
except Exception:failure=traceback.format_exc()
finally:
 if 'child'in globals()and child.poll()is None:child.kill();child.wait()
 build=R/'reports/m4-original141/build-r1/build.json';b=json.loads(build.read_bytes())if build.exists()else{}
 closed=all(sha(p)==h for p,h in d['files'].items());files={str(ad):expected,str(Path(__file__).resolve()):sha(__file__),str(shell):sha(shell)}
 for p in out.iterdir():files[str(p)]=sha(p)
 if build.exists():files[str(build)]=sha(build)
 report=dict(passed=code==0 and b.get('passed')is True and closed,exit_code=code,elapsed_seconds=time.monotonic()-t,command=cmd,failure=failure,admitted_inputs_unchanged=closed,worker_executed=False,worker_launch_admitted=False,initializer_credit=0,files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=report['passed'],exit_code=code,report_sha256=sha(out/'report.json'))),flush=True)
raise SystemExit(0 if report['passed']else 1)
