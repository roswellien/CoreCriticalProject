"""Current full138 original admission binding, preparation only."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 out=R/'reports/m4-startup138-original'/name;need(not out.exists(),'Fresh admission configuration');files={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No archive reader');v=sha(p);need(h is None or h==v,'Current physical identity '+str(p));need(str(p)not in files or files[str(p)]==v,'One identity');files[str(p)]=v;return p
 cp=R/'reports/m4-startup138-original/controller-preparation-r1/report.json';rp=R/'reports/m4-tree-review/original138-prelaunch-r5/report.json'
 c=json.loads(pin(cp,'b598077c08d1355cf7210233ff7e32eecc36b634230ac6a8596622ff1899bc90').read_bytes());r=json.loads(pin(rp,'efaa5d25802440f8cd47092d16a0368084cf5ea744d8c2cda5c826522f96122a').read_bytes())
 need(c['passed']and r['passed']and r['files'].get(str(Path(c['build_path']).resolve()))==c['build_sha256']and r['files'].get(str(Path(c['worker_path']).resolve()))==c['worker_sha256'],'Whole current linked worker/build physically admitted')
 for v in(c,r):
  for p,h in v['files'].items():pin(p,h)
 ordinary=R/'reports/m4-tree-review/original138-source-r2/report.json';o=json.loads(pin(ordinary,'341f656ac7c4d45ca4f9574d1884a2783ddc070779269878fea22091e43137e2').read_bytes());need(o['passed'],'Current ordinary source/dependency gate')
 for p,h in o['files'].items():pin(p,h)
 pin(__file__);out.mkdir();d=dict(passed=True,scope='Direct current full138 controller/current machine and ordinary source admission; root scheduling required separately',controller_path=c['controller_path'],controller_sha256=c['controller_sha256'],controller_preparation_sha256=sha(cp),preparation_path=c['preparation_path'],preparation_sha256=c['preparation_sha256'],build_path=c['build_path'],build_sha256=c['build_sha256'],preflight_path=str(rp),preflight_sha256=sha(rp),ordinary_source_review_sha256=sha(ordinary),planned_arguments=[c['build_path'],c['build_sha256'],str(rp),sha(rp),'FRESH_EXECUTION_NAME'],actual_worker_cwd=c['actual_worker_cwd'],capture_root=c['capture_root'],root_slot_still_required=True,original_executed=False,archive_reader_opened=False,initializer_credit=0,files=files)
 q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),pins=len(files))))
if __name__=='__main__':main(sys.argv[1])
