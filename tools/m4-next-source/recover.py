"""Four exact fixed-vtable normal game roots after accepted116, no execution."""
from pathlib import Path
import copy,hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-next-source'
sys.path.insert(0,str(R/'tools/m4-service-initializers'))
s=importlib.util.spec_from_file_location('fixed_batch_recover',R/'tools/m4-onexit-batch-recovery/recover.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
SELECTED=(0x40f0e0,0x4795f0,0x47f5f0,0x4b5220)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(name):
 out=B/name;need(not out.exists(),'Fresh fixed dispatch source contracts');out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Physical frozen input');pins[str(p)]=v;return p
 scan=json.loads(pin(B/'scan-r1/report.json','fb053221c49c6d8765966128047661c2c06bf7db3e7b25b59cb0443b4443a487').read_bytes());need(scan['passed'],'Exact new physical target closure');pin(R/'reports/m4-joint-startup116-root/acceptance-r1/report.json','de76b4e006e5ad2ce0b90f634054379f2271abd14ecb8591643c24e72cc4c0e6');game=M.Module(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'));allnodes=json.loads(pin(B/'scan-r1/game-normal-graphs.json').read_bytes());targets=json.loads(pin(B/'scan-r1/static-indirect-inputs.json').read_bytes());inputs={r['CALL_pc']:r for r in targets}
 for g in allnodes.values():M.ingest(game,g['instructions'])
 # Bind three actual indirect CALLs; exact physical rows remain unchanged.
 for g in allnodes.values():
  for unresolved in list(g['unresolved_controls']):
   pc=unresolved['pc']
   if pc not in inputs:continue
   row=unresolved['row'];target=inputs[pc];need(row['mnemonic']=='call','Exact source indirect CALL');g['direct_calls'].append(dict(site=pc,target=target['target'],return_pc=pc+row['size'],source_indirect=True,source_slot=target['slot']));g['unresolved_controls'].remove(unresolved)
 entries=set()
 for root in SELECTED:entries.update(M.descendants(allnodes,root))
 normal={e:allnodes[str(e)]if str(e)in allnodes else allnodes[e]for e in entries}if False else {int(e):g for e,g in allnodes.items()if int(e)in entries}
 # descendants expects integer entry keys; rebuild explicit exact closure.
 normal_all={int(e):g for e,g in allnodes.items()};entries=set()
 for root in SELECTED:entries.update(M.descendants(normal_all,root))
 normal={e:normal_all[e]for e in entries};need(not any(g['unresolved_controls']for g in normal.values()),'Complete selected normal fixed-control closure');rows={r['pc']:r for g in normal.values()for r in g['instructions']};need(not any(g['FP_sites']for g in normal.values()),'Integer-only source family')
 prior=set()
 for path in('reports/m4-onexit-source/lifts-r4/report.json','reports/m4-strings-source/lifts-r1/report.json','reports/m4-mfc-source/lifts-r1/report.json','reports/m4-fs-source/lifts-r1/report.json','reports/m4-container-source/lifts-r2/report.json'):
  d=json.loads(pin(R/path).read_bytes());prior.update(x['entry']for x in d['source_bodies'].values())
 prior.add(0x42a570);new={e:g for e,g in normal.items()if e not in prior};roots=[];remaining=json.loads(pin(R/'reports/m4-joint-startup116-root/next-frontier-r1/remaining-roots.json').read_bytes());objects={0x40f0e0:0x5fc338,0x4795f0:0x608ae0,0x47f5f0:0x608ea0,0x4b5220:0x60b270}
 for root in SELECTED:
  table=next(r for r in remaining if r['entry']==root);off,_=game.image.rva_range(table['slot']-game.base,4);need(struct.unpack_from('<I',game.image.data,off)[0]==root,'Exact remaining initializer slot');sub=M.descendants(normal,root);registration=[]
  for e in sub:
   g=normal[e];byend={r['pc']+r['size']:r for r in g['instructions']}
   for call in g['direct_calls']:
    if call['target']!=0x5ac140:continue
    row=byend[call['site']];need(row['mnemonic']=='push'and row['operands'].startswith('0x'),'Literal callback source PUSH');callback=int(row['operands'],16);need(game.executable(callback),'Exact callback code pointer');registration.append(dict(push_pc=row['pc'],callback=callback,CALL_pc=call['site'],return_pc=call['return_pc']))
  need(len(registration)==1,'Exactly one registered callback');roots.append(dict(entry=root,slot=table['slot'],objects=[dict(address=objects[root],static_source_object=True)],registration=registration[0],normal=M.requirements(normal,sub),callback_execution_claimed=False,allocations=0,strdups=0))
 roots.sort(key=lambda r:r['slot']);old=json.loads(pin(R/'reports/m4-container-source/recovery-r3/instruction-contracts.json','3aeed69c05122c689a2f0951c2d49052db307beba917f5bcf756969aa7bbb09d').read_bytes());order=sorted(old['selected_order']+[dict(entry=r['entry'],slot=r['slot'])for r in roots],key=lambda r:r['slot']);need(len(order)==120 and len({r['slot']for r in order})==120,'Exact prospective120 table order');pages=set(old['source_data_pages'])|{0x5bc000,0x5cf000,0x5fc000};pages.update(o['address']&~4095 for r in roots for o in r['objects']);pages.add(0x5f4000)
 parser_path=pin(R/'tools/m4-crt-locale-batch-recovery/recover_v2.py');s=importlib.util.spec_from_file_location('fixed_operand_parser',parser_path);P=importlib.util.module_from_spec(s);s.loader.exec_module(P);contracts=[]
 for r in sorted(rows.values(),key=lambda r:r['pc']):
  off,_=game.image.rva_range(r['pc']-game.base,r['size']);need(game.image.data[off:off+r['size']]==bytes.fromhex(r['bytes']),'Every game source row physically exact');contracts.append(P.instruction_contract(dict(pc=r['pc'],width=r['size'],bytes_hex=r['bytes'],mnemonic=r['mnemonic'],operands=r['operands'].split(' <')[0])))
 calls=[]
 for root,obj in objects.items():
  if root in(0x40f0e0,0x47f5f0):calls.append(dict(root=root,CALL_pc=0x59fbab,slot=0x5cfd14,target=0x40e820,return_pc=0x59fbb1,entry_ECX=obj+(8 if root==0x47f5f0 else 0),argument=0,RET_cleanup=4,source_object=obj,normal_nonzero_pointer_path=False))
  else:
   for pc,slot,target,ret,cleanup in((0x59fdc5,0x5bc100,0x59ff00,0x59fdcb,0),(0x59ff6e,0x5bc0fc,0x59ff80,0x59ff71,4)):calls.append(dict(root=root,CALL_pc=pc,slot=slot,target=target,return_pc=ret,entry_ECX=obj,argument=0 if cleanup else None,RET_cleanup=cleanup,source_object=obj,source_vtable=0x5bc0e0,dominating_vtable_store_PC=0x59fdb3,normal_nonzero_pointer_path=False))
 frames=[dict(root=0x47f5f0,entry=0x4824a0,handler=0x5b41c8,read=0x4824a7,install=0x4824ae,saved=0x4824da,restore=0x4824ed,ret=0x4824f8,bytes=12,ret_cleanup=0,saved_operand=next(r['decoded_operands'][1]for r in contracts if r['pc']==0x4824da))]
 payloads={'game-normal-graphs.json':normal,'game-new-graphs.json':new,'fixed-roots.json':roots,'fs-roots.json':roots,'indirect-call-inputs.json':calls,'FS-frame-contracts.json':frames,'instruction-contracts.json':dict(schema='mw34-fixed-vtable-game-source-v1',instructions=contracts,selected_order=order,roots=roots,source_data_pages=sorted(pages),source_code_pages=sorted({r['pc']&~4095 for r in rows.values()}),FS_frame_contracts=frames,static_indirect_inputs=calls,allocations=[],string_inputs=[],AFTER_machine_seed=False),'source-page-inventory.json':dict(pages=sorted(pages),new_pages=[0x5bc000,0x5cf000,0x5fc000],strategy='Exact every-section raw/BSS page intersection; no entire partially raw page zeroing',new_game_imports=0,new_providers=0,allocated_owner_count_change=0)}
 for label,value in payloads.items():(out/label).write_text(json.dumps(value,indent=2)+'\n');pin(out/label)
 pin(__file__);report=dict(passed=True,scope='Four exact fixed-vtable normal roots and full literal integer game bodies, with one normal FS frame and zero new providers/allocations/string copies. No execution/admission.',root_count=4,roots=roots,order=order,game_bodies=len(new),all_game_entries=len(normal),unique_instructions=len(rows),unique_bytes=sum(r['size']for r in rows.values()),source_data_pages=sorted(pages),data_pages=sorted(pages),source_code_pages=sorted({r['pc']&~4095 for r in rows.values()}),FS_frame_contracts=frames,indirect_inputs=calls,new_pages=[0x5bc000,0x5cf000,0x5fc000],new_providers=0,new_allocations=0,new_strdups=0,selected_normal_pointer_arguments_zero=True,nonzero59FF80_pointee_path_admitted=False,original_executed=False,native_executed=False,initializer_credit=0,files=pins);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),bodies=len(new),all_entries=len(normal),rows=len(rows),bytes=report['unique_bytes'])))
if __name__=='__main__':main(sys.argv[1])
