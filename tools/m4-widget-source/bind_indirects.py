"""Physical widget vptr/slot and exact caller-supplied array contracts.

Static provenance candidates require future measured instance/frame joins.
The complete conditional graphs deliberately keep dormant paths visible.
"""
from pathlib import Path
import copy, hashlib, importlib.util, json, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-widget-source'
sys.path.insert(0,str(R/'tools/m4-service-initializers'))
s=importlib.util.spec_from_file_location('widget_recover',R/'tools/m4-onexit-batch-recovery/recover.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
PINS={}
def need(v,t):
 if not v:raise ValueError(t)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No capture payload');a=sha(p);need(h is None or a==h,'Physical frozen dependency '+str(p));PINS[str(p)]=a;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def main(name):
 out=B/name;need(not out.exists(),'Fresh widget dispatch contract');out.mkdir(parents=True);commands=[];passed=False
 try:
  rec=read(B/'recovery-r2/report.json','75e1f2f3deddfc790e118b4d73e76b7ef321497f5bcf68935592d0c35eb6d29c');need(rec['passed'],'Exact five-root source recovery')
  game=M.Module(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'))
  nodes={int(e):g for e,g in read(B/'recovery-r2/game-physical-graphs.json').items()}
  for g in nodes.values():M.ingest(game,g['instructions'])
  rows={r['pc']:r for g in nodes.values()for r in g['instructions']}
  def row(pc):need(pc in rows,'Source retained PC '+hex(pc));return rows[pc]
  # Every tuple binds exact CALL PC, source instance vptr store, and slot.
  # Object roles are affine to selected root ECX and array iteration.
  specs=[
   (0x59fdc5,0x5bc0e0,0x20,0x59fdb3,'current base object',0x59ff00),
   (0x59ff6e,0x5bc0e0,0x1c,0x59fdb3,'current base object; zero pointer argument',0x59ff80),
   (0x59fbab,0x5cfd10,4,0x59fba5,'current list object',0x40e820),
   (0x5a2dfe,0x5cfed8,0x20,0x5a2dd4,'current text base object',0x59ff00),
   (0x5a2e0f,0x5cfed8,0x20,0x5a2dd4,'same text base object after previous virtual return',0x59ff00),
   (0x5a2f86,0x5cfed8,0x20,0x5a2dd4,'nonzero format branch of text base constructor; unadmitted',0x59ff00),
   (0x5a0669,0x5bc598,0x8c,0x40e880,'root40E250+48+i*4B0 or root40EF50+10+i*4B0',0x5a0680),
   (0x40e2f8,0x5bc598,0xc,0x40e880,'root40E250+48+i*4B0; 0<=i<25',0x409b10),
   (0x40e2ff,0x5bc598,0x64,0x40e880,'same current element after setter return',0x59ff50),
   (0x40ffa5,0x5bc598,0xc,0x40e880,'root40EF50+10+i*4B0; 0<=i<25',0x409b10),
   (0x40ffac,0x5bc598,0x64,0x40e880,'same current element after setter return',0x59ff50),
   (0x5a3d7c,0x5cfd28,0x88,0x5a0114,'root5A3C30+10+i*4B0; 0<=i<15',0x5a0710),
   (0x5a3da4,0x5cfd28,0xc,0x5a0114,'same current element after font setter return',0x409b10),
   (0x5a3dab,0x5cfd28,0x64,0x5a0114,'same current element after position setter return',0x59ff50),
   (0x5a4614,0x5d0290,0x64,0x5a45ca,'root5A3FF0/5A66F0+28',0x59ff50),
   (0x5a4628,0x5d04a8,0x64,0x5a53f3,'root5A3FF0/5A66F0+70+i*4C; 0<=i<5',0x59ff50),
   (0x5a463d,0x5d0288,4,0x5a45ee,'root5A3FF0/5A66F0; argument1',0x40e820),
  ]
  bindings=[]
  for pc,vptr,offset,store,role,target in specs:
   call=row(pc);st=row(store);need(call['mnemonic']=='call','Actual indirect CALL row');need(st['mnemonic']=='mov'and st['operands'].endswith(hex(vptr)),'Exact dominating source vptr store candidate')
   physical=game.data(vptr+offset,4);need(int.from_bytes(bytes.fromhex(physical['initial_hex']),'little')==target,'Exact readonly slot target');section=game.section(vptr+offset);need(section and section['readable']and not section['writable']and not section['executable'],'File-backed readonly vtable slot')
   bindings.append(dict(CALL_pc=pc,CALL_row=call,source_vptr=vptr,source_vptr_store_PC=store,source_vptr_store_row=st,slot_offset=offset,slot=vptr+offset,slot_physical=physical,target=target,object_role=role,provenance_scope='Literal dominating store and exact slot; actual same-instance last-store, current source frame and return conservation remain runtime obligations',measured=False))
  arrays=[]
  for pc,base,lea,count,stride,ctor,dtor,pushes,roots in [
   (0x40e2d9,0x48,0x40e2c9,25,0x4b0,0x40e830,0x409ef0,(0x40e2bf,0x40e2c4,0x40e2cc,0x40e2ce,0x40e2d3),(0x40e250,)),
   (0x40ff82,0x10,0x40ff6f,25,0x4b0,0x40e830,0x409ef0,(0x40ff65,0x40ff6a,0x40ff72,0x40ff74,0x40ff79),(0x40ef50,)),
   (0x5a3d12,0x10,0x5a3d01,15,0x4b0,0x47eab0,0x5a05a0,(0x5a3cf5,0x5a3cfa,0x5a3cff,0x5a3d04,0x5a3d09),(0x5a3c30,)),
   (0x5a45e7,0x70,0x5a45da,5,0x4c,0x5a53e0,0x5a01f0,(0x5a45d0,0x5a45d5,0x5a45dd,0x5a45df,0x5a45e1),(0x5a3ff0,0x5a66f0)),
  ]:
   need(row(pc)['mnemonic']=='call'and row(pc)['operands'].startswith('0x5ac2a0'),'Exact vector constructor CALL')
   for p,v in zip(pushes[:4],(dtor,ctor,count,stride)):need(row(p)['mnemonic']=='push'and int(row(p)['operands'],0)==v,'Exact callback/count/stride source PUSH')
   arrays.append(dict(roots=list(roots),CALL_pc=pc,base_root_offset=base,base_LEA_pc=lea,constructor=ctor,destructor=dtor,count=count,stride=stride,push_rows=[row(p)for p in pushes],constructor_indirect_PC=0x5ac2db,constructor_argument_ebp_offset=0x14,constructor_current_ECX='base+iteration*stride',successful_iteration_store_PC=0x5ac2e4,success_store_PC=0x5ac2e9,cleanup_guard_PC=0x5ac31d,success_cleanup_skips_reverse_destructor=True,failure_destructor_indirect_PC=0x5ac24b,failure_path_admitted=False,measured=False))
  targets=sorted({b['target']for b in bindings});added,deferred=M.closure(game,targets,out,commands,maximum=180);nodes.update(added)
  for b in bindings:
   for g in nodes.values():
    for u in list(g['unresolved_controls']):
     if u['pc']==b['CALL_pc']:
      g['direct_calls'].append(dict(site=b['CALL_pc'],target=b['target'],return_pc=b['CALL_pc']+b['CALL_row']['size'],source_indirect=True,source_slot=b['slot'],source_vptr_store=b['source_vptr_store_PC'],runtime_instance_join_required=True));g['unresolved_controls'].remove(u)
  # Single indirect helper has multiple precisely caller-bound targets.
  # Never replace it with a free-standing allowed callback set.
  for g in nodes.values():
   if any(u['pc']==0x5ac2db for u in g['unresolved_controls']):
    for ctor in sorted({a['constructor']for a in arrays}):g['direct_calls'].append(dict(site=0x5ac2db,target=ctor,return_pc=0x5ac2de,source_indirect=True,caller_array_contract_required=True))
    g['unresolved_controls']=[u for u in g['unresolved_controls']if u['pc']!=0x5ac2db]
  allrows={r['pc']:r for g in nodes.values()for r in g['instructions']}
  unresolved=[dict(entry=e,**u)for e,g in nodes.items()for u in g['unresolved_controls']]
  imports={c['site']:c for g in nodes.values()for c in g['import_sites']}
  data=dict(font_lookup_gate=dict(address=0x6384e8,physical=game.data(0x6384e8,4),static_zero_is_not_current_input=True),source_roots=[dict(root=r,object=o)for r,o in((0x40e250,0x5f4d78),(0x40ef50,0x5fc838),(0x5a3c30,0x731ac0),(0x5a3ff0,0x736130),(0x5a66f0,0x736328))])
  payloads={'source-indirect-contracts.json':bindings,'source-array-contracts.json':arrays,'game-bound-graphs.json':nodes,'new-target-graphs.json':added,'open-frontiers.json':dict(direct_deferred=deferred,unresolved_controls=unresolved,imports=list(imports.values()),conditional_full_graph_retained=True,handler_execution_admitted=False),'finite-input-prerequisites.json':data}
  for label,v in payloads.items():p=out/label;p.write_text(json.dumps(v,indent=2)+'\n');pin(p)
  for p in(Path(__file__),R/'tools/m4-onexit-batch-recovery/recover.py',R/'tools/m4-service-initializers/recover.py',R/'tools/analysis/pe.py',M.DECODER):pin(p)
  for p in out.iterdir():
   if p.is_file():pin(p)
  passed=True
 finally:
  report=dict(passed=passed,scope='Exact literal source vptr/slot and finite caller-supplied vector contracts; same-instance/frame/generation runtime joins unmeasured',counts=dict(selected_roots=5,indirect_source_bindings=len(locals().get('bindings',[])),array_source_calls=len(locals().get('arrays',[])),distinct_ctor_callbacks=3,total_ctor_callbacks_if_normal_five_roots_complete=75,target_entries=len(locals().get('added',{})),all_graph_entries=len(locals().get('nodes',{})),unique_instructions=len(locals().get('allrows',{})),unique_bytes=sum(r['size']for r in locals().get('allrows',{}).values()),fresh_decodes=len(commands)),source_targets=locals().get('targets',[]),direct_deferred=locals().get('deferred',[]),unresolved_count=len(locals().get('unresolved',[])),commands=commands,original_executed=False,native_executed=False,initializer_credit=0,files=PINS)
  p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(p),counts=report['counts'],unresolved=report['unresolved_count'])))
if __name__=='__main__':main(sys.argv[1])
