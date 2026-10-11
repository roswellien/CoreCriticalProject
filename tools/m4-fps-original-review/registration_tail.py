"""Independent physical FPS registration tail and affine stack review; no captures."""
from pathlib import Path
import hashlib, importlib.util, json, struct, sys, traceback
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def need(value, message):
    if not value:
        raise ValueError(message)

def main(name):
    out = ROOT / 'reports/m4-fps-original-review' / name
    need(not out.exists(), 'Fresh additive independent registration-tail receipt')
    out.mkdir(parents=True)
    pins, physical, passed = {}, [], False
    def pin(path, digest=None):
        path = Path(path).resolve()
        need(path.suffix.lower() != '.mwb', 'No capture archive')
        actual = sha(path)
        need(digest is None or digest == actual, 'Exact current physical input ' + str(path))
        need(str(path) not in pins or pins[str(path)] == actual, 'Immutable successful read')
        pins[str(path)] = actual
        return path
    def read(path, digest=None):
        return json.loads(pin(path, digest).read_bytes())
    try:
        prep_path = ROOT / 'reports/m4-fps-native/component-preparation-r1/report.json'
        prep = read(prep_path, '294ac018294dbb35b341d8c86e195d23b68ce0f249fa86aa02781e8c181c5a18')
        need(prep['passed'] and prep['root_count'] == 7, 'Current seven-route component preparation')
        contracts_path = prep_path.parent / 'contracts.json'
        contracts = read(contracts_path, prep['files'][str(contracts_path.resolve())])
        inherited_path = ROOT / 'reports/m4-widget-original-review/registration-tail-r1/report.json'
        inherited = read(inherited_path, 'abaa48c8dd533c56cdbd48118676bf0800f0c942ce9319a537a03c4c4b4f3cb5')
        need(inherited['passed'] and inherited['counts'] == {'roots': 6, 'physical_tail_instruction_occurrences': 60, 'source_RET_reads': 18}, 'Pinned inherited six-tail review')
        pe_path = pin(ROOT / 'tools/analysis/pe.py')
        spec = importlib.util.spec_from_file_location('independent_FPS_tail_PE', pe_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        image_path = pin(ROOT / 'MW3/Mech3.exe', '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
        game = module.PEImage(image_path.read_bytes())
        by_pc = {row['pc']: row for row in contracts['instructions']}
        root = next(row for row in contracts['roots'] if row['root'] == 0x40f000)
        tail = next(row for row in contracts['registration_epilogues'] if row['root'] == root['root'])
        registration = root['registration']
        need(registration == {'callback': 0x40f030, 'push_PC': 0x40f020, 'CALL_pc': 0x40f025, 'return_PC': 0x40f02a}, 'Exact new FPS source registration association')
        pcs = [0x5ac124,0x5ac127,0x5ac14a,0x5ac14d,0x5ac14f,0x5ac151,0x5ac153,0x5ac154,0x40f02a,0x40f02d]
        need(tail['source_PCs'] == pcs and tail['source_read_PC_and_frame_offsets'] == [[0x5ac127,-16,4,False],[0x5ac154,-8,4,False],[0x40f02d,0,4,False]] and not tail['value_oracle'], 'Exact ten-PC and three-RET declaration, no value oracle')
        for prior in inherited['rows']:
            current = next(row for row in contracts['registration_epilogues'] if row['root'] == prior['root'])
            current_root = next(row for row in contracts['roots'] if row['root'] == prior['root'])
            need(current['source_PCs'] == prior['source_PCs'] and current['source_read_PC_and_frame_offsets'] == prior['RET_operands'] and current_root['registration']['CALL_pc'] == prior['registration_CALL_pc'] and not current['value_oracle'], 'Exact inherited six-tail association in current component')
        prefix = [0x40f020,0x40f025,0x5ac140,0x5ac144,0x5ac145,0x5ac110,0x5ac117,0x5ac119,0x5ac11d,0x5ac11e]
        for pc in prefix + pcs:
            row = by_pc[pc]
            offset, _ = game.rva_range(pc - game.image_base, row['width'])
            need(game.data[offset:offset+row['width']] == bytes.fromhex(row['bytes_hex']), 'Whole exact physical registration instruction ' + hex(pc))
            physical.append({key: row[key] for key in ('pc','width','bytes_hex','mnemonic','operands')} | {'physical_file_offset': offset, 'scope': 'prefix' if pc in prefix else 'tail'})
        def raw(pc):
            return bytes.fromhex(by_pc[pc]['bytes_hex'])
        expected_tail = ['83c404','c3','83c404','f7d8','1bc0','f7d8','48','c3','83c404','c3']
        need([raw(pc).hex() for pc in pcs] == expected_tail, 'Exact full physical ADD/RET/Boolean tail sequence')
        need(raw(0x40f020) == b'\x68\x30\xf0\x40\x00' and raw(0x40f025)[0] == 0xe8 and 0x40f02a + struct.unpack('<i',raw(0x40f025)[1:])[0] == 0x5ac140, 'Physical callback PUSH and registration CALL')
        need(raw(0x5ac140) == b'\x8b\x44\x24\x04' and raw(0x5ac144) == b'\x50' and raw(0x5ac145) == b'\xe8\xc6\xff\xff\xff', 'Physical callback forwarding and own inner CALL return')
        need(raw(0x5ac110) == b'\x83\x3d\xf0\x17\x9a\x00\xff' and raw(0x5ac117) == b'\x75\x0f' and raw(0x5ac119) == b'\x8b\x44\x24\x04' and raw(0x5ac11d) == b'\x50' and raw(0x5ac11e) == b'\xff\x15\x2c\xb5\x5b\x00', 'Exact admitted sentinel-mode provider CALL route')
        frame = 0x20001800
        stores = [[0x40f020,-4,0x40f030],[0x40f025,-8,0x40f02a],[0x5ac144,-12,0x40f030],[0x5ac145,-16,0x5ac14a],[0x5ac11d,-20,0x40f030],[0x5ac11e,-24,0x5ac124]]
        esp, reads = -20, []
        for pc in pcs:
            row = by_pc[pc]
            if row['mnemonic'] == 'add':
                need(raw(pc) == b'\x83\xc4\x04', 'Only literal ADD ESP,4 stack cleanup')
                esp += 4
            elif row['mnemonic'] == 'ret':
                need(raw(pc) == b'\xc3', 'Exact near RET')
                reads.append([pc,esp,4,False])
                esp += 4
            else:
                need(row['mnemonic'] in ('neg','sbb','dec'), 'Source-only Boolean integer conversion')
        need(reads == tail['source_read_PC_and_frame_offsets'] and esp == 4, 'Complete affine source stack walk to original caller')
        need({offset:value for _,offset,value in stores}[-16] == 0x5ac14a and {offset:value for _,offset,value in stores}[-8] == 0x40f02a, 'Both inner RET values derive earlier source CALL stores')
        # Recheck all successful inputs after interpretation, before sealing.
        pin(__file__)
        pin(sys.executable)
        for path,digest in list(pins.items()):
            pin(path,digest)
        passed = True
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc())
        raise
    finally:
        report = dict(passed=passed,scope='Independent exact physical ten-PC FPS registration tail and three affine RET reads, plus literal callback/return-store prefix on the admitted sentinel-mode provider route. No provider response value, captured endpoint or execution supplied.',component_preparation_sha256=sha(prep_path) if 'prep_path' in locals() else None,inherited_six_tail_sha256=sha(inherited_path) if 'inherited_path' in locals() else None,counts=dict(new_roots=int(passed),physical_tail_instruction_occurrences=10 if passed else 0,source_RET_reads=3 if passed else 0,physical_prefix_instruction_occurrences=10 if passed else 0),root=0x40f000,registration=registration if 'registration' in locals() else None,physical_instructions=physical,source_stack_stores=stores if 'stores' in locals() else [],RET_operands=reads if 'reads' in locals() else [],root_frame=0x20001800,provider_entry_frame_offset=-24,provider_cdecl_return_PC=0x5ac124,provider_cdecl_return_ESP_offset=-20,final_ESP_offset=4,normal_route_condition=dict(PC=0x5ac110,address=0x9a17f0,value=0xffffffff,branch_5ac117='not taken',current_runtime_condition_proven_by_this_static_review=False),provider_result_remains_external_input=True,provider_CPU_modeled=False,root_constructor_exit_frame_is_a_separate_obligation=True,capture_reader_opened=False,worker_executed=False,source_callback_executed=False,initializer_credit=0,files=pins)
        path=out/'report.json'
        path.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(dict(passed=passed,sha256=sha(path),counts=report['counts'])))

if __name__ == '__main__':
    main(sys.argv[1])
