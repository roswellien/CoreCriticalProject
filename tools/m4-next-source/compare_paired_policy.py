"""Bounded paired original/native120 initialization data and numeric contract.

Every branch retains its genuine bytes. Exact typed IAT identities and one
source-derived indeterminate representation byte are relations, not edits.
Real32 provider/API volatile registers and scratch-stack contents are retained
as observations; strict native source State/stack proof is a separate gate.
"""
from pathlib import Path
import collections, hashlib, importlib.util, json, struct, sys, traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PINS={}
PAGES=(0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000,0x5ca000,0x5ed000,0x5f4000,0x603000,0x606000,0x609000,0x638000,0x63c000,0x63d000,0x72c000,0x730000,0x9a1000,0x5e4000,0x5e5000,0x5e7000,0x72b000,0x731000,0x5f498000,0x736000,0x5f4cc000,0x5bc000,0x5cf000,0x5fc000)
IATS={0x5bb4fc:(0x780c10f0,0x1df59c),0x5bb52c:(0x78004a36,0x1decb0),0x5bb530:(0x78002fe5,0x1deca2),0x5bb6dc:(None,0x1df20c),0x5bb670:(0x78010a6d,0x1df886),0x5bb4bc:(0x5f401ea0,0x80000337),0x5bb454:(0x5f4020b4,0x8000021c),0x5bb4c8:(0x5f401782,0x80000339)}
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
def main(native_report,name):
 out=ROOT/'reports/m4-next-source'/name;need(not out.exists(),'Fresh paired policy');out.mkdir(parents=True);passed=False;counts=collections.Counter();rows=[];field_rows=[]
 try:
  original_report=json.loads(pin(ROOT/'reports/m4-vtable-original/validation-r1/report.json').read_bytes());need(original_report['passed'],'Corrected actual original run')
  need(json.loads(pin(ROOT/'reports/m4-next-source/original-game-source-r1/report.json').read_bytes())['passed'],'Literal original120constructor/string source gate')
  need(json.loads(pin(ROOT/'reports/m4-next-source/connected-native-source-r1/report.json').read_bytes())['passed'],'Strict persistent native120 source gate')
  nr=pin(native_report);need(json.loads(nr.read_bytes())['passed'],'Current native120 run')
  D=load('paired_direct',ROOT/'tools/m4-crt-allocation-root/run_v2.py');J=load('paired_old_numeric',ROOT/'tools/m4-joint-startup27-review/observe.py');m,_,_,_=J.models();G=load('paired_original_source',ROOT/'tools/m4-mfc-source/compare_original_game.py');G.PINS=PINS
  rootrows=json.loads(pin(ROOT/'reports/m4-onexit-batch-recovery/recovery-r3/registration-roots.json','88979fcc7494e8ada7821bc4b2f804f7194ca43f3265621b86a50fb32ffe84fc').read_bytes())+json.loads(pin(ROOT/'reports/m4-strings-source/recovery-r7/string-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-mfc-source/recovery-r4/mfc-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-fs-source/recovery-r3/fs-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-container-source/recovery-r3/container-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-next-source/recovery-r1/fixed-roots.json').read_bytes());
  for item in json.loads(pin(ROOT/'reports/m4-container-source/allocation-interface-r1/string-inputs.json').read_bytes()):next(r for r in rootrows if r['entry']==item['root'])['string']=item
  roots={r['entry']:r['registration']['callback']for r in rootrows};stringrows={r['entry']:r for r in rootrows if 'string'in r}
  order=json.loads(pin(ROOT/'reports/m4-next-source/recovery-r1/instruction-contracts.json').read_bytes())['selected_order'];ori=D.DirectSet(Path(original_report['original_capture']),pin);MFC_IMPORTS=[tuple(v[:3])for v in struct.iter_unpack('<7I',ori.data('mfc-import-ledger.bin'))];G.MFC_IMPORTS=MFC_IMPORTS;H=load('mfc_header_source_relations',ROOT/'tools/m4-mfc-source/header_relations_v2.py');newroots={r['entry']:r for r in rootrows if r['entry']in{r['entry']for r in json.loads(pin(ROOT/'reports/m4-mfc-source/recovery-r4/mfc-roots.json').read_bytes())}};field_contract=json.loads(pin(ROOT/'reports/m4-mfc-source/field-contracts-r1/report.json','63cd8d2665580dc397745d0f34769dac321089fa2ec422eeea7681b08e3a1a55').read_bytes());pointer_fields=field_contract['pointer_fields'];header_fields=field_contract['header_fields'];geometry=json.loads(pin(ROOT/'reports/m4-mfc-source/allocation-contracts-r4/report.json','30ef9954b16ba185294871d5cb419df502b656aab7f12fc521a4e3b09fe156f2').read_bytes());bindings=json.loads(pin(ROOT/'reports/m4-mfc-source/allocation-contracts-r4/allocation-inputs.json',geometry['allocation_inputs_sha256']).read_bytes());spi_phase=next(i for i,r in enumerate(order)if r['entry']==0x482cf0);oldheader_phase=next(i for i,r in enumerate(order)if r['entry']==0x4c58c0);graphs=json.loads(pin(ROOT/'reports/m4-service-initializers/static-r1/game-all-initializer-graphs.json').read_bytes());nextfp=next(i for i,r in enumerate(order)if i>spi_phase and graphs[str(r['entry'])]['FP_sites']);need(len(MFC_IMPORTS)==511,'All physical/authenticated original MFC import slots')
  fsbindings=json.loads(pin(ROOT/'reports/m4-fs-source/allocation-interface-r1/allocation-inputs.json','a3fb27e6f16c12bbc7499c912415b2c294d74e97c7600dbaeb3be4770ab492ff').read_bytes());original_fs_headers=json.loads(pin(ROOT/'reports/m4-next-source/original-game-source-r1/new-header-derivations.json').read_bytes());native_fs_headers=json.loads(pin(ROOT/'reports/m4-next-source/connected-native-source-r1/new-header-derivations.json').read_bytes());vectorinputs=json.loads(pin(ROOT/'reports/m4-container-source/allocation-interface-r1/vector-endpoints.json').read_bytes());loaded_page=ori.data('mfc540-loaded-page.bin');raw_page=bytearray(4096)
  PE=load('paired_container_PE',ROOT/'tools/analysis/pe.py');mfc=PE.PEImage(ori.data('mfc-image.bin'));raw_page=bytearray(4096)
  for sec in mfc.sections:
   lo=max(0x5f4cc000,mfc.image_base+sec['virtual_address']);hi=min(0x5f4cd000,mfc.image_base+sec['virtual_address']+sec['raw_size'])
   if hi>lo:off=sec['raw_offset']+lo-mfc.image_base-sec['virtual_address'];raw_page[lo-0x5f4cc000:hi-0x5f4cc000]=mfc.data[off:off+hi-lo]
  loader_rows=[];loader_differences=delta(loaded_page,raw_page);observer_spans=[]
  observer_gate=json.loads(pin(ROOT/'reports/m4-vtable-original/observer-compiled-r1/report.json').read_bytes());need(observer_gate['passed'],'Compiled transparent FS original observer');build=json.loads(pin(ROOT/'reports/m4-vtable-original/build-r1/build.json').read_bytes());execution=json.loads(pin(ROOT/'reports/m4-vtable-original/execution-r1/report.json').read_bytes());worker_path=ROOT/'reports/m4-vtable-original/build-r1/original-worker.exe';worker_bytes=pin(worker_path,execution['files'][str(worker_path.resolve())]).read_bytes();worker=PE.PEImage(worker_bytes);need(worker.image_base==0x18000000,'Actual original fixed declared worker base');observer_spans=[]
  for hook in json.loads(pin(ROOT/'reports/m4-vtable-original/preparation-r1/fs-hook-bindings.json').read_bytes()):
   pc=hook['PC'];raw=bytes.fromhex(hook['raw_bytes'])
   if pc&~4095 not in PAGES:continue
   key=struct.pack('<3I',pc,len(raw),hook['kind']);matches=[i for i in range(len(worker_bytes))if worker_bytes.startswith(key,i)and worker_bytes[i+16:i+16+len(raw)]==raw];need(len(matches)==1,'One physical linked FsHook initializer for observed source span');target=words(worker_bytes,matches[0]+12)[0];toff,_=worker.rva_range(target-worker.image_base,1);need(worker_bytes[toff:toff+2]==bytes.fromhex('c705')and words(worker_bytes,toff+6)[0]==hook['kind']and worker_bytes[toff+10]==0xa3,'Actual compiled trampoline begins declaring exact event direction and saving EAX; full ESP-before-push checked by pinned compiled observer gate');original_bytes=b'\xe9'+struct.pack('<I',(target-pc-5)&0xffffffff)+b'\x90'*(len(raw)-5);observer_spans.append(dict(PC=pc,width=len(raw),original_hex=original_bytes.hex(),native_hex=raw.hex(),compiled_target=target,compiled_table_offset=matches[0],declared_symbol=hook['declared_observer']))
  need(sorted((r['PC'],r['width'])for r in observer_spans)==[(0x4824a7,6),(0x4824ae,7),(0x4824ed,7),(0x482b47,6),(0x482b4e,7),(0x482b8e,7)],'Only six exact observed-page original observer spans')
  loader_rows=[];loader_differences=delta(loaded_page,raw_page);need(len(loaded_page)==4096 and words(loaded_page,0xb54)[0]==words(raw_page,0xb54)[0]==0x5f4cecec,'Same-worker loaded/raw page exact borrowed source DWORD')
  for level in ('O0','O2'):
   native=D.DirectSet(nr.parent/level/'transport.json',pin)
   for seq in range(6):
    expected_callbacks=[];values={};live_string_fields={};live_mfc_fields={};live_header_fields={};live_fs_fields={};live_vector_fields={};mfc_records=list(struct.iter_unpack('<32Q',native.data(f'sequence-{seq}/selected/mfc-allocation-witnesses.bin')));need(len(mfc_records)==50,'50 exact native allocation owners');header_predictions={}
    for phase,item in enumerate(order):
     a=ori.data(f'phase/{seq}/{phase}.bin');b=native.data(f'sequence-{seq}/phase-{phase}.bin');entry=item['entry'];equal(a[:32],b[:32],'Exact original/native sequence association/status');need(words(a,32)[0]==1 and words(b,32)[0]in(0,1),'Declared original/native service activity tag')
     if entry in newroots:
      before_original=G.normalize_memory(a[2276:166120],0x1df20c);before_native={p:(b[2276+i*4096:2276+(i+1)*4096]if i<17 else native.data(f'sequence-{seq}/phase-{phase}-before-page-{p}.bin'))for i,p in enumerate(PAGES)};ha=H.derive(newroots[entry],words(a,36,10),before_original);hb=H.derive(newroots[entry],words(b,36,10),before_native);need([(r['field'],r['write_pc'])for r in ha]==[(r['field'],r['write_pc'])for r in hb],'Exact branch header source write identities');header_predictions={r['field']:(r['value'],n['value'],r,n)for r,n in zip(ha,hb)};need({(r['field'],r['write_pc'])for r in ha}=={(r['field'],r['write_pc'])for r in header_fields if r['root']==entry},'All and only36 physically/source-declared byte header fields')
     observation=dict(level=level,sequence=seq,phase=phase,entry=entry,CPU_before_original_hex=a[36:76].hex(),CPU_before_native_hex=b[36:76].hex(),CPU_after_original_hex=a[76:120].hex(),CPU_after_native_hex=b[76:120].hex(),CPU_before_differences=delta(a[36:76],b[36:76]),CPU_after_differences=delta(a[76:120],b[76:120]),FX_before_differences=delta(a[120:628],b[120:628]),FX_after_differences=delta(a[628:1140],b[628:1140]),ENV_before_original_hex=a[2164:2192].hex(),ENV_before_native_hex=b[2164:2192].hex(),ENV_after_original_hex=a[2192:2220].hex(),ENV_after_native_hex=b[2192:2220].hex(),nonstack_pages=[])
     for side,co,fo,eo,mo,no in (('before',36,120,2164,2276,2276),('after',76,628,2192,166120,71908)):
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
         ar=next(r for r in original_fs_headers if r['sequence']==seq);br=next(r for r in native_fs_headers if r['sequence']==seq and r['level']==level);need(ar['field']==br['field']==0x60b51c and ar['write_pc']==br['write_pc']==0x4d4922 and ar['read_pc']==br['read_pc']==0x4d4914 and ar['read_address']==br['read_address']==0x200017eb,'Exact new literal saved-byte field/source PC/address');equal(original[0x51c],ar['value'],'Exact original header from genuine own BEFORE stack byte');equal(actual[0x51c],br['value'],'Exact native header from persistent source own BEFORE stack byte');live_header_fields[0x60b51c]=(ar['value'],br['value']);field_rows.append(dict(level=level,sequence=seq,address=0x60b51c,original_source=ar,native_source=br,new_FS_local_byte_relation=True));counts['new_FS_header_branch_derivations']+=2
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
      need(words(a,307328,len(expected_callbacks))==tuple(expected_callbacks),'Original carried callback vector');counts['registration_return_order_checks']+=1
     rows.append(observation);counts['paired_phases']+=1
    equal(ori.data(f'cleanup/{seq}/registry.bin'),struct.pack('<88I',*expected_callbacks),'Exact original complete callback vector');counts['paired120_sequences']+=1
   native.close()
  ori.close()
  for module in (J,m):
   for p,h in getattr(module,'PINS',{}).items():pin(p,h if isinstance(h,str)else h['sha256'])
  pin(__file__);passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  for label,value in (('observer-span-relations.json',observer_spans),('paired-observations.json',rows),('indeterminate-field.json',field_rows),('loader-page-input-relation.json',dict(page=0x5f4cc000,original_bootstrap_sha256=hashlib.sha256(loaded_page).hexdigest(),native_raw_sha256=hashlib.sha256(raw_page).hexdigest(),own_process_complete_4096_differences=loader_differences,observations=loader_rows,exact_reached_DWORD=0x5f4cecec,ordinary_page_mask=False,ordinary_page_relation=False))):
   (out/label).write_text(json.dumps(value,indent=2)+'\n');pin(out/label)
  report=dict(passed=passed,scope='Bounded selected120 initialization relation against fresh genuine original120: entire35 ordinary nonstack pages plus separate whole initialized/raw loader-page input relation, literal callback order and atexit success return, complete numeric FX projection and finite API metadata seams, backed by strict persistent native source State/CPU/FX/ENV/full37pages',counts=dict(counts),paired_initialization_data_contract=passed,original_record_bytes=307840,native_record_bytes=159716,original_and_native_bytes_modified=False,blanket_page_mask=False,owning_IAT_projection_addresses=list(IATS),observed_original_observer_spans=observer_spans,indeterminate_relation_address=0x6099e8,new_MFC_source_header_relations=True,new_FS_source_publication_fields=[r['publication']for r in fsbindings if r['publication']],new_FS_header_relation_address=0x60b51c,new_FS_header_relation_scope='Exact own-branch literal local-byte read/write and carry, from genuine original BEFORE stack or persistent native source BEFORE stack. Raw values retained; whole-game liveness not claimed.',own_branch_header_input='Exact genuine branch BEFORE CPU/pages only; literal saved stack-byte provenance with last dominating source store; declared positive allocation facts establish normal path without any candidate AFTER byte',MFC_import_relation_slots=511,MFC_typed_pointer_fields=[r['field']for r in pointer_fields],MFC_one_past_end_fields=[r['field']for r in pointer_fields if r['is_one_past_end']],MFC_header_fields=[r['field']for r in header_fields],MFC_private_padding_relation='Each branch retains its own actual pre-guest-write API allocation backing; source-owned initialized nodes compared by separate full original/native ownership gates. No cross-branch arbitrary heap padding equality is claimed.',indeterminate_relation='Each branch literal PUSH ECX/MOV AL,[ESP+3] highbyte independently derived from its genuine constructor BEFORE; raw values retained and exact carry checked. Known selected suffix and recovered UI/container/cleanup consumers do not read byte0; whole-game dynamic aliases are excluded.',crossbranch_CPU_contract='EAX, nonvolatile GPRs, ESP, returnPC exact at every phase. ECX/EFLAGS exact outside one finite SPI return/immediate input seam. EDX and real32 API volatile outputs retained as observed typed boundary state; strict native full CPU/State separately modeled, no whole original API volatile equality claimed.',crossbranch_numeric_contract='Frozen hardwarefx capability-mask projection only; exact CW/TOP/status/raw80/SIMD all phases. Exact ENV head throughout; actual SPI FIP/FOP/FDP metadata retained on finite the measured source/table-derived interval until next original/literal source FP overwrites it. Exact complete ENV otherwise.',original_provider_scratch_stack_crossbranch_equal=False,native_full_stack_source_proven=True,whole_game_liveness_proven=False,FSQRT_scope='Exact measured default-zero constructor inputs in six CW/TOP cases; broader nonzero/denormal Remill behavior excluded.',initializers_added_by_this_report=0,whole_M4_complete=False,files=PINS)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=PINS),indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2])


