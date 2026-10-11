"""Physical next-root recovery; static dependencies are not runtime credit."""
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import struct
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]


def main(name):
    out = ROOT / 'reports/m4-hypot-original' / name
    assert re.fullmatch(r'recovery-r[1-9][0-9]*', name) and not out.exists()
    out.mkdir(parents=True)
    pins = {}

    def pin(path, expected=None):
        path = Path(path).resolve()
        assert path.suffix.lower() not in ('.mwb', '.zip')
        with path.open('rb') as stream:
            identity = hashlib.file_digest(stream, 'sha256').hexdigest()
        assert expected is None or identity == expected, str(path)
        assert str(path) not in pins or pins[str(path)] == identity
        pins[str(path)] = identity
        return path

    def emit(name, value):
        path = out / name
        path.write_text(json.dumps(value, indent=2) + '\n')
        pin(path)
        return str(path)

    module = importlib.util.spec_from_file_location(
        'hypot_recovery', pin(ROOT / 'tools/m4-service-initializers/recover.py'))
    recovery = importlib.util.module_from_spec(module)
    module.loader.exec_module(recovery)
    game = recovery.Module(pin(ROOT / 'MW3/Mech3.exe',
        recovery.IDENTITIES['MW3/Mech3.exe']))
    crt_path = 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'
    crt = recovery.Module(pin(ROOT / crt_path, recovery.IDENTITIES[crt_path]))
    graphs_path = ROOT / 'reports/m4-service-initializers/static-r1/game-all-initializer-graphs.json'
    graphs = json.loads(pin(graphs_path,
        'da2482873e1678a0a2493ed7f60421440447c43e63826b53f2d5b09cf573ba5a').read_bytes())
    selected = {entry: graphs[str(entry)] for entry in (0x4b5910, 0x4b5860)}
    rows = {row['pc']: row for graph in selected.values() for row in graph['instructions']}
    assert len(rows) == 65
    for row in rows.values():
        raw = bytes.fromhex(row['bytes'])
        offset, _ = game.image.rva_range(row['pc'] - game.base, len(raw))
        assert game.image.data[offset:offset + len(raw)] == raw
    assert game.image.rva_u32(0x5e0154 - game.base) == 0x4b5910
    imports = selected[0x4b5860]['import_sites']
    assert [(v['site'], v['iat'], v['return_pc']) for v in imports] == [
        (0x4b58b8, 0x5bb5b0, 0x4b58be), (0x4b58e3, 0x5bb5b0, 0x4b58e9)]
    assert game.imports[0x5bb5b0]['name'] == '_hypot'
    export = next(v for v in crt.exports if '_hypot' in v['names'])
    assert export['ordinal'] == 269 and crt.base + export['rva'] == 0x7802a122
    assert rows[0x4b590c]['bytes'] == 'c21000'

    # Retain the original physical provider graph. No branch is called reached
    # merely because it is present in this finite disassembly.
    lookup = pin(ROOT / 'reports/m4-service-initializers/static-r1/MSVCRT.DLL.linear-lookup.txt')
    for line in lookup.read_text().splitlines():
        match = recovery.ROW.match(line)
        if match:
            pc = int(match[1], 16)
            raw = bytes.fromhex(match[2])
            assembly = re.sub(r'\s+', ' ', match[3].strip())
            op, _, args = assembly.partition(' ')
            crt.rows[pc] = dict(pc=pc, size=len(raw), bytes=raw.hex(), mnemonic=op, operands=args)
    provider, deferred = recovery.closure(crt, [0x7802a122], maximum=80)
    provider_rows = {r['pc']: r for g in provider.values() for r in g['instructions']}
    assert 0x7802a122 in provider_rows
    for row in provider_rows.values():
        raw = bytes.fromhex(row['bytes'])
        offset, _ = crt.image.rva_range(row['pc'] - crt.base, len(raw))
        assert crt.image.data[offset:offset + len(raw)] == raw
    constants = []
    for address, size in [(0x5c93a8, 8)]:
        offset, _ = game.image.rva_range(address - game.base, size)
        raw = game.image.data[offset:offset + size]
        constants.append(dict(address=address, bytes=size, hex=raw.hex(),
            bits=int.from_bytes(raw, 'little'), finite_value=struct.unpack('<d', raw)[0]))
    stores = [r for r in rows.values() if r['mnemonic'] == 'fstp' and '[esi' in r['operands']]
    assert len(stores) == 9
    emit('game-graphs.json', selected)
    emit('CRT-provider-graphs.json', provider)
    emit('physical-constants.json', constants)
    contract = dict(entry=0x4b5910, slot=0x5e0154, helper=0x4b5860,
        literal_object=0x60b2c8,
        source_pushed_F32_bits=[0x43480000, 0x41200000, 0x41f00000, 0x41200000],
        ordered_game_import_calls=imports, owning_CRT_export=export,
        owning_CRT_preferred_entry=0x7802a122,
        helper_RET_cleanup=16, whole_F32_store_instructions=stores,
        source_x87_rows=sum(r['mnemonic'].startswith('f') for r in rows.values()),
        original_results_observed=False, numerical_oracle_admitted=False)
    emit('root-contract.json', contract)
    plan = """# Authentic hypot probe

Capture one actual root4B5910 under the admitted authentic loader, preserving
the exact six control-word/TOP cases used by the current startup worker. The
literal four F32 arguments and object60B2C8 are source inputs, not recovered
from an AFTER image. Capture complete BEFORE and AFTER State/CPU/FX/ENV and
whole current stack and object backing. Preserve all nine F32 publications,
the returned EAX, RET16 cleanup and unchanged surrounding bytes.

At both CALLs4B58B8/4B58E3 capture the actual named CRT _hypot16-byte cdecl
argument frame, CPU/FX/ENV entry and actual return at4B58BE/4B58E9. Preserve the
live x87 stack around each call, raw80 result, status/control state and caller
cleanup. Do not preinvoke the provider, replace it with host hypot/sqrt, or
reuse a whole observed AFTER machine as a source prediction. Model literal
game x87 effects from their BEFORE inputs. Any admitted original provider
scalar oracle must be tied to those exact source-derived operand pairs.

Retain the physical CRT graph, including cold/error paths, without claiming
they executed. Recover and capture every actually reached CRT/API dependency
and any errno/matherr side effects before admitting provider equivalence.
This static recovery provides no native initializer acceptance.
"""
    path = out / 'next-probe.md'
    path.write_text(plan, encoding='utf-8')
    pin(path)
    pin(__file__)
    pin(ROOT / 'tools/analysis/pe.py')
    pin(sys.executable)
    report = dict(passed=True, scope='Physical root4B5910 and finite static CRT _hypot frontier',
        game_instructions=len(rows), game_bytes=sum(r['size'] for r in rows.values()),
        x87_instructions=contract['source_x87_rows'], F32_publications=len(stores),
        actual_named_import_sites=len(imports), provider_entries=len(provider),
        provider_instructions=len(provider_rows), deferred_direct_entries=deferred,
        unresolved_controls=sum(len(g['unresolved_controls']) for g in provider.values()),
        capture_reader_opened=False, original_executed=False, native_executed=False,
        source_numerical_prediction_proven=False, initializer_credit=0, files=pins)
    path = out / 'report.json'
    path.write_text(json.dumps(report, indent=2) + '\n')
    identity = pin(path)
    print(json.dumps({k:v for k,v in report.items() if k != 'files'}), flush=True)
    print(pins[str(identity)], flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
