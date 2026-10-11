"""Additive finite seal with normalized closure and direct execution identities."""
from pathlib import Path
import ast,hashlib
T=Path(__file__).resolve().parent
old=T/'seal_indirect_source.py';target=T/'seal_indirect_source_v2.py'
assert not target.exists()
s=old.read_text()
s=s.replace('pins={};counts=', 'pins={};normalized={};counts=')
s=s.replace(" def pin(p,h=None):\n  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact frozen indirect source dependency');pins[str(p)]=v;return p\n def report(p):\n  r=json.loads(pin(p).read_bytes());need(r['passed'],'Only passed current source gate');return r", """ def register(p,h):
  p=Path(p).resolve();k=str(p).replace('\\\\','/').casefold();need(len(h)==64 and all(c in '0123456789abcdef'for c in h),'Exact SHA256 identity');need(k not in normalized or normalized[k][1]==h,'No normalized physical dependency hash conflicts');need(p.is_file(),'Physical transitive source input remains present');normalized[k]=(str(p),h);pins[str(p)]=h;return p
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact frozen indirect source dependency');register(p,v);return p
 def report(p,h=None):
  r=json.loads(pin(p,h).read_bytes());need(r['passed'],'Only passed current source gate')
  for path,value in r.get('files',{}).items():register(path,value)
  return r""")
anchor="  inputs=json.loads(pin(BASE/'recovery-r1/indirect-call-inputs.json'"
assert s.count(anchor)==1
pre="""  report(ROOT/'reports/m4-vtable-original/preparation-r3/report.json','a2e7635100478713acbc5efbc7557ba20ac8d060c461241b2ef1785b291105b5')
  report(ROOT/'reports/m4-vtable-original/build-r2/build.json','ea4fb73e11dfa0d5c4b6f4145eb57df5148e5b096bb44e3fdd6c8d9d99e6dc5a')
  report(ROOT/'reports/m4-vtable-original/execution-r1/report.json','6eae8008920f9b108eef5d14c20bb090aa1010dfdb3e428d0c4bf4258ac80136')
  report(ROOT/'reports/m4-vtable-original/validation-r1/report.json','2a072a38b8f0ff98377709a10da203b017bea92615baa9b153f548027565c251')
  report(ROOT/'reports/m4-vtable-native/preparation-r4/report.json','b52c62a1ec6e1306a9629f53fbe80621be96404907d322efbbeef136ec10ee93')
  report(ROOT/'reports/m4-joint-startup120-root/execution-r3/report.json')
  pin(BASE/'recovery-r1/instruction-contracts.json','a58e31641f42e8e37c1d66bad5e41dd57854b82a7a00bd86a02b1bc85aec9108')
"""
s=s.replace(anchor,pre+anchor)
anchor="  pin(__file__);pin(ROOT/'tools/m4-next-source/indirect_trace.py');passed=True"
assert s.count(anchor)==1
s=s.replace(anchor,"""  need(counts['actual_original_full_CPU_FX_ENV_boundaries']==72 and counts['actual_native_full_State_CPU_FX_boundaries']==144 and counts['native_zero_argument_no_pointee_prefixes']==24 and counts['native_dominating_vptr_publications']==48,'Required complete actual boundary and precise vptr/null-prefix counters')
  pin(__file__);pin(ROOT/'tools/m4-next-source/indirect_trace.py');passed=True""")
s=s.replace('files=pins);','normalized_dependency_hash_conflicts_rejected=True,transitive_sourcegate_identity_metadata_registered=True,transitive_physical_bytes_rehashed_here=False,root_final_acceptance_rehash_required=True,files=pins);')
ast.parse(s);target.write_text(s)
print(hashlib.sha256(target.read_bytes()).hexdigest())
