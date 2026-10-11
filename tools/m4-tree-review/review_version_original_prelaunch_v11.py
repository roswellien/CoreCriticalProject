"""Use the actual pinned VERSION observer assembly filename."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('review_version_original_prelaunch_v10.py')
scope={'__file__':str(p),'__name__':'materialize_isolation_ASM_name'}
exec(compile(p.read_text(),str(p),'exec'),scope)
t=scope['t']
a="'version_return_x86.asm'"
assert t.count(a)==1;t=t.replace(a,"'version_observer_x86.asm'")
a="pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v9.py');"
assert t.count(a)==1;t=t.replace(a,"pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v10.py');"+a)
exec(compile(t,str(Path(__file__)),'exec'),globals())
