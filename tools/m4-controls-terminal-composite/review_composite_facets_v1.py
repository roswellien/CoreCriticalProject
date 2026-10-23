"""Pure named-domain facet derivations; no acceptance or source interpreter."""
import collections
class Blocker(ValueError):pass
def need(v,s):
 if not v:raise Blocker(s)
def typed(a,b):return type(a)is type(b)and a==b
def at(d,key):
 for k in key.split('.'):d=d[k]
 return d
PHYSICAL={'whole_intended_protected_IAT_mutation_repairs':2,'whole_diagnostic_only_delta':1,'whole_authored_public_faults':12,'whole_true_source_entry_observer':1,'actual_compiler_TLS_cells':56,'whole_linked_control_functions':7,'entry_observer_inlined_in_whole_MFC_entry':1}
def derive(gates,roles,cases,expanded,controls_sha):
 need(len(cases)==24 and{(c['level'],c['mode'])for c in cases}=={(l,m)for l in('O0','O2')for m in range(1,13)},'Exact actual24 legacy source cases')
 sums=collections.Counter()
 for c in cases:
  need(c['passed']is True and c['all_bounded_readers_closed']is True,'Closed exact legacy source case')
  need(all(type(v)is int and v>=0 for v in c['counts'].values()),'Typed actual source case counters')
  for k in ('whole_Runtime_hidden_private_retry_claim','whole_old_registry_private_retry_claim','whole_permissions_retry_claim'):need(c[k]is False,'No invented private or permission scope')
  need(c['counts']['actual_precise_denials']==c['counts']['actual_unchanged_poisoned_retries']==c['counts']['entryframe64_checked']==1 and c['counts']['whole_caller_FX512_ENV28']==2,'Whole same-case refusal/retry/frame/FP source predicates')
  sums.update(c['counts'])
 aggregate=roles['legacy24_aggregate'];need(aggregate['passed']is True and aggregate['case_count']==24 and dict(sums)==aggregate['counts'],'Reproduce entire legacy aggregate, not selected positive counters')
 p=roles['legacy_prelaunch_complete_review'];need(p['passed']is True and p['all_seven_named_fields_physically_reviewed']is True and p['current8_used_as_legacy_proof']is False and p['physical_domain_derivation_schema']=='legacy12-complete7-source-derived-v1','Actual named legacy source/compiled proof domain')
 need(set(p['counts'])==set(PHYSICAL)and all(typed(p['counts'][k],v)for k,v in PHYSICAL.items()),'All seven named physical facets from same legacy source proof')
 named=roles['named_CS24_TLS64_supplement'];need(named['passed']is True and named['all_bounded_readers_closed']is True and named['source_seed_from_AFTER']is False and typed(named['counts']['whole_borrowed_guestCS24_prefixes'],12)and typed(named['counts']['source_TLS_refusal_frame64'],2),'Whole named guestCS24 and zero-index TLS64, not nativeCS40 substitution')
 sem=roles['current16_semantic_review'];scope=roles['current8_scope_review']
 need(sem['passed']is True and scope['passed']is True and sem['all16_distinct_modes_reviewed']is True and sem['finite_GDI_owner_manual_cleanup_lifetime_predicates_reviewed']is True,'Separate actual16 finite semantic and manual owned cleanup review')
 for obj in (sem,scope):need(obj['committed_source_write_values_independently_instruction_evaluated']is False and obj['committed_write_values_from_actual_source_witness']is True and obj['whole_fault_memory_fully_source_predicted']is False,'Current16 measured write/partial-memory limits, not legacy source semantics')
 need(sem['source_callbacks_executed']is False and sem['raw_integrity_is_semantic_equivalence']is False,'Raw inventory is not source semantic execution')
 for k in ('old_registry_private_vectors_retry_claim','full_memory_permission_snapshot_claim','whole_hidden_Runtime_frames_or_permissions_claim'):need(scope['observation_limits'][k]is False,'Same current8 observation limits')
 need(expanded['passed']is True and expanded['database_reader_closed']is True and expanded['scoped_provenance_preserved']is True and expanded['metadata_only_cache_used']is False and expanded['current16_raw_rows']==10691866,'Actual whole closed expansion required')
 legacy=dict(sums);legacy.update(named['counts']);legacy['whole_export_targets_authenticated']=expanded['raw_rows']
 preparation={'control_cases':len({c['mode']for c in cases}),'old_registry_private_vectors_retry_claim':False,'full_memory_permission_snapshot_claim':False}
 need(gates['controls_preparation']['passed']is True and all(typed(at(gates['controls_preparation'],k),v)for k,v in preparation.items()),'Composite prep values reproduce same named legacy12/current8 domains')
 need(gates['controls_prelaunch']['passed']is True and all(typed(gates['controls_prelaunch']['counts'][k],p['counts'][k])for k in PHYSICAL),'Composite prelaunch preserves exact independent legacy7 physical fields')
 controls=gates['controls'];need(controls['passed']is True and controls['all_bounded_readers_closed']is True and controls['raw_export_readers_closed']is True and controls['raw_exports_all_logical_entries']is True and controls['initializer_credit']==0,'New actual composite closed only after full inventory checks')
 need(all(typed(controls['counts'][k],v)for k,v in legacy.items()),'Every composite legacy counter plus scoped total exactly reproduced')
 for k in ('whole_old_registry_private_retry_claim','whole_permissions_retry_claim'):need(controls[k]is False,'Composite limitations preserved')
 review=dict(passed=True,controls_sha256=controls_sha,controls_verification_sha256=controls_sha,all_bounded_readers_closed=True,capture_archives_opened=0,initializer_credit=0,counts=legacy)
 return dict(preparation=preparation,physical=p['counts'],legacy_source_counts=legacy,review_fields=review)
