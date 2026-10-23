"""Independently retain parent five blocks and admit exact owner/TLS join."""
from pathlib import Path
import ast,json,hashlib,traceback
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
out=R/'reports/m4-138-criteria-frontier/root-schema-admission-r2';assert not out.exists();out.mkdir();pins={};checks=[];passed=False
def pin(p,h=None):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json'
 v=sha(p);assert h is None or h==v,(p,h,v);assert pins.setdefault(str(p),v)==v;return p
def receipt(rel,h):
 p=pin(R/rel,h);d=json.loads(p.read_bytes());assert d['passed']
 for q,v in d['files'].items():pin(q,v)
 return d
try:
 parent=receipt('reports/m4-138-criteria-frontier/root-schema-admission-r1/report.json','7cd49572ab802e2c024357ddba278b630657956493a9c93af39f47ba83d3a3e7')
 d=receipt('reports/m4-138-criteria-frontier/schema-checker-preparation-r3/report.json','f278ee71f41a498ea9047008f86afd7b28d1f00cf4332812ec54140248805464')
 assert d['whole_extracted_baseline_predicates_preserved']
 new=R/'reports/m4-138-criteria-frontier/schema-checker-preparation-r3';old=new.with_name('schema-checker-preparation-r2')
 for name in ('accepted131-materialized.py','native-inputs.py','native-TLS.py','native-boundary.py','native-graph.py','inputs.json'):assert pin(new/name).read_bytes()==pin(old/name).read_bytes()
 linked=pin(new/'native-linked.py').read_text();ast.parse(linked);delta=d['linked_delta']
 for a,b in ((delta['old_case'],delta['new_case']),(delta['before'],delta['after'])):
  assert linked.count(b)==1;linked=linked.replace(b,a)
 assert linked==pin(old/'native-linked.py').read_text()
 checks.append('All five accepted131 predicate blocks retained through admitted parent; only exact whole owning function/TLS attribution added')
 tool=pin(R/'tools/m4-138-criteria-frontier/check_schema138_v3.py','517c18c1ff14151fabb98326ffed73f8da0acbac4b85fb50961c7dfdec4b05ef')
 ast.parse(tool.read_text())
 c=receipt('reports/m4-138-criteria-frontier/schema-synthetic-preflight-r2/report.json','72f57c671f77a8bbf20254676f3d47fd8a6bf5b6789d062371da63825b58c4dd')
 checks.append('Seven inverse/adverse controls retained; actual current PE measurements remain required')
 for p,h in tuple(pins.items()):assert sha(p)==h
 pin(__file__);passed=True
except Exception:(out/'failure.txt').write_text(traceback.format_exc())
(out/'report.json').write_text(json.dumps(dict(passed=passed,independent_review=True,checks=checks,code_admitted=passed,current_measurements_executed=False,criteria_allowances_created=False,canonical_reader_opened=False,initializer_credit=0,files=pins),indent=2)+'\n')
print(json.dumps(dict(passed=passed,files=len(pins),report_sha256=sha(out/'report.json'))))
raise SystemExit(0 if passed else 1)
