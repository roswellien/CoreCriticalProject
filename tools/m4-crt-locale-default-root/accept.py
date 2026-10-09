"""Seal the bounded default locale evidence and preserve historical anchors."""
import json
from pathlib import Path
import sys
import time
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
BASE = ROOT / 'reports/m4-crt-locale-default-root'
sys.path.insert(0, str(ROOT/'tools/m4-pipeline'))
from capture_bundle import CaptureBundle, sha_file
from manifests import normalized, unique_object, verify_manifest
from paths import publish_bytes, workspace_path
from stages import verify_stage

NAMES = {'recovery', 'source_contract', 'preparation', 'build', 'author_execution',
         'root_model', 'source_audit', 'model_audit', 'compiled_build', 'compiled_native', 'hardware_review'}
CATEGORIES = ('files', 'sources', 'source_files', 'tools', 'tool_files', 'libraries',
              'entry_objects', 'matherr_objects', 'control_objects', 'initterm_objects',
              'mainargs_objects', 'normal_argv_objects', 'producer_objects', 'parser_objects',
              'locale_objects', 'compiler_read_headers', 'artifacts', 'input_files')


def need(value, why):
    if not value:
        raise ValueError(why)


def read(path):
    return json.loads(Path(path).read_bytes(), object_pairs_hook=unique_object)


def main(config_path, config_sha, directory):
    started = time.perf_counter_ns()
    out = workspace_path(directory, reports=True)
    need(out.parent == BASE and not out.exists(), 'Fresh root acceptance output')
    files = {}

    def add(path, digest=None):
        path = Path(path).absolute()
        key = normalized(str(path))
        value = sha_file(path) if digest is None else digest
        need(key not in files or files[key] == value, 'Consistent current dependency '+str(path))
        files[key] = value
        return path

    cfg = add(config_path, config_sha)
    need(sha_file(cfg) == config_sha, 'External admission config digest')
    config = read(cfg)
    need(set(config) == {'receipts', 'pins', 'history', 'documents', 'observer_stage'}, 'Exact admission schema')
    need(set(config['receipts']) == NAMES, 'All required current proof domains')
    values = {}
    for name, identity in config['receipts'].items():
        need(set(identity) == {'path', 'sha256'}, 'Exact receipt identity')
        path = add(identity['path'], identity['sha256'])
        need(sha_file(path) == identity['sha256'], 'Fixed current receipt '+name)
        value = read(path)
        need(value['passed'] is True, 'Successful current receipt '+name)
        values[name] = value
        for category in CATEGORIES:
            for p, h in value.get(category, {}).items():
                add(p, h)
    for identity in config['pins']:
        path = add(identity['path'], identity['sha256'])
        need(sha_file(path) == identity['sha256'], 'Fixed explicit pin map')
        for p, h in read(path)['files'].items():
            add(p, h)
    # Old accepted/failed evidence remains an anchor; its possibly superseded
    # dependency maps and flat captures do not enter this current closure.
    for identity in config['history'] + config['documents']:
        path = add(identity['path'], identity['sha256'])
        need(sha_file(path) == identity['sha256'], 'Fixed history/document binding')

    def equals(name, assertions):
        for key, expected in assertions.items():
            need(values[name].get(key) == expected, name+'/'+key)

    build_hash = config['receipts']['build']['sha256']
    prep_hash = config['receipts']['preparation']['sha256']
    need(values['build']['preparation_sha256'] == prep_hash, 'Production build binds exact preparation')
    need(values['author_execution']['build_sha256'] == values['source_audit']['build_sha256'] == build_hash,
         'Native execution and independent source audit bind exact production build')
    need(values['source_audit']['preparation_sha256'] == prep_hash and
         values['source_audit']['preparation_pins_sha256'] ==
         '746c347e6978ef1657e00847d173c9b19c3c7684ed2ec710a5869e52fbcfe91d', 'Exact reviewed preparation closure')
    equals('preparation', dict(source_identity_bytes=1856, compiled_locale_source_bytes=221,
        guarded_locale_source_bytes=269, lock_lifted_span_bytes=43, lock_guarded_span_bytes=91,
        full_lock_RET_claimed=False, source_accesses=15, source_PCs=20, borrowed_pages=17,
        prior_pages_preserved=16, State_bytes=3504, FX_bytes=512, State_reseed_after_writer=False,
        Runtime_CPU_preserved=True, Runtime_call_record_added=False, original_attach_executed=False,
        locale_table_initialized=False, parser_body_executed=False, original_executed=False,
        native_component_executed=False, whole_M4_complete=False))
    equals('source_audit', dict(unchanged_guest_objects=16, new_guest_objects=6,
        unchanged_FDIV_libraries=2, compiled_source_bytes=221, locale_source_identity_bytes=269,
        total_source_identity_bytes=1856, Runtime_CPU_preserved=True, Runtime_call_record_added=False,
        State_reseed_after_writer=False, original_executed=False, native_executed=False,
        malloc_body_executed=False, table_initialization_proved=False, whole_M4_complete=False))
    equals('author_execution', dict(positive_sequences=48, causal_sequences=24,
        native_stages_completed=2, original_executed=False, game_launched=False, whole_M4_complete=False))
    # The inherited author report's "native_executed_by_root" field is not
    # evidence of a second execution. Actual delegated stages are verified below.
    equals('root_model', dict(independently_modeled_ordinary_sequences=48,
        standard_causal_sequences_independently_modeled_by_root=0, checks=83423,
        selected_semantic_byte_corruption_denials=960, State_bytes=3504, FX_bytes=512,
        borrowed_pages=17, prior_pages_preserved=16, new_raw_RX_page=0x78003000,
        source_identity_bytes=1856, new_compiled_source_bytes=221, new_guarded_source_bytes=269,
        actual_source_PCs=20, actual_source_DWORD_accesses=15, actual_nested_source_CALLs=3,
        explicit_host_scheduler_store_separate=True, generic_Runtime_CPU_preserved=True,
        allocator_body_executed=False, locale_initialized=False, locale_RET_executed=False,
        codepage_API_executed=False, parser_executed_in_this_gate=False,
        DllMain_or_original_scheduling_recovered=False, State_reseed=False,
        argument_initialization_complete=False, main_initializer_count=27,
        inherited_execution_root_label_grants_independent_root_execution_credit=False,
        AFTER_machine_state_used_as_seed=False, author_expected_model_imported=False,
        original_executed=False, game_launched=False, whole_M4_complete=False))
    audit = values['model_audit']
    proof = audit['final_root_proof']
    need(audit['current_native_proof_bound'] and proof['execution_sha256'] == config['receipts']['author_execution']['sha256']
         and proof['observer_sha256'] == config['receipts']['root_model']['sha256'], 'Independent audit binds exact current model/native receipts')
    equals('model_audit', dict(whole_BEFORE_source_rows=48, independent_affine_source_ledger=True,
        full_frozen_model_mainargs_before_crosscheck=True, stopping_subclass_used_as_seam_expected_seed=False,
        root_consumer_equals_accepted_bytes=True, scheduler_store_separate_from_source=True,
        source_accesses_per_row=15, source_PCs_per_row=20, whole_State_bytes=3504,
        whole_FX_bytes=512, whole_Runtime_CPU_bytes=40, whole_mappings=17,
        additional_raw_RX_mapping=0x78003000, full_prior_mapping_preservation=True,
        State_projection_only_EIP_ESP=True, generic_Runtime_CPU_preserved=True,
        AFTER_machine_state_used_as_seed=False, candidate_expected_value_code_imported=False,
        root_model_full_causal_audit=False, allocator_body_or_result_proved=False,
        locale_initialized=False, original_attach_proved=False, full_parser_sizing_proved=False,
        whole_M4_complete=False))
    native = values['compiled_native']
    equals('compiled_native', dict(native_scenarios=132, malformed_token_denials=50,
        original_executed=False, ordinary_game_launched=False, malloc_body_executed=False,
        table_initialization_proved=False, whole_M4_complete=False))
    equals('hardware_review', dict(native_scenarios=132, actual_hardware_pairs=264,
        hardware_semantic_denials=548, inventory_request_denials=14, native_executed=False,
        original_executed=False, malloc_body_executed=False, table_initialization_proved=False,
        whole_M4_complete=False))
    need(native['native_checks'] == values['hardware_review']['native_checks'] == 4838,
         'Actual compiled assertions from completed native receipts')
    need(values['hardware_review']['native_sha256'] == config['receipts']['compiled_native']['sha256'],
         'Rich hardware/inventory checks bind exact native corpus')
    need(native['compiled_sha256'] == config['receipts']['compiled_build']['sha256'], 'Native corpus binds current independent fixture build')
    fixture = values['compiled_build']
    fixture_sources = {normalized(str(Path(p).absolute())):h for p,h in fixture['sources'].items()}
    need(fixture['compiled_only'] is True and fixture_sources[normalized(str(Path(config['receipts']['build']['path']).absolute()))] == build_hash,
         'Compile-only fixture binds exact current production build')

    observer_stage = config['observer_stage']
    need(proof['stage_sha256'] == observer_stage['sha256'], 'Independent audit binds completed observer stage')
    need(verify_stage(observer_stage['path'], observer_stage['sha256'])['recorded_stage_passed'], 'Actual stable zero-exit observer stage')
    recorded = read(Path(observer_stage['path'])/'stage.json')
    need({normalized(p):h for p,h in recorded['artifact_sha256'].items()}[normalized(str(Path(config['receipts']['root_model']['path']).absolute()))] ==
         config['receipts']['root_model']['sha256'], 'Completed stage output association')
    for path in Path(observer_stage['path']).iterdir():
        if path.is_file():
            add(path)
    archives, native_stages = [], []
    for kind, levels in (('author', values['author_execution']['levels']), ('independent', native['levels'])):
        need(set(levels) == {'O0', 'O2'}, 'Both exact optimization levels '+kind)
        for level, info in levels.items():
            for key in ('native_stage', 'pack_stage'):
                stage = Path(info[key])
                receipt = add(stage/'stage.json')
                checked = verify_stage(stage, sha_file(receipt))
                need(checked['recorded_stage_passed'], 'Completed native/archive stage '+kind+'/'+level+'/'+key)
                command = read(receipt)
                if key == 'native_stage':
                    need([normalized(p) for p in command['argv']] == [normalized(p) for p in info['argv']], 'Direct native request matches bound receipt')
                    need(normalized(command['argv'][0]) == normalized(info['worker']), 'Actual isolated worker')
                for name in ('stdout.bin', 'stderr.bin'):
                    add(stage/name)
                native_stages.append(dict(kind=kind, level=level, role=key, verification=checked))
            digest = info['bundle_sha256']
            with CaptureBundle(add(info['bundle'], digest), digest) as reader:
                need(reader.read_bytes('COMPLETE') == b'COMPLETE', 'Closed capture writer')
                need(len(reader.names()) == info['logical_files'], 'Complete external archive inventory')
                if kind == 'author':
                    need(info['logical_files'] == 41268, 'Exact author capture inventory')
                else:
                    completed = json.loads(reader.read_bytes('controls.json'), object_pairs_hook=unique_object)
                    need(completed == info['result'] and completed['passed'] is True and completed['scenarios'] == 66
                         and completed['malformed_token_denials'] == 25, 'Closed independent native corpus result')
            archives.append(dict(kind=kind, level=level, path=info['bundle'], sha256=digest, logical_files=info['logical_files']))
    need(not any('/actual-o' in p.replace('\\','/') and '/case-' in p.replace('\\','/') for p in files),
         'Current independent captures use sealed archives')
    for path in (Path(__file__), Path(__file__).with_name('create_config.py'), Path(sys.executable)):
        add(path)
    closure = verify_manifest(files)
    out.mkdir()
    publish_bytes(out/'pins.json', (json.dumps(dict(files=files), indent=2)+'\n').encode())
    report = dict(passed=True, scope='Bounded genuine default locale prefix to unresolved real malloc(24) CALL',
        receipts=config['receipts'], history=config['history'], documents=config['documents'],
        historical_receipts_expanded=False, files=files, physical_closure=closure,
        pins_sha256=sha_file(out/'pins.json'), archives=archives, verified_stages=native_stages,
        native_executor='Delegated author and independent reviewer; root independently compares and seals evidence',
        independent_root_native_execution_count=0, author_normal_sequences=48, author_fault_sequences=24,
        root_original_BEFORE_sequences=48, root_model_checks=83423, root_model_corruption_denials=960,
        root_full_causal_model_sequences=0, independent_compiled_scenarios=132,
        independent_compiled_checks=4838, actual_hardware_pairs=264, hardware_semantic_denials=548,
        inventory_request_denials=14, new_compiled_bytes=221, new_guarded_source_bytes=269,
        full_lock_lifted=False, lock_lifted_bytes=43, lock_identity_bytes=91, total_source_identity_bytes=1856,
        whole_State_bytes=3504, whole_FX_bytes=512, whole_Runtime_CPU_bytes=40, full_pages=17,
        prior_pages_preserved=16, source_PCs=20, source_accesses=15, actual_source_CALLs=3,
        distinct_host_scheduler_stores=1, generic_Runtime_CPU_preserved=True,
        actual_malloc_CALL=0x7800107b, actual_malloc_target=0x780012b3, malloc_argument=24,
        malloc_return_word=0x78001080, terminal_ESP=0x20001810, malloc_body_or_result=False,
        lock_publication=False, locale_initialized=False, codepage_API=False, source_RET=False,
        parser_sizing_complete=False, argument_outputs=False, original_attach=False,
        full_CRT_complete=False, selected_initializers=27, total_initializer_roots=144,
        ordinary_game_launched=False, original_executed=False, whole_M4_complete=False,
        performance_comparison_made=False, seconds=(time.perf_counter_ns()-started)/1e9)
    publish_bytes(out/'report.json', (json.dumps(report, indent=2)+'\n').encode())
    print(json.dumps({k:v for k,v in report.items() if k not in ('files','archives','receipts','verified_stages','history','documents')}))


if __name__ == '__main__':
    need(len(sys.argv) == 4, 'Fixed config, external config SHA, fresh output')
    main(*sys.argv[1:])
