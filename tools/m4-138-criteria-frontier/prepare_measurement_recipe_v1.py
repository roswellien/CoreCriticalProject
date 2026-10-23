"""Exact per-predicate ordinary review recipe; no reader/model/controller invocation."""
from pathlib import Path
import ast, collections, hashlib, json, sys
R=Path(__file__).resolve().parents[2]
PINS={}
def pin(p,h=None):
 p=Path(p).resolve();assert p.is_relative_to(R) and p.suffix.lower() not in('.mwb','.mwi','.zip') and p.name!='transport.json'
 assert p.stat().st_size<32*1024*1024
 with p.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
 assert h is None or h==actual;PINS[str(p)]=actual;return p
def read(p,h=None):return json.loads(pin(R/p,h).read_bytes())
TOOLS={
 'native_prelaunch':['tools/m4-tree-review/review_joint131_prelaunch_v2.py','tools/m4-tree-review/review_joint131_prelaunch.py','tools/m4-tree-review/review_mfc1168_connected_controls_prelaunch.py','tools/m4-tree-review/review_mfc1168_connected_native_prefix_v11.py','tools/m4-tree-review/review_joint138_prelaunch_v10.py','tools/m4-tree-review/review_joint138_prelaunch.py'],
 'controls_prelaunch':['tools/m4-tree-review/review_mfc1168_connected_controls_prelaunch.py','tools/m4-tree-review/review_joint138_controls_prelaunch_v4.py','tools/m4-tree-review/review_joint138_controls_prelaunch.py'],
 'original_prelaunch':['tools/m4-tree-review/review_original131_prelaunch.py','tools/m4-tree-review/review_original131_prelaunch_v4.py','tools/m4-138-validation-review/review_original_observers.py'],
 'original_preparation':['tools/m4-startup131-original/prepare_v4.py'],
 'source_preparation':['tools/m4-joint-startup131/prepare_source_v6.py','tools/m4-tree-review/review_joint131_source_preflight_v4.py','tools/m4-138-controls-review/seal_source6_closure.py'],
 'pair_policy_review':['tools/m4-tree-review/review_paired131_preparation_v2.py','tools/m4-startup138-paired/root_seal_current_policy.py','tools/m4-startup138-paired/root_seal_current_policy_v12.py'],
 'pair_preparation':['tools/m4-startup131-paired/derive_v2.py'],
 'controls_preparation':['tools/m4-mfc1168-native/connected_controls.inc'],
 'controls_execution':['tools/m4-joint-startup138/run_context_controls.py'],
 'controls_equivalence':['tools/m4-tree-review/review_mfc131_control_equivalence_v3.py','tools/m4-138-controls-review/equivalence_v2.py']}
def action(g,f):
 k=f.removeprefix('counts.')
 if g in ('native_prelaunch','controls_prelaunch'):
  actions={
   'worker_launched':'Inspect exact materialized current prelaunch main: no run controller/subprocess/native entry is invoked; preserve Boolean false, rather than coercing actual_worker_launches integer0.',
   'source_AFTER_seed':'Join baseline source/bridge seed guards to current prelaunch exact whole source inversion and current source6 false candidate_AFTER_machine_seed. Limit Boolean to source bootstrap/bridge input, not every current memory allocation.',
   'whole_new_manager_CRT_TIB_endpoint_observations_declared':'Inspect current native_main/component serializer and current original/input contracts: enumerate all five borrowed owners, three exact CRT cells and both true TIB pieces with BEFORE/AFTER extent and owner; no declaration inferred from a passed report.',
   'whole_genuine_borrowed_BEFORE_relations':'Repeat baseline five-role genuine BEFORE owner/HeapSize/full-byte relation against current original3 six MFC source derivations and current native prep4 typed inputs; compare every role, not six-case count.',
   'exact_consumed_pointer_projections':'Repeat baseline exact six source-consumed pointer-cell projections using current input-domain and MFC source access indices; unconsumed differing cells retain whole carry, never generalized opaque projection.',
   'finite_three_CRT_cell_source_relations':'Repeat baseline three exact physical CRT cell/source-PC/value-origin checks using current named provider imports and carried source6 original/native input domain; preserve exactly that finite subdomain.',
   'owning_raw_IAT_relations':'Repeat baseline seven actual Mech3/MFC/CRT owning import cells, raw ordinals/name bytes, source reads and physical exports against current imports; do not use all current linked-target count.',
   'whole_unchanged_positive_component_files':'Enumerate baseline77 component relative files and current inherited source relation path mapping; whole-byte compare with ONLY explicit generated path relocation substitution. Any changed body requires exact inverse review, not count-only adjustment.',
   'whole_current_typed_bridge_functions':'Partition current1510/1547 physical-links by exact baseline14 bridge symbol/level identities, then replay baseline whole COFF function and target/TLS checks in current linked executable; finite changed adapter bodies require reviewed source inverses.',
   'whole_typed_bridge_relocation_targets':'For the exact baseline bridge partition, replay every typed relocation target/name/physical-source proof from current COFF and whole linked function;3220/3279 global targets cannot stand in for539 bridge-domain relocations.',
   'actual_missing_thunk_source_CALL_targets':'Extract current finite thunk/bridge source-target map, replay baseline physical CALL source bytes and exact127 missing-target provenance with all owning symbols. New widget targets form separate finite domain.',
   'whole_linked_literal_functions':'Partition current physical-links by the baseline26 literal symbol+level+object identities from whole-link-observations.json and replay original exact full raw function/TLS/relocation matching. Global1510/1547 totals are unrelated.',
   'whole_linked_changed_adapter_functions':'Partition exact baseline12 changed adapter symbol/level identities; replay current whole-function equality and each reviewed source inversion. Whole current function count cannot replace this partition.',
   'actual_compiler_TLS_cells':'Replay baseline TLS relocation sites over exact baseline functions against current TLS directory, including reviewed compiler thread epoch exceptional four-byte initial value; count that named retained partition separately from89/103 all initialized relations.',
   'whole_hardware_caller_boundaries':'Replay exact two baseline full ASM invoke/caller functions against current compiled objects/executable, source unwind, input/output FX512+ENV28 boundaries. Current6/8 unwind relations do not measure two caller boundaries.',
   'whole_current_main_growth_functions':'Select exact O0/O2 main and growth_and_cleanup symbols and repeat original whole bytes/relocations/TLS source-to-linked proof; new Context additions need exact reviewed inverse to retain chronology, not all1510 funcs.',
   'current_compiler_dependency_paths':'Parse each current .ninja_deps with original dependency parser and preserve actual complete per-target consumed paths plus physical hashes.1132/1134 header paths are not16080/16118 occurrence domain; explicitly discriminate unique paths vs occurrences.',
   'whole_intended_protected_IAT_mutation_repairs':'Retain exact two historical protected IAT physical address/VirtualProtect owner/rights restoration controls in retained old12-control artifact domain. Current widget IAT mutations are a different scope; require prefix transfer proof before assigning current worker credit.',
   'whole_diagnostic_only_delta':'Inverse-review exact one historical diagnostic-only body delta in oldcontrols versus oldpositive source; current new controls main adds a distinct finite8-mode delta. Preserve both source relations as separate domains.',
   'whole_authored_public_faults':'Keep historical12 distinct finite fault causes; current8 modes do not satisfy same12. Prove current source prefix/adapter transfer of the old12 whole source causes or require narrow old14-prefix current-context fault execution.',
   'whole_true_source_entry_observer':'Preserve exact historical MFC source-entry observer serializer/control target/time-before-API relation and join its current linked MFC entry; current widget snapshot is not this observer.',
   'whole_linked_control_functions':'Preserve exact seven historical control functions O0/O2 and the inlined observer case from old12 worker. Join unchanged current source/linked dependencies if retained scope is admitted; do not count new widget controls functions.',
   'entry_observer_inlined_in_whole_MFC_entry':'Replay exact O2 historical mfc_control_entry inlining into whole MFC entry and its observable TLS64 argument frame. Current widget entry is not an equivalent function.'}
  assert k in actions,(g,k);return actions[k]
 if g=='original_prelaunch':
  return {
   'whole_inherited_pack_pages':'Parse both sparse packs from baseline/current sealed ordinary preparation metadata; enumerate baseline132 exact address/owner/fullpage bytes as retained subset of current161. Added27 family pages and exact overlays require separately discriminated origins.',
   'exact_literal_pack_delta_bytes':'Replay original baseline six physical pack overlay bytes and new current overlay regions as disjoint named source-owned sets. Current1594 RX padding overlay bytes are not the same six-byte domain.',
   'whole_unchanged_accepted_observers':'Whole-byte compare exact baseline nine accepted observer files with mapped current retained11 accepted observer identities; retain each full-body identity and explicitly review extra widgets separately.',
   'whole_chronological_MFC_ASM_relations':'Repeat exact three baseline MFC ASM source hook/frame/order checks on current retained MFC ASM and current original3 source proof; current93 FS hook spans do not measure these three relations.',
   'whole_current_format_targets':'Replay baseline six formatter target symbols into current compiled-observers.json/objects/linker map; source-entry target bytes and retained exact formatter hooks remain substantive.',
   'actual_compiler_input_files':'Parse current observer compiler logs/dependency files using baseline consumed-input predicate; current266 actual consumed inputs is a plausible finite domain264→266 only after enumerating exact old plus two inputs and inverse source attribution.'}[k]
 if g=='original_preparation':
  return {'ordinary_record_pages':'Enumerate exact43 baseline ordinary record pages from current prep8 pages inventory;69 combined source pages includes extra modules and cannot replace this subdomain.',
   'MFC_domain_extra_regions':'Enumerate exact12 baseline MFC extra owners/addresses/regions in current genuine source contracts and pack; distinguish added widget/CRT family pages.',
   'true_TIB8192_from_reviewed_current_ASM':'Inspect current genuine observer ASM true FS-base discovery and whole8192-byte TIB serializer/bounds; join current original compiled observer identity. Retained source pure TIB projection is a different check.',
   'constructor_prerequisites_observation_only':'Inspect current0x5f2000 prerequisite observation binding and selected138 excludes three constructor roots; inspect no constructor root entry executes to supply initializer credit. Persistent141 later is a different gate.'}[k]
 if g=='source_preparation':return 'Retain exact historical preparation6 '+k+' predicate in adjacent-TIB repair scope; source138 closure pins that receipt and all its files. Current prep11 is a separate checkpoint-name derivative. Build composite source-preparation proof that binds current final consumer and exact inherited repair inverse; do not broaden nonTIB false to claim all138 extensions leave nonTIB unchanged.'
 if g=='pair_policy_review':
  if k=='physically_verified_preparation_files':return 'Keep exact historical ten preparation files in its old preparation2 inverse scope, then enumerate every ordinary current prep15 file as separate whole physical union. Do not replace10 with a guessed files-map length; pin complete current inverse hunks/comparer/helper/policy and all53 code changes.'
  if k in ('paired_executed','current_configuration_reviewed','capture_archives_opened'):return 'Inspect current policy-only seal/controller and all materialized preflight imports; prove no paired main/config approval/canonical reader occurs in THAT receipt scope. Preserve false/false/integer0 types. Actual paired5 execution and configuration8 approval stay separately true in their own gates.'
  return 'Retain exact inherited finite MFC relation helper Boolean scope: '+k+'. Inspect identical4ab2c11a helper whole body and current ROOT policy code; prove no additional original intermediate API-CS24/native hardware observation/cold alias domain is credited. Current own-input and carried endpoint proofs are separate.'
 if g=='pair_preparation':return 'Current prep15 retains exact helper4ab2c11a and source-generation-only inverse contract. Add typed measured '+k+' from generator code/dependency closure in preparation scope, not from actual paired5 execution; pin53 inverse hunks and current7d3aa comparer.'
 if g=='controls_preparation':return 'Retain historical12 pre-resource control domain and literal old registry/private-permission observation exclusions. Current prep4 has8 post-resource modes; exact field '+k+' must be scoped to historical retained proof plus separately current8, never a Boolean flip or12→8 generic substitution.'
 if g=='controls_execution':return 'Inspect current execution controller ordinary-only process/stream ownership: prove all16 worker processes terminal and every bounded diagnostic/output stream is closed. all_workers_terminal is not automatically all_bounded_readers_closed; enumerate actual reader objects and try/finally paths.'
 if g=='controls_equivalence':return 'Join exact historical identical14-root prefix/newMFCphase13 into current138 selected-order prefix and whole component identities. Current equivalence1 AST/header claim and current-link1490 function proof help but do not directly measure '+k+'; prove old14 prefix includes same slot/entry/order and exact new MFC root at13, plus old control bootstrap/function transfer.'
 raise AssertionError((g,f))
def main(name):
 out=R/'reports/m4-138-criteria-frontier'/name;assert not out.exists()
 previous=read('reports/m4-138-criteria-frontier/bounded-frontier-r3/report.json','7f420e06799077145b5937327945198d6c217c442f12642b06997c56c4266e1a')
 rows=read('reports/m4-138-criteria-frontier/bounded-frontier-r3/predicate-recommendations.json',previous['files'][str((R/'reports/m4-138-criteria-frontier/bounded-frontier-r3/predicate-recommendations.json').resolve())])
 selected=[x for x in rows if x['audit_status']=='missing_same_domain_measurement'];assert len(selected)==69
 baseline=read('reports/m4-joint-startup131-root/configuration-r1/configuration.json','ba2fbf12ddedbac6c57ffb1ef6f14ade3712319a368671585daddd5f011c5ef7')
 for g in {x['gate'] for x in selected}:
  b=read(baseline['gates'][g]['path'],baseline['gates'][g]['sha256'])
  # Pin complete baseline authored reviewer/adapter source closure, never its raw payloads.
  for p,h in b.get('files',{}).items():
   if Path(p).suffix.lower()=='.py' and Path(p).is_relative_to(R):ast.parse(pin(p,h).read_text())
 recipes=[]
 for x in selected:
  g,f=x['gate'],x['baseline_field'];sources=[]
  for p in TOOLS[g]:
   q=R/p
   if q.exists():
    text=pin(q).read_text();sources.append(dict(path=str(q),sha256=PINS[str(q)],matching_baseline_lines=[n for n,line in enumerate(text.splitlines(),1) if f.removeprefix('counts.') in line]))
  recipes.append(dict(gate=g,baseline_field=f,baseline_expected=x['baseline_expected'],baseline_type=type(x['baseline_expected']).__name__,baseline_receipt=baseline['gates'][g],current_action=action(g,f),source_inputs=sources,primary_method='bounded ordinary source/input/whole-linked review',new_source_run_required=False,execution_frontier='Historical pre-resource control transfer must first be proved with complete current14-root prefix, adapters, provider/ABI/input ownership and exact fault cause. If not provable, ROOT must admit narrow current14-prefix12 controls; no current16 post-resource substitution.' if g in('controls_preparation','controls_prelaunch','controls_equivalence') else None,predicate_relaxation_permitted=False))
 closure=read('reports/m4-tree-review/source138-closure-r1/report.json')
 old_controls=read('reports/m4-tree-review/mfc131-controls-review-r2/report.json','136c015cf1d3d332e84752232dba7b83b56b82b657892465575a713ef9e39748')
 retained={p:closure['files'].get(p)==h for p,h in old_controls['files'].items()}
 out.mkdir(parents=True)
 q=out/'measurement-recipes.json';q.write_text(json.dumps(recipes,indent=2)+'\n');pin(q)
 pin(__file__)
 report=dict(passed=True,scope='Exact69-predicate preparation-only recipe; baseline complete authored source retained physically, no code/body count relaxation or resource/capture reader opened',missing_measurements=69,gate_counts=dict(collections.Counter(x['gate'] for x in recipes)),all69_named_actions=True,no_new_successful_source_run_needed_for_static_schema_reconstruction=True,control_transfer_proof_pending=True,current_source_closure_retains_old_controls_review_receipt=False,legacy_controls_dependency_overlap=sum(retained.values()),legacy_controls_dependency_total=len(retained),old_controls_accepted_parent_retention_is_not_current_execution=True,materialization_recipe='Before adaptation, use each pinned baseline reviewer wrapper with __name__=definition_only; retain its COMPLETE materialized predicates. Invert only explicit current path/receipt identities and enumerate old/new finite physical partitions. Never invoke main during materialization. ROOT independently reviews exact inverse changes before ordinary physical checker runs.',archive_reader_opened=False,source_machine_executed=False,worker_launched=False,fullraw_report_opened=False,configuration_created=False,allowance_created=False,acceptance_executed=False,initializer_credit=0,files=PINS)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest(),counts=report['gate_counts'])))
if __name__=='__main__':main(sys.argv[1])
