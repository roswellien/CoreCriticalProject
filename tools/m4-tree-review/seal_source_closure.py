"""Bounded source-program dependency closure supplement.

Independent source_program reads are observed here. This is not a runtime
read trace of the producing native/source capture consumer. Every inherited
input also binds the separately observed genuine-original read receipt.
"""
import collections
import hashlib
import importlib.util
import inspect
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
PINS = {}
SOURCE_HASH = '02fbae62687ca09d73c8c05ae86981c02570208b2a3ae92faea8b81ac9509f76'
PARENT_HASH = '2ebc48e5f6dd213e77b33bea8dda79ef2cd4a46b9e48997f6f346cd4e01d6c2c'


def need(value, label):
    if not value:
        raise ValueError(label)


def pin(path, expected=None):
    path = Path(path).resolve()
    need(path.suffix not in ('.mwb', '.zip'), 'No archive consumer in bounded source closure')
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    need(expected is None or digest == expected, 'Physically immutable source dependency ' + str(path))
    need(str(path) not in PINS or PINS[str(path)] == digest, 'One frozen identity for each dependency')
    PINS[str(path)] = digest
    return path


def read(path, expected=None):
    path = pin(path, expected)
    need(path.stat().st_size <= 16 * 1024 * 1024, 'Bounded metadata input')
    return json.loads(path.read_bytes())


def main(provider_path, name):
    out = ROOT / 'reports/m4-tree-review' / name
    need(not out.exists(), 'Fresh closure supplement')
    out.mkdir(parents=True)
    passed = False
    error = None
    counts = collections.Counter()
    observations = []
    source_path = ROOT / 'reports/m4-tree-source/connected-native125-source-r2/report.json'
    raw_read = Path.read_bytes
    text_read = Path.read_text
    try:
        pin(__file__)
        source = read(source_path, SOURCE_HASH)
        parent_path = ROOT / 'reports/m4-tree-original/old-Lockit-source-r3/report.json'
        parent = read(parent_path, PARENT_HASH)
        need(source['passed'] and parent['passed'] and parent['recursive_workspace_source_reads_sealed'],
             'Current native source and genuine-original observed read closure passed')
        provider = None
        if provider_path != 'none':
            provider_path = Path(provider_path).resolve()
            provider = read(provider_path)
            need(provider['passed'] and provider['complete_provider_lifecycle'], 'Fresh complete actual provider gate')
            for key in ('execution', 'build', 'joint_preparation', 'native_preparation'):
                need(provider['executed_lineage'][key] == source['executed_lineage'][key],
                     'Supplement attaches only to same exact full125 lineage')
        for path, digest in source['files'].items():
            if Path(path).suffix == '.py':
                pin(path, digest); counts['source_report_code_files_physically_sealed'] += 1
        if provider:
            for path, digest in provider['files'].items():
                if Path(path).suffix == '.py':
                    pin(path, digest); counts['provider_report_code_files_physically_sealed'] += 1

        def observed(path, method, args, kwargs):
            path = Path(path).resolve()
            need(path.is_relative_to(ROOT) and path.suffix in ('.json', '.py'),
                 'Only bounded workspace source input is read during source_program audit')
            need(path.stat().st_size <= 16 * 1024 * 1024, 'Bounded source-program input')
            raw = raw_read(path)
            digest = hashlib.sha256(raw).hexdigest()
            # Record the actual caller performing the read, beyond this adapter.
            caller = inspect.currentframe().f_back.f_back
            code = Path(caller.f_code.co_filename).resolve()
            observations.append(dict(path=str(path), sha256=digest, caller=str(code),
                                     caller_line=caller.f_lineno, function=caller.f_code.co_name,
                                     read_method=method, bytes=len(raw)))
            need(str(code) in source['files'] and hashlib.sha256(raw_read(code)).hexdigest() == source['files'][str(code)],
                 'Audited input belongs to exact already-consumed producing source code')
            PINS[str(code)] = source['files'][str(code)]
            PINS[str(path)] = digest
            return raw if method == 'read_bytes' else text_read(path, *args, **kwargs)

        def read_bytes(path):
            return observed(path, 'read_bytes', (), {})

        def read_text(path, *args, **kwargs):
            return observed(path, 'read_text', args, kwargs)

        Path.read_bytes = read_bytes
        Path.read_text = read_text
        module_path = ROOT / 'tools/m4-tree-source/game_model_v4.py'
        spec = importlib.util.spec_from_file_location('bounded125_dependency_source', module_path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        program, callbacks = module.source_program()
        Path.read_bytes = raw_read
        Path.read_text = text_read
        need(0x4b7f70 in program and 0x7810a290 in program and 0x7810a350 in program,
             'Independently constructed full source program contains new tree and inherited provider')
        consumed = {r['path']: r['sha256'] for r in observations}
        supplemental = []
        for path, digest in consumed.items():
            pin(path, digest)
            if path in source['files']:
                need(source['files'][path] == digest, 'Previously exposed source input exact identity')
                counts['consumed_inputs_already_exposed'] += 1
            else:
                # Old source inputs are authenticated against the genuine
                # original's actual observed read audit, in addition to each
                # executed model's internal checks where present.
                need(path in parent['files'] and parent['files'][path] == digest,
                     'Every inherited implicit input matches genuine original observed source-program input')
                counts['inherited_implicit_JSON_inputs_sealed'] += 1
                supplemental.append(path)
            if provider and path in provider['files']:
                need(provider['files'][path] == digest, 'Provider already exposed input has same immutable identity')
            counts['complete_consumed_source_program_JSON_inputs'] += 1
        need(counts['inherited_implicit_JSON_inputs_sealed'] == 20,
             'Exactly twenty inherited hardcoded source-program JSON inputs receive explicit closure')
        # Preserve caller code and all source_program read occurrences, rather
        # than crediting a broad directory scan or inference as runtime reads.
        (out / 'source-program-read-correspondence.json').write_text(json.dumps(observations, indent=2) + '\n', encoding='utf-8')
        pin(out / 'source-program-read-correspondence.json')
        counts['observed_independent_bounded_read_occurrences'] = len(observations)
        counts['independently_constructed_program_rows'] = len(program)
        counts['independently_constructed_callback_PC_rows'] = len(callbacks)
        passed = True
    except Exception as failure:
        error = repr(failure)
    finally:
        Path.read_bytes = raw_read
        Path.read_text = text_read
        report = dict(passed=passed, scope='Additive physically verified hardcoded source-program JSON closure and exact caller/input correspondence; bounded independent program construction only',
                      source_report=str(source_path.resolve()), source_sha256=SOURCE_HASH,
                      provider_report=str(provider_path) if provider_path != 'none' else None,
                      provider_sha256=PINS.get(str(provider_path)) if provider_path != 'none' else None,
                      inherited_observed_read_report_sha256=PARENT_HASH, counts=dict(counts),
                      producing_native_consumer_runtime_read_tracing=False,
                      independent_bounded_source_program_reads_observed=True,
                      whole_capture_consumption_repeated=False, captures_opened=0,
                      initializer_credit=False, error=error, files=PINS)
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(dict(passed=passed, report_sha256=hashlib.sha256((out / 'report.json').read_bytes()).hexdigest(), counts=dict(counts), error=error)))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
