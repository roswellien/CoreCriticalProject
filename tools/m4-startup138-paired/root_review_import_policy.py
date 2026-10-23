"""Independent admission of finite CRT import identities; ordinary inputs only."""
from pathlib import Path
import hashlib, importlib.util, json, struct, sys, traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]

def sha(p):
 with Path(p).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main(name):
 out=ROOT/'reports/m4-startup138-paired'/name
 assert not out.exists();out.mkdir();pins={};passed=False;controls=0;relations=0
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower() not in ('.mwb','.mwi','.zip')
  actual=sha(p);assert h is None or h==actual
  assert str(p) not in pins or pins[str(p)]==actual
  pins[str(p)]=actual;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 try:
  proof=read(ROOT/'reports/m4-startup138-paired/CRT-import-cell-policy-r3/report.json','07a81409de7d5aae90945079dd4ce295ead37fd6b3ea1cac4e723e95792e10aa')
  assert proof['passed'] and proof['ordinary_readers_closed'] and proof['physical_named_cell_relations']==1728 and proof['forwarded_relations']==96
  inverse=read(ROOT/'reports/m4-startup138-paired/CRT-import-helper-inverse-r1/report.json','00459a1d5a888752145c1f10b2a14a90543f0fc0c75b74a98324c858b3b8911c')
  for report in (proof,inverse):
   for path,h in report['files'].items():pin(path,h)
  policy=pin(ROOT/'tools/m4-startup138-paired/crt_page_policy_v3.py','8d8cc4dc3b0626f1f13d522cd17c183b543d4eedb2d1d0fcf9332b7ebf41fec0')
  spec=importlib.util.spec_from_file_location('root_current_CRT_policy',policy);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  prior=read(ROOT/'reports/m4-startup138-paired/CRT-page-policy-r4/report.json','35fab86e1f2fe5199b69759cff6d995edd4a041ad40d9e99b8aece382c179f5e')
  domains=read(prior['domains_path'],prior['domains_sha256']);cases=read(proof['physical_import_cells_path'],proof['physical_import_cells_sha256'])
  assert [(r['level'],r['sequence'])for r in cases]==[(l,s)for l in ('O0','O2')for s in range(6)]
  def refused(action):
   nonlocal controls
   try:action()
   except (ValueError,KeyError,struct.error):controls+=1
   else:raise AssertionError('Policy failed to reject changed identity/carry')
  for domain,case in zip(domains,cases):
   assert (domain['level'],domain['sequence'])==(case['level'],case['sequence'])
   original={int(k):bytes.fromhex(v)for k,v in domain['original_inputs'].items()};native={int(k):bytes.fromhex(v)for k,v in domain['native_inputs'].items()}
   cells=case['physical_import_cells'];patches=domain['patches'];unused=domain['unused_input_offsets']
   assert len(cells)==144 and len(patches)==8
   instance=module.Policy(original,native,patches,unused,cells)
   declared=set()
   for row in cells:
    offset=row['offset'];assert 0<=offset<=4092 and row['physical_export_chain'][0]['name']==row['name']
    assert row['physical_export_chain'][0]['library']=='KERNEL32.DLL'
    if row['observer_shim']:
     patch=next(p for p in patches if p['pc']==0x7802e000+offset)
     assert patch['named_API']==row['name'] and int.from_bytes(bytes.fromhex(patch['original_hex']),'little')==row['original_real_target']
    else:assert row['original_real_target']==row['original_installed_target']
    for field in ('native_raw_thunk','original_installed_target'):
     wrong=[dict(r)for r in cells];wrong[cells.index(row)][field]^=1
     refused(lambda wrong=wrong:module.Policy(original,native,patches,unused,wrong))
    declared.update(range(offset,offset+4));relations+=1
   assert len(declared)==576
   for phase in (0,12,13,14,137):
    actual=bytearray(original[0x7802e000])
    if phase==13:
     for row in cells:
      if row['observer_shim']:struct.pack_into('<I',actual,row['offset'],row['original_real_target'])
    for side in ('before','after'):
     assert instance.page(phase,side,0x7802e000,bytes(actual),native[0x7802e000],[],[])==declared
     for address in (min(declared),next(i for i in range(4096)if i not in declared),4095):
      wrong=bytearray(native[0x7802e000]);wrong[address]^=1
      refused(lambda wrong=wrong:instance.page(phase,side,0x7802e000,bytes(actual),bytes(wrong),[],[]))
   for rows in (cells[:-1],cells+[cells[0]]):refused(lambda rows=rows:module.Policy(original,native,patches,unused,rows))
  for path,h in list(pins.items()):pin(path,h)
  pin(__file__);pin(sys.executable);assert relations==1728 and controls==3840;passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  result=dict(passed=passed,scope='Root complete policy/source read plus physical import lineage and exhaustive per-cell target mutation/carry adverses; no archives or complete comparer invocation',physical_import_relations=relations,negative_controls=controls,finite_144_import_cell_policy_reviewed=passed,full_paired_policy_reviewed=False,source_machine_executed=False,initializer_credit=0,files=pins)
  p=out/'report.json';p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(p),relations=relations,controls=controls)))
if __name__=='__main__':main(sys.argv[1])
