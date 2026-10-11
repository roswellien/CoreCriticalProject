"""Bind the two reused widget helper IRs' actual original namespace."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
parent=Path(__file__).with_name('review_version_prelaunch.py')
s=parent.read_text()
a="before.replace(b'mw34_onexit_game_',b'mw34_version_game_')==after"
b="before.replace(b'mw34_widget_game_'if x['entry']in(0x5ac110,0x5ac140)else b'mw34_onexit_game_',b'mw34_version_game_')==after"
assert s.count(a)==1;s=s.replace(a,b)
s=s.replace('  pin(__file__);pin(sys.executable);',"  pin(R/'tools/m4-tree-review/review_version_prelaunch.py');pin(__file__);pin(sys.executable);")
exec(compile(s,str(Path(__file__)),'exec'),globals())
