"""Separate counted paired observations from their independent replay."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def main(name):
    out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir(parents=True)
    p=R/'tools/m4-tree-review/review_paired131_v2.py';t=p.read_text()
    a='pin(MP.__file__);counts.update(MP.compare(paired_report,report,source_report,source,pin))'
    b="pin(MP.__file__);replayed=MP.compare(paired_report,report,source_report,source,pin)\n        for key,value in replayed.items():\n            if key=='independent_full_MFC_paired_derivations':counts[key]=value\n            else:counts['independently_rederived_'+key]=value"
    assert t.count(a)==1;t=t.replace(a,b);ast.parse(t)
    q=R/'tools/m4-tree-review/review_paired131_v3.py';assert not q.exists();q.write_text(t)
    files={str(x.resolve()):hashlib.sha256(x.read_bytes()).hexdigest()for x in(p,q,Path(__file__))}
    r=dict(passed=True,scope='Unexecuted additive reporting-only independent replay counter names; every full paired equality comparison unchanged',changes=[dict(before=a,after=b)],files=files,capture_reader_opened=False,worker_executed=False,initializer_credit=0)
    f=out/'report.json';f.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=hashlib.sha256(f.read_bytes()).hexdigest())))
if __name__=='__main__':main(sys.argv[1])
