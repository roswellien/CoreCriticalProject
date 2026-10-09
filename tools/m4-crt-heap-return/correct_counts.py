"""Correct only the observational-public-flag rollup from sealed native archives."""
import json,struct,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import CaptureBundle,sha_file
from manifests import normalized,verify_manifest
from paths import publish_bytes
BASE=ROOT/'reports/m4-crt-heap-return'
ORIGINAL_SHA='7e1c25565468f3d286e8262076825e616bd24c10b9ce1665fa06237a1be8d52b'
def main():
 started=time.perf_counter_ns()
 original=BASE/'execution-r1/report.json'
 assert sha_file(original)==ORIGINAL_SHA
 report=json.loads(original.read_text())
 assert report['passed'] and report['native_stages_completed']==2
 history=BASE/'counts-correction-r1';current=BASE/'execution-r2'
 assert not history.exists() and not current.exists()
 history.mkdir();current.mkdir()
 rows=[];mode_stores=initializer_returns=public_mode=0
 for level in ('O0','O2'):
  record=report['levels'][level]
  with CaptureBundle(record['bundle'],record['bundle_sha256']) as bundle:
   assert len(bundle.names())==record['logical_files']==96068
   for n in range(36):
    job=struct.unpack('<72I',bundle.read_bytes(f'row-{n}/heap-return-job.bin'))
    accesses=struct.unpack('<320I',bundle.read_bytes(f'row-{n}/heap-return-accesses.bin'))
    events=struct.unpack('<64I',bundle.read_bytes(f'row-{n}/heap-return-events.bin'))
    private=struct.unpack('<8I',bundle.read_bytes(f'row-{n}/heap-create-after/heap-return-progress.bin'))
    exact=(0x780039eb,0x78035004,1,4,1)
    committed=tuple(accesses[31*5:32*5])==exact
    assert committed==(job[3]>=32) and committed==bool(private[3])
    assert private[4]==int(committed)
    initializer=tuple(events[12*4:13*4])==(13,0x78003a0b,0x78001843,0x20001858)
    assert initializer==bool(private[6])==bool(job[69])
    if initializer:
     assert job[3]==35 and tuple(accesses[34*5:35*5])==(0x78003a0b,0x20001858,0x78001843,4,0)
    if bool(job[66])!=committed:
     assert job[0]==158 and job[3]==31 and private[3]==0 and not any(events[11*4:])
    elif job[0]==158:raise AssertionError('Expected authored public-only forgery preserved')
    if n<24:assert job[0]==0 and committed and initializer
    rows.append(dict(level=level,row=n,control=job[0],public_mode_flag=job[66],source_mode_store=committed,private_mode_flag=private[3],genuine_initializer_RET=initializer))
    public_mode+=bool(job[66]);mode_stores+=committed;initializer_returns+=initializer
 assert public_mode==70 and mode_stores==68 and initializer_returns==52 and len(rows)==72
 correction=dict(passed=True,scope='Read-only source-ledger/private-progress rollup correction over existing sealed native archives; no worker execution or new native credit',
  corrected_from_execution_path=str(original),corrected_from_execution_sha256=ORIGINAL_SHA,
  original_public_flag_count=public_mode,actual_source_mode_publication_sequences=mode_stores,genuine_initializer_RET_sequences=initializer_returns,
  intentional_public_flag_forgery_sequences=2,controls=[158],rows=rows,native_rerun=False,source_or_worker_changed=False,
  archives={k:dict(path=v['bundle'],sha256=v['bundle_sha256'],logical_files=v['logical_files'])for k,v in report['levels'].items()},
  tool_path=str(Path(__file__).resolve()),tool_sha256=sha_file(__file__))
 correction_path=history/'report.json';publish_bytes(correction_path,(json.dumps(correction,indent=2)+'\n').encode())
 files=report['files'].copy()
 for p in (original,correction_path,Path(__file__),Path(sys.executable)):
  key=normalized(str(p.absolute()));digest=sha_file(p)
  assert key not in files or files[key]==digest
  files[key]=digest
 report.update(actual_source_mode_publication_sequences=mode_stores,genuine_initializer_RET_sequences=initializer_returns,
  corrected_from_execution_path=str(original),corrected_from_execution_sha256=ORIGINAL_SHA,
  original_public_mode_flag_true_sequences=70,rollup_correction_path=str(correction_path),rollup_correction_sha256=sha_file(correction_path),
  rollup_correction_tool_path=str(Path(__file__).resolve()),rollup_correction_tool_sha256=sha_file(__file__),
  native_rerun=False,new_native_execution_credit=False,files=files,physical_closure=verify_manifest(files),
  receipt_publication_seconds=(time.perf_counter_ns()-started)/1e9)
 publish_bytes(current/'report.json',(json.dumps(report,indent=2)+'\n').encode())
 print(json.dumps(dict(passed=True,correction_sha256=sha_file(correction_path),execution_sha256=sha_file(current/'report.json'),mode_stores=mode_stores,initializer_returns=initializer_returns)))
if __name__=='__main__':main()
