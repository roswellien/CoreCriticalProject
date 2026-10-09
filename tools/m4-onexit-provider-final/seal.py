"""Authenticate the complete bounded provider evidence without new execution."""
from pathlib import Path
import hashlib,json,sys,traceback
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(name):
 out=ROOT/'reports/m4-onexit-provider-final'/name;need(not out.exists(),'Fresh sealed provider receipt');out.mkdir(parents=True);pins={};passed=False;counts={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Unchanged actual provider evidence '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Same physical input throughout seal');pins[str(p)]=v;return p
 try:
  p=pin(ROOT/'reports/m4-onexit-provider-final/validation-r9/report.json','58ee0cf3cf10388a965d264f644c87330f4e822dbecb51c23b71e4ef3bc34553');v=json.loads(p.read_bytes());need(v['passed'],'Complete observed persistent provider comparison')
  for p,h in v['files'].items():pin(p,h)
  counts=v['provider_counts'];required=dict(whole_State_checkpoints=5016,whole_CPU_checkpoints=5016,whole_FX_checkpoints=5016,whole_Runtime_CPU_checkpoints=4524,whole_checkpoint_pages=190140,whole_owner_lifecycle_dumps=36,source_access_records=107580,API_transport_records=36960,research_access_records=264,genuine_growth_replays=84,actual_typed_API_identity_proofs=1332,actual_heap_API_identity_proofs=24,actual_pre_HeapDestroy_identity_proofs=12,post_HeapDestroy_identity_unobserved=12,complete54_provider_sequences=12,selected_registration_closures=312,real_producer_allocations=12,successful_actual_growth=12,actual_source_frees=12,actual_CS_deletes=48,actual_heap_destroys=12,true_bootstrap_BEFORE_inputs=12)
  need(all(counts[k]==n for k,n in required.items()),'Exact successful observation counts')
  need({(r['level'],r['sequence'])for r in v['provider_rows']}=={(l,s)for l in ('O0','O2')for s in range(6)},'Every actual case at both optimization levels')
  need(all(r['compared_checkpoints']==418 and r['selected_API_count']==83 and r['grown_API_count']==106 and r['cleaned_API_count']==111 and r['all_resources_released'] and r['post_HeapDestroy_identity_unobserved']for r in v['provider_rows']),'Every provider lifecycle independently verified')
  execution=json.loads(pin(ROOT/'reports/m4-joint-startup54-root/execution-r6/report.json','796ed2ea41261b9949b6b1a12d963ce53d4d83bf4b0158c7f15559e3f4a9bafb').read_bytes());need(execution['passed'],'Actual current complete native worker evidence')
  build=json.loads(pin(execution['build_path'],execution['build_sha256']).read_bytes());need(build['passed'],'Actual candidate compile passed')
  prep=json.loads(pin(ROOT/'reports/m4-onexit-native/preparation-r11/report.json','ffbf18afdcf9756f2e5cee96edccb0e3ecd6ae614c568353e0e6dec4ee5797d4').read_bytes());need(prep['passed'],'Same candidate native preparation')
  for file in ('session_impl.inc','locale_batch_operations.inc','locale_batch_binding.inc','registry_library.cpp'):
   p=ROOT/'reports/m4-onexit-native/preparation-r11'/file;pin(p,prep['files'][str(p)]);need(build['sources'].get(str(p))==sha(p),'Exact typed provider body used by observed candidate build')
  for w in build['workers'].values():pin(w['path'],w['sha256'])
  body=(ROOT/'reports/m4-onexit-native/preparation-r11/locale_batch_binding.inc').read_text();need('const auto actual=owned_handle_;++destroy_calls_;destroy_input_handle_=reinterpret_cast<std::uintptr_t>(actual);const auto ok=::HeapDestroy(actual);'in body,'Literal typed actual HeapDestroy receives exact privately owned HANDLE')
  for report,h in (
   ('reports/m4-onexit-source/connected-native-source-r2/report.json','c2f439bb528cdd8b660908909b835fed638bfc0190ba55cfd1cc89ee7e997188'),
   ('reports/m4-onexit-source/original-run-r5/report.json','dbf50bb8d64645565b7b1f7ff6a622eae4257cb8fae5a188a06cb329b907143a'),
   ('reports/m4-onexit-source/original-game-source-r4/report.json','0c346bbc0c5fd2d33a39eb0db6f68a78ce057fe28dd6f53c14fca5bf036a9597')):
   proof=json.loads(pin(ROOT/report,h).read_bytes());need(proof['passed'],'Actual current independent source provenance')
  derivative=json.loads(pin(ROOT/'tools/m4-onexit-provider-final/source-observation-receipt.json').read_bytes());pin(derivative['original_source'],derivative['original_source_sha256']);pin(derivative['derived_source'],derivative['derived_source_sha256']);need(not derivative['semantic_game_computation_changes'] and not derivative['checkpoint_machine_seed'],'Exact frozen source computation plus observation hooks')
  for p in (ROOT/'reports/m4-crt-locale-batch-recovery/recovery-r2/API-contracts.json',ROOT/'reports/m4-crt-locale-batch-recovery/recovery-r2/report.json',ROOT/'tools/m4-crt-locale-batch-review/transport.py',ROOT/'tools/m4-onexit-provider-final/README.md',Path(__file__)):pin(p)
  passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(schema='mw34-selected54-independent-provider-final-v1',passed=passed,scope='Independent BEFORE-derived provider producer,26 ordered selected registrations,actual growth,complete source/API/owner cleanup at O0 and O2 for6 cases',counts=counts,one_true_bootstrap_BEFORE_per_case=True,per_phase_machine_reseed=False,candidate_AFTER_machine_seed=False,API_input_domain='Finite actual typed scalar/owned-byte witnesses authenticated against original source arguments; full machine/owner dumps comparison only',whole_pages_masked=False,all_captured_provider_AFTER_checkpoints_checked=passed,State_bytes=3504,FX_bytes=512,CPU_bytes=40,worker_post_HeapDestroy_identity_observed=False,worker_post_HeapDestroy_identity_stability_claimed=False,cleanup_admission='Physical pre-call direct HeapDestroy export +exact compiled typed call +same full HANDLE actual success ledger +zero live resources; separate compiled controls required for immediate post-finish identity',sentinel_stop_PC_projection='Declared scheduler frontier5AC3EC after literal last instruction5AC3E2',provider_ledger_scope='Inherited source prefix retained; selected Runtime dispatcher stores while provider paused remain in full-game caller research scope',growth_replays_separate_from_initializer_credit=True,callback_execution=False,full_CRT=False,native_game_launch=False,initializer_credit=False,whole_M4_complete=False,files=pins)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pins[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'),counts=counts)))
if __name__=='__main__':main(sys.argv[1])
