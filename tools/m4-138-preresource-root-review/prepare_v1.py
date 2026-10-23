"""Materialize retained schema6 physical predicates for the narrow control main."""
from pathlib import Path
import hashlib,json,ast
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-138-preresource-root-review/preparation-r1';out.mkdir(parents=True);parent=R/'reports/m4-138-criteria-frontier/schema-checker-preparation-r7';files={};delta=[]
 def pin(p):p=Path(p).resolve();files[str(p)]=sha(p);return p
 for leaf in('native-inputs.py','native-TLS.py','native-boundary.py','native-linked.py'):
  p=pin(parent/leaf);text=p.read_text()
  def change(a,b,n=1):
   nonlocal text
   assert text.count(a)==n,(leaf,a,text.count(a));text=text.replace(a,b);delta.append(dict(file=leaf,old=a,new=b,count=n))
  if leaf=='native-boundary.py':change("Path(build['workers']['O0']['path']).parent.parent/'connected_hardware_boundary.obj'","R/'reports/m4-joint-startup138/build-r5/connected_hardware_boundary.obj'")
  if leaf=='native-linked.py':
   change("bf/'CMakeFiles/mw34_joint_startup138.dir/connected_component.cpp.obj'","component_object_path")
   change("obj=pin(bf/'CMakeFiles/mw34_joint_startup138.dir'/filename)","obj=pin(component_object_path if filename=='connected_component.cpp.obj'else main_object_path)")
   change("blob(bf/'CMakeFiles/mw34_joint_startup138.dir/native_main.cpp.obj')","blob(main_object_path)")
   a="for prefix in ('main','?growth_and_cleanup@@'):";start=text.index(a);removed=text[start:];assert removed.count('whole_current_main_growth_functions')==1;change(removed,'# Positive main/growth are outside the13-root refusal prefix.\n# Full current control-main/caller/cleanup proof is performed in driver.\n')
  reverse=text
  for d in reversed([d for d in delta if d['file']==leaf]):assert reverse.count(d['new'])==d['count'];reverse=reverse.replace(d['new'],d['old'])
  assert reverse==p.read_text();ast.parse(text);q=out/leaf;q.write_text(text);pin(q)
 p=out/'deltas.json';p.write_text(json.dumps(delta,indent=2)+'\n');pin(p);pin(__file__)
 (out/'report.json').write_text(json.dumps(dict(passed=True,scope='Unexecuted ordinary linked reviewer predicate preparation',retained_schema6_blocks=True,exact_inverse=True,scope_delta='Do not require dropped unused positive main/growth; replace with actual whole new control main/functions/caller/cleanup in driver.',changes=len(delta),worker_executed=False,canonical_reader_opened=False,initializer_credit=0,files=files),indent=2)+'\n');print(sha(out/'report.json'))
if __name__=='__main__':main()
