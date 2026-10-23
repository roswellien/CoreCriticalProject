"""Independent ROOT input, inverse and adverse admission for semantic138."""
from pathlib import Path
import hashlib,json,traceback
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
out=R/'reports/m4-138-semantic-review/root-admission-r2'
assert not out.exists();out.mkdir(parents=True);pins={};checks=[];passed=False
def pin(p,h=None):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json',p
 actual=sha(p);assert h is None or h==actual,(p,h,actual)
 assert str(p)not in pins or pins[str(p)]==actual;pins[str(p)]=actual;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def collect(d):
 for p,h in d.get('files',{}).items():
  q=Path(p)
  if q.suffix.lower()not in('.mwb','.mwi','.zip')and q.name!='transport.json':pin(p,h)
def inverse(text,hunks):
 for row in reversed(hunks):
  for position in reversed(row['positions']):
   assert text[position:position+len(row['new'])]==row['new'],row
   text=text[:position]+row['old']+text[position+len(row['new']):]
 return text
try:
 prep=R/'reports/m4-138-semantic-review/preparation-r4/report.json'
 d=read(prep,'d72457a55321e74eac1c80f7ebf33119519968729a45d46ddf6f07e565895c09');assert d['passed'];collect(d)
 closing=read(R/'reports/m4-138-semantic-review/preparation-r3/closure-delta-hunks.json');baseline=read(R/'reports/m4-138-semantic-review/preparation-r2/inverse-hunks.json')
 for label,child,middle,accepted in [('semantic',d['semantic_reviewer'],'tools/m4-138-semantic-review/review_paired138_v2.py','tools/m4-tree-review/review_paired131_v3.py'),('MFC',d['MFC_reviewer'],'tools/m4-138-semantic-review/review_mfc_pair138_v1.py','tools/m4-tree-review/review_mfc_pair131.py')]:
  body=pin(child).read_text()
  if label=='semantic':
   body=inverse(body,read(prep.parent/'exact-two-delta-hunks.json'))
   assert body==pin(R/'tools/m4-138-semantic-review/review_paired138_v3.py').read_text()
  first=inverse(body,closing[label]);assert first==pin(R/middle).read_text()
  assert inverse(first,baseline[label])==pin(R/accepted).read_text()
 checks.append('Every semantic and MFC adaptation plus pre-import closure change inverts exactly to accepted131')
 assist=read(R/'reports/m4-138-semantic-review/root-assist-controller-r2/report.json','596cd4b1ef8b59dc325728b73834486290992709336d68aafd4f612b55d5407a');assert assist['passed']and assist['independent_review'];collect(assist)
 actual=read(R/'reports/m4-138-semantic-review/root-ordinary-assist-r2/report.json','bc1b2fbe683f873bd9f6c98f240ff48ea97ac2c416c26a570ac8ff9ef7c70be3');assert actual['passed'];collect(actual)
 assert len(actual['controls'])==14 and all(r['refused']is True for r in actual['controls'])and actual['formatter_controls']==504
 assert actual['current_compiled_provider_spans']==4 and actual['whole_RW_bytes']==actual['whole_IAT_bytes']==4096
 checks.append('Fresh ROOT physical bootstrap/build/four observer spans and518 semantic mutation controls')
 required=R/'reports/m4-138-semantic-review/minimal-MFC-admission-closure-r1/required-files.json'
 extras=read(required)
 for p,row in extras.items():pin(p,row['sha256'])
 assert len([p for p in extras if Path(p).name in('index.json','payload.bin')])==6
 checks.append('Allthree sealed ordinary raw indices and entire payloads freshly hashed before MFC replay')
 paired=read(R/'reports/m4-startup138-paired/paired-r5/report.json','5d5a4e5082512617f972e383868004d3c1fbbc79fe1679d365431ab119d8a42e')
 config=read(paired['configuration_path'],paired['configuration_sha256'])
 for row in config.values():
  if isinstance(row,dict)and'path'in row:
   gate=read(row['path'],row['sha256']);assert gate['passed'];collect(gate)
 # Current source/report and physical-model sets are admitted; archives stay
 # outside this bounded review and remain mandatory in final acceptance.
 for p in ('reports/m4-startup138-original/mfc-source-r2/report.json','reports/m4-startup138-original/original-validation-r3/report.json','reports/m4-joint-startup138/preparation-r4/report.json'):
  gate=read(R/p);assert gate['passed'];collect(gate)
 manifest=read(R/'reports/m4-138-semantic-review/complete-admission-manifest-r1/report.json','d491d7e750eff1d8b457d8b99529435d572ca7cd03ffc51ae0893e2ae23466ba');assert manifest['passed'];collect(manifest)
 whole=read(R/'reports/m4-138-semantic-review/complete-admission-manifest-r1/required-files.json');assert len(whole)==8901
 for path,digest in whole.items():pin(path,digest)
 checks.append('Complete8901 ordinary current external dependencies including retained helper and nested import closure')
 for p,h in tuple(pins.items()):assert sha(p)==h
 pin(__file__);passed=True
except Exception:(out/'failure.txt').write_text(traceback.format_exc())
report=dict(passed=passed,independent_review=True,semantic_preparation_sha256=sha(R/'reports/m4-138-semantic-review/preparation-r4/report.json'),checks=checks,semantic_main_admitted=passed,semantic_main_executed=False,canonical_reader_opened=False,initializer_credit=0,files=pins)
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,files=len(pins),report_sha256=sha(out/'report.json'))))
raise SystemExit(0 if passed else 1)
