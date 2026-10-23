"""Repeat admitted controls with accurate actual-normal fixture attribution."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
ad=R/'reports/m4-141-consumer-review/root-source-admission-r4/report.json'
assert sha(ad)=='0786193d656f797fbdf2af4bd35232cc3a62780791333222bfb88de2d71058ab'
d=json.loads(ad.read_bytes());assert d['passed']
for p,h in d['files'].items():assert sha(p)==h
p=R/'reports/m4-141-consumer-review/root-source-admission-r4/FS-controls.py'
t=p.read_text();changes=[('root-FS-domain-controls-r2','root-FS-domain-controls-r4'),('normal_fixture_is_synthetic=True','normal_fixture_is_synthetic=False'),('Retained actual source-computed component fixture plus synthetic inherited normal scaffolding; genuine current native constructor journals were compared by failed full source run, current global native cardinality diagnostic remains ROOT-owned.','Actual native normal28/56 diagnostic bytes with retained source-computed constructor fixture; source control fixture is not genuine constructor runtime equivalence.')]
for a,b in changes:assert t.count(a)==1;t=t.replace(a,b)
a="files={str(p):sha(p),";b="files={str(ad):sha(ad),str(physical_normal/'fs-frame-witnesses.bin'):sha(physical_normal/'fs-frame-witnesses.bin'),str(physical_normal/'fs-record-bytes.bin'):sha(physical_normal/'fs-record-bytes.bin'),str(Path(__file__).resolve()):sha(Path(__file__)),str(root_control_derivative):sha(root_control_derivative),str(p):sha(p),"
assert t.count(a)==1;t=t.replace(a,b)
out=R/'reports/m4-141-consumer-review/root-actual-FS-controls-preparation-r3';assert not out.exists();out.mkdir()
q=out/'controls.py';q.write_text(t)
ns={'__name__':'root_FS_actual','__file__':str(R/'tools/m4-141-consumer-review/FS_domain_controls_v2.py'),'ad':ad,'root_control_derivative':q};exec(compile(t,str(q),'exec'),ns);ns['main']()
for p,h in d['files'].items():assert sha(p)==h
print(json.dumps(dict(admitted_inputs_unchanged=True,tool_sha256=sha(__file__),derivative_sha256=sha(q))))
