"""Preserve ROOT3 closed frontier and additionally invert/bind exact checker5."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-138-preresource-strict-review/admission-builder-preparation-r4';assert not out.exists();out.mkdir()
 parent=R/'tools/m4-138-preresource-strict-review/root_admission_builder_v3.py';assert sha(parent)=='e981fb6f993bd87a4b349a0c06cc1c18bb30a80befe95fcdee36b10f43f1ca16'
 s=parent.read_text();d=[];p5=R/'reports/m4-138-preresource-strict-review/preparation-r5/report.json';v=json.loads(p5.read_bytes());assert v['passed']and v['exact_hunks']==1
 def change(a,b,n=1):
  nonlocal s
  assert s.count(a)==n;s=s.replace(a,b);d.append(dict(before=a,after=b,count=n))
 old="'b30f479ddedae272549417c4b764d59e252ae918973d1ffd114ea0bc13b01a77']"
 change(old,old[:-1]+",'"+sha(p5)+"']")
 change(" 'reports/m4-138-preresource-strict-review/preparation-r4/verify_case_v4.py',"," 'reports/m4-138-preresource-strict-review/preparation-r5/verify_case_v5.py',")
 marker=" need('ROOT=Path(__file__).resolve().parents[3]'in v4"
 extra=""" v5=source_text(prep/'preparation-r5/verify_case_v5.py');ds=read(prep/'preparation-r5/exact-deltas.json');need(len(ds)==1 and invert(v5,ds)==v4,'Exactly one current ROOT admission own-path+SHA pin exception inverse');inverses.append(1)
 need("(p==admission_path and v==admission_sha)or p.is_relative_to(out.resolve())or admitted.get(str(p))==v"in v5,'Only exact already-authenticated current admission exception')
 need("for q,h in pins.items():eq(sha(q),h"in v5,'Every final entire physical dependency rehash retained')
 need('ROOT=Path(__file__).resolve().parents[3]'in v4"""
 change(marker,extra)
 change("strict_checker=str(prep/'preparation-r4/verify_case_v4.py'),strict_checker_sha256=sha(prep/'preparation-r4/verify_case_v4.py')", "strict_checker=str(prep/'preparation-r5/verify_case_v5.py'),strict_checker_sha256=sha(prep/'preparation-r5/verify_case_v5.py')")
 inverse=s
 for h in reversed(d):assert inverse.count(h['after'])==h['count'];inverse=inverse.replace(h['after'],h['before'])
 assert inverse==parent.read_text();ast.parse(s);q=parent.with_name('root_admission_builder_v4.py');assert not q.exists();q.write_text(s)
 (out/'exact-deltas.json').write_text(json.dumps(d,indent=2)+'\n')
 files={str(p):sha(p)for p in(parent,q,Path(__file__),p5,out/'exact-deltas.json',R/'reports/m4-138-preresource-strict-review/root-admission-builder-preparation-r3/report.json')}
 (out/'report.json').write_text(json.dumps(dict(passed=True,scope='Unexecuted ROOT3 admission frontier retained; exact checker5 preparation/hash/inverse/current-target bindings added',whole_parent_inverse=True,exact_hunks=len(d),builder_executed=False,checker_executed=False,worker_executed=False,initializer_credit=0,files=files),indent=2)+'\n');print(json.dumps(dict(report_sha256=sha(out/'report.json'),builder_sha256=sha(q))))
if __name__=='__main__':main()
