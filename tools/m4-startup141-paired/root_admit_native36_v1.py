"""Independent ROOT cold source/projector admission; no model or reader."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2]

def main(name):
 out=R/'reports/m4-startup141-paired'/name;assert not out.exists();files={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip','.pyc')and p.name!='transport.json'
  assert p.is_relative_to(R)or p.is_relative_to(Path(sys.prefix).resolve())or p.is_relative_to(Path('C:/Program Files/Microsoft Visual Studio/18/Community'))or p.is_relative_to(Path('C:/Program Files (x86)/Windows Kits/10'))or p in{Path('C:/Windows/SysWOW64')/n for n in('kernel32.dll','ntdll.dll','apphelp.dll','gdi32.dll','user32.dll')}
  with p.open('rb')as f:v=hashlib.file_digest(f,'sha256').hexdigest()
  assert h is None or h==v;assert files.setdefault(str(p),v)==v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 base=R/'reports/m4-startup141-paired';Csha='a5c92bfb81bcc981d1fe8adf532d4c6876f1a5eb9b28091f70e81f6f7aac37e0'
 closure=read(base/'native-constructor-projector-closure-r1/report.json','0d9c9dd9e7485c04becfe677ea672726f20d03e723940cfcd3982dd0318fb36c')
 assert closure['prepared_only']and not closure['source_execution']and not closure['ordinary_export_reader_opened']and closure['configuration_sha256']==Csha
 for p,h in closure['files'].items():pin(p,h)
 for p,h in read(closure['required_ordinary_files'],closure['required_ordinary_files_sha256']).items():pin(p,h)
 def inverse(parent,child,deltas):
  a=pin(parent).read_text();b=pin(child).read_text().splitlines(True)
  for d in deltas:assert ''.join(b[d['child_start']:d['child_stop']])==d['child']
  for d in reversed(deltas):b[d['child_start']:d['child_stop']]=d['parent'].splitlines(True)
  assert ''.join(b)==a;ast.parse(pin(child).read_text())
 for stage in(1,3,4):
  q=read(base/f'native-constructor-source-preparation-r{stage}/report.json')
  assert q['prepared_only']and not q['source_execution']and not q['imports_executed']
  for p,h in q['files'].items():pin(p,h)
  if stage==1:parent=R/'tools/m4-138-validation-review/constructor_native36_source_v6.py'
  else:parent=R/f'tools/m4-startup141-paired/constructor_native36_source141_v{stage-1}.py'
  child=R/f'tools/m4-startup141-paired/constructor_native36_source141_v{stage}.py'
  inverse(parent,child,read(base/f'native-constructor-source-preparation-r{stage}/inverse.json'))
 q=read(base/'native-constructor-source-preparation-r2/report.json');assert q['prepared_only']and not q['source_execution']
 for p,h in q['files'].items():pin(p,h)
 for v in q['whole_inverse_files']:inverse(v['parent'],v['child'],v['deltas'])
 C=read(base/'native-constructor-source-preparation-r1/configuration.json',Csha)
 N=read(C['native_source']['path'],C['native_source']['sha256']);assert N['passed']and N['reader_closed']and N['complete_persistent141_constructors']and N['counts']['literal_constructor_roots']==36
 selected={x['branch']for x in read(base/'native-constructor-source-preparation-r3/report.json')['current_native_only_exports']};assert selected=={'O0','O2'}
 ctor=read(C['current_original18']['path'],C['current_original18']['sha256']);assert ctor['passed']and len(ctor['cases'])==18 and not ctor['source_AFTER_seed']
 contract=read(base/'native-constructor-source-preparation-r4/projector-contract.json');assert contract['source_State_bytes']==3504 and contract['source_x87_offset']==2768 and contract['source_sw_offset']==2736 and not contract['hardware_ENV_equality_from_FX_claim']
 for p,h in contract['files'].items():pin(p,h)
 assert contract['native_build_sha256']==N['executed_lineage']['build_sha256']and contract['joint_preparation_sha256']==N['executed_lineage']['joint_preparation_sha256']
 tests=read(base/'root-ENV-projector-controls-r1/report.json','6dd12762c1b14991b073b713b7915be19f8f812292249a87f7ffc6eb58e88057');assert tests['passed']and tests['independent_ROOT_review']and len(tests['tests'])==25 and not tests['source_machine_executed']and not tests['hardware_ENV_from_FX_inferred']
 for p,h in tests['files'].items():pin(p,h)
 pin(__file__);pin(sys.executable)
 for p,h in list(files.items()):pin(p,h)
 out.mkdir();q=out/'report.json';q.write_text(json.dumps(dict(passed=True,independent_review=True,scope_identity='native141_constructor36_own_source',configuration_sha256=Csha,complete_source_parent_inverses_reviewed=True,physical_computed_State_ENV_projector_reviewed=True,pure_projector_controls=25,source_execution=False,reader_opened=False,native_worker_launched=False,previous_checkpoint_nonphase_owner_carry_proven=False,complete_constructor_pair_gate=False,accepted_function_credit=0,files=files),indent=2)+'\n')
 with q.open('rb')as f:print(hashlib.file_digest(f,'sha256').hexdigest())
if __name__=='__main__':main(sys.argv[1])
