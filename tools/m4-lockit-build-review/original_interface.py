"""Bind authenticated original owner observations to native field-order contracts.

This additive metadata derivation never opens a capture archive.
"""
from pathlib import Path
import hashlib, json, sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
PINS = {}
OWN = ('root', 'pc', 'write', 'bytes', 'owner_root', 'owner_CALL_pc', 'owner_offset')
PUB = ('root', 'CALL_pc', 'requested_size', 'object', 'publication', 'publication_PC', 'owner_root', 'owner_CALL_pc', 'owner_offset')

def need(value, message):
    if not value:
        raise ValueError(message)

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def unique(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, 'Duplicate JSON key')
        result[key] = value
    return result

def read(path, expected):
    path = Path(path).resolve()
    need(path.suffix != '.mwb', 'No archive reader in this gate')
    actual = sha(path)
    need(actual == expected, 'Exact physical input ' + str(path))
    PINS[str(path)] = actual
    return json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=unique)

def pin(report, relative):
    path = ROOT / relative
    matches = [value for name, value in report['files'].items() if Path(name).resolve() == path.resolve()]
    need(len(matches) == 1, 'Exact source proof pin ' + relative)
    return read(path, matches[0])

def fields(rows, keys):
    return [[int(row[key]) for key in keys] for row in rows]

def main(name):
    out = ROOT / 'reports/m4-lockit-build-review' / name
    need(not out.exists(), 'Fresh additive gate')
    original_path = ROOT / 'reports/m4-lockit-paired-provider/original-r2/report.json'
    original = read(original_path, '48f184d6edbaae5e1ec9d384f743089210e65dea9655822a4f517b41fa3b757b')
    interface_path = ROOT / 'reports/m4-lockit-source/owned-interface-r1/report.json'
    interface = read(interface_path, sha(interface_path))
    need(original['passed'] is True and interface['passed'] is True, 'Actual successful observations and source interface')
    source_report = pin(original, 'reports/m4-lockit-source/owned-contracts-r1/report.json')
    need(source_report['passed'] is True, 'Successful affine source derivation')
    need(original['source_contract_sha256'] == sha(ROOT / 'reports/m4-lockit-source/owned-contracts-r1/report.json'), 'Original report binds source contract')
    need(interface['files'][str(ROOT / 'reports/m4-lockit-source/owned-contracts-r1/report.json')] == original['source_contract_sha256'], 'Interface derives from exact original-corroborated source')
    owned = pin(original, 'reports/m4-lockit-source/owned-contracts-r1/shared-owner-accesses.json')
    publications = pin(original, 'reports/m4-lockit-source/owned-contracts-r1/allocation-inputs.json')
    contracts = read(interface['contracts'], interface['contracts_sha256'])
    need(set(contracts) == {'fs_owned_accesses', 'fs_inputs'}, 'Exact native contract shape')
    need(contracts['fs_owned_accesses'] == fields(owned, OWN) and len(owned) == 32, 'Complete ordered native ownership serialization')
    need(contracts['fs_inputs'] == fields(publications, PUB) and len(publications) == 8, 'Complete ordered native publication serialization')
    observed_owned = pin(original, 'reports/m4-lockit-paired-provider/original-r2/original-source-owned-contract-corroborations.json')
    observed_publications = pin(original, 'reports/m4-lockit-paired-provider/original-r2/original-source-publication-contract-corroborations.json')
    need(len(observed_owned) == 192 and len(observed_publications) == 48, 'Six authentic original cases')
    for sequence in range(6):
        current = [row for row in observed_owned if row['sequence'] == sequence]
        inputs = [row for row in observed_publications if row['sequence'] == sequence]
        need(fields(current, OWN) == contracts['fs_owned_accesses'], 'Actual ordered original ownership case')
        need(fields(inputs, PUB) == contracts['fs_inputs'], 'Actual ordered original publication case')
        need(all(row['source_address'] == row['owner_pointer'] + row['owner_offset'] for row in current), 'Actual source affine owner geometry')
    need(original['AFTER_machine_seed'] is False and original['observed_original_postRET'] is False, 'Original proof scope retained')
    PINS[str(Path(__file__).resolve())] = sha(__file__)
    out.mkdir(parents=True)
    report = dict(passed=True, scope='Independent metadata derivation of exact native field-order arrays from six authenticated original owner/publication cases', source_owned_contracts=32, source_publication_contracts=8, source_contract_sha256=interface['contracts_sha256'], original_source_contract_sha256=original['source_contract_sha256'], original_source_sha256=sha(original_path), source_interface_sha256=sha(interface_path), counts=dict(source_owned_contract_corroborations=192, source_publication_contract_corroborations=48, authentic_original_sequences=6), capture_archives_opened=False, AFTER_machine_seed=False, initializer_credit=False, files=PINS)
    path = out / 'report.json'
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=True, sha256=sha(path), path=str(path))))

if __name__ == '__main__':
    main(sys.argv[1])
