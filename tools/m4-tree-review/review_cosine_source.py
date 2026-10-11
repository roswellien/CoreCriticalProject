"""Independent bounded review of the explicit finite numerical-oracle seam."""
import ast
import collections
import hashlib
import json
import re
import struct
import sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
import review_connected125_v2 as C


def main(name):
    out = ROOT / 'reports/m4-tree-review' / name
    C.need(not out.exists(), 'Fresh finite numerical source review'); out.mkdir(parents=True)
    counts = collections.Counter(); passed = False
    try:
        C.pin(__file__); C.pin(C.__file__)
        area = ROOT / 'reports/m4-cosine-native'
        report = C.read(area / 'fixture-source-r1/report.json', '7f8ed5dd50a62574ce404cdd2081e592ab4cd111cd4423e2ef668e5367929045')
        C.need(report['passed'] and report['reader_closed'] and report['full_State_source_comparison'] and
               not report['candidate_AFTER_machine_seed'] and not report['original_AFTER_machine_seed'] and
               not report['independent_trigonometric_prediction'] and report['initializer_credit'] == 0,
               'Whole State source proof carries only an explicit finite original numerical reference')
        source_path = ROOT / 'tools/m4-cosine-native/source_model.py'
        source = C.pin(source_path, report['files'][str(source_path)]).read_text()
        comparer_path = ROOT / 'tools/m4-cosine-native/compare_source.py'
        comparer = C.pin(comparer_path, report['files'][str(comparer_path)]).read_text()
        tree = ast.parse(source)
        original_reads = [ast.unparse(n.slice) for n in ast.walk(tree) if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name) and n.value.id == 'original']
        C.need(set(original_reads) == {'2276 + start:2276 + start + 8', '178404 + start:178404 + start + 4', '628:1140'} and len(original_reads) == 3,
               'Only source input8, three numerical F32 slices, and bounded original FX container are read')
        C.need('state = bytearray(state_before)' in source and 'memory = bytearray(pages_before)' in source and
               "state[2486 + index * 16:2496 + index * 16] = fx[32 + index * 16:42 + index * 16]" in source and
               "sw = struct.unpack_from('<H', fx, 2)[0]" in source and 'for bit, at in SF:' in source and
               'before_sw & ~0x3800' in source and 'cpu[8] & ~0x8d5' in source,
               'Source reconstructs CPU/memory and only SW/raw80 field-sized numerical State effects')
        C.need("before = n[100:3604]" in comparer and "memory = n[9268:185396]" in comparer and
               "eq(result['state'], n[3604:7108]" in comparer and "eq(result['pages'], n[185396:361524]" in comparer and
               "eq(n[20:60], o[36:76]" in comparer and "eq(memory, o[2276:178404]" in comparer,
               'Whole current BEFORE inputs are authenticated, AFTER is only the comparison destination')
        prep_path = area / 'fixture-preparation-r1/report.json'
        prep = C.read(prep_path, report['files'][str(prep_path)])
        contract_path = ROOT / 'reports/m4-cosine-original/prefix-preparation-r2/instruction-contracts.json'
        contract = C.read(contract_path, report['files'][str(contract_path)])
        derivation_path = area / 'fixture-source-r1/derivations.json'
        derivations = C.read(derivation_path, report['files'][str(derivation_path)])
        cmp = C.read(area / 'fixture-comparison-r3/report.json', 'f65f414b929c9cedec5d34b6376b9e771a710a98f79e667550c28a143b950955')
        cmp_path = area / 'fixture-comparison-r3/observations.json'
        actual = {(r['level'],r['sequence']):r for r in C.read(cmp_path, cmp['files'][str(cmp_path)])}
        pages = prep['observed_pages']; C.need(len(pages) == 43 and len(set(pages)) == 43, 'All whole43 source pages')
        C.need(len(derivations) == 12 and {(r['level'],r['sequence']) for r in derivations} == set(actual), 'Exact current 12 actual native/source cases')
        for row in derivations:
            pack_path = area / 'fixture-preparation-r1' / ('input-' + str(row['sequence']) + '.bin')
            pack = C.pin(pack_path, prep['files'][str(pack_path)]).read_bytes()
            C.need(pack[:8] == b'MW4J124P', 'Immutable genuine BEFORE source pack')
            page_rows = {}
            for index in range(struct.unpack_from('<I',pack,8)[0]):
                offset = 12 + index * 4104; address, permissions = struct.unpack_from('<II',pack,offset)
                C.need(address not in page_rows and permissions in (0,1,2), 'Whole bounded unique admitted pages')
                page_rows[address] = pack[offset + 8:offset + 4104]
            before = b''.join(page_rows[p] for p in pages); after = bytearray(before)
            observed = actual[row['level'],row['sequence']]
            oracle = row['numerical_oracle']
            C.need(len(oracle['F32']) == 3 and len(oracle['raw80_hex']) == 8 and all(len(bytes.fromhex(x)) == 10 for x in oracle['raw80_hex']),
                   'Exactly three F32 and eight complete raw80 numerical values')
            C.need(not oracle['original_SW'] & 0x400, 'Actual finite FCOS argument range C2-clear only')
            outputs = {x['address']:x['F32_bits'] for x in observed['outputs']}
            expected_events = []
            for instruction in contract['instructions']:
                op, pc = instruction['mnemonic'], instruction['pc']
                if op in ('mov','fld','fstp'):
                    address = int(re.search(r'\[(0x[0-9a-f]+)\]',instruction['operands'])[1],16)
                    offset = pages.index(address & ~4095) * 4096 + (address & 4095)
                    if op == 'fld':
                        value = int.from_bytes(after[offset:offset+8],'little'); width = 8; writing = False
                        item = next(x for x in contract['inputs'] if x['address'] == address)
                        C.need(value.to_bytes(8,'little').hex() == item['bytes_hex'], 'Complete genuine default F64 input')
                        counts['whole_default_F64_source_values'] += 1
                    else:
                        width = 4; writing = True
                        if op == 'mov':
                            operand = instruction['operands'].split(',')[-1].strip(); value = 0 if operand == 'eax' else int(operand,0)
                            counts['independent_literal_scalar_writes'] += 1
                        else:
                            item = next(x for x in oracle['F32'] if x['pc'] == pc and x['address'] == address)
                            value = int.from_bytes(bytes.fromhex(item['bytes_hex']),'little')
                            C.need(value == outputs[address], 'Numerical seam equals only separately sealed actual original/native F32 observation')
                            counts['finite_F32_oracle_joins'] += 1
                        after[offset:offset+width] = value.to_bytes(width,'little')
                    expected_events.append(dict(pc=pc,address=address,width=width,writing=writing,value=value))
                elif op == 'ret':
                    address = 0x20001800; offset = pages.index(address & ~4095) * 4096 + (address & 4095)
                    value = int.from_bytes(after[offset:offset+4],'little')
                    C.need(value == 0x410a80, 'Genuine guest return frame source value')
                    expected_events.append(dict(pc=pc,address=address,width=4,writing=False,value=value))
                else:
                    C.need(op in ('jmp','fcos','xor'), 'Only literal supported compound source instructions')
            C.need(expected_events == row['accesses'] and len(expected_events) == 14, 'Every independent exact source operand value and order')
            C.need(hashlib.sha256(after).hexdigest() == row['source_pages_AFTER_sha256'], 'Independent whole43-page source reconstruction hash')
            counts['independent_literal_operand_values'] += 14; counts['independent_whole_page_effects'] += 43
            counts['bound_complete_State_source_cases'] += 1
        C.need(report['counts'] == dict(whole_State3504_AFTER=12,whole_CPU40_AFTER=12,whole43_page_AFTER=516,literal_source_instructions=228,
                                       exact_source_access_values=168,exact_immutable_F64_inputs=36,explicit_F32_numerical_oracles=36,
                                       explicit_original_SW_raw80_seams=12,source_root_phases=12), 'Exact producer full source proof counts')
        passed = True
    finally:
        result = dict(passed=passed,scope='Independent finite original numerical-oracle/source seam and full literal memory effect review; complete State equality is the bound producer gate',
                      counts=dict(counts),source_gate_sha256='7f8ed5dd50a62574ce404cdd2081e592ab4cd111cd4423e2ef668e5367929045',
                      independent_trigonometric_prediction=False,whole_AFTER_State_or_page_seed=False,XOR_AF_semantic_equality_claimed=False,
                      generic_FCOS_claim=False,capture_archives_opened=0,native_result_payloads_opened=0,initializer_credit=0,files=C.PINS)
        target = out / 'report.json'; target.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(dict(passed=passed,sha256=hashlib.sha256(target.read_bytes()).hexdigest(),counts=dict(counts))))


if __name__ == '__main__': main(sys.argv[1])
