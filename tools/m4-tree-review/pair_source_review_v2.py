"""Independent bounded review of tree pairing types and original125 exports.

No capture reader is opened. The source receipts retain responsibility for
actual execution and source reconstruction; this review checks their exported
finite type, occurrence, backing and saved-local provenance contracts.
"""
import collections
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PINS = {}


def need(value, label):
    if not value:
        raise ValueError(label)


def pin(path, expected=None):
    path = Path(path).resolve()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    need(expected is None or digest == expected, 'Exact bounded dependency ' + str(path))
    PINS[str(path)] = digest
    return path


def read(path, expected=None):
    return json.loads(pin(path, expected).read_bytes())


def own_value(row, owners, expected_role):
    """Source field types govern normalization, never numeric coincidence."""
    offset = row['offset']
    value = row['value']
    need(row['bytes'] == 4, 'Exact DWORD owned operand')
    if offset in (0, 4, 8):
        if expected_role is None:
            need(value == 0, 'Only source-null pointer field may have no owner role')
            return ('null',)
        need(value == owners[expected_role]['guest'], 'Exact live source owner base, no interior offset')
        return ('owner-base', expected_role)
    need(expected_role is None, 'Scalar or borrowed field cannot normalize as an owner')
    if offset == 12:
        need(value in range(5), 'Literal key scalar')
    elif offset == 16:
        need(value in (0, 0x5e88cc, 0x5e88c4, 0x5e88bc, 0x5e88b4, 0x5e88a8),
             'Exact borrowed static pointer or initial null')
    elif offset == 20:
        need(value in (0, 1), 'Exact color scalar')
    else:
        need(False, 'No undeclared owned field')
    return ('raw', value)


def saved_locals(source):
    accesses = source['source_accesses']
    invocation = next(x for x in source['function_invocations'] if x['entry'] == 0x4b7f80)
    entry_esp = invocation['frame'][1]
    address = entry_esp - 41
    facts = []
    for read_pc, store_pc, destination, ri, wi in (
        (0x4b7d98, 0x4b7daf, 0x60b2f8, 6, 12),
        (0x4b7da0, 0x4b7da6, 0x60b2f9, 9, 10),
    ):
        read_row, write_row = accesses[ri], accesses[wi]
        need(read_row == [read_pc, address, read_row[2], 1, 0], 'Exact physical saved-local source read')
        need(write_row == [store_pc, destination, read_row[2], 1, 1], 'Exact own-branch read-to-store byte')
        need(not any(r[4] and r[1] <= address < r[1] + r[3] for r in accesses[:ri]),
             'Saved-local byte comes from untouched current phase BEFORE stack')
        declarations = [r for r in source['static_field_writes'] if r['pc'] == store_pc]
        need(len(declarations) == 1 and declarations[0] == dict(
            pc=store_pc, address=destination, width=1, value=read_row[2], source_access_index=wi),
            'Exactly one saved-local declaration with complete source-access identity')
        facts.append(dict(read_PC=read_pc, write_PC=store_pc, read_index=ri, write_index=wi,
                          read_address=address, entry_ESP=entry_esp, value=read_row[2],
                          static_address=destination, prior_source_store=False))
    return facts


def main():
    out = ROOT / 'reports/m4-tree-review/pair-source-r2'
    need(not out.exists(), 'Fresh bounded review directory')
    out.mkdir(parents=True)
    counts = collections.Counter()
    passed = False
    report = {}
    try:
        pin(__file__)
        pairing = pin(ROOT / 'tools/m4-tree-paired/tree_relations.py')
        recovery = read(ROOT / 'reports/m4-tree-source/recovery-r1/instruction-contracts.json',
                        'a3e74efdaaca40677dbd27c24924c9a20f955fd3d7f67fa75164ee93d3ca34d8')
        instructions = {r['pc']: r for r in recovery['instructions']}
        for pc, raw in ((0x4b7d98, '8a442403'), (0x4b7da0, '8a4c240b'),
                        (0x4b7da6, '884e01'), (0x4b7daf, '8806')):
            need(instructions[pc]['bytes_hex'] == raw, 'Exact physical saved-local instruction')
            counts['physical_saved_local_instructions'] += 1
        contracts = read(ROOT / 'reports/m4-tree-source/dynamic-contracts-r1/normal-contracts.json',
                         'fbdd6e79dc26328ae2bd6a2e02d264971eaa190251d589f085904ffd9486829c')
        baseline = read(ROOT / 'reports/m4-tree-source/original-source-r3/source-derivations.json',
                        '406cfc6f8f14b0d97e66e501cf105e48dcc9f1d2db9d3706cb02755aee2c3475')
        gate = read(ROOT / 'reports/m4-tree-source/original125-source-r1/report.json')
        need(gate['passed'] and len(gate['cases']) == 6, 'All genuine current original125 cases')
        rows = []
        for case in gate['cases']:
            receipt = Path(case['receipt'])
            sealed = read(receipt, case['sha256'])
            need(sealed['passed'] and not sealed['candidate_AFTER_machine_seed'], 'Literal own original branch')
            artifact = receipt.parent / 'source-derivations.json'
            source = read(artifact, sealed['files'][str(artifact.resolve())])
            owners = source['owners']
            need(len(owners) == 7 and not source['candidate_AFTER_seed'], 'Finite seven actual original roles')
            local = saved_locals(source)
            counts['exact_saved_local_read_store_joins'] += len(local)
            accesses = source['owned_accesses']
            need(len(accesses) == len(contracts['owned_causal_order']) == 172, 'Exact complete owned order')
            capacities = [bytearray.fromhex(o['initial_hex']) for o in owners]
            for index, (owner, role) in enumerate(zip(owners, contracts['owners'])):
                keys = ('index', 'root', 'CALL_pc', 'per_site_invocation_ordinal', 'function_invocation', 'requested', 'capacity', 'role')
                need(tuple(owner[k] for k in keys) == tuple(role[k] for k in keys), 'Repeated owner source role identity')
                need(owner['index'] == index and owner['capacity'] == 32 and len(capacities[index]) == 32,
                     'Whole own initial backing')
            for ordinal, (access, contract, original) in enumerate(zip(accesses, contracts['owned_causal_order'], baseline['owned_accesses'])):
                need((access['owner_index'], access['source_access_index'], access['pc'], bool(access['write']), access['bytes'], access['offset']) ==
                     (contract['owner_role_index'], contract['source_access_index'], contract['pc'], contract['write'], contract['bytes'], contract['offset']),
                     'Exact original125 PC/width/role/order')
                owner = owners[access['owner_index']]
                need((access['generation'], access['owner_pointer'], access['address'], access['owner_CALL_pc'], access['owner_invocation_ordinal']) ==
                     (owner['generation'], owner['guest'], owner['guest'] + access['offset'], owner['CALL_pc'], owner['per_site_invocation_ordinal']),
                     'Actual current role/generation/address')
                value = own_value(access, owners, contract['value_owner_role_index'])
                if value[0] == 'raw':
                    need(access['value'] == original['value'], 'Raw scalar/borrowed literal equality, no range identity')
                    counts['raw_scalar_or_borrowed_operands'] += 1
                else:
                    counts['nullable_exact_owner_base_operands'] += 1
                start = access['offset']; width = access['bytes']
                raw = access['value'].to_bytes(width, 'little')
                if access['write']:
                    capacities[access['owner_index']][start:start + width] = raw
                else:
                    need(capacities[access['owner_index']][start:start + width] == raw,
                         'Literal owner read retains own initial or latest source write')
                counts['exact_ordered_owned_accesses'] += 1
            for owner, final in zip(owners, capacities):
                need(bytes(final).hex() == owner['source_final_hex'], 'Whole own capacity replay including untouched bytes')
                counts['whole_original_capacity_replays'] += 1
            static = source['static_field_writes']
            need(len(static) == 12, 'Only twelve normal static stores')
            for row in static:
                if row['address'] in (0x60b2f8, 0x60b2f9):
                    continue
                if row['address'] in (0x60b314, 0x60b2fc):
                    role = 0 if row['address'] == 0x60b314 else 1
                    need(row['width'] == 4 and row['value'] == owners[role]['guest'], 'Exact typed static owner publication')
                    need(row['pc'] == (0x4ba315 if role == 0 else 0x4ba347), 'Physical static pointer declaration')
                    counts['typed_static_pointer_stores'] += 1
                else:
                    matches = [r for r in baseline['static_field_writes'] if (r['pc'], r['address'], r['width'], r['source_access_index']) ==
                               (row['pc'], row['address'], row['width'], row['source_access_index'])]
                    need(len(matches) == 1 and matches[0]['value'] == row['value'], 'Raw static scalar value and occurrence')
                    counts['raw_static_scalar_stores'] += 1
            rows.append(dict(sequence=case['sequence'], saved_local_derivations=local))
        report.update(original_cases=rows,
                      required_pair_policy=dict(owned_pointer_offsets=[0, 4, 8], owned_key_offset=12,
                                                owned_borrowed_static_offset=16, owned_color_offset=20,
                                                pointer_base_only=True, saved_local_read_before_store=True),
                      current_pair_policy_tightening=[
                          'Use source field type and exact role base for reads and writes; value_kind alone describes only required pointer writes.',
                          'Explicitly join exactly two saved-local source reads, exact current source frame address and unique static write occurrence.',
                      ], current_pair_policy_ready=False)
        passed = True
    except Exception as error:
        report['error'] = repr(error)
    finally:
        report.update(passed=passed, scope='Independent bounded physical/source-export review only; no capture consumer or initializer credit',
                      counts=dict(counts), captures_opened=0, initializer_credit=False, files=PINS)
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(dict(passed=passed, report_sha256=hashlib.sha256((out / 'report.json').read_bytes()).hexdigest(), counts=dict(counts), error=report.get('error'))))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
