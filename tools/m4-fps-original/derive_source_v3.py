"""Correct superseded FPS vptr contract using the genuine carried instance."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];T=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def one(s,a,b):
 if s.count(a)!=1:raise ValueError('Exact pure source correction '+a[:80])
 return s.replace(a,b,1)
p=T/'prepare_source_v2.py';s=p.read_text();old=R/'reports/m4-fps-original/source-r1/report.json';r=json.loads(old.read_bytes())
if r['passed']or r['files'][str(T/'compare_source.py')]!=sha(T/'compare_source.py'):raise ValueError('Frozen failed source comparison')
a=" binding=next(v for v in c['source_indirect_contracts']if v['CALL_pc']==0x5a2f86);binding.update(worker['fps']['new_virtual']);binding.update(slot_offset=0x20,object_role='Current FPS instance5FC378 from literal base vptr store5A0114; observed root BEFORE and whole source object endpoints remain independent inputs/joins')"
b=" binding=next(v for v in c['source_indirect_contracts']if v['CALL_pc']==0x5a2f86);need((binding['source_vptr_store_PC'],binding['source_vptr'],binding['slot'],binding['target'])==(0x5a2dd4,0x5cfed8,0x5cfef8,0x59ff00),'Exact later dominating text-constructor vptr store supersedes base5A0114');binding['object_role']='Current FPS instance5FC378; literal5A2DD4 is the most recent source vptr store before CALL5A2F86; full genuine source-page observations remain independent joins'"
s=one(s,a,b);s=one(s,"qp=T/'compare_source.py'","qp=T/'compare_source_v2.py'")
s=s.replace("pin(R/'tools/m4-fps-original/prepare_source_v2.py');pin(R/'tools/m4-fps-original/derive_source_v2.py');","pin(R/'tools/m4-fps-original/prepare_source_v3.py');pin(R/'tools/m4-fps-original/derive_source_v3.py');pin(R/'tools/m4-fps-original/prepare_source_v2.py');pin(R/'tools/m4-fps-original/derive_source_v2.py');")
s=one(s," pin(__file__)\n", " pin(__file__)\n") if " pin(__file__)\n"in s else s
s=one(s," actual=read(B/'validation-r1/report.json'", " read(B/'source-r1/report.json','d161348ff6018519004bbb946769e30e6ca09f6cf02ea241f38f6dd8c54fdb70')\n actual=read(B/'validation-r1/report.json'")
q=T/'prepare_source_v3.py'
if q.exists():raise ValueError('Fresh exact source adapter')
q.write_text(s);print(json.dumps(dict(passed=True,source=str(q),sha256=sha(q))))
