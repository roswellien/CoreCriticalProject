"""Use actual C observer definitions and globally scoped external target joins."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('review_version_original_prelaunch_v3.py');scope={'__file__':str(p),'__name__':'materialize_actual_C_names'}
exec(compile(p.read_text(),str(p),'exec'),scope);t=scope['t']
t=t.replace("'_main','_observe_boundary','_observe_named_API','_registry_observe_allocation','_version_observe','_nullfree_observe'","'_main','_registry_observe_allocation','_version_observe','_version_note_allocation','_nullfree_observe','_fs_observe_before','_fs_observe_after','_fs_observe_allocation','_container_observe_allocation','_lockit_observe_allocation','_vtable_observe','_lockit_observe'")
a="if 'actual_symbol_address'not in row:continue";assert t.count(a)==1;t=t.replace(a,"if 'actual_symbol_address'not in row or row['symbol_section']!=0:continue")
t=t.replace("pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v2.py');","pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v3.py');pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v2.py');")
exec(compile(t,str(Path(__file__)),'exec'),globals())
