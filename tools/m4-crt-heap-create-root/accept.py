"""Admit real HeapCreate ownership and source continuation to mode-selector entry."""
import json
from pathlib import Path
import sys
import time
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
BASE = ROOT/'reports/m4-crt-heap-create-root'
sys.path.insert(0, str(ROOT/'tools/m4-pipeline'))
from capture_bundle import CaptureBundle, sha_file
from manifests import normalized, unique_object, verify_manifest
from paths import publish_bytes, workspace_path
from stages import verify_stage

NAMES = {'recovery', 'source_contract', 'preparation', 'build', 'author_execution',
         'root_model', 'source_audit', 'model_audit', 'compiled_build', 'compiled_native',
         'hardware_review', 'caller_error_review', 'independent_seal'}
CATEGORIES = ('files', 'sources', 'source_files', 'tools', 'tool_files', 'libraries',
              'entry_objects', 'matherr_objects', 'control_objects', 'initterm_objects',
              'mainargs_objects', 'normal_argv_objects', 'producer_objects', 'parser_objects',
              'locale_objects', 'heap_objects', 'compiler_read_headers', 'artifacts', 'input_files')


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
    need(set(config['receipts']) == NAMES, 'All current proof domains')
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
    # Superseded closures can name older working sources. Anchor the immutable
    # receipts without reopening historical flat captures or old pin maps.
    for identity in config['history'] + config['documents']:
        path = add(identity['path'], identity['sha256'])
        need(sha_file(path) == identity['sha256'], 'Fixed history/document binding')

    def equals(name, assertions):
        for key, expected in assertions.items():
            need(values[name].get(key) == expected, name+'/'+key)

    build_hash = config['receipts']['build']['sha256']
    prep_hash = config['receipts']['preparation']['sha256']
    execution_hash = config['receipts']['author_execution']['sha256']
    observer_hash = config['receipts']['root_model']['sha256']
    need(values['build']['preparation_sha256'] == values['source_audit']['preparation_sha256'] == prep_hash,
         'Compiled and audited exact preparation')
    need(values['author_execution']['build_sha256'] == values['source_audit']['build_sha256'] == build_hash,
         'Executed and independently audited production build')
    equals('recovery', dict(native_executed=False, original_executed=False, API_executed=False,
        host_handle_created=False, host_guest_execution_stores=0, heap_initialized=False,
        mode_selected=False, original_attach_proved=False, whole_M4_complete=False))
    recovered = values['recovery']
    success = recovered['success_contract']
    need(success['total_source_instructions'] == 13 and success['total_source_accesses'] == 10
         and success['executed_source_bytes'] == 48 and success['compiled_guarded_source_bytes'] == 84
         and success['source_stop_site'] == 0x780039e3 and success['source_stop_target'] == 0x78003a0c
         and success['stop_before_mode_selector_body'] is True
         and success['mode_global_produced'] is False and success['source_initializer_RET_executed'] is False,
         'Original static source and bounded mode-selector CALL')
    need(recovered['API_return_bridge']['actual_source_arguments'] == [0,4096,0]
         and recovered['API_return_bridge']['declared_State_effects'] == ['EAX','ESP','EIP']
         and recovered['API_return_bridge']['guest_memory_stores'] == 0,
         'Finite declared API return contract')
    equals('source_contract', dict(completed_source_accesses_expected=10, executed_PCs_expected=13,
        actual_source_CALLs_expected=3, new_compiled_bytes=0, reused_heap_compiled_bytes=84,
        executed_prefix_bytes=48, total_source_identity_bytes=1940, native_executed=False,
        original_executed=False, API_executed=False, mode_selected=False, heap_initialized=False,
        full_CRT_complete=False, whole_M4_complete=False))
    api_contract = values['source_contract']['API_contract']
    need(api_contract['host_HANDLE_bytes'] == 8 and api_contract['opaque_guest_token'] == 0x48450001
         and api_contract['handle_truncation'] is False and api_contract['full64_handle_private_owned'] is True
         and api_contract['owned_immediately_before_throwing_observers'] is True
         and api_contract['failed_destroy_retains_ownership'] is True,
         'Reviewed full-width private resource ownership')
    equals('preparation', dict(source_identity_bytes=1940, reused_compiled_source_bytes=84,
        new_guest_objects=0, reused_guest_objects=26, success_executed_source_bytes=48,
        zero_prefix_executed_source_bytes=43, source_accesses=10, source_PCs=13,
        separate_API_return_reads=1, borrowed_pages=18, prior_pages_preserved=17,
        additional_raw_RW_page=0x78035000,
        raw_page_sha256='e26f5dc868bcd5e27e775540dc063331d45d91dc5f6863560f04b0a252e68c50',
        State_bytes=3504, FX_bytes=512, State_reseed_after_writer=False, Runtime_CPU_preserved=True,
        Runtime_call_record_added=False, scheduler_store_count=0, scheduler_State_projection='EIP only',
        token=0x48450001, private_handle_bytes=8, original_attach_executed=False,
        HeapCreate_called=False, heap_mode_selected=False, initializer_RET_executed=False,
        heap_initialized=False, locale_body_executed=False, parser_body_executed=False,
        original_executed=False, native_component_executed=False, whole_M4_complete=False))
    equals('source_audit', dict(reused_guest_objects=26, new_guest_objects=0, reused_heap_objects=4,
        unchanged_FDIV_libraries=2, compiled_guarded_heap_bytes=84, executed_success_prefix_bytes=48,
        source_PCs=13, source_accesses=10, separate_API_return_reads=1, borrowed_pages=18,
        prior_pages_preserved=17, private_HANDLE_bytes=8, guest_token=0x48450001,
        API_incoming_and_restored_LastError_reads_actual=True, undefined_AF_artifact_representative=0,
        heap_initialized=False, mode_selector_body_executed=False, original_attach_executed=False,
        original_executed=False, native_executed=False, full_causal_source_model_oracle=False))
    equals('author_execution', dict(positive_sequences=48, causal_sequences=24,
        native_executed_by_author=True, native_stages_completed=2, actual_HeapCreate_calls=70,
        actual_owned_results=70, actual_successful_HeapDestroy_calls=70,
        injected_zero_result_sequences=2, injected_pre_OS_cleanup_skip_sequences=2,
        API_guest_model_universal_original_equivalence_claimed=False, heap_mode_selected=False,
        initializer_RET_executed=False, heap_initialized=False, original_executed=False,
        game_launched=False, whole_M4_complete=False))
    equals('root_model', dict(original_BEFORE_ordinary_sequences=48, root_full_causal_model_sequences=0,
        checks=116986, selected_semantic_byte_corruption_denials=1620,
        whole_State_bytes=3504, whole_FX_bytes=512, whole_Runtime_CPU_bytes=40, whole_pages=18,
        source_identity_bytes=1940, executed_source_bytes=48, new_guest_objects=0,
        prior_guest_objects_preserved=26, source_PCs=13, source_accesses=10, actual_source_CALLs=3,
        distinct_API_return_reads=1, host_guest_stack_stores=0, State_projection='EIP only',
        generic_Runtime_CPU_preserved=True, undefined_AF_architectural_equivalence_claimed=False,
        borrowed_heap_global_page=True, HeapCreate_executed=True, host_heap_cleanup=True,
        heap_initialized=False, source_RET_executed=False, locale_executed=False, locale_initialized=False,
        parser_executed=False, argument_initialization_complete=False, original_attach_proved=False,
        main_initializer_count=27, independently_executed_by_root=False,
        execution_sha256=execution_hash, author_expected_model_imported=False,
        AFTER_machine_state_used_as_seed=False, original_executed=False,
        ordinary_game_launched=False, whole_M4_complete=False, original_x86_API_internals_equivalence=False))
    # These inherited observer field names mean the current reused 84-byte heap
    # source footprint. Preparation and COFF audit establish zero new objects.
    need(values['root_model']['new_compiled_source_bytes'] == 84
         and values['root_model']['new_guarded_source_bytes'] == 84, 'Reused guarded source identity')
    audit = values['model_audit']
    proof = audit['final_root_proof']
    need(audit['current_native_proof_bound'] is True and proof['execution_sha256'] == execution_hash
         and proof['observer_sha256'] == observer_hash, 'Independent model audit binds actual current proof')
    need(audit['source_report_sha256'] == config['receipts']['recovery']['sha256']
         and audit['ordinary_rows'] == 48 and audit['AFTER_machine_state_used_as_seed'] is False
         and audit['author_expected_model_imported'] is False
         and audit['native_or_original_or_game_executed_by_this_audit'] is False,
         'Independent source model with no candidate AFTER seed or native execution credit')
    # Exact final affine audit fields are checked in validate_model_audit below.
    validate_model_audit(audit)
    native = values['compiled_native']
    hardware = values['hardware_review']
    equals('compiled_native', dict(native_scenarios=132, native_checks=6198, malformed_token_denials=36,
        original_executed=False, ordinary_game_launched=False, HeapCreate_executed=True,
        genuine_source_token_published=True, full_heap_initialization_complete=False,
        full_causal_source_model_oracle=False, table_initialization_proved=False, whole_M4_complete=False))
    validate_hardware(hardware)
    caller_archives, caller_stages = validate_caller_error(values['caller_error_review'], add)
    seal = values['independent_seal']
    for key, wanted in dict(native_scenarios=144,native_assertions=6850,actual_hardware_pairs=288,
        actual_HeapCreate_calls=80,actual_successful_HeapDestroy_calls=80,malformed_token_denials=36,
        hardware_semantic_denials=548,inventory_API_ownership_denials=27,new_guest_objects=0,
        reused_guest_objects=26,heap_initialized=False,mode_selector_body_executed=False,
        full_causal_source_model_oracle=False,original_executed=False,ordinary_game_launched=False,
        whole_M4_complete=False).items():
        need(seal.get(key) == wanted, 'Independent aggregate seal/'+key)
    for name, role in (('source','source_contract'),('audit','source_audit'),('native','compiled_native'),
                       ('hardware','hardware_review'),('caller_error','caller_error_review')):
        need(seal['evidence'][name]['sha256'] == config['receipts'][role]['sha256']
             and normalized(seal['evidence'][name]['path']) == normalized(config['receipts'][role]['path']),
             'Aggregate independent exact evidence binding '+name)
    need(hardware['native_sha256'] == config['receipts']['compiled_native']['sha256'], 'Hardware review binds actual native corpus')
    need(native['compiled_sha256'] == config['receipts']['compiled_build']['sha256'], 'Native corpus binds fixture build')
    fixture = values['compiled_build']
    fixture_sources = {normalized(str(Path(p).absolute())):h for p,h in fixture['sources'].items()}
    need(fixture['compiled_only'] is True and fixture_sources[normalized(config['receipts']['build']['path'])] == build_hash,
         'Independent compile-only fixture binds production build')

    observer_stage = config['observer_stage']
    need(proof['stage_sha256'] == observer_stage['sha256'], 'Independent audit binds observer stage')
    need(verify_stage(observer_stage['path'], observer_stage['sha256'])['recorded_stage_passed'], 'Successful stable observer stage')
    recorded = read(Path(observer_stage['path'])/'stage.json')
    need({normalized(p):h for p,h in recorded['artifact_sha256'].items()}[normalized(config['receipts']['root_model']['path'])] == observer_hash,
         'Completed observer output association')
    for path in Path(observer_stage['path']).iterdir():
        if path.is_file():
            add(path)
    archives, verified_stages = caller_archives, caller_stages
    for kind, levels in (('author', values['author_execution']['levels']), ('independent', native['levels'])):
        need(set(levels) == {'O0', 'O2'}, 'Exact optimization levels '+kind)
        for level, info in levels.items():
            for key in ('native_stage', 'pack_stage'):
                stage = Path(info[key])
                receipt = add(stage/'stage.json')
                checked = verify_stage(stage, sha_file(receipt))
                need(checked['recorded_stage_passed'], 'Completed native/archive stage '+kind+'/'+level+'/'+key)
                if kind == 'independent':
                    need(sha_file(receipt) == info[key+'_sha256'], 'Fixed independent stage identity')
                command = read(receipt)
                if key == 'native_stage':
                    need([normalized(p) for p in command['argv']] == [normalized(p) for p in info['argv']], 'Exact direct native request')
                    need(normalized(command['argv'][0]) == normalized(info['worker']), 'Actual isolated worker')
                for name in ('stdout.bin', 'stderr.bin'):
                    add(stage/name)
                verified_stages.append(dict(kind=kind, level=level, role=key, verification=checked))
            digest = info['bundle_sha256']
            with CaptureBundle(add(info['bundle'], digest), digest) as reader:
                need(reader.read_bytes('COMPLETE') == b'COMPLETE', 'Closed capture writer')
                need(len(reader.names()) == info['logical_files'] == (51626 if kind == 'author' else 72083), 'Exact strict archive inventory')
                if kind == 'independent':
                    completed = json.loads(reader.read_bytes('controls.json'), object_pairs_hook=unique_object)
                    need(completed == info['result'] and completed['passed'] is True and completed['scenarios'] == 66
                         and completed['checks'] == 3099 and completed['malformed_token_denials'] == 18, 'Closed independent native corpus')
            archives.append(dict(kind=kind, level=level, path=info['bundle'], sha256=digest, logical_files=info['logical_files']))
    need(not any('/actual-o' in p.replace('\\','/') and '/case-' in p.replace('\\','/') for p in files), 'Sealed independent captures only')
    for path in (Path(__file__), Path(__file__).with_name('create_config.py'),
                 Path(__file__).with_name('final_check.py'), Path(sys.executable)):
        add(path)
    closure = verify_manifest(files)
    out.mkdir()
    publish_bytes(out/'pins.json', (json.dumps(dict(files=files), indent=2)+'\n').encode())
    report = dict(passed=True, scope='Actual host HeapCreate, full-width ownership, finite guest API return, original token publication and genuine mode-selector CALL',
        receipts=config['receipts'], history=config['history'], documents=config['documents'], files=files,
        physical_closure=closure, pins_sha256=sha_file(out/'pins.json'), archives=archives, verified_stages=verified_stages,
        historical_receipts_expanded=False, native_executor='Delegated author and independent reviewer; root compares and seals evidence',
        independent_root_native_execution_count=0, author_normal_sequences=48, author_fault_sequences=24,
        root_original_BEFORE_sequences=48, root_model_checks=116986, root_model_corruption_denials=1620,
        root_full_causal_model_sequences=0, independent_compiled_scenarios=132, independent_compiled_checks=6198,
        actual_hardware_pairs=hardware['actual_hardware_pairs'], hardware_semantic_denials=hardware['hardware_semantic_denials'],
        inventory_request_denials=hardware['inventory_request_denials'],
        reused_compiled_source_bytes=84, new_guest_compiled_bytes=0, new_guest_objects=0,
        executed_source_bytes=48, total_source_identity_bytes=1940, unchanged_guest_objects=26,
        whole_State_bytes=3504, whole_FX_bytes=512, whole_Runtime_CPU_bytes=40, full_pages=18,
        prior_pages_preserved=17, additional_mappings=1, source_PCs=13, source_accesses=10,
        actual_source_CALLs=3, distinct_API_return_reads=1, host_guest_stack_stores=0,
        State_projection='EIP only', generic_Runtime_CPU_preserved=True,
        undefined_AF_universal_equivalence=False, source_AF_representatives={str(pc):0 for pc in (0x780039bf,0x780039d6)},
        actual_HeapCreate_CALL=0x780039d0, import_slot=0x7802e0a8, API_arguments=[0,4096,0],
        terminal_EIP=0x78003a0c, terminal_ESP=0x20001854, source_mode_return_word=0x780039e8,
        opaque_guest_token=0x48450001, private_handle_bytes=8, bounded_registry_slots=1,
        author_actual_HeapCreate_calls=70, author_actual_successful_HeapDestroy_calls=70,
        independent_actual_HeapCreate_calls=70, independent_actual_successful_HeapDestroy_calls=70,
        separate_nonzero_caller_error_scenarios=12, separate_caller_error_hardware_pairs=24,
        separate_caller_error_actual_HeapCreate_calls=10, separate_caller_error_successful_HeapDestroy_calls=10,
        HeapCreate_API_executed=True, heap_handle_published_by_source=True, host_heap_cleanup=True,
        guest_token_valid_after_cleanup=False, original_x86_API_internals_equivalence=False,
        injected_zero_is_actual_Windows_failure=False, injected_cleanup_skip_is_actual_HeapDestroy_failure=False,
        source_mode_selector_body=False, heap_mode_selected=False, heap_initialized=False,
        allocator_result=False, initializer_RET=False, locale_initialized=False, parser_sizing_complete=False,
        argument_outputs=False, original_attach=False, full_CRT_complete=False,
        selected_initializers=27, total_initializer_roots=144, ordinary_game_launched=False,
        original_executed=False, whole_M4_complete=False, performance_comparison_made=False,
        seconds=(time.perf_counter_ns()-started)/1e9)
    publish_bytes(out/'report.json', (json.dumps(report, indent=2)+'\n').encode())
    print(json.dumps({k:v for k,v in report.items() if k not in ('files','archives','receipts','verified_stages','history','documents')}))


def validate_model_audit(audit):
    expected = dict(schema='mw34-m4-heap-create-root-final-audit-v1', ordinary_rows=48,
        model_comparisons=9024,preserved_draft_static_token_formula_controls=10,
        current_ordinary_native_rows_compared=48,current_native_checkpoints_per_row=31,
        current_phase_machine_and_W_R_metadata_pairs_compared=1488,
        exact_unused_older_later_native_records_compared=912,
        full_frozen_mainargs_before_crosscheck=True,stopping_subclass_used_as_expected_seed=False,
        independent_affine_source_ledger=True,whole_State_bytes=3504,whole_FX_bytes=512,
        whole_Runtime_CPU_bytes=40,captured_mappings=18,prior_mappings_preserved=17,
        new_raw_RW_page=0x78035000,
        new_raw_RW_page_sha256='e26f5dc868bcd5e27e775540dc063331d45d91dc5f6863560f04b0a252e68c50',
        semantic_memory_aliases_preserved=True,semantic_aliases_counted_as_extra_mappings=False,
        actual_source_PCs=13,actual_source_accesses=10,actual_source_CALLs=3,separate_API_return_reads=1,
        separate_API_return_log_context_PC=0x780039d0,separate_API_return_incoming_State_EIP=0x3461e,
        source_identity_compiled_guarded_bytes=84,source_identity_executed_bytes=48,
        host_scheduler_changes_only=['State.EIP'],host_guest_execution_stores=0,
        declared_API_return_changes_only=['State.EAX.low32','State.ESP.low32','State.EIP.low32'],
        generic_Runtime_CPU_and_call_records_preserved=True,original_x86_API_internals_equivalence=False,
        original_volatile_register_or_flag_equivalence=False,declared_token=0x48450001,
        root_predicted_API_executed_flag_is_draft_hypothesis=False,
        actual_native_API_result_bound_to_full_width_registry=True,
        handle_publication_phase_PC=0x780039d8,publication_snapshot_at_source_write_before_PC_advance=True,
        raw_heap_page_only_source_handle_DWORD_changed=True,source_CALL_store_precedes_ESP_publication=True,
        source_IAT_read_precedes_API_CALL_return_store=True,source_return_bridge_read_precedes_State_publication=True,
        declared_AF_representatives=[dict(pc=0x780039bf,value=0),dict(pc=0x780039d6,value=0)],
        undefined_AF_universal_original_equivalence=False,current_native_proof_bound=True,
        current_native_compared=True,HeapCreate_executed=False,
        actual_named_host_HeapCreate_results_witnessed=48,actual_owned_host_HeapDestroy_successes_witnessed=48,
        host_handle_created_by_this_audit=False,heap_initialized=False,mode_selected=False,
        source_initializer_RET_executed=False,original_attach_proved=False,
        root_full_causal_model_audited=False,whole_M4_complete=False)
    for key, wanted in expected.items():
        need(audit.get(key) == wanted, 'Independent complete affine audit/'+key)
    need(audit['final_root_proof']['independent_root_native_execution_credit'] is False,
         'Actual delegated evidence grants no additional root native run')


def validate_hardware(value):
    expected = dict(native_scenarios=132, native_checks=6198, actual_hardware_pairs=264,
        hardware_semantic_denials=548, inventory_request_denials=27, actual_HeapCreate_calls=70,
        actual_successful_HeapDestroy_calls=70, full_causal_source_model_oracle=False,
        native_executed=False, original_executed=False, HeapCreate_executed=False,
        validates_actual_heap_ownership=True, heap_initialized=False, table_initialization_proved=False,
        whole_M4_complete=False)
    for key, wanted in expected.items():
        need(value.get(key) == wanted, 'Independent hardware/inventory/'+key)


def validate_caller_error(value, add):
    for key, wanted in dict(native_scenarios=12, native_checks=652, actual_hardware_pairs=24,
        actual_HeapCreate_calls=10, actual_successful_HeapDestroy_calls=10,
        incoming_nonzero_error_prefix=0xbeef0000, source_or_candidate_changed=False,
        original_executed=False, ordinary_game_launched=False, heap_initialized=False,
        full_causal_source_model_oracle=False, whole_M4_complete=False).items():
        need(value.get(key) == wanted, 'Separate actual nonzero caller-error proof/'+key)
    need(value['requests'] == [0,0,121,122,132,39], 'Exact separate fixture requests')
    need(set(value['levels']) == {'O0','O2'}, 'Both nonzero-error fixture levels')
    compiled = add(value['compiled_path'], value['compiled_sha256'])
    need(sha_file(compiled) == value['compiled_sha256'] and read(compiled)['compiled_only'] is True,
         'Actual separate fixture compilation')
    archives, stages = [], []
    for level, info in value['levels'].items():
        for key in ('native_stage','pack_stage'):
            stage = Path(info[key])
            need(verify_stage(stage, info[key+'_sha256'])['recorded_stage_passed'], 'Actual separate '+key)
            receipt = add(stage/'stage.json', info[key+'_sha256'])
            if key == 'native_stage':
                need(read(receipt)['argv'] == info['argv'] and info['argv'][0] == info['worker'], 'Actual separate direct worker request')
            for name in ('stdout.bin','stderr.bin'):
                add(stage/name)
            stages.append(dict(kind='caller_error', level=level, role=key, sha256=info[key+'_sha256']))
        need(sha_file(add(info['worker'],info['worker_sha256'])) == info['worker_sha256'], 'Actual separate worker hash')
        with CaptureBundle(add(info['bundle'],info['bundle_sha256']),info['bundle_sha256']) as bundle:
            need(bundle.read_bytes('COMPLETE') == b'COMPLETE' and len(bundle.names()) == info['logical_files'] == 7328, 'Closed complete separate archive')
            result = json.loads(bundle.read_bytes('controls.json'),object_pairs_hook=unique_object)
            need(result == info['result'] and result['passed'] is True and result['scenarios'] == 6
                 and result['checks'] == 326 and result['malformed_token_denials'] == 0, 'Exact separate native assertions')
            import struct
            for number, mode in enumerate(value['requests'],1):
                witness = struct.unpack('<16Q',bundle.read_bytes(f'case-{number}/heap-witness.bin'))
                need(witness[8] == witness[10] == 0xbeef0000+number
                     and witness[:6] == (1,int(mode==121),int(mode!=121),0,4096,0),
                     'Actually measured nonzero incoming/restored LastError and explicit zero provenance')
        archives.append(dict(kind='caller_error',level=level,path=info['bundle'],sha256=info['bundle_sha256'],logical_files=info['logical_files']))
    need(sum(info['result']['checks'] for info in value['levels'].values()) == value['native_checks'], 'Actual separate assertion count')
    return archives, stages


if __name__ == '__main__':
    need(len(sys.argv) == 4, 'Fixed config, external SHA, fresh output')
    main(*sys.argv[1:])
