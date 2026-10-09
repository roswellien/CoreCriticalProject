"""Rehash independent compiled fixtures and inspect direct hardware boundaries.

This review grants no original-process equivalence and predicts no guest result
from captured AFTER State. The parent independently models guest execution.
"""
import hashlib, json, pathlib, re, struct, subprocess, sys, traceback
sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = ROOT / 'reports/m4-crt-filename'
PINS = {}

def need(ok, why):
    if not ok: raise ValueError(why)

def sha(path):
    with pathlib.Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def pin(path, expected=None):
    path = pathlib.Path(path).resolve(); digest = sha(path)
    need(expected is None or digest == expected, 'Exact compiled fixture binding: ' + str(path))
    need(str(path) not in PINS or PINS[str(path)] == digest, 'Conflicting physical binding')
    PINS[str(path)] = digest
    return path

def read(path):
    return json.loads(pin(path).read_text(encoding='utf-8-sig'))

def map_receipt(receipt):
    count = 0
    for key in ('sources', 'source_files', 'tools', 'tool_files', 'libraries',
                'entry_objects', 'matherr_objects', 'control_objects', 'initterm_objects', 'mainargs_objects', 'normal_argv_objects',
                'compiler_read_headers', 'artifacts'):
        for path, digest in receipt.get(key, {}).items():
            pin(path, digest); count += 1
    return count

def host_pair(before, after, scenario):
    b = pin(before).read_bytes(); a = pin(after).read_bytes()
    need(len(b) == len(a) == 544, 'Aligned direct ASM hardware FX512 plus ENV28 record')
    need(b[512:540] == a[512:540], 'Complete direct legacy ENV preserved across actual call and catch')
    ranges = [(0, 5), (24, 28)]
    ranges += [(32+16*i, 42+16*i) for i in range(8)]
    ranges += [(160+16*i, 176+16*i) for i in range(6, 16)]
    for lo, hi in ranges:
        need(b[lo:hi] == a[lo:hi], 'Caller CW/SW/FTW/MXCSR/raw80/ABI XMM6..15 retained')
    for i in range(6, 16):
        expected = bytes((i*31+k*17+scenario+1) & 255 for k in range(16))
        need(b[160+16*i:176+16*i] == expected, 'Distinct directly measured BEFORE ABI XMM fixture')
    metadata = struct.pack('<IHHIH', 0x11223344, 0x23, 0x11d, 0x55667788, 0x2b)
    need(b[524:538] == metadata, 'Measured nonzero FIP/CS/FOP/FDP/DS legacy hardware BEFORE')
    top = 3 if scenario % 2 else 7; depth = (0, 1, 3, 7)[scenario % 4]
    ftw = sum(1 << ((top+i) & 7) for i in range(depth))
    need(struct.unpack_from('<H', b)[0] == 0xa7f and
         struct.unpack_from('<H', b, 2)[0] == top*2048+0x20 and b[4] == ftw and
         struct.unpack_from('<I', b, 24)[0] == 0x1fa0,
         'Measured occupied/empty x87 TOP, sticky SW, masked CW and MXCSR BEFORE')
    return {'TOP': top, 'depth': depth, 'metadata_nonzero': True,
            'volatile_XMM0_5_equality_claimed': False}

def decode(path, output, label):
    path = pin(path)
    directory = ROOT / 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
    objdump = pin(directory/'llvm-objdump.exe'); readobj = pin(directory/'llvm-readobj.exe')
    commands = []
    contents = []
    for tool, arguments, suffix in ((objdump, ['--disassemble', '--reloc', '--x86-asm-syntax=intel'], 'decode'),
                                    (readobj, ['--unwind'], 'unwind')):
        command = [str(tool)] + arguments + [str(path)]
        result = subprocess.run(command, capture_output=True, text=True)
        need(result.returncode == 0, 'Fresh actual compiled decode/unwind tool succeeded')
        target = output/(label+'-'+suffix+'.txt'); target.write_text(result.stdout)
        pin(target); contents.append(result.stdout)
        commands.append({'command': command, 'exit_code': result.returncode,
                         'output_path': str(target), 'output_sha256': sha(target)})
    return contents, commands

def review(build_path, output):
    need(output.parent == BASE and output.name.startswith('independent-compiled-') and not output.exists(),
         'Fresh immediate independent compiled report')
    output.mkdir(parents=True)
    source = pathlib.Path(__file__).resolve(); pin(source)
    build = read(build_path); need(build['passed'], 'Actual independent compiled fixtures passed')
    bindings = map_receipt(build)
    checks = scenarios = records = malformed = 0; host_domains = []; commands = []; objects = []
    for level in ('O0', 'O2'):
        directory = build_path.parent/level/'actual'; result = read(directory/'controls.json')
        need(result['passed'], 'Actual fixture assertions completed')
        log = pin(build_path.parent/level/'controls.log').read_text()
        match = re.fullmatch(r'(\d+) independent compiled checks / (\d+) scenarios passed\s*', log)
        need(match and int(match[1]) == result['checks']+1 and int(match[2]) == result['scenarios'],
             'Independent assertion log/result framing')
        checks += int(match[1]); scenarios += result['scenarios']
        malformed += result.get('malformed_token_denials', 0)
        cases = sorted(directory.glob('case-*'), key=lambda path: int(path.name.split('-')[-1]))
        need(len(cases) == result['scenarios'], 'One fresh actual directory per scenario')
        for row in cases:
            scenario = int(row.name.split('-')[-1])
            for name in ('writer', 'entry'):
                host_domains.append(host_pair(row/(name+'-host-before.bin'), row/(name+'-host-after.bin'), scenario))
                records += 1
        obj = build_path.parent/level/'controls.obj'
        (compiled, unwind), decoded_commands = decode(obj, output, level+'-independent-fixture')
        commands += decoded_commands
        need('sub_5ac3a0' in compiled and 'sub_5ac5a0' in compiled and 'sub_7800b38f' in compiled and
             'sub_780042e1' in compiled and 'sub_780014f8' in compiled and
             'mw34_mainargs_mainargs_body' in compiled and 'mw34_mainargs_normal_argv_body' in compiled,
             'Fixture links actual entry/control/matherr/initterm/mainargs/builder translated symbols')
        need('__CxxFrameHandler' in unwind, 'Compiled fixture has actual C++ exception unwind handlers')
        objects.append({'level': level, 'path': str(obj), 'sha256': sha(obj), 'unwind_inspected': True})
    need(records == scenarios*2, 'Every actual scenario measures producer and entered root boundary')
    need({v['TOP'] for v in host_domains} == {3, 7} and {v['depth'] for v in host_domains} == {0, 1, 3, 7},
         'Direct hardware measured all declared nonempty/empty caller domains')
    for path, digest in list(PINS.items()): need(sha(path) == digest, 'Stable final binding: ' + path)
    report = {'passed': True, 'scope': 'Independent actual compiled causal and direct hardware caller review; parent scalar source observer is separate',
              'build_path': str(build_path), 'physical_bindings_rehashed': bindings,
              'checks': checks, 'scenarios': scenarios, 'direct_host_records': records,
              'nonzero_complete_legacy_metadata_records': records, 'malformed_token_denials': malformed,
              'host_CW': 0xa7f, 'host_TOP': [3, 7], 'host_live_x87_depths': [0, 1, 3, 7],
              'host_SW_sticky': 0x20, 'host_MXCSR': 0x1fa0, 'objects': objects,
              'ordinary_game_launched': False, 'original_executed': False,
              'guest_original_equivalence_claimed': False, 'whole_M4_complete': False,
              'tools_commands': commands, 'files': PINS}
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({key: report[key] for key in ('passed', 'checks', 'scenarios', 'direct_host_records', 'malformed_token_denials')}))

if __name__ == '__main__':
    try:
        need(len(sys.argv) == 3, 'review.py compiled-build.json fresh-independent-compiled-output')
        review(pathlib.Path(sys.argv[1]).resolve(), pathlib.Path(sys.argv[2]).resolve())
    except Exception:
        traceback.print_exc(); sys.exit(1)
