"""Native19 prelaunch, with wrapper path explicitly named outside local prep variable."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
v3=Path(__file__).with_name('review_joint130_prelaunch_v3.py');s=v3.read_text()
s=s.replace("s=s.replace('  C.pin(__file__);','  C.pin(__file__);C.pin(p);')","s=s.replace('  C.pin(__file__);',\"  C.pin(__file__);C.pin(R/'tools/m4-tree-review/review_joint130_prelaunch_v2.py');C.pin(R/'tools/m4-tree-review/review_joint130_prelaunch_v3.py');\")")
assert 'C.pin(p);'not in s
exec(compile(s,str(v3),'exec'),globals())
