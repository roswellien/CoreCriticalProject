"""Bounded observed failed-checker diagnosis; no worker or source input changes."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
pins={}
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);assert h is None or h==v;assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
def module(p,n):
 s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
out=R/'reports/m4-mfc1168-native/connected-controls-mode11-diagnostic-r1';assert not out.exists();out.mkdir()
e_path=pin(R/'reports/m4-mfc1168-native/connected-controls-execution-r3/report.json','fefde7d6702410cda8d2b5092935e67507474a4605a149056a819f1064ac38bd');e=json.loads(e_path.read_bytes());D=module(R/'tools/m4-crt-allocation-root/run_v2.py','mfc_control_diag_direct');X=module(R/'tools/m4-joint-startup131/paired_exports.py','mfc_control_diag_exports');rows=[];exports=[];closed=True
for row in e['levels']:
 a=D.DirectSet(row['capture'],pin);closed=False;ex=X.Export(out/'raw-controls',row['level'],a.path,pin)
 try:
  for key in sorted(a.entries):ex.write(key,a.data(key))
  exports.append(ex.finish())
  stem='control-11/';prefix=stem+'MFC/';accesses=list(struct.iter_unpack('<IIQII',a.data(prefix+'refused/accesses.bin')))
  frames=list(struct.iter_unpack('<8Q',a.data(prefix+'refused/frames.bin')))if prefix+'refused/frames.bin'in a.entries else []
  rows.append(dict(level=row['level'],terminal=a.words(stem+'terminal-facts.bin',13),facts=a.words(stem+'facts.bin',8),reason=a.data(stem+'refusal.txt').decode(),source_access_prefix=accesses,API_records_bytes=len(a.data(prefix+'refused/APIs.bin')),frames=frames,component_keys=[k for k in a.entries if k.startswith(prefix+'refused/')]))
 finally:ex.close();a.close();a.entries.clear();a.bundles.clear();del a;closed=True
q=out/'mode11-observations.json';q.write_text(json.dumps(rows,indent=2)+'\n');pin(q);pin(__file__)
q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Observed mode11 checker failure diagnosis and complete existing raw controls equality targets, no semantic verdict or initializer credit',execution=str(e_path),execution_sha256=sha(e_path),raw_exports=exports,all_bounded_readers_closed=closed,files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(q),observations=rows)))
