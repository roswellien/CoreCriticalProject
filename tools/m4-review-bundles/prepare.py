"""Pack complete frozen fixture trees and prove every original byte binding."""
import hashlib
import json
import pathlib
import sys
import time
from transport import (ANCHORS, BASE, BUILD, SOURCES, CaptureBundle, add, anchored_inputs,
    expected_tree, need, sha_file, validate_inventory, workspace_path)
from capture_bundle import pack_capture
from paths import publish_bytes


def main(directory):
    out = workspace_path(directory, reports=True)
    need(out.parent == BASE and not out.exists(), 'Fresh immediate review-bundle preparation')
    out.mkdir(parents=True)
    started = time.perf_counter_ns()
    build = anchored_inputs()
    files = {}
    for p, h in {**ANCHORS, **SOURCES}.items():
        add(files, p, h)
    for p in pathlib.Path(__file__).parent.iterdir():
        if p.is_file():
            add(files, p, sha_file(p))
    add(files, sys.executable, sha_file(sys.executable))
    levels = {}
    for level in ('O0', 'O2'):
        source, expected = expected_tree(build, level)
        packed = pack_capture(source, out / (level + '.mwb'))
        add(files, packed['bundle_path'], packed['sha256'])
        comparison_start = time.perf_counter_ns()
        inventory = {}
        with CaptureBundle(packed['bundle_path'], packed['sha256']) as reader:
            need(reader.names() == tuple(expected), 'Complete pinned artifact tree inventory')
            for name, frozen_sha in expected.items():
                flat = (source / name).read_bytes()
                data = reader.read_bytes(name)
                need(hashlib.sha256(flat).hexdigest() == frozen_sha, 'Original physical capture matches build artifact SHA')
                need(data == flat, 'Every actual flat/bundled capture byte is equal')
                inventory[name] = {'size_bytes': len(flat), 'sha256': frozen_sha}
            validate_inventory(reader, inventory)
        inventory_path = out / (level + '-inventory.json')
        publish_bytes(inventory_path, (json.dumps({'files': inventory}, indent=2) + '\n').encode())
        add(files, inventory_path, sha_file(inventory_path))
        levels[level] = {**packed, 'inventory_path': str(inventory_path),
            'inventory_sha256': sha_file(inventory_path),
            'flat_bundle_byte_equivalence_seconds': (time.perf_counter_ns() - comparison_start) / 1e9,
            'build_artifact_source_path': str(source), 'all_original_entry_bytes_verified': True,
            'logical_extent_authority': 'Byte-identical original data whose SHA is fixed by the external build receipt'}
        print(json.dumps({'level': level, 'logical_files': len(inventory), 'pack_seconds': packed['pack_seconds'],
                          'equivalence_seconds': levels[level]['flat_bundle_byte_equivalence_seconds']}), flush=True)
    report = {'passed': True, 'scope': 'Full frozen independent fixture transport byte/inventory equivalence only',
        'build_path': str(BUILD), 'build_sha256': ANCHORS[str(BUILD)], 'anchors': ANCHORS,
        'levels': levels, 'logical_files': sum(v['logical_files'] for v in levels.values()),
        'elapsed_seconds': (time.perf_counter_ns() - started) / 1e9, 'files': files,
        'flat_captures_modified': False, 'extraction_used': False, 'new_native_executions': False,
        'guest_machine_expectations_derived_from_AFTER': False, 'whole_M4_complete': False}
    publish_bytes(out / 'report.json', (json.dumps(report, indent=2) + '\n').encode())
    print(json.dumps({'passed': True, 'report_sha256': sha_file(out / 'report.json'),
                      'logical_files': report['logical_files']}))


if __name__ == '__main__':
    main(sys.argv[1])
