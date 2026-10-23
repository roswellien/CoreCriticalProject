"""ROOT whole retained schema blocks and exact two-file extension review."""
from pathlib import Path
import ast,json,hashlib,traceback,runpy,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
out=R/'reports/m4-138-criteria-frontier/root-schema-admission-r5';assert not out.exists();out.mkdir();pins={};passed=False;checks=[]
def pin(p,h=None):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or h==v;assert pins.setdefault(str(p),v)==v;return p
def receipt(rel,h):
 d=json.loads(pin(R/rel,h).read_bytes());assert d['passed']
 for p,h in d['files'].items():pin(p,h)
 return d
try:
 receipt('reports/m4-138-criteria-frontier/root-schema-admission-r4/report.json','da06bc10f7e576d95f6ab22a1b25d9999199b37ecb58f812f9094d1c1aa244d8')
 d=receipt('reports/m4-138-criteria-frontier/schema-checker-preparation-r7/report.json','21204a6c0511100caae296f557710124de7f2d35d2223cf365d715ef54af4d11')
 a=R/'reports/m4-138-criteria-frontier/schema-checker-preparation-r6';b=a.with_name('schema-checker-preparation-r7')
 for name in ('accepted131-materialized.py','native-inputs.py','native-TLS.py','native-boundary.py','native-graph.py','native-linked.py','inputs.json'):assert pin(a/name).read_bytes()==pin(b/name).read_bytes()
 tool=pin(R/'tools/m4-138-criteria-frontier/check_schema138_v6.py','737749fb40562ed9ce89a3d1b9944e41eb936e158810101b097415cca6dbda09');text=tool.read_text();ast.parse(text)
 delta=d['checker_source_delta']
 assert text.count(delta['after'])==1
 inverse=text.replace(delta['after'],delta['before'])
 base=pin(R/'tools/m4-138-criteria-frontier/check_schema138_v5.py','06343be28bc404d11cbaf923a098c894f91435d56f55198a8297ec17914d26df')
 assert inverse==base.read_text()
 checks.append('Exact full current checker inverse; all previous whole linked bridge/target/unwind/TLS predicates retained')
 receipt('reports/m4-138-criteria-frontier/tlog-preflight-r1/report.json','c2240b835d00c51b07a546443c36bf7e13af56714614f1e942967e4b4ddb4734')
 checks.append('Actual successful compiler command, project source/IntDir, linked byte identity and worker tlog ownership required; consumed266 domain preserved')
 for p,h in tuple(pins.items()):assert sha(p)==h
 pin(__file__);passed=True
except Exception:(out/'failure.txt').write_text(traceback.format_exc())
(out/'report.json').write_text(json.dumps(dict(passed=passed,independent_review=True,checks=checks,code_admitted=passed,current_measurements_executed=False,criteria_allowances_created=False,canonical_reader_opened=False,initializer_credit=0,files=pins),indent=2)+'\n')
print(json.dumps(dict(passed=passed,files=len(pins),report_sha256=sha(out/'report.json'))))
raise SystemExit(0 if passed else 1)
