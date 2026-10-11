"""Whole header equality includes the explicit measured source return/frame cells."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('review_version_original_prelaunch_v2.py');scope={'__file__':str(p),'__name__':'materialize_return_cells'}
exec(compile(p.read_text(),str(p),'exec'),scope);t=scope['t']
a="assert observer==text(R/'tools/m4-version-source/original_observer_v3.hpp')"
b="""original_header=text(R/'tools/m4-version-source/original_observer_v3.hpp')
  seam=' unsigned short version_DS{}';assert original_header.count(seam)==1
  original_header=original_header.replace(seam,' unsigned version_return_PCs[3]{0x4af113,0x4af131,0x4af16c},version_frame{};\\n'+seam)
  assert observer==original_header"""
assert t.count(a)==1;t=t.replace(a,b)
t=t.replace("pin(R/'tools/m4-tree-review/review_version_original_prelaunch.py');","pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v2.py');pin(R/'tools/m4-tree-review/review_version_original_prelaunch.py');")
exec(compile(t,str(Path(__file__)),'exec'),globals())
