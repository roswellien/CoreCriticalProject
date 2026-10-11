"""Use the actual frozen PEImage parser API; preserve the failed first audit."""
from pathlib import Path
import hashlib,sys
sys.dont_write_bytecode=True
p=Path(__file__).parent
parent=p/'audit_legacy_flags.py'
assert hashlib.sha256(parent.read_bytes()).hexdigest()=='8ae272710976a6398515c255756e68a0f81d6c880223ef24fd3814e8521674d6'
text=parent.read_text();assert text.count('module.PE(image)')==1
text=text.replace('module.PE(image)','module.PEImage(image)')
text=text.replace('pin(__file__); pin(sys.executable)',"pin(p/'audit_legacy_flags_v2.py'); pin(parent); pin(sys.executable)")
exec(compile(text,str(parent),'exec'),globals())
