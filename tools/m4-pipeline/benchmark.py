"""Measure strict transport of frozen captures; supplies no new game execution."""
import contextlib
import hashlib
import json
import statistics
import sys
import time
from pathlib import Path
from capture_bundle import CaptureBundle, sha_file
from manifests import normalized
from paths import ROOT, publish_bytes, workspace_path
from stages import run_stage, verify_stage

BASE = ROOT / 'reports/m4-crt-mainargs/root-execution-r1'
BASE_PINS_SHA = '2d151a4b0b83da3a23bf379ee8a911f769884d2b68bb93844ffe91de4d4bc606'
ACCEPTANCE = ROOT / 'reports/m4-crt-mainargs/root-acceptance-r1/report.json'
ACCEPTANCE_SHA = '47a7ee8c611c936cd74190903c8f2a306d6e713242e6b0f43263a6172b07cf35'
CASES = [('O0-positive', 'native-O0/row-0', 0), ('O2-positive', 'native-O2/row-0', 0),
    ('O0-early-fault', 'native-O0/row-26', 3), ('O2-late-fault', 'native-O2/row-83', 60)]


def main(directory):
    output = workspace_path(directory, reports=True)
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    if sha_file(BASE / 'pins.json') != BASE_PINS_SHA or sha_file(ACCEPTANCE) != ACCEPTANCE_SHA:
        raise ValueError('Frozen accepted capture identity changed')
    pins = json.loads((BASE / 'pins.json').read_text(encoding='utf-8'))['files']
    pins = {normalized(name): digest for name, digest in pins.items()}
    tools = [Path(__file__), *[Path(__file__).parent / name for name in
        ('capture_bundle.py', 'paths.py', 'stages.py', 'manifests.py')]]
    evidence = {str(path): sha_file(path) for path in tools + [Path(sys.executable), BASE / 'pins.json', ACCEPTANCE]}
    rows = []
    for label, relative, control in CASES:
        source = BASE / relative
        bundle_path = output / (label + '.mwb')
        stage_path = output / ('pack-' + label)
        stage = run_stage([sys.executable, str(Path(__file__).parent / 'capture_bundle.py'),
            'pack', str(source), str(bundle_path)], stage_path, required_outputs=[bundle_path],
            inputs=tools + [BASE / 'pins.json', ACCEPTANCE])
        if not stage['passed']:
            raise ValueError('Capture pack stage failed: ' + str(stage_path))
        verify_stage(stage_path, sha_file(stage_path / 'stage.json'))
        packed = json.loads((stage_path / 'stdout.bin').read_text(encoding='utf-8'))
        if packed['sha256'] != sha_file(bundle_path):
            raise ValueError('Packed capture hash mismatch')
        for name in ('stdout.bin', 'stderr.bin', 'stage.json'):
            evidence[str(stage_path / name)] = sha_file(stage_path / name)
        evidence[str(bundle_path)] = packed['sha256']
        names = tuple(sorted(p.relative_to(source).as_posix() for p in source.rglob('*') if p.is_file()))
        expected = {name: pins[normalized(str(source / name))] for name in names}
        result = json.loads((source / 'result.json').read_text(encoding='utf-8'))
        if result['control'] != control:
            raise ValueError('Representative capture role changed')
        rows.append(dict(label=label, source=source, bundle_path=bundle_path, packed=packed,
            names=names, expected=expected, control=control, flat_seconds=[], bundle_read_seconds=[]))
    with contextlib.ExitStack() as stack:
        for row in rows:
            start = time.perf_counter_ns()
            row['reader'] = stack.enter_context(CaptureBundle(row['bundle_path'], row['packed']['sha256']))
            row['bundle_open_and_full_verify_seconds'] = (time.perf_counter_ns() - start) / 1e9
            if row['reader'].names() != row['names']:
                raise ValueError('Frozen/bundled logical inventory mismatch')
        for repetition in range(3):
            order = ('flat', 'bundle') if repetition % 2 == 0 else ('bundle', 'flat')
            for kind in order:
                for row in rows:
                    start = time.perf_counter_ns()
                    for name in row['names']:
                        data = (row['source'] / name).read_bytes() if kind == 'flat' else row['reader'].read_bytes(name)
                        if hashlib.sha256(data).hexdigest() != row['expected'][name]:
                            raise ValueError('Frozen logical file SHA mismatch: ' + name)
                    seconds = (time.perf_counter_ns() - start) / 1e9
                    row['flat_seconds' if kind == 'flat' else 'bundle_read_seconds'].append(seconds)
    results = []
    for row in rows:
        results.append(dict(label=row['label'], control=row['control'], source=str(row['source']),
            bundle_path=str(row['bundle_path']), bundle_sha256=row['packed']['sha256'],
            logical_files=len(row['names']), payload_bytes=row['packed']['payload_bytes'],
            bundle_bytes=row['packed']['bundle_bytes'], pack_seconds=row['packed']['pack_seconds'],
            bundle_open_and_full_verify_seconds=row['bundle_open_and_full_verify_seconds'],
            flat_seconds=row['flat_seconds'], bundle_read_seconds=row['bundle_read_seconds'],
            flat_median_seconds=statistics.median(row['flat_seconds']),
            bundle_read_median_seconds=statistics.median(row['bundle_read_seconds'])))
    flat = sum(row['flat_median_seconds'] for row in results)
    bundled = sum(row['bundle_read_median_seconds'] for row in results)
    report = dict(passed=True, scope='Representative frozen-capture transport only',
        rows=results, logical_files=sum(row['logical_files'] for row in results),
        payload_bytes=sum(row['payload_bytes'] for row in results), repetitions=3,
        flat_median_total_seconds=flat, bundle_read_median_total_seconds=bundled,
        bundle_full_open_verify_seconds=sum(row['bundle_open_and_full_verify_seconds'] for row in results),
        measured_warm_read_ratio=flat / bundled,
        limits=['Warm local filesystem with alternating ordering, four representative rows only',
            'Reader startup full verification and pack conversion costs recorded separately',
            'Every logical byte hash compared with the frozen root execution manifest',
            'No original/native rerun, new semantic comparison or whole-project speedup claim',
            'Old flat captures and receipts stay unchanged; old observers are not silently redirected'],
        original_executed=False, native_executed=False, old_sources_modified=False,
        whole_M4_complete=False, files=evidence)
    publish_bytes(output / 'report.json', (json.dumps(report, indent=2) + '\n').encode('utf-8'))
    print(json.dumps(dict(passed=True, logical_files=report['logical_files'],
        measured_warm_read_ratio=report['measured_warm_read_ratio'],
        report_sha256=sha_file(output / 'report.json'))))


if __name__ == '__main__':
    main(sys.argv[1])
