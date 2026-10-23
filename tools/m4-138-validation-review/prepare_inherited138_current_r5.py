"""Exact current receipt/transition bindings; inherited semantic gates unchanged."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2];T=R/'tools/m4-startup138-original';P={};deltas={}
def pin(p,h=None):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip');v=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();assert h is None or h==v;P[str(p)]=v;return p
oldprep=R/'reports/m4-startup138-original/inherited-source-preparation-r4/report.json';prep=json.loads(pin(oldprep,'b7c553df61f31d1aa8c3bfbcd22d2fa19d2f1cab18ea40cf94f2d9f94959d4e8').read_bytes())
for p,h in prep['files'].items():pin(p,h)
for p,h in [(R/'reports/m4-startup138-original/original-validation-r3/report.json','02ea1ce07ac3e5aa5dff6e20813b956117383784ae4f5e1ffd6aa1822f603f5f'),(R/'reports/m4-startup138-original/mfc-source-r2/report.json','6a4e28040c31aebbc108904cb6a574d964aa28f045ff446f1362deaedd260801'),(R/'reports/m4-138-validation-review/mfc-transition-r4/report.json','e14fbc230d19b05f3e5b711beb10bfd42e876d48b879ee13d98113a3ba3ac386'),(R/'reports/m4-138-validation-review/mfc-transition-r4/patch-identities.json','8eb2db9ceb5853d40b35eaa638e5875b9c7876d179993f450e8cd2be9a3c7a87')]:pin(p,h)
common=[('original-validation-r2','original-validation-r3'),('74d444a5c9cfef4af293a0340af5bdfe6e6891d848b4ac16f9d1f8e562fa6181','02ea1ce07ac3e5aa5dff6e20813b956117383784ae4f5e1ffd6aa1822f603f5f')]
def derive(base,name,extra=()):
 p=pin(T/base);source=p.read_text();text=source;changes=[]
 for a,b in common+list(extra):
  count=text.count(a);assert count>0,(base,a)
  for _ in range(count):
   pos=text.index(a);changes.append(dict(position=pos,old=a,new=b));text=text[:pos]+b+text[pos+len(a):]
 reverse=text
 for d in reversed(changes):
  pos=d['position'];assert reverse[pos:pos+len(d['new'])]==d['new'];reverse=reverse[:pos]+d['old']+reverse[pos+len(d['new']):]
 assert reverse==source;ast.parse(text);target=T/name;assert not target.exists();target.write_text(text);pin(target);deltas[name]=changes
derive('format_source_v4_r3.py','format_source_v4_r5.py')
derive('tree_source_r4.py','tree_source_r5.py')
derive('old4_source_r4.py','old4_source_r5.py',[('mfc-transition-r3','mfc-transition-r4'),('56cc2983c3448cf872e9247cb315cede98a83fa9a63c831264d9008b7ad9e834','e14fbc230d19b05f3e5b711beb10bfd42e876d48b879ee13d98113a3ba3ac386'),('1f8768938aa8f2ebb938e6a782a93734bb569cea8634d634fe23d335d7b9b2ed','8eb2db9ceb5853d40b35eaa638e5875b9c7876d179993f450e8cd2be9a3c7a87')])
derive('current_inherited_source_v2_r4.py','current_inherited_source_v2_r5.py',[('inherited-source-preparation-r4','inherited-source-preparation-r5'),('format_source_v4_r3.py','format_source_v4_r5.py'),('tree_source_r4.py','tree_source_r5.py'),('old4_source_r4.py','old4_source_r5.py'),('mfc-source-r1','mfc-source-r2'),('e320179826dc0d0ab6033e98502eb5706186afa235222dd906d67c7d9605180f','6a4e28040c31aebbc108904cb6a574d964aa28f045ff446f1362deaedd260801')])
pin(__file__);out=R/'reports/m4-startup138-original/inherited-source-preparation-r5';assert not out.exists();out.mkdir();q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Only current validation/whole physical13observer transition/new sealed MFC source bindings changed',exact_inverse_restores_each_parent=True,all_inherited_source_gates_retained=True,capture_reader_opened=False,payload_reader_opened=False,source_execution_performed=False,initializer_credit=0,changes=deltas,files=P),indent=2)+'\n');print(q,hashlib.sha256(q.read_bytes()).hexdigest())
