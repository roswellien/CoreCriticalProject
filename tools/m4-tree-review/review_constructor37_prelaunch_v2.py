"""Include the established sparse-pack RO0 tag in whole physical page checks."""
from pathlib import Path
import hashlib,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
parent=R/'tools/m4-tree-review/review_constructor37_prelaunch.py'
assert hashlib.sha256(parent.read_bytes()).hexdigest()=='b41fb7810010189edba1ebf22f121e5c6d5db18a5adbf556840dad50b63ee67f'
text=parent.read_text()
old='permission in(1,2)';assert text.count(old)==1;text=text.replace(old,'permission in(0,1,2)')
old='address not in oldpack and permission==2';assert text.count(old)==1;text=text.replace(old,'address not in oldpack and permission in(0,2)')
old="pin(R/'tools/m4-constructor-original/run.py');pin(__file__);";assert text.count(old)==1;text=text.replace(old,"pin(parent);"+old)
exec(compile(text,str(parent),'exec'),globals())
