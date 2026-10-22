"""Export metadata only for original-input control/FDIV startup generation."""
import argparse
import json
from pathlib import Path
import struct

from translate import sha, source_span
import hashlib


def export(root, output):
    if output.exists():
        raise ValueError('Use a fresh recipe file')
    game = root / 'MW3/Mech3.exe'
    provider = root / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'

    def spans(image, ranges):
        blob = image.read_bytes()
        return [dict(start=a, end=b, sha256=hashlib.sha256(source_span(blob, a, b)).hexdigest()) for a,b in ranges]

    def pin(relative):
        path = root / relative
        return dict(expected_object_sha256=sha(path), coff_timestamp=struct.unpack_from('<I', path.read_bytes(), 4)[0])

    layout = json.loads((root / 'reports/m4-crt-control/research-r1/layout.json').read_text())
    pcs = sorted({pc for item in layout['functions'].values() for pc in item['CFG']['instruction_PCs']})
    recovery = json.loads((root / 'reports/m4-crt-fdiv/source-recovery-r1/report.json').read_text())
    result = dict(contract='mw3-control-startup-v1', game_sha256=sha(game), provider_sha256=sha(provider),
        provider=dict(image='provider', entries=[0x780042e1,0x780042f7,0x7800432c,0x7800439f],
            instruction_pcs=pcs, spans=spans(provider, [(0x780042e1,0x78004410),(0x7801129b,0x78011318)])),
        game=dict(image='game', entries=[0x5ac5a0,0x5ac5d6], spans=spans(game, [(0x5ac5a0,0x5ac5b3),(0x5ac5d6,0x5ac5dc)])),
        writer=dict(image='provider', entries=[0x78004254,0x7800426b,0x780042a3,0x780042cf,0x7802c070,
            0x780042e1,0x780042f7,0x7800432c,0x7800439f],
            spans=[dict(start=s['address'],end=s['address']+s['size_bytes'],sha256=s['sha256']) for s in recovery['source_spans']]),
        control_object=pin('reports/m4-crt-entry-control/build-r6/control-O2.obj'),
        writer_object=pin('reports/m4-crt-fdiv/native-build-r3/writer-O2.obj'))
    names = ['sub_5ac5a0','sub_5ac5d6','__remill_flag_computation_zero','__remill_flag_computation_sign',
        '__remill_undefined_8','__remill_compare_eq','__remill_compare_neq','__remill_flag_computation_carry','__remill_flag_computation_overflow']
    result['control_object']['symbol_renames'] = {name:'mw34_entry_control_'+name for name in names}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result,indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    export(args.root.resolve(), args.output.resolve())
