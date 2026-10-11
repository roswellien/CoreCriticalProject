"""Accept complete selected125 only after measured gates and physical union rehash.

The accepted124 receipt supplies inherited recovery and finite seam proofs. All
125 original/native phases, resource lifetimes and cross-branch relations are
fresh gates. Controls bind the final library through exact COFF equivalence,
with only the four-byte TimeDateStamp permitted to differ.
"""
from pathlib import Path
import hashlib, json, sys, time, traceback
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
from manifests import normalized, digest, unique_object, verify_manifest
PINS = {}
REQUIRED = {'parent', 'game_recovery', 'game_lifts', 'game_callbacks', 'game_static', 'game_trace', 'owner_source', 'original_preparation', 'original_build', 'original_run', 'original_validation', 'original_review', 'original_source', 'tree_original_source', 'native_preparation', 'preparation', 'build', 'abi', 'link', 'resource', 'build_review', 'iteration', 'lineage', 'native', 'source', 'source_review', 'source_closure', 'provider', 'provider_review', 'paired', 'paired_review', 'pair_source', 'pair_policy', 'fixture_build', 'fixture_execution', 'fixture_source', 'controls_build', 'controls_execution', 'controls', 'controls_review', 'controls_equivalence', 'loaded_input_relation'}
EXTENT = dict(selected_roots=125, new_roots=1, original_sequences=6, original_phases=750, native_sequences=12, native_phases=1500, ordered_callbacks_per_sequence=97, observed_source_pages=43, MFC_allocations_per_sequence=65, string_allocations_per_sequence=19, live_ordinary_owners_per_sequence=85, live_critical_sections_per_sequence=5, new_requested24_allocations_per_sequence=7, new_actual_capacity32_allocations_per_sequence=7, tree_owned_accesses_per_sequence=172, tree_primary_publications_per_sequence=7, tree_Lockit_pairs_per_sequence=26, normal_game_FS_records_per_sequence=26, linked_literal_COFFs_per_level=371, compiled_objects_per_level=27, capture_objects_per_level=2, actual_linked_inputs_per_level=400)
BOUNDED = {'callback_execution', 'full_CRT_attach', 'full_native_MFC_attach', 'native_MSVCP_DllMain', 'MSVCP_lazy_or_Sleep_path', 'native_menu', 'native_Training', 'whole_game_alias_liveness', 'handler_execution', 'exception_dispatch', 'allocation_NULL_paths', 'whole_original_provider_stack_equality', 'whole_original_Windows_TIB_page_claimed', 'general_virtual_dispatch', 'nonzero_59FF80_pointee_path', 'naked_throwing_Session_plus_caller_catch_ENV_metadata_guaranteed'}
SOURCE_COUNTS = dict(persistent125_sequences=12, persistent_phases=1500, whole_page_BEFORE=64500, whole_page_AFTER=64500, literal_registration_roots=1164, literal_Lockit_CALL_RET_pairs=408, actual_native_CS40_source_API_relations=408, native_FS_source_accesses=936, actual_native12B_source_relations=624, actual_generation_occurrence_joins=84, whole_owned_access_relations=2064, whole_publication_relations=84, whole12B_FS_relations=168, whole_native_scratch_contexts=312, whole_native_tree_owner_backings=84, actual_native_indirect_full_State_CPU_FX_boundary_joins=144, literal_indirect_CALL_RET_derivations=72, actual_native_indirect_CALL_RET_joins=72)
PROVIDER_COUNTS = dict(complete125_provider_sequences=12, selected_registration_closures=1164, actual_MFC_allocations=780, actual_duplicate_allocations=228, actual_source_frees=1020, actual_MFC_source_frees=780, actual_CS_deletes=60, actual_heap_destroys=12)
PAIRED_COUNTS = dict(paired_phases=1500, paired125_sequences=12, whole_nonstack_page_relations=123000, separate_whole_loader_page_input_relations=3000, whole42_nonstack_page_endpoint_relations=126000, Lockit_paired_complete12B_normal_FS_relations=96, Lockit_paired_bounded_API_semantic_relations=96, Lockit_actual_owner_publication_activations=96, Lockit_branch_field_source_derivations=216, Lockit_whole_native_owned_carries=288, tree_paired_owned_accesses=2064, tree_whole_branch_owner_backing_pairs=84, tree_saved_local_byte_relations=24, whole_exact_loaded_input_endpoint_relations=3000)

def need(value, message):
    if not value:
        raise ValueError(message)

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def register(path, identity):
    key = normalized(str(Path(path).resolve())); identity = digest(identity)
    need(key not in PINS or PINS[key] == identity, 'Conflicting physical dependency ' + key)
    PINS[key] = identity

def read(path, identity=None):
    path = Path(path).resolve(); actual = sha(path)
    need(identity is None or identity == actual, 'Exact physical report ' + str(path))
    register(path, actual)
    return json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=unique_object)

def absorb(report):
    for field in ('files', 'physical_inputs', 'physical_dependencies', 'generated_sources', 'sources', 'tools', 'artifacts'):
        for path, identity in report.get(field, {}).items():
            register(path, identity)

def has(report, path, identity):
    key = normalized(str(Path(path).resolve()))
    return any(normalized(str(Path(p).resolve())) == key and h == identity for field in ('files', 'physical_inputs', 'physical_dependencies', 'generated_sources', 'sources', 'tools', 'artifacts') for p, h in report.get(field, {}).items())

def extent_value(report, field):
    for key in field.split('.'):
        report = report[int(key)] if isinstance(report, list) else report[key]
    return report

def exact_counts(actual, expected, label):
    for field, value in expected.items():
        need(type(actual[field]) is type(value) and actual[field] == value, 'Complete ' + label + ' count ' + field)

def main(configuration, name, review_path, review_sha256):
    started = time.perf_counter(); out = ROOT / 'reports/m4-joint-startup125-root' / name
    need(not out.exists(), 'Fresh acceptance output'); out.mkdir(parents=True)
    passed = False; config = {}; rows = {}; closure = {}; predicates = 0
    try:
        config = read(configuration); register(__file__, sha(__file__))
        register(ROOT / 'tools/m4-pipeline/manifests.py', sha(ROOT / 'tools/m4-pipeline/manifests.py'))
        register(config['configuration_source'], config['configuration_source_sha256'])
        register(config['review_specification'], config['review_specification_sha256'])
        need(set(config['gates']) == REQUIRED and config['extent'] == EXTENT, 'Complete exact125 gate set and extent')
        need(set(config['bounded_scope']) == BOUNDED and all(v is False for v in config['bounded_scope'].values()), 'Explicit supported frontier')
        review = read(review_path, review_sha256); absorb(review)
        need(review['passed'] is True and review['gates_reviewed'] == len(REQUIRED), 'Independent complete configuration review')
        need(has(review, configuration, sha(configuration)) and has(review, __file__, sha(__file__)), 'Exact reviewed configuration and acceptance source')
        for label, item in config['gates'].items():
            path = ROOT / item['path']; report = read(path, item['sha256'])
            need(report['passed'] is True, 'Passed gate ' + label); absorb(report)
            manifest = path.parent / 'pins.json'
            if manifest.exists():
                pins = read(manifest); need(set(pins) == {'files'}, 'Exact sibling manifest ' + label); absorb(pins)
            need(len(item['equal']) >= 2, 'Substantial measured gate extent ' + label)
            for field, expected in item['equal'].items():
                actual = extent_value(report, field)
                need(type(actual) is type(expected) and actual == expected, 'Measured typed extent ' + label + ':' + field); predicates += 1
            rows[label] = report
        def edge(label, target):
            item = config['gates'][target]
            need(has(rows[label], ROOT / item['path'], item['sha256']), 'Exact physical evidence edge ' + label + ' -> ' + target)
        for label in ('abi', 'link', 'resource'): edge(label, 'build')
        for label in ('native_preparation', 'preparation', 'build'): edge('lineage', label)
        for label in ('source', 'provider', 'paired'): edge(label, 'native')
        edge('paired', 'loaded_input_relation')
        for label, target in [('source_review', 'source'), ('source_closure', 'source'), ('source_closure', 'provider'), ('provider_review', 'provider'), ('paired_review', 'paired'), ('controls_review', 'controls'), ('controls', 'controls_execution'), ('controls_equivalence', 'controls_build'), ('controls_equivalence', 'controls'), ('controls_equivalence', 'build'), ('original_source', 'original_validation'), ('original_review', 'original_validation'), ('build_review', 'abi'), ('build_review', 'link'), ('build_review', 'resource'), ('build_review', 'fixture_source')]: edge(label, target)
        need(rows['parent']['connected_roots'] == 124 and rows['parent']['remaining_inventory_roots'] == 20 and not rows['parent']['whole_M4_complete'], 'Complete accepted124 parent')
        need(rows['native']['native_executed'] is True and [r['level'] for r in rows['native']['levels']] == ['O0', 'O2'], 'Both actual final native levels')
        need(rows['native']['build_sha256'] == config['gates']['build']['sha256'], 'Execution binds exact build')
        need(rows['build']['preparation_sha256'] == config['gates']['preparation']['sha256'], 'Build binds exact preparation')
        need(rows['preparation']['native_preparation_sha256'] == config['gates']['native_preparation']['sha256'] and rows['preparation']['parent_acceptance_sha256'] == config['gates']['parent']['sha256'], 'Actual native candidate and accepted parent')
        for label in ('original_run', 'original_validation'): need(rows[label]['build_sha256'] == config['gates']['original_build']['sha256'], 'Exact authentic original worker ' + label)
        need(rows['original_build']['preparation_sha256'] == config['gates']['original_preparation']['sha256'], 'Exact original preparation')
        need(rows['controls_execution']['build_sha256'] == config['gates']['controls_build']['sha256'], 'Exact actual controls worker')
        need(rows['fixture_execution']['build_sha256'] == config['gates']['fixture_build']['sha256'], 'Exact actual registered fixture worker')
        for level in rows['controls_equivalence']['levels']:
            need(level['only_permitted_difference'] == [4, 8] and all(4 <= i < 8 for i in level['actual_differing_offsets']) and level['all_non_timestamp_bytes_equal'] and level['code_data_relocation_symbol_bytes_equal'] and level['linked_literal_inputs'] == 371 and level['actual_compiler_dependencies'] == 481, 'Whole exact controls/final native library and dependency equivalence')
        for label in ('source', 'provider'): need(rows[label]['per_phase_BEFORE_machine_seed'] is False and rows[label]['candidate_AFTER_machine_seed'] is False, 'Persistent source, single bootstrap ' + label)
        exact_counts(rows['source']['counts'], SOURCE_COUNTS, 'source125')
        exact_counts(rows['provider']['provider_counts'], PROVIDER_COUNTS, 'provider125')
        sequences = rows['provider']['provider_sequences']; c = rows['provider']['provider_counts']
        need(len(sequences) == 12 and {(r['level'], r['sequence']) for r in sequences} == {(level, seq) for level in ('O0', 'O2') for seq in range(6)}, 'Every actual current provider sequence')
        need(c['whole_State_checkpoints'] == c['whole_CPU_checkpoints'] == c['whole_FX_checkpoints'] == sum(r['compared_checkpoints'] for r in sequences), 'Complete provider machine checkpoints')
        for row in sequences:
            capacity = row['first_replay_msize_capacity']
            need(row['all_resources_released'] and row['actual_post_HeapDestroy_identity'], 'Actual complete resource destruction')
            need(row['selected_used_bytes'] == 388 and capacity >= 388 and capacity % 4 == 0 and row['predicted_growth_replays'] == row['actual_growth_replays'] == (capacity - 388) // 4 + 1 and row['first_replay_msize_queries'] == (2 if capacity == 388 else 1), 'Genuine same-owner capacity predicts actual next registry growth')
        need(c['actual_first_replay_msize_queries'] == sum(r['first_replay_msize_queries'] for r in sequences) and c['genuine_growth_replays'] == sum(r['actual_growth_replays'] for r in sequences), 'Actual provider size/growth totals')
        exact_counts(rows['paired']['counts'], PAIRED_COUNTS, 'paired125')
        paired = rows['paired']
        need(paired['loaded_input_relation_report_sha256'] == config['gates']['loaded_input_relation']['sha256'] and paired['loaded_input_difference_bytes'] == 71 and paired['loaded_input_difference_DWORDs'] == 25 and paired['loaded_input_opaque_pointer_targets_proven'] is False and paired['loaded_input_native_DllMain_credit'] is False, 'Exact finite whole loaded-input relation and scope')
        for field in ('blanket_page_mask', 'original_and_native_bytes_modified', 'whole_game_liveness_proven', 'Lockit_original_postRET_observed', 'Lockit_opaque_loaded_bytes_masked'): need(paired[field] is False, 'Unmodified and explicitly bounded paired observations ' + field)
        need(paired['original_record_bytes'] == 356992 and paired['native_record_bytes'] == 159716 and paired['Lockit_whole_private_initial_backings'] == 32 and paired['Lockit_native_whole_mapped_backings'] == 4096, 'Unchanged ABI and complete owner backing extents')
        need(rows['original_source']['AFTER_machine_seed'] is False and rows['original_source']['observed_original_postRET'] is False and rows['original_source']['whole_original_provider_stack_equivalence'] is False, 'Actual original observation limits retained')
        need(len(rows['preparation']['selected_order']) == 125 and len(rows['preparation']['registration_roots']) == 97, 'Exact whole selected schedule')
        native = rows['native_preparation']
        need(native['new_roots'] == [0x4b7f70] and native['live_owner_bound'] == 85 and native['exact_owned_causal_accesses'] == 172 and native['exact_primary_publications'] == 7 and native['normal_branch_only'] is True and native['native_DllMain_executed'] is False and native['guest_CS_native_opaque_copy'] is False, 'Actual tree root, source owner contracts and native resource scope')
        old_interface = read(native['owner_contract_report'], native['owner_contract_report_sha256']); absorb(old_interface)
        need(rows['original_source']['source_contract_sha256'] == old_interface['contracts_sha256'] and has(rows['original_source'], old_interface['contracts'], old_interface['contracts_sha256']), 'Fresh old-owner source proof shares authentic accepted interface')
        for label in ('preparation', 'build', 'native'):
            need(rows[label]['full_dependency_acceptance_rehash_required'] is True, 'Local iteration final full rehash obligation ' + label)
            reuse = rows[label]['inherited_capture_payload_hashes_reused']; need(len(reuse) == 166, 'Every inherited archive identity ' + label)
            for path, identity in reuse.items(): need(PINS.get(normalized(str(Path(path).resolve()))) == identity, 'Historical payload retained in complete final union')
        # The acceptance gate physically reads every dependency, including all
        # historical capture parts. Metadata iteration reuse has no exemption.
        closure = verify_manifest(PINS)
        need(closure['passed'] and closure['metadata_only_cache_used'] is False, 'Complete conflict-normalized physical rehash'); passed = True
    except BaseException:
        (out / 'failure.txt').write_text(traceback.format_exc()); raise
    finally:
        result = dict(passed=passed, scope='Connected selected125: complete original/native/source/provider/paired initialization with exact seven-owner tree and real native CS association', connected_roots=125 if passed else 124, new_roots=1 if passed else 0, total_inventory_roots=144, remaining_inventory_roots=19 if passed else 20, initializer_inventory_fraction=125/144 if passed else 124/144, inventory_is_project_completion_percentage=False, gates=config.get('gates', {}), extent=config.get('extent', {}), explicit_measured_predicates=predicates, bounded_scope=config.get('bounded_scope', {}), physical_closure=closure, elapsed_seconds=time.perf_counter()-started, whole_M4_complete=False, native_game_launch_complete=False, files=PINS)
        path = out / 'report.json'; path.write_text(json.dumps(result, indent=2)+'\n'); register(path, sha(path))
        (out / 'pins.json').write_text(json.dumps(dict(files=PINS), indent=2)+'\n')
        print(json.dumps(dict(passed=passed, sha256=sha(path), connected_roots=result['connected_roots'], physical_inputs=len(PINS))))

if __name__ == '__main__': main(Path(sys.argv[1]).resolve(), sys.argv[2], Path(sys.argv[3]).resolve(), sys.argv[4])
