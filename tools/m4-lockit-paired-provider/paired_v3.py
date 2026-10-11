"""Bounded paired original/native124 initialization data and numeric contract.

Every branch retains its genuine bytes. Exact typed IAT identities and one
source-derived indeterminate representation byte are relations, not edits.
Real32 provider/API volatile registers and scratch-stack contents are retained
as observations; strict native source State/stack proof is a separate gate.
"""
from pathlib import Path
import collections, hashlib, importlib.util, json, struct, sys, traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PINS={}
PAGES=(0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000,0x5ca000,0x5ed000,0x5f4000,0x603000,0x606000,0x609000,0x638000,0x63c000,0x63d000,0x72c000,0x730000,0x9a1000,0x5e4000,0x5e5000,0x5e7000,0x72b000,0x731000,0x5f498000,0x736000,0x5f4cc000,0x5bc000,0x5cf000,0x5fc000,0x7810a000,0x78145000,0x78146000)
IATS={0x5bb4fc:(0x780c10f0,0x1df59c),0x5bb52c:(0x78004a36,0x1decb0),0x5bb530:(0x78002fe5,0x1deca2),0x5bb6dc:(None,0x1df20c),0x5bb670:(0x78010a6d,0x1df886),0x5bb4bc:(0x5f401ea0,0x80000337),0x5bb454:(0x5f4020b4,0x8000021c),0x5bb4c8:(0x5f401782,0x80000339),0x5bb4f8:(0x7810a290,0x1df582),0x5bb4f4:(0x7810a350,0x1df568)}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(x,s):
 if not x:raise ValueError(s)
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Frozen paired input '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable paired input');PINS[str(p)]=v;return p
def load(n,p):
 s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def words(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def equal(a,b,s):need(a==b,s)
def delta(a,b):
 if a==b:return []
 return [dict(offset=i,original=x,native=y)for i,(x,y)in enumerate(zip(a,b))if x!=y]
def main(native_report,name,native_source_report,native_source_sha):
 out=ROOT/'reports/m4-lockit-paired-provider'/name;need(not out.exists(),'Fresh paired policy');out.mkdir(parents=True);passed=False;counts=collections.Counter();rows=[];field_rows=[];private_rows=[];new_header_rows=[];provider_page_rows=[];new_FS_rows=[];API_rows=[];observer_spans=[];loader_rows=[];loader_differences=[];loaded_page=b'';raw_page=b'';fsbindings=[];pointer_fields=[];header_fields=[];lockit_allocations=[]
 try:
  original_report=json.loads(pin(ROOT/'reports/m4-lockit-original/original-validation-r2/report.json','4a6f998156b13fc24ed6e6cb285ae482ff562c8d267d1a171c35b0bf7a36c6c3').read_bytes());need(original_report['passed'],'Corrected actual original run')
  need(json.loads(pin(ROOT/'reports/m4-next-source/original-game-source-r1/report.json').read_bytes())['passed'],'Literal original120constructor/string source gate')
  source_gate=json.loads(pin(native_source_report,native_source_sha).read_bytes());need(source_gate['passed'],'Strict persistent native124 source gate')
  need(json.loads(pin(ROOT/'reports/m4-lockit-paired-provider/original-r2/report.json','48f184d6edbaae5e1ec9d384f743089210e65dea9655822a4f517b41fa3b757b').read_bytes())['passed'],'Independent four literal original source/owned/header gates')
  nr=pin(native_report);execution=json.loads(nr.read_bytes());need(execution['passed']and execution['build_sha256']=='05a198d319f2e3ee2259b998a8989db23df0b20afd40416fb185e7a0b1d17c30','Exact finalprep5/build4 actual native124 run');pin(execution['build_path'],execution['build_sha256'])
  D=load('paired_direct',ROOT/'tools/m4-crt-allocation-root/run_v2.py');J=load('paired_old_numeric',ROOT/'tools/m4-joint-startup27-review/observe.py');m,_,_,_=J.models();G=load('paired_original_source',ROOT/'tools/m4-mfc-source/compare_original_game.py');G.PINS=PINS
  rootrows=json.loads(pin(ROOT/'reports/m4-onexit-batch-recovery/recovery-r3/registration-roots.json','88979fcc7494e8ada7821bc4b2f804f7194ca43f3265621b86a50fb32ffe84fc').read_bytes())+json.loads(pin(ROOT/'reports/m4-strings-source/recovery-r7/string-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-mfc-source/recovery-r4/mfc-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-fs-source/recovery-r3/fs-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-container-source/recovery-r3/container-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-next-source/recovery-r1/fixed-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-lockit-source/recovery-r1/lockit-roots.json').read_bytes());
  for item in json.loads(pin(ROOT/'reports/m4-container-source/allocation-interface-r1/string-inputs.json').read_bytes()):next(r for r in rootrows if r['entry']==item['root'])['string']=item
  roots={r['entry']:r['registration']['callback']for r in rootrows};stringrows={r['entry']:r for r in rootrows if 'string'in r}
  order=json.loads(pin(ROOT/'reports/m4-lockit-original/original-preparation-r4/report.json','6a25b9b16ccdbfefe30488ea6b87afd5c266489fd63f2b5710c05c04a14fd68b').read_bytes())['order'];G.PAGES=PAGES;ori=D.DirectSet(Path(original_report['original_capture']),pin);MFC_IMPORTS=[tuple(v[:3])for v in struct.iter_unpack('<7I',ori.data('mfc-import-ledger.bin'))];G.MFC_IMPORTS=MFC_IMPORTS;H=load('mfc_header_source_relations',ROOT/'tools/m4-mfc-source/header_relations_v2.py');newroots={r['entry']:r for r in rootrows if r['entry']in{r['entry']for r in json.loads(pin(ROOT/'reports/m4-mfc-source/recovery-r4/mfc-roots.json').read_bytes())}};field_contract=json.loads(pin(ROOT/'reports/m4-mfc-source/field-contracts-r1/report.json','63cd8d2665580dc397745d0f34769dac321089fa2ec422eeea7681b08e3a1a55').read_bytes());pointer_fields=field_contract['pointer_fields'];header_fields=field_contract['header_fields'];geometry=json.loads(pin(ROOT/'reports/m4-mfc-source/allocation-contracts-r4/report.json','30ef9954b16ba185294871d5cb419df502b656aab7f12fc521a4e3b09fe156f2').read_bytes());bindings=json.loads(pin(ROOT/'reports/m4-mfc-source/allocation-contracts-r4/allocation-inputs.json',geometry['allocation_inputs_sha256']).read_bytes());spi_phase=next(i for i,r in enumerate(order)if r['entry']==0x482cf0);oldheader_phase=next(i for i,r in enumerate(order)if r['entry']==0x4c58c0);graphs=json.loads(pin(ROOT/'reports/m4-service-initializers/static-r1/game-all-initializer-graphs.json').read_bytes());nextfp=next(i for i,r in enumerate(order)if i>spi_phase and graphs[str(r['entry'])]['FP_sites']);need(len(MFC_IMPORTS)==511,'All physical/authenticated original MFC import slots')
  fsbindings=json.loads(pin(ROOT/'reports/m4-fs-source/allocation-interface-r1/allocation-inputs.json','a3fb27e6f16c12bbc7499c912415b2c294d74e97c7600dbaeb3be4770ab492ff').read_bytes());original_fs_headers=json.loads(pin(ROOT/'reports/m4-next-source/original-game-source-r1/new-header-derivations.json').read_bytes());native_fs_headers=json.loads(pin(Path(native_source_report).parent/'new-header-derivations.json').read_bytes());vectorinputs=json.loads(pin(ROOT/'reports/m4-container-source/allocation-interface-r1/vector-endpoints.json').read_bytes());loaded_page=ori.data('mfc540-loaded-page.bin');raw_page=bytearray(4096)
  PE=load('paired_container_PE',ROOT/'tools/analysis/pe.py');mfc=PE.PEImage(ori.data('mfc-image.bin'));raw_page=bytearray(4096)
  for sec in mfc.sections:
   lo=max(0x5f4cc000,mfc.image_base+sec['virtual_address']);hi=min(0x5f4cd000,mfc.image_base+sec['virtual_address']+sec['raw_size'])
   if hi>lo:off=sec['raw_offset']+lo-mfc.image_base-sec['virtual_address'];raw_page[lo-0x5f4cc000:hi-0x5f4cc000]=mfc.data[off:off+hi-lo]
  loader_rows=[];loader_differences=delta(loaded_page,raw_page);observer_spans=[]
  observer_gate=json.loads(pin(ROOT/'reports/m4-vtable-review/observer-compiled-r1/report.json').read_bytes());need(observer_gate['passed'],'Compiled transparent FS original observer');build=json.loads(pin(ROOT/'reports/m4-lockit-original/original-build-r3/build.json','3a2214354b280439342e5b128bf48d980d9f3fb8ac9aab88ac8d8e570ed693a6').read_bytes());execution=json.loads(pin(ROOT/'reports/m4-lockit-original/original-execution-r2/report.json','2caaa9be2cd24c2862d4f6e98cf92f5418a4492ffda244a8a19527c15e65e5a1').read_bytes());worker_path=Path(build['worker']);worker_bytes=pin(worker_path,execution['files'][str(worker_path.resolve())]).read_bytes();worker=PE.PEImage(worker_bytes);need(worker.image_base==0x18000000,'Actual original fixed declared worker base');observer_spans=[]
  for hook in json.loads(pin(ROOT/'reports/m4-lockit-original/original-preparation-r4/fs-hook-bindings.json').read_bytes()):
   pc=hook['PC'];raw=bytes.fromhex(hook['raw_bytes'])
   if pc&~4095 not in PAGES:continue
   key=struct.pack('<3I',pc,len(raw),hook['kind']);matches=[i for i in range(len(worker_bytes))if worker_bytes.startswith(key,i)and worker_bytes[i+16:i+16+len(raw)]==raw];need(len(matches)==1,'One physical linked FsHook initializer for observed source span');target=words(worker_bytes,matches[0]+12)[0];toff,_=worker.rva_range(target-worker.image_base,1);need(worker_bytes[toff:toff+2]==bytes.fromhex('c705')and words(worker_bytes,toff+6)[0]==hook['kind']and worker_bytes[toff+10]==0xa3,'Actual compiled trampoline begins declaring exact event direction and saving EAX; full ESP-before-push checked by pinned compiled observer gate');original_bytes=b'\xe9'+struct.pack('<I',(target-pc-5)&0xffffffff)+b'\x90'*(len(raw)-5);observer_spans.append(dict(PC=pc,width=len(raw),original_hex=original_bytes.hex(),native_hex=raw.hex(),compiled_target=target,compiled_table_offset=matches[0],declared_symbol=hook['declared_observer']))
  need(sorted((r['PC'],r['width'])for r in observer_spans)==[(0x4824a7,6),(0x4824ae,7),(0x4824ed,7),(0x482b47,6),(0x482b4e,7),(0x482b8e,7)],'Only six exact observed-page original observer spans')
  loader_rows=[];loader_differences=delta(loaded_page,raw_page);need(len(loaded_page)==4096 and words(loaded_page,0xb54)[0]==words(raw_page,0xb54)[0]==0x5f4cecec,'Same-worker loaded/raw page exact borrowed source DWORD')
  original_source_dir=ROOT/'reports/m4-lockit-paired-provider/original-r2'
  original_source_gate=json.loads(pin(original_source_dir/'report.json','48f184d6edbaae5e1ec9d384f743089210e65dea9655822a4f517b41fa3b757b').read_bytes())
  def source_artifact(folder,gate,name):
   path=(folder/name).resolve();return json.loads(pin(path,gate['files'][str(path)]).read_bytes())
  original_owners=source_artifact(original_source_dir,original_source_gate,'original-owned-source-relations.json')
  original_owner_writes=source_artifact(original_source_dir,original_source_gate,'original-source-owned-contract-corroborations.json')
  original_accesses=source_artifact(original_source_dir,original_source_gate,'original-source-access-ledgers.json')
  lockit_patches=source_artifact(original_source_dir,original_source_gate,'provider-observer-spans.json')
  native_header_rows=source_artifact(Path(native_source_report).parent,source_gate,'Lockit-header-derivations.json')
  need(len(native_header_rows)==108,'Nine literal branch fields in12 native sequences')
  lockit_allocations=json.loads(pin(ROOT/'reports/m4-lockit-source/owned-contracts-r1/allocation-inputs.json','7f4777615485a734e8009d76b5d9999ea290d294f95474be97f1f920ff74e543').read_bytes())
  lockit_fields=json.loads(pin(ROOT/'reports/m4-lockit-source/owned-contracts-r1/static-field-writes.json','f7233347a2ac63fd282c0358d669f2f0b8a1381307c2ee86c3630190bf71c3e7').read_bytes())
  # The wrapper's auxiliary byte store follows the constructor and is outside
  # the constructor-only static field inventory. Authenticate its literal
  # physical instruction, then join its complete original/source byteflow.
  game_instructions=json.loads(pin(ROOT/'reports/m4-lockit-source/recovery-r1/instruction-contracts.json','c102e277742f2cd6e2a352f9e40f44f7d7d2ea1107d8bde242d103b586e75f25').read_bytes())['instructions']
  auxiliary=next(r for r in game_instructions if r['pc']==0x50068b)
  need(auxiliary['bytes_hex']=='881590bf6000' and auxiliary['mnemonic']=='mov' and auxiliary['explicit_memory_writes']==[0] and auxiliary['decoded_operands']==[dict(kind='memory',bits=8,segment='default',terms=[],displacement=0x60bf90),dict(kind='register',register='dl',bits=8)],'Literal complete wrapper auxiliary MOV [60BF90],DL instruction')
  lockit_fields.append(dict(root=0x500660,pc=0x50068b,address=0x60bf90,write=True,bytes=1,source_value=None))
  native_branch_identities={(r['root'],r['field'],r['write_pc'])for r in native_header_rows}
  authored_branch_identities={(r['root'],r['address'],r['pc'])for r in lockit_fields if(r['root'],r['address'],r['pc'])in native_branch_identities}
  need(len(authored_branch_identities)==9 and authored_branch_identities==native_branch_identities,'All nine source-declared constructor/wrapper branch fields')
  lockit_roots={r['root']for r in lockit_allocations};private_rows=[];new_header_rows=[];provider_page_rows=[];new_FS_rows=[];API_rows=[]
  loaded_cp_IAT=ori.data('lockit/post-DllMain/2014601216-page.bin');loaded_cp_RW=ori.data('lockit/post-DllMain/2014597120-page.bin')
  native_Lockit_derivations=source_artifact(Path(native_source_report).parent,source_gate,'Lockit-source-derivations.json')
  full_original_gate=json.loads(pin(ROOT/'reports/m4-lockit-review/full-original-r1/report.json','570bc3dc54aadcb7b67abccb06182c7177eeb7d059bb31ea5caf40f57625659f').read_bytes());need(full_original_gate['passed']and full_original_gate['original_validation_sha256']=='4a6f998156b13fc24ed6e6cb285ae482ff562c8d267d1a171c35b0bf7a36c6c3','Independent six complete compiled/final-linked observer function and actual target authentication')
  first_Lockit_phase=next(i for i,r in enumerate(order)if r['entry']in lockit_roots);first_Lockit_snaps=ori.data(f'phase/0/{first_Lockit_phase}/lockit-snapshots.bin');need(len(first_Lockit_snaps)==6*12988,'Full actual first six Lockit boundary identity');original_API_shim_targets={slot:words(first_Lockit_snaps,8892+(slot&4095))[0]for slot in(0x78146198,0x78146184)}
  original_thread=words(ori.data('lockit/thread.bin'))[0];need(original_thread>0,'Actual original loaded process current thread input')
  lockit_API_imports={cell:target for cell,target,*rest in struct.iter_unpack('<5I',ori.data('lockit/import-ledger.bin'))}
  need(len(loaded_cp_IAT)==len(loaded_cp_RW)==4096 and words(loaded_cp_RW,0x658)[0]==2,'Authentic complete initialized CP input pages')
  for level in ('O0','O2'):
   native=D.DirectSet(nr.parent/level/'transport.json',pin)
   for seq in range(6):
    expected_callbacks=[];values={};live_string_fields={};live_mfc_fields={};live_header_fields={};live_fs_fields={};live_vector_fields={};mfc_records=list(struct.iter_unpack('<32Q',native.data(f'sequence-{seq}/selected/mfc-allocation-witnesses.bin')));need(len(mfc_records)==58,'58 exact native allocation owners');header_predictions={};live_lockit_fields={};live_lockit_header_fields={};stem=f'sequence-{seq}/selected/';native_FS_frames=list(struct.iter_unpack('<32Q',native.data(stem+'fs-frame-witnesses.bin')));native_FS_raw=list(struct.iter_unpack('<16Q',native.data(stem+'fs-record-bytes.bin')));checkpoint_index={native.data(logical).decode():logical[:-9]for logical in native.entries if logical.startswith(stem+'registry-checkpoint-')and logical.endswith('-name.bin')};native_thread=struct.unpack('<8Q',native.data(stem+'lockit-resource.bin'))[6];need(native_thread>0,'Actual native current-thread identity');native_Lockit=next(r for r in native_Lockit_derivations if r['level']==level and r['sequence']==seq)['API_relations'];need(len(native_Lockit)==8,'All8 current actual native Lockit source API relations')
    for phase,item in enumerate(order):
     a=ori.data(f'phase/{seq}/{phase}.bin');b=native.data(f'sequence-{seq}/phase-{phase}.bin');entry=item['entry'];equal(a[:32],b[:32],'Exact original/native sequence association/status');need(words(a,32)[0]==1 and words(b,32)[0]in(0,1),'Declared original/native service activity tag')
     if entry in newroots:
      before_original=G.normalize_memory(a[2276:178404],0x1df20c);before_native={p:(b[2276+i*4096:2276+(i+1)*4096]if i<17 else native.data(f'sequence-{seq}/phase-{phase}-before-page-{p}.bin'))for i,p in enumerate(PAGES)};ha=H.derive(newroots[entry],words(a,36,10),before_original);hb=H.derive(newroots[entry],words(b,36,10),before_native);need([(r['field'],r['write_pc'])for r in ha]==[(r['field'],r['write_pc'])for r in hb],'Exact branch header source write identities');header_predictions={r['field']:(r['value'],n['value'],r,n)for r,n in zip(ha,hb)};need({(r['field'],r['write_pc'])for r in ha}=={(r['field'],r['write_pc'])for r in header_fields if r['root']==entry},'All and only36 physically/source-declared byte header fields')
     if entry==0x4d4830:
      prior=next(r for r in original_fs_headers if r['sequence']==seq);need(prior['provenance']['no_root_source_store_before_read'] and prior['read_address']==0x200017eb,'Frozen unchanged literal root saved byte is untouched before its reached MOV AL')
      current_original_FS_header=prior|dict(phase=phase,value=a[2276+PAGES.index(0x20001000)*4096+0x7eb],provenance=dict(kind='fresh_genuine_branch_BEFORE_stack_byte',address=0x200017eb,value=a[2276+PAGES.index(0x20001000)*4096+0x7eb],no_root_source_store_before_read=True))
     if entry in lockit_roots:
      fs=ori.data(f'phase/{seq}/{phase}/fs-events.bin');need(len(fs)==3648,'Actual three original normal FS observations')
      frame=next(f for f in native_FS_frames if f[2]==entry)
      for kind,point in((1,81),(2,84)):
       original_event=fs[kind*1216:(kind+1)*1216];ev=words(original_event,0,8);raw=original_event[112:124];w=words(raw,0,3);observed=next(r for r in native_FS_raw if r[2]==frame[1]and r[4]==point)
       need(ev[1]==observed[3]==entry and ev[2]==observed[5]and ev[6]==observed[6]==frame[9]and ev[7]and observed[7]==12,'Exact original/native normal FS source PC and complete12B frame identity')
       need(w[0]==words(fs,16)[0]and observed[8]==frame[8]and w[1:]==observed[9:11],'Whole observed12B record: own literal saved predecessor plus equal source handler/scope')
       new_FS_rows.append(dict(level=level,sequence=seq,phase=phase,root=entry,kind=kind,PC=ev[2],frame_address=ev[6],original_record_hex=raw.hex(),native_record_hex=struct.pack('<3I',*observed[8:11]).hex(),original_saved_predecessor=w[0],native_saved_predecessor=observed[8]));counts['Lockit_paired_complete12B_normal_FS_relations']+=1
      snapshots=ori.data(f'phase/{seq}/{phase}/lockit-snapshots.bin');need(len(snapshots)==6*12988,'Six genuine bounded original Lockit snapshots')
      rootordinal=sorted(lockit_roots).index(entry)
      for kind,index in((1,0),(4,1)):
       rel=native_Lockit[rootordinal*2+index];aentry=snapshots[kind*12988:(kind+1)*12988];areturned=snapshots[(kind+1)*12988:(kind+2)*12988];CPU_entry=words(aentry,64,10);CPU_returned=words(areturned,64,10)
       need(rel['source_PC']==(0x7810a30b if index==0 else 0x7810a35e)and CPU_entry[4]==rel['frame']and CPU_returned[4]==rel['frame']+8 and CPU_returned[9]==rel['return_pc'],'Genuine original actual APIentry/sourceAPIreturn vs independently derived exact native source CALL/stdcall frame')
       factname=stem+'locale-api-'+str(rel['API_index']);actualfact=struct.unpack('<32Q',native.data(factname+'-witness.bin'));equal(tuple(rel['actual_API_words']),actualfact,'Exact current native actual API witness retained')
       ninput=native.data(factname+'-input-0.bin');noutput=native.data(factname+'-output-0.bin');need(words(aentry,24)[0]==words(areturned,24)[0]==original_thread and words(aentry,688)[0]==(0 if index==0 else original_thread)and words(areturned,688)[0]==(original_thread if index==0 else 0),'Actual original CS24 owning thread is authenticated own current thread');need(words(ninput,12)[0]==(0 if index==0 else native_thread)and words(noutput,12)[0]==(native_thread if index==0 else 0),'Native semantic CS24 owning thread is authenticated own current thread');equal(noutput,bytes.fromhex(rel['derived_CS24_hex']),'Whole native semantic CS24 output from independently source-derived current-thread/depth relation')
       for offset in(0,4,8,16,20):equal(ninput[offset:offset+4],aentry[676+offset:680+offset],'Whole typed API CS24 input except own current-thread DWORD');equal(noutput[offset:offset+4],areturned[676+offset:680+offset],'Whole typed API CS24 returned state except own current-thread DWORD')
       nb=checkpoint_index['locale-api-'+str(rel['API_index'])+'-before'];na=checkpoint_index['locale-api-'+str(rel['API_index'])+'-after'];ncpu=native.data(nb+'-cpu.bin');equal(ncpu,native.data(na+'-cpu.bin'),'Actual native VOID API preserves full source CPU projection before derived RET');equal(native.data(nb+'-state.bin'),native.data(na+'-state.bin'),'Actual native VOID API preserves whole guest State before derived RET');equal(native.data(nb+'-fx.bin'),native.data(na+'-fx.bin'),'Actual native API preserves full guest FX before derived RET')
       API_rows.append(dict(level=level,sequence=seq,phase=phase,root=entry,kind=kind,actual_original_APIentry_CPU=list(CPU_entry),actual_original_sourceAPIreturn_CPU=list(CPU_returned),actual_original_FX512_sha256=hashlib.sha256(aentry[104:616]).hexdigest(),actual_original_ENV28_hex=aentry[616:644].hex(),actual_original_API_frame32_hex=aentry[644:676].hex(),actual_original_CS24_before_hex=aentry[676:700].hex(),actual_original_CS24_returned_hex=areturned[676:700].hex(),native_API_CPU_hex=ncpu.hex(),native_source_relation=rel,original_postRET_observed=False,native_postRET_API_observed=False));counts['Lockit_paired_bounded_API_semantic_relations']+=1
      source_rows=next(r['rows']for r in original_accesses if r['sequence']==seq and r['root']==entry)
      for field in lockit_fields:
       if field['root']!=entry or not any(r['level']==level and r['sequence']==seq and r['root']==entry and r['field']==field['address'] and r['write_pc']==field['pc']for r in native_header_rows):continue
       writes=[r for r in source_rows if r[0]==field['pc'] and r[1]==field['address'] and r[3:]==[1,1]];need(len(writes)==1,'One literal original branch field source write')
       native_field=next(r for r in native_header_rows if r['level']==level and r['sequence']==seq and r['root']==entry and r['field']==field['address'] and r['write_pc']==field['pc'])
       pair=(writes[0][2],native_field['value']);live_lockit_header_fields[field['address']]=(phase,pair)
       new_header_rows.append(dict(level=level,sequence=seq,phase=phase,root=entry,field=field['address'],original_source_write=writes[0],native_source_derivation=native_field));counts['Lockit_branch_field_source_derivations']+=2
      for binding in lockit_allocations:
       if binding['root']!=entry:continue
       original_owner=next(r for r in original_owners if r['sequence']==seq and r['binding']['root']==entry and r['binding']['CALL_pc']==binding['CALL_pc']);meta=original_owner['meta'];record=next(w for w in mfc_records if w[2]==entry and w[4]==binding['CALL_pc'])
       need(meta[4]==record[7]==binding['requested_size'] and meta[7] and meta[8]==record[19]==32 and record[16] and record[17] and record[18] and record[21]==record[23]==1 and not any(record[25:]),'Both positive actual Lockit owners and exactly one source publication')
       live_lockit_fields[binding['publication']]=(phase,(meta[7],record[16]));counts['Lockit_actual_owner_publication_activations']+=1
       original_initial=bytes.fromhex(original_owner['initial_hex']);original_expected=bytes.fromhex(original_owner['source_owned_hex']);need(len(original_initial)==len(original_expected)==32,'Complete genuine original32B backing')
       initial=native.data(f'sequence-{seq}/selected/locale-allocation-{record[18]}-initial.bin');need(len(initial)==32,'Complete genuine native32B backing');expected=bytearray(4096);expected[:32]=initial;predicted_original=bytearray(original_initial)
       writes=[r for r in original_owner_writes if r['sequence']==seq and r['owner_index']==meta[1]];need(len(writes)==4 and all(r['write']and r['bytes']==4 for r in writes),'Four literal DWORD stores in each private owner')
       for write in writes:
        value=write['source_value'];translated=value
        targets=[r for r in original_owners if r['sequence']==seq and r['meta'][7]==value]
        if targets:
         need(len(targets)==1,'Unique literal source pointer value');target=targets[0];translated=next(w[16]for w in mfc_records if w[2]==target['binding']['root']and w[4]==target['binding']['CALL_pc'])
        offset=write['owner_offset'];predicted_original[offset:offset+4]=struct.pack('<I',value);expected[offset:offset+4]=struct.pack('<I',translated);counts['Lockit_typed_owned_source_writes']+=1
       equal(bytes(predicted_original),original_expected,'Complete original32B exact source byteflow plus genuine initial padding')
       for suffix in ('selected','grown','cleaned'):
        equal(bytes(expected),native.data(f'sequence-{seq}/{suffix}/locale-allocation-{record[18]}-expected.bin'),'Complete native4096 source expected owner carry')
        if suffix!='cleaned':equal(bytes(expected),native.data(f'sequence-{seq}/{suffix}/locale-allocation-{record[18]}-owned-page.bin'),'Complete actual native4096 owned page carry')
        counts['Lockit_whole_native_owned_carries']+=1
       private_rows.append(dict(level=level,sequence=seq,phase=phase,root=entry,CALL_pc=binding['CALL_pc'],requested_size=binding['requested_size'],original_meta=meta,native_record=list(record),original_initial_hex=original_initial.hex(),original_expected_hex=original_expected.hex(),native_initial_hex=initial.hex(),native_expected_sha256=hashlib.sha256(expected).hexdigest(),source_writes=writes))
     observation=dict(level=level,sequence=seq,phase=phase,entry=entry,CPU_before_original_hex=a[36:76].hex(),CPU_before_native_hex=b[36:76].hex(),CPU_after_original_hex=a[76:116].hex(),CPU_after_native_hex=b[76:116].hex(),CPU_before_differences=delta(a[36:76],b[36:76]),CPU_after_differences=delta(a[76:116],b[76:116]),FX_before_differences=delta(a[116:628],b[116:628]),FX_after_differences=delta(a[628:1140],b[628:1140]),ENV_before_original_hex=a[2164:2192].hex(),ENV_before_native_hex=b[2164:2192].hex(),ENV_after_original_hex=a[2192:2220].hex(),ENV_after_native_hex=b[2192:2220].hex(),nonstack_pages=[])
     for side,co,fo,eo,mo,no in (('before',36,116,2164,2276,2276),('after',76,628,2192,178404,71908)):
      ca=words(a,co,10);cb=words(b,co,10)
      for index in (0,3,4,5,6,7,9):equal(ca[index],cb[index],'Exact EAX/nonvolatile/ESP/return-PC '+side);counts['exact_CPU_field_checks']+=1
      # ECX and flags are equal at every normal initializer return; retain
      # actual volatile outputs at SPI and its immediate caller input seam.
      spi_boundary=phase==(spi_phase if side=='after' else spi_phase+1)
      if not spi_boundary:
       equal(ca[1],cb[1],'ECX outside literal SPI volatile seam');equal(ca[8],cb[8],'EFLAGS outside literal SPI volatile seam');counts['additional_CPU_field_checks']+=2
      # Physical MXCSR_MASK is a CPU capability descriptor. It is imported
      # only by hardwarefx under the frozen accepted numeric policy.
      equal(m.hardwarefx(b[fo:fo+512]),a[fo:fo+512],'Whole hardware FX projection: CW/TOP/status/raw80/SIMD');counts['whole_hardware_FX_projection_checks']+=1
      equal(a[eo:eo+12],b[eo:eo+12],'Exact x87 control/status/tag and reserved words');counts['exact_x87_environment_head_checks']+=1
      metadata_boundary=phase in(range(spi_phase,nextfp)if side=='after' else range(spi_phase+1,nextfp+1))
      if not metadata_boundary:equal(a[eo:eo+28],b[eo:eo+28],'Exact complete ENV outside finite SPI metadata interval');counts['whole_ENV_checks']+=1
      for i,page in enumerate(PAGES):
       original=a[mo+i*4096:mo+(i+1)*4096];actual=b[no+i*4096:no+(i+1)*4096]if i<17 else native.data(f'sequence-{seq}/phase-{phase}-{side}-page-{page}.bin')
       if page==0x20001000:continue
       if page==0x5f4cc000:
        equal(original,loaded_page,'Every original initialized loader-page byte carries from same-worker bootstrap');equal(actual,bytes(raw_page),'Every native raw loader-page byte carries from physical PE input');equal(delta(original,actual),loader_differences,'Entire explicit own-process loaded/raw input-page difference list stays constant');loader_rows.append(dict(level=level,sequence=seq,phase=phase,side=side,page=page,original_sha256=hashlib.sha256(original).hexdigest(),native_sha256=hashlib.sha256(actual).hexdigest()));counts['separate_whole_loader_page_input_relations']+=1;continue
       differences=delta(original,actual);declared=set()
       for span in observer_spans:
        if span['PC']&~4095!=page:continue
        off=span['PC']&4095;n=span['width'];equal(original[off:off+n],bytes.fromhex(span['original_hex']),'Exact source-bound original compiled transparent observer JMP/padding');equal(actual[off:off+n],bytes.fromhex(span['native_hex']),'Native keeps exact physical literal FS MOV bytes');declared.update(range(off,off+n));counts['exact_observer_span_relations']+=1
       if page==0x7810a000:
        for span in lockit_patches:
         off=span['PC']&4095;n=span['width'];equal(original[off:off+n],bytes.fromhex(span['original_hex']),'Exact actual linked original Lockit observer code');equal(actual[off:off+n],bytes.fromhex(span['source_hex']),'Exact native source DLL Lockit instruction span');declared.update(range(off,off+n));counts['Lockit_compiled_observer_span_relations']+=1
       if page==0x78146000:
        equal(actual,loaded_cp_IAT,'Whole native provider IAT authentic loaded input page')
        for slot in(0x78146198,0x78146184):
         off=slot&4095;target=words(original,off)[0];need(target==original_API_shim_targets[slot] and words(actual,off)[0]==lockit_API_imports[slot],'Only exact actual original API shim versus authenticated named loaded target');declared.update(range(off,off+4));counts['Lockit_loaded_API_IAT_relations']+=1
       if page==0x78145000:
        equal(original,loaded_cp_RW,'Whole original balanced root checkpoint restores genuine loaded CS24/page');equal(actual,loaded_cp_RW,'Whole native balanced root checkpoint preserves identical genuine loaded opaque page input');counts['Lockit_whole_loaded_RW_page_relations']+=1
       if page in(0x7810a000,0x78145000,0x78146000):provider_page_rows.append(dict(level=level,sequence=seq,phase=phase,side=side,page=page,original_sha256=hashlib.sha256(original).hexdigest(),native_sha256=hashlib.sha256(actual).hexdigest(),exact_declared_difference_offsets=sorted(declared)))
       for address,(activation,pair)in live_lockit_fields.items():
        if address&~4095==page and(phase>activation or side=='after'):
         off=address&4095;equal(words(original,off)[0],pair[0],'Exact original new private owner publication carry');equal(words(actual,off)[0],pair[1],'Exact native new private owner publication carry');declared.update(range(off,off+4));counts['Lockit_typed_owner_publication_carries']+=1
       for address,(activation,pair)in live_lockit_header_fields.items():
        if address&~4095==page and(phase>activation or side=='after'):
         off=address&4095;equal(original[off],pair[0],'Exact original literal own-branch local byte carry');equal(actual[off],pair[1],'Exact native literal own-branch local byte carry');declared.add(off);counts['Lockit_branch_byte_carries']+=2
       if page==0x5bb000:
        for address,(target,raw)in IATS.items():
         off=address&4095;need(words(actual,off)[0]==raw,'Pinned native raw owning-IAT identity');need(target is None or words(original,off)[0]==target,'Actual32 owning-IAT target')
         if target is None:need(words(original,off)[0]!=raw and words(original,off)[0]!=0,'Actual32 SPI worker shim target')
         declared.update(range(off,off+4));counts['owning_IAT_identity_checks']+=1
       if page==0x5f498000:
        for address,raw,target in MFC_IMPORTS:
         off=address&4095;equal(words(original,off)[0],target,'Original actual own-process named/ordinal import target');equal(words(actual,off)[0],raw,'Native exact physical raw import DWORD');declared.update(range(off,off+4));counts['exact_MFC_import_relations']+=1
       if entry in newroots and side=='after':
        for mi,binding in enumerate(bindings):
         if binding['root']!=entry or binding['publication']&~4095!=page:continue
         address=binding['publication'];meta=words(ori.data(f'phase/{seq}/{phase}/mfc/{mi}/meta.bin'),0,8);record=next(w for w in mfc_records if w[2]==entry and w[4]==binding['CALL_pc']);need(record[7]==binding['requested_size']and record[16]and record[17]and record[18]and record[19]==((binding['requested_size']+15)&~15)and record[21]==1 and record[23]==1 and not any(record[25:]),'Actual returned live native MFC allocator and one publication');need(meta[:5]==tuple(binding[k]for k in('root','CALL_pc','requested_size','object','publication'))and meta[5]and meta[6]>=binding['requested_size']and meta[7]==mi,'Exact original MFC source owner/publication association');live_mfc_fields[address]=(meta[5],record[16]);counts['source_MFC_owner_relations']+=1
         source=next(r for r in geometry['allocations']if r['root']==entry and r['CALL_pc']==binding['CALL_pc']);api=ori.data(f'phase/{seq}/{phase}/api-ledger.bin');apirows=list(struct.iter_unpack('<26I',api));ai=next(i for i,r in enumerate(apirows)if r[24]==0 and r[10]==meta[5]);initial=ori.data(f'phase/{seq}/{phase}/api-initial/{ai}/bytes.bin');predicted_original=bytearray(initial);native_initial=native.data(f'sequence-{seq}/selected/locale-allocation-{record[18]}-initial.bin');need(len(native_initial)==record[19]and len(initial)==meta[6],'Both genuine initial full API backing extents');predicted_native=bytearray(4096);predicted_native[:len(native_initial)]=native_initial
         for write in source['owned_source_writes']:
          off=write['address']-source['declared_pointer'];n=write['bytes'];value=write['value'];self_reference=source['declared_pointer']<=value<source['declared_pointer']+source['rounded_extent'];av=meta[5]+value-source['declared_pointer']if self_reference else value;bv=record[16]+value-source['declared_pointer']if self_reference else value;predicted_original[off:off+n]=av.to_bytes(n,'little');predicted_native[off:off+n]=bv.to_bytes(n,'little');counts['typed_MFC_owned_source_writes']+=1
         equal(bytes(predicted_original),ori.data(f'phase/{seq}/{phase}/mfc/{mi}/bytes.bin'),'Complete genuine original owned bytes from actual initial API BEFORE + exact source node writes');equal(bytes(predicted_native),native.data(f'sequence-{seq}/selected/locale-allocation-{record[18]}-expected.bin'),'Complete native4096 owned expected backing from actual initial API BEFORE + exact source node writes');equal(bytes(predicted_native),native.data(f'sequence-{seq}/selected/locale-allocation-{record[18]}-owned-page.bin'),'Complete actual native mapped4096 guest-owned page');counts['whole_original_and_native_MFC_owned_relations']+=1
        for address,prediction in header_predictions.items():
         if address&~4095!=page:continue
         off=address&4095;av,bv,ar,br=prediction;equal(original[off],av,'Every original header from literal source own-branch BEFORE saved byte');equal(actual[off],bv,'Every native header from literal source own-branch BEFORE saved byte');live_header_fields[address]=(av,bv);field_rows.append(dict(level=level,sequence=seq,address=address,original_source=ar,native_source=br));counts['new_header_branch_derivations']+=2
       if entry in newroots and side=='after':
        for field in pointer_fields:
         address=field['field']
         if field['root']!=entry or address&~4095!=page or field['pointer_offset']==0:continue
         meta=words(ori.data(f'phase/{seq}/{phase}/mfc/{bindings.index(next(v for v in bindings if v["root"]==entry and v["CALL_pc"]==field["CALL_pc"]))}/meta.bin'),0,8);record=next(w for w in mfc_records if w[2]==entry and w[4]==field['CALL_pc']);need(field['pointer_offset']==field['requested_size']==record[7]and field['is_one_past_end'],'Exact literal bounded vector one-past-end source relation');pair=(meta[5]+field['pointer_offset'],record[16]+field['pointer_offset']);live_mfc_fields[address]=pair;counts['source_MFC_one_past_end_relations']+=1
       if side=='after':
        for fi,binding in enumerate(fsbindings):
         address=binding['publication']
         if binding['root']!=entry or not address or address&~4095!=page:continue
         meta=words(ori.data(f'phase/{seq}/{phase}/fs-allocation/{fi}/meta.bin'),0,9);record=next(w for w in mfc_records if w[2]==entry and w[4]==binding['CALL_pc']);need(meta[:5]==(1,fi,entry,binding['CALL_pc'],binding['requested_size'])and meta[7]and meta[8]>=binding['requested_size'],'Original dynamic FS source allocation join');need(record[7]==binding['requested_size']and record[21]and record[16]and record[17]and record[18],'Native dynamic FS source allocation join');live_fs_fields[address]=(meta[7],record[16]);counts['new_FS_static_publication_relations']+=1
        if entry==0x4d4830 and page==0x60b000:
         ar=current_original_FS_header;br=next(r for r in native_fs_headers if r['sequence']==seq and r['level']==level);need(ar['field']==br['field']==0x60b51c and ar['write_pc']==br['write_pc']==0x4d4922 and ar['read_pc']==br['read_pc']==0x4d4914 and ar['read_address']==br['read_address']==0x200017eb,'Exact new literal saved-byte field/source PC/address');equal(original[0x51c],ar['value'],'Exact original header from genuine own BEFORE stack byte');equal(actual[0x51c],br['value'],'Exact native header from persistent source own BEFORE stack byte');live_header_fields[0x60b51c]=(ar['value'],br['value']);field_rows.append(dict(level=level,sequence=seq,address=0x60b51c,original_source=ar,native_source=br,new_FS_local_byte_relation=True));counts['new_FS_header_branch_derivations']+=2
       if side=='after':
        for vi,item in enumerate(vectorinputs):
         if item['root']!=entry:continue
         meta=words(ori.data(f'phase/{seq}/{phase}/container-allocation/{vi}/meta.bin'),0,9);record=next(w for w in mfc_records if w[2]==entry and w[4]==item['CALL_pc']);need(meta[:5]==(1,vi,entry,item['CALL_pc'],item['requested_size'])and record[7]==item['requested_size']and record[21],'Both actual positive vector owners match source root/CALL/request');
         for address,PC,offset in [(item['publication'],item['publication_PC'],0),(item['end_address'],item['end_PC'],0),(item['capacity_address'],item['capacity_PC'],item['requested_size'])]+[(r['address'],r['PC'],r['offset'])for r in item['additional_empty_pointer_fields']]:
          if address&~4095!=page:continue
          need(address not in live_vector_fields,'One source store activation per new vector field');live_vector_fields[address]=(meta[7]+offset,record[16]+offset);counts['new_vector_typed_field_activations']+=1
       for address,pair in live_vector_fields.items():
        if address&~4095==page:
         off=address&4095;equal(words(original,off)[0],pair[0],'Literal original vector field own pointer/one-past-end');equal(words(actual,off)[0],pair[1],'Literal native vector field own alias/one-past-end');declared.update(range(off,off+4));counts['new_vector_typed_field_carries']+=1
       for address,pair in live_fs_fields.items():
        if address&~4095==page:
         off=address&4095;equal(words(original,off)[0],pair[0],'Original carried shared/private FS static publication');equal(words(actual,off)[0],pair[1],'Native carried shared/private FS static publication');declared.update(range(off,off+4));counts['new_FS_static_publication_carries']+=1
       for address,pair in live_mfc_fields.items():
        if address&~4095==page:
         off=address&4095;equal(words(original,off)[0],pair[0],'Original source-established live MFC publication');equal(words(actual,off)[0],pair[1],'Native source-established live MFC publication');declared.update(range(off,off+4));counts['live_MFC_field_relation_checks']+=1
       for address,pair in live_header_fields.items():
        if address&~4095==page:
         off=address&4095;equal(original[off],pair[0],'Exact original derived header carry');equal(actual[off],pair[1],'Exact native derived header carry');declared.add(off);counts['new_header_carry_checks']+=2
       for address,pair in live_string_fields.items():
        if address&~4095==page:
         off=address&4095;equal(words(original,off)[0],pair[0],'Original source-established live duplicate field');equal(words(actual,off)[0],pair[1],'Native source-established live duplicate field');declared.update(range(off,off+4));counts['live_duplicate_field_relation_checks']+=1
       if entry in stringrows and side=='after':
        binding=stringrows[entry];obj=binding['objects'][0]['address'];address=obj+(0 if entry==0x4e6a10 else 4)
        if address&~4095==page:
         off=address&4095
         if entry==0x4e6a10:equal(words(original,off)[0],0,'Exact original null constructor');equal(words(actual,off)[0],0,'Exact native null constructor');counts['null_descriptor_relations']+=1
         else:
          meta=words(ori.data(f'phase/{seq}/{phase}/strings/{entry}/meta.bin'),0,6);prefix=f'sequence-{seq}/selected/';witness=native.data(prefix+'strings-witnesses.bin');wrows=list(struct.iter_unpack('<32Q',witness));record=next(w for w in wrows if w[2]==entry);need(record[4]==binding['string']['source'] and record[7]==binding['string']['size'] and record[17]==1 and record[28],'Exact native returned live strdup owner')
          equal(words(original,off)[0],meta[3],'Actual original typed allocation identity');equal(words(actual,off)[0],record[10],'Actual native typed allocation alias');raw=bytes.fromhex(binding['string']['bytes_hex']);equal(ori.data(f'phase/{seq}/{phase}/strings/{entry}/bytes.bin')[:len(raw)],raw,'Original literal complete duplicate bytes');equal(native.data(prefix+f'string-{record[1]}-input.bin'),raw,'Native actual NULinclusive input witness');live_string_fields[address]=(meta[3],record[10]);declared.update(range(off,off+4));counts['source_string_owner_relations']+=1
       if page==0x609000:
        field=0x9e8
        if phase==oldheader_phase:
         if side=='before':
          values={'original_before':original[field],'native_before':actual[field],'original_derived':(words(a,36,10)[1]>>24)&255,'native_derived':(words(b,36,10)[1]>>24)&255}
         else:
          equal(original[field],values['original_derived'],'Literal original PUSH ECX/local highbyte derivation');equal(actual[field],values['native_derived'],'Literal native PUSH ECX/local highbyte derivation')
          field_rows.append(dict(level=level,sequence=seq,address=0x6099e8,write_PC=0x49d5d5,constructor_before_ECX_original=words(a,36,10)[1],constructor_before_ECX_native=words(b,36,10)[1],original_after=original[field],native_after=actual[field],**values));counts['own_branch_field_derivations']+=2
        if phase>oldheader_phase or(phase==oldheader_phase and side=='after'):
         equal(original[field],values['original_derived'],'Original indeterminate field carries');equal(actual[field],values['native_derived'],'Native indeterminate field carries');declared.add(field);counts['indeterminate_field_carry_checks']+=2
       need(all(x['offset']in declared for x in differences),'No undeclared paired byte difference '+str((level,seq,phase,side,hex(page),differences[:10])))
       # Preserve physical observations including exact raw unequal bytes.
       observation['nonstack_pages'].append(dict(side=side,page=page,original_sha256=hashlib.sha256(original).hexdigest(),native_sha256=hashlib.sha256(actual).hexdigest(),differences=differences));counts['whole_nonstack_page_relations']+=1
     if entry in roots:
      callback=roots[entry];expected_callbacks.append(callback);need(words(a,76)[0]==0 and words(b,76)[0]==0,'Exact original/native atexit wrapper success return')
      # Successful realloc resets the cached HeapSize capacity to0. The
      # exact committed rounded owner extent is proven by persistent source
      # and provider ownership gates, and capacity becomes known on next msize.
      registry=native.data(f'sequence-{seq}/phase-{phase}-after-registry.bin');summary=struct.unpack('<32Q',registry);need(summary[9]==len(expected_callbacks) and summary[7]-summary[6]==4*len(expected_callbacks) and (summary[8]>=4*len(expected_callbacks)or(summary[8]==0 and summary[14]>0)),'Native actual owned registry extent/count; exact contents proven by persistent source gate')
      need(words(a,356480,len(expected_callbacks))==tuple(expected_callbacks),'Original carried callback vector');counts['registration_return_order_checks']+=1
     rows.append(observation);counts['paired_phases']+=1
     if phase==len(order)-1:print(json.dumps(dict(progress='paired124 sequence complete',level=level,sequence=seq)),flush=True)
    equal(ori.data(f'cleanup/{seq}/registry.bin'),struct.pack('<96I',*expected_callbacks),'Exact original complete callback vector');counts['paired124_sequences']+=1
   native.close();del native
  ori.close()
  for module in (J,m):
   for p,h in getattr(module,'PINS',{}).items():pin(p,h if isinstance(h,str)else h['sha256'])
  # Keep the41 ordinary-page counter distinct from the separately related
  # complete loader page; both relations contribute to42 nonstack coverage.
  counts['whole42_nonstack_page_endpoint_relations']=counts['whole_nonstack_page_relations']+counts['separate_whole_loader_page_input_relations']
  need(counts['paired_phases']==1488 and counts['paired124_sequences']==12 and counts['whole_nonstack_page_relations']==122016 and counts['separate_whole_loader_page_input_relations']==2976 and counts['whole42_nonstack_page_endpoint_relations']==124992 and counts['Lockit_paired_complete12B_normal_FS_relations']==96 and counts['Lockit_paired_bounded_API_semantic_relations']==96 and counts['Lockit_actual_owner_publication_activations']==96 and counts['Lockit_branch_field_source_derivations']==216 and counts['Lockit_whole_native_owned_carries']==288 and len(provider_page_rows)==8928,'Complete full124 paired coverage and allnewroot bounded contracts')
  pin(__file__);passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  for label,value in (('Lockit-paired-normal-FS.json',new_FS_rows),('Lockit-paired-API-observations.json',API_rows),('Lockit-private-owners.json',private_rows),('Lockit-branch-byte-relations.json',new_header_rows),('Lockit-provider-page-relations.json',provider_page_rows),('observer-span-relations.json',observer_spans),('paired-observations.json',rows),('indeterminate-field.json',field_rows),('loader-page-input-relation.json',dict(page=0x5f4cc000,original_bootstrap_sha256=hashlib.sha256(loaded_page).hexdigest(),native_raw_sha256=hashlib.sha256(raw_page).hexdigest(),own_process_complete_4096_differences=loader_differences,observations=loader_rows,exact_reached_DWORD=0x5f4cecec,ordinary_page_mask=False,ordinary_page_relation=False))):
   (out/label).write_text(json.dumps(value,indent=2)+'\n');pin(out/label)
  report=dict(passed=passed,scope='Fresh whole selected124 paired initialization relation: all43 page coverage via42 nonstack whole-page paired relations plus separately proven complete source stack, complete callback order/numeric state and finite typed provider seams; eight new private owners from genuine branch initial backings' ,counts=dict(counts),native_source_report_sha256=native_source_sha,new_original_source_report_sha256='48f184d6edbaae5e1ec9d384f743089210e65dea9655822a4f517b41fa3b757b',Lockit_original_postRET_observed=False,Lockit_original_ctor_APIreturn_scope='Actual7810A311 before MOV EAX,EDI/POP EDI/POP ESI/RET; postRET is independently source-derived',Lockit_original_dtor_APIreturn_scope='Actual7810A364 literal preRET; postRET is independently source-derived',Lockit_private_requested_sizes=[r['requested_size']for r in lockit_allocations],Lockit_whole_private_initial_backings=32,Lockit_native_whole_mapped_backings=4096,Lockit_opaque_loaded_bytes_masked=False,Lockit_exact_original_API_observer_targets=original_API_shim_targets,Lockit_independent_original_compiled_observer_gate_sha256='570bc3dc54aadcb7b67abccb06182c7177eeb7d059bb31ea5caf40f57625659f',paired_initialization_data_contract=passed,original_record_bytes=356992,native_record_bytes=159716,original_and_native_bytes_modified=False,blanket_page_mask=False,owning_IAT_projection_addresses=list(IATS),observed_original_observer_spans=observer_spans,indeterminate_relation_address=0x6099e8,new_MFC_source_header_relations=True,new_FS_source_publication_fields=[r['publication']for r in fsbindings if r['publication']],new_FS_header_relation_address=0x60b51c,new_FS_header_relation_scope='Exact own-branch literal local-byte read/write and carry, from genuine original BEFORE stack or persistent native source BEFORE stack. Raw values retained; whole-game liveness not claimed.',own_branch_header_input='Exact genuine branch BEFORE CPU/pages only; literal saved stack-byte provenance with last dominating source store; declared positive allocation facts establish normal path without any candidate AFTER byte',MFC_import_relation_slots=511,MFC_typed_pointer_fields=[r['field']for r in pointer_fields],MFC_one_past_end_fields=[r['field']for r in pointer_fields if r['is_one_past_end']],MFC_header_fields=[r['field']for r in header_fields],MFC_private_padding_relation='Each branch retains its own actual pre-guest-write API allocation backing; source-owned initialized nodes compared by separate full original/native ownership gates. No cross-branch arbitrary heap padding equality is claimed.',indeterminate_relation='Each branch literal PUSH ECX/MOV AL,[ESP+3] highbyte independently derived from its genuine constructor BEFORE; raw values retained and exact carry checked. Known selected suffix and recovered UI/container/cleanup consumers do not read byte0; whole-game dynamic aliases are excluded.',crossbranch_CPU_contract='EAX, nonvolatile GPRs, ESP, returnPC exact at every phase. ECX/EFLAGS exact outside one finite SPI return/immediate input seam. EDX and real32 API volatile outputs retained as observed typed boundary state; strict native full CPU/State separately modeled, no whole original API volatile equality claimed.',crossbranch_numeric_contract='Frozen hardwarefx capability-mask projection only; exact CW/TOP/status/raw80/SIMD all phases. Exact ENV head throughout; actual SPI FIP/FOP/FDP metadata retained on finite the measured source/table-derived interval until next original/literal source FP overwrites it. Exact complete ENV otherwise.',original_provider_scratch_stack_crossbranch_equal=False,native_full_stack_source_proven=True,whole_game_liveness_proven=False,FSQRT_scope='Exact measured default-zero constructor inputs in six CW/TOP cases; broader nonzero/denormal Remill behavior excluded.',initializers_added_by_this_report=0,whole_M4_complete=False,files=PINS)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=PINS),indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4])


