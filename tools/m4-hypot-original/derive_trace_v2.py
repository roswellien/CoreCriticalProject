"""Seal unexecuted preparation error and derive exact additive fixes."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];T=Path(__file__).parent;B=R/'reports/m4-hypot-original';pins={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p):
 p=Path(p).resolve();pins[str(p)]=sha(p);return p
base=pin(T/'prepare_trace.py');kernel=pin(T/'trace.hpp');failed=B/'trace-preparation-r1';assert failed.exists()and not(failed/'report.json').exists()
for p in failed.iterdir():pin(p)
failure=dict(passed=False,scope='Unexecuted preparation failed while constructing report metadata because source_after_seed appeared twice; no worker build or capture occurred',exception='TypeError: dict() got multiple values for keyword argument source_after_seed',files=dict(pins))
(failed/'report.json').write_text(json.dumps(failure,indent=2)+'\n');pin(failed/'report.json')
s=kernel.read_text();old=' __asm {mov eax,dword ptr fs:[18h] mov hypot_trace_teb,eax}';new=' __asm {\n  mov eax,dword ptr fs:[18h]\n  mov hypot_trace_teb,eax\n }';assert s.count(old)==1
k=T/'trace_v2.hpp';assert not k.exists();k.write_text(s.replace(old,new));pin(k)
s=base.read_text();old=',source_after_seed=False,files=files)';assert s.count(old)==1;s=s.replace(old,',files=files)');old="Path(__file__).parent/'trace.hpp'";assert s.count(old)==1;s=s.replace(old,"Path(__file__).parent/'trace_v2.hpp'")
old=" parent=json.loads(pin(PARENT/";assert s.count(old)==1;s=s.replace(old," pin(BASE/'prefix-validation-r2/report.json','80a4e558e8fc5d11bc2fb0f6fa9446d881c848690b8fd44c8543beca014ff313')\n"+old)
q=T/'prepare_trace_v2.py';assert not q.exists();q.write_text(s);pin(q);pin(__file__);pin(sys.executable)
out=B/'trace-derivation-r2';assert not out.exists();out.mkdir();report=dict(passed=True,scope='Exact additive report metadata correction plus explicit two-instruction inline assembly line boundaries and actual normal-validation lineage binding; tracer behavior otherwise unchanged',source_after_seed=False,numerical_expected_inputs_added=False,original_executed=False,files=pins);p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(p))))
