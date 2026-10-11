"""Freeze the exact producer-key-only validator repair before its reader."""
from pathlib import Path
import ast
h=Path(__file__).resolve().parent;t=(h/'seal_validator_v6.py').read_text();out=h/'seal_validator_v7.py'
if out.exists():raise ValueError('Fresh additive controller required')
for a,b in [("'validate_v6.py','derive_validator_v2.py'","'validate_v6.py','validate_v7.py','derive_validator_v2.py'"),("'derive_validator_v5.py','derive_validator_v6.py')","'derive_validator_v5.py','derive_validator_v6.py','derive_validator_v7.py')"),("'tools/m4-constructor-original/derive_seal_validator_v6.py')","'tools/m4-constructor-original/derive_seal_validator_v6.py','tools/m4-constructor-original/seal_validator_v6.py','tools/m4-constructor-original/derive_seal_validator_v7.py','reports/m4-constructor-original/cleanup-diagnostic-r1/report.json')"),("validator_path=str(R/'tools/m4-constructor-original/validate_v6.py'),validator_sha256=sha(R/'tools/m4-constructor-original/validate_v6.py')","validator_path=str(R/'tools/m4-constructor-original/validate_v7.py'),validator_sha256=sha(R/'tools/m4-constructor-original/validate_v7.py')"),("'All ordered actual allocation/free/reallocation occurrence transitions and whole cleanup metadata from validator3'","'All ordered actual allocation/free/reallocation occurrence transitions and whole cleanup metadata from validator3','Exact current out.append cleanup producer keys; uniqueness/fullmetadata/capacity/returned/exhaustive live-new ownership guards unchanged'")]:
    if t.count(a)!=1:raise ValueError('Exact frozen controller hunk '+a)
    t=t.replace(a,b,1)
ast.parse(t);out.write_text(t)
