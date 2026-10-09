"""Author closure for the bounded actual control-to-selected26 carry gate."""
import hashlib, importlib.util, json, pathlib, re, struct, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = ROOT / 'reports/m4-crt-control-carry'
MIXED = ROOT / 'reports/m4-mixed-startup'
CONNECTED = ROOT / 'reports/m4-crt-control-integration'
sys.dont_write_bytecode = True

def sha(path):
    with open(path, 'rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def read(path):
    return json.loads(pathlib.Path(path).read_text(encoding='utf-8-sig'))

def need(value, reason):
    if not value:
        raise ValueError(reason)

def seal(out):
    need(not out.exists() and out.is_relative_to(BASE), 'Fresh private carry author aggregate required')
    files, copies, resolutions, checks = {}, {}, [], []

    def bind(path, expected=None):
        path = pathlib.Path(path).resolve()
        actual = sha(path)
        need(expected is None or expected == actual, 'Physical identity ' + str(path))
        need(str(path) not in files or files[str(path)] == actual, 'Conflicting physical identity')
        files[str(path)] = actual
        return actual

    documents = []
    def authored_or_frozen_original(path):
        first = path.relative_to(BASE).parts[0]
        return not first.startswith('independent-') or first == 'independent-original-carry-r1'
    for path in sorted(BASE.rglob('*.json')):
        if not authored_or_frozen_original(path):
            continue
        try:
            value = read(path)
        except json.JSONDecodeError:
            continue
        documents.append((path, value))
        bind(path)
        if isinstance(value, dict):
            for row in value.get('literal_source_copies', []):
                bind(row['preserved_path'], row['sha256'])
                copies[(str(pathlib.Path(row['original_path']).resolve()).casefold(), row['sha256'])] = row['preserved_path']

    def rehash_map(path, value):
        for name in ('files', 'sources', 'source_files', 'tools', 'tool_files', 'artifacts', 'original_sources', 'generated_sources'):
            for original, expected in value.get(name, {}).items():
                if not isinstance(expected, str) or not re.fullmatch('[0-9a-f]{64}', expected):
                    continue
                physical = pathlib.Path(original)
                if physical.is_file() and sha(physical) == expected:
                    bind(physical, expected)
                    continue
                replacement = copies.get((str(physical.resolve()).casefold(), expected))
                need(replacement is not None, 'Missing exact historical source copy: ' + str(path) + ' ' + original)
                bind(replacement, expected)
                resolutions.append({'historical_map': str(path.resolve()), 'historical_map_sha256': sha(path),
                                    'original_path': original, 'recorded_sha256': expected, 'physical_path': str(pathlib.Path(replacement).resolve()),
                                    'reason': 'Literal pre-build source version retained before additive namespace/fixture admission repair'})

    for path, value in documents:
        if isinstance(value, dict):
            rehash_map(path, value)
    checks.append({'name': 'Every carry historical identity map rehashed with literal version associations',
                   'maps': len(documents), 'historical_source_resolutions': len(resolutions), 'passed': True})

    builds = {}
    for name, keys, counts in [('original-build-r1', ('source_files', 'tool_files', 'artifacts', 'commands'), (9,8,97,3)),
                               ('native-build-r4', ('sources', 'tools', 'artifacts', 'commands'), (275,12,434,50)),
                               ('context-build-r1', ('source_files', 'tool_files', 'artifacts', 'commands'), (278,10,352,3))]:
        path = BASE / name / 'build.json'
        value = read(path)
        need(value['passed'] and value['failure'] is None and all(row['exit_code'] == 0 for row in value['commands']), 'Successful complete actual build ' + name)
        need(tuple(len(value[key]) for key in keys) == counts, 'Exact build inventory ' + name)
        for row in value['commands']:
            bind(row.get('log_path', row.get('log')), row['log_sha256'])
        builds[name] = {'path': str(path.resolve()), 'sha256': bind(path), 'source_count': counts[0],
                        'tool_count': counts[1], 'artifact_count': counts[2], 'command_count': counts[3]}
    native = read(BASE / 'native-build-r4/build.json')
    context = read(BASE / 'context-build-r1/build.json')
    original = read(BASE / 'original-run-r1/report.json')
    comparison = read(BASE / 'comparison-r2/report.json')
    controls = read(BASE / 'native-controls-r1/report.json')
    need(context['consumed_native_build_sha256'] == sha(BASE / 'native-build-r4/build.json') and context['consumed_guest_objects'] == native['objects'], 'Exact actual reused guest objects')
    ctest = (BASE / 'context-build-r1/ctest.log').read_text(encoding='utf-8-sig')
    need(ctest.count('346 compiled carry checks across 22 scenarios passed') == 2 and '100% tests passed, 0 tests failed out of 2' in ctest, 'Both actual compiled capability/carry controls')
    need(original['passed'] and original['records'] == 648 and len(original['actual_controls']) == 9, 'Complete original and causal controls')
    need(original['build_sha256'] == sha(BASE / 'original-build-r1/build.json') and native['original_report_sha256'] == sha(BASE / 'original-run-r1/report.json'), 'Exact original build/run/native input association')
    need(controls['passed'] and controls['build_sha256'] == sha(BASE / 'native-build-r4/build.json') and len(controls['actual_controls']) == 24, 'Actual native causal controls')
    for document in (original, controls):
        for row in document['commands']:
            bind(row['program'])
            bind(row['stdout'], row['stdout_sha256'])
            bind(row['stderr'], row['stderr_sha256'])
            if row.get('expected_diagnostic'):
                need(row['exit_code'] == 1 and row['expected_diagnostic'] in pathlib.Path(row['stderr']).read_text(), 'Causal intended diagnosis')
    for row in controls['actual_controls']:
        if 'sentinel_path' in row:
            bind(row['sentinel_path'], row['sentinel_sha256'])
            need(pathlib.Path(row['sentinel_path']).stat().st_size == row['sentinel_size_bytes'] == 32, 'Actual external sentinel extent')
    need(comparison['passed'] and comparison['original_phases'] == 648 and comparison['native_phases'] == 1296 and comparison['differences'] == 0,
         'Actual full original/native differential')
    need(len(comparison['observer_controls']) == 70 and all(row['rejected'] for row in comparison['observer_controls']), 'Actual author observer corruptions')
    checks.append({'name': 'Fresh builds, positive actual records, intended worker denials and exact compiled carry/capability controls',
                   'builds': builds, 'original_phases': 648, 'native_phases': 1296, 'actual_worker_controls': 33,
                   'observer_controls': 70, 'compiled_checks_per_level': 346, 'compiled_scenarios_per_level': 22, 'passed': True})

    spec = importlib.util.spec_from_file_location('author_carry_observer', ROOT / 'tools/m4-crt-control-carry/compare.py')
    observer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(observer)
    observer.mixed.configure(read(MIXED / 'original-extract-original-build-r2/extraction.json'))
    static = read(ROOT / 'reports/m4-startup/next-initializer-410940-events/report.json')['memory_events']
    ob = pathlib.Path(original['raw']['path']).read_bytes()
    bind(original['raw']['path'], original['raw']['sha256'])
    need(ob[:8] == b'MW4CCO01' and len(ob) == 32 + 648 * 92388, 'Complete actual original extent')
    event_counts, raw_bindings = {}, {}
    for level in ('O0', 'O2'):
        path = BASE / 'native-build-r4' / ('native-' + level + '.bin')
        bind(path)
        raw_bindings[level] = {'path': str(path.resolve()), 'sha256': sha(path), 'size_bytes': path.stat().st_size}
        need(controls['positive_raws'][level]['sha256'] == sha(path), 'Same positive raw controlled worker')
        nb = path.read_bytes()
        need(nb[:8] == b'MW4CCN01' and len(nb) == 32 + 648 * 104808, 'Complete actual native extent')
        previous, selected_events, control_events, routes = None, 0, 0, 0
        for i in range(648):
            row = nb[32 + i * 104808:32 + (i + 1) * 104808]
            previous = observer.row_check(ob[32 + i * 92388:32 + (i + 1) * 92388], row, i, previous, static)
            selected_events += struct.unpack_from('<I', row, 99396)[0]
            control_events += struct.unpack_from('<I', row, 104492)[0]
            routes += struct.unpack_from('<I', row, 104752)[0]
        need(control_events == 312 and routes == 672, 'Actual complete ordered control phases/r9 records')
        event_counts[level] = {'selected_checked_events': selected_events, 'control_events': control_events, 'Runtime_call_records': routes}
        # Previous r3 positives are an observed immutable baseline; the additional
        # exact State admission guard does not change any admitted guest result.
        old = BASE / 'native-build-r3' / ('native-' + level + '.bin')
        old_bytes = old.read_bytes()
        need(old_bytes[:32] == nb[:32] and len(old_bytes) == len(nb), 'Preserved r3 complete positive extent')
        for i in range(648):
            before = old_bytes[32 + i * 104808:32 + (i + 1) * 104808]
            after = nb[32 + i * 104808:32 + (i + 1) * 104808]
            need(before[:1140] == after[:1140] and before[2164:2220] == after[2164:2220] and before[2276:] == after[2276:],
                 'Complete r3/r4 guest fields, State, FX, pages and actual routes unchanged')
            need(observer.observe.host_equal(before[1140:1652], before[1652:2164], before[2220:2248], before[2248:2276]),
                 'Preserved r3 host restoration observed separately')
        bind(old)
    checks.append({'name': 'Author raw replay of full CPU/State/pages/FP/host/event carry and complete-r3 guest equality',
                   'raws': raw_bindings, 'actual_event_counts': event_counts, 'persistent_boundaries_per_level': 624, 'passed': True})

    generation = read(BASE / 'research-r4/generation.json')
    need(generation['passed'] and native['generation_sha256'] == sha(BASE / 'research-r4/generation.json'), 'Frozen exact final derivative association')
    old_generation = read(MIXED / 'native-derived-r2/generation.json')
    guard = ('\n    require(word<std::uint32_t>(domain.fx.data()+28)==0x2ffff&&word<std::uint32_t>(reinterpret_cast<const std::uint8_t *>(&s.x87)+28)==0x2ffff,"Observed carry FX capability mask changed");'
             '\n    std::fill_n(domain.fx.data()+28,4,0); // temporary Request only; resident State/FX unchanged')
    reverse_count = 0
    for old_path, expected in old_generation['generated_sources'].items():
        old_path = pathlib.Path(old_path)
        bind(old_path, expected)
        relative = old_path.relative_to(MIXED / 'native-derived-r2')
        current = BASE / 'research-r4/native' / relative
        text = current.read_text(encoding='utf-8-sig')
        if relative.as_posix() in ('chain/runtime_adapter.cpp', 'integer/runtime_adapter.cpp'):
            need(text.count(guard) == 1 and text.index(guard) < text.index('validate_request(domain)'), 'Exact temporary Request guard before validation')
            text = text.replace(guard, '')
        restored = text.replace('m4_crt_control_carry::', 'm4_mixed::').replace('mw34::m4_crt_control_carry', 'mw34::m4_mixed').replace('mw34_carry_', 'mw34_mixed_')
        restored = restored.replace((ROOT / 'tools/m4-crt-control-carry/native_protocol.hpp').as_posix(), (ROOT / 'tools/m4-mixed-startup/native_protocol.hpp').as_posix())
        need(restored == old_path.read_text(encoding='utf-8-sig'), 'Full shared derivative reversal ' + str(relative))
        bind(current)
        reverse_count += 1
    control = BASE / 'research-r4/native/control.ll'
    text = control.read_text(encoding='utf-8-sig')
    for old, new in generation['control_external_mapping'].items():
        text = re.sub(r'\b' + re.escape(new) + r'\b', old, text)
    need(text == (CONNECTED / 'research-r1/host.ll').read_text(encoding='utf-8-sig'), 'Entire compiled game/provider IR reversal')
    pack = (BASE / 'research-r4/pack.bin').read_bytes()
    mixed_pack = pathlib.Path(read(MIXED / 'original-extract-original-build-r2/extraction.json')['pack']['path']).read_bytes()
    old_control = (CONNECTED / 'research-r1/pack.bin').read_bytes()
    expected_extra = bytearray(old_control[12:])
    struct.pack_into('<I', expected_extra, 8 + 0x437, (0x410A80 - 0x5AC43B) & 0xFFFFFFFF)
    struct.pack_into('<I', expected_extra, 4104 + 4, 0)
    need(pack == b'MW4CCP01' + struct.pack('<I',26) + mixed_pack[12:] + expected_extra, 'Complete original page equality except declared instrumentation/role')
    need((BASE / 'research-r4/original/reference_x86.asm').read_text() == (ROOT / 'tools/m4-mixed-startup/original/reference_x86.asm').read_text(), 'Exact unchanged original CPU/FP capture assembly text; generated LF/source CRLF files separately hashed')
    first_pack = BASE / 'research-r1/pack.bin'
    need(first_pack.read_bytes() == pack, 'Final native and frozen original exact pack association')
    need(generation['temporary_Request_representation'] == {'adapters':['chain','integer'], 'offset':28, 'bytes':4,
         'required_actual_resident_FX_value':0x2ffff, 'temporary_offline_validator_value':0,
         'resident_State_or_Runtime_FX_mutated':False, 'architectural_CW_MXCSR_or_status_mutated':False}, 'Exact fixture transport scope')
    checks.append({'name': 'Full derivative/source pack reversal and precise temporary-only capability admission exception',
                   'shared_derivative_files': reverse_count, 'control_external_symbols': len(generation['control_external_mapping']),
                   'original_pages':26, 'capability_offset':28, 'capability_bytes':4, 'resident_value':0x2ffff, 'passed':True})

    failed1, failed2 = read(BASE / 'native-build-r1/build.json'), read(BASE / 'native-build-r2/build.json')
    need(not failed1['passed'] and 'undeclared identifier' in failed1['failure'], 'Preserved namespace compile failure')
    need(not failed2['passed'] and 'Unsupported guest MXCSR input' in failed2['failure'], 'Preserved actual fixture-domain failure')
    need(not (BASE / 'native-build-r2/native-O0.bin').exists(), 'Failed r2 had no published raw prefix; no prefix execution credit')
    need(read(BASE / 'native-build-r3/build.json')['passed'], 'Literal positive r3 before additional State guard')
    checks.append({'name':'Literal failed r1/r2 versions and successful r3 baseline preserved', 'r2_published_raw_prefix':False,
                   'r2_failed_log_is_not_native_acceptance':True, 'shared_Runtime_r9_changed':False, 'passed':True})

    dependency_maps = [MIXED / 'independent-review-r1/pins.json', CONNECTED / 'independent-final-review-r1/pins.json',
                       ROOT / 'reports/m4-runtime/independent-service-r9/pins.json', ROOT / 'reports/m4-guest-cw/independent-review-r1/pins.json',
                       ROOT / 'reports/m4-crt-control/independent-review-r4/pins.json']
    dependencies = []
    for path in dependency_maps:
        value = read(path)
        bind(path)
        rehash_map(path, value)
        dependencies.append({'path':str(path.resolve()), 'sha256':sha(path), 'bindings':len(value['files']), 'passed':True})
    own_original = read(BASE / 'independent-original-carry-r1/report.json')
    need(own_original['passed'], 'Independent original-only model passed')
    tooling = read(BASE / 'tooling-supplement-r1/report.json')
    need(tooling['passed'] and tooling['primary_native_build_sha256'] == sha(BASE / 'native-build-r4/build.json') and
         tooling['primary_context_build_sha256'] == sha(BASE / 'context-build-r1/build.json'), 'Exact post-build tooling association')
    checks.append({'name':'Accepted dependencies and original-only review unchanged; actual compiler dependency supplement bound',
                   'dependencies':dependencies, 'compiler_dependencies':len(tooling['compiler_recorded_dependencies']),
                   'independent_original_model_sha256':sha(BASE / 'independent-original-carry-r1/report.json'), 'passed':True})

    for directory in [BASE, ROOT / 'tools/m4-crt-control-carry', ROOT / 'tests/m4-crt-control-carry'] + list((ROOT / 'build').glob('m4-crt-control-carry-*')):
        for path in directory.rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and (directory != BASE or authored_or_frozen_original(path)):
                bind(path)
    bind(ROOT / 'docs/m4-crt-control-carry-experiment.md')
    bind(sys.executable)
    report = {'passed':True, 'scope':'Author actual control-result CW plus selected26 shared-runtime carry closure; independent final acceptance pending',
              'checks':checks, 'final_builds':builds, 'generation_path':str(BASE / 'research-r4/generation.json'),
              'generation_sha256':sha(BASE / 'research-r4/generation.json'), 'original_report_path':str(BASE / 'original-run-r1/report.json'),
              'original_report_sha256':sha(BASE / 'original-run-r1/report.json'), 'native_controls_path':str(BASE / 'native-controls-r1/report.json'),
              'native_controls_sha256':sha(BASE / 'native-controls-r1/report.json'), 'comparison_path':str(BASE / 'comparison-r2/report.json'),
              'comparison_sha256':sha(BASE / 'comparison-r2/report.json'), 'historical_source_resolutions':resolutions,
              'native_raws':raw_bindings, 'connected_execution_observed':True, 'final_independent_acceptance':False,
              'shared_Runtime_r9_changed':False, 'original_expected_results_used_as_native_execution_input':False,
              'full_ledger_completed':False, 'full_CRT_startup_executed':False, 'whole_M4_complete':False,
              'limitations':['Serial workers with stable trusted Context/Runtime borrowers in fresh private ordinary directories; concurrent writers, reparse/dangling links and atomic publisher guarantees are excluded',
                             'Twelve masked incoming CW values, empty TOP0/SW0/FTW and initial installed image operands; pending/deferred exceptions, live stacks, unmasked numerical operations, TOP7 and arbitrary numerical operands are not accepted here',
                             'Temporary integer-validator Request capability DWORD28 alone maps actual2FFFF to fixture0 after both resident views are checked; no resident or architectural CW/MXCSR/status canonicalization',
                             'Control-only original capture5AC436→410A80 projects to native5AC436; next caller rewrites only the single return DWORD and ESP/entry PC. The provider tail port retains the reviewed same-word orchestration',
                             'State legacy ENV metadata is distinct from Windows FX zero metadata; complete raw storage is recorded without assuming cross-process host storage equality',
                             'No general thread-owned/one-use production callback API, arbitrary swallowed raw GuestMemory fault prevention, arbitrary host mapping replacement, all144-root traversal, full CRT/SEH/import/module attach, frontend/menu or M4 completion']}
    out.mkdir()
    rp = out / 'report.json'
    rp.write_text(json.dumps(report, indent=2) + '\n')
    bind(rp)
    pp = out / 'pins.json'
    pp.write_text(json.dumps({'files':dict(sorted(files.items()))}, indent=2) + '\n')
    print('Carry author seal passed:',len(files),'physical bindings;',len(resolutions),'historical associations;',sha(rp),sha(pp))

if __name__ == '__main__':
    seal(pathlib.Path(sys.argv[1]).resolve())
