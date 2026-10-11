"""Preserve initial adapter-generation failure; correct exact lineage/path hunks."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];T=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def one(s,a,b):
 if s.count(a)!=1:raise ValueError('Exact generator correction '+a[:80])
 return s.replace(a,b,1)
p=T/'prepare_source.py';s=p.read_text();old=R/'reports/m4-fps-original/source-preparation-r1';pins={str(p):sha(p)}
if(old/'report.json').exists():raise ValueError('Partial generation remains unsealed')
s=one(s,"comp=one(comp,\"pin(R/'tools/m4-fps-original/prepare_source.py');\",\"pin(R/'tools/m4-fps-original/prepare_source.py');pin(R/'tools/m4-fps-original/fps_source_join.inc');pin(R/'tools/m4-font479590-original/compare_source.py');\")", "comp=one(comp,\"pin(R/'tools/m4-font479590-original/prepare_source.py');\",\"pin(R/'tools/m4-fps-original/prepare_source_v2.py');pin(R/'tools/m4-fps-original/derive_source_v2.py');pin(R/'tools/m4-fps-original/fps_source_join.inc');pin(R/'tools/m4-font479590-original/prepare_source.py');pin(R/'tools/m4-font479590-original/compare_source.py');\")")
s=one(s," comp=one(comp,'results=[];API_inputs=[];memory_joins=[]'", " comp=comp.replace('reports/m4-fps-original/source-preparation-r1/',out.relative_to(R).as_posix()+'/')\n comp=one(comp,'results=[];API_inputs=[];memory_joins=[]'")
q=T/'prepare_source_v2.py'
if q.exists():raise ValueError('Fresh generator correction')
q.write_text(s)
for a in old.iterdir():pins[str(a)]=sha(a)
f=old/'generation-failure.json';f.write_text(json.dumps(dict(passed=False,source_model_executed=False,reason='Exact parent comparator tool lineage literal retained font namespace; no compare/write/capture was launched',files=pins),indent=2)+'\n')
print(json.dumps(dict(passed=True,source=str(q),sha256=sha(q))))
