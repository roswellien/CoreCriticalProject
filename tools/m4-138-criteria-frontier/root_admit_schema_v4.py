"""ROOT whole retained schema blocks and exact two-file extension review."""
from pathlib import Path
import ast,json,hashlib,traceback,runpy,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
out=R/'reports/m4-138-criteria-frontier/root-schema-admission-r4';assert not out.exists();out.mkdir();pins={};passed=False;checks=[]
def pin(p,h=None):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or h==v;assert pins.setdefault(str(p),v)==v;return p
def receipt(rel,h):
 d=json.loads(pin(R/rel,h).read_bytes());assert d['passed']
 for p,h in d['files'].items():pin(p,h)
 return d
try:
 receipt('reports/m4-138-criteria-frontier/root-schema-admission-r3/report.json','001dcf86a94e7e88994253c240716a6a8040704a4288c9fa2eece7e3f78e874c')
 d=receipt('reports/m4-138-criteria-frontier/schema-checker-preparation-r6/report.json','e337ba3bd78f717dd25dc7888bb164042f9c01526d9e82db331f34787eea0549')
 a=R/'reports/m4-138-criteria-frontier/schema-checker-preparation-r4';b=a.with_name('schema-checker-preparation-r6')
 for name in ('accepted131-materialized.py','native-inputs.py','native-TLS.py','native-boundary.py','native-graph.py','native-linked.py','inputs.json'):assert pin(a/name).read_bytes()==pin(b/name).read_bytes()
 tool=pin(R/'tools/m4-138-criteria-frontier/check_schema138_v5.py','06343be28bc404d11cbaf923a098c894f91435d56f55198a8297ec17914d26df');text=tool.read_text();ast.parse(text)
 delta=d['checker_source_delta'];anchor=delta['anchor'];addition=delta['addition']
 assert text.count(anchor+addition)==1 and text.count(delta['after'])==1
 inverse=text.replace(anchor+addition,anchor).replace(delta['after'],delta['before'])
 base=pin(R/'tools/m4-138-criteria-frontier/check_schema138_v3.py','517c18c1ff14151fabb98326ffed73f8da0acbac4b85fb50961c7dfdec4b05ef')
 assert inverse==runpy.run_path(str(base),run_name='root_definition_only')['s']
 checks.append('Exact full current checker inverse; all previous whole linked bridge/target/unwind/TLS predicates retained')
 receipt('reports/m4-138-criteria-frontier/positive-files-preflight-r1/report.json','327c493959262b9cd51175429cbfa82f2de48d1f66b3cc5f9ab9d2b3a485e7f6')
 checks.append('Two genuine positive-file extensions require whole inverse and actual source-derived callback/page union; every inherited file remains required')
 for p,h in tuple(pins.items()):assert sha(p)==h
 pin(__file__);passed=True
except Exception:(out/'failure.txt').write_text(traceback.format_exc())
(out/'report.json').write_text(json.dumps(dict(passed=passed,independent_review=True,checks=checks,code_admitted=passed,current_measurements_executed=False,criteria_allowances_created=False,canonical_reader_opened=False,initializer_credit=0,files=pins),indent=2)+'\n')
print(json.dumps(dict(passed=passed,files=len(pins),report_sha256=sha(out/'report.json'))))
raise SystemExit(0 if passed else 1)
