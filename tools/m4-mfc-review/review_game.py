"""Independent original game-byte/root/call/store review for the MFC family."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def need(value,message):
 if not value:raise ValueError(message)
def sha(path):
 with Path(path).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def main(version):
 out=ROOT/'reports/m4-mfc-review'/version;need(not out.exists(),'Fresh independent MFC game review');pins={}
 def pin(path,expected=None):
  path=Path(path).resolve();digest=sha(path);need(expected is None or digest==expected,'Exact physical source game dependency '+str(path));pins[str(path)]=digest;return path
 recovery=json.loads(pin(ROOT/'reports/m4-mfc-source/recovery-r4/report.json','b50217399d254eddc620ab39bf8d934fd2cc30233e575356a9d8c40761c33e0f').read_bytes())
 need(recovery['passed']and recovery['root_count']==32 and recovery['all_game_entries']==69 and recovery['game_bodies']==65 and not recovery['original_executed'],'Static original32-family recovery only')
 roots=json.loads(pin(ROOT/'reports/m4-mfc-source/recovery-r4/mfc-roots.json').read_bytes())
 graphs=json.loads(pin(ROOT/'reports/m4-mfc-source/recovery-r4/game-normal-graphs.json').read_bytes())
 supplied=json.loads(pin(ROOT/'reports/m4-mfc-source/recovery-r4/instruction-contracts.json').read_bytes())
 PE=load('mfc_game_independent_PE',pin(ROOT/'tools/analysis/pe.py'));parser=load('mfc_game_independent_parser',pin(ROOT/'tools/m4-crt-locale-batch-recovery/recover_v2.py'))
 game=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes();pe=PE.PEImage(game)
 def physical(address,size):
  offset,_=pe.rva_range(address-pe.image_base,size);return game[offset:offset+size]
 instructions={}
 for entry,graph in graphs.items():
  need(int(entry)==graph['entry']and not graph['FS_sites']and not graph['unresolved_controls'],'Each exact bounded game root closure')
  for row in graph['instructions']:
   raw=bytes.fromhex(row['bytes']);need(len(raw)==row['size']and physical(row['pc'],len(raw))==raw,'Exact physical game instruction '+hex(row['pc']))
   parsed=parser.instruction_contract(dict(pc=row['pc'],width=row['size'],bytes_hex=row['bytes'],mnemonic=row['mnemonic'],operands=row['operands'].split(' <')[0].strip()))
   need(row['pc']not in instructions or instructions[row['pc']]==parsed,'Overlapping game bodies retain one operand contract');instructions[row['pc']]=parsed
 need(len(instructions)==547 and {r['pc']:r for r in supplied['instructions']}==instructions,'All 547 independently parsed original rows match supplied operand interface')
 family=[];call_total=0
 for root in roots:
  need(struct.unpack('<I',physical(root['slot'],4))[0]==root['entry']and 0x5e0000<=root['slot']<0x5e0000+144*4,'Genuine original initializer table slot')
  registration=root['registration'];push=instructions[registration['push_pc']];call=instructions[registration['CALL_pc']]
  need(push['mnemonic']=='push'and push['decoded_operands'][0]['value']==registration['callback']and call['mnemonic']=='call'and call['decoded_operands'][0]['value']==0x5ac140 and call['pc']+call['width']==registration['return_pc'],'Literal callback registration identity and source call frame')
  closure={r['pc']:instructions[r['pc']]for entry in root['normal']['local_entries']for r in graphs[str(entry)]['instructions']}
  calls=[r for r in closure.values()if r['mnemonic']=='call'and r['decoded_operands'][0].get('value')==0x5abd26]
  call_total+=len(calls);stores=[];stack_reads=[]
  for row in closure.values():
   for index in row['explicit_memory_writes']:
    operand=row['decoded_operands'][index]
    if any(term['register']in('esp','ebp')for term in operand['terms']):continue
    stores.append(dict(PC=row['pc'],bytes=row['width'],source_bytes=row['bytes_hex'],width_bits=operand['bits'],operand=operand,value_operand=row['decoded_operands'][1]if len(row['decoded_operands'])>1 else None))
   for index in row['explicit_memory_reads']:
    operand=row['decoded_operands'][index]
    if operand['bits']==8 and any(term['register']=='esp'for term in operand['terms']):stack_reads.append(dict(PC=row['pc'],operand=operand,source_bytes=row['bytes_hex']))
  for obj in root['objects']:
   row=instructions[obj['pc']]
   need(any(value.get('value')==obj['address']or value['kind']=='memory'and not value['terms']and value['displacement']==obj['address'] for value in row['decoded_operands']),'Every object designation comes from exact literal memory/immediate operand')
  family.append(dict(root=root['entry'],slot=root['slot'],objects=root['objects'],literal_allocation_calls=[dict(PC=r['pc'],return_PC=r['pc']+r['width'],target=0x5abd26)for r in sorted(calls,key=lambda r:r['pc'])],nonstack_literal_stores=sorted(stores,key=lambda r:r['PC']),stack_byte_reads=sorted(stack_reads,key=lambda r:r['PC']),registration=registration))
 need(call_total==35,'Current physical per-root closure has 35 allocation sites; execution count still requires source path and actual calls')
 first=next(r for r in family if r['root']==0x40ffe0)
 for pc in(0x4c7b8a,0x4c7b91,0x4c7b93,0x4c7b99):need(pc in {v['PC']for v in first['nonstack_literal_stores']},'Exact first-root source store control frontiers')
 out.mkdir(parents=True);path=out/'root-call-store-contracts.json';path.write_text(json.dumps(dict(schema='mw34-mfc-independent-game-static-contracts-v1',roots=family,actual_allocation_count_not_inferred_from_root_count=True),indent=2)+'\n');pin(path);pin(__file__)
 report=dict(passed=True,scope='Independent original physical 547-row/root table/register-or-inline object/callback/store review only',family_roots=32,physical_literal_rows=547,body_entries=69,new_game_bodies=65,per_root_static_allocation_sites=35,multiple_allocation_roots=[r['root']for r in family if len(r['literal_allocation_calls'])>1],stack_byte_read_roots=sum(bool(r['stack_byte_reads'])for r in family),actual_allocations=None,game_object_bytes_from_API_volatile_stack_must_be_derived=True,after_alloc_first_owner_store=0x4c7b91,after_alloc_second_owner_store=0x4c7b93,first_pointer_publication_store=0x4c7b99,first_object_preallocation_byte_store=0x4c7b8a,original_executed=False,native_executed=False,initializer_credit=0,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),per_root_static_allocation_sites=35)))
if __name__=='__main__':main(sys.argv[1])
