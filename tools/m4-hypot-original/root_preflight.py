"""Independent physical prelaunch review of three x86 hypot observation bridges."""
from pathlib import Path
import collections
import hashlib
import importlib.util
import json
import struct
import sys
import traceback

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]


def expected_bridge(pc, kind, tail):
    code = bytearray()
    relocations = []

    def emit(raw):
        code.extend(bytes.fromhex(raw))

    def ins(opcode, symbol, addend=0, typ=6):
        emit(opcode)
        relocations.append((len(code), '_' + symbol, typ))
        code.extend(struct.pack('<I', addend))

    for i, op in enumerate(('a3', '890d', '8915', '891d', '8925', '892d', '8935', '893d')):
        ins(op, 'hypot_cpu', i * 4)
    ins('c705', 'hypot_cpu', 36)
    code.extend(struct.pack('<I', pc))
    ins('c705', 'hypot_kind')
    code.extend(struct.pack('<I', kind))
    ins('8b25', 'mixed_host_esp')
    emit('9c')
    ins('8f05', 'hypot_cpu', 32)
    emit('fc64a100000000')
    ins('a3', 'hypot_head')
    ins('0fae05', 'hypot_fx')
    ins('d935', 'hypot_env')
    ins('d925', 'hypot_env')
    ins('e8', 'hypot_observe', typ=0x14)
    ins('0fae0d', 'hypot_fx')
    ins('d925', 'hypot_env')
    ins('ff35', 'hypot_cpu', 32)
    emit('9d')
    for offset, op in ((0,'a1'),(4,'8b0d'),(8,'8b15'),(12,'8b1d'),
                       (20,'8b2d'),(24,'8b35'),(28,'8b3d'),(16,'8b25')):
        ins(op, 'hypot_cpu', offset)
    emit(tail)
    ins('ff25', 'hypot_target' if kind == 0 else 'hypot_continues',
        4 if kind == 2 else 0)
    return bytes(code), relocations


def main(name):
    out = ROOT / 'reports/m4-hypot-original' / name
    assert not out.exists()
    out.mkdir(parents=True)
    pins, counts, linked = {}, collections.Counter(), []
    passed = False

    def pin(path, expected=None):
        path = Path(path).resolve()
        assert path.suffix.lower() not in ('.mwb', '.zip')
        with path.open('rb') as stream:
            identity = hashlib.file_digest(stream, 'sha256').hexdigest()
        assert expected is None or identity == expected, str(path)
        assert str(path) not in pins or pins[str(path)] == identity
        pins[str(path)] = identity
        return path

    def read(path, expected=None):
        return json.loads(pin(path, expected).read_text(encoding='utf-8-sig'))

    def module(path, name):
        spec = importlib.util.spec_from_file_location(name, pin(path))
        value = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(value)
        return value

    try:
        build = read(ROOT / 'reports/m4-hypot-original/prefix-build-r1/build.json',
            '579280372eb328bc383a703927e8279ec8cb6c1351b5a8fe129f58ae7bb00ae5')
        prepdir = Path(build['preparation'])
        prep = read(prepdir / 'report.json', build['preparation_sha256'])
        assert prep['passed'] is True and build['passed'] is True
        assert build['roots'] == 1 and build['sequences'] == build['phases'] == 6
        assert prep['record_bytes'] == build['record_bytes'] == 356992
        assert prep['game_rows'] == 65 and prep['game_bytes'] == 211
        for field in ('predicted_outputs_supplied_to_execution', 'provider_preinvoked',
                      'source_after_seed', 'archive_reader_opened', 'original_executed'):
            assert prep[field] is False
        for label in ('sources', 'tools', 'artifacts'):
            for path, identity in build.get(label, {}).items():
                pin(path, identity)
        for path, identity in prep['files'].items():
            pin(path, identity)
        counts['physically_checked_prelaunch_inputs'] = len(pins)
        contract = read(prepdir / 'instruction-contracts.json')
        assert contract['snapshot_bytes'] == 271012
        assert contract['snapshot_layout'] == dict(header=0, CPU40=64, FX512=104,
            ENV28=616, frame32=644, stack4096=676, source4096=4772, CRT64pages=8868)
        assert contract['root'] == 0x4b5910 and contract['slot'] == 0x5e0154
        assert contract['owning_IAT'] == 0x5bb5b0 and contract['actual_preferred_provider'] == 0x7802a122
        assert contract['provider_preinvoked'] is False and contract['numerical_result_expected_seed'] is False
        PE = module(ROOT / 'tools/analysis/pe.py', 'hypot_preflight_PE')
        worker = PE.PEImage(pin(build['worker'], build['worker_sha256']).read_bytes())
        assert worker.machine == 0x14c
        COFF = module(ROOT / 'tools/m4-fs-source/observer_attribution.py', 'hypot_preflight_COFF')
        linker = module(ROOT / 'tools/m4-tree-review/review_cosine_original.py', 'hypot_preflight_linker')
        release = Path(build['worker']).parent / 'build-x86/mw34_joint_startup124_original.dir/Release'
        symbols, sections = COFF.parse_coff(pin(release / 'hypot_observer_x86.obj').read_bytes())
        definitions = {r['name']:r for r in symbols.values() if r['section'] > 0 and r['storage'] == 2}
        addresses = {}
        for name, pc, kind, tail in [('_hypot_entry',0x7802a122,0,''),
                ('_hypot_return_first',0x4b58be,1,'d94608d9c9'),
                ('_hypot_return_second',0x4b58e9,2,'d9460cd9c9')]:
            expected, relocs = expected_bridge(pc, kind, tail)
            definition = definitions[name]
            section = sections[definition['section']]
            begin = definition['value']
            ends = [r['value'] for r in definitions.values()
                    if r['section'] == definition['section'] and r['value'] > begin]
            end = min(ends, default=len(section['bytes']))
            assert section['bytes'][begin:end] == expected, name
            assert [(offset-begin,symbol,typ) for offset,symbol,typ in section['relocations']
                    if begin <= offset < end] == relocs, name
            target, actual = linker.matching_linked_function(worker, expected, relocs)
            for offset, symbol, typ in relocs:
                operand = struct.unpack_from('<I', actual, offset)[0]
                addend = struct.unpack_from('<I', expected, offset)[0]
                if typ == 6:
                    address = (operand-addend) & 0xffffffff
                else:
                    assert typ == 0x14
                    address = (target+offset+4+operand-addend) & 0xffffffff
                assert symbol not in addresses or addresses[symbol] == address, symbol
                addresses[symbol] = address
            linked.append(dict(symbol=name, address=target, bytes=len(expected),
                               relocations=len(relocs), original_PC=pc, kind=kind))
            counts['whole_final_linked_observer_functions'] += 1
            counts['whole_final_linked_observer_bytes'] += len(expected)
            counts['whole_final_linked_observer_relocations'] += len(relocs)
        assert addresses['_hypot_fx'] % 16 == 0
        for symbol in ('_hypot_cpu','_hypot_fx','_hypot_env','_hypot_kind',
                       '_hypot_head','_hypot_target','_hypot_continues','_mixed_host_esp'):
            rva = addresses[symbol] - worker.image_base
            assert any(s['writable'] and s['virtual_address'] <= rva <
                       s['virtual_address']+max(s['raw_size'],s['virtual_size']) for s in worker.sections)
        observer = (prepdir / 'hypot_observer.hpp').read_text()
        reference = (prepdir / 'reference.cpp').read_text()
        assert 's.header[9]=saved_error;' in observer
        assert 'hypot_count>=8' in observer and 'hypot_kind>2' in observer
        assert 'hypot_cpu.esp<0x20001000||hypot_cpu.esp+32>0x20002000' in observer
        assert 'SetLastError(saved_error)' in observer
        for phrase in ('Exact genuine named _hypot export', 'Actual named hypot target before observer',
                       'Hypot game IAT observer protection restored',
                       'Hypot named game IAT restored protection',
                       'Exact physical hypot return span', 'Exact declared hypot return observer byte',
                       'Hypot exact return source restoration', 'Actual two _hypot entry/first-game-return pairs'):
            assert phrase in reference, phrase
        assert reference.count('r->tag.status=execute();') == 1
        assert 'hypot-CRT-before/' in reference and 'hypot-CRT-after/' in reference
        assert 'reinterpret_cast<unsigned>(GetProcAddress(crt,"_hypot"))' in reference
        counts['planned_cases'] = 6
        counts['planned_actual_cdecl_boundaries'] = 24
        counts['full_stack_bytes_per_boundary'] = 4096
        counts['full_CRT_pages_per_boundary'] = 64
        passed = True
    except BaseException:
        (out / 'failure.txt').write_text(traceback.format_exc())
        raise
    finally:
        pin(__file__)
        artifact = out / 'linked-observers.json'
        artifact.write_text(json.dumps(dict(functions=linked), indent=2)+'\n')
        pin(artifact)
        report = dict(passed=passed, scope='Independent exact x86 prelaunch observer/code/relocation/linked-worker and declared capture scope',
            counts=dict(counts), build_sha256=build.get('worker_sha256') if 'build' in locals() else None,
            capture_archives_opened=0, original_execution_claimed=False,
            runtime_scope_validated=False, provider_numerical_equivalence=False,
            original_source_FIP_of_replayed_FLDFXCH_preserved=False,
            literal_replayed_FIP_overwrite_requires_later_source_validation=True,
            initializer_credit=0, files=pins)
        path = out / 'report.json'
        path.write_text(json.dumps(report, indent=2)+'\n')
        pin(path)
        print(json.dumps(dict(passed=passed, sha256=pins[str(path)], counts=dict(counts))))


if __name__ == '__main__':
    main(sys.argv[1])
