"""New reader measurement only against unchanged pilot and canonical archives."""
import json,sys,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path[:0]=[str(H),str(R/'tools/m4-pipeline')]
from capture_bundle import sha_file
from stages import run_stage,verify_stage
from manifests import verify_manifest
from validate_pilot_v3 import pin,need,native_build
def main(directory):
 out=Path(directory).resolve();need(out.parent==R/'reports/m4-capture-shared' and not out.exists(),'Fresh reader measurement');out.mkdir();files={};report={'passed':False,'game_executed':False,'format_adopted':False}
 try:
  native_build(files);pin(files,H/'reader_measure_v4.py');pin(files,H/'read_probe_v2.py');pin(files,R/'tools/m4-pipeline/stages.py')
  previous=pin(files,R/'reports/m4-capture-shared/benchmark-r2/report.json');before=json.loads(previous.read_bytes());cases={}
  for workload,level in [('authored','O0'),('authored','O2'),('retained','O2')]:
   key=workload+'-'+level;cases[key]={}
   for kind in ('canonical','shared'):
    manifest=pin(files,R/f'reports/m4-capture-shared/benchmark-r2/{key}/{kind}/transport.json')
    for part in json.loads(manifest.read_bytes())['parts']:pin(files,manifest.parent/part['bundle'],part['sha256'])
    stage=out/(key+'-'+kind)
    result=run_stage([sys.executable,str(H/'read_probe_v2.py'),kind,str(manifest)],stage,timeout_seconds=180,inputs=[H/'read_probe_v2.py',H/'capture_shared_v4.py',manifest])
    need(result['passed'] and verify_stage(stage,sha_file(stage/'stage.json'))['recorded_stage_passed'],'Actual final reader measurement')
    for path in stage.iterdir():pin(files,path)
    metric=json.loads((stage/'stdout.bin').read_bytes());cases[key][kind]=metric
   need(cases[key]['canonical']['checksum']==cases[key]['shared']['checksum'],'Unchanged actual steady logical access')
  report.update(passed=True,cases=cases,current_physical_closure=verify_manifest(files),files=files,scope='Reader v4 only against unchanged benchmark-r2 archives; writer and32k full-byte identity receipts unchanged. One uncontrolled-cache measured trial per reader/workload. No adoption.')
 except BaseException as exc:report.update(error=str(exc),traceback=traceback.format_exc(),files=files);raise
 finally:(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'passed':True,'cases':{k:{r:{f:v[r][f] for f in ('startup_seconds','steady_access_seconds','after_open')} for r in ('canonical','shared')} for k,v in cases.items()},'format_adopted':False}))
if __name__=='__main__':main(*sys.argv[1:])
