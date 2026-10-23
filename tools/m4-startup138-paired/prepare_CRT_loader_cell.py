"""Exact retained lock25 descriptor typing; correct finite unused-data domain."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup138-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 def receipt(path,h):
  p=pin(R/path,h);g=json.loads(p.read_bytes());assert g['passed']
  for path,digest in g['files'].items():pin(path,digest)
  return p,g
 cp,cg=receipt('reports/m4-startup138-paired/CRT-page-policy-r4/report.json','35fab86e1f2fe5199b69759cff6d995edd4a041ad40d9e99b8aece382c179f5e');domains=json.loads(pin(cg['domains_path'],cg['domains_sha256']).read_bytes());mp,mg=receipt('reports/m4-startup138-paired/current-MFC-pair-domain-r1/report.json','4409cba2b0bfde4c9f1edc7850d44ab183cd94a4fae161ab1cdc43d643bf8179');mrows=json.loads(pin(mp.parent/'relations.json',mg['files'][str((mp.parent/'relations.json').resolve())]).read_bytes());ip,ig=receipt('reports/m4-startup138-paired/CRT-import-cell-policy-r3/report.json','07a81409de7d5aae90945079dd4ce295ead37fd6b3ea1cac4e723e95792e10aa');imports=json.loads(pin(ig['physical_import_cells_path'],ig['physical_import_cells_sha256']).read_bytes());fp,fg=receipt('reports/m4-startup138-paired/original-CRT-data-footprint-r3/report.json','c94284517f4aec9afd43edc5efd5b732dbbc35038ee79b075e0c952d736fc351');assert not fg['provider_full_CPU_executed']and fg['closed_successors'];helper=pin(R/'tools/m4-startup138-paired/crt_page_policy_v4.py');spec=importlib.util.spec_from_file_location('typedCRT',helper);P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P);controls=[]
 for domain in domains:
  row=next(r for r in mrows if r['level']==domain['level']and r['sequence']==domain['sequence']);module=next(r for r in row['whole_module_input_relations']if r['page']==0x78037000);assert set(range(0x8c,0x90))<=set(module['exact_typed_loader_cell_offsets']);a={int(k):bytes.fromhex(v)for k,v in domain['original_inputs'].items()};b={int(k):bytes.fromhex(v)for k,v in domain['native_inputs'].items()};av=struct.unpack_from('<I',a[0x78037000],0x8c)[0];bv=struct.unpack_from('<I',b[0x78037000],0x8c)[0];assert struct.unpack_from('<I',bytes.fromhex(module['original_initial_hex']),0x8c)[0]==av and struct.unpack_from('<I',bytes.fromhex(module['native_initial_hex']),0x8c)[0]==bv
  api=next(r for r in row['API_lifetimes']if r['original_source']['API']=='EnterCriticalSection');assert api['original_source']['args']==[av]and struct.unpack_from('<I',bytes.fromhex(api['native_literal']['frame64_hex']),4)[0]==bv;assert api['original_actual_entry']['CPU'][0]==25 and api['native_literal']['CPU_before'][0]==25;assert bv==0x33007000
  cells=[dict(offset=0x8c,role='initialized_lock25',original_target=av,native_target=bv,source_operand_PCs=[0x7800105c,0x7800106d,0x780012a4],retained_MFC_relation_report_sha256=sha(mp),whole_actual_original_CS24_hex=row['original_whole_balanced_CS24_hex'],full_original_provider_CPU_executed=False)];domain['typed_CRT_loader_cells']=cells;domain['unused_input_offsets']=[v for v in domain['unused_input_offsets']if v not in range(0x8c,0x90)];assert not set(range(0x8c,0x90))&set(domain['unused_input_offsets']);physical=next(r['physical_import_cells']for r in imports if r['level']==domain['level']and r['sequence']==domain['sequence']);policy=P.Policy(a,b,domain['patches'],domain['unused_input_offsets'],physical,cells)
  for label in('missing-lock25','wrong-original-lock25','wrong-native-lock25'):
   bad=[dict(v)for v in cells]
   if label=='missing-lock25':bad=[]
   elif label=='wrong-original-lock25':bad[0]['original_target']^=1
   else:bad[0]['native_target']^=1
   try:P.Policy(a,b,domain['patches'],domain['unused_input_offsets'],physical,bad)
   except ValueError:controls.append(dict(level=domain['level'],sequence=domain['sequence'],name=label,refused=True))
   else:raise AssertionError(label)
 assert len(domains)==12 and len(controls)==36;dp=out/'domains.json';dp.write_text(json.dumps(domains,indent=2)+'\n');pin(dp);pin(__file__);pin(sys.executable);q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Exact retained current MFC lock25 loaded-input pointer cell explicitly typed; four consumed bytes removed fromunused domain; all other wholeCRT carry and144import relations retained',domains_path=str(dp),domains_sha256=sha(dp),typed_lock25_cell_relations=12,negative_controls=controls,original_provider_static_footprint_sha256=sha(fp),complete_paired_policy_admitted=False,archive_reader_opened=False,raw_reader_opened=False,initializer_credit=0,files=pins),indent=2)+'\n');print(sha(q))
if __name__=='__main__':main(sys.argv[1])
