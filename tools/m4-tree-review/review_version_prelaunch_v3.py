"""Correct the root review's Path normalization order, retaining all checks."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('review_version_prelaunch_v2.py')
t=p.read_text();a="exec(compile(s,str(Path(__file__)),'exec'),globals())"
assert t.count(a)==1
t=t.replace(a,"s=s.replace('str(Path(x)).resolve().as_posix()','Path(x).resolve().as_posix()');s=s.replace('  pin(__file__);pin(sys.executable);',\"  pin(R/'tools/m4-tree-review/review_version_prelaunch_v2.py');pin(__file__);pin(sys.executable);\");"+a)
exec(compile(t,str(Path(__file__)),'exec'),globals())
