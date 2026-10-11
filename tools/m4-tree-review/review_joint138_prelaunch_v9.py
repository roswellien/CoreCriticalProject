"""Preserve complete growth review; handle its typed physical file records."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('review_joint138_prelaunch_v8.py')
scope={'__file__':str(p),'__name__':'materialize_typed_growth_pins'}
exec(compile(p.read_text(),str(p),'exec'),scope);t=scope['t']
for h in ('d6f76cacd9cdeb9644b67091a5be0d884c3abce732ec6b0c9f08bd624068243c','7170e349dcecf013a616cc593029354154fe38edf964148490fa2bec207fe724'):
 a="'"+h+"')";assert t.count(a)==1;t=t.replace(a,"'"+h+"',closure=False)")
a="  service=read(R/'reports/m4-fps-native/service-preparation-r3/report.json'"
at=t.index(a)
t=t[:at]+"  for receipt in (growth_source,growth_guard):\n   for path,identity in receipt['files'].items():\n    q=pin(path,identity['sha256']if isinstance(identity,dict)else identity)\n    if isinstance(identity,dict):assert q.stat().st_size==identity['bytes']\n"+t[at:]
t=t.replace("  pin(R/'tools/m4-tree-review/review_joint138_prelaunch_v7.py');","  pin(R/'tools/m4-tree-review/review_joint138_prelaunch_v8.py');pin(R/'tools/m4-tree-review/review_joint138_prelaunch_v7.py');")
exec(compile(t,str(Path(__file__)),'exec'),globals())
