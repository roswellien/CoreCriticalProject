"""Admit the actual version API bridge and genuine source selector return."""
import json
import hashlib
from pathlib import Path
import sys
import time
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
BASE = ROOT/'reports/m4-crt-heap-version-root'
sys.path.insert(0, str(ROOT/'tools/m4-pipeline'))
from capture_bundle import CaptureBundle, sha_file
from manifests import normalized, unique_object, verify_manifest
from paths import publish_bytes, workspace_path
from stages import verify_stage

NAMES = {'recovery', 'source_contract', 'preparation', 'build', 'author_execution',
    'root_model', 'source_audit', 'draft_model_audit', 'model_audit', 'compiled_build',
    'compiled_native', 'hardware_review', 'independent_seal'}
CATEGORIES = ('files', 'sources', 'source_files', 'tools', 'tool_files', 'libraries',
    'entry_objects', 'matherr_objects', 'control_objects', 'initterm_objects', 'mainargs_objects',
    'normal_argv_objects', 'producer_objects', 'parser_objects', 'locale_objects', 'heap_objects',
    'heap_mode_objects', 'heap_version_objects', 'compiler_read_headers', 'artifacts', 'input_files')


def need(value, why):
    if not value: raise ValueError(why)


def read(path):
    return json.loads(Path(path).read_bytes(), object_pairs_hook=unique_object)


def main(config_path, config_sha, directory):
    started = time.perf_counter_ns(); out = workspace_path(directory, reports=True)
    need(out.parent == BASE and not out.exists(), 'Fresh acceptance output')
    files = {}
    def add(path, digest=None):
        path = Path(path).absolute(); key = normalized(str(path))
        value = sha_file(path) if digest is None else digest
        need(key not in files or files[key] == value, 'Consistent current dependency '+str(path))
        files[key] = value; return path
    config = read(add(config_path, config_sha))
    need(sha_file(config_path) == config_sha, 'External admission config digest')
    need(set(config) == {'receipts', 'pins', 'history', 'documents', 'observer_stage'}, 'Exact config schema')
    need(set(config['receipts']) == NAMES, 'All independent current proof domains')
    values = {}
    for name, item in config['receipts'].items():
        need(set(item) == {'path', 'sha256'}, 'Exact receipt identity')
        path = add(item['path'], item['sha256'])
        need(sha_file(path) == item['sha256'], 'Fixed receipt '+name)
        value = read(path); need(value['passed'] is True, 'Successful receipt '+name); values[name] = value
        for field in ('whole_M4_complete', 'original_executed', 'ordinary_game_launched',
            'game_launched', 'heap_mode_global_published', 'guest_heap_mode_global_published',
            'heap_mode_global_publication', 'heap_initialized', 'initializer_RET_executed',
            'source_initializer_RET_executed', 'heap_initializer_RET', 'environment_API_called',
            'environment_API_executed', 'original_attach_proved', 'table_initialization_proved',
            'full_heap_initialization_complete'):
            if field in value: need(value[field] is False, 'Bounded scope '+name+'/'+field)
        for category in CATEGORIES:
            for p, h in value.get(category, {}).items(): add(p, h)
    for item in config['pins']:
        path = add(item['path'], item['sha256'])
        need(sha_file(path) == item['sha256'], 'Fixed pin map')
        for p, h in read(path)['files'].items(): add(p, h)
    # Historical receipt identities are retained without reopening their closures.
    for item in config['history']+config['documents']:
        path = add(item['path'], item['sha256'])
        need(sha_file(path) == item['sha256'], 'Fixed history/document')
    def equals(name, wanted):
        for key, value in wanted.items(): need(values[name].get(key) == value, name+'/'+key)
    def digest(name): return config['receipts'][name]['sha256']
    need(values['build']['preparation_sha256'] == values['source_audit']['preparation_sha256'] == digest('preparation'),
         'Compiled and independently audited exact preparation')
    need(values['author_execution']['build_sha256'] == values['source_audit']['build_sha256'] == digest('build'),
         'Executed and independently audited exact production build')
    note = values['build']
    add(note['source_scope_note'], note['source_scope_note_sha256'])
    counts = values['recovery']['counts']
    for k, v in dict(qualifying_total_instructions=51, qualifying_total_source_accesses=31,
        qualifying_total_source_CALLs=5, qualifying_source_RETs=2, qualifying_added_executed_bytes=37,
        qualifying_total_executed_bytes=169, new_guarded_source_bytes=60, total_heap_guarded_source_bytes=230,
        total_source_identity_bytes=2086, distinct_API_return_reads=2, prior_mappings=20, total_mappings=21).items():
        need(counts[k] == v, 'Original recovered counts/'+k)
    entry = values['recovery']['query_entry_contract']
    need(entry['actual_source_query_CALL'] == 0x78003a2b and entry['source_IAT'] == 0x7802e0a0
         and entry['EIP'] == 0x34600 and entry['ESP'] == 0x20000618
         and entry['actual_return_word'] == 0x78003a31 and entry['argument_pointer'] == 0x200017b8
         and entry['structure_bytes'] == 148 and entry['structure_end_exclusive'] == 0x2000184c
         and entry['only_size_DWORD_source_initialized'] is True, 'Exact genuine source query')
    api = values['recovery']['finite_query_API_contract']
    need(api['input_bytes'] == api['output_bytes'] == 148 and api['stdcall_return_plus_argument_bytes'] == 8
         and api['declared_State_effects'] == ['EAX.low32', 'ESP.low32', 'EIP.low32']
         and api['FX_CPU_other_State_carried'] is True and api['API_executed_by_this_recovery'] is False,
         'Finite full actual API witness contract')
    ret = values['recovery']['conditional_mode1_contract']
    need(ret['selector_RET_pc'] == 0x78003a7f and ret['EIP'] == 0x780039e8
         and ret['ESP'] == 0x20001858 and ret['selector_computed_return'] == 1
         and ret['stop_before_heap_CMP39E8_and_MOV39EB'] is True
         and ret['heap_mode_global_publication'] is False, 'Genuine selector RET before caller')
    need(len(values['recovery']['alternative_contracts']) == 3
         and all(x['API_executed'] is False and x['source_CALL'] == 0x78003a5c
                 and x['source_IAT'] == 0x7802e09c for x in values['recovery']['alternative_contracts']),
         'Alternate actual-response source frontier only')
    equals('source_contract', dict(new_guarded_source_bytes=60, prior_guarded_source_bytes=86,
        combined_source_identity_bytes=2086, mode1_new_executed_source_bytes=37,
        mode1_combined_executed_source_bytes=169, mode1_combined_source_PCs=51,
        mode1_combined_source_accesses=31, mode1_original_source_CALLs=5, mode1_original_source_RETs=2,
        separate_API_return_reads=2, new_compiled_objects_expected=8, reused_guest_objects_expected=30,
        native_query_executed=False, native_executed=False))
    maps = values['source_contract']['mapping_contract']
    need(maps['total_mappings'] == 21 and maps['prior_mappings'] == 20 and maps['new_raw_RX_page'] == 0x7800c000
         and maps['Policy_and_TIB_unchanged'] is True and maps['original_guard_growth_equivalence'] is False,
         'Additional exact cold page and declared prior lower research input')
    equals('preparation', dict(source_identity_bytes=2086, reused_compiled_source_bytes=170,
        new_compiled_source_bytes=60, new_guest_objects=8, reused_guest_objects=30,
        success_executed_source_bytes=169, source_accesses=31, source_PCs=51, separate_API_return_reads=2,
        declared_API_output_DWORD_stores=37, borrowed_pages=21, prior_pages_preserved=20,
        Policy_and_TIB_unchanged=True, State_bytes=3504, FX_bytes=512, State_reseed_after_writer=False,
        Runtime_CPU_preserved=True, Runtime_call_record_added=False, scheduler_store_count=0,
        scheduler_State_projection='EIP only', OS_query_called=False, native_component_executed=False))
    equals('source_audit', dict(reused_guest_objects=30, new_guest_objects=8, unchanged_FDIV_libraries=2,
        new_guarded_source_bytes=60, mode1_executed_source_bytes=169, mode1_source_PCs=51,
        mode1_source_accesses=31, separate_API_return_reads=2, mode1_original_source_CALLs=5,
        mode1_original_source_RETs=2, borrowed_pages=21, original_stack_guard_growth_proved=False,
        original_lower_stack_bytes_equivalent=False, native_executed=False))
    equals('author_execution', dict(positive_sequences=48, causal_sequences=24, native_stages_completed=2,
        native_executed_by_author=True, actual_HeapCreate_calls=72, actual_owned_results=72,
        actual_successful_HeapDestroy_calls=72, injected_zero_result_sequences=0,
        injected_pre_OS_cleanup_skip_sequences=0, actual_GetVersionExA_calls=70,
        actual_API_output_DWORD_commits=2296, qualifying_selector_RET_sequences=50,
        alternate_environment_frontier_sequences=0, ordinary_source_PCs_if_qualifying=51,
        ordinary_source_accesses_if_qualifying=31, source_RET_count_if_qualifying=2, separate_API_return_reads=2,
        actual_full_BOOL_and_all148_output_bytes_witnessed=True, API_output_store_ledger_separate=True,
        genuine_probe_RET_executed=True, real_version_query_executed=True,
        declared_ordinary_lower_stack_input_zero=True, borrowed_pages=21, new_guest_objects=8,
        reused_guest_objects=30, API_guest_model_universal_original_equivalence_claimed=False))
    equals('root_model', dict(original_BEFORE_ordinary_sequences=48, checks=256046,
        selected_semantic_byte_corruption_denials=4176, root_full_causal_model_sequences=0,
        whole_State_bytes=3504, whole_FX_bytes=512, whole_Runtime_CPU_bytes=40, whole_pages=21,
        checkpoints_per_row=40, source_identity_bytes=2086, new_compiled_source_bytes=60,
        reused_heap_source_bytes=84, reused_selector_probe_source_bytes=86, qualifying_executed_source_bytes=169,
        qualifying_source_PCs=51, qualifying_source_accesses=31, qualifying_source_CALLs=5,
        qualifying_genuine_source_RETs=2, separate_API_return_reads=2, API_output_DWORDs_per_row=37,
        API_output_bytes_per_row=148, native_version_fields_and_BOOL_witness_drives_source=True,
        synthetic_API_response_used=False, host_source_execution_stores=0, State_projection='EIP only',
        generic_Runtime_CPU_preserved=True, ordinary_selector_RET_sequences=48, ordinary_environment_frontier_sequences=0,
        GetVersionExA_executed=True, main_initializer_count=27, independently_executed_by_root=False,
        execution_sha256=digest('author_execution'), author_expected_model_imported=False,
        AFTER_machine_state_used_as_seed=False, lower_stack_original_observed=False,
        original_guard_stack_growth_proved=False, TIB_and_Policy_changed=False))
    equals('draft_model_audit', dict(ordinary_rows=48, model_comparisons=6894, current_native_proof_bound=False,
        source_report_sha256=digest('recovery'), AFTER_machine_state_used_as_seed=False,
        author_expected_model_imported=False, hypothetical_API_response_is_native_witness=False))
    equals('model_audit', dict(ordinary_rows=48, model_comparisons=14910, current_native_proof_bound=True,
        current_native_compared=True, current_ordinary_native_rows_compared=48, current_native_checkpoints_per_row=40,
        current_phase_machine_W_R_Q_input_output_transport_sets_compared=1920,
        exact_unused_older_later_native_records_compared=1632, distinct_typed_ctor_private_owner_checks=96,
        unused_heap_create_and_heap_mode_ctor_registries_have_no_resource=True,
        actual_named_host_HeapCreate_results_witnessed=48, actual_owned_host_HeapDestroy_successes_witnessed=48,
        actual_named_GetVersionExA_results_and_full148_outputs_witnessed=48, actual_ordinary_selector_RET_sequences=48,
        actual_ordinary_environment_frontier_sequences=0, source_report_sha256=digest('recovery'),
        qualifying_source_PCs=51, qualifying_source_accesses=31, qualifying_source_CALLs=5,
        genuine_source_probe_RET=1, genuine_source_selector_RET=1, separate_API_return_reads=2,
        captured_mappings=21, AFTER_machine_state_used_as_seed=False, author_expected_model_imported=False,
        lower_stack_bytes_original_observed=False, original_stack_guard_growth_proved=False,
        TIB_and_Policy_stack_limit_changed=False, query_output_DWORD_ledger_checked_in_every_phase=True,
        complete_query20Q_and_heap16Q18Q_metadata_checked_in_every_phase=True,
        actual_native_BOOL_and_complete148_output_witness_drives_source=True, actual_version_assumed=False,
        current_fault_site=0x78003a7f, current_fault_target=0x780039e8, current_fault_reason=0))
    proof = values['model_audit']['final_root_proof']; stage = config['observer_stage']
    need(proof['execution_sha256'] == digest('author_execution') and proof['observer_sha256'] == digest('root_model')
         and proof['stage_sha256'] == stage['sha256'], 'Final independent audit binds actual root proof')
    need(verify_stage(stage['path'], stage['sha256'])['recorded_stage_passed'], 'Stable successful observer stage')
    command = read(Path(stage['path'])/'stage.json')
    need({normalized(p): h for p, h in command['artifact_sha256'].items()}.get(
         normalized(config['receipts']['root_model']['path'])) == digest('root_model'), 'Observer output association')
    for p in Path(stage['path']).iterdir():
        if p.is_file(): add(p)
    native = values['compiled_native']; hardware = values['hardware_review']; seal = values['independent_seal']
    equals('compiled_native', dict(native_scenarios=196, malformed_token_denials=40,
        counterfactual_direct_host_failure_queries=4, GetVersionExA_executed=True, synthetic_API_results=False,
        declared_lower_stack_inputs=6, probe_return_proved=True, full_causal_source_model_oracle=False))
    need(native['compiled_sha256'] == digest('compiled_build'), 'Actual independent corpus binds fixture build')
    need(hardware['native_sha256'] == digest('compiled_native'), 'Independent hardware review binds actual corpus')
    equals('hardware_review', dict(actual_hardware_pairs=396, native_scenarios=196,
        hardware_semantic_denials=548, inventory_request_denials=56, actual_HeapCreate_calls=148,
        actual_successful_HeapDestroy_calls=148, actual_integrated_GetVersionExA_calls=82,
        counterfactual_direct_host_failure_queries=4, declared_initial_lower_stack_patterns=6,
        probe_return_proved=True, validates_actual_query_native_witness=True,
        synthetic_API_results=False, alternate_query_branch_live_coverage=False))
    need(hardware['native_checks'] == native['native_checks'] > 0, 'Actual independently reviewed assertions')
    fixture = values['compiled_build']
    need(fixture['compiled_only'] is True and {normalized(p): h for p, h in fixture['sources'].items()}[
        normalized(config['receipts']['build']['path'])] == digest('build'), 'Independent fixture binds production build')
    need(len(fixture['heap_version_objects']) == 8 and len(values['build']['entry_objects']) == 38
         and len(fixture['libraries']) == len(values['build']['libraries']) == 2, 'Exact immutable COFF and library composition')
    fixture_objects = {}
    for category in CATEGORIES:
        if category.endswith('_objects'):
            for p, h in fixture.get(category, {}).items():
                key = normalized(p)
                need(key not in fixture_objects or fixture_objects[key] == h, 'Consistent fixture object identity')
                fixture_objects[key] = h
    need(fixture_objects == {normalized(p): h for p, h in values['build']['entry_objects'].items()},
         'All 38 exact fixture-to-production object paths and hashes')
    need({normalized(p): h for p, h in fixture['libraries'].items()} ==
         {normalized(p): h for p, h in values['build']['libraries'].items()}, 'Both exact production FDIV libraries')
    validate_independent_seal(seal, values, config)
    archives = []; verified_stages = []
    for kind, levels in (('author', values['author_execution']['levels']), ('independent', native['levels'])):
        need(set(levels) == {'O0', 'O2'}, 'Exact optimization levels '+kind)
        for level, info in levels.items():
            expected_worker = (values['build']['workers'][level] if kind == 'author' else
                               str(Path(config['receipts']['compiled_build']['path']).parent/level/'controls.exe'))
            need(normalized(info['worker']) == normalized(expected_worker), 'Exact compiled worker composition')
            owner = values['build'] if kind == 'author' else fixture
            worker_sha = {normalized(p): h for p, h in owner['artifacts'].items()}[normalized(info['worker'])]
            need(sha_file(info['worker']) == worker_sha, 'Native worker equals its owning build artifact')
            native_outputs = None
            for key in ('native_stage', 'pack_stage'):
                s = Path(info[key]); receipt = add(s/'stage.json'); h = sha_file(receipt)
                checked = verify_stage(s, h)
                need(checked['recorded_stage_passed'], 'Successful actual native/archive stage')
                if kind == 'independent': need(h == info[key+'_sha256'], 'Externally bound independent stage')
                command = read(receipt)
                outputs = {normalized(p): h for p, h in command['artifact_sha256'].items()}
                if key == 'native_stage':
                    need([normalized(p) for p in command['argv']] == [normalized(p) for p in info['argv']],
                         'Exact native worker request')
                    need(normalized(command['argv'][0]) == normalized(info['worker']), 'Actual isolated worker')
                    need({normalized(p): h for p, h in command['input_sha256'].items()}.get(
                         normalized(info['worker'])) == worker_sha, 'Native stage binds exact compiled worker hash')
                    native_outputs = outputs
                    need(outputs.get(normalized(str(Path(info['argv'][-1])/'COMPLETE'))) ==
                         hashlib.sha256(b'COMPLETE').hexdigest(), 'Native closed-output association')
                else:
                    need(outputs.get(normalized(info['bundle'])) == info['bundle_sha256'],
                         'Pack stage produces exactly the admitted archive')
                    expected_pack = [str(Path(sys.executable)), str(ROOT/'tools/m4-pipeline/capture_bundle.py'),
                                     'pack', info['argv'][-1], info['bundle']]
                    need(len(command['argv']) == 5 and command['argv'][2] == 'pack' and
                         [normalized(command['argv'][i]) for i in (0, 1, 3, 4)] ==
                         [normalized(expected_pack[i]) for i in (0, 1, 3, 4)], 'Exact capture pack request and source tree')
                for name in ('stdout.bin', 'stderr.bin'): add(s/name)
                verified_stages.append(dict(kind=kind, level=level, role=key, verification=checked))
            h = info['bundle_sha256']
            with CaptureBundle(add(info['bundle'], h), h) as reader:
                need(reader.read_bytes('COMPLETE') == b'COMPLETE', 'Closed strict capture')
                need(len(reader.names()) == info['logical_files'], 'Exact externally bound capture inventory')
                if kind == 'author':
                    need(info['logical_files'] == 84834, 'Exact author archive size')
                    for i in range(36):
                        result = json.loads(reader.read_bytes(f'row-{i}/result.json'), object_pairs_hook=unique_object)
                        need(type(result['passed']) is bool and result['passed'] and result['scenario'] == i
                             and result['control'] == (0 if i < 24 else i+121), 'Complete author row request')
                else:
                    result_bytes = reader.read_bytes('controls.json')
                    result = json.loads(result_bytes, object_pairs_hook=unique_object)
                    need(native_outputs.get(normalized(str(Path(info['argv'][-1])/'controls.json'))) ==
                         hashlib.sha256(result_bytes).hexdigest(), 'Native result and archive exact association')
                    need(result == info['result'] and result['passed'] is True and result['scenarios'] == 98
                         and result['malformed_token_denials'] == 20 and result['direct_host_failure_queries'] == 2
                         and result['synthetic_API_results'] is False, 'Closed independent actual request corpus')
            archives.append(dict(kind=kind, level=level, path=info['bundle'], sha256=h, logical_files=info['logical_files']))
    need(native['native_checks'] == sum(x['result']['checks'] for x in native['levels'].values()),
         'Exact native assertion aggregate')
    need(not any('/actual-o' in p.replace('\\', '/') and '/case-' in p.replace('\\', '/') for p in files),
         'Current independent evidence is strict archives, without flat capture expansion')
    for p in (Path(__file__), Path(__file__).with_name('create_config.py'),
              Path(__file__).with_name('final_check.py'), Path(sys.executable)): add(p)
    closure = verify_manifest(files); out.mkdir()
    publish_bytes(out/'pins.json', (json.dumps(dict(files=files), indent=2)+'\n').encode())
    report = dict(passed=True, scope='Actual native GetVersionExA bridge and genuine source selector RET before caller execution',
        receipts=config['receipts'], history=config['history'], documents=config['documents'], files=files,
        physical_closure=closure, pins_sha256=sha_file(out/'pins.json'), archives=archives, verified_stages=verified_stages,
        historical_receipts_expanded=False, independent_root_native_execution_count=0,
        author_normal_sequences=48, author_fault_sequences=24, root_original_BEFORE_sequences=48,
        root_model_checks=256046, root_model_corruption_denials=4176, root_full_causal_model_sequences=0,
        independent_compiled_scenarios=196, independent_compiled_checks=native['native_checks'], actual_hardware_pairs=396,
        hardware_semantic_denials=hardware['hardware_semantic_denials'], inventory_request_denials=hardware['inventory_request_denials'],
        author_actual_HeapCreate_calls=72, author_actual_successful_HeapDestroy_calls=72,
        independent_actual_HeapCreate_calls=148, independent_actual_successful_HeapDestroy_calls=148,
        author_actual_GetVersionExA_calls=70, author_actual_API_output_DWORD_commits=2296,
        author_selector_RET_sequences=50, ordinary_selector_RET_sequences=48,
        independent_actual_GetVersionExA_calls=82, independent_actual_API_output_DWORD_commits=seal['actual_output_DWORD_commits'],
        independent_selector_RET_sequences=seal['actual_selector_RETs'], counterfactual_direct_host_failure_queries=4,
        synthetic_API_results=False, alternate_query_branch_live_coverage=False,
        new_guest_objects=8, unchanged_guest_objects=30, new_guest_compiled_bytes=60,
        reused_compiled_heap_source_bytes=84, reused_compiled_selector_probe_bytes=86,
        executed_source_bytes=169, total_source_identity_bytes=2086, whole_State_bytes=3504, whole_FX_bytes=512,
        whole_Runtime_CPU_bytes=40, full_pages=21, prior_pages_preserved=20, checkpoints_per_ordinary_row=40,
        source_PCs=51, source_accesses=31, actual_source_CALLs=5, genuine_probe_RET=1, genuine_selector_RET=1,
        distinct_API_return_reads=2, separate_API_output_DWORDs=37, complete_API_input_and_output_bytes=148,
        host_guest_source_execution_stores=0, scheduler_State_projection='EIP only',
        API_return_State_projection='EAX.low32, ESP.low32, EIP.low32', generic_Runtime_CPU_preserved=True,
        terminal_EIP=0x780039e8, terminal_ESP=0x20001858, terminal_EAX=1,
        query_source_CALL=0x78003a2b, query_import=0x7802e0a0, query_struct_pointer=0x200017b8,
        only_query_size_DWORD_initialized_by_source=True, actual_version_fields_and_full_BOOL_drive_source=True,
        lower_stack_initial_input_declared=True, lower_stack_original_observed=False, original_guard_stack_growth_proved=False,
        TIB_and_Policy_changed=False, undefined_AF_universal_original_equivalence=False,
        source_AF_representatives={str(pc): 0 for pc in (0x780039bf, 0x780039d6, 0x780058db, 0x780058c5, 0x78003a31)},
        GetVersionExA_executed=True, original_API_internals_or_manifest_response_universal_equivalence=False,
        environment_API_executed=False, heap_mode_global_published=False, selector_RET=True,
        heap_initializer_RET=False, heap_initialized=False, locale_initialized=False, argument_initialization_complete=False,
        selected_initializer_roots=27, selected_initializer_inventory=144, full_CRT_complete=False,
        original_attach_proved=False, ordinary_game_launched=False, original_executed=False, whole_M4_complete=False,
        failed_initial_hardware_sample_retained=True, initial_metadata_loss_cause_proved=False,
        seconds=(time.perf_counter_ns()-started)/1e9)
    publish_bytes(out/'report.json', (json.dumps(report, indent=2)+'\n').encode())
    print(json.dumps({k: v for k, v in report.items() if k not in ('files', 'receipts', 'history', 'documents', 'archives', 'verified_stages')}))


def validate_independent_seal(seal, values, config):
    for key, wanted in dict(native_scenarios=196, actual_hardware_pairs=396, malformed_token_denials=40,
        new_guest_objects=8, reused_guest_objects=30, declared_initial_lower_stack_patterns=6,
        author_controls_per_optimization=12, independent_controls_per_optimization=80,
        counterfactual_direct_host_failure_queries=4, actual_HeapCreate_calls=148,
        actual_successful_HeapDestroy_calls=148, actual_integrated_GetVersionExA_calls=82,
        actual_output_DWORD_commits=1934, actual_selector_RETs=20, synthetic_API_results=False,
        alternate_query_branch_live_coverage=False, full_causal_source_model_oracle=False,
        original_executed=False, ordinary_game_launched=False, whole_M4_complete=False).items():
        need(seal.get(key) == wanted, 'Independent final aggregate/'+key)
    for role, name in (('source', 'source_contract'), ('audit', 'source_audit'),
                       ('native', 'compiled_native'), ('hardware', 'hardware_review')):
        item = seal['evidence'][role]; bound = config['receipts'][name]
        need(item['sha256'] == bound['sha256'] and normalized(item['path']) == normalized(bound['path']),
             'Independent final aggregate exact evidence '+role)
    for key in ('actual_HeapCreate_calls', 'actual_successful_HeapDestroy_calls',
                'actual_integrated_GetVersionExA_calls', 'hardware_semantic_denials', 'inventory_request_denials'):
        need(seal[key] == values['hardware_review'][key], 'Independent exact reviewed count '+key)
    need(seal['native_assertions'] == values['compiled_native']['native_checks'] > 0,
         'Independent aggregate assertions bind actual native corpus')


if __name__ == '__main__': main(*sys.argv[1:])
