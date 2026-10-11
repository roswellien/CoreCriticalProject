"""Pinned physical next-root/provider dependency plan; no code or capture execution."""
from collections import deque
from pathlib import Path
import hashlib, importlib.util, json, re, struct, subprocess, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]

def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)

def main(name):
 out=R/'reports/m4-mfc1168-original'/name
 need(re.fullmatch('recovery-r[1-9][0-9]*',name)and not out.exists(),'Fresh additive output')
 out.mkdir(parents=True);files={};commands=[]
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No archive reader');v=sha(p);need(h is None or v==h,'Physical pin '+str(p));need(str(p)not in files or files[str(p)]==v,'Stable pin');files[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(R/p,h).read_bytes())
 def emit(n,v):
  p=out/n;p.write_text(json.dumps(v,indent=2)+'\n');pin(p);return p
 s=importlib.util.spec_from_file_location('mfc1168_PE',pin(R/'tools/m4-service-initializers/recover.py'));A=importlib.util.module_from_spec(s);s.loader.exec_module(A)
 modules={k:A.Module(pin(R/p,A.IDENTITIES[p]))for k,p in [('game','MW3/Mech3.exe'),('MFC','local/mw3-staged/Shared_DLLs/MFC42.DLL'),('CRT','local/mw3-staged/Shared_DLLs/MSVCRT.DLL')]}
 def parse(data):
  rows={}
  for line in data.splitlines():
   m=A.ROW.match(line)
   if not m:continue
   pc=int(m[1],16);code=bytes.fromhex(m[2]);asm=re.sub(r'\s+',' ',m[3].strip());op,_,args=asm.partition(' ')
   need(pc not in rows,'Unique source boundary');rows[pc]=dict(pc=pc,size=len(code),bytes=code.hex(),mnemonic=op,operands=args)
  return rows
 for key,module in modules.items():
  locator=pin(R/'reports/m4-service-initializers/static-r1'/(module.path.name+'.linear-lookup.txt'));module.rows.update(parse(locator.read_text()))
 # Exact export roots are PE identities, not semantic inferences from an ordinal.
 mfc=modules['MFC'];crt=modules['CRT'];game=modules['game']
 exp=next(x for x in mfc.exports if x['ordinal']==1168)
 need(exp==dict(ordinal=1168,rva=0x1083,names=[]),'Exact unnamed physical export1168')
 crt_exp=next(x for x in crt.exports if '_setmbcp'in x['names']);crt_entry=crt.base+crt_exp['rva'];need(crt_entry==0x78003ddb,'Exact CRT owning export')
 need(game.image.rva_u32(0x5e0040-game.base)==0x5ae3e4,'Exact physical root slot')
 need(game.imports[0x5bb210]['ordinal']==1168 and game.imports[0x5bb210]['library'].upper()=='MFC42.DLL','Owning game1168 IAT')
 need(game.imports[0x5bb674]['name']=='_setmbcp','Owning game CRT IAT')
 decoder=pin(A.DECODER,A.IDENTITIES[str(A.DECODER.relative_to(R)).replace('\\','/')])
 # Focus the exact returned-export and two literal callback entries. Decode beyond
 # those entries to retain normal RET plus cold branches, never claim callback reach.
 for key,label,start,end in [('MFC','1168',0x5f401083,0x5f4010fd),('MFC','callback-53fe',0x5f4053fe,0x5f405466),('MFC','callback-b293',0x5f40b293,0x5f40b350),('CRT','setmbcp',0x78003ddb,0x78004040)]:
  module=modules[key];argv=[str(decoder),'-d','--x86-asm-syntax=intel','--start-address='+hex(start),'--stop-address='+hex(end),str(module.path)]
  cp=subprocess.run(argv,capture_output=True,timeout=30,creationflags=0x08000000);need(cp.returncode==0,'Focused decode '+label)
  for suffix,value in [('.stdout',cp.stdout),('.stderr',cp.stderr)]:p=out/(label+suffix);p.write_bytes(value);pin(p)
  rows=parse(cp.stdout.decode());need(start in rows,'True focused entry '+label)
  for pc,row in rows.items():
   raw=bytes.fromhex(row['bytes']);off,_=module.image.rva_range(pc-module.base,len(raw));need(module.image.data[off:off+len(raw)]==raw,'Focused opcode '+hex(pc))
  module.rows.update(rows);commands.append(dict(argv=argv,exit_code=0))
 game_graphs={e:A.walk(game,e)for e in [0x5ae3e4,0x5ae3a8,0x5abed0]}
 game_rows={x['pc']:x for g in game_graphs.values()for x in g['instructions']};need(len(game_rows)==25,'Exact25 game rows')
 provider={};limits={}
 for key,entries in [('MFC',[0x5f401083,0x5f4053fe,0x5f40b293]),('CRT',[crt_entry])]:
  # Retain a finite static direct-call frontier. Indirect controls remain open;
  # executable literals never become a prediction that the callback was called.
  nodes,deferred=A.closure(modules[key],entries,maximum=80);provider[key]=nodes;limits[key]=deferred
 for key,graphs in [('game',game_graphs),*provider.items()]:
  module=modules[key]
  for graph in graphs.values():
   for row in graph['instructions']:
    raw=bytes.fromhex(row['bytes']);off,_=module.image.rva_range(row['pc']-module.base,len(raw));need(module.image.data[off:off+len(raw)]==raw,'Every selected physical instruction '+hex(row['pc']))
 emit('game-graphs.json',game_graphs);emit('provider-graphs.json',provider)
 dependencies=[];refs=[];open_controls=[]
 for key,graphs in provider.items():
  for entry,g in graphs.items():
   dependencies.extend(dict(module=key,entry=entry,**c)for c in g['direct_calls'])
   dependencies.extend(dict(module=key,entry=entry,**c)for c in g['import_sites'])
   refs.extend(dict(module=key,entry=entry,**c)for c in g['absolute_memory_references'])
   open_controls.extend(dict(module=key,entry=entry,**c)for c in g['unresolved_controls'])
 emit('dependencies.json',dependencies);emit('physical-memory-inputs.json',refs);emit('unresolved-controls.json',open_controls)
 mfc_primary=[dict(entry=e,instructions=provider['MFC'][e]['instruction_count'],imports=provider['MFC'][e]['import_sites'],direct_calls=provider['MFC'][e]['direct_calls'],unresolved_controls=provider['MFC'][e]['unresolved_controls'])for e in [0x5f401083,0x5f401000,0x5f4010ab,0x5f4053fe,0x5f40b293]]
 root_contract=dict(entry=0x5ae3e4,slot=0x5e0040,source_object=0x7365a4,source_object_lifetime='Literal ECX retained as ESI then returned as EAX; not the MFC return object',constructor=0x5ae3d1,helper=0x5ae3a8,arguments=[0,0x421],MFC_import=dict(game_trampoline=0x5abed0,IAT=0x5bb210,ordinal=1168,preferred_entry=0x5f401083,names=exp['names']),MFC_result_writes=[dict(PC=0x5ae3b7,offset=0x14,bytes=1,value=0),dict(PC=0x5ae3ba,offset=0x1040,bytes=4,value=0x421)],CRT_import=dict(CALL_pc=0x5ae3c4,IAT=0x5bb674,name='_setmbcp',preferred_entry=crt_entry,source_argument_signed=-3,return_pc=0x5ae3ca),helper_RET_cleanup=8,root_callbacks=[],observed=False)
 emit('root-contract.json',root_contract);emit('primary-provider-frontier.json',mfc_primary)
 # Physical .data zero bytes do not assert current TLS index/object state.
 domains=[dict(module='MFC',address=a,bytes=n,PE_initial=mfc.data(a,n),runtime_input_required=True)for a,n in [(0x5f4cb000,4),(0x5f4cb008,24),(0x5f4cb03c,4),(0x5f4cb040,4)]]
 domains.append(dict(module='game',address=0x7365a4,bytes=4,PE_initial=game.data(0x7365a4,4),runtime_input_required=True))
 emit('domain-inputs.json',domains)
 plan='''# Genuine next-root probe prerequisites

Root5AE3E4 at slot5E0040 has25 physical game instructions. Its fixed game ECX7365A4 is retained as ESI and returned, while the two writes use the distinct actual MFC1168 EAX result. The game object must not be substituted for that live provider object.

The pinned MFC export table resolves ordinal1168 to unnamed5F401083. It calls5F401000 with ECX5F4CB03C and literal callback5F4053FE. That helper reads5F4CB000, the slot ordinal in5F4CB03C, TlsGetValue, the current-thread array/count/object and actual object+4. A zero+4 result calls5F4010AB on5F4CB040 with callback5F40B293. Both cached and lazy paths are retained statically. No default live path is claimed.

A bounded authentic-loader probe must capture untouched whole5F4CB000, the actual TLS manager/index/current-thread array and returned object's complete allocation/backing extent BEFORE invoking1168; then capture the actual reached path, every named API frame/return, each callback occurrence, new allocation initial backing and every literal write. Calling1168 to discover a pointer is itself a potentially mutating invocation and cannot precede the BEFORE receipt. Do not seed a TLS index, manager, per-thread object or success return.

At game5AE3B7 capture actual result+14 before/after and at5AE3BA capture result+1040 before/after. Preserve all untouched bytes of that same actual backing. The wrapper's retained game object is a separate input and must remain source-derived. No native owner association is admitted from a coincidental address.

The reached argument0 causes the game to CALL physical CRT _setmbcp78003DDB with signed argument−3. Capture current CRT data and every reached codepage/locale API dependency from genuine post-DllMain state. The full static CRT graph includes branches for other codepages; only the actual−3 path may receive finite admission. Preserve actual CPU40/FX512/ENV28 and full cdecl frame at entry/return, source RET8 cleanup, status/error outputs and table mutations. No success shortcut or host locale conversion replaces the physical source.

The existing130 capture's46 pages omit5F4CB000 and dynamic TLS state. Its wholebefore pages cannot close this live domain. First prefix should be one root under the authentic accepted bootstrap and actual current-thread association, not a broad131 schedule. Determine whether actual manager/current-thread object already exists; if not, recover every literal lazy constructor/allocator/critical-section dependency and its cleanup before native integration.

Static source/side-effect recovery is credited only as a plan. No original execution, native execution, callback, allocation count, current default codepage or initializer inventory acceptance is claimed.
'''
 p=out/'next-probe.md';p.write_text(plan,encoding='utf-8');pin(p)
 pin(__file__);pin(sys.executable);pin(R/'tools/analysis/pe.py')
 report=dict(passed=True,scope='Pinned physical root5AE3E4 and MFC1168/CRT _setmbcp finite static dependency plan',game_instructions=25,game_bytes=sum(x['size']for x in game_rows.values()),provider_entries={k:len(v)for k,v in provider.items()},provider_instructions={k:len({x['pc']for g in v.values()for x in g['instructions']})for k,v in provider.items()},deferred_direct_entries=limits,unresolved_control_count=len(open_controls),root=root_contract,primary_frontier=str(out/'primary-provider-frontier.json'),probe_plan=str(p),commands=commands,files=files,capture_reader_opened=False,original_executed=False,native_executed=False,default_live_object_measured=False,initializer_credit=0)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k in ['passed','game_instructions','provider_entries','provider_instructions','unresolved_control_count']}));print(sha(out/'report.json'))
if __name__=='__main__':main(sys.argv[1])
