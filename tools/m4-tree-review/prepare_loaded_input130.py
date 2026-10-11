"""Fresh complete130 loaded input-page declaration; operand proof is separate."""
from pathlib import Path
import hashlib,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(name):
 out=R/'reports/m4-tree-review'/name;need(not out.exists(),'Fresh physical loaded-input declaration');out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();a=sha(p);need(h is None or a==h,'Physical current loaded input identity '+str(p));need(str(p)not in pins or pins[str(p)]==a,'Stable input');pins[str(p)]=a;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 op=R/'reports/m4-startup130-original/validation-r2/report.json'
 original=read(op,'91a3ca940214636b0d4c1a08c7ccf503a5c06127a3af4b26fdad50c876f1ffca')
 np=R/'reports/m4-formatting-native/preparation-r19/report.json'
 native=read(np,'1f704ba8254433b9ae7387a53322c33b4db536b99eb79363ff71e54169cb65f3')
 jp=R/'reports/m4-joint-startup130/preparation-r2/report.json'
 joint=read(jp,'060094c0019760a1095d60ee39a73ea7193a060a332bc67db9aae628c128857c')
 need(original['passed'] and original['original_executed'] and native['passed'] and joint['passed'],'Genuine current original and frozen corrected native input receipts')
 need(joint['native_preparation_sha256']==sha(np),'Current broad preparation binds corrected19')
 obp=op.parent/'post-DllMain-78145000-page.bin';nbp=Path(native['loaded_input_page'])
 ob=pin(obp,original['files'][str(obp.resolve())]).read_bytes();nb=pin(nbp,native['loaded_input_page_sha256']).read_bytes()
 need(len(ob)==len(nb)==4096,'Both entire physically authenticated RW bootstrap input pages')
 loader=read(native['loaded_original_bootstrap_report'],native['loaded_original_bootstrap_sha256'])
 need(loader['passed'] and loader['files'][str(nbp.resolve())]==sha(nbp),'Native whole input is exact genuine original loaded bootstrap output')
 differences=[dict(offset=i,address=0x78145000+i,original=x,native=y) for i,(x,y) in enumerate(zip(ob,nb)) if x!=y]
 fields=sorted({r['offset']&~3 for r in differences})
 dwords=[dict(offset=i,address=0x78145000+i,original_DWORD=struct.unpack_from('<I',ob,i)[0],native_DWORD=struct.unpack_from('<I',nb,i)[0],original_bytes=ob[i:i+4].hex(),native_bytes=nb[i:i+4].hex(),differing_byte_offsets=[r['offset'] for r in differences if i<=r['offset']<i+4]) for i in fields]
 need(ob[0x640:0x658]==nb[0x640:0x658] and ob[0x658:0x65c]==nb[0x658:0x65c]==struct.pack('<I',2),'Exact sourceCS24/state2 typed input bytes')
 domain={r['offset'] for r in differences};need(not(domain & set(range(0x640,0x65c))),'No differing byte in declared CS24/state2 input scope')
 artifact=out/'input-domain.json';artifact.write_text(json.dumps(dict(base=0x78145000,bytes=4096,whole_original_hex=ob.hex(),whole_native_hex=nb.hex(),differences=differences,differing_DWORDs=dwords,typed_CS24_hex=ob[0x640:0x658].hex(),typed_state2_bytes=ob[0x658:0x65c].hex()),indent=2)+'\n');pin(artifact);pin(__file__)
 report=dict(passed=True,scope='Fresh physical current130 complete loaded RW input-page declaration and exact finite byte/DWORD difference; selected source/API disjointness and allphase endpoint carry are separate',original_validation_sha256=sha(op),native_preparation_sha256=sha(np),broad_preparation_sha256=sha(jp),counts=dict(whole_bootstrap_input_pages=2,whole_input_bytes=8192,explicit_loaded_input_difference_bytes=len(differences),explicit_loaded_input_difference_DWORDs=len(dwords),identical_source_CS24_bytes=24,identical_source_state2_bytes=4),whole_original_input_page=str(obp.resolve()),whole_original_input_page_sha256=sha(obp),whole_native_input_page=str(nbp.resolve()),whole_native_input_page_sha256=sha(nbp),input_domain_path=str(artifact.resolve()),input_domain_sha256=sha(artifact),prior125_difference_list_reused=False,selected_operand_disjointness_claimed=False,actual_current_native_execution_claimed=False,paired_endpoint_capture_reads=0,endpoint_carry_acceptance=False,whole_page_mask=False,opaque_pointer_target_equivalence=False,native_DllMain_credit=False,initializer_credit=0,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),counts=report['counts'])))
if __name__=='__main__':main(sys.argv[1])
