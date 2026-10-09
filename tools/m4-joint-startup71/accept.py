"""Accept the additive family only from physically bound independent receipts."""
from pathlib import Path
import hashlib,json,sys,time,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def pin(p,h=None):
 p=Path(p).resolve();key=str(p)
 if key not in PINS:PINS[key]=sha(p)
 need(h is None or PINS[key]==h,'Physical receipt dependency '+key);return p
def receipt(item):
 p=pin(ROOT/item['path'],item['sha256']);r=json.loads(p.read_text(encoding='utf-8-sig'));need(r['passed']is True,'Passed '+str(p))
 for path,h in r.get('files',{}).items():pin(path,h)
 for path,h in r.get('physical_inputs',{}).items():pin(path,h)
 if (p.parent/'pins.json').exists():
  for path,h in json.loads(pin(p.parent/'pins.json').read_text(encoding='utf-8-sig'))['files'].items():pin(path,h)
 for field,expected in item.get('equal',{}).items():
  value=r
  for part in field.split('.'):value=value[part]
  need(value==expected,'Receipt extent '+str(p)+' '+field)
 return r
def main(configuration,name):
 started=time.perf_counter();out=ROOT/'reports/m4-joint-startup71-root'/name;need(not out.exists(),'Fresh acceptance');out.mkdir(parents=True);passed=False;rows={};config={}
 try:
  config=json.loads(pin(configuration).read_bytes());pin(__file__);pin(config['configuration_source'],config['configuration_source_sha256'])
  need(set(config['gates'])=={'parent','original','original_constructors','native','source','paired','paired_review','source_fields','provider','controls','control_snapshot','control_audit','control_causality','continuity','interface','provider_symbols','game_symbols','game_callbacks','calibration','source_correction','ghidra'},'Complete acceptance gates')
  for label,item in config['gates'].items():rows[label]=receipt(item)
  need(rows['parent']['connected_roots']==54,'Accepted54 parent')
  need(rows['original']['original_executed']and rows['original']['phases']==426 and not rows['original']['per_phase_reseed'],'Six continuous original71 sequences')
  need([x['level']for x in rows['native']['levels']]==['O0','O2']and rows['native']['native_executed'],'Both actual native modes')
  source=rows['source'];need(source['counts']['persistent_phases']==852 and source['counts']['persistent71_sequences']==12 and source['counts']['literal_registration_roots']==516,'Full current native source extent')
  need(source['counts']['whole_page_BEFORE']==source['counts']['whole_page_AFTER']==27264 and not source['per_phase_BEFORE_machine_seed']and not source['candidate_AFTER_machine_seed'],'All32 pages and persistent machine source proof')
  need(rows['original_constructors']['counts']['constructor_prefixes']==258 and rows['original_constructors']['counts']['original_string_byteflows']==96 and rows['original_constructors']['counts']['original_null_descriptor_constructors']==6,'Actual original literal constructors and strings')
  c=rows['continuity']['counts'];need(c['complete_State_and_projection_checks']==1704 and c['registry_carries']==840 and c['selected_host_returns']==c['growth_cleanup_host_returns']==12,'Complete persistent continuity and outside returns')
  p=rows['paired'];need(p['counts']['paired_phases']==852 and p['counts']['source_string_owner_relations']==192 and p['counts']['null_descriptor_relations']==12 and p['counts']['registration_return_order_checks']==516,'Exact original/native string and callback relations')
  need(set(p['owning_IAT_projection_addresses'])=={0x5bb4fc,0x5bb52c,0x5bb530,0x5bb6dc,0x5bb670}and len(p['source_duplicate_pointer_fields'])==16 and not p['blanket_page_mask']and not p['original_and_native_bytes_modified'],'Exactly scoped named imports and source object fields')
  provider=rows['provider'];pc=provider['counts'];need(pc['complete71_provider_sequences']==12 and pc['selected_registration_closures']==516 and pc['actual_duplicate_allocations']==192 and pc['actual_source_frees']==204 and pc['actual_heap_destroys']==pc['actual_post_HeapDestroy_identity_proofs']==12,'Source-driven allocated-string and heap lifecycle')
  need(provider['one_true_bootstrap_BEFORE_per_case']and provider['sourcefree_all17_before_HeapDestroy']and not provider['per_phase_machine_reseed']and not provider['candidate_AFTER_machine_seed']and provider['worker_post_HeapDestroy_identity_observed'],'Independent persistent source provider proof and measured final identity')
  controls=rows['controls'];need(controls['native_executed']and not controls['source_bodies_modified']and not controls['API_response_injection'],'Actual immutable compiled causal controls')
  cm=controls['metrics'];need(cm['actual_attempts']==56 and cm['ordinary_sequences']==2 and cm['causal_faults']==26 and cm['retry_refusals']==28 and cm['rich_hardware_pairs']==56 and cm['partial_transfer_faults']==2 and cm['normal_duplicate_source_frees']==32,'Exact controls and committed partial transfers')
  need(cm['independent_postdestroy_identity_pairs']==cm['candidate_destroy_after_observed']==28 and cm['candidate_destroy_after_missing']==0,'Independently observed successful cleanup identities')
  # Each gate's detailed extents are frozen in the configuration, including
  # independent source/provider/paired/control assertions. Require them explicitly.
  for key in('original','source','paired','provider','controls','continuity'):
   need(bool(config['gates'][key].get('equal')),'Explicit measured acceptance contract '+key)
  need(config['extent']==dict(selected_roots=71,new_roots=17,original_sequences=6,original_phases=426,native_sequences=12,native_phases=852,string_calls_per_sequence=16,ordered_callbacks_per_sequence=43,observed_source_pages=32),'Exact connected schedule')
  need(config['bounded_scope']==dict(new_FSQRT='Inherited accepted zero-vector constructor only',callback_execution=False,full_CRT_attach=False,native_menu=False,native_Training=False,whole_game_alias_liveness=False,whole_original_provider_stack_equality=False,per_phase_machine_reseed=False,candidate_AFTER_machine_seed=False,host_libc_string_replacement=False),'Explicit supported frontier')
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  value=dict(passed=passed,scope='Connected selected71 in actual table order; literal string/registration source and exact typed allocation lifetime',connected_roots=71 if passed else 54,new_roots=17 if passed else 0,total_inventory_roots=144,remaining_inventory_roots=73 if passed else 90,initializer_inventory_fraction=71/144 if passed else 54/144,inventory_is_project_completion_percentage=False,gates=config.get('gates',{}),extent=config.get('extent',{}),bounded_scope=config.get('bounded_scope',{}),elapsed_seconds=time.perf_counter()-started,whole_M4_complete=False,native_game_launch_complete=False,files=PINS)
  (out/'report.json').write_text(json.dumps(value,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=PINS),indent=2)+'\n');print(json.dumps(dict(passed=passed,report=str(out/'report.json'),sha256=sha(out/'report.json'),connected_roots=value['connected_roots'])))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2])
