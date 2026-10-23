"""Independent ROOT review of a configure_acceptance138_v5 configuration for acceptance138_v6.

Re-measures independently of the configurator:
- every configured predicate of all 39 gates, from the gate report or the predicate's
  pinned source report; each report must match its SHA and report passed;
- the bindings, their per-field sources and the gate identities;
- the 841 retained criteria and the exact finite-delta allowances, with the sealed
  criteria module against the accepted131 baseline configuration;
- the machinery chain, by re-running every derivation script with its write replaced
  by a byte comparison: expander v3->v4, proof v1->v2, acceptance v4->v5->v6,
  configurator v4->v5 and templates v1->v2;
- the bridge/expander base reviews (root-machinery-review-r1, parallel check-r1).

Writes the review receipt acceptance138_v6 requires. Creates no acceptance.
Usage: python -B root_config_review_v6.py CONFIG_REPORT CONFIG_REPORT_SHA FRESH_NAME
"""
from pathlib import Path
import ast,hashlib,importlib.util,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
BASE_SHA='ba2fbf12ddedbac6c57ffb1ef6f14ade3712319a368671585daddd5f011c5ef7'
POLICY_SHA='4fa464674bd2f0b5d1558fc6e1fbe8e847d3d12267689280f6e1e73f60326b86'
IDENTITIES={'tools/m4-controls-strict-bridge/controls_graph_v1.py':'6060dc2724cae2ad2d33a325aae4eed5216e82862ec4b8bbc494218c53ce049e',
 'tools/m4-controls-terminal-composite/expand_composite_inventory_v4.py':'343a593a99dc771a134d6eab5918a20797891fcc2c1d69d7f8bfb3dbf0398782',
 'tools/m4-parallel-measure/ordered_pool.py':'4b3f3d465bfc909fbd6c4b4a7a08b26daa98bfbb50dbb2286df53c15a00616b0'}
ADDITIONAL={'source_widget_journal_review','source_widget_memory_review','source_widget_semantic_review','controls_full_raw','controls_gdi_owners','controls_current_link'}
pins={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);assert h is None or v==h,(str(p),v,h);assert pins.setdefault(str(p),v)==v,str(p);return p
cache={}
def load(p,h):
 key=str(Path(p).resolve())
 if key not in cache:cache[key]=json.loads(pin(p,h).read_bytes());assert cache[key].get('passed')is True,'Passed report '+key
 return cache[key]
def value_at(d,field):
 for k in field.split('.'):d=d[int(k)]if isinstance(d,list)else d[k]
 return d
def typed(a,b):return type(a)is type(b)and a==b
def rederive(script,subs):
 script=R/script;text=pin(script).read_text(encoding='utf-8')
 for a,b in subs:assert text.count(a)==1,(str(script),a);text=text.replace(a,b)
 exec(compile(text,str(script),'exec'),{'__file__':str(script),'__name__':'root_rederive'})
def main(config_report,config_report_sha,name):
 pin(__file__)
 CR=json.loads(pin(config_report,config_report_sha).read_bytes());assert CR['passed']is True and CR['gates']==39 and CR['baseline_predicates']==841 and CR['acceptance_executed']is False
 config=json.loads(pin(CR['configuration_path'],CR['configuration_sha256']).read_bytes())
 assert Path(config['configuration_source']).resolve()==(R/'tools/m4-controls-strict-bridge/configure_acceptance138_v5.py').resolve()
 pin(config['configuration_source'],config['configuration_source_sha256'])
 tree=ast.parse(pin(R/'tools/m4-joint-startup131/acceptance.py').read_text())
 base=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='REQUIRED'for t in n.targets))
 required=base|ADDITIONAL;assert set(config['gates'])==required and len(required)==39
 B=json.loads(pin(config['bindings'],config['bindings_sha256']).read_bytes());assert set(B)=={'gates','field_translations','field_sources'}
 # Independently re-measure every configured predicate from its gate or pinned source report.
 predicates=0;sourced=0;source_reports=set()
 for label,g in config['gates'].items():
  assert set(g)=={'path','sha256','equal','sources'}and B['gates'][label]=={'path':g['path'],'sha256':g['sha256']}
  assert g['sources']==B['field_sources'].get(label,{})and set(g['sources'])<=set(g['equal'])
  report=load(g['path'],g['sha256'])
  for field,expected in g['equal'].items():
   src=g['sources'].get(field)
   if src is not None:assert set(src)=={'path','sha256'};source_reports.add((str(Path(src['path']).resolve()),src['sha256']));sourced+=1
   actual=value_at(report if src is None else load(src['path'],src['sha256']),field)
   assert typed(actual,expected),('Configured predicate re-measured',label,field,actual,expected);predicates+=1
 assert set(B['field_sources'])<=set(config['gates'])
 # Retained criteria and exact finite-delta allowances (sealed criteria module, accepted131 baseline).
 policy=pin(R/'tools/m4-138-controls-review/acceptance138_criteria_v1.py',None)
 spec=importlib.util.spec_from_file_location('root_review_criteria',policy);C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
 baseline=json.loads(pin(R/'reports/m4-joint-startup131-root/configuration-r1/configuration.json',BASE_SHA).read_bytes())
 deltas=C.validate(config,baseline,base)
 S=json.loads(pin(config['review_specification'],config['review_specification_sha256']).read_bytes())
 assert S['required_exact_finite_delta_allowances']==deltas and S['baseline_measured_predicates']==841 and S['current_gate_count']==39
 # Machinery chain: every derivation re-run with its write replaced by an exact byte comparison.
 rederive('tools/m4-parallel-measure/make_parallel_versions.py',[("out=R/dst;assert not out.exists(),dst;out.write_bytes(","out=R/dst;assert out.read_bytes()==(")])
 rederive('tools/m4-controls-strict-bridge/make_acceptance_v5.py',[("assert not dst.exists();dst.write_bytes(s)","assert dst.read_bytes()==s")])
 rederive('tools/m4-controls-strict-bridge/make_acceptance_v6.py',[("assert not dst.exists();dst.write_bytes(s)","assert dst.read_bytes()==s")])
 rederive('tools/m4-controls-strict-bridge/make_configure_v5.py',[("assert not dst.exists();dst.write_bytes(s)","assert dst.read_bytes()==s")])
 rederive('tools/m4-controls-terminal-composite/make_templates_v2.py',[("assert not dst.exists();dst.write_bytes(s)","assert dst.read_bytes()==s")])
 for rel,h in IDENTITIES.items():pin(R/rel,h)
 for rel in ('tools/m4-controls-strict-bridge/acceptance138_v6.py','tools/m4-controls-strict-bridge/acceptance138_v5.py','tools/m4-controls-strict-bridge/acceptance138_v4.py',
  'tools/m4-138-controls-review/acceptance138_storage_v3.py','tools/m4-138-controls-review/acceptance138_storage_v2.py','tools/m4-138-controls-review/acceptance138_storage.py',
  'tools/m4-controls-strict-bridge/semantics_composite_v2.py','tools/m4-138-controls-review/expand_proof_inventory_v2.py','tools/m4-controls-terminal-composite/expand_composite_inventory_v3.py',
  'tools/m4-controls-terminal-composite/prepare_postterminal_templates_v2.py','tools/m4-controls-strict-bridge/configure_acceptance138_v4.py'):pin(R/rel)
 # Bridge/expander base reviews.
 MR=json.loads(pin(R/'reports/m4-controls-strict-bridge/root-machinery-review-r1/report.json').read_bytes())
 assert MR['passed']is True and MR['controls_composite_source_bridge_reviewed']is True and MR['controls_composite_inventory_expander_reviewed']is True
 v3=str((R/'tools/m4-controls-terminal-composite/expand_composite_inventory_v3.py').resolve());graph=str((R/'tools/m4-controls-strict-bridge/controls_graph_v1.py').resolve())
 assert MR['files'].get(v3)==sha(v3)and MR['files'].get(graph)==IDENTITIES['tools/m4-controls-strict-bridge/controls_graph_v1.py'],'Base review covered the current expander v3 and graph bytes'
 PC=json.loads(pin(R/'reports/m4-parallel-measure/check-r1/report.json').read_bytes())
 assert PC['passed']is True and len(PC['controls'])==12
 for rel in ('tools/m4-parallel-measure/ordered_pool.py','tools/m4-controls-terminal-composite/expand_composite_inventory_v4.py','tools/m4-138-controls-review/expand_proof_inventory_v2.py','tools/m4-138-controls-review/acceptance138_storage_v3.py'):
  p=str((R/rel).resolve());assert PC['files'].get(p)==sha(p),'Parallel equivalence check covered current '+rel
 for p_,h in list(pins.items()):assert sha(p_)==h
 assert re.fullmatch('[A-Za-z0-9_-]{1,90}',name);out=R/'reports/m4-138-controls-review'/name;assert not out.exists();out.mkdir()
 value=dict(passed=True,independent_review=True,scope='Independent ROOT configuration/criteria/machinery review for acceptance138_v6; no acceptance executed',gates_reviewed=39,baseline_predicates_reviewed=841,
  criteria_translation_reviewed=True,criteria_delta_allowances=deltas,configured_predicates_remeasured=predicates,per_predicate_sources_remeasured=sourced,per_predicate_source_reports=len(source_reports),
  controls_composite_source_bridge_reviewed=True,controls_composite_inventory_expander_reviewed=True,machinery_derivations_reproduced=['expander v3->v4 / proof v1->v2','acceptance v4->v5','acceptance v5->v6','configurator v4->v5','templates v1->v2'],
  configuration_path=str(Path(CR['configuration_path']).resolve()),configuration_sha256=CR['configuration_sha256'],acceptance_executed=False,allowance_created_by_author=False,accepted_function_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),predicates=predicates,sourced=sourced,deltas=sum(len(v)for v in deltas.values()))))
if __name__=='__main__':main(*sys.argv[1:])
