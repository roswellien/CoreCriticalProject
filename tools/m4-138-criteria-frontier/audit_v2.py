"""Additive recommendation-schema correction; all bounded proof predicates retained."""
from pathlib import Path
import hashlib
p=Path(__file__).with_name('audit_v1.py')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='bc2151ce1aafca7077ce58a0326d3300309738e7e81d3c98d182510430232c8f'
s=p.read_text()
changes=[
 ("candidate=dict(proof_file='current-original-MFC-corroborations.json',field=f,expected=value)","candidate=dict(path=str(out/'report.json'),field='current_original_MFC_counts.'+f[7:],expected=value,whole_witness_file='current-original-MFC-corroborations.json')"),
 ("candidate=dict(path=str(hp if f=='helper_sha256' else Path(pp['comparer'])),sha256=value,expected=value)","candidate=dict(path=str(out/'report.json'),field='policy_helper_sha256' if f=='helper_sha256' else 'current_comparer_sha256',expected=value,physical_source_path=str(hp if f=='helper_sha256' else Path(pp['comparer'])))"),
 ("pin(__file__);pin(sys.executable)","pin(p,'bc2151ce1aafca7077ce58a0326d3300309738e7e81d3c98d182510430232c8f');pin(__file__);pin(sys.executable)"),
 ("current_original_MFC_counts=dict(counts),historical_legacy", "current_original_MFC_counts=dict(counts),policy_helper_sha256=PINS[str(hp)],current_comparer_sha256=pp['comparer_sha256'],historical_legacy")
]
for a,b in changes:
 assert s.count(a)==1
 s=s.replace(a,b)
exec(compile(s,str(Path(__file__).resolve()),'exec'),globals())
