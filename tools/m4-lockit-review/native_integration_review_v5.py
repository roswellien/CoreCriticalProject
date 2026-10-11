"""Physical publication correction: each instance slot is its proven objectESI+4."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).resolve().parent/'native_integration_review_v4.py'
s=p.read_text(encoding='utf-8')
old="row['operands']==f'dword ptr [0x{publication:x}], eax'"
new="(row['operands']==f'dword ptr [0x{publication:x}], eax' or (publication==obj+4 and row['operands']=='dword ptr [esi + 0x4], eax' and any(r['mnemonic']=='mov' and r['operands']==f'ecx, 0x{obj:x}' for r in literal_rows.values())))"
assert s.count(old)==1
exec(compile(s.replace(old,new),str(p),'exec'),globals())
