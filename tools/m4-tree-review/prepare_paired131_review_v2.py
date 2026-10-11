"""Add a full finite MFC rederivation to the inherited paired reviewer."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def main(name):
    out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir(parents=True)
    p=R/'tools/m4-tree-review/review_paired131.py';t=p.read_text()
    a="        counts['paired_comparer_exact_preflight_bound']=1"
    b="        import review_mfc_pair131 as MP\n        pin(MP.__file__);counts.update(MP.compare(paired_report,report,source_report,source,pin))\n"+a
    assert t.count(a)==1;t=t.replace(a,b);ast.parse(t)
    q=R/'tools/m4-tree-review/review_paired131_v2.py';assert not q.exists();q.write_text(t)
    files={str(x.resolve()):hashlib.sha256(x.read_bytes()).hexdigest()for x in(p,q,R/'tools/m4-tree-review/review_mfc_pair131.py',Path(__file__))}
    r=dict(passed=True,scope='Unexecuted additive independent full finite MFC paired rederivation from raw equality targets and genuine original/persistent native source; exact entire12 exported paired rows plus counters, no canonical archives opened',changes=[dict(before=a,after=b)],files=files,capture_reader_opened=False,worker_executed=False,initializer_credit=0)
    f=out/'report.json';f.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=hashlib.sha256(f.read_bytes()).hexdigest())))
if __name__=='__main__':main(sys.argv[1])
