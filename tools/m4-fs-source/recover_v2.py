"""Additive literal normal FS game contracts; accepted103 preserved."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-fs-source'
sys.path.insert(0,str(ROOT/'tools/m4-service-initializers'))
spec=importlib.util.spec_from_file_location('recover',ROOT/'tools/m4-service-initializers/recover.py');service=importlib.util.module_from_spec(spec);sys.modules['recover']=service;spec.loader.exec_module(service)
spec=importlib.util.spec_from_file_location('fs_game_recovery',ROOT/'tools/m4-onexit-batch-recovery/recover.py');batch=importlib.util.module_from_spec(spec);spec.loader.exec_module(batch)
Module,ingest,closure,descendants,requirements=(batch.Module,batch.ingest,batch.closure,batch.descendants,batch.requirements)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(x,w):
 if not x:raise ValueError(w)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh original MFC recovery');out.mkdir(parents=True);files={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact original source identity');files[str(p)]=v;return p
 plan=json.loads(pin(ROOT/'reports/m4-mfc-source/normal-FS-plan-r1/plan.json').read_bytes());pin(ROOT/'reports/m4-mfc-source/normal-FS-plan-r1/report.json','76b05a5e234e7647a8e04a128e1187d82a148dc1ee17a117bea5e5886d56a879');pin(ROOT/'reports/m4-joint-startup103-root/acceptance-r1/report.json','13cc2567f30f2dae2d12991a3a76aa6c953c70a49148dc4ed13df34837b14c7c');roots=[dict(entry=r['entry'],slot=r['slot']) for r in plan['roots']];need(len(roots)==6,'Exact new FS family6')
 loader=json.loads(pin(ROOT/'reports/m4-mfc-source/loader-identity-r1/report.json','7925f659144954487b1b13d781d4aee48aa0b8d20887ce9ee8aa40ce7a12b09b').read_bytes());need(loader['passed'],'Genuine loader-resolved MFC named CRT imports')
 game=Module(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'));allgraphs=json.loads(pin(ROOT/'reports/m4-service-initializers/static-r1/game-all-initializer-graphs.json','da2482873e1678a0a2493ed7f60421440447c43e63826b53f2d5b09cf573ba5a').read_bytes())
 for graph in allgraphs.values():ingest(game,graph['instructions'])
 commands=[];normal,deferred=closure(game,[r['entry']for r in roots],out,commands);need(not deferred,'Closed literal normal constructor source graphs')
 tails={edge['to']for graph in normal.values()for edge in graph['edges']if edge['to']<graph['entry']and 'jump'in edge['kind']};tailgraphs,taildeferred=closure(game,sorted(tails),out,commands);need(not taildeferred,'Literal lower-tail dependencies closed');normal.update(tailgraphs)
 prior=json.loads(pin(ROOT/'reports/m4-strings-native/preparation-r5/report.json','94382b5470bfe5d6bd1b0bbbabeca69df13c52de5a910c43de606c0db29524bf').read_bytes());oldgame=json.loads(pin(ROOT/'reports/m4-onexit-source/lifts-r4/report.json','03c369d138fb0c00a018f5bcc5c2640f71e4822aec2815816139048edf5bfd0e').read_bytes());priorentries={v['entry']for v in oldgame['dispatch_manifest']}|set(prior['physical_dispatch_entries'])|{0x42a570};priorentries.update(json.loads(pin(ROOT/'reports/m4-mfc-source/lifts-r1/report.json','2b1c617c612cc35ccbf76ed644d023752f3ba946d124bfe62a43f6a643c55f9f').read_bytes())['source_bodies'][n]['entry'] for n in json.loads((ROOT/'reports/m4-mfc-source/lifts-r1/report.json').read_bytes())['source_bodies']);new={str(entry):graph for entry,graph in normal.items()if entry not in priorentries}
 rows={r['pc']:r for graph in normal.values()for r in graph['instructions']};entries=[];pages={ref['address']&~4095 for graph in normal.values()for ref in graph['absolute_memory_references']}
 for item in roots:
  subentries=descendants(normal,item['entry']);sub=[normal[e]for e in subentries if e in normal];registration=[];objects=[]
  for graph in sub:
   byend={r['pc']+r['size']:r for r in graph['instructions']}
   objects.extend(dict(pc=r['pc'],address=int(m[1],16))for r in graph['instructions']if r['mnemonic']=='mov'and(m:=re.fullmatch(r'ecx, (0x[0-9a-f]+)',r['operands'])))
   for call in graph['direct_calls']:
    if call['target']==0x5ac140:
     candidates=[r for r in graph['instructions']if r['pc']<call['site']and r['mnemonic']=='push'and re.fullmatch('0x[0-9a-f]+',r['operands'])and game.executable(int(r['operands'],16))];need(candidates,'Literal executable callback PUSH '+hex(call['site']));previous=max(candidates,key=lambda r:r['pc']);between=[r for r in graph['instructions']if previous['pc']<r['pc']<call['site']];need(all(r['mnemonic']=='mov'and 'esp'not in r['operands']for r in between),'Callback remains at actual top of source stack');registration.append(dict(push_pc=previous['pc'],callback=int(previous['operands'],16),CALL_pc=call['site'],return_pc=call['return_pc']))
  for graph in sub:
   for row in graph['instructions']:
    m=re.fullmatch(r'byte ptr \[(0x[0-9a-f]+)\], [a-z]+',row['operands'])
    if row['mnemonic']=='mov'and m:objects.append(dict(pc=row['pc'],address=int(m[1],16),inline_absolute_header=True))
  objects=list({o['address']:o for o in objects if game.section(o['address'])and not game.executable(o['address'])}.values());need(len(registration)==1 and objects,'Actual source object headers and one callback per root '+hex(item['entry'])+' '+str(objects)+' '+str(registration))
  off,_=game.image.rva_range(item['slot']-game.base,4);need(struct.unpack_from('<I',game.image.data,off)[0]==item['entry'],'Actual original table entry')
  for o in objects:pages.update((o['address']&~4095,(o['address']+128)&~4095))
  entries.append(dict(**item,registration=registration[0],objects=objects,normal=requirements(normal,subentries),callback_execution_claimed=False,allocation_contract_status='Persistent BEFORE-derived FS frame/shared-registry/allocation derivation follows; no allocator result assumptions'))
 for row in rows.values():
  raw=bytes.fromhex(row['bytes']);off,_=game.image.rva_range(row['pc']-game.base,len(raw));need(game.image.data[off:off+len(raw)]==raw,'Exact original game source instruction')
 spec=importlib.util.spec_from_file_location('mfc_original_operand_parser',pin(ROOT/'tools/m4-crt-locale-batch-recovery/recover_v2.py'));parser=importlib.util.module_from_spec(spec);spec.loader.exec_module(parser)
 contracts=[parser.instruction_contract(dict(pc=r['pc'],width=r['size'],bytes_hex=r['bytes'],mnemonic=r['mnemonic'],operands=r['operands'].split(' <')[0]))for r in sorted(rows.values(),key=lambda x:x['pc'])]
 old=json.loads(pin(ROOT/'reports/m4-mfc-source/recovery-r4/instruction-contracts.json','e01223ba12a4e07f50fa00a23c1297f1dcf9920d259c99ef5c4df9073d3d770e').read_bytes());order=sorted(old['selected_order']+[dict(entry=r['entry'],slot=r['slot'])for r in entries],key=lambda r:r['slot']);need(len(order)==109 and len({r['slot']for r in order})==109,'Exact prospective original109 order')
 pages.update(old['source_data_pages']);need(not any(r['mnemonic'].startswith('f')for r in rows.values()),'Integer-only new game family')
 artifacts={'game-normal-graphs.json':normal,'game-new-graphs.json':new,'fs-roots.json':entries,'instruction-contracts.json':dict(schema='mw34-fs-original-game-source-v1',instructions=contracts,selected_order=order,source_data_pages=sorted(pages),source_code_pages=sorted({r['pc']&~4095 for r in rows.values()}),roots=entries,tail_entries=sorted(tails),AFTER_machine_seed=False),'source-page-inventory.json':dict(pages=sorted(pages),strategy='For every4096B page, intersect each original section raw extent exactly; copy those physical bytes and retain zeros only for unmapped raw/BSS remainder. Never classify a partially raw page wholly zero.',pages_are_complete=True)}
 for name_,value in artifacts.items():(out/name_).write_text(json.dumps(value,indent=2)+'\n');pin(out/name_)
 for p in (Path(__file__),ROOT/'tools/m4-onexit-batch-recovery/recover.py',ROOT/'tools/m4-service-initializers/recover.py',Path(sys.executable)):pin(p)
 report=dict(passed=True,schema='mw34-fs-original-source-recovery-v1',scope='Exact original6 new FS game constructors and sparse lower-tail entry contracts only; no execution credit',root_count=6,roots=entries,order=order,game_bodies=len(new),all_game_entries=len(normal),unique_instructions=len(rows),data_pages=sorted(pages),source_data_pages=sorted(pages),code_pages=sorted({r['pc']&~4095 for r in rows.values()}),tail_entries=sorted(tails),prior_game_bodies_preserved=True,commands=commands,files=files,original_executed=False,native_executed=False,initializer_credit=False)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),new_bodies=len(new),all_bodies=len(normal),data_pages=len(pages))))
if __name__=='__main__':main(sys.argv[1])
