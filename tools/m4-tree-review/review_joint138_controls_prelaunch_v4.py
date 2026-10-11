"""Scope physical attribution to the negative worker's actual entry paths.

The renamed positive main and its growth-only helper are never invoked by this
worker. Positive growth has its own unchanged admitted executable and receipts.
"""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('review_joint138_controls_prelaunch_v3.py')
scope={'__file__':str(p),'__name__':'materialize_negative_entry_paths'}
exec(compile(p.read_text(),str(p),'exec'),scope)
t=scope['t']
a="n in ('main','mw34_context_controls_unused_positive_main')"
assert t.count(a)==1
t=t.replace(a,"n=='main'")
a="'?widget_whole_checkpoint','?growth_and_cleanup'"
assert t.count(a)==1
t=t.replace(a,"'?widget_whole_checkpoint'")
a="  pin(R/'tools/m4-tree-review/review_joint138_controls_prelaunch_v2.py');"
assert t.count(a)==1
t=t.replace(a,"  pin(R/'tools/m4-tree-review/review_joint138_controls_prelaunch_v3.py');"+a.strip())
a="actual_worker_launches=0,initializer_credit=0,"
assert t.count(a)==1
t=t.replace(a,"actual_worker_launches=0,unused_positive_main_and_growth_helper_not_admitted=True,initializer_credit=0,")
exec(compile(t,str(Path(__file__)),'exec'),globals())
