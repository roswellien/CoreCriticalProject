"""Current138 acceptance using retained131 criteria and full disk-backed union (v6: v5 plus per-predicate pinned ROOT measurement sources; criteria unchanged).

Never use an incomplete configuration: all39 current evidence gates and an
independent exact checker/configuration review are mandatory. Every physical
dependency is freshly whole-byte hashed, including every sealed controls row.
"""
from pathlib import Path
import ast,hashlib,importlib.util,json,re,sys,time,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'));sys.path.insert(0,str(ROOT/'tools/m4-138-controls-review'))
from manifests import normalized,digest,unique_object
import acceptance138_storage_v3 as storage
import acceptance138_criteria_v1 as criteria
PARENT_SHA='aa9462f30bf4fa6c80ef926488928bb8680f207020e4f0aa166968caaf724061'
PARENT_CHECKER=ROOT/'tools/m4-joint-startup131/acceptance.py'
tree=ast.parse(PARENT_CHECKER.read_text());BASE_REQUIRED=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='REQUIRED'for t in n.targets))
ADDITIONAL={'source_widget_journal_review','source_widget_memory_review','source_widget_semantic_review','controls_full_raw','controls_gdi_owners','controls_current_link'}
REQUIRED=BASE_REQUIRED|ADDITIONAL
PINS=None;SCOPES=None;DIRECT={};GRAPH=None
def need(v,label):
 if not v:raise ValueError(label)
def sha(path):return storage.sha(path)
def register(path,h):PINS[str(Path(path).resolve())]=h
def read(path,h=None,stream=False):
 path=Path(path).resolve();actual=sha(path);need(h is None or h==actual,'Exact current receipt '+str(path));register(path,actual);DIRECT[str(path)]=actual
 if stream:return storage.read_report(path,register,SCOPES)
 return json.loads(path.read_text(encoding='utf-8-sig'),object_pairs_hook=unique_object)
FIELDS=('files','physical_inputs','physical_dependencies','generated_sources','sources','tools','artifacts','retained_capture_inputs')
def absorb(report):
 for field in FIELDS:
  for p,h in report.get(field,{}).items():register(p,h)
def value_at(report,field):
 for key in field.split('.'):report=report[int(key)]if isinstance(report,list)else report[key]
 return report
def typed_equal(actual,expected,label):need(type(actual)is type(expected)and actual==expected,'Exact typed '+label)
SOURCED={};REVIEW=None
def sourced(row,label,field):
 # A predicate whose current value was measured in a separately pinned ROOT report.
 need(set(row)=={'path','sha256'},'Exact per-predicate source schema '+label+':'+field);path=(ROOT/row['path']).resolve();key=str(path)
 if key not in SOURCED:
  report=read(path,row['sha256']);typed_equal(report.get('passed'),True,'Passed predicate source '+key);absorb(report)
  need(has(REVIEW,path,row['sha256']),'Independent review owns predicate source '+key);SOURCED[key]=report
 return SOURCED[key]
def has(report,path,h):
 target=normalized(str(Path(path).resolve()))
 for field in FIELDS:
  values=report.get(field,{})
  if isinstance(values,storage.ScopedFiles):
   if values.get(target)==h:return True
  elif any(normalized(str(Path(p).resolve()))==target and identity==h for p,identity in values.items()):return True
 return False
def baseline_criteria(config):
 old=read(ROOT/'reports/m4-joint-startup131-root/configuration-r1/configuration.json')
 return criteria.validate(config,old,BASE_REQUIRED)

def additions(rows,gates):
 source=rows['source_provider'];typed_equal(gates['source_provider']['sha256'],'40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052','Sealed current source6')
 for field,count in {'literal_widget_roots':84,'actual_GDI_source_calls':1788,'actual_manual_owned_font_frees':180,'complete_widget_caller_cleanup_restores':12,'literal_registration_roots':1296}.items():typed_equal(source['counts'][field],count,'Whole current widget/source extent '+field)
 for label in ('source_widget_journal_review','source_widget_memory_review','source_widget_semantic_review'):
  row=rows[label];need(has(row,ROOT/gates['source_provider']['path'],gates['source_provider']['sha256']),'Independent current source widget edge '+label);typed_equal(row['reader_closed'],True,label+' closed');typed_equal(row['initializer_credit'],0,label+' no standalone credit')
 mem=rows['source_widget_memory_review'];typed_equal(mem['independent_component_memory_byteflow'],True,'Independent own BEFORE byteflow');typed_equal(mem['independent_raw_identity_equality'],True,'Actual raw GDI equality')
 for key,n in {'independent_widget_memory_byteflows':84,'independently_authenticated_raw_GDI_calls':1968,'physically_discriminated_growth_intervals':24}.items():typed_equal(mem['counts'][key],n,'Exact independent memory domain '+key)
 sem=rows['source_widget_semantic_review']
 for key,n in {'whole_unchanged_inherited_interpreter_layers':7,'whole_reached_physical_instruction_rows':1016,'whole_reached_callback_offset_rows':31,'whole_source_defined_flag_consumers':45924,'whole_State_CPU_FX_raw_boundaries':168}.items():typed_equal(sem['counts'][key],n,'Entire actual semantic supplement '+key)
 for key in ('independent_semantic_code_and_physical_program_review','independent_whole_State_CPU_FX_source_correspondence','source_equivalence_prediction_owned_by_current_consumer'):typed_equal(sem[key],True,key)
 typed_equal(sem['second_interpreter_execution'],False,'No fabricated second source execution');need(has(sem,ROOT/gates['source_widget_memory_review']['path'],gates['source_widget_memory_review']['sha256']),'Exact current memory review consumed')
 GRAPH.old_semantic_composite(rows,gates,ROOT=ROOT,read=read,has=has,typed_equal=typed_equal,need=need);raw=rows['controls_full_raw']
 for field,n in {'whole_export_targets_authenticated':10691866,'whole_exported_retry_files_equal':3547696}.items():typed_equal(raw['counts'][field],n,'Complete raw/private retry extent '+field)
 for field in ('acceptance_requires_inventory_expansion','all_bounded_readers_closed','raw_export_readers_closed','raw_exports_all_logical_entries'):typed_equal(raw[field],True,'Closed durable controls proof '+field)
 typed_equal(raw['capture_archives_opened'],0,'No fullraw archive reads');typed_equal(raw['worker_executed'],False,'No new fullraw worker');typed_equal(raw['initializer_credit'],0,'No standalone fullraw credit')
 for label,target in [('controls_current_link','native_execution')]:need(has(rows[label],ROOT/gates[target]['path'],gates[target]['sha256']),'Exact current physical review edge '+label)
def main(configuration,name,review_path,review_sha):
 global PINS,SCOPES,GRAPH,REVIEW
 out=ROOT/'reports/m4-joint-startup138-root'/name;need(not out.exists(),'Fresh acceptance output');out.mkdir(parents=True);PINS=storage.Union(out/'physical-union.sqlite');SCOPES=storage.ScopeIndex(out/'receipt-scopes.sqlite');passed=False;config={};closure={};inventory={};expanded={};predicates=0;started=time.monotonic()
 try:
  config=read(configuration);need(set(config['gates'])==REQUIRED,'All39 mandatory evidence gates');deltas=baseline_criteria(config)
  for field in ('configuration_source','review_specification','bindings'):
   register(config[field],config[field+'_sha256']);DIRECT[config[field]]=config[field+'_sha256']
  for p in [Path(criteria.__file__),Path(__file__),Path(storage.__file__),Path(storage.base.__file__),ROOT/'tools/m4-138-controls-review/expand_accepted138_union.py',PARENT_CHECKER,Path(sys.executable),ROOT/'tools/m4-pipeline/manifests.py',ROOT/'tools/m4-controls-strict-bridge/semantics_composite_v2.py',ROOT/'tools/m4-138-controls-review/full_raw_review_v2.py',ROOT/'tools/m4-138-controls-review/expand_proof_inventory_v2.py',ROOT/'tools/m4-parallel-measure/ordered_pool.py']:
   register(p,sha(p));DIRECT[str(p.resolve())]=sha(p)
  review=read(review_path,review_sha);absorb(review);REVIEW=review;criteria.review_allowances(review,deltas)
  need(review['passed']is True and review['gates_reviewed']==len(REQUIRED)and review['baseline_predicates_reviewed']==841 and review['criteria_translation_reviewed']is True,'Independent full criteria/configuration review')
  for p in [Path(criteria.__file__),configuration,Path(__file__),Path(storage.__file__),ROOT/'tools/m4-controls-strict-bridge/semantics_composite_v2.py']:need(has(review,p,sha(p)),'Independent sealed exact machinery '+str(p))
  graph_path=ROOT/'tools/m4-controls-strict-bridge/controls_graph_v1.py';expander_path=ROOT/'tools/m4-controls-terminal-composite/expand_composite_inventory_v4.py';pool_path=ROOT/'tools/m4-parallel-measure/ordered_pool.py'
  for path,identity in((graph_path,'6060dc2724cae2ad2d33a325aae4eed5216e82862ec4b8bbc494218c53ce049e'),(expander_path,'343a593a99dc771a134d6eab5918a20797891fcc2c1d69d7f8bfb3dbf0398782'),(pool_path,'4b3f3d465bfc909fbd6c4b4a7a08b26daa98bfbb50dbb2286df53c15a00616b0')):
   typed_equal(sha(path),identity,'Exact prepared finite bridge/expansion helper');need(has(review,path,identity),'Independent ROOT owns actual helper before import');register(path,identity);DIRECT[str(path.resolve())]=identity
  typed_equal(review['controls_composite_source_bridge_reviewed'],True,'Independent ROOT finite producer/raw/source graph review');typed_equal(review['controls_composite_inventory_expander_reviewed'],True,'Independent ROOT distinct full scoped union expansion review')
  GRAPH=storage.load('accepted138_exact_controls_graph',graph_path);POOL=storage.load('accepted138_ordered_measure_pool',pool_path);PINS.mapper=POOL.ordered_map
  rows={}
  for label,gate in config['gates'].items():
   need(set(gate)=={'path','sha256','equal','sources'}and len(gate['equal'])>=2 and set(gate['sources'])<=set(gate['equal']),'Exact complete measured gate schema '+label);path=ROOT/gate['path'];report=read(path,gate['sha256'],stream=label=='controls');typed_equal(report['passed'],True,'Passed current gate '+label);absorb(report)
   sibling=path.parent/'pins.json'
   # Giant controls declarations are already streamed from report.files; all
   # other supplementary ordinary manifest receipts are absorbed whole.
   if sibling.exists():absorb(read(sibling,stream=label=='controls'))
   for field,expected in gate['equal'].items():source=gate['sources'].get(field);typed_equal(value_at(report if source is None else sourced(source,label,field),field),expected,label+':'+field);predicates+=1
   rows[label]=report
  module=storage.load('accepted138_retained_semantics',ROOT/'tools/m4-controls-strict-bridge/semantics_composite_v2.py')
  for key in ('ROOT','PARENT_SHA','PINS','need','typed_equal','read','register','sha','has','Path','re','normalized'):setattr(module,key,globals()[key])
  module.GRAPH=GRAPH;module.semantic_checks(rows,config['gates']);additions(rows,config['gates'])
  expansion=storage.load('accepted138_full_controls_expansion',ROOT/'tools/m4-138-controls-review/expand_proof_inventory_v2.py')
  expanded=expansion.expand(ROOT/config['gates']['controls_full_raw']['path'],config['gates']['controls_full_raw']['sha256'],register,lambda n:print(json.dumps(dict(progress='expand_fullraw',rows=n)),flush=True),mapper=POOL.ordered_map)
  need(expanded['passed']is True and expanded['database_reader_closed']is True and expanded['metadata_only_cache_used']is False,'Complete closed controls expansion')
  composite_module=storage.load('accepted138_distinct_composite_expansion',expander_path)
  composite_expanded=composite_module.expand(ROOT/config['gates']['controls']['path'],config['gates']['controls']['sha256'],register,register_edge=lambda scope,path,identity:SCOPES.add('controls-composite:'+normalized(str((ROOT/config['gates']['controls']['path']).resolve()))+':'+scope,path,identity),progress=lambda n:print(json.dumps(dict(progress='expand_distinct_controls_composite',rows=n)),flush=True),mapper=POOL.ordered_map)
  need(composite_expanded['passed']is True and composite_expanded['database_reader_closed']is True and composite_expanded['metadata_only_cache_used']is False and composite_expanded['scoped_provenance_preserved']is True,'Complete distinct old24/current16 physical AND scoped union expanded')
  typed_equal(composite_expanded['current16_raw_rows'],10691866,'Distinct exact current16 raw domain');typed_equal(composite_expanded['initializer_credit'],0,'Composite expansion no initializer credit');typed_equal(composite_expanded['accepted_function_credit'],0,'Composite expansion no independent count credit')
  expanded=dict(actual_current16=expanded,distinct_scoped_composite=composite_expanded)
  SCOPES.close();register(SCOPES.path,sha(SCOPES.path));DIRECT[str(SCOPES.path)]=sha(SCOPES.path)
  closure=PINS.verify(lambda n:print(json.dumps(dict(progress='fresh_all_history_union',rows=n)),flush=True));inventory=PINS.seal();need(closure['passed']and not closure['metadata_only_cache_used']and closure['unique_physical_dependencies']==inventory['physical_rows'],'Fresh complete historical/current union')
  DIRECT[inventory['path']]=inventory['sha256'];passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  SCOPES.close();PINS.close()
  result=dict(passed=passed,scope='Connected selected138 startup inventory after retained131/current original/native/source/provider/widget/pair/controls gates and complete byte-rehashed union',connected_roots=138 if passed else 131,new_roots=7 if passed else 0,total_inventory_roots=144,remaining_inventory_roots=6 if passed else 13,inventory_is_project_completion_percentage=False,gates=config.get('gates',{}),explicit_measured_predicates=predicates,baseline_measured_predicates=841,physical_closure=closure,full_controls_expansion=expanded,proof_inventory=inventory,acceptance_requires_inventory_expansion=passed,all_bounded_readers_closed=True,whole_M4_complete=False,native_game_launch_complete=False,native_menu=False,native_Training=False,elapsed_seconds=time.monotonic()-started,files=DIRECT)
  q=out/'report.json';q.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(q),connected_roots=result['connected_roots'],physical_inputs=inventory.get('physical_rows',0))),flush=True)
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4])
