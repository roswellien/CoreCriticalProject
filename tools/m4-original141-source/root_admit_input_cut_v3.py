"""ROOT physically rehashes reviewed input cut before one ordinary reader."""
from pathlib import Path
import hashlib,json,sys,time
R=Path(__file__).resolve().parents[2]
def main(name):
 started=time.monotonic();out=R/'reports/m4-original141-source'/name;assert not out.exists();files={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json'
  with p.open('rb')as f:v=hashlib.file_digest(f,'sha256').hexdigest()
  assert h is None or h==v,(str(p),h,v)
  assert str(p)not in files or files[str(p)]==v
  files[str(p)]=v;return p
 base=R/'reports/m4-original141-source/input-materialization-preparation-r3'
 recipe=json.loads(pin(base/'report.json','00a83cb5e819ab4469e4816fc7aab60b5e88f4307b6a24c481cabc078913b8c4').read_bytes())
 for p,h in recipe['files'].items():pin(p,h)
 required=json.loads(pin(base/'required-ordinary-files.json','7bdf60c3a0834533a5f4c39e15ca188ce78573cc60abf327c194ee05b5c92a98').read_bytes());assert len(required)==20
 for p,h in required.items():pin(p,h)
 validation=json.loads(pin(R/'reports/m4-original141/root-capture-validation-r3/report.json','e981f00f520ce83019bdb7c77fef740871de14f24c2e9aee0052293fcec1a58c').read_bytes())
 assert validation['passed']is True and validation['reader_closed']is True and validation['paired_export_readers_closed']is True and validation['counts']['phases']==846 and validation['initializer_credit']==0
 assert len(validation['paired_exports'])==1
 export=validation['paired_exports'][0]
 assert export['branch']=='original'and export['logical_files']==261543 and export['payload_bytes']==1540126431
 for field in ('index','payload'):
  assert required[export[field+'_path']]==export[field+'_sha256']==validation['files'][export[field+'_path']]
 for p,h in required.items():
  if Path(p).drive.upper()=='G:':assert p in (export['index_path'],export['payload_path'])
 pin(__file__);pin(sys.executable)
 for p,h in files.items():pin(p,h)
 out.mkdir();q=out/'report.json';q.write_text(json.dumps(dict(passed=True,independent_review=True,scope_identity='original141_current_input_materialization',validation_sha256='e981f00f520ce83019bdb7c77fef740871de14f24c2e9aee0052293fcec1a58c',actual_required_files=20,reader_opened=False,source_execution=False,worker_launched=False,initializer_credit=0,elapsed_seconds=time.monotonic()-started,files=files),indent=2)+'\n');print(hashlib.sha256(q.read_bytes()).hexdigest())
if __name__=='__main__':main(sys.argv[1])
