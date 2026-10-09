"""Bounded existing-graph MFC lookahead; no import, reanalysis, capture or credit."""
import hashlib,importlib.util,json,re,struct,sys
from collections import deque
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(x,w):
 if not x:raise RuntimeError(w)
def js(p):return json.loads(Path(p).read_bytes())
def main(name):
 out=ROOT/'reports/m4-strings-native'/name;need(re.fullmatch('next-mfc-r[1-9][0-9]*',name) and not out.exists(),'Fresh readonly MFC lookahead');pins={}
 def pin(p,h=None):
  p=Path(p).absolute();v=sha(p);need(h is None or h==v,'Existing static evidence binding');pins[str(p)]=v;return p
 classification=js(pin(ROOT/'reports/m4-service-initializers/static-r1/root-classification.json','57908c0839a3afc32c702471f87e94d497c38a86dd3f63de8123abecc9b65470'))
 games=js(pin(ROOT/'reports/m4-service-initializers/static-r1/game-all-initializer-graphs.json','da2482873e1678a0a2493ed7f60421440447c43e63826b53f2d5b09cf573ba5a'))
 mfcs=js(pin(ROOT/'reports/m4-service-initializers/static-r1/MFC42.DLL.provider.json','91096dad5ce5cad49941359c3c3e809f0101d4196ade44493e2e2c07e9b2cf03'))
 crtpath=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7');mfcpath=pin(ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8');gamepath=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
 pe_path=pin(ROOT/'tools/analysis/pe.py');spec=importlib.util.spec_from_file_location('mfc_lookahead_pe',pe_path);P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
 game=P.PEImage(gamepath.read_bytes());mfc=P.PEImage(mfcpath.read_bytes());crt=P.PEImage(crtpath.read_bytes())
 def read(image,address,size):
  off,_=image.rva_range(address-image.image_base,size);return image.read(off,size)
 group=[g for g in classification['groups'] if g['count']==32 and g['import_set']==['MFC42.DLL:823','MSVCRT.dll:__dllonexit','MSVCRT.dll:_onexit']];need(len(group)==1,'Exact existing 32-root family');rootrows=group[0]['roots'];roots=[r['entry'] for r in rootrows]
 todo=deque(roots);bodies={};instructions={};imports={};unknown=[]
 while todo:
  entry=todo.popleft()
  if entry in bodies:continue
  need(str(entry) in games,'Existing game graph in bounded closure');g=games[str(entry)];bodies[entry]=g
  for r in g['instructions']:
   need(read(game,r['pc'],r['size'])==bytes.fromhex(r['bytes']),'Exact original game closure bytes');need(r['pc'] not in instructions or instructions[r['pc']]==r,'Unique original instruction record');instructions[r['pc']]=r
  for c in g['direct_calls']:todo.append(c['target'])
  for i in g['import_sites']:imports[i['site']]=i
  unknown.extend(g['unresolved_controls'])
 entry=0x5f401ea0;allocation=mfcs['graphs'][str(entry)];free=mfcs['graphs'][str(0x5f401782)]
 for g in (allocation,free):
  for r in g['instructions']:need(read(mfc,r['pc'],r['size'])==bytes.fromhex(r['bytes']),'Exact original MFC allocation/free bytes')
 exports=crt.exports();names={n:crt.image_base+e['rva'] for e in exports for n in e['names']}
 imports_by_slot={mfc.image_base+s['iat_rva']:{'library':d['library'],**s} for d in mfc.imports() for s in d['symbols']}
 binding=[]
 for slot,label in [(0x5f49814c,'malloc'),(0x5f498148,'free')]:
  raw=struct.unpack('<I',read(mfc,slot,4))[0];need(imports_by_slot[slot]['name']==label and label in names,'Exact original MFC named CRT dependency');binding.append(dict(slot=slot,name=label,raw_bound_IAT=raw,current_exact_staged_CRT_export=names[label],raw_bound_matches_staged_export=raw==names[label],raw_bytes=read(mfc,slot,4).hex(),loader_resolution_observed=False))
 game_iat=0x5bb4bc;game_symbol=[s for d in game.imports() for s in d['symbols'] if game.image_base+s['iat_rva']==game_iat];need(len(game_symbol)==1 and game_symbol[0].get('ordinal')==823,'Exact original game MFC ordinal import')
 selected=next(e for e in mfcs['requested_exports'] if e['requested']==823)
 prior=js(pin(ROOT/'reports/m4-strings-native/preparation-r5/report.json','94382b5470bfe5d6bd1b0bbbabeca69df13c52de5a910c43de606c0db29524bf'))
 oldgame=js(pin(ROOT/'reports/m4-onexit-source/lifts-r4/report.json','03c369d138fb0c00a018f5bcc5c2640f71e4822aec2815816139048edf5bfd0e'));priorentries={v['entry'] for v in oldgame['dispatch_manifest']}|set(prior['physical_dispatch_entries'])|{0x42a570}
 new_entries=sorted(set(bodies)-priorentries)
 out.mkdir(parents=True)
 (out/'game-closure.json').write_text(json.dumps(dict(roots=rootrows,entries=sorted(bodies),new_entries=new_entries,unique_instructions=[instructions[p] for p in sorted(instructions)],imports=[imports[p] for p in sorted(imports)]),indent=2)+'\n')
 (out/'provider-local.json').write_text(json.dumps(dict(ordinal823=allocation,ordinal825=free,named_CRT_IATs=binding,game_IAT=dict(slot=game_iat,raw_bound=struct.unpack('<I',read(game,game_iat,4))[0],ordinal=823,target=entry),new_handler=dict(address=0x5f498970,raw=struct.unpack('<I',read(mfc,0x5f498970,4))[0],actual_initialized_value_observed=False)),indent=2)+'\n')
 next_steps=[
 'Export game closure and MFC823/825 from warm persistent Ghidra once; preserve exact literal rows including cold tails.',
 'Capture original table-order constructor results and exact MFC named malloc/free IAT resolution; existing bound IAT values differ from the exact staged CRT exports.',
 'Add an MFC source identity/page owner, validate register-indirect EBX target at actual source CALL5F401EB5, and reuse one actual mode1 CRT heap/private allocation owner.',
 'Keep game-published container storage live through selected103 scheduling and free through literal MFC825 to source CRTfree before heap destruction.',
 'Gate successful non-null allocator frontier with BEFORE-derived fullState/pages/ownedbytes and actual API facts; failure at5F41B01E requires initialized handler/TLS paths or explicit source-bound rejection retaining private ownership.',
 'Run allocation-failure, corrupt IAT/indirect target, stale/interior pointer, partial object write and cleanup controls before newroot credit.'
 ]
 for p in (Path(__file__),Path(sys.executable)):pin(p)
 for p in out.iterdir():
  if p.is_file():pin(p)
 result=dict(passed=True,scope='Bounded reuse of existing static graphs plus exact source byte/IAT rechecks only; no new analysis, execution, actual loaded provider or coverage claim',root_count=32,prospective_selected_count=103,game_literal_entries=len(bodies),game_new_entries=len(new_entries),game_reused_entries=len(bodies)-len(new_entries),game_unique_instructions=len(instructions),game_FS_sites=sum(len(g['FS_sites']) for g in bodies.values()),game_unresolved_controls=unknown,provider_local_allocation_instructions=33,provider_local_allocation_bytes=sum(r['size'] for r in allocation['instructions']),provider_normal_contiguous_span=dict(start=0x5f401ea0,end=0x5f401ec9,bytes=41,instructions=19),provider_cleanup_instructions=4,provider_cleanup_bytes=12,first_new_frontier=dict(pc=0x5f401eb5,bytes='ffd3',kind='CALL EBX',IAT_load_PC=0x5f401ea1,IAT=0x5f49814c,request_register='EBP copied from original [ESP+0xC]',intended_named_target='MSVCRT.dll:malloc',current_staged_target=names['malloc'],original_linkage_observed=False),failure_frontier=dict(branch_PC=0x5f401ebc,target=0x5f41b01e,handler_global=0x5f498970,raw_value=0xffffffff,cold_get_thread_context=0x5f4010fd,handler_indirect_PC=0x5f41b02f,fully_recovered=False),broad_provider_closure=dict(entries=len(selected['local_entries']),instructions=selected['unique_instructions'],FS_sites=len(selected['FS_sites']),unresolved_controls=len(selected['unresolved_controls'])),named_CRT_bindings=binding,loaded_module_identity_observed=False,original_executed=False,native_executed=False,new_roots_admitted=0,REA_or_Ghidra_new_sessions_opened=False,next_execution_steps=next_steps,files=pins)
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),game_entries=len(bodies),new_entries=len(new_entries),instructions=len(instructions))))
if __name__=='__main__':main(sys.argv[1])
