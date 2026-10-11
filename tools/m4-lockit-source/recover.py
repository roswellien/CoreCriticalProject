"""Exact four-root Lockit source contracts after accepted120; static only."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
SELECTED=(0x411010,0x4dc140,0x500660,0x5968f0)
SHAPES={
 0x411010:dict(object=0x6040b8,header=0x604e38,counter=0x604e3c,size=24,body=0x4125a0,handler=0x5aed59,read=0x4125a0,install=0x4125b6,saved=0x41264e,restore=0x412656,ret=0x412661,ret_cleanup=8,ctor=0x4125d4,dtor=0x412648,first=0x4125e9,second=0x412620),
 0x4dc140:dict(object=0x60b5a8,header=0x60b5c4,counter=0x60b5c8,size=24,body=0x4dc160,handler=0x5b8979,read=0x4dc167,install=0x4dc16e,saved=0x4dc20d,restore=0x4dc215,ret=0x4dc220,ret_cleanup=0,ctor=0x4dc193,dtor=0x4dc207,first=0x4dc1a8,second=0x4dc1df),
 0x500660:dict(object=0x60bfa0,auxiliary_object=0x60bf90,header=0x60bfb0,counter=0x60bfb4,size=20,body=0x500cd0,handler=0x5b99c9,read=0x500cd0,install=0x500ce6,saved=0x500d7e,restore=0x500d86,ret=0x500d91,ret_cleanup=8,ctor=0x500d04,dtor=0x500d78,first=0x500d19,second=0x500d50),
 0x5968f0:dict(object=0x731868,header=0x731894,counter=0x731898,size=24,body=0x596b00,handler=0x5ba419,read=0x596b07,install=0x596b0e,saved=0x596bad,restore=0x596bb5,ret=0x596bc0,ret_cleanup=0,ctor=0x596b33,dtor=0x596ba7,first=0x596b48,second=0x596b7f),
}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def module(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main(name):
 out=ROOT/'reports/m4-lockit-source'/name;need(not out.exists(),'Fresh source recovery');out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Frozen physical input '+str(p));pins[str(p)]=v;return p
 def load(p,h=None):return json.loads(pin(ROOT/p,h).read_bytes())
 def emit(n,v):
  p=out/n;p.write_text(json.dumps(v,indent=2)+'\n');pin(p);return p
 parent=load('reports/m4-joint-startup120-root/acceptance-r1/report.json','e640ff4eaa068a039a5e810ad99b4c0ca0336821b8b1a6f33f81012ad43ed0ee');need(parent['passed']and parent['connected_roots']==120,'Accepted120')
 frontier=load('reports/m4-lockit-frontier/recovery-r1/report.json','411a4d7cf07f7cd816eae3dc5baa3822d364d8369e77a8042195ee7afa0be46b');need(frontier['passed'],'Frozen five-root frontier')
 graphs={int(e):g for e,g in load('reports/m4-lockit-frontier/recovery-r1/game-normal-graphs.json',frontier['files'][str((ROOT/'reports/m4-lockit-frontier/recovery-r1/game-normal-graphs.json').resolve())]).items()}
 shapes=load('reports/m4-lockit-frontier/recovery-r1/root-shapes.json');selected=[x for x in shapes if x['root']in SELECTED];need(tuple(x['root']for x in selected)==SELECTED,'Four rooted table-order contracts')
 sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage
 game=PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes());cp=PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a').read_bytes())
 entries={e for r in selected for e in r['entries']};normal={e:graphs[e]for e in sorted(entries)};need(not any(g['unresolved_controls']for g in normal.values()),'Four closed game roots');rows={r['pc']:r for g in normal.values()for r in g['instructions']}
 old=load('reports/m4-next-source/recovery-r1/instruction-contracts.json','a58e31641f42e8e37c1d66bad5e41dd57854b82a7a00bd86a02b1bc85aec9108');need(len(old['selected_order'])==120,'Prior120 table entries')
 oldentries=set()
 for p in('reports/m4-onexit-source/lifts-r4/report.json','reports/m4-strings-source/lifts-r1/report.json','reports/m4-mfc-source/lifts-r1/report.json','reports/m4-fs-source/lifts-r1/report.json','reports/m4-container-source/lifts-r2/report.json','reports/m4-next-source/lifts-r1/report.json'):
  d=load(p);oldentries.update(x['entry']for x in d.get('source_bodies',{}).values());oldentries.update(x['entry']for x in d.get('dispatch_manifest',[]))
 new={e:g for e,g in normal.items()if e not in oldentries};need(len(new)==10,'Ten genuinely additive literal game bodies')
 parser=module(pin(ROOT/'tools/m4-crt-locale-batch-recovery/recover_v2.py'),'lockit_source_parser')
 def contracts(rs,pe):
  answer=[]
  for r in sorted(rs.values(),key=lambda r:r['pc']):
   raw=bytes.fromhex(r['bytes']);off,_=pe.rva_range(r['pc']-pe.image_base,len(raw));need(pe.data[off:off+len(raw)]==raw,'Every exact physical instruction '+hex(r['pc']));answer.append(parser.instruction_contract(dict(pc=r['pc'],width=r['size'],bytes_hex=r['bytes'],mnemonic=r['mnemonic'],operands=r['operands'].split(' <')[0])))
  return answer
 decoded=contracts(rows,game);by_pc={r['pc']:r for r in decoded};roots=[];frames=[];alloc=[];calls=[]
 for r in selected:
  root=r['root'];shape=SHAPES[root];off,_=game.rva_range(r['slot']-game.image_base,4);need(struct.unpack_from('<I',game.data,off)[0]==root,'Exact PE initializer slot')
  need(len(r['MFC_syntactic_CALLs'])==2 and r['MFC_syntactic_CALLs'][0]['immediate_requested_size']==shape['size'],'Two exact allocation sites')
  for role,site in(('shared-header',shape['first']),('object-sentinel',shape['second'])):
   call=rows[site];need(call['mnemonic']=='call'and call['operands'].startswith('0x5abd26 '),'Actual MFC823 source CALL')
   alloc.append(dict(root=root,CALL_pc=site,return_pc=site+call['size'],requested=shape['size'],kind=role,header_global=shape['header'],conditional=role=='shared-header',source_condition='Header source DWORD equals zero'if role=='shared-header'else'Always on constructor normal path',header_null_must_be_observed=True))
  frame=dict(root=root,entry=shape['body'],handler=shape['handler'],read=shape['read'],install=shape['install'],saved=shape['saved'],restore=shape['restore'],ret=shape['ret'],ret_cleanup=shape['ret_cleanup'],bytes=12,saved_operand=by_pc[shape['saved']]['decoded_operands'][1]);frames.append(frame)
  for kind,site,target,slot in(('constructor',shape['ctor'],0x7810a290,0x5bb4f8),('destructor',shape['dtor'],0x7810a350,0x5bb4f4)):
   row=rows[site];need(row['mnemonic']=='call'and row['operands']==f'dword ptr [0x{slot:x}]','Actual Lockit IAT call');calls.append(dict(root=root,kind=kind,CALL_pc=site,return_pc=site+row['size'],slot=slot,target=target,argument_bytes=0,RET_cleanup=0,scratch_object=True,pointee_write_claimed=False))
  roots.append(dict(entry=root,slot=r['slot'],entries=r['entries'],objects=[dict(address=shape['object'],bytes=16,static_source_object=True)],auxiliary_object=shape.get('auxiliary_object'),header_global=shape['header'],header_counter=shape['counter'],allocation_request=shape['size'],normal=r,registration=r['registration'],callback_execution_claimed=False,allocations_static_sites=2,actual_allocations_known=False,normal_FS=frame))
 order=sorted(old['selected_order']+[dict(entry=r['entry'],slot=r['slot'])for r in roots],key=lambda r:r['slot']);need(len(order)==124 and len({r['slot']for r in order})==124,'Prospective124 exact rooted order')
 pages=set(old['source_data_pages']);pages.update(x['address']&~4095 for g in normal.values()for x in g['absolute_memory_references']if x['address']);pages.update(shape['object']&~4095 for shape in SHAPES.values());pages.update((0x78145000,0x78146000));newpages=sorted(pages-set(old['source_data_pages']))
 providers={int(e):g for e,g in load('reports/m4-lockit-frontier/recovery-r1/provider-graphs.json').items()};providerrows={r['pc']:r for g in providers.values()for r in g['instructions']};providerdecoded=contracts(providerrows,cp);inputs=load('reports/m4-lockit-frontier/recovery-r1/provider-inputs.json');fast=load('reports/m4-lockit-frontier/recovery-r1/initialized-provider-path.json')
 interface=dict(schema='mw34-four-Lockit-source-v1',instructions=decoded,provider_instructions=providerdecoded,selected_order=order,roots=roots,source_data_pages=sorted(pages),source_code_pages=sorted({r['pc']&~4095 for r in rows.values()}),provider_code_pages=sorted({r['pc']&~4095 for r in providerrows.values()}),FS_frame_contracts=frames,allocations=alloc,Lockit_calls=calls,AFTER_machine_seed=False,provider_loaded_state_observed=False,provider_runtime_admission=False)
 emit('game-normal-graphs.json',normal);emit('game-new-graphs.json',new);emit('fs-roots.json',roots);emit('lockit-roots.json',roots);emit('FS-frame-contracts.json',frames);emit('allocation-contracts.json',alloc);emit('Lockit-call-contracts.json',calls);emit('provider-graphs.json',providers);emit('provider-inputs.json',inputs);emit('initialized-provider-path.json',fast);emit('instruction-contracts.json',interface);emit('source-page-inventory.json',dict(pages=sorted(pages),new_pages=newpages,static_game_pages_new=sorted(set(newpages)-{0x78145000,0x78146000}),provider_data_pages=[0x78145000,0x78146000],strategy='Exact every-section raw/BSS intersection plus authentic postDllMain pages, no initialized-state seed',new_game_imports=2,new_providers=1,allocation_static_sites=8,allocation_count_not_observed=True))
 for p in(Path(__file__),ROOT/'tools/analysis/pe.py'):pin(p)
 report=dict(passed=True,scope='Exact physical four smaller Lockit root bodies, table order, allocation/FS/import contracts; static only, genuine MSVCP loaded state pending',root_count=4,roots=roots,order=order,game_bodies=len(new),all_game_entries=sorted(normal),unique_instructions=len(rows),unique_bytes=sum(r['size']for r in rows.values()),provider_full_instructions=len(providerrows),provider_full_bytes=sum(r['size']for r in providerrows.values()),data_pages=sorted(pages),source_data_pages=sorted(pages),source_code_pages=interface['source_code_pages'],provider_code_pages=interface['provider_code_pages'],FS_frame_contracts=frames,Lockit_calls=calls,allocations=alloc,registration_callbacks=4,new_pages=newpages,provider_loaded_state_known=False,actual_allocation_count_known=False,native_execution_credit=False,original_execution_credit=False,initializer_credit=False,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),bodies=len(new),instructions=len(rows),physical_bytes=report['unique_bytes'],new_pages=[hex(x)for x in newpages])))
if __name__=='__main__':main(sys.argv[1])
