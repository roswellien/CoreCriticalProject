"""Keep source-script attribution distinct from the parent receipt dictionary."""
from pathlib import Path
import hashlib, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
parent6=R/'tools/m4-tree-review/review_constructor37_prelaunch_v6.py'
expected=''
wrapper=parent6.read_text()
before="'pin(parent);pin(R/':'pin(parent5);pin(parent);pin(R/',"
after="'pin(parent);pin(R/':\"pin(parent6);pin(parent5);pin(R/'tools/m4-tree-review/review_constructor37_prelaunch.py');pin(R/\","
assert wrapper.count(before)==1
wrapper=wrapper.replace(before,after)
exec(compile(wrapper,str(parent6),'exec'),globals())
