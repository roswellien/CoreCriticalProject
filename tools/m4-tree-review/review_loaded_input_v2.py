"""Bounded finite relation for two authentic MSVCP initialized input pages.

This reads sealed source exports and 4096-byte inputs, never capture payloads.
Endpoint carry remains an obligation of the actual paired consumer.
"""
import collections
import hashlib
import json
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
import review_connected125_v2 as C


def main(name):
    out = ROOT / 'reports/m4-tree-review' / name
    C.need(not out.exists(), 'Fresh loaded-input review')
    out.mkdir(parents=True)
    counts = collections.Counter()
    passed = False
    error = None
    observations = []
    try:
        C.pin(__file__)
        C.pin(C.__file__)
        native_prep = C.read(ROOT / 'reports/m4-tree-native/preparation-r5/report.json',
                             C.EXPECTED['reports/m4-tree-native/preparation-r5/report.json'])
        original_path = ROOT / 'reports/m4-tree-original/original125-validation-r1/report.json'
        original = C.read(original_path, '5a7911dee3f77d504a5a28cf66de2be7cc0b159a15a4e81282368a24d3a45534')
        C.need(original['passed'] and native_prep['passed'], 'Authentic executed original and frozen native inputs')
        original_input = original_path.parent / 'post-DllMain-78145000-page.bin'
        original_bytes = C.pin(original_input, original['files'][str(original_input.resolve())]).read_bytes()
        native_bytes = C.pin(native_prep['loaded_input_page'], native_prep['loaded_input_page_sha256']).read_bytes()
        C.need(len(original_bytes) == len(native_bytes) == 4096, 'Both entire bootstrap input pages')
        differences = [dict(offset=i, original=a, native=b) for i, (a, b) in enumerate(zip(original_bytes, native_bytes)) if a != b]
        domain = {r['offset'] for r in differences}
        fields = sorted({offset & ~3 for offset in domain})
        C.need(len(domain) == 71 and len(fields) == 25, 'Exact fresh finite differing-byte and DWORD domains')
        C.need(original_bytes[0x640:0x65c] == native_bytes[0x640:0x65c] and
               struct.unpack_from('<I', original_bytes, 0x658)[0] == 2,
               'Complete CS24 and state2 source input domain is byte-identical')
        counts['whole_bootstrap_input_pages'] = 2
        counts['explicit_loaded_input_difference_bytes'] = len(domain)
        counts['explicit_loaded_input_difference_DWORDs'] = len(fields)

        source_path = ROOT / 'reports/m4-tree-source/connected-native125-source-r2/report.json'
        source = C.read(source_path, '02fbae62687ca09d73c8c05ae86981c02570208b2a3ae92faea8b81ac9509f76')
        C.lineage(source)
        native_cases = C.output(source, source_path.parent, 'Tree-source-derivations.json')
        original_tree_path = ROOT / 'reports/m4-tree-source/original125-source-r1/report.json'
        tree = C.read(original_tree_path, '884abbe43d69570265b2b8539d04455bdb622664d136b0055b8ab073a8735c5f')
        old_path = ROOT / 'reports/m4-tree-original/old-Lockit-source-r3/report.json'
        old = C.read(old_path, '2ebc48e5f6dd213e77b33bea8dda79ef2cd4a46b9e48997f6f346cd4e01d6c2c')
        old_ledgers = C.output(old, old_path.parent, 'original-source-access-ledgers.json')
        ledger_cases = [('native', (row['level'], row['sequence']), row['source']['source_accesses'], 34)
                        for row in native_cases]
        for case in tree['cases']:
            receipt = Path(case['receipt'])
            row = C.read(receipt, case['sha256'])
            ledger_cases.append(('original-tree', case['sequence'],
                                 C.output(row, receipt.parent, 'source-derivations.json')['source_accesses'], 26))
        for row in old_ledgers:
            ledger_cases.append(('original-old4', (row['sequence'], row['root']), row['rows'], 2))
        for branch, case, ledger, expected in ledger_cases:
            operands = [r for r in ledger if r[1] < 0x78146000 and r[1] + r[3] > 0x78145000]
            C.need(len(operands) == expected, 'Entire finite source RW-page operand domain')
            for row in operands:
                C.need(row[0] in (0x7810a290, 0x7810a350) and row[1:] == [0x78145658, 2, 4, 0],
                       'Every reached source RW operand is the identical four-byte state2 read')
                C.need(not (set(range(row[1] - 0x78145000, row[1] - 0x78145000 + row[3])) & domain),
                       'No selected source operand reads or writes any differing bootstrap byte')
                counts['native_literal_state2_operand_joins' if branch == 'native' else 'original_literal_state2_operand_joins'] += 1
            observations.append(dict(branch=branch, case=case, source_rows=len(ledger), RW_operands=operands))

        provider_path = ROOT / 'reports/m4-tree-source/native125-provider-r2/report.json'
        provider = C.read(provider_path, 'ad2b8c376e9cad7790750556f0292d8d1bb764b690dba37c667c3bc382c0a95f')
        C.lineage(provider)
        relations = C.output(source, source_path.parent, 'Lockit-source-derivations.json')
        for case in relations:
            C.need(len(case['API_relations']) == 34, 'Every selected actual source/API call')
            for relation in case['API_relations']:
                words = relation['actual_API_words']
                C.need(words[2] in (0x7810a30b, 0x7810a35e) and words[20] == relation['guest_CS'] == 0x78145640,
                       'Both actual selected APIs operate on the exact disjoint CS24 source region')
                C.need(not (set(range(0x640, 0x658)) & domain), 'No API semantic input/output byte overlaps differing bootstrap fields')
                counts['native_API_disjoint_CS24_joins'] += 1
        C.need(counts['native_literal_state2_operand_joins'] == 408 and
               counts['original_literal_state2_operand_joins'] == 204 and
               counts['native_API_disjoint_CS24_joins'] == 408,
               'Complete independent finite native/original/source/API access extent')
        passed = True
    except BaseException as exc:
        error = repr(exc)
        raise
    finally:
        artifact = out / 'input-domain.json'
        artifact.write_text(json.dumps(dict(differences=locals().get('differences', []),
                                           differing_DWORDs=locals().get('fields', []),
                                           observations=observations), indent=2) + '\n')
        C.pin(artifact)
        report = dict(passed=passed, error=error, scope='Two complete authentic loaded input pages with exact finite difference and disjoint reached operand/API domains; paired endpoint own-page carry required separately',
                      counts=dict(counts), whole_original_input_page=str(locals().get('original_input', '')), whole_native_input_page=locals().get('native_prep', {}).get('loaded_input_page'), whole_original_input_page_sha256=hashlib.sha256(locals().get('original_bytes', b'')).hexdigest(),
                      whole_native_input_page_sha256=hashlib.sha256(locals().get('native_bytes', b'')).hexdigest(),
                      paired_endpoint_capture_reads=0, endpoint_carry_acceptance=False, whole_page_mask=False,
                      opaque_pointer_target_equivalence=False, native_DllMain_credit=False,
                      whole_M4_complete=False, initializer_credit=False, files=C.PINS)
        path = out / 'report.json'
        path.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(dict(passed=passed, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), counts=dict(counts))))


if __name__ == '__main__':
    main(sys.argv[1])
