"""Seal a bounded54-root acceptance only from independently passed receipts."""
from pathlib import Path
import hashlib,json,sys,time,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def pin(p,h=None):
 p=Path(p).resolve();key=str(p)
 if key not in PINS:PINS[key]=sha(p)
 need(h is None or PINS[key]==h,'Unchanged physical input '+key);return p
def receipt(item):
 path=pin(ROOT/item['path'],item['sha256']);r=json.loads(path.read_text(encoding='utf-8-sig'));need(r['passed']is True,'Passed receipt '+str(path))
 for p,h in r.get('files',{}).items():pin(p,h)
 pins=path.parent/'pins.json'
 if pins.exists():
  for p,h in json.loads(pin(pins).read_text(encoding='utf-8-sig'))['files'].items():pin(p,h)
 for field,expected in item.get('equal',{}).items():
  actual=r
  for key in field.split('.'):actual=actual[key]
  need(actual==expected,'Receipt contract '+field)
 return r
def main(configuration,name):
 started=time.perf_counter();out=ROOT/'reports/m4-joint-startup54-root'/name;need(not out.exists(),'Fresh acceptance');out.mkdir(parents=True);passed=False;rows={}
 try:
  config=json.loads(pin(configuration).read_bytes());need(set(config['gates'])=={'parent','original','native','source','original_constructors','native_constructors_O0','native_constructors_O2','paired','paired_review','provider','controls','control_snapshot','continuity','repair','hardware','tail'},'Complete named acceptance gates')
  pin(__file__)
  for label,item in config['gates'].items():rows[label]=receipt(item)
  need(rows['parent']['connected_roots']==28,'Accepted parent28');need(rows['original']['original_executed']and rows['original']['phases']==324 and not rows['original']['per_phase_reseed'],'Actual continuous original324 phases')
  need([x['level']for x in rows['native']['levels']]==['O0','O2'],'Both native levels');need(rows['source']['counts']['persistent_phases']==648 and rows['source']['counts']['literal_registration_roots']==312 and rows['source']['counts']['persistent54_sequences']==12,'Complete persistent source extent')
  need(rows['source']['counts']['whole_page_BEFORE']==rows['source']['counts']['whole_page_AFTER']==18792,'Whole29 source pages every phase');need(not rows['source']['per_phase_BEFORE_machine_seed']and not rows['source']['candidate_AFTER_machine_seed'],'Source carry has no candidate machine oracle')
  for label,total,fp in(('original_constructors',156,6),('native_constructors_O0',156,6),('native_constructors_O2',156,6)):
   r=rows[label];need(r['counts']['constructor_prefixes']==total and r['counts']['BEFORE_only_zero_FP_checks']==fp and r['counts']['whole_nonstack_page_checks']==total*28,'Complete literal constructor prefix '+label);need(not r['AFTER_machine_seed']and not r['AFTER_numeric_oracle_used'],'BEFORE-only new numerical model '+label)
  c=rows['continuity']['counts'];need(c['complete_State_and_projection_checks']==1296 and c['registry_carries']==636 and c['selected_host_returns']==c['growth_cleanup_host_returns']==12,'Exact carried State and measured outside returns')
  p=rows['paired'];need(p['paired_initialization_data_contract']and not p['original_and_native_bytes_modified']and not p['blanket_page_mask'],'Explicit retained paired data relation');need(p['counts']['paired_phases']==648 and p['counts']['paired54_sequences']==12 and p['counts']['whole_nonstack_page_relations']==36288 and p['counts']['registration_return_order_checks']==312,'Complete paired original extent');need(p['owning_IAT_projection_addresses']==[0x5bb4fc,0x5bb52c,0x5bb530,0x5bb6dc]and p['indeterminate_relation_address']==0x6099e8,'Exactly named IAT and single indeterminate representation byte');need(p['native_full_stack_source_proven']and not p['original_provider_scratch_stack_crossbranch_equal']and not p['whole_game_liveness_proven'],'Accurate paired proof limits')
  h=rows['hardware'];need(h['cases']==192 and h['all_IE_DE_PE_preserved']and h['all_CW_TOP_raw80_zero_preserved']and h['host_full_FX_restored'],'Independent exact zero-FSQRT hardware evidence');t=rows['tail'];need(t['tail_entry']==0x42a570 and t['source_bytes']==22 and t['physical_COFF_count']==2,'Exact shared source tail')
  need(rows['controls']['native_executed']and not rows['controls']['source_bodies_modified']and not rows['controls']['API_response_injection'],'Independent actual controls');need([x['level']for x in rows['controls']['levels']]==['O0','O2'],'Both compiled control levels')
  control=rows['controls']['metrics'];need(control['actual_attempts']==56 and control['ordinary_sequences']==2 and control['causal_faults']==26 and control['retry_refusals']==28 and control['rich_hardware_pairs']==56,'Complete independent control extent');need(control['actual_native_moves']>=2 and control['partial_transfer_faults']==2 and control['independent_postdestroy_identity_pairs']==28 and control['candidate_destroy_after_missing']==28,'Genuine relocation, partial writes and separate post-cleanup identity proof')
  provider=rows['provider'];need(provider['one_true_bootstrap_BEFORE_per_case']and not provider['per_phase_machine_reseed']and not provider['candidate_AFTER_machine_seed']and not provider['whole_pages_masked'],'Independent persistent provider machine');need(provider['all_captured_provider_AFTER_checkpoints_checked']and not provider['worker_post_HeapDestroy_identity_observed']and not provider['worker_post_HeapDestroy_identity_stability_claimed'],'Honest provider checkpoint and identity scope');pc=provider['counts'];need(pc['complete54_provider_sequences']==12 and pc['whole_State_checkpoints']==pc['whole_CPU_checkpoints']==pc['whole_FX_checkpoints']==5016 and pc['whole_checkpoint_pages']==190140,'Full provider checkpoint extent');need(pc['selected_registration_closures']==312 and pc['genuine_growth_replays']==84 and pc['successful_actual_growth']==pc['actual_source_frees']==pc['actual_heap_destroys']==12 and pc['actual_CS_deletes']==48,'Source registration, growth and actual cleanup lifecycle')
  need(config['bounded_scope']=={'new_FSQRT':'zero-vector constructor only','callback_execution':False,'full_CRT_attach':False,'native_menu':False,'native_Training':False,'whole_game_alias_liveness':False,'whole_original_provider_stack_equality':False,'main_worker_post_HeapDestroy_identity_observed':False,'independent_controls_post_HeapDestroy_identity_required':True},'Explicit bounded admission')
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Connected selected54 callback registration and accepted28 in actual relative table order; bounded source/API/numerical/representation contracts',connected_roots=54 if passed else 28,new_roots=26 if passed else 0,total_inventory_roots=144,remaining_inventory_roots=90 if passed else 116,initializer_inventory_fraction=54/144 if passed else 28/144,inventory_is_project_completion_percentage=False,gates=config['gates']if 'config'in locals()else {},bounded_scope=config.get('bounded_scope',{})if 'config'in locals()else {},elapsed_seconds=time.perf_counter()-started,whole_M4_complete=False,native_game_launch_complete=False,files=PINS)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=PINS),indent=2)+'\n');print(json.dumps(dict(passed=passed,report=str(out/'report.json'),sha256=sha(out/'report.json'),connected_roots=report['connected_roots'])))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2])
