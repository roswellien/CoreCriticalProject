"""Exact current compiler anonymous namespace identity for immutable component copy."""
from pathlib import Path
parent=Path(__file__).with_name('review_mfc1168_connected_controls_prelaunch.py')
source=parent.read_text()
assert source.count('C7D6B430')==2
source=source.replace('C7D6B430','3EF3D8F5')
source=source.replace("exec(compile(text,str(__file__),'exec'),globals())", "text=text.replace(\"  pin(BASE);pin(V2);pin(V3);pin(V4);\",\"  pin(R/'tools/m4-tree-review/review_mfc1168_connected_controls_prelaunch.py');pin(BASE);pin(V2);pin(V3);pin(V4);\");exec(compile(text,str(__file__),'exec'),globals())")
exec(compile(source,str(parent),'exec'),globals())
