"""Tighten exact case-scoped hash grants and audit bootstrap source-only."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2]
parent=R/'tools/m4-138-preresource-strict-review/source_read_audit_v1.py';old=parent.read_text();s=old
changes=[
 ('self.hashing=set();self.reads=set();self.pyc_refusals=set()','self.hashing=set();self.reads=set();self.pyc_refusals=set();self.case_allowed={}'),
 (' def begin_hash(self,p,expected):',""" def select_case(self,allowed,receipt,receipt_sha):
  key=str(Path(receipt).resolve())
  if self.declared.get(key)!=receipt_sha:raise ValueError('Exact current strict receipt must be ROOT-declared and already whole-hashed')
  self.case_allowed={str(Path(p).resolve()):h for p,h in allowed.items()}
 def begin_hash(self,p,expected):"""),
 ("  if key in self.declared and self.declared[key]!=expected:raise ValueError('Root ordinary declaration identity differs')", """  if key in self.declared and self.declared[key]!=expected:raise ValueError('Root ordinary declaration identity differs')
  if key not in self.declared and not p.is_relative_to(self.out) and self.case_allowed.get(key)!=expected and self.verified_raw.get(key)!=expected:raise ValueError('Raw hash requires exact SAME-case streamed declaration or already verified final-rehash proof')"""),
]
for a,b in changes:assert s.count(a)==1;s=s.replace(a,b)
inverse=s
for a,b in reversed(changes):assert inverse.count(b)==1;inverse=inverse.replace(b,a)
assert inverse==old;ast.parse(s)
helper=parent.with_name('source_read_audit_v2.py');assert not helper.exists();helper.write_text(s)
p=R/'tools/m4-138-preresource-strict-review/prepare_named_facets_v2.py';t=p.read_text()
assert t.count('named-facets-preparation-r2')==1;t=t.replace('named-facets-preparation-r2','named-facets-preparation-r3')
assert t.count('review_named_facets_v2.py')==1;t=t.replace('review_named_facets_v2.py','review_named_facets_v3.py')
assert t.count('source_read_audit_v1.py')==2;t=t.replace('source_read_audit_v1.py','source_read_audit_v2.py')
a="  Audit=module(R/'tools/m4-138-preresource-strict-review/source_read_audit_v2.py','named_source_read_audit')"
b="  audit_source=ordinary(R/'tools/m4-138-preresource-strict-review/source_read_audit_v2.py');audit_ns={'__file__':str(audit_source)};exec(compile(audit_source.read_bytes(),str(audit_source),'exec'),audit_ns)"
assert t.count(a)==1;t=t.replace(a,b);assert t.count('audit_policy=Audit.Reads(')==1;t=t.replace('audit_policy=Audit.Reads(',"audit_policy=audit_ns['Reads'](")
needle=' inverse=s\n for d in reversed(deltas):'
replacement=""" replace("   assert str(causal_path)in allowed;case_data=json.loads", "   audit_policy.select_case(allowed,rp,row['sha256'])\\n   assert str(causal_path)in allowed;case_data=json.loads")
 inverse=s
 for d in reversed(deltas):"""
assert t.count(needle)==1;t=t.replace(needle,replacement)
ns={'__file__':str(Path(__file__).resolve()),'__name__':'prepare_only'};exec(compile(t,str(p),'exec'),ns);ns['main']()
out=R/'reports/m4-138-preresource-strict-review/named-facets-preparation-r3';delta=out/'audit-helper-whole-inverse.json';delta.write_text(json.dumps([dict(before=a,after=b)for a,b in changes],indent=2)+'\n')
pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in(parent,helper,Path(__file__).resolve(),delta,out/'report.json',R/'reports/m4-138-preresource-strict-review/named-facets-preparation-r2/review_named_facets_v2.py')}
q=out/'source-audit-binding-preparation.json';q.write_text(json.dumps(dict(passed=True,scope='Exact source-only audit bootstrap and case-scoped hash grants; no checker run',whole_audit_helper_inverse=True,helper_exact_hunks=3,raw_hash_requires_same_case_declaration=True,all_cached_pyc_refused=True,checker_executed=False,worker_executed=False,canonical_reader_opened=False,ROOT_admission_created=False,files=pins),indent=2)+'\n');print(hashlib.sha256(q.read_bytes()).hexdigest())
