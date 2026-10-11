"""Freeze exact tree operand/dispatch contracts; no execution admission."""
from pathlib import Path
import hashlib, importlib.util, json, sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
PINS = {}

def pin(path, expected=None):
    path = Path(path).resolve()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert expected is None or digest == expected, str(path)
    PINS[str(path)] = digest
    return path

def read(path, expected=None):
    return json.loads(pin(ROOT/path, expected).read_bytes())

def main(name):
    out = ROOT/'reports/m4-tree-source'/name
    assert not out.exists()
    out.mkdir(parents=True)
    base = 'reports/m4-lockit-source/complex-plan-r1/'
    source = read(base+'instruction-contracts.json', 'f4432ad7e4866a78b60b3c952a1bea255a97dfa2c386e9ac086b4ef831586a1c')
    plan = read(base+'execution-plan.json', 'a972f30e1c707bf6645ff608313b581395a62b347c3cb0c9c8e91d02ba19ec24')
    graphs = read(base+'game-new-graphs.json', 'ebf14d153ed8e85d5d595c428e73d4df120c1a1cfe178ef5625372469e8523b5')
    previous = read('reports/m4-lockit-source/recovery-r1/instruction-contracts.json', 'c102e277742f2cd6e2a352f9e40f44f7d7d2ea1107d8bde242d103b586e75f25')
    nextplan = read('reports/m4-lockit-source/complex-next-plan-r1/contracts.json')
    accepted = read('reports/m4-joint-startup124-root/acceptance-r1/report.json', '6bd35e55bca15e1a0537044bf59a1c3ced5e9ef8b30a8a169b71c78824811462')
    assert accepted['passed'] and len(previous['selected_order']) == 124
    spec = importlib.util.spec_from_file_location('tree_physical_PE', pin(ROOT/'tools/analysis/pe.py'))
    pe_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pe_module)
    pe = pe_module.PEImage(pin(ROOT/'MW3/Mech3.exe', '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
    rows = {r['pc']:r for r in source['instructions']}
    for row in rows.values():
        raw = bytes.fromhex(row['bytes_hex'])
        offset, _ = pe.rva_range(row['pc']-pe.image_base, len(raw))
        assert pe.data[offset:offset+len(raw)] == raw
    lower = plan['lower_tail_entry']
    tail = dict(graphs[str(0x4b7f80)])
    tail['entry'] = lower
    tail['instructions'] = [r for r in tail['instructions'] if r['pc'] < 0x4b7f80]
    tail['instruction_count'] = len(tail['instructions'])
    tail['instruction_bytes_sha256'] = hashlib.sha256(b''.join(bytes.fromhex(r['bytes']) for r in tail['instructions'])).hexdigest()
    tail['physical_lower_tail_of'] = 0x4b7f80
    graphs[str(lower)] = tail
    order = sorted(previous['selected_order']+[dict(entry=plan['root'], slot=plan['slot'])], key=lambda r:r['slot'])
    assert len(order) == 125 and len(rows) == 613 and sum(r['width'] for r in rows.values()) == 1894
    operands = []
    for row in rows.values():
        for index, operand in enumerate(row['decoded_operands']):
            if operand['kind'] != 'memory':
                continue
            op = row['mnemonic']
            write = index == 0 and op in ('mov','movzx','setl','sete','add','sub','inc','dec','neg','and','or','xor','sbb')
            operands.append(dict(root=plan['root'], pc=row['pc'], mnemonic=op, operand_index=index,
                                 source_operand=operand, bytes=operand['bits']//8,
                                 read=not write or op not in ('mov','movzx','setl','sete'), write=write,
                                 address_only=op == 'lea', bytes_hex=row['bytes_hex'],
                                 admission='Source operand only; actual live pointer, generation and requested offset require literal prefix'))
    imports = []
    for row in rows.values():
        args = row['decoded_operands']
        for operand in args:
            if operand['kind'] == 'memory' and not operand['terms'] and operand['displacement'] in (0x5bb4f8,0x5bb4f4):
                slot = operand['displacement']
                imports.append(dict(pc=row['pc'], slot=slot, raw=0x1df582 if slot == 0x5bb4f8 else 0x1df568,
                                    target=0x7810a290 if slot == 0x5bb4f8 else 0x7810a350,
                                    definition_register=args[0]['register'] if row['mnemonic'] == 'mov' else None,
                                    source_row=row))
    branch = dict(CALL_pc=0x4badd0, admitted_only_after_actual_prefix=False,
                  normal_expected_LEA_pc=0x4badcc, target_entry_ESP_bias=24,
                  source_straight_interval=[rows[p] for p in (0x4badc7,0x4badc9,0x4badcc,0x4badd0)],
                  preceding_committed_owned_write_PCs=[0x4badc7,0x4badc9],
                  other_static_variants_pending=True)
    contract = dict(schema='mw34-tree-source-v1', instructions=source['instructions'], roots=[source['root']],
                    selected_order=order, selected_order_admitted=False, physical_dispatch_entries=plan['physical_dispatch_entries'],
                    source_data_pages=source['source_data_pages'], FS_frame_contracts=nextplan['FS_frames'],
                    Lockit_scratch_contracts=nextplan['Lockit_scratch_contracts'], game_imports=imports,
                    register_import_calls=source['register_import_calls'], allocations=plan['syntactic_MFC_sites'],
                    static_map_assignments=plan['static_map_assignments'], registration=plan['registration'],
                    repeated_owner_key=['root','CALL_pc','per_site_invocation_ordinal','actual_generation'],
                    branch_scratch=branch, native_owned_admission_pending_genuine_prefix=True)
    def emit(filename, value):
        path = out/filename
        path.write_text(json.dumps(value, indent=2)+'\n')
        pin(path)
    emit('instruction-contracts.json', contract)
    emit('game-new-graphs.json', graphs)
    emit('operand-access-obligations.json', operands)
    emit('register-import-contracts.json', imports)
    emit('branch-scratch-contracts.json', branch)
    emit('FS-frame-contracts.json', nextplan['FS_frames'])
    pin(__file__)
    report = dict(passed=True, scope='Exact physical tree reconstruction and native-use operands, no executed initializer credit',
                  instructions=613, physical_bytes=1894, physical_dispatch_entries=8, roots=1,
                  instructions_path=str(out/'instruction-contracts.json'), instructions_sha256=PINS[str((out/'instruction-contracts.json').resolve())],
                  source_or_native_executed=False, initializer_credit=False, files=PINS)
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(passed=True, report=str(out/'report.json'), report_sha256=hashlib.sha256((out/'report.json').read_bytes()).hexdigest())))

if __name__ == '__main__':
    main(sys.argv[1])
