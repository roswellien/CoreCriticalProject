"""Bounded actual841-criterion data tests; no acceptance/configuration execution."""
from pathlib import Path
import ast,copy,hashlib,json,sys
sys.dont_write_bytecode=True
import acceptance138_criteria_v1 as C
R=Path(__file__).resolve().parents[2];T=Path(__file__).parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
baseline_path=R/'reports/m4-joint-startup131-root/configuration-r1/configuration.json'
B=json.loads(baseline_path.read_bytes());required=set(B['gates']);assert len(required)==33
assert sum(len(g['equal'])for g in B['gates'].values())==841
config={'gates':copy.deepcopy(B['gates']),'baseline_criteria':{label:{field:C.relation(field,v,v)for field,v in g['equal'].items()}for label,g in B['gates'].items()}}
tests=[]
def good(name,fn):fn();tests.append(dict(name=name,passed=True,expected='pass'))
def bad(name,fn):
 try:fn()
 except (ValueError,KeyError,TypeError)as e:tests.append(dict(name=name,passed=True,expected='refusal',reason=str(e)));return
 raise AssertionError('Adverse test unexpectedly passed '+name)
def validate(q):return C.validate(q,B,required)
good('all_actual33_gates841_unchanged_typed_expectations',lambda:assert_empty(validate(config))) if False else None
assert validate(config)=={};tests.append(dict(name='all_actual33_gates841_unchanged_typed_expectations',passed=True,expected='pass'))
label,field,old=next((l,f,v)for l,g in B['gates'].items()for f,v in g['equal'].items()if type(v)is int)
boollabel,boolfield,boolold=next((l,f,v)for l,g in B['gates'].items()for f,v in g['equal'].items()if type(v)is bool and f!='passed')
changed=copy.deepcopy(config)
delta=dict(baseline_expected=old,current_field=field,current_expected=old+1,physical_domain='Synthetic finite selected-root extent only',reason='Synthetic increment binds one exact old and new count; this is no actual138 domain admission')
changed['gates'][label]['equal'][field]=old+1;changed['baseline_criteria'][label][field]=C.relation(field,old,old+1,delta)
allowed=validate(changed);good('explicit_count_delta_exact_separate_allowance',lambda:C.review_allowances(dict(criteria_delta_allowances=allowed),allowed))
bad('arbitrary_count_delta_without_independent_allowance',lambda:C.review_allowances(dict(criteria_delta_allowances={}),allowed))
bad('missing_independent_delta_allowance_field',lambda:C.review_allowances({},allowed))
q=copy.deepcopy(config);q['baseline_criteria'][label][field]['baseline_expected']=old+1
bad('mutated_actual_baseline_expected_value',lambda:validate(q))
q=copy.deepcopy(config);q['baseline_criteria'][boollabel][boolfield]['current_field']='passed';q['baseline_criteria'][boollabel][boolfield]['current_expected']=True
bad('duplicate_success_field_mapping',lambda:validate(q))
q=copy.deepcopy(config);q['gates'][label]['equal'][field]=old+1;q['baseline_criteria'][label][field]['current_expected']=old+1
bad('silent_actual_count_value_freeze',lambda:validate(q))
d=copy.deepcopy(delta);d['reason']='';bad('missing_finite_physical_reason',lambda:C.relation(field,old,old+1,d))
d=copy.deepcopy(delta);d['physical_domain']='current value';bad('generic_success_only_domain',lambda:C.relation(field,old,old+1,d))
d=copy.deepcopy(delta);d['current_expected']=str(old+1);bad('retained_predicate_type_mutation',lambda:C.relation(field,old,str(old+1),d))
d=dict(baseline_expected=boolold,current_field=boolfield,current_expected=not boolold,physical_domain='Synthetic incorrect invariant mutation',reason='Synthetic alteration must refuse the inherited boolean acceptance condition')
bad('boolean_acceptance_invariant_flip',lambda:C.relation(boolfield,boolold,not boolold,d))
d=copy.deepcopy(delta);d['current_field']='passed';bad('single_success_only_translation',lambda:C.relation(field,old,old+1,d))
wrong=copy.deepcopy(allowed);wrong[label][field]['current_expected']=old+2
bad('independent_allowance_inexact_current_value',lambda:C.review_allowances(dict(criteria_delta_allowances=wrong),allowed))
for p in [T/'acceptance138_v3.py',T/'configure_acceptance138_v3.py',T/'acceptance138_criteria_v1.py']:ast.parse(p.read_text())
out=R/'reports/m4-138-controls-review/acceptance138-strict-criteria-preflight-r1';assert not out.exists();out.mkdir()
inputs=[Path(__file__),baseline_path,T/'acceptance138_v3.py',T/'configure_acceptance138_v3.py',T/'acceptance138_criteria_v1.py',R/'reports/m4-138-controls-review/acceptance138-strict-criteria-preparation-r1/report.json',Path(sys.executable)]
q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Actual33/841 baseline criterion identities plus bounded synthetic finite-delta/adverse controls; author preparation, no independent ROOT seal',controls=tests,controls_count=len(tests),all841_predicate_data_validated=True,actual138_configuration_built=False,acceptance_executed=False,physical_union_executed=False,archive_reader_opened=False,worker_executed=False,initializer_credit=0,files={str(p.resolve()):sha(p)for p in inputs}),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),controls=len(tests))))
