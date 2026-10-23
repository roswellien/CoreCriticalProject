"""ROOT admission of the carried141 consumer; no capture access in this step."""
from pathlib import Path
import ast, hashlib, json, sys, traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-141-consumer-review/root-source-admission-r3'
 assert not out.exists();out.mkdir(parents=True)
 pins={};checks=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve()
  assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json',p
  v=sha(p);assert h is None or h==v,(p,h,v)
  assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def receipt(p,h=None):
  d=json.loads(pin(R/p,h).read_bytes());assert d['passed'],p
  for q,v in d.get('files',{}).items():pin(q,v)
  return d
 try:
  prep=receipt('reports/m4-startup141-source/preparation-r6/report.json','08f2ea8a1940bfd20c4b3036a834fccd1b4330093d35751499607089a6e2058c')
  driver=pin(prep['entrypoint']);text=driver.read_text()
  deltas=json.loads(pin(driver.parent/'driver-deltas.json').read_bytes());assert len(deltas)==28
  inverse=text
  for row in reversed(deltas):
   assert inverse.count(row['new'])==row['count'],row
   inverse=inverse.replace(row['new'],row['old'])
  parent=pin(R/'reports/m4-joint-startup138-source/preparation-r11/compare_provider138.py','093dbb3ddac7cab868058c45f6b7a14280a8a2a49ee33b06d5d931345b79e0d2')
  assert inverse==parent.read_text();checks.append('All28 exact inverse adaptations retain complete source6')
  tree=ast.parse(text);mainnode=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
  calls=[n for n in ast.walk(mainnode)if isinstance(n,ast.Call)]
  closure=next(n for n in calls if isinstance(n.func,ast.Attribute)and n.func.attr=='pin_current_inputs')
  readers=[n for n in calls if isinstance(n.func,ast.Attribute)and n.func.attr=='DirectSet']
  assert len(readers)==2 and all(closure.lineno<n.lineno for n in readers)
  assert 'original_constructor_equivalence=False'in text and 'candidate_AFTER_machine_seed=False'in text
  assert "machine.bytes(0x5f2000,4096)"in text and "counts['whole_constructor_global_BEFORE']==counts['whole_constructor_global_AFTER']==1692"in text
  checks.append('Pre-reader child closure, whole constructor global endpoints, and genuine-original scope retained')
  for p in ('reports/m4-141-consumer-review/closure-preparation-r2/report.json','reports/m4-141-consumer-review/review-r4/report.json','reports/m4-141-consumer-review/closure-wiring-r1/report.json','reports/m4-141-consumer-review/closure-controls-r2/report.json','reports/m4-startup141-source/export-root-review-r1/report.json','reports/m4-native141-source/observer-preparation-r6/report.json','reports/m4-138-validation-review/constructor-source-dependency-review-r8/report.json','reports/m4-138-validation-review/constructor-provider-named-proof-r1/report.json'):
   receipt(p)
  receipt('reports/m4-141-consumer-review/FS-domain-preparation-r2/report.json','3e756e0c847baf33857b33c9b29471ed3085c59fda75d9e46873acf5e4e7862a')
  receipt('reports/m4-141-consumer-review/FS-domain-controls-r2/report.json','02d8aa0dd07c3721b25c3f060f9528ed945ed19992f2bc78cf6259461b142b17')
  diagnostic=R/'reports/m4-141-consumer-review/root-FS-diagnostic-r2/report.json'
  raw=json.loads(pin(diagnostic,'a5a5319dba8c8b7c107e50afd876a3567e5111c64c3780dacaa749d895ba7f2d').read_bytes())
  assert raw['passed']and raw['reader_closed']and raw['actual_global_frames']==28 and raw['actual_global_records']==56 and raw['constructor_frames_in_global_journal']==0
  for value in raw['logical_outputs'].values():pin(value['file'],value['sha256'])
  delta=json.loads(pin(R/'reports/m4-141-consumer-review/FS-domain-preparation-r2/deltas.json').read_bytes())
  helper=pin(R/'tools/m4-native141-source/constructor_fs_union141_v3.py').read_text()
  for row in reversed(delta['helper']):
   assert helper.count(row['new'])==1;helper=helper.replace(row['new'],row['old'])
  assert helper==pin(R/'tools/m4-native141-source/constructor_fs_union141_v2.py').read_text()
  observer=pin(prep['observer']).read_text()
  for row in reversed(delta['observer']):
   assert observer.count(row['new'])==row['count'];observer=observer.replace(row['new'],row['old'])
  assert observer==pin(R/'tools/m4-native141-source/final_observer141_v8.py').read_text()
  edits=json.loads(pin(R/'reports/m4-141-consumer-review/FS-domain-preparation-r1/observer-deltas.json').read_bytes())
  for row in reversed(edits):
   assert observer.count(row['new'])==row['count'];observer=observer.replace(row['new'],row['old'])
  assert observer==pin(R/'tools/m4-native141-source/final_observer141_v7.py').read_text()
  checks.append('Actual normal28/56 and source-derived constructor7/21/14 separate journals; entire observer7 body retained')
  # Re-execute inspected failure controls with a fresh ROOT output. Only the
  # output destination changes; the source helper and receipt inputs are exact.
  source=pin(R/'tools/m4-141-consumer-review/FS_domain_controls_v2.py')
  old="out=R/'reports/m4-141-consumer-review/FS-domain-controls-r2'"
  new="out=R/'reports/m4-141-consumer-review/root-FS-domain-controls-r2'"
  code=source.read_text();assert code.count(old)==1
  derivative=out/'FS-controls.py';anchor="obs=[e for v in rows for e in v['game_FS_observations']];checks=[]"
  assert code.count(anchor)==1
  actual="""
 physical_normal=R/'reports/m4-141-consumer-review/root-FS-diagnostic-r2'
 data[stem+'fs-frame-witnesses.bin']=(physical_normal/'fs-frame-witnesses.bin').read_bytes()
 data[stem+'fs-record-bytes.bin']=(physical_normal/'fs-record-bytes.bin').read_bytes()
 frames=list(struct.iter_unpack('<32Q',data[stem+'fs-frame-witnesses.bin']))
 records=list(struct.iter_unpack('<16Q',data[stem+'fs-record-bytes.bin']))
 """
  derivative.write_text(code.replace(old,new).replace(anchor,actual+anchor));pin(derivative)
  ns={'__name__':'root_FS_controls','__file__':str(source)}
  exec(compile(derivative.read_text(),str(derivative),'exec'),ns);ns['main']()
  controls=receipt('reports/m4-141-consumer-review/root-FS-domain-controls-r2/report.json')
  assert controls['controls']==11
  checks.append('Fresh11 controls using actual normal journal bytes reject wrong record bytes/handler/depth, missing events, fake normal rows and unreturned scopes')
  for p,h in tuple(pins.items()):assert sha(p)==h
  pin(__file__);passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc())
 report=dict(passed=passed,independent_review=True,consumer_preparation_sha256=sha(R/'reports/m4-startup141-source/preparation-r6/report.json'),checks=checks,source_consumer_admitted=passed,source_consumer_executed=False,canonical_reader_opened=False,original141_equivalence=False,initializer_credit=0,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':passed,'files':len(pins),'report_sha256':sha(out/'report.json')}))
 return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
