"""Limit the physical loop initializer search to its dominating prefix."""
from pathlib import Path
import hashlib,sys
sys.dont_write_bytecode=True
p=Path(__file__).parent; parent=p/'audit_legacy_flags.py'
assert hashlib.sha256(parent.read_bytes()).hexdigest()=='8ae272710976a6398515c255756e68a0f81d6c880223ef24fd3814e8521674d6'
text=parent.read_text().replace('module.PE(image)','module.PEImage(image)')
old="r['mnemonic']=='mov' and r['operands'].startswith('ecx,')"
assert text.count(old)==1
text=text.replace(old,"r['pc'] < body and r['mnemonic']=='mov' and r['operands'].startswith('ecx,')")
text=text.replace('pin(__file__); pin(sys.executable)',"pin(p/'audit_legacy_flags_v3.py'); pin(parent); pin(sys.executable)")
exec(compile(text,str(parent),'exec'),globals())
