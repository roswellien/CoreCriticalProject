"""ROOT admission of the carried141 consumer; no capture access in this step."""
from pathlib import Path
import ast, hashlib, json, sys, traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-141-consumer-review/root-source-admission-r1'
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
  prep=receipt('reports/m4-startup141-source/preparation-r4/report.json','2a95f9bcbf1374bd6594685ffa690d995582c00cb1e58fd6c45da0d4dfcd5d58')
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
  for p in ('reports/m4-141-consumer-review/closure-preparation-r2/report.json','reports/m4-141-consumer-review/review-r4/report.json','reports/m4-141-consumer-review/closure-wiring-r1/report.json','reports/m4-141-consumer-review/closure-controls-r2/report.json','reports/m4-startup141-source/export-root-review-r1/report.json','reports/m4-native141-source/observer-preparation-r5/report.json','reports/m4-138-validation-review/constructor-source-dependency-review-r8/report.json','reports/m4-138-validation-review/constructor-provider-named-proof-r1/report.json'):
   receipt(p)
  # Re-execute inspected failure controls with a fresh ROOT output. Only the
  # output destination changes; the source helper and receipt inputs are exact.
  source=pin(R/'tools/m4-141-consumer-review/closure_controls_v2.py')
  old="out=R/'reports/m4-141-consumer-review/closure-controls-r2'"
  new="out=R/'reports/m4-141-consumer-review/root-closure-controls-r1'"
  code=source.read_text();assert code.count(old)==1
  derivative=out/'closure-controls.py';derivative.write_text(code.replace(old,new));pin(derivative)
  ns={'__name__':'root_controls','__file__':str(source)}
  exec(compile(derivative.read_text(),str(derivative),'exec'),ns);assert ns['main']()==0
  controls=receipt('reports/m4-141-consumer-review/root-closure-controls-r1/report.json')
  assert len(controls['checks'])==7
  checks.append('Fresh ROOT closure controls reject every changed helper and wrong loaded module path')
  for p,h in tuple(pins.items()):assert sha(p)==h
  pin(__file__);passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc())
 report=dict(passed=passed,independent_review=True,consumer_preparation_sha256=sha(R/'reports/m4-startup141-source/preparation-r4/report.json'),checks=checks,source_consumer_admitted=passed,source_consumer_executed=False,canonical_reader_opened=False,original141_equivalence=False,initializer_credit=0,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':passed,'files':len(pins),'report_sha256':sha(out/'report.json')}))
 return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
