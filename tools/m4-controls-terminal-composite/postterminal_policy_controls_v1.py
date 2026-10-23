"""Pure actual criteria-policy controls; no finalizer/configuration imported."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def main(output):
 out=Path(output).resolve();assert not out.exists();out.mkdir(parents=True);p=R/'tools/m4-138-controls-review/acceptance138_criteria_v1.py';assert hashlib.sha256(p.read_bytes()).hexdigest()=='4fa464674bd2f0b5d1558fc6e1fbe8e847d3d12267689280f6e1e73f60326b86';s=importlib.util.spec_from_file_location('retained_production_criteria_policy',p);P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
 basepath=R/'reports/m4-joint-startup131-root/configuration-r1/configuration.json';baseline=json.loads(basepath.read_text());required=set(baseline['gates']);coverage={};gates={}
 for label,g in baseline['gates'].items():
  coverage[label]={f:P.relation(f,v,v)for f,v in g['equal'].items()};gates[label]=dict(equal=copy.deepcopy(g['equal']))
 assert sum(map(len,coverage.values()))==841 and len(required)==33;assert P.validate(dict(gates=gates,baseline_criteria=coverage),baseline,required)=={}
 # Finalizer's candidate status is not criteria necessity: same field/type/value is identity.
 assert P.relation('counts.actual_precise_denials',24,24)['kind']=='identity'
 d=dict(baseline_expected=35,current_field='counts.actual_compiler_TLS_cells',current_expected=56,physical_domain='legacy12 prefix actual compiler TLS capture-helper cells',reason='Physical complete7 compiled-prefix proof measures56 cells, distinct from old35 bridge cells and current8 TLS64.')
 assert P.relation('counts.actual_compiler_TLS_cells',35,56,d)['kind']=='finite_delta';rejected=[]
 def bad(name,fn):
  try:fn()
  except ValueError:rejected.append(name);return
  raise AssertionError('Must refuse '+name)
 bad('unnecessary-finite-same-field-value',lambda:P.relation('counts.actual_precise_denials',24,24,{**d,'baseline_expected':24,'current_expected':24,'current_field':'counts.actual_precise_denials'}))
 bad('Boolean-flip',lambda:P.relation('scope',False,True,{**d,'baseline_expected':False,'current_expected':True,'current_field':'scope'}))
 bad('baseline-value-mutation',lambda:P.relation('counts.actual_compiler_TLS_cells',35,56,{**d,'baseline_expected':34}))
 bad('type-coercion',lambda:P.relation('n',0,False,{**d,'baseline_expected':0,'current_expected':False,'current_field':'n'}))
 bad('generic-reason',lambda:P.relation('counts.actual_compiler_TLS_cells',35,56,{**d,'reason':'independently reviewed'}))
 bad('missing-domain',lambda:P.relation('counts.actual_compiler_TLS_cells',35,56,{k:v for k,v in d.items()if k!='physical_domain'}))
 bad('success-collapse',lambda:P.relation('counts.actual_compiler_TLS_cells',35,56,{**d,'current_field':'passed'}))
 faulty=copy.deepcopy(coverage);label=next(k for k,v in faulty.items()if len(v)>2);fields=list(faulty[label]);faulty[label][fields[1]]['current_field']=fields[0]
 bad('duplicate-current-target',lambda:P.validate(dict(gates=gates,baseline_criteria=faulty),baseline,required))
 faulty=copy.deepcopy(coverage);del faulty[label][fields[0]];bad('missing841-predicate',lambda:P.validate(dict(gates=gates,baseline_criteria=faulty),baseline,required))
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,pure_production_criteria_policy_used=True,actual_baseline_33gates_841_retained=True,synthetic_current_data_only=True,positive_identity_same_path_value=True,positive_explicit_finite_TLS_domain=True,adverse_controls=rejected,finalizer_imported=False,configurator_imported=False,acceptance_checker_imported=False,allowance_created=False,configuration_created=False,accepted_function_credit=0,files={str(x):hashlib.sha256(x.read_bytes()).hexdigest()for x in(p,basepath,Path(__file__).resolve())}),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest(),adverses=len(rejected))))
if __name__=='__main__':main(sys.argv[1])
