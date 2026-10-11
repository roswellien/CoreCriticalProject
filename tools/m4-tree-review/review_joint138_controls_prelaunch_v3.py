"""Use the admitted PE parser's physical RVA API for whole initializer cells."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('review_joint138_controls_prelaunch_v2.py')
scope={'__file__':str(p),'__name__':'materialize_controls_PE_cells'}
exec(compile(p.read_text(),str(p),'exec'),scope)
t=scope['t']
a="game.read_va(x['slot'],4)"
assert t.count(a)==1
t=t.replace(a,"game.read(game.rva_range(x['slot']-game.image_base,4)[0],4)")
a="  pin(R/'tools/m4-tree-review/review_joint138_controls_prelaunch.py');"
assert t.count(a)==1
t=t.replace(a,"  pin(R/'tools/m4-tree-review/review_joint138_controls_prelaunch_v2.py');"+a.strip())
exec(compile(t,str(Path(__file__)),'exec'),globals())
