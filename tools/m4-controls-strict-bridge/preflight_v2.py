"""UNEXECUTED pure AST graph/inverse controls; no checker/config/main/DB."""
from pathlib import Path
import ast,copy,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def need(v,s):
 if not v:raise ValueError(s)
def typed_equal(a,b,s):need(type(a)is type(b)and a==b,s)
def run(name):
 folder=R/'tools/m4-controls-strict-bridge';prep=R/'reports/m4-controls-strict-bridge/preparation-r1';checks=[];files={}
 def bytesof(p):
  raw=p.read_bytes();files[str(p)]=hashlib.sha256(raw).hexdigest();return raw
 child=bytesof(folder/'acceptance138_v4.py').decode();deltas=json.loads((prep/'strict-checker-deltas.json').read_text(encoding='utf-8-sig'))
 for delta in reversed(deltas):assert child.count(delta['new'])==delta['count'];child=child.replace(delta['new'],delta['old'])
 assert child==bytesof(R/'tools/m4-138-controls-review/acceptance138_v3.py').decode();checks.append('Entire strictv4 nine substitutions invert6654 body exactly')
 cfg=bytesof(folder/'configure_acceptance138_v4.py').decode();cfg=cfg.replace('import acceptance138_v4 as A','import acceptance138_v3 as A').replace("R/'tools/m4-controls-strict-bridge/semantics_composite_v2.py'","R/'tools/m4-138-controls-review/acceptance138_semantics_v3.py'");assert cfg==bytesof(R/'tools/m4-138-controls-review/configure_acceptance138_v3.py').decode();checks.append('Whole configurator2 substitutions invert efcd')
 sem=bytesof(folder/'semantics_composite_v2.py').decode();added='\n        GRAPH.current8_legacy12_preparation(rows,gates,ROOT=ROOT,read=read,has=has,typed_equal=typed_equal,need=need)';assert sem.count(added)==1;sem=sem.replace(added,'');assert sem==bytesof(folder/'semantics_composite_v1.py').decode();checks.append('Whole strengthened semantic1 addition inverse to7e756 candidate')
 for leaf in('acceptance138_v4.py','configure_acceptance138_v4.py','semantics_composite_v2.py','controls_graph_v1.py'):ast.parse(bytesof(folder/leaf))
 graph=ast.parse(bytesof(folder/'controls_graph_v1.py'));scope={'ROOT':R,'need':need,'typed_equal':typed_equal}
 for node in graph.body:
  if isinstance(node,ast.Assign):
   assert len(node.targets)==1;scope[node.targets[0].id]=ast.literal_eval(node.value)
 functions=[n for n in graph.body if isinstance(n,ast.FunctionDef)];exec(compile(ast.Module(body=functions,type_ignores=[]),'<exact graph-only source functions>','exec'),scope)
 old=R/'reports/m4-joint-startup138/context-controls-verification-r1/report.json';rawpath=R/'synthetic-raw2a.json';sem_path=R/'reports/m4-controls-terminal-composite/root-current16-finite-review-r1/current16-semantic-review.json';scope_path=sem_path.with_name('current8-scope-review.json');complete=R/'reports/m4-controls-terminal-composite/root-complete7-physical-r1/report.json'
 limits=dict(committed_source_write_values_independently_instruction_evaluated=False,committed_write_values_from_actual_source_witness=True,whole_fault_memory_fully_source_predicted=False,source_callbacks_executed=False)
 sem=dict(passed=True,preparation_sha256=scope['PREP'],build_sha256=scope['BUILD'],executed_semantic_sha256=scope['SEMANTICS'],current16_fullraw_sha256=scope['RAW'],execution_sha256='3'*64,all16_distinct_modes_reviewed=True,finite_GDI_owner_manual_cleanup_lifetime_predicates_reviewed=True,source_bootstrap_or_teardown_modeled=False,partial_fault_register_prediction=False,whole_hidden_Runtime_frames_or_permissions_claim=False,forwarder_origin_or_transitive_wrapper_body_claim=False,whole_current138_positive_semantic_equivalence_claim=False,files={str(rawpath):scope['RAW']},**limits);policy=dict(passed=True,preparation_sha256=scope['PREP'],build_sha256=scope['BUILD'],executed_semantic_sha256=scope['SEMANTICS'],manual_native_owned_cleanup_only=True,final_named_owner_entry64_only=True,files={str(rawpath):scope['RAW']},**limits)
 rows={'controls':dict(scope_identity='current138_terminal_legacy24_current16_controls_composite_v1',initializer_credit=0,files={str(rawpath):scope['RAW'],str(sem_path):scope['SEM_ROLE'],str(scope_path):scope['SCOPE_ROLE'],str(complete):scope['COMPLETE7']}),'controls_full_raw':dict(controls_verification_sha256=scope['SEMANTICS'],capture_archives_opened=0,worker_executed=False,source_machine_executed=False,whole_hidden_Runtime_frames_or_permissions_claim=False,whole_current138_positive_semantic_equivalence_claim=False,initializer_credit=0,files={str(old):scope['SEMANTICS']}),'controls_gdi_owners':dict(files={str(old):scope['SEMANTICS']})};gates={'controls_full_raw':dict(path=str(rawpath),sha256=scope['RAW']),'controls_execution':dict(sha256='3'*64)}
 def has(row,path,h):return row['files'].get(str(path))==h
 def accepted(r,s,p):
  def read(path,h):
   if path==sem_path:assert h==scope['SEM_ROLE'];return s
   if path==scope_path:assert h==scope['SCOPE_ROLE'];return p
   raise AssertionError('Only exact finite metadata roles')
  try:scope['old_semantic_composite'](r,gates,ROOT=R,read=read,has=has,typed_equal=typed_equal,need=need);return True
  except ValueError:return False
 assert accepted(rows,sem,policy);checks.append('Actual old88 raw/GDI plus exact new composite/finite roles positive')
 mutations=[('Relabeled raw to new composer',lambda r,s,p:r['controls_full_raw'].update(controls_verification_sha256='9'*64)),('Missing exact old producer edge raw',lambda r,s,p:r['controls_full_raw']['files'].pop(str(old))),('Missing exact old producer edge owner',lambda r,s,p:r['controls_gdi_owners']['files'].pop(str(old))),('Missing actual raw edge in new composite',lambda r,s,p:r['controls']['files'].pop(str(rawpath))),('Missing exact finite semantic role',lambda r,s,p:r['controls']['files'].pop(str(sem_path))),('Missing exact finite scope role',lambda r,s,p:r['controls']['files'].pop(str(scope_path))),('Wrong legacy7 receipt',lambda r,s,p:r['controls']['files'].__setitem__(str(complete),'0'*64)),('Fabricated raw worker execution',lambda r,s,p:r['controls_full_raw'].update(worker_executed=True)),('Fabricated source replay',lambda r,s,p:r['controls_full_raw'].update(source_machine_executed=True)),('Full write prediction inferred',lambda r,s,p:s.update(whole_fault_memory_fully_source_predicted=True)),('Source callback cleanup inferred',lambda r,s,p:s.update(source_callbacks_executed=True)),('Manual scope broadened',lambda r,s,p:p.update(manual_native_owned_cleanup_only=False)),('Wrong raw producer role',lambda r,s,p:s.update(current16_fullraw_sha256='0'*64)),('Wrong genuine preparation role',lambda r,s,p:s.update(preparation_sha256='0'*64))]
 for label,mutate in mutations:
  r,s,p=copy.deepcopy(rows),copy.deepcopy(sem),copy.deepcopy(policy);mutate(r,s,p);assert not accepted(r,s,p);checks.append(label+' rejected')
 # Independently exercise only actual/composite preparation graph function.
 cp=R/'synthetic-current8-prep.json';lp=R/'synthetic-legacy12-prep.json';lb=R/'synthetic-legacy12-build.json'
 prep=dict(passed=True,scope_identity='current138_controls_preparation_composite_v1',control_cases=12,underlying_current8_preparation=dict(path=str(cp),sha256=scope['PREP']),underlying_legacy12_preparation=dict(path=str(lp),sha256=scope['LEGACY_PREP']),old_registry_private_vectors_retry_claim=False,full_memory_permission_snapshot_claim=False,observation_limits=dict(old_registry_private_vectors_retry_claim=False,full_memory_permission_snapshot_claim=False,whole_hidden_Runtime_frames_or_permissions_claim=False),files={str(cp):scope['PREP'],str(lp):scope['LEGACY_PREP'],str(lb):scope['LEGACY_BUILD']});prelaunch=dict(scoped_legacy_build=dict(path=str(lb),sha256=scope['LEGACY_BUILD']),files={str(lb):scope['LEGACY_BUILD']});current=dict(control_modes=8,control_phase=135,completed_prefix_roots=135,source_owned_font_create_calls=15);old=dict(preparation_sha256=scope['LEGACY_PREP']);pr={'controls_preparation':prep,'controls_build':dict(preparation_sha256=scope['PREP']),'controls_prelaunch':prelaunch};pg={'controls_build':dict(sha256=scope['BUILD'])}
 def prepaccepted(r,c,o):
  def read(path,h):
   if path==cp:assert h==scope['PREP'];return c
   if path==lb:assert h==scope['LEGACY_BUILD'];return o
   raise AssertionError('Only genuine underlying preparation/build metadata')
  try:scope['current8_legacy12_preparation'](r,pg,ROOT=R,read=read,has=has,typed_equal=typed_equal,need=need);return True
  except ValueError:return False
 assert prepaccepted(pr,current,old);checks.append('Composite prep retains actual f413/e064 and distinct8a322/9a656 source schema positive')
 for label,mutate in(('Arbitrary prep schema',lambda r,c,o:r['controls_preparation'].update(extra_passed_claim=True)),('Current build retargeted to composite',lambda r,c,o:r['controls_build'].update(preparation_sha256='9'*64)),('Missing physical underlying source edge',lambda r,c,o:r['controls_preparation']['files'].pop(str(cp))),('Current prep replacing legacy prep',lambda r,c,o:r['controls_preparation']['underlying_legacy12_preparation'].update(sha256=scope['PREP'])),('Current8 build replacing legacy build',lambda r,c,o:r['controls_prelaunch']['scoped_legacy_build'].update(sha256=scope['BUILD'])),('Wrong actual rootphase schema',lambda r,c,o:c.update(control_phase=136)),('Wrong actual legacy sourcebuild',lambda r,c,o:o.update(preparation_sha256=scope['PREP']))):
  r,c,o=copy.deepcopy(pr),copy.deepcopy(current),copy.deepcopy(old);mutate(r,c,o);assert not prepaccepted(r,c,o);checks.append(label+' rejected')
 # Freeze core retained criteria identifiers without importing final checker.
 tree=ast.parse((folder/'acceptance138_v4.py').read_text());assign={n.targets[0].id:n.value for n in tree.body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)};assert ast.literal_eval(assign['PARENT_SHA'])=='aa9462f30bf4fa6c80ef926488928bb8680f207020e4f0aa166968caaf724061';assert len(ast.literal_eval(assign['ADDITIONAL']))==6;assert 'baseline_measured_predicates=841'in(folder/'acceptance138_v4.py').read_text();checks.append('Accepted131/841/6 additional39 total predicates retained')
 out=R/'reports/m4-controls-strict-bridge'/name;assert not out.exists();out.mkdir();(out/'report.json').write_text(json.dumps(dict(pure_controls_completed=True,controls=checks,control_count=len(checks),checker_or_configurator_imported=False,actual_composer_or_DB_opened=False,ROOT_admission_created=False,accepted_function_credit=0,files=files),indent=2)+'\n')
if __name__=='__main__':run(sys.argv[1])
