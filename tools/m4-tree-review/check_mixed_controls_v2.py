"""Additive exact measured named dtor-import first cause; candidate unchanged."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('check_mixed_controls.py');s=p.read_text()
a="if case==8:need(v[1]==0x5bb4f4 and reason=='Only committed source/API/research effects may change owned locale pages'and fault[2]==0x5bb000,'Actual named dtorIAT cell conservation firstfault')"
b="if case==8:need(v[1]==0x5bb4f4 and reason=='Exact root and loaded-image named Lockit import projection required'and fault[1]==0x4e5389 and fault[2]==0x5bb4f4,'Actual exact named dtor owning-IAT source projection firstfault')"
assert s.count(a)==1;s=s.replace(a,b)
a="pin(__file__); pin(R/'tools/m4-tree-review/check_formatting_controls_v2.py'); pin(R/'tools/m4-tree-review/check_controls_v3.py')"
b=a+"; pin(R/'tools/m4-tree-review/check_mixed_controls.py'); read(R/'reports/m4-tree-review/mixed-first-reasons-r1/report.json','0a097e693fca064f4d598fbd1ea981ff912dcb56b810b949d9dced12ac3bd3aa')"
assert s.count(a)==1;s=s.replace(a,b)
exec(compile(s,str(p),'exec'),globals())
