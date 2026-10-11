"""Add only the physically declared FS fields to the frozen103 raw audit."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 old=ROOT/'tools/m4-joint-startup103/paired_audit.py'
 text=old.read_text();pins={str(old):sha(old)}
 def replace(a,b):
  nonlocal text
  assert text.count(a)==1,a;text=text.replace(a,b)
 replace("out=ROOT/'reports/m4-joint-startup103-root'/name","out=ROOT/'reports/m4-joint-startup109-root'/name")
 text=text.replace('1236','1308').replace('paired103','paired109').replace('selected103','selected109')
 replace("contract=read(ROOT/'reports/m4-mfc-source/recovery-r4/instruction-contracts.json')", "contract=read(ROOT/'reports/m4-fs-source/recovery-r3/instruction-contracts.json')\n oldcontract=read(ROOT/'reports/m4-mfc-source/recovery-r4/instruction-contracts.json')")
 replace("need(len(order)==103,'Exact selected109 order')","need(len(order)==109,'Exact selected109 order')")
 replace("instructions={x['pc']:x for x in contract['instructions']}","instructions={x['pc']:x for x in oldcontract['instructions']}")
 replace("roots={x['entry']:x for x in contract['roots']}","roots={x['entry']:x for x in oldcontract['roots']}")
 replace("imports=read(ROOT/'reports/m4-mfc-source/original-preparation-r1/mfc-import-bindings.json')", """fsfields=read(ROOT/'reports/m4-fs-source/field-contracts-r1/report.json','c087385c8ed1ff9834dcd00dc8b9164124cd1189fafc2c4791c61ebbafd2704a')
 need(fsfields['passed'] and len(fsfields['pointer_fields'])==3 and len(fsfields['header_fields'])==1,'Exactly three FS DWORD fields and one BYTE field')
 fsinstructions={x['pc']:x for x in contract['instructions']}
 for field in fsfields['pointer_fields']:
  need(field['width']==4 and fsinstructions[field['write_PC']]['bytes_hex']==field['bytes_hex'],'Exact physical FS pointer-store bytes')
  need(field['field'] not in fields,'Distinct FS static pointer publication');fields[field['field']]=order[field['root']]
 need(len(fields)==58,'Exactly58 source pointer fields')
 newheader=fsfields['header_fields'][0]
 need((newheader['root'],newheader['field'],newheader['width'],newheader['read_PC'],newheader['write_PC'],newheader['actual_read_address'])==(0x4d4830,0x60b51c,1,0x4d4914,0x4d4922,0x200017eb),'Exact new literal header geometry')
 need(fsinstructions[newheader['read_PC']]['bytes_hex']==newheader['read_bytes'] and fsinstructions[newheader['write_PC']]['bytes_hex']==newheader['write_bytes'],'Exact new header read/write bytes')
 imports=read(ROOT/'reports/m4-mfc-source/original-preparation-r1/mfc-import-bindings.json')""")
 replace("sources=[row['original_source'],row['native_source']];a,b=sources", """sources=[row['original_source'],row['native_source']];a,b=sources
  if row.get('new_FS_local_byte_relation'):
   need(row['address']==0x60b51c,'Only one additional byte field')
   for source in sources:
    need((source['root'],source['field'],source['read_pc'],source['write_pc'],source['read_address'])==(0x4d4830,0x60b51c,0x4d4914,0x4d4922,0x200017eb),'Exact source byte PC/address relation')
    proof=source['provenance'];need(proof['kind'] in ('genuine_branch_BEFORE_stack_byte','carried_source_BEFORE_stack_byte') and proof['address']==source['read_address'] and proof['value']==source['value'] and proof['no_root_source_store_before_read'] is True,'Genuine branch BEFORE byte, no invented dominating store')
    need(len(source['branch_BEFORE_cpu'])==10 and 0<=source['value']<=255,'Genuine branch BEFORE CPU and full byte');counts['new_FS_BEFORE_stack_byte_proofs']+=1
   key=identity+(row['address'],);need(key not in header_fields,'Unique new header relation');header_fields[key]=(order[0x4d4830],a['value'],b['value']);continue""")
 replace("expected_headers=set(header_by_field)","expected_headers=set(header_by_field)|{0x60b51c}")
 replace("object_header_relations_per_sequence=len(expected_headers)","object_header_relations_per_sequence=len(expected_headers),new_FS_DWORD_fields=3,new_FS_BYTE_fields=1")
 out=ROOT/'tools/m4-joint-startup109/paired_audit.py';assert not out.exists();out.write_text(text);pins[str(out)]=sha(out);pins[str(Path(__file__).resolve())]=sha(__file__)
 report=ROOT/'reports/m4-joint-startup109-root/paired-audit-derivation-r1';assert not report.exists();report.mkdir()
 result=dict(passed=True,scope='Additive audit derivation only; exact raw109 observations still required',new_pointer_fields=3,new_byte_fields=1,comparison_masks_changed=False,initializer_credit=False,files=pins)
 (report/'report.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(passed=True,sha256=sha(report/'report.json'))))
if __name__=='__main__':main()
