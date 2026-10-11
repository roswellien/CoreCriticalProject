"""Limit allocation admission to the reached genuine version owner observers."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('review_version_original_prelaunch_v4.py');scope={'__file__':str(p),'__name__':'materialize_reached_observers'}
exec(compile(p.read_text(),str(p),'exec'),scope);t=scope['t']
for name in ('_fs_observe_allocation','_container_observe_allocation','_lockit_observe_allocation'):
 t=t.replace(",'"+name+"'",'')
t=t.replace("pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v3.py');","pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v4.py');pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v3.py');")
exec(compile(t,str(Path(__file__)),'exec'),globals())
