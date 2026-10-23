"""Seal the root-reviewed exact current comparer and finite input domains."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(caller_path,caller_sha):
 out=R/'reports/m4-startup138-paired/root-policy-admission-r2';assert not out.exists()
 pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json'
  v=sha(p);assert h is None or v==h;assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def read(p,h=None):
  g=json.loads(pin(p,h).read_bytes());assert g['passed']
  for q,v in g.get('files',{}).items():pin(q,v)
  return g
 caller=read(caller_path,caller_sha)
 assert caller['complete_selected138_original_provider_input_footprint_reviewed'] is True
 prep=read(R/'reports/m4-startup138-paired/comparer-preparation-r6/report.json','e44982fcb1cdc7938c89ea0c65ce3aff66b9ceeb13d01931c0f87b8db638ecc6')
 for p,h in [('CRT-import-independent-r1','3ae59486055ce3d0ad21ff48075248fe3544d4c2ef3dbbe7d82181874a0c36a3'),('CRT-lock25-domain-r1','974053dfbd2dc7b4808e1f09b14efcdc57a968e29c0a7539d2e99fb8cd61eae1'),('CRT-lock25-helper-inverse-r1','a57cfd22aff563d7749534e808421fcca9a4a5ba976572be91a795e7626e1398')]:read(R/f'reports/m4-startup138-paired/{p}/report.json',h)
 read(R/'reports/m4-startup138-paired/CRT-lock13-domain-r2/report.json','6bf6c226e40dea50912fb126eaaa97715af4aadd436189114ec292f599a161eb')
 read(R/'reports/m4-startup138-paired/CRT-lock13-helper-preflight-r2/report.json','3a34fb5c22458cd670903c89f9e4cb60af25a967aa2b5869f95a8f53845d196c')
 path=pin(R/'tools/m4-startup138-paired/preflight_comparer_v7.py')
 spec=importlib.util.spec_from_file_location('root_preflight',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 m.main('root-definition-preflight-r2')
 pre=read(R/'reports/m4-startup138-paired/root-definition-preflight-r2/report.json')
 assert pre['all48_hunks_exactly_invert']and pre['accepted131_CPU_FX_ENV_rules_byte_for_byte_retained']and len(pre['physical_import_negative_controls'])==96
 ps=pin(R/'tools/m4-startup138-paired/crt_page_policy_v5.py');ns={};exec(compile(ps.read_text(),str(ps),'exec'),ns)
 policy_path=pin(prep['policy_preparation'],prep['policy_preparation_sha256']);policy=json.loads(policy_path.read_bytes())
 domains=json.loads(pin(policy['CRT_page_source_domains_path'],policy['CRT_page_source_domains_sha256']).read_bytes())
 imports=json.loads(pin(policy['CRT_physical_import_cells_path'],policy['CRT_physical_import_cells_sha256']).read_bytes());controls=0
 for d in domains:
  a={int(k):bytes.fromhex(v)for k,v in d['original_inputs'].items()};b={int(k):bytes.fromhex(v)for k,v in d['native_inputs'].items()}
  cells=next(r['physical_import_cells']for r in imports if(r['level'],r['sequence'])==(d['level'],d['sequence']))
  p=ns['Policy'](a,b,d['patches'],d['unused_input_offsets'],cells,d['typed_CRT_loader_cells'],d['typed_CRT_lock13_objects'])
  assert not (set(range(0x8c,0x90))|set(range(0x130,0x148)))&set(d['unused_input_offsets'])
  for row in d['registry_fields']:
   phase=row['phase'];assert not row['AFTER_page_bytes_used_as_input']
   for side in('before','after'):
    aa=bytearray(a[0x78037000]);bb=bytearray(b[0x78037000]);struct.pack_into('<II',aa,0x888,row[side+'_original'][1],row[side+'_original'][0]);struct.pack_into('<II',bb,0x888,row[side+'_native'][1],row[side+'_native'][0])
    declared=p.page(phase,side,0x78037000,bytes(aa),bytes(bb),row[side+'_original'],row[side+'_native']);assert set(range(0x8c,0x90))<=declared
    for offset in(0x8c,0x888,0xfff):
     bad=bytearray(bb);bad[offset]^=1
     try:p.page(phase,side,0x78037000,bytes(aa),bytes(bad),row[side+'_original'],row[side+'_native'])
     except ValueError:controls+=1
     else:raise AssertionError('Changed whole carry accepted')
 assert controls==9936
 for q,h in pins.items():assert sha(q)==h
 pin(__file__);pin(sys.executable);out.mkdir()
 receipt=dict(passed=True,independent_review=True,current138_complete_typed_domain_policy_reviewed=True,comparer_preparation_sha256=sha(R/'reports/m4-startup138-paired/comparer-preparation-r6/report.json'),policy=str(policy_path),policy_sha256=sha(policy_path),whole_data_carry_adverses=controls,caller_review_sha256=caller_sha,second_interpreter_execution=False,initializer_credit=0,files=pins)
 p=out/'report.json';p.write_text(json.dumps(receipt,indent=2)+'\n');print(sha(p))
if __name__=='__main__':main(*sys.argv[1:])
