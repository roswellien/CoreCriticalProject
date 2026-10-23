"""Exact additive sealed program/callback identity correction, no execution."""
from pathlib import Path
import ast,json,hashlib
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-loader-message-review/persistent_lifecycle_v1.py';old=p.read_text();s=old
changes=[
 ('import hashlib','import hashlib,json'),
 ('def __init__(self,machine,program,callbacks,provider,region_guard,flag_tracker,ledger):','def __init__(self,machine,program_bytes,callback_bytes,provider,region_guard,flag_tracker,ledger):'),
 ("  need(len(program)==1100 and len(set(program))==1100,'Exact1100 physical program')", """  need(hashlib.sha256(program_bytes).hexdigest()=='a25bed469f6b0e8ce5054e638b9de02a9e3303d5af01d0299298048146a86af2','Exact sealed physical1100 program bytes')
  need(hashlib.sha256(callback_bytes).hexdigest()=='71ae25eb20c57dcc3518f88b18c91a73e994315cc52f703494dae05f60caca38','Exact compiled952 callback attribution bytes')
  rows=json.loads(program_bytes)['rows'];program={r['pc']:r for r in rows};callbacks={int(k):tuple(v)for k,v in json.loads(callback_bytes)['State_offsets_by_original_PC'].items()}
  need(len(rows)==len(program)==1100 and len(callbacks)==160,'Exact1100 physical program/952 callback scope')"""),
]
for a,b in changes:assert s.count(a)==1;s=s.replace(a,b)
inverse=s
for a,b in reversed(changes):assert inverse.count(b)==1;inverse=inverse.replace(b,a)
assert inverse==old;ast.parse(s)
q=p.with_name('persistent_lifecycle_v2.py');assert not q.exists();q.write_text(s)
source=R/'tools/m4-loader-message-review/prepare_persistent_code_v1.py';text=source.read_text()
assert text.count("'persistent_lifecycle_v1.py'")==1
text=text.replace("'persistent_lifecycle_v1.py'","'persistent_lifecycle_v2.py'")
ns={'__file__':str(source),'__name__':'static_preparation_only'};exec(compile(text,str(source),'exec'),ns);ns['main']('persistent-code-preparation-r2')
out=R/'reports/m4-loader-message-review/persistent-code-preparation-r2'
delta=out/'exact-carried-adapter-inverse.json';delta.write_text(json.dumps([dict(before=a,after=b)for a,b in changes],indent=2)+'\n')
report_path=out/'adapter-identity-preparation-report.json';pins={str(v):hashlib.sha256(v.read_bytes()).hexdigest()for v in(p,q,source,Path(__file__).resolve(),delta,out/'report.json')}
report=dict(passed=True,scope='Additive exact3 adapter identity hunks and code-preparation derivative; no runtime or compilation',whole_parent_adapter_inverse=True,adapter_delta_hunks=3,source_program_bytes_bound=True,compiled952_callback_bytes_bound=True,new148_native_callback_proof_still_pending=True,source_evaluator_invoked=False,compiler_invoked=False,DLL_loaded=False,worker_executed=False,canonical_reader_opened=False,initializer_credit=0,files=pins)
report_path.write_text(json.dumps(report,indent=2)+'\n');print(hashlib.sha256(report_path.read_bytes()).hexdigest())
