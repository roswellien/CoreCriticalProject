"""Correct preparation-only selector metadata wording; captured code unchanged."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];T=R/'tools/m4-widget-original';P=R/'reports/m4-widget-original/preparation-r5/report.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=T/'prepare_v4.py';d=json.loads(P.read_text())
if sha(P)!='fe867d85c6ac4246624467c4fe11ec9271ba5e9dcd01e6b89fba3f3c9c673c30'or sha(p)!=d['files'][str(p.resolve())]:raise ValueError('Immutable source')
s=p.read_text();a='actual_DS_ES_SS_flatness_observed=True';b='actual_DS_ES_SS_flatness_observation_prepared=True'
if s.count(a)!=1:raise ValueError('Exact wording correction')
s=s.replace(a,b,1);a=" pin(__file__);pin(R/'tools/m4-widget-original/derive_prepare_v4.py');";b=" pin(__file__);pin(R/'tools/m4-widget-original/derive_prepare_v5.py');pin(R/'tools/m4-widget-original/prepare_v4.py');pin(R/'reports/m4-widget-original/preparation-r5/report.json','fe867d85c6ac4246624467c4fe11ec9271ba5e9dcd01e6b89fba3f3c9c673c30');pin(R/'tools/m4-widget-original/derive_prepare_v4.py');"
if s.count(a)!=1:raise ValueError('Exact lineage')
s=s.replace(a,b,1);q=T/'prepare_v5.py'
if q.exists():raise ValueError('Fresh source')
q.write_text(s);print(json.dumps(dict(passed=True,source=str(q),sha256=sha(q))))
