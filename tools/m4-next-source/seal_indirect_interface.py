"""Physical finite interface for absolute cells and source-derived virtual slot."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-next-source'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=BASE/name;assert not out.exists();out.mkdir();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 sp=importlib.util.spec_from_file_location('physical120_indirect_PE',pin(ROOT/'tools/analysis/pe.py'));P=importlib.util.module_from_spec(sp);sp.loader.exec_module(P)
 image=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');pe=P.PEImage(image.read_bytes())
 contract=json.loads(pin(BASE/'recovery-r1/instruction-contracts.json','a58e31641f42e8e37c1d66bad5e41dd57854b82a7a00bd86a02b1bc85aec9108').read_bytes());rows={r['pc']:r for r in contract['instructions']}
 inputs=json.loads(pin(BASE/'recovery-r1/indirect-call-inputs.json','a329e3988a4d77137e1270d9606c2c65f8b6aee95d1f04fb5928eb9a28a90d9a').read_bytes())
 def raw(address,n):
  off,section=pe.rva_range(address-pe.image_base,n);return pe.data[off:off+n],off,section
 proofs=[]
 for row in inputs:
  cell,offset,section=raw(row['slot'],4);assert struct.unpack('<I',cell)[0]==row['target'];call=rows[row['CALL_pc']];assert call['mnemonic']=='call';physical,po,_=raw(call['pc'],call['width']);assert physical.hex()==call['bytes_hex'];assert row['return_pc']==call['pc']+call['width'];virtual=row['CALL_pc']==0x59ff6e
  if virtual:
   assert call['operands']=='dword ptr [edx + 0x1c]' and row['slot']==0x5bc0e0+0x1c
   assert rows[0x59ff64]['operands']=='edx, dword ptr [ecx]' and rows[0x59fdb3]['operands']=='dword ptr [esi], 0x5bc0e0'
  else:
   assert call['operands']==f'dword ptr [{hex(row["slot"])}]'
  if row.get('source_vtable'):
   assert row['source_vtable']==0x5bc0e0 and row['dominating_vtable_store_PC']==0x59fdb3
  if row['target']==0x59ff80:
   assert row['argument']==0 and rows[0x59ff80]['operands']=='eax, dword ptr [esp + 4]' and rows[0x59ff84]['mnemonic']=='test' and rows[0x59ff86]['decoded_operands'][0]['value']==0x59ffa1
  assert rows[{0x40e820:0x40e827,0x59ff00:0x59ff0d,0x59ff80:0x59ffa1}[row['target']]]['mnemonic']=='ret'
  proofs.append(dict(row,cell_file_offset=offset,cell_raw_hex=cell.hex(),physical_CALL_file_offset=po,physical_CALL_bytes=physical.hex(),derived_instance_slot=virtual,absolute_cell=not virtual,absolute_publication_metadata_only=row['CALL_pc']==0x59fdc5,normal_nonzero_pointer_path_admitted=False))
 assert len(proofs)==6 and len({r['root']for r in proofs})==4
 pin(__file__);(out/'interfaces.json').write_text(json.dumps(proofs,indent=2)+'\n');pin(out/'interfaces.json')
 r=dict(passed=True,scope='Six exact rooted physical game CALL interfaces and raw target DWORDs: four absolute-cell calls, two instance-derived slot calls; source vptr publication distinct from actual instance read; zero pointer normal constructor path only, no execution/admission.',root_count=4,rooted_calls=6,absolute_cell_calls=4,actual_instance_slot_calls=2,new_provider_calls=0,new_allocations=0,new_string_copies=0,nonzero_pointer_path_admitted=False,files=pins);(out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
