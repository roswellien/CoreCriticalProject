"""Fix inherited receipt paths and bind the frozen current reader6."""
from pathlib import Path
import ast, hashlib, json, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def main(name):
    out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir(parents=True)
    files={};changes={}
    def pin(p,h=None):
        p=Path(p).resolve();v=hashlib.sha256(p.read_bytes()).hexdigest();assert h is None or v==h;files[str(p)]=v;return p
    pin(R/'reports/m4-tree-review/provider131-review-preparation-r1/report.json','de5a680f9e719a93080816b3e1a33ebfa66bea321ec8f7b38c6ec31cc458ae49')
    for old,new in [('review_provider131.py','review_provider131_v2.py'),('seal_source131_closure.py','seal_source131_closure_v2.py')]:
        text=pin(R/'tools/m4-tree-review'/old).read_text();delta=[]
        for a,b in [('reports/m4-formatting-source/provider131-preflight-r4','reports/m4-formatting-source/provider130-preflight-r4'),('tools/m4-joint-startup131/compare_provider_v5.py','tools/m4-joint-startup131/compare_provider_v6.py')]:
            assert text.count(a)==1;text=text.replace(a,b);delta.append(dict(before=a,after=b))
        if old.startswith('review_provider'):
            a='reports/m4-formatting-source/provider131-preparation-r8';b='reports/m4-formatting-source/provider130-preparation-r8';assert text.count(a)==1;text=text.replace(a,b);delta.append(dict(before=a,after=b))
        marker='  boundary=' if old.startswith('review_provider') else "  for q,h in source['files'].items():"
        extra="  current_preparation=read(R/'reports/m4-joint-startup131-source/preparation-r6/report.json','fb90b0dc1d47b9fc89878049100a957d10ad6638bc718e8eff32b04ad861b6f8');current_preflight=read(R/'reports/m4-tree-review/joint131-source-preflight-r4/report.json','efba70d0a02bb89fd95f87eb4707f138e48444b4cb8cc076389c80bec32ad2f2')\n  need(current_preparation['passed']and current_preflight['passed']and current_preflight['capture_reader_opened']is False,'Exact current reader6 representation repair independently admitted')\n  for record in(current_preparation,current_preflight):\n   for q,h in record['files'].items():pin(q,h)\n"
        assert marker in text;text=text.replace(marker,extra+marker,1);delta.append(dict(before=marker,after=extra+marker))
        ast.parse(text);q=R/'tools/m4-tree-review'/new;assert not q.exists();q.write_text(text);pin(q);changes[new]=delta
    pin(__file__)
    r=dict(passed=True,scope='Unexecuted additive inherited130 receipt path repair and exact current reader6/preflight binding; all measured provider, physical API and dependency closure comparisons unchanged',changes=changes,files=files,capture_reader_opened=False,worker_executed=False,initializer_credit=0)
    f=out/'report.json';f.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=hashlib.sha256(f.read_bytes()).hexdigest())))
if __name__=='__main__':main(sys.argv[1])
