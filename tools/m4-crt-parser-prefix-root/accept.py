"""Seal the current bounded parser evidence without expanding historical captures."""
import json
from pathlib import Path
import subprocess
import sys
import time
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
from capture_bundle import CaptureBundle, sha_file
from manifests import normalized, unique_object, verify_manifest
from paths import publish_bytes, workspace_path
from stages import verify_stage

BASE = ROOT / 'reports/m4-crt-parser-prefix'
NAMES = {'preparation', 'build', 'root_execution', 'root_model', 'source_audit',
         'model_audit', 'compiled_build', 'compiled_review', 'hardware_review',
         'bundle_preparation', 'bundle_review', 'bundle_root_check'}
CATEGORIES = ('files', 'sources', 'source_files', 'tools', 'tool_files', 'libraries',
              'entry_objects', 'matherr_objects', 'control_objects', 'initterm_objects',
              'mainargs_objects', 'normal_argv_objects', 'producer_objects',
              'parser_objects', 'compiler_read_headers', 'artifacts', 'input_files')


def need(ok, why):
    if not ok:
        raise ValueError(why)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique_object)


def main(config_path, config_sha, directory):
    started = time.perf_counter_ns()
    out = workspace_path(directory, reports=True)
    need(out.parent == BASE and not out.exists(), 'Fresh root acceptance output required')
    files = {}

    def add(path, digest=None):
        path = Path(path).absolute()
        key = normalized(str(path))
        value = sha_file(path) if digest is None else digest
        need(key not in files or files[key] == value, 'Conflicting current physical dependency: ' + str(path))
        files[key] = value
        return path

    config_path = add(config_path, config_sha)
    need(sha_file(config_path) == config_sha, 'Externally fixed admission config')
    config = read(config_path)
    need(set(config) == {'receipts', 'pins', 'history', 'documents', 'observer_stage'}, 'Exact admission schema')
    need(set(config['receipts']) == NAMES, 'All required current evidence domains')
    values = {}
    for name, identity in config['receipts'].items():
        need(set(identity) == {'path', 'sha256'}, 'Exact receipt binding')
        path = add(identity['path'], identity['sha256'])
        need(sha_file(path) == identity['sha256'], 'Fixed current receipt: ' + name)
        value = read(path)
        need(value['passed'] is True, 'Successful current receipt: ' + name)
        values[name] = value
        for category in CATEGORIES:
            for p, h in value.get(category, {}).items():
                add(p, h)
    for identity in config['pins']:
        path = add(identity['path'], identity['sha256'])
        need(sha_file(path) == identity['sha256'], 'Fixed current explicit pin map')
        for p, h in read(path)['files'].items():
            add(p, h)
    for identity in config['history']:
        path = add(identity['path'], identity['sha256'])
        need(sha_file(path) == identity['sha256'], 'Preserved historical receipt')
        # Historical receipts are fixed anchors, never recursively expanded.
    for identity in config['documents']:
        path = add(identity['path'], identity['sha256'])
        need(sha_file(path) == identity['sha256'], 'Current review document')

    def equals(name, assertions):
        for key, expected in assertions.items():
            need(values[name].get(key) == expected, name + '/' + key)

    build_hash = config['receipts']['build']['sha256']
    need(values['root_execution']['build_sha256'] == values['source_audit']['build_sha256'] == build_hash,
         'Execution/source review bind exact production build')
    need(values['build']['preparation_sha256'] == config['receipts']['preparation']['sha256'],
         'Exact current prepared source')
    need(values['source_audit']['preparation_pins_sha256'] ==
         '5502f44033b0215da34b3542da40c00d0d52b56361a0f1c82d30b7307e9dcd41',
         'Current preparation disambiguates identical static recovery report')
    equals('root_execution', dict(positive_sequences=48, causal_sequences=24,
        native_stages_completed=2, native_executed_by_root=True, original_executed=False,
        game_launched=False, whole_M4_complete=False))
    equals('root_model', dict(checks=146113, independently_modeled_ordinary_sequences=48,
        standard_causal_sequences_independently_modeled_by_root=0,
        selected_semantic_byte_corruption_denials=2648, State_bytes=3504, FX_bytes=512,
        borrowed_pages=16, source_identity_bytes=1587, parser_source_bytes=436,
        parser_body_executed=True, locale_read_completed=False, parser_RET_executed=False,
        parser_sizing_complete=False, argument_initialization_complete=False,
        State_reseed=False, main_initializer_count=27, whole_M4_complete=False))
    equals('source_audit', dict(unchanged_guest_COFF_objects=14, unchanged_FDIV_libraries=2,
        reused_complete_parser_COFF_objects=2, actual_named_State_types_checked=34,
        completed_generated_memory_accesses=16, required_unperformed_read_ordinal=17,
        prefix_PC_count_including_unperformed_table_read=23, source_stop_PC=0x7800bce6,
        source_required_byte_address=0x78037a25, locale_table_initialization_proved=False,
        original_executed=False, native_worker_executed=False, whole_M4_complete=False))
    audit = values['model_audit']
    need(audit['root_proof_sha256'] == config['receipts']['root_model']['sha256'] and
         audit['root_execution_sha256'] == config['receipts']['root_execution']['sha256'],
         'Independent root-model audit binds exact execution and oracle')
    equals('compiled_review', dict(scenarios=132, malformed_token_denials=54,
        direct_host_records=264, nonzero_complete_legacy_metadata_records=264,
        original_executed=False, ordinary_game_launched=False, whole_M4_complete=False))
    need(type(values['compiled_review']['checks']) is int and values['compiled_review']['checks'] > 4000,
         'Actual substantial compiled assertions')
    equals('hardware_review', dict(actual_hardware_raw80_before_fixtures=264,
        actual_complete_legacy_tag_before_fixtures=264, meaningful_corruption_denials=548,
        independent_inventory_request_denials=14, new_native_executions=False,
        guest_result_inferred_from_AFTER=False, whole_M4_complete=False))
    fixture_identity = config['receipts']['compiled_build']
    need(Path(values['compiled_review']['build_path']).absolute() == Path(fixture_identity['path']).absolute(),
         'Compiled review uses exact admitted fixture build')
    need(sha_file(values['hardware_review']['publication_stage']['build_path']) == fixture_identity['sha256'],
         'Hardware review uses exact admitted fixture build')
    stage = values['compiled_review']['publication_stage']
    need(stage == values['hardware_review']['publication_stage'] and stage['passed'] is True and
         stage['build_sha256'] == fixture_identity['sha256'] and stage['source_watch_rechecked'] is True,
         'Both reviews bind completed archive publication')
    fixture = values['compiled_build']
    need(fixture['sources'][normalized(str(Path(config['receipts']['build']['path']).absolute()))] == build_hash,
         'Independently authored fixture uses current production build')
    for level in ('O0', 'O2'):
        directory = Path(fixture_identity['path']).parent / level
        command = read(add(directory / 'native-command.json'))
        expected_argv = [str(directory / 'controls.exe'), str(ROOT / 'MW3/Mech3.exe'),
            str(ROOT / f'reports/m4-crt-fdiv-entry-prefix/preparation-r2/candidate-{level}.obj'),
            str(ROOT / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'),
            str(ROOT / 'reports/m4-crt-fdiv/native-derived-r1/pack.bin'),
            str(ROOT / 'reports/m4-crt-fdiv-replay/preparation-r1/before-inputs.bin'),
            str(directory / 'actual')]
        need([normalized(p) for p in command['argv']] == [normalized(p) for p in expected_argv]
             and command['exit_code'] == 0 and command['direct_argv'] is True
             and command['worker_unchanged'] is True and command['original_executed'] is False
             and command['ordinary_game_launched'] is False, 'Actual isolated fixture command')
        need(command['command_line'] == subprocess.list2cmdline(command['argv']) and
             command['command_line'][0] == 'D' and command['monotonic_start_ns'] <= command['monotonic_end_ns'] and
             command['duration_seconds'] == (command['monotonic_end_ns']-command['monotonic_start_ns'])/1e9,
             'Honest direct command and monotonic timing')
        need(normalized(command['worker_path']) == normalized(expected_argv[0]) and
             normalized(command['stdout_path']) == normalized(str(directory/'controls.log')),
             'Exact per-level worker and child log paths')
        add(command['worker_path'], command['worker_sha256'])
        add(command['stdout_path'], command['stdout_sha256'])
    equals('bundle_preparation', dict(logical_files=130064, new_native_executions=False,
        flat_captures_modified=False, whole_M4_complete=False))
    equals('bundle_review', dict(complete_equivalent_logical_files=130064, direct_host_records=264,
        meaningful_semantic_corruption_denials=548, warm_repetitions_per_backend=5,
        metadata_only_cache_used=False, new_native_executions=False, whole_project_speedup_claimed=False))
    equals('bundle_root_check', dict(equivalent_logical_files=130064, actual_hardware_pairs_preserved=264,
        unchanged_hardware_semantic_denials=548,
        current_native_executions=False, end_to_end_speedup_claimed=False))
    transport_denials = values['bundle_root_check']['independent_transport_denials']
    need(isinstance(transport_denials, list) and len(transport_denials) == 37 and
         len(set(transport_denials)) == 37, 'Complete distinct independent transport denial labels')

    observer_stage = config['observer_stage']
    need(audit['root_observer_stage_sha256'] == observer_stage['sha256'],
         'Exact independently audited original BEFORE/source oracle stage')
    need(verify_stage(observer_stage['path'], observer_stage['sha256'])['recorded_stage_passed'],
         'Completed stable original BEFORE/source oracle stage')
    recorded_stage = read(Path(observer_stage['path'])/'stage.json')
    model_path = normalized(str(Path(config['receipts']['root_model']['path']).absolute()))
    need({normalized(p):h for p,h in recorded_stage['artifact_sha256'].items()}[model_path] ==
         config['receipts']['root_model']['sha256'], 'Exact completed oracle output association')
    for path in Path(observer_stage['path']).iterdir():
        if path.is_file():
            add(path)
    archives = []
    groups = [('root', values['root_execution']['levels'], 60591),
              ('independent', fixture['capture_archives'], 98678),
              ('transport', values['bundle_preparation']['levels'], 65032)]
    for kind, levels, count in groups:
        need(set(levels) == {'O0', 'O2'}, 'Both exact optimization levels in ' + kind + ' archives')
        for level, info in levels.items():
            path = info.get('bundle', info.get('path', info.get('bundle_path')))
            digest = info.get('bundle_sha256', info.get('sha256'))
            with CaptureBundle(add(path, digest), digest) as reader:
                need(len(reader.names()) == count, 'Complete current ' + kind + ' archive')
                if kind == 'transport':
                    completed = json.loads(reader.read_bytes('controls.json'), object_pairs_hook=unique_object)
                    need(completed['passed'] is True and completed['scenarios'] == 66 and
                         completed['original_executed'] is False and completed['ordinary_game_launched'] is False,
                         'Preserved historical fixture completion; exact old inventory has no COMPLETE record')
                else:
                    need(reader.read_bytes('COMPLETE') == b'COMPLETE', 'Closed new native writer')
            archives.append(dict(kind=kind, level=level, path=path, sha256=digest, logical_files=count))
    need(not any('/actual/case-' in p.replace('\\', '/') or '/captures/row-' in p.replace('\\', '/')
                 for p in files), 'Current physical union uses sealed captures')
    add(__file__)
    add(ROOT/'tools/m4-crt-parser-prefix-root/create_config.py')
    add(sys.executable)
    closure = verify_manifest(files)
    out.mkdir()
    pins = dict(files=files)
    publish_bytes(out/'pins.json', (json.dumps(pins, indent=2)+'\n').encode())
    report = dict(passed=True, scope='Bounded native parser prefix and separately verified capture transport',
        receipts=config['receipts'], historical_receipts_expanded=False, files=files,
        physical_closure=closure, pins_sha256=sha_file(out/'pins.json'), archives=archives,
        root_normal_sequences=48, root_fault_sequences=24, root_model_checks=146113,
        root_model_corruption_denials=2648, root_full_causal_model_sequences=0,
        independent_compiled_scenarios=132, independent_compiled_checks=values['compiled_review']['checks'],
        actual_hardware_pairs=264, hardware_semantic_denials=548, inventory_request_denials=14,
        transport_inventory_denials=37, warm_reader_ratio=values['bundle_review']['measured_warm_semantic_reader_ratio'],
        end_to_end_speedup_claimed=False, parser_source_bytes=436, source_identity_bytes=1587,
        completed_parser_accesses=16, prefix_PCs_including_stop=23, locale_read_completed=False,
        parser_RET=False, sizing_complete=False, argument_outputs=False, full_CRT_complete=False,
        selected_initializers=27, total_initializer_roots=144, ordinary_game_launched=False,
        original_executed=False, whole_M4_complete=False, seconds=(time.perf_counter_ns()-started)/1e9)
    publish_bytes(out/'report.json', (json.dumps(report, indent=2)+'\n').encode())
    print(json.dumps({k:v for k,v in report.items() if k not in ('files','archives','receipts')}))


if __name__ == '__main__':
    need(len(sys.argv) == 4, 'accept.py fixed-config.json config-SHA fresh-output')
    main(*sys.argv[1:])
