"""Literal original MFC-family game contracts and sparse tail entry closure."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-mfc-source'
sys.path.insert(0,str(ROOT/'tools/m4-service-initializers'))
spec=importlib.util.spec_from_file_location('recover',ROOT/'tools/m4-service-initializers/recover.py');service=importlib.util.module_from_spec(spec);sys.modules['recover']=service;spec.loader.exec_module(service)
spec=importlib.util.spec_from_file_location('mfc_game_recovery',ROOT/'tools/m4-onexit-batch-recovery/recover.py');batch=importlib.util.module_from_spec(spec);spec.loader.exec_module(batch)
Module,ingest,closure,descendants,requirements=(batch.Module,batch.ingest,batch.closure,batch.descendants,batch.requirements)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(x,w):
 if not x:raise ValueError(w)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh original MFC recovery');out.mkdir(parents=True);files={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact original source identity');files[str(p)]=v;return p
 look=json.loads(pin(ROOT/'reports/m4-strings-native/next-mfc-r1/game-closure.json','d6c646f3d80b6f414ddaf8053fe4ddef7d451c9af714ad24c79d05346997f81e').read_bytes());roots=look['roots'];need(len(roots)==32,'Exact new family32')
 loader=json.loads(pin(BASE/'loader-identity-r1/report.json','7925f659144954487b1b13d781d4aee48aa0b8d20887ce9ee8aa40ce7a12b09b').read_bytes());need(loader['passed'],'Genuine loader-resolved MFC named CRT imports')
 game=Module(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'));allgraphs=json.loads(pin(ROOT/'reports/m4-service-initializers/static-r1/game-all-initializer-graphs.json','da2482873e1678a0a2493ed7f60421440447c43e63826b53f2d5b09cf573ba5a').read_bytes())
 for graph in allgraphs.values():ingest(game,graph['instructions'])
 commands=[];normal,deferred=closure(game,[r['entry']for r in roots],out,commands);need(not deferred,'Closed literal normal constructor source graphs')
 tails={edge['to']for graph in normal.values()for edge in graph['edges']if edge['to']<graph['entry']and 'jump'in edge['kind']};tailgraphs,taildeferred=closure(game,sorted(tails),out,commands);need(not taildeferred,'Literal lower-tail dependencies closed');normal.update(tailgraphs)
 prior=json.loads(pin(ROOT/'reports/m4-strings-native/preparation-r5/report.json','94382b5470bfe5d6bd1b0bbbabeca69df13c52de5a910c43de606c0db29524bf').read_bytes());oldgame=json.loads(pin(ROOT/'reports/m4-onexit-source/lifts-r4/report.json','03c369d138fb0c00a018f5bcc5c2640f71e4822aec2815816139048edf5bfd0e').read_bytes());priorentries={v['entry']for v in oldgame['dispatch_manifest']}|set(prior['physical_dispatch_entries'])|{0x42a570};new={str(entry):graph for entry,graph in normal.items()if entry not in priorentries}
 rows={r['pc']:r for graph in normal.values()for r in graph['instructions']};entries=[];pages={ref['address']&~4095 for graph in normal.values()for ref in graph['absolute_memory_references']}
 for item in roots:
  subentries=descendants(normal,item['entry']);sub=[normal[e]for e in subentries if e in normal];registration=[];objects=[]
  for graph in sub:
   byend={r['pc']+r['size']:r for r in graph['instructions']}
   objects.extend(dict(pc=r['pc'],address=int(m[1],16))for r in graph['instructions']if r['mnemonic']=='mov'and(m:=re.fullmatch(r'ecx, (0x[0-9a-f]+)',r['operands'])))
   for call in graph['direct_calls']:
    if call['target']==0x5ac140:
     previous=byend[call['site']];need(previous['mnemonic']=='push'and previous['operands'].startswith('0x'),'Literal executable callback PUSH');registration.append(dict(push_pc=previous['pc'],callback=int(previous['operands'],16),CALL_pc=call['site'],return_pc=call['return_pc']))
  objects=list({o['address']:o for o in objects}.values());need(len(registration)==1 and len(objects)==1,'One actual source object and callback per root')
  off,_=game.image.rva_range(item['slot']-game.base,4);need(struct.unpack_from('<I',game.image.data,off)[0]==item['entry'],'Actual original table entry')
  for o in objects:pages.update((o['address']&~4095,(o['address']+128)&~4095))
  entries.append(dict(**item,registration=registration[0],objects=objects,normal=requirements(normal,subentries),callback_execution_claimed=False,allocation_contract_status='Literal BEFORE-derived constructor allocation/field derivation follows; no allocator result assumptions'))
 for row in rows.values():
  raw=bytes.fromhex(row['bytes']);off,_=game.image.rva_range(row['pc']-game.base,len(raw));need(game.image.data[off:off+len(raw)]==raw,'Exact original game source instruction')
 spec=importlib.util.spec_from_file_location('mfc_original_operand_parser',pin(ROOT/'tools/m4-crt-locale-batch-recovery/recover_v2.py'));parser=importlib.util.module_from_spec(spec);spec.loader.exec_module(parser)
 contracts=[parser.instruction_contract(dict(pc=r['pc'],width=r['size'],bytes_hex=r['bytes'],mnemonic=r['mnemonic'],operands=r['operands'].split(' <')[0]))for r in sorted(rows.values(),key=lambda x:x['pc'])]
 old=json.loads(pin(ROOT/'reports/m4-strings-source/recovery-r7/instruction-contracts.json','e1a4a4e2a6f1d55b5a1a94b10254202e88304e67dfbedd77326e72f0986e97a9').read_bytes());order=sorted(old['selected_order']+[dict(entry=r['entry'],slot=r['slot'])for r in entries],key=lambda r:r['slot']);need(len(order)==103 and len({r['slot']for r in order})==103,'Exact prospective original103 order')
 pages.update(old['source_data_pages']);need(not any(r['mnemonic'].startswith('f')for r in rows.values()),'Integer-only new game family')
 artifacts={'game-normal-graphs.json':normal,'game-new-graphs.json':new,'mfc-roots.json':entries,'instruction-contracts.json':dict(schema='mw34-mfc-original-game-source-v1',instructions=contracts,selected_order=order,source_data_pages=sorted(pages),source_code_pages=sorted({r['pc']&~4095 for r in rows.values()}),roots=entries,tail_entries=sorted(tails),AFTER_machine_seed=False),'source-page-inventory.json':dict(pages=sorted(pages),strategy='For every4096B page, intersect each original section raw extent exactly; copy those physical bytes and retain zeros only for unmapped raw/BSS remainder. Never classify a partially raw page wholly zero.',pages_are_complete=True)}
 for name_,value in artifacts.items():(out/name_).write_text(json.dumps(value,indent=2)+'\n');pin(out/name_)
 for p in (Path(__file__),ROOT/'tools/m4-onexit-batch-recovery/recover.py',ROOT/'tools/m4-service-initializers/recover.py',Path(sys.executable)):pin(p)
 report=dict(passed=True,schema='mw34-mfc-original-source-recovery-v1',scope='Exact original32 new game constructors and sparse lower-tail entry contracts only; no execution credit',root_count=32,roots=entries,order=order,game_bodies=len(new),all_game_entries=len(normal),unique_instructions=len(rows),data_pages=sorted(pages),source_data_pages=sorted(pages),code_pages=sorted({r['pc']&~4095 for r in rows.values()}),tail_entries=sorted(tails),prior_game_bodies_preserved=True,commands=commands,files=files,original_executed=False,native_executed=False,initializer_credit=False)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),new_bodies=len(new),all_bodies=len(normal),data_pages=len(pages))))
if __name__=='__main__':main(sys.argv[1])
