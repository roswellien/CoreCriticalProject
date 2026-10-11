"""Use symbol-resolved complete function candidates for unwind joins."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('review_joint138_prelaunch_v6.py');scope={'__file__':str(p),'__name__':'materialize_bound_ASM'}
exec(compile(p.read_text(),str(p),'exec'),scope);t=scope['t']
a='    links.append(dict(level=level,object=str(q),symbol=n,'
assert t.count(a)==1;t=t.replace(a,'    candidates[n]=matches\n'+a)
t=t.replace("  pin(R/'tools/m4-tree-review/review_joint138_prelaunch_v5.py');", "  pin(R/'tools/m4-tree-review/review_joint138_prelaunch_v6.py');pin(R/'tools/m4-tree-review/review_joint138_prelaunch_v5.py');")
exec(compile(t,str(Path(__file__)),'exec'),globals())
