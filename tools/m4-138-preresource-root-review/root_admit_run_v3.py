"""Seal reviewed physical prefix and bounded controller; runtime gates pending."""
from pathlib import Path
import hashlib,json,traceback
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
out=R/'reports/m4-138-preresource-root-review/root-run-admission-r1';assert not out.exists();out.mkdir();files={};passed=False
def pin(p,h=None):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or h==v;assert files.setdefault(str(p),v)==v;return p
def read(rel,h):
 d=json.loads(pin(R/rel,h).read_bytes());assert d['passed']
 for p,v in d.get('files',{}).items():pin(p,v)
 return d
try:
 base=read('reports/m4-138-preresource-root-review/root-review-r1/report.json','c86c8082f396b517b805e182c4ea4a9b4396a9e19b290bf8fc098d172e9478bb')
 controls=read('reports/m4-138-preresource-root-review/root-controls-r1/report.json','61bad667360723e3155cada04c787974a437dbea0e1086a3e1e13239d9f7b7a0');assert controls['controls']==60 and controls['actual_current_function_target_joins']==15
 budget=read('reports/m4-138-preresource-controls/run-preparation-r4/report.json','d0d5a8149729347c6242f5d08eb667decf718ed3396b904833591cb8a269fb72');assert budget['exact_inverse_restores_prior_controller']and not budget['worker_executed']and not budget['actual_payload_revalidated']
 code=pin(R/'tools/m4-138-preresource-controls/run_v3.py','a238cc72d568caa33a73367719391c67c248287171a1f8a5a8fb072d80e4effc').read_text()
 assert code.count("a='assert len(leaves)<=4096 and sum(p.stat().st_size for p in leaves)<=128*1024*1024'")==1 and code.count("b='assert len(leaves)<=100000 and sum(p.stat().st_size for p in leaves)<=512*1024*1024'")==1
 for n,b,maxleaf,expected in budget['controls']:assert (n<=100000 and b<=512*1024*1024 and maxleaf<=32*1024*1024)==expected
 for p,h in tuple(files.items()):assert sha(p)==h
 pin(__file__);passed=True
except Exception:(out/'failure.txt').write_text(traceback.format_exc())
report={k:base[k]for k in('scope_identity','ordinary_outputs_only','modes','levels','prelaunch_checks','counts')}
report.update(passed=passed,independent_review=True,source_physical_review_only=True,budget_only_controller_delta=True,current12_refusals_proven=False,TLS64_runtime_proven=False,worker_executed=False,canonical_reader_opened=False,initializer_credit=0,files=files)
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'),files=len(files))));raise SystemExit(0 if passed else 1)
