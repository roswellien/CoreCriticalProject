"""Development-only BEFORE/source prediction on a previously accepted API witness."""
import copy
import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path
sys.dont_write_bytecode = True
from consumer import F, M, predict as consumer_predict
from model import expected
import parser
sys.path.insert(0, str(F.ROOT / 'tools/m4-pipeline'))
from capture_bundle import CaptureBundle, sha_file
from manifests import verify_manifest
from paths import publish_bytes, workspace_path


def main(directory):
    out = workspace_path(directory, reports=True)
    if out.exists() or out.parent != F.ROOT / 'reports/m4-crt-parser-prefix':
        raise ValueError('Fresh preview output required')
    out.mkdir()
    previous = F.pin(F.ROOT / 'reports/m4-crt-commandline-carry/root-execution-r1/report.json',
                     '930355cc98ecb11eb7f9d57621b69fd9fa9c0ac1df8a14deee363738efa32bf9')
    execution = json.loads(previous.read_text(encoding='utf-8'))
    source = M.source_material(out)
    program, providers, maths, ctrl, init, args, argv, pages, commands = source
    wp, pp, gp = M.R.source_material()
    original = F.pin(F.ROOT / 'reports/m4-crt-fdiv-reference/run-normal-r1/original.bin', F.ORIGINAL_SHA)
    payload = M.R.project(M.R.originals(original.read_bytes())[0])
    parser_program, command = parser.source_material(out)
    identity = execution['levels']['O0']
    with CaptureBundle(identity['bundle'], identity['bundle_sha256']) as reader:
        row = F.LogicalPath(reader, 'row-0')
        host_bytes = (row / 'commandline-api-bytes.bin').read_bytes()
        F.require(host_bytes == subprocess.list2cmdline(identity['argv']).encode('mbcs') + b'\0',
                  'Previously admitted actual API witness remains tied to its launch')
        entry, phases = expected(row, payload, wp, pp, gp, program, providers, maths,
                                ctrl, init, args, argv, pages, host_bytes, 'O0')
        # Only the filename API result is an external service witness. No native
        # State, registers, memory pages or parser output supplies the machine.
        state, memory = bytearray(entry.state), copy.deepcopy(entry.mem)
        witness = (row / 'filename-witness.bin').read_bytes()
        capacity, incoming, length, error = struct.unpack_from('<4I', witness)
        F.require(capacity == 260 and incoming == 0xa11c0000 and 0 < length < 260,
                  'Original accepted bounded filename request witness')
        memory[0x7803b000][0x3f0:0x4f4] = witness[276:]
        struct.pack_into('<I', state, 2216, length)
        struct.pack_into('<I', state, 2312, 0x20001844)
        struct.pack_into('<I', state, 2472, 0x7800bbd6)
        before = type('BeforeConsumer', (), dict(state=state, mem=memory, fx=entry.fx,
                                                runtime_cpu=entry.runtime_cpu))()
        consumed = consumer_predict(before, argv, host_bytes)
        before_parser = type('BeforeParser', (), dict(state=consumed['state'], mem=consumed['memory'],
                            fx=consumed['fx'], runtime_cpu=consumed['cpu']))()
        result = parser.predict(before_parser, parser_program, host_bytes)
    registers = {name: struct.unpack_from('<I', result['state'], off)[0] for name, off in parser.STATE_REG.items()}
    F.require(len(result['accesses']) == 16 and len(result['PCs']) == 23 and
              result['stop_PC'] == 0x7800bce6 and result['stop_address'] == 0x78037a25,
              'Independent literal prefix trace and first unresolved table dependency')
    F.require(registers['esp'] == 0x2000181c and registers['ebp'] == 0x20001828 and
              registers['eax'] == 0x33000001 and registers['ebx'] == 0x44 and
              registers['ecx'] == 0x2000184c and registers['esi'] == registers['edi'] == 0,
              'Source-derived prefix registers')
    counts = struct.unpack_from('<2I', result['memory'][0x20001000], 0x84c)
    F.require(counts == (1, 1) and not result['locale_read_completed'],
              'Source-written count locals without table read or sizing completion')
    for p in Path(__file__).parent.glob('*.py'):
        F.pin(p)
    for p in out.iterdir():
        if p.is_file():
            F.pin(p)
    for module in (M, M.M, M.M.M, M.M.M.M, M.D, M.R, M.N, M.D.E, M.F, M.C):
        for p, h in module.PINS.items():
            F.pin(p, h)
    closure = verify_manifest(F.PHYSICAL)
    report = dict(passed=True, scope='Development-only original BEFORE/source prefix prediction; no current native admission',
        source_bytes=436, registers=registers, counts=counts, PCs=result['PCs'], accesses=result['accesses'],
        stop_PC=result['stop_PC'], stop_address=result['stop_address'], physical_closure=closure,
        native_parser_executed=False, original_executed=False, guest_machine_seeded_from_AFTER=False,
        whole_M4_complete=False, files=F.PHYSICAL)
    publish_bytes(out / 'report.json', (json.dumps(report, indent=2) + '\n').encode('utf-8'))
    print(json.dumps({k: v for k, v in report.items() if k not in ('files', 'PCs', 'accesses')}))


if __name__ == '__main__':
    main(*sys.argv[1:])
