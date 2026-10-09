"""Strict additive transport of frozen independent-review artifacts."""
import ast
import hashlib
import importlib.util
import json
import pathlib
import struct
import sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).absolute().parents[2]
PIPELINE = ROOT / 'tools/m4-pipeline'
sys.path.insert(0, str(PIPELINE))
from capture_bundle import CaptureBundle, sha_file
from manifests import digest, normalized, unique_object
from paths import logical_name, workspace_path

BASE = ROOT / 'reports/m4-review-bundles'
BUILD = ROOT / 'reports/m4-crt-commandline-carry/independent-compiled-r4/build.json'
ANCHORS = {
    str(BUILD): 'f5d75b4c08bbd218216674858468a5e204d89383679c279caf5011c945d9405d',
    str(ROOT / 'reports/m4-crt-commandline-carry/independent-compiled-review-r1/report.json'):
        '82df266750a53b0e66f595029632675c118aa1e33e7c1c9176190749ed0857a1',
    str(ROOT / 'reports/m4-crt-commandline-carry/independent-compiled-observer-r1/report.json'):
        '78cbc271dac39ce63ddf3a968ab76b3a294bb73062980e822f284ef369ab2b34',
}
SOURCES = {
    str(ROOT / 'tools/m4-crt-commandline-carry-review/review.py'):
        '0c2f00ee443de979a5a3afb49d53b6450f4ca34aa4840afdb28a497df5f539da',
    str(ROOT / 'tools/m4-crt-commandline-carry-review/check_observer.py'):
        '930b9ad91cda9485b6e7c0ba5c98aa3425258eb52e18f52f7e9247c63cadc980',
    str(PIPELINE / 'capture_bundle.py'):
        '486ec0074d1a7e5171f7744dc23cd5b0acb5b1e104242e58749ae77ccb79f4e1',
    str(PIPELINE / 'paths.py'):
        'c17b154b5dc86074d4df85f64108fe2cc587dbe8dacc3f303bf1b4f4d865ef66',
    str(PIPELINE / 'manifests.py'):
        '67b56e5622a1d3dd1b0cbf4d6eb5de5a71a773f01ac2cf584ea5f97a03a4dd9b',
}
CATEGORIES = ('sources', 'source_files', 'tools', 'tool_files', 'libraries',
    'entry_objects', 'matherr_objects', 'control_objects', 'initterm_objects',
    'mainargs_objects', 'normal_argv_objects', 'commandline_objects',
    'producer_objects', 'compiler_read_headers', 'artifacts')


def need(ok, why):
    if not ok:
        raise ValueError(why)


def read_json(path):
    return json.loads(pathlib.Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique_object)


def add(files, path, expected):
    key = normalized(str(pathlib.Path(path).absolute()))
    expected = digest(expected)
    need(key not in files or files[key] == expected, 'Conflicting transport dependency: ' + key)
    files[key] = expected


def anchored_inputs():
    for path, expected in {**ANCHORS, **SOURCES}.items():
        need(sha_file(path) == expected, 'Frozen source/receipt identity: ' + path)
    build = read_json(BUILD)
    need(build['passed'] and not build['ordinary_game_launched'] and not build['original_executed'],
         'Frozen fixture build scope')
    review, observer = [read_json(p) for p in list(ANCHORS)[1:]]
    need(review['passed'] and review['checks'] == 4878 and review['scenarios'] == 132 and
         review['direct_host_records'] == 264 and review['malformed_token_denials'] == 42,
         'Frozen actual compiled review domain')
    need(observer['passed'] and observer['actual_hardware_raw80_before_fixtures'] == 264 and
         observer['actual_complete_legacy_tag_before_fixtures'] == 264 and
         observer['meaningful_corruption_denials'] == 548,
         'Frozen actual hardware observer domain')
    need(normalized(review['build_path']) == normalized(str(BUILD)) ==
         normalized(observer['compiled_build_path']), 'Frozen review/build association')
    return build


def expected_tree(build, level):
    root = BUILD.parent / level / 'actual'
    prefix = normalized(str(root)) + '\\'
    expected = {}
    for path, value in build['artifacts'].items():
        key = normalized(path)
        if key.startswith(prefix):
            name = logical_name(pathlib.Path(path).relative_to(root).as_posix())
            need(name not in expected, 'Unique pinned actual logical path')
            expected[name] = digest(value)
    need(len(expected) == 65032, 'Full frozen actual tree inventory')
    return root, dict(sorted(expected.items()))


def validate_inventory(reader, expected):
    """Same strict reader/inventory admission for real captures and controls."""
    need(reader.names() == tuple(sorted(expected)), 'Exact externally pinned logical inventory')
    for name, record in expected.items():
        logical_name(name)
        need(isinstance(record, dict) and set(record) == {'size_bytes', 'sha256'}, 'Exact logical binding schema')
        need(type(record['size_bytes']) is int and record['size_bytes'] >= 0, 'Exact logical extent type')
        data = reader.read_bytes(name)
        need(len(data) == record['size_bytes'], 'Externally associated logical extent')
        need(hashlib.sha256(data).hexdigest() == digest(record['sha256']), 'Externally pinned logical entry SHA')


class LogicalPath:
    def __init__(self, owner, name):
        self.owner, self.name = owner, logical_name(name)

    def read_bytes(self):
        return self.owner.read_bytes(self.name)


class LogicalReader:
    def __init__(self, expected, *, bundle=None, flat=None, overlay=None):
        need(sum(v is not None for v in (bundle, flat, overlay)) == 1, 'Exactly one explicit logical backend')
        self.expected, self.bundle, self.flat, self.overlay = expected, bundle, flat, overlay
        self.reads = 0

    def path(self, name):
        name = logical_name(name)
        need(name in self.expected, 'Logical path must have an admitted binding')
        return LogicalPath(self, name)

    def read_bytes(self, name):
        name = logical_name(name)
        need(name in self.expected, 'No unbound logical read')
        if self.bundle is not None:
            data = self.bundle.read_bytes(name)
        elif self.flat is not None:
            data = (self.flat / name).read_bytes()
        else:
            data = self.overlay[name]
        record = self.expected[name]
        need(len(data) == record['size_bytes'] and hashlib.sha256(data).hexdigest() == record['sha256'],
             'Strict logical read size/SHA binding')
        self.reads += 1
        return data


def overlay_paths(before, after):
    # Only explicit adversarial fixtures use this backend. No native machine
    # expectation or guest State is seeded from AFTER by this transport.
    values = {'before.bin': bytes(before), 'after.bin': bytes(after)}
    expected = {name: {'size_bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                for name, data in values.items()}
    reader = LogicalReader(expected, overlay=values)
    return reader.path('before.bin'), reader.path('after.bin')


def load_validator():
    """Use the two unchanged frozen validator bodies, not a mirrored test."""
    old_review, old_observer = [pathlib.Path(p) for p in list(SOURCES)[:2]]
    for path in (old_review, old_observer):
        need(sha_file(path) == SOURCES[str(path)], 'Frozen validator source identity')
    spec = importlib.util.spec_from_file_location('mw34_review_bundle_frozen_host', old_review)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Replaces only physical pin/read transport. The frozen host_pair body is
    # called unchanged and every ordinary read remains digest checked.
    def logical_pin(path, expected=None):
        need(isinstance(path, LogicalPath) and expected is None, 'Hardware validator requires explicit logical path')
        return path
    module.pin = logical_pin
    tree = ast.parse(old_observer.read_text(encoding='utf-8'))
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
    validate = next(node for node in main.body if isinstance(node, ast.FunctionDef) and node.name == 'validate')
    env = {'module': module, 'need': module.need, 'struct': struct}
    compile_tree = ast.Module(body=[validate], type_ignores=[])
    exec(compile(ast.fix_missing_locations(compile_tree), str(old_observer), 'exec'), env)
    association = {'host_pair_source_sha256': SOURCES[str(old_review)],
        'validate_source_sha256': SOURCES[str(old_observer)],
        'host_pair_AST_sha256': hashlib.sha256(ast.dump(next(n for n in ast.parse(old_review.read_text()).body
            if isinstance(n, ast.FunctionDef) and n.name == 'host_pair'), include_attributes=False).encode()).hexdigest(),
        'validate_AST_sha256': hashlib.sha256(ast.dump(validate, include_attributes=False).encode()).hexdigest(),
        'validator_bodies_modified': False, 'physical_pin_transport_replaced': True}
    return env['validate'], association


def semantic_workload(readers, validator, *, keep_controls=False):
    actual = 0
    domains = set()
    for level in ('O0', 'O2'):
        reader = readers[level]
        result = json.loads(reader.read_bytes('controls.json').decode('utf-8'), object_pairs_hook=unique_object)
        need(result['passed'] and result['checks'] == 2438 and result['scenarios'] == 66 and
             result['malformed_token_denials'] == 21, 'Exact frozen actual fixture control result')
        cases = sorted({n.split('/')[0] for n in reader.expected if n.startswith('case-')},
                       key=lambda n: int(n.split('-')[-1]))
        need(cases == ['case-' + str(i) for i in range(1, 67)], 'Full scenario logical inventory')
        for case in cases:
            scenario = int(case.split('-')[-1])
            for actor in ('writer', 'entry'):
                validator(reader.path(case + '/' + actor + '-host-before.bin'),
                          reader.path(case + '/' + actor + '-host-after.bin'), scenario)
                actual += 1
                domains.add((3 if scenario % 2 else 7, (0, 1, 3, 7)[scenario % 4]))
    need(actual == 264 and {t for t, d in domains} == {3, 7} and
         {d for t, d in domains} == {0, 1, 3, 7}, 'All frozen actual hardware domains')
    baseline = readers['O0']
    before = baseline.read_bytes('case-1/entry-host-before.bin')
    after = baseline.read_bytes('case-1/entry-host-after.bin')
    preservation = list(range(0, 5)) + list(range(24, 28))
    preservation += [32 + 16*i + k for i in range(8) for k in range(10)]
    preservation += [160 + 16*i + k for i in range(6, 16) for k in range(16)]
    preservation += list(range(512, 540))
    fixtures = list(range(0, 5)) + list(range(24, 28))
    fixtures += [32 + 16*i + k for i in range(8) for k in range(10)]
    fixtures += [160 + 16*i + k for i in range(6, 16) for k in range(16)]
    fixtures += [512, 513, 516, 517, 520, 521] + list(range(524, 538))
    denials, controls = 0, []
    for direction, offsets in (('after', preservation), ('coherent_wrong_before_fixture', fixtures)):
        for offset in offsets:
            b, a = bytearray(before), bytearray(after)
            a[offset] ^= 1
            if direction != 'after':
                b[offset] ^= 1
            paths = overlay_paths(b, a)
            try:
                validator(*paths, 1)
            except ValueError as error:
                reason = str(error)
            else:
                raise ValueError('Frozen validator accepted semantic corruption: ' + direction + '/' + str(offset))
            denials += 1
            if keep_controls:
                controls.append({'direction': direction, 'offset': offset, 'denied': True, 'reason': reason})
    for size in (543, 545):
        b = before[:size] if size < 544 else before + b'\0'
        try:
            validator(*overlay_paths(b, after), 1)
        except ValueError:
            pass
        else:
            raise ValueError('Frozen validator accepted host record extent corruption')
        denials += 1
        if keep_controls:
            controls.append({'direction': 'wrong_extent', 'bytes': size, 'denied': True})
    need(denials == 548, 'Exact unchanged semantic corruption domain')
    return {'actual_hardware_raw80_before_fixtures': actual,
        'actual_complete_legacy_tag_before_fixtures': actual, 'meaningful_corruption_denials': denials,
        'logical_reads': sum(r.reads for r in readers.values()), 'tests': controls}
