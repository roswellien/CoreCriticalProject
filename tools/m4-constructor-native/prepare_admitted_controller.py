"""Pin current whole-link admission and its exact frozen controller, no run."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 out=R/'reports/m4-constructor-native'/name;need(not out.exists(),'Fresh admitted-controller receipt');files={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No archive reader');v=sha(p);need(h is None or h==v,'Current physical identity '+str(p));need(str(p)not in files or files[str(p)]==v,'No conflicting identity');files[str(p)]=v;return p
 cpath=R/'reports/m4-constructor-native/controller-preparation-r3/report.json';rpath=R/'reports/m4-tree-review/constructor-native37-prelaunch-r4/report.json'
 c=json.loads(pin(cpath,'021d6f0dd5161b3b5d5dc53b02f1669fd0846fafcfa12cdd6a25fe3410366498').read_bytes());r=json.loads(pin(rpath,'e6784852257c7ad30d26e8675735e5cd52db5857074a0b03e2e583408048f7ea').read_bytes())
 need(c['passed']and r['passed']and r['build_sha256']==c['build_sha256']and r['preparation_sha256']==c['preparation_sha256'],'Exact current whole-linked controller admission')
 for receipt in(c,r):
  for p,h in receipt['files'].items():pin(p,h)
 for l,w in c['workers'].items():need(r['files'].get(str(Path(w['path']).resolve()))==w['sha256'],'Every actual current final worker physically reviewed');pin(w['path'],w['sha256'])
 pin(__file__);out.mkdir();d=dict(passed=True,scope='Exact current constructor37 controller and independent whole-linked machine admission; scheduling remains root-owned',controller_path=c['controller_path'],controller_sha256=c['controller_sha256'],controller_preparation_sha256=sha(cpath),preflight_path=str(rpath),preflight_sha256=sha(rpath),build_sha256=c['build_sha256'],preparation_sha256=c['preparation_sha256'],planned_arguments=[str(rpath),sha(rpath),'FRESH_EXECUTION_NAME'],workers=c['workers'],root_slot_still_required=True,native_executed=False,archive_reader_opened=False,initializer_credit=0,files=files)
 q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),pins=len(files))))
if __name__=='__main__':main(sys.argv[1])
