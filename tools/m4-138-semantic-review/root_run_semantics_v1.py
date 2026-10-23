"""Run admitted bounded semantic replay; retains failures and terminal receipt."""
from pathlib import Path
import hashlib,json,subprocess,sys,time,traceback
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
out=R/'reports/m4-138-semantic-review/root-semantic-execution-r1'
assert not out.exists();out.mkdir(parents=True)
admission=R/'reports/m4-138-semantic-review/root-admission-r1/report.json'
expected='72790014fab99fad38b91d9a404e47b6ac306b7ad52aa348cc6f1345c8ed7e38'
assert sha(admission)==expected
d=json.loads(admission.read_bytes());assert d['passed']and d['independent_review']and d['semantic_main_admitted']
driver=R/'tools/m4-138-semantic-review/review_paired138_v3.py';assert sha(driver)==d['files'][str(driver)]
command=[sys.executable,'-B',str(driver),'reports/m4-startup138-paired/paired-r5/report.json','reports/m4-joint-startup138-source/combined-source-provider-r6/report.json','semantic-review-r1']
assert not(R/'reports/m4-138-semantic-review/semantic-review-r1').exists()
started=time.monotonic();code=None;failure=None
try:
 with(out/'stdout.txt').open('wb')as stdout,(out/'stderr.txt').open('wb')as stderr:
  child=subprocess.Popen(command,cwd=R,stdout=stdout,stderr=stderr)
  (out/'running.json').write_text(json.dumps(dict(pid=child.pid,command=command,admission_sha256=expected),indent=2)+'\n');print(json.dumps({'pid':child.pid}),flush=True)
  code=child.wait(timeout=1800)
except Exception:
 failure=traceback.format_exc()
 if 'child'in globals()and child.poll()is None:child.kill();child.wait()
finally:
 files={str(admission):expected,str(driver):sha(driver),str(Path(__file__).resolve()):sha(__file__)}
 for name in('stdout.txt','stderr.txt','running.json'):files[str(out/name)]=sha(out/name)
 source=R/'reports/m4-138-semantic-review/semantic-review-r1/report.json';current=json.loads(source.read_bytes())if source.exists()else{}
 if source.exists():files[str(source)]=sha(source)
 stable=all(sha(p)==h for p,h in d['files'].items())
 report=dict(passed=code==0 and current.get('passed')is True and stable,exit_code=code,elapsed_seconds=time.monotonic()-started,command=command,failure=failure,admitted_inputs_unchanged=stable,semantic_report_sha256=sha(source)if source.exists()else None,initializer_credit=0,files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'exit_code':code,'report_sha256':sha(out/'report.json')}),flush=True)
raise SystemExit(0 if report['passed']else 1)
