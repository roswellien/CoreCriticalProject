"""ROOT admission for bounded current named-domain physical schema review."""
from pathlib import Path
import ast,hashlib,json,textwrap,traceback
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
out=R/'reports/m4-138-criteria-frontier/root-schema-admission-r1';assert not out.exists();out.mkdir(parents=True);pins={};passed=False;checks=[]
def pin(p,h=None):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json'
 v=sha(p);assert h is None or h==v;(pins.setdefault(str(p),v));assert pins[str(p)]==v;return p
try:
 prep=R/'reports/m4-138-criteria-frontier/schema-checker-preparation-r2/report.json'
 d=json.loads(pin(prep,'f8f6a16f1cabe3309d8b78768b5948e4d5d83da2e920da1e67fdd12a58234f32').read_bytes());assert d['passed']and d['whole_extracted_baseline_predicates_preserved']
 for p,h in d['files'].items():pin(p,h)
 parent=pin(prep.parent/'accepted131-materialized.py','77c33bc8bca072a869df2d44b26875dd496fa672d9138b6de38d4b568c7d0768').read_text()
 anchors={'native-graph.py':("   assert len(prep['objects']","   component_object=pin("),'native-inputs.py':('  retained=read(','  main=pin('),'native-linked.py':('   component_object=pin(',"   db=pin(bf/'.ninja_deps')"),'native-TLS.py':('  TLS_names={',"  assert 'const Inputs input;'"),'native-boundary.py':('  boundary=pin(','  lift=read(')}
 for row in d['relations']:
  body=pin(prep.parent/row['file']).read_text();ast.parse(body)
  for change in reversed(row['changes']):assert change['after']in body;body=body.replace(change['after'],change['before'])
  a,b=anchors[row['file']];assert parent.count(a)==parent.count(b)==1
  assert body==textwrap.dedent(parent[parent.index(a):parent.index(b)])
 checks.append('Allfive exact full baseline predicate blocks restored including actual linker graph')
 tool=pin(R/'tools/m4-138-criteria-frontier/check_schema138_v2.py','6a25b1108de0cbf5bfab9eef54a2266af782877b94a26a70d52e84b65e2ff1f2')
 base=pin(R/'tools/m4-138-criteria-frontier/check_schema138_v1.py','f549f36a03a2a6c5123b2f29dc86f76eec14f2c445f1307972afbadc0d895ea8').read_text()
 assert "subprocess.run([str(ninja),'-C',str(bf),'-t','deps']"in base
 assert 'allowance_created=False'in base and 'acceptance_executed=False'in base
 assert "'No duplicate physical identity'"in base
 controls=R/'reports/m4-138-criteria-frontier/schema-synthetic-preflight-r1/report.json'
 c=json.loads(pin(controls,'8cc08f0c0f11debb41f660919b80b2c3937d42991d63042c650b1007abeb91c7').read_bytes());assert c['passed']
 for p,h in c['files'].items():pin(p,h)
 for p,h in tuple(pins.items()):assert sha(p)==h
 pin(__file__);passed=True
except Exception:(out/'failure.txt').write_text(traceback.format_exc())
(out/'report.json').write_text(json.dumps(dict(passed=passed,independent_review=True,checks=checks,code_admitted=passed,current_measurements_executed=False,criteria_allowances_created=False,canonical_reader_opened=False,initializer_credit=0,files=pins),indent=2)+'\n');print(json.dumps({'passed':passed,'files':len(pins),'report_sha256':sha(out/'report.json')}))
raise SystemExit(0 if passed else 1)
