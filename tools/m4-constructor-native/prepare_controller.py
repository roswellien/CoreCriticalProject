"""Freeze the exact service5/fixture8 controller without starting workers."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PREP='fa3783ea0dd32723e8d2b7917d7847e5b1951408d699fc3d82e77af0364c404d'
BUILD='97d32f7dbf5003f3ec0c79d95b8cfa02729b099cf2f03288ff69a69f6be9efe4'
SERVICE='61d3107f4003741e07c9c31b3c9b0b9c3911563fc4370df71743ae63e0e3e761'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 out=R/'reports/m4-constructor-native'/name;need(not out.exists(),'Fresh controller preparation');files={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No archive reader');d=sha(p);need(h is None or d==h,'Exact current controller input '+str(p));need(str(p)not in files or files[str(p)]==d,'One physical identity');files[str(p)]=d;return p
 prep_path=R/'reports/m4-constructor-native/fixture-preparation-r4/report.json';build_path=R/'reports/m4-constructor-native/fixture-build-r8/build.json';service_path=R/'reports/m4-constructor-native/service-preparation-r5/report.json'
 p=json.loads(pin(prep_path,PREP).read_bytes());b=json.loads(pin(build_path,BUILD).read_bytes());s=json.loads(pin(service_path,SERVICE).read_bytes());need(p['passed']and b['passed']and s['passed']and b['preparation_sha256']==PREP and p['service_preparation_sha256']==SERVICE,'Exact service5/fixture8 lineage')
 source=pin(R/'tools/m4-constructor-native/run_fixture.py').read_text()
 for old,new in [('8eacf3dfadf4d69f420683ad5abee7bdc4db645516e720ecd422f7310ec5f56e',BUILD),('5507c72aef7bcf8afdd7c2b6fe3a906f3c65da58e69cc555f0671670cf289ad9',PREP),('fixture-build-r7/build.json','fixture-build-r8/build.json'),('fixture-preparation-r3/report.json','fixture-preparation-r4/report.json')]:
  need(source.count(old)==1,'Exact previous controller binding');source=source.replace(old,new)
 # A whole-linked preflight must explicitly pin the physical workers, not just
 # metadata from their build report. No preflight is guessed at preparation.
 anchor="  for q,h in b['files'].items():pin(q,h)\n";need(source.count(anchor)==1,'Exact controller physical guard')
 source=source.replace(anchor,"  need(a['files'].get(str((R/'reports/m4-constructor-native/fixture-build-r8/build.json').resolve()))==BUILD and a['files'].get(str((R/'reports/m4-constructor-native/fixture-preparation-r4/report.json').resolve()))==PREP,'Current preflight physically binds fixture8')\n  for level in('O0','O2'):need(a['files'].get(str(Path(b['workers'][level]['path']).resolve()))==b['workers'][level]['sha256'],'Current preflight physically binds each worker')\n  for q,h in a['files'].items():pin(q,h)\n"+anchor)
 controller=R/'tools/m4-constructor-native/run_fixture_v2.py';need(not controller.exists(),'Additive controller only');controller.write_text(source);ast.parse(source);pin(controller)
 for receipt in(p,b,s):
  for path,d in receipt['files'].items():pin(path,d)
 for level in('O0','O2'):pin(b['workers'][level]['path'],b['workers'][level]['sha256'])
 pin(R/'tools/m4-pipeline/stages.py');pin(__file__);pin(sys.executable);out.mkdir();copy=out/'controller.py';copy.write_bytes(controller.read_bytes());pin(copy)
 d=dict(passed=True,scope='Current constructor37 service5/fixture8 two-level controller preparation only; independent current whole-linked admission and root slot required',controller_path=str(controller),controller_sha256=sha(controller),preparation_path=str(prep_path),preparation_sha256=PREP,build_path=str(build_path),build_sha256=BUILD,service_preparation_path=str(service_path),service_preparation_sha256=SERVICE,workers={l:{'path':b['workers'][l]['path'],'sha256':b['workers'][l]['sha256']}for l in('O0','O2')},planned_arguments=['CURRENT_REVIEW_PATH','CURRENT_REVIEW_SHA256','FRESH_EXECUTION_NAME'],current_prelaunch_pending=True,native_executed=False,archive_reader_opened=False,initializer_credit=0,files=files)
 q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),pins=len(files))))
if __name__=='__main__':main(sys.argv[1])
