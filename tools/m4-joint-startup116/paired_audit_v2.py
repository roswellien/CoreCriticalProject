"""Independent bounds on retained raw paired differences and byte provenance.

This observation audit adds no execution credit. The source/owner gates verify
the complete canonical archives; final acceptance rehashes every physical input.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(paired_path,name):
 out=ROOT/'reports/m4-joint-startup116-root'/name;need(not out.exists(),'Fresh paired audit');out.mkdir(parents=True);pins={}
 def read(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Frozen bounded-audit input');pins[str(p)]=v;return json.loads(p.read_bytes())
 p=Path(paired_path).resolve();r=read(p);need(r['passed']and not r['blanket_page_mask']and not r['original_and_native_bytes_modified'],'Unmodified paired bytes')
 need(r['counts']['paired_phases']==1392 and r['MFC_import_relation_slots']==511,'Complete paired116 extent')
 contract=read(ROOT/'reports/m4-container-source/recovery-r3/instruction-contracts.json')
 fscontract=read(ROOT/'reports/m4-fs-source/recovery-r3/instruction-contracts.json')
 oldcontract=read(ROOT/'reports/m4-mfc-source/recovery-r4/instruction-contracts.json')
 order={x['entry']:i for i,x in enumerate(contract['selected_order'])};need(len(order)==116,'Exact selected116 order')
 instructions={x['pc']:x for x in oldcontract['instructions']}
 roots={x['entry']:x for x in oldcontract['roots']};need(len(roots)==32,'32 new constructors')
 strings=read(ROOT/'reports/m4-strings-source/recovery-r7/string-roots.json')
 fields={x['objects'][0]['address']+4:order[x['entry']]for x in strings if x['entry']!=0x4e6a10};need(len(fields)==16,'16 inherited strdup publications')
 bindings=read(ROOT/'reports/m4-mfc-source/allocation-contracts-r4/allocation-inputs.json')
 need(len(bindings)==35 and len({(x['root'],x['CALL_pc'])for x in bindings})==35,'35 exact source allocation calls')
 field_receipt=read(ROOT/'reports/m4-mfc-source/field-contracts-r1/report.json','63cd8d2665580dc397745d0f34769dac321089fa2ec422eeea7681b08e3a1a55')
 need(field_receipt['passed']and not field_receipt['AFTER_machine_seed'],'Source field geometry before paired results')
 typed_fields=read(ROOT/'reports/m4-mfc-source/field-contracts-r1/pointer-fields.json')
 header_contracts=read(ROOT/'reports/m4-mfc-source/field-contracts-r1/header-fields.json')
 need(typed_fields==field_receipt['pointer_fields']and header_contracts==field_receipt['header_fields'],'Separate physical typed-field files')
 need(len(typed_fields)==39 and len(header_contracts)==36,'39 pointer fields and36 byte headers')
 for x in typed_fields:
  allocation=next(a for a in bindings if(a['root'],a['CALL_pc'])==(x['root'],x['CALL_pc']))
  need(x['object']==allocation['object']and x['primary_publication']==allocation['publication']and x['requested_size']==allocation['requested_size'],'Exact allocation owner binding')
  need(x['source_row']==instructions[x['write_pc']]and x['source_row']['mnemonic']=='mov'and x['source_row']['decoded_operands'][0]['bits']==32,'Exact physical pointer-store row')
  need(x['pointer_offset']==(x['requested_size']if x['is_one_past_end']else 0),'Only source base or genuine one-past-end')
  need(x['field']not in fields,'Distinct source pointer field');fields[x['field']]=order[x['root']]
 need(len(fields)==55 and sum(x['is_one_past_end']for x in typed_fields)==4,'55 exact owner pointer fields including four endpoints')
 header_by_field={x['field']:x for x in header_contracts};need(len(header_by_field)==36,'Unique complete header geometry')
 fsfields=read(ROOT/'reports/m4-fs-source/field-contracts-r1/report.json','c087385c8ed1ff9834dcd00dc8b9164124cd1189fafc2c4791c61ebbafd2704a')
 need(fsfields['passed'] and len(fsfields['pointer_fields'])==3 and len(fsfields['header_fields'])==1,'Exactly three FS DWORD fields and one BYTE field')
 fsinstructions={x['pc']:x for x in fscontract['instructions']}
 for field in fsfields['pointer_fields']:
  need(field['width']==4 and fsinstructions[field['write_PC']]['bytes_hex']==field['bytes_hex'],'Exact physical FS pointer-store bytes')
  need(field['field'] not in fields,'Distinct FS static pointer publication');fields[field['field']]=order[field['root']]
 need(len(fields)==58,'Exactly58 inherited source pointer fields')
 interface=read(ROOT/'reports/m4-container-source/allocation-interface-r1/report.json','89a6a4b581bedd7a1b98ccfad1344ba35f6c50a011964230aecaa1f7295e95ec')
 need(interface['passed']and interface['count']==5 and interface['string_count']==3 and not interface['AFTER_machine_seed'],'Frozen exact new pointer geometry')
 cinstructions={x['pc']:x for x in contract['instructions']};container_fields=[];container_roots={x['entry']:x for x in contract['roots']}
 for vector in interface['vector_endpoints']:
  allocation=next(a for a in interface['allocations']if(a['root'],a['CALL_pc'])==(vector['root'],vector['CALL_pc']))
  need(all(allocation[k]==vector[k]for k in('requested_size','object','publication')),'Same actual positive vector source allocation')
  sites=[(vector['publication_PC'],vector['publication'],0),(vector['end_PC'],vector['end_address'],0),(vector['capacity_PC'],vector['capacity_address'],vector['requested_size'])]
  sites += [(x['PC'],x['address'],x['offset'])for x in vector['additional_empty_pointer_fields']]
  for pc,address,offset in sites:
   code=cinstructions[pc];need(code['mnemonic']=='mov'and code['decoded_operands'][0]['bits']==32 and code['explicit_memory_writes']==[0],'Exact reached32bit vector source store')
   operand=code['decoded_operands'][0]
   source_object=next(x for x in container_roots[vector['root']]['objects'] if x['address']==vector['object'])
   seed=cinstructions[source_object['pc']];need(seed['mnemonic']=='mov' and seed['decoded_operands']==[dict(kind='register',register='ecx',bits=32),dict(kind='immediate',value=vector['object'],signed_text=seed['decoded_operands'][1]['signed_text'])],'Physical caller ECX object constant')
   tail=cinstructions[source_object['pc']+seed['width']];need(tail['mnemonic']=='jmp' and tail['decoded_operands'][0]['kind']=='immediate','Literal constructor tail target')
   constructor=tail['decoded_operands'][0]['value'];moves=[x for x in cinstructions.values() if constructor<=x['pc']<constructor+32 and x['mnemonic']=='mov' and x['decoded_operands']==[dict(kind='register',register='esi',bits=32),dict(kind='register',register='ecx',bits=32)]]
   need(len(moves)==1 and moves[0]['pc']<pc,'Literal constructor ESI receives caller ECX before endpoint store; complete reached source verified separately')
   need(operand['kind']=='memory' and operand['segment']=='default' and operand['terms']==[dict(register='esi',scale=1)] and operand['displacement']==address-vector['object'],'Exact physical ESI-relative object destination')
   need(offset in(0,vector['requested_size'])and address not in fields,'Unique exact base/end vector relation')
   fields[address]=order[vector['root']];container_fields.append(dict(root=vector['root'],pc=pc,address=address,offset=offset))
 need(len(container_fields)==17,'All17 actual empty vector endpoint stores')
 for string in read(ROOT/'reports/m4-container-source/allocation-interface-r1/string-inputs.json'):
  need(string['publication']==string['object_addresses'][0]+4 and string['publication']not in fields,'Exact new string publication destination')
  code=cinstructions[string['publication_PC']];need(code['mnemonic']=='mov'and code['decoded_operands'][0]['bits']==32 and code['explicit_memory_writes']==[0],'Actual source32bit strdup publication')
  fields[string['publication']]=order[string['root']]
 need(len(fields)==78,'Exactly78 complete inherited/new typed pointer fields')
 newheader=fsfields['header_fields'][0]
 need((newheader['root'],newheader['field'],newheader['width'],newheader['read_PC'],newheader['write_PC'],newheader['actual_read_address'])==(0x4d4830,0x60b51c,1,0x4d4914,0x4d4922,0x200017eb),'Exact new literal header geometry')
 need(fsinstructions[newheader['read_PC']]['bytes_hex']==newheader['read_bytes'] and fsinstructions[newheader['write_PC']]['bytes_hex']==newheader['write_bytes'],'Exact new header read/write bytes')
 imports=read(ROOT/'reports/m4-mfc-source/original-preparation-r1/mfc-import-bindings.json')
 iats={0x5bb4fc,0x5bb52c,0x5bb530,0x5bb6dc,0x5bb670,0x5bb4bc,0x5bb454,0x5bb4c8}
 need(set(r['owning_IAT_projection_addresses'])==iats,'Exactly eight owning game IAT DWORDs')
 mfc_iats={x['slot']for x in imports};need(len(mfc_iats)==511 and all(x&~4095==0x5f498000 for x in mfc_iats),'511 declared MFC import DWORDs')
 headers=read(p.parent/'indeterminate-field.json');header_fields={};counts=collections.Counter();old_header_rows=0
 for row in headers:
  identity=(row['level'],row['sequence']);need(identity[0]in('O0','O2')and 0<=identity[1]<6,'Header sequence identity')
  if row['address']==0x6099e8:
   need(row['write_PC']==0x49d5d5,'Inherited literal byte store')
   for side in('original','native'):
    need(row[side+'_derived']==row['constructor_before_ECX_'+side]>>24 and row[side+'_after']==row[side+'_derived'],'Inherited byte from own BEFORE ECX')
   old_header_rows+=1;continue
  sources=[row['original_source'],row['native_source']];a,b=sources
  if row.get('new_FS_local_byte_relation'):
   need(row['address']==0x60b51c,'Only one additional byte field')
   for source in sources:
    need((source['root'],source['field'],source['read_pc'],source['write_pc'],source['read_address'])==(0x4d4830,0x60b51c,0x4d4914,0x4d4922,0x200017eb),'Exact source byte PC/address relation')
    proof=source['provenance'];need(proof['kind'] in ('genuine_branch_BEFORE_stack_byte','carried_source_BEFORE_stack_byte') and proof['address']==source['read_address'] and proof['value']==source['value'] and proof['no_root_source_store_before_read'] is True,'Genuine branch BEFORE byte, no invented dominating store')
    need(len(source['branch_BEFORE_cpu'])==10 and 0<=source['value']<=255,'Genuine branch BEFORE CPU and full byte');counts['new_FS_BEFORE_stack_byte_proofs']+=1
   key=identity+(row['address'],);need(key not in header_fields,'Unique new header relation');header_fields[key]=(order[0x4d4830],a['value'],b['value']);continue
  need((a['root'],a['object'],a['field'],a['write_pc'])==(b['root'],b['object'],b['field'],b['write_pc']),'Same literal header write')
  root=roots[a['root']];address=row['address'];geometry=header_by_field[address]
  need(address==a['field']and(a['root'],a['object'],a['write_pc'])==(geometry['root'],geometry['object'],geometry['write_pc']),'Exact constructor object/header field')
  need(a['object']in {x['address']for x in root['objects']}and address-a['object']==geometry['object_offset']in(0,4),'Exact object base or vtable+4 header')
  code=instructions[a['write_pc']];need(code==geometry['source_row']and code['mnemonic']=='mov'and code['decoded_operands'][0]['bits']==8 and code['explicit_memory_writes']==[0],'Exact physical byte publication instruction')
  for source in sources:
   need(len(source['branch_BEFORE_cpu'])==10 and 0<=source['value']<=255,'Own genuine branch BEFORE and byte value')
   proof=source['source_stack_byte_provenance'];need(len(proof)==1,'One literal saved-byte provenance')
   q=proof[0];need(q['source_store_index']<q['access_index']and q['bytes']==1 and q['source_store_bytes']in(1,2,4),'Dominating saved-byte store precedes read')
   need(0x20001000<=q['address']<0x20002000 and q['source_store_address']<=q['address']<q['source_store_address']+q['source_store_bytes'],'Exact stack byte contained in source store')
   need((q['source_store_value']>>(8*(q['address']-q['source_store_address'])))&255==q['value']==source['value'],'Exact retained byte from saved source value')
   need(q['pc']in instructions and q['source_store_pc']in instructions,'Both provenance PCs in physical new game source')
   load=instructions[q['pc']];need(load['mnemonic']=='mov'and instructions[q['source_store_pc']]['mnemonic']in('push','call','mov'),'Literal load and dominating stack store')
   need(load['decoded_operands'][0]==code['decoded_operands'][1],'Same literal AL/CL byte register at load and publication')
   need(q['pc']==geometry['read_pc']and q['source_store_pc']==geometry['store_pc']and q['address']-q['source_store_address']==geometry['byte_offset'],'Same statically recovered source byte-read/store sites')
   counts['retained_own_branch_saved_byte_proofs']+=1
  key=identity+(address,);need(key not in header_fields,'One constructor header relation per sequence/object');header_fields[key]=(order[a['root']],a['value'],b['value'])
 need(old_header_rows==12,'12 inherited own-branch byte relations')
 expected_headers=set(header_by_field)|{0x60b51c}
 for level in('O0','O2'):
  for seq in range(6):need({k[2]for k in header_fields if k[:2]==(level,seq)}==expected_headers,'Every reached object header relation in each sequence')
 observations=read(p.parent/'paired-observations.json');need(len(observations)==1392,'1392 raw phase observations');identities=set()
 def physical(path,expected=None):
  path=Path(path).resolve();actual=sha(path);need(expected is None or actual==expected,'Exact physical observer input');pins[str(path)]=actual;return path.read_bytes()
 compiled=read(ROOT/'reports/m4-container-review/observer-compiled-r3/report.json','9cd673ab15e2a6e06baa617a7d84ee341e85fb80d41531e253a7449933642e59')
 need(compiled['passed'] and compiled['counts']['compiled_FS_trampolines']==30,'Compiled transparent original observer')
 build=read(ROOT/'reports/m4-container-source/original-build-r2/build.json','8b1e7694bf3d9a651b729dc6740310c72c1b7409918de62c9411394da3021541')
 worker_bytes=physical(build['worker'],build['worker_sha256'])
 physical(ROOT/'tools/analysis/pe.py');spec=importlib.util.spec_from_file_location('observer_span_PE',ROOT/'tools/analysis/pe.py');PE=importlib.util.module_from_spec(spec);spec.loader.exec_module(PE)
 worker=PE.PEImage(worker_bytes);need(worker.image_base==0x18000000,'Exact original fixed worker base')
 game=PE.PEImage(physical(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'))
 bindings={x['PC']:x for x in read(ROOT/'reports/m4-container-source/original-preparation-r2/fs-hook-bindings.json')}
 observer_spans=read(p.parent/'observer-span-relations.json')
 need(observer_spans==r['observed_original_observer_spans'],'Same frozen exact observer relations')
 need([(x['PC'],x['width']) for x in observer_spans]==[(0x482b47,6),(0x482b4e,7),(0x482b8e,7)],'Only three exact observed-page spans,20 source bytes')
 observer_bytes={}
 for span in observer_spans:
  hook=bindings[span['PC']];raw=bytes.fromhex(hook['raw_bytes']);pc=span['PC']
  need(len(raw)==span['width'] and raw.hex()==span['native_hex'] and hook['declared_observer']==span['declared_symbol'],'Exact physical observer declaration')
  offset,_=game.rva_range(pc-game.image_base,len(raw));need(game.data[offset:offset+len(raw)]==raw,'Native observer-span bytes are physical game bytes')
  key=struct.pack('<3I',pc,len(raw),hook['kind']);matches=[];cursor=0
  while True:
   position=worker_bytes.find(key,cursor)
   if position<0:break
   if worker_bytes[position+16:position+16+len(raw)]==raw:matches.append(position)
   cursor=position+1
  need(matches==[span['compiled_table_offset']],'One exact final linked FsHook table identity')
  target=struct.unpack_from('<I',worker_bytes,matches[0]+12)[0]
  need(target==span['compiled_target'],'Exact compiled observer target')
  target_offset,_=worker.rva_range(target-worker.image_base,11)
  need(worker_bytes[target_offset:target_offset+2]==b'\xc7\x05' and struct.unpack_from('<I',worker_bytes,target_offset+6)[0]==hook['kind'] and worker_bytes[target_offset+10]==0xa3,'Compiled observer direction and saved EAX entry; complete transparency checked separately')
  original=b'\xe9'+struct.pack('<I',(target-pc-5)&0xffffffff)+b'\x90'*(len(raw)-5)
  need(original.hex()==span['original_hex'],'Exact E9 relative compiled target and NOP span')
  for index,(a,b) in enumerate(zip(original,raw)):
   need(pc+index not in observer_bytes,'Distinct source observer byte');observer_bytes[pc+index]=(a,b)
 need(len(observer_bytes)==20,'Exactly20 source-bound observer bytes')
 old_start=order[0x4c58c0]
 for row in observations:
  phase=row['phase'];identity=(row['level'],row['sequence']);need(order[row['entry']]==phase,'Exact phase association');key=identity+(phase,);need(key not in identities,'Unique observed phase');identities.add(key)
  need(len(row['nonstack_pages'])==70,'35 ordinary entire nonstack pages on both sides; loader page relation is separate')
  for address in expected_headers:
   start,av,bv=header_fields[identity+(address,)]
   if phase==start:
    source=next(h for h in headers if(h['level'],h['sequence'],h['address'])==identity+(address,))
    for side in('original','native'):
     need(source[side+'_source']['branch_BEFORE_cpu']==list(__import__('struct').unpack('<10I',bytes.fromhex(row['CPU_before_'+side+'_hex']))),'Retained derivation uses exact own-branch genuine phase BEFORE CPU')
  for field in('FX_before_differences','FX_after_differences'):
   need(all(d['offset']in(28,29,30)for d in row[field]),'Only retained raw capability descriptor differences');counts['raw_FX_pairs_with_only_capability_differences']+=1
  seen=set()
  for page in row['nonstack_pages']:
   side=page['side'];address=page['page'];need(side in('before','after')and address not in(0x20001000,0x5f4cc000)and(address,side)not in seen,'Unique whole nonstack page');seen.add((address,side));allowed=set()
   for slot in iats|mfc_iats:
    if slot&~4095==address:allowed.update(range(slot,slot+4))
   for slot,start in fields.items():
    if slot&~4095==address and(phase>start or(phase==start and side=='after')):allowed.update(range(slot,slot+4))
   for hkey,(start,av,bv)in header_fields.items():
    if hkey[:2]==identity and hkey[2]&~4095==address and(phase>start or(phase==start and side=='after')):allowed.add(hkey[2])
   if phase>old_start or(phase==old_start and side=='after'):allowed.add(0x6099e8)
   need(len(page['original_sha256'])==len(page['native_sha256'])==64,'Whole raw page hashes')
   differences=page['differences'];need(len({d['offset']for d in differences})==len(differences),'Unique retained unequal byte offsets')
   observed={d['offset']:(d['original'],d['native']) for d in differences}
   for span in observer_spans:
    if span['PC']&~4095!=address:continue
    for absolute in range(span['PC'],span['PC']+span['width']):
     a,b=observer_bytes[absolute];offset=absolute-address
     need(observed.get(offset)==((a,b) if a!=b else None),'Every actual observed hook byte equals exact original compiled patch and native physical source')
     allowed.add(absolute)
    counts['raw_source_bound_observer_span_relations']+=1
   need(all(0<=d['offset']<4096 and address+d['offset']in allowed and 0<=d['original']<=255 and 0<=d['native']<=255 and d['original']!=d['native']for d in differences),'All actual unequal bytes inside exactly activated relations')
   for d in differences:
    hkey=identity+(address+d['offset'],)
    if hkey in header_fields:
     start,av,bv=header_fields[hkey];need(phase>start or(phase==start and side=='after'),'Header activated only after source write');need((d['original'],d['native'])==(av,bv),'Raw byte equals both retained source derivations')
   need(bool(differences)==(page['original_sha256']!=page['native_sha256']),'Raw unequal bytes consistent with whole hashes');counts['raw_whole_page_difference_scopes']+=1
 need(len(identities)==1392 and {x[0]for x in identities}=={'O0','O2'},'Both complete observed native levels')
 for path,h in r['files'].items():
  if not str(path).endswith('.mwb'):need(sha(path)==h,'Immutable paired observation dependency');pins[str(path)]=h
 pins[str(Path(__file__).resolve())]=sha(__file__)
 result=dict(passed=True,scope='Independent exact retained raw page/FX difference bounds, compiled20byte original observer spans and own-branch saved-byte provenance; complete original/native source and owner validation remains required',counts=dict(counts),source_publication_fields=sorted(fields),owning_game_IAT_slots=sorted(iats),declared_MFC_IAT_slots=511,object_header_relations_per_sequence=len(expected_headers),new_FS_DWORD_fields=3,new_FS_BYTE_fields=1,new_vector_pointer_stores=17,new_string_pointer_fields=3,exact_original_observer_spans=3,exact_original_observer_bytes=20,loader_page_relation_separate=True,blanket_page_mask=False,raw_archives_rehashed=False,parent_full_archive_validation_required=True,whole_game_alias_liveness=False,files=pins)
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1],sys.argv[2])
