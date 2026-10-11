"""Accept the four Lockit roots only after fresh complete gates and full union rehash."""
from pathlib import Path
import hashlib,json,sys,time,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from manifests import normalized,digest,unique_object,verify_manifest
PINS={}
REQUIRED={'parent','game_recovery','game_lifts','game_symbols','game_callbacks','game_static','game_interface','provider_recovery','provider_lifts','provider_interface','ghidra','original_preparation','original_build','original_run','original_validation','original_review','original_source','owner_source','owner_original','native_preparation','preparation','build','abi','link','resource','native_integration','iteration','lineage','native','source','source_review','provider','provider_review','paired','paired_review','controls_build','controls_execution','controls','controls_review'}
EXTENT=dict(selected_roots=124,new_roots=4,original_sequences=6,original_phases=744,native_sequences=12,native_phases=1488,ordered_callbacks_per_sequence=96,observed_source_pages=43,MFC_allocations_per_sequence=58,string_allocations_per_sequence=19,live_ordinary_owners_per_sequence=78,live_critical_sections_per_sequence=5,new_MFC_allocations_per_sequence=8,new_requested20_allocations_per_sequence=2,new_requested24_allocations_per_sequence=6,new_actual_capacity32_allocations_per_sequence=8,new_FS_owned_store_contracts=32,new_FS_publication_contracts=8,normal_game_FS_records_per_sequence=19,linked_literal_COFFs_per_level=363,compiled_objects_per_level=27,capture_objects_per_level=2,actual_linked_inputs_per_level=392)
BOUNDED={'callback_execution','full_CRT_attach','full_native_MFC_attach','native_MSVCP_DllMain','MSVCP_lazy_or_Sleep_path','native_menu','native_Training','whole_game_alias_liveness','handler_execution','exception_dispatch','allocation_NULL_paths','whole_original_provider_stack_equality','whole_original_Windows_TIB_page_claimed','general_virtual_dispatch','nonzero_59FF80_pointee_path','naked_throwing_Session_plus_caller_catch_ENV_metadata_guaranteed'}
def need(v,message):
 if not v:raise ValueError(message)
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def register(p,h):
 p=str(Path(p).resolve());key=normalized(p);h=digest(h)
 need(key not in PINS or PINS[key]==h,'Conflicting physical dependency '+p);PINS[key]=h
def read(p,h=None):
 p=Path(p).resolve();actual=sha(p);need(h is None or h==actual,'Exact report identity '+str(p));register(p,actual)
 return json.loads(p.read_text(encoding='utf-8-sig'),object_pairs_hook=unique_object)
def absorb(report):
 for field in ('files','physical_inputs','physical_dependencies','generated_sources','sources','tools','artifacts'):
  for p,h in report.get(field,{}).items():
   need(isinstance(h,str),'Flat exact physical map '+field);register(p,h)
def has(report,p,h):
 key=normalized(str(Path(p).resolve()))
 return any(normalized(str(Path(q).resolve()))==key and value==h for field in ('files','sources','physical_inputs','physical_dependencies','tools','artifacts') for q,value in report.get(field,{}).items())
def binds(report,item,message):need(has(report,ROOT/item['path'],item['sha256']),message)
def extent_value(report,field):
 value=report
 for key in field.split('.'):
  value=value[int(key)] if isinstance(value,list) else value[key]
 return value
def main(configuration,name,review_path,review_sha256):
 started=time.perf_counter();out=ROOT/'reports/m4-joint-startup124-root'/name
 need(not out.exists(),'Fresh acceptance');out.mkdir(parents=True);passed=False;config={};rows={};closure={};predicates=0
 try:
  config=read(configuration);register(__file__,sha(__file__));register(ROOT/'tools/m4-pipeline/manifests.py',sha(ROOT/'tools/m4-pipeline/manifests.py'))
  register(config['configuration_source'],config['configuration_source_sha256'])
  register(config['review_specification'],config['review_specification_sha256'])
  need(set(config['gates'])==REQUIRED and config['extent']==EXTENT,'Complete exact124 gate set and extents')
  need(set(config['bounded_scope'])==BOUNDED and all(v is False for v in config['bounded_scope'].values()),'Explicit supported frontier')
  review=read(review_path,review_sha256);absorb(review)
  need(review['passed'] is True and review['gates_reviewed']==len(REQUIRED),'Independent complete configuration review')
  need(has(review,configuration,sha(configuration)) and has(review,__file__,sha(__file__)),'Exact reviewed configuration and final acceptance source')
  for label,item in config['gates'].items():
   path=ROOT/item['path'];report=read(path,item['sha256']);need(report['passed'] is True,'Passed gate '+label);absorb(report)
   manifest=path.parent/'pins.json'
   if manifest.exists():
    m=read(manifest);need(set(m)=={'files'},'Exact physical manifest '+label)
    for p,h in m['files'].items():register(p,h)
   need(item['equal'] and len(item['equal'])>=2,'Explicit measured gate extent '+label)
   for field,expected in item['equal'].items():need(extent_value(report,field)==expected,'Measured gate extent '+label+' '+field);predicates+=1
   rows[label]=report
  need(rows['parent']['connected_roots']==120 and not rows['parent']['whole_M4_complete'],'Accepted120 parent')
  need(rows['native']['native_executed'] and [r['level'] for r in rows['native']['levels']]==['O0','O2'],'Both actual final native levels')
  need(rows['native']['build_sha256']==config['gates']['build']['sha256'],'Execution binds exact build')
  need(rows['build']['preparation_sha256']==config['gates']['preparation']['sha256'],'Build binds exact preparation')
  need(rows['original_run']['build_sha256']==config['gates']['original_build']['sha256'],'Original exact reviewed worker')
  need(rows['original_validation']['build_sha256']==config['gates']['original_build']['sha256'],'Original validation exact reviewed worker')
  need(rows['controls_execution']['build_sha256']==config['gates']['controls_build']['sha256'],'Controls exact reviewed worker')
  need(rows['controls_build']['parent_build_sha256']==config['gates']['build']['sha256'],'Controls compiled final candidate')
  binds(rows['original_source'],config['gates']['original_validation'],'Source binds exact actual original validation')
  for label in ('abi','link','resource'):binds(rows[label],config['gates']['build'],'Independent final build review '+label)
  for label in ('native_preparation','preparation','build'):binds(rows['lineage'],config['gates'][label],'Exact physical preparation lineage '+label)
  for label in ('source','provider','paired'):binds(rows[label],config['gates']['native'],'Fresh final native input '+label)
  for label in ('source','provider'):
   need(rows[label]['per_phase_BEFORE_machine_seed'] is False and rows[label]['candidate_AFTER_machine_seed'] is False,'Single bootstrap and persistent source '+label)
  c=rows['source']['counts']
  need(c['persistent124_sequences']==12 and c['persistent_phases']==1488 and c['whole_page_BEFORE']==c['whole_page_AFTER']==63984 and c['literal_registration_roots']==1152,'Complete persistent source124 schedule and43pages')
  need(c['literal_Lockit_CALL_RET_pairs']==c['actual_native_CS40_source_API_relations']==96 and c['native_FS_source_accesses']==684 and c['actual_native12B_source_relations']==456,'Every new native Lockit pair and normal game chain record')
  c=rows['provider']['provider_counts'];sequences=rows['provider']['provider_sequences']
  need(len(sequences)==12 and {(r['level'],r['sequence']) for r in sequences}=={(level,sequence) for level in ('O0','O2') for sequence in range(6)},'Every current provider sequence')
  need(c['complete124_provider_sequences']==12 and c['selected_registration_closures']==1152 and c['actual_MFC_allocations']==696 and c['actual_duplicate_allocations']==228 and c['actual_source_frees']==936 and c['actual_MFC_source_frees']==696 and c['actual_CS_deletes']==60 and c['actual_heap_destroys']==12,'Complete current provider allocation and real cleanup counts')
  need(all(r['all_resources_released'] and r['actual_post_HeapDestroy_identity'] for r in sequences),'All current resources released and destroyed heap identities observed')
  need(c['whole_State_checkpoints']==c['whole_CPU_checkpoints']==c['whole_FX_checkpoints']==sum(r['compared_checkpoints'] for r in sequences),'Complete provider machine checkpoints')
  need(all(r['selected_used_bytes']==384 and r['first_replay_msize_capacity']>=384 and r['first_replay_msize_capacity']%4==0 and r['predicted_growth_replays']==r['actual_growth_replays']==(r['first_replay_msize_capacity']-384)//4+1 and r['first_replay_msize_queries']==(2 if r['first_replay_msize_capacity']==384 else 1) for r in sequences),'Genuine same-owner size query independently predicts next callback-vector growth')
  need(c['actual_first_replay_msize_queries']==sum(r['first_replay_msize_queries'] for r in sequences) and c['genuine_growth_replays']==sum(r['actual_growth_replays'] for r in sequences),'Exact actual size query and growth totals')
  need(rows['original_source']['AFTER_machine_seed'] is False and rows['original_source']['observed_original_postRET'] is False,'Actual original boundaries versus source-derived postRET')
  need(rows['original_source']['whole_original_provider_stack_equivalence'] is False,'Bounded actual API observation scope')
  binds(rows['provider_review'],config['gates']['provider'],'Independent exact provider proof review')
  binds(rows['source_review'],config['gates']['source'],'Independent exact persistent source proof review')
  binds(rows['paired_review'],config['gates']['paired'],'Independent exact paired proof review')
  paired=rows['paired'];c=paired['counts']
  need(c['paired_phases']==1488 and c['paired124_sequences']==12 and c['whole_nonstack_page_relations']==122016 and c['separate_whole_loader_page_input_relations']==2976 and c['whole42_nonstack_page_endpoint_relations']==c['whole_nonstack_page_relations']+c['separate_whole_loader_page_input_relations']==124992,'Complete124 paired phases,41 ordinary pages and separately retained complete loader page')
  need(c['Lockit_paired_complete12B_normal_FS_relations']==c['Lockit_paired_bounded_API_semantic_relations']==c['Lockit_actual_owner_publication_activations']==96 and c['Lockit_branch_field_source_derivations']==216 and c['Lockit_whole_native_owned_carries']==288,'Every new paired API, chain, owner and source byte relation')
  need(paired['blanket_page_mask'] is False and paired['original_and_native_bytes_modified'] is False and paired['whole_game_liveness_proven'] is False and paired['Lockit_original_postRET_observed'] is False and paired['Lockit_opaque_loaded_bytes_masked'] is False,'Unmodified actual bytes and explicit bounded original observation scope')
  need(paired['original_record_bytes']==356992 and paired['native_record_bytes']==159716 and paired['Lockit_whole_private_initial_backings']==32 and paired['Lockit_native_whole_mapped_backings']==4096,'Unchanged packed schemas and complete original/native owner extents')
  binds(rows['controls_review'],config['gates']['controls'],'Independent exact causal controls review')
  binds(rows['controls'],config['gates']['controls_execution'],'Controls bind actual execution')
  binds(rows['controls'],config['gates']['build'],'Controls use final candidate implementation')
  need(rows['owner_original']['source_contract_sha256']==rows['owner_source']['contracts_sha256'],'Original source and native owner interface share exact physical contract')
  need(has(rows['owner_original'],rows['owner_source']['contracts'],rows['owner_source']['contracts_sha256']),'Actual original source pins common owner contract')
  binds(rows['owner_original'],config['gates']['owner_source'],'Exact corroborated native owner interface')
  binds(rows['owner_original'],config['gates']['original_source'],'Exact actual original source owner observations')
  need(len(rows['preparation']['selected_order'])==124 and len(rows['preparation']['registration_roots'])==96,'Final exact schedule and callbacks')
  need(rows['native_preparation']['new_FS_owned_accesses']==32 and rows['native_preparation']['new_FS_owned_publications']==8 and rows['native_preparation']['generic_MFC_publication_count_for_new_sites']==0,'Exact sole ownership publication contract')
  need(rows['native_preparation']['native_DllMain_executed'] is False and rows['native_preparation']['guest_CS_native_opaque_copy'] is False,'Explicit native resource association and typed guest fields')
  # No historical archive exemptions: local iteration reuse ends at this gate.
  for label in ('build','native'):
   need(rows[label]['full_dependency_acceptance_rehash_required'] is True,'Local iteration full-acceptance obligation '+label)
   for p,h in rows[label]['inherited_capture_payload_hashes_reused'].items():
    need(PINS.get(normalized(str(Path(p).resolve())))==h,'Every reused payload retained in final union')
  closure=verify_manifest(PINS);need(closure['passed'] and closure['metadata_only_cache_used'] is False,'Complete conflict-normalized physical rehash');passed=True
 except BaseException:
  (out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  result=dict(passed=passed,scope='Connected selected124: four new literal Lockit/container initializers and real native CS association; bounded actual/source/paired/resource proofs',connected_roots=124 if passed else 120,new_roots=4 if passed else 0,total_inventory_roots=144,remaining_inventory_roots=20 if passed else 24,initializer_inventory_fraction=124/144 if passed else 120/144,inventory_is_project_completion_percentage=False,gates=config.get('gates',{}),extent=config.get('extent',{}),explicit_measured_predicates=predicates,bounded_scope=config.get('bounded_scope',{}),physical_closure=closure,elapsed_seconds=time.perf_counter()-started,whole_M4_complete=False,native_game_launch_complete=False,files=PINS)
  (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');register(out/'report.json',sha(out/'report.json'));(out/'pins.json').write_text(json.dumps(dict(files=PINS),indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),connected_roots=result['connected_roots'],physical_inputs=len(PINS))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4])
