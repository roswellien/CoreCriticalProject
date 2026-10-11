"""Bounded independent full-byte/COFF review of actual formatter observers.

The producing original gate owns the runtime IAT and hook observations. This
review reconstructs every compiled and final-linked wrapper without archives.
"""
import collections
import importlib.util
import json
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
import review_connected125_v2 as C


def expected(pc, kind, index, replay):
    code = bytearray()
    relocations = []
    def emit(raw):
        code.extend(bytes.fromhex(raw))
    def address(symbol, addend=0, type_=6):
        relocations.append((len(code), symbol, type_))
        code.extend(struct.pack('<I', addend))
    for i, opcode in enumerate(('a3', '890d', '8915', '891d', '8925', '892d', '8935', '893d')):
        emit(opcode); address('_format_cpu', i * 4)
    emit('c705'); address('_format_cpu', 36); code.extend(struct.pack('<I', pc))
    emit('c705'); address('_format_kind'); code.extend(struct.pack('<I', kind))
    emit('8b25'); address('_mixed_host_esp')
    emit('9c8f05'); address('_format_cpu', 32)
    emit('fc64a100000000a3'); address('_format_head')
    emit('0fae05'); address('_format_fx')
    emit('d935'); address('_format_env')
    emit('d925'); address('_format_env')
    emit('e8'); address('_format_observe', 0, 0x14)
    emit('0fae0d'); address('_format_fx')
    emit('d925'); address('_format_env')
    emit('ff35'); address('_format_cpu', 32); emit('9d')
    for i, opcode in enumerate(('a1', '8b0d', '8b15', '8b1d', '8b25', '8b2d', '8b35', '8b3d')):
        if i != 4:
            emit(opcode); address('_format_cpu', i * 4)
    emit('8b25'); address('_format_cpu', 16)
    code.extend(replay)
    emit('ff25'); address('_format_continues' if kind & 1 else '_format_targets', index * 4)
    return bytes(code), relocations


def module(path, name, digest):
    spec = importlib.util.spec_from_file_location(name, C.pin(path, digest))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def main(name):
    out = ROOT / 'reports/m4-tree-review' / name
    C.need(not out.exists(), 'Fresh independent formatter observer review')
    out.mkdir(parents=True)
    passed = False
    counts = collections.Counter()
    try:
        C.pin(__file__); C.pin(C.__file__)
        path = ROOT / 'reports/m4-formatting-original/linked-observer-r1/report.json'
        report = C.read(path, 'cc4ffd4a690fc64537d86cac28f8fd0781e1862a7ac738b2adce069c18f47c93')
        C.need(report['passed'] and report['return_hook_runtime_page_observed'] is False and report['no_native_acceptance_credit'],
               'Producing scope preserves installer attribution versus unobserved live hook page')
        rows = C.output(report, path.parent, 'compiled-observer-attribution.json')
        PE = module(ROOT / 'tools/analysis/pe.py', 'formatter_review_PE',
                    'bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638')
        COFF = module(ROOT / 'tools/m4-fs-source/observer_attribution.py', 'formatter_review_COFF',
                      '74c7f343543c0ccf7fdf4e99293db5945a22b344d3c7b6b122357d0a4aef31fb')
        game = PE.PEImage(C.pin(ROOT / 'MW3/Mech3.exe', '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
        pattern = {}
        for gate in ('prefix-validation-r1', 'trace-prefix-validation-r1'):
            validation_path = ROOT / 'reports/m4-formatting-original' / gate / 'report.json'
            validation = C.read(validation_path, report['files'][str(validation_path.resolve())])
            execution = C.read(validation['execution_path'], validation['execution_sha256'])
            build_path = Path(execution['build_path'])
            build = C.read(build_path, execution['build_sha256'])
            worker_bytes = C.pin(build['worker'], build['worker_sha256']).read_bytes()
            worker = PE.PEImage(worker_bytes)
            release = build_path.parent / 'build-x86/mw34_joint_startup124_original.dir/Release'
            obj = release / 'format_observer_x86.obj'
            symbols, sections = COFF.parse_coff(C.pin(obj, report['files'][str(obj.resolve())]).read_bytes())
            definitions = {s['name']: s for s in symbols.values() if s['section'] > 0 and s['storage'] == 2}
            shared = {}
            selected = [row for row in rows if row['gate'] == gate]
            C.need(len(selected) == 6, 'All actual observer wrappers once per worker')
            for row in selected:
                kind, index = row['kind'], row['tail_field_index']
                replay = bytes.fromhex(row['replay_hex'])
                raw, relocations = expected(row['source_PC'], kind, index, replay)
                definition = definitions[row['symbol']]
                section = sections[definition['section']]
                start = definition['value']
                C.need(section['bytes'][start:start + len(raw)] == raw and
                       [(offset - start, symbol, type_) for offset, symbol, type_ in section['relocations']
                        if start <= offset < start + len(raw)] == relocations,
                       'Every independently derived compiled save/host-stack/FP/flags/replay byte and relocation')
                target = row['actual_worker_target']
                linked = worker.read(worker.rva_range(target - worker.image_base, len(raw))[0], len(raw))
                normalized = bytearray(linked)
                for offset, symbol, type_ in relocations:
                    addend = struct.unpack_from('<I', raw, offset)[0]
                    value = struct.unpack_from('<I', linked, offset)[0]
                    address = ((value - addend) if type_ == 6 else (target + offset + 4 + value - addend)) & 0xffffffff
                    C.need(symbol not in shared or shared[symbol] == address, 'Every final linked symbol identity remains consistent')
                    shared[symbol] = address
                    normalized[offset:offset + 4] = raw[offset:offset + 4]
                C.need(bytes(normalized) == raw, 'Every final executable wrapper byte equals exact relocation-aware COFF')
                if kind & 1:
                    pc = row['source_PC']
                    C.need(game.read(game.rva_range(pc - game.image_base, len(replay))[0], len(replay)) == replay,
                           'Exact source cdecl caller cleanup/replay span')
                    key = struct.pack('<2I', pc, len(replay))
                    offsets = [i for i in range(len(worker_bytes)) if worker_bytes.startswith(key, i)
                               and worker_bytes[i + 12:i + 12 + len(replay)] == replay]
                    C.need(len(offsets) == 1 and struct.unpack_from('<I', worker_bytes, offsets[0] + 8)[0] == target,
                           'Return target equals actual unique consumed physical hook initializer')
                if row['symbol'] in pattern:
                    C.need(pattern[row['symbol']] == (raw, relocations), 'Normal/traced full compiled pattern equality')
                pattern[row['symbol']] = raw, relocations
                counts['independent_compiled_linked_functions'] += 1
                counts['independent_compiled_linked_bytes'] += len(raw)
                counts['independent_compiled_linked_relocations'] += len(relocations)
            continue_bytes = worker.read(worker.rva_range(shared['_format_continues'] - worker.image_base, 12)[0], 12)
            C.need(continue_bytes == struct.pack('<3I', 0x4dea20, 0x4deabc, 0x4deade), 'Every actual linked cdecl continuation field')
            counts['actual_workers'] += 1
        C.need(len(pattern) == 6 and counts['independent_compiled_linked_functions'] == 12,
               'Complete both genuine original worker code attribution')
        passed = True
    finally:
        receipt = dict(passed=passed, scope='Independent bounded exact compiled and final linked12 formatter wrappers; genuine actual target observations attributed to producing original gate',
                       counts=dict(counts), archives_opened=0, runtime_hook_page_independently_observed=False,
                       literal_formatter_semantics_accepted=False, native_executed=False,
                       initializer_credit=False, whole_M4_complete=False, files=C.PINS)
        target = out / 'report.json'
        target.write_text(json.dumps(receipt, indent=2) + '\n')
        import hashlib
        print(json.dumps(dict(passed=passed, sha256=hashlib.sha256(target.read_bytes()).hexdigest(), counts=dict(counts))))


if __name__ == '__main__':
    main(sys.argv[1])
