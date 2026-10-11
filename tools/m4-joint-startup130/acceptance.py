"""Accept selected130 only from reviewed, current semantic evidence and full rehash.

The accepted125 receipt carries the earlier finite proofs. This gate adds five
roots only after current original/native/source/provider/paired chains agree.
Compilation and structural execution alone confer no inventory credit.
"""
from pathlib import Path
import hashlib
import json
import sys
import time
import traceback

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
from manifests import normalized, digest, unique_object, verify_manifest

REQUIRED = {
    'parent', 'native_preparation', 'cleanup_review', 'preparation', 'build',
    'abi', 'link', 'resource', 'build_review', 'prelaunch',
    'original_preparation', 'original_build', 'original_run',
    'original_validation', 'original_review', 'old_owner_source',
    'current_original_source', 'current_original_review',
    'source_provider_preflight', 'source_provider_preparation_review',
    'native', 'source_provider', 'source_provider_review',
    'source_provider_closure', 'pair_preparation', 'pair_policy_review',
    'paired', 'paired_review', 'loaded_input_relation',
    'mixed_controls_build', 'mixed_controls_execution', 'mixed_controls',
    'mixed_controls_review', 'controls_equivalence',
    'formatter_fixture_source', 'formatter_fixture_witnesses',
    'formatter_fixture_review', 'formatter_controls',
    'formatter_controls_review', 'formatter_control_applicability',
    'cosine_runtime', 'cosine_runtime_review',
}
NEW_ROOTS = {0x4df610, 0x4e0710, 0x4e0810, 0x4e1ca0, 0x4b64f0}
EXTENT = dict(selected_roots=130, new_roots=5, original_sequences=6,
    original_phases=780, native_sequences=12, native_phases=1560,
    callbacks_per_sequence=101, whole_source_pages=46,
    literal_objects_per_level=397, compiled_objects_per_level=30,
    capture_objects_per_level=2, linked_inputs_per_level=429,
    live_owners_per_sequence=92, MFC_owners_per_sequence=68,
    duplicate_owners_per_sequence=19, formatter_owners_per_sequence=4,
    source_State_bytes=3504, source_CPU_bytes=40, source_FX_bytes=512,
    source_ENV_bytes=28)
BOUNDED = {
    'whole_M4_complete', 'native_game_launch_complete', 'native_menu',
    'native_Training', 'native_DllMain', 'full_native_CRT_attach',
    'full_native_MFC_attach', 'MSVCP_lazy_or_Sleep_path',
    'general_formatter', 'general_trigonometric_equivalence',
    'whole_original_provider_stack_equality', 'whole_original_TIB_equality',
    'whole_game_alias_liveness', 'handler_execution', 'exception_dispatch',
    'allocation_NULL_paths', 'original_postRET_observed',
    'opaque_loaded_pointer_targets_proven',
}
PINS = {}


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def register(path, identity):
    key = normalized(str(Path(path).resolve()))
    identity = digest(identity)
    need(key not in PINS or PINS[key] == identity,
         'Conflicting physical dependency ' + key)
    PINS[key] = identity


def read(path, identity=None):
    path = Path(path).resolve()
    actual = sha(path)
    need(identity is None or identity == actual, 'Exact receipt ' + str(path))
    register(path, actual)
    return json.loads(path.read_text(encoding='utf-8-sig'),
                      object_pairs_hook=unique_object)


def absorb(report):
    for field in ('files', 'physical_inputs', 'physical_dependencies',
                  'generated_sources', 'sources', 'tools', 'artifacts'):
        for path, identity in report.get(field, {}).items():
            register(path, identity)


def has(report, path, identity):
    target = normalized(str(Path(path).resolve()))
    return any(normalized(str(Path(p).resolve())) == target and h == identity
        for field in ('files', 'physical_inputs', 'physical_dependencies',
                      'generated_sources', 'sources', 'tools', 'artifacts')
        for p, h in report.get(field, {}).items())


def extent_value(report, field):
    for key in field.split('.'):
        report = report[int(key)] if isinstance(report, list) else report[key]
    return report


def exact_counts(actual, expected, label):
    for field, value in expected.items():
        need(type(actual[field]) is type(value) and actual[field] == value,
             'Exact typed ' + label + ' count: ' + field)


def semantic_checks(rows, gates):
    def edge(label, target):
        item = gates[target]
        need(has(rows[label], ROOT / item['path'], item['sha256']),
             'Current physical evidence edge ' + label + ' -> ' + target)

    for label in ('abi', 'link', 'resource', 'prelaunch'):
        edge(label, 'build')
    for label in ('source_provider', 'paired'):
        edge(label, 'native')
    for label in ('original_review', 'old_owner_source',
                  'current_original_source'):
        edge(label, 'original_validation')
    for label, target in (
        ('cleanup_review', 'native_preparation'),
        ('build_review', 'abi'), ('build_review', 'link'),
        ('build_review', 'resource'),
        ('current_original_review', 'current_original_source'),
        ('source_provider_preparation_review', 'source_provider'),
        ('source_provider_review', 'source_provider'),
        ('source_provider_closure', 'source_provider'),
        ('loaded_input_relation', 'source_provider'),
        ('loaded_input_relation', 'native'),
        ('paired_review', 'paired'), ('paired', 'loaded_input_relation'),
        ('paired', 'source_provider'), ('paired', 'current_original_source'),
        ('paired', 'current_original_review'),
        ('mixed_controls', 'mixed_controls_execution'),
        ('mixed_controls_review', 'mixed_controls'),
        ('controls_equivalence', 'mixed_controls_build'),
        ('controls_equivalence', 'build'),
        ('formatter_fixture_review', 'formatter_fixture_source'),
        ('formatter_controls_review', 'formatter_controls'),
        ('formatter_control_applicability', 'formatter_controls'),
        ('formatter_control_applicability', 'native_preparation'),
        ('cosine_runtime_review', 'cosine_runtime'),
    ):
        edge(label, target)

    parent = rows['parent']
    need(parent['connected_roots'] == 125 and
         parent['remaining_inventory_roots'] == 19 and
         parent['whole_M4_complete'] is False and
         parent['native_game_launch_complete'] is False,
         'Exact accepted125 parent scope')
    preparation, build, native = (rows[k] for k in ('preparation', 'build', 'native'))
    need(preparation['parent_acceptance_sha256'] == gates['parent']['sha256'] and
         preparation['native_preparation_sha256'] == gates['native_preparation']['sha256'],
         'Exact parent and corrected native19 preparation')
    need(build['preparation_sha256'] == gates['preparation']['sha256'] and
         native['build_sha256'] == gates['build']['sha256'],
         'Exact final compile and actual execution lineage')
    order = preparation['selected_order']
    need(len(order) == 130 and len({r['entry'] for r in order}) == 130 and
         len({r['slot'] for r in order}) == 130 and
         set(preparation['new_roots']) == NEW_ROOTS and
         len(preparation['registration_roots']) == 101,
         'Exact130 table with five new roots and101 callbacks')
    old_item = parent['gates']['preparation']
    old_preparation = read(ROOT / old_item['path'], old_item['sha256'])
    absorb(old_preparation)
    old_order = old_preparation['selected_order']
    need([r for r in order if r['entry'] not in NEW_ROOTS] == old_order,
         'Complete accepted125 relative order preserved')
    need(native['native_executed'] is True and
         [r['level'] for r in native['levels']] == ['O0', 'O2'],
         'Both actual final optimized levels')
    for level in native['levels']:
        need(level['logical_files'] == 4330908 and
             level['payload_bytes'] == 16907803835,
             'Complete current strict130 capture extent')
    for name in ('original_run', 'original_validation'):
        need(rows[name]['build_sha256'] == gates['original_build']['sha256'],
             'Exact current original worker ' + name)
    need(rows['original_build']['preparation_sha256'] == gates['original_preparation']['sha256'],
         'Exact original130 preparation')
    need(rows['mixed_controls_execution']['build_sha256'] == gates['mixed_controls_build']['sha256'],
         'Actual corrected19 fault-test worker')

    source = rows['source_provider']
    for field in ('complete_selected_source', 'complete_private_mixed_publications',
                  'complete_private_mixed_FS32Q', 'complete_provider_lifecycle',
                  'worker_post_HeapDestroy_identity_observed', 'source_and_provider_combined',
                  'reader_closed'):
        need(source[field] is True, 'Complete persistent source/provider ' + field)
    for field in ('per_phase_BEFORE_machine_seed', 'candidate_AFTER_machine_seed',
                  'canonical_reader_changed', 'duplicate_selected_source_reader',
                  'native_CS40_opaque_copy', 'native_DllMain_credit'):
        need(source[field] is False, 'Explicit persistent source scope ' + field)
    exact_counts(source['counts'], dict(persistent130_sequences=12,
        persistent_phases=1560, whole_page_BEFORE=71760, whole_page_AFTER=71760,
        literal_registration_roots=1212, literal_Lockit_CALL_RET_pairs=432,
        actual_native_CS40_source_API_relations=432, native_FS_source_accesses=1008,
        actual_native12B_source_relations=672, literal_formatter_roots=48,
        whole_formatter_native_capacity_derivations=48,
        whole_mixed_native_capacity_derivations=36, literal_compound_cosine_roots=12,
        actual_generation_occurrence_joins=84, whole_owned_access_relations=2064,
        whole_publication_relations=84, whole_native_scratch_contexts=312,
        whole_native_tree_owner_backings=84,
        whole_mixed_private_owned_operands=120,
        whole_mixed_private_publications=36,
        whole_mixed_private_FS32Q_frames=24,
        whole_mixed_private_raw12B_records=48,
        whole_mixed_private_Lockit16Q_calls=24,
        whole_mixed_private_raw8Q_imports=24,
        actual_native_indirect_full_State_CPU_FX_boundary_joins=144,
        literal_indirect_CALL_RET_derivations=72, actual_native_indirect_CALL_RET_joins=72),
        'source130')
    provider = source['provider_counts']
    exact_counts(provider, dict(complete130_provider_sequences=12,
        selected_registration_closures=1212, actual_MFC_allocations=816,
        actual_duplicate_allocations=228, actual_source_frees=1056,
        actual_MFC_source_frees=816, actual_formatter_cleanup_frees=48,
        actual_CS_deletes=60, actual_heap_destroys=12,
        **{'whole_formatting-calls_rows': 432,
           'whole_formatting-owned_rows': 1620,
           'whole_formatting-publications_rows': 144,
           'whole_formatting-dispatches_rows': 576}),
        'provider130')
    cases = source['provider_sequences']
    need(len(cases) == 12 and {(r['level'], r['sequence']) for r in cases} ==
         {(level, seq) for level in ('O0', 'O2') for seq in range(6)},
         'Every actual current provider chain')
    total = sum(r['compared_checkpoints'] for r in cases)
    need(total > 0 and provider['whole_State_checkpoints'] ==
         provider['whole_CPU_checkpoints'] == provider['whole_FX_checkpoints'] == total,
         'Every measured provider machine checkpoint')
    for case in cases:
        capacity = case['first_replay_msize_capacity']
        need(case['all_resources_released'] and case['actual_post_HeapDestroy_identity'],
             'Actual complete same-owner resource destruction')
        need(case['selected_used_bytes'] == 404 and capacity >= 404 and capacity % 4 == 0 and
             case['predicted_growth_replays'] == case['actual_growth_replays'] ==
             (capacity - 404) // 4 + 1 and
             case['first_replay_msize_queries'] == (2 if capacity == 404 else 1),
             'Genuine source capacity predicts one reached registry growth')
    need(provider['genuine_growth_replays'] == sum(r['actual_growth_replays'] for r in cases) and
         provider['actual_first_replay_msize_queries'] ==
         sum(r['first_replay_msize_queries'] for r in cases),
         'Measured growth/query totals from all12 chains')

    # Per-gate typed predicates cover each complete new mixed private witness,
    # pair-policy domain and finite loaded-input difference set. The independently
    # reviewed configuration seals their exact schema as well as this source.
    paired = rows['paired']
    need(paired['original_record_bytes'] == 356992 and paired['native_record_bytes'] == 159716,
         'Unchanged full original/native ABI')
    for field in ('blanket_page_mask', 'original_and_native_bytes_modified',
                  'whole_game_liveness_proven', 'Lockit_original_postRET_observed',
                  'Lockit_opaque_loaded_bytes_masked', 'loaded_input_opaque_pointer_targets_proven',
                  'loaded_input_native_DllMain_credit'):
        need(paired[field] is False, 'Explicit unmodified paired scope ' + field)
    need(paired['loaded_input_relation_report_sha256'] == gates['loaded_input_relation']['sha256'],
         'Fresh current original/native whole loaded-input relation')
    need(paired['paired_initialization_data_contract'] is True and
         paired['reader_closed'] is True and paired['native_full_stack_source_proven'] is True and
         paired['native_execution_sha256'] == gates['native']['sha256'] and
         paired['native_source_report_sha256'] == gates['source_provider']['sha256'] and
         paired['original_combined_source_sha256'] == gates['current_original_source']['sha256'] and
         paired['original_combined_review_sha256'] == gates['current_original_review']['sha256'],
         'Complete current source-backed original/native paired proof lineage')
    loaded = rows['loaded_input_relation']
    need(loaded['original_validation_sha256'] == gates['original_validation']['sha256'] and
         loaded['native_execution_sha256'] == gates['native']['sha256'] and
         loaded['native_source_sha256'] == gates['source_provider']['sha256'],
         'Exact current physical original/native loaded-input proof lineage')
    # The current composer carries166 old preparation archives plus40 new
    # finite formatting/cosine inputs. Its reused subset is not the complete
    # accepted125 union: all253 parent archives remain separate final pins.
    parent_archives = {normalized(str(Path(path).resolve())): identity
        for path, identity in parent['files'].items()
        if Path(path).suffix.lower() == '.mwb'}
    old_archives = {normalized(str(Path(path).resolve())): identity
        for path, identity in old_preparation['inherited_capture_payload_hashes_reused'].items()}
    need(len(parent_archives) == 253 and len(old_archives) == 166,
         'Exact complete accepted125 archive union and inherited preparation subset')
    for path, identity in parent_archives.items():
        need(PINS.get(path) == identity, 'Every accepted125 archive retained in final union')
    current_inherited = None
    for label in ('preparation', 'build', 'native'):
        need(rows[label]['full_dependency_acceptance_rehash_required'] is True,
             'Complete final physical rehash obligation ' + label)
        inherited = rows[label]['inherited_capture_payload_hashes_reused']
        normalized_inherited = {normalized(str(Path(path).resolve())): identity
            for path, identity in inherited.items()}
        need(len(inherited) == len(normalized_inherited) == 206,
             'All current inherited archive identities retained ' + label)
        if current_inherited is None:
            current_inherited = normalized_inherited
        need(normalized_inherited == current_inherited,
             'Exact unchanged inherited archive map through preparation/build/execution')
        need(all(normalized_inherited.get(path) == identity
                 for path, identity in old_archives.items()),
             'All166 older preparation archives preserved ' + label)
        for path, identity in normalized_inherited.items():
            need(PINS.get(path) == identity,
                 'Historical archive present in final physical union')


def main(configuration, name, review_path, review_sha256):
    started = time.perf_counter()
    out = ROOT / 'reports/m4-joint-startup130-root' / name
    need(not out.exists(), 'Fresh acceptance output')
    out.mkdir(parents=True)
    passed = False
    config, rows, closure = {}, {}, {}
    predicates = 0
    try:
        config = read(configuration)
        register(__file__, sha(__file__))
        register(ROOT / 'tools/m4-pipeline/manifests.py', sha(ROOT / 'tools/m4-pipeline/manifests.py'))
        for field in ('configuration_source', 'requirements_source', 'review_specification'):
            register(config[field], config[field + '_sha256'])
        need(set(config['gates']) == REQUIRED and set(config['extent']) == set(EXTENT),
             'Complete exact130 gate set and extent fields')
        for field, expected in EXTENT.items():
            actual = config['extent'][field]
            need(type(actual) is type(expected) and actual == expected,
                 'Exact typed130 extent ' + field)
        need(set(config['bounded_scope']) == BOUNDED and
             all(type(v) is bool and v is False for v in config['bounded_scope'].values()),
             'Explicit open project frontiers')
        review = read(review_path, review_sha256)
        absorb(review)
        need(review['passed'] is True and review['gates_reviewed'] == len(REQUIRED) and
             has(review, configuration, sha(configuration)) and
             has(review, __file__, sha(__file__)), 'Independent exact complete acceptance review')
        for label, item in config['gates'].items():
            need(set(item) == {'path', 'sha256', 'equal'}, 'Exact configured gate schema')
            path = ROOT / item['path']
            report = read(path, item['sha256'])
            need(report['passed'] is True, 'Passed gate ' + label)
            absorb(report)
            sibling = path.parent / 'pins.json'
            if sibling.exists():
                manifest = read(sibling)
                need(set(manifest) == {'files'}, 'Exact sibling manifest ' + label)
                absorb(manifest)
            need(len(item['equal']) >= 2, 'Measured typed extent ' + label)
            for field, expected in item['equal'].items():
                actual = extent_value(report, field)
                need(type(actual) is type(expected) and actual == expected,
                     'Measured typed extent ' + label + ':' + field)
                predicates += 1
            rows[label] = report
        semantic_checks(rows, config['gates'])
        # Re-read every file, including all old/new capture parts. No hash-cache
        # or metadata-only substitution is permitted for accepted inventory.
        closure = verify_manifest(PINS)
        need(closure['passed'] and closure['metadata_only_cache_used'] is False,
             'Complete conflict-normalized physical union rehash')
        passed = True
    except BaseException:
        (out / 'failure.txt').write_text(traceback.format_exc())
        raise
    finally:
        result = dict(passed=passed,
            scope='Connected selected130: current original/native/source/provider/paired startup, four literal formatter families and finite compound cosine',
            connected_roots=130 if passed else 125, new_roots=5 if passed else 0,
            total_inventory_roots=144, remaining_inventory_roots=14 if passed else 19,
            initializer_inventory_fraction=130/144 if passed else 125/144,
            inventory_is_project_completion_percentage=False,
            gates=config.get('gates', {}), extent=config.get('extent', {}),
            explicit_measured_predicates=predicates,
            bounded_scope=config.get('bounded_scope', {}), physical_closure=closure,
            elapsed_seconds=time.perf_counter()-started, whole_M4_complete=False,
            native_game_launch_complete=False, files=PINS)
        path = out / 'report.json'
        path.write_text(json.dumps(result, indent=2) + '\n')
        register(path, sha(path))
        (out / 'pins.json').write_text(json.dumps(dict(files=PINS), indent=2) + '\n')
        print(json.dumps(dict(passed=passed, sha256=sha(path),
            connected_roots=result['connected_roots'], physical_inputs=len(PINS))), flush=True)


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), sys.argv[2], Path(sys.argv[3]).resolve(), sys.argv[4])
