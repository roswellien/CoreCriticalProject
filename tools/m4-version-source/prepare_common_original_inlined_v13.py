"""Admit only exact wholly inlined common fx helper with no executable refs."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2];base=R/'tools/m4-tree-review/review_version_original_common_v12.py';text=base.read_text();old="  for n in names:links.append(C.linked_function(worker,sy,se,n));counts['whole_linked_version_CPP_functions']+=1"
new="""  common_inlined=[n for n in names if n=='?fx@m4_version_common@mw34@@YA?AV?$array@E$0CAA@@std@@XZ']
  assert len(common_inlined)==1
  for name in common_inlined:
   assert not any(r['symbol']['name']==name for symbols,sections in symbols_by_object.values()for section in sections.values()if section['flags']&0x20000000 for r in section['relocations']),'Exact common fx helper wholly inlined with no executable object reference'
  names=[n for n in names if n not in common_inlined];counts['inlined_common_fx_no_executable_references']=len(common_inlined)
  for n in names:links.append(C.linked_function(worker,sy,se,n));counts['whole_linked_version_CPP_functions']+=1"""
assert text.count(old)==1;pos=text.index(old);text=text.replace(old,new);assert text.replace(new,old)==base.read_text();ast.parse(text);target=base.with_name('review_version_original_common_v13.py');assert not target.exists();target.write_text(text)
out=R/'reports/m4-version-source/common-original-inlined-preparation-r1';assert not out.exists();out.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
q=out/'report.json';q.write_text(json.dumps(dict(passed=True,exact_reverse_restores_parent=True,delta=dict(position=pos,old=old,new=new),whole_main_still_required=True,all_executable_objects_checked_for_helper_refs=True,worker_launched=False,archive_reader_opened=False,initializer_credit=0,files={str(p.resolve()):sha(p)for p in(base,target,Path(__file__))}),indent=2)+'\n');print(q,sha(q))
