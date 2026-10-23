"""Fix retained ancestor dependency paths without changing validation gates."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=R/'tools/m4-138-validation-review/validate_constructor_input_capture_v2.py'
assert sha(p)=='41133f12faeb9cc83c1f6091cb0979ae4697dbf14c4c02ea3f053fd299c9d942'
s=p.read_text();line=next(v for v in s.splitlines() if "pin(__file__);pin(Path(__file__).with_name('validate.py'))" in v)
fixed=line.replace("Path(__file__).with_name(","(ROOT/'tools/m4-constructor-original').joinpath(")
assert s.count(line)==1
t=s.replace(line,fixed)
assert t.replace(fixed,line)==s
q=p.with_name('validate_constructor_input_capture_v3.py');assert not q.exists();q.write_text(t)
out=R/'reports/m4-138-validation-review/constructor-validator-path-fix-r1';assert not out.exists();out.mkdir()
pins={str(x.resolve()):sha(x) for x in (p,q,Path(__file__))}
report=dict(passed=True,exact_inverse=True,scope='Only retained validator ancestor paths move to existing parent directory; complete observed gates unchanged.',initializer_credit=0,files=pins,before=line,after=fixed)
f=out/'report.json';f.write_text(json.dumps(report,indent=2)+'\n');print(sha(f))
