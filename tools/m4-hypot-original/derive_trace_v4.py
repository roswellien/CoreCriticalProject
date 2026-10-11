"""Write only CONTROL after observing complete source x86 contexts."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-hypot-original'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 parent=B/'trace-preparation-r3';out=B/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 old=json.loads(pin(parent/'report.json','e893615c4d35b526c9411ba456ef5c3667f47b1b2e785723e692379d55009616').read_bytes())
 for p,h in old['files'].items():pin(p,h)
 pin(B/'trace-build-r2/build.json','634ac9c6cd3673516f0882d94cc5faaa2a8080f4b2c79759745d5844646ff447');out.mkdir()
 for p in parent.iterdir():
  if p.name not in('report.json','pins.json'):(out/p.name).write_bytes(pin(p).read_bytes())
 p=out/'hypot_trace.hpp';s=p.read_text();old_call='require(SetThreadContext(thread.value,&c),';assert s.count(old_call)==2;s=s.replace(old_call,'c.ContextFlags=CONTEXT_CONTROL;'+old_call);p.write_text(s)
 pin(__file__);pin(sys.executable)
 for p in out.iterdir():pin(p)
 report={**old,'scope':old['scope']+'; full stopped FP/EXTENDED context is observed while only EIP/EFLAGS CONTROL is written for debugger stepping','previous_trace_preparation_sha256':sha(parent/'report.json'),'SetThreadContext_written_sections':'CONTEXT_CONTROL only','GetThreadContext_observed_sections':'CONTEXT_FULL|CONTEXT_FLOATING_POINT|CONTEXT_EXTENDED_REGISTERS','debugger_FP_or_integer_sections_written':False,'source_hunks':2,'files':pins};q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');pin(q);(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
