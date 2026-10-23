"""Execute only the independently admitted141 source consumer, with run receipt."""
from pathlib import Path
import hashlib,json,subprocess,sys,time,traceback
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
out=R/'reports/m4-141-consumer-review/root-source-execution-r6'
assert not out.exists();out.mkdir(parents=True)
admission=R/'reports/m4-141-consumer-review/root-source-admission-r7/report.json'
expected='365c88f1875c3640354df669acfd54abf593d48f8413d23ba213ff76272a4737'
assert sha(admission)==expected
d=json.loads(admission.read_bytes());assert d['passed']and d['independent_review']and d['source_consumer_admitted']
for p,h in d['files'].items():assert sha(p)==h
driver=R/'reports/m4-startup141-source/preparation-r9/compare_provider141.py'
command=[sys.executable,'-B',str(driver),'reports/m4-startup141-root/execution-r2/report.json','reports/m4-startup138-original/original-validation-r3/report.json','02ea1ce07ac3e5aa5dff6e20813b956117383784ae4f5e1ffd6aa1822f603f5f','combined-source-provider-r6']
assert not(R/'reports/m4-startup141-source/combined-source-provider-r6').exists()
t=time.monotonic();code=None;failure=None
try:
 with(out/'stdout.txt').open('wb')as stdout,(out/'stderr.txt').open('wb')as stderr:
  child=subprocess.Popen(command,cwd=R,stdout=stdout,stderr=stderr)
  (out/'running.json').write_text(json.dumps(dict(pid=child.pid,command=command,admission_sha256=expected),indent=2)+'\n')
  print(json.dumps(dict(pid=child.pid,command=command)),flush=True)
  code=child.wait(timeout=7200)
except Exception:
 failure=traceback.format_exc()
 if 'child'in globals()and child.poll()is None:child.kill();child.wait()
finally:
 files={str(admission):expected,str(driver):sha(driver),str(Path(__file__).resolve()):sha(__file__)}
 for name in('running.json','stdout.txt','stderr.txt'):files[str(out/name)]=sha(out/name)
 source=R/'reports/m4-startup141-source/combined-source-provider-r6/report.json'
 current=json.loads(source.read_bytes())if source.exists()else{}
 if source.exists():files[str(source)]=sha(source)
 closure=all(sha(p)==h for p,h in d['files'].items())
 report=dict(passed=code==0 and current.get('passed')is True and closure,exit_code=code,elapsed_seconds=time.monotonic()-t,command=command,failure=failure,admitted_inputs_unchanged=closure,source_report_sha256=sha(source)if source.exists()else None,original141_equivalence=False,initializer_credit=0,files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
raise SystemExit(0 if report['passed']else 1)
