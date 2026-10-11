"""Freeze a request-projection-only checker repair with unchanged reader ABI."""
from pathlib import Path
import ast
h=Path(__file__).resolve().parent;t=(h/'seal_validator_v5.py').read_text();out=h/'seal_validator_v6.py'
if out.exists():raise ValueError('Fresh additive controller required')
old="'validate_v5.py','derive_validator_v2.py'";new="'validate_v5.py','validate_v6.py','derive_validator_v2.py'"
if t.count(old)!=1:raise ValueError('Exact frozen validator source inventory')
t=t.replace(old,new,1)
old="'derive_validator_v4.py','derive_validator_v5.py')";new="'derive_validator_v4.py','derive_validator_v5.py','derive_validator_v6.py')"
if t.count(old)!=1:raise ValueError('Exact frozen derivation inventory')
t=t.replace(old,new,1)
t=t.replace("'reports/m4-constructor-source/preparation-r1/contracts.json')", "'reports/m4-constructor-source/preparation-r1/contracts.json','reports/m4-constructor-original/request-rounding-r1/report.json','tools/m4-constructor-original/seal_validator_v5.py','tools/m4-constructor-original/derive_seal_validator_v6.py')",1)
t=t.replace("validator_path=str(R/'tools/m4-constructor-original/validate_v5.py'),validator_sha256=sha(R/'tools/m4-constructor-original/validate_v5.py')", "validator_path=str(R/'tools/m4-constructor-original/validate_v6.py'),validator_sha256=sha(R/'tools/m4-constructor-original/validate_v6.py')",1)
t=t.replace("'No volatile or void-return expected values copied; no original postRET snapshot claim'", "'Whole18 physical CRT instructions derive mode1 HeapAlloc request from separately retained original MFC request; all API occurrence/frame checks retained','No volatile or void-return expected values copied; no original postRET snapshot claim'",1)
ast.parse(t);out.write_text(t)
