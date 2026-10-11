"""The seven-byte DWORD accessor is inlined and has no executable call target."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('review_version_original_prelaunch_v5.py');scope={'__file__':str(p),'__name__':'materialize_inlined_DWORD'}
exec(compile(p.read_text(),str(p),'exec'),scope);t=scope['t']
a="or v['name'].startswith('?version_'))]";assert t.count(a)==1;t=t.replace(a,"or v['name'].startswith('?version_')and not v['name'].startswith('?version_dword@@'))]")
a="  for n in names:links.append(C.linked_function(worker,sy,se,n));counts['whole_linked_version_CPP_functions']+=1"
assert t.count(a)==1
t=t.replace(a,"  for section in se.values():\n   if section['flags']&0x20000000:assert not any(r['symbol']['name'].startswith('?version_dword@@')for r in section['relocations'])\n  counts['inlined_DWORD_accessor_no_executable_references']=1\n"+a)
t=t.replace("pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v4.py');","pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v5.py');pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v4.py');")
exec(compile(t,str(Path(__file__)),'exec'),globals())
