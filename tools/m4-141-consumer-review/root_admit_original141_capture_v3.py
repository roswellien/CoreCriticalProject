"""Seal current rebased writer and capture validator after independent reviews."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-original141';T=R/'tools/m4-141-consumer-review'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
files={}
def pin(p,h=None):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip') and p.name!='transport.json';v=sha(p);assert h is None or v==h,(p,v,h);assert files.setdefault(str(p),v)==v;return p
recipe=pin(B/'capture-admission-recipe-r3/report.json','dd479148c678aa3d4eaaf6b6fe2f796994cd32ab8de8d3060be36112caa23e60');q=json.loads(recipe.read_bytes());assert q['passed'] and q['self_admission'] is False
u=pin(B/'capture-admission-recipe-r3/current-input-union.json','a310328bef5914f11fd659dbbcb07ce44ce2287820fced15613dfbb20eedca9c');union=json.loads(u.read_bytes());assert len(union)==1301
for p,h in union.items():pin(p,h)
# Every whole adapted body must invert to the independently read retained body.
for leaf,parents in [('complete-helper-deltas.json',{'prepare_original141_PUSHFD_v2.py':'prepare_original141_PUSHFD_v1.py','prepare_original141_transition_v3.py':'prepare_original141_transition_v1.py','prepare_original141_stack_v3.py':'prepare_original141_stack_v2.py'}),('controller-deltas.json',{'validate_original141_v6.py':'validate_original141_v5.py','run_original141_v4.py':'run_original141_v3.py','test_original141_wiring_v3.py':'test_original141_wiring_v2.py','test_original141_runner_v3.py':'test_original141_runner_v2.py'})]:
 folder='rebase-helper-preparation-r1' if leaf.startswith('complete') else 'rebase-controller-preparation-r1';d=json.loads(pin(B/folder/leaf).read_bytes())
 for current,parent in parents.items():
  a=pin(T/current).read_text()
  for x in reversed(d[current]):assert a.count(x['new'])==x['count'];a=a.replace(x['new'],x['old'])
  assert a==pin(T/parent).read_text(),current
for rel,h in [('root-compiled-review-r2','e756132a1c938d6b5318f8a2b65e954a17c44870be2bab556427767ef233214c'),('root-source-stack-review-r2','1f6d28fc61f94b2a8c500463d16fc8e17e1dce44bfff84534caee60c04c6cfbe'),('root-image-layout-r1','552413f04dbab844445eb107ceb664cefbc10d80dd67192c8e5af9b2c90d55ad'),('root-validator-wiring-controls-r2','3145ff21898bd5a2372809a37e2df8260c25744138814983c36408cf17346c33'),('root-runner-controls-r2','51eb42f725abf5a6e4a7d47453a61e581b888324980d877435412df44332e281'),('root-transition-controls-r1','017a4ed15ee06da00c45b331a9d2575d362a74fab9e697c987db8d4a5b1e8841')]:
 p=pin(B/rel/'report.json',h);v=json.loads(p.read_bytes());assert v['passed']
 for path,digest in v['files'].items():pin(path,digest)
assert json.loads((B/'transition-preparation-r3/patch-declarations.json').read_bytes())==json.loads((B/'root-transition-controls-r1/patch-declarations.json').read_bytes())
pin(__file__);assert all(sha(p)==h for p,h in files.items())
out=B/'root-capture-admission-r2';out.mkdir();p=out/'report.json'
p.write_text(json.dumps(dict(passed=True,independent_ROOT_review=True,original141_writer_admitted=True,original141_validator_admitted=True,actual_rebased_PE_and_whole_linked_relocations_reviewed=True,compiled_stack_ownership_reviewed=True,whole_controller_and_helper_inverses_reviewed=True,one_original_writer_required=True,one_injected_validator_reader_required=True,actual_original141_dynamic_source_equivalence_pending=True,worker_executed=False,reader_opened=False,accepted_function_credit=0,initializer_credit=0,files=files),indent=2)+'\n',encoding='utf-8');print(sha(p),len(files))
