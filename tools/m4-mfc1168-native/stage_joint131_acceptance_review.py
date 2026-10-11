"""Independent archive-free gate/edge checklist for the concrete131 config."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
out=R/'reports/m4-joint-startup131-source/acceptance-draft-review-r1';assert not out.exists();out.mkdir()
draft=R/'tools/m4-joint-startup131/acceptance.py';copied=out/'acceptance-draft.py';copied.write_bytes(draft.read_bytes());tree=ast.parse(copied.read_text());required=next(ast.literal_eval(v.value)for v in tree.body if isinstance(v,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='REQUIRED'for t in v.targets));assert len(required)==33
source=R/'reports/m4-joint-startup131-source/combined-source-provider-r2/report.json';controls=R/'reports/m4-mfc1168-native/connected-controls-verification-r5/report.json';s=json.loads(source.read_bytes());c=json.loads(controls.read_bytes());assert s['passed']and c['passed']and s['reader_closed']and s['paired_export_readers_closed']and c['all_bounded_readers_closed']and c['raw_export_readers_closed']
source_counts=dict(persistent131_sequences=12,persistent_phases=1572,whole_page_BEFORE=72312,whole_page_AFTER=72312,MFC_source_instructions=1704,MFC_source_operands=1356,MFC_typed_API_CPU_frame_relations=48,MFC_whole_region_BEFORE=144,MFC_whole_region_AFTER=144,MFC_whole_State_CPU_FX=12,MFC_owned_resource_lifecycles=12,MFC_actual_API_identity_CS40_sides=312,MFC_whole_actual_caller_FX512_ENV28=12,MFC_defined_flag_consumers=132,MFC_literal_normal_boundary_snapshots=84,MFC_computed_BEFORE_exports=12,explicit_defined_flag_consumers=33660)
control_counts=dict(actual_precise_denials=24,actual_unchanged_poisoned_retries=24,whole_retry_vectors=2508,whole_caller_FX512_ENV28=48,whole_borrowed_capacity_prefixes=60,whole_borrowed_guestCS24_prefixes=12,actual_API_identity_CS40_sides=208,actual_owned_lifecycles=12,pre_resource_refusals=12,recorded_rejected_source_write_payloads=2)
for k,v in source_counts.items():assert type(s['counts'][k])is int and s['counts'][k]==v
for k,v in control_counts.items():assert type(c['counts'][k])is int and c['counts'][k]==v
edges=[
 dict(from_gate='original_execution',to_gate='original_prelaunch',mechanism='Exact admission_review_sha256 or physical files edge; original build/preparation already checked by draft'),
 dict(from_gate='original_validation',to_gate='original_execution',mechanism='Exact execution_sha256; all six normal domains must belong to current worker'),
 dict(from_gate='source_preflight',to_gate='source_preparation',mechanism='Exact source_preparation_sha256 for current6, not earlier failed5'),
 dict(from_gate='source_provider',to_gate='source_preparation',mechanism='Physical files edge to prep6 and exact executed compare_provider_v6/mfc_source_v4/layout pins'),
 dict(from_gate='source_provider',to_gate='original_validation',mechanism='Physical files edge to current validation2 and raw original transport identity'),
 dict(from_gate='pair_policy_review',to_gate='pair_preparation',mechanism='Exact physical files edge to final finite TIB/source/typed-alias policy'),
 dict(from_gate='loaded_input_relation',to_gate='source_provider',mechanism='Exact current source receipt plus fresh whole inputs/loaded provider scope; no inherited loader receipt substitution'),
 dict(from_gate='paired',to_gate='source_provider',mechanism='Exact current source receipt/three bounded export indices and payload hashes; all raw records retain actual transport lineage'),
 dict(from_gate='paired',to_gate='original_validation',mechanism='Exact current validation2/whole original current131 schedule'),
 dict(from_gate='controls_execution',to_gate='controls_prelaunch',mechanism='Exact admission_review_sha256 for repaired actual current24 workers'),
 dict(from_gate='controls',to_gate='controls_execution',mechanism='Exact execution_sha256 fefde7... and raw exports transport/index/payload identities'),
 dict(from_gate='controls_equivalence',to_gate='controls',mechanism='Exact sealed checker5 and its unchanged strict24 predicates; observed mode11 TLS-index refusal correction explicitly reviewed'),
 dict(from_gate='controls_review',to_gate='controls',mechanism='Already required by draft; additionally full raw retries/caller/service40/backing bytes, not only exported summary counters')]
recommendations=dict(current_source_count_predicates=source_counts,current_control_count_predicates=control_counts,source_true_fields=['reader_closed','paired_export_readers_closed','source_and_provider_combined','complete_selected_source','explicit_defined_flag_consumers','complete_private_mixed_publications','complete_private_mixed_FS32Q','complete_provider_lifecycle','worker_post_HeapDestroy_identity_observed'],control_true_fields=['all_bounded_readers_closed','raw_export_readers_closed','raw_exports_all_logical_entries'],control_false_fields=['whole_Runtime_hidden_private_retry_claim','whole_old_registry_private_retry_claim','whole_permissions_retry_claim'],required_additional_edges=edges,paired_export_extents={'original':[91438,351517155],'O0':[386169,749062229],'O2':[386169,749062229]},controls_export_extents={'O0':[4345,36743981],'O2':[4345,36743981]},no_extra_canonical_reader=True)
q=out/'recommended-current-predicates.json';q.write_text(json.dumps(recommendations,indent=2)+'\n')
notes='''The draft requires all33 gates and checks selected131/current101 callback schedules, parent130 order and physical closure. Its generic equal predicates can carry the remaining lineage edges; they must be explicit in the final concrete config or its independent review. The draft itself does not yet assert the seven new literal boundary snapshots, computed BEFORE exports, finite flag-consumer extents, controls measured counts, or raw-export closure/extent. Those fields are now measured and sealed; bind them directly.

Pairing and loaded-input reviewers must pin the actual e520d40b source receipt and current original validation2. The controls reviewer must pin actual23d10d82 and check retained raw retry/lifetime/caller vectors. Mode11 reaches an earlier exact TLSindex guard; the admitted argument3 and actual source argument0 are proved by the literal read/push/current64B stack. No lazy path or rejected read payload is credited.

This is a draft checklist, not approval of a final configuration. Current accepted count stays130. Final concrete config and reviewer must preserve the entire parent physical union and freshly rehash it. No canonical archive opened for this analysis.
''';(out/'review.md').write_text(notes)
pins={str(p.resolve()):sha(p)for p in(copied,source,controls,q,out/'review.md',Path(__file__))}
q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Independent archive-free draft33 gate/edge checklist; concrete final acceptance configuration remains to be reviewed',gates_reviewed=len(required),required_gates=sorted(required),current_source_sha256=sha(source),current_controls_sha256=sha(controls),draft_origin=str(draft),draft_origin_sha256=sha(copied),final_configuration_approved=False,capture_reader_opened=False,initializer_credit=0,files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(q),gates=len(required))))
