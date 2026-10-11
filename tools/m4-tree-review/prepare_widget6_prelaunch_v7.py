"""Allow only the reviewed service include-path transition."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def main(name):
    out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir(parents=True)
    p=R/'tools/m4-tree-review/review_widget6_prelaunch_v6.py';t=p.read_text()
    a="            assert pin(base / 'fixture-preparation-r12'/leaf).read_bytes()==pin(base / 'fixture-preparation-r9'/leaf).read_bytes()"
    b="            current=pin(base / 'fixture-preparation-r12'/leaf).read_bytes();prior=pin(base / 'fixture-preparation-r9'/leaf).read_bytes()\n            if leaf=='inherited_main.cpp':\n                old_path=b'D:/Projects/MW34Recomp/reports/m4-widget-native/service-preparation-r2/session.hpp'\n                new_path=b'D:/Projects/MW34Recomp/reports/m4-widget-native/service-preparation-r3/session.hpp'\n                assert prior.count(old_path)==1 and current.count(new_path)==1\n                prior=prior.replace(old_path,new_path)\n            assert current==prior"
    assert t.count(a)==1;t=t.replace(a,b);ast.parse(t)
    q=R/'tools/m4-tree-review/review_widget6_prelaunch_v7.py';assert not q.exists();q.write_text(t)
    files={str(x.resolve()):hashlib.sha256(x.read_bytes()).hexdigest()for x in(p,q,Path(__file__))}
    r=dict(passed=True,scope='Unexecuted exact one inherited session include path transition to physically reviewed service3; every fixture byte otherwise unchanged and all physical link checks retained',changes=[dict(before=a,after=b)],files=files,capture_reader_opened=False,worker_executed=False,initializer_credit=0)
    f=out/'report.json';f.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=hashlib.sha256(f.read_bytes()).hexdigest())))
if __name__=='__main__':main(sys.argv[1])
