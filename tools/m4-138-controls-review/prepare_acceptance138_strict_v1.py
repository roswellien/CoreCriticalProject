"""Additive source-only criteria repair; no real configuration or union run."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2];T=R/'tools/m4-138-controls-review'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def replace(text,a,b):
 assert text.count(a)==1,a;return text.replace(a,b)
def write(name,text):
 p=T/name;assert not p.exists();p.write_text(text);return p
old=T/'acceptance138_v2.py';s=old.read_text();changes=[]
def edit(a,b):
 global s
 s=replace(s,a,b);changes.append(dict(before=a,after=b))
edit('import acceptance138_storage_v2 as storage','import acceptance138_storage_v2 as storage\nimport acceptance138_criteria_v1 as criteria')
start=s.index('def baseline_criteria(config):');end=s.index('def additions(rows,gates):',start)
edit(s[start:end],"def baseline_criteria(config):\n old=read(ROOT/'reports/m4-joint-startup131-root/configuration-r1/configuration.json')\n return criteria.validate(config,old,BASE_REQUIRED)\n\n")
edit("baseline_criteria(config)\n","deltas=baseline_criteria(config)\n")
edit("review=read(review_path,review_sha);absorb(review)","review=read(review_path,review_sha);absorb(review);criteria.review_allowances(review,deltas)")
edit("for p in [Path(__file__),Path(storage.__file__)","for p in [Path(criteria.__file__),Path(__file__),Path(storage.__file__)")
edit("for p in [configuration,Path(__file__),Path(storage.__file__)","for p in [Path(criteria.__file__),configuration,Path(__file__),Path(storage.__file__)")
checker=write('acceptance138_v3.py',s)
inverse=s
for row in reversed(changes):inverse=replace(inverse,row['after'],row['before'])
assert inverse==old.read_text()
prior=T/'configure_acceptance138_v2.py';s=prior.read_text();configchanges=[]
def ce(a,b):
 global s
 s=replace(s,a,b);configchanges.append(dict(before=a,after=b))
ce('import acceptance138_v2 as A','import acceptance138_v3 as A')
a="   for field in baseline['gates'][label]['equal']:\n    relation=given.get(field,dict(current_field=field,reason='Same current receipt predicate path; current domain/value independently reviewed'))\n    need(set(relation)=={'current_field','reason'}and isinstance(relation['reason'],str)and relation['reason'].strip(),'Explicit reviewable field translation')\n    target=relation['current_field'];value=A.value_at(row,target);need(type(value)in(bool,int,str),'Typed ordinary measurable translated predicate');equal[target]=value;coverage[label][field]=relation"
b="   for field,old_expected in baseline['gates'][label]['equal'].items():\n    delta=given.get(field);target=field if delta is None else delta['current_field']\n    value=A.value_at(row,target);need(type(value)in(bool,int,str),'Typed ordinary measurable translated predicate')\n    relation=A.criteria.relation(field,old_expected,value,delta)\n    equal[target]=value;coverage[label][field]=relation"
ce(a,b)
ce(" specification=out/'review-specification.json';", " deltas=A.criteria.validate(dict(gates=gates,baseline_criteria=coverage),baseline,A.BASE_REQUIRED)\n specification=out/'review-specification.json';")
ce('baseline_criteria=coverage,mandatory_review=', 'baseline_criteria=coverage,required_exact_finite_delta_allowances=deltas,mandatory_review=')
ce("criteria_translation_reviewed=True)","criteria_translation_reviewed=True,criteria_delta_allowances=deltas)")
ce("for p in [Path(__file__).resolve(),Path(sys.executable)","for p in [Path(A.criteria.__file__),Path(__file__).resolve(),Path(sys.executable)")
configuration=write('configure_acceptance138_v3.py',s)
inverse=s
for row in reversed(configchanges):inverse=replace(inverse,row['after'],row['before'])
assert inverse==prior.read_text()
out=R/'reports/m4-138-controls-review/acceptance138-strict-criteria-preparation-r1';assert not out.exists();out.mkdir()
q=out/'source-delta.json';q.write_text(json.dumps(dict(checker=changes,configuration=configchanges),indent=2)+'\n')
pins={str(p.resolve()):sha(p)for p in [Path(__file__),old,prior,checker,configuration,T/'acceptance138_criteria_v1.py',T/'acceptance138_storage_v2.py',T/'acceptance138_storage.py',T/'acceptance138_semantics_v3.py',T/'expand_proof_inventory.py',T/'expand_accepted138_union.py',R/'tools/m4-joint-startup131/acceptance.py',R/'reports/m4-joint-startup131-root/configuration-r1/configuration.json',R/'reports/m4-joint-startup131-root/acceptance-r1/report.json',q,Path(sys.executable)]}
report=out/'report.json';report.write_text(json.dumps(dict(passed=True,scope='Exact inverse additive criteria-only preparation; prior semantic/storage/expansion bodies retained',checker_source_inverse=True,configuration_source_inverse=True,finite_delta_allowances_required=True,baseline_predicates=841,required_gates=39,acceptance_executed=False,configuration_executed=False,worker_executed=False,capture_reader_opened=False,initializer_credit=0,files=pins),indent=2)+'\n');print(json.dumps(dict(path=str(report),sha256=sha(report),checker_sha256=sha(checker),configuration_sha256=sha(configuration))))
