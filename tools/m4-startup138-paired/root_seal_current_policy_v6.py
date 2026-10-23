"""Close materialized wrapper-source dependencies of ROOT policy review3."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
q=R/'reports/m4-startup138-paired/root-policy-admission-r3/report.json'
assert sha(q)=='c2a46969272aa32d5450a546a85129fb668fcb8554c713947a564dbc9663d18e'
v=json.loads(q.read_bytes());assert v['passed'] and v['independent_review'] and v['whole_data_carry_adverses']==9936
for p,h in v['files'].items():assert sha(p)==h
files=dict(v['files']);files[str(q)]=sha(q)
for name in ['root_seal_current_policy_v4.py','root_seal_current_policy_v5.py','root_seal_current_policy_v6.py']:
 p=Path(__file__).with_name(name);files[str(p)]=sha(p)
v.update(files=files,review_source_dependencies_closed=True,whole_data_carry_adverses_reexecuted=False,whole_data_carry_adverses_source_receipt=str(q),whole_data_carry_adverses_source_sha256=sha(q))
out=R/'reports/m4-startup138-paired/root-policy-admission-r4';assert not out.exists();out.mkdir()
p=out/'report.json';p.write_text(json.dumps(v,indent=2)+'\n');print(sha(p))
