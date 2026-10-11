"""Inlined identity comparisons are checked in the complete actual observer body."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('review_version_original_prelaunch_v6.py');scope={'__file__':str(p),'__name__':'materialize_inlined_identity'}
exec(compile(p.read_text(),str(p),'exec'),scope);t=scope['t']
a="  for n in names:links.append(C.linked_function(worker,sy,se,n));counts['whole_linked_version_CPP_functions']+=1"
assert t.count(a)==1
extra="""  inlined=[n for n in names if n.startswith('?version_same@@')]
  assert len(inlined)==2
  for n in inlined:
   refs=[(section,r)for section in se.values()for r in section['relocations']if r['symbol']['name']==n]
   assert refs and all(not section['flags']&0x20000000 and r['type']in(7,10)for section,r in refs)
  names=[n for n in names if n not in inlined];counts['inlined_identity_comparisons_no_executable_references']=len(inlined)
"""
t=t.replace(a,extra+a)
t=t.replace("pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v5.py');","pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v6.py');pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v5.py');")
exec(compile(t,str(Path(__file__)),'exec'),globals())
