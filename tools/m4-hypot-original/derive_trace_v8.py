"""Pass the exact diagnostic's temporary string as the required const char*."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-hypot-original'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 parent=B/'trace-preparation-r7';out=B/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 old=json.loads(pin(parent/'report.json','d1ed80d4d982e3e687a946ac0e4d7d2ce2ced95f9750264e02ba0e3ab1b30e31').read_bytes())
 for p,h in old['files'].items():pin(p,h)
 failed=pin(B/'trace-build-r6/build.json');assert not json.loads(failed.read_text(encoding='utf-8-sig'))['passed'];pin(B/'trace-build-r6/compile.log');out.mkdir()
 for p in parent.iterdir():
  if p.name not in('report.json','pins.json'):(out/p.name).write_bytes(pin(p).read_bytes())
 p=out/'hypot_trace.hpp';s=p.read_text();a='require(actual==p.opcode,"Exact physical source first opcode before trace PC="+std::to_string(p.pc)+" expected="+std::to_string(p.opcode)+" actual="+std::to_string(actual));';b='require(actual==p.opcode,("Exact physical source first opcode before trace PC="+std::to_string(p.pc)+" expected="+std::to_string(p.opcode)+" actual="+std::to_string(actual)).c_str());';assert s.count(a)==1;p.write_text(s.replace(a,b));pin(__file__);pin(sys.executable)
 for p in out.iterdir():pin(p)
 report={**old,'previous_trace_preparation_sha256':sha(parent/'report.json'),'diagnostic_type_repair_hunks':1,'files':pins};q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');pin(q);(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
