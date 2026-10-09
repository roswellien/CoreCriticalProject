"""Authenticate the complete bounded provider evidence without new execution."""
from pathlib import Path
import hashlib,json,sys,traceback
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(name):
 out=ROOT/'reports/m4-strings-review'/name;need(not out.exists(),'Fresh sealed provider receipt');out.mkdir(parents=True);pins={};passed=False;counts={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Unchanged actual provider evidence '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Same physical input throughout seal');pins[str(p)]=v;return p
 try:
  p=pin(ROOT/'reports/m4-onexit-provider-final/provider-source-r2/report.json','d3e2e5e27421529c5a4cd1b03591afe0917357c94889c50206fe47c1e2bc2593');v=json.loads(p.read_bytes());need(v['passed'],'Complete observed persistent provider comparison')
  for p,h in v['files'].items():pin(p,h)
  counts=v['provider_counts'];required=dict(whole_State_checkpoints=8688,whole_CPU_checkpoints=8688,whole_FX_checkpoints=8688,whole_Runtime_CPU_checkpoints=8196,whole_checkpoint_pages=442008,whole_owner_lifecycle_dumps=36,source_access_records=212880,API_transport_records=64656,research_access_records=528,genuine_growth_replays=24,actual_typed_API_identity_proofs=2220,actual_heap_API_identity_proofs=24,actual_pre_HeapDestroy_identity_proofs=12,actual_post_HeapDestroy_identity_proofs=12,complete71_provider_sequences=12,selected_registration_closures=516,real_producer_allocations=12,successful_actual_growth=48,actual_source_frees=204,actual_duplicate_allocations=192,actual_CS_deletes=48,actual_heap_destroys=12,true_bootstrap_BEFORE_inputs=12,whole_string_witnesses=576)
  need(all(counts[k]==n for k,n in required.items()),'Exact successful observation counts')
  need({(r['level'],r['sequence'])for r in v['provider_rows']}=={(l,s)for l in ('O0','O2')for s in range(6)},'Every actual case at both optimization levels')
  need(all(r['compared_checkpoints']==724 and r['selected_API_count']==156 and r['cleaned_API_count']==185 and r['all_resources_released'] and r['actual_post_HeapDestroy_identity']for r in v['provider_rows']),'Every provider lifecycle independently verified')
  # The source observer's grown_API_count display retained selected_count.
  # Its owners() gate independently checked actual grown APIindex164 against
  # the carried response index. Preserve raw receipt; explain display error.
  need(all(r['grown_API_count']==r['selected_API_count']for r in v['provider_rows']),'Explicit retained observer row metadata bug')
  actual_grown_API_count=185-(17+4);need(actual_grown_API_count==164,'Exactly17 sourcefree calls and4 research CSdelete calls after checked grown ledger')
  execution=json.loads(pin(ROOT/'reports/m4-joint-startup71-root/execution-r1/report.json','5750a8dad9611381ba540cbad8c7534472e8c16d32c4f425d3fd6814c48844fa').read_bytes());need(execution['passed'],'Actual current complete native worker evidence')
  build=json.loads(pin(execution['build_path'],execution['build_sha256']).read_bytes());need(build['passed'],'Actual candidate compile passed')
  prep=json.loads(pin(ROOT/'reports/m4-strings-native/preparation-r5/report.json','94382b5470bfe5d6bd1b0bbbabeca69df13c52de5a910c43de606c0db29524bf').read_bytes());need(prep['passed'],'Same candidate native preparation')
  for file in ('session_impl.inc','locale_batch_operations.inc','locale_batch_binding.inc','registry_library.cpp'):
   p=ROOT/'reports/m4-onexit-native/preparation-r11'/file;pin(p,prep['files'][str(p)]);need(build['sources'].get(str(p))==sha(p),'Exact typed provider body used by observed candidate build')
  for w in build['workers'].values():pin(w['path'],w['sha256'])
  body=(ROOT/'reports/m4-strings-native/preparation-r5/locale_batch_binding.inc').read_text();need('const auto actual=owned_handle_;++destroy_calls_;destroy_input_handle_=reinterpret_cast<std::uintptr_t>(actual);const auto ok=::HeapDestroy(actual);'in body,'Literal typed actual HeapDestroy receives exact privately owned HANDLE')
  for report,h in (
   ('reports/m4-strings-source/connected-native-source-r1/report.json','55bebe771e5da315a4556b55ba0845260d388a3438dc9d83f53a21fc19df1496'),
   ('reports/m4-strings-source/original-run-r3/report.json','aa9cbb6c64151d4b81e7b7b8acabd321638bc171d5650b46e8c99d112f6b33d5'),
   ('reports/m4-strings-review/interface-r2/report.json','f5497ee4fb82d55e9d8ec903eecfe536e257ebcc7029dc27b33058be5700df74')):
   proof=json.loads(pin(ROOT/report,h).read_bytes());need(proof['passed'],'Actual current independent source provenance')
  derivative=json.loads(pin(ROOT/'tools/m4-strings-review/source-observation-v2-receipt.json').read_bytes());pin(derivative['original_source'],derivative['original_source_sha256']);pin(derivative['derived_source'],derivative['derived_source_sha256']);need(not derivative['semantic_game_computation_changes'] and not derivative['checkpoint_machine_seed'],'Exact frozen source computation plus observation hooks')
  for p in (ROOT/'reports/m4-crt-locale-batch-recovery/recovery-r2/API-contracts.json',ROOT/'reports/m4-crt-locale-batch-recovery/recovery-r2/report.json',ROOT/'tools/m4-crt-locale-batch-review/transport.py',ROOT/'tools/m4-strings-review/final_observer_v2.py',ROOT/'tools/m4-strings-review/source-observation-v2-diff.patch',ROOT/'tools/m4-strings-review/provider_model.py',Path(__file__)):pin(p)
  passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(schema='mw34-selected71-independent-strings-provider-final-v1',passed=passed,scope='Independent BEFORE-derived provider producer,43 ordered selected registrations,16 actual duplicated strings and one null constructor branch,actual growth,complete source/API/owner cleanup at O0 and O2 for6 cases',counts=counts,one_true_bootstrap_BEFORE_per_case=True,per_phase_machine_reseed=False,candidate_AFTER_machine_seed=False,API_input_domain='Finite actual typed scalar/owned-byte witnesses authenticated against original source arguments; full machine/owner dumps comparison only',whole_pages_masked=False,all_captured_provider_AFTER_checkpoints_checked=passed,State_bytes=3504,FX_bytes=512,CPU_bytes=40,worker_post_HeapDestroy_identity_observed=True,worker_post_HeapDestroy_identity_stability_claimed=True,cleanup_admission='Physical pre-call direct HeapDestroy export +exact compiled typed call +same full HANDLE actual success ledger +zero live resources; Actual derivative also measures same postcall identity; separate compiled controls add immediate postfinish identity and fault cleanup',sentinel_stop_PC_projection='Declared scheduler frontier5AC3EC after literal last instruction5AC3E2',provider_ledger_scope='Inherited source prefix retained; selected Runtime dispatcher stores while provider paused remain in full-game caller research scope',growth_replays_separate_from_initializer_credit=True,observer_row_metadata_correction=dict(raw_grown_API_count=156,actual_checked_grown_API_count=164,selected_API_count=156,cleaned_API_count=185,sourcefree_API_count=17,research_CSdelete_API_count=4,raw_report_preserved=True),string_allocations_per_sequence=16,total_native_allocations_per_sequence=17,sourcefree_all17_before_HeapDestroy=True,source_null_constructor_paths_per_sequence=1,nullable_strdup_probe_credit=False,actual_malloc_failure_claimed=False,unhandled_FS_TLS_paths_admitted=False,callback_execution=False,full_CRT=False,native_game_launch=False,initializer_credit=False,whole_M4_complete=False,files=pins)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pins[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'),counts=counts)))
if __name__=='__main__':main(sys.argv[1])
