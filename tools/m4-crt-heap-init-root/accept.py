"""Admit the bounded original heap caller/initializer to HeapCreate refusal."""
import json
from pathlib import Path
import sys
import time
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
BASE = ROOT / 'reports/m4-crt-heap-init-root'
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
    # Historical closures may refer to superseded working sources. Their fixed
    # receipts are anchors only and do not reopen old flat captures.
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
    need(values['build']['preparation_sha256'] == prep_hash, 'Build binds preparation')
    need(values['author_execution']['build_sha256'] == values['source_audit']['build_sha256'] == build_hash,
         'Executed and independently audited production build identity')
    need(values['source_audit']['preparation_sha256'] == prep_hash and
         values['source_audit']['preparation_pins_sha256'] ==
         '7d1f78976273ec242b3bfbdabc66d5906d983d286a2f921bb9846579f65dec1c', 'Exact reviewed preparation closure')
    equals('recovery', dict(executed_source_instruction_count=9, successful_source_memory_accesses=8,
        native_executed=False, original_executed=False, API_executed=False, initialized_heap_proved=False,
        locale_initialized=False, parser_sizing_completed=False, whole_M4_complete=False))
    equals('source_contract', dict(completed_source_accesses_expected=8, executed_PCs_expected=9,
        actual_source_CALLs_expected=2, new_compiled_bytes=84, executed_prefix_bytes=30,
        new_source_identity_bytes=84, total_source_identity_bytes=1940, native_executed=False,
        original_executed=False, HeapCreate_executed=False, heap_handle_published=False,
        heap_mode_selected=False, heap_initialized=False, locale_initialized=False, whole_M4_complete=False))
    equals('preparation', dict(source_identity_bytes=1940, compiled_new_source_bytes=84,
        source_accesses=8, source_PCs=9, borrowed_pages=17, prior_pages_preserved=17,
        State_bytes=3504, FX_bytes=512, State_reseed_after_writer=False, Runtime_CPU_preserved=True,
        Runtime_call_record_added=False, scheduler_store_count=0, original_attach_executed=False,
        HeapCreate_called=False, heap_initialized=False, locale_body_executed=False,
        parser_body_executed=False, original_executed=False, native_component_executed=False, whole_M4_complete=False))
    equals('source_audit', dict(unchanged_guest_objects=22, new_guest_objects=4,
        unchanged_FDIV_libraries=2, compiled_source_bytes=84, executed_prefix_bytes=30,
        heap_source_identity_bytes=84, total_source_identity_bytes=1940, Runtime_CPU_preserved=True,
        Runtime_call_record_added=False, State_reseed_after_writer=False, original_executed=False,
        native_executed=False, HeapCreate_executed=False, heap_initialized=False, heap_handle_published=False,
        source_artifact_undefined_AF_representative=0, table_initialization_proved=False, whole_M4_complete=False))
    equals('author_execution', dict(positive_sequences=48, causal_sequences=24,
        native_executed_by_author=True, native_stages_completed=2,
        original_executed=False, game_launched=False, whole_M4_complete=False))
    equals('root_model', dict(original_BEFORE_ordinary_sequences=48, root_full_causal_model_sequences=0,
        checks=81977, selected_semantic_byte_corruption_denials=840,
        whole_State_bytes=3504, whole_FX_bytes=512, whole_Runtime_CPU_bytes=40, whole_pages=17,
        source_identity_bytes=1940, new_compiled_source_bytes=84, new_guarded_source_bytes=84,
        source_PCs=9, source_accesses=8, actual_source_CALLs=2, host_guest_stack_stores=0,
        State_projection='EIP only', generic_Runtime_CPU_preserved=True,
        undefined_AF_architectural_equivalence_claimed=False, defined_final_arithmetic_flags='CMP1-0: all6zero',
        borrowed_heap_global_page=False, HeapCreate_executed=False, heap_initialized=False,
        source_RET_executed=False, locale_executed=False, locale_initialized=False,
        parser_executed=False, argument_initialization_complete=False, original_attach_proved=False,
        main_initializer_count=27, independently_executed_by_root=False,
        execution_sha256=execution_hash, author_expected_model_imported=False,
        AFTER_machine_state_used_as_seed=False, original_executed=False,
        ordinary_game_launched=False, whole_M4_complete=False))
    audit = values['model_audit']
    proof = audit['final_root_proof']
    need(audit['current_native_proof_bound'] is True and proof['execution_sha256'] == execution_hash
         and proof['observer_sha256'] == observer_hash, 'Independent model audit binds actual current evidence')
    equals('model_audit', dict(ordinary_rows=48, full_frozen_mainargs_before_crosscheck=True,
        source_report_sha256=config['receipts']['recovery']['sha256'], model_comparisons=6672,
        new_source_identity_bytes=84, current_native_checkpoints_per_row=27,
        declared_undefined_AF_representative=dict(pc=0x780039BF, value=0, universal_original_AF_equivalence=False),
        final_defined_arithmetic_flags=dict(pc=0x780039C3, CF=0, PF=0, AF=0, ZF=0, SF=0, OF=0),
        stopping_subclass_used_as_expected_seed=False, independent_affine_source_ledger=True,
        whole_State_bytes=3504, whole_FX_bytes=512, whole_Runtime_CPU_bytes=40,
        prior_mappings=17, additional_mappings=0, State_EIP_only_scheduler=True,
        host_guest_memory_stores=0, actual_source_PCs=9, actual_source_accesses=8, actual_source_CALLs=2,
        source_checked_store_precedes_ESP_publication=True, source_IAT_read_precedes_CALL_return_store=True,
        AFTER_machine_state_used_as_seed=False, author_expected_model_imported=False,
        root_full_causal_model_audited=False, native_or_original_or_game_executed_by_this_audit=False,
        HeapCreate_executed=False, heap_initialized=False, original_GetVersion_or_attach_proved=False,
        locale_initialized=False, whole_M4_complete=False))
    need(proof['ordinary_current_native_rows_compared'] == 48 and
         proof['exact_unused_later_native_records_compared'] == 672 and
         proof['independent_root_execution_credit'] is False, 'Complete bounded independent native comparison')
    native = values['compiled_native']
    hardware = values['hardware_review']
    equals('compiled_native', dict(native_scenarios=132, malformed_token_denials=50,
        original_executed=False, ordinary_game_launched=False, HeapCreate_executed=False,
        heap_initialized=False, heap_handle_published=False, table_initialization_proved=False, whole_M4_complete=False))
    equals('hardware_review', dict(native_scenarios=132, actual_hardware_pairs=264,
        hardware_semantic_denials=548, inventory_request_denials=14, native_executed=False,
        original_executed=False, HeapCreate_executed=False, heap_initialized=False,
        table_initialization_proved=False, whole_M4_complete=False))
    need(native['native_checks'] == hardware['native_checks'] == 5034, 'Actual independent compiled assertions')
    need(hardware['native_sha256'] == config['receipts']['compiled_native']['sha256'], 'Hardware review binds native corpus')
    need(native['compiled_sha256'] == config['receipts']['compiled_build']['sha256'], 'Native corpus binds fixture build')
    fixture = values['compiled_build']
    fixture_sources = {normalized(str(Path(p).absolute())):h for p,h in fixture['sources'].items()}
    need(fixture['compiled_only'] is True and fixture_sources[normalized(config['receipts']['build']['path'])] == build_hash,
         'Compile-only fixture binds frozen production build')

    observer_stage = config['observer_stage']
    need(proof['stage_sha256'] == observer_stage['sha256'], 'Independent audit binds observer stage')
    need(verify_stage(observer_stage['path'], observer_stage['sha256'])['recorded_stage_passed'], 'Stable successful observer stage')
    recorded = read(Path(observer_stage['path'])/'stage.json')
    need({normalized(p):h for p,h in recorded['artifact_sha256'].items()}[normalized(config['receipts']['root_model']['path'])] == observer_hash,
         'Actual completed observer output')
    for path in Path(observer_stage['path']).iterdir():
        if path.is_file():
            add(path)
    archives, verified_stages = [], []
    for kind, levels in (('author', values['author_execution']['levels']), ('independent', native['levels'])):
        need(set(levels) == {'O0', 'O2'}, 'Both exact optimization levels '+kind)
        for level, info in levels.items():
            for key in ('native_stage', 'pack_stage'):
                stage = Path(info[key])
                receipt = add(stage/'stage.json')
                checked = verify_stage(stage, sha_file(receipt))
                need(checked['recorded_stage_passed'], 'Completed native/archive stage '+kind+'/'+level+'/'+key)
                if kind == 'independent':
                    need(sha_file(receipt) == info[key+'_sha256'], 'External independent stage identity')
                command = read(receipt)
                if key == 'native_stage':
                    need([normalized(p) for p in command['argv']] == [normalized(p) for p in info['argv']], 'Direct native request matches receipt')
                    need(normalized(command['argv'][0]) == normalized(info['worker']), 'Actual isolated worker')
                for name in ('stdout.bin', 'stderr.bin'):
                    add(stage/name)
                verified_stages.append(dict(kind=kind, level=level, role=key, verification=checked))
            digest = info['bundle_sha256']
            with CaptureBundle(add(info['bundle'], digest), digest) as reader:
                need(reader.read_bytes('COMPLETE') == b'COMPLETE', 'Closed capture writer')
                need(len(reader.names()) == info['logical_files'], 'Complete strict archive inventory')
                if kind == 'author':
                    need(info['logical_files'] == 42120, 'Exact author inventory')
                else:
                    need(info['logical_files'] == 61868, 'Exact independent capture inventory')
                    completed = json.loads(reader.read_bytes('controls.json'), object_pairs_hook=unique_object)
                    need(completed == info['result'] and completed['passed'] is True and completed['scenarios'] == 66
                         and completed['checks'] == 2517 and completed['malformed_token_denials'] == 25, 'Closed independent native corpus')
            archives.append(dict(kind=kind, level=level, path=info['bundle'], sha256=digest, logical_files=info['logical_files']))
    need(not any('/actual-o' in p.replace('\\','/') and '/case-' in p.replace('\\','/') for p in files), 'Sealed independent captures')
    for path in (Path(__file__), Path(__file__).with_name('create_config.py'), Path(sys.executable)):
        add(path)
    closure = verify_manifest(files)
    out.mkdir()
    publish_bytes(out/'pins.json', (json.dumps(dict(files=files), indent=2)+'\n').encode())
    report = dict(passed=True, scope='Original caller and heap initializer prefix through unresolved first HeapCreate CALL',
        receipts=config['receipts'], history=config['history'], documents=config['documents'], files=files,
        physical_closure=closure, pins_sha256=sha_file(out/'pins.json'), archives=archives, verified_stages=verified_stages,
        historical_receipts_expanded=False, native_executor='Delegated author and independent reviewer; root compares and seals evidence',
        independent_root_native_execution_count=0, author_normal_sequences=48, author_fault_sequences=24,
        root_original_BEFORE_sequences=48, root_model_checks=81977, root_model_corruption_denials=840,
        root_full_causal_model_sequences=0, independent_compiled_scenarios=132, independent_compiled_checks=5034,
        actual_hardware_pairs=264, hardware_semantic_denials=548, inventory_request_denials=14,
        new_compiled_bytes=84, new_guarded_source_bytes=84, new_executed_prefix_bytes=30,
        total_source_identity_bytes=1940, unchanged_guest_objects=22, new_guest_objects=4,
        whole_State_bytes=3504, whole_FX_bytes=512, whole_Runtime_CPU_bytes=40, full_pages=17,
        prior_pages_preserved=17, additional_mappings=0, source_PCs=9, source_accesses=8, actual_source_CALLs=2,
        host_guest_stack_stores=0, State_projection='EIP only', generic_Runtime_CPU_preserved=True,
        undefined_AF_universal_equivalence=False, XOR_AF_generated_representative=0,
        actual_HeapCreate_CALL=0x780039D0, import_slot=0x7802E0A8, terminal_EIP=0x3461E,
        terminal_ESP=0x20001848, API_return_word=0x780039D6, API_arguments=[0,4096,0],
        HeapCreate_API_executed=False, API_result=False, heap_handle_published=False, heap_mode_selected=False,
        heap_initialized=False, allocator_result=False, initializer_RET=False, locale_initialized=False,
        parser_sizing_complete=False, argument_outputs=False, original_attach=False, full_CRT_complete=False,
        selected_initializers=27, total_initializer_roots=144, ordinary_game_launched=False,
        original_executed=False, whole_M4_complete=False, performance_comparison_made=False,
        seconds=(time.perf_counter_ns()-started)/1e9)
    publish_bytes(out/'report.json', (json.dumps(report, indent=2)+'\n').encode())
    print(json.dumps({k:v for k,v in report.items() if k not in ('files','archives','receipts','verified_stages','history','documents')}))


if __name__ == '__main__':
    need(len(sys.argv) == 4, 'Fixed config, external SHA, fresh output')
    main(*sys.argv[1:])
