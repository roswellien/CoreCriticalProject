"""Five widget roots: physical callback and finite indirect-source recovery.

Static source only. Constructor-array callbacks are separately inventoried;
registered destructor/handler paths retain their own unresolved controls.
"""
from pathlib import Path
import hashlib, importlib.util, json, re, struct, sys, traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];BASE=R/'reports/m4-widget-source'
sys.path.insert(0,str(R/'tools/m4-service-initializers'))
sp=importlib.util.spec_from_file_location('widget_graph_recovery',R/'tools/m4-onexit-batch-recovery/recover.py')
M=importlib.util.module_from_spec(sp);sp.loader.exec_module(M)
ROOTS=(0x40e250,0x40ef50,0x5a3c30,0x5a3ff0,0x5a66f0)
CONSTRUCTORS=(0x40e830,0x47eab0,0x5a53e0)
CALLBACKS=(0x409ef0,0x5a05a0,0x5a01f0)
REGISTERED=(0x40e420,0x40ef90,0x5a3c60,0x5a4020,0x5a6720)
PINS={}
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No capture payload reads');a=sha(p);need(h is None or a==h,'Exact admitted physical input '+str(p));PINS[str(p)]=a;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh widget physical recovery');out.mkdir(parents=True);commands=[];passed=False
 try:
  scan=read(R/'reports/m4-next-source/scan-r1/report.json','fb053221c49c6d8765966128047661c2c06bf7db3e7b25b59cb0443b4443a487');need(scan['passed'],'Existing exact physical nine-root scan')
  game=M.Module(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'))
  seeds=read(R/'reports/m4-next-source/scan-r1/game-normal-graphs.json')
  for graph in seeds.values():M.ingest(game,graph['instructions'])
  seed_all=read(R/'reports/m4-service-initializers/static-r1/game-all-initializer-graphs.json','da2482873e1678a0a2493ed7f60421440447c43e63826b53f2d5b09cf573ba5a')
  for graph in seed_all.values():M.ingest(game,graph['instructions'])
  # Direct closure remains bounded; unresolved indirect/import/handler paths
  # are retained as frontiers instead of guessed from a nearby vtable.
  nodes,deferred=M.closure(game,list(ROOTS)+list(CONSTRUCTORS),out,commands,maximum=140)
  rows={r['pc']:r for g in nodes.values()for r in g['instructions']}
  callback_nodes={e:M.complete_graph(game,e,out,commands)for e in CALLBACKS+REGISTERED}
  contracts=[]
  parserpath=pin(R/'tools/m4-crt-locale-batch-recovery/recover_v2.py')
  ps=importlib.util.spec_from_file_location('widget_operand_contract',parserpath);P=importlib.util.module_from_spec(ps);ps.loader.exec_module(P)
  for row in sorted(rows.values(),key=lambda r:r['pc']):
   off,_=game.image.rva_range(row['pc']-game.base,row['size']);need(game.image.data[off:off+row['size']]==bytes.fromhex(row['bytes']),'Each exact widget/constructor/direct dependency row')
   contracts.append(P.instruction_contract(dict(pc=row['pc'],width=row['size'],bytes_hex=row['bytes'],mnemonic=row['mnemonic'],operands=row['operands'].split(' <')[0])))
  selected={v['root']:v for v in scan['roots']if v['root']in ROOTS};need(set(selected)==set(ROOTS),'Every five-root scan entry')
  registrations=[]
  for root in ROOTS:
   graph=nodes[root];sites=[c for c in graph['direct_calls']if c['target']==0x5ac140];need(len(sites)==1,'Exactly one literal registration in each selected root')
   call=sites[0];push=next(r for r in graph['instructions']if r['pc']+r['size']==call['site']);need(push['mnemonic']=='push','Literal callback immediately before registration CALL');value=int(push['operands'],0);need(value in REGISTERED,'Exact registered widget destructor target')
   fact=game.data(selected[root]['slot'],4);need(int.from_bytes(bytes.fromhex(fact['initial_hex']),'little')==root,'Current original initializer table root')
   registrations.append(dict(root=root,slot=selected[root]['slot'],slot_physical=fact,push_PC=push['pc'],CALL_pc=call['site'],callback=value,return_PC=call['return_pc'],callback_executed=False))
  vptrs=[dict(PC=r['pc'],instruction=r)for r in contracts if r['mnemonic']=='mov'and len(r['decoded_operands'])==2 and r['decoded_operands'][0]['kind']=='memory'and r['decoded_operands'][1]['kind']=='immediate'and r['decoded_operands'][0]['bits']==32 and game.section(r['decoded_operands'][1]['value'])and not game.executable(r['decoded_operands'][1]['value'])]
  payloads={'game-physical-graphs.json':nodes,'callback-physical-graphs.json':callback_nodes,'instruction-contracts.json':dict(instructions=contracts,selected_roots=list(ROOTS),registrations=registrations),'registration-roots.json':registrations,'source-vptr-store-candidates.json':vptrs,'unresolved-frontiers.json':dict(direct_deferred=deferred,normal_unresolved=[dict(entry=e,**v)for e,g in nodes.items()for v in g['unresolved_controls']],callback_unresolved=[dict(entry=e,**v)for e,g in callback_nodes.items()for v in g['unresolved_controls']],callback_direct_dependencies=[dict(entry=e,target=c['target'],CALL_pc=c['site'])for e,g in callback_nodes.items()for c in g['direct_calls']],callback_execution_claimed=False)}
  for name,value in payloads.items():p=out/name;p.write_text(json.dumps(value,indent=2)+'\n');pin(p)
  for p in (Path(__file__),R/'tools/m4-onexit-batch-recovery/recover.py',R/'tools/m4-service-initializers/recover.py',R/'tools/analysis/pe.py',M.DECODER):pin(p)
  for p in out.iterdir():
   if p.is_file():pin(p)
  passed=True
 finally:
  report=dict(passed=passed,scope='Physical source/callback/direct widget closure only; indirect targets require retained instance/vptr/slot provenance and finite normal source validation',selected_roots=list(ROOTS),counts=dict(roots=len(ROOTS),normal_graph_entries=len(locals().get('nodes',{})),unique_instructions=len(locals().get('rows',{})),unique_decoded_bytes=sum(r['size']for r in locals().get('rows',{}).values()),constructor_array_callback_entries=len(CONSTRUCTORS),registered_callback_entries=len(REGISTERED),fresh_decode_commands=len(commands)),commands=commands,normal_direct_deferred=locals().get('deferred',[]),native_executed=False,original_executed=False,constructor_callback_execution_claimed=False,registered_callback_execution_claimed=False,initializer_credit=0,files=PINS)
  p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(p),counts=report['counts'],deferred=report['normal_direct_deferred'])))
if __name__=='__main__':main(sys.argv[1])
