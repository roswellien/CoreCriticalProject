"""Join the raw exporter to its actual canonical transport metadata."""
from pathlib import Path
import hashlib,json,sys,ast
R=Path(__file__).resolve().parents[2]
def main(name):
    out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir(parents=True)
    p=R/'tools/m4-tree-review/review_original131_combined.py';t=p.read_text()
    a="need(raw_export['capture_sha256']==v['original_capture_sha256'],'Whole canonical original identity retained by raw exporter')"
    b="need(Path(raw_export['transport_path']).resolve()==Path(v['original_capture']).resolve()and raw_export['transport_sha256']==sha(pin(v['original_capture'])),'Whole canonical original transport identity retained by raw exporter')"
    assert t.count(a)==1;t=t.replace(a,b);ast.parse(t)
    q=R/'tools/m4-tree-review/review_original131_combined_v2.py';assert not q.exists();q.write_text(t)
    files={str(x.resolve()):hashlib.sha256(x.read_bytes()).hexdigest()for x in(p,q,Path(__file__))}
    r=dict(passed=True,scope='Unexecuted exact exporter-schema transport path/full SHA join; all inherited source and byteflow review predicates unchanged',changes=[dict(before=a,after=b)],files=files,capture_reader_opened=False,worker_executed=False,initializer_credit=0)
    f=out/'report.json';f.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=hashlib.sha256(f.read_bytes()).hexdigest())))
if __name__=='__main__':main(sys.argv[1])
