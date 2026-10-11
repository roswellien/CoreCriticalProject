"""Freeze byte-identical authored controls sources after actual execution/checks."""
from pathlib import Path
import hashlib,json,sys,traceback
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-fs-controls'
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from manifests import verify_manifest
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(check,digest,name):
 out=BASE/name;assert not out.exists();out.mkdir();pins={};copies=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v,(p,h,v);pins[str(p)]=v;return p
 try:
  receipt=json.loads(pin(check,digest).read_bytes());assert receipt['passed']
  for p,h in receipt['files'].items():pin(p,h)
  pin(__file__)
  paths=[ROOT/'tools/m4-fs-controls'/n for n in('build_v5.py','build_v5.ps1','fixture_v3.inc','hooks.hpp','capture.py','check_controls_v3.py')]
  paths+=[ROOT/'reports/m4-fs-controls/build-r5'/n for n in('fixture.cpp','hooks.hpp','capture.s','CMakeLists.txt')]
  paths+=[ROOT/'tools/m4-strings-review/fixture_hooks_v2.hpp',ROOT/'tools/m4-crt-allocation/capture.s']
  for i,path in enumerate(paths):
   src=pin(path);dst=out/f'{i:02}-{path.name}';dst.write_bytes(src.read_bytes());pin(dst,sha(src));copies.append(dict(source=str(src),copy=str(dst),sha256=sha(src)))
  assert all(Path(r['source']).read_bytes()==Path(r['copy']).read_bytes()for r in copies)
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,schema='mw34-normal-FS-controls-byte-identical-source-seal-v1',checker=str(check),checker_sha256=digest,copies=copies,files=pins,physical_closure=verify_manifest(pins),source_bodies_modified=False,canonical_initializer_credit=False)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pins[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=passed,report=str(out/'report.json'),sha256=sha(out/'report.json'),copies=len(copies))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
