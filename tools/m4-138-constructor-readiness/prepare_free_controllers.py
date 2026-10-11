"""Path/hash-only controller and checker binding; independent review still pending."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
BUILD='0f5761af58092ef55ccd265ed0acf5a0bbdead40fab96cdb87eccb79f99f1d18'
PREP='f0dfc1427c9cca0c1b920be6fc030c6b9bb7e53ef631946abcbf4ddf215001a0'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-138-constructor-readiness'/name;assert not out.exists();pins={};derivatives=[]
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or v==h,str(p);pins[str(p)]=v;return p
 changes=[('fixture-build-r9/build.json','fixture-build-r10/build.json'),('fixture-preparation-r5/report.json','fixture-preparation-r6/report.json')]
 for parent_name,child_name,extra in [('run_fixture_v3.py','run_fixture_v4.py',[
     ('4bbe778a6938db08f3e583d98dd31429c1bbbf0d0a4de6475edd0e6a758ef805',BUILD),
     ('31b3f6b5ce2f8af0bb43dbcf7b983629c6978f2d1fcf71c25f14efc6750682a1',PREP)]),
    ('validate_fixture_v4.py','validate_fixture_v5.py',[])]:
  parent=pin(R/'tools/m4-constructor-native'/parent_name);child=R/'tools/m4-constructor-native'/child_name;assert not child.exists()
  original=parent.read_text();source=original;deltas=[]
  for before,after in changes+extra:
   count=source.count(before);assert count>0,(parent_name,before);source=source.replace(before,after);deltas.append(dict(before=before,after=after,occurrences=count))
  restored=source
  for row in reversed(deltas):assert restored.count(row['after'])==row['occurrences'];restored=restored.replace(row['after'],row['before'])
  assert restored==original,'Exact reverse delta restores all previous predicates';ast.parse(source)
  child.write_text(source);pin(child)
  derivatives.append(dict(parent=str(parent),parent_sha256=sha(parent),child=str(child),child_sha256=sha(child),deltas=deltas,
   inverse_recovers_exact_parent=True,ast_parsed=True,semantic_predicates_unchanged=True))
 for relative,h in [('reports/m4-constructor-native/service-preparation-r8/report.json','7437fa44e96c0ad7ec07431b8b69c00e08e63a8be139827bf7e1e11caaa53140'),
                    ('reports/m4-constructor-native/service-build-r8/build.json','17d9a84bf3cdef4404024e27e692d3432546b9751a77750889cfa974e3be1cc3'),
                    ('reports/m4-constructor-native/fixture-preparation-r6/report.json',PREP),
                    ('reports/m4-constructor-native/fixture-build-r10/build.json',BUILD)]:
  d=json.loads(pin(R/relative,h).read_bytes());assert d['passed']and d['initializer_credit']==0
  # Every artifact identity declared by the current preparations/builds is
  # checked; ordinary archives (.lib) are compiler inputs, canonical .mwb are not.
  for p,v in d['files'].items():pin(p,v)
 pin(__file__);pin(sys.executable)
 report=dict(passed=True,scope='Unexecuted exact path/hash-only r10/r6 writer controller and strict validator preparation; independent current source/linked prelaunch review pending',
  derivatives=derivatives,build_sha256=BUILD,preparation_sha256=PREP,
  independent_prelaunch_review_bound=False,execution_admitted=False,worker_executed=False,
  archive_reader_opened=False,initializer_credit=0,
  planned_writer_argv=['C:\\Python314\\python.exe','-B',str(R/'tools/m4-constructor-native/run_fixture_v4.py'),
   'CURRENT_VERIFIED_PRELAUNCH_R6_REPORT','CURRENT_VERIFIED_PRELAUNCH_R6_SHA256','fixture-execution-r4'],
  planned_validator_argv=['C:\\Python314\\python.exe','-B',str(R/'tools/m4-constructor-native/validate_fixture_v5.py'),
   str(R/'reports/m4-constructor-native/fixture-execution-r4/report.json'),'CURRENT_TERMINAL_EXECUTION_SHA256','FRESH_VALIDATION_NAME'],
  files=pins)
 out.mkdir(parents=True);q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),derivatives=derivatives)))
if __name__=='__main__':main(sys.argv[1])
