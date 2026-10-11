"""Admit explicit typed extent/hash file pins without changing physical checks."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('review_joint138_controls_prelaunch.py')
scope={'__file__':str(p),'__name__':'materialize_controls_typed_pins'}
exec(compile(p.read_text(),str(p),'exec'),scope)
t=scope['t']
a="  assert h is None or v==h,(str(p),h,v);"
assert t.count(a)==1
t=t.replace(a,"  if isinstance(h,dict):\n   assert set(h)=={'bytes','sha256'} and p.stat().st_size==h['bytes'];h=h['sha256']\n  assert h is None or v==h,(str(p),h,v);")
a="  pin(R/'tools/m4-tree-review/review_joint138_prelaunch_v10.py');"
assert t.count(a)==1
t=t.replace(a,"  pin(R/'tools/m4-tree-review/review_joint138_controls_prelaunch.py');"+a.strip())
exec(compile(t,str(Path(__file__)),'exec'),globals())
