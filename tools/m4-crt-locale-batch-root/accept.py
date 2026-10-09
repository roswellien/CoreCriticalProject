"""Accept the entire locale/argv unit against fresh, distinct proof domains.

Historical acceptance is reused by identity. Only the current native archives
are read; this tool never extracts, repacks, or creates per-record files.
"""
import ast
import json
from pathlib import Path
import struct
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'reports/m4-crt-locale-batch-root'
sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
from capture_bundle import CaptureBundle, sha_file
from manifests import normalized, unique_object, verify_manifest
from paths import publish_bytes, workspace_path
from stages import verify_stage

ROLES = {'baseline', 'recovery', 'interface', 'lifts', 'supplement', 'callbacks',
         'preparation', 'build', 'native', 'model', 'fixtures', 'compiled', 'exports'}
CATEGORIES = ('files', 'sources', 'source_files', 'tools', 'tool_files', 'libraries',
              'entry_objects', 'direct_writer_objects', 'compiler_read_headers',
              'artifacts', 'input_files', 'objects', 'reused_object_hashes',
              'reused_library_hashes')
TRANSPORT_KEYS = {'emit_seconds', 'finalize_parts_seconds', 'format', 'logical_files',
                  'native_executed', 'parts', 'passed', 'payload_bytes', 'transport_only'}
PART_KEYS = {'bundle', 'bundle_bytes', 'index_bytes', 'index_sha256', 'logical_files',
             'payload_bytes', 'sha256'}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique_object)


def field(value, path):
    for part in path.split('/'):
        need(isinstance(value, dict) and part in value, 'Existing reviewed field: ' + path)
        value = value[part]
    return value


def main(config_path, config_sha, directory):
    started = time.perf_counter()
    out = workspace_path(directory, reports=True)
    need(out.parent == BASE and not out.exists(), 'Fresh owned acceptance destination')
    files = {}

    def pin(path, expected=None):
        path = Path(path).resolve()
        actual = sha_file(path)
        need(expected is None or actual == expected, 'Current physical identity: ' + str(path))
        key = normalized(str(path))
        need(key not in files or files[key] == actual, 'Consistent physical dependency')
        files[key] = actual
        return path

    config = read(pin(config_path, config_sha))
    need(set(config) == {'receipts', 'facts', 'associations', 'stages', 'captures',
                         'extra_receipts', 'documents', 'syntax_sources'}, 'Exact acceptance configuration')
    need(set(config['receipts']) == ROLES and set(config['facts']) == ROLES,
         'Distinct baseline/source/literal/native/independent review domains')
    values = {}
    checked_facts = 0
    for role, identity in config['receipts'].items():
        need(set(identity) == {'path', 'sha256'}, 'Exact receipt identity')
        value = read(pin(identity['path'], identity['sha256']))
        need(value.get('passed') is True, 'Successful receipt: ' + role)
        for claim in ('whole_M4_complete', 'full_CRT_complete', 'full_CRT',
                      'original_attach_proved', 'original_game_executed', 'ordinary_game_launched'):
            if claim in value:
                need(value[claim] is False, 'Bounded unit scope: ' + role + '/' + claim)
        for category in CATEGORIES:
            mapping = value.get(category, {})
            need(isinstance(mapping, dict), 'Physical dependency map: ' + role + '/' + category)
            for path, digest in mapping.items():
                pin(path, digest)
        for path, expected in config['facts'][role].items():
            actual = field(value, path)
            need(type(actual) is type(expected) and actual == expected,
                 'Exact independently reviewed fact: ' + role + '/' + path)
            checked_facts += 1
        values[role] = value

    need(set(config['extra_receipts']) == {'compiled_build', 'compiled_native'},
         'Independent actual build and native execution receipts')
    extras = {}
    for role, item in config['extra_receipts'].items():
        value = read(pin(item['path'], item['sha256']))
        need(value['passed'] is True, 'Successful referenced independent build/native stage')
        for category in CATEGORIES:
            for path, digest in value.get(category, {}).items():
                pin(path, digest)
        extras[role] = value
    for role, path, target_role, target_key in config['associations']:
        actual = field(values[role], path)
        expected = config['receipts'][target_role][target_key]
        need(actual == expected if target_key == 'sha256' else normalized(actual) == normalized(expected),
             'Exact proof association: ' + role + '/' + path)

    execution = values['native']
    need(len(values['preparation']['entry_objects']) == 166 and
         values['build']['entry_objects'] == values['preparation']['entry_objects'] and
         len(values['preparation']['generated_undefined_sites']) == 103 and
         len(values['preparation']['body_entries']) == 78,
         'Complete exact literal-object/source-callback closure reused by the actual build')
    model_files = {normalized(path): digest for path, digest in values['model']['files'].items()}
    need(model_files.get(normalized(config['receipts']['recovery']['path'])) ==
         config['receipts']['recovery']['sha256'] and
         model_files.get(normalized(values['interface']['instruction_contracts_path'])) ==
         values['interface']['instruction_contracts_sha256'],
         'Independent interpreter uses these exact recovered original instruction contracts')
    model_rows = values['model']['rows']
    need(len(model_rows) == 12 and {(row['level'], row['index']) for row in model_rows} ==
         {(level, number) for level in ('O0', 'O2') for number in range(6)},
         'Every canonical case independently compared from original BEFORE inputs')
    for row in model_rows:
        need(row['whole_machine_phases'] == 175 and row['new_source_phases'] == 129 and
             row['pages'] == 26 and row['argc'] == 7 and row['source_API_calls'] == 30 and
             row['cleanup_API_calls'] == 7, 'Complete exact source/ownership sequence in every case')
    need(set(execution['levels']) == {'O0', 'O2'}, 'Both authored optimization levels')
    ordinary, controls = 0, 0
    for level, native in execution['levels'].items():
        need(native['passed'] is True and len(native['rows']) == 18, 'Whole native authored corpus')
        for number, row in enumerate(native['rows']):
            control = 0 if number < 6 else 201 + number - 6
            need(row['scenario'] == number and row['control'] == control and
                 row['result']['passed'] is True, 'Exact actual row and control')
            final, live = row['summary'], row['live_summary']
            need(final[14] == final[15] == final[30] == 0 and final[23] == 1,
                 'Finished same-owner cleanup without native resources')
            if control:
                need(row['result']['builder_returned'] is False, 'Refusal is not credited as completion')
                controls += 1
            else:
                need(live[3:7] == [1, 1, 2, 1] and live[7] == 7 and
                     live[14] == 2 and live[15] == 5 and row['result']['builder_returned'] is True,
                     'Whole static/default locale/two parser passes/genuine builder RET')
                ordinary += 1
    need(ordinary == 12 and controls == 24, 'Complete authored corpus totals')

    stages = []
    for identity in config['stages']:
        path = pin(Path(identity['directory']) / 'stage.json', identity['sha256'])
        verified = verify_stage(str(path.parent), identity['sha256'])
        stages.append({'directory': str(path.parent), 'sha256': identity['sha256'], 'verified': verified})
    declared_stages = {(normalized(x['directory']), x['sha256']) for x in config['stages']}
    declared_captures = {(normalized(x['path']), x['sha256']) for x in config['captures']}
    compiled_native, compiled_build = extras['compiled_native'], extras['compiled_build']
    need(values['compiled']['native_sha256'] == config['extra_receipts']['compiled_native']['sha256'] and
         normalized(values['compiled']['native_path']) == normalized(config['extra_receipts']['compiled_native']['path']),
         'Independent raw checker belongs to this complete actual native corpus')
    need(compiled_native['native_executed'] is True and compiled_native['native_scenarios'] == 24 and
         compiled_native['native_stages_completed'] == 12 and set(compiled_native['levels']) == {'O0', 'O2'},
         'Complete independently compiled actual corpus')
    need(compiled_native['build_sha256'] == config['extra_receipts']['compiled_build']['sha256'] and
         normalized(compiled_native['build_path']) == normalized(config['extra_receipts']['compiled_build']['path']) and
         compiled_build['author_build_sha256'] == config['receipts']['build']['sha256'] and
         normalized(compiled_build['author_build']) == normalized(config['receipts']['build']['path']) and
         compiled_build['fixture_report_sha256'] == config['receipts']['fixtures']['sha256'] and
         normalized(compiled_build['fixture_report']) == normalized(config['receipts']['fixtures']['path']) and
         compiled_build['entry_objects'] == values['build']['entry_objects'],
         'Independent fixture compilation is bound to the current authored candidate')
    for level, native in compiled_native['levels'].items():
        need(len(native['invocations']) == 6, 'Every independently selected command-line pattern')
        for number, invocation in enumerate(native['invocations']):
            need(invocation['selection'] == number and
                 (normalized(invocation['native_stage']), invocation['native_stage_sha256']) in declared_stages and
                 (normalized(invocation['transport_manifest']), invocation['transport_sha256']) in declared_captures,
                 'Every independent actual native stage and direct output belongs to this closure')
            stage = read(Path(invocation['native_stage']) / 'stage.json')
            need(stage['argv'] == invocation['argv'] and
                 normalized(stage['argv'][0]) == normalized(compiled_build['workers'][level]) and
                 normalized(str(Path(stage['argv'][6]) / 'transport.json')) == normalized(invocation['transport_manifest']),
                 'Exact independent worker argv and transport destination')
    for level, native in execution['levels'].items():
        need((normalized(str(Path(native['stage_path']).parent)), native['stage_sha256']) in declared_stages,
             'Actual authored stage included in closure')
        need((normalized(native['transport_path']), native['transport_sha256']) in declared_captures,
             'Actual authored compact captures included in closure')
        stage = read(native['stage_path'])
        need(normalized(stage['argv'][0]) == normalized(values['build']['workers'][level]) and
             normalized(str(Path(stage['argv'][-1]) / 'transport.json')) == normalized(native['transport_path']),
             'Actual stage executable and transport association')

    capture_sets = []
    for identity in config['captures']:
        capture_started = time.perf_counter()
        path = pin(identity['path'], identity['sha256'])
        manifest = read(path)
        need(set(manifest) == TRANSPORT_KEYS and manifest['format'] == 'mw34.capture.direct.v1' and
             manifest['passed'] is True and manifest['transport_only'] is True and
             manifest['native_executed'] is False, 'Exact strict transport-only manifest')
        need(manifest['logical_files'] == identity['logical_files'] and manifest['parts'],
             'Declared finite strict union')
        logical_names, physical_names, payload, complete = set(), {path.name}, 0, None
        for part in manifest['parts']:
            need(set(part) == PART_KEYS, 'Exact bounded archive part schema')
            name = part['bundle']
            need(isinstance(name, str) and Path(name).name == name and name.endswith('.mwb') and
                 name.casefold() not in {x.casefold() for x in physical_names}, 'Safe distinct archive basename')
            physical_names.add(name)
            bundle_path = pin(path.parent / name, part['sha256'])
            with bundle_path.open('rb') as stream:
                magic, index_bytes, index_sha = struct.unpack('<8sQ32s', stream.read(48))
            need(magic == b'MW34CAP1' and index_bytes == part['index_bytes'] and
                 index_sha.hex() == part['index_sha256'] and
                 bundle_path.stat().st_size == part['bundle_bytes'], 'Unchanged actual strict archive header')
            part_payload = 0
            with CaptureBundle(bundle_path, part['sha256']) as bundle:
                need(len(bundle.names()) == part['logical_files'], 'Exact strict part record count')
                for name in bundle.names():
                    key = name.casefold()
                    need(key not in logical_names, 'Disjoint normalized capture union')
                    logical_names.add(key)
                    data = bundle.read_bytes(name)
                    part_payload += len(data)
                    if key == 'complete':
                        complete = data
            need(part_payload == part['payload_bytes'], 'Every logical payload independently verified')
            payload += part_payload
        need(complete == b'COMPLETE' and 'incomplete' not in logical_names and 'failure.txt' not in logical_names,
             'Only completed semantic corpora receive acceptance')
        need(len(logical_names) == manifest['logical_files'] and payload == manifest['payload_bytes'],
             'Complete finite strict archive union')
        need({x.name for x in path.parent.iterdir()} == physical_names, 'No physical per-record capture tree')
        capture_sets.append({'path': str(path), 'logical_files': len(logical_names), 'payload_bytes': payload,
                             'parts': len(manifest['parts']), 'seconds': time.perf_counter() - capture_started,
                             'per_record_physical_files': 0})

    for identity in config['documents']:
        pin(identity['path'], identity['sha256'])
    for identity in config['syntax_sources']:
        source = pin(identity['path'], identity['sha256'])
        need(source.suffix == '.py', 'Declared Python syntax scope')
        ast.parse(source.read_text(encoding='utf-8-sig'), filename=str(source))
    pin(__file__)
    pin(sys.executable)
    for module in ('capture_bundle.py', 'manifests.py', 'paths.py', 'stages.py'):
        pin(ROOT / 'tools/m4-pipeline' / module)
    closure = verify_manifest(files)
    report = {'schema': 'mw34-m4-locale-argv-functional-acceptance-v1', 'passed': True,
              'scope': 'Complete bounded critical-section/default-locale/argv builder native research unit',
              'receipts': config['receipts'], 'checked_receipt_facts': checked_facts,
              'ordinary_authored_cases': ordinary, 'authored_fault_cases': controls,
              'static_critical_sections_completed': True, 'default_locale_completed': True,
              'classification_completed': True, 'both_original_parser_passes_completed': True,
              'original_argc_argv_published': True, 'original_builder_return_target': 0x7800BA9E,
              'clean_native_lifetimes': True, 'stages': stages, 'capture_sets': capture_sets,
              'current_physical_closure': closure, 'files': files,
              'flat_capture_trees_expanded': False, 'historical_native_suites_rerun': False,
              'environment_builder_completed': False, 'full_CRT_complete': False,
              'original_attach_proved': False, 'ordinary_native_game_launched': False,
              'whole_M4_complete': False, 'seconds': time.perf_counter() - started}
    publish_bytes(out / 'report.json', (json.dumps(report, indent=2) + '\n').encode())
    print(json.dumps({k: v for k, v in report.items() if k not in ('files', 'stages', 'receipts', 'capture_sets')}))
    print(json.dumps({'report_sha256': sha_file(out / 'report.json')}))


if __name__ == '__main__':
    main(*sys.argv[1:])
