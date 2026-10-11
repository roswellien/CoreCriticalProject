"""Remove an inert diagnostic expression before first current writer."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=R/'reports/m4-fps-native'/name;assert not out.exists();out.mkdir();parent=R/'tools/m4-fps-native/run_fixture_v2.py';target=R/'tools/m4-fps-native/run_fixture_v3.py';assert not target.exists();t=parent.read_text();a="pin(Path(str(stem)+'-after.bin').read_bytes() if False else Path(str(stem)+'-after.bin')).read_bytes()";b="pin(Path(str(stem)+'-after.bin')).read_bytes()";assert t.count(a)==1;t=t.replace(a,b);ast.parse(t);target.write_text(t)
 pp=R/'reports/m4-fps-native/controller-preparation-r2/report.json';prior=json.loads(pp.read_bytes());pins=dict(prior['files']);pins.update({str(p.resolve()):sha(p)for p in(pp,parent,target,Path(__file__))});report=dict(prior);report.update(parent_controller_preparation_sha256=sha(pp),controller=str(target),controller_sha256=sha(target),source_changes=[dict(before=a,after=b,count=1,semantic_effect=False)],files=pins);q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(q,sha(q))
if __name__=='__main__':main(sys.argv[1])
