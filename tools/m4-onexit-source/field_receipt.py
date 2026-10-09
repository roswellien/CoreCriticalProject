"""Bounded exact static consumer inventory for the6099E8 constructor byte."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(name):
 out=ROOT/'reports/m4-onexit-source'/name;need(not out.exists(),'Fresh field receipt');out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Pinned exact field source');pins[str(p)]=v;return p
 sp=importlib.util.spec_from_file_location('field_PE',pin(ROOT/'tools/analysis/pe.py'));PE=importlib.util.module_from_spec(sp);sp.loader.exec_module(PE)
 raw=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes();pe=PE.PEImage(raw)
 static=json.loads(pin(ROOT/'reports/m4-onexit-source/field-reference-r2/export.json').read_bytes());refs=static['references'];functions={f['entry']:f for f in static['exports']};checked=0
 for f in functions.values():
  for r in f['instructions']:
   code=bytes.fromhex(r['bytes_hex']);off,_=pe.rva_range(r['pc']-pe.image_base,len(code));need(raw[off:off+len(code)]==code,'Exact Ghidra instruction matches PE');checked+=1
 immediate=[]
 for address in range(0x6099e8,0x6099f8):
  pattern=struct.pack('<I',address);cursor=0;hits=[]
  while (cursor:=raw.find(pattern,cursor))>=0:
   owner=next((s for s in pe.sections if s['raw_offset']<=cursor<s['raw_offset']+s['raw_size']),None);need(owner is not None,'Bounded source immediate');va=pe.image_base+owner['virtual_address']+cursor-owner['raw_offset'];hits.append(dict(file_offset=cursor,immediate_address=va,section=owner['name']));cursor+=1
  immediate.append(dict(target=address,hits=hits))
 direct=[r for r in refs if r['to']==0x6099e8];need({r['from']for r in direct}=={0x49d454,0x49d487,0x49d546,0x49d5d5},'Complete persisted direct field references')
 hits=immediate[0]['hits'];need({h['immediate_address']-1 for h in hits}=={r['from']for r in direct},'All literal field-address DWORD occurrences resolve exact four instructions');need(not any(r['hits']for r in immediate[1:4]),'No exact pointer literal to three pad bytes')
 f=functions[0x49da10];rows={r['pc']:r for r in f['instructions']}
 # Literal object aliases, spills and reloads are visible in the sealed225-row method. Heap-buffer aliases are a different pointer domain.
 alias_sources=[(0x49da14,'MOV EBX,ECX'),(0x49da2a,'MOV dword ptr [ESP + 0x10],EBX'),(0x49dac3,'MOV EAX,dword ptr [ESP + 0x10]'),(0x49daf1,'MOV EAX,dword ptr [ESP + 0x10]'),(0x49db0a,'MOV EDX,dword ptr [ESP + 0x14]'),(0x49db7b,'MOV EBX,dword ptr [ESP + 0x10]')]
 for pc,text in alias_sources:need(rows[pc]['text']==text,'Literal object alias source/spill')
 accesses=[(0x49da1b,8,'read'),(0x49da1e,12,'read'),(0x49da34,4,'read'),(0x49da89,4,'read'),(0x49dace,8,'read'),(0x49daf5,4,'read'),(0x49db14,4,'read'),(0x49db17,12,'write'),(0x49db20,4,'write'),(0x49db28,8,'write'),(0x49db35,8,'read'),(0x49db38,4,'write'),(0x49db45,8,'write'),(0x49db89,8,'read'),(0x49dbab,8,'read'),(0x49dbbf,8,'read/write'),(0x49dbf3,8,'read'),(0x49dc25,8,'read/write')]
 for pc,offset,op in accesses:need(pc in rows and ('+ 0x'+format(offset,'x')+']')in rows[pc]['text'],'Declared literal object member access')
 no_op=functions[0x40baf0];need(len(no_op['instructions'])==1 and no_op['instructions'][0]['bytes_hex']=='c20800','Exact erasure helper RET8 reads no object storage')
 raw_cleanup=bytes.fromhex('518a0de0996000b00184c8752d8ad10ad0a1ec996000508815e099600089442404e8f4e6100083c40433c0a3ec996000a3f0996000a3f499600059c3');off,_=pe.rva_range(0x49d600-pe.image_base,len(raw_cleanup));need(raw[off:off+len(raw_cleanup)]==raw_cleanup,'Exact cleanup span')
 # No selected later recovered startup row names the object; all exact outside-init direct references belong to the later dialog vector method/UI path above.
 interface=json.loads(pin(ROOT/'reports/m4-onexit-source/interface-r1/instruction-contracts.json','3f0d96b381dc4e89dc7cb63c7f252414ba1392deae140718daba6e17c3d438d3').read_bytes());later=[r for r in interface['instructions']if '0x6099e8'in r['operands']and r['pc']!=0x49d5d5];need(not later,'No remaining selected recovered direct field consumer')
 data=dict(field_address=0x6099e8,object_extent=16,member_layout=[dict(offset=0,width=1,role='Opaque allocator-like/dummy byte; exact source copies incomingECX highbyte'),dict(offset=1,width=3,role='Untouched padding'),dict(offset=4,width=4,role='Element begin pointer'),dict(offset=8,width=4,role='Element end pointer'),dict(offset=12,width=4,role='Allocation end pointer')],container_inference='Contiguous DWORD-element vector-like container used by dialog49D350 and49D710, inferred from pointer arithmetic, operator_new/delete and insertion loops. Exact source type and intentional allocator semantics are unproved.',constructor=dict(root=0x49d5c0,body=0x49d5d0,write=0x49d5d5,source='PUSH ECX allocates4B local, MOV AL,[ESP+3] reads its uninitialized high byte, no explicit local initialization; saves/restores ECX',write_is_literal=True,deliberate_uninitialized_allocator_intent_proven=False),exact_direct_references=direct,all_literal_DWORD_occurrences=immediate,alias_sources=[rows[pc]for pc,_ in alias_sources],insertion_object_accesses=[dict(pc=pc,member_offset=off,operation=op,row=rows[pc])for pc,off,op in accesses],insert_method=dict(entry=0x49da10,instructions=len(f['instructions']),object_byte0_read=False,known_object_address_escape=False,calls=[r for r in f['instructions']if r['text'].startswith('CALL')]),erase_helper=dict(entry=0x40baf0,bytes_hex='c20800',object_read=False),cleanup=dict(entry=0x49d600,stop=0x49d63c,bytes_hex=raw_cleanup.hex(),field_byte0_read=False,first_member_access=0x6099ec),known_later_UI_consumers=[0x49d350,0x49d710],selected_suffix_direct_consumers=later,whole_game_indirect_alias_liveness_proven=False,unknown_dynamic_pointer_creation_excluded=False)
 (out/'field.json').write_text(json.dumps(data,indent=2)+'\n');pin(out/'field.json');pin(__file__)
 for x in ('field-reference-r1','field-reference-r2'):pin(ROOT/'reports/m4-onexit-source'/x/'report.json')
 report=dict(passed=True,scope='Exact bounded static field/object consumer inventory from persistedGhidra DB and literalPE; no ABI normalization or game edit',exact_PE_checked_instructions=checked,field_byte0_direct_write_sites=1,field_byte0_direct_read_sites=0,object_address_materializations=3,insertion_member_accesses=len(accesses),known_UI_and_cleanup_byte0_consumers=0,uninitialized_local_read_established=True,allocator_type_inference_only=True,whole_game_liveness_proven=False,initializer_credit=False,masked_bytes=0,source_modified=False,native_modified=False,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),exact_PE_checked_instructions=checked)))
if __name__=='__main__':main(sys.argv[1])
