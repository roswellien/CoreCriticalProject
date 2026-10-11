"""Bound both named labels before extracting an assembly bundle's functions."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
parent=Path(__file__).with_name('review_joint138_prelaunch_v5.py')
scope={'__file__':str(parent),'__name__':'materialize_with_GDI'}
exec(compile(parent.read_text(),str(parent),'exec'),scope)
t=scope['t']
a="assert s['type']==0;s['type']=32"
b="assert s['type']in(0,32);s['type']=32\n     if q.name in ('native_api.obj','connected_hardware_boundary.obj'):\n      for label in sy.values():\n       if label['name']in('mw34_widget_native_api','mw34_widget_hardware_call','mfc_connected_hardware_call')and label['section']>0:assert label['type']in(0,32);label['type']=32"
assert t.count(a)==1;t=t.replace(a,b)
t=t.replace("  pin(R/'tools/m4-tree-review/review_joint138_prelaunch_v3.py');", "  pin(R/'tools/m4-tree-review/review_joint138_prelaunch_v5.py');pin(R/'tools/m4-tree-review/review_joint138_prelaunch_v3.py');")
exec(compile(t,str(Path(__file__)),'exec'),globals())
