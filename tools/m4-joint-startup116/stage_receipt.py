"""Expose completed actual worker stages while structural validation continues."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from stages import verify_stage
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(build,digest,execution,name):
 out=ROOT/'reports/m4-joint-startup116-root'/name;assert not out.exists();out.mkdir(parents=True);pins={};rows=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v,(p,h,v);pins[str(p)]=v;return p
 b=json.loads(pin(build,digest).read_bytes());assert b['passed'];prep=json.loads(pin(b['preparation'],b['preparation_sha256']).read_bytes());assert prep['passed']and len(prep['selected_order'])==116
 execution=Path(execution).resolve();assert execution.parent==ROOT/'reports/m4-joint-startup116-root'
 for level in('O0','O2'):
  stage=execution/(level+'-stage');sp=pin(stage/'stage.json');verify_stage(stage,sha(sp));s=json.loads(sp.read_bytes());assert s['passed']and s['status']=='success'
  pin(b['workers'][level]['path'],b['workers'][level]['sha256']);capture=pin(execution/level/'transport.json');transport=json.loads(capture.read_bytes());assert transport['passed']and transport['format']=='mw34.capture.direct.v1'
  rows.append(dict(level=level,stage=str(sp),stage_sha256=sha(sp),capture=str(capture),capture_sha256=sha(capture),elapsed_seconds=s['elapsed_seconds']))
 pin(__file__);pin(ROOT/'tools/m4-pipeline/stages.py')
 r=dict(passed=True,scope='Both actual frozen116 worker stages completed; structural/logical and semantic capture verification are separate required gates. Allows independent source consumers to overlap coordinator validation.',build_path=str(Path(build).resolve()),build_sha256=digest,levels=rows,native_executed=True,structural_capture_validation_pending=True,initializer_credit=False,whole_M4_complete=False,files=pins)
 (out/'report.json').write_text(json.dumps(r,indent=2)+'\n');(out/'pins.json').write_text(json.dumps(dict(files=pins|{str(out/'report.json'):sha(out/'report.json')}),indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'))))
if __name__=='__main__':main(*sys.argv[1:])
