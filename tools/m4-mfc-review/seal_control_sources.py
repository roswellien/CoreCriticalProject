"""Persist exact independent fixture and tooling inputs used by frozen controls."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(report,digest,name):
 report=Path(report).resolve();assert sha(report)==digest;q=json.loads(report.read_bytes());assert q['passed']
 execution=Path(q['execution']);assert sha(execution)==q['execution_sha256'];x=json.loads(execution.read_bytes());assert x['passed'];build=Path(x['build']);assert sha(build)==x['build_sha256'];b=json.loads(build.read_bytes());assert b['passed']
 out=ROOT/'reports/m4-mfc-review'/name;assert not out.exists();out.mkdir(parents=True);pins={str(report):digest,str(build):sha(build),str(execution):sha(execution)};rows=[]
 paths={Path(p):h for p,h in q['files'].items()if Path(p).is_relative_to(ROOT/'tools/m4-mfc-review')}
 for name_ in('build_controls_v2.ps1',):
  path=ROOT/'tools/m4-mfc-review'/name_;paths[path]=sha(path)
 for path,h in paths.items():
  assert sha(path)==h;destination=out/'sources'/path.relative_to(ROOT);destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(path.read_bytes());assert sha(destination)==h
  pins[str(path)]=h;pins[str(destination)]=h;rows.append(dict(source=str(path),copy=str(destination),sha256=h))
 for name_ in('fixture.cpp','fixture_hooks_v2.hpp','capture.s','CMakeLists.txt'):
  path=build.parent/name_;h=sha(path);assert b['artifacts'][str(path)]==h
  destination=out/'compiled-inputs'/name_;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(path.read_bytes());assert sha(destination)==h
  pins[str(path)]=h;pins[str(destination)]=h;rows.append(dict(source=str(path),copy=str(destination),sha256=h))
 pins[str(Path(__file__).resolve())]=sha(__file__)
 result=dict(passed=True,scope='Byte-identical persistent copies of independent fixture/hooks/assembly/CMake and control build/checker tools, authenticated against successful frozen actual execution and compilation',copied_sources=rows,actual_control_report=str(report),actual_control_report_sha256=digest,build_report_sha256=sha(build),source_semantics_changed=False,worker_rebuilt=False,original_control_receipts_modified=False,files=pins)
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');pins[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),source_copies=len(rows))))
if __name__=='__main__':main(Path(sys.argv[1]),sys.argv[2],sys.argv[3])
