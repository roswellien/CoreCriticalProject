"""Additive exact string constructor contracts; source operands, never AFTER."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-strings-source'
sys.path.insert(0,str(ROOT/'tools/m4-service-initializers'))
sp=importlib.util.spec_from_file_location('recover',ROOT/'tools/m4-service-initializers/recover.py');service=importlib.util.module_from_spec(sp);sys.modules['recover']=service;sp.loader.exec_module(service)
sp=importlib.util.spec_from_file_location('registration_recovery',ROOT/'tools/m4-onexit-batch-recovery/recover.py');batch=importlib.util.module_from_spec(sp);sp.loader.exec_module(batch)
Module,ingest,closure,descendants,requirements=(batch.Module,batch.ingest,batch.closure,batch.descendants,batch.requirements)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh strings recovery');out.mkdir(parents=True);files={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Pinned input '+str(p));files[str(p)]=v;return p
 family=json.loads(pin(ROOT/'reports/m4-onexit-native/next-family-r2/report.json','2ad1d8ce2a7b7db6a108e1775def2eb1c89d6ab4e1803b7421c01feb23fc64c0').read_bytes());roots=[int(x,16)for x in family['recommended']['root_hex']]
 game=Module(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'));old=json.loads(pin(ROOT/'reports/m4-onexit-source/interface-r1/instruction-contracts.json','3f0d96b381dc4e89dc7cb63c7f252414ba1392deae140718daba6e17c3d438d3').read_bytes())
 graphs=json.loads(pin(ROOT/'reports/m4-service-initializers/static-r1/game-all-initializer-graphs.json').read_bytes())
 for g in graphs.values():ingest(game,g['instructions'])
 extra=json.loads(pin(ROOT/'reports/m4-service-initializers/static-r1/game-extra-callback-SEH-graphs.json').read_bytes())['graphs']
 for g in extra.values():ingest(game,g['instructions'])
 commands=[];normal,deferred=closure(game,roots,out,commands);need(not deferred,'Closed game string normal graphs')
 # An entry-relative Remill buffer cannot represent lower-address tail chunks.
 # Retain each tail as a separate exact literal body and dispatch to that PC.
 tailentries={r['to']for g in normal.values()for r in g['edges']if r['to']<g['entry']and 'jump'in r['kind']}
 tails,_=closure(game,sorted(tailentries),out,commands)
 normal.update(tails)
 priorentries=set(json.loads(pin(ROOT/'reports/m4-onexit-source/lifts-r4/report.json').read_bytes())['source_bodies'])|{'f_42a570'}
 new={str(e):g for e,g in normal.items()if f'f_{e:x}'not in priorentries}
 # Recover exact original table cells and literal strdup arguments. Symbolic
 # EAX tracks the immediate source value up to the import PUSH in each ctor.
 inv=json.loads(pin(ROOT/'reports/m4-rea-evaluation/initializer-inventory-r1.json').read_bytes());table=bytes.fromhex(inv['table_bytes_hex']);slots={struct.unpack_from('<I',table,i)[0]:inv['table_start']+i for i in range(0,len(table),4)}
 entries=[];strings=[];allrows={r['pc']:r for g in normal.values()for r in g['instructions']}
 for entry in roots:
  sub=[normal[e]for e in descendants(normal,entry)if e in normal];regs=[];strsites=[];objects=[]
  for g in sub:
   rs=g['instructions'];end={r['pc']+r['size']:r for r in rs}
   objects.extend(dict(pc=r['pc'],address=int(m[1],16))for r in rs if r['mnemonic']=='mov'and(m:=re.fullmatch(r'ecx, (0x[0-9a-f]+)',r['operands'])))
   for c in g['direct_calls']:
    if c['target']==0x5ac140:
     p=end[c['site']];need(p['mnemonic']=='push','Literal callback PUSH');regs.append(dict(push_pc=p['pc'],callback=int(p['operands'],16),CALL_pc=c['site'],return_pc=c['return_pc']))
   for c in g['import_sites']:
    if c['iat']!=0x5bb670:continue
    p=end[c['site']];need(p['mnemonic']=='push','Source string pointer PUSH');value=None
    if p['operands'].startswith('0x'):value=int(p['operands'],16)
    else:
     need(p['operands']=='eax','Bounded source immediate EAX string operand')
     prev=[r for r in rs if r['pc']<p['pc']and r['mnemonic']=='mov'and re.fullmatch(r'eax, 0x[0-9a-f]+',r['operands'])]
     if prev:value=int(prev[-1]['operands'].split(', ')[1],16)
     else:
      candidates={int(r['operands'],16)for n in sub for r in n['instructions']if r['pc']<0x5ac000 and r['mnemonic']=='push'and re.fullmatch('0x[0-9a-f]+',r['operands'])and game.section(int(r['operands'],16))and not game.executable(int(r['operands'],16))}
      need(len(candidates)==1,'One fixed caller-pushed string source for parameterized ctor '+hex(entry)+' '+str([hex(x)for x in candidates]));value=candidates.pop()
    literal=bytearray(4096)
    for section in game.image.sections:
     base=game.base+section['virtual_address'];lo=max(value,base);hi=min(value+4096,base+section['raw_size'])
     if lo<hi:
      off=section['raw_offset']+lo-base;literal[lo-value:hi-value]=game.image.data[off:off+hi-lo]
    z=literal.index(0);raw=bytes(literal[:z+1])
    # strlen/strcpy align source then inspect whole DWORDs until the NUL.
    aligned=(value+3)&~3;extent=max(value+len(raw),(value+len(raw)+3)&~3);size=extent-value;phys=bytes(literal[:size]);need(len(phys)==size,'Literal physical wordread extent')
    s=dict(root=entry,object_addresses=[o['address']for o in objects],CALL_pc=c['site'],return_pc=c['return_pc'],push_pc=p['pc'],source=value,bytes_hex=raw.hex(),size=len(raw),nul_address=value+len(raw)-1,physical_read_end=extent,physical_bytes_hex=phys.hex(),alignment_prefix=aligned-value,source_section=game.section(value)['name'],actual_strdup_called=True)
    if entry==0x4e6a10:
     need(value==0x60b868 and bytes(literal[:8])==bytes(8),'Literal BSS pointer/payload descriptor')
     # 4E6A68 loads the descriptor pointer before passing it to49D1C0.
     need(allrows[0x4e6a68]['bytes']=='8b07','Exact descriptor indirection')
     s.update(source=0,source_descriptor=value,descriptor_bytes_hex=bytes(literal[:8]).hex(),bytes_hex='',size=0,nul_address=None,physical_read_end=value+8,physical_bytes_hex=bytes(literal[:8]).hex(),alignment_prefix=0,actual_strdup_called=False,null_branch_source_PC=0x49d1cf)
    strsites.append(s);strings.append(s)
  need(len(regs)==1 and len(strsites)==1,'One strdup and registration per root')
  entries.append(dict(entry=entry,slot=slots[entry],registration=regs[0],string=strsites[0],objects=objects,normal=requirements(normal,descendants(normal,entry))))
 selected=sorted(old['selected_order']+[dict(entry=r['entry'],slot=r['slot'])for r in entries],key=lambda r:r['slot']);need(len(selected)==71 and len({r['slot']for r in selected})==71,'Exact71 original table-order cells')
 sp=importlib.util.spec_from_file_location('strings_operands',pin(ROOT/'tools/m4-crt-locale-batch-recovery/recover_v2.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
 contracts=[m.instruction_contract(dict(pc=r['pc'],width=r['size'],bytes_hex=r['bytes'],mnemonic=r['mnemonic'],operands=r['operands'].split(' <')[0]))for r in sorted(allrows.values(),key=lambda x:x['pc'])]
 pages={x['address']&~4095 for g in normal.values()for x in g['absolute_memory_references']}
 for r in entries:
  for o in r['objects']:pages.update(((o['address']&~4095),((o['address']+128)&~4095)))
 for s in strings:pages.update(range(s.get('source_descriptor',s['source'])&~4095,(s['physical_read_end']+4095)&~4095,4096))
 for fn,data in [('game-normal-graphs.json',normal),('game-new-graphs.json',new),('string-roots.json',entries),('string-inputs.json',strings),('instruction-contracts.json',dict(instructions=contracts,selected_order=selected,source_data_pages=sorted(pages),roots=entries,source_code_pages=sorted({r['pc']&~4095 for r in allrows.values()}),tail_entries=sorted(tailentries)))]:
  (out/fn).write_text(json.dumps(data,indent=2)+'\n');pin(out/fn)
 for p in (Path(__file__),ROOT/'tools/m4-onexit-batch-recovery/recover.py',ROOT/'tools/m4-service-initializers/recover.py'):pin(p)
 report=dict(passed=True,scope='Literal source string operands and game constructor graphs only',root_count=17,roots=entries,order=selected,game_bodies=len(new),prior_game_bodies_preserved=True,unique_instructions=len(allrows),data_pages=sorted(pages),code_pages=sorted({r['pc']&~4095 for r in allrows.values()}),commands=commands,files=files,original_executed=False,native_executed=False)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),roots=17,new_bodies=len(new),pages=sorted(pages))))
if __name__=='__main__':main(sys.argv[1])
