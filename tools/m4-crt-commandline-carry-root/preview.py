"""Preserved one-row observer development check; supplies no root admission."""
import json
import sys
import traceback
from pathlib import Path
sys.dont_write_bytecode = True
from observe import positive
from model import expected
from consumer import F, M

class FlatRow:
    def __init__(self, root):
        self.root = root
    def names(self):
        return ['row-0/' + p.relative_to(self.root / 'row-0').as_posix()
                for p in (self.root / 'row-0').rglob('*') if p.is_file()]
    def read_bytes(self, name):
        return (self.root / name).read_bytes()

def main(receipt, directory):
    out = Path(directory).absolute()
    if out.exists() or out.parent != F.ROOT / 'reports/m4-crt-commandline-carry':
        raise ValueError('Fresh model preview output required')
    out.mkdir()
    passed = False
    try:
        value = json.loads(Path(receipt).read_text(encoding='utf-8'))
        command = value['commands'][0]['arguments']
        row = F.LogicalPath(FlatRow(Path(command[-1])), 'row-0')
        program, providers, maths, ctrl, init, args, argv, source, commands = M.source_material(out)
        wp, pp, gp = M.R.source_material()
        payload = M.R.project(M.R.originals((F.ROOT / 'reports/m4-crt-fdiv-reference/run-normal-r1/original.bin').read_bytes())[0])
        host_bytes = (row / 'commandline-api-bytes.bin').read_bytes()
        entry, phases = expected(row, payload, wp, pp, gp, program, providers,
            maths, ctrl, init, args, argv, source, host_bytes, 'O0')
        positive(row, entry, phases, argv, 0, Path(command[0]), host_bytes, command, False)
        passed = True
    except Exception:
        (out / 'failure.txt').write_text(traceback.format_exc(), encoding='utf-8')
        raise
    finally:
        (out / 'report.json').write_text(json.dumps(dict(passed=passed,
            scope='Observer-development preview of one older author row; no root execution or final admission',
            root_native_executed=False, whole_M4_complete=False), indent=2) + '\n', encoding='utf-8')
        print(json.dumps(dict(passed=passed, checks=F.CHECKS, scope='Model preview only')))

if __name__ == '__main__':
    main(*sys.argv[1:])
