"""Refresh only candidate native resource source; reuse the exact124 schedule."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(native_report,expected,name):
 base=ROOT/'reports/m4-joint-startup124/preparation-r3'
 assert sha(base/'report.json')=='4954639d674ac7421d4567cd6bc496c2222614d7e986da0cb54dc05da225b3e1'
 old=json.loads((base/'report.json').read_bytes());assert old['passed']
 nr=Path(native_report).resolve();assert sha(nr)==expected;n=json.loads(nr.read_bytes());assert n['passed']
 out=ROOT/'reports/m4-joint-startup124'/name;assert not out.exists();out.mkdir(parents=True)
 files=json.loads((base/'pins.json').read_bytes())['files'];files[str(base/'report.json')]=sha(base/'report.json');generated={}
 for p in base.rglob('*'):
  if p.is_file() and p.suffix in('.cpp','.hpp','.inc','.ps1','.py','.txt'):
   assert sha(p)==files[str(p.resolve())];q=out/p.relative_to(base);q.parent.mkdir(parents=True,exist_ok=True)
   q.write_text(p.read_text().replace(base.as_posix(),out.as_posix()));generated[str(q.resolve())]=sha(q)
 for p,h in n['files'].items():assert p not in files or files[p]==h;files[p]=h
 files[str(nr)]=expected;files[str(Path(__file__).resolve())]=sha(__file__)
 report=old|dict(scope='Connected124 exact FS-prolog source refresh; no execution credit',native_library=n['native_library'],native_include=n['native_include'],generated_sources=generated,physical_dependencies=files,previous_candidate_preparation_sha256=sha(base/'report.json'),native_preparation_sha256=expected)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');generated[str((out/'report.json').resolve())]=sha(out/'report.json')
 (out/'pins.json').write_text(json.dumps(dict(files=files|generated),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(*sys.argv[1:])
