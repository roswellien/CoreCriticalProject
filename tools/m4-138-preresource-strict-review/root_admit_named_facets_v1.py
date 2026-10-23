"""ROOT exact named-facet source/audit inverses, whole inputs, pure controls."""
from pathlib import Path
import hashlib,json,sys,ast
R=Path(__file__).resolve().parents[2]
def main():
 base=R/'reports/m4-138-preresource-strict-review';prepdir=base/'named-facets-preparation-r3';out=base/'root-named-facets-admission-r1';assert not out.exists();files={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json'
  with p.open('rb')as f:v=hashlib.file_digest(f,'sha256').hexdigest()
  assert h is None or v==h;assert files.setdefault(str(p),v)==v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 prep=read(prepdir/'report.json','efeb9f04dd5f1fbc9370ebf5b6796269300cb4b16108e706e03f714ae1466e18');assert prep['passed']and prep['exact_hunks']==6 and not prep['checker_executed']
 for p,h in prep['files'].items():pin(p,h)
 required=read(prepdir/'required-ordinary-input-map.json','795bf72ebed232f524fbfcccc6f83b4a1d3867b61fb5fc5a98834e00ff364dbd')
 for p,h in required.items():pin(p,h)
 def inverse(parent,child,deltas):
  a=pin(parent).read_text();b=pin(child).read_text()
  for d in reversed(deltas):assert b.count(d['after'])==1;b=b.replace(d['after'],d['before'])
  assert b==a;ast.parse(pin(child).read_text())
 inverse(R/'tools/m4-138-preresource-strict-review/review_named_facets_v1.py',prepdir/'review_named_facets_v3.py',read(prepdir/'whole-source-inverse.json'))
 inverse(R/'tools/m4-138-preresource-strict-review/source_read_audit_v1.py',R/'tools/m4-138-preresource-strict-review/source_read_audit_v2.py',read(prepdir/'audit-helper-whole-inverse.json'))
 # The source model is never imported here. Exercise the actual pure read
 # authority, without installing its process audit or opening any raw files.
 ap=pin(R/'tools/m4-138-preresource-strict-review/source_read_audit_v2.py');ns={'__file__':str(ap)};exec(compile(ap.read_bytes(),str(ap),'exec'),ns)
 declared=R/'named-control-source.py';raw=R/'named-control-raw.bin';receipt=R/'named-control-strict.json';policy=ns['Reads']({str(declared):'a',str(receipt):'b'},out);tests=[]
 def test(label,action,exception=None):
  try:action()
  except BaseException as e:assert exception is not None and isinstance(e,exception)
  else:assert exception is None
  tests.append(dict(name=label,passed=True))
 test('Declared source read',lambda:policy.audit('open',(str(declared),'rb',0)))
 test('Fresh own output read',lambda:policy.audit('open',(str(out/'own.json'),'rb',0)))
 test('Undeclared source refused',lambda:policy.audit('open',(str(R/'not-declared.py'),'rb',0)),PermissionError)
 test('Cached bytecode forces source compilation',lambda:policy.audit('open',(str(declared.with_suffix('.pyc')),'rb',0)),FileNotFoundError)
 test('Canonical transport refused',lambda:policy.audit('open',(str(out/'transport.json'),'rb',0)),PermissionError)
 test('Raw before exact declaration refused',lambda:policy.begin_hash(raw,'c'),ValueError)
 test('Wrong strict receipt refused',lambda:policy.select_case({str(raw):'c'},receipt,'wrong'),ValueError)
 policy.select_case({str(raw):'c'},receipt,'b')
 test('Different raw hash refused',lambda:policy.begin_hash(raw,'wrong'),ValueError)
 test('Exact scoped raw hash grant',lambda:policy.begin_hash(raw,'c'))
 policy.audit('open',(str(raw),'rb',0));policy.end_hash(raw,'c','c')
 test('Verified raw final rehash read',lambda:policy.audit('open',(str(raw),'rb',0)))
 assert len(tests)==10
 pin(__file__);pin(sys.executable)
 for p,h in list(files.items()):pin(p,h)
 out.mkdir();q=out/'report.json';q.write_text(json.dumps(dict(passed=True,independent_review=True,scope_identity='current138_preresource_named_facets',whole_checker_inverse_hunks=6,whole_audit_inverse_hunks=3,pure_production_read_authority_controls=tests,checker_executed=False,worker_executed=False,canonical_reader_opened=False,accepted_function_credit=0,files=files),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest(),files=len(files))))
if __name__=='__main__':main()
