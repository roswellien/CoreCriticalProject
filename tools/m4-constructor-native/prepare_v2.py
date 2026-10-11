"""Correct only the frozen body inventory key and retain observed getter scope."""
from pathlib import Path
import hashlib
h=Path(__file__).resolve().parent;source=h/'prepare.py';s=source.read_text()
for a,b in [("for row in bodies['reused']:","for row in bodies['reusable']:"),("return address==0x5bcc80||address==0x5cab78||address==0x5ca6f0;","return address==0x5bcc80;"),("for p in(__file__,R/'tools/m4-constructor-native/build.py'","for p in(__file__,R/'tools/m4-constructor-native/prepare.py',R/'tools/m4-constructor-native/build.py'")]:
 if s.count(a)!=1:raise ValueError('Exact additive constructor preparer hunk')
 s=s.replace(a,b,1)
exec(compile(s,str(source),'exec'),globals())
