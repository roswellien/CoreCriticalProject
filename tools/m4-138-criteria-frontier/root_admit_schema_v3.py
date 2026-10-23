"""Independently retain parent five blocks and admit exact owner/TLS join."""
from pathlib import Path
import ast,json,hashlib,traceback
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
out=R/'reports/m4-138-criteria-frontier/root-schema-admission-r3';assert not out.exists();out.mkdir();pins={};checks=[];passed=False
def pin(p,h=None):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json'
 v=sha(p);assert h is None or h==v,(p,h,v);assert pins.setdefault(str(p),v)==v;return p
def receipt(rel,h):
 p=pin(R/rel,h);d=json.loads(p.read_bytes());assert d['passed']
 for q,v in d['files'].items():pin(q,v)
 return d
try:
 parent=receipt('reports/m4-138-criteria-frontier/root-schema-admission-r2/report.json','1b3cf5498c45f17be491c50e81eb75955cb8e51d95d579136bc0d8f33e1f8da6')
 d=receipt('reports/m4-138-criteria-frontier/schema-checker-preparation-r4/report.json','292b94cf8caeed8f7871e4ee952d10e1caaf7af3deb2bb0b52d99a3cbf3844ca')
 assert d['whole_extracted_baseline_predicates_preserved']
 new=R/'reports/m4-138-criteria-frontier/schema-checker-preparation-r4';old=new.with_name('schema-checker-preparation-r3')
 for name in ('accepted131-materialized.py','native-inputs.py','native-TLS.py','native-boundary.py','native-graph.py','inputs.json'):assert pin(new/name).read_bytes()==pin(old/name).read_bytes()
 linked=pin(new/'native-linked.py').read_text();ast.parse(linked);delta=d['changes']
 for a,b in [(x['before'],x['after'])for x in reversed(delta)]:
  assert linked.count(b)==1;linked=linked.replace(b,a)
 assert linked==pin(old/'native-linked.py').read_text()
 checks.append('All five accepted131 predicate blocks retained through admitted parent; only exact whole owning function/TLS attribution added')
 tool=pin(R/'tools/m4-138-criteria-frontier/check_schema138_v3.py','517c18c1ff14151fabb98326ffed73f8da0acbac4b85fb50961c7dfdec4b05ef')
 ast.parse(tool.read_text())
 c=receipt('reports/m4-138-criteria-frontier/schema-synthetic-preflight-r3/report.json','d41232cb5bc5ddf19a319af938f2610c056faa46d7c6829ca54a37b91a0e2d0f')
 checks.append('Four target/inverse/adverse controls retained; actual current PE measurements remain required')
 for p,h in tuple(pins.items()):assert sha(p)==h
 pin(__file__);passed=True
except Exception:(out/'failure.txt').write_text(traceback.format_exc())
(out/'report.json').write_text(json.dumps(dict(passed=passed,independent_review=True,checks=checks,code_admitted=passed,current_measurements_executed=False,criteria_allowances_created=False,canonical_reader_opened=False,initializer_credit=0,files=pins),indent=2)+'\n')
print(json.dumps(dict(passed=passed,files=len(pins),report_sha256=sha(out/'report.json'))))
raise SystemExit(0 if passed else 1)
