"""Accept four finite-vtable roots after measured gates and a complete physical rehash."""
from pathlib import Path
import hashlib,json,sys,time,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from manifests import normalized,digest,unique_object,verify_manifest
PINS={}

def need(value,message):
 if not value:raise ValueError(message)

def sha(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def register(path,value):
 path=str(Path(path).resolve());key=normalized(path);value=digest(value)
 need(key not in PINS or PINS[key]==value,'Conflicting acceptance dependency '+path)
 PINS[key]=value

def read(path,expected=None):
 path=Path(path).resolve();actual=sha(path)
 need(expected is None or expected==actual,'Exact receipt identity '+str(path));register(path,actual)
 return json.loads(path.read_text(encoding='utf-8-sig'),object_pairs_hook=unique_object)

def receipt(label,item):
 path=ROOT/item['path'];report=read(path,item['sha256'])
 need(report['passed'] is True,'Passed gate '+str(path))
 for field in ('files','physical_inputs'):
  for dependency,value in report.get(field,{}).items():register(dependency,value)
 manifest=path.parent/'pins.json'
 if manifest.exists():
  pins=read(manifest);need(set(pins)=={'files'},'Exact nested physical manifest schema '+label)
  for dependency,value in pins['files'].items():register(dependency,value)
 for field,expected in item['equal'].items():
  actual=report
  for key in field.split('.'):actual=actual[key]
  need(actual==expected,'Measured gate extent '+label+' '+field)
 return report

def binds(report,path,expected,message):
 files={normalized(str(Path(p).resolve())):value for p,value in report.get('files',{}).items()}
 need(files.get(normalized(str(Path(path).resolve())))==expected,message)

REQUIRED={'parent','source_recovery','game_lifts','provider_lifts','game_symbols','game_callbacks','geometry','allocation_interface','loader_identity','ghidra','game_static','original_preparation','original_build','original_run','original_validation','original_FS','original_observer_static','original_observer_compiled','malloc_EDX','original_source','native_preparation','preparation','build','native','link','source','provider_preparation','provider','provider_review','provider_seal','paired','paired_FS','paired_owned','paired_review','controls_build','controls_execution','controls','control_audit','control_static','control_seal','continuity','loader_page_review','indirect_interface','indirect_source'}
EXTENT=dict(selected_roots=120,new_roots=4,original_sequences=6,original_phases=720,native_sequences=12,native_phases=1440,MFC_allocations_per_sequence=50,string_allocations_per_sequence=19,live_ordinary_owners_per_sequence=70,ordered_callbacks_per_sequence=92,observed_source_pages=40,linked_literal_COFFs_per_level=351,compiled_objects_per_level=27,capture_objects_per_level=2,actual_linked_inputs_per_level=380,retained_unlinked_archives_per_level=1,new_vector_allocations_per_sequence=5,new_string_allocations_per_sequence=3,normal_new_NULL_frees_per_sequence=5,new_borrowed_string_constructors_per_sequence=3,new_vector_endpoint_stores_per_sequence=17,normal_game_FS_records_per_sequence=15,native_game_FS_record_snapshots_per_sequence=30)

def main(configuration,name):
 started=time.perf_counter();out=ROOT/'reports/m4-joint-startup120-root'/name
 need(not out.exists(),'Fresh acceptance');out.mkdir(parents=True);passed=False;physical={};config={}
 try:
  config=read(configuration);register(__file__,sha(__file__))
  register(ROOT/'tools/m4-pipeline/manifests.py',sha(ROOT/'tools/m4-pipeline/manifests.py'))
  register(config['configuration_source'],config['configuration_source_sha256'])
  register(config['review_specification'],config['review_specification_sha256'])
  need(set(config['gates'])==REQUIRED and config['extent']==EXTENT,'Complete exact120 gate set and extent')
  rows={label:receipt(label,item) for label,item in config['gates'].items()}
  need(rows['parent']['connected_roots']==116 and not rows['parent']['whole_M4_complete'],'Accepted116 parent')
  need(rows['native']['native_executed'] and [x['level'] for x in rows['native']['levels']]==['O0','O2'],'Both actual final native levels')
  need(rows['native']['build_sha256']==config['gates']['build']['sha256'],'Final execution binds exact final build')
  need(rows['original_run']['build_sha256']==config['gates']['original_build']['sha256'],'Original capture binds exact reviewed worker')
  need(rows['controls_execution']['build_sha256']==config['gates']['controls_build']['sha256'],'Controls execution binds exact reviewed worker')
  need(rows['build']['preparation_sha256']==config['gates']['preparation']['sha256'],'Final build binds exact frozen preparation')
  need(rows['preparation']['parent_acceptance_sha256']==rows['native_preparation']['parent_acceptance_sha256']==config['gates']['parent']['sha256'],'Both preparations bind accepted116')
  need(rows['original_validation']['build_sha256']==config['gates']['original_build']['sha256'],'Original validation binds final reviewed worker')
  binds(rows['original_source'],ROOT/config['gates']['original_validation']['path'],config['gates']['original_validation']['sha256'],'Original source binds exact original validation')
  for key in ('source','provider','paired','paired_FS','paired_owned','continuity','loader_page_review','indirect_source'):
   binds(rows[key],ROOT/config['gates']['native']['path'],config['gates']['native']['sha256'],'Final native capture identity '+key)
  for key in ('original_run','original_validation','native_preparation','source_recovery'):
   binds(rows['indirect_source'],ROOT/config['gates'][key]['path'],config['gates'][key]['sha256'],'Exact finite-call source input '+key)
  for report_key,input_keys in [('paired_review',('paired','original_observer_compiled')),('control_audit',('controls_execution','controls')),('original_observer_compiled',('original_build','original_preparation')),('provider_review',('provider','provider_preparation')),('provider_seal',('provider','provider_preparation','provider_review','native'))]:
   for input_key in input_keys:
    binds(rows[report_key],ROOT/config['gates'][input_key]['path'],config['gates'][input_key]['sha256'],'Exact independent review input '+report_key+' '+input_key)
  binds(rows['controls'],ROOT/config['gates']['controls_execution']['path'],config['gates']['controls_execution']['sha256'],'Strict controls bind final actual controls execution')
  need(rows['native_preparation']['normal_new_allocations']==0 and rows['native_preparation']['normal_total_live_owners']==70,'Actual positive-path native admission geometry')
  for key in ('original_validation','original_FS','original_source','source','provider','paired','paired_FS','paired_owned','paired_review','controls','control_audit','provider_review','continuity','loader_page_review','indirect_interface','indirect_source'):
   need(len(config['gates'][key]['equal'])>=2,'Explicit measured scope contract '+key)
  i=rows['indirect_interface']
  need(i['rooted_calls']==6 and i['absolute_cell_calls']==4 and i['actual_instance_slot_calls']==2 and i['root_count']==4 and i['new_provider_calls']==i['new_allocations']==i['new_string_copies']==0 and not i['nonzero_pointer_path_admitted'],'Exact finite physical six-call interface')
  i=rows['indirect_source'];c=i['counts']
  need(c['actual_native_CALL_RET_joins']==72 and c['actual_native_full_State_CPU_FX_boundaries']==144 and c['actual_original_CALL_preRET_joins']==36 and c['actual_original_full_CPU_FX_ENV_boundaries']==72 and c['paired_source_CALL_interfaces']==72,'Every actual native and original finite-call boundary')
  need(c['native_zero_argument_no_pointee_prefixes']==24 and c['original_zero_argument_no_pointee_prefixes']==12 and c['native_whole_OR_CPU_flags_prefixes']==24 and c['original_whole_OR_CPU_flags_prefixes']==12 and c['native_dominating_vptr_publications']==48 and c['original_dominating_vptr_publications']==24,'Exact null-path, OR prefix and dominating publication scope')
  need(i['original_postRET_CPU_source_derived_only'] and not i['AFTER_machine_seed'] and not i['per_phase_machine_seed'] and not i['whole_crossbranch_volatile_CPU_equality_claimed'] and not i['nonzero_pointer_path_admitted'] and i['new_provider_or_owner_operations']==0,'Measured entry/preRET original scope and genuine native source joins')
  c=rows['source']['counts']
  need(c['persistent_phases']==1440 and c['persistent120_sequences']==12 and c['literal_registration_roots']==1104 and c['whole_page_BEFORE']==c['whole_page_AFTER']==57600,'Complete persistent source120 extent')
  for key in ('source','provider'):
   need(not rows[key]['per_phase_BEFORE_machine_seed'] and not rows[key]['candidate_AFTER_machine_seed'],'One bootstrap; no per-phase or AFTER model seeding')
  c=rows['provider']['provider_counts']
  need(c['complete120_provider_sequences']==12 and c['selected_registration_closures']==1104 and c['actual_MFC_allocations']==600 and c['actual_duplicate_allocations']==228 and c['actual_source_frees']==840 and c['actual_MFC_source_frees']==600 and c['actual_heap_destroys']==c['actual_post_HeapDestroy_identity_proofs']==12 and c['actual_first_replay_msize_capacity_derivations']==12,'Complete genuine provider/owner/growth/cleanup proof')
  need(c['actual_normal_null_frees']==60 and c['actual_borrowed_constructors']==36 and c['source_unchanged_acquired_vector_extents']==60,'Complete carried container/provider source footprint')
  sequences=rows['provider']['provider_sequences']
  need(len(sequences)==12 and {(r['level'],r['sequence']) for r in sequences}=={(level,seq) for level in ('O0','O2') for seq in range(6)} and all(r['all_resources_released'] and r['actual_post_HeapDestroy_identity'] for r in sequences),'Every actual provider sequence and released heap identity')
  need(c['whole_State_checkpoints']==c['whole_CPU_checkpoints']==c['whole_FX_checkpoints']==sum(r['compared_checkpoints'] for r in sequences),'Each complete provider checkpoint has whole machine projections')
  need(all(r['selected_used_bytes']==368 and r['first_replay_msize_capacity']>=368 and r['first_replay_msize_capacity']%4==0 and r['predicted_growth_replays']==r['actual_growth_replays']==(r['first_replay_msize_capacity']-368)//4+1 and r['first_replay_msize_queries']==(2 if r['first_replay_msize_capacity']==368 else 1) for r in sequences),'First genuine measured capacity and literal four-byte append predict each actual growth')
  need(c['actual_first_replay_msize_queries']==sum(r['first_replay_msize_queries'] for r in sequences) and c['genuine_growth_replays']==sum(r['actual_growth_replays'] for r in sequences),'Actual per-sequence query and source replay totals')
  need(all(field in config['gates']['provider']['equal'] for field in ('provider_counts.actual_first_replay_msize_queries','provider_counts.genuine_growth_replays','provider_counts.successful_actual_growth')),'Explicit measured actual growth extent')
  paired=rows['paired']
  need(not paired['blanket_page_mask'] and not paired['original_and_native_bytes_modified'] and not paired['whole_game_liveness_proven'],'Unmodified bytes and bounded exact typed relations')
  need(paired['counts']['paired_phases']==1440 and paired['counts']['whole_nonstack_page_relations']==109440 and paired['counts']['paired120_sequences']==12,'Every paired phase and complete38ordinary nonstack pages on both sides')
  need(rows['link']['literal_COFF_links']==702 and rows['link']['actual_linked_inputs']==760 and rows['link']['retained_unlinked_archives']==2,'Actual final link extents')
  need(config['bounded_scope']['naked_throwing_Session_plus_caller_catch_ENV_metadata_guaranteed'] is False and config['bounded_scope']['controls_host_boundary_scope']=='Authored caller NumericHostBoundary enclosing invocation and C++ catch','Exact tested error-boundary scope')
  for key in ('callback_execution','full_CRT_attach','full_native_MFC_attach','native_menu','native_Training','whole_game_alias_liveness','handler_execution','exception_dispatch','allocation_NULL_paths','whole_original_provider_stack_equality','whole_original_Windows_TIB_page_claimed','capture_shared_format_adopted','general_virtual_dispatch','nonzero_59FF80_pointee_path'):
   need(config['bounded_scope'][key] is False,'Explicit supported frontier '+key)
  physical=verify_manifest(PINS)
  need(physical['passed'] and not physical['metadata_only_cache_used'],'Full conflict-normalized physical verification');passed=True
 except BaseException:
  (out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  result=dict(passed=passed,scope='Connected selected120 in original relative table order: four new finite-vtable constructors, persistent literal source/typed owners and normal chain records',connected_roots=120 if passed else 116,new_roots=4 if passed else 0,total_inventory_roots=144,remaining_inventory_roots=24 if passed else 28,initializer_inventory_fraction=120/144 if passed else 116/144,inventory_is_project_completion_percentage=False,gates=config.get('gates',{}),extent=config.get('extent',{}),bounded_scope=config.get('bounded_scope',{}),physical_closure=physical,elapsed_seconds=time.perf_counter()-started,whole_M4_complete=False,native_game_launch_complete=False,files=PINS)
  (out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
  register(out/'report.json',sha(out/'report.json'));(out/'pins.json').write_text(json.dumps(dict(files=PINS),indent=2)+'\n')
  print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),connected_roots=result['connected_roots'],physical_inputs=len(PINS))))

if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2])
