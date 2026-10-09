"""Exact frozen hardware validators over strict bundles, with matched timings."""
import contextlib
import hashlib
import json
import pathlib
import statistics
import sys
import time
from transport import (ANCHORS, BASE, BUILD, CATEGORIES, SOURCES, CaptureBundle,
    LogicalReader, add, anchored_inputs, expected_tree, load_validator, need,
    normalized, read_json, semantic_workload, sha_file, validate_inventory, workspace_path)
from manifests import verify_manifest
from paths import publish_bytes
from reader_controls import run_controls


def seconds(start):
    return (time.perf_counter_ns() - start) / 1e9


def main(preparation_path, preparation_sha, directory):
    out = workspace_path(directory, reports=True)
    need(out.parent == BASE and not out.exists(), 'Fresh immediate review-bundle hardware proof')
    need(sha_file(preparation_path) == preparation_sha, 'External complete transport preparation SHA')
    prep = read_json(preparation_path)
    need(prep['passed'] and prep['build_sha256'] == ANCHORS[str(BUILD)] and prep['logical_files'] == 130064,
         'Complete exact frozen fixture transport preparation')
    build = anchored_inputs()
    validator, association = load_validator()
    out.mkdir(parents=True)
    files = {}
    for p, h in {**ANCHORS, **SOURCES, **prep['files']}.items():
        add(files, p, h)
    add(files, preparation_path, preparation_sha)
    for p in pathlib.Path(__file__).parent.iterdir():
        if p.is_file():
            add(files, p, sha_file(p))
    add(files, sys.executable, sha_file(sys.executable))
    expected, flat_roots = {}, {}
    capture_prefixes = []
    for level in ('O0', 'O2'):
        root, source_sha = expected_tree(build, level)
        flat_roots[level] = root
        capture_prefixes.append(normalized(str(root)) + '\\')
        row = prep['levels'][level]
        need(sha_file(row['inventory_path']) == row['inventory_sha256'], 'External prepared logical inventory SHA')
        inventory = read_json(row['inventory_path'])
        need(set(inventory) == {'files'} and isinstance(inventory['files'], dict), 'Exact prepared inventory schema')
        expected[level] = inventory['files']
        need(tuple(expected[level]) == tuple(source_sha) and
             {n: v['sha256'] for n, v in expected[level].items()} == source_sha,
             'Every logical digest remains admitted by frozen build artifact manifest')
    historical_capture_bindings = 0
    for category in CATEGORIES:
        for p, h in build.get(category, {}).items():
            key = normalized(p)
            if any(key.startswith(prefix) for prefix in capture_prefixes):
                historical_capture_bindings += 1
            else:
                add(files, p, h)
    need(historical_capture_bindings == 130064, 'Only proven-equivalent actual flat captures leave current physical closure')
    startup_start = time.perf_counter_ns()
    with contextlib.ExitStack() as stack:
        bundles, readers = {}, {}
        level_open = {}
        for level in ('O0', 'O2'):
            start = time.perf_counter_ns()
            row = prep['levels'][level]
            bundle = stack.enter_context(CaptureBundle(row['bundle_path'], row['sha256']))
            validate_inventory(bundle, expected[level])
            level_open[level] = seconds(start)
            bundles[level] = bundle
            readers[level] = LogicalReader(expected[level], bundle=bundle)
        full_open_seconds = seconds(startup_start)
        first_start = time.perf_counter_ns()
        proof = semantic_workload(readers, validator, keep_controls=True)
        first_semantic_seconds = seconds(first_start)
        # Alternate order under the same already-warm filesystem conditions.
        # Both backends run the exact 264 actual-pair + 548-control workload.
        timings = {'flat_strict_reader': [], 'retained_bundle_strict_reader': []}
        workload_checks = []
        for repetition in range(5):
            order = ('flat_strict_reader', 'retained_bundle_strict_reader') if repetition % 2 == 0 else (
                     'retained_bundle_strict_reader', 'flat_strict_reader')
            for kind in order:
                active = {level: LogicalReader(expected[level], **({'flat': flat_roots[level]} if kind == 'flat_strict_reader'
                          else {'bundle': bundles[level]})) for level in ('O0', 'O2')}
                start = time.perf_counter_ns()
                result = semantic_workload(active, validator)
                timings[kind].append(seconds(start))
                workload_checks.append({k: result[k] for k in ('actual_hardware_raw80_before_fixtures',
                    'actual_complete_legacy_tag_before_fixtures', 'meaningful_corruption_denials', 'logical_reads')})
        baseline = readers['O0']
        transport_controls = run_controls(out, baseline.read_bytes('case-1/entry-host-before.bin'),
                                           baseline.read_bytes('case-1/entry-host-after.bin'))
    for p in (out / 'reader-controls').iterdir():
        if p.is_file():
            add(files, p, sha_file(p))
    # One full byte/hash verification of every CURRENT source/tool/receipt,
    # noncapture native artifact and aggregate. No size/mtime cache exists.
    closure = verify_manifest(files)
    flat = statistics.median(timings['flat_strict_reader'])
    bundled = statistics.median(timings['retained_bundle_strict_reader'])
    report = {'passed': True, 'scope': 'Additive bundled transport of the exact frozen independent hardware review',
        'build_path': str(BUILD), 'build_sha256': ANCHORS[str(BUILD)],
        'preparation_path': str(preparation_path), 'preparation_sha256': preparation_sha,
        'validator_association': association, 'proof': proof, 'reader_controls': transport_controls,
        'complete_equivalent_logical_files': 130064, 'direct_host_records': 264,
        'meaningful_semantic_corruption_denials': 548, 'historical_flat_capture_bindings': historical_capture_bindings,
        'fresh_reader_full_aggregate_inventory_verify_seconds': full_open_seconds,
        'fresh_reader_level_open_seconds': level_open, 'first_bundled_semantic_workload_seconds': first_semantic_seconds,
        'packing_seconds_separate': {level: row['pack_seconds'] for level, row in prep['levels'].items()},
        'flat_bundle_byte_equivalence_seconds_separate': {level: row['flat_bundle_byte_equivalence_seconds']
            for level, row in prep['levels'].items()},
        'warm_repetitions_per_backend': 5, 'warm_workload': 'All 264 actual raw80/legacy pairs plus the same 548 semantic controls',
        'warm_times_seconds': timings, 'warm_workload_records': workload_checks,
        'flat_strict_reader_median_seconds': flat, 'retained_bundle_strict_reader_median_seconds': bundled,
        'measured_warm_semantic_reader_ratio': flat / bundled, 'current_physical_closure': closure,
        'files': files, 'metadata_only_cache_used': False, 'old_sources_or_captures_modified': False,
        'new_native_executions': False, 'original_executed': False, 'ordinary_game_launched': False,
        'guest_machine_expectations_derived_from_AFTER': False, 'extraction_used': False,
        'volatile_XMM0_5_equality_claimed': False, 'OS_cold_cache_claimed': False,
        'whole_project_speedup_claimed': False, 'whole_M4_complete': False,
        'limits': ['First reader opens follow preparation; they are cold-reader starts, not OS-cold cache measurements',
            'The flat timing uses the identical strict logical adapter and validators, not the old whole closure script',
            'Semantic corruption overlays are explicit in-memory adversarial fixtures for both backends',
            'Full source/native baseline artifacts remain bound; only byte-equivalent flat captures are historical anchors',
            'Packing, full entry-equivalence proof and aggregate startup costs are measured separately']}
    publish_bytes(out / 'pins.json', (json.dumps({'files': dict(sorted(files.items()))}, indent=2) + '\n').encode())
    report['pins_sha256'] = sha_file(out / 'pins.json')
    publish_bytes(out / 'report.json', (json.dumps(report, indent=2) + '\n').encode())
    print(json.dumps({'passed': True, 'report_sha256': sha_file(out / 'report.json'),
        'direct_host_records': 264, 'semantic_denials': 548, 'transport_denials': transport_controls['denials'],
        'warm_ratio': flat / bundled, 'current_physical_dependencies': closure['unique_physical_dependencies']}))


if __name__ == '__main__':
    main(*sys.argv[1:])
