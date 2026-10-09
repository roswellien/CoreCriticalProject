"""Author aggregate for the bounded connected wrapper/provider experiment."""
import hashlib, importlib.util, json, pathlib, re, struct, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = ROOT / 'reports/m4-crt-control-integration'


def sha(path):
    with open(path, 'rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(pathlib.Path(path).read_text(encoding='utf-8-sig'))


def need(condition, reason):
    if not condition:
        raise ValueError(reason)


def seal(out):
    need(not out.exists() and out.is_relative_to(BASE), 'Fresh private author aggregate required')
    files, copies, resolutions, checks = {}, {}, [], []

    def bind(path, expected=None):
        path = pathlib.Path(path).resolve()
        actual = sha(path)
        need(expected is None or actual == expected, 'Physical identity ' + str(path))
        need(str(path) not in files or files[str(path)] == actual, 'Conflicting physical identity')
        files[str(path)] = actual
        return actual

    documents = []
    for path in sorted(BASE.rglob('*.json')):
        try:
            value = read(path)
        except json.JSONDecodeError:
            continue
        documents.append((path, value))
        bind(path)
        if not isinstance(value, dict):
            continue
        for row in value.get('literal_source_copies', []):
            bind(row['preserved_path'], row['sha256'])
            copies[(str(pathlib.Path(row['original_path']).resolve()).casefold(), row['sha256'])] = row['preserved_path']

    def rehash_map(path, value):
        need(isinstance(value, dict), 'Object identity map ' + str(path))
        for key in ('source_files', 'tool_files', 'artifacts', 'immutable_files', 'files', 'sources'):
            for original, expected in value.get(key, {}).items():
                if not isinstance(expected, str) or not re.fullmatch('[0-9a-f]{64}', expected):
                    continue
                actual = pathlib.Path(original)
                if actual.is_file() and sha(actual) == expected:
                    bind(actual, expected)
                    continue
                replacement = copies.get((str(actual.resolve()).casefold(), expected))
                need(replacement is not None, 'Explicit historical source resolution missing: ' + str(path) + ' ' + original)
                bind(replacement, expected)
                resolutions.append({'historical_map': str(path.resolve()), 'historical_map_sha256': sha(path), 'original_path': original, 'recorded_sha256': expected, 'physical_path': str(pathlib.Path(replacement).resolve()), 'reason': 'Exact literal historical source preserved before host-placement or test-field repair'})

    for path, value in documents:
        if isinstance(value, dict):
            rehash_map(path, value)
    checks.append({'name': 'Every gate identity map rehashed with explicit historical source resolution', 'maps': len(documents), 'historical_resolutions': len(resolutions), 'passed': True})

    build_counts = {'original-build-normal-r3': (12, 8, 64, 3), 'native-build-r1': (49, 12, 109, 12), 'context-build-r2': (52, 10, 82, 3)}
    builds = {}
    for name, counts in build_counts.items():
        path = BASE / name / 'build.json'
        value = read(path)
        need(value['passed'] and value['failure'] is None, 'Complete final actual build ' + name)
        need(tuple(len(value[key]) for key in ('source_files', 'tool_files', 'artifacts', 'commands')) == counts, 'Exact build inventory ' + name)
        need(all(row['exit_code'] == 0 for row in value['commands']), 'Actual successful command closure ' + name)
        for row in value['literal_source_copies']:
            bind(row['original_path'], row['sha256'])
            bind(row['preserved_path'], row['sha256'])
        for row in value['commands']:
            bind(row['log_path'], row['log_sha256'])
        builds[name] = {'path': str(path.resolve()), 'sha256': bind(path), 'source_count': counts[0], 'tool_count': counts[1], 'artifact_count': counts[2], 'command_count': counts[3]}
    context = read(BASE / 'context-build-r2/build.json')
    native = read(BASE / 'native-build-r1/build.json')
    need(context['consumed_native_build_sha256'] == sha(BASE / 'native-build-r1/build.json'), 'Exact reused native object association')
    for level, expected in context['consumed_guest_objects'].items():
        bind(BASE / 'native-build-r1' / ('native-' + level + '.obj'), expected)
    ctest = (BASE / 'context-build-r2/ctest.log').read_text(encoding='utf-8-sig')
    need(ctest.count('125 authored connected compiled-body/frame/fault controls passed') == 2 and '100% tests passed, 0 tests failed out of 2' in ctest, 'Both actual compiled causal controls')
    checks.append({'name': 'Exact fresh original/native/helper builds and compiled causal control closure', 'builds': builds, 'compiled_checks_per_level': 125, 'compiled_semantic_scenarios_per_level': 22, 'guest_objects_reused_by_context_tests': context['consumed_guest_objects'], 'passed': True})

    op = BASE / 'original-normal-windows-r2/report.json'
    np = BASE / 'native-run-r1/report.json'
    cp = BASE / 'comparison-r1/report.json'
    original, native_run, comparison = read(op), read(np), read(cp)
    need(original['passed'] and native_run['passed'] and comparison['passed'], 'Actual final worker/comparison passes')
    need(original['build_sha256'] == sha(BASE / 'original-build-normal-r3/build.json') and native_run['build_sha256'] == sha(BASE / 'native-build-r1/build.json'), 'Exact worker/build associations')
    need(native_run['original_report_sha256'] == sha(op) and native_run['original_raw_sha256'] == original['raw']['sha256'], 'Before-only original observation association')
    need(original['records'] == native_run['records_per_level'] == 192 and len(original['actual_controls']) == 9 and len(native_run['actual_controls']) == 20, 'Actual corpus and causal worker controls')
    for value in (original, native_run):
        for row in value['commands']:
            bind(row['program'])
            bind(row['stdout'], row['stdout_sha256'])
            bind(row['stderr'], row['stderr_sha256'])
    need(comparison['original_records'] == 192 and comparison['native_records'] == 384 and comparison['differences'] == 0 and len(comparison['observer_controls']) == 180 and all(row['rejected'] for row in comparison['observer_controls']), 'Complete actual differential and observers')
    need(comparison['all_defined_FLAGS_mask'] == 0xCD5 and comparison['undefined_FLAG_exclusions'] == 0 and comparison['actual_native_phase_events'] == 4992 and comparison['actual_Runtime_call_records'] == 768, 'Complete flags and actual ordered routes')
    raw = pathlib.Path(original['raw']['path'])
    bind(raw, original['raw']['sha256'])
    module = importlib.util.spec_from_file_location('author_connected_observer', ROOT / 'tools/m4-crt-control-integration/compare_connected.py')
    observer = importlib.util.module_from_spec(module)
    module.loader.exec_module(observer)
    ob = raw.read_bytes()
    for level in ('O0', 'O2'):
        path = pathlib.Path(native_run['raws'][level]['path'])
        bind(path, native_run['raws'][level]['sha256'])
        nb = path.read_bytes()
        need(len(nb) == 24 + 192 * 17764 and nb[:8] == b'MW4CIN01', 'Actual native extent')
        for i in range(192):
            observer.differential(ob[24 + i * 10444:24 + (i + 1) * 10444], nb[24 + i * 17764:24 + (i + 1) * 17764], i)
    checks.append({'name': 'Author full raw observer replay with exact worker controls, State/stack/FP/host/routes/defined AF', 'original_records': 192, 'native_records': 384, 'worker_controls': 29, 'observer_controls': 180, 'phase_events': 4992, 'Runtime_call_records': 768, 'passed': True})

    # Every guest field is unchanged across the narrow modern host-placement repair.
    old_streams = []
    for name in ('original-run-r1', 'original-normal-windows-r1'):
        path = BASE / name / 'original.bin'
        old = path.read_bytes()
        need(old[:24] == ob[:24] and len(old) == len(ob), 'Preserved original baseline extent')
        for i in range(192):
            before = old[24 + i * 10444:24 + (i + 1) * 10444]
            after = ob[24 + i * 10444:24 + (i + 1) * 10444]
            observer.original(before, i)
            need(before[:1116] == after[:1116] and before[2140:2196] == after[2140:2196] and before[2252:] == after[2252:], 'Guest state unchanged by modern host probe placement')
        need(read(BASE / name / 'failure.json')['passed'] is False and b'487' in (BASE / name / 'missing-pack.stderr').read_bytes(), 'Preserved unrelated pre-CRT reservation collision')
        old_streams.append({'path': str(path.resolve()), 'sha256': bind(path), 'guest_equal_final_records': 192, 'excluded_from_causal_acceptance': True})
    need(read(BASE / 'original-build-r2/build.json')['passed'] is False and 'Illegal System DLL Relocation' in read(BASE / 'original-build-r2/build.json')['failure'], 'Preserved AppContainer process-start refusal')
    need(read(BASE / 'context-build-r1/build.json')['passed'] is False and 'size_bytes' in (BASE / 'context-build-r1/build.log').read_text(encoding='utf-8-sig'), 'Preserved compile-only test typo')
    checks.append({'name': 'Literal failed attempts preserved; all 384 earlier positive guest records equal fixed-placement baseline', 'old_positive_streams': old_streams, 'host_FX_and_ENV_cross_process_equality_not_claimed': True, 'AppContainer_process_start_failure_is_not_original_execution': True, 'test_only_field_repair_is_not_guest_semantic_change': True, 'passed': True})

    prep = read(BASE / 'preparation-r1/report.json')
    research = read(BASE / 'research-r1/report.json')
    layout = read(BASE / 'research-r1/game-layout.json')
    game = pathlib.Path(research['game_path'])
    provider = pathlib.Path(research['provider_path'])
    gb = game.read_bytes()
    bind(game, prep['game_image_sha256'])
    bind(provider, prep['provider_sha256'])
    pack_path = BASE / 'research-r1/pack.bin'
    pack = pack_path.read_bytes()
    bind(pack_path, research['pack_sha256'])
    need(pack[:8] == b'MW4CIPK1' and len(pack) == 16428 and struct.unpack_from('<I', pack, 8) == (4,), 'Four exact source pages')
    gamepage = pack[20:4116]
    for row in prep['complete_source_ranges']:
        source = gb[row['file_offset']:row['file_offset'] + row['size_bytes']]
        need(hashlib.sha256(source).hexdigest() == row['sha256'] and source == gamepage[row['address'] - 0x5AC000:row['address'] - 0x5AC000 + len(source)], 'Literal complete game source/pack equality')
    need(struct.unpack_from('<I', pack, 12 + 4104 + 8 + 0x578) == (0x780042E1,), 'Declared original one-slot IAT resolution')
    old_pack = pathlib.Path(research['consumed_provider_pack_path'])
    bind(old_pack, research['consumed_provider_pack_sha256'])
    old_bytes = old_pack.read_bytes()
    need(pack[12 + 2 * 4104:] == old_bytes[12:], 'Frozen complete provider pages unchanged')
    need(layout['all_layouts_equal'] and layout['complete_State_bytes'] == 3504 and layout['complete_game_instruction_PCs'] == [0x5AC5A0, 0x5AC5A5, 0x5AC5AA, 0x5AC5AF, 0x5AC5B2, 0x5AC5D6] and layout['provider_mechanical_repairs_unchanged'], 'Complete bounded game lowering and frozen provider repair')
    bind(layout['accepted_provider_host_path'], layout['accepted_provider_host_sha256'])
    checks.append({'name': 'Exact literal game/provider source pack and complete six-PC game lowering association', 'game_bytes': 25, 'game_PCs': 6, 'provider_pages': 2, 'State_layouts_equal': 34, 'native_raw_IAT_preserved': True, 'passed': True})

    dependency_pins = [ROOT / 'reports/m4-runtime/independent-service-r9/pins.json', ROOT / 'reports/m4-guest-cw/independent-review-r1/pins.json', ROOT / 'reports/m4-crt-control/independent-review-r4/pins.json']
    dependency_checks = []
    for path in dependency_pins:
        value = read(path)
        bind(path)
        rehash_map(path, value)
        dependency_checks.append({'path': str(path), 'sha256': sha(path), 'bindings': len(value['files']), 'passed': True})
    independent_raw = []
    for name in ('independent-original-model-r1', 'independent-native-model-r1'):
        path = BASE / name / 'report.json'
        value = read(path)
        need(value['passed'] and value['whole_M4_complete'] is False, 'Independent bounded raw model')
        independent_raw.append({'report_path': str(path.resolve()), 'report_sha256': bind(path), 'pins_path': str((BASE / name / 'pins.json').resolve()), 'pins_sha256': bind(BASE / name / 'pins.json')})
    checks.append({'name': 'Earlier accepted Runtime/CW/provider and unchanged independent raw models physically rehashed', 'dependency_maps': dependency_checks, 'independent_models': independent_raw, 'new_independent_final_acceptance_pending': True, 'passed': True})

    for directory in [BASE, ROOT / 'tools/m4-crt-control-integration', ROOT / 'tests/m4-crt-control-integration'] + list((ROOT / 'build').glob('m4-crt-control-integration-*')):
        for path in directory.rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts:
                bind(path)
    bind(ROOT / 'docs/m4-crt-control-integration-experiment.md')
    bind(ROOT / 'docs/m4-crt-control-integration-plan.md')
    bind(pathlib.Path(sys.executable))
    # Logged build providers are kept separate from their supplemental current hashes.
    lib = pathlib.Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231/bin/Hostx64/x64/lib.exe')
    bind(lib)
    report = {'passed': True, 'scope': 'Author closure of actual connected game wrapper/thunk/provider through unchanged r9 tail-frame orchestration; final independent source/build/causal closure pending', 'checks': checks, 'final_builds': builds, 'original_report_path': str(op.resolve()), 'original_report_sha256': sha(op), 'native_report_path': str(np.resolve()), 'native_report_sha256': sha(np), 'comparison_path': str(cp.resolve()), 'comparison_sha256': sha(cp), 'historical_source_resolutions': resolutions, 'independent_raw_models': independent_raw, 'tool_identity_note': 'Primary recorded tool maps and command logs associate current post-build hashes with actual invocation paths. Supplemental current Lib.exe hash is not a historical invocation hash; no per-instruction historical tool attestation is claimed.', 'supplemental_current_lib_path': str(lib), 'supplemental_current_lib_sha256': sha(lib), 'connected_native_execution_observed': True, 'final_independent_acceptance': False, 'shared_Runtime_r9_changed': False, 'following_numerical_callback_integrated': False, 'full_CRT_startup_executed': False, 'whole_M4_complete': False, 'limitations': ['Serial workers and trusted stable Context/Runtime in fresh private ordinary directories; concurrent writers, reparse/dangling links, atomic publication and arbitrary host mapping/permission replacement are excluded', 'Empty TOP0/SW0/FTW with masked incoming twelve-CW domain; unsupported pending/live FP is denied; no following numerical callback or general host-CW synchronization is credited', 'Only original capture10000100 projects to actual native return5AC436; the r9 tail port rewrites the same existing return DWORD at the same address without claiming another guest CALL', 'Native raw IAT retains original source value and requires named typed route; missing services fault without substitute success', 'No general thread-owned or one-use production callback API, arbitrary swallowed raw GuestMemory fault prevention, full CRT/SEH/initializer ledger, frontend/menu or M4 completion']}
    out.mkdir()
    report_path = out / 'report.json'
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    bind(report_path)
    pins_path = out / 'pins.json'
    pins_path.write_text(json.dumps({'files': dict(sorted(files.items()))}, indent=2) + '\n')
    print('Author connected seal passed:', len(files), 'physical bindings;', len(resolutions), 'explicit historical source resolutions;', sha(report_path), sha(pins_path))


if __name__ == '__main__':
    seal(pathlib.Path(sys.argv[1]).resolve())
