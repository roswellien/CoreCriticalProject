"""Bounded policy controls using sealed source exports, never capture inputs."""
import collections
import copy
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
PINS = {}


def need(value, message):
    if not value:
        raise ValueError(message)


def pin(path, digest=None):
    path = Path(path).resolve()
    raw = path.read_bytes()
    measured = hashlib.sha256(raw).hexdigest()
    need(digest is None or digest == measured, 'Exact bounded input ' + str(path))
    PINS[str(path)] = measured
    return raw


def read(path, digest=None):
    return json.loads(pin(path, digest))


class DerivedMappingAdapter:
    """Only derived fixture exports; it is not an actual capture reader."""
    def __init__(self, source):
        self.values = {}
        rows = []
        for owner in source['owners']:
            row = [0] * 32
            for index, value in ((2, 0x4b7f70), (4, owner['CALL_pc']), (7, owner['requested']),
                                 (16, owner['guest']), (17, owner['native']), (18, owner['generation']),
                                 (19, owner['capacity']), (21, 1), (23, 1)):
                row[index] = value
            rows.append(struct.pack('<32Q', *row))
            prefix = f'locale-allocation-{owner["generation"]}'
            self.values[prefix + '-initial.bin'] = bytes.fromhex(owner['initial_hex'])
            page = bytes.fromhex(owner['source_final_hex']) + bytes(4096 - owner['capacity'])
            self.values[prefix + '-expected.bin'] = page
            self.values[prefix + '-owned-page.bin'] = page
        self.values['mfc-allocation-witnesses.bin'] = b''.join(rows)

    def data(self, key):
        return self.values[key]


def change_scalar_owner(original, native):
    # Old range-based relation would accept a coincidental owner value in a
    # key/scalar field in both branches. The typed helper must retain raw values.
    for source in (original, native):
        owner = source['owners'][2]
        value = source['owners'][0]['guest']
        raw = bytearray.fromhex(owner['source_final_hex'])
        raw[12:16] = value.to_bytes(4, 'little')
        owner['source_final_hex'] = raw.hex()


def main():
    helper = ROOT / 'tools/m4-tree-paired/tree_relations_v2.py'
    paired = ROOT / 'tools/m4-tree-paired/paired_v2.py'
    out = ROOT / 'reports/m4-tree-review/pair-helper-r2'
    need(not out.exists(), 'Fresh bounded helper review')
    out.mkdir(parents=True)
    counts = collections.Counter()
    results = []
    passed = False
    error = None
    try:
        pin(__file__)
        pin(helper); pin(paired)
        spec = importlib.util.spec_from_file_location('reviewed_typed_tree_pair', helper)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        contracts = read(ROOT / 'reports/m4-tree-source/dynamic-contracts-r1/normal-contracts.json',
                         'fbdd6e79dc26328ae2bd6a2e02d264971eaa190251d589f085904ffd9486829c')
        originals = read(ROOT / 'reports/m4-tree-source/original125-source-r1/report.json')
        fixture_path = ROOT / 'reports/m4-tree-source/native-fixture-source-r5/report.json'
        fixture = read(fixture_path, 'feb1e72cb81526104ff64284bcfb1cb9a04ffbc5059eb84b7c3c1331b8a3c255')
        artifact = fixture_path.parent / 'source-derivations.json'
        native = read(artifact, fixture['files'][str(artifact.resolve())])
        need(fixture['passed'] and fixture['native_whole_stack_compared'] and len(native) == 2,
             'Sealed actual fixture literal source is the bounded test input')
        sources = []
        for row in originals['cases']:
            receipt = Path(row['receipt'])
            sealed = read(receipt, row['sha256'])
            artifact = receipt.parent / 'source-derivations.json'
            source = read(artifact, sealed['files'][str(artifact.resolve())])
            sources.append(source)
            for branch in native:
                fields, measured = module.compare(source, branch, DerivedMappingAdapter(branch), '', contracts)
                need(len(fields) == 19, 'Exact finite source static byte declaration domain')
                counts['bounded_positive_policy_pairs'] += 1
                counts.update(measured)
        original = sources[0]
        branch = native[0]
        scenarios = [
            ('scalar-owner-coincidence', change_scalar_owner),
            ('interior-node-link', lambda a, b: b['owned_accesses'][4].update(value=b['owners'][0]['guest'] + 4)),
            ('wrong-repeated-owner', lambda a, b: b['owned_accesses'][10].update(owner_invocation_ordinal=1)),
            ('wrong-owned-role', lambda a, b: b['owned_accesses'][10].update(owner_index=3)),
            ('wrong-owned-PC', lambda a, b: b['owned_accesses'][10].update(pc=0x4bab43)),
            ('wrong-owned-width', lambda a, b: b['owned_accesses'][10].update(bytes=1)),
            ('wrong-link-value-role', lambda a, b: b['owned_accesses'][4].update(value=b['owners'][1]['guest'])),
            ('saved-local-store-value', lambda a, b: b['static_field_writes'][0].update(value=b['static_field_writes'][0]['value'] ^ 1)),
            ('saved-local-read-PC', lambda a, b: b['source_accesses'][next(i for i, r in enumerate(b['source_accesses']) if r[0] == 0x4b7da0)].__setitem__(0, 0x4b7da1)),
            ('saved-local-read-address', lambda a, b: b['source_accesses'][next(i for i, r in enumerate(b['source_accesses']) if r[0] == 0x4b7da0)].__setitem__(1, 0x200017d4)),
            ('own-tail-changed', lambda a, b: b['owners'][0].update(source_final_hex=b['owners'][0]['source_final_hex'][:62] + 'ff')),
            ('raw-static-counter-owner', lambda a, b: b['static_field_writes'][4].update(value=b['owners'][0]['guest'])),
        ]
        for name, mutate in scenarios:
            a, b = copy.deepcopy(original), copy.deepcopy(branch)
            mutate(a, b)
            refusal = None
            try:
                module.compare(a, b, DerivedMappingAdapter(b), '', contracts)
            except ValueError as failure:
                refusal = str(failure)
            need(refusal is not None, 'Altered finite policy input must be refused: ' + name)
            results.append(dict(name=name, refused=True, first_reason=refusal))
            counts['bounded_policy_refusal_controls'] += 1
        need("tree_relations_v2.py" in paired.read_text() and "tree_causal_contract" in paired.read_text(),
             'Full paired tool consumes the reviewed causal typed helper')
        passed = True
    except Exception as failure:
        error = repr(failure)
    finally:
        report = dict(passed=passed, scope='Independent bounded typed helper/source policy controls; synthesized mapping adapter from sealed source exports only',
                      counts=dict(counts), controls=results, captures_opened=0, actual_capture_credit=False,
                      full125_paired_execution_review_pending=True, initializer_credit=False, error=error, files=PINS)
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(dict(passed=passed, report_sha256=hashlib.sha256((out / 'report.json').read_bytes()).hexdigest(), counts=dict(counts), error=error)))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
