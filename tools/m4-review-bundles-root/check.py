"""Independent byte/inventory and unchanged-validator association check.

This transports already accepted hardware evidence; it grants no new native
execution or guest-machine equivalence beyond that original receipt.
"""
import ast
import copy
import hashlib
import json
import ntpath
import sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
from capture_bundle import CaptureBundle, sha_file
from manifests import normalized, unique_object, verify_manifest
from paths import logical_name, publish_bytes, workspace_path

BASE = ROOT / 'reports/m4-review-bundles'
FIXTURE = ROOT / 'reports/m4-crt-commandline-carry/independent-compiled-r4/build.json'
ANCHORS = {
    str(FIXTURE): 'f5d75b4c08bbd218216674858468a5e204d89383679c279caf5011c945d9405d',
    str(BASE / 'preparation-r1/report.json'): '8e01fd37fb0f15f9998696fb1a64c6dcbc675d0319ff06435f61910a4dc12a11',
    str(BASE / 'review-r1/report.json'): '98bc8760f94a9b3f604d922e95f5af762cf7459d61b43c24d1d8dbc074953a09',
    str(BASE / 'review-r1/pins.json'): 'b56780bea99171d54ee3242ff3b342a7321aa95787f96ef466724f27e6f9f329',
}


def need(ok, why):
    if not ok:
        raise ValueError(why)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique_object)


def inventory(reader, expected):
    need(reader.names() == tuple(sorted(expected)), 'Exact independent external logical inventory')
    for name, binding in expected.items():
        logical_name(name)
        need(isinstance(binding, dict) and set(binding) == {'size_bytes', 'sha256'} and
             type(binding['size_bytes']) is int and binding['size_bytes'] >= 0,
             'Exact independent logical schema and extent')
        value = reader.read_bytes(name)
        need(len(value) == binding['size_bytes'] and hashlib.sha256(value).hexdigest() == binding['sha256'],
             'Every logical byte remains bound to the original artifact digest')


def function_digest(path, name, nested=None):
    module = ast.parse(Path(path).read_text(encoding='utf-8'))
    node = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == name)
    if nested:
        node = next(n for n in node.body if isinstance(n, ast.FunctionDef) and n.name == nested)
    return hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()


def main(directory):
    out = workspace_path(directory, reports=True)
    need(out.parent == BASE and not out.exists(), 'Fresh root transport check output')
    files = {}

    def pin(path, expected=None):
        key = normalized(str(Path(path).absolute()))
        actual = sha_file(path)
        need(expected is None or actual == expected, 'External physical identity: ' + key)
        need(key not in files or files[key] == actual, 'Unambiguous root current identity')
        files[key] = actual
        return Path(path)

    for p, h in ANCHORS.items():
        pin(p, h)
    prep, proof = read(BASE / 'preparation-r1/report.json'), read(BASE / 'review-r1/report.json')
    build = read(FIXTURE)
    need(prep['passed'] and proof['passed'] and proof['complete_equivalent_logical_files'] == 130064 and
         proof['direct_host_records'] == 264 and proof['meaningful_semantic_corruption_denials'] == 548 and
         proof['reader_controls']['denials'] == 37, 'Exact completed transport and hardware scope')
    need(not proof['new_native_executions'] and not proof['original_executed'] and
         not proof['whole_project_speedup_claimed'] and not proof['OS_cold_cache_claimed'] and
         not proof['whole_M4_complete'], 'Transport and timing credit stays bounded')
    need(proof['build_sha256'] == ANCHORS[str(FIXTURE)] and
         proof['preparation_sha256'] == ANCHORS[str(BASE / 'preparation-r1/report.json')],
         'Current exact preparation/build association')
    association = proof['validator_association']
    old_review = pin(ROOT / 'tools/m4-crt-commandline-carry-review/review.py',
                     '0c2f00ee443de979a5a3afb49d53b6450f4ca34aa4840afdb28a497df5f539da')
    old_observer = pin(ROOT / 'tools/m4-crt-commandline-carry-review/check_observer.py',
                       '930b9ad91cda9485b6e7c0ba5c98aa3425258eb52e18f52f7e9247c63cadc980')
    need(function_digest(old_review, 'host_pair') == association['host_pair_AST_sha256'] and
         function_digest(old_observer, 'main', 'validate') == association['validate_AST_sha256'] and
         not association['validator_bodies_modified'] and association['physical_pin_transport_replaced'],
         'Both semantic validator bodies are identical to the independently accepted sources')
    source_pins = read(BASE / 'review-r1/pins.json')['files']
    capture_prefixes, levels, first_pair = [], {}, None
    for level in ('O0', 'O2'):
        original_root = FIXTURE.parent / level / 'actual'
        prefix = normalized(str(original_root)) + '\\'
        capture_prefixes.append(prefix)
        expected_sha = {}
        for path, digest in build['artifacts'].items():
            if normalized(path).startswith(prefix):
                name = logical_name(Path(path).relative_to(original_root).as_posix())
                need(name not in expected_sha, 'Independent unique original logical name')
                expected_sha[name] = digest
        row = prep['levels'][level]
        original_inventory = read(pin(row['inventory_path'], row['inventory_sha256']))['files']
        need(len(expected_sha) == 65032 and set(expected_sha) == set(original_inventory) and
             {name: value['sha256'] for name, value in original_inventory.items()} == expected_sha,
             'Every logical inventory binding is still anchored to the original native build')
        archive = pin(row['bundle_path'], row['sha256'])
        with CaptureBundle(archive, row['sha256']) as reader:
            inventory(reader, original_inventory)
            if level == 'O0':
                first_pair = (reader.read_bytes('case-1/entry-host-before.bin'),
                              reader.read_bytes('case-1/entry-host-after.bin'))
        levels[level] = dict(logical_files=len(expected_sha), archive_sha256=row['sha256'],
                             every_entry_hash_and_extent_verified=True)
    # The current closure must actually drop only the proven flat capture trees.
    need(all(not any(normalized(p).startswith(prefix) for prefix in capture_prefixes) for p in source_pins),
         'No hidden flat capture rehash remains in the admitted current dependency set')
    for p, h in source_pins.items():
        key = normalized(p)
        need(key not in files or files[key] == h, 'Root/proof current dependency conflict')
        files[key] = h
    expected = {'after.bin': {'size_bytes': len(first_pair[1]), 'sha256': hashlib.sha256(first_pair[1]).hexdigest()},
                'before.bin': {'size_bytes': len(first_pair[0]), 'sha256': hashlib.sha256(first_pair[0]).hexdigest()}}
    control_dir = BASE / 'review-r1/reader-controls'
    valid = pin(control_dir / 'valid.mwb')
    with CaptureBundle(valid, sha_file(valid)) as reader:
        inventory(reader, expected)
    denials = []
    for test in proof['reader_controls']['tests']:
        path = pin(test['path'], test['sha256'])
        admitted = copy.deepcopy(expected)
        label = test['label']
        external = test['sha256']
        if label in ('aggregate_changed_original_external_pin', 'aggregate_truncated_original_external_pin',
                     'aggregate_trailing_original_external_pin'):
            external = sha_file(valid)
        elif label == 'aggregate_wrong_external_pin':
            external = '0' * 64
        elif label == 'external_expected_size_changed':
            admitted['before.bin']['size_bytes'] += 1
        elif label == 'external_expected_digest_changed':
            admitted['before.bin']['sha256'] = '0' * 64
        elif label == 'external_expected_bool_size':
            admitted['before.bin']['size_bytes'] = True
        elif label == 'external_expected_schema_extra':
            admitted['before.bin']['extra'] = 1
        try:
            with CaptureBundle(path, external) as reader:
                inventory(reader, admitted)
        except ValueError:
            denials.append(label)
        else:
            raise ValueError('Root reader accepted published control: ' + label)
    need(len(denials) == len(set(denials)) == 37, 'All distinct published transport controls independently refused')
    warm = proof['warm_workload_records']
    need(len(warm) == 10 and all(v == warm[0] for v in warm) and
         warm[0]['actual_hardware_raw80_before_fixtures'] == 264 and
         warm[0]['actual_complete_legacy_tag_before_fixtures'] == 264 and
         warm[0]['meaningful_corruption_denials'] == 548, 'Matched warm workload rather than reduced semantic checking')
    pin(__file__)
    pin(sys.executable)
    closure = verify_manifest(files)
    out.mkdir()
    publish_bytes(out / 'pins.json', (json.dumps(dict(files=dict(sorted(files.items()))), indent=2) + '\n').encode('utf-8'))
    report = dict(passed=True, scope='Independent strict aggregate equivalence and unchanged hardware-validator transport association',
        levels=levels, equivalent_logical_files=130064, actual_hardware_pairs_preserved=264,
        unchanged_hardware_semantic_denials=548, independent_transport_denials=denials,
        current_physical_closure=closure, files=files, pins_sha256=sha_file(out / 'pins.json'),
        current_native_executions=False, original_executed=False, guest_machine_seeded_from_AFTER=False,
        whole_M4_complete=False, end_to_end_speedup_claimed=False)
    publish_bytes(out / 'report.json', (json.dumps(report, indent=2) + '\n').encode('utf-8'))
    print(json.dumps({k: v for k, v in report.items() if k not in ('files', 'independent_transport_denials')}))


if __name__ == '__main__':
    main(*sys.argv[1:])
