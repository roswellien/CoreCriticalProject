"""Root admission of exact finite141 allocation cap and current controllers."""
from pathlib import Path
import hashlib,json,importlib.util,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-startup141-root/budget-root-admission-r1';assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or h==v;assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def read(p,h):
  g=json.loads(pin(p,h).read_bytes());assert g['passed']
  for q,v in g['files'].items():pin(q,v)
  return g
 a=read(R/'reports/m4-138-validation-review/full141-prelaunch-r2/report.json','207e37dcafd10b62886ee8cd22dd3ef82962e029c9d40d1d1129efab41e5426f')
 source=read(R/'reports/m4-138-validation-review/full141-budget-source-review-r1/report.json','cf34cc3dfb0b66d0031f4c99755baa1f4ae286a0a5791946460faf6437ae8029')
 controllers=read(R/'reports/m4-138-validation-review/full141-budget-controller-preparation-r1/report.json','e2e8d4f94e7d6f68c0f2b82228446e74e80028a2f7a289d783b9988c8ba97e4c')
 assert a['build_sha256']=='ba1f699354fc2a14eb5dcc3bbfa4497e9ceb4ce01786e75cd95430f6c58de1bc'and a['preparation_sha256']=='98b3f726249ef233ccdc63855cd5c735aa2ff01cc8717494b686bec34dafb46e'
 budget=source['budget_contract'];assert budget['new_live_cap']==budget['old_live_cap']+6==98 and budget['actual_failed_summary'][14]==93
 rows=budget['literal54_birth_proofs'];assert len(rows)==54 and {(v['branch'],v['sequence'],v['root'])for v in rows}=={(b,s,r)for b in('original','O0','O2')for s in range(6)for r in(0x4103f0,0x410440,0x459b40)}
 assert all(v['genuine_HeapAlloc_births']==2 and v['no_constructor_owner_retirements']for v in rows)
 parent=R/'reports/m4-startup141-runway/service-preparation-r1';child=R/'reports/m4-startup141-runway/service-preparation-r2';unchanged=0
 for p in parent.iterdir():
  if not p.is_file()or p.name=='report.json':continue
  q=child/p.name;aa=pin(p).read_bytes();bb=pin(q).read_bytes()
  if p.name=='locale_batch_operations.inc':assert aa.count(b'live_allocations()>92')==bb.count(b'live_allocations()>98')==1 and bb.replace(b'live_allocations()>98',b'live_allocations()>92')==aa
  else:assert aa==bb;unchanged+=1
 for key,changes in controllers['exact_inverse_changes'].items():
  p=pin(R/'tools/m4-startup141-root'/key);current=p.read_text();old=current
  for aa,bb in reversed(changes):assert bb in old;old=old.replace(bb,aa)
  before='run_v1.py'if key=='run_v2.py'else'validate_v2.py';assert old==pin(p.with_name(before)).read_text()
 p=pin(R/'tools/m4-startup141-root/allocation_budget_v1.py');s=importlib.util.spec_from_file_location('root_budget',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);controls=[]
 normal=[0]*32;normal[0]=1;normal[10]=98;normal[18]=200000;m.registry_summary(normal)
 for field,value in((10,99),(12,4097),(13,200001),(18,199999)):
  bad=normal[:];bad[field]=value
  try:m.registry_summary(bad)
  except ValueError:controls.append(dict(schema='registry',field=field,value=value,refused=True))
  else:raise AssertionError('Invalid resource extent admitted')
 normal=[0]*32;normal[0]=1;normal[14]=98;m.locale_summary(normal)
 for field,value in((14,99),(16,200001),(18,4097),(19,33)):
  bad=normal[:];bad[field]=value
  try:m.locale_summary(bad)
  except ValueError:controls.append(dict(schema='locale',field=field,value=value,refused=True))
  else:raise AssertionError('Invalid resource extent admitted')
 for q,h in pins.items():assert sha(q)==h
 pin(__file__);pin(sys.executable);out.mkdir();q=out/'report.json';q.write_text(json.dumps(dict(passed=True,independent_review=True,scope='Actual failed141 live93 plus literal54 sixbirth budget and exact linked/current controller admission; capture validation and acceptance separate',whole_unchanged_service_units=unchanged,finite_live_cap=98,other_caps_unchanged=True,exact_controller_inverses=True,negative_controls=controls,all_workers_to_be_launched=2,archive_reader_opened=False,initializer_credit=0,current141_acceptance=False,files=pins),indent=2)+'\n');print(sha(q))
if __name__=='__main__':main()
