"""Reuse the prepared124 schedule; change only final authentic provider input owner."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 base=ROOT/'reports/m4-joint-startup124/preparation-r2';assert sha(base/'report.json')=='d37db0ae65f6cc625f85f2b86096bb7f034cf36a9956c0bbf433187ea23dc513';old=json.loads((base/'report.json').read_bytes());assert old['passed']
 native=ROOT/'reports/m4-lockit-native/preparation-r3';assert sha(native/'report.json')=='4c28406fb33cc34976b754ceedd0203540be80535c557a79b322407aae342b7d';n=json.loads((native/'report.json').read_bytes());assert n['passed']
 out=ROOT/'reports/m4-joint-startup124'/name;assert not out.exists();out.mkdir(parents=True)
 files=json.loads((base/'pins.json').read_bytes())['files'];files[str(base/'report.json')]=sha(base/'report.json');generated={}
 for p in base.rglob('*'):
  if p.is_file()and p.suffix in('.cpp','.hpp','.inc','.ps1','.py','.txt'):
   assert sha(p)==files[str(p.resolve())];q=out/p.relative_to(base);q.parent.mkdir(parents=True,exist_ok=True);q.write_text(p.read_text().replace(base.as_posix(),out.as_posix()));generated[str(q.resolve())]=sha(q)
 for p,h in n['files'].items():assert p not in files or files[p]==h;files[p]=h
 files[str(native/'report.json')]=sha(native/'report.json');files[str(Path(__file__).resolve())]=sha(__file__)
 report=old|dict(scope='Connected124 final loaded-input preparation only; no execution credit',native_library=str(native/'registry_library.cpp'),native_include=str(native),generated_sources=generated,physical_dependencies=files,previous_candidate_preparation_sha256=sha(base/'report.json'),native_preparation_sha256=sha(native/'report.json'))
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');generated[str((out/'report.json').resolve())]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=files|generated),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
