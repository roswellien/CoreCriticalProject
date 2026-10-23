"""Independently check proposed841 field identities, without granting allowances."""
from pathlib import Path
import hashlib,json,traceback,collections
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
out=R/'reports/m4-138-criteria-frontier/root-proposal-review-r4';assert not out.exists();out.mkdir();pins={};passed=False
def read(p,h=None):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json'
 v=sha(p);assert h is None or v==h;pins[str(p)]=v;return json.loads(p.read_bytes())
def at(v,p):
 for k in p.split('.'):v=v[int(k)]if isinstance(v,list)else v[k]
 return v
try:
 p=R/'reports/m4-138-controls-review/criterion-delta-proposal-r5-r4'
 d=read(p/'report.json','9e4d9dd58f34bafae4c8a4368f1fbaa0c89b91ffd3ca1e895d14470505534f3d');assert d['passed']and not d['allowance_created']and not d['configuration_created']
 for q,h in d['files'].items():
  q=Path(q);assert q.suffix.lower()not in('.mwb','.mwi','.zip')and q.name!='transport.json';assert sha(q)==h;pins[str(q)]=h
 baseline=read(R/'reports/m4-joint-startup131-root/configuration-r1/configuration.json')
 rows=read(p/'criterion-841-proposal.json');gates=read(p/'candidate-33-gate-bindings.json')
 assert len(rows)==841 and {(r['gate'],r['baseline_field'])for r in rows}=={(g,f)for g,x in baseline['gates'].items()for f in x['equal']}
 measured={g:read(R/x['path'],x['sha256'])for g,x in gates.items()if x['path']is not None}
 counts=collections.Counter();paired=[]
 for row in rows:
  g=row['gate'];f=row['baseline_field'];old=baseline['gates'][g]['equal'][f]
  assert type(old)is type(row['baseline_expected'])and old==row['baseline_expected'];counts[row['status']]+=1
  if row['status']!='unresolved':
   target=read(row['current_report_path'],row['current_report_sha256'])if row.get('current_report_path')else measured[g]
   value=at(target,row['current_field']);assert type(value)is type(old)and value==row['current_expected']
   assert row['status']==('identity_candidate'if old==value else'finite_delta_candidate')
   if isinstance(old,bool):assert value==old
  if g=='paired_review':assert row['status']!='unresolved';paired.append(row)
 assert dict(counts)==d['status_counts']=={'identity_candidate':600,'finite_delta_candidate':182,'unresolved':59}and len(paired)==64
 for label in baseline['gates']:
  selected=[r['current_field']for r in rows if r['gate']==label and r['status']!='unresolved'];assert len(set(selected))==len(selected)
 assert len({x['current_field']for x in paired})==64
 assert measured['paired_review']['paired_report_sha256']=='5d5a4e5082512617f972e383868004d3c1fbbc79fe1679d365431ab119d8a42e'
 execution=read(R/'reports/m4-138-semantic-review/root-semantic-execution-r2/report.json','567944eef26f2d198ab61e80b662060fce85f651b963b044fdaee3416ff1aa66');assert execution['passed']and execution['exit_code']==0
 for q,h in tuple(pins.items()):assert sha(q)==h
 pins[str(Path(__file__).resolve())]=sha(__file__);passed=True
except Exception:(out/'failure.txt').write_text(traceback.format_exc())
(out/'report.json').write_text(json.dumps(dict(passed=passed,independent_review=True,typed_predicates=841,paired_review_fields=64,previously_missing_paired_review_fields=63,counts=dict(counts),authoritative_allowances_created=False,configuration_created=False,acceptance_executed=False,canonical_reader_opened=False,initializer_credit=0,files=pins),indent=2)+'\n')
print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'))))
raise SystemExit(0 if passed else 1)
