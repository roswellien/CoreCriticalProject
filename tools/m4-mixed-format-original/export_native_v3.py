"""Finite source-use interfaces for the measured mixed initializer; no outcomes seed runtime."""
from pathlib import Path
import hashlib,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-mixed-format-original'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh finite export');pins={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix!='.mwb','No capture reader');v=sha(p);need(h is None or h==v,'Exact source identity');pins[str(p)]=v;return p
 def js(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
 recovery=js(BASE/'recovery-r1/report.json','5627b4234b16f5bdb493f4102f541166cbf8bde11c53c3b9a691a24d1230e5fa');c=js(BASE/'recovery-r1/instruction-contracts.json');rows={r['pc']:r for r in c['instructions']};graphs=js(BASE/'recovery-r1/game-normal-graphs.json');root=c['roots'][0]
 source=js(BASE/'original-source-r7/report.json','3a30f008243812bc5205487cbb08265e4ab9fd1e0e8377cb7ccd176230929823');d=js(BASE/'original-source-r7/source-derivations.json')[0];lifts=js(BASE/'lifts-r1/report.json','44138f2cb1c9eb6208bd16d7fc8c6de1a400869aa70a1ef2788058a89f9ec569')
 reviewed=js(ROOT/'reports/m4-tree-review/mixed-original-r1/report.json','d2d959744455ad49cbad5f121c3a8ca7d749cca6ed11f9feb6ece55f27152ad3');need(source['passed']and lifts['passed']and reviewed['passed'],'Source and independently reviewed original seams')
 for p,h in lifts['files'].items():pin(p,h)
 sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage
 game=PEImage(pin(ROOT/'MW3/Mech3.exe').read_bytes());normal_loaded={0x5bb4bc:0x5f401ea0,0x5bb4f8:0x7810a290,0x5bb4f4:0x7810a350,0x5bb5a8:0x780264a9,0x5bb664:0x780012b3,0x5bb658:0x78022b9a,0x5bb670:0x78010a6d,0x5bb530:0x78002fe5,0x5bb52c:0x78004a36}
 imports=[]
 for entry,g in graphs.items():
  for site in g['import_sites']:
   cell=site['iat'];off,_=game.rva_range(cell-game.image_base,4);raw=struct.unpack_from('<I',game.data,off)[0];pc=site['site'];r=rows[pc];normal=pc in d['source_PCs']
   imports.append(dict(root=0x4e1ca0,function=int(entry),source_pc=pc,cell=cell,source_bytes_hex=r['bytes_hex'],raw_file_pointer32=raw,named_loaded_pointer32=normal_loaded[cell],library=site['symbol']['library'],name=site['symbol'].get('name'),ordinal=site['symbol'].get('ordinal'),kind=site['kind'],return_pc=site['return_pc'],source_target_register=None,source_target_definition='literal owning IAT read at this CALL/JMP; no held target register',reached_literal_normal=normal,physical_input_offset=off))
 owner_API={r['source_game_CALL']:r for r in d['API_inputs']if r.get('source_game_CALL')in(0x49cc8d,0x4e5325,0x4e535b)};need(len(owner_API)==3,'Exact three measured mixed MFC owner inputs')
 owners=[];accesses=[];pubs=[]
 for i,a in enumerate(c['allocations']):
  measured=owner_API[a['CALL_pc']];pointer=measured['actual_EAX'];capacity=measured['initial_capacity'];publication=[(0x49cc9a,0x60b750),(0x4e5334,0x60b7d4),(0x4e5366,0x60b764)][i]
  owners.append(dict(root=0x4e1ca0,owner_index=i,allocation_CALL_pc=a['CALL_pc'],allocation_return_pc=a['return_pc'],requested=a['request'],role=a['role'],source_allocator_thunk=0x5abd26,source_MFC_target=0x5f401ea0,MFC_malloc_CALL_pc=0x5f401eb5,MFC_malloc_return_pc=0x5f401eb7,source_HeapAlloc_CALL_pc=0x7800137f,source_HeapAlloc_return_pc=0x78001385,source_game_frame_from_HeapAlloc_frame=104,publication_pc=publication[0],publication_address=publication[1],measured_capacity=capacity,capacity_is_observed_domain_only=True,measured_API_request=measured['args'][2],initial_bytes_are_actual_API_inputs_not_zero_seed=True))
  for n,(pc,address,value,width,write)in enumerate(d['source_accesses']):
   if pointer<=address and address+width<=pointer+capacity:
    affine=next((dict(owner_index=j,offset=value-b['actual_EAX'])for j,b in enumerate(owner_API.values())if b['actual_EAX']<=value<b['actual_EAX']+b['initial_capacity']),None)
    row=dict(root=0x4e1ca0,owner_index=i,allocation_CALL_pc=a['CALL_pc'],source_pc=pc,owned_offset=address-pointer,width=width,write=bool(write),source_access_index=n,source_value_relation=affine or dict(literal=value))
    accesses.append(row)
  pc,address=publication;matched=[(n,x)for n,x in enumerate(d['source_accesses'])if x[0]==pc and x[1]==address and x[2]==pointer and x[3:]==[4,1]];need(len(matched)==1,'Publication source value exactly returned live owner')
  pubs.append(dict(root=0x4e1ca0,owner_index=i,allocation_CALL_pc=a['CALL_pc'],publication_pc=pc,publication_address=address,width=4,source_value_relation=dict(owner_index=i,offset=0),source_access_index=matched[0][0],source_instruction=rows[pc]))
 need(len(accesses)==10 and all(r['write']for r in accesses),'Ten exact literal MFC owner writes; no reached dynamic MFC owner read')
 fs=[]
 for f in c['FS_frame_contracts']:
  fs.append(dict(root=0x4e1ca0,function=f['entry'],read_pc=f['read'],install_pc=f['install'],saved_predecessor_read_pc=f['saved'],restore_pc=f['restore'],return_pc=f['ret'],return_cleanup=f['ret_cleanup'],handler=f['handler'],record_bytes=12,source_definition='literal FS:[0] predecessor read, PUSH handler/PUSH predecessor, install currentESP, restore saved predecessor',source_instructions=[rows[f[k]]for k in('read','install','saved','restore')]))
 lockit=[]
 for l in c['Lockit_calls']:
  lea=rows[l['scratch_LEA_pc']];call=rows[l['CALL_pc']];need(lea['decoded_operands'][1]['terms']==[dict(register='esp',scale=1)]and lea['decoded_operands'][1]['displacement']==44,'Exact LEA scratch+44')
  middle=[r for r in c['instructions']if l['scratch_LEA_pc']<r['pc']<l['CALL_pc']];need(all(not(r['decoded_operands']and r['decoded_operands'][0].get('kind')=='register'and r['decoded_operands'][0].get('register')=='ecx')for r in middle),'All literal instructions between LEA and CALL retain ECX')
  lockit.append(dict(root=0x4e1ca0,CALL_pc=l['CALL_pc'],return_pc=l['return_pc'],owning_IAT=l['IAT'],source_target=l['target'],scratch_register='ecx',scratch_definition_pc=l['scratch_LEA_pc'],scratch_source_ESP_offset=44,scratch_from_entered_CALL_frame_offset=48,definition_instruction=lea,CALL_instruction=call,retained_register_instruction_PCs=[r['pc']for r in middle],outer_function=0x4e5290,normal_balanced_pair=0,constructor_original_response='7810A311 before MOV EAX,EDI and source epilogue'if l['IAT']==0x5bb4f8 else'7810A364 actual preRET',postRET_cpu_supplied_as_input=False))
 contract=dict(schema='mw34-mixed-native-finite-source-interface-v1',root=0x4e1ca0,slot=0x5e01d4,entry_to_object=dict(entry=0x4e1ca0,object=0x60b668,extent=264,format_owned_pointer_field=0x60b66c,filename=0x5e97dc,filename_hex='76616c76657300'),registration=dict(CALL_pc=0x4e1cd5,callback=0x4e1ce0,wrapper=0x5ac140,source_lifecycle_already_accepted=True),shared_dispatch_entries=[0x4de9c0,0x5abd26,0x5ac110,0x5ac140,0x5ac580],new_dispatch_entries=sorted(b['entry']for b in lifts['source_bodies'].values()),owning_IAT_rows=imports,MFC_allocation_contracts=owners,owned_access_contracts=accesses,publication_contracts=pubs,FS_frame_contracts=fs,Lockit_scratch_contracts=lockit,source_format_domain=dict(CALLs=[0x4dea15,0x4deab1,0x4dead1],format_string=0x5e37f0,format_hex='2573257300',output_owned_field=0x60b66c,publication_pc=0x4deabc,request_formula='literal filename NUL scan plus4',normal_filename='valves',normal_request=11,normal_actual_capacity=16,normal_return=10,finite_domain_only=True),source_strdup_normal_domain=dict(static_CALL_pc=0x4e22f2,owning_IAT=0x5bb670,normal_NULL_calls=5,actual_provider_reached=False,cold_non_NULL_path_admitted=False),genuine_original_source_sha256=sha(BASE/'original-source-r7/report.json'),compiled_lifts_sha256=sha(BASE/'lifts-r1/report.json'),actual_owner_capacity_or_output_values_supplied_to_native=False,native_acceptance=False)
 out.mkdir(parents=True)
 for name,value in [('contracts.json',contract),('owned-accesses.json',accesses),('allocation-publications.json',pubs),('FS-frame-contracts.json',fs),('owning-IAT-contracts.json',imports),('Lockit-scratch-contracts.json',lockit)]:
  (out/name).write_text(json.dumps(value,indent=2)+'\n');pin(out/name)
 pin(__file__)
 (out/'report.json').write_text(json.dumps(dict(passed=True,scope='Measured finite mixed source interface and exact fourteen O0/O2 object paths for native integration; no runtime effects or expected heap bytes provided.',contracts_sha256=sha(out/'contracts.json'),root=0x4e1ca0,new_bodies=7,new_objects=14,MFC_allocation_sites=3,owned_access_rows=10,publication_rows=3,FS_frames=2,Lockit_scratch_rows=2,source_report_sha256=sha(BASE/'original-source-r7/report.json'),lifts_sha256=sha(BASE/'lifts-r1/report.json'),files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
