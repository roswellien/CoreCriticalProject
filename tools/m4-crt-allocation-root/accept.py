"""Accept one functional allocation batch without expanding historical captures."""
import ast
import hashlib
import json
from pathlib import Path
import struct
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
BASE = ROOT / 'reports/m4-crt-allocation-root'
sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
from capture_bundle import CaptureBundle, sha_file
from manifests import normalized, unique_object, verify_manifest
from paths import publish_bytes, workspace_path
from stages import verify_stage

CATEGORIES = ('files', 'sources', 'source_files', 'tools', 'tool_files', 'libraries',
              'entry_objects', 'direct_writer_objects', 'compiler_read_headers', 'artifacts', 'input_files',
              'objects', 'reused_object_hashes', 'reused_library_hashes')
TRANSPORT_KEYS = {'emit_seconds', 'finalize_parts_seconds', 'format', 'logical_files',
                  'native_executed', 'parts', 'passed', 'payload_bytes', 'transport_only'}
PART_KEYS = {'bundle', 'bundle_bytes', 'index_bytes', 'index_sha256', 'logical_files',
             'payload_bytes', 'sha256'}
RECEIPTS = {'direct_build', 'direct_controls', 'direct_seal', 'direct_compatibility',
            'direct_workload', 'source_recovery', 'source_model_readiness', 'literal_lifts',
            'preparation', 'build', 'native_execution', 'model_review', 'compiled_review'}


def need(value, why):
    if not value:
        raise ValueError(why)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique_object)


def main(config_path, config_sha, directory):
    started = time.perf_counter()
    out = workspace_path(directory, reports=True)
    need(out.parent == BASE and not out.exists(), 'Fresh allocation acceptance report')
    files = {}

    def pin(path, expected=None):
        path = Path(path).absolute()
        key = normalized(str(path))
        digest = sha_file(path) if expected is None else expected
        need(key not in files or files[key] == digest, 'Consistent current dependency: ' + key)
        files[key] = digest
        return path

    config_path = pin(config_path, config_sha)
    need(sha_file(config_path) == config_sha, 'Externally fixed acceptance configuration')
    config = read(config_path)
    need(set(config) == {'receipts', 'facts', 'pin_manifests', 'history', 'documents',
                         'syntax_sources', 'stages', 'capture_sets'}, 'Exact acceptance configuration')
    need(set(config['receipts']) == RECEIPTS, 'Complete distinct source/native/review and transport proof domains')
    values = {}
    for name, item in config['receipts'].items():
        need(set(item) == {'path', 'sha256'}, 'Exact receipt identity')
        path = pin(item['path'], item['sha256'])
        need(sha_file(path) == item['sha256'], 'Actual fixed receipt: ' + name)
        value = read(path)
        need(value.get('passed') is True, 'Successful receipt: ' + name)
        for claim in ('whole_M4_complete', 'full_CRT_complete', 'original_attach_proved',
                      'original_or_game_executed', 'ordinary_game_launched', 'game_launched'):
            if claim in value:
                need(value[claim] is False, 'Bounded functional research scope: ' + name + '/' + claim)
        for category in CATEGORIES:
            mapping = value.get(category, {})
            need(isinstance(mapping, dict), 'Physical dependency dictionary: ' + name + '/' + category)
            for path_name, digest in mapping.items():
                pin(path_name, digest)
        values[name] = value
    need(set(config['facts']) == RECEIPTS, 'Explicit reviewed facts in every required proof domain')
    checked_facts = 0
    for name, facts in config['facts'].items():
        for field, expected in facts.items():
            value = values[name]
            for component in field.split('/'):
                need(isinstance(value, dict) and component in value, 'Existing declared fact: ' + field)
                value = value[component]
            need(type(value) is type(expected) and value == expected, 'Exact reviewed fact: ' + name + '/' + field)
            checked_facts += 1
    for item in config['pin_manifests']:
        path = pin(item['path'], item['sha256'])
        need(sha_file(path) == item['sha256'], 'Fixed current pin manifest')
        value = read(path)
        if set(value) == {'files'}:
            pass
        elif set(value) == {'files', 'schema'}:
            need(value['schema'] in {'mw34-m4-allocation-lift-pins-v1',
                                     'mw34-m4-allocation-observer-pins-v1'}, 'Exact reviewed pin schema')
        elif set(value) == {'files', 'schema', 'physical_files'}:
            need(value['schema'] == 'mw34-m4-allocation-model-review-pins-v1' and
                 value['physical_files'] == len(value['files']), 'Exact source model pin schema')
        else:
            raise ValueError('Unrecognized current pin manifest schema')
        for name, digest in value['files'].items():
            pin(name, digest)
    for item in config['history'] + config['documents']:
        path = pin(item['path'], item['sha256'])
        need(sha_file(path) == item['sha256'], 'Fixed history/document identity')
    python_sources = 0
    for item in config['syntax_sources']:
        path = pin(item['path'], item['sha256'])
        need(sha_file(path) == item['sha256'], 'Fixed current syntax source')
        need(path.suffix == '.py', 'Explicit Python syntax scope')
        ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
        python_sources += 1
    stages = []
    for item in config['stages']:
        stage = pin(Path(item['directory']) / 'stage.json', item['sha256'])
        value = verify_stage(str(stage.parent), item['sha256'])
        stages.append({'directory': str(stage.parent), 'verification': value})

    execution = values['native_execution']
    need(normalized(execution['build_path']) == normalized(config['receipts']['build']['path']) and
         execution['build_sha256'] == config['receipts']['build']['sha256'],
         'Functional native execution belongs to the fixed current authored build')
    need(execution['native_stages_completed'] == 2 and set(execution['levels']) == {'O0', 'O2'},
         'Both current authored optimization levels completed')
    need(values['model_review']['execution_sha256'] == config['receipts']['native_execution']['sha256'] and
         values['model_review']['source_recovery_sha256'] == config['receipts']['source_recovery']['sha256'],
         'Independent source model belongs to these exact native captures and recovered original bytes')
    compiled_review = values['compiled_review']
    compiled_native_path = pin(compiled_review['native_path'], compiled_review['native_sha256'])
    need(sha_file(compiled_native_path) == compiled_review['native_sha256'],
         'Fixed actual independent native execution reviewed by the compiled checker')
    compiled_native = read(compiled_native_path)
    need(compiled_native['passed'] is True and compiled_native['native_executed'] is True and
         compiled_native['native_scenarios'] == 48 and compiled_native['native_stages_completed'] == 2 and
         set(compiled_native['levels']) == {'O0', 'O2'}, 'Complete independent native corpus')
    compiled_build_path = pin(compiled_native['build_path'], compiled_native['build_sha256'])
    need(sha_file(compiled_build_path) == compiled_native['build_sha256'], 'Fixed compiled reviewer build')
    compiled_build = read(compiled_build_path)
    need(compiled_build['passed'] is True and
         normalized(compiled_build['author_build']) == normalized(config['receipts']['build']['path']) and
         compiled_build['author_build_sha256'] == config['receipts']['build']['sha256'],
         'Independent compiled review belongs to this exact authored build')
    for value in (compiled_native, compiled_build):
        for category in CATEGORIES:
            for path_name, digest in value.get(category, {}).items():
                pin(path_name, digest)
    declared_stages = {(normalized(x['directory']), x['sha256']) for x in config['stages']}
    declared_captures = {(normalized(x['manifest']), x['sha256'], x['logical_files'])
                         for x in config['capture_sets']}
    semantic_captures = set()
    native_domains = ((execution, values['build'], 'stage_sha256'),
                      (compiled_native, compiled_build, 'native_stage_sha256'))
    for domain, build, stage_key in native_domains:
        for level, native in domain['levels'].items():
            need((normalized(native['native_stage']), native[stage_key]) in declared_stages,
                 'Credited native stage included in current closure: ' + level)
            identity = (normalized(native['transport_manifest']), native['transport_sha256'], native['logical_files'])
            need(identity in declared_captures, 'Credited transport included in current closure: ' + level)
            stage = read(Path(native['native_stage']) / 'stage.json')
            need(stage['argv'] == native['argv'] and native['argv'][0] == native['worker'] and
                 normalized(native['worker']) == normalized(build['workers'][level]),
                 'Exact current native command association: ' + level)
            need(normalized(str(Path(native['argv'][-1]) / 'transport.json')) == identity[0] and
                 {normalized(p):d for p,d in stage['artifact_sha256'].items()}.get(identity[0]) == identity[1],
                 'The credited transport is the actual successful worker output: ' + level)
            semantic_captures.add(identity)

    # Independently read every logical record with the unchanged strict reader.
    # No extraction, tree copy, pack pass, or per-record dependency expansion.
    capture_sets = []
    for item in config['capture_sets']:
        path = pin(item['manifest'], item['sha256'])
        need(sha_file(path) == item['sha256'], 'Fixed direct transport manifest')
        manifest = read(path)
        need(set(manifest) == TRANSPORT_KEYS and manifest['format'] == 'mw34.capture.direct.v1',
             'Exact native direct transport schema')
        need(manifest['passed'] is True and manifest['native_executed'] is False and
             manifest['transport_only'] is True, 'Transport does not confer source execution credit')
        need(manifest['logical_files'] == item['logical_files'], 'Fixed native capture record count')
        need(manifest['parts'], 'Nonempty direct archive set')
        names, payload, physical, parts = set(), 0, {path.name}, []
        complete_bytes = None
        verify_started = time.perf_counter()
        for part in manifest['parts']:
            need(set(part) == PART_KEYS, 'Exact bounded part identity')
            name = part['bundle']
            need(isinstance(name, str) and Path(name).name == name and name.endswith('.mwb') and
                 name not in physical, 'Distinct direct archive basename')
            physical.add(name)
            bundle_path = pin(path.parent / name, part['sha256'])
            with bundle_path.open('rb') as stream:
                magic, index_bytes, index_sha = struct.unpack('<8sQ32s', stream.read(48))
            need(magic == b'MW34CAP1' and index_bytes == part['index_bytes'] and
                 index_sha.hex() == part['index_sha256'], 'Actual unchanged archive header')
            need(bundle_path.stat().st_size == part['bundle_bytes'], 'Actual complete archive extent')
            with CaptureBundle(bundle_path, part['sha256']) as bundle:
                need(len(bundle.names()) == part['logical_files'], 'Actual strict archive count')
                part_payload = 0
                for logical in bundle.names():
                    key = logical.casefold()
                    need(key not in names, 'Disjoint normalized logical union across archive parts')
                    names.add(key)
                    data = bundle.read_bytes(logical)
                    part_payload += len(data)
                    if key == 'complete':
                        complete_bytes = data
            need(part_payload == part['payload_bytes'], 'Actual strict archive payload extent')
            payload += part_payload
            parts.append(dict(bundle=str(bundle_path), logical_files=part['logical_files'],
                              payload_bytes=part_payload))
        need(len(names) == manifest['logical_files'] and payload == manifest['payload_bytes'],
             'Complete unchanged bounded archive union')
        need({p.name for p in path.parent.iterdir()} == physical,
             'Only direct bounded archives and manifest; zero physical per-record files')
        identity = (normalized(str(path)), item['sha256'], item['logical_files'])
        if identity in semantic_captures or item.get('semantic_complete') is True:
            need(complete_bytes == b'COMPLETE' and 'incomplete' not in names and 'failure.txt' not in names,
                 'Complete functional captures confer credit; diagnostic partial transports do not')
        capture_sets.append(dict(manifest=str(path), logical_files=len(names), payload_bytes=payload,
                                 parts=parts, verify_seconds=time.perf_counter()-verify_started,
                                 per_record_physical_files=0))
    pin(__file__)
    for module in ('capture_bundle.py', 'manifests.py', 'paths.py', 'stages.py'):
        pin(ROOT / 'tools/m4-pipeline' / module)
    pin(sys.executable)
    closure = verify_manifest(files)
    report = dict(passed=True, scope='Functional native allocation/free research batch and direct captures',
                  receipts=config['receipts'], checked_receipt_facts=checked_facts,
                  capture_sets=capture_sets, stages=stages, python_syntax_sources=python_sources,
                  current_physical_closure=closure, files=files,
                  elapsed_seconds=time.perf_counter()-started,
                  historical_flat_capture_trees_expanded=False, original_game_executed=False,
                  original_attach_proved=False, full_CRT_complete=False, whole_M4_complete=False)
    publish_bytes(out / 'report.json', (json.dumps(report, indent=2) + '\n').encode())
    print(json.dumps({k:v for k,v in report.items() if k not in ('files','stages','receipts')}))


if __name__ == '__main__':
    main(*sys.argv[1:])
