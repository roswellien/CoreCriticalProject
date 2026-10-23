"""Read two already captured FS diagnostics through the existing strict reader."""
from pathlib import Path
import hashlib,json,struct,sys,time,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
out=R/'reports/m4-141-consumer-review/root-FS-diagnostic-r2'
assert not out.exists();out.mkdir(parents=True);pins={};started=time.monotonic();passed=False;closed=True;found={}
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);assert h is None or h==v,(p,h,v)
 assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
try:
 failure=R/'reports/m4-startup141-source/combined-source-provider-r1/report.json'
 f=json.loads(pin(failure,'69e2ddad2bac46db0ee8d5c0b515c55665a94ff0fa80de711c30cd3e0124e361').read_bytes());assert f['passed']is False and f['reader_closed']
 execution=R/'reports/m4-startup141-root/execution-r2/report.json'
 e=json.loads(pin(execution,'536eeb8c62c9de8276e46d727907faea417b91a22c2cbae2b3cdbca80da7c2b6').read_bytes());assert e['passed']and e['all_workers_terminal']
 manifest=Path(e['runs']['O0']['capture']).resolve();m=json.loads(pin(manifest,f['files'][str(manifest)]).read_bytes())
 assert m['passed']and m['format']=='mw34.capture.direct.v1'and m['transport_only']and m['native_executed']is False
 for name in ('capture_bundle_storage.py','paths_capture_storage.py'):
  p=R/'tools/m4-pipeline'/name;pin(p,f['files'][str(p.resolve())])
 sys.path.insert(0,str(R/'tools/m4-pipeline'));from capture_bundle_storage import CaptureBundle
 wanted={'sequence-0/cleaned/fs-frame-witnesses.bin','sequence-0/cleaned/fs-record-bytes.bin'}
 candidates=[];index_checks=[]
 for part in m['parts']:
  p=manifest.parent/part['bundle']
  # Navigation uses the independently SHA-bound index in the already pinned
  # manifest. Selected payloads still use the unchanged strict whole reader.
  with p.open('rb')as stream:
   magic,index_bytes,index_digest=struct.unpack('<8sQ32s',stream.read(48))
   assert magic==b'MW34CAP1'and index_bytes==part['index_bytes']and 0<index_bytes<=64*1024*1024
   raw=stream.read(index_bytes)
  assert hashlib.sha256(raw).hexdigest()==index_digest.hex()==part['index_sha256']
  idx=json.loads(raw);assert idx['format']=='mw34.capture.v1'
  names={v['path']for v in idx['files']}
  index_checks.append(dict(bundle=str(p),index_sha256=index_digest.hex(),index_bytes=index_bytes))
  if wanted.intersection(names):candidates.append(part)
 for part in candidates:
  p=manifest.parent/part['bundle'];assert f['files'][str(p.resolve())]==part['sha256']
  pin(p,part['sha256']);closed=False
  with CaptureBundle(p,part['sha256'])as b:
   for name in wanted.intersection(b.names()):
    assert name not in found;raw=b.read_bytes(name);target=out/Path(name).name;target.write_bytes(raw);pin(target);found[name]=dict(bytes=len(raw),sha256=sha(target),file=str(target))
  closed=True
  if set(found)==wanted:break
 assert set(found)==wanted
 frames=list(struct.iter_unpack('<32Q',(out/'fs-frame-witnesses.bin').read_bytes()));records=list(struct.iter_unpack('<16Q',(out/'fs-record-bytes.bin').read_bytes()))
 assert len(frames)==28 and len(records)==56
 assert all(row[2]not in(0x4103f0,0x410440,0x459b40)for row in frames)
 pin(__file__);passed=True
except Exception:(out/'failure.txt').write_text(traceback.format_exc())
report=dict(passed=passed,scope='Two diagnostic logical files of already executed O0 sequence0; not full source acceptance',reader_closed=closed,actual_global_frames=len(frames)if'frames'in globals()else None,actual_global_records=len(records)if'records'in globals()else None,constructor_frames_in_global_journal=0 if passed else None,logical_outputs=found,index_navigation=index_checks if 'index_checks'in globals()else [],elapsed_seconds=time.monotonic()-started,native_worker_launched=False,source_machine_executed=False,initializer_credit=0,files=pins)
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':passed,'reader_closed':closed,'report_sha256':sha(out/'report.json')}),flush=True)
raise SystemExit(0 if passed else 1)
