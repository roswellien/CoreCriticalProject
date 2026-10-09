"""Independent strict-reader parity and same-input direct-emission measurement."""
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
from capture_bundle import CaptureBundle, pack_capture, sha_file
from manifests import unique_object, verify_manifest
from paths import publish_bytes, workspace_path
from stages import run_stage, verify_stage

FROZEN = (
    ('O0-positive', '078a843e5ed8363545a65426e0028ef3187e364b958f956f885e475d01b78fbc'),
    ('O2-positive', '620dcd7001a4ec2ecbfc415cd7718830dcf7bde976cd07946a943a8ebacffe8d'),
    ('O0-early-fault', '798c898e49547a5bbb6c0ca9aa8d85cb34a715a89e50492fa1a91d54c01ad8eb'),
    ('O2-late-fault', '99c0045b7a02e8cd421b1836a9485fd0103ff6c1e346286dd70f8e49f7c72b66'))


def need(ok, why):
    if not ok:
        raise ValueError(why)


def record_input(items):
    data = bytearray(b'MW34REC1' + struct.pack('<I', len(items)))
    for name, raw in items:
        name = name.encode('ascii')
        data += struct.pack('<IQ', len(name), len(raw)) + name + raw
    return data


def read_set(directory, expected):
    """Verify every actual archive byte with the existing independent reader."""
    seen, parts, elapsed = {}, [], 0.0
    physical = sorted(p for p in directory.rglob('*') if p.is_file())
    archives = sorted(directory.glob('*.mwb'))
    need(archives, 'Direct native archives exist')
    need(all(p.parent == directory for p in physical), 'No per-record directories or flat capture files')
    manifest = json.loads((directory / 'transport.json').read_bytes(), object_pairs_hook=unique_object)
    need(set(manifest) == {'emit_seconds', 'finalize_parts_seconds', 'format', 'logical_files',
                          'native_executed', 'parts', 'passed', 'payload_bytes', 'transport_only'} and manifest['passed'] is True and
         manifest['format'] == 'mw34.capture.direct.v1' and manifest['native_executed'] is False and
         manifest['transport_only'] is True, 'Exact transport-only complete-set manifest')
    need(all(type(manifest[k]) in (int, float) and math.isfinite(manifest[k]) and manifest[k] >= 0
             for k in ('emit_seconds', 'finalize_parts_seconds')), 'Finite distinct transport phase durations')
    need(set(physical) == {*archives, directory / 'transport.json'}, 'Only archives and transport manifest are published')
    claims = manifest['parts']
    need(len(claims) == len(archives) and len({p['bundle'] for p in claims}) == len(claims),
         'Exact unique complete manifest parts')
    part_claims = {p['bundle']: p for p in claims}
    for archive in archives:
        digest = sha_file(archive)
        need(archive.name in part_claims, 'Actual archive is named by complete manifest')
        claim = part_claims[archive.name]
        need(set(claim) == {'bundle', 'bundle_bytes', 'index_bytes', 'index_sha256', 'logical_files',
                           'payload_bytes', 'sha256'} and claim['sha256'] == digest and
             claim['bundle_bytes'] == archive.stat().st_size, 'Manifest archive size and external hash association')
        with archive.open('rb') as stream:
            magic, index_bytes, index_digest = struct.unpack('<8sQ32s', stream.read(48))
        need(magic == b'MW34CAP1' and claim['index_bytes'] == index_bytes and
             claim['index_sha256'] == index_digest.hex(), 'Manifest canonical index association')
        started = time.perf_counter_ns()
        with CaptureBundle(archive, digest) as reader:
            payload_bytes = 0
            for name in reader.names():
                need(name not in seen, 'Strict parts have disjoint exact logical names')
                raw = reader.read_bytes(name)
                payload_bytes += len(raw)
                need(name in expected and raw == expected[name], 'Exact independent logical byte parity: ' + name)
                seen[name] = dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
            count = len(reader.names())
            need(count == claim['logical_files'] and payload_bytes == claim['payload_bytes'],
                 'Actual archive logical/payload counts agree with manifest')
        elapsed += (time.perf_counter_ns() - started) / 1e9
        parts.append(dict(path=str(archive), sha256=digest, logical_files=count))
    need(set(seen) == set(expected), 'Complete exact disjoint capture union')
    need(manifest['logical_files'] == len(seen) and
         manifest['payload_bytes'] == sum(v['bytes'] for v in seen.values()), 'Exact complete-set manifest totals')
    return dict(parts=parts, logical_files=len(seen), physical_files=len(physical),
                payload_bytes=sum(v['bytes'] for v in seen.values()), verify_and_compare_seconds=elapsed,
                emit_seconds=manifest['emit_seconds'], finalize_parts_seconds=manifest['finalize_parts_seconds'])


def main(driver_path, driver_sha, directory):
    out = workspace_path(directory, reports=True)
    need(out.parent == ROOT / 'reports/m4-capture-direct-root' and not out.exists(), 'Fresh independent report')
    driver = workspace_path(driver_path)
    need(sha_file(driver) == driver_sha, 'Externally fixed native driver')
    files = {}

    def pin(path, digest=None):
        path = Path(path).absolute()
        actual = sha_file(path)
        need(digest is None or actual == digest, 'Fixed content identity: ' + str(path))
        files[str(path)] = actual
        return path

    pin(driver, driver_sha)
    build_path = pin(ROOT / 'reports/m4-capture-direct/build-r1/build.json',
                     '9d9424b37c45ec1a4f72f0925072e671a901510b747acffefec731879f9bb1c6')
    build = json.loads(build_path.read_bytes(), object_pairs_hook=unique_object)
    need(build['passed'] is True and build['artifacts'].get(str(driver)) == driver_sha,
         'Actual fixed driver belongs to the successful native compile')
    for category in ('sources', 'tools', 'artifacts', 'libraries', 'compiler_read_headers'):
        for path, digest in build.get(category, {}).items():
            pin(path, digest)
    for path in (Path(__file__), Path(sys.executable), *(ROOT / 'tools/m4-pipeline' / name
                 for name in ('capture_bundle.py', 'paths.py', 'manifests.py', 'stages.py'))):
        pin(path)
    items = []
    for label, digest in FROZEN:
        path = pin(ROOT / 'reports/m4-pipeline/benchmark-r3' / (label + '.mwb'), digest)
        with CaptureBundle(path, digest) as reader:
            items.extend((label + '/' + name, reader.read_bytes(name)) for name in reader.names())
    need(len(items) == 2945, 'Exact previously frozen representative corpus')
    expected = dict(items)
    need(len(expected) == len(items), 'Unique frozen representative paths')
    out.mkdir(parents=True)
    input_path = publish_bytes(out / 'representative.records', record_input(list(reversed(items))))
    pin(input_path)

    def run(label, mode, input_path, target, success=True, options=()):
        stage = out / ('stage-' + label)
        request = [str(driver), mode, str(input_path), str(target), *map(str, options)]
        result = run_stage(request, stage, timeout_seconds=180, inputs=[driver, input_path])
        stage_digest = sha_file(stage / 'stage.json')
        need(verify_stage(stage, stage_digest)['recorded_stage_passed'] == success, 'Actual native stage status')
        need(result['passed'] == success and (success or result['status'] == 'nonzero_exit'), 'Native exit matches request')
        for name in ('stage.json', 'stdout.bin', 'stderr.bin'):
            pin(stage / name)
        return dict(stage=str(stage), stage_sha256=stage_digest, seconds=result['elapsed_seconds'])

    direct = out / 'direct'
    direct_stage = run('direct', 'replay', input_path, direct)
    direct_result = read_set(direct, expected)
    for p in direct.iterdir():
        if p.is_file():
            pin(p)
    flat = out / 'flat-benchmark-only'
    flat_stage = run('flat', 'flat', input_path, flat)
    flat_inventory = {p.relative_to(flat).as_posix(): p for p in flat.rglob('*') if p.is_file()}
    need(set(flat_inventory) == set(expected), 'Same-input legacy benchmark inventory')
    for name, path in flat_inventory.items():
        need(path.read_bytes() == expected[name], 'Same-input legacy benchmark byte parity')
    packed_path = out / 'legacy-benchmark.mwb'
    packed = pack_capture(flat, packed_path)
    pin(packed_path, packed['sha256'])
    started = time.perf_counter_ns()
    with CaptureBundle(packed_path, packed['sha256']) as reader:
        need(set(reader.names()) == set(expected), 'Legacy benchmark archive exact inventory')
        for name in reader.names():
            need(reader.read_bytes(name) == expected[name], 'Legacy benchmark archive byte parity')
    legacy_verify = (time.perf_counter_ns() - started) / 1e9

    edge_items = [('z/empty.bin', b''), ('a/all-bytes.bin', bytes(range(256))),
                  ('a/quote$-safe.bin', b'\x00\xff\n\r'), ('a/space name.bin', b'payload')]
    edge_input = publish_bytes(out / 'edges.records', record_input(edge_items))
    pin(edge_input)
    edge_target = out / 'edges'
    edge_stage = run('edges', 'replay', edge_input, edge_target)
    edge_result = read_set(edge_target, dict(edge_items))
    for p in edge_target.iterdir():
        if p.is_file():
            pin(p)
    partitions = []
    for label, options, count in (
            ('count', ('--files-per-part', 2), 2),
            ('bytes', ('--bytes-per-part', 260), 2),
            ('index', ('--index-bytes-per-part', 300), 4),
            ('explicit', ('--close-every', 1), 4)):
        target = out / ('parts-' + label)
        result_stage = run('parts-' + label, 'replay', edge_input, target, options=options)
        result = read_set(target, dict(edge_items))
        need(len(result['parts']) == count, 'Actual bounded partition count')
        for p in target.iterdir():
            if p.is_file():
                pin(p)
        partitions.append(dict(control=label, stage=result_stage, **result))
    denials = []
    bad_cases = [('duplicate', [('same.bin', b'1'), ('same.bin', b'2')]),
                 ('case-alias', [('Same.bin', b'1'), ('same.bin', b'2')]),
                 ('traversal', [('../escape.bin', b'x')]), ('absolute', [('/escape.bin', b'x')]),
                 ('backslash', [('a\\b.bin', b'x')]), ('device', [('a/CON.bin', b'x')]),
                 ('trailing-dot', [('a/b.', b'x')]), ('colon', [('a:b.bin', b'x')]),
                 ('control', [('a/\x01.bin', b'x')]), ('empty-component', [('a//b.bin', b'x')])]
    for label, records in bad_cases:
        path = publish_bytes(out / (label + '.records'), record_input(records))
        pin(path)
        target = out / ('refused-' + label)
        stage = run(label, 'replay', path, target, success=False)
        need(not target.exists(), 'Failed append publishes no completed capture set')
        denials.append(dict(label=label, **stage))
    occupied = out / 'occupied'
    occupied.mkdir()
    marker = publish_bytes(occupied / 'keep.bin', b'Original destination bytes')
    pin(marker)
    occupied_stage = run('no-overwrite', 'replay', edge_input, occupied, success=False)
    need(marker.read_bytes() == b'Original destination bytes' and list(occupied.iterdir()) == [marker],
         'Existing destination remains exact after refused publication')
    denials.append(dict(label='no-overwrite', **occupied_stage))
    failed_target = out / 'refused-partial-write'
    failed_stage = run('partial-write', 'replay', edge_input, failed_target, success=False,
                       options=('--files-per-part', 2, '--fail-after', 1200))
    need(not failed_target.exists(), 'Partial multi-part write publishes no completed set')
    denials.append(dict(label='partial-write', **failed_stage))
    truncated = publish_bytes(out / 'truncated.records', record_input(edge_items)[:-1])
    pin(truncated)
    truncated_target = out / 'refused-truncated'
    truncated_stage = run('truncated', 'replay', truncated, truncated_target, success=False,
                          options=('--close-every', 1))
    need(not truncated_target.exists(), 'Late malformed input cannot publish completed earlier parts')
    denials.append(dict(label='truncated', **truncated_stage))
    need(sha_file(input_path) == files[str(input_path)], 'Replay input remains immutable')
    report = dict(passed=True, scope='Direct native capture transport; no game source-equivalence credit',
                  direct=direct_result, direct_stage=direct_stage,
                  legacy_flat_stage=flat_stage, legacy_pack_seconds=packed['pack_seconds'],
                  legacy_verify_and_compare_seconds=legacy_verify,
                  direct_seconds=direct_stage['seconds'] + direct_result['verify_and_compare_seconds'],
                  legacy_seconds=flat_stage['seconds'] + packed['pack_seconds'] + legacy_verify,
                  same_reversed_input=True, frozen_logical_files=2945, edge_cases=edge_result,
                  edge_stage=edge_stage, refusal_controls=denials, direct_main_per_record_files=0,
                  bounded_partition_controls=partitions,
                  current_physical_closure=verify_manifest(files), files=files,
                  performance_scope='One representative local emission/finalization/verification workload; no whole-project ratio',
                  original_or_game_executed=False, native_transport_driver_executed=True, whole_M4_complete=False)
    report['measured_workload_ratio'] = report['legacy_seconds'] / report['direct_seconds']
    publish_bytes(out / 'report.json', (json.dumps(report, indent=2) + '\n').encode())
    print(json.dumps({k: v for k, v in report.items() if k not in ('files', 'refusal_controls')}))


if __name__ == '__main__':
    main(*sys.argv[1:])
