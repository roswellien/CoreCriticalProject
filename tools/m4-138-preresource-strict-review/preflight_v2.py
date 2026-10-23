"""Immutable current helper binding; bounded named retry-scope mutation controls."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=Path(__file__).with_name('preflight_v1.py');s=p.read_text()
changes=[("schema-preflight-r1","schema-preflight-r2"),("p=R/'tools/m4-138-preresource-strict-review/ordinary_case.py'","p=R/'reports/m4-138-preresource-strict-review/preparation-r2/ordinary_case_v2.py'"),("preparation-r1/report.json","preparation-r4/report.json"),("v['whole_parent_inverse']","v['whole_parent_inverse']"),("verify_case_v1.py","verify_case_v4.py")]
for a,b in changes:
 if a==b:continue
 assert s.count(a)>=1;s=s.replace(a,b)
marker=' checks=[]'
replacement=""" checks=[]
 domains=('State3504','CPU40','FX512','ENV28','Runtime-calls','memory-index','whole-memory-page','Registry-private-vector','MFC-source-ledger','Widget-FS-ledger','Widget-format-dispatches','Widget-font-vector')"""
assert s.count(marker)==1;s=s.replace(marker,replacement)
needle=" reject('short-entry64',lambda:m.frame64(frame[:-1],cpu,bytes(page)))"
extra="""
 for domain in domains:
  d={'before/'+domain:b'own-complete-field','after/'+domain:b'own-complete-field'}
  assert m.retry_scope(Schema(d),'before/','after/',(domain,))==1
  bad=dict(d);bad['after/'+domain]=b'X'+bad['after/'+domain][1:]
  reject('changed-whole-'+domain,lambda bad=bad,domain=domain:m.retry_scope(Schema(bad),'before/','after/',(domain,)))
  bad=dict(d);bad.pop('after/'+domain)
  reject('missing-after-'+domain,lambda bad=bad,domain=domain:m.retry_scope(Schema(bad),'before/','after/',(domain,)))"""
assert s.count(needle)==1;s=s.replace(needle,needle+extra)
exec(compile(s,str(Path(__file__).resolve()),'exec'),globals())
