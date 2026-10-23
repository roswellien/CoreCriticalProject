"""Admit complete source-owned five+two NULL container union; no reader."""
from pathlib import Path
import hashlib,json,traceback,ast
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
out=R/'reports/m4-141-consumer-review/root-source-admission-r7';assert not out.exists();out.mkdir();pins={};checks=[];passed=False
def pin(p,h=None):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or h==v;assert pins.setdefault(str(p),v)==v;return p
def receipt(rel,h):
 d=json.loads(pin(R/rel,h).read_bytes());assert d['passed']
 for p,v in d.get('files',{}).items():pin(p,v)
 return d
def inverse(body,rows,parent,n):
 assert len(rows)==n;ast.parse(body)
 for row in reversed(rows):assert body.count(row['new'])==row['count'];body=body.replace(row['new'],row['old'])
 assert body==pin(parent).read_text()
try:
 receipt('reports/m4-141-consumer-review/root-source-admission-r6/report.json','57bcbec907ade6e626105f231f3a46821fc1716acb3da7f537d21ed2b26d8056')
 prep=receipt('reports/m4-startup141-source/preparation-r9/report.json','b4fc36e6aeb7293b310f59a4fecbc33bfcc9aa31006e5ae12fb610819b48621c')
 review=receipt('reports/m4-141-consumer-review/container-union-preparation-r1/report.json','6ab3a0fff3bce22cd0fd08d0bc8a98737553490ed737cdda70d8449b284b2768')
 folder=R/'reports/m4-141-consumer-review/container-union-preparation-r1'
 model=pin(R/'tools/m4-native141-source/container_events141_v1.py','32a8dedbc127051d7efafed73bb7645625833484f4172584ad7144cb827554f6')
 inverse(model.read_text(),json.loads(pin(folder/'model-deltas.json').read_bytes()),R/'tools/m4-vtable-review/event_model.py',4)
 inverse(pin(prep['observer']).read_text(),json.loads(pin(folder/'observer-deltas.json').read_bytes()),R/'tools/m4-native141-source/final_observer141_v11.py',5)
 inverse(pin(prep['entrypoint']).read_text(),json.loads(pin(Path(prep['entrypoint']).parent/'driver-deltas.json').read_bytes()),R/'reports/m4-joint-startup138-source/preparation-r11/compare_provider138.py',28)
 producer=pin(R/'reports/m4-startup141-runway/service-preparation-r2/container_operations.inc').read_text()
 assert 'registry_root_'in producer and 'container_nulls_'in producer
 checks.append('Exact4 full retained container model and5 observer inverses plus28 source6 driver inverse; ROOT source/container scope is explicit five inherited +two logical constructor/root0 borrowed body rows')
 source=pin(R/'tools/m4-141-consumer-review/container_union_controls_v1.py');code=source.read_text();assert code.count('container-union-controls-r1')==1;code=code.replace('container-union-controls-r1','root-container-union-controls-r1');q=out/'controls.py';q.write_text(code);pin(q)
 ns={'__name__':'root_container_controls','__file__':str(source)};exec(compile(code,str(q),'exec'),ns);ns['main']()
 c=receipt('reports/m4-141-consumer-review/root-container-union-controls-r1/report.json',None);assert c['controls']==101 and c['source_API_generation_live_counters_synthetic']and not c['actual_source_equivalence_claim']
 checks.append('Fresh101 source-event counterfactual and whole actual diagnostic comparison adverses; all fields/cardinalities preserved, counters are explicitly synthetic')
 for p,h in tuple(pins.items()):assert sha(p)==h
 pin(__file__);passed=True
except Exception:(out/'failure.txt').write_text(traceback.format_exc())
(out/'report.json').write_text(json.dumps(dict(passed=passed,independent_review=True,checks=checks,source_consumer_admitted=passed,source_consumer_executed=False,canonical_reader_opened=False,original141_equivalence=False,initializer_credit=0,files=pins),indent=2)+'\n')
print(json.dumps(dict(passed=passed,files=len(pins),report_sha256=sha(out/'report.json'))));raise SystemExit(0 if passed else 1)
