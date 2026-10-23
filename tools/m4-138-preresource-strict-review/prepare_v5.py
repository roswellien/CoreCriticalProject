"""Exact current ROOT admission receipt exception; no external pin relaxation."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-138-preresource-strict-review/preparation-r5';assert not out.exists();out.mkdir()
 parent=R/'reports/m4-138-preresource-strict-review/preparation-r4/verify_case_v4.py';s=parent.read_text()
 a="need(p.is_relative_to(out.resolve())or admitted.get(str(p))==v,'Every external ordinary dependency admitted before use')"
 b="need((p==admission_path and v==admission_sha)or p.is_relative_to(out.resolve())or admitted.get(str(p))==v,'Every external ordinary dependency admitted before use')"
 assert s.count(a)==1;t=s.replace(a,b);assert t.count(b)==1 and t.replace(b,a)==s;ast.parse(t)
 q=out/'verify_case_v5.py';q.write_text(t);(out/'exact-deltas.json').write_text(json.dumps([dict(before=a,after=b)],indent=2)+'\n')
 files={str(p):sha(p)for p in(parent,q,Path(__file__),out/'exact-deltas.json')}
 (out/'report.json').write_text(json.dumps(dict(passed=True,scope='Exact immutable already-authenticated current ROOT admission path+SHA allowed during final complete dependency rehash; every other input still admitted/output constrained',whole_parent_inverse=True,exact_hunks=1,final_entire_rehash_retained=True,admission_initial_authentication_retained=True,external_pin_fallback_added=False,retained_failed_strict_mode7_sha256='9c14006e287041e2aacc30966137ddca774cfc5a739df0bb22e5ba7689617f63',checker_executed=False,worker_executed=False,initializer_credit=0,files=files),indent=2)+'\n');print(json.dumps(dict(report_sha256=sha(out/'report.json'),checker_sha256=sha(q))))
if __name__=='__main__':main()
