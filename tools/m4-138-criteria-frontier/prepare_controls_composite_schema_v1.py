"""Pending finite composite mapping only. Never resolves missing receipts."""
from pathlib import Path
import collections, hashlib, json, sys
R=Path(__file__).resolve().parents[2]
PARENT='626c590fdde8e2077b4fa1fa2decdd76ef07f762466c0aad92a8fd81fe447505'
DOMAINS={
 'legacy12':dict(levels=['O0','O2'],modes=list(range(1,13)),actual_cases=24,completed_prefix_roots=13,failed_phase=13,selected_refused_root='0x5ae3e4',actual_entry_frame_bytes=64,source_TLS_refusal_modes=[11],must_preserve_all_literal_API_owner_lifecycle_retry_predicates=True),
 'current8':dict(levels=['O0','O2'],modes=list(range(1,9)),actual_cases=16,completed_prefix_roots=135,failed_phase=135,owned_fonts_before_fault=15,full_raw_files=10691866,whole_exported_retry_file_pairs=3547696),
 'whole7':dict(O0=['main','mfc_mutate','mfc_retry_snapshot','mfc_control_entry'],O2=['main','mfc_mutate','mfc_retry_snapshot'],whole_functions=7,target_joins_separate=15,O2_entry_observer_requires_actual_whole_mfc_entry_inline_proof=True),
 'compiler_TLS':dict(baseline_occurrences=35,current_legacy_prefix_occurrences=56,current8_occurrences_separate=64,source_TLS_argument_frame64_is_a_separate_runtime_proof=True),
}
PRELAUNCH={
 'counts.whole_intended_protected_IAT_mutation_repairs':('legacy12_source_inverse','Exact two protected-IAT source mutations at 0x5f498330 and0x7802e0c8; current inherited mutation repair inverse, actual respective refusal paths retained.'),
 'counts.whole_diagnostic_only_delta':('legacy12_source_inverse','Exact whole diagnostic-only inverse, retained protected repair inverses; no source-failure suppression.'),
 'counts.whole_authored_public_faults':('legacy12','Exactly twelve authored pre-resource public faults, independently strict O0/O2 actual coverage; eight post-resource modes remain separate.'),
 'counts.whole_true_source_entry_observer':('legacy12','Source CALL root entry hook plus complete actual frame64/CPU/State input for every refusal; current8 before_phase hook is not this entry observer.'),
 'counts.actual_compiler_TLS_cells':('compiler_TLS','Exact current prefix56 compiler relocation occurrences, including complete owning typed TLS cells and compiled caller provenance; do not substitute current8 64 or runtime64-byte frame.'),
 'counts.whole_linked_control_functions':('whole7','Exactly deduplicated complete seven COFF/linked function bodies, every relocation and TLS proof retained;15 target joins cannot supply this count.'),
 'counts.entry_observer_inlined_in_whole_MFC_entry':('whole7','Exact absent O2 standalone observer plus whole owning mfc_entry/source inlining proof and actual entry64 bytes; absence alone gives no credit.'),
}

def rule(gate,field):
 if gate=='controls_preparation':
  domain='legacy12'if field=='control_cases'else'closed_observation_scope'
  source='legacy12_preparation.control_cases'if field=='control_cases'else'current_preparation_scoped_review.'+field
  requirement=('Actual twelve pre-resource modes remain a separately named input contract; additionally require current8 preparation domain without treating12 as8.'if field=='control_cases'else'Explicit source/serializer/member coverage audit: false means no complete hidden Runtime private vector or memory permission snapshot claim; exported Session/Binding bytes do not imply either claim.')
 elif gate=='controls_prelaunch':
  domain,requirement=PRELAUNCH[field];source='legacy_prefix_physical_review.'+field
  if field in('counts.whole_authored_public_faults','counts.whole_true_source_entry_observer'):source+=' + legacy24_strict_actual_domain'
 elif gate in('controls','controls_review'):
  if field.startswith('counts.')and field!='counts.whole_export_targets_authenticated':
   domain='legacy12';source='legacy24_strict_aggregate.'+field
   requirement='Require exact named original-MFC literal/source/API/lifecycle/refusal/retry counter from all24 actual current-prefix cases; retain complete source/borrowed byteflow/physical API joins. Current8 expanded widget counts are additional, not replacement.'
   if gate=='controls_review':
    source='legacy24_independent_raw_review.'+field
    requirement+=' Independently authenticate the full ordinary inventory and reproduce this facet; do not infer the review from the producing verifier passed flag.'
  elif field=='counts.whole_export_targets_authenticated':
   domain='all40_full_raw';source='closed_raw_union.distinct_authenticated_raw_paths'
   requirement='Measured deduplicated full physical raw union of current16 and legacy24 sealed exports; authenticate each actual payload and complete manifest, retain both exact inventories. Not10691866 by itself, not logical-name count or metadata-only sum.'
  elif field=='execution_sha256':
   domain='all40_actual_execution_lineage';source='closed_execution_join_manifest.sha256'
   requirement='Actual closed execution lineage manifest explicitly pins current16 execution and each24 legacy run/controller/build/admission; SHA is measured from immutable whole join bytes, not an invented digest or success flag.'
  elif field=='controls_verification_sha256':
   domain='composite_verification_identity';source='controls_composite_report.sha256'
   requirement='Exact physical SHA of current complete semantic composite controls report; independent reviewer must join every named raw/source/lifecycle and inventory facet.'
  elif field in('whole_old_registry_private_retry_claim','whole_permissions_retry_claim'):
   domain='closed_observation_scope';source='current_scoped_observation_review.'+field
   requirement='Explicit false observation claim, established by serializer/source/member audit, never inferred from byte retry equality or changed to true; Runtime hidden maps/frames and permissions remain outside observed scope.'
  elif field=='initializer_credit':
   domain='no_initializer_credit';source='all_joined_reviews.initializer_credit'
   requirement='All producing and reviewing receipts explicitly have integer zero; no accepted initializer/native-game credit.'
  elif field=='capture_archives_opened':
   domain='ordinary_only_independent_review';source='composite_raw_reviewer.capture_archives_opened'
   requirement='Actual reviewer controller accesses only sealed ordinary inputs and readonly durable proof inventory; explicit integer zero, not source capture reader count.'
  elif field in('raw_exports_all_logical_entries','raw_export_readers_closed','all_bounded_readers_closed'):
   domain='all40_full_raw';source='current_fullraw.'+field+' AND legacy24_inventory_and_review.'+field
   requirement='Require actual closed terminal current16 durable SQLite proof and independently complete legacy24 inventories/reader closures. Each name set, byte hash and closure must be proven; partial progress is not true.'
  elif field=='passed':
   domain='whole_named_composite';source='all_required_semantic_physical_inventory_and_lineage_predicates'
   requirement='True only after every typed field and named-domain mandatory obligation in this schema passes; passed alone cannot bind any other criterion.'
  else:raise AssertionError((gate,field))
 else:raise AssertionError(gate)
 return dict(named_domain=domain,pending_measurement_source=source,substantive_requirement=requirement)

def main(name):
 assert name and Path(name).name==name
 out=R/'reports/m4-138-criteria-frontier'/name;assert not out.exists();out.mkdir();pins={}
 def read(p,h=None):
  p=Path(p).resolve();assert p.stat().st_size<32*1024*1024 and p.suffix.lower()not in('.mwb','.mwi','.zip')
  data=p.read_bytes();v=hashlib.sha256(data).hexdigest();assert h is None or h==v;assert pins.setdefault(str(p),v)==v;return json.loads(data)
 pp=R/'reports/m4-138-controls-review/root-criterion-delta-proposal-r6/report.json';parent=read(pp,PARENT);assert parent['passed']is True
 fp=pp.parent/'remaining-45-field-frontier.json';frontier=read(fp,parent['files'][str(fp)])
 assert len(frontier)==45 and collections.Counter(x['gate']for x in frontier)==dict(controls_preparation=3,controls_prelaunch=7,controls=18,controls_review=17)
 mapping=[]
 for x in frontier:
  assert x['status']=='unresolved'
  mapping.append(dict(gate=x['gate'],baseline_field=x['baseline_field'],baseline_expected=x['baseline_expected'],baseline_type=type(x['baseline_expected']).__name__,**rule(x['gate'],x['baseline_field']),current_measured_value=None,pending_receipt_path=None,pending_receipt_sha256=None,no_Boolean_flip=True,no_type_coercion=True,authoritative_allowance=False,status='pending_actual_terminal_measurement'))
 assert len({(x['gate'],x['baseline_field'])for x in mapping})==45
 schema=dict(scope='Unexecuted pending finite authoritative-composite design only; no bindings/allowances',domains=DOMAINS,field_mapping=mapping,mandatory_pending_inputs=[
  dict(role='legacy24_strict_aggregate',requirement='All24 passed exact O0/O2 modes1..12, whole final dependency hash/reader closure, current phase13/refusal frame64/private observable retries/source byteflows/native owner lifecycle; no partial2-case promotion'),
  dict(role='legacy24_independent_raw_review',requirement='Actual independently authenticated full ordinary inventories and retained accepted131 raw/source/owner/CPU/FX/retry predicates in each named legacy field; no producer-only duplicate success binding'),
  dict(role='current16_terminal_fullraw',requirement='Terminal PASS, exactly10691866 raw outputs and3547696 genuine retry pairs; final entire integrity rehash; closed immutable hashed SQLite and tool/Python/dependency pins; expand every measured physical row into mandatory final fresh acceptance union'),
  dict(role='current16_semantic_resource_source_equivalence',requirement='Actual current phase135/source/GDI/borrowed causal semantic/refusal cleanup proofs and full-link identities; do not confuse partial raw inventory with semantic proof'),
  dict(role='closed_execution_join_manifest',requirement='Exactly24 legacy and16 current distinct level/mode namespaces pinned to actual terminal controller/build/worker identities'),
  dict(role='complete_composite_independent_review',requirement='All old and new named physical domains reviewed; signed or authoritative ROOT admission is separate and not created by this pending schema')],
  known_bounded_support=[dict(path='reports/m4-138-criteria-frontier/root-current-controls-field-review-r1/report.json',sha256='cb1d8b5fd4eae31ba3c062289b54de5e1f2c1ef4245a1b911652a45da0f7ff10',scope='Only14 closed current8 fields and deduplicated whole7 source/link support; legacy actual aggregate pending'),dict(path='reports/m4-138-criteria-frontier/current-controls-prelaunch-domain-map-r1/report.json',sha256='05ab7ab24e748bdf9dd82859714ddb98e73cee7fb9290c48c3a575ff2d3cd72f',scope='Distinct21-field named physical domains, not acceptance')],
  observation_limits=dict(old_registry_private_vectors_retry_claim=False,full_memory_permission_snapshot_claim=False,whole_hidden_Runtime_frames_or_permissions_claim=False),
  storage_requirements=['No giant JSON materialization; bounded metadata or streaming exact required keys only','SQLite absolute ordinary unique path/key/schema/count/final-seen checks; exact entire DB SHA before and after readonly expansion','Every physical union row content SHA and actual size rehashed; no retained receipt metadata shortcut','Composite controls and review own scoped dependency edges to each producing/reviewing report; no global-union substitution for scoped lineage','Closed old and new case inventory unions measured from physical identities; preserve disjoint raw namespaces and exact controls domains'],
  worker_executed=False,archive_reader_opened=False,configuration_created=False,allowance_created=False,accepted_function_credit=0)
 q=out/'pending-45-composite-schema.json';q.write_text(json.dumps(schema,indent=2)+'\n');pins[str(q)]=hashlib.sha256(q.read_bytes()).hexdigest()
 for p in(Path(__file__).resolve(),Path(sys.executable).resolve()):pins[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 report=dict(passed=True,scope='Schema preparation only; all45 remain pending until genuine actual terminal composite measurements',criteria=45,field_domain_counts=dict(collections.Counter(x['gate']for x in mapping)),all_current_values_unresolved=True,actual_control_receipts_opened=False,worker_executed=False,archive_reader_opened=False,configuration_created=False,allowance_created=False,accepted_function_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(hashlib.sha256(q.read_bytes()).hexdigest())
if __name__=='__main__':main(sys.argv[1])
