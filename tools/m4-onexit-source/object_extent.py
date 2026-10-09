"""Actual original object-field addresses: one new page, no broad BSS inference."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=ROOT/'reports/m4-onexit-source'/name;assert not out.exists();out.mkdir(parents=True);files={}
 def pin(p,h=None):
  p=Path(p).absolute();v=sha(p);assert h is None or h==v;files[str(p)]=v;return p
 ref=pin(ROOT/'reports/m4-onexit-source/original-run-r4/report.json','da0fd8d0bd3c1c0b4e57bc7a8b33875d33020aa8ab240cfd5d011b247620fe0e');run=json.loads(ref.read_bytes());assert run['passed']
 prep=json.loads(pin(ROOT/'reports/m4-onexit-source/original-preparation-r7/report.json','91fdcc4522e5a4bb71ea44c207f878f707350328e5b4255981bb4765076d7744').read_bytes());interface=json.loads(pin(ROOT/'reports/m4-onexit-source/interface-r1/instruction-contracts.json').read_bytes());rows={r['pc']:r for r in interface['instructions']};assert rows[0x51af60]['decoded_operands'][1]['value']==0x638578 and rows[0x51b020]['operands']=='eax, ecx';fields=[]
 for pc in(0x51b024,0x51b02a,0x51b030,0x51b036,0x51b03c,0x51b042):
  r=rows[pc];op=r['decoded_operands'][0];assert op['terms']==[dict(register='eax',scale=1)]and op['bits']==32;fields.append(dict(pc=pc,address=0x638578+op['displacement'],value=8 if pc==0x51b042 else 0,bytes_hex=r['bytes_hex']))
 assert all(x['address']&~4095==0x63c000 for x in fields)
 p=pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py');spec=importlib.util.spec_from_file_location('extent_original_direct',p);d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d);cap=d.DirectSet(Path(run['original_capture']),pin)
 try:
  phase=next(i for i,r in enumerate(prep['order'])if r['entry']==0x51af50);page=prep['observed_pages'].index(0x63c000);checks=0
  for seq in range(6):
   r=cap.data(f'phase/{seq}/{phase}.bin');before=r[2276+page*4096:2276+(page+1)*4096];after=r[121060+page*4096:121060+(page+1)*4096];expected=bytearray(before)
   for f in fields:struct.pack_into('<I',expected,f['address']&4095,f['value']);checks+=1
   assert after==expected,'Complete newobjectfieldpage changes from original BEFORE and literal source'
 finally:cap.close()
 pin(Path(__file__));report=dict(passed=True,scope='Actualoriginal54 object638578 field-store page derivedfromoriginalBEFORE+literalrows',object=0x638578,maximum_source_field_end=0x485c,field_storage_start=0x63cdbc,field_storage_end=0x63cdd4,additional_observed_page=0x63c000,field_stores=fields,actualoriginalcases=6,field_checks=checks,complete_page_comparisons=6,fullinterveningobjectreadclaimed=False,native_execution=False,AFTER_machine_seed=False,files=files);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
