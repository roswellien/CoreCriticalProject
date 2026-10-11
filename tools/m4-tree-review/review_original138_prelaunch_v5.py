"""Pin the base review explicitly through every materialized wrapper."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('review_original138_prelaunch_v4.py')
scope={'__file__':str(p),'__name__':'materialize_original138_pinned_review'}
exec(compile(p.read_text(),str(p),'exec'),scope)
t=scope['t']
a='        pin(parent)'
assert t.count(a)==1
t=t.replace(a,"        pin(R/'tools/m4-tree-review/review_original138_prelaunch.py')\n        pin(R/'tools/m4-tree-review/review_original138_prelaunch_v4.py')",1)
exec(compile(t,str(Path(__file__)),'exec'),globals())
