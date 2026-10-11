"""Seal the additive auxiliary byte and explicit page coverage comparer change."""
from pathlib import Path
import ast, hashlib, json, sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def main(name):
    out = ROOT / 'reports/m4-lockit-paired-provider' / name
    assert not out.exists()
    paths = [ROOT / relative for relative in ('tools/m4-lockit-paired-provider/paired_v2.py', 'tools/m4-lockit-paired-provider/paired_v3.py', 'reports/m4-lockit-paired-provider/paired-preparation-r2/report.json', 'reports/m4-lockit-paired-provider/paired-r1/report.json', 'reports/m4-lockit-source/recovery-r1/instruction-contracts.json', 'reports/m4-lockit-source/connected-native-source-r3/report.json', 'reports/m4-lockit-source/connected-native-source-r3/Lockit-header-derivations.json', 'reports/m4-lockit-paired-provider/original-r2/original-source-access-ledgers.json', Path(__file__).resolve())]
    assert sha(paths[2]) == 'b8a170186d5fafb2feeb10cc4b7d84e773ae47f7683e7f98e70ce8a7d1675f77'
    assert sha(paths[3]) == '39480ecfd301a466faa33697fb4017cf904b17b7ca7aa0bcc315430e172cdeb5'
    assert sha(paths[4]) == 'c102e277742f2cd6e2a352f9e40f44f7d7d2ea1107d8bde242d103b586e75f25'
    assert sha(paths[5]) == '5aea52d95b8a84ab0c8ae273604af7121ae3f2b88763610fd5d18a51fc99533f'
    old = json.loads(paths[3].read_bytes())
    assert old['passed'] is False and old['counts']['paired124_sequences'] == 12 and old['counts']['paired_phases'] == 1488
    ast.parse(paths[1].read_text())
    instruction = next(row for row in json.loads(paths[4].read_bytes())['instructions'] if row['pc'] == 0x50068b)
    assert instruction['bytes_hex'] == '881590bf6000' and instruction['operands'] == 'byte ptr [0x60bf90], dl'
    native = [row for row in json.loads(paths[6].read_bytes()) if row['field'] == 0x60bf90]
    original = [row for case in json.loads(paths[7].read_bytes()) if case['root'] == 0x500660 for row in case['rows'] if row[0] == 0x50068b and row[1] == 0x60bf90]
    assert len(native) == 12 and all(row['write_pc'] == 0x50068b for row in native) and len(original) == 6 and all(row[3:] == [1, 1] for row in original)
    report = dict(passed=True, scope='Additive paired comparer preparation: literal root500660 auxiliary byte plus explicit41 ordinary/one complete loader page coverage', native_reader_opened=False, initializer_credit=False, previous_full_data_checks_completed=12, failed_final_counter_receipt_preserved=True, auxiliary_source_instruction=instruction, expected_ordinary_nonstack_page_relations=122016, expected_separate_loader_page_relations=2976, expected_combined42_nonstack_page_endpoint_relations=124992, expected_branch_derivations=216, genuine_original_auxiliary_source_writes=original, native_source_auxiliary_rows=native, files={str(path.resolve()): sha(path) for path in paths})
    out.mkdir(parents=True)
    path = out / 'report.json'
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=True, sha256=sha(path), path=str(path))))

if __name__ == '__main__':
    main(sys.argv[1])
