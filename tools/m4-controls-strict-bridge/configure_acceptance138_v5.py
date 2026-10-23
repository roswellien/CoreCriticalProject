"""Freeze explicitly bound completed gates; no unresolved identity defaults (v5: per-predicate pinned measurement sources for acceptance138_v6).

Usage: python configure_acceptance138.py BINDINGS_JSON FRESH_OUTPUT_NAME
Bindings must provide all39 path/SHA pairs and explicit baseline field
translations where current receipt schemas differ. No capture/worker/union run.
"""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
import acceptance138_v6 as A
R=A.ROOT
def sha(p):return A.sha(p)
def need(v,label):A.need(v,label)
def source_report(given,target,pins):
 row=given[target];need(set(row)=={'path','sha256'},'Exact per-predicate source '+target);p=(R/row['path']).resolve();need(sha(p)==row['sha256'],'Whole per-predicate source identity '+str(p))
 report=json.loads(p.read_bytes(),object_pairs_hook=A.unique_object);need(report.get('passed')is True,'Passed per-predicate source '+str(p));pins[str(p)]=row['sha256'];return report
def facets(row):
 result={}
 for k,v in row.items():
  if type(v)in(bool,int)and not any(s in k.lower()for s in('elapsed','time','duration')):result[k]=v
  elif k.endswith('_sha256')and isinstance(v,str):result[k]=v
 for group in('counts','provider_counts'):
  for k,v in row.get(group,{}).items():
   if type(v)in(bool,int):result[group+'.'+k]=v
 need(result.get('passed')is True and len(result)>=2,'Complete measured successful facets');return result
def main(binding_path,name):
 binding_path=Path(binding_path).resolve();bindings=json.loads(binding_path.read_bytes(),object_pairs_hook=A.unique_object);need(set(bindings)=={'gates','field_translations','field_sources'}and set(bindings['field_sources'])<=A.REQUIRED,'Exact39-gate binding/translation/source schema');need(set(bindings['gates'])==A.REQUIRED,'All39 explicit path/hash bindings')
 out=R/'reports/m4-138-controls-review'/name;need(not out.exists(),'Fresh frozen configuration');out.mkdir(parents=True)
 parentconfig=R/'reports/m4-joint-startup131-root/configuration-r1/configuration.json';baseline=json.loads(parentconfig.read_bytes(),object_pairs_hook=A.unique_object);gates={};coverage={};pins={str(binding_path):sha(binding_path),str(parentconfig):sha(parentconfig)}
 for label,b in bindings['gates'].items():
  need(set(b)=={'path','sha256'},'Exact bound completed gate '+label);p=(R/b['path']).resolve();need(sha(p)==b['sha256'],'Whole current gate identity '+label);pins[str(p)]=b['sha256']
  if label=='controls':row=A.storage.read_report(p,lambda *args:None)
  else:row=json.loads(p.read_bytes(),object_pairs_hook=A.unique_object)
  equal=facets(row);sources={};given_sources=bindings['field_sources'].get(label,{});gates[label]=dict(path=b['path'],sha256=b['sha256'],equal=equal,sources=sources)
  if label in A.BASE_REQUIRED:
   coverage[label]={}
   given=bindings['field_translations'].get(label,{})
   need(set(given)<=set(baseline['gates'][label]['equal']),'Only actual accepted predicate translations '+label)
   for field,old_expected in baseline['gates'][label]['equal'].items():
    delta=given.get(field);target=field if delta is None else delta['current_field']
    value=A.value_at(source_report(given_sources,target,pins)if target in given_sources else row,target);need(type(value)in(bool,int,str),'Typed ordinary measurable translated predicate')
    relation=A.criteria.relation(field,old_expected,value,delta)
    equal[target]=value;coverage[label][field]=relation
    if target in given_sources:sources[target]=dict(given_sources[target])
 need(all(set(bindings['field_sources'].get(label,{}))==set(gate['sources'])for label,gate in gates.items()),'Every per-predicate source used exactly once by its predicate')
 need(set(bindings['field_translations'])<=A.BASE_REQUIRED,'Translations only retained accepted gates')
 deltas=A.criteria.validate(dict(gates=gates,baseline_criteria=coverage),baseline,A.BASE_REQUIRED)
 specification=out/'review-specification.json';specification.write_text(json.dumps(dict(required_gates=sorted(A.REQUIRED),baseline_measured_predicates=841,baseline_gate_count=33,current_gate_count=39,baseline_criteria=coverage,required_exact_finite_delta_allowances=deltas,mandatory_review=['All current evidence paths/whole identities and typed predicates','Every baseline predicate preserved with explicitly justified schema/count/domain/lineage translation','Exact inverse semantic delta and physical108 callbacks/seven root slots','New widget code/raw-State/memory/owner/flag/source gates','Actual current original source/loaded-input/paired policy/equivalence','Fullraw/retry closed durable inventory and expansion','Every current/parent dependency bytehash; full disk-backed union, no metadata shortcut','All source modules/toolchains/Python pinned; no current gate inferred from success boolean alone'],admission_requires=dict(passed=True,gates_reviewed=39,baseline_predicates_reviewed=841,criteria_translation_reviewed=True,criteria_delta_allowances=deltas),acceptance_executed=False,initializer_credit=0),indent=2)+'\n')
 config=dict(gates=gates,baseline_criteria=coverage,configuration_source=str(Path(__file__).resolve()),configuration_source_sha256=sha(__file__),review_specification=str(specification),review_specification_sha256=sha(specification),bindings=str(binding_path),bindings_sha256=sha(binding_path))
 q=out/'configuration.json';q.write_text(json.dumps(config,indent=2)+'\n')
 for p in [Path(A.criteria.__file__),Path(__file__).resolve(),Path(sys.executable),Path(A.__file__),Path(A.storage.__file__),R/'tools/m4-controls-strict-bridge/semantics_composite_v2.py',specification,q]:pins[str(p.resolve())]=sha(p)
 report=out/'report.json';report.write_text(json.dumps(dict(passed=True,scope='Frozen completed explicit39-gate identities and retained841-predicate translation configuration; no acceptance',configuration_path=str(q),configuration_sha256=sha(q),gates=39,baseline_predicates=841,acceptance_executed=False,initializer_credit=0,capture_reader_opened=False,worker_executed=False,files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(report),sha256=sha(report),configuration_sha256=sha(q))))
if __name__=='__main__':main(Path(sys.argv[1]),sys.argv[2])
