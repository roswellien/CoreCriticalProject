"""ROOT exact derivative admission; preserve previous failed attempts."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=R/'tools/m4-141-consumer-review/root_admit_source_v2.py'
t=p.read_text()
changes=[('root-source-admission-r2','root-source-admission-r3'),('preparation-r5','preparation-r6'),('30cf99256ebbc7584f6e1b15b73d15e76ac029809dda675d89749916b7dae9c9','08f2ea8a1940bfd20c4b3036a834fccd1b4330093d35751499607089a6e2058c'),('FS-domain-preparation-r1/report.json','FS-domain-preparation-r2/report.json'),('2683770625edcbf5f8c4af497bf51510013c93b2c983a4cab392c8ed2f4aadb6','3e756e0c847baf33857b33c9b29471ed3085c59fda75d9e46873acf5e4e7862a'),('FS-domain-controls-r1/report.json','FS-domain-controls-r2/report.json'),('92091445b9ca694179e9cfaaed47f27c6c9daafe43d0f1d399c7abad2692790b','02d8aa0dd07c3721b25c3f060f9528ed945ed19992f2bc78cf6259461b142b17')]
for a,b in changes:assert a in t;t=t.replace(a,b)
a="edits=json.loads(pin(R/'reports/m4-141-consumer-review/FS-domain-preparation-r1/observer-deltas.json').read_bytes())\n  observer=pin(prep['observer']).read_text()"
b="""delta=json.loads(pin(R/'reports/m4-141-consumer-review/FS-domain-preparation-r2/deltas.json').read_bytes())
  helper=pin(R/'tools/m4-native141-source/constructor_fs_union141_v3.py').read_text()
  for row in reversed(delta['helper']):
   assert helper.count(row['new'])==1;helper=helper.replace(row['new'],row['old'])
  assert helper==pin(R/'tools/m4-native141-source/constructor_fs_union141_v2.py').read_text()
  observer=pin(prep['observer']).read_text()
  for row in reversed(delta['observer']):
   assert observer.count(row['new'])==row['count'];observer=observer.replace(row['new'],row['old'])
  assert observer==pin(R/'tools/m4-native141-source/final_observer141_v8.py').read_text()
  edits=json.loads(pin(R/'reports/m4-141-consumer-review/FS-domain-preparation-r1/observer-deltas.json').read_bytes())"""
assert t.count(a)==1;t=t.replace(a,b)
t=t.replace('FS_domain_controls_v1.py','FS_domain_controls_v2.py')
t=t.replace("old=\"out=R/'reports/m4-141-consumer-review/FS-domain-controls-r1'\"","old=\"out=R/'reports/m4-141-consumer-review/FS-domain-controls-r2'\"")
t=t.replace("root-FS-domain-controls-r1","root-FS-domain-controls-r2")
t=t.replace("derivative.write_text(code.replace(old,new))","""anchor="obs=[e for v in rows for e in v['game_FS_observations']];checks=[]"
  assert code.count(anchor)==1
  actual="""+'"""'+"""
 physical_normal=R/'reports/m4-141-consumer-review/root-FS-diagnostic-r2'
 data[stem+'fs-frame-witnesses.bin']=(physical_normal/'fs-frame-witnesses.bin').read_bytes()
 data[stem+'fs-record-bytes.bin']=(physical_normal/'fs-record-bytes.bin').read_bytes()
 frames=list(struct.iter_unpack('<32Q',data[stem+'fs-frame-witnesses.bin']))
 records=list(struct.iter_unpack('<16Q',data[stem+'fs-record-bytes.bin']))
 """+'"""'+"""
  derivative.write_text(code.replace(old,new).replace(anchor,actual+anchor))""")
t=t.replace("controls['controls']==10","controls['controls']==11").replace('Fresh10 controls','Fresh11 controls using actual normal journal bytes')
q=R/'tools/m4-141-consumer-review/root_admit_source_v3.py';assert not q.exists();q.write_text(t)
print(json.dumps(dict(tool=str(q),sha256=sha(q))))
