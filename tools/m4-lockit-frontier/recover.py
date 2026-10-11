"""Static exact-image Lockit family frontier; no guest execution or credit."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-service-initializers'))
from recover import Module
spec=importlib.util.spec_from_file_location('lockit_batch',ROOT/'tools/m4-onexit-batch-recovery/recover.py')
B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)
FAMILY=(0x411010,0x4b7f70,0x4dc140,0x500660,0x5968f0)

def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)

def main(name):
 out=ROOT/'reports/m4-lockit-frontier'/name;need(not out.exists(),'Fresh static recovery');out.mkdir(parents=True);pins={};commands=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact static input '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Immutable input');pins[str(p)]=v;return p
 def emit(n,v):
  p=out/n;p.write_text(json.dumps(v,indent=2)+'\n');pin(p)
 parent=pin(ROOT/'reports/m4-joint-startup116-root/acceptance-r1/report.json');accepted=json.loads(parent.read_bytes());need(accepted['passed']and accepted['connected_roots']==116,'Accepted116 only')
 game=Module(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'))
 cp=Module(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a'))
 frontier=json.loads(pin(ROOT/'reports/m4-joint-startup116-root/next-frontier-r1/remaining-roots.json').read_bytes())
 roots=[x for x in frontier if x['entry']in FAMILY];need(tuple(x['entry']for x in roots)==FAMILY,'Exact five table-order roots')
 allgraphs=json.loads(pin(ROOT/'reports/m4-service-initializers/static-r1/game-all-initializer-graphs.json','da2482873e1678a0a2493ed7f60421440447c43e63826b53f2d5b09cf573ba5a').read_bytes())
 dossier=json.loads(pin(ROOT/'reports/m4-service-initializers/static-r1/MSVCP50.DLL.provider.json').read_bytes())
 for g in allgraphs.values():B.ingest(game,g['instructions'])
 for g in dossier['graphs'].values():B.ingest(cp,g['instructions'])
 normal,deferred=B.closure(game,FAMILY,out,commands);need(not deferred,'Literal local family closure')
 lower={x['to']for g in normal.values()for x in g['edges']if x['to']<g['entry']and 'jump'in x['kind']}
 tail,deferred=B.closure(game,sorted(lower),out,commands);need(not deferred,'Exact lower shared bodies');normal.update(tail)
 rows={r['pc']:r for g in normal.values()for r in g['instructions']}
 # Indirect calls are import values retained in nonvolatile source registers.
 projections=[dict(pc=p,register='ebp',IAT=0x5bb4f8,definition_PC=0x4bab1a,provider=0x7810a290)for p in(0x4bab28,0x4bac27,0x4bac8f,0x4bad25,0x4bad8f)]
 projections += [dict(pc=p,register='ebx',IAT=0x5bb4f8,definition_PC=0x4bae49,provider=0x7810a290)for p in(0x4bae58,0x4bae90)]
 projections += [dict(pc=p,register='ebp',IAT=0x5bb4f4,definition_PC=0x4bae5c,provider=0x7810a350)for p in(0x4baeac,0x4baed4)]
 unresolved={r['pc']:r for g in normal.values()for r in g['unresolved_controls']};need(set(unresolved)=={p['pc']for p in projections},'Only nine statically named Lockit register calls')
 for p in projections:
  call,load=rows[p['pc']],rows[p['definition_PC']]
  need(call['mnemonic']=='call'and call['operands']==p['register'],'Exact actual indirect source CALL')
  need(load['mnemonic']=='mov'and load['operands']==f"{p['register']}, dword ptr [0x{p['IAT']:x}]",'Exact named IAT source register definition')
  # Canonical owner function contains no other explicit register definition;
  # callees must preserve the nonvolatile register in the future source model.
  owner=normal[0x4bab00 if p['definition_PC']==0x4bab1a else 0x4bae30]
  definitions=[r for r in owner['instructions']if r['mnemonic']in('mov','lea','xor','sub','add','and','or','pop')and r['operands'].split(',')[0]==p['register']and p['definition_PC']<=r['pc']<p['pc']]
  need(len(definitions)==1 and definitions[0]['pc']==p['definition_PC'],'No explicit source overwrite before indirect CALL')
  p.update(source_call=call,source_definition=load,evidence_scope='Static within-body provenance; retained nonvolatile value across each genuine callee still requires persistent source execution proof')
 provider_entries=(0x7810a290,0x7810a350,0x781102f0,0x781102c0,0x781104d8)
 providers={e:dossier['graphs'][str(e)]for e in provider_entries};provider_rows={r['pc']:r for g in providers.values()for r in g['instructions']}
 fastpcs=(0x7810a290,0x7810a295,0x7810a296,0x7810a297,0x7810a29a,0x7810a29c,0x7810a306,0x7810a30b,0x7810a311,0x7810a313,0x7810a314,0x7810a315)
 fast=[provider_rows[p]for p in fastpcs];dtor=providers[0x7810a350]['instructions']
 exports=[]
 for name_,target in(('??0_Lockit@std@@QAE@XZ',0x7810a290),('??1_Lockit@std@@QAE@XZ',0x7810a350)):
  x=next(x for x in dossier['requested_exports']if x['requested']==name_);need(x['preferred_va']==target,'Physical named Lockit export');exports.append(x)
 inputs=dict(preferred_module_base=cp.base,entry_point=cp.base+cp.image.entry_point_rva,game_imports=[dict(address=s,raw=game.data(s,4),symbol=game.imports[s])for s in(0x5bb4f8,0x5bb4f4)],provider_imports=[dict(address=s,raw=cp.data(s,4),symbol=cp.imports[s])for s in(0x78146184,0x7814618c,0x78146190,0x78146194,0x78146198,0x78146278,0x7814627c)],lazy_state=cp.data(0x78145658,4),critical_section=cp.data(0x78145640,24),DLL_termination_globals=[cp.data(a,4)for a in(0x7814577c,0x78145780)],exports=exports,actual_loaded_state_known=False,actual_loaded_CS_identity_known=False)
 perroot=[]
 for r in roots:
  off,_=game.image.rva_range(r['slot']-game.base,4);need(struct.unpack_from('<I',game.image.data,off)[0]==r['entry'],'Original initializer table DWORD')
  gentries=B.descendants(normal,r['entry']);gr=[normal[e]for e in gentries if e in normal];rr={x['pc']:x for g in gr for x in g['instructions']};alloc=[];regs=[]
  for g in gr:
   for call in g['direct_calls']:
    if call['target']==0x5abd26:
     prev=next((x for x in g['instructions']if x['pc']+x['size']==call['site']),None)
     size=int(prev['operands'],16)if prev and prev['mnemonic']=='push'and re.fullmatch('0x[0-9a-f]+',prev['operands'])else None
     alloc.append(dict(CALL_pc=call['site'],return_PC=call['return_pc'],immediate_requested_size=size,previous_row=prev))
    if call['target']==0x5ac140:
     prev=next(x for x in g['instructions']if x['pc']+x['size']==call['site']);need(prev['mnemonic']=='push','Exact callback source PUSH');regs.append(dict(CALL_pc=call['site'],callback=int(prev['operands'],16),push_PC=prev['pc']))
  need(len(regs)==1,'One literal registration per root')
  perroot.append(dict(root=r['entry'],slot=r['slot'],entries=gentries,unique_rows=len(rr),bytes=sum(x['size']for x in rr.values()),MFC_syntactic_CALLs=alloc,registration=regs[0],FS_sites=[x for x in rr.values()if 'fs:['in x['operands']],absolute_memory_refs=[x for g in gr for x in g['absolute_memory_references']],unresolved_before_named_projection=[x for g in gr for x in g['unresolved_controls']]))
 old=json.loads(pin(ROOT/'reports/m4-container-source/recovery-r3/instruction-contracts.json','3aeed69c05122c689a2f0951c2d49052db307beba917f5bcf756969aa7bbb09d').read_bytes());oldentries=set()
 for p in('reports/m4-onexit-source/lifts-r4/report.json','reports/m4-strings-source/lifts-r1/report.json','reports/m4-mfc-source/lifts-r1/report.json','reports/m4-fs-source/lifts-r1/report.json','reports/m4-container-source/lifts-r2/report.json'):
  q=json.loads(pin(ROOT/p).read_bytes())
  if 'dispatch_manifest'in q:oldentries.update(x['entry']for x in q['dispatch_manifest'])
  if 'source_bodies'in q:oldentries.update(x['entry']for x in q['source_bodies'].values())
 new={e:g for e,g in normal.items()if e not in oldentries};need(all(p in rows for p in (0x4125d4,0x4dc193,0x500d04,0x596b33)),'Actual family lock source sites')
 parser=load_parser(pin(ROOT/'tools/m4-crt-locale-batch-recovery/recover_v2.py'))
 def contracts(rs):return[parser.instruction_contract(dict(pc=r['pc'],width=r['size'],bytes_hex=r['bytes'],mnemonic=r['mnemonic'],operands=r['operands'].split(' <')[0]))for r in sorted(rs.values(),key=lambda r:r['pc'])]
 emit('game-normal-graphs.json',normal);emit('game-new-graphs.json',new);emit('provider-graphs.json',providers);emit('provider-inputs.json',inputs);emit('root-shapes.json',perroot);emit('named-indirect-projections.json',projections)
 emit('instruction-contracts.json',dict(game=contracts(rows),provider=contracts(provider_rows),selected_order=sorted(old['selected_order']+[dict(entry=r['entry'],slot=r['slot'])for r in roots],key=lambda r:r['slot']),candidate_count=121,original_execution_credit=False,native_execution_credit=False))
 emit('initialized-provider-path.json',dict(condition='Source state78145658==2 and genuine privately owned initialized CS78145640',constructor_entry=0x7810a290,constructor_rows=fast,destructor_entry=0x7810a350,destructor_rows=dtor,constructor_returns_original_ECX_in_EAX=True,destructor_VOID_no_EAX_override=True,normal_FS_sites=0,missing_behavior='Distinct MSVCP typed full-native CS owner, read-time exact owning game/provider imports and authentic post-loader source state',no_op_lock_allowed=False,source_seed_or_API_result_injection=False,source_model_measured_lifecycle_required=True,unadmitted_zero_state_initialization=True,unadmitted_contended_state1_Sleep=True,unadmitted_shutdown_callback=True))
 for p in(Path(__file__),ROOT/'tools/m4-service-initializers/recover.py',ROOT/'tools/m4-onexit-batch-recovery/recover.py',ROOT/'tools/analysis/pe.py'):pin(p)
 report=dict(passed=True,scope='Physical static five-root Lockit family and exact named register-import projections; no loaded-state, geometry execution or initializer credit',roots=list(FAMILY),root_count=5,new_game_bodies=len(new),all_game_entries=len(normal),unique_game_rows=len(rows),physical_game_bytes=sum(r['size']for r in rows.values()),lower_tail_entries=sorted(lower),provider_full_rows=len(provider_rows),provider_full_bytes=sum(r['size']for r in provider_rows.values()),initialized_constructor_rows=len(fast),initialized_constructor_bytes=sum(r['size']for r in fast),destructor_rows=len(dtor),destructor_bytes=sum(r['size']for r in dtor),named_indirect_CALLs=len(projections),registration_callbacks=5,actual_loaded_state_known=False,actual_allocations_known=False,original_executed=False,native_executed=False,initializer_credit=False,excluded_extra_Lockit_root=0x4e1ca0,commands=commands,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps({k:report[k]for k in('passed','new_game_bodies','all_game_entries','unique_game_rows','physical_game_bytes','provider_full_rows','named_indirect_CALLs')}));print(sha(out/'report.json'))

def load_parser(p):
 s=importlib.util.spec_from_file_location('lockit_operand_parser',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
if __name__=='__main__':main(sys.argv[1])
