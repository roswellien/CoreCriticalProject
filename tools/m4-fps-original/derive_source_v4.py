"""Add literal FPS-derived font vptr store variant, preserving every source byte."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];T=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def one(s,a,b):
 if s.count(a)!=1:raise ValueError('Exact source variant '+a[:80])
 return s.replace(a,b,1)
p=T/'prepare_source_v3.py';s=p.read_text();failed=R/'reports/m4-fps-original/source-r2/report.json';r=json.loads(failed.read_bytes())
if r['passed']or r['files'][str(T/'compare_source_v2.py')]!=sha(T/'compare_source_v2.py'):raise ValueError('Frozen failed source comparison')
s=one(s," registration=next(v for v in worker['roots']", " fontbinding=next(v for v in c['source_indirect_contracts']if v['CALL_pc']==0x5a0669);fontbinding['source_vptr_store_PC_by_root']={'4255744':0x40f187};fontbinding['source_vptr_store_variants']=[dict(root=0x40f000,PC=0x40f187,value=0x5bc598,physical_hex='c70698c55b00')];need(known[0x40f187]['bytes_hex']=='c70698c55b00','Literal current FPS derived-class font vptr store')\n registration=next(v for v in worker['roots']")
s=one(s," mp=out/'game_model.py';mp.write_text(model);pin(mp)", " model=one(model,\"  self.widget_array_contracts=data['source_array_contracts']\",\"  for binding in data['source_indirect_contracts']:\\n   for variant in binding.get('source_vptr_store_variants',[]):self.widget_vptr_stores[variant['PC']]=variant['value']\\n  self.widget_array_contracts=data['source_array_contracts']\")\n model=one(model,\"   I.need(token and token['root']==self.widget_root and token['PC']==binding['source_vptr_store_PC']and token['value']==binding['source_vptr'],'Same current instance most recent literal source vptr store')\",\"   expected_store=binding.get('source_vptr_store_PC_by_root',{}).get(str(self.widget_root),binding['source_vptr_store_PC'])\\n   I.need(token and token['root']==self.widget_root and token['PC']==expected_store and token['value']==binding['source_vptr'],'Same current instance most recent root-specific literal source vptr store')\")\n mp=out/'game_model.py';mp.write_text(model);pin(mp)")
s=one(s,"qp=T/'compare_source_v2.py'","qp=T/'compare_source_v3.py'")
s=s.replace("pin(R/'tools/m4-fps-original/prepare_source_v3.py');pin(R/'tools/m4-fps-original/derive_source_v3.py');","pin(R/'tools/m4-fps-original/prepare_source_v4.py');pin(R/'tools/m4-fps-original/derive_source_v4.py');pin(R/'tools/m4-fps-original/prepare_source_v3.py');pin(R/'tools/m4-fps-original/derive_source_v3.py');")
s=one(s," read(B/'source-r1/report.json'", " read(B/'source-r2/report.json','33483b5a720375641397e102d2a2e6f640a54e222212095429423a089615c816')\n read(B/'source-r1/report.json'")
q=T/'prepare_source_v4.py'
if q.exists():raise ValueError('Fresh literal store variant')
q.write_text(s);print(json.dumps(dict(passed=True,source=str(q),sha256=sha(q))))
