"""Independent metadata/configuration review; final acceptance rehashes payloads.

This tool reads only JSON receipts, manifests and Python source. It never calls
accept.main, verify_manifest, DirectSet, or an archive reader.
"""
from pathlib import Path
import ast, hashlib, json, ntpath, re, sys, traceback
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
PINS = {}
REQUIRED = set('parent game_recovery game_lifts game_symbols game_callbacks game_static game_interface provider_recovery provider_lifts provider_interface ghidra original_preparation original_build original_run original_validation original_review original_source owner_source owner_original native_preparation preparation build abi link resource native_integration iteration lineage native source source_review provider provider_review paired paired_review controls_build controls_execution controls controls_review'.split())
MAPS = ('files', 'physical_inputs', 'physical_dependencies', 'generated_sources', 'sources', 'tools', 'artifacts')

def need(value, message):
    if not value:
        raise ValueError(message)

def key(path):
    path = str(Path(path).resolve())
    need(ntpath.isabs(path) and len(ntpath.splitdrive(path)[0]) == 2, 'Absolute local physical path')
    need('\x00' not in path and ':' not in ntpath.splitdrive(path)[1], 'Unambiguous local physical path')
    return ntpath.normcase(ntpath.normpath(path))

def register(path, digest):
    need(isinstance(digest, str) and re.fullmatch('[0-9a-f]{64}', digest), 'Exact SHA256 syntax')
    name = key(path)
    need(name not in PINS or PINS[name] == digest, 'No conflicting physical identities')
    PINS[name] = digest

def sha(path):
    path = Path(path)
    need(path.suffix.lower() != '.mwb', 'No capture archive may be opened here')
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def unique(pairs):
    result = {}
    for field, value in pairs:
        need(field not in result, 'No duplicate JSON keys')
        result[field] = value
    return result

def read(path, expected=None):
    actual = sha(path)
    need(expected is None or expected == actual, 'Exact metadata/source physical SHA')
    register(path, actual)
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique)

def absorb(report):
    for field in MAPS:
        mapping = report.get(field, {})
        need(isinstance(mapping, dict), 'Flat physical map ' + field)
        for path, digest in mapping.items():
            register(path, digest)

def has(report, path, digest):
    return any(key(name) == key(path) and value == digest for field in MAPS for name, value in report.get(field, {}).items())

def value(report, field):
    for part in field.split('.'):
        report = report[int(part)] if isinstance(report, list) else report[part]
    return report

def literal_constants(tree):
    result = {}
    for statement in tree.body:
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name):
            name = statement.targets[0].id
            if name in ('REQUIRED', 'BOUNDED'):
                result[name] = ast.literal_eval(statement.value)
            elif name == 'EXTENT':
                need(isinstance(statement.value, ast.Call) and isinstance(statement.value.func, ast.Name) and statement.value.func.id == 'dict' and not statement.value.args, 'Literal extent schema')
                result[name] = {item.arg: ast.literal_eval(item.value) for item in statement.value.keywords}
    return result

def source_contract(accept_path, manifests_path):
    raw = accept_path.read_text(encoding='utf-8-sig')
    tree = ast.parse(raw)
    constants = literal_constants(tree)
    need(constants['REQUIRED'] == REQUIRED and len(REQUIRED) == 39, 'Actual exact independent39 gate set')
    main = next(item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == 'main')
    success = [item for item in ast.walk(main) if isinstance(item, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'passed' for target in item.targets) and isinstance(item.value, ast.Constant) and item.value.value is True]
    verify = [item for item in ast.walk(main) if isinstance(item, ast.Call) and isinstance(item.func, ast.Name) and item.func.id == 'verify_manifest']
    need(len(success) == 1 and len(verify) == 1 and success[0].lineno == verify[0].lineno, 'Sole success assignment follows actual full union verifier')
    line = raw.splitlines()[success[0].lineno - 1]
    need(line.index('verify_manifest(PINS)') < line.index("closure['passed']") < line.index('passed=True'), 'Full physical rehash must succeed before credit')
    need("closure['metadata_only_cache_used'] is False" in line, 'No metadata-only final closure')
    for required in (
        "len(item['equal'])>=2", "set(config['gates'])==REQUIRED", "config['extent']==EXTENT",
        "review['gates_reviewed']==len(REQUIRED)", "has(review,configuration,sha(configuration))",
        "has(review,__file__,sha(__file__))", "full_dependency_acceptance_rehash_required",
        "inherited_capture_payload_hashes_reused", "PINS.get(normalized(str(Path(p).resolve())))==h",
        "original_source", "owner_original", "provider_review", "paired_review", "source_review",
        "connected_roots=124 if passed else 120", "whole_M4_complete=False", "native_game_launch_complete=False",
    ):
        need(required in raw, 'Required concrete acceptance guard ' + required)
    manifest_source = manifests_path.read_text(encoding='utf-8-sig')
    manifest_tree = ast.parse(manifest_source)
    verifier = next(item for item in manifest_tree.body if isinstance(item, ast.FunctionDef) and item.name == 'verify_manifest')
    body = ast.get_source_segment(manifest_source, verifier)
    need("for path, expected in normalized_files.items():" in body and "Path(path).open('rb')" in body and "hashlib.file_digest(stream, 'sha256')" in body and 'actual != expected' in body and 'metadata_only_cache_used=False' in body, 'Verifier physically hashes every normalized file without historical exemption')
    need('.mwb' not in body and 'cache' not in body.replace('metadata_only_cache_used=False', ''), 'No final archive/caching exception')
    for path in (accept_path, manifests_path):
        register(path, sha(path))
    return constants

def main(configuration, name):
    out = ROOT / 'reports/m4-lockit-build-review' / name
    need(not out.exists(), 'Fresh additive review')
    out.mkdir(parents=True)
    passed = False
    predicates = 0
    gates = {}
    try:
        accept_path = ROOT / 'tools/m4-joint-startup124/accept.py'
        constants = source_contract(accept_path, ROOT / 'tools/m4-pipeline/manifests.py')
        config = read(configuration)
        need(set(config) == {'gates', 'extent', 'bounded_scope', 'configuration_source', 'configuration_source_sha256', 'review_specification', 'review_specification_sha256'}, 'Exact configuration schema')
        need(set(config['gates']) == REQUIRED and config['extent'] == constants['EXTENT'], 'Every39 gate and exact124 extents')
        need(set(config['bounded_scope']) == constants['BOUNDED'] and all(item is False for item in config['bounded_scope'].values()), 'Actual/source bounded frontier retained')
        for label, expected in dict(selected_roots=124, new_roots=4, original_sequences=6, original_phases=744, native_sequences=12, native_phases=1488, ordered_callbacks_per_sequence=96, observed_source_pages=43, new_FS_owned_store_contracts=32, new_FS_publication_contracts=8, linked_literal_COFFs_per_level=363, compiled_objects_per_level=27, capture_objects_per_level=2, actual_linked_inputs_per_level=392).items():
            need(config['extent'][label] == expected, 'Independent actual selected extent ' + label)
        need(sha(config['configuration_source']) == config['configuration_source_sha256'], 'Exact generator source')
        register(config['configuration_source'], config['configuration_source_sha256'])
        specification = read(config['review_specification'], config['review_specification_sha256'])
        need(specification == config['gates'], 'Configuration equals actual physically reviewed gate specification')
        for label in sorted(REQUIRED):
            item = config['gates'][label]
            need(set(item) == {'path', 'sha256', 'equal'}, 'Exact measured gate schema ' + label)
            path = (ROOT / item['path']).resolve()
            need(path.is_relative_to(ROOT) and path.suffix == '.json', 'Workspace gate receipt ' + label)
            gate = read(path, item['sha256'])
            need(gate['passed'] is True, 'Successful concrete gate ' + label)
            absorb(gate)
            manifest = path.parent / 'pins.json'
            if manifest.exists():
                pins = read(manifest)
                need(set(pins) == {'files'}, 'Exact sibling manifest ' + label)
                absorb(pins)
            need(isinstance(item['equal'], dict) and len(item['equal']) >= 2, 'Explicit substantial gate predicates ' + label)
            for field, expected in item['equal'].items():
                actual = value(gate, field)
                need(type(actual) is type(expected) and actual == expected, 'Exact typed measured predicate ' + label + ':' + field)
                predicates += 1
            gates[label] = gate
        def edge(label, target):
            item = config['gates'][target]
            need(has(gates[label], ROOT / item['path'], item['sha256']), 'Independent physical evidence edge ' + label + ' -> ' + target)
        for label in ('abi', 'link', 'resource'):
            edge(label, 'build')
        for label in ('native_preparation', 'preparation', 'build'):
            edge('lineage', label)
        for label in ('source', 'provider', 'paired'):
            edge(label, 'native')
        for label, target in [('source_review', 'source'), ('provider_review', 'provider'), ('paired_review', 'paired'), ('controls_review', 'controls'), ('controls', 'controls_execution'), ('controls', 'build'), ('original_source', 'original_validation'), ('owner_original', 'owner_source'), ('owner_original', 'original_source')]:
            edge(label, target)
        for label in ('source', 'provider'):
            need(gates[label]['per_phase_BEFORE_machine_seed'] is False and gates[label]['candidate_AFTER_machine_seed'] is False, 'Fresh persistent source without observed machine reseeding')
        source_counts = gates['source']['counts']
        for field, expected in dict(persistent124_sequences=12, persistent_phases=1488, whole_page_BEFORE=63984, whole_page_AFTER=63984, literal_registration_roots=1152, literal_Lockit_CALL_RET_pairs=96, actual_native_CS40_source_API_relations=96, native_FS_source_accesses=684, actual_native12B_source_relations=456).items():
            need(source_counts[field] == expected, 'Independent full source count ' + field)
        provider_counts = gates['provider']['provider_counts']
        for field, expected in dict(complete124_provider_sequences=12, selected_registration_closures=1152, actual_MFC_allocations=696, actual_duplicate_allocations=228, actual_source_frees=936, actual_MFC_source_frees=696, actual_CS_deletes=60, actual_heap_destroys=12).items():
            need(provider_counts[field] == expected, 'Independent full provider count ' + field)
        provider_sequences = gates['provider']['provider_sequences']
        need(len(provider_sequences) == 12 and {(row['level'], row['sequence']) for row in provider_sequences} == {(level, sequence) for level in ('O0', 'O2') for sequence in range(6)}, 'All current actual provider cases')
        need(provider_counts['whole_State_checkpoints'] == provider_counts['whole_CPU_checkpoints'] == provider_counts['whole_FX_checkpoints'] == sum(row['compared_checkpoints'] for row in provider_sequences), 'Every complete provider checkpoint')
        for row in provider_sequences:
            capacity = row['first_replay_msize_capacity']
            need(row['all_resources_released'] and row['actual_post_HeapDestroy_identity'], 'Actual final resource cleanup')
            need(row['selected_used_bytes'] == 384 and capacity >= 384 and capacity % 4 == 0, 'Genuine selected vector size/capacity')
            need(row['predicted_growth_replays'] == row['actual_growth_replays'] == (capacity - 384) // 4 + 1, 'Independent first replay capacity predicts real next growth')
            need(row['first_replay_msize_queries'] == (2 if capacity == 384 else 1), 'Genuine cache/query count')
        need(provider_counts['actual_first_replay_msize_queries'] == sum(row['first_replay_msize_queries'] for row in provider_sequences) and provider_counts['genuine_growth_replays'] == sum(row['actual_growth_replays'] for row in provider_sequences), 'Whole current provider growth/query totals')
        paired = gates['paired']
        for field, expected in dict(paired_phases=1488, paired124_sequences=12, whole_nonstack_page_relations=122016, separate_whole_loader_page_input_relations=2976, whole42_nonstack_page_endpoint_relations=124992, Lockit_paired_complete12B_normal_FS_relations=96, Lockit_paired_bounded_API_semantic_relations=96, Lockit_actual_owner_publication_activations=96, Lockit_branch_field_source_derivations=216, Lockit_whole_native_owned_carries=288).items():
            need(paired['counts'][field] == expected, 'Independent full paired count ' + field)
        for field in ('blanket_page_mask', 'original_and_native_bytes_modified', 'whole_game_liveness_proven', 'Lockit_original_postRET_observed', 'Lockit_opaque_loaded_bytes_masked'):
            need(paired[field] is False, 'Actual paired bound ' + field)
        need(paired['original_record_bytes'] == 356992 and paired['native_record_bytes'] == 159716 and paired['Lockit_whole_private_initial_backings'] == 32 and paired['Lockit_native_whole_mapped_backings'] == 4096, 'Actual unchanged packed and owner backing extents')
        need(gates['original_source']['AFTER_machine_seed'] is False and gates['original_source']['observed_original_postRET'] is False and gates['original_source']['whole_original_provider_stack_equivalence'] is False, 'Original observations retain actual pre-epilogue/preRET limits')
        need(gates['native']['build_sha256'] == config['gates']['build']['sha256'], 'Actual normal worker exact reviewed final build')
        need(gates['build']['preparation_sha256'] == config['gates']['preparation']['sha256'], 'Actual build exact final preparation')
        need([level['level'] for level in gates['native']['levels']] == ['O0', 'O2'] and gates['native']['native_executed'] is True, 'Both actual current native levels')
        for label in ('original_run', 'original_validation'):
            need(gates[label]['build_sha256'] == config['gates']['original_build']['sha256'], 'Exact authentic original worker build')
        need(gates['controls_execution']['build_sha256'] == config['gates']['controls_build']['sha256'] and gates['controls_build']['parent_build_sha256'] == config['gates']['build']['sha256'], 'Controls actually compile final implementation')
        need(gates['owner_original']['source_contract_sha256'] == gates['owner_source']['contracts_sha256'], 'Exact original corroboration to native arrays')
        need(has(gates['owner_original'], gates['owner_source']['contracts'], gates['owner_source']['contracts_sha256']), 'Physical native owner arrays pinned')
        need(len(gates['preparation']['selected_order']) == 124 and len(gates['preparation']['registration_roots']) == 96, 'Full final root/callback schedule')
        reused = {}
        for label in ('build', 'native'):
            need(gates[label]['full_dependency_acceptance_rehash_required'] is True, 'Final closure obligation from local iteration')
            for path, digest in gates[label]['inherited_capture_payload_hashes_reused'].items():
                need(PINS.get(key(path)) == digest, 'Every historical payload remains in final physical closure')
                reused[key(path)] = digest
        need(reused and all(Path(path).suffix == '.mwb' for path in reused), 'Actual historical archive identities retained')
        register(__file__, sha(__file__))
        passed = True
    except BaseException:
        (out / 'failure.txt').write_text(traceback.format_exc())
        raise
    finally:
        result = dict(passed=passed, scope='Independent light review of actual39 gate metadata, typed extents, lineage, configuration/source identity and mandatory final complete physical closure; archive payload verification remains the acceptance gate', gates_reviewed=len(gates), explicit_typed_predicates_reviewed=predicates, whole_capture_payloads_rehashed=False, capture_archive_reader_opened=False, final_full_union_rehash_mandatory=True, initializer_credit=False, configuration=str(Path(configuration).resolve()), files=PINS)
        path = out / 'report.json'
        path.write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(dict(passed=passed, sha256=sha(path), gates_reviewed=len(gates), physical_identities=len(PINS))))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), sys.argv[2])
