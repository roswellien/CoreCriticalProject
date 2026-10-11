"""Independent physical and affine registration-tail review; no captures."""
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
    out = ROOT / 'reports/m4-widget-original-review' / name
    need(not out.exists(), 'Fresh independent tail review')
    out.mkdir(parents=True)
    pins, rows, passed = {}, [], False
    def pin(path, digest=None):
        path = Path(path).resolve()
        need(path.suffix.lower() != '.mwb', 'No capture archive in this review')
        actual = sha(path)
        need(digest is None or actual == digest, 'Exact physical input ' + str(path))
        need(str(path) not in pins or pins[str(path)] == actual, 'Immutable input')
        pins[str(path)] = actual
        return path
    def read(path, digest=None):
        return json.loads(pin(path, digest).read_bytes())
    try:
        prep_path = ROOT / 'reports/m4-widget-native/preparation-r3/report.json'
        prep = read(prep_path, '69a29eddf46f6c189edc462e5f5734a96e3d98c2c1f37778a54d36c0fd62eae5')
        need(prep['passed'], 'Current native preparation')
        contracts_path = prep_path.parent / 'contracts.json'
        contracts = read(contracts_path, prep['files'][str(contracts_path.resolve())])
        source_path = ROOT / 'reports/m4-font479590-original/source-r1/report.json'
        source = read(source_path, '7a5b070228618400a1a4524b4df4214226f12c2570bcff9775fc6416265c4e9b')
        original_path = source_path.parent / 'source-derivations.json'
        original = read(original_path, source['files'][str(original_path.resolve())])
        pe_path = pin(ROOT / 'tools/analysis/pe.py')
        spec = importlib.util.spec_from_file_location('independent_tail_PE', pe_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        game = module.PEImage(pin(ROOT / 'MW3/Mech3.exe', '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
        by_pc = {row['pc']: row for row in contracts['instructions']}
        tails = contracts['registration_epilogues']
        need(len(tails) == len(original) == len(contracts['roots']) == 6, 'Every six-root tail')
        frame = 0x20001800
        for root, prior, tail in zip(contracts['roots'], original, tails):
            entry = root['root']
            need(entry == prior['root'] == tail['root'], 'Exact root association')
            registration = root['registration']
            call = registration.get('CALL_pc', registration.get('registration_CALL_pc'))
            pcs = [0x5ac124, 0x5ac127, 0x5ac14a, 0x5ac14d, 0x5ac14f,
                   0x5ac151, 0x5ac153, 0x5ac154, call + 5, call + 8]
            need(tail['source_PCs'] == pcs, 'Complete ten physical straight-line source PCs')
            for pc in pcs:
                row = by_pc[pc]
                offset, _ = game.rva_range(pc - game.image_base, row['width'])
                need(game.data[offset:offset + row['width']] == bytes.fromhex(row['bytes_hex']), 'Entire physical tail instruction')
            accesses = prior['source_accesses']
            need(prior['source_PCs'][-1] == 0x5ac11e and accesses[-1] == [0x5ac11e, frame - 24, 0x5ac124, 4, 1], 'Actual literal prefix commits true provider return')
            writes = {(pc, address): value for pc, address, value, width, writing in accesses if writing and width == 4}
            need(writes[(0x5ac145, frame - 16)] == 0x5ac14a and writes[(call, frame - 8)] == call + 5, 'Both RET values follow own earlier literal CALL stores')
            need(tail['source_read_PC_and_frame_offsets'] == [[0x5ac127, -16, 4, False], [0x5ac154, -8, 4, False], [call + 8, 0, 4, False]], 'Exact three affine RET operand declarations')
            need(not tail['value_oracle'], 'No output value supplied by tail declarations')
            # Provider cdecl RET consumes its return at F-24. Only source ADD/RET
            # changes ESP in this epilogue; values remain source-derived.
            esp = frame - 20
            reads = []
            for pc in pcs:
                mnemonic = by_pc[pc]['mnemonic']
                if mnemonic == 'add':
                    need(by_pc[pc]['operands'] == 'esp, 0x4', 'Exact literal stack cleanup')
                    esp += 4
                elif mnemonic == 'ret':
                    reads.append([pc, esp - frame, 4, False])
                    esp += 4
                else:
                    need(mnemonic in ('neg', 'sbb', 'dec'), 'Source-only integer Boolean conversion')
            need(reads == tail['source_read_PC_and_frame_offsets'] and esp == frame + 4, 'Complete literal stack walk to caller')
            rows.append(dict(root=entry,registration_CALL_pc=call,source_PCs=pcs,RET_operands=reads,final_ESP=esp,provider_result_remains_external_input=True,provider_CPU_not_modeled_by_this_review=True))
        pin(ROOT / 'tools/m4-widget-native/prepare_v3.py')
        pin(__file__)
        passed = True
    except BaseException:
        (out / 'failure.txt').write_text(traceback.format_exc())
        raise
    finally:
        report = dict(passed=passed,scope='Independent exact physical ten-PC registration tails and three affine RET reads for six widget/font roots, extended from each previously literal-derived committed provider CALL. No API result value or AFTER seed.',widget_preparation_sha256=sha(prep_path) if 'prep_path' in locals() else None,counts=dict(roots=len(rows),physical_tail_instruction_occurrences=10*len(rows),source_RET_reads=3*len(rows)),rows=rows,files=pins,capture_reader_opened=False,worker_executed=False,registration_provider_CPU_modeled=False,initializer_credit=0)
        (out / 'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=report['counts'])))

if __name__ == '__main__':
    main(sys.argv[1])
