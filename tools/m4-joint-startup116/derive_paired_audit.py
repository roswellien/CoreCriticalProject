"""Add precise116 fields to the frozen independent109 raw paired review."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
old=ROOT/'tools/m4-joint-startup109/paired_audit.py';new=HERE/'paired_audit.py'
def one(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
s=old.read_text().replace('m4-joint-startup109-root','m4-joint-startup116-root').replace('1308','1392').replace('paired109','paired116').replace('len(order)==109','len(order)==116').replace('selected109','selected116')
s=one(s,"contract=read(ROOT/'reports/m4-fs-source/recovery-r3/instruction-contracts.json')","contract=read(ROOT/'reports/m4-container-source/recovery-r3/instruction-contracts.json')\n fscontract=read(ROOT/'reports/m4-fs-source/recovery-r3/instruction-contracts.json')")
s=one(s,"fsinstructions={x['pc']:x for x in contract['instructions']}","fsinstructions={x['pc']:x for x in fscontract['instructions']}")
a="need(len(fields)==58,'Exactly58 source pointer fields')"
b="""need(len(fields)==58,'Exactly58 inherited source pointer fields')
 interface=read(ROOT/'reports/m4-container-source/allocation-interface-r1/report.json','89a6a4b581bedd7a1b98ccfad1344ba35f6c50a011964230aecaa1f7295e95ec')
 need(interface['passed']and interface['count']==5 and interface['string_count']==3 and not interface['AFTER_machine_seed'],'Frozen exact new pointer geometry')
 cinstructions={x['pc']:x for x in contract['instructions']};container_fields=[]
 for vector in interface['vector_endpoints']:
  allocation=next(a for a in interface['allocations']if(a['root'],a['CALL_pc'])==(vector['root'],vector['CALL_pc']))
  need(all(allocation[k]==vector[k]for k in('requested_size','object','publication')),'Same actual positive vector source allocation')
  sites=[(vector['publication_PC'],vector['publication'],0),(vector['end_PC'],vector['end_address'],0),(vector['capacity_PC'],vector['capacity_address'],vector['requested_size'])]
  sites += [(x['PC'],x['address'],x['offset'])for x in vector['additional_empty_pointer_fields']]
  for pc,address,offset in sites:
   code=cinstructions[pc];need(code['mnemonic']=='mov'and code['decoded_operands'][0]['bits']==32 and code['explicit_memory_writes']==[0],'Exact reached32bit vector source store')
   operand=code['decoded_operands'][0];need(operand['kind']=='memory'and not operand['terms']and operand['displacement']==address,'Exact physical absolute vector destination')
   need(offset in(0,vector['requested_size'])and address not in fields,'Unique exact base/end vector relation')
   fields[address]=order[vector['root']];container_fields.append(dict(root=vector['root'],pc=pc,address=address,offset=offset))
 need(len(container_fields)==17,'All17 actual empty vector endpoint stores')
 for string in read(ROOT/'reports/m4-container-source/allocation-interface-r1/string-inputs.json'):
  need(string['publication']==string['object_addresses'][0]+4 and string['publication']not in fields,'Exact new string publication destination')
  code=cinstructions[string['publication_PC']];need(code['mnemonic']=='mov'and code['decoded_operands'][0]['bits']==32 and code['explicit_memory_writes']==[0],'Actual source32bit strdup publication')
  fields[string['publication']]=order[string['root']]
 need(len(fields)==78,'Exactly78 complete inherited/new typed pointer fields')"""
s=one(s,a,b)
s=one(s,'iats={0x5bb4fc,0x5bb52c,0x5bb530,0x5bb6dc,0x5bb670,0x5bb4bc}','iats={0x5bb4fc,0x5bb52c,0x5bb530,0x5bb6dc,0x5bb670,0x5bb4bc,0x5bb454,0x5bb4c8}')
s=s.replace('Exactly six owning game IAT DWORDs','Exactly eight owning game IAT DWORDs').replace("len(row['nonstack_pages'])==68,'34 entire nonstack pages on both sides'","len(row['nonstack_pages'])==70,'35 ordinary entire nonstack pages on both sides; loader page relation is separate'")
s=one(s,"and address!=0x20001000 and(address,side)not in seen","and address not in(0x20001000,0x5f4cc000)and(address,side)not in seen")
s=one(s,'new_FS_DWORD_fields=3,new_FS_BYTE_fields=1,blanket_page_mask=False','new_FS_DWORD_fields=3,new_FS_BYTE_fields=1,new_vector_pointer_stores=17,new_string_pointer_fields=3,loader_page_relation_separate=True,blanket_page_mask=False')
assert not new.exists();compile(s,str(new),'exec');new.write_text(s,encoding='utf-8');print(str(new))
