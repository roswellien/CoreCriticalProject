"""Bounded tree domain/inverse tests, never executes source or any reader."""
from pathlib import Path
import ast,copy,hashlib,json
R=Path(__file__).resolve().parents[2]
def main():
 out=R/'reports/m4-original141-tree-source/preflight-r1';out.mkdir();files={};controls=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=hashlib.sha256(p.read_bytes()).hexdigest();assert h is None or h==v;files[str(p)]=v;return p
 q=pin(R/'tools/m4-original141-tree-source/tree_source_v2.py');s=q.read_text(encoding='utf-8');d=json.loads(pin(R/'reports/m4-original141-tree-source/preparation-r2/deltas.json').read_bytes());rev=s
 for row in reversed(d):assert rev.count(row['new'])==1;rev=rev.replace(row['new'],row['old'])
 assert rev==pin(R/'tools/m4-startup138-original/tree_source_r5.py').read_text(encoding='utf-8')
 parsed=ast.parse(s);checks={n.args[1].value:n.args[0]for n in ast.walk(parsed)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='need'and len(n.args)==2 and isinstance(n.args[1],ast.Constant)}
 def test(name,label,env,want):
  try:got=bool(eval(compile(ast.Expression(checks[label]),str(q),'eval'),env))
  except (KeyError,ValueError,TypeError):got=False
  assert got==want,name;controls.append(dict(name=name,production_predicate=label,expected_accept=want,passed=True))
 order=json.loads(pin(R/'reports/m4-original141/source-preparation-r6/selected-order.json').read_bytes());label='Current physical tree slot after exact three constructor insertions';env=dict(tree_phase=86,preparation=dict(selected_order=order));test('physical141order_tree86',label,env,True);test('reject_old83',label,dict(env,tree_phase=83),False)
 for slot in (13,14,39):
  e=copy.deepcopy(env);e['preparation']['selected_order'][slot]['entry']+=1;test('wrong_constructor_slot_'+str(slot),label,e,False)
 links=json.loads(pin(R/'reports/m4-original141/root-compiled-review-r2/physical-links.json').read_bytes());res={}
 for row in links:
  for rel in row['relocations']:
   if rel['symbol_section']==0 and rel['resolution_kind']=='virtual address':
    k,v=rel['symbol'],rel['actual_symbol_address'];assert k not in res or res[k]==v;res[k]=v
 exact={0x78146198:res['_lockit_api_Enter'],0x78146184:res['_lockit_api_Leave']};label='Exact current wholly compiled x86 API observer cell'
 for slot,v in exact.items():
  e=dict(slot=slot,current=v,exact_CS_shims=exact);test('current_CS_shim_'+hex(slot),label,e,True)
  for name,wrong in [('oldfixture',0x18010000),('sameimage_wrong_symbol',v+1),('opposite_CS',next(t for k,t in exact.items()if k!=slot))]:test('reject_'+name+'_'+hex(slot),label,dict(e,current=wrong),False)
 label='Genuine independently measured original141 prefix and closed export';valid=dict(passed=True,reader_closed=True,paired_export_readers_closed=True,callbacks=111);test('strict_current_closed111',label,dict(validation=valid),True)
 for k in ('passed','reader_closed','paired_export_readers_closed','callbacks'):
  e=copy.deepcopy(valid);e[k]=108 if k=='callbacks'else False;test('reject_validation_'+k,label,dict(validation=e),False)
 model=pin(R/'tools/m4-tree-source/game_model_v4.py');assert str(model)in json.loads(pin(R/'reports/m4-original141-tree-source/closure-preparation-r1/report.json').read_bytes())['files']
 pin(__file__);p=out/'controls.json';p.write_text(json.dumps(controls,indent=2)+'\n',encoding='utf-8');pin(p)
 report=dict(passed=True,prepared_only=True,exact_eleven_delta_inverse=True,controls=len(controls),source_instruction_model_unchanged=True,canonical_reader_opened=False,ordinary_reader_opened=False,worker_launched=False,files=files);p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=='__main__':main()
