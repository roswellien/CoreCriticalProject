"""Current138 acceptance using retained131 criteria and full disk-backed union.

Never use an incomplete configuration: all39 current evidence gates and an
independent exact checker/configuration review are mandatory. Every physical
dependency is freshly whole-byte hashed, including every sealed controls row.
"""
from pathlib import Path
import ast,hashlib,importlib.util,json,re,sys,time,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'));sys.path.insert(0,str(Path(__file__).parent))
from manifests import normalized,digest,unique_object
import acceptance138_storage as storage
PARENT_SHA='aa9462f30bf4fa6c80ef926488928bb8680f207020e4f0aa166968caaf724061'
PARENT_CHECKER=ROOT/'tools/m4-joint-startup131/acceptance.py'
tree=ast.parse(PARENT_CHECKER.read_text());BASE_REQUIRED=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='REQUIRED'for t in n.targets))
ADDITIONAL={'source_widget_journal_review','source_widget_memory_review','source_widget_semantic_review','controls_full_raw','controls_gdi_owners','controls_current_link'}
REQUIRED=BASE_REQUIRED|ADDITIONAL
PINS=None;DIRECT={}
def need(v,label):
 if not v:raise ValueError(label)
def sha(path):return storage.sha(path)
def register(path,h):PINS[str(Path(path).resolve())]=h
def read(path,h=None,stream=False):
 path=Path(path).resolve();actual=sha(path);need(h is None or h==actual,'Exact current receipt '+str(path));register(path,actual);DIRECT[str(path)]=actual
 if stream:return storage.read_report(path,register)
 return json.loads(path.read_text(encoding='utf-8-sig'),object_pairs_hook=unique_object)
FIELDS=('files','physical_inputs','physical_dependencies','generated_sources','sources','tools','artifacts','retained_capture_inputs')
def absorb(report):
 for field in FIELDS:
  for p,h in report.get(field,{}).items():register(p,h)
def value_at(report,field):
 for key in field.split('.'):report=report[int(key)]if isinstance(report,list)else report[key]
 return report
def typed_equal(actual,expected,label):need(type(actual)is type(expected)and actual==expected,'Exact typed '+label)
def has(report,path,h):
 target=normalized(str(Path(path).resolve()));return any(normalized(str(Path(p).resolve()))==target and identity==h for field in FIELDS for p,identity in report.get(field,{}).items())
def baseline_criteria(config):
 old=read(ROOT/'reports/m4-joint-startup131-root/configuration-r1/configuration.json');coverage=config['baseline_criteria']
 need(set(coverage)==BASE_REQUIRED,'Every accepted131 gate predicate preserved/translated')
 for label,gate in old['gates'].items():
  need(set(coverage[label])==set(gate['equal']),'Every accepted baseline predicate covered '+label)
  for oldfield,relation in coverage[label].items():
   need(set(relation)=={'current_field','reason'}and isinstance(relation['reason'],str)and relation['reason'].strip(),'Reviewed explicit criterion translation')
   need(relation['current_field']in config['gates'][label]['equal'],'Exact current typed predicate for '+label+'.'+oldfield)
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
 raw=rows['controls_full_raw'];typed_equal(raw['controls_verification_sha256'],gates['controls']['sha256'],'Complete raw current controls join')
 for field,n in {'whole_export_targets_authenticated':10691866,'whole_exported_retry_files_equal':3547696}.items():typed_equal(raw['counts'][field],n,'Complete raw/private retry extent '+field)
 for field in ('acceptance_requires_inventory_expansion','all_bounded_readers_closed','raw_export_readers_closed','raw_exports_all_logical_entries'):typed_equal(raw[field],True,'Closed durable controls proof '+field)
 typed_equal(raw['capture_archives_opened'],0,'No fullraw archive reads');typed_equal(raw['worker_executed'],False,'No new fullraw worker');typed_equal(raw['initializer_credit'],0,'No standalone fullraw credit')
 for label,target in [('controls_gdi_owners','controls'),('controls_current_link','native_execution'),('controls_full_raw','controls')]:need(has(rows[label],ROOT/gates[target]['path'],gates[target]['sha256']),'Exact current physical review edge '+label)
def main(configuration,name,review_path,review_sha):
 global PINS
 out=ROOT/'reports/m4-joint-startup138-root'/name;need(not out.exists(),'Fresh acceptance output');out.mkdir(parents=True);PINS=storage.Union(out/'physical-union.sqlite');passed=False;config={};closure={};inventory={};expanded={};predicates=0;started=time.monotonic()
 try:
  config=read(configuration);need(set(config['gates'])==REQUIRED,'All39 mandatory evidence gates');baseline_criteria(config)
  for field in ('configuration_source','review_specification','bindings'):
   register(config[field],config[field+'_sha256']);DIRECT[config[field]]=config[field+'_sha256']
  for p in [Path(__file__),Path(storage.__file__),PARENT_CHECKER,Path(sys.executable),ROOT/'tools/m4-pipeline/manifests.py',ROOT/'tools/m4-138-controls-review/acceptance138_semantics_v3.py',ROOT/'tools/m4-138-controls-review/full_raw_review_v2.py',ROOT/'tools/m4-138-controls-review/expand_proof_inventory.py']:
   register(p,sha(p));DIRECT[str(p.resolve())]=sha(p)
  review=read(review_path,review_sha);absorb(review)
  need(review['passed']is True and review['gates_reviewed']==len(REQUIRED)and review['baseline_predicates_reviewed']==841 and review['criteria_translation_reviewed']is True,'Independent full criteria/configuration review')
  for p in [configuration,Path(__file__),Path(storage.__file__),ROOT/'tools/m4-138-controls-review/acceptance138_semantics_v3.py']:need(has(review,p,sha(p)),'Independent sealed exact machinery '+str(p))
  rows={}
  for label,gate in config['gates'].items():
   need(set(gate)=={'path','sha256','equal'}and len(gate['equal'])>=2,'Exact complete measured gate schema '+label);path=ROOT/gate['path'];report=read(path,gate['sha256'],stream=label=='controls');typed_equal(report['passed'],True,'Passed current gate '+label);absorb(report)
   sibling=path.parent/'pins.json'
   # Giant controls declarations are already streamed from report.files; all
   # other supplementary ordinary manifest receipts are absorbed whole.
   if sibling.exists():absorb(read(sibling,stream=label=='controls'))
   for field,expected in gate['equal'].items():typed_equal(value_at(report,field),expected,label+':'+field);predicates+=1
   rows[label]=report
  module=storage.load('accepted138_retained_semantics',ROOT/'tools/m4-138-controls-review/acceptance138_semantics_v3.py')
  for key in ('ROOT','PARENT_SHA','PINS','need','typed_equal','read','register','sha','has','Path','re'):setattr(module,key,globals()[key])
  module.semantic_checks(rows,config['gates']);additions(rows,config['gates'])
  expansion=storage.load('accepted138_full_controls_expansion',ROOT/'tools/m4-138-controls-review/expand_proof_inventory.py')
  expanded=expansion.expand(ROOT/config['gates']['controls_full_raw']['path'],config['gates']['controls_full_raw']['sha256'],register,lambda n:print(json.dumps(dict(progress='expand_fullraw',rows=n)),flush=True))
  need(expanded['passed']is True and expanded['database_reader_closed']is True and expanded['metadata_only_cache_used']is False,'Complete closed controls expansion')
  closure=PINS.verify(lambda n:print(json.dumps(dict(progress='fresh_all_history_union',rows=n)),flush=True));inventory=PINS.seal();need(closure['passed']and not closure['metadata_only_cache_used']and closure['unique_physical_dependencies']==inventory['physical_rows'],'Fresh complete historical/current union')
  DIRECT[inventory['path']]=inventory['sha256'];passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  PINS.close()
  result=dict(passed=passed,scope='Connected selected138 startup inventory after retained131/current original/native/source/provider/widget/pair/controls gates and complete byte-rehashed union',connected_roots=138 if passed else 131,new_roots=7 if passed else 0,total_inventory_roots=144,remaining_inventory_roots=6 if passed else 13,inventory_is_project_completion_percentage=False,gates=config.get('gates',{}),explicit_measured_predicates=predicates,baseline_measured_predicates=841,physical_closure=closure,full_controls_expansion=expanded,proof_inventory=inventory,acceptance_requires_inventory_expansion=passed,all_bounded_readers_closed=True,whole_M4_complete=False,native_game_launch_complete=False,native_menu=False,native_Training=False,elapsed_seconds=time.monotonic()-started,files=DIRECT)
  q=out/'report.json';q.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(q),connected_roots=result['connected_roots'],physical_inputs=inventory.get('physical_rows',0))),flush=True)
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4])
