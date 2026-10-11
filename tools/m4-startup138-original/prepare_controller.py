"""Freeze the exact current full138 controller without starting a writer."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PREP='e3d4cf14f17132d4dcf08bbef503711820b2f095f0ec52aedff27d088ef8d3c2'
BUILD='748e6404963be6b5ef0a0aaeac80447023814ce46ff316962ea83a749b70ab69'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 out=R/'reports/m4-startup138-original'/name;need(not out.exists(),'Fresh controller preparation');files={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No archive reader');d=sha(p);need(h is None or d==h,'Exact current controller input '+str(p));need(str(p)not in files or files[str(p)]==d,'One physical identity');files[str(p)]=d;return p
 p=R/'reports/m4-startup138-original/preparation-r7/report.json';b=R/'reports/m4-startup138-original/build-r4/build.json'
 prep=json.loads(pin(p,PREP).read_bytes());build=json.loads(pin(b,BUILD).read_bytes());need(prep['passed']and build['passed']and build['preparation_sha256']==PREP,'Current exact build lineage')
 source=pin(R/'tools/m4-startup138-original/run.py').read_text();anchor='def main(build,digest,preflight,preflight_digest,name):\n'
 need(source.count(anchor)==1,'Exact inherited controller entry')
 source=source.replace(anchor,anchor+" if build.resolve()!=R/'reports/m4-startup138-original/build-r4/build.json' or digest!='"+BUILD+"':raise ValueError('Only the frozen current original138 build is admitted')\n")
 anchor=" if not b['passed']or not q['passed']or(b['roots'],b['phases'],b['record_bytes'])!=(138,828,356992):raise ValueError('Exact full138 current build and independent prelaunch required')\n"
 need(source.count(anchor)==1,'Exact build guard')
 source=source.replace(anchor,anchor+" if b['preparation_sha256']!='"+PREP+"':raise ValueError('Only exact final preparation7 is admitted')\n pin(R/'reports/m4-startup138-original/preparation-r7/report.json','"+PREP+"')\n")
 controller=R/'tools/m4-startup138-original/run_v2.py';need(not controller.exists(),'Additive controller only');controller.write_text(source);ast.parse(source)
 pin(controller);pin(build['worker'],build['worker_sha256']);pin(build['pack']);pin(b.parent/'pins.json')
 for path,d in json.loads((b.parent/'pins.json').read_bytes())['files'].items():pin(path,d)
 for path,d in prep['files'].items():pin(path,d)
 for path in('tools/m4-pipeline/stages_capture_storage.py','tools/m4-pipeline/paths_capture_storage.py','reports/m4-tree-review/capture-storage-r1/report.json'):pin(R/path)
 pin(__file__);pin(sys.executable);out.mkdir();copy=out/'controller.py';copy.write_bytes(controller.read_bytes());pin(copy)
 d=dict(passed=True,scope='Current full138 single-writer controller preparation only; independent current prelaunch and root slot admission required at execution',controller_path=str(controller),controller_sha256=sha(controller),preparation_path=str(p),preparation_sha256=PREP,build_path=str(b),build_sha256=BUILD,worker_path=build['worker'],worker_sha256=build['worker_sha256'],actual_worker_cwd='G:/Projects/MW34Recomp-Captures',capture_root='G:/Projects/MW34Recomp-Captures/reports/m4-startup138-original',planned_arguments=[str(b),BUILD,'CURRENT_REVIEW_PATH','CURRENT_REVIEW_SHA256','FRESH_EXECUTION_NAME'],current_prelaunch_pending=True,original_executed=False,archive_reader_opened=False,initializer_credit=0,files=files)
 q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),pins=len(files))))
if __name__=='__main__':main(sys.argv[1])
