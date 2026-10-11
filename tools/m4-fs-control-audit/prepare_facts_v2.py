"""Additive correction of archive logical name, no candidate changes."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-fs-control-audit/facts.py'
o=R/'reports/m4-fs-control-audit/facts-r1/report.json'
assert not o.exists()
o.write_text(json.dumps({'passed':False,'checker_failure':'Wrong assumed logical name mfc-witnesses.bin; actual existing name mfc-allocation-witnesses.bin','candidate_failure':False,'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest()},indent=2)+'\n')
s=p.read_text();assert s.count('mfc-witnesses.bin')==1
t=p.with_name('facts_v2.py');assert not t.exists();t.write_text(s.replace('mfc-witnesses.bin','mfc-allocation-witnesses.bin'))
