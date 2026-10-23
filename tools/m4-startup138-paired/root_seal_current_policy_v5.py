"""Correct transcript hash to the actual existing ROOT policy2 dependency."""
from pathlib import Path
import hashlib,json
p=Path(__file__).with_name('root_seal_current_policy_v4.py');s=p.read_text()
old='804becc86bbeaad3c991dbdeb166e07f4c4bbf60ee2598fc4f1a910ef2529e97';new='d484982603ab920ab2d6824bda43b400182dd29a5c7a0185830bad69e97db43f'
assert s.count(old)==2
receipt=Path(__file__).resolve().parents[2]/'reports/m4-startup138-paired/root-policy-admission-r2/report.json'
with receipt.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()=='580ac018cbf834644863a52f2edb64f8b754b77d4b2addf10de358bfd0c89029'
v=json.loads(receipt.read_bytes());assert v['files'][str(p.with_name('root_seal_current_policy_v3.py'))]==new
s=s.replace(old,new);exec(compile(s,str(p),'exec'))
