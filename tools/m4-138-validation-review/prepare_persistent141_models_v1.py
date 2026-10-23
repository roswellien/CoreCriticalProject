"""Ordinary-only exact parent rebasing of constructor semantics onto widgets."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-startup141-source/model-preparation-r1'
 assert not out.exists();out.mkdir(parents=True)
 dst=R/'tools/m4-native141-source';dst.mkdir(exist_ok=True)
 parents=['game_model.py','game_model_v2.py','game_model_v3.py','game_model_v5.py','game_model_v6.py','game_model_v8.py','game_model_v9.py']
 files={};relations=[]
 for name in parents:
  p=R/'tools/m4-constructor-native'/name;t=p.read_text();changes=[]
  if name=='game_model.py':
   old="R/'reports/m4-formatting-source/persistent-family-model-r1/persistent_model.py'"
   new="R/'reports/m4-fps-original/source-preparation-r4/game_model.py'"
  elif name in ('game_model_v2.py','game_model_v3.py','game_model_v5.py'):
   predecessor={'game_model_v2.py':'game_model.py','game_model_v3.py':'game_model_v2.py','game_model_v5.py':'game_model_v3.py'}[name]
   old="R/'tools/m4-constructor-native/"+predecessor+"'"
   new="R/'tools/m4-native141-source/"+predecessor+"'"
  else:
   old=new=None # with_name resolves the fresh rebased sibling, text unchanged.
  if old:
   assert t.count(old)==1;t=t.replace(old,new);changes=[dict(old=old,new=new)]
  target=dst/name;assert not target.exists();target.write_text(t)
  ast.parse(t);reverse=t
  for c in reversed(changes):assert reverse.count(c['new'])==1;reverse=reverse.replace(c['new'],c['old'])
  assert reverse==p.read_text()
  files[str(p)]=sha(p);files[str(target)]=sha(target)
  relations.append(dict(parent=str(p),derived=str(target),exact_text_inverse=True,changes=changes))
 (out/'inverse-relations.json').write_text(json.dumps(relations,indent=2)+'\n');files[str(out/'inverse-relations.json')]=sha(out/'inverse-relations.json')
 report=dict(passed=True,source_semantics_changed=False,parent_rebased_to_current_widgets=True,native_executed=False,canonical_reader_opened=False,persistent141_source_complete=False,initializer_credit=0,relations=str(out/'inverse-relations.json'),files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(sha(out/'report.json'))
if __name__=='__main__':main()
