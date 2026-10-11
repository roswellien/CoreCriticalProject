"""Accept six FS roots only after measured109 gates and one full rehash."""
from pathlib import Path
import hashlib,json,sys,time,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from manifests import normalized,digest,unique_object,verify_manifest
PINS={}
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def register(p,h):
 p=str(Path(p).resolve());key=normalized(p);h=digest(h)
 need(key not in PINS or PINS[key]==h,'Conflicting acceptance dependency '+p);PINS[key]=h
def read(p,h=None):
 p=Path(p).resolve();actual=sha(p);need(h is None or h==actual,'Exact receipt identity '+str(p));register(p,actual)
 return json.loads(p.read_text(encoding='utf-8-sig'),object_pairs_hook=unique_object)
def receipt(label,item):
 p=ROOT/item['path'];r=read(p,item['sha256']);need(r['passed'] is True,'Passed gate '+str(p))
 for field in ('files','physical_inputs'):
  for path,h in r.get(field,{}).items():register(path,h)
 manifest=p.parent/'pins.json'
 if manifest.exists():
  m=read(manifest)
  if label=='native_preparation':
   need(isinstance(m,dict) and bool(m) and 'files' not in m,'Exact existing flat native-preparation manifest');files=m
  else:
   need(set(m)=={'files'},'Exact physical manifest schema');files=m['files']
  for path,h in files.items():register(path,h)
 for field,expected in item['equal'].items():
  value=r
  for key in field.split('.'):value=value[key]
  need(value==expected,'Measured gate extent '+item['path']+' '+field)
 return r
REQUIRED={'parent','source_recovery','game_lifts','game_symbols','game_callbacks','geometry','allocation_interface','fields','ghidra','game_static','original_preparation','original_build','original_run','original_validation','original_observer','original_FS','original_source','native_preparation','preparation','build','native','link','source','provider','provider_review','provider_seal','paired','paired_FS','paired_owned','paired_review','controls_build','controls_execution','controls','control_audit','control_static','control_seal','continuity'}
EXTENT=dict(selected_roots=109,new_roots=6,original_sequences=6,original_phases=654,native_sequences=12,native_phases=1308,MFC_allocations_per_sequence=45,new_FS_allocations_per_sequence=10,string_allocations_per_sequence=16,live_ordinary_owners_per_sequence=62,ordered_callbacks_per_sequence=81,observed_source_pages=35,linked_literal_COFFs_per_level=312,compiled_objects_per_level=27,capture_objects_per_level=2,actual_linked_inputs_per_level=341,retained_unlinked_archives_per_level=1,normal_FS_records_per_sequence=7,native_FS_record_snapshots_per_sequence=14)
def main(configuration,name):
 started=time.perf_counter();out=ROOT/'reports/m4-joint-startup109-root'/name;need(not out.exists(),'Fresh acceptance');out.mkdir(parents=True);passed=False;physical={};config={}
 try:
  config=read(configuration);register(__file__,sha(__file__));register(ROOT/'tools/m4-pipeline/manifests.py',sha(ROOT/'tools/m4-pipeline/manifests.py'))
  register(config['configuration_source'],config['configuration_source_sha256'])
  register(config['review_specification'],config['review_specification_sha256'])
  need(set(config['gates'])==REQUIRED and config['extent']==EXTENT,'Complete exact109 gate set and extent')
  rows={label:receipt(label,item) for label,item in config['gates'].items()}
  need(rows['parent']['connected_roots']==103 and not rows['parent']['whole_M4_complete'],'Accepted103 parent')
  need(rows['native']['native_executed'] and [x['level'] for x in rows['native']['levels']]==['O0','O2'],'Both actual final native levels')
  need(rows['native']['build_sha256']==config['gates']['build']['sha256'],'Final execution binds exact final build')
  need(rows['original_run']['build_sha256']==config['gates']['original_build']['sha256'],'Original capture binds exact reviewed worker')
  need(rows['controls_execution']['build_sha256']==config['gates']['controls_build']['sha256'],'Controls execution binds exact reviewed worker')
  need(rows['build']['preparation_sha256']==config['gates']['preparation']['sha256'],'Final build binds exact frozen preparation')
  need(rows['native_preparation']['normal_new_allocations']==10 and rows['native_preparation']['normal_total_live_owners']==62,'Actual positive-path native admission geometry')
  for key in ('original_validation','original_FS','original_source','source','provider','paired','paired_FS','paired_owned','paired_review','controls','control_audit','provider_review','continuity'):
   need(len(config['gates'][key]['equal'])>=2,'Explicit measured scope contract '+key)
  c=rows['source']['counts'];need(c['persistent_phases']==1308 and c['persistent109_sequences']==12 and c['literal_registration_roots']==972 and c['whole_page_BEFORE']==c['whole_page_AFTER']==45780,'Complete source109 extent')
  for key in ('source','provider'):
   need(not rows[key]['per_phase_BEFORE_machine_seed'] and not rows[key]['candidate_AFTER_machine_seed'],'One bootstrap; no per-phase or AFTER model seeding')
  c=rows['provider']['provider_counts'];need(c['complete109_provider_sequences']==12 and c['selected_registration_closures']==972 and c['actual_MFC_allocations']==540 and c['actual_duplicate_allocations']==192 and c['actual_source_frees']==744 and c['actual_MFC_source_frees']==540 and c['actual_heap_destroys']==c['actual_post_HeapDestroy_identity_proofs']==12 and c['actual_first_replay_msize_capacity_derivations']==12,'Complete genuine provider/owner/growth/cleanup proof')
  sequences=rows['provider']['provider_sequences'];need(len(sequences)==12 and {(r['level'],r['sequence']) for r in sequences}=={(level,seq) for level in ('O0','O2') for seq in range(6)} and all(r['all_resources_released'] and r['actual_post_HeapDestroy_identity'] for r in sequences),'Every actual provider sequence and released heap identity')
  need(c['whole_State_checkpoints']==c['whole_CPU_checkpoints']==c['whole_FX_checkpoints']==sum(r['compared_checkpoints'] for r in rows['provider']['provider_sequences']),'Each measured complete provider checkpoint has whole machine projections')
  p=rows['paired'];need(not p['blanket_page_mask'] and not p['original_and_native_bytes_modified'] and not p['whole_game_liveness_proven'],'Unmodified bytes and bounded exact typed relations')
  need(p['counts']['paired_phases']==1308 and p['counts']['whole_nonstack_page_relations']==88944 and p['counts']['paired109_sequences']==12,'Every paired phase and complete34nonstack pages on both sides')
  need(set(p['new_FS_source_publication_fields'])=={0x60b888,0x609990,0x60b520} and p['new_FS_header_relation_address']==0x60b51c,'Only exact new fixed-page FS field relations')
  need(rows['link']['literal_COFF_links']==624 and rows['link']['actual_linked_inputs']==682 and rows['link']['retained_unlinked_archives']==2,'Actual final link extents')
  need(config['bounded_scope']['naked_throwing_Session_plus_caller_catch_ENV_metadata_guaranteed'] is False and config['bounded_scope']['controls_host_boundary_scope']=='Authored caller NumericHostBoundary enclosing invocation and C++ catch','Exact tested error-boundary scope')
  for key in ('callback_execution','full_CRT_attach','full_native_MFC_attach','native_menu','native_Training','whole_game_alias_liveness','handler_execution','exception_dispatch','allocation_NULL_paths','whole_original_provider_stack_equality','whole_original_Windows_TIB_page_claimed','capture_shared_format_adopted'):
   need(config['bounded_scope'][key] is False,'Explicit supported frontier '+key)
  physical=verify_manifest(PINS);need(physical['passed'] and not physical['metadata_only_cache_used'],'Full conflict-normalized physical verification');passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  result=dict(passed=passed,scope='Connected selected109 in original relative table order: six new normal FS constructors, persistent literal source/typed owners and normal chain records',connected_roots=109 if passed else 103,new_roots=6 if passed else 0,total_inventory_roots=144,remaining_inventory_roots=35 if passed else 41,initializer_inventory_fraction=109/144 if passed else 103/144,inventory_is_project_completion_percentage=False,gates=config.get('gates',{}),extent=config.get('extent',{}),bounded_scope=config.get('bounded_scope',{}),physical_closure=physical,elapsed_seconds=time.perf_counter()-started,whole_M4_complete=False,native_game_launch_complete=False,files=PINS)
  (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');register(out/'report.json',sha(out/'report.json'));(out/'pins.json').write_text(json.dumps(dict(files=PINS),indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),connected_roots=result['connected_roots'],physical_inputs=len(PINS))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2])
