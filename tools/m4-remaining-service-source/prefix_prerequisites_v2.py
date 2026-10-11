"""Pin observed13-prefix scalar inputs and unresolved constructor ownership gaps."""
from pathlib import Path
import hashlib,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-remaining-service-source'
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=B/name
 if out.exists():raise ValueError('Fresh scalar prerequisite receipt')
 pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p)
  if h is not None and h!=v:raise ValueError('Exact current bounded input '+str(p))
  if p.suffix=='.mwb':raise ValueError('No capture archives')
  pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
 current=read(R/'reports/m4-mfc1168-connected-original/validation-r1/report.json','0c768ff2d22a06d44e16175b511920422dceb94deb1482a98ee9c327e362d777')
 if not current['passed']or not current['reader_closed']:raise ValueError('Closed genuine chronological prefix')
 exports=read(R/'reports/m4-mfc1168-connected-original/validation-r1/retained-actual-inputs.json')
 prep=read(R/'reports/m4-startup130-original/preparation-r2/report.json','8664d889eee0b3d65453205dd969d4bd377ae6bf6ff1dd0ca7185b002ccbd814')
 source=read(B/'preparation-r2/report.json','e137cf7e923009c39de1ba3b6135e0e8ca5b43826f0ec993396f77bd82acc2c4')
 if not source['passed']:raise ValueError('Physical remaining source')
 instructions=read(B/'preparation-r2/instruction-contracts.json')['instructions']
 normal=read(B/'preparation-r2/normal-prerequisites.json')
 item=exports['phase/0/13.bin'];record=pin(item['path'],item['sha256']).read_bytes()
 if len(record)!=356992 or struct.unpack_from('<I',record,16)[0]!=0x5ae3e4:raise ValueError('Genuine after13roots before untouched MFC')
 def value(address,n=4):
  page=address&~4095;index=prep['observed_pages'].index(page);offset=2276+index*4096+(address&4095)
  if(address&4095)+n>4096:raise ValueError('Whole finite page extent')
  return record[offset:offset+n]
 observations=[]
 for address,role in((0x603fdc,'shared header pointer'),(0x72c508,'shared object-list pointer'),(0x72c2cc,'lookup tree pointer'),(0x5f2a48,'source identifier base')):
  if address&~4095 not in prep['observed_pages']:
   observations.append(dict(address=address,role=role,observed=False,actual_scalar_unavailable=True,required_new_BEFORE_page=address&~4095,value_supplied_to_execution=False));continue
  raw=value(address);observations.append(dict(address=address,role=role,observed_DWORD=int.from_bytes(raw,'little'),raw_hex=raw.hex(),source_endpoint='Current genuine13accepted-root prefix AFTER, before5AE3E4; new constructors have not run',predicted_value=False))
 allocations=[]
 for row in instructions:
  if row['mnemonic']=='call'and row['operands']=='0x5abd26':allocations.append(dict(CALL_pc=row['pc'],return_PC=row['pc']+row['width'],raw_bytes=row['bytes_hex'],request='Read true cdecl frame argument at each invocation; no static request supplied as observation',occurrence_identity='Dynamic CALL ordinal within current root, allocation return pointer and actual capacity',initial_capacity_bytes='Full actual backing before guest writes, including untouched tails'))
 plan=dict(roots=[0x4103f0,0x410440,0x459b40],sequence='Authentic existing13root prefix then4103F0 then410440 then459B40; preserve explicit bounded-order scope until full144physical chronology',root_frame=0x20001800,carried_scalar_observations=observations,required_new_domain=[
  'Whole current603FDC shared header actual capacity, sentinel/current links and each borrowed node/object edge before first new constructor',
  'Actual repeated MFC823/MFC825 entry/return CPU40/FX512/ENV28/frames; genuine initial and final whole allocation backings, HeapSize capacity, ordered publication/link stores and full cleanup',
  'Every current virtual58B183 slot+18 must join most recent source vptr store, actual current object/list role, raw readonly slot40A850 and true CALL/RET frame',
  'If72C508 is nonNULL, actual5733B0→5560C0 held EDI definition5733D0 must join both indirect CALL sites and current node graph',
  'Cold self-recursive56FEA0 excluded only if literal source from genuine newroot BEFORE proves it unreachable; otherwise repair and independently review recursive lift before integration',
  'Full repeated source FS records and actual source callback registrations; no predicted allocator/FS/virtual counts',
  'No native reuse of original heap virtual addresses until exact finite owned/borrowed role mappings and pointer-cell relations are proven'],physical_MFC823_source_sites=allocations,existing_shared_providers=normal['constructor_batch']['known_providers'],new_original_writer_prepared=False,new_original_executed=False,source_after_seed=False,initializer_credit=0)
 out.mkdir(parents=True);p=out/'constructor-prefix-plan.json';p.write_text(json.dumps(plan,indent=2)+'\n');pin(p);pin(__file__);pin(R/'tools/m4-remaining-service-source/derive_prefix_v2.py');pin(R/'tools/m4-remaining-service-source/prefix_prerequisites.py','c136f5a8a4d4e4849628814f2015eec569a3afc34f32ecb9b333dc46de285e06')
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Bounded actual13-prefix scalar prerequisites and source ownership gaps only; no newroot admission',counts=dict(observed_scalar_inputs=sum(not v.get('actual_scalar_unavailable',False)for v in observations),missing_actual_scalar_pages=sum(v.get('actual_scalar_unavailable',False)for v in observations),new_original_roots=0),actual_observed_scalar_inputs=observations,new_original_writer_prepared=False,new_original_executed=False,initializer_credit=0,reader_opened=False,files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),observations=observations)))
if __name__=='__main__':main(sys.argv[1])
