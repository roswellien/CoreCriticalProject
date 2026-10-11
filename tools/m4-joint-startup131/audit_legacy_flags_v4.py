"""Physical two-loop ZF proof with explicit additive source pins."""
from pathlib import Path
import hashlib,sys
sys.dont_write_bytecode=True
parent=Path(__file__).parent/'audit_legacy_flags.py'
assert hashlib.sha256(parent.read_bytes()).hexdigest()=='8ae272710976a6398515c255756e68a0f81d6c880223ef24fd3814e8521674d6'
text=parent.read_text().replace('module.PE(image)','module.PEImage(image)')
old="r['mnemonic']=='mov' and r['operands'].startswith('ecx,')"
assert text.count(old)==1
text=text.replace(old,"r['pc'] < body and r['mnemonic']=='mov' and r['operands'].startswith('ecx,')")
text=text.replace('pin(__file__); pin(sys.executable)',"pin(ROOT/'tools/m4-joint-startup131/audit_legacy_flags_v4.py'); pin(ROOT/'tools/m4-joint-startup131/audit_legacy_flags.py'); pin(sys.executable)")
exec(compile(text,str(parent),'exec'),globals())
