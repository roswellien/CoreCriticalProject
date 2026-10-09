"""Count candidate103 only after all independent measured gates are frozen."""
from pathlib import Path
import hashlib,json,sys,time,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PINS={}
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from manifests import verify_manifest
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def pin(p,h=None):
 p=Path(p).resolve();key=str(p)
 if key not in PINS:PINS[key]=sha(p)
 need(h is None or PINS[key]==h,'Exact physical acceptance dependency '+key);return p
def receipt(item):
 p=pin(ROOT/item['path'],item['sha256']);r=json.loads(p.read_text(encoding='utf-8-sig'));need(r['passed']is True,'Passed gate '+str(p))
 for field in('files','physical_inputs'):
  for path,h in r.get(field,{}).items():pin(path,h)
 if(p.parent/'pins.json').exists():
  for path,h in json.loads(pin(p.parent/'pins.json').read_text(encoding='utf-8-sig'))['files'].items():pin(path,h)
 for field,expected in item.get('equal',{}).items():
  value=r
  for key in field.split('.'):value=value[key]
  need(value==expected,'Measured gate extent '+str(p)+' '+field)
 return r
def main(configuration,name):
 started=time.perf_counter();out=ROOT/'reports/m4-joint-startup103-root'/name;need(not out.exists(),'Fresh acceptance');out.mkdir(parents=True);passed=False;rows={};config={};physical_closure={}
 try:
  config=json.loads(pin(configuration).read_bytes());pin(__file__);pin(config['configuration_source'],config['configuration_source_sha256']);pin(config['control_specification'],config['control_specification_sha256'])
  required={'parent','preflight','original','original_constructors','native','source','paired','paired_scope','paired_review','fields','provider','provider_seal','controls','control_execution','control_snapshot','control_audit','control_link','control_dependency','control_plan','continuity','interface','game_static','provider_symbols','game_symbols','game_callbacks','calibration','source_recovery','allocation_geometry','loader','ghidra','provider_lifts','game_lifts','native_preparation','build'}
  need(set(config['gates'])==required,'Complete independent103 gates')
  for label,item in config['gates'].items():rows[label]=receipt(item)
  need(rows['parent']['connected_roots']==71,'Accepted71 parent')
  need(rows['original']['original_executed']and rows['original']['phases']==618 and rows['original']['record_bytes']==291456 and not rows['original']['per_phase_reseed'],'Six genuine continuous original103 sequences')
  native=rows['native'];need(native['native_executed']and [x['level']for x in native['levels']]==['O0','O2'],'Both actual native optimization levels')
  source=rows['source'];c=source['counts'];need(c['persistent_phases']==1236 and c['persistent103_sequences']==12 and c['literal_registration_roots']==900,'All persistent native103 source calls')
  need(c['whole_page_BEFORE']==c['whole_page_AFTER']==43260 and not source['per_phase_BEFORE_machine_seed']and not source['candidate_AFTER_machine_seed'],'Whole35-page and complete persistent source State/CPU/FX/ENV proof')
  original=rows['original_constructors'];c=original['counts'];need(c['constructor_prefixes']==450 and c['actual_MFC_source_owned_byteflows']==210 and original['actual_MFC_malloc_calls']==210 and c['original_string_byteflows']==96 and c['original_null_descriptor_constructors']==6 and c['whole_nonstack_page_checks']==15300 and original['original_heap_padding_modeled']and not original['AFTER_machine_seed'],'Actual original full constructor and owner extent')
  continuity=rows['continuity']['counts'];need(continuity['complete_State_and_projection_checks']==2472 and continuity['registry_carries']==1224 and continuity['selected_host_returns']==continuity['growth_cleanup_host_returns']==12,'Persistent State/pages/owners and actual outside return preservation')
  p=rows['paired'];c=p['counts'];need(c['paired_phases']==1236 and c['paired103_sequences']==12 and c['whole_nonstack_page_relations']==84048 and c['source_MFC_owner_relations']==420 and c['whole_original_and_native_MFC_owned_relations']==420 and c['source_MFC_one_past_end_relations']==48 and c['source_string_owner_relations']==192 and c['null_descriptor_relations']==12 and c['registration_return_order_checks']==900,'All actual original/native source-established relations')
  need(set(p['owning_IAT_projection_addresses'])=={0x5bb4fc,0x5bb52c,0x5bb530,0x5bb6dc,0x5bb670,0x5bb4bc}and p['MFC_import_relation_slots']==511 and len(p['MFC_typed_pointer_fields'])==39 and len(p['MFC_one_past_end_fields'])==4 and len(p['MFC_header_fields'])==36,'Exact declared imports, primary/endpoint pointers and saved-byte headers')
  need(not p['blanket_page_mask']and not p['original_and_native_bytes_modified']and not p['whole_game_liveness_proven'],'Bounded raw observations retained')
  scope=rows['paired_scope'];need(scope['metadata_correction_only']and not scope['comparison_algorithm_changed']and not scope['comparisons_rerun']and not scope['callback_execution_claimed']and not scope['whole_game_header_liveness_proven'],'Exact current comparison scope; no callback or whole-game liveness credit')
  provider=rows['provider'];c=provider['provider_counts'];need(c['complete103_provider_sequences']==12 and c['selected_registration_closures']==900 and c['actual_MFC_allocations']==420 and c['actual_duplicate_allocations']==192 and c['actual_source_frees']==624 and c['actual_MFC_source_frees']==420 and c['successful_actual_growth']==144 and c['actual_heap_destroys']==c['actual_post_HeapDestroy_identity_proofs']==12 and c['true_bootstrap_BEFORE_inputs']==12,'Independent actual provider ownership, genuine growth and full source cleanup')
  need(not provider['per_phase_BEFORE_machine_seed']and not provider['candidate_AFTER_machine_seed']and provider['worker_post_HeapDestroy_identity_observed'],'Source-driven persistent provider and measured final export identity')
  fields=rows['fields'];need(fields['primary_allocation_fields']==35 and fields['one_past_end_fields']==4 and fields['header_count']==36 and not fields['AFTER_machine_seed'],'Before-derived complete typed field geometry')
  need(rows['control_execution']['native_executed'],'Actual compiled functional controls executed')
  controls=rows['controls'];c=controls['metrics'];need(controls['native_executed']and not controls['source_bodies_modified']and not controls['API_response_injection']and not controls['actual_API_null_failure_claimed'],'Actual compiled immutable functional controls without invented API results')
  need(c['actual_attempts']==84 and c['ordinary_sequences']==2 and c['causal_faults']==40 and c['retry_refusals']==42 and c['rich_hardware_pairs']==84 and c['partial_transfer_faults']==6 and c['normal_MFC_source_frees']==70 and c['actual_research_probe_inputs']==14,'Exact compiled fault, partial-write, retry and actual request-input extent')
  need(c['independent_postdestroy_identity_pairs']==c['candidate_destroy_after_observed']==42 and c['candidate_destroy_after_missing']==0,'All actual pre/post/independent HeapDestroy export identities')
  snapshot=rows['control_snapshot'];need(len(snapshot['copied_sources'])==11 and not snapshot['source_semantics_changed']and not snapshot['worker_rebuilt']and not snapshot['original_control_receipts_modified'],'Immutable copies of actual compiled reviewer sources')
  link=rows['control_link'];need(link['actual_literal_COFF_links']==590 and link['declared_source_inputs']==592 and link['retained_unlinked_archives']==2 and link['metadata_correction_only']and not link['workers_rebuilt'],'295 actually linked direct COFFs plus one retained historical archive per level')
  audit=rows['control_audit'];need(set(audit['physical_workers'])=={'O0','O2'}and {(x['level'],x['case'])for x in audit['cases']}=={(level,case)for level in('O0','O2')for case in range(21)},'Both independent audit modes cover every actual control scenario')
  c=audit['counts'];need(c['actual_attempts']==84 and c['actual_refusal_causes']==40 and c['immediate_probe_inputs']==14 and c['complete_MFC_owned_replays']==130 and c['outside_hardware_pairs']==84 and c['full_machine_owner_retry_pairs']==c['destroy_identity_triplets']==42 and not audit['findings'],'Independent exact cause/argument/ownership/hardware/retry/cleanup extent')
  dependency=rows['control_dependency'];need(dependency['archive_specific_undefined_symbols_reached']==0 and not dependency['candidate_rebuild_required']and not dependency['candidate_replay_required']and not dependency['candidate_or_capture_modified'],'Omitted historical archive has no required reached symbols')
  need({(x['kind'],x['level'])for x in dependency['levels']}=={(kind,level)for kind in('normal','controls')for level in('O0','O2')}and all(x['actually_linked_declared_source_COFFs']==295 and x['declared_source_dependencies']==296 for x in dependency['levels']),'Actual ordinary/control source link extents, both modes')
  for key in('original','source','paired','paired_review','provider','provider_seal','controls','control_snapshot','control_audit','continuity'):
   need(bool(config['gates'][key].get('equal')),'Explicit measured acceptance contract '+key)
  need(config['extent']==dict(selected_roots=103,new_roots=32,original_sequences=6,original_phases=618,native_sequences=12,native_phases=1236,MFC_allocations_per_sequence=35,string_allocations_per_sequence=16,live_ordinary_owners_per_sequence=52,ordered_callbacks_per_sequence=75,observed_source_pages=35,declared_source_inputs_per_level=296,linked_literal_COFFs_per_level=295,retained_unlinked_archives_per_level=1),'Exact connected103 schedule and honest physical link extent')
  need(config['bounded_scope']==dict(new_FSQRT='Inherited accepted zero-vector constructor only',callback_execution=False,full_CRT_attach=False,full_native_MFC_attach=False,native_menu=False,native_Training=False,whole_game_alias_liveness=False,whole_original_provider_stack_equality=False,per_phase_machine_reseed=False,candidate_AFTER_machine_seed=False,host_libc_string_replacement=False,malloc_NULL_or_handler_TLS_execution=False,source_owned_header_and_pointer_relations=True),'Explicit supported frontier')
  pin(ROOT/'tools/m4-pipeline/manifests.py');physical_closure=verify_manifest(PINS)
  need(physical_closure['passed']and not physical_closure['metadata_only_cache_used'],'Final conflict-normalized complete physical verification')
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  result=dict(passed=passed,scope='Connected selected103 in actual table order; literal constructor/MFC/string/registration source and actual typed allocation lifetime',connected_roots=103 if passed else 71,new_roots=32 if passed else 0,total_inventory_roots=144,remaining_inventory_roots=41 if passed else 73,initializer_inventory_fraction=103/144 if passed else 71/144,inventory_is_project_completion_percentage=False,gates=config.get('gates',{}),extent=config.get('extent',{}),bounded_scope=config.get('bounded_scope',{}),physical_closure=physical_closure,elapsed_seconds=time.perf_counter()-started,whole_M4_complete=False,native_game_launch_complete=False,files=PINS)
  (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=PINS),indent=2)+'\n');print(json.dumps(dict(passed=passed,report=str(out/'report.json'),sha256=sha(out/'report.json'),connected_roots=result['connected_roots'],physical_inputs=len(PINS))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2])
